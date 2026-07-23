import json
import subprocess
import sys
import uuid
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "reproduce-research-paper"
SCRIPTS = SKILL / "scripts"
EXAMPLES = SKILL / "assets" / "examples"
RUNTIME = ROOT / "tests" / ".reproduce-runtime"
PAPER_CONTEXT = {
    "research_question": "Can a toy command reproduce one declared metric?",
    "method": "Run a deterministic toy script.",
    "data_and_splits": "Fixed synthetic test split.",
    "training_or_inference": "Run once without tuning.",
    "evaluation_protocol": "Read one JSON metric from standard output.",
    "limitations": "Fixture only; not a scientific result.",
}


class ReproduceResearchPaperTests(unittest.TestCase):
    def setUp(self):
        RUNTIME.mkdir(parents=True, exist_ok=True)

    def runtime_path(self, suffix):
        path = RUNTIME / f"reproduce-{uuid.uuid4().hex}-{suffix}"
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def run_script(self, name, *args, expect=0):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPTS / name), *map(str, args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, expect, result.stderr + result.stdout)
        return result

    def test_example_plan_validates_and_previews_without_execution(self):
        plan = EXAMPLES / "reproduction-plan.json"
        result = self.run_script("validate_reproduction_plan.py", "--plan", plan)
        self.assertTrue(json.loads(result.stdout)["valid"])
        preview = self.run_script(
            "run_reproduction.py", "--plan", plan, "--output", RUNTIME
        )
        payload = json.loads(preview.stdout)
        self.assertEqual(payload["mode"], "preview")
        self.assertEqual(payload["commands"][0]["argv"], ["python", "run_experiment.py"])

    def test_inventory_compare_and_report_example(self):
        plan = EXAMPLES / "reproduction-plan.json"
        observed = EXAMPLES / "observed-metrics.json"
        inventory = self.runtime_path("inventory.json")
        comparison = self.runtime_path("comparison.json")
        report = self.runtime_path("report.md")
        self.run_script(
            "inventory_artifacts.py", "--repository", EXAMPLES / "toy-repository", "--output", inventory
        )
        comparison_result = self.run_script(
            "compare_metrics.py", "--plan", plan, "--observed", observed, "--output", comparison
        )
        self.assertEqual(json.loads(comparison_result.stdout or comparison.read_text(encoding="utf-8"))["summary"]["verified"], 1)
        self.run_script(
            "build_report.py", "--plan", plan, "--inventory", inventory,
            "--comparison", comparison, "--output", report
        )
        text = report.read_text(encoding="utf-8")
        self.assertIn("`PARTIAL`", text)
        self.assertIn("table-1-accuracy", text)

    def test_execute_creates_logs_and_verified_report(self):
        source_repository = EXAMPLES / "toy-repository"
        for name in ("smoke-experiment.stdout.log", "smoke-experiment.stderr.log", "run-record.json"):
            path = RUNTIME / name
            path.unlink(missing_ok=True)
            self.addCleanup(path.unlink, missing_ok=True)
        plan = json.loads((EXAMPLES / "reproduction-plan.json").read_text(encoding="utf-8"))
        plan["repository"] = str(source_repository)
        plan["commands"][0]["argv"][0] = sys.executable
        plan_path = self.runtime_path("plan.json")
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        self.run_script("run_reproduction.py", "--plan", plan_path, "--output", RUNTIME, "--execute")
        self.assertIn("test_accuracy", (RUNTIME / "smoke-experiment.stdout.log").read_text(encoding="utf-8"))
        inventory = self.runtime_path("execute-inventory.json")
        comparison = self.runtime_path("execute-comparison.json")
        report = self.runtime_path("execute-report.md")
        self.run_script("inventory_artifacts.py", "--repository", source_repository, "--output", inventory)
        self.run_script("compare_metrics.py", "--plan", plan_path, "--observed", EXAMPLES / "observed-metrics.json", "--output", comparison)
        self.run_script(
            "build_report.py", "--plan", plan_path, "--inventory", inventory, "--comparison", comparison,
            "--run-record", RUNTIME / "run-record.json", "--output", report
        )
        self.assertIn("`VERIFIED`", report.read_text(encoding="utf-8"))

    def test_plan_rejects_shell_and_secret_like_keys(self):
        plan = {
            "repository": str(EXAMPLES / "toy-repository"),
            "paper_context": PAPER_CONTEXT,
            "commands": [{"id": "unsafe", "command": "python x.py", "argv": ["python", "x.py"], "timeout_seconds": 30}],
            "claims": [{"id": "c1", "paper_location": "p. 1", "metric": "score", "expected": 1, "tolerance": {"absolute": 0}, "protocol": "one fixed evaluation", "command_ids": ["unsafe"], "evidence_output": "stdout score"}],
            "api_key": "must-not-be-here",
        }
        path = self.runtime_path("unsafe-plan.json")
        path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.run_script("validate_reproduction_plan.py", "--plan", path, expect=1)
        self.assertIn("shell command strings", result.stdout)
        self.assertIn("secret-like keys", result.stdout)
        self.assertNotIn("must-not-be-here", result.stdout)

    def test_runner_redacts_secret_like_command_output(self):
        for name in ("redaction.stdout.log", "redaction.stderr.log", "run-record.json"):
            path = RUNTIME / name
            path.unlink(missing_ok=True)
            self.addCleanup(path.unlink, missing_ok=True)
        plan = {
            "repository": str(EXAMPLES / "toy-repository"),
            "paper_context": PAPER_CONTEXT,
            "commands": [{"id": "redaction", "argv": [sys.executable, "-c", "print('token=super-secret-value')"], "timeout_seconds": 30}],
            "claims": [{"id": "c1", "paper_location": "p. 1", "metric": "score", "expected": 1, "tolerance": {"absolute": 0}, "protocol": "one fixed evaluation", "command_ids": ["redaction"], "evidence_output": "stdout score"}],
        }
        path = self.runtime_path("redaction-plan.json")
        path.write_text(json.dumps(plan), encoding="utf-8")
        self.run_script("run_reproduction.py", "--plan", path, "--output", RUNTIME, "--execute")
        log = (RUNTIME / "redaction.stdout.log").read_text(encoding="utf-8")
        self.assertIn("[REDACTED]", log)
        self.assertNotIn("super-secret-value", log)

    def test_plan_requires_whole_paper_context_and_safe_command_id(self):
        plan = {
            "repository": str(EXAMPLES / "toy-repository"),
            "commands": [{"id": "../escape", "argv": ["python", "run_experiment.py"], "timeout_seconds": 30}],
            "claims": [{"id": "c1", "paper_location": "p. 1", "metric": "score", "expected": 1, "tolerance": {"absolute": 0}}],
        }
        path = self.runtime_path("unsafe-plan.json")
        path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.run_script("validate_reproduction_plan.py", "--plan", path, expect=1)
        self.assertIn("paper_context must summarize", result.stdout)
        self.assertIn("commands[1].id must match", result.stdout)

    def test_report_refuses_verified_status_for_mismatched_plan_evidence(self):
        source_repository = EXAMPLES / "toy-repository"
        for name in ("smoke-experiment.stdout.log", "smoke-experiment.stderr.log", "run-record.json"):
            path = RUNTIME / name
            path.unlink(missing_ok=True)
            self.addCleanup(path.unlink, missing_ok=True)
        plan = json.loads((EXAMPLES / "reproduction-plan.json").read_text(encoding="utf-8"))
        plan["repository"] = str(source_repository)
        plan["commands"][0]["argv"][0] = sys.executable
        original_plan = self.runtime_path("original-plan.json")
        original_plan.write_text(json.dumps(plan), encoding="utf-8")
        self.run_script("run_reproduction.py", "--plan", original_plan, "--output", RUNTIME, "--execute")
        comparison = self.runtime_path("comparison.json")
        self.run_script("compare_metrics.py", "--plan", original_plan, "--observed", EXAMPLES / "observed-metrics.json", "--output", comparison)
        altered = json.loads(json.dumps(plan))
        altered["claims"][0]["expected"] = 0.91
        altered_plan = self.runtime_path("altered-plan.json")
        altered_plan.write_text(json.dumps(altered), encoding="utf-8")
        inventory = self.runtime_path("inventory.json")
        report = self.runtime_path("mismatched-report.md")
        self.run_script("inventory_artifacts.py", "--repository", source_repository, "--output", inventory)
        self.run_script(
            "build_report.py", "--plan", altered_plan, "--inventory", inventory, "--comparison", comparison,
            "--run-record", RUNTIME / "run-record.json", "--output", report
        )
        text = report.read_text(encoding="utf-8")
        self.assertIn("`PARTIAL`", text)
        self.assertIn("Evidence integrity warning", text)

    def test_missing_observation_is_blocked(self):
        plan = EXAMPLES / "reproduction-plan.json"
        observed = self.runtime_path("observed.json")
        observed.write_text("{}", encoding="utf-8")
        result = self.run_script("compare_metrics.py", "--plan", plan, "--observed", observed)
        self.assertEqual(json.loads(result.stdout)["summary"]["blocked"], 1)


if __name__ == "__main__":
    unittest.main()
