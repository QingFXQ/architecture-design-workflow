#!/usr/bin/env python3
"""Normalize a manually prepared case file by validating its structured fields."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


RAG_ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="验证人工整理后的 Architecture Case")
    parser.add_argument("case", type=Path)
    args = parser.parse_args(argv)
    command = [sys.executable, str(RAG_ROOT / "scripts" / "validate_case.py"), str(args.case)]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
