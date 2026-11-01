#!/usr/bin/env python3
"""Ingest a reviewed local Markdown case into both retrieval indexes."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


RAG_ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="入库一个已结构化、已核实的 Architecture Case Markdown")
    parser.add_argument("case", type=Path, help="已按模板整理的 Markdown")
    parser.add_argument("--skip-semantic", action="store_true", help="只重建 metadata index")
    args = parser.parse_args(argv)
    validation = [sys.executable, str(RAG_ROOT / "scripts" / "validate_case.py"), str(args.case)]
    if subprocess.run(validation, check=False).returncode:
        return 1
    destination = RAG_ROOT / "cases" / args.case.name
    if args.case.resolve() != destination.resolve():
        if destination.exists():
            print(f"拒绝覆盖已有案例：{destination}", file=sys.stderr)
            return 1
        shutil.copy2(args.case, destination)
    commands = [[sys.executable, str(RAG_ROOT / "scripts" / "build_index.py")]]
    if not args.skip_semantic:
        commands.append([sys.executable, str(RAG_ROOT / "scripts" / "build_semantic_index.py")])
    for command in commands:
        if subprocess.run(command, check=False).returncode:
            return 1
    print(f"已入库：{destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
