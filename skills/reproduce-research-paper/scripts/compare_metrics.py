#!/usr/bin/env python3
"""Recompute claim comparisons from traceable observation artifacts."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

from evidence_common import object_sha256, read_json, sha256_file, write_json


REPRODUCED = "CLAIM_REPRODUCED_WITHIN_TOLERANCE"
NOT_REPRODUCED = "CLAIM_NOT_REPRODUCED"
PARTIAL = "PARTIALLY_REPRODUCED"
INCONCLUSIVE = "INCONCLUSIVE"
BLOCKED = "BLOCKED"
NOT_ATTEMPTED = "NOT_ATTEMPTED"
MANUAL = "MANUAL_REVIEW_REQUIRED"


def _flatten(value: Any) -> list[float]:
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite number")
        return [number]
    if isinstance(value, list):
        result: list[float] = []
        for item in value:
            result.extend(_flatten(item))
        return result
    raise ValueError("value is not a numeric scalar or array")


def _shape(value: Any) -> tuple[int, ...]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return ()
    if not isinstance(value, list):
        raise ValueError("value is not numeric")
    if not value:
        return (0,)
    children = [_shape(item) for item in value]
    if any(item != children[0] for item in children):
        raise ValueError("ragged arrays cannot be compared")
    return (len(value), *children[0])


def _rank(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    position = 0
    while position < len(indexed):
        end = position + 1
        while end < len(indexed) and indexed[end][1] == indexed[position][1]:
            end += 1
        rank = (position + 1 + end) / 2.0
        for original_index, _ in indexed[position:end]:
            result[original_index] = rank
        position = end
    return result


def _pearson(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("correlation needs equally sized arrays with at least two values")
    left_mean, right_mean = statistics.fmean(left), statistics.fmean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    denominator = math.sqrt(
        sum((a - left_mean) ** 2 for a in left) * sum((b - right_mean) ** 2 for b in right)
    )
    if denominator == 0:
        raise ValueError("correlation is undefined for a constant array")
    return numerator / denominator


def _combine(checks: list[bool], policy: str) -> bool:
    if not checks:
        return False
    return all(checks) if policy == "all" else any(checks)


def _tolerance_checks(
    observed: float,
    expected: float,
    policy: dict,
    *,
    interval: tuple[float, float] | None = None,
) -> tuple[list[dict], bool]:
    absolute_error = abs(observed - expected)
    relative_error = absolute_error / max(abs(expected), 1e-12)
    checks: list[dict] = []
    if "absolute" in policy:
        tolerance = float(policy["absolute"])
        passed = absolute_error <= tolerance
        if interval:
            passed = interval[0] >= expected - tolerance and interval[1] <= expected + tolerance
        checks.append({"kind": "absolute", "limit": tolerance, "passed": passed})
    if "relative" in policy:
        tolerance = float(policy["relative"])
        passed = relative_error <= tolerance
        if interval:
            margin = abs(expected) * tolerance
            passed = interval[0] >= expected - margin and interval[1] <= expected + margin
        checks.append({"kind": "relative", "limit": tolerance, "passed": passed})
    if "rounding_absolute" in policy:
        tolerance = float(policy["rounding_absolute"])
        passed = absolute_error <= tolerance
        if interval:
            passed = interval[0] >= expected - tolerance and interval[1] <= expected + tolerance
        checks.append({"kind": "rounding_absolute", "limit": tolerance, "passed": passed})
    return checks, _combine([item["passed"] for item in checks], policy["combination"])


def compare_claim(claim: dict, observation: dict, invalidation_reasons: list[str]) -> dict:
    base = {
        "claim_id": claim["id"],
        "metric": claim["metric"],
        "paper_location": claim["paper_location"],
        "expected": claim["expected"],
        "unit": claim.get("unit", "unitless"),
        "observation_source_sha256": observation.get("source_sha256"),
        "extractor": observation.get("extractor"),
        "extractor_version": observation.get("extractor_version"),
    }
    if invalidation_reasons:
        return {
            **base,
            "status": INCONCLUSIVE,
            "reason": "execution evidence was invalidated",
            "invalidation_reasons": invalidation_reasons,
        }
    if observation.get("status") == MANUAL:
        return {**base, "status": MANUAL, "reason": observation.get("reason")}
    if observation.get("status") != "EXTRACTED":
        return {
            **base,
            "status": BLOCKED,
            "reason": observation.get("reason", "machine observation was not extracted"),
        }
    try:
        observed_value = observation["normalized_value"]
        expected_value = claim["expected"]
        observed_flat = _flatten(observed_value)
        expected_flat = _flatten(expected_value)
        policy = claim["comparison"]
        method = policy["method"]
        aggregate = policy.get("aggregate", "mean")
        minimum_runs = int(policy.get("minimum_runs", 1))
        details: dict[str, Any] = {"method": method, "combination": policy["combination"]}
        if aggregate == "none" or len(expected_flat) > 1:
            if _shape(observed_value) != _shape(expected_value):
                raise ValueError(
                    f"shape mismatch: expected {_shape(expected_value)}, observed {_shape(observed_value)}"
                )
            if method == "exact_order":
                passed = sorted(range(len(expected_flat)), key=expected_flat.__getitem__) == sorted(
                    range(len(observed_flat)), key=observed_flat.__getitem__
                )
                details["order_matches"] = passed
            elif method == "spearman_correlation":
                correlation = _pearson(_rank(expected_flat), _rank(observed_flat))
                passed = correlation >= float(policy["minimum_correlation"])
                details.update(
                    {
                        "spearman_correlation": correlation,
                        "minimum_correlation": float(policy["minimum_correlation"]),
                    }
                )
            else:
                cell_results = []
                for expected, observed in zip(expected_flat, observed_flat):
                    checks, cell_passed = _tolerance_checks(observed, expected, policy)
                    cell_results.append(
                        {
                            "expected": expected,
                            "observed": observed,
                            "absolute_error": abs(observed - expected),
                            "relative_error": abs(observed - expected) / max(abs(expected), 1e-12),
                            "checks": checks,
                            "passed": cell_passed,
                        }
                    )
                passed = all(item["passed"] for item in cell_results)
                details["cells"] = cell_results
        else:
            if len(observed_flat) < minimum_runs:
                return {
                    **base,
                    "observed": observed_value,
                    "status": INCONCLUSIVE,
                    "reason": f"minimum_runs={minimum_runs}, but only {len(observed_flat)} value(s) were observed",
                }
            observed = (
                statistics.fmean(observed_flat)
                if aggregate == "mean"
                else statistics.median(observed_flat)
                if aggregate == "median"
                else observed_flat[0]
            )
            expected = expected_flat[0]
            details.update(
                {
                    "aggregate": aggregate,
                    "run_count": len(observed_flat),
                    "mean": statistics.fmean(observed_flat),
                    "standard_deviation": statistics.stdev(observed_flat) if len(observed_flat) > 1 else 0.0,
                }
            )
            if method == "equivalence_interval":
                if len(observed_flat) < 2:
                    return {
                        **base,
                        "observed": observed_value,
                        "status": INCONCLUSIVE,
                        "reason": "equivalence_interval requires at least two observations",
                    }
                standard_error = statistics.stdev(observed_flat) / math.sqrt(len(observed_flat))
                confidence = float(policy.get("confidence", 0.95))
                if confidence != 0.95:
                    raise ValueError("V1 supports confidence=0.95 only")
                interval = (observed - 1.96 * standard_error, observed + 1.96 * standard_error)
                checks, passed = _tolerance_checks(observed, expected, policy, interval=interval)
                details.update({"confidence": confidence, "interval": list(interval), "checks": checks})
            elif method == "non_inferiority":
                direction = policy.get("direction", "higher_is_better")
                margins = []
                if "absolute" in policy:
                    margins.append(float(policy["absolute"]))
                if "relative" in policy:
                    margins.append(abs(expected) * float(policy["relative"]))
                if "rounding_absolute" in policy:
                    margins.append(float(policy["rounding_absolute"]))
                margin = min(margins) if policy["combination"] == "all" else max(margins)
                passed = observed >= expected - margin if direction == "higher_is_better" else observed <= expected + margin
                details.update({"direction": direction, "margin": margin, "passed": passed})
            elif method == "numeric_tolerance":
                checks, passed = _tolerance_checks(observed, expected, policy)
                details.update(
                    {
                        "absolute_error": abs(observed - expected),
                        "relative_error": abs(observed - expected) / max(abs(expected), 1e-12),
                        "checks": checks,
                    }
                )
            else:
                raise ValueError(f"{method} requires aggregate=none and array values")
        return {
            **base,
            "observed": observed_value,
            "status": REPRODUCED if passed else NOT_REPRODUCED,
            "details": details,
        }
    except (KeyError, TypeError, ValueError, statistics.StatisticsError) as exc:
        return {**base, "status": INCONCLUSIVE, "reason": str(exc)}


def compare_all(plan: dict, observations: dict, run_record: dict) -> dict:
    by_claim = {
        item.get("claim_id"): item for item in observations.get("observations", [])
        if isinstance(item, dict)
    }
    invalidation_reasons: list[str] = []
    repository_integrity = run_record.get("repository_integrity", {})
    if repository_integrity.get("source_tree_changed"):
        invalidation_reasons.append("original source tree changed during execution")
    if repository_integrity.get("workspace_core_changed"):
        invalidation_reasons.append("execution modified files outside declared write_paths")
    if run_record.get("policy_violations"):
        invalidation_reasons.extend(str(item) for item in run_record["policy_violations"])
    command_records = {item.get("id"): item for item in run_record.get("commands", [])}
    results = []
    for claim in plan.get("claims", []):
        observation = by_claim.get(claim["id"])
        if observation is None:
            results.append(
                {
                    "claim_id": claim["id"],
                    "metric": claim["metric"],
                    "status": BLOCKED,
                    "reason": "no traceable observation artifact exists",
                }
            )
            continue
        command_failures = [
            command_id for command_id in claim.get("command_ids", [])
            if command_id not in command_records
            or command_records[command_id].get("exit_code") != 0
            or command_records[command_id].get("timed_out")
        ]
        if command_failures:
            results.append(
                {
                    "claim_id": claim["id"],
                    "metric": claim["metric"],
                    "status": BLOCKED,
                    "reason": "required command(s) did not complete: " + ", ".join(command_failures),
                }
            )
        else:
            results.append(compare_claim(claim, observation, invalidation_reasons))
    statuses = [
        REPRODUCED, NOT_REPRODUCED, PARTIAL, INCONCLUSIVE, BLOCKED, NOT_ATTEMPTED, MANUAL
    ]
    return {
        "schema_version": 1,
        "plan_sha256": object_sha256(plan),
        "observations_sha256": object_sha256(observations),
        "run_record_sha256": object_sha256(run_record),
        "claims": results,
        "summary": {status: sum(item["status"] == status for item in results) for status in statuses},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    try:
        plan = read_json(bundle / "plan.json")
        observations = read_json(bundle / "observations.json")
        run_record = read_json(bundle / "run-record.json")
        if observations.get("run_record_sha256") != sha256_file(bundle / "run-record.json"):
            raise ValueError("observations are not bound to this run-record.json")
        result = compare_all(plan, observations, run_record)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
