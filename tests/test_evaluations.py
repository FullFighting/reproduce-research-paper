from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "evaluations" / "run_codex_evaluation.py"
SCORER = ROOT / "evaluations" / "score_plan.py"
RUNTIME = ROOT / "tests" / ".evaluation-runtime"


@contextmanager
def local_temp():
    path = RUNTIME / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


def load_runner():
    spec = importlib.util.spec_from_file_location("evaluation_runner", RUNNER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        RUNTIME.mkdir(parents=True, exist_ok=True)
        cls.runner = load_runner()

    def command(self, *arguments: str, env: dict[str, str] | None = None):
        return subprocess.run(
            [sys.executable, *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            check=False,
        )

    def test_five_public_refusal_cases_validate(self) -> None:
        result = self.command(str(RUNNER_PATH), "--validate-cases")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        value = json.loads(result.stdout)
        self.assertTrue(value["valid"])
        self.assertEqual(value["case_count"], 5)

    def test_preview_does_not_require_key_or_write_output(self) -> None:
        with local_temp() as temp:
            output = Path(temp) / "result"
            env = dict(os.environ)
            env.pop("OPENAI_API_KEY", None)
            result = self.command(
                str(RUNNER_PATH),
                "--case",
                "megatron-512-gpu-budget-block",
                "--model",
                "gpt-5.6-terra",
                "--output",
                str(output),
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PREVIEW ONLY", result.stdout)
            self.assertFalse(output.exists())

    def test_send_without_environment_key_fails_before_output(self) -> None:
        with local_temp() as temp:
            output = Path(temp) / "result"
            env = dict(os.environ)
            env.pop("OPENAI_API_KEY", None)
            result = self.command(
                str(RUNNER_PATH),
                "--case",
                "megatron-512-gpu-budget-block",
                "--model",
                "gpt-5.6-terra",
                "--output",
                str(output),
                "--send",
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("OPENAI_API_KEY is not set", result.stderr)
            self.assertFalse(output.exists())

    def test_nonempty_output_is_rejected_without_network_call(self) -> None:
        with local_temp() as temp:
            output = Path(temp) / "result"
            output.mkdir()
            (output / "keep.txt").write_text("keep\n", encoding="utf-8")
            env = dict(os.environ)
            env["OPENAI_API_KEY"] = "not-a-real-key"
            result = self.command(
                str(RUNNER_PATH),
                "--case",
                "megatron-512-gpu-budget-block",
                "--model",
                "gpt-5.6-terra",
                "--output",
                str(output),
                "--send",
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing a paid request", result.stderr)
            self.assertEqual(
                (output / "keep.txt").read_text(encoding="utf-8"), "keep\n"
            )

    def test_secret_fields_in_cases_are_rejected(self) -> None:
        case = {
            "schema_version": 1,
            "case_id": "secret-case",
            "title": "secret",
            "expected_outcome": "REVISE",
            "paper": {"source_url": "https://example.invalid/paper"},
            "repository": {
                "status": "IDENTIFIED",
                "source_url": "https://example.invalid/repository",
                "revision": "fixture",
                "api_key": "must-not-be-here",
            },
            "constraints": {},
            "required_behavior": "reject",
            "evidence": [
                {
                    "claim": "fixture",
                    "url": "https://example.invalid/evidence",
                    "retrieved_at": "2026-07-23",
                    "note": "fixture",
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "secret-like fields"):
            self.runner.validate_case(case)
        del case["repository"]["api_key"]
        case["repository"]["notes"] = "Bearer abcdefghijklmnopqrstuvwxyz"
        with self.assertRaisesRegex(ValueError, "secret-like fields"):
            self.runner.validate_case(case)

    def test_usage_cost_and_structured_output_parsing(self) -> None:
        response = {
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 200,
                "total_tokens": 1200,
                "input_tokens_details": {"cached_tokens": 400},
            },
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": '{"case_id":"x","outcome":"REVISE","reason":"missing"}',
                        }
                    ],
                }
            ],
        }
        usage = self.runner.usage_record(response)
        self.assertEqual(usage["cached_input_tokens"], 400)
        self.assertEqual(
            self.runner.estimate_cost(
                usage, {"input": 2.5, "cached_input": 0.25, "output": 15.0}
            ),
            0.0046,
        )
        self.assertEqual(
            json.loads(self.runner.extract_output_text(response))["outcome"], "REVISE"
        )

    def test_persisted_telemetry_matches_public_contract_without_credentials(self) -> None:
        with local_temp() as temp:
            output = Path(temp) / "run"
            case = self.runner.load_cases(
                ROOT / "evaluations" / "cases.jsonl"
            )[1]
            prompt_path = ROOT / "evaluations" / "prompts" / "plan-v2.md"
            prompt = prompt_path.read_text(encoding="utf-8")
            request_body = self.runner.build_request(
                case, prompt, "gpt-5.6-terra", 1000, "low"
            )
            response = {
                "id": "resp_public_fixture",
                "model": "gpt-5.6-terra",
                "usage": {
                    "input_tokens": 900,
                    "output_tokens": 100,
                    "total_tokens": 1000,
                    "input_tokens_details": {"cached_tokens": 0},
                },
                "output": [],
            }
            plan = {
                "case_id": case["case_id"],
                "outcome": "BLOCKED_DATA_OR_LICENSE",
                "reason": "License and access evidence are missing.",
            }
            pricing_path = ROOT / "evaluations" / "pricing.json"
            pricing, rates = self.runner.load_pricing(
                pricing_path, "gpt-5.6-terra"
            )
            usage = self.runner.usage_record(response)
            self.runner.persist_run(
                output,
                case,
                prompt_path,
                prompt,
                request_body,
                response,
                plan,
                usage,
                321,
                "gpt-5.6-terra",
                pricing_path,
                pricing,
                rates,
                "fixture-run",
            )
            telemetry = json.loads(
                (output / "telemetry.json").read_text(encoding="utf-8")
            )
            schema = json.loads(
                (ROOT / "evaluations" / "telemetry-schema.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(set(telemetry), set(schema["required"]))
            self.assertEqual(telemetry["usage"]["total_tokens"], 1000)
            self.assertEqual(telemetry["human_review"]["status"], "PENDING")
            self.assertEqual(
                telemetry["final_evidence_bundle"]["status"], "UNBOUND"
            )
            all_artifacts = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in output.iterdir()
                if path.is_file()
            )
            self.assertNotIn("OPENAI_API_KEY=", all_artifacts)
            self.assertNotIn("Authorization", all_artifacts)

    def test_independent_review_is_bound_and_scored(self) -> None:
        with local_temp() as temp:
            root = Path(temp)
            plan = root / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "case_id": "review-case",
                        "outcome": "REVISE",
                        "reason": "needs a bound extractor",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            plan_hash = hashlib.sha256(plan.read_bytes()).hexdigest()
            review = root / "review.json"
            review.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_id": "review-case",
                        "plan_sha256": plan_hash,
                        "reviewed_at": "2026-07-23T00:00:00+00:00",
                        "reviewer": {
                            "id": "reviewer-public-id",
                            "affiliation": "Independent laboratory",
                            "independent": True,
                            "conflict_of_interest": "None declared",
                        },
                        "scores": {
                            "claim_identification": 2,
                            "command_mapping": 1,
                            "data_license_handling": 2,
                            "budget_design": 1,
                            "comparison_policy": 1,
                        },
                        "decision": "REVISE",
                        "decision_reason": "Extractor and tolerance need revision.",
                        "modifications": [
                            {
                                "field": "observation.extractor",
                                "before": None,
                                "after": "stdout JSONPath",
                                "reason": "Bind the observation to the run.",
                            }
                        ],
                        "evidence_bundle": {
                            "status": "UNBOUND",
                            "path": None,
                            "provenance_sha256": None,
                            "reason": "Plan not yet approved or executed.",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            output = root / "summary.json"
            result = self.command(
                str(SCORER),
                "--plan",
                str(plan),
                "--review",
                str(review),
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(summary["adjudication_status"], "COMPLETE")
            self.assertEqual(summary["final_decision"], "REVISE")
            self.assertEqual(summary["human_modifications"][0]["items"][0]["field"], "observation.extractor")


if __name__ == "__main__":
    unittest.main()
