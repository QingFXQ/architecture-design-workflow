#!/usr/bin/env python3
"""Run the non-mutating Revit MCP connection probe through Windows SSH."""

from __future__ import annotations

import argparse
import json
import queue
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional


READ_ONLY_PROBES = (
    {"name": "get_current_view_info", "arguments": {}},
    {"name": "analyze_model_statistics", "arguments": {"includeDetailedTypes": False}},
)


def ssh_command(user: str, host: str) -> List[str]:
    return [
        "ssh", "-T", "-l", user, host,
        'cmd.exe /d /s /c "npx -y mcp-server-for-revit"',
    ]


def send(process: subprocess.Popen, message: Dict[str, Any]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(message) + "\n")
    process.stdin.flush()


def _read_stdout(stream: Any, received: "queue.Queue[str]") -> None:
    """Forward JSON-RPC stdout without letting a blocking readline defeat timeout."""
    for line in iter(stream.readline, ""):
        received.put(line)


def response_for(
    received: "queue.Queue[str]", request_id: int, timeout: int
) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            line = received.get(timeout=min(1, max(0.1, deadline - time.monotonic())))
        except queue.Empty:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if message.get("id") == request_id:
            return message
    raise TimeoutError(f"MCP request {request_id} timed out after {timeout}s")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="只读验证 Windows Revit MCP 链路")
    parser.add_argument("--host", default="YOUR_REVIT_HOST")
    parser.add_argument("--user", default="codex")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args(argv)

    process = subprocess.Popen(
        ssh_command(args.user, args.host), text=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace",
    )
    responses: Dict[int, Any] = {}
    received: "queue.Queue[str]" = queue.Queue()
    assert process.stdout is not None
    reader = threading.Thread(target=_read_stdout, args=(process.stdout, received), daemon=True)
    reader.start()
    stderr = ""
    try:
        send(process, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "multica-arch-studio-smoke", "version": "1"}},
        })
        responses[1] = response_for(received, 1, args.timeout)
        send(process, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        for index, probe in enumerate(READ_ONLY_PROBES, 2):
            send(process, {"jsonrpc": "2.0", "id": index, "method": "tools/call", "params": probe})
            responses[index] = response_for(received, index, args.timeout)
    except (OSError, TimeoutError) as exc:
        responses["error"] = str(exc)
    finally:
        process.terminate()
        try:
            _stdout, stderr = process.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            _stdout, stderr = process.communicate()

    payload = {"host": args.host, "user": args.user, "read_only": True,
               "responses": responses, "server_stderr": (stderr or "").strip()}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    succeeded = all(
        response.get("result", {}).get("content")
        for response in (responses.get(2, {}), responses.get(3, {}))
    )
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
