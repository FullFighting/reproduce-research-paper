#!/usr/bin/env python3
"""Build a concise evidence-first Markdown reproduction report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_reproduction_plan import plan_fingerprint


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def overall(plan: dict, comparison: dict, run_record: dict | None, fingerprint: str) -> str:
    outcomes = [item.get("status") for item in comparison.get("claims", [])]
    if "contradicted" in outcomes:
        return "CONTRADICTED"
    if outcomes and all(status == "verified" for status in outcomes) and run_record:
        commands = run_record.get("commands", [])
        executed = {item.get("id"): item for item in commands}
        claims_covered = all(
            all(command_id in executed and executed[command_id].get("exit_code") == 0 and not executed[command_id].get("timed_out")
                for command_id in claim.get("command_ids", []))
            for claim in plan.get("claims", [])
        )
        matching_plan = comparison.get("plan_sha256") == fingerprint and run_record.get("plan_sha256") == fingerprint
        if matching_plan and commands and claims_covered:
            return "VERIFIED"
    if "verified" in outcomes:
        return "PARTIAL"
    if "blocked" in outcomes:
        return "BLOCKED"
    return "NOT_RUN"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--comparison", required=True, type=Path)
    parser.add_argument("--run-record", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        plan, inventory, comparison = read_json(args.plan), read_json(args.inventory), read_json(args.comparison)
        run_record = read_json(args.run_record) if args.run_record else None
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    fingerprint = plan_fingerprint(plan)
    verdict = overall(plan, comparison, run_record, fingerprint)
    paper = plan.get("paper", {})
    lines = [
        "# Reproduction evidence report", "", f"**Status:** `{verdict}`", "",
        "## Scope", "", f"- Paper: {paper.get('title', 'not supplied')}",
        f"- Reference: {paper.get('reference', 'not supplied')}", f"- Repository: {inventory.get('repository', 'not supplied')}",
        f"- Reviewed plan SHA-256: `{fingerprint}`", "",
        "## Paper-wide reproduction basis", "",
        f"- Research question: {plan.get('paper_context', {}).get('research_question', 'not recorded')}",
        f"- Method: {plan.get('paper_context', {}).get('method', 'not recorded')}",
        f"- Data and splits: {plan.get('paper_context', {}).get('data_and_splits', 'not recorded')}",
        f"- Training or inference: {plan.get('paper_context', {}).get('training_or_inference', 'not recorded')}",
        f"- Evaluation protocol: {plan.get('paper_context', {}).get('evaluation_protocol', 'not recorded')}",
        f"- Reported limitations: {plan.get('paper_context', {}).get('limitations', 'not recorded')}", "",
        "## Artifact inventory", "", f"- Files inspected: {inventory.get('file_count', 0)}",
        f"- Dependency files: {', '.join(inventory.get('dependency_files', [])) or 'none found'}",
        f"- Entrypoints: {', '.join(inventory.get('entrypoints', [])) or 'none found'}",
        f"- Data files: {len(inventory.get('data_files', []))}", f"- Weight files: {len(inventory.get('weight_files', []))}",
        f"- License present: {'yes' if inventory.get('has_license') else 'no'}", "",
        "## Claim outcomes", "",
        "| Claim | Metric | Commands | Expected | Observed | Status |", "|---|---|---|---:|---:|---|",
    ]
    for item in comparison.get("claims", []):
        claim_plan = next((claim for claim in plan.get("claims", []) if claim.get("id") == item.get("claim_id")), {})
        lines.append(f"| {item.get('claim_id', '')} | {item.get('metric', '')} | {', '.join(claim_plan.get('command_ids', []))} | {item.get('expected', '—')} | {item.get('observed', '—')} | {item.get('status', '').upper()} |")
    lines.extend(["", "## Execution record", ""])
    if run_record:
        if comparison.get("plan_sha256") != fingerprint or run_record.get("plan_sha256") != fingerprint:
            lines.append("- Evidence integrity warning: the comparison or run record does not match this exact reviewed plan; status cannot be VERIFIED.")
        for item in run_record.get("commands", []):
            state = "timed out" if item.get("timed_out") else f"exit {item.get('exit_code')}"
            lines.append(f"- `{item.get('id')}`: {state}; {item.get('duration_seconds')} s; logs: `{item.get('stdout_log')}`, `{item.get('stderr_log')}`")
    else:
        lines.append("- No execution record was supplied; metrics alone do not establish a verified reproduction.")
    lines.extend(["", "## Limitations", "", "- This report evaluates only the declared claims and observed outputs.", "- Matching a reported metric does not by itself establish the paper's causal interpretation or generalizability.", "- Missing artifacts, licenses, access, seeds, or environment details remain material evidence.", ""])
    rendered = "\n".join(lines)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
