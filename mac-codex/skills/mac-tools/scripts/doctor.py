#!/usr/bin/env python3
"""Read-only baseline tool discovery and version probes for this Mac."""

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess


BASELINE = (
    "brew", "codex", "git", "gh", "rg", "fd", "jq", "yq", "node", "npm",
    "python3", "uv", "shellcheck", "shfmt",
)
TIMEOUT_SECONDS = 4
VERSION_PATTERN = re.compile(r"(?<![\w.])v?(\d+(?:\.\d+)+(?:[-+][A-Za-z0-9.-]+)?)")
VERSION_LINE_PATTERNS = {
    "brew": r"^Homebrew\s+",
    "codex": r"^codex(?:-cli)?\s+",
    "git": r"^git version\s+",
    "gh": r"^gh version\s+",
    "rg": r"^ripgrep\s+",
    "fd": r"^fd\s+",
    "jq": r"^jq-",
    "yq": r"^yq(?:\s|\()",
    "node": r"^v?\d+\.",
    "npm": r"^\d+\.",
    "python3": r"^Python\s+",
    "uv": r"^uv\s+",
    "shellcheck": r"^version:\s+",
    "shfmt": r"^v?\d+\.",
}


def find_executable(name):
    """Prefer the current PATH; report conventional fallback locations separately."""
    on_path = shutil.which(name)
    if on_path:
        return str(Path(on_path).absolute()), True
    directories = (
        Path("/opt/homebrew/bin"), Path("/opt/homebrew/sbin"),
        Path("/usr/local/bin"), Path("/usr/bin"), Path("/bin"),
        Path("/usr/sbin"), Path("/sbin"), Path.home() / ".local/bin",
    )
    for directory in directories:
        candidate = directory / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate), False
    return None, False


def run_probe(argv):
    # Version commands only. Discard unrelated stderr instead of exposing logs.
    probe_environment = os.environ.copy()
    probe_environment.update({
        "HOMEBREW_NO_AUTO_UPDATE": "1",
        "HOMEBREW_NO_ANALYTICS": "1",
        "NO_COLOR": "1",
    })
    try:
        completed = subprocess.run(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, errors="replace",
            timeout=TIMEOUT_SECONDS, check=False, env=probe_environment,
        )
    except subprocess.TimeoutExpired:
        return "timed_out", None, None
    except OSError:
        return "probe_failed", None, None
    if completed.returncode:
        return "probe_failed", None, completed.returncode
    # Some tools print their version on stderr. Only an identified version line
    # is consumed; neither stream is forwarded to the report.
    return "ok", completed.stdout + "\n" + completed.stderr, 0


def check_tool(name):
    executable, on_path = find_executable(name)
    result = {"name": name, "path": executable, "on_path": on_path}
    if executable is None:
        return dict(result, status="missing", version=None)
    status, output, returncode = run_probe([executable, "--version"])
    if status != "ok":
        return dict(result, status=status, version=None, returncode=returncode)
    line_pattern = re.compile(VERSION_LINE_PATTERNS[name], re.IGNORECASE)
    for line in output.splitlines():
        if line_pattern.search(line.strip()):
            match = VERSION_PATTERN.search(line)
            if match:
                return dict(result, status="ok" if on_path else "off_path",
                            version=match.group(1))
    return dict(result, status="version_unrecognized", version=None)


def check_developer_directory():
    executable, on_path = find_executable("xcode-select")
    result = {"name": "xcode-select", "path": executable, "on_path": on_path}
    if executable is None:
        return dict(result, status="missing", active_developer_directory=None)
    status, output, returncode = run_probe([executable, "-p"])
    if status != "ok":
        return dict(result, status=status, active_developer_directory=None,
                    returncode=returncode)
    # Only report the expected absolute directory, never diagnostic stderr.
    directory = output.splitlines()[0].strip() if output.splitlines() else ""
    if not directory.startswith("/"):
        return dict(result, status="directory_unrecognized",
                    active_developer_directory=None)
    return dict(result, status="ok", active_developer_directory=directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    arguments = parser.parse_args()
    tools = [check_tool(name) for name in BASELINE]
    developer_directory = check_developer_directory()
    needs_attention = [tool["name"] for tool in tools if tool["status"] != "ok"]
    report = {
        "schema_version": 1,
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "tools": tools,
        "xcode_select": developer_directory,
        "baseline_ready": not needs_attention,
        "baseline_needs_attention": needs_attention,
    }
    if arguments.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Platform: {report['platform']['system']} {report['platform']['machine']}")
        for tool in tools:
            details = tool["path"] or "not found"
            if tool["version"]:
                details = f"{tool['version']} | {details}"
            print(f"{tool['name']:10} {tool['status']:20} {details}")
        directory = developer_directory.get("active_developer_directory")
        print(f"xcode-select: {developer_directory['status']} | {directory or 'unavailable'}")
        if needs_attention:
            print("Baseline needs attention: " + ", ".join(needs_attention))
        else:
            print("Baseline ready.")
    return 1 if needs_attention else 0


if __name__ == "__main__":
    raise SystemExit(main())
