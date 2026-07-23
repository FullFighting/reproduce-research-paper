import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "reproduce-research-paper"
SCRIPTS = SKILL / "scripts"
EXAMPLES = SKILL / "assets" / "examples"
RUNTIME = ROOT / "tests" / ".reproduce-runtime"
REPRODUCED = "CLAIM_REPRODUCED_WITHIN_TOLERANCE"


PAPER_CONTEXT = {
    "research_question": "Can a declared computation reproduce one paper value?",
    "method": "Run a deterministic public computation.",
    "data_and_splits": "Use a fixed public or synthetic fixture without tuning.",
    "training_or_inference": "Execute the declared command once.",
    "evaluation_protocol": "Extract the metric from the recorded command artifact.",
    "limitations": "Test fixture only.",
}


def execution(**overrides):
    value = {
        "workspace_mode": "copy",
        "network": "unrestricted",
        "write_paths": [],
        "max_memory_mb": 512,
        "max_cpu_seconds": 60,
        "max_disk_mb": 32,
        "max_output_files": 50,
        "max_single_file_mb": 8,
        "max_gpus": 0,
        "retain_workspace": False,
        "exclude_paths": {},
    }
    value.update(overrides)
    return value


def claim(observation, **overrides):
    value = {
        "id": "claim-1",
        "paper_location": "Table 1",
        "metric": "score",
        "expected": 0.9,
        "unit": "ratio",
        "protocol": "Run once on the fixed fixture.",
        "command_ids": ["experiment"],
        "observation": observation,
        "comparison": {
            "method": "numeric_tolerance",
            "absolute": 0.02,
            "relative": 0.03,
            "combination": "all",
            "minimum_runs": 1,
            "aggregate": "mean",
            "direction": "two_sided",
        },
    }
    value.update(overrides)
    return value


class ReproduceResearchPaperTests(unittest.TestCase):
    def setUp(self):
        RUNTIME.mkdir(parents=True, exist_ok=True)
        self.case_root = RUNTIME / f"case-{uuid.uuid4().hex}"
        self.repository = self.case_root / "repository"
        self.repository.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(self.case_root, ignore_errors=True))

    def write_program(self, source):
        (self.repository / "experiment.py").write_text(source, encoding="utf-8")

    def make_plan(self, observation=None, **overrides):
        if observation is None:
            observation = {
                "source": "stdout",
                "command_id": "experiment",
                "extractor": "jsonpath",
                "expression": "$.score",
                "unit": "ratio",
            }
        value = {
            "schema_version": 1,
            "repository": str(self.repository),
            "paper": {
                "title": "Test paper",
                "reference": "Test fixture",
                "paper_url": "https://example.org/paper",
                "code_url": "https://example.org/code",
            },
            "paper_context": PAPER_CONTEXT,
            "execution": execution(),
            "commands": [
                {
                    "id": "experiment",
                    "argv": [sys.executable, "experiment.py"],
                    "cwd": ".",
                    "timeout_seconds": 30,
                }
            ],
            "claims": [claim(observation)],
        }
        value.update(overrides)
        plan_path = self.case_root / "plan.json"
        plan_path.write_text(json.dumps(value), encoding="utf-8")
        return value, plan_path

    def run_script(self, name, *args, expect=0, env=None):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPTS / name), *map(str, args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, expect, result.stderr + result.stdout)
        return result

    def execute_bundle(self, plan_path, expect=0):
        bundle = self.case_root / "evidence-bundle"
        self.run_script(
            "run_reproduction.py",
            "--plan",
            plan_path,
            "--output",
            bundle,
            "--execute",
            expect=expect,
        )
        return bundle

    def test_example_plan_validates_and_previews_without_execution(self):
        plan = EXAMPLES / "reproduction-plan.json"
        result = self.run_script("validate_reproduction_plan.py", "--plan", plan)
        self.assertTrue(json.loads(result.stdout)["valid"])
        preview = self.run_script(
            "run_reproduction.py", "--plan", plan, "--output", self.case_root / "preview"
        )
        payload = json.loads(preview.stdout)
        self.assertEqual(payload["mode"], "preview")
        self.assertEqual(payload["commands"][0]["argv"], ["python", "run_experiment.py"])
        self.assertFalse((self.case_root / "preview").exists())

    def test_network_policy_must_be_explicit(self):
        self.write_program("print('{\"score\": 0.9}')\n")
        plan, plan_path = self.make_plan()
        del plan["execution"]["network"]
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.run_script(
            "validate_reproduction_plan.py",
            "--plan",
            plan_path,
            expect=1,
        )
        self.assertIn("execution.network must be explicitly declared", result.stdout)

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links unavailable")
    def test_external_symlink_is_rejected(self):
        self.write_program("print('{\"score\": 0.9}')\n")
        outside = self.case_root / "outside.txt"
        outside.write_text("not part of the research repository", encoding="utf-8")
        link = self.repository / "external.txt"
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symbolic link creation unavailable: {error}")
        _plan, plan_path = self.make_plan()
        result = self.run_script(
            "run_reproduction.py",
            "--plan",
            plan_path,
            "--output",
            self.case_root / "bundle",
            "--execute",
            expect=2,
        )
        self.assertIn("symlinks that escape its root", result.stderr)

    def test_stdout_jsonpath_creates_self_verifying_reproduced_bundle(self):
        self.write_program("import json\nprint(json.dumps({'score': 0.905}))\n")
        _, plan = self.make_plan()
        bundle = self.execute_bundle(plan)
        comparison = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(comparison["claims"][0]["status"], REPRODUCED)
        observation = json.loads((bundle / "observations.json").read_text(encoding="utf-8"))
        item = observation["observations"][0]
        self.assertEqual(item["source_artifact"], "logs/experiment.stdout.log")
        self.assertEqual(item["normalized_value"], 0.905)
        self.assertTrue(item["run_record_sha256"])
        self.assertTrue(item["source_sha256"])
        report = (bundle / "report.md").read_text(encoding="utf-8")
        self.assertIn(f"`{REPRODUCED}`", report)
        verifier = self.run_script("build_report.py", "--bundle", bundle)
        self.assertTrue(json.loads(verifier.stdout)["valid"])
        self.assertFalse((bundle / "workspace").exists())

    def test_handwritten_observed_metrics_interface_is_removed(self):
        self.write_program("print('{\"score\": 0.1}')\n")
        _, plan = self.make_plan()
        fake = self.case_root / "observed-metrics.json"
        fake.write_text('{"score": 0.9}', encoding="utf-8")
        result = self.run_script(
            "compare_metrics.py",
            "--plan",
            plan,
            "--observed",
            fake,
            expect=2,
        )
        self.assertIn("--bundle", result.stderr)

    def test_manual_observation_can_never_be_reproduced(self):
        self.write_program("print('figure created')\n")
        observation = {
            "source": "manual",
            "extractor": "manual",
            "reason": "Figure 2 needs domain-expert visual inspection.",
        }
        _, plan = self.make_plan(observation)
        bundle = self.execute_bundle(plan)
        comparison = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(comparison["claims"][0]["status"], "MANUAL_REVIEW_REQUIRED")
        self.assertNotIn(f"`{REPRODUCED}`", (bundle / "report.md").read_text(encoding="utf-8"))

    def test_tampering_with_log_or_comparison_invalidates_bundle(self):
        self.write_program("print('{\"score\": 0.905}')\n")
        _, plan = self.make_plan()
        bundle = self.execute_bundle(plan)
        log = bundle / "logs" / "experiment.stdout.log"
        log.write_text('{"score": 0.9}\n', encoding="utf-8")
        result = self.run_script("build_report.py", "--bundle", bundle, expect=1)
        self.assertIn("artifact hash mismatch", result.stdout)

    def test_report_recomputes_and_rejects_forged_comparison(self):
        self.write_program("print('{\"score\": 0.5}')\n")
        _, plan = self.make_plan()
        bundle = self.execute_bundle(plan)
        comparison_path = bundle / "comparison.json"
        payload = json.loads(comparison_path.read_text(encoding="utf-8"))
        payload["claims"][0]["status"] = REPRODUCED
        comparison_path.write_text(json.dumps(payload), encoding="utf-8")
        result = self.run_script("build_report.py", "--bundle", bundle, expect=1)
        self.assertIn("artifact hash mismatch: comparison.json", result.stdout)

    def test_copy_mode_preserves_original_and_detects_undeclared_writes(self):
        self.write_program(
            "from pathlib import Path\n"
            "Path('mutated.txt').write_text('changed')\n"
            "print('{\"score\": 0.905}')\n"
        )
        _, plan = self.make_plan()
        bundle = self.execute_bundle(plan, expect=1)
        self.assertFalse((self.repository / "mutated.txt").exists())
        run_record = json.loads((bundle / "run-record.json").read_text(encoding="utf-8"))
        self.assertFalse(run_record["repository_integrity"]["source_tree_changed"])
        self.assertTrue(run_record["repository_integrity"]["workspace_core_changed"])
        comparison = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(comparison["claims"][0]["status"], "INCONCLUSIVE")
        self.run_script("build_report.py", "--bundle", bundle)

    def test_csv_result_file_is_preserved_and_extracted(self):
        self.write_program(
            "import os\n"
            "from pathlib import Path\n"
            "root = Path(os.environ['REPRO_OUTPUT_DIR'])\n"
            "(root / 'metrics').mkdir(parents=True, exist_ok=True)\n"
            "(root / 'metrics' / 'scores.csv').write_text('split,score\\ntest,0.905\\n')\n"
            "print('done')\n"
        )
        observation = {
            "source": "file",
            "command_id": "experiment",
            "root": "outputs",
            "path": "metrics/scores.csv",
            "extractor": "csv",
            "expression": {
                "column": "score",
                "where": {"split": "test"},
                "aggregate": "first",
            },
            "unit": "ratio",
        }
        plan_value, plan = self.make_plan(observation)
        plan_value["execution"]["write_paths"] = ["metrics"]
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        bundle = self.execute_bundle(plan)
        observation_payload = json.loads((bundle / "observations.json").read_text(encoding="utf-8"))
        item = observation_payload["observations"][0]
        self.assertEqual(item["normalized_value"], 0.905)
        self.assertTrue((bundle / item["source_artifact"]).is_file())
        self.run_script("build_report.py", "--bundle", bundle)

    def test_all_tolerances_must_pass_when_combination_is_all(self):
        self.write_program("print('{\"score\": 0.91}')\n")
        plan_value, plan = self.make_plan()
        plan_value["claims"][0]["comparison"]["absolute"] = 0.02
        plan_value["claims"][0]["comparison"]["relative"] = 0.005
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        bundle = self.execute_bundle(plan)
        result = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(result["claims"][0]["status"], "CLAIM_NOT_REPRODUCED")

    def test_multi_run_equivalence_interval_and_unit_conversion(self):
        self.write_program("print('{\"scores\": [90.0, 90.1, 89.9, 90.0, 90.0]}')\n")
        observation = {
            "source": "stdout",
            "command_id": "experiment",
            "extractor": "jsonpath",
            "expression": "$.scores",
            "unit": "percent",
        }
        custom_claim = claim(
            observation,
            comparison={
                "method": "equivalence_interval",
                "absolute": 0.01,
                "relative": 0.02,
                "combination": "all",
                "minimum_runs": 5,
                "aggregate": "mean",
                "direction": "two_sided",
                "confidence": 0.95,
            },
        )
        _, plan = self.make_plan(observation, claims=[custom_claim])
        bundle = self.execute_bundle(plan)
        result = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(result["claims"][0]["status"], REPRODUCED)
        self.assertEqual(result["claims"][0]["details"]["run_count"], 5)

    def test_literal_secrets_are_rejected_and_secret_refs_are_masked(self):
        self.write_program("print('{\"score\": 0.905}')\n")
        plan_value, plan = self.make_plan()
        plan_value["commands"][0]["argv"].extend(["--api-key", "literal-secret"])
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        result = self.run_script(
            "validate_reproduction_plan.py", "--plan", plan, expect=1
        )
        self.assertIn("use secret_ref", result.stdout)
        self.assertNotIn("literal-secret", result.stdout)

        plan_value["commands"][0]["argv"] = [
            sys.executable,
            "experiment.py",
            "--api-key",
            {"secret_ref": "TEST_REPRO_SECRET"},
        ]
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        environment = dict(os.environ)
        environment["TEST_REPRO_SECRET"] = "super-private-value"
        bundle = self.case_root / "secret-bundle"
        self.run_script(
            "run_reproduction.py",
            "--plan",
            plan,
            "--output",
            bundle,
            "--execute",
            env=environment,
        )
        serialized = (bundle / "run-record.json").read_text(encoding="utf-8")
        self.assertIn("[SECRET_REF:TEST_REPRO_SECRET]", serialized)
        self.assertNotIn("super-private-value", serialized)
        for log in (bundle / "logs").iterdir():
            self.assertNotIn("super-private-value", log.read_text(encoding="utf-8"))

    def test_network_disabled_is_not_falsely_claimed_on_host_mode(self):
        self.write_program("print('{\"score\": 0.905}')\n")
        plan_value, plan = self.make_plan()
        plan_value["execution"]["network"] = "disabled"
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        bundle = self.execute_bundle(plan, expect=1)
        record = json.loads((bundle / "run-record.json").read_text(encoding="utf-8"))
        self.assertIn("requires container mode", record["commands"][0]["error"])
        comparison = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(comparison["claims"][0]["status"], "BLOCKED")

    def test_inventory_hashes_every_file_and_changes_with_core_code(self):
        self.write_program("print(1)\n")
        (self.repository / "requirements.lock.txt").write_text(
            "example==1.0\n", encoding="utf-8"
        )
        first = self.case_root / "first.json"
        second = self.case_root / "second.json"
        self.run_script(
            "inventory_artifacts.py", "--repository", self.repository, "--output", first
        )
        (self.repository / "core_model.py").write_text("WEIGHT = 1\n", encoding="utf-8")
        self.run_script(
            "inventory_artifacts.py", "--repository", self.repository, "--output", second
        )
        left = json.loads(first.read_text(encoding="utf-8"))
        right = json.loads(second.read_text(encoding="utf-8"))
        self.assertNotEqual(left["tree_sha256"], right["tree_sha256"])
        self.assertIn("core_model.py", [item["path"] for item in right["files"]])
        categories = {item["path"]: item["category"] for item in right["files"]}
        self.assertEqual(categories["requirements.lock.txt"], "environment")


if __name__ == "__main__":
    unittest.main()
