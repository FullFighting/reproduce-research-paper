import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "benchmarks"
RUNNER = BENCHMARKS / "run_benchmarks.py"
RESULTS = BENCHMARKS / "results"
VERIFIER = (
    ROOT
    / "skills"
    / "reproduce-research-paper"
    / "scripts"
    / "build_report.py"
)
REPRODUCED = "CLAIM_REPRODUCED_WITHIN_TOLERANCE"


class PublicBenchmarkTests(unittest.TestCase):
    def test_fifteen_public_cases_have_complete_verified_bundles(self):
        cases = json.loads((BENCHMARKS / "cases.json").read_text(encoding="utf-8"))
        summary = json.loads(
            (BENCHMARKS / "benchmark-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(cases), 15)
        self.assertEqual(summary["case_count"], 15)
        self.assertEqual(summary["reproduced_count"], 15)
        self.assertEqual(summary["verified_bundle_count"], 15)
        self.assertEqual(summary["total_api_tokens"], 0)
        self.assertEqual(summary["total_estimated_cost_usd"], 0)
        by_id = {item["id"]: item for item in cases}
        for record in summary["cases"]:
            with self.subTest(case=record["id"]):
                case = by_id[record["id"]]
                self.assertTrue(case["paper_url"].startswith("https://"))
                self.assertTrue(case["code_url"].startswith("https://"))
                self.assertTrue(case["data_license"])
                self.assertEqual(record["status"], REPRODUCED)
                self.assertTrue(record["verified_bundle"])
                bundle = RESULTS / record["id"]
                for required in (
                    "plan.json",
                    "inventory-before.json",
                    "inventory-after.json",
                    "environment.json",
                    "run-record.json",
                    "observations.json",
                    "comparison.json",
                    "report.md",
                    "provenance.json",
                ):
                    self.assertTrue((bundle / required).is_file(), required)
                verification = subprocess.run(
                    [sys.executable, "-X", "utf8", str(VERIFIER), "--bundle", str(bundle)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(
                    verification.returncode,
                    0,
                    verification.stderr + verification.stdout,
                )
                self.assertTrue(json.loads(verification.stdout)["valid"])
                plan = json.loads((bundle / "plan.json").read_text(encoding="utf-8"))
                observation = plan["claims"][0]["observation"]
                self.assertNotEqual(observation["source"], "manual")
                self.assertIn("extractor", observation)
                environment = json.loads(
                    (bundle / "environment.json").read_text(encoding="utf-8")
                )
                for package in plan.get("environment", {}).get("packages", []):
                    self.assertTrue(
                        environment["declared_package_versions"].get(package),
                        package,
                    )


    def test_case_registry_is_well_formed(self):
        cases = json.loads((BENCHMARKS / "cases.json").read_text(encoding="utf-8"))
        required = {
            "id",
            "version",
            "category",
            "venue_tier",
            "title",
            "reference",
            "paper_url",
            "code_url",
            "paper_location",
            "research_question",
            "method",
            "data",
            "training",
            "protocol",
            "limitations",
            "metric",
            "expected",
            "unit",
            "comparison",
            "packages",
            "network",
            "timeout_seconds",
            "data_license",
        }
        identifiers = [case["id"] for case in cases]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for case in cases:
            with self.subTest(case=case.get("id")):
                self.assertEqual(required - set(case), set())
                self.assertIsInstance(case["version"], int)
                self.assertGreaterEqual(case["version"], 1)
                self.assertTrue(case["paper_url"].startswith("https://"))
                self.assertTrue(case["code_url"].startswith("https://"))
                self.assertIn("method", case["comparison"])
                self.assertGreater(case["timeout_seconds"], 0)
                self.assertTrue(case["limitations"].strip())

    def test_runner_registry_helpers_never_touch_published_facts(self):
        summary_before = (BENCHMARKS / "benchmark-summary.json").read_bytes()
        report_before = (BENCHMARKS / "benchmark-report.md").read_bytes()

        listing = subprocess.run(
            [sys.executable, "-X", "utf8", str(RUNNER), "--list-cases"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(listing.returncode, 0, listing.stderr)
        lines = [line for line in listing.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 15)
        for line in lines:
            entry = json.loads(line)
            self.assertIn("id", entry)
            self.assertIn("category", entry)

        rejected = subprocess.run(
            [sys.executable, "-X", "utf8", str(RUNNER), "--only", "no-such-case"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("unknown case id", rejected.stderr)

        self.assertEqual(summary_before, (BENCHMARKS / "benchmark-summary.json").read_bytes())
        self.assertEqual(report_before, (BENCHMARKS / "benchmark-report.md").read_bytes())

    def test_report_includes_category_rollup_consistent_with_cases(self):
        spec = importlib.util.spec_from_file_location("benchmark_runner_under_test", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        summary = json.loads(
            (BENCHMARKS / "benchmark-summary.json").read_text(encoding="utf-8")
        )
        rollup = module.category_rollup(summary["cases"])
        self.assertEqual(sum(entry["case_count"] for entry in rollup), summary["case_count"])
        self.assertEqual(
            sum(entry["reproduced_count"] for entry in rollup), summary["reproduced_count"]
        )
        report = module.render_report(summary)
        self.assertIn("## Coverage by category", report)
        for entry in rollup:
            self.assertIn(f"| {entry['category']} |", report)


if __name__ == "__main__":
    unittest.main()
