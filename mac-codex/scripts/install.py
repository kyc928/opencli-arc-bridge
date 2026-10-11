#!/usr/bin/env python3
"""Install the reviewed Codex setup; default to a read-only plan."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- codex-mac-setup:begin -->"
END = "<!-- codex-mac-setup:end -->"
FORMULAE = {
    "git": "git", "gh": "gh", "ripgrep": "rg", "fd": "fd",
    "jq": "jq", "yq": "yq", "shellcheck": "shellcheck", "shfmt": "shfmt",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def ensure_destination(path, codex_home):
    if not path.is_relative_to(codex_home):
        raise ValueError(f"Destination is outside the selected Codex home: {path}")
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError(f"Refusing to write through symlink: {parent}")
        if parent == codex_home:
            break


def atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        f.write(data)
    try:
        temporary.chmod(mode)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def formulae():
    result = []
    for line in (ROOT / "Brewfile").read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r'brew "([a-z0-9@-]+)"', line)
        if not match or match[1] not in FORMULAE:
            raise ValueError(f"Unexpected Brewfile entry: {line}")
        result.append(match[1])
    return result


def planned_files(codex_home):
    target = codex_home / "AGENTS.md"
    ensure_destination(target, codex_home)
    original = target.read_bytes().decode("utf-8") if target.exists() else ""
    snippet = (ROOT / "guidance/AGENTS.md").read_text().rstrip()
    block = f"{BEGIN}\n{snippet}\n{END}"
    if original.count(BEGIN) != original.count(END) or original.count(BEGIN) > 1:
        raise ValueError("Global guidance has ambiguous setup markers; review it manually.")
    if BEGIN in original:
        start, end_start = original.index(BEGIN), original.index(END)
        if end_start < start:
            raise ValueError("Global guidance setup markers are out of order.")
        end = end_start + len(END)
        merged = original[:start] + block + original[end:]
    else:
        merged = original + ("\n\n" if original and not original.endswith("\n\n") else "") + block + "\n"
    files = [(target, merged.encode(), 0o644)]
    for name in ("mac-tools", "agent-improvement"):
        source = ROOT / "skills" / name
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"Missing staged skill: {source}")
        destination = codex_home / "skills" / name
        ensure_destination(destination, codex_home)
        # Existing skills with the same name must be owned by this setup.
        if destination.exists() and not destination.is_dir():
            raise ValueError(f"Skill destination is not a directory: {destination}")
        contains_content = any(not path.is_dir() or path.is_symlink() for path in destination.rglob("*"))
        if contains_content and not (destination / ".codex-mac-setup").is_file():
            raise ValueError(f"Existing independent skill at {destination}; refusing to replace it.")
        for path in sorted(source.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                if path.is_symlink():
                    raise ValueError(f"Staged skill contains a symlink: {path}")
                files.append((destination / path.relative_to(source), path.read_bytes(), 0o644))
        files.append((destination / ".codex-mac-setup", b"Managed by the Codex Mac setup.\n", 0o644))
    for path, _, _ in files:
        ensure_destination(path, codex_home)
    return [(p, data, mode) for p, data, mode in files if not p.exists() or p.read_bytes() != data]


def restore(manifest_path):
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_relative_to(ROOT / ".local" / "backups"):
        raise ValueError("Restore accepts only this setup's local backup manifests.")
    manifest = json.loads(manifest_path.read_text())
    entries = manifest["files"]
    codex_home = Path(manifest["codex_home"])
    for entry in entries:
        path = Path(entry["path"])
        ensure_destination(path, codex_home)
        if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != entry["installed_sha256"]:
            raise ValueError(f"{path} changed after installation; restore stopped without modifying files.")
    for entry in reversed(entries):
        path = Path(entry["path"])
        if entry["backup"] is None:
            path.unlink()
        else:
            data = (manifest_path.parent / entry["backup"]).read_bytes()
            atomic_write(path, data, entry["mode"])
    print("Restored prior guidance and skill files. Homebrew packages are retained.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore", type=Path, metavar="MANIFEST")
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))))
    parser.add_argument("--skip-tools", action="store_true", help="Apply guidance and skills only")
    args = parser.parse_args()
    if args.restore:
        restore(args.restore)
        return
    codex_home = args.codex_home.expanduser().resolve()
    override = codex_home / "AGENTS.override.md"
    if override.exists() and override.read_text().strip():
        raise ValueError(f"{override} overrides global guidance; resolve its scope before installing.")
    changes = planned_files(codex_home)
    for path, _, _ in changes:
        ensure_destination(path, codex_home)
    before = {path: digest(path.read_bytes()) if path.exists() else None for path, _, _ in changes}
    missing = [] if args.skip_tools else [f for f in formulae() if not shutil.which(FORMULAE[f])]
    print("Missing Homebrew tools: " + (", ".join(missing) or "none"))
    for path, _, _ in changes:
        print(f"Write: {path}")
    print("Codex model, permissions, config.toml, hooks, and shell profiles are not edited.")
    if not args.apply:
        print("Dry run. Use --apply to install this plan.")
        return
    if missing:
        brew = shutil.which("brew")
        if not brew:
            raise ValueError("Install Homebrew from https://brew.sh first; no bootstrap was executed.")
        env = dict(os.environ, HOMEBREW_NO_AUTO_UPDATE="1", HOMEBREW_NO_ANALYTICS="1", HOMEBREW_NO_INSTALL_CLEANUP="1")
        subprocess.run([brew, "install", *missing], check=True, env=env)
    for path, _, _ in changes:
        ensure_destination(path, codex_home)
        current = digest(path.read_bytes()) if path.exists() else None
        if path.is_symlink() or current != before[path]:
            raise ValueError(f"{path} changed while installation was running; guidance and skills were not modified.")
    if not changes:
        print("Guidance and skills already match the staged setup.")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup_dir = ROOT / ".local" / "backups" / stamp
    backup_dir.mkdir(parents=True, mode=0o700)
    entries = []
    for index, (path, data, mode) in enumerate(changes):
        backup = None
        if path.exists():
            backup = f"{index}.before"
            mode = path.stat().st_mode & 0o777
            atomic_write(backup_dir / backup, path.read_bytes(), 0o600)
        entries.append({"path": str(path), "backup": backup, "mode": mode, "installed_sha256": digest(data)})
    manifest = backup_dir / "manifest.json"
    atomic_write(manifest, (json.dumps({"codex_home": str(codex_home), "files": entries}, indent=2) + "\n").encode(), 0o600)
    for (path, data, _), entry in zip(changes, entries):
        atomic_write(path, data, entry["mode"])
    print(f"Installed guidance and skills. Backup manifest: {manifest}")
    print("Start a new Codex chat to load global guidance.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
