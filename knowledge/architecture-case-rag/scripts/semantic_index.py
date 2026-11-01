#!/usr/bin/env python3
"""Section-level semantic index utilities for Architecture Case RAG.

The implementation deliberately keeps storage local: JSON sections plus vectors
generated through a locally running Ollama embedding model.  It does not require
a vector database or a cloud service.
"""

from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, ProxyHandler, build_opener, urlopen


SECTION_HEADINGS = {
    1: "initial_conditions",
    2: "core_problem",
    3: "design_intent",
    4: "concept_to_massing",
    5: "massing_to_site",
    6: "site_to_program",
    7: "program_to_plan",
    8: "plan_to_section",
    9: "section_to_form",
    10: "circulation",
    11: "scale_module",
    12: "indoor_outdoor",
    13: "best_methods",
    14: "transferable_methods",
    15: "do_not_copy",
}

HEADING_PATTERN = re.compile(r"^##\s+(\d+)\s*[.、]\s*(.+?)\s*$")
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
DEFAULT_MODEL = "qwen3-embedding:0.6b"


class SemanticIndexError(RuntimeError):
    """A local embedding index cannot be built or queried."""


def normalize_text(value: str) -> str:
    """Normalize text for transparent lexical evidence matching."""
    return re.sub(r"\s+", " ", value.casefold()).strip()


def is_substantive_section(text: str) -> bool:
    """Keep unknown placeholders out of vector evidence while retaining them in Markdown."""
    normalized = normalize_text(text)
    if len(normalized) < 12:
        return False
    placeholder = normalized.rstrip("。；;，,：:")
    return not (
        placeholder in {"资料未提供", "具体资料未提供"}
        or placeholder.startswith("资料未提供")
        or placeholder.startswith("具体资料未提供")
    )


def extract_sections(record: Mapping[str, Any], markdown: str) -> List[Dict[str, Any]]:
    """Split one case into semantically meaningful, metadata-bearing sections."""
    common = {
        "case_id": str(record.get("id", "")),
        "title": str(record.get("title", "")),
        "type": list(record.get("type") or []),
        "site": list(record.get("site") or []),
        "problem": list(record.get("problem") or []),
        "strategy": list(record.get("strategy") or []),
        "quality": record.get("quality", ""),
        "year": record.get("year"),
        "path": record.get("path", ""),
    }
    sections: List[Dict[str, Any]] = []
    summary = str(record.get("summary") or "").strip()
    if summary:
        sections.append({**common, "section": "summary", "text": summary})

    active_name: str | None = None
    active_lines: List[str] = []
    for line in markdown.splitlines():
        match = HEADING_PATTERN.match(line.strip())
        if match:
            if active_name and (text := "\n".join(active_lines).strip()) and is_substantive_section(text):
                sections.append({**common, "section": active_name, "text": text})
            active_name = SECTION_HEADINGS.get(int(match.group(1)))
            active_lines = []
        elif active_name:
            active_lines.append(line)
    if active_name and (text := "\n".join(active_lines).strip()) and is_substantive_section(text):
        sections.append({**common, "section": active_name, "text": text})
    return sections


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Calculate cosine similarity without a numerical dependency."""
    if len(left) != len(right) or not left:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _open_url(request: Request, *, timeout: int):
    """Bypass HTTP(S)_PROXY for loopback Ollama endpoints.

    A machine-wide HTTP_PROXY can otherwise intercept 127.0.0.1:11434 and turn a
    local embedding call into a 502.  Non-loopback URLs keep the normal proxy
    behaviour.
    """
    host = (urlparse(request.full_url).hostname or "").lower()
    if host in {"127.0.0.1", "localhost", "::1"}:
        return build_opener(ProxyHandler({})).open(request, timeout=timeout)
    return urlopen(request, timeout=timeout)


def embed_texts(
    texts: Sequence[str],
    *,
    model: str = DEFAULT_MODEL,
    url: str = DEFAULT_OLLAMA_URL,
    timeout: int = 120,
) -> List[List[float]]:
    """Embed a batch through Ollama's local API and validate its response."""
    if not texts:
        return []
    request = Request(
        url,
        data=json.dumps({"model": model, "input": list(texts)}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _open_url(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError) as exc:
        raise SemanticIndexError(
            f"无法调用本地 Ollama embedding API（{url}）：{exc}"
        ) from exc
    embeddings = payload.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise SemanticIndexError("Ollama embedding API 返回的向量数量不正确")
    if not all(isinstance(vector, list) and vector for vector in embeddings):
        raise SemanticIndexError("Ollama embedding API 返回了无效向量")
    return [[float(value) for value in vector] for vector in embeddings]


def build_semantic_records(
    records: Iterable[Mapping[str, Any]],
    rag_root: Path,
    *,
    embedder=embed_texts,
    model: str = DEFAULT_MODEL,
    batch_size: int = 32,
) -> List[Dict[str, Any]]:
    """Parse every case section and add one local embedding per section."""
    sections: List[Dict[str, Any]] = []
    for record in records:
        path = rag_root / str(record["path"])
        sections.extend(extract_sections(record, path.read_text(encoding="utf-8")))
    for start in range(0, len(sections), batch_size):
        batch = sections[start : start + batch_size]
        vectors = embedder(
            [
                f"建筑案例：{item['title']}\n章节：{item['section']}\n{item['text']}"
                for item in batch
            ],
            model=model,
        )
        for item, vector in zip(batch, vectors):
            item["embedding"] = vector
    return sections


def corpus_fingerprint(records: Iterable[Mapping[str, Any]], rag_root: Path) -> str:
    """Fingerprint the exact section corpus represented by an embedding index.

    This intentionally fingerprints only retrieval inputs, not generated vectors,
    so a Markdown or summary edit is detected before an obsolete index is used.
    """
    corpus: List[Dict[str, Any]] = []
    for record in records:
        path = rag_root / str(record.get("path", ""))
        markdown = path.read_text(encoding="utf-8")
        for section in extract_sections(record, markdown):
            corpus.append(
                {key: section.get(key) for key in ("case_id", "section", "text", "path")}
            )
    return hashlib.sha256(
        json.dumps(corpus, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def write_semantic_index(
    sections: Sequence[Mapping[str, Any]], output: Path, *, model: str = DEFAULT_MODEL
) -> None:
    """Write deterministic local section index payload."""
    corpus = [
        {key: item.get(key) for key in ("case_id", "section", "text", "path")}
        for item in sections
    ]
    dimensions = len(sections[0].get("embedding", [])) if sections else 0
    payload = {
        "version": 1,
        "model": model,
        "embedding_dimensions": dimensions,
        "corpus_sha256": hashlib.sha256(
            json.dumps(corpus, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "sections": list(sections),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def load_semantic_index(path: Path) -> Dict[str, Any]:
    """Load and minimally validate a generated semantic section index."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticIndexError(f"无法读取语义索引 {path}：{exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("sections"), list):
        raise SemanticIndexError("语义索引缺少 sections 数组")
    dimensions = payload.get("embedding_dimensions")
    if not isinstance(dimensions, int) or dimensions < 1:
        raise SemanticIndexError("语义索引缺少有效 embedding_dimensions")
    if any(len(item.get("embedding", [])) != dimensions for item in payload["sections"]):
        raise SemanticIndexError("语义索引包含维度不一致的 embedding")
    return payload


def hybrid_score(
    *,
    semantic: float,
    problem_match: float,
    strategy_match: float,
    site_match: float,
    type_match: float,
    keyword_evidence: float,
    quality: int,
) -> float:
    """Architecture-specific score where problem similarity outweighs type."""
    quality_score = max(0, min(quality, 5)) / 5
    return (
        0.70 * max(0.0, semantic)
        + 0.12 * problem_match
        + 0.05 * strategy_match
        + 0.03 * site_match
        + 0.03 * type_match
        + 0.03 * keyword_evidence
        + 0.04 * quality_score
    )


def aggregate_case_sections(section_results: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate section hits while preserving ranked evidence section names."""
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for result in section_results:
        grouped.setdefault(str(result["case_id"]), []).append(result)
    cases: List[Dict[str, Any]] = []
    for case_id, hits in grouped.items():
        priority = {
            "core_problem": 0.06, "transferable_methods": 0.04, "best_methods": 0.03,
            "circulation": 0.02, "indoor_outdoor": 0.02, "do_not_copy": -0.05,
        }
        ordered = sorted(
            hits,
            key=lambda item: (float(item["score"]) + priority.get(str(item["section"]), 0.0), float(item["score"])),
            reverse=True,
        )
        # The best section is decisive; the second prevents a one-line accidental hit.
        score = float(ordered[0]["score"]) + (0.08 * float(ordered[1]["score"]) if len(ordered) > 1 else 0.0)
        cases.append(
            {
                **dict(ordered[0]),
                "case_id": case_id,
                "score": score,
                "evidence_sections": [str(item["section"]) for item in ordered[:3]],
                "evidence_texts": [str(item.get("section_text", item.get("text", ""))) for item in ordered[:3]],
            }
        )
    return sorted(cases, key=lambda item: (-float(item["score"]), str(item["case_id"])))
