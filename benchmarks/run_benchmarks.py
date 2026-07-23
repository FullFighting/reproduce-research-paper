#!/usr/bin/env python3
"""Generate and verify all public low-cost V1 evidence bundles."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = BENCHMARK_ROOT.parent
CASES_PATH = BENCHMARK_ROOT / "cases.json"
WORK_ROOT = BENCHMARK_ROOT / ".work"
RESULTS_ROOT = BENCHMARK_ROOT / "results"
RUNNER = (
    REPOSITORY_ROOT
    / "skills"
    / "reproduce-research-paper"
    / "scripts"
    / "run_reproduction.py"
)
VERIFIER = RUNNER.with_name("build_report.py")


def plan_for(case: dict) -> dict:
    return {
        "schema_version": 1,
        "repository": "../../harness",
        "paper": {
            "title": case["title"],
            "reference": case["reference"],
            "paper_url": case["paper_url"],
            "code_url": case["code_url"],
        },
        "paper_context": {
            "research_question": case["research_question"],
            "method": case["method"],
            "data_and_splits": case["data"],
            "training_or_inference": case["training"],
            "evaluation_protocol": case["protocol"],
            "limitations": case["limitations"],
        },
        "environment": {
            "packages": case["packages"],
            "lock_files": ["requirements.lock.txt"],
        },
        "execution": {
            "workspace_mode": "copy",
            "network": case["network"],
            "write_paths": [],
            "max_memory_mb": 4096,
            "max_cpu_seconds": case["timeout_seconds"],
            "max_disk_mb": 64,
            "max_output_files": 50,
            "max_single_file_mb": 16,
            "max_gpus": 0,
            "retain_workspace": False,
            "exclude_paths": {},
        },
        "commands": [
            {
                "id": "paper-claim",
                "argv": ["python", "experiment.py", "--case", case["id"]],
                "cwd": ".",
                "timeout_seconds": case["timeout_seconds"],
            }
        ],
        "claims": [
            {
                "id": case["id"],
                "paper_location": case["paper_location"],
                "metric": case["metric"],
                "expected": case["expected"],
                "unit": case["unit"],
                "protocol": case["protocol"],
                "command_ids": ["paper-claim"],
                "observation": {
                    "source": "stdout",
                    "command_id": "paper-claim",
                    "extractor": "jsonpath",
                    "expression": "$.metric",
                    "unit": case["unit"],
                },
                "comparison": case["comparison"],
            }
        ],
    }


def safe_remove(path: Path, root: Path) -> None:
    resolved, resolved_root = path.resolve(), root.resolve()
    if resolved.parent != resolved_root:
        raise ValueError(f"refusing to remove path outside {resolved_root}: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def run_case(case: dict, clean: bool) -> dict:
    work = WORK_ROOT / case["id"]
    result = RESULTS_ROOT / case["id"]
    if clean:
        safe_remove(work, WORK_ROOT)
        safe_remove(result, RESULTS_ROOT)
    work.mkdir(parents=True, exist_ok=True)
    plan_path = work / "plan.json"
    plan_path.write_text(
        json.dumps(plan_for(case), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    started = time.time()
    process = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(RUNNER),
            "--plan",
            str(plan_path),
            "--output",
            str(result),
            "--execute",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    verification = subprocess.run(
        [sys.executable, "-X", "utf8", str(VERIFIER), "--bundle", str(result)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    status = "MISSING_REPORT"
    observed = None
    if (result / "comparison.json").is_file():
        comparison = json.loads((result / "comparison.json").read_text(encoding="utf-8"))
        if comparison.get("claims"):
            status = comparison["claims"][0]["status"]
            observed = comparison["claims"][0].get("observed")
    run_record = {}
    if (result / "run-record.json").is_file():
        run_record = json.loads((result / "run-record.json").read_text(encoding="utf-8"))
    return {
        "id": case["id"],
        "title": case["title"],
        "category": case["category"],
        "venue_tier": case["venue_tier"],
        "status": status,
        "expected": case["expected"],
        "observed": observed,
        "unit": case["unit"],
        "duration_seconds": round(time.time() - started, 3),
        "runner_exit_code": process.returncode,
        "verifier_exit_code": verification.returncode,
        "verified_bundle": verification.returncode == 0,
        "paper_url": case["paper_url"],
        "code_url": case["code_url"],
        "data_license": case["data_license"],
        "limitations": case["limitations"],
        "api_tokens": run_record.get("cost", {}).get("api_tokens", 0),
        "estimated_cost_usd": run_record.get("cost", {}).get("estimated_cost_usd", 0),
    }


def render_report(summary: dict) -> str:
    rows = []
    for item in summary["cases"]:
        rows.append(
            f"| [{item['id']}](results/{item['id']}/report.md) | {item['category']} | "
            f"{item['venue_tier']} | `{item['status']}` | {item['observed']} | "
            f"{item['duration_seconds']} | {'yes' if item['verified_bundle'] else 'no'} |"
        )
    details = []
    for item in summary["cases"]:
        details.extend(
            [
                f"### {item['id']}",
                "",
                f"- Paper: [{item['title']}]({item['paper_url']})",
                f"- Code/reference implementation: [{item['code_url']}]({item['code_url']})",
                f"- Data/license: {item['data_license']}",
                f"- Expected / observed: `{item['expected']}` / `{item['observed']}` {item['unit']}",
                f"- Status: `{item['status']}`; bundle verification: `{'PASS' if item['verified_bundle'] else 'FAIL'}`",
                f"- Cost: {item['api_tokens']} API tokens; ${item['estimated_cost_usd']} estimated external API cost",
                f"- Scope limit: {item['limitations']}",
                "",
            ]
        )
    return "\n".join(
        [
            "# Public paper-linked claim-level benchmark",
            "",
            f"Generated: {summary['generated_at']}",
            "",
            "This benchmark contains 15 public, paper-linked, low-cost, claim-level executable cases. "
            "It does not claim that the papers themselves were independently replicated. "
            "Each linked evidence bundle contains its plan, repository/environment inventory, raw logs, "
            "machine-extracted observation, recomputed comparison, report, and provenance manifest.",
            "",
            f"- Cases executed: **{summary['case_count']}**",
            f"- Reproduced within declared tolerance: **{summary['reproduced_count']}**",
            f"- Cryptographically self-consistent bundles: **{summary['verified_bundle_count']}**",
            f"- Total wall time: **{summary['total_duration_seconds']} seconds**",
            f"- API tokens: **{summary['total_api_tokens']}**",
            f"- Estimated external API cost: **${summary['total_estimated_cost_usd']}**",
            "",
            "## Results",
            "",
            "| Case | Category | Venue level | Claim status | Observed | Seconds | Bundle valid |",
            "|---|---|---|---|---:|---:|---|",
            *rows,
            "",
            "## Interpretation",
            "",
            "These are deliberately bounded claim-level reproductions selected for public data, CPU execution, "
            "and low cost. Software papers are tested through deterministic API or algorithm invariants; small "
            "machine-learning cases use fixed public splits without tuning; the finance case recomputes official "
            "Fama–French factors from the official portfolio archive. Original large-scale speedups, GPU training, "
            "human studies, and causal/generalization claims remain outside this benchmark.",
            "",
            "SHA-256 detects unsynchronized changes inside each bundle but is not a signature and does not prove "
            "authorship. The report generator re-hashes every tracked artifact and recomputes comparisons from logs.",
            "",
            "## Case notes",
            "",
            *details,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="replace generated work and result directories")
    args = parser.parse_args()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if len(cases) < 15:
        raise SystemExit("benchmark requires at least 15 cases")
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    records = []
    for case in cases:
        print(f"[{len(records) + 1}/{len(cases)}] {case['id']}", flush=True)
        records.append(run_case(case, args.clean))
    summary = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "case_count": len(records),
        "reproduced_count": sum(
            item["status"] == "CLAIM_REPRODUCED_WITHIN_TOLERANCE" for item in records
        ),
        "verified_bundle_count": sum(item["verified_bundle"] for item in records),
        "total_duration_seconds": round(sum(item["duration_seconds"] for item in records), 3),
        "total_api_tokens": sum(item["api_tokens"] for item in records),
        "total_estimated_cost_usd": sum(item["estimated_cost_usd"] for item in records),
        "cases": records,
    }
    (BENCHMARK_ROOT / "benchmark-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (BENCHMARK_ROOT / "benchmark-report.md").write_text(
        render_report(summary),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2))
    return 0 if summary["reproduced_count"] == len(records) and summary["verified_bundle_count"] == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
