import hashlib
import json
import os
import shutil
import subprocess
import sys
import types
import unittest
import uuid
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "reproduce-research-paper"
SCRIPTS = SKILL / "scripts"
EXAMPLES = SKILL / "assets" / "examples"
RUNTIME = ROOT / "tests" / ".reproduce-runtime"
REPRODUCED = "CLAIM_REPRODUCED_WITHIN_TOLERANCE"
UNITLESS_V2 = {"symbol": "1", "scale": 1, "semantic_type": "unitless"}


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

    def test_validator_rejects_wrong_json_types_without_crashing(self):
        self.write_program("print('{\"score\": 0.9}')\n")
        mutations = (
            lambda plan: plan.update(schema_version=[]),
            lambda plan: plan["execution"].update(network=[]),
            lambda plan: plan["execution"].update(workspace_mode=[]),
            lambda plan: plan["claims"][0].update(
                expected={"type": [], "value": 0.9}
            ),
            lambda plan: plan["claims"][0]["observation"].update(source=[]),
            lambda plan: plan["claims"][0]["comparison"].update(method=[]),
            lambda plan: plan["claims"][0].update(command_ids=[{}]),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                plan_value, plan = self.make_plan()
                mutate(plan_value)
                plan.write_text(json.dumps(plan_value), encoding="utf-8")
                result = self.run_script(
                    "validate_reproduction_plan.py",
                    "--plan",
                    plan,
                    expect=1,
                )
                payload = json.loads(result.stdout)
                self.assertFalse(payload["valid"])
                self.assertTrue(payload["errors"])

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

    def test_git_worktree_mode_rejects_dirty_source(self):
        self.write_program("print('{\"score\": 0.905}')\n")
        for command in (
            ["git", "init"],
            ["git", "add", "experiment.py"],
            [
                "git",
                "-c",
                "user.name=Reproduction Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "fixture",
            ],
        ):
            result = subprocess.run(
                command,
                cwd=self.repository,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        plan_value, plan = self.make_plan()
        plan_value["execution"]["workspace_mode"] = "git_worktree"
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        self.write_program("print('{\"score\": 0.1}')\n")
        result = self.run_script(
            "run_reproduction.py",
            "--plan",
            plan,
            "--output",
            self.case_root / "dirty-bundle",
            "--execute",
            expect=2,
        )
        self.assertIn("requires a clean source worktree", result.stderr)

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

    def test_parquet_extractor_parses_numeric_values(self):
        class FakeColumn:
            def to_pylist(self):
                return ["1.5", 2.5]

        class FakeTable:
            def __getitem__(self, name):
                self.requested_name = name
                return FakeColumn()

        parquet = types.ModuleType("pyarrow.parquet")
        parquet.read_table = lambda *_args, **_kwargs: FakeTable()
        pyarrow = types.ModuleType("pyarrow")
        pyarrow.__path__ = []
        pyarrow.parquet = parquet

        sys.path.insert(0, str(SCRIPTS))
        try:
            from extract_observations import _parquet_extract

            with mock.patch.dict(
                sys.modules,
                {"pyarrow": pyarrow, "pyarrow.parquet": parquet},
            ):
                self.assertEqual(
                    _parquet_extract(
                        self.repository / "fixture.parquet",
                        {"column": "score", "aggregate": "values"},
                    ),
                    [1.5, 2.5],
                )
        finally:
            sys.path.pop(0)

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

    def test_schema_v2_accepts_typed_expected_values_and_custom_units(self):
        observation = {
            "source": "stdout",
            "command_id": "experiment",
            "extractor": "jsonpath",
            "expression": "$.value",
            "unit": UNITLESS_V2,
        }
        cases = [
            ({"type": "scalar", "value": 0.91}, "numeric_tolerance", {"absolute": 0.01}),
            ({"type": "array", "value": ["cat", "dog"]}, "exact_match", {}),
            (
                {
                    "type": "table",
                    "value": {
                        "columns": ["model", "score"],
                        "row_labels": ["row-1"],
                        "rows": [["A", 0.91]],
                    },
                },
                "exact_match",
                {},
            ),
            ({"type": "ranking", "value": ["A", "B", "C"]}, "exact_order", {}),
            ({"type": "categorical", "value": "positive"}, "exact_match", {}),
            ({"type": "string", "value": "model-v2"}, "exact_match", {}),
            ({"type": "artifact_hash", "value": "a" * 64}, "artifact_hash", {}),
            (
                {"type": "distribution", "value": [0.1, 0.2, 0.3]},
                "distribution_distance",
                {"maximum_distance": 0.1},
            ),
        ]
        for index, (expected, method, extra) in enumerate(cases):
            with self.subTest(expected_type=expected["type"]):
                plan_value, plan = self.make_plan(observation)
                plan_value["schema_version"] = 2
                plan_value["claims"][0]["expected"] = expected
                plan_value["claims"][0]["unit"] = UNITLESS_V2
                plan_value["claims"][0]["comparison"] = {
                    "method": method,
                    "combination": "all",
                    "minimum_runs": 1,
                    "aggregate": "none",
                    "direction": "two_sided",
                    **extra,
                }
                plan.write_text(json.dumps(plan_value), encoding="utf-8")
                result = self.run_script(
                    "validate_reproduction_plan.py", "--plan", plan
                )
                self.assertTrue(json.loads(result.stdout)["valid"], index)

        custom_unit = {
            "symbol": "BLEU",
            "scale": 1,
            "semantic_type": "quality_metric",
        }
        milli_unit = {
            "symbol": "mBLEU",
            "scale": 0.001,
            "semantic_type": "quality_metric",
        }
        self.write_program("print('{\"value\": 42000}')\n")
        observation["unit"] = milli_unit
        plan_value, plan = self.make_plan(observation)
        plan_value["schema_version"] = 2
        plan_value["claims"][0]["expected"] = {"type": "scalar", "value": 42.0}
        plan_value["claims"][0]["unit"] = custom_unit
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        bundle = self.execute_bundle(plan)
        result = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(result["claims"][0]["status"], REPRODUCED)

    def test_schema_v2_compares_structured_and_distribution_results(self):
        digest = "b" * 64
        self.write_program(
            "import json\n"
            f"print(json.dumps({{'category': 'positive', 'ranking': ['A', 'B', 'C'], "
            f"'table': {{'columns': ['model', 'score'], 'row_labels': ['r1'], "
            f"'rows': [['A', 0.91]]}}, 'hash': '{digest}', "
            "'distribution': [0.1, 0.2, 0.3]}))\n"
        )
        specs = [
            ("category", {"type": "categorical", "value": "positive"}, "exact_match", {}),
            ("ranking", {"type": "ranking", "value": ["A", "B", "C"]}, "exact_order", {}),
            (
                "table",
                {
                    "type": "table",
                    "value": {
                        "columns": ["model", "score"],
                        "row_labels": ["r1"],
                        "rows": [["A", 0.91]],
                    },
                },
                "exact_match",
                {},
            ),
            ("hash", {"type": "artifact_hash", "value": digest}, "artifact_hash", {}),
            (
                "distribution",
                {"type": "distribution", "value": [0.1, 0.2, 0.3]},
                "distribution_distance",
                {"maximum_distance": 0.0},
            ),
        ]
        claims = []
        for field, expected, method, extra in specs:
            claims.append(
                claim(
                    {
                        "source": "stdout",
                        "command_id": "experiment",
                        "extractor": "jsonpath",
                        "expression": f"$.{field}",
                        "unit": UNITLESS_V2,
                    },
                    id=f"claim-{field}",
                    expected=expected,
                    unit=UNITLESS_V2,
                    comparison={
                        "method": method,
                        "combination": "all",
                        "minimum_runs": 1,
                        "aggregate": "none",
                        "direction": "two_sided",
                        **extra,
                    },
                )
            )
        plan_value, plan = self.make_plan(claims[0]["observation"], claims=claims)
        plan_value["schema_version"] = 2
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        bundle = self.execute_bundle(plan)
        comparison = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertTrue(all(item["status"] == REPRODUCED for item in comparison["claims"]))
        self.run_script("build_report.py", "--bundle", bundle)

    def test_schema_v2_normalizes_numeric_table_rows(self):
        source_unit = {
            "symbol": "mF1",
            "scale": 0.001,
            "semantic_type": "quality_metric",
        }
        target_unit = {
            "symbol": "F1",
            "scale": 1,
            "semantic_type": "quality_metric",
        }
        self.write_program(
            "import json\n"
            "print(json.dumps({'table': {'columns': ['fold-1', 'fold-2'], "
            "'row_labels': ['model-a'], 'rows': [[910, 920]]}}))\n"
        )
        observation = {
            "source": "stdout",
            "command_id": "experiment",
            "extractor": "jsonpath",
            "expression": "$.table",
            "unit": source_unit,
        }
        plan_value, plan = self.make_plan(observation)
        plan_value["schema_version"] = 2
        plan_value["claims"][0]["expected"] = {
            "type": "table",
            "value": {
                "columns": ["fold-1", "fold-2"],
                "row_labels": ["model-a"],
                "rows": [[0.91, 0.92]],
            },
        }
        plan_value["claims"][0]["unit"] = target_unit
        plan_value["claims"][0]["comparison"]["aggregate"] = "none"
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        bundle = self.execute_bundle(plan)
        comparison = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(comparison["claims"][0]["status"], REPRODUCED)

    def test_artifact_hash_is_extracted_from_the_run_file(self):
        payload = b"model artifact bytes\n"
        digest = hashlib.sha256(payload).hexdigest()
        self.write_program(
            "import os\n"
            "from pathlib import Path\n"
            "root = Path(os.environ['REPRO_OUTPUT_DIR'])\n"
            "(root / 'artifacts').mkdir(parents=True, exist_ok=True)\n"
            "(root / 'artifacts' / 'model.bin').write_bytes(b'model artifact bytes\\n')\n"
        )
        hash_unit = {
            "symbol": "sha256",
            "scale": 1,
            "semantic_type": "artifact_identity",
        }
        observation = {
            "source": "file",
            "command_id": "experiment",
            "root": "outputs",
            "path": "artifacts/model.bin",
            "extractor": "sha256",
            "unit": hash_unit,
        }
        plan_value, plan = self.make_plan(observation)
        plan_value["schema_version"] = 2
        plan_value["execution"]["write_paths"] = ["artifacts"]
        plan_value["claims"][0]["expected"] = {
            "type": "artifact_hash",
            "value": digest,
        }
        plan_value["claims"][0]["unit"] = hash_unit
        plan_value["claims"][0]["comparison"] = {
            "method": "artifact_hash",
            "combination": "all",
            "minimum_runs": 1,
            "aggregate": "none",
            "direction": "two_sided",
        }
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        bundle = self.execute_bundle(plan)
        comparison = json.loads((bundle / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(comparison["claims"][0]["status"], REPRODUCED)
        observation_payload = json.loads(
            (bundle / "observations.json").read_text(encoding="utf-8")
        )
        self.assertEqual(observation_payload["observations"][0]["normalized_value"], digest)

    def test_argv_secrets_are_denied_by_default_and_environment_secrets_are_redacted(self):
        sys.path.insert(0, str(SCRIPTS))
        try:
            from run_reproduction import _resolve_command

            with self.assertRaisesRegex(ValueError, "disabled by default"):
                _resolve_command(
                    {"argv": ["python", {"secret_ref": "API_KEY"}]}
                )
        finally:
            sys.path.pop(0)

        self.write_program(
            "import json, os\n"
            "print(os.environ.get('TEST_API_KEY', 'missing'))\n"
            "print(json.dumps({'score': 0.905}))\n"
        )
        plan_value, plan = self.make_plan()
        plan_value["commands"][0]["argv"].extend(["--api-key", "literal-secret"])
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        result = self.run_script(
            "validate_reproduction_plan.py", "--plan", plan, expect=1
        )
        self.assertIn("use secret_bindings", result.stdout)
        self.assertNotIn("literal-secret", result.stdout)

        plan_value["commands"][0]["argv"] = [
            sys.executable,
            "experiment.py",
            "--api-key",
            {"secret_ref": "TEST_REPRO_SECRET"},
        ]
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        result = self.run_script(
            "validate_reproduction_plan.py", "--plan", plan, expect=1
        )
        self.assertIn("disabled by default", result.stdout)

        plan_value["commands"][0]["argv"] = [sys.executable, "experiment.py"]
        plan_value["commands"][0]["secret_bindings"] = [
            {"name": "TEST_API_KEY", "secret_ref": "TEST_REPRO_SECRET"}
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
        self.assertNotIn("super-private-value", serialized)
        self.assertFalse(json.loads(serialized)["argv_secret_compatibility_mode"])
        for log in (bundle / "logs").iterdir():
            self.assertNotIn("super-private-value", log.read_text(encoding="utf-8"))

        plan_value["commands"][0].pop("secret_bindings")
        plan_value["commands"][0]["argv"] = [
            sys.executable,
            "experiment.py",
            "--api-key",
            {"secret_ref": "TEST_REPRO_SECRET"},
        ]
        plan_value["execution"]["allow_argv_secrets"] = True
        compatibility_plan = self.case_root / "compatibility-plan.json"
        compatibility_plan.write_text(json.dumps(plan_value), encoding="utf-8")
        compatibility_bundle = self.case_root / "compatibility-bundle"
        self.run_script(
            "run_reproduction.py",
            "--plan",
            compatibility_plan,
            "--output",
            compatibility_bundle,
            "--execute",
            env=environment,
        )
        compatibility_record = json.loads(
            (compatibility_bundle / "run-record.json").read_text(encoding="utf-8")
        )
        self.assertTrue(compatibility_record["argv_secret_compatibility_mode"])
        self.assertIn(
            "HIGH_RISK_COMPATIBILITY",
            " ".join(compatibility_record["deviations"]),
        )
        self.assertIn(
            "[SECRET_REF:TEST_REPRO_SECRET]",
            (compatibility_bundle / "run-record.json").read_text(encoding="utf-8"),
        )

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

    def test_container_limits_apply_to_container_not_docker_wrapper(self):
        sys.path.insert(0, str(SCRIPTS))
        try:
            import run_reproduction

            capabilities = execution(network="disabled")
            outputs = self.case_root / "outputs"
            outputs.mkdir()
            with mock.patch.object(
                run_reproduction,
                "_local_argv",
                return_value=(0, False, "ok", "", {}),
            ) as wrapper:
                _, _, _, _, enforcement = run_reproduction._container_argv(
                    ["python", "experiment.py"],
                    {"cwd": "."},
                    capabilities,
                    self.repository,
                    outputs,
                    "python@sha256:" + "a" * 64,
                    60,
                    {},
                )
            docker_argv = wrapper.call_args.args[0]
            self.assertIn("--network", docker_argv)
            self.assertEqual(docker_argv[docker_argv.index("--network") + 1], "none")
            self.assertEqual(
                docker_argv[docker_argv.index("--cap-drop") + 1], "ALL"
            )
            security_options = [
                docker_argv[index + 1]
                for index, value in enumerate(docker_argv)
                if value == "--security-opt"
            ]
            self.assertIn("no-new-privileges=true", security_options)
            self.assertIn("seccomp=builtin", security_options)
            self.assertEqual(
                docker_argv[docker_argv.index("--user") + 1], "65532:65532"
            )
            self.assertEqual(
                docker_argv[docker_argv.index("--pull") + 1], "never"
            )
            self.assertIn("cpu=60:61", docker_argv)
            self.assertIn(
                f"fsize={8 * 1024 * 1024}:{8 * 1024 * 1024}",
                docker_argv,
            )
            self.assertFalse(wrapper.call_args.kwargs["apply_posix_limits"])
            self.assertEqual(enforcement["memory"], "Docker --memory")
            self.assertIn("Docker --ulimit cpu", enforcement["cpu"])
            self.assertIn("cap-drop ALL", enforcement["capabilities"])
            self.assertIn("non-root", enforcement["identity"])
        finally:
            sys.path.pop(0)

    def test_container_requires_digest_only_image_and_non_root_user(self):
        self.write_program("print('{\"score\": 0.9}')\n")
        invalid_values = (
            "python:3.12",
            "python:3.12@sha256:" + "a" * 64,
            "python@sha256:" + "A" * 64,
        )
        for image in invalid_values:
            with self.subTest(image=image):
                plan_value, plan = self.make_plan()
                plan_value["execution"].update(
                    workspace_mode="container",
                    network="disabled",
                    container_image=image,
                )
                plan.write_text(json.dumps(plan_value), encoding="utf-8")
                result = self.run_script(
                    "validate_reproduction_plan.py", "--plan", plan, expect=1
                )
                self.assertIn("digest-only", result.stdout)

        plan_value, plan = self.make_plan()
        plan_value["execution"].update(
            workspace_mode="container",
            network="disabled",
            container_image="python@sha256:" + "a" * 64,
            container_user="0:0",
        )
        plan.write_text(json.dumps(plan_value), encoding="utf-8")
        result = self.run_script(
            "validate_reproduction_plan.py", "--plan", plan, expect=1
        )
        self.assertIn("non-root numeric UID", result.stdout)

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

    def make_claims_map(self, claims=None, **overrides):
        if claims is None:
            claims = [
                {
                    "id": "map-score",
                    "claim_type": "quantitative",
                    "paper_location": "Table 1",
                    "paper_quote": "The method reaches a score of 0.9 on the fixed fixture (Table 1).",
                    "paper_values": ["0.9"],
                    "disposition": "reproduce",
                    "plan_claim_ids": ["claim-1"],
                },
                {
                    "id": "map-conclusion",
                    "claim_type": "conclusion",
                    "paper_location": "Section 5",
                    "paper_quote": "We conclude the method reproduces the reported score.",
                    "disposition": "reproduce",
                    "supported_by": ["map-score"],
                },
                {
                    "id": "map-figure",
                    "claim_type": "visual",
                    "paper_location": "Figure 1",
                    "paper_quote": "Figure 1 shows the loss curve.",
                    "disposition": "manual_review",
                    "reason": "Visual-only figure without a machine-readable artifact.",
                },
            ]
        value = {
            "schema_version": 1,
            "paper": {"title": "Test paper"},
            "coverage": {
                "read_completely": True,
                "sections": ["Abstract", "Method", "Experiments", "Conclusion"],
                "excluded_content": [],
            },
            "claims": claims,
        }
        value.update(overrides)
        map_path = self.case_root / "paper-claims-map.json"
        map_path.write_text(json.dumps(value), encoding="utf-8")
        return value, map_path

    def test_example_claims_map_grounds_example_plan(self):
        result = self.run_script(
            "validate_paper_claims_map.py",
            "--map",
            EXAMPLES / "paper-claims-map.json",
            "--plan",
            EXAMPLES / "reproduction-plan.json",
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["summary"]["claims"], 3)

    def test_claims_map_rejects_values_missing_from_the_quote(self):
        _, map_path = self.make_claims_map(
            claims=[
                {
                    "id": "map-score",
                    "claim_type": "quantitative",
                    "paper_location": "Table 1",
                    "paper_quote": "The method reaches a score of 0.9 on the fixture.",
                    "paper_values": ["0.95"],
                    "disposition": "reproduce",
                    "plan_claim_ids": ["claim-1"],
                }
            ]
        )
        result = self.run_script(
            "validate_paper_claims_map.py", "--map", map_path, expect=1
        )
        self.assertIn("does not appear verbatim in paper_quote", result.stdout)

    def test_claims_map_requires_whole_paper_reading_and_reasons(self):
        value, map_path = self.make_claims_map()
        value["coverage"]["read_completely"] = False
        value["claims"][2].pop("reason")
        map_path.write_text(json.dumps(value), encoding="utf-8")
        result = self.run_script(
            "validate_paper_claims_map.py", "--map", map_path, expect=1
        )
        self.assertIn("read_completely must be true", result.stdout)
        self.assertIn("reason must explain", result.stdout)

    def test_plan_expected_values_must_come_from_the_paper(self):
        self.write_program("print('{\"score\": 0.9}')\n")
        _, plan_path = self.make_plan()
        _, map_path = self.make_claims_map(
            claims=[
                {
                    "id": "map-score",
                    "claim_type": "quantitative",
                    "paper_location": "Table 1",
                    "paper_quote": "The method reaches a score of 0.8 on the fixture.",
                    "paper_values": ["0.8"],
                    "disposition": "reproduce",
                    "plan_claim_ids": ["claim-1"],
                }
            ]
        )
        result = self.run_script(
            "validate_paper_claims_map.py",
            "--map",
            map_path,
            "--plan",
            plan_path,
            expect=1,
        )
        self.assertIn("is not quoted in paper_values", result.stdout)

    def test_unmapped_plan_claims_are_rejected_as_ungrounded(self):
        self.write_program("print('{\"score\": 0.9}')\n")
        _, plan_path = self.make_plan()
        _, map_path = self.make_claims_map(
            claims=[
                {
                    "id": "map-figure",
                    "claim_type": "visual",
                    "paper_location": "Figure 1",
                    "paper_quote": "Figure 1 shows the loss curve.",
                    "disposition": "manual_review",
                    "reason": "Visual-only figure.",
                }
            ]
        )
        result = self.run_script(
            "validate_paper_claims_map.py",
            "--map",
            map_path,
            "--plan",
            plan_path,
            expect=1,
        )
        self.assertIn("has no paper grounding in the claims map", result.stdout)

    def test_percent_quotes_ground_ratio_expected_values(self):
        _, map_path = self.make_claims_map(
            claims=[
                {
                    "id": "map-score",
                    "claim_type": "quantitative",
                    "paper_location": "Table 2",
                    "paper_quote": "Our approach attains 90% accuracy on the fixture.",
                    "paper_values": ["90%"],
                    "disposition": "reproduce",
                    "plan_claim_ids": ["claim-1"],
                }
            ]
        )
        self.write_program("print('{\"score\": 0.9}')\n")
        _, plan_path = self.make_plan()
        result = self.run_script(
            "validate_paper_claims_map.py", "--map", map_path, "--plan", plan_path
        )
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_coverage_report_resolves_conclusions_from_their_support(self):
        self.write_program("import json\nprint(json.dumps({'score': 0.905}))\n")
        _, plan_path = self.make_plan()
        bundle = self.execute_bundle(plan_path)
        _, map_path = self.make_claims_map()
        coverage_dir = self.case_root / "coverage"
        result = self.run_script(
            "build_coverage_report.py",
            "--map",
            map_path,
            "--bundle",
            bundle,
            "--output",
            coverage_dir,
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["overall_status"], "PARTIALLY_REPRODUCED")
        self.assertEqual(payload["claims"]["map-score"]["status"], REPRODUCED)
        self.assertEqual(payload["claims"]["map-conclusion"]["status"], REPRODUCED)
        self.assertEqual(
            payload["claims"]["map-figure"]["status"], "MANUAL_REVIEW_REQUIRED"
        )
        report = (coverage_dir / "coverage-report.md").read_text(encoding="utf-8")
        self.assertIn("Whole-paper coverage report", report)
        self.assertIn("supported by: map-score", report)
        stored = json.loads(
            (coverage_dir / "coverage.json").read_text(encoding="utf-8")
        )
        self.assertEqual(stored["overall_status"], "PARTIALLY_REPRODUCED")

    def test_coverage_report_refuses_tampered_bundles(self):
        self.write_program("import json\nprint(json.dumps({'score': 0.905}))\n")
        _, plan_path = self.make_plan()
        bundle = self.execute_bundle(plan_path)
        log = bundle / "logs" / "experiment.stdout.log"
        log.write_text('{"score": 0.99}\n', encoding="utf-8")
        _, map_path = self.make_claims_map()
        result = self.run_script(
            "build_coverage_report.py",
            "--map",
            map_path,
            "--bundle",
            bundle,
            expect=1,
        )
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        self.assertTrue(any("bundle" in error for error in payload["errors"]))

    def test_coverage_report_marks_missing_evidence_as_not_attempted(self):
        _, map_path = self.make_claims_map()
        result = self.run_script("build_coverage_report.py", "--map", map_path)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["claims"]["map-score"]["status"], "NOT_ATTEMPTED")
        self.assertEqual(payload["claims"]["map-conclusion"]["status"], "NOT_ATTEMPTED")


if __name__ == "__main__":
    unittest.main()
