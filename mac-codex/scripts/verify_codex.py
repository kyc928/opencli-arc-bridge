#!/usr/bin/env python3
"""Verify skill discovery without starting a model turn or creating a chat."""

import argparse
import json
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"mac-tools", "agent-improvement"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills", nargs="+", default=sorted(EXPECTED))
    expected = set(parser.parse_args().skills)
    codex = shutil.which("codex")
    if not codex:
        raise SystemExit("Codex executable is missing from PATH.")
    with subprocess.Popen([codex, "app-server"], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          text=True, bufsize=1) as process:
        responses = queue.Queue()

        def read_responses():
            for line in process.stdout:
                try:
                    responses.put(json.loads(line))
                except json.JSONDecodeError:
                    continue
            responses.put(None)

        threading.Thread(target=read_responses, daemon=True).start()

        def send(value):
            process.stdin.write(json.dumps(value) + "\n")
            process.stdin.flush()

        def response(request_id):
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    item = responses.get(timeout=max(0.01, deadline - time.monotonic()))
                except queue.Empty:
                    break
                if item is None:
                    raise RuntimeError("Codex app-server closed before verification completed.")
                if item.get("id") == request_id:
                    if "error" in item:
                        raise RuntimeError(f"Codex app-server rejected request {request_id}.")
                    return item["result"]
            raise RuntimeError("Timed out checking Codex skill discovery.")

        try:
            send({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "codex_mac_setup_check", "version": "1.0.0"}}})
            response(1)
            send({"method": "initialized", "params": {}})
            send({"id": 2, "method": "skills/list", "params": {
                "cwds": [str(ROOT)], "forceReload": True}})
            result = response(2)
            found = {}
            for group in result.get("data", []):
                for skill in group.get("skills", []):
                    if skill.get("name") in expected:
                        found[skill["name"]] = skill
            for name in sorted(expected):
                skill = found.get(name)
                if not skill or not skill.get("enabled", False):
                    raise RuntimeError(f"{name} is not discoverable and enabled in Codex.")
                print(f"Codex loaded: {name} ({skill.get('path', 'path unavailable')})")
            print(f"All {len(expected)} requested skills are discoverable and enabled.")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as exc:
        raise SystemExit(str(exc))
