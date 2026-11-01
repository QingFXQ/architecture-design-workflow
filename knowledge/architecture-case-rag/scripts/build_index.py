#!/usr/bin/env python3
"""扫描 Architecture Case Markdown，生成可检索的 JSON 索引。

仅使用 Python 标准库。解析器支持本项目 frontmatter 实际使用的 YAML 子集：
标量、行内数组、块列表、块列表中的对象，以及行内对象。
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Sequence, Tuple


RAG_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_DIR = RAG_ROOT / "cases"
DEFAULT_OUTPUT = RAG_ROOT / "index" / "cases.json"


class FrontmatterError(ValueError):
    """frontmatter 缺失或格式超出轻量解析器支持范围。"""


def _strip_inline_comment(value: str) -> str:
    """移除引号外、且前方为空白的 YAML 行尾注释。"""
    quote = ""
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote:
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in ("'", '"'):
            quote = char
        elif char == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.strip()


def _split_top_level(value: str, delimiter: str = ",") -> List[str]:
    """按顶层分隔符切分，忽略引号及方括号/花括号内部的分隔符。"""
    parts: List[str] = []
    start = 0
    quote = ""
    escaped = False
    depth = 0
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote:
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in ("'", '"'):
            quote = char
        elif char in "[{(":
            depth += 1
        elif char in "]})":
            depth -= 1
        elif char == delimiter and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    parts.append(value[start:].strip())
    return [part for part in parts if part]


def _split_key_value(value: str) -> Tuple[str, str]:
    """切分对象中的首个顶层冒号。"""
    quote = ""
    escaped = False
    depth = 0
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote:
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in ("'", '"'):
            quote = char
        elif char in "[{(":
            depth += 1
        elif char in "]})":
            depth -= 1
        elif char == ":" and depth == 0:
            return value[:index].strip(), value[index + 1 :].strip()
    raise FrontmatterError(f"无法解析键值：{value}")


def parse_scalar(raw_value: str) -> Any:
    """解析项目 frontmatter 中使用的 YAML 标量与行内容器。"""
    value = _strip_inline_comment(raw_value)
    if value == "" or value in ("null", "Null", "NULL", "~"):
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [] if not inner else [parse_scalar(item) for item in _split_top_level(inner)]
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        result: Dict[str, Any] = {}
        if inner:
            for pair in _split_top_level(inner):
                key, item_value = _split_key_value(pair)
                result[key] = parse_scalar(item_value)
        return result
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise FrontmatterError(f"无效的引号字符串：{value}") from exc
    lowered = value.casefold()
    if lowered in ("true", "false"):
        return lowered == "true"
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)", value):
        return float(value)
    return value


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_sequence(lines: Sequence[str], start: int) -> Tuple[List[Any], int]:
    """解析缩进两格的 YAML 块列表。"""
    items: List[Any] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        indent = _leading_spaces(line)
        if indent < 2 or not line.lstrip().startswith("- "):
            break
        content = line.lstrip()[2:].strip()
        if content.startswith("{"):
            items.append(parse_scalar(content))
            index += 1
            continue
        if ":" not in content:
            items.append(parse_scalar(content))
            index += 1
            continue

        key, raw_value = _split_key_value(content)
        record: Dict[str, Any] = {key: parse_scalar(raw_value)}
        index += 1
        while index < len(lines):
            continuation = lines[index]
            if not continuation.strip():
                index += 1
                continue
            continuation_indent = _leading_spaces(continuation)
            if continuation_indent <= indent:
                break
            continuation_key, continuation_value = _split_key_value(continuation.strip())
            record[continuation_key] = parse_scalar(continuation_value)
            index += 1
        items.append(record)
    return items, index


def parse_frontmatter(text: str, source: str = "<文本>") -> Tuple[Dict[str, Any], str]:
    """返回 frontmatter 字典与 Markdown 正文。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError(f"{source}：文件必须以 --- 开始")
    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise FrontmatterError(f"{source}：缺少 frontmatter 结束标记 ---") from exc

    frontmatter_lines = lines[1:closing]
    data: Dict[str, Any] = {}
    index = 0
    while index < len(frontmatter_lines):
        line = frontmatter_lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if _leading_spaces(line) != 0:
            raise FrontmatterError(f"{source}：意外缩进（第 {index + 2} 行）")
        key, raw_value = _split_key_value(line)
        if raw_value:
            data[key] = parse_scalar(raw_value)
            index += 1
            continue

        next_index = index + 1
        while next_index < len(frontmatter_lines) and not frontmatter_lines[next_index].strip():
            next_index += 1
        if (
            next_index < len(frontmatter_lines)
            and _leading_spaces(frontmatter_lines[next_index]) >= 2
            and frontmatter_lines[next_index].lstrip().startswith("- ")
        ):
            data[key], index = _parse_sequence(frontmatter_lines, next_index)
        else:
            data[key] = None
            index += 1

    body = "\n".join(lines[closing + 1 :]).lstrip("\n")
    if text.endswith("\n"):
        body += "\n"
    return data, body


def parse_case(case_path: Path, rag_root: Path) -> Dict[str, Any]:
    """解析单个案例并补充相对于 RAG 根目录的文件路径。"""
    text = case_path.read_text(encoding="utf-8")
    data, _ = parse_frontmatter(text, str(case_path))
    missing = [field for field in ("id", "title", "summary") if not data.get(field)]
    if missing:
        raise FrontmatterError(f"{case_path}：缺少必填字段 {', '.join(missing)}")
    record = dict(data)
    try:
        record["path"] = case_path.resolve().relative_to(rag_root.resolve()).as_posix()
    except ValueError as exc:
        raise FrontmatterError(f"{case_path}：案例文件不在 RAG 根目录 {rag_root} 内") from exc
    return record


def build_index(cases_dir: Path, output_path: Path, rag_root: Path) -> List[Dict[str, Any]]:
    """解析全部案例，稳定排序并幂等写入 JSON 索引。"""
    case_paths = sorted(cases_dir.glob("*.md"), key=lambda path: path.name.casefold())
    records = [parse_case(case_path, rag_root) for case_path in case_paths]
    seen: Dict[str, str] = {}
    for record in records:
        case_id = str(record["id"])
        if case_id in seen:
            raise FrontmatterError(
                f"重复案例 id {case_id!r}：{seen[case_id]} 与 {record['path']}"
            )
        seen[case_id] = str(record["path"])
    records.sort(key=lambda item: (str(item["id"]).casefold(), str(item["path"])))

    payload = json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not output_path.exists() or output_path.read_text(encoding="utf-8") != payload:
        output_path.write_text(payload, encoding="utf-8")
    return records


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建 Architecture Case RAG JSON 索引")
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_CASES_DIR, help="案例目录")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="索引输出路径")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    cases_dir = args.cases_dir.resolve()
    output_path = args.output.resolve()
    rag_root = RAG_ROOT if cases_dir == DEFAULT_CASES_DIR.resolve() else cases_dir.parent
    try:
        records = build_index(cases_dir, output_path, rag_root)
    except (OSError, FrontmatterError) as exc:
        print(f"构建失败：{exc}", file=sys.stderr)
        return 1
    print(f"已生成 {output_path}，共 {len(records)} 个案例。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
