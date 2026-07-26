#!/usr/bin/env python3
"""Verify an evidence bundle and reproduce its comparison and Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compare_metrics import (
    BLOCKED,
    INCONCLUSIVE,
    MANUAL,
    NOT_ATTEMPTED,
    NOT_REPRODUCED,
    PARTIAL,
    REPRODUCED,
    compare_all,
)
from evidence_bundle import verify_provenance
from evidence_common import is_within, object_sha256, read_json, sha256_file

DISCLAIMER = (
    "This result verifies only the declared computational claim under the recorded "
    "environment and protocol."
)


def overall_status(comparison: dict) -> str:
    outcomes = [item.get("status") for item in comparison.get("claims", [])]
    if not outcomes:
        return NOT_ATTEMPTED
    if all(status == REPRODUCED for status in outcomes):
        return REPRODUCED
    if any(status == REPRODUCED for status in outcomes):
        return PARTIAL
    if any(status == NOT_REPRODUCED for status in outcomes):
        return NOT_REPRODUCED
    if any(status == INCONCLUSIVE for status in outcomes):
        return INCONCLUSIVE
    if any(status == MANUAL for status in outcomes):
        return MANUAL
    if all(status == BLOCKED for status in outcomes):
        return BLOCKED
    return INCONCLUSIVE


def _display(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        return f"`{json.dumps(value, ensure_ascii=False, separators=(',', ':'))}`"
    return str(value)


def render_report(
    plan: dict,
    inventory_before: dict,
    inventory_after: dict,
    environment: dict,
    run_record: dict,
    observations: dict,
    comparison: dict,
) -> str:
    status = overall_status(comparison)
    paper = plan.get("paper", {})
    state = run_record.get("repository_state", {})
    source_before = state.get("source_before", {})
    source_after = state.get("source_after", {})
    lines = [
        "# Reproduction evidence report",
        "",
        f"**Status:** `{status}`",
        "",
        f"> {DISCLAIMER}",
        "",
        "## Scope",
        "",
        f"- Paper: {paper.get('title', 'not supplied')}",
        f"- Reference: {paper.get('reference', 'not supplied')}",
        f"- Official paper URL: {paper.get('paper_url', 'not supplied')}",
        f"- Official code URL: {paper.get('code_url', 'not supplied')}",
        f"- Reviewed plan SHA-256: `{object_sha256(plan)}`",
        f"- Workspace mode: `{plan.get('execution', {}).get('workspace_mode')}`",
        "",
        "## Paper-wide reproduction basis",
        "",
        f"- Research question: {plan.get('paper_context', {}).get('research_question', 'not recorded')}",
        f"- Method: {plan.get('paper_context', {}).get('method', 'not recorded')}",
        f"- Data and splits: {plan.get('paper_context', {}).get('data_and_splits', 'not recorded')}",
        f"- Training or inference: {plan.get('paper_context', {}).get('training_or_inference', 'not recorded')}",
        f"- Evaluation protocol: {plan.get('paper_context', {}).get('evaluation_protocol', 'not recorded')}",
        f"- Reported limitations: {plan.get('paper_context', {}).get('limitations', 'not recorded')}",
        "",
        "## Repository and environment binding",
        "",
        f"- Git commit: `{source_before.get('git_commit') or 'not a Git checkout'}`",
        f"- Dirty working tree before run: `{source_before.get('git_dirty')}`",
        f"- Dirty diff SHA-256: `{source_before.get('dirty_diff_sha256') or 'not applicable'}`",
        f"- Source tree before: `{source_before.get('tree_sha256')}`",
        f"- Source tree after: `{source_after.get('tree_sha256')}`",
        f"- Inventory before: `{inventory_before.get('inventory_sha256')}`",
        f"- Inventory after: `{inventory_after.get('inventory_sha256')}`",
        f"- Environment artifact SHA-256: `{object_sha256(environment)}`",
        f"- Submodules: {_display(source_before.get('submodules', {}))}",
        f"- Recorded exclusions: {_display(source_before.get('exclusions', []))}",
        "",
        "### Artifact categories",
        "",
        "| Category | Files | Bytes | SHA-256 |",
        "|---|---:|---:|---|",
    ]
    for category, record in source_before.get("categories", {}).items():
        lines.append(
            f"| {category} | {record.get('file_count')} | {record.get('bytes')} | `{record.get('sha256')}` |"
        )
    lines.extend(
        [
            "",
            "## Claim outcomes",
            "",
            "| Claim | Location | Metric | Expected | Observed | Extractor | Source SHA-256 | Status |",
            "|---|---|---|---:|---:|---|---|---|",
        ]
    )
    observations_by_claim = {
        item.get("claim_id"): item for item in observations.get("observations", [])
    }
    for item in comparison.get("claims", []):
        observation = observations_by_claim.get(item.get("claim_id"), {})
        lines.append(
            f"| {item.get('claim_id', '')} | {item.get('paper_location', '')} | "
            f"{item.get('metric', '')} | {_display(item.get('expected'))} | "
            f"{_display(item.get('observed'))} | "
            f"{observation.get('extractor', '—')}@{observation.get('extractor_version', '—')} | "
            f"`{observation.get('source_sha256') or '—'}` | `{item.get('status', INCONCLUSIVE)}` |"
        )
        if item.get("reason"):
            lines.append(f"| ↳ |  |  |  |  |  |  | {item['reason']} |")
    lines.extend(["", "## Execution record", ""])
    for command in run_record.get("commands", []):
        state_text = "timed out" if command.get("timed_out") else f"exit {command.get('exit_code')}"
        lines.extend(
            [
                f"### `{command.get('id')}`",
                "",
                f"- Result: {state_text} in {command.get('duration_seconds')} seconds",
                f"- Reviewed argv: `{json.dumps(command.get('argv'), ensure_ascii=False)}`",
                f"- Standard output: `{command.get('stdout_log')}` (`{command.get('stdout_sha256')}`)",
                f"- Standard error: `{command.get('stderr_log')}` (`{command.get('stderr_sha256')}`)",
                f"- Filesystem changes: {_display(command.get('filesystem_diff', {}))}",
                f"- Capability enforcement: {_display(command.get('capability_enforcement', {}))}",
                "",
            ]
        )
    lines.extend(
        [
            "## Cost, access, and deviations",
            "",
            f"- API tokens used: `{run_record.get('cost', {}).get('api_tokens', 0)}`",
            f"- Estimated monetary cost: `{run_record.get('cost', {}).get('estimated_cost_usd', 0)}` USD",
            f"- Network policy: `{run_record.get('network_policy')}`",
            *(
                [
                    "- Argv secret compatibility mode: "
                    f"`{run_record.get('argv_secret_compatibility_mode')}`"
                ]
                if "argv_secret_compatibility_mode" in run_record
                else []
            ),
            f"- Policy violations: {_display(run_record.get('policy_violations', []))}",
            f"- Deviations: {_display(run_record.get('deviations', []))}",
            "",
            "## Interpretation limits",
            "",
            f"- {DISCLAIMER}",
            "- A matching number does not prove the paper's causal explanation, "
            "scientific validity, or generalizability.",
            "- SHA-256 binds bytes inside this bundle, but does not prove who produced "
            "them or prevent a party from rewriting both artifacts and unsigned provenance.",
            "- Manual tables, figures, and images are never promoted to a reproduced "
            "claim; they remain `MANUAL_REVIEW_REQUIRED`.",
            "",
        ]
    )
    return "\n".join(lines)


def load_and_recompute(bundle: Path) -> tuple[dict, str]:
    plan = read_json(bundle / "plan.json")
    inventory_before = read_json(bundle / "inventory-before.json")
    inventory_after = read_json(bundle / "inventory-after.json")
    environment = read_json(bundle / "environment.json")
    run_record = read_json(bundle / "run-record.json")
    observations = read_json(bundle / "observations.json")
    stored_comparison = read_json(bundle / "comparison.json")
    if run_record.get("plan_sha256") != object_sha256(plan):
        raise ValueError("run record is not bound to plan.json")
    if run_record.get("inventory_before_sha256") != sha256_file(bundle / "inventory-before.json"):
        raise ValueError("run record is not bound to inventory-before.json")
    if run_record.get("environment_sha256") != sha256_file(bundle / "environment.json"):
        raise ValueError("run record is not bound to environment.json")
    if observations.get("run_record_sha256") != sha256_file(bundle / "run-record.json"):
        raise ValueError("observations are not bound to run-record.json")
    for observation in observations.get("observations", []):
        source = observation.get("source_artifact")
        if source:
            source_path = (bundle / source).resolve()
            if not is_within(source_path, bundle):
                raise ValueError(f"observation source escapes bundle for {observation.get('claim_id')}")
            if sha256_file(source_path) != observation.get("source_sha256"):
                raise ValueError(f"observation source hash mismatch for {observation.get('claim_id')}")
    recomputed = compare_all(plan, observations, run_record)
    if recomputed != stored_comparison:
        raise ValueError("comparison.json does not equal a fresh computation from raw evidence")
    report = render_report(
        plan,
        inventory_before,
        inventory_after,
        environment,
        run_record,
        observations,
        recomputed,
    )
    return recomputed, report


def verify_bundle(bundle: Path) -> list[str]:
    errors = verify_provenance(bundle)
    if errors:
        return errors
    try:
        _, report = load_and_recompute(bundle)
        if (bundle / "report.md").read_text(encoding="utf-8") != report:
            errors.append("report.md does not equal a fresh rendering from raw evidence")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args()
    errors = verify_bundle(args.bundle.resolve())
    print(
        json.dumps(
            {"valid": not errors, "errors": errors},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
