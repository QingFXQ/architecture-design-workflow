#!/usr/bin/env python3
"""Regression checks for the read-only Revit MCP smoke runner."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("smoke_revit_mcp.py")
SPEC = importlib.util.spec_from_file_location("smoke_revit_mcp", SCRIPT)
smoke = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(smoke)


class SmokeContractTests(unittest.TestCase):
    def test_read_only_probe_sequence_never_contains_model_writes(self):
        names = [item["name"] for item in smoke.READ_ONLY_PROBES]
        self.assertEqual(names, ["get_current_view_info", "analyze_model_statistics"])
        self.assertFalse(any(name.startswith("create_") or name.startswith("delete_") for name in names))

    def test_ssh_command_targets_windows_side_mcp_server(self):
        command = smoke.ssh_command("codex", "YOUR_REVIT_HOST")
        self.assertEqual(command[:5], ["ssh", "-T", "-l", "codex", "YOUR_REVIT_HOST"])
        self.assertIn("npx -y mcp-server-for-revit", command[-1])


if __name__ == "__main__":
    unittest.main()
