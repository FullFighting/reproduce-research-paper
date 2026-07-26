#!/usr/bin/env python3
"""Validate independent reviews and score one exact reproduction plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[1]
DIMENSIONS = (
    "claim_identification",
    "command_mapping",
    "data_license_handling",
    "budget_design",
    "comparison_policy",
)
DECISIONS = {
    "ACCEPTED_FOR_DETERMINISTIC_EXECUTION",
    "REVISE",
    "REJECTED_SCIENTIFIC_SCOPE",
    "REJECTED_SAFETY_OR_PRIVACY",
    "BLOCKED_DATA_OR_LICENSE",
    "BLOCKED_COMPUTE_OR_ACCESS",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def validate_review(
    review: dict[str, Any], path: Path, case_id: str, plan_hash: str
) -> None:
    required = {
        "schema_version",
        "case_id",
        "plan_sha256",
        "reviewed_at",
        "reviewer",
        "scores",
        "decision",
        "decision_reason",
        "modifications",
        "evidence_bundle",
    }
    missing = required - set(review)
    if missing:
        raise ValueError(f"{path}: missing fields {sorted(missing)}")
    if review["schema_version"] != 1:
        raise ValueError(f"{path}: unsupported schema_version")
    if review["case_id"] != case_id:
        raise ValueError(f"{path}: review case_id does not match plan")
    if review["plan_sha256"] != plan_hash:
        raise ValueError(f"{path}: review is not bound to the exact plan bytes")
    reviewer = review["reviewer"]
    if not isinstance(reviewer, dict) or reviewer.get("independent") is not True:
        raise ValueError(f"{path}: reviewer must attest independent=true")
    for field in ("id", "affiliation", "conflict_of_interest"):
        if not isinstance(reviewer.get(field), str):
            raise ValueError(f"{path}: reviewer.{field} is required")
    scores = review["scores"]
    if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
        raise ValueError(f"{path}: scores must contain exactly {list(DIMENSIONS)}")
    for dimension, value in scores.items():
        if not isinstance(value, int) or isinstance(value, bool) or value not in {0, 1, 2}:
            raise ValueError(f"{path}: {dimension} must be integer 0, 1, or 2")
    if review["decision"] not in DECISIONS:
        raise ValueError(f"{path}: invalid decision")
    if not isinstance(review["decision_reason"], str) or not review["decision_reason"].strip():
        raise ValueError(f"{path}: decision_reason is required")
    if not isinstance(review["modifications"], list):
        raise ValueError(f"{path}: modifications must be an array")
    bundle = review["evidence_bundle"]
    if not isinstance(bundle, dict) or bundle.get("status") not in {
        "UNBOUND",
        "BOUND",
        "NOT_APPLICABLE",
    }:
        raise ValueError(f"{path}: invalid evidence_bundle")
    if bundle["status"] == "BOUND":
        relative = bundle.get("path")
        expected = bundle.get("provenance_sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError(f"{path}: bound evidence requires path and provenance_sha256")
        provenance = (REPOSITORY / relative / "provenance.json").resolve()
        try:
            provenance.relative_to(REPOSITORY.resolve())
        except ValueError:
            raise ValueError(f"{path}: evidence bundle escapes repository") from None
        if not provenance.is_file() or sha256(provenance) != expected:
            raise ValueError(f"{path}: evidence provenance binding is invalid")
    else:
        if bundle.get("path") is not None or bundle.get("provenance_sha256") is not None:
            raise ValueError(f"{path}: unbound evidence must use null path and hash")


def infer_case_id(plan: dict[str, Any], explicit: str | None) -> str:
    case_id = explicit or plan.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("--case-id is required when the plan has no case_id")
    return case_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--run-dir",
        type=Path,
        help="API evaluation result directory containing initial-plan.json.",
    )
    source.add_argument(
        "--plan",
        type=Path,
        help="Any exact plan JSON, including an existing three-case pilot plan.",
    )
    parser.add_argument("--case-id")
    parser.add_argument(
        "--review", action="append", type=Path, required=True, help="Repeat per reviewer."
    )
    parser.add_argument(
        "--adjudication",
        type=Path,
        help="JSON with adjudicator_id, decision, reason, and resolved_dimensions.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        telemetry_path: Path | None = None
        if args.run_dir:
            run_dir = args.run_dir.resolve()
            plan_path = run_dir / "initial-plan.json"
            telemetry_path = run_dir / "telemetry.json"
            if not telemetry_path.is_file():
                raise ValueError(f"{run_dir} has no telemetry.json")
        else:
            plan_path = args.plan.resolve()
        plan = load_object(plan_path)
        plan_hash = sha256(plan_path)
        case_id = infer_case_id(plan, args.case_id)
        reviews: list[dict[str, Any]] = []
        reviewer_ids: set[str] = set()
        for review_path in args.review:
            resolved = review_path.resolve()
            review = load_object(resolved)
            validate_review(review, resolved, case_id, plan_hash)
            reviewer_id = review["reviewer"]["id"]
            if reviewer_id in reviewer_ids:
                raise ValueError(f"duplicate reviewer id: {reviewer_id}")
            reviewer_ids.add(reviewer_id)
            reviews.append(review)
        averages = {
            dimension: round(
                sum(review["scores"][dimension] for review in reviews) / len(reviews), 3
            )
            for dimension in DIMENSIONS
        }
        score_ranges = {
            dimension: {
                "minimum": min(review["scores"][dimension] for review in reviews),
                "maximum": max(review["scores"][dimension] for review in reviews),
            }
            for dimension in DIMENSIONS
        }
        decision_set = sorted({review["decision"] for review in reviews})
        disputed_dimensions = [
            dimension
            for dimension, values in score_ranges.items()
            if values["maximum"] - values["minimum"] > 1
        ]
        needs_adjudication = len(decision_set) > 1 or bool(disputed_dimensions)
        adjudication: dict[str, Any] | None = None
        if args.adjudication:
            adjudication = load_object(args.adjudication.resolve())
            required = {"adjudicator_id", "decision", "reason", "resolved_dimensions"}
            if required - set(adjudication):
                raise ValueError("adjudication is missing required fields")
            if adjudication["decision"] not in DECISIONS:
                raise ValueError("adjudication decision is invalid")
            if not isinstance(adjudication["resolved_dimensions"], list):
                raise ValueError("adjudication resolved_dimensions must be an array")
        status = (
            "ADJUDICATED"
            if adjudication
            else "NEEDS_ADJUDICATION"
            if needs_adjudication
            else "COMPLETE"
        )
        final_decision = (
            adjudication["decision"]
            if adjudication
            else decision_set[0]
            if len(decision_set) == 1
            else None
        )
        bundle_states = [review["evidence_bundle"] for review in reviews]
        result = {
            "schema_version": 1,
            "case_id": case_id,
            "plan": {"path": str(plan_path), "sha256": plan_hash},
            "telemetry": (
                {"path": str(telemetry_path), "sha256": sha256(telemetry_path)}
                if telemetry_path
                else None
            ),
            "review_count": len(reviews),
            "reviewer_ids": sorted(reviewer_ids),
            "average_scores": averages,
            "total_average": round(sum(averages.values()), 3),
            "score_ranges": score_ranges,
            "decisions": decision_set,
            "disputed_dimensions": disputed_dimensions,
            "adjudication_status": status,
            "adjudication": adjudication,
            "final_decision": final_decision,
            "human_modifications": [
                {
                    "reviewer_id": review["reviewer"]["id"],
                    "items": review["modifications"],
                }
                for review in reviews
            ],
            "evidence_bundle_bindings": bundle_states,
            "generated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
        }
        output = (
            args.output.resolve()
            if args.output
            else (
                args.run_dir.resolve() / "review-summary.json"
                if args.run_dir
                else plan_path.with_name(plan_path.stem + "-review-summary.json")
            )
        )
        if output.exists() and not args.force:
            raise FileExistsError(f"refusing to overwrite {output}; use --force")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "status": status,
                    "case_id": case_id,
                    "review_count": len(reviews),
                    "total_average": result["total_average"],
                    "final_decision": final_decision,
                    "output": str(output),
                },
                indent=2,
            )
        )
        return 0 if status != "NEEDS_ADJUDICATION" else 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
