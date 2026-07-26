#!/usr/bin/env python3
"""Validate the public Codex planning-evaluation pilot and its evidence links."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = ROOT / "docs" / "codex-evaluation"
REQUIRED = {
    "initial-prompt.md",
    "codex-plan.json",
    "review.md",
    "revised-plan.json",
    "evidence-link.json",
    "token-cost.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_case(case_dir: Path) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED - {path.name for path in case_dir.iterdir() if path.is_file()}
    if missing:
        errors.append(f"{case_dir.name}: missing {sorted(missing)}")
        return errors

    draft = load_json(case_dir / "codex-plan.json")
    revised = load_json(case_dir / "revised-plan.json")
    evidence = load_json(case_dir / "evidence-link.json")
    telemetry = load_json(case_dir / "token-cost.json")
    case_id = evidence.get("case_id")
    if not case_id or draft.get("case_id") != case_id or revised.get("case_id") != case_id:
        errors.append(f"{case_dir.name}: inconsistent case_id")

    if draft.get("execution_authorized") is not False:
        errors.append(f"{case_dir.name}: draft must be preview-only")
    if revised.get("status") != "ACCEPTED_FOR_DETERMINISTIC_EXECUTION":
        errors.append(f"{case_dir.name}: revised plan status is not accepted")

    bundle_rel = evidence.get("bundle_path")
    if not isinstance(bundle_rel, str):
        errors.append(f"{case_dir.name}: bundle_path is required")
        return errors
    bundle = (case_dir / bundle_rel).resolve()
    try:
        bundle.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"{case_dir.name}: bundle escapes repository")
        return errors
    if not bundle.is_dir():
        errors.append(f"{case_dir.name}: missing evidence bundle {bundle_rel}")
        return errors

    artifacts = {
        "plan_sha256": bundle / "plan.json",
        "provenance_sha256": bundle / "provenance.json",
        "report_sha256": bundle / "report.md",
    }
    for field, path in artifacts.items():
        if not path.is_file() or evidence.get(field) != sha256(path):
            errors.append(f"{case_dir.name}: invalid {field}")
    if revised.get("accepted_plan_sha256") != evidence.get("plan_sha256"):
        errors.append(f"{case_dir.name}: revised plan is not bound to evidence plan")

    status = telemetry.get("measurement_status")
    if status not in {"MEASURED", "UNAVAILABLE"}:
        errors.append(f"{case_dir.name}: invalid measurement_status")
    if status == "UNAVAILABLE":
        for field in ("input_tokens", "output_tokens", "total_tokens", "estimated_cost_usd"):
            if telemetry.get(field) is not None:
                errors.append(f"{case_dir.name}: unavailable telemetry must use null for {field}")
    if telemetry.get("independent_human_review") is not False:
        errors.append(f"{case_dir.name}: pilot must not claim independent human review")
    return errors


def main() -> int:
    case_dirs = sorted(path for path in EVALUATION_ROOT.glob("paper-*") if path.is_dir())
    errors: list[str] = []
    if len(case_dirs) < 3:
        errors.append("evaluation requires at least three paper cases")
    for case_dir in case_dirs:
        errors.extend(validate_case(case_dir))
    summary = load_json(EVALUATION_ROOT / "evaluation-summary.json")
    if summary.get("case_count") != len(case_dirs):
        errors.append("evaluation-summary.json case_count is stale")
    if summary.get("independent_human_review") is not False:
        errors.append("summary must not claim independent human review")
    print(
        json.dumps(
            {
                "status": "invalid" if errors else "valid",
                "case_count": len(case_dirs),
                "errors": errors,
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
