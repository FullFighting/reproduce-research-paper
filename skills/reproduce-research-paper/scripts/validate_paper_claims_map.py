#!/usr/bin/env python3
"""Validate a whole-paper claims map and its paper-grounded expected values."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

from evidence_common import read_json
from value_contract import expected_spec, finite_number

SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
NUMBER_PATTERN = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][+-]?\d+)?")
CLAIM_TYPES = {"quantitative", "conclusion", "qualitative", "visual", "theoretical"}
DISPOSITIONS = {"reproduce", "manual_review", "not_reproducible", "not_attempted"}
REPRODUCIBLE_TYPES = {"quantitative", "conclusion"}


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_coverage(coverage: Any, errors: list[str]) -> None:
    if not isinstance(coverage, dict):
        errors.append("coverage must declare whole-paper reading")
        return
    if coverage.get("read_completely") is not True:
        errors.append("coverage.read_completely must be true; partial reading cannot ground a whole-paper map")
    sections = coverage.get("sections")
    if (
        not isinstance(sections, list)
        or not sections
        or not all(_non_empty_string(item) for item in sections)
    ):
        errors.append("coverage.sections must list every paper section that was read")
    excluded = coverage.get("excluded_content", [])
    if not isinstance(excluded, list):
        errors.append("coverage.excluded_content must be a list")
    else:
        for index, item in enumerate(excluded):
            if (
                not isinstance(item, dict)
                or set(item) != {"location", "reason"}
                or not _non_empty_string(item.get("location"))
                or not _non_empty_string(item.get("reason"))
            ):
                errors.append(
                    f"coverage.excluded_content[{index}] must contain a non-empty location and reason"
                )


def _validate_id_list(value: Any, label: str, errors: list[str]) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item for item in value)
    ):
        errors.append(f"{label} must be a non-empty list of IDs")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label} must not contain duplicates")
    return [item for item in value if isinstance(item, str)]


def _validate_claim(claim: dict, label: str, errors: list[str]) -> None:
    claim_type = claim.get("claim_type")
    disposition = claim.get("disposition")
    quote = claim.get("paper_quote")
    for key in ("paper_location", "paper_quote"):
        if not _non_empty_string(claim.get(key)):
            errors.append(f"{label}.{key} must be a non-empty string")
    if not isinstance(claim_type, str) or claim_type not in CLAIM_TYPES:
        errors.append(f"{label}.claim_type must be one of {sorted(CLAIM_TYPES)}")
        return
    if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
        errors.append(f"{label}.disposition must be one of {sorted(DISPOSITIONS)}")
        return
    if disposition != "reproduce" and not _non_empty_string(claim.get("reason")):
        errors.append(f"{label}.reason must explain why the claim is not reproduced")
    if disposition == "reproduce" and claim_type not in REPRODUCIBLE_TYPES:
        errors.append(
            f"{label}.disposition reproduce is only valid for quantitative or conclusion claims"
        )
    if claim_type == "visual" and disposition != "manual_review":
        errors.append(f"{label} visual claims must keep disposition manual_review")
    paper_values = claim.get("paper_values", [])
    if not isinstance(paper_values, list) or not all(
        _non_empty_string(item) for item in paper_values
    ):
        errors.append(f"{label}.paper_values must be a list of non-empty strings")
        paper_values = []
    if claim_type == "quantitative" and not paper_values:
        errors.append(f"{label}.paper_values must quote the paper's reported values")
    if isinstance(quote, str):
        for index, value in enumerate(paper_values):
            if isinstance(value, str) and value not in quote:
                errors.append(
                    f"{label}.paper_values[{index}] {value!r} does not appear verbatim in paper_quote"
                )
    if claim_type == "conclusion":
        if "plan_claim_ids" in claim:
            errors.append(
                f"{label} conclusion claims are verified only through supported_by, "
                "not direct plan_claim_ids"
            )
        _validate_id_list(claim.get("supported_by"), f"{label}.supported_by", errors)
    else:
        if "supported_by" in claim:
            errors.append(f"{label}.supported_by is only valid for conclusion claims")
        if disposition == "reproduce":
            _validate_id_list(claim.get("plan_claim_ids"), f"{label}.plan_claim_ids", errors)
        elif "plan_claim_ids" in claim:
            errors.append(f"{label}.plan_claim_ids is only valid when disposition is reproduce")


def validate_claims_map(claims_map: Any) -> list[str]:
    if not isinstance(claims_map, dict):
        return ["claims map root must be an object"]
    errors: list[str] = []
    schema_version = claims_map.get("schema_version")
    if schema_version != 1 or isinstance(schema_version, bool):
        errors.append("schema_version must be 1")
    paper = claims_map.get("paper")
    if not isinstance(paper, dict) or not _non_empty_string(paper.get("title")):
        errors.append("paper.title must identify the paper being mapped")
    _validate_coverage(claims_map.get("coverage"), errors)
    claims = claims_map.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list covering the whole paper")
        return errors
    claim_ids: set[str] = set()
    claim_types: dict[str, str] = {}
    for index, claim in enumerate(claims):
        label = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{label} must be an object")
            continue
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not SAFE_ID_PATTERN.fullmatch(claim_id):
            errors.append(f"{label}.id must match {SAFE_ID_PATTERN.pattern}")
        elif claim_id in claim_ids:
            errors.append(f"{label}.id duplicates {claim_id!r}")
        else:
            claim_ids.add(claim_id)
            if isinstance(claim.get("claim_type"), str):
                claim_types[claim_id] = claim["claim_type"]
        _validate_claim(claim, label, errors)
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict) or claim.get("claim_type") != "conclusion":
            continue
        label = f"claims[{index}]"
        supported_by = claim.get("supported_by")
        if not isinstance(supported_by, list):
            continue
        for reference in supported_by:
            if not isinstance(reference, str):
                continue
            if reference == claim.get("id"):
                errors.append(f"{label}.supported_by must not reference the conclusion itself")
            elif reference not in claim_ids:
                errors.append(f"{label}.supported_by references unknown claim {reference!r}")
            elif claim_types.get(reference) == "conclusion":
                errors.append(
                    f"{label}.supported_by must reference non-conclusion claims, not {reference!r}"
                )
    return errors


def _paper_number_candidates(paper_values: list[str]) -> list[float]:
    candidates: list[float] = []
    for value in paper_values:
        for match in NUMBER_PATTERN.finditer(value):
            try:
                number = float(match.group(0).replace(",", ""))
            except ValueError:
                continue
            candidates.append(number)
            if "%" in value:
                candidates.append(number / 100.0)
    return candidates


def _matches_any(leaf: float, candidates: list[float]) -> bool:
    return any(
        math.isclose(float(leaf), candidate, rel_tol=1e-9, abs_tol=1e-12)
        for candidate in candidates
    )


def _grounding_errors(
    expected_type: str,
    value: Any,
    quote: str,
    paper_values: list[str],
    label: str,
) -> list[str]:
    errors: list[str] = []
    candidates = _paper_number_candidates(paper_values)
    quote_lower = quote.lower()

    def check_leaf(leaf: Any) -> None:
        if finite_number(leaf):
            if not _matches_any(leaf, candidates):
                errors.append(f"{label} expected number {leaf!r} is not quoted in paper_values")
        elif isinstance(leaf, bool):
            if str(leaf).lower() not in quote_lower:
                errors.append(f"{label} expected value {leaf!r} does not appear in paper_quote")
        elif isinstance(leaf, str):
            if leaf.lower() not in quote_lower:
                errors.append(f"{label} expected text {leaf!r} does not appear in paper_quote")
        elif isinstance(leaf, list):
            for item in leaf:
                check_leaf(item)
        elif leaf is not None:
            errors.append(f"{label} expected value {leaf!r} cannot be grounded in the paper")

    if expected_type == "table" and isinstance(value, dict):
        check_leaf(value.get("rows"))
    elif expected_type == "artifact_hash" and isinstance(value, str):
        haystack = quote_lower + " " + " ".join(item.lower() for item in paper_values)
        if value.lower() not in haystack:
            errors.append(f"{label} expected artifact hash is not published in the paper text")
    else:
        check_leaf(value)
    return errors


def cross_check_plan(claims_map: dict, plan: dict) -> list[str]:
    """Require every plan claim to be grounded in a verbatim paper quote."""
    errors: list[str] = []
    plan_claims: dict[str, dict] = {
        claim["id"]: claim
        for claim in plan.get("claims", [])
        if isinstance(claim, dict) and isinstance(claim.get("id"), str)
    }
    referenced: set[str] = set()
    for index, claim in enumerate(claims_map.get("claims", [])):
        if not isinstance(claim, dict):
            continue
        label = f"claims[{index}]"
        plan_claim_ids = claim.get("plan_claim_ids")
        if not isinstance(plan_claim_ids, list):
            continue
        quote = claim.get("paper_quote")
        paper_values = claim.get("paper_values", [])
        if not isinstance(quote, str):
            quote = ""
        if not isinstance(paper_values, list):
            paper_values = []
        for plan_claim_id in plan_claim_ids:
            if not isinstance(plan_claim_id, str):
                continue
            referenced.add(plan_claim_id)
            plan_claim = plan_claims.get(plan_claim_id)
            if plan_claim is None:
                errors.append(f"{label}.plan_claim_ids references unknown plan claim {plan_claim_id!r}")
                continue
            spec = expected_spec(plan_claim.get("expected"))
            errors.extend(
                _grounding_errors(
                    spec.get("type", "scalar"),
                    spec.get("value"),
                    quote,
                    [item for item in paper_values if isinstance(item, str)],
                    f"{label} (plan claim {plan_claim_id!r}):",
                )
            )
    for plan_claim_id in sorted(set(plan_claims) - referenced):
        errors.append(
            f"plan claim {plan_claim_id!r} has no paper grounding in the claims map; "
            "expected values must come from the paper"
        )
    return errors


def summarize(claims_map: dict) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    by_disposition: dict[str, int] = {}
    claims = claims_map.get("claims", [])
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_type = claim.get("claim_type")
        disposition = claim.get("disposition")
        if isinstance(claim_type, str):
            by_type[claim_type] = by_type.get(claim_type, 0) + 1
        if isinstance(disposition, str):
            by_disposition[disposition] = by_disposition.get(disposition, 0) + 1
    return {
        "claims": len(claims) if isinstance(claims, list) else 0,
        "by_type": dict(sorted(by_type.items())),
        "by_disposition": dict(sorted(by_disposition.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", dest="claims_map", required=True, type=Path)
    parser.add_argument(
        "--plan",
        action="append",
        default=[],
        type=Path,
        help="Reproduction plan(s) whose expected values must be grounded in the map",
    )
    args = parser.parse_args()
    try:
        claims_map = read_json(args.claims_map)
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"could not read claims map: {exc}")
    errors = validate_claims_map(claims_map)
    if not errors:
        for plan_path in args.plan:
            try:
                plan = read_json(plan_path)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"could not read plan {plan_path}: {exc}")
                continue
            if not isinstance(plan, dict):
                errors.append(f"plan root must be an object: {plan_path}")
                continue
            errors.extend(cross_check_plan(claims_map, plan))
    payload = {
        "valid": not errors,
        "errors": errors,
        "summary": summarize(claims_map) if isinstance(claims_map, dict) else {},
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
