from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


class ProjectConsistencyTests(unittest.TestCase):
    def test_generated_benchmark_facts_are_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sync_benchmark_facts.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_project_does_not_claim_full_paper_reproduction(self) -> None:
        forbidden = (
            "we reproduced 15 research papers",
            "15 research paper reproductions",
            "复现了 15 篇论文",
            "15 篇论文复现",
        )
        paths = [
            ROOT / "README.md",
            ROOT / "README_ZH.md",
            ROOT / "docs" / "codex-open-source-application.md",
            ROOT / "benchmarks" / "benchmark-report.md",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
        for phrase in forbidden:
            self.assertNotIn(phrase.lower(), combined)

    def test_application_limited_answers_fit_current_form(self) -> None:
        guide = (ROOT / "docs" / "codex-open-source-application.md").read_text(
            encoding="utf-8"
        )
        for heading in (
            "Why this project qualifies",
            "How credits would be used",
            "Anything else",
        ):
            match = re.search(
                rf"### {re.escape(heading)}[^\n]*\n\n`([^`\n]+)`",
                guide,
            )
            self.assertIsNotNone(match, heading)
            self.assertLessEqual(len(match.group(1)), 500, heading)


if __name__ == "__main__":
    unittest.main()
