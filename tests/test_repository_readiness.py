import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "reproduce-research-paper"
    / "scripts"
    / "assess_repository_readiness.py"
)
RUNTIME = ROOT / "tests" / ".readiness-runtime"


def run_tool(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(SCRIPT), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class RepositoryReadinessTests(unittest.TestCase):
    def setUp(self):
        RUNTIME.mkdir(parents=True, exist_ok=True)
        self.case_root = RUNTIME / f"case-{uuid.uuid4().hex}"
        self.repository = self.case_root / "repository"
        self.repository.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(self.case_root, ignore_errors=True))

    def write(self, relative: str, content: str = "placeholder\n") -> None:
        path = self.repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def signals_by_id(self, payload: dict) -> dict:
        return {signal["id"]: signal for signal in payload["signals"]}

    def test_populated_repository_reports_present_signals_with_evidence(self):
        self.write("requirements.txt", "numpy==2.0.0\n")
        self.write("poetry.lock")
        self.write("LICENSE", "MIT\n")
        self.write("README.md", "# Demo\n\n```bash\npython train.py\n```\n")
        self.write("tests/test_model.py", "def test_ok():\n    assert True\n")
        self.write(".github/workflows/ci.yml", "on: push\n")
        self.write("Dockerfile", "FROM python:3.12\n")
        self.write("configs/train.yaml", "epochs: 3\n")
        self.write("CITATION.cff", "cff-version: 1.2.0\n")
        self.write("train.py", "def main(seed=7):\n    return seed\n")
        output = self.case_root / "readiness.json"
        result = run_tool(
            "--repository", str(self.repository), "--output", str(output)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(output.read_text(encoding="utf-8"))
        signals = self.signals_by_id(payload)
        for expected_present in (
            "dependency_declaration",
            "pinned_environment",
            "license_statement",
            "run_instructions",
            "automated_tests",
            "continuous_integration",
            "containerized_environment",
            "experiment_configuration",
            "citation_metadata",
            "seed_control_mentions",
        ):
            with self.subTest(signal=expected_present):
                self.assertTrue(signals[expected_present]["present"])
                self.assertTrue(signals[expected_present]["evidence"])
        for path in signals["dependency_declaration"]["evidence"]:
            self.assertNotIn("\\", path)
        self.assertEqual(payload["signals_total"], len(payload["signals"]))
        self.assertEqual(
            payload["signals_present"],
            sum(signal["present"] for signal in payload["signals"]),
        )
        self.assertFalse(payload["scan"]["truncated"])

    def test_empty_repository_reports_absent_signals_without_failing(self):
        result = run_tool("--repository", str(self.repository))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["signals_present"], 0)
        self.assertTrue(all(not signal["present"] for signal in payload["signals"]))
        self.assertTrue(all(signal["evidence"] == [] for signal in payload["signals"]))
        self.assertIn("not proof of absence", payload["interpretation"])
        self.assertIn("never a reproduction status", payload["interpretation"])

    def test_missing_repository_is_rejected(self):
        result = run_tool("--repository", str(self.repository / "does-not-exist"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a directory", result.stderr)

    def test_seed_scan_ignores_prose_and_respects_word_boundaries(self):
        self.write("notes.md", "We seed every run.\n")
        self.write("model.py", "self.seedling = 1\nRESEEDED = 2\n")
        result = run_tool("--repository", str(self.repository))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(self.signals_by_id(payload)["seed_control_mentions"]["present"])
        self.write("run.py", "parser.add_argument('--seed', type=int)\n")
        rerun = run_tool("--repository", str(self.repository))
        payload = json.loads(rerun.stdout)
        signal = self.signals_by_id(payload)["seed_control_mentions"]
        self.assertTrue(signal["present"])
        self.assertEqual(signal["evidence"], ["run.py"])

    def test_scan_is_bounded_and_reports_truncation(self):
        for index in range(12):
            self.write(f"src/module_{index:02d}.py")
        result = run_tool("--repository", str(self.repository), "--max-files", "5")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["scan"]["truncated"])
        self.assertEqual(payload["scan"]["files_scanned"], 5)

    def test_symlinked_files_are_not_scanned(self):
        outside = self.case_root / "outside"
        outside.mkdir()
        target = outside / "LICENSE"
        target.write_text("MIT\n", encoding="utf-8")
        try:
            os.symlink(target, self.repository / "LICENSE")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform")
        result = run_tool("--repository", str(self.repository))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(self.signals_by_id(payload)["license_statement"]["present"])


if __name__ == "__main__":
    unittest.main()
