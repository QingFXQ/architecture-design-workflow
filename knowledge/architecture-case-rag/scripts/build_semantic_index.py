#!/usr/bin/env python3
"""Build the local section-level embedding index for Architecture Case RAG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from build_index import DEFAULT_OUTPUT, RAG_ROOT, FrontmatterError
from semantic_index import DEFAULT_MODEL, SemanticIndexError, build_semantic_records, write_semantic_index


DEFAULT_SEMANTIC_INDEX = RAG_ROOT / "index" / "semantic-sections.json"


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建 Architecture Case RAG section-level semantic index")
    parser.add_argument("--index", type=Path, default=DEFAULT_OUTPUT, help="cases.json 路径")
    parser.add_argument("--output", type=Path, default=DEFAULT_SEMANTIC_INDEX, help="语义索引输出路径")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="本地 Ollama embedding 模型")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    index_path = args.index.resolve()
    rag_root = RAG_ROOT if index_path == DEFAULT_OUTPUT.resolve() else index_path.parent.parent
    try:
        records = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise SemanticIndexError("cases.json 根节点必须是对象数组")
        sections = build_semantic_records(records, rag_root, model=args.model)
        write_semantic_index(sections, args.output.resolve(), model=args.model)
    except (OSError, FrontmatterError, SemanticIndexError) as exc:
        print(f"构建失败：{exc}", file=sys.stderr)
        return 1
    print(f"已生成 {args.output.resolve()}，共 {len(sections)} 个 section embeddings，来自 {len(records)} 个案例。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
