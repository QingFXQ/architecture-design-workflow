#!/usr/bin/env python3
"""Run repeatable A/B retrieval benchmarks against reviewed architecture queries."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from statistics import mean
import sys
from typing import Any, Dict, List, Sequence


BENCHMARK_ROOT = Path(__file__).resolve().parent
RAG_ROOT = BENCHMARK_ROOT.parent
SCRIPTS = RAG_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


search_cases = load_script("search_cases")
rerank_cases = load_script("rerank_cases")


def relevance_rank(ids: Sequence[str], query: Dict[str, Any]) -> int | None:
    relevant = set(query["must_hit"]) | set(query["strong_relevance"]) | set(query["acceptable"])
    return next((position for position, case_id in enumerate(ids, 1) if case_id in relevant), None)


def run_mode(query: Dict[str, Any], mode: str, *, rerank: bool = False, rerank_top: int = 1) -> List[str]:
    if mode == "baseline":
        # Baseline deliberately has no semantic text: this measures current tag/keyword behavior.
        terms = [word for word in query["query"].replace("，", " ").replace("。", " ").split() if word]
        result = search_cases.search(
            RAG_ROOT / "index" / "cases.json", RAG_ROOT, keyword=terms[:2], maximum=10
        )
    else:
        result = search_cases.semantic_search(
            RAG_ROOT / "index" / "cases.json", RAG_ROOT / "index" / "semantic-sections.json", RAG_ROOT,
            query=query["query"], mode=mode, maximum=20 if rerank else 10
        )
        if rerank:
            result = rerank_cases.rerank(query["query"], result, top_n=rerank_top)[:10]
    return [str(item.get("id", item.get("case_id"))) for item in result]


def calculate_metrics(rows: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    count = len(rows)
    recall = lambda limit: mean(any(case_id in row["must_hit"] for case_id in row["results"][:limit]) for row in rows)
    rr = []
    for row in rows:
        rank = relevance_rank(row["results"], row)
        rr.append(1 / rank if rank else 0)
    must_coverage = mean(any(case_id in row["must_hit"] for case_id in row["results"][:10]) for row in rows)
    negative_annotated = [row for row in rows if row["negative"]]
    false_positive = mean(
        sum(case_id in set(row["negative"]) for case_id in row["results"][:5]) / 5
        for row in negative_annotated
    ) if negative_annotated else 0.0
    return {
        "queries": count,
        "Recall@3": round(recall(3), 3),
        "Recall@5": round(recall(5), 3),
        "Recall@10": round(recall(10), 3),
        "MRR": round(mean(rr), 3),
        "must_hit_coverage": round(must_coverage, 3),
        "false_positive_rate": round(false_positive, 3),
        "negative_annotation_coverage": round(len(negative_annotated) / count, 3),
    }


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Architecture Case RAG retrieval benchmark")
    parser.add_argument("--mode", choices=("baseline", "semantic", "hybrid", "rerank"), default="hybrid")
    parser.add_argument("--rerank-top", type=int, default=1, help="rerank 模式每题实际 LLM 复核案例数（默认 1）")
    parser.add_argument("--output", type=Path, help="结果 JSON 输出路径")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    queries = json.loads((BENCHMARK_ROOT / "queries.json").read_text(encoding="utf-8"))
    rows: List[Dict[str, Any]] = []
    for query in queries:
        ids = run_mode(query, "hybrid" if args.mode == "rerank" else args.mode, rerank=args.mode == "rerank", rerank_top=args.rerank_top)
        rows.append({**query, "results": ids})
    report = {
        "mode": args.mode,
        "settings": {"rerank_top": args.rerank_top} if args.mode == "rerank" else {},
        "metrics": calculate_metrics(rows),
        "rows": rows,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["metrics"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
