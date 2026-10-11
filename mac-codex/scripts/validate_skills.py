#!/usr/bin/env python3
"""Run Codex's skill validator for this setup's two skills."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
validator = codex_home / "skills/.system/skill-creator/scripts/quick_validate.py"
if not validator.is_file():
    raise SystemExit(f"Codex skill validator is unavailable at {validator}")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("paths", nargs="*", type=Path)
paths = parser.parse_args().paths or [root / "skills" / name for name in ("mac-tools", "agent-improvement")]
for path in paths:
    print(f"Validating {path.name}", flush=True)
    subprocess.run([sys.executable, str(validator), str(path)], check=True)
