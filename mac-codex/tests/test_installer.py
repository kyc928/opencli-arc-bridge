"""Exercise real installer commands against disposable Codex homes."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.setup = self.root / "setup"
        shutil.copytree(SOURCE, self.setup, ignore=shutil.ignore_patterns(".local", "__pycache__"))
        self.home = self.root / "codex-home"
        self.home.mkdir()

    def run_installer(self, *args, success=True):
        result = subprocess.run([sys.executable, str(self.setup / "scripts/install.py"),
                                 "--codex-home", str(self.home), "--skip-tools", *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def manifest(self):
        manifests = list((self.setup / ".local/backups").glob("*/manifest.json"))
        self.assertEqual(len(manifests), 1)
        return manifests[0]

    def test_dry_run_writes_nothing(self):
        self.run_installer()
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse((self.setup / ".local").exists())

    def test_apply_repeat_and_restore_preserve_unrelated_data(self):
        original = b"# Existing preferences\n\nKeep my formatting.\n"
        agents = self.home / "AGENTS.md"
        agents.write_bytes(original)
        agents.chmod(0o640)
        unrelated = self.home / "config.toml"
        unrelated.write_bytes(b'custom = "untouched"\n')
        self.run_installer("--apply")
        self.assertTrue(agents.read_bytes().startswith(original))
        self.assertEqual(agents.stat().st_mode & 0o777, 0o640)
        installed = agents.read_bytes()
        self.run_installer("--apply")
        self.assertEqual(agents.read_bytes(), installed)
        self.run_installer("--restore", str(self.manifest()))
        self.assertEqual(agents.read_bytes(), original)
        self.assertEqual(agents.stat().st_mode & 0o777, 0o640)
        self.assertEqual(unrelated.read_bytes(), b'custom = "untouched"\n')
        self.assertFalse((self.home / "skills/mac-tools/SKILL.md").exists())

    def test_restore_refuses_edits_before_changing_any_file(self):
        self.run_installer("--apply")
        agents = self.home / "AGENTS.md"
        agents.write_text(agents.read_text() + "User edit\n")
        before = {str(p.relative_to(self.home)): p.read_bytes()
                  for p in self.home.rglob("*") if p.is_file()}
        self.run_installer("--restore", str(self.manifest()), success=False)
        after = {str(p.relative_to(self.home)): p.read_bytes()
                 for p in self.home.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_existing_independent_skill_is_preserved(self):
        skill = self.home / "skills/mac-tools/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("My independent skill\n")
        self.run_installer("--apply", success=False)
        self.assertEqual(skill.read_text(), "My independent skill\n")
        self.assertFalse((self.home / "AGENTS.md").exists())

    def test_symlink_destination_is_refused(self):
        external = self.root / "external"
        external.mkdir()
        (self.home / "skills").symlink_to(external, target_is_directory=True)
        self.run_installer("--apply", success=False)
        self.assertEqual(list(external.iterdir()), [])
        self.assertFalse((self.home / "AGENTS.md").exists())

    def test_override_guidance_is_preserved(self):
        override = self.home / "AGENTS.override.md"
        override.write_text("Existing override\n")
        self.run_installer("--apply", success=False)
        self.assertEqual(override.read_text(), "Existing override\n")
        self.assertFalse((self.home / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
