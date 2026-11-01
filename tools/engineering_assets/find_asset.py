"""Small offline task index. No embeddings, app access or automatic execution."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "knowledge" / "engineering-assets"
CATALOG = ASSETS / "catalog.json"

def load_entries():
    return json.loads(CATALOG.read_text(encoding="utf-8"))["entries"]

def normal(text):
    return re.sub(r"[\s_\-]+", "", text.casefold())

def search(task, software="all", limit=3):
    query = normal(task)
    matches = []
    for entry in load_entries():
        if software != "all" and entry["software"] != software:
            continue
        terms = {normal(term) for term in entry["keywords"]}
        score = sum(min(len(term), 12) for term in terms if term and term in query)
        if score:
            hit = dict(entry)
            hit["score"] = score
            hit["card_path"] = str(ASSETS / entry["card"])
            hit["source_paths"] = [str(ROOT / source) for source in entry["sources"]]
            matches.append(hit)
    return sorted(matches, key=lambda hit: (-hit["score"], hit["id"]))[:limit]

def check_catalog():
    errors, ids = [], set()
    for entry in load_entries():
        key = entry.get("id")
        if not key or key in ids:
            errors.append(f"Duplicate/missing ID: {key}")
        ids.add(key)
        for field in ("title", "software", "kind", "keywords", "verification", "card", "sources"):
            if not entry.get(field) and field != "sources":
                errors.append(f"{key}: missing {field}")
        verification = entry.get("verification", {})
        if verification.get("host_verified") and not (verification.get("state") == "host-verified"
                and verification.get("host_version") and verification.get("evidence")):
            errors.append(f"{key}: host verification needs a host version and evidence")
        for path in [ASSETS / entry["card"], *[ROOT / source for source in entry["sources"]]]:
            resolved = path.resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.is_file():
                errors.append(f"{key}: missing/out-of-root asset: {path}")
        for evidence in entry.get("verification", {}).get("evidence", []):
            if not (ROOT / evidence).is_file():
                errors.append(f"{key}: missing evidence: {evidence}")
    return errors

def self_test():
    cases = json.loads(Path(__file__).with_name("routing-cases.json").read_text(encoding="utf-8"))
    failures = []
    for case in cases:
        hits = search(case["task"], case["software"], 1)
        actual = hits[0]["id"] if hits else None
        if actual != case["expected"]:
            failures.append({"task": case["task"], "expected": case["expected"], "actual": actual})
    return len(cases), failures

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task")
    parser.add_argument("--software", choices=["revit", "cad", "all"], default="all")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.check or args.self_test:
        errors = check_catalog()
        count, failures = self_test() if args.self_test else (0, [])
        print(json.dumps({"catalog_entries": len(load_entries()), "errors": errors,
                          "routing_cases": count, "failures": failures}, ensure_ascii=False, indent=2))
        return 1 if errors or failures else 0
    if not args.task or not args.task.strip() or args.limit < 1:
        parser.error("provide --task and a positive --limit")
    hits = search(args.task, args.software, args.limit)
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    elif not hits:
        print("没有已登记的匹配资产；不要冒充已有经验，按任务补充并标明验证状态。")
    else:
        for hit in hits:
            print(f'{hit["id"]} | {hit["title"]} | {hit["verification"]["state"]}')
            print(f'  操作卡: {hit["card_path"]}')
            for source in hit["source_paths"]:
                print(f"  相关资产: {source}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
