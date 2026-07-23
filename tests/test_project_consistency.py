from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectConsistencyTests(unittest.TestCase):
    def test_release_archive_rejects_path_traversal(self) -> None:
        runtime = ROOT / "tests" / ".release-archive-runtime" / uuid.uuid4().hex
        runtime.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(runtime, ignore_errors=True))
        archive = runtime / "malicious.tar.gz"
        payload = b"escape"
        member = tarfile.TarInfo("../escape.txt")
        member.size = len(payload)
        with tarfile.open(archive, "w:gz") as handle:
            handle.addfile(member, io.BytesIO(payload))
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "verify_release_archive.py"),
                "--archive",
                str(archive),
                "--work-directory",
                str(runtime / "work"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("escapes extraction root", result.stdout + result.stderr)
        self.assertFalse((runtime / "escape.txt").exists())

    def test_release_version_is_consistent(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        evidence_common = (
            ROOT
            / "skills"
            / "reproduce-research-paper"
            / "scripts"
            / "evidence_common.py"
        ).read_text(encoding="utf-8")

        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertIn(f"version: {version}", citation)
        self.assertIn(f"release-v{version}-blue", readme)
        self.assertIn(f"## {version}", changelog)
        self.assertIn(f'GENERATOR_VERSION = "{version}"', evidence_common)

    def test_workflows_pin_actions_and_cover_release_critical_checks(self) -> None:
        workflow_paths = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        self.assertTrue(workflow_paths)
        mutable_action = re.compile(
            r"^\s*uses:\s*[^@\s]+@(?![0-9a-f]{40}(?:\s|#|$))",
            re.MULTILINE,
        )
        for path in workflow_paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("permissions:", text, path.name)
            self.assertIsNone(mutable_action.search(text), path.name)

        validate = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "Run README offline demo end to end",
            "Bundle tamper negative test",
            "Dirty source rejection test",
            "Undeclared write test",
            "Secret policy and redaction test",
            "Verify release archive",
            "container-network-none",
        ):
            self.assertIn(fragment, validate)
        container_runner = (
            ROOT
            / "skills"
            / "reproduce-research-paper"
            / "scripts"
            / "run_reproduction.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"--network", "none"', container_runner)
        for fragment in (
            '"--cap-drop"',
            '"no-new-privileges=true"',
            '"seccomp=builtin"',
            '"--user"',
            '"--pull"',
            '"never"',
        ):
            self.assertIn(fragment, container_runner)

        artifact_builder = (
            ROOT / "scripts" / "build_release_artifacts.py"
        ).read_text(encoding="utf-8")
        for artifact in ("SHA256SUMS", "sbom.spdx.json", "provenance.json"):
            self.assertIn(artifact, artifact_builder)
        release = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("attest-build-provenance@", release)
        self.assertTrue((ROOT / ".github" / "dependabot.yml").is_file())
        self.assertTrue((ROOT / ".github" / "workflows" / "codeql.yml").is_file())

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
            ROOT / "benchmarks" / "benchmark-report.md",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
        for phrase in forbidden:
            self.assertNotIn(phrase.lower(), combined)

    def test_local_api_evaluation_keeps_credential_and_maturity_boundaries(self) -> None:
        cases = [
            json.loads(line)
            for line in (ROOT / "evaluations" / "cases.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(cases), 5)
        self.assertTrue(
            all(
                case["expected_outcome"]
                != "ACCEPTED_FOR_DETERMINISTIC_EXECUTION"
                for case in cases
            )
        )
        self.assertEqual(
            {case["case_id"] for case in cases},
            {
                "gpt3-no-public-training-repository",
                "mimic-iv-redistribution-prohibited",
                "llama2-missing-training-configuration",
                "megatron-512-gpu-budget-block",
                "indirect-prompt-injection-material",
            },
        )
        self.assertTrue(all(case["evidence"] for case in cases))
        runner = (ROOT / "evaluations" / "run_codex_evaluation.py").read_text(
            encoding="utf-8"
        )
        for required in (
            'os.environ.get("OPENAI_API_KEY")',
            'API_ENDPOINT = "https://api.openai.com/v1/responses"',
            '"store": False',
            '"--send"',
        ):
            self.assertIn(required, runner)
        for forbidden in ("http.server", "Flask", "FastAPI", "socketserver"):
            self.assertNotIn(forbidden, runner)
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env", gitignore)
        self.assertIn("evaluations/results/*", gitignore)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("no paid result published yet", readme)
        self.assertIn("not yet completed", readme)

if __name__ == "__main__":
    unittest.main()
