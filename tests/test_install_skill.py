from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_skill.py"
RUNTIME = ROOT / "tests" / ".evaluation-runtime"


@contextmanager
def local_temp():
    path = RUNTIME / f"install-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


class InstallSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        RUNTIME.mkdir(parents=True, exist_ok=True)

    def command(self, target: Path, action: str, *extra: str):
        return subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                "--scope",
                "repository",
                "--target",
                str(target),
                "--action",
                action,
                *extra,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def test_install_check_and_uninstall(self) -> None:
        with local_temp() as temp:
            repository = Path(temp) / "consumer"
            repository.mkdir()
            destination = (
                repository / ".codex" / "skills" / "reproduce-research-paper"
            )
            installed = self.command(repository, "install")
            self.assertEqual(
                installed.returncode, 0, installed.stdout + installed.stderr
            )
            self.assertTrue((destination / "SKILL.md").is_file())
            manifest = json.loads(
                (destination / ".codex-install-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(manifest["files"])
            checked = self.command(repository, "check")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            state = json.loads(checked.stdout)
            self.assertEqual(state["integrity"], "valid")
            uninstalled = self.command(repository, "uninstall")
            self.assertEqual(
                uninstalled.returncode, 0, uninstalled.stdout + uninstalled.stderr
            )
            self.assertFalse(destination.exists())

    def test_local_change_blocks_update_and_uninstall(self) -> None:
        with local_temp() as temp:
            repository = Path(temp) / "consumer"
            repository.mkdir()
            installed = self.command(repository, "install")
            self.assertEqual(
                installed.returncode, 0, installed.stdout + installed.stderr
            )
            destination = (
                repository / ".codex" / "skills" / "reproduce-research-paper"
            )
            skill = destination / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8") + "\nlocal change\n",
                encoding="utf-8",
            )
            updated = self.command(repository, "update")
            self.assertNotEqual(updated.returncode, 0)
            self.assertIn("local changes", updated.stderr)
            uninstalled = self.command(repository, "uninstall")
            self.assertNotEqual(uninstalled.returncode, 0)
            self.assertTrue(skill.is_file())
            forced = self.command(repository, "uninstall", "--force")
            self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
