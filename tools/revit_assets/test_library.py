"""Real-file integration checks. Scratch data stays under the asset-library disk."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import library

ROOT = library.DEFAULT_ROOT


class LibraryTests(unittest.TestCase):
    def test_inventory_integrity_and_no_failed_files(self):
        report = json.loads((ROOT / "manifests/verification.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(report["files"], 2700)
        self.assertFalse(report["errors"])
        self.assertFalse(report["host_verified"])
        con = library.connect(ROOT)
        self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(con.execute("SELECT COUNT(DISTINCT relative_path) FROM assets").fetchone()[0], report["files"])
        con.close()

    def test_real_family_metadata_preview_and_type_parameters(self):
        path = ROOT / "originals/Autodesk-2021-Samples/rac_basic_sample_family.rfa"
        meta = library.inspect_native(path, ROOT, library.sha256(path))
        self.assertEqual(meta["revit_year"], 2021)
        self.assertEqual(meta["category"], "Furniture")
        self.assertEqual(len(meta["types"]), 3)
        self.assertTrue(meta["preview"])
        params = next(iter(meta["type_parameters"].values()))
        self.assertTrue(any(p["units"] == "mm" for p in params))

    def test_html_named_rfa_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tools") as td:
            p = Path(td) / "not-a-family.rfa"
            p.write_text("<html>Download login page</html>")
            with self.assertRaises(ValueError):
                library.native_check(p)

    def test_compatibility_filters_newer_projects(self):
        self.assertEqual(library.query(ROOT, "Snowdon", "project", 2021, 20), [])
        newer = library.query(ROOT, "Snowdon", "project", 2024, 20)
        self.assertEqual(len(newer), 7)
        self.assertTrue(all(r["revit_year"] == 2024 for r in newer))

    def test_chinese_category_and_literal_search(self):
        rows = library.query(ROOT, "窗", "family", 2021, 100)
        self.assertTrue(any(r["category"] == "Windows" for r in rows))
        self.assertEqual(library.query(ROOT, "' OR 1=1 --", limit=3), [])
        self.assertEqual(library.query(ROOT, "%", limit=3), [])

    def test_type_catalog_and_idempotent_working_copy(self):
        con = library.connect(ROOT)
        row = con.execute("SELECT a.id FROM assets a JOIN auxiliary_files x ON a.id=x.asset_id ORDER BY a.bytes LIMIT 1").fetchone()
        con.close()
        self.assertIsNotNone(row)
        with tempfile.TemporaryDirectory(dir=ROOT / "tools") as td:
            dest = Path(td)
            first = library.stage(ROOT, row[0], dest)
            second = library.stage(ROOT, row[0], dest)
            self.assertEqual(first, second)
            self.assertGreaterEqual(len(first["paths"]), 2)
            self.assertEqual(len(list(dest.iterdir())), len(first["paths"]))
            changed = Path(first["paths"][0])
            changed.write_bytes(b"changed working copy")
            with self.assertRaises(ValueError):
                library.stage(ROOT, row[0], dest)
            self.assertEqual(changed.read_bytes(), b"changed working copy")

    def test_stage_preserves_originals_and_version_boundary(self):
        newer = library.query(ROOT, "Snowdon", "project", 2024, 1)[0]
        with tempfile.TemporaryDirectory(dir=ROOT / "tools") as td:
            with self.assertRaises(ValueError):
                library.stage(ROOT, newer["id"], Path(td), 2021)
        old = library.query(ROOT, "rac_basic_sample_family", "family", 2021, 1)[0]
        with self.assertRaises(ValueError):
            library.stage(ROOT, old["id"], ROOT / "originals/test-working-copy")

    def test_competition_documents_are_not_native_projects(self):
        con = library.connect(ROOT)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM reference_files WHERE source_id='CIC-BIM-Competition-2024'").fetchone()[0], 4)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM assets WHERE source_id='CIC-BIM-Competition-2024'").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM assets WHERE source_id='BIMNet-openBIM-2025'").fetchone()[0], 0)
        con.close()


if __name__ == "__main__":
    unittest.main()
