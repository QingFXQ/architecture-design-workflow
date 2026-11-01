#!/usr/bin/env python3
"""Check project.yaml against decisions, artifacts, and the filesystem.

Read-only reconciliation: it does not design, edit drawings, or approve a Gate.
It reports where the state snapshot disagrees with decisions, the artifact
manifest, or files on disk.

Usage:
    python tools/studio_state/check_state.py
    python tools/studio_state/check_state.py --root "D:/path/to/project"
    python tools/studio_state/check_state.py --json
    python tools/studio_state/check_state.py --strict

Exit codes: 0 no errors; 1 errors; 2 state/PyYAML load failure.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("需要 PyYAML：python -m pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)


GATE_STATUSES = {"passed", "not_passed", "not_started", "in_progress", "blocked", "waived"}
SEVERITIES = {"blocking", "partial", "known_unknown", "closed"}
FLOOR_RE = re.compile(r"^(?:\d+F|B\d+)$")
DECISION_ROW_RE = re.compile(r"^\|\s*(D-\d{3})\s*\|")
AMOUNT_TOLERANCE = 0.05


class Report:
    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []
        self.infos: list[dict[str, str]] = []

    def error(self, code: str, message: str) -> None:
        self.errors.append({"code": code, "message": message})

    def warn(self, code: str, message: str) -> None:
        self.warnings.append({"code": code, "message": message})

    def info(self, code: str, message: str) -> None:
        self.infos.append({"code": code, "message": message})


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def close(left: float, right: float, tolerance: float = AMOUNT_TOLERANCE) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def resolve(root: Path, raw: Any) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else (root / path).resolve()


def load_state(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report the concrete parse failure
        print(f"无法读取状态文件 {path}：{exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    if not isinstance(payload, dict):
        print(f"状态文件根节点必须是对象：{path}", file=sys.stderr)
        raise SystemExit(2)
    return payload


def read_decision_rows(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = DECISION_ROW_RE.match(line)
        if match:
            rows[match.group(1)] = line
    return rows


def has_gate_decision(rows: dict[str, str], gate: str, *, need_approval: bool) -> bool:
    for line in rows.values():
        lowered = line.lower()
        if gate.lower() not in lowered:
            continue
        if "撤销" in line or "revoked" in lowered or "superseded" in lowered:
            continue
        if need_approval:
            if re.search(r"批准|通过|approved|passed", line, re.IGNORECASE):
                return True
        else:
            if re.search(r"选定|批准|通过|生效|selected|approved|passed", line, re.IGNORECASE):
                return True
    return False


def check_structure(state: dict[str, Any], report: Report) -> None:
    required = [
        "schema_version", "project", "gates", "hard_constraints", "current",
        "decisions", "blockers", "next", "record_sources",
    ]
    for key in required:
        if key not in state:
            report.error("STRUCT_MISSING", f"缺少顶层字段：{key}")
    if state.get("schema_version") != 1:
        report.error("STRUCT_SCHEMA", "schema_version 必须为 1")
    project = state.get("project")
    if not isinstance(project, dict):
        report.error("STRUCT_PROJECT", "project 必须是对象")
    else:
        for key in ("id", "name", "phase"):
            if not project.get(key):
                report.error("STRUCT_PROJECT_FIELD", f"project.{key} 不能为空")
    gates = state.get("gates")
    if not isinstance(gates, dict):
        report.error("STRUCT_GATES", "gates 必须是对象")
    else:
        for letter in "ABCD":
            gate = gates.get(letter)
            if not isinstance(gate, dict):
                report.error("STRUCT_GATE", f"gates.{letter} 必须是对象")
                continue
            status = gate.get("status")
            if status not in GATE_STATUSES:
                report.error("STRUCT_GATE_STATUS", f"gates.{letter}.status 非法：{status!r}")
    for key in ("decisions", "blockers", "next", "record_sources"):
        if not isinstance(state.get(key), list):
            report.error("STRUCT_LIST", f"{key} 必须是数组")


def check_areas(state: dict[str, Any], report: Report) -> None:
    current = state.get("current") or {}
    areas = current.get("areas_m2") if isinstance(current, dict) else None
    if not isinstance(areas, dict):
        report.error("AREA_MISSING", "current.areas_m2 必须是对象")
        return
    floors = {key: value for key, value in areas.items() if FLOOR_RE.match(str(key))}
    if not floors:
        report.error("AREA_FLOORS", "没有找到 1F/2F/B1 形式的楼层面积")
        return
    for key, value in floors.items():
        if not is_number(value) or float(value) <= 0:
            report.error("AREA_VALUE", f"楼层 {key} 的面积必须为正数：{value!r}")
    above = {key: value for key, value in floors.items() if not str(key).startswith("B")}
    below = {key: value for key, value in floors.items() if str(key).startswith("B")}
    sum_above = sum(float(value) for value in above.values())
    sum_below = sum(float(value) for value in below.values())
    total = sum_above + sum_below

    declared_above = areas.get("above_ground")
    if is_number(declared_above):
        if not close(declared_above, sum_above):
            report.error("AREA_ABOVE_MISMATCH", f"above_ground={declared_above}，但地上楼层相加={sum_above:.2f}")
    else:
        report.warn("AREA_ABOVE_MISSING", "未声明 above_ground；无法核对地上合计")

    declared_total = areas.get("physical_total")
    if is_number(declared_total):
        if not close(declared_total, total):
            report.error("AREA_TOTAL_MISMATCH", f"physical_total={declared_total}，但楼层相加={total:.2f}")
    else:
        report.warn("AREA_TOTAL_MISSING", "未声明 physical_total；无法核对物理合计")

    roof = areas.get("roof_m2")
    if roof is not None:
        if not is_number(roof) or float(roof) <= 0:
            report.error("AREA_ROOF", f"roof_m2 必须为正数：{roof!r}")
        else:
            report.info("AREA_ROOF", f"roof_m2={roof} 为屋面面积，不计入 physical_total")

    if "RF" in floors:
        report.warn("AREA_RF_KEY", "areas_m2 中含 RF；若它是屋面面积，请移到 roof_m2，否则楼层相加会把屋面算进去")

    base = areas.get("base_geometry")
    if is_number(base) and is_number(declared_total) and float(base) < float(declared_total):
        report.warn("AREA_BASE_SMALLER", f"base_geometry={base} 小于 physical_total={declared_total}；请确认是否漏计井道/楼梯")

    if areas.get("legal_gfa") is True:
        report.warn("AREA_LEGAL", "legal_gfa=true；必须写清法定 GFA 的依据，不能把物理面积直接当法定面积")

    constraints = state.get("hard_constraints") or {}
    gfa = constraints.get("gfa_m2") if isinstance(constraints, dict) else None
    if isinstance(gfa, dict):
        target = gfa.get("target")
        minimum = gfa.get("min")
        maximum = gfa.get("max")
        tolerance = gfa.get("tolerance_ratio")
        if not all(is_number(value) for value in (target, minimum, maximum)):
            report.error("GFA_FIELDS", "hard_constraints.gfa_m2 需要数值 target/min/max")
        else:
            if not float(minimum) <= float(target) <= float(maximum):
                report.error("GFA_RANGE", f"target={target} 不在 [{minimum}, {maximum}] 内")
            if is_number(tolerance):
                expected_min = float(target) * (1 - float(tolerance))
                expected_max = float(target) * (1 + float(tolerance))
                if not close(minimum, expected_min, 1.0):
                    report.warn("GFA_MIN", f"min={minimum} 与 target×(1-tol)={expected_min:.2f} 不一致")
                if not close(maximum, expected_max, 1.0):
                    report.warn("GFA_MAX", f"max={maximum} 与 target×(1+tol)={expected_max:.2f} 不一致")
            if is_number(declared_total) and not float(minimum) <= float(declared_total) <= float(maximum):
                report.warn("GFA_OUTSIDE", f"physical_total={declared_total} 不在硬区间 [{minimum}, {maximum}] 内")

    if is_number(declared_total):
        report.info("AREA_TOTAL", f"楼层相加 = {total:.2f}；申报 physical_total = {declared_total}")


def check_gates(state: dict[str, Any], rows: dict[str, str], report: Report) -> None:
    gates = state.get("gates") or {}
    project = state.get("project") or {}
    blockers = state.get("blockers") or []
    blocking = [item for item in blockers if isinstance(item, dict) and item.get("severity") == "blocking"]
    gate_a = (gates.get("A") or {}).get("status")
    gate_b = (gates.get("B") or {}).get("status")

    if gate_a == "passed" and not has_gate_decision(rows, "Gate A", need_approval=False):
        report.error("GATE_A_EVIDENCE", "gates.A=passed，但 DECISIONS.md 没有可核查的 Gate A 选择记录")

    if gate_b == "passed":
        if not has_gate_decision(rows, "Gate B", need_approval=True):
            report.error("GATE_B_EVIDENCE", "gates.B=passed，但 DECISIONS.md 没有 Gate B 批准记录")
        if blocking:
            report.error("GATE_B_BLOCKERS", f"gates.B=passed，但仍有 {len(blocking)} 个 blocking 项；Gate B 不能通过")

    if project.get("formal_drawing_started") and gate_b != "passed":
        report.error("DRAWING_BEFORE_GATE_B", "formal_drawing_started=true，但 Gate B 未通过")
    if project.get("drawing_mode") == "formal_drawing" and gate_b != "passed":
        report.error("DRAWING_MODE_BEFORE_GATE_B", "drawing_mode=formal_drawing，但 Gate B 未通过")

    report.info("GATE_STATUS", f"A={gate_a} B={gate_b} C={(gates.get('C') or {}).get('status')} D={(gates.get('D') or {}).get('status')}")


def check_decisions(state: dict[str, Any], rows: dict[str, str], report: Report) -> None:
    seen: set[str] = set()
    for item in state.get("decisions") or []:
        if not isinstance(item, dict):
            report.error("DECISION_SHAPE", f"decisions 项必须是对象：{item!r}")
            continue
        decision_id = str(item.get("id", "")).strip()
        if not decision_id:
            report.error("DECISION_ID", "decisions 项缺少 id")
            continue
        if decision_id in seen:
            report.error("DECISION_DUPLICATE", f"decisions 中 {decision_id} 重复")
        seen.add(decision_id)
        if decision_id not in rows:
            report.error("DECISION_MISSING", f"{decision_id} 在 DECISIONS.md 中不存在")
            continue
        status = str(item.get("status", "")).strip()
        if not status:
            report.error("DECISION_STATUS", f"{decision_id} 缺少 status")
        line = rows[decision_id]
        lowered = line.lower()
        if status in {"revoked", "superseded"} and "撤销" not in line and "revoked" not in lowered:
            report.warn("DECISION_STATUS_DRIFT", f"{decision_id} 在 YAML 中标为 {status}，但 DECISIONS.md 行内没有撤销标记")
        if status in {"active", "approved", "passed"} and re.search(r"被撤销|已撤销|revoked", line, re.IGNORECASE):
            report.warn("DECISION_STATUS_DRIFT", f"{decision_id} 在 YAML 中标为 {status}，但 DECISIONS.md 行内写的是撤销")


def check_blockers(state: dict[str, Any], root: Path, report: Report) -> None:
    seen: set[str] = set()
    for item in state.get("blockers") or []:
        if not isinstance(item, dict):
            report.error("BLOCKER_SHAPE", f"blockers 项必须是对象：{item!r}")
            continue
        blocker_id = str(item.get("id", "")).strip()
        if not blocker_id:
            report.error("BLOCKER_ID", "blocker 缺少 id")
            continue
        if blocker_id in seen:
            report.error("BLOCKER_DUPLICATE", f"blocker {blocker_id} 重复")
        seen.add(blocker_id)
        for key in ("area", "issue"):
            if not item.get(key):
                report.error("BLOCKER_FIELD", f"{blocker_id} 缺少 {key}")
        severity = item.get("severity")
        if severity not in SEVERITIES:
            report.error("BLOCKER_SEVERITY", f"{blocker_id} 的 severity 非法：{severity!r}")
        evidence = item.get("evidence")
        if isinstance(evidence, str):
            evidence = [evidence]
        if not isinstance(evidence, list) or not evidence:
            report.error("BLOCKER_EVIDENCE", f"{blocker_id} 缺少 evidence")
            continue
        for raw in evidence:
            if not resolve(root, raw).exists():
                report.error("BLOCKER_EVIDENCE_MISSING", f"{blocker_id} 的证据不存在：{raw}")


def check_next(state: dict[str, Any], report: Report) -> None:
    seen: set[str] = set()
    for item in state.get("next") or []:
        if not isinstance(item, dict):
            report.error("NEXT_SHAPE", f"next 项必须是对象：{item!r}")
            continue
        next_id = str(item.get("id", "")).strip()
        if not next_id:
            report.error("NEXT_ID", "next 项缺少 id")
            continue
        if next_id in seen:
            report.error("NEXT_DUPLICATE", f"next 中 {next_id} 重复")
        seen.add(next_id)
        for key in ("action", "owner"):
            if not item.get(key):
                report.error("NEXT_FIELD", f"{next_id} 缺少 {key}")
        if not isinstance(item.get("blocking"), bool):
            report.error("NEXT_BLOCKING", f"{next_id} 的 blocking 必须是 true/false")


def check_current_files(state: dict[str, Any], root: Path, report: Report) -> None:
    current = state.get("current") or {}
    for key in ("model", "drawing_set"):
        item = current.get(key) if isinstance(current, dict) else None
        if not isinstance(item, dict):
            report.error("CURRENT_MISSING", f"current.{key} 必须是对象")
            continue
        raw_path = item.get("path")
        if not raw_path:
            report.error("CURRENT_PATH", f"current.{key}.path 不能为空")
            continue
        path = resolve(root, raw_path)
        if not path.exists():
            report.error("CURRENT_PATH_MISSING", f"current.{key}.path 不存在：{raw_path}")
            continue
        declared_bytes = item.get("bytes")
        if is_number(declared_bytes) and path.is_file() and int(declared_bytes) != path.stat().st_size:
            report.error("CURRENT_BYTES", f"current.{key}.bytes={declared_bytes}，实际={path.stat().st_size}")
        saved = item.get("saved_at")
        if saved and path.is_file():
            try:
                declared_time = datetime.fromisoformat(str(saved).replace("Z", "+00:00"))
                file_time = datetime.fromtimestamp(path.stat().st_mtime, tz=declared_time.tzinfo)
                if abs((file_time - declared_time).total_seconds()) > 86400:
                    report.warn("CURRENT_SAVED_AT", f"current.{key}.saved_at 与文件修改时间相差超过 1 天")
            except ValueError:
                report.warn("CURRENT_SAVED_AT", f"current.{key}.saved_at 不是 ISO 时间：{saved!r}")

    rooms = current.get("rooms") if isinstance(current, dict) else None
    if isinstance(rooms, dict):
        latest = rooms.get("latest_readback")
        if not isinstance(latest, int) or latest <= 0:
            report.error("ROOMS_READBACK", "current.rooms.latest_readback 必须是正整数")
        if rooms.get("non_positive") not in (0, None):
            report.warn("ROOMS_NON_POSITIVE", f"current.rooms.non_positive={rooms.get('non_positive')}，应记录处理状态")
        if rooms.get("warnings") not in (0, None):
            report.warn("ROOMS_WARNINGS", f"current.rooms.warnings={rooms.get('warnings')}，应记录处理状态")

    rotation = current.get("rotation") if isinstance(current, dict) else None
    if isinstance(rotation, dict):
        rotated = rotation.get("upper_elements_rotated")
        if not isinstance(rotated, int) or rotated <= 0:
            report.warn("ROTATION_COUNT", "current.rotation.upper_elements_rotated 不是正整数")


def check_artifacts(root: Path, report: Report) -> None:
    path = root / "ARTIFACTS.csv"
    if not path.exists():
        report.error("ARTIFACTS_MISSING", "ARTIFACTS.csv 不存在")
        return
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            for column in ("id", "path", "bytes", "status"):
                if column not in fields:
                    report.error("ARTIFACTS_COLUMN", f"ARTIFACTS.csv 缺少列：{column}")
            if not fields:
                return
            seen: set[str] = set()
            for row in reader:
                artifact_id = str(row.get("id", "")).strip()
                raw_path = str(row.get("path", "")).strip()
                if not artifact_id:
                    report.error("ARTIFACTS_ID", "ARTIFACTS.csv 存在无 id 的行")
                    continue
                if artifact_id in seen:
                    report.error("ARTIFACTS_DUPLICATE", f"ARTIFACTS.csv 中 {artifact_id} 重复")
                seen.add(artifact_id)
                if not raw_path:
                    report.error("ARTIFACTS_PATH", f"{artifact_id} 缺少 path")
                    continue
                resolved = resolve(root, raw_path)
                if not resolved.exists():
                    report.error("ARTIFACTS_MISSING_PATH", f"{artifact_id} 的路径不存在：{raw_path}")
                    continue
                declared = str(row.get("bytes", "")).strip()
                if resolved.is_file() and declared.isdigit() and int(declared) > 0:
                    actual = resolved.stat().st_size
                    if int(declared) != actual:
                        report.error("ARTIFACTS_BYTES", f"{artifact_id} 的 bytes={declared}，实际={actual}")
                if str(row.get("status", "")).strip() == "pending":
                    report.warn("ARTIFACTS_PENDING", f"{artifact_id} 仍是 pending")
    except Exception as exc:  # noqa: BLE001 - report the concrete CSV failure
        report.error("ARTIFACTS_READ", f"无法读取 ARTIFACTS.csv：{exc}")


def check_log_index(root: Path, report: Report) -> None:
    csv_path = root / "LOG_INDEX.csv"
    summary_path = root / "LOG_INDEX_SUMMARY.json"
    if not csv_path.exists() or not summary_path.exists():
        return
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = sum(1 for _ in csv.DictReader(handle))
        declared = summary.get("total")
        if isinstance(declared, int) and declared != rows:
            report.warn("LOG_INDEX_COUNT", f"LOG_INDEX.csv 有 {rows} 行，但 summary.total={declared}")
        else:
            report.info("LOG_INDEX", f"LOG_INDEX.csv 行数与 summary.total 一致：{rows}")
    except Exception as exc:  # noqa: BLE001 - report the concrete index failure
        report.warn("LOG_INDEX_READ", f"无法核对日志索引：{exc}")


def git_head(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:  # noqa: BLE001 - git is optional
        pass
    return ""


def git_is_ancestor(path: Path, ancestor: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "merge-base", "--is-ancestor", ancestor, "HEAD"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        return result.returncode == 0
    except Exception:  # noqa: BLE001 - git is optional
        return False


def check_repository(state: dict[str, Any], root: Path, report: Report, no_git: bool) -> None:
    repository = state.get("repository")
    if not isinstance(repository, dict) or no_git:
        return
    workflow_path = repository.get("workflow_path")
    declared_head = str(repository.get("head", "")).strip()
    actual_head = ""
    if workflow_path:
        path = resolve(root, workflow_path)
        if not path.exists():
            report.error("REPO_PATH", f"repository.workflow_path 不存在：{workflow_path}")
        else:
            actual_head = git_head(path)
            if not actual_head:
                report.warn("REPO_GIT", "无法读取 workflow_path 的 git HEAD")
            elif declared_head and not (actual_head.startswith(declared_head) or declared_head.startswith(actual_head)):
                if git_is_ancestor(path, declared_head):
                    report.info("REPO_HEAD_ANCESTOR", f"repository.head={declared_head} 是当前 HEAD={actual_head} 的祖先；快照基于该提交")
                else:
                    report.error("REPO_HEAD", f"repository.head={declared_head}，但实际 HEAD={actual_head}")
            else:
                report.info("REPO_HEAD", f"repository.head 与实际 HEAD 一致：{actual_head}")

    shallow_path = repository.get("shallow_clone_path")
    if shallow_path and repository.get("shallow_clone_synced"):
        path = resolve(root, shallow_path)
        if not path.exists():
            report.error("REPO_SHALLOW_PATH", f"shallow_clone_path 不存在：{shallow_path}")
        else:
            shallow_head = git_head(path)
            if actual_head and shallow_head and shallow_head != actual_head:
                report.warn("REPO_SHALLOW_HEAD", f"shallow clone HEAD={shallow_head} 与 workflow HEAD={actual_head} 不一致")
            elif shallow_head:
                report.info("REPO_SHALLOW", f"shallow clone 已同步：{shallow_head}")

    if repository.get("pushed") is False:
        report.info("REPO_PUSH", "repository.pushed=false；GitHub 尚未推送")


def check_record_sources(state: dict[str, Any], root: Path, report: Report) -> None:
    for raw in state.get("record_sources") or []:
        if not resolve(root, raw).exists():
            report.error("RECORD_SOURCE_MISSING", f"record_sources 指向不存在的路径：{raw}")


def main() -> int:
    parser = argparse.ArgumentParser(description="核对 project.yaml 与 DECISIONS.md、ARTIFACTS.csv 及文件系统")
    parser.add_argument("--root", default=".", help="项目根目录（默认当前目录）")
    parser.add_argument("--state", default="", help="project.yaml 路径（默认 <root>/project.yaml）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--strict", action="store_true", help="把 warning 当作 error")
    parser.add_argument("--no-git", action="store_true", help="跳过 git HEAD 检查")
    parser.add_argument("--verbose", action="store_true", help="打印 info 项")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    state_path = Path(args.state).resolve() if args.state else root / "project.yaml"
    if not state_path.exists():
        print(f"找不到状态文件：{state_path}", file=sys.stderr)
        return 2

    state = load_state(state_path)
    report = Report()
    decision_rows = read_decision_rows(root / "DECISIONS.md")

    check_structure(state, report)
    check_areas(state, report)
    check_gates(state, decision_rows, report)
    check_decisions(state, decision_rows, report)
    check_blockers(state, root, report)
    check_next(state, report)
    check_current_files(state, root, report)
    check_artifacts(root, report)
    check_log_index(root, report)
    check_repository(state, root, report, args.no_git)
    check_record_sources(state, root, report)

    if args.strict:
        report.errors.extend(report.warnings)
        report.warnings.clear()

    result = {
        "ok": not report.errors,
        "state": str(state_path),
        "root": str(root),
        "errors": report.errors,
        "warnings": report.warnings,
        "infos": report.infos,
        "counts": {
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "infos": len(report.infos),
        },
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Project state check")
        print(f"  state: {state_path}")
        print(f"  root:  {root}")
        print(f"  errors={len(report.errors)} warnings={len(report.warnings)} infos={len(report.infos)}")
        for item in report.errors:
            print(f"[ERROR] {item['code']}: {item['message']}")
        for item in report.warnings:
            print(f"[WARN]  {item['code']}: {item['message']}")
        if args.verbose:
            for item in report.infos:
                print(f"[INFO]  {item['code']}: {item['message']}")
        print("RESULT:", "PASS" if not report.errors else "FAIL")

    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
