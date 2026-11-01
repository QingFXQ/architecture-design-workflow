#!/usr/bin/env python3
"""Validate a structured Architecture Case before it enters the local index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Mapping, Sequence

from build_index import RAG_ROOT, parse_frontmatter
from semantic_index import SECTION_HEADINGS


DEFAULT_ONTOLOGY = RAG_ROOT / "ontology" / "tags.json"
REQUIRED_FIELDS = ("id", "title", "type", "site", "strategy", "problem", "quality", "sources", "summary")
HEADING_PATTERN = re.compile(r"^##\s+(\d+)\s*[.、]", re.MULTILINE)


def load_ontology(path: Path = DEFAULT_ONTOLOGY) -> Dict[str, List[str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_case(path: Path, ontology: Mapping[str, Sequence[str]]) -> List[str]:
    """Return human-readable errors; unknown facts are permitted only as blank fields."""
    frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"), str(path))
    errors: List[str] = []
    for field in REQUIRED_FIELDS:
        if not frontmatter.get(field):
            errors.append(f"missing required frontmatter: {field}")
    for field in ("type", "site", "strategy", "problem"):
        values = list(frontmatter.get(field) or [])
        allowed = set(ontology.get(field, []))
        aliases = set()
        aliases_path = RAG_ROOT / "ontology" / "aliases.json"
        if aliases_path.exists():
            aliases = set(json.loads(aliases_path.read_text(encoding="utf-8")).get(field, {}))
        unknown = [str(value) for value in values if str(value) not in allowed | aliases]
        if unknown:
            errors.append(f"non-canonical {field}: {', '.join(unknown)}")
    sources = list(frontmatter.get("sources") or [])
    for source in sources:
        if not isinstance(source, dict) or not source.get("name") or not source.get("url") or not source.get("accessed"):
            errors.append("sources entries require name, url, accessed")
            break
    for image in list(frontmatter.get("images") or []):
        if not isinstance(image, dict) or not image.get("kind") or not image.get("url"):
            errors.append("images entries require kind and url")
            break
    sections = set(int(match) for match in HEADING_PATTERN.findall(body))
    expected = set(SECTION_HEADINGS)
    if sections != expected:
        errors.append("正文必须包含完整 15 个章节（1—15）")
    return errors


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 Architecture Case 入库格式")
    parser.add_argument("case", type=Path)
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    errors = validate_case(args.case, load_ontology(args.ontology))
    if errors:
        print("验证失败：", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"验证通过：{args.case}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
