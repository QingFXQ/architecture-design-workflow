#!/usr/bin/env python3
"""Report evidence gaps that conflict with the Case RAG quality-star definitions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from build_index import RAG_ROOT


DEFAULT_INDEX = RAG_ROOT / "index" / "cases.json"


def audit(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Flag ratings whose registered image evidence falls below the published threshold."""
    issues = []
    for record in records:
        if str(record.get("quality", "")).count("★") < 4:
            continue
        kinds = {str(image.get("kind", "")) for image in record.get("images", []) if isinstance(image, dict)}
        site_plan = any("site-plan" in kind or "site_plan" in kind for kind in kinds)
        plan = any("plan" in kind for kind in kinds)
        section = any("section" in kind for kind in kinds)
        photo = any("photo" in kind for kind in kinds)
        stars = str(record.get("quality", "")).count("★")
        # A four-star case is allowed to support spatial transfer only if the
        # registered source evidence includes a plan, a section and a photo.
        # This is a warning queue, never an automatic star downgrade.
        required = {"plan": plan, "section": section, "photo": photo}
        if stars >= 5:
            required = {"site-plan": site_plan, **required, "photo": photo}
        if not all(required.values()):
            issues.append({
                "id": record.get("id"), "quality": record.get("quality"), "path": record.get("path"),
                "missing": [name for name, present in required.items() if not present],
                "image_kinds": sorted(kinds),
            })
    return {"four_star_or_higher": sum(str(item.get("quality", "")).count("★") >= 4 for item in records), "issues": issues}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="审计 Architecture Case 质量星级与图面 metadata")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = audit(json.loads(args.index.read_text(encoding="utf-8")))
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
