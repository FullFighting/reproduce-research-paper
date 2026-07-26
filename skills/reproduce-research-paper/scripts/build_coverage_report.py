#!/usr/bin/env python3
"""Aggregate verified evidence bundles into a whole-paper coverage report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_report import verify_bundle
from compare_metrics import (
    BLOCKED,
    INCONCLUSIVE,
    MANUAL,
    NOT_ATTEMPTED,
    NOT_REPRODUCED,
    PARTIAL,
    REPRODUCED,
)
from evidence_common import object_sha256, read_json, sha256_file, write_json
from validate_paper_claims_map import cross_check_plan, validate_claims_map

DISCLAIMER = (
    "This result verifies only the declared computational claim under the recorded "
    "environment and protocol."
)
COVERAGE_DISCLAIMER = (
    "Whole-paper coverage means every mapped claim received an explicit status; "
    "it does not mean the paper's scientific conclusions are true."
)


def aggregate_status(statuses: list[str]) -> str:
    if not statuses:
        return NOT_ATTEMPTED
    if all(status == statuses[0] for status in statuses):
        return statuses[0]
    if any(status == REPRODUCED for status in statuses):
        return PARTIAL
    if any(status == NOT_REPRODUCED for status in statuses):
        return NOT_REPRODUCED
    if any(status == INCONCLUSIVE for status in statuses):
        return INCONCLUSIVE
    if any(status == MANUAL for status in statuses):
        return MANUAL
    if any(status == BLOCKED for status in statuses):
        return BLOCKED
    return NOT_ATTEMPTED


def _collect_bundle_evidence(
    bundles: list[Path], errors: list[str]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    evidence: dict[str, dict[str, Any]] = {}
    bundle_records: list[dict[str, Any]] = []
    for bundle in bundles:
        bundle_errors = verify_bundle(bundle)
        if bundle_errors:
            errors.extend(f"bundle {bundle}: {item}" for item in bundle_errors)
            continue
        plan = read_json(bundle / "plan.json")
        comparison = read_json(bundle / "comparison.json")
        bundle_records.append(
            {
                "bundle": str(bundle),
                "plan_sha256": object_sha256(plan),
                "comparison_sha256": sha256_file(bundle / "comparison.json"),
                "plan": plan,
            }
        )
        for item in comparison.get("claims", []):
            claim_id = item.get("claim_id")
            if not isinstance(claim_id, str):
                continue
            record = {
                "status": item.get("status", INCONCLUSIVE),
                "bundle": str(bundle),
                "expected": item.get("expected"),
                "observed": item.get("observed"),
                "reason": item.get("reason"),
            }
            existing = evidence.get(claim_id)
            if existing is None:
                evidence[claim_id] = record
            elif existing["status"] != record["status"]:
                evidence[claim_id] = {
                    "status": INCONCLUSIVE,
                    "bundle": f"{existing['bundle']} vs {bundle}",
                    "expected": item.get("expected"),
                    "observed": None,
                    "reason": "conflicting statuses across bundles",
                }
    return evidence, bundle_records


def resolve_statuses(
    claims_map: dict, evidence: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}
    claims = [claim for claim in claims_map.get("claims", []) if isinstance(claim, dict)]
    for claim in claims:
        if claim.get("claim_type") == "conclusion":
            continue
        claim_id = claim["id"]
        disposition = claim.get("disposition")
        if disposition == "manual_review":
            resolved[claim_id] = {"status": MANUAL, "reason": claim.get("reason")}
        elif disposition == "not_reproducible":
            resolved[claim_id] = {"status": BLOCKED, "reason": claim.get("reason")}
        elif disposition == "not_attempted":
            resolved[claim_id] = {"status": NOT_ATTEMPTED, "reason": claim.get("reason")}
        else:
            statuses: list[str] = []
            supporting: list[dict[str, Any]] = []
            for plan_claim_id in claim.get("plan_claim_ids", []):
                record = evidence.get(plan_claim_id)
                if record is None:
                    statuses.append(NOT_ATTEMPTED)
                    supporting.append(
                        {
                            "plan_claim_id": plan_claim_id,
                            "status": NOT_ATTEMPTED,
                            "reason": "no verified bundle contains this claim",
                        }
                    )
                else:
                    statuses.append(record["status"])
                    supporting.append({"plan_claim_id": plan_claim_id, **record})
            resolved[claim_id] = {
                "status": aggregate_status(statuses),
                "evidence": supporting,
            }
    for claim in claims:
        if claim.get("claim_type") != "conclusion":
            continue
        statuses = [
            resolved.get(reference, {}).get("status", NOT_ATTEMPTED)
            for reference in claim.get("supported_by", [])
        ]
        if claim.get("disposition") != "reproduce":
            status = {
                "manual_review": MANUAL,
                "not_reproducible": BLOCKED,
                "not_attempted": NOT_ATTEMPTED,
            }.get(claim.get("disposition"), INCONCLUSIVE)
            resolved[claim["id"]] = {"status": status, "reason": claim.get("reason")}
        else:
            resolved[claim["id"]] = {
                "status": aggregate_status(statuses),
                "supported_by": dict(
                    zip(claim.get("supported_by", []), statuses, strict=True)
                ),
            }
    return resolved


def _truncate(value: str, limit: int = 160) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_coverage_report(
    claims_map: dict,
    resolved: dict[str, dict[str, Any]],
    bundle_records: list[dict[str, Any]],
    overall: str,
) -> str:
    paper = claims_map.get("paper", {})
    coverage = claims_map.get("coverage", {})
    claims = [claim for claim in claims_map.get("claims", []) if isinstance(claim, dict)]
    counts: dict[str, int] = {}
    for claim in claims:
        status = resolved.get(claim["id"], {}).get("status", NOT_ATTEMPTED)
        counts[status] = counts.get(status, 0) + 1
    lines = [
        "# Whole-paper coverage report",
        "",
        f"**Overall status:** `{overall}`",
        "",
        f"> {DISCLAIMER}",
        ">",
        f"> {COVERAGE_DISCLAIMER}",
        "",
        "## Paper",
        "",
        f"- Title: {paper.get('title', 'not supplied')}",
        f"- Reference: {paper.get('reference', 'not supplied')}",
        f"- Read completely: `{json.dumps(coverage.get('read_completely'))}`",
        f"- Sections read: {', '.join(coverage.get('sections', [])) or 'not recorded'}",
        f"- Claims map SHA-256: `{object_sha256(claims_map)}`",
        "",
        "## Coverage summary",
        "",
        f"- Mapped claims: {len(claims)}",
    ]
    for status in sorted(counts):
        lines.append(f"- `{status}`: {counts[status]}")
    excluded = coverage.get("excluded_content", [])
    if excluded:
        lines.extend(["", "### Explicitly excluded content", ""])
        for item in excluded:
            lines.append(f"- {item.get('location')}: {item.get('reason')}")
    lines.extend(
        [
            "",
            "## Claim coverage",
            "",
            "| Claim | Type | Location | Paper quote | Paper values | Disposition | Status |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for claim in claims:
        record = resolved.get(claim["id"], {})
        lines.append(
            f"| {claim['id']} | {claim.get('claim_type', '')} | "
            f"{claim.get('paper_location', '')} | {_truncate(claim.get('paper_quote', ''))} | "
            f"{', '.join(claim.get('paper_values', [])) or '—'} | "
            f"{claim.get('disposition', '')} | `{record.get('status', NOT_ATTEMPTED)}` |"
        )
        if claim.get("claim_type") == "conclusion" and record.get("supported_by"):
            supports = ", ".join(
                f"{reference} → `{status}`"
                for reference, status in record["supported_by"].items()
            )
            lines.append(f"| ↳ |  |  | supported by: {supports} |  |  |  |")
    lines.extend(["", "## Evidence bundles", ""])
    if bundle_records:
        for record in bundle_records:
            lines.extend(
                [
                    f"- `{record['bundle']}`",
                    f"  - plan SHA-256: `{record['plan_sha256']}`",
                    f"  - comparison SHA-256: `{record['comparison_sha256']}`",
                ]
            )
    else:
        lines.append("- No verified evidence bundles were supplied.")
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            f"- {DISCLAIMER}",
            f"- {COVERAGE_DISCLAIMER}",
            "- Conclusion claims inherit status from their supporting computational "
            "claims; they are never verified by prose agreement alone.",
            "- Manual tables, figures, and images are never promoted to a reproduced "
            "claim; they remain `MANUAL_REVIEW_REQUIRED`.",
            "",
        ]
    )
    return "\n".join(lines)


def build_coverage(
    claims_map_path: Path, bundles: list[Path], output: Path | None
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    claims_map = read_json(claims_map_path)
    errors.extend(validate_claims_map(claims_map))
    if errors:
        return {}, errors
    evidence, bundle_records = _collect_bundle_evidence(bundles, errors)
    for record in bundle_records:
        errors.extend(
            f"bundle {record['bundle']}: {item}"
            for item in cross_check_plan(claims_map, record["plan"])
        )
    if errors:
        return {}, errors
    resolved = resolve_statuses(claims_map, evidence)
    overall = aggregate_status([record["status"] for record in resolved.values()])
    report = render_coverage_report(claims_map, resolved, bundle_records, overall)
    payload = {
        "overall_status": overall,
        "claims_map_sha256": object_sha256(claims_map),
        "claims": {
            claim_id: record for claim_id, record in sorted(resolved.items())
        },
        "bundles": [
            {key: value for key, value in record.items() if key != "plan"}
            for record in bundle_records
        ],
    }
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / "coverage.json", payload)
        (output / "coverage-report.md").write_text(report, encoding="utf-8")
    return payload, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", dest="claims_map", required=True, type=Path)
    parser.add_argument(
        "--bundle",
        action="append",
        default=[],
        type=Path,
        help="Verified evidence bundle directory; repeat for multiple bundles",
    )
    parser.add_argument("--output", type=Path, help="Directory for coverage.json and coverage-report.md")
    args = parser.parse_args()
    try:
        payload, errors = build_coverage(
            args.claims_map.resolve(),
            [bundle.resolve() for bundle in args.bundle],
            args.output.resolve() if args.output else None,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        payload, errors = {}, [str(exc)]
    print(
        json.dumps(
            {"valid": not errors, "errors": errors, **payload},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
