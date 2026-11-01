"""Offline regressions for the task-facing retrieval path; no model service."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import search_cases


class WorkingRetrievalTests(unittest.TestCase):
    def setUp(self):
        local = search_cases.RAG_ROOT / "local"
        local.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="retrieval-test-", dir=local)
        self.root = Path(self.temp.name).resolve()
        self.assertTrue(self.root.is_relative_to(local.resolve()))
        self.addCleanup(self.temp.cleanup)
        (self.root / "cases").mkdir()
        (self.root / "index").mkdir()
        records = []
        texts = {
            "night": "剧场设独立入口，可在夜间独立运营，门禁形成闭馆边界。",
            "courtyard": "围绕庭院设置阅览带，通过天窗和侧窗改善采光。",
            "unknown": "夜间独立开放和门禁资料未提供。",
        }
        for key, text in texts.items():
            (self.root / f"cases/{key}.md").write_text(
                f"# {key}\n\n## 10. 人流与服务流线\n{text}\n", encoding="utf-8")
            records.append({"id":key,"title":key,"path":f"cases/{key}.md",
                            "type":["library"],"quality":"★★★","year":2024,
                            "summary":"","problem":[],"site":[],"strategy":[]})
        self.index = self.root / "index/cases.json"
        self.index.write_text(json.dumps(records), encoding="utf-8")

    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = search_cases.main(["--index",str(self.index),*args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_operational_evidence_and_unknown_gap(self):
        hits = search_cases.lexical_search(self.index,self.root,
            query="夜间独立开放与门禁")
        self.assertEqual([x["id"] for x in hits],["night"])
        self.assertFalse(hits[0]["visual_evidence_checked"])

    def test_different_problem_returns_different_case(self):
        hits = search_cases.lexical_search(self.index,self.root,query="庭院采光")
        self.assertEqual(hits[0]["id"],"courtyard")

    def test_baseline_does_not_ignore_query(self):
        code, _, stderr = self.run_cli("--mode","baseline","--query","夜间")
        self.assertEqual(code,1)
        self.assertIn("不接受--query",stderr)

    def test_auto_missing_index_explicitly_falls_back(self):
        code, stdout, stderr = self.run_cli("--query","夜间独立开放",
            "--semantic-index",str(self.root/"missing.json"),"--format","json")
        self.assertEqual(code,0)
        self.assertIn("回退lexical",stderr)
        self.assertEqual(json.loads(stdout)[0]["retrieval_mode"],"lexical")

    def test_explicit_semantic_does_not_hide_failure(self):
        code, _, stderr = self.run_cli("--mode","semantic","--query","夜间",
            "--semantic-index",str(self.root/"missing.json"))
        self.assertEqual(code,1)
        self.assertIn("检索失败",stderr)


if __name__ == "__main__":
    unittest.main()
