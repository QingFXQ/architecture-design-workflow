"""Exercise actual DXF outputs; does not access an AutoCAD session or DWG."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
from datetime import datetime
import hashlib

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "knowledge/engineering-assets/examples/cad-parametric"
spec = importlib.util.spec_from_file_location("engineering_cad_sample", SAMPLE / "generate.py")
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)

def main():
    # Keep test outputs in an ignored, dedicated directory; no recursive cleanup.
    work = ROOT / "tools/engineering_assets/local" / datetime.now().strftime("test-%Y%m%d-%H%M%S-%f")
    work.mkdir(parents=True)
    p = sample.load_params(SAMPLE / "params.json")
    base = work / "base"
    holes = sample.build(p, base)
    first = sample.verify(p, base / "sample.dxf", holes)
    holes2 = sample.build(p, base)
    second = sample.verify(p, base / "sample.dxf", holes2)
    assert first["entity_counts"] == second["entity_counts"]
    assert holes == holes2 and second["window_definitions"] == 1

    changed = dict(p, width=14400)
    changed_holes = sample.build(changed, base)
    third = sample.verify(changed, base / "sample.dxf", changed_holes)
    assert third["dimensions_mm"] == [8000, 14400]
    assert third["window_instances"] == 20 and third["entity_counts"] == first["entity_counts"]
    assert changed_holes != holes

    unowned = work / "unowned"
    unowned.mkdir()
    sentinel = unowned / "sample.dxf"
    sentinel.write_bytes(b"USER-FILE-DO-NOT-REPLACE")
    try:
        sample.build(p, unowned)
        raise AssertionError("Unowned output overwritten")
    except ValueError as error:
        assert "unowned" in str(error)
    assert sentinel.read_bytes() == b"USER-FILE-DO-NOT-REPLACE"

    bad = work / "bad-params.json"
    bad.write_text(json.dumps(dict(p, units="m")), encoding="utf-8")
    try:
        sample.load_params(bad)
        raise AssertionError("Implicit unit change accepted")
    except ValueError as error:
        assert "mm" in str(error)

    # Inspect the actual rendered dimension text, not just measurement points.
    doc = sample.ezdxf.readfile(base / "sample.dxf")
    labels = []
    for dim in doc.modelspace().query("DIMENSION"):
        for entity in doc.blocks[dim.dxf.geometry]:
            if entity.dxftype() == "MTEXT": labels.append(entity.plain_text())
            elif entity.dxftype() == "TEXT": labels.append(entity.dxf.text)
    assert "14400" in labels and "8000" in labels, labels

    report = json.loads((SAMPLE / "out/verification.json").read_text(encoding="utf-8"))
    report.update({
        "checked_on": "2026-10-28",
        "tests": {
            "actual_dxf_readback": True,
            "repeat_generation_no_entity_growth": True,
            "parameter_change_updates_geometry": True,
            "shared_window_definition": True,
            "wall_openings_clear": True,
            "dimension_text_matches_measurement": True,
            "unowned_output_preserved": True,
            "ambiguous_units_rejected": True,
        },
        "script_sha256": hashlib.sha256((SAMPLE / "generate.py").read_bytes()).hexdigest(),
        "host_verified": False,
        "dwg_verified": False,
        "scope": "Offline DXF generation/readback and PDF rendering only; no AutoCAD install or session",
    })
    (SAMPLE / "VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tests": report["tests"], "host_verified": False}, indent=2))

if __name__ == "__main__":
    main()
