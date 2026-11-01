#!/usr/bin/env python3
"""Optional local LLM reranking for architecture-case candidates.

One request evaluates the complete candidate set for a query.  This preserves
the evidence-first quality mode while avoiding one expensive model invocation
per case.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_RERANK_MODEL = "qwen3.5:4b-q4_K_M"
DEFAULT_RERANK_TOP = 5
DEFAULT_GENERATE_URL = "http://127.0.0.1:11434/api/generate"


class RerankError(RuntimeError):
    """The local optional reranker could not provide structured output."""


RERANK_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "relevance": {"type": "integer", "minimum": 0, "maximum": 100},
                    "matched_problem": {"type": "string"},
                    "transferable_method": {"type": "string"},
                    "limitations": {"type": "string"},
                },
                "required": ["case_id", "relevance", "matched_problem", "transferable_method", "limitations"],
            },
        },
    },
    "required": ["results"],
}


def _candidate_evidence(candidate: Dict[str, Any]) -> str:
    sections = candidate.get("evidence_sections") or [candidate.get("section", "summary")]
    texts = candidate.get("evidence_texts") or [candidate.get("section_text", "")]
    evidence = "\n\n".join(
        f"[{section}]\n{text}" for section, text in zip(sections, texts)
    )[:2600]
    return (
        f"case_id: {candidate.get('case_id', candidate.get('id'))}\n"
        f"title: {candidate.get('title', '')}\n"
        f"evidence:\n{evidence}"
    )


def _prompt(query: str, candidate: Dict[str, Any]) -> str:
    """Keep the former single-candidate prompt for inspection and compatibility."""
    return f"""你是建筑设计案例检索复核器。只判断案例是否真正解决设计问题，不能补充案例未提供的事实。
设计问题：{query}
候选案例：{candidate.get('title')}（{candidate.get('case_id', candidate.get('id'))}）
候选证据：\n{_candidate_evidence(candidate)}
只输出 JSON：{{\"relevance\":0-100整数,\"matched_problem\":\"简短中文\",\"transferable_method\":\"简短中文\",\"limitations\":\"简短中文\"}}。"""


def _batch_prompt(query: str, candidates: Sequence[Dict[str, Any]]) -> str:
    evidence = "\n\n---\n\n".join(_candidate_evidence(candidate) for candidate in candidates)
    return f"""你是建筑设计案例检索复核器。只依据每个候选给出的证据，判断它是否真正回答设计问题；不得补充未提供的事实。
设计问题：{query}

候选：
{evidence}

只输出 JSON 对象，`results` 数组中每项必须对应一个输入 case_id：
{{\"results\":[{{\"case_id\":\"...\",\"relevance\":0-100整数,\"matched_problem\":\"简短中文\",\"transferable_method\":\"简短中文\",\"limitations\":\"简短中文\"}}]}}
不要输出 Markdown 或额外解释。"""


def _parse_judgements(response_text: str, candidates: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    parsed = json.loads(response_text)
    if isinstance(parsed, dict):
        if "case_id" in parsed:
            parsed = [parsed]
        else:
            parsed = parsed.get("results", parsed.get("cases", _unwrap_case_keyed_results(parsed)))
    if not isinstance(parsed, list):
        raise ValueError("rerank 输出不是 JSON 数组")
    candidate_ids = {str(item.get("case_id", item.get("id"))) for item in candidates}
    judgements: Dict[str, Dict[str, Any]] = {}
    for item in parsed:
        if not isinstance(item, dict):
            continue
        case_id = str(item.get("case_id", ""))
        if case_id not in candidate_ids or case_id in judgements:
            continue
        relevance = max(0, min(100, int(item["relevance"])))
        judgements[case_id] = {
            "relevance": relevance,
            "matched_problem": str(item.get("matched_problem", "")),
            "transferable_method": str(item.get("transferable_method", "")),
            "limitations": str(item.get("limitations", "")),
        }
    if set(judgements) != candidate_ids:
        missing = sorted(candidate_ids - set(judgements))
        raise ValueError(f"rerank 输出遗漏候选 case_id：{missing}")
    if not judgements:
        returned = [str(item.get("case_id", "")) for item in parsed if isinstance(item, dict)]
        raise ValueError(f"rerank 输出没有匹配的 case_id（返回：{returned}；期待：{sorted(candidate_ids)}）")
    return judgements


def _unwrap_case_keyed_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Accept qwen's occasional ``{case_id: [{judgement}]}`` JSON envelope.

    It is still subject to the complete-candidate check below, so a model that
    answers for only one candidate cannot silently influence a multi-case run.
    """
    items: List[Dict[str, Any]] = []
    for case_id, value in payload.items():
        values = value if isinstance(value, list) else [value]
        for item in values:
            if not isinstance(item, dict):
                continue
            copy = dict(item)
            copy.setdefault("case_id", str(case_id))
            items.append(copy)
    return items


def rerank(
    query: str,
    candidates: Sequence[Dict[str, Any]],
    *,
    model: str = DEFAULT_RERANK_MODEL,
    top_n: int = DEFAULT_RERANK_TOP,
    url: str = DEFAULT_GENERATE_URL,
) -> List[Dict[str, Any]]:
    """Rerank top candidates in one evidence-limited local LLM request."""
    reviewed = list(candidates[:top_n])
    if not reviewed:
        return []
    request = Request(
        url,
        data=json.dumps({
            "model": model,
            "prompt": _batch_prompt(query, reviewed),
            "stream": False,
            "format": RERANK_SCHEMA,
            "options": {"temperature": 0, "think": False},
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
        response_text = payload.get("response") or ""
        try:
            judgements = _parse_judgements(response_text, reviewed)
        except (ValueError, json.JSONDecodeError):
            # qwen3.5 may place its structured answer in ``thinking`` while
            # leaving ``response`` empty or incomplete; retain the same
            # evidence-only parser rather than accepting prose.
            judgements = _parse_judgements(str(payload.get("thinking") or ""), reviewed)
    except (URLError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RerankError(f"本地 LLM rerank 失败：{exc}") from exc

    reranked = []
    for candidate in reviewed:
        case_id = str(candidate.get("case_id", candidate.get("id")))
        judgement = judgements.get(case_id)
        reranked.append({**candidate, **judgement} if judgement else {**candidate, "relevance": None})
    untouched = [{**candidate, "relevance": None} for candidate in candidates[top_n:]]
    return sorted(
        reranked + untouched,
        key=lambda item: (
            -(0.7 * (int(item["relevance"]) / 100) + 0.3 * float(item.get("score", 0)))
            if item.get("relevance") is not None else -float(item.get("score", 0)),
            -float(item.get("score", 0)),
        ),
    )
