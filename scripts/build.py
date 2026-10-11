#!/usr/bin/env python3
"""Build and test a pinned upstream release with the Arc compatibility patch."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REF = "8271afc67e8504bda94c147f446ee29775d08274"


def run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True)


def checksums(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def main():
    for tool in ("git", "node", "npm"):
        if not shutil.which(tool):
            raise SystemExit(f"Required tool missing: {tool}")
    output = ROOT / "build"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="opencli-arc-") as temp:
        source = Path(temp) / "upstream"
        run("git", "clone", "--no-checkout", "https://github.com/jackwener/OpenCLI.git", str(source), cwd=ROOT)
        run("git", "checkout", "--detach", REF, cwd=source)
        run("git", "apply", "--check", str(ROOT / "patches/arc-compat.patch"), cwd=source)
        run("git", "apply", str(ROOT / "patches/arc-compat.patch"), cwd=source)
        run("npm", "ci", "--ignore-scripts", cwd=source)
        ext = source / "extension"
        run("npm", "ci", "--ignore-scripts", cwd=ext)
        run("node", "node_modules/vitest/vitest.mjs", "run", "--project", "extension", cwd=source)
        run("node", "node_modules/typescript/bin/tsc", "--noEmit", "--target", "ES2022",
            "--module", "ESNext", "--moduleResolution", "bundler", "--strict",
            "--esModuleInterop", "--skipLibCheck", "--types", "chrome", "src/background.ts", cwd=ext)
        run("npm", "run", "build", cwd=ext)
        # Package into a new temporary directory before replacing previous output.
        package = Path(temp) / "extension"
        run("node", "extension/scripts/package-release.mjs", "--out", str(package), cwd=source)
        shutil.copy2(source / "LICENSE", package / "LICENSE")
        shutil.copy2(ROOT / "NOTICE", package / "NOTICE")
        manifest_path = package / "manifest.json"
        official = json.loads(manifest_path.read_text())
        manifest = dict(official)
        manifest.update(name="OpenCLI — Arc compatibility", version_name="1.0.24 + Arc compatibility 1")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        for field in ("permissions", "host_permissions", "content_security_policy"):
            assert manifest[field] == official[field], f"Unexpected permission change: {field}"
        worker = package / "dist/background.js"
        worker.write_text("// Modified for OpenCLI Arc compatibility; see patches/arc-compat.patch.\n" + worker.read_text())
        destination = output / "extension"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(package, destination)
    metadata = {"source": "https://github.com/jackwener/OpenCLI", "source_ref": REF,
                "patch_sha256": hashlib.sha256((ROOT / "patches/arc-compat.patch").read_bytes()).hexdigest(),
                "files": checksums(destination)}
    (output / "provenance.json").write_text(json.dumps(metadata, indent=2) + "\n")
    archive = output / "opencli-arc-bridge-v1.0.24-arc.1.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for file in sorted(destination.rglob("*")):
            if file.is_file():
                zipped.write(file, Path("extension") / file.relative_to(destination))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
    print(f"Built and tested: {archive}")


if __name__ == "__main__":
    main()
