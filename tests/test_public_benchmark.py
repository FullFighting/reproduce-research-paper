import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "benchmarks"
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


if __name__ == "__main__":
    unittest.main()
