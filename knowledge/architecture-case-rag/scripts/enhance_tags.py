#!/usr/bin/env python3
"""Canonicalize existing case metadata through the conservative tag alias map.

The script never infers new architectural facts. It only expands already present
legacy labels to their reviewed canonical equivalents, leaving source labels in
place so existing links and manual review remain transparent.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from build_index import DEFAULT_CASES_DIR, RAG_ROOT, parse_frontmatter


DEFAULT_ALIASES = RAG_ROOT / "ontology" / "aliases.json"


def canonical_tags(tags: Sequence[Any], aliases: Mapping[str, Sequence[str]]) -> List[str]:
    """Keep source tags and append de-duplicated canonical targets."""
    expanded: List[str] = []
    for tag in tags:
        value = str(tag)
        for candidate in [value, *aliases.get(value, [])]:
            if candidate not in expanded:
                expanded.append(candidate)
    return expanded


def enhancement_preview(case_path: Path, aliases: Mapping[str, Mapping[str, Sequence[str]]]) -> Dict[str, Any]:
    """Return proposed metadata changes without altering case Markdown."""
    frontmatter, _ = parse_frontmatter(case_path.read_text(encoding="utf-8"), str(case_path))
    proposal: Dict[str, Any] = {"path": str(case_path), "id": frontmatter.get("id"), "changes": {}}
    for field in ("problem", "strategy", "site"):
        original = list(frontmatter.get(field) or [])
        expanded = canonical_tags(original, aliases.get(field, {}))
        if expanded != original:
            proposal["changes"][field] = {"from": original, "to": expanded}
    return proposal


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="预览现有案例的 canonical tag 补全")
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_CASES_DIR)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    aliases = json.loads(args.aliases.read_text(encoding="utf-8"))
    proposals = [enhancement_preview(path, aliases) for path in sorted(args.cases_dir.glob("*.md"))]
    changed = [item for item in proposals if item["changes"]]
    print(json.dumps({"total": len(proposals), "changed": len(changed), "proposals": changed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
