#!/usr/bin/env python3
"""Architecture Case RAG 命令行检索工具，仅依赖 Python 标准库。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, Iterable, List, Sequence

from semantic_index import (
    DEFAULT_MODEL,
    SemanticIndexError,
    aggregate_case_sections,
    cosine_similarity,
    corpus_fingerprint,
    embed_texts,
    extract_sections,
    hybrid_score,
    load_semantic_index,
)
from rerank_cases import DEFAULT_RERANK_MODEL, DEFAULT_RERANK_TOP, RerankError, rerank
from lexical_retrieval import retrieve as lexical_retrieve


RAG_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = RAG_ROOT / "index" / "cases.json"
DEFAULT_SEMANTIC_INDEX = RAG_ROOT / "index" / "semantic-sections.json"


class SearchError(ValueError):
    """索引或查询参数无法用于检索。"""


def normalize(value: Any) -> str:
    """统一英文大小写，并忽略关键词两端空白。"""
    return str(value).strip().casefold()


def normalize_query(query: str) -> str:
    """Remove accidental whitespace while preserving natural-language meaning."""
    return re.sub(r"\s+", " ", query).strip()


def as_tags(value: Any) -> List[str]:
    """把 frontmatter 标签字段规范为字符串列表。"""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def quality_stars(value: Any) -> int:
    """把 ★★★ 等级转换为整数。"""
    return str(value or "").count("★")


def numeric_year(value: Any) -> int | None:
    """把索引年份转换为整数；未知年份返回 None。"""
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_problem_section(markdown: str) -> str:
    """提取“## 2. 核心设计问题”到下一个二级标题之前的正文。"""
    lines = markdown.splitlines()
    captured: List[str] = []
    in_section = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if in_section:
                break
            normalized_heading = heading.lstrip("2").lstrip(".、 ")
            if heading.startswith("2") and normalized_heading.startswith("核心设计问题"):
                in_section = True
            continue
        if in_section:
            captured.append(line)
    return "\n".join(captured).strip()


def _has_exact_tag(record: Dict[str, Any], field: str, expected: str | None) -> bool:
    if expected is None:
        return True
    needle = normalize(expected)
    return any(normalize(tag) == needle for tag in as_tags(record.get(field)))


def _all_keywords_match(text: str, keywords: Sequence[str] | None) -> bool:
    if not keywords:
        return True
    normalized_text = text.casefold()
    return all(normalize(keyword) in normalized_text for keyword in keywords)


def _tag_overlap(query: str, tags: Sequence[str]) -> float:
    """Return a conservative lexical tag-evidence ratio for natural-language queries."""
    query_text = normalize(query).replace("-", " ")
    aliases = {
        "daylight": ("采光", "日照", "光线"), "natural-ventilation": ("通风",),
        "indoor-outdoor": ("室外", "室内外", "户外"), "topography": ("坡地", "高差", "地形"),
        "vertical-circulation": ("竖向", "楼梯", "坡道"), "circulation-conflict": ("流线", "走廊"),
        "heritage-conservation": ("遗产", "保护", "遗址"), "urban-regeneration": ("更新", "改造"),
        "public-realm": ("公共空间", "公共活动"), "landscape-response": ("景观", "山地", "滨水"),
        "children-supervision": ("儿童", "幼儿", "看护"), "play-learning": ("儿童", "幼儿", "游戏", "学习"),
        "loop-circulation": ("环形", "环行", "环路"), "terrace": ("露台", "退台", "平台"),
        "sunken-space": ("下沉", "地下"), "adaptive-reuse": ("改造", "再利用"),
        "courtyard": ("庭院",), "atrium": ("中庭",), "continuous-ramp": ("坡道",),
    }
    matches = 0
    for tag in tags:
        tag_key = normalize(tag)
        if tag_key.replace("-", " ") in query_text or any(term in query_text for term in aliases.get(tag_key, ())):
            matches += 1
    return min(1.0, matches / 2.0)


def _quality_score(record: Dict[str, Any]) -> int:
    return quality_stars(record.get("quality"))


def load_index(index_path: Path) -> List[Dict[str, Any]]:
    """读取并校验最外层索引结构。"""
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SearchError(f"索引不存在：{index_path}；请先运行 build_index.py") from exc
    except json.JSONDecodeError as exc:
        raise SearchError(f"索引不是有效 JSON：{index_path}（{exc}）") from exc
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise SearchError("索引根节点必须是对象数组")
    return data


def search(
    index_path: Path,
    rag_root: Path,
    *,
    problem: Sequence[str] | None = None,
    type_filter: str | None = None,
    site: str | None = None,
    strategy: str | None = None,
    minimum_quality: int | None = None,
    keyword: Sequence[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    maximum: int = 10,
) -> List[Dict[str, Any]]:
    """组合过滤案例，并按问题标签命中数、质量、年份降序排序。"""
    if maximum < 1:
        raise SearchError("--max 必须大于等于 1")
    if minimum_quality is not None and not 1 <= minimum_quality <= 5:
        raise SearchError("--quality 必须是 1 到 5 的整数")
    if year_from is not None and year_to is not None and year_from > year_to:
        raise SearchError("--year-from 不能晚于 --year-to")

    problem_terms = [term for term in (problem or []) if normalize(term)]
    keyword_terms = [term for term in (keyword or []) if normalize(term)]
    results: List[Dict[str, Any]] = []
    for source_record in load_index(index_path):
        if not _has_exact_tag(source_record, "type", type_filter):
            continue
        if not _has_exact_tag(source_record, "site", site):
            continue
        if not _has_exact_tag(source_record, "strategy", strategy):
            continue
        stars = quality_stars(source_record.get("quality"))
        if minimum_quality is not None and stars < minimum_quality:
            continue
        year = numeric_year(source_record.get("year"))
        if year_from is not None and (year is None or year < year_from):
            continue
        if year_to is not None and (year is None or year > year_to):
            continue

        relative_path = source_record.get("path")
        if not isinstance(relative_path, str) or not relative_path:
            raise SearchError(f"案例 {source_record.get('id', '<未知>')} 缺少 path 字段")
        case_path = rag_root / relative_path
        try:
            markdown = case_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SearchError(f"无法读取案例正文：{case_path}（{exc}）") from exc
        if not _all_keywords_match(markdown, keyword_terms):
            continue

        problem_tags = as_tags(source_record.get("problem"))
        normalized_tags = {normalize(tag): tag for tag in problem_tags}
        problem_text = extract_problem_section(markdown).casefold()
        matched_tags: List[str] = []
        if problem_terms:
            all_problem_terms_match = True
            for term in problem_terms:
                normalized_term = normalize(term)
                if normalized_term in normalized_tags:
                    matched_tags.append(normalized_tags[normalized_term])
                elif normalized_term not in problem_text:
                    all_problem_terms_match = False
                    break
            if not all_problem_terms_match:
                continue

        record = dict(source_record)
        record["_matched_problem_tags"] = list(dict.fromkeys(matched_tags))
        record["_problem_terms"] = problem_terms
        record["_quality_stars"] = stars
        record["_numeric_year"] = year
        results.append(record)

    results.sort(
        key=lambda item: (
            -len(item["_matched_problem_tags"]),
            -item["_quality_stars"],
            -(item["_numeric_year"] if item["_numeric_year"] is not None else -1),
            normalize(item.get("id", "")),
        )
    )
    return results[:maximum]


def semantic_search(
    index_path: Path,
    semantic_index_path: Path,
    rag_root: Path,
    *,
    query: str,
    mode: str = "hybrid",
    type_filter: str | None = None,
    site: str | None = None,
    strategy: str | None = None,
    minimum_quality: int | None = None,
    keyword: Sequence[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    maximum: int = 10,
    embedding_timeout: int | None = None,
) -> List[Dict[str, Any]]:
    """Retrieve sections semantically, then aggregate results to architecture cases."""
    if mode not in {"semantic", "hybrid"}:
        raise SearchError("语义检索模式必须是 semantic 或 hybrid")
    normalized_query = normalize_query(query)
    if not normalized_query:
        raise SearchError("--query 不能为空")
    if maximum < 1:
        raise SearchError("--max 必须大于等于 1")
    if minimum_quality is not None and not 1 <= minimum_quality <= 5:
        raise SearchError("--quality 必须是 1 到 5 的整数")
    if year_from is not None and year_to is not None and year_from > year_to:
        raise SearchError("--year-from 不能晚于 --year-to")

    semantic_payload = load_semantic_index(semantic_index_path)
    case_record_list = load_index(index_path)
    indexed_fingerprint = semantic_payload.get("corpus_sha256")
    if indexed_fingerprint:
        current_fingerprint = corpus_fingerprint(case_record_list, rag_root)
        if current_fingerprint != indexed_fingerprint:
            raise SearchError("semantic index 已过期：案例正文或摘要已变化；请运行 build_semantic_index.py")
    model = str(semantic_payload.get("model") or DEFAULT_MODEL)
    embedding_options = {"model": model}
    if embedding_timeout is not None:
        embedding_options["timeout"] = embedding_timeout
    query_vector = embed_texts([normalized_query], **embedding_options)[0]
    if len(query_vector) != semantic_payload["embedding_dimensions"]:
        raise SearchError("query embedding 维度与 semantic index 不一致；请重建索引或检查模型")
    case_records = {str(item.get("id")): item for item in case_record_list}
    keyword_terms = [term for term in (keyword or []) if normalize(term)]
    section_results: List[Dict[str, Any]] = []
    for section in semantic_payload["sections"]:
        case_id = str(section.get("case_id", ""))
        record = case_records.get(case_id)
        if not record:
            continue
        if not _has_exact_tag(record, "type", type_filter):
            continue
        if not _has_exact_tag(record, "site", site):
            continue
        if not _has_exact_tag(record, "strategy", strategy):
            continue
        quality = _quality_score(record)
        if minimum_quality is not None and quality < minimum_quality:
            continue
        year = numeric_year(record.get("year"))
        if year_from is not None and (year is None or year < year_from):
            continue
        if year_to is not None and (year is None or year > year_to):
            continue
        if keyword_terms:
            path = rag_root / str(record.get("path", ""))
            if not _all_keywords_match(path.read_text(encoding="utf-8"), keyword_terms):
                continue
        semantic_score = max(0.0, cosine_similarity(query_vector, section.get("embedding", [])))
        if mode == "semantic":
            score = semantic_score
        else:
            score = hybrid_score(
                semantic=semantic_score,
                problem_match=_tag_overlap(normalized_query, as_tags(record.get("problem"))),
                strategy_match=_tag_overlap(normalized_query, as_tags(record.get("strategy"))),
                site_match=_tag_overlap(normalized_query, as_tags(record.get("site"))),
                type_match=1.0 if type_filter and _has_exact_tag(record, "type", type_filter) else _tag_overlap(normalized_query, as_tags(record.get("type"))),
                keyword_evidence=1.0 if keyword_terms else 0.0,
                quality=quality,
            )
        section_results.append(
            {
                **record,
                "case_id": case_id,
                "section": section.get("section", "summary"),
                "section_text": section.get("text", ""),
                "semantic_score": semantic_score,
                "score": score,
            }
        )
    results = aggregate_case_sections(section_results)
    for result in results:
        result["_query"] = normalized_query
        result["_mode"] = mode
    return results[:maximum]


def attach_baseline_evidence(
    results: Sequence[Dict[str, Any]],
    rag_root: Path,
    terms: Sequence[str],
) -> None:
    """Attach section-level evidence to baseline results before card output.

    Baseline search is tag/keyword based and does not use the semantic index, so
    results otherwise carry no evidence sections and violate the handoff-card
    contract.  This keeps baseline cards useful without pretending they are
    semantic matches.
    """
    normalized_terms = [normalize(term) for term in terms if normalize(term)]
    for record in results:
        if record.get("evidence_sections") and record.get("evidence_texts"):
            continue
        case_path = rag_root / str(record.get("path", ""))
        try:
            markdown = case_path.read_text(encoding="utf-8")
        except OSError:
            continue
        sections = extract_sections(record, markdown)
        if not sections:
            continue
        scored = []
        for section in sections:
            text = str(section.get("text", "")).casefold()
            score = sum(1 for term in normalized_terms if term in text)
            scored.append((score, section))
        scored.sort(
            key=lambda item: (-item[0], 0 if item[1].get("section") == "summary" else 1)
        )
        positive = [section for score, section in scored if score > 0]
        chosen = positive[:3] or sections[:2]
        record["evidence_sections"] = [str(section.get("section")) for section in chosen]
        record["evidence_texts"] = [str(section.get("text", ""))[:900] for section in chosen]


def rag_transfer_cards(
    results: Sequence[Dict[str, Any]],
    *,
    query: str,
    mode: str,
    semantic_metadata: Dict[str, Any] | None = None,
    index_metadata: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Serialize retrieval evidence into the compact, reproducible Scheme handoff contract."""
    metadata = semantic_metadata or index_metadata or {}
    index = {
        key: metadata.get(key)
        for key in (
            "version",
            "model",
            "corpus_sha256",
            "embedding_dimensions",
            "index_sha256",
            "cases",
            "index_path",
        )
        if metadata.get(key) is not None
    }
    cards: List[Dict[str, Any]] = []
    for record in results:
        sections = record.get("evidence_sections") or []
        texts = record.get("evidence_texts") or []
        cards.append(
            {
                "query": query,
                "mode": mode,
                "index": index,
                "case": {
                    "id": record.get("id", record.get("case_id")),
                    "title": record.get("title"),
                    "path": record.get("path"),
                    "quality": record.get("quality"),
                },
                "evidence": [
                    {"section": section, "text": text}
                    for section, text in zip(sections, texts)
                ],
                "sources": record.get("sources") or [],
                "transferable_operation": record.get("transferable_method", "待 Concept/Scheme 基于证据转译"),
                "do_not_copy_or_gap": record.get("limitations", "需阅读案例第 15 节并记录本项目差异"),
                "scheme_decision": {
                    "status": "unresolved",
                    "required_fields": [
                        "project_problem", "same_conditions", "different_conditions",
                        "transferable_operation", "target_artifact", "validation", "reject_reason",
                    ],
                    "note": "本卡是可选检索记录，不是批准或必经关卡；采用时简短记录适用条件、模型位置和验证结果即可，兼容字段列表不要求全部填写。",
                },
            }
        )
    return cards


def rerank_with_fallback(
    query: str,
    results: Sequence[Dict[str, Any]],
    *,
    model: str = DEFAULT_RERANK_MODEL,
    top_n: int = DEFAULT_RERANK_TOP,
) -> tuple[List[Dict[str, Any]], str | None]:
    """Keep quality mode optional when the local LLM is unavailable or malformed."""
    try:
        return rerank(query, results, model=model, top_n=top_n), None
    except RerankError as exc:
        return list(results), f"quality rerank 不可用，已回退 fast 结果：{exc}"


def format_results(results: Iterable[Dict[str, Any]]) -> str:
    """输出编号、核心元数据、匹配问题标签和文件路径。"""
    rows = list(results)
    if not rows:
        return "未找到匹配案例。\n结果数：0"
    lines = [f"结果数：{len(rows)}"]
    for number, record in enumerate(rows, 1):
        if "score" in record:
            if record.get("retrieval_mode") == "lexical":
                lines.append(f"{number}. {record.get('id')} | {record.get('title')} | "
                             f"mode=lexical | score={record['score']:.3f} | "
                             f"文字证据：{', '.join(record.get('evidence_sections', []))} | "
                             f"图纸尚未查看 | {record.get('path')}")
                continue
            evidence = ", ".join(record.get("evidence_sections", [])) or "—"
            judgement = ""
            if record.get("relevance") is not None:
                judgement = (
                    f" | LLM relevance={int(record['relevance'])} | 匹配：{record.get('matched_problem', '—')}"
                    f" | 可迁移：{record.get('transferable_method', '—')} | 限制：{record.get('limitations', '—')}"
                )
            lines.append(
                f"{number}. {record.get('id', record.get('case_id', '—'))} | {record.get('title', '—')} | "
                f"score={float(record['score']):.3f} | semantic={float(record.get('semantic_score', 0)):.3f} | "
                f"证据章节：{evidence} | {record.get('quality', '—')} | {record.get('path', '—')}{judgement}"
            )
            continue
        matched_tags = record.get("_matched_problem_tags", [])
        problem_terms = record.get("_problem_terms", [])
        if matched_tags:
            match_display = ", ".join(matched_tags)
        elif problem_terms:
            match_display = "正文匹配（" + ", ".join(problem_terms) + "）"
        else:
            match_display = "—"
        type_display = ", ".join(as_tags(record.get("type"))) or "—"
        year_display = record.get("year") if record.get("year") is not None else "未知"
        quality_display = record.get("quality") or "—"
        lines.append(
            f"{number}. {record.get('id', '—')} | {record.get('title', '—')} | "
            f"{year_display} | {record.get('location', '—')} | {type_display} | "
            f"{quality_display} | 匹配问题标签：{match_display} | {record.get('path', '—')}"
        )
    return "\n".join(lines)


def quality_argument(value: str) -> int:
    try:
        quality = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是 1 到 5 的整数") from exc
    if not 1 <= quality <= 5:
        raise argparse.ArgumentTypeError("必须是 1 到 5 的整数")
    return quality


def lexical_search(index_path: Path, rag_root: Path, *, query: str,
                   type_filter=None, site=None, strategy=None, minimum_quality=None,
                   keyword=None, year_from=None, year_to=None, maximum=5):
    """Reuse exact filters, then rank actual positive text evidence offline."""
    records = search(index_path, rag_root, type_filter=type_filter, site=site,
                     strategy=strategy, minimum_quality=minimum_quality, keyword=keyword,
                     year_from=year_from, year_to=year_to,
                     maximum=max(1, len(load_index(index_path))))
    return lexical_retrieve(records, rag_root, query, maximum)


def positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是正整数") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("必须是正整数")
    return number


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检索 Architecture Case RAG（设计问题匹配优先）"
    )
    parser.add_argument(
        "--query",
        help="自然语言建筑设计问题；默认auto尝试embedding语义检索，失败时明确回退离线文字检索",
    )
    parser.add_argument(
        "--problem",
        nargs="+",
        help="设计问题关键词；多词 AND，每词须命中 problem 标签或第 2 节正文",
    )
    parser.add_argument("--type", dest="type_filter", help="建筑类型标签（精确匹配）")
    parser.add_argument("--site", help="场地标签（精确匹配）")
    parser.add_argument("--strategy", help="策略标签（精确匹配）")
    parser.add_argument("--quality", type=quality_argument, help="最低质量星级（1-5）")
    parser.add_argument("--keyword", nargs="+", help="完整 Markdown 正文关键词；多词 AND")
    parser.add_argument("--year-from", type=int, help="最早年份（含）")
    parser.add_argument("--year-to", "--to", dest="year_to", type=int, help="最晚年份（含）")
    parser.add_argument("--max", dest="maximum", type=positive_integer, default=10, help="最多输出条数（默认 10）")
    parser.add_argument("--mode", choices=("auto", "baseline", "lexical", "semantic", "hybrid"), default=None, help="--query默认auto；lexical不需要Ollama；baseline仅精确过滤")
    parser.add_argument("--quality-mode", action="store_true", help="对当前 semantic/hybrid Top 20 启用可选本地 LLM evidence rerank")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help=argparse.SUPPRESS)
    parser.add_argument("--rerank-top", type=positive_integer, default=DEFAULT_RERANK_TOP, help="quality mode 最大复核案例数（默认 5）")
    parser.add_argument("--format", choices=("text", "json", "card"), default="text", help="输出格式；card 供 Concept→Scheme handoff")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help=argparse.SUPPRESS)
    parser.add_argument("--semantic-index", type=Path, default=DEFAULT_SEMANTIC_INDEX, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    index_path = args.index.resolve()
    rag_root = RAG_ROOT if index_path == DEFAULT_INDEX.resolve() else index_path.parent.parent
    try:
        if args.query is not None and not normalize_query(args.query):
            raise SearchError("--query 不能为空")
        mode = args.mode or ("auto" if args.query else "baseline")
        semantic_metadata: Dict[str, Any] | None = None
        baseline_metadata: Dict[str, Any] | None = None
        if mode == "baseline":
            if args.query:
                raise SearchError("baseline只做精确过滤，不接受--query；自然语言请用auto或lexical，避免忽略问题返回无关列表")
            results = search(
                index_path, rag_root, problem=args.problem, type_filter=args.type_filter,
                site=args.site, strategy=args.strategy, minimum_quality=args.quality,
                keyword=args.keyword, year_from=args.year_from, year_to=args.year_to,
                maximum=args.maximum,
            )
            baseline_terms: List[str] = []
            if args.query:
                baseline_terms.extend(args.query.split())
            baseline_terms.extend(args.problem or [])
            baseline_terms.extend(args.keyword or [])
            attach_baseline_evidence(results, rag_root, baseline_terms)
            baseline_metadata = {
                "version": "baseline-v1",
                "index_path": (
                    str(index_path.relative_to(rag_root))
                    if index_path.is_relative_to(rag_root)
                    else str(index_path)
                ),
                "index_sha256": hashlib.sha256(index_path.read_bytes()).hexdigest(),
                "cases": len(load_index(index_path)),
            }
        elif mode == "lexical":
            if not args.query or args.problem:
                raise SearchError("lexical需要--query；--problem仅用于baseline精确过滤")
            results = lexical_search(index_path, rag_root, query=args.query,
                type_filter=args.type_filter, site=args.site, strategy=args.strategy,
                minimum_quality=args.quality, keyword=args.keyword,
                year_from=args.year_from, year_to=args.year_to, maximum=args.maximum)
            baseline_metadata = {"version":"lexical-v1", "index_path":str(index_path),
                "index_sha256":hashlib.sha256(index_path.read_bytes()).hexdigest(),
                "cases":len(load_index(index_path))}
            if args.quality_mode:
                print("lexical模式未运行本地LLM重排；文字匹配不等于语义理解或图纸核验。", file=sys.stderr)
        else:
            if not args.query:
                raise SearchError("semantic/hybrid 模式需要 --query")
            if args.problem:
                raise SearchError("--query 与 --problem 不能同时使用；--problem 仅用于 baseline 精确检索")
            try:
                results = semantic_search(
                    index_path, args.semantic_index.resolve(), rag_root, query=args.query,
                    mode=("semantic" if mode == "auto" else mode),
                    type_filter=args.type_filter, site=args.site, strategy=args.strategy,
                    minimum_quality=args.quality, keyword=args.keyword, year_from=args.year_from,
                    year_to=args.year_to, maximum=(20 if args.quality_mode else args.maximum),
                    embedding_timeout=(30 if mode == "auto" else None),
                )
                mode = "semantic" if mode == "auto" else mode
                semantic_metadata = load_semantic_index(args.semantic_index.resolve())
            except (OSError, SemanticIndexError) as exc:
                if mode != "auto":
                    raise
                print(f"语义检索不可用，已明确回退lexical文字检索：{exc}", file=sys.stderr)
                mode = "lexical"
                results = lexical_search(index_path, rag_root, query=args.query,
                    type_filter=args.type_filter, site=args.site, strategy=args.strategy,
                    minimum_quality=args.quality, keyword=args.keyword,
                    year_from=args.year_from, year_to=args.year_to, maximum=args.maximum)
                baseline_metadata = {"version":"lexical-v1", "index_path":str(index_path),
                    "index_sha256":hashlib.sha256(index_path.read_bytes()).hexdigest(),
                    "cases":len(load_index(index_path))}
            if args.quality_mode and mode != "lexical":
                results, rerank_warning = rerank_with_fallback(
                    args.query, results, model=args.rerank_model, top_n=args.rerank_top
                )
                if rerank_warning:
                    print(rerank_warning, file=sys.stderr)
                results = results[:args.maximum]
    except (OSError, SearchError, SemanticIndexError, RerankError) as exc:
        print(f"检索失败：{exc}", file=sys.stderr)
        return 1
    if args.format == "text":
        print(format_results(results))
    elif args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        card_query = (
            args.query
            or " ".join(args.problem or [])
            or " ".join(args.keyword or [])
            or "(baseline filter)"
        )
        print(json.dumps(rag_transfer_cards(results, query=card_query, mode=mode, semantic_metadata=semantic_metadata, index_metadata=baseline_metadata), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
