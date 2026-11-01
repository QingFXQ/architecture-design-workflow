#!/usr/bin/env python3
"""Architecture Case RAG 脚本的标准库回归测试。"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_module(name: str):
    """从脚本目录加载被测模块。"""
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_index = load_module("build_index")
search_cases = load_module("search_cases")
semantic_index = load_module("semantic_index")
validate_case = load_module("validate_case")
rerank_cases = load_module("rerank_cases")
audit_case_quality = load_module("audit_case_quality")


def case_markdown(
    *,
    case_id: str,
    title: str,
    year: int,
    quality: str,
    problem: str,
    problem_body: str,
    case_type: str = "museum",
) -> str:
    """生成最小但结构真实的临时案例。"""
    return f"""---
id: {case_id}
title: {title}
architect: 测试事务所
year: {year}
location: 测试城市, 中国
area_m2: 1000
floors: 两层
type: [{case_type}]
site: [urban-infill]
strategy: [courtyard]
problem: [{problem}]
quality: {quality}
sources:
  - name: example
    url: https://example.com/{case_id}
    accessed: 2026-08-11
images:
  - {{ kind: plan, url: "https://example.com/{case_id}.jpg" }}
summary: {title}摘要
---

# {title}

## 1. 初始条件
正文关键词：雨水花园。

## 2. 核心设计问题
{problem_body}

## 3. 核心设计意图
测试正文。
"""


class BuildIndexTests(unittest.TestCase):
    def test_build_index_preserves_frontmatter_and_nested_records(self):
        """防止解析器丢失数组、来源对象、空值或相对路径。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cases_dir = root / "cases"
            cases_dir.mkdir()
            case_path = cases_dir / "alpha.md"
            case_path.write_text(
                case_markdown(
                    case_id="alpha",
                    title="甲案例",
                    year=2024,
                    quality="★★★★",
                    problem="privacy",
                    problem_body="如何同时处理隐私与采光。",
                ),
                encoding="utf-8",
            )
            output = root / "index" / "cases.json"

            records = build_index.build_index(cases_dir, output, root)

            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["year"], 2024)
            self.assertEqual(record["type"], ["museum"])
            self.assertEqual(record["sources"][0]["name"], "example")
            self.assertEqual(record["images"][0]["kind"], "plan")
            self.assertEqual(record["path"], "cases/alpha.md")
            self.assertEqual(record["summary"], "甲案例摘要")
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), records)

    def test_build_index_is_deterministic(self):
        """防止重复构建改变顺序或文件内容。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cases_dir = root / "cases"
            cases_dir.mkdir()
            for case_id in ("zeta", "alpha"):
                (cases_dir / f"{case_id}.md").write_text(
                    case_markdown(
                        case_id=case_id,
                        title=case_id,
                        year=2020,
                        quality="★★",
                        problem="access",
                        problem_body="如何组织入口。",
                    ),
                    encoding="utf-8",
                )
            output = root / "index" / "cases.json"

            build_index.build_index(cases_dir, output, root)
            first = output.read_bytes()
            build_index.build_index(cases_dir, output, root)

            self.assertEqual(output.read_bytes(), first)
            self.assertEqual([item["id"] for item in json.loads(first)], ["alpha", "zeta"])


class SearchCasesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        cases_dir = self.root / "cases"
        cases_dir.mkdir()
        fixtures = [
            case_markdown(
                case_id="tag-both",
                title="双标签命中",
                year=2022,
                quality="★★★",
                problem="privacy, daylight",
                problem_body="如何处理隐私和自然采光。",
            ),
            case_markdown(
                case_id="body-only",
                title="正文命中",
                year=2025,
                quality="★★★★★",
                problem="compact-site",
                problem_body="如何处理 privacy 和 daylight 的冲突。",
            ),
            case_markdown(
                case_id="one-missing",
                title="缺一关键词",
                year=2026,
                quality="★★★★★",
                problem="privacy",
                problem_body="只处理 privacy。",
            ),
            case_markdown(
                case_id="tag-one",
                title="一项标签命中",
                year=2024,
                quality="★★★★",
                problem="privacy",
                problem_body="同时回应 privacy 与 daylight。",
                case_type="school",
            ),
        ]
        for content in fixtures:
            case_id = content.split("id: ", 1)[1].splitlines()[0]
            (cases_dir / f"{case_id}.md").write_text(content, encoding="utf-8")
        self.index_path = self.root / "index" / "cases.json"
        build_index.build_index(cases_dir, self.index_path, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_problem_terms_are_and_and_tag_matches_rank_first(self):
        """防止多词退化为 OR，或高星正文命中压过标签命中。"""
        results = search_cases.search(
            self.index_path,
            self.root,
            problem=["privacy", "daylight"],
            maximum=10,
        )

        self.assertEqual(
            [item["id"] for item in results],
            ["tag-both", "tag-one", "body-only"],
        )
        self.assertEqual(results[0]["_matched_problem_tags"], ["privacy", "daylight"])
        self.assertEqual(results[2]["_matched_problem_tags"], [])

    def test_frontmatter_keyword_quality_and_year_filters_compose(self):
        """防止组合过滤时忽略标签精确匹配、正文、星级或年份边界。"""
        results = search_cases.search(
            self.index_path,
            self.root,
            type_filter="school",
            site="urban-infill",
            strategy="courtyard",
            minimum_quality=4,
            keyword=["雨水花园"],
            year_from=2024,
            year_to=2024,
            maximum=10,
        )

        self.assertEqual([item["id"] for item in results], ["tag-one"])

    def test_quality_then_year_sort_without_problem(self):
        """防止无 problem 查询时未按质量、年份降序排列。"""
        results = search_cases.search(self.index_path, self.root, maximum=3)

        self.assertEqual(
            [item["id"] for item in results],
            ["one-missing", "body-only", "tag-one"],
        )

    def test_natural_language_query_uses_section_semantic_index(self):
        """自然语言 query 必须召回案例的相关章节并聚合为案例。"""
        semantic_path = self.root / "index" / "semantic.json"
        semantic_path.write_text(
            json.dumps(
                {
                    "model": "fake-model",
                    "embedding_dimensions": 2,
                    "sections": [
                        {
                            "case_id": "tag-one",
                            "section": "circulation",
                            "text": "短环形流线连接教室与户外。",
                            "embedding": [1.0, 0.0],
                        },
                        {
                            "case_id": "body-only",
                            "section": "core_problem",
                            "text": "无关章节。",
                            "embedding": [0.0, 1.0],
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        original_embed = search_cases.embed_texts
        search_cases.embed_texts = lambda texts, model: [[1.0, 0.0]]
        try:
            results = search_cases.semantic_search(
                self.index_path,
                semantic_path,
                self.root,
                query="如何组织短环形流线到户外",
                mode="hybrid",
                maximum=2,
            )
        finally:
            search_cases.embed_texts = original_embed

        self.assertEqual(results[0]["id"], "tag-one")
        self.assertEqual(results[0]["evidence_sections"], ["circulation"])

    def test_query_and_problem_are_rejected_as_ambiguous_modes(self):
        """语义 query 不得静默忽略用户给出的 baseline problem 过滤。"""
        self.assertEqual(
            search_cases.main(["--query", "室内外关系", "--problem", "indoor-outdoor"]),
            1,
        )

    def test_empty_explicit_query_is_rejected_instead_of_falling_back_to_baseline(self):
        """自动化调用的空 query 不能伪装成一次成功的 baseline 检索。"""
        self.assertEqual(search_cases.main(["--query", ""]), 1)

    def test_rag_transfer_card_includes_index_evidence_and_source(self):
        """Concept→Scheme 交接必须可复现检索版本并追溯到案例来源。"""
        card = search_cases.rag_transfer_cards(
            [{
                "id": "case-a", "title": "案例 A", "path": "cases/a.md", "quality": "★★★★",
                "sources": [{"name": "official", "url": "https://example.com/a", "accessed": "2026-08-12"}],
                "evidence_sections": ["core_problem"], "evidence_texts": ["连续坡道回应高差。"],
            }],
            query="高差如何组织连续路径",
            mode="semantic",
            semantic_metadata={"version": 1, "model": "test-model", "corpus_sha256": "abc"},
        )

        self.assertEqual(card[0]["index"]["corpus_sha256"], "abc")
        self.assertEqual(card[0]["evidence"][0]["text"], "连续坡道回应高差。")
        self.assertEqual(card[0]["sources"][0]["url"], "https://example.com/a")

    def test_rag_transfer_card_marks_scheme_decision_as_unresolved(self):
        """检索卡只提供证据，不能伪装成已完成的方案迁移决定。"""
        card = search_cases.rag_transfer_cards(
            [{"case_id": "case-a", "evidence_sections": ["core_problem"], "evidence_texts": ["证据。"]}],
            query="测试", mode="semantic",
        )
        self.assertEqual(card[0]["scheme_decision"]["status"], "unresolved")
        self.assertIn("same_conditions", card[0]["scheme_decision"]["required_fields"])


class SemanticIndexTests(unittest.TestCase):
    def test_section_parser_excludes_specific_unknown_placeholders(self):
        """“资料未提供儿童流线”等变体不能伪装成可检索的设计证据。"""
        self.assertFalse(semantic_index.is_substantive_section("资料未提供儿童、接送与后勤流线。"))

    def test_section_parser_keeps_meaningful_sections_and_metadata(self):
        """语义索引必须按章节而非整篇案例建立候选。"""
        record = {
            "id": "section-case",
            "title": "章节案例",
            "type": ["kindergarten"],
            "site": ["urban-infill"],
            "problem": ["indoor-outdoor"],
            "strategy": ["terrace"],
            "quality": "★★★★",
            "year": 2024,
        }
        markdown = """# 章节案例

## 1. 初始条件
紧凑基地，需要建立可使用的活动空间。

## 2. 核心设计问题
每班应直接抵达室外活动场地，并以短路径组织日常使用。

## 10. 人流与服务流线
短环形流线避免长走廊，并连接每个班级的室外活动空间。
"""

        sections = semantic_index.extract_sections(record, markdown)

        self.assertEqual([item["section"] for item in sections], ["initial_conditions", "core_problem", "circulation"])
        self.assertEqual(sections[1]["case_id"], "section-case")
        self.assertEqual(sections[1]["problem"], ["indoor-outdoor"])
        self.assertIn("每班", sections[1]["text"])

    def test_hybrid_score_prioritizes_problem_over_type(self):
        """跨类型但问题匹配的候选不能被同类型弱相关案例压过。"""
        cross_type = semantic_index.hybrid_score(
            semantic=0.76,
            problem_match=1.0,
            strategy_match=0.5,
            site_match=0.0,
            type_match=0.0,
            keyword_evidence=0.5,
            quality=4,
        )
        same_type = semantic_index.hybrid_score(
            semantic=0.38,
            problem_match=0.0,
            strategy_match=0.0,
            site_match=0.0,
            type_match=1.0,
            keyword_evidence=0.0,
            quality=4,
        )

        self.assertGreater(cross_type, same_type)

    def test_load_index_rejects_inconsistent_embedding_dimensions(self):
        """损坏或换模型后的索引不得静默产生零相似度。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "semantic.json"
            path.write_text(json.dumps({"embedding_dimensions": 2, "sections": [{"embedding": [1.0]}]}), encoding="utf-8")
            with self.assertRaises(semantic_index.SemanticIndexError):
                semantic_index.load_semantic_index(path)

    def test_corpus_fingerprint_changes_when_case_content_changes(self):
        """索引必须能识别案例正文已变更，避免用旧向量给出伪精确结果。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cases = root / "cases"
            cases.mkdir()
            path = cases / "a.md"
            path.write_text("## 2. 核心设计问题\n以连续坡道组织场地高差与完整参观路径。\n", encoding="utf-8")
            record = {"id": "a", "path": "cases/a.md", "summary": "高差案例"}
            first = semantic_index.corpus_fingerprint([record], root)
            path.write_text("## 2. 核心设计问题\n以庭院组织自然采光与相邻公共空间。\n", encoding="utf-8")
            self.assertNotEqual(first, semantic_index.corpus_fingerprint([record], root))

    def test_aggregate_sections_uses_best_evidence_per_case(self):
        """一个案例的关键章节应决定其案例级分数和证据章节。"""
        results = semantic_index.aggregate_case_sections(
            [
                {"case_id": "a", "section": "core_problem", "score": 0.84},
                {"case_id": "a", "section": "massing", "score": 0.38},
                {"case_id": "b", "section": "circulation", "score": 0.72},
            ]
        )

        self.assertEqual([item["case_id"] for item in results], ["a", "b"])
        self.assertEqual(results[0]["evidence_sections"], ["core_problem", "massing"])


class IngestionValidationTests(unittest.TestCase):
    def test_validator_rejects_missing_canonical_tag_and_sections(self):
        """新入库案例必须有 15 节、来源和 canonical 标签，不能静默放行。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.md"
            path.write_text(
                case_markdown(
                    case_id="invalid", title="无效案例", year=2024, quality="★★★",
                    problem="invented-problem", problem_body="问题。",
                ), encoding="utf-8"
            )
            errors = validate_case.validate_case(path, validate_case.load_ontology())

        self.assertTrue(any("canonical problem" in error for error in errors))
        self.assertTrue(any("15 个章节" in error for error in errors))


class CaseQualityAuditTests(unittest.TestCase):
    def test_four_star_case_without_section_is_flagged(self):
        """四星案例缺少所声称的关键图面时必须进入数据修复队列。"""
        report = audit_case_quality.audit([
            {"id": "weak-four", "quality": "★★★★", "path": "cases/weak.md", "images": [{"kind": "floor-plan"}]},
            {"id": "strong-four", "quality": "★★★★", "path": "cases/strong.md", "images": [{"kind": "floor-plan"}, {"kind": "section"}, {"kind": "photo"}]},
        ])
        self.assertEqual(report["four_star_or_higher"], 2)
        self.assertEqual(report["issues"][0]["missing"], ["section", "photo"])

    def test_five_star_case_requires_site_plan_plan_section_and_photo(self):
        """五星证据门槛必须高于四星，避免把宣传图案例当作完整图纸案例。"""
        report = audit_case_quality.audit([
            {"id": "weak-five", "quality": "★★★★★", "path": "cases/weak.md", "images": [
                {"kind": "site-plan"}, {"kind": "floor-plan"}, {"kind": "section"},
            ]},
        ])
        self.assertEqual(report["issues"][0]["missing"], ["photo"])


class RerankTests(unittest.TestCase):
    def test_batch_reranker_judges_multiple_candidates_in_one_request(self):
        """一条 query 的 quality rerank 不能退化成每个候选一次本地模型调用。"""
        original_urlopen = rerank_cases.urlopen
        calls = []

        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self):
                return ('{"response":"[{\\\"case_id\\\":\\\"a\\\",\\\"relevance\\\":91},'
                        '{\\\"case_id\\\":\\\"b\\\",\\\"relevance\\\":40}]"}').encode("utf-8")

        rerank_cases.urlopen = lambda request, **_kwargs: (calls.append(request) or Response())
        try:
            results = rerank_cases.rerank(
                "连续参观路径",
                [
                    {"case_id": "a", "title": "甲", "score": 0.6, "evidence_sections": ["circulation"], "evidence_texts": ["连续坡道。"]},
                    {"case_id": "b", "title": "乙", "score": 0.8, "evidence_sections": ["summary"], "evidence_texts": ["普通大厅。"]},
                ],
                top_n=2,
            )
        finally:
            rerank_cases.urlopen = original_urlopen

        self.assertEqual(len(calls), 1)
        payload = json.loads(calls[0].data.decode("utf-8"))
        self.assertEqual(payload["format"], rerank_cases.RERANK_SCHEMA)
        self.assertEqual(results[0]["case_id"], "a")
        self.assertEqual(results[0]["relevance"], 91)

    def test_batch_reranker_accepts_model_cases_wrapper(self):
        """本地 qwen 有时把数组包装成 cases 对象，不能因此丢弃所有 quality 结果。"""
        parsed = rerank_cases._parse_judgements(
            '{"cases":[{"case_id":"a","relevance":88}]}',
            [{"case_id": "a"}],
        )
        self.assertEqual(parsed["a"]["relevance"], 88)

    def test_batch_reranker_accepts_qwen_case_keyed_wrapper(self):
        """真实 qwen3.5 有时以 case_id 为 JSON key 包裹其单项判断。"""
        parsed = rerank_cases._parse_judgements(
            '{"a":[{"relevance":88}]}',
            [{"case_id": "a"}],
        )
        self.assertEqual(parsed["a"]["relevance"], 88)

    def test_batch_reranker_rejects_partial_judgement(self):
        """一次性 rerank 若遗漏候选，必须整体回退 fast，不能混用半份排序。"""
        with self.assertRaises(ValueError):
            rerank_cases._parse_judgements(
                '{"case_id":"a","relevance":76}',
                [{"case_id": "a"}, {"case_id": "b"}],
            )

    def test_quality_rerank_falls_back_to_fast_results(self):
        """本地 LLM 离线时 quality mode 仍必须返回确定性的快速检索结果。"""
        original_rerank = search_cases.rerank
        search_cases.rerank = lambda *_args, **_kwargs: (_ for _ in ()).throw(search_cases.RerankError("offline"))
        candidates = [{"case_id": "a", "score": 0.8}]
        try:
            results, warning = search_cases.rerank_with_fallback("测试", candidates)
        finally:
            search_cases.rerank = original_rerank
        self.assertEqual(results, candidates)
        self.assertIn("offline", warning)

    def test_reranker_consumes_top_evidence_sections_for_each_case(self):
        """quality mode 必须让模型基于一个案例的多段证据，而非任意首段。"""
        prompt = rerank_cases._prompt(
            "如何组织参观路径",
            {
                "title": "测试馆", "case_id": "test", "evidence_sections": ["core_problem", "circulation"],
                "evidence_texts": ["处理高差。", "连续坡道组织参观。"],
            },
        )
        self.assertIn("core_problem", prompt)
        self.assertIn("连续坡道", prompt)

    def test_reranker_keeps_unreviewed_fast_candidates(self):
        """quality mode 只复核前 N 个，但不能截断用户要求的结果数。"""
        original_urlopen = rerank_cases.urlopen

        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self): return b'{"response":"[{\\\"case_id\\\":\\\"a\\\",\\\"relevance\\\":80}]"}'

        rerank_cases.urlopen = lambda *_args, **_kwargs: Response()
        try:
            results = rerank_cases.rerank(
                "测试", [{"case_id": "a", "score": 0.8}, {"case_id": "b", "score": 0.7}], top_n=1
            )
        finally:
            rerank_cases.urlopen = original_urlopen
        self.assertEqual(len(results), 2)
        self.assertIsNone(results[1]["relevance"])


if __name__ == "__main__":
    unittest.main()
