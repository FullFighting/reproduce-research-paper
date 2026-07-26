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
from value_contract import expected_spec

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
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True))
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


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _set_matches(expected: list[Any], observed: list[Any]) -> bool:
    return {_canonical(item) for item in expected} == {_canonical(item) for item in observed}


def _table_values(value: Any) -> tuple[list[str], list[str] | None, list[list[Any]]]:
    if not isinstance(value, dict):
        raise ValueError("table observation must be an object")
    columns, rows = value.get("columns"), value.get("rows")
    row_labels = value.get("row_labels")
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise ValueError("table observation must contain columns and rows")
    if not all(isinstance(row, list) and len(row) == len(columns) for row in rows):
        raise ValueError("table observation rows are not rectangular")
    if row_labels is not None and (
        not isinstance(row_labels, list) or len(row_labels) != len(rows)
    ):
        raise ValueError("table row_labels do not match rows")
    return columns, row_labels, rows


def _distribution_distance(expected: list[float], observed: list[float]) -> float:
    if len(expected) < 2 or len(observed) < 2:
        raise ValueError("distribution_distance needs at least two samples per distribution")
    points = sorted(set(expected + observed))
    return max(
        abs(
            sum(item <= point for item in expected) / len(expected)
            - sum(item <= point for item in observed) / len(observed)
        )
        for point in points
    )


def _ranking_correlation(expected: list[Any], observed: list[Any]) -> float:
    if not _set_matches(expected, observed) or len(expected) < 2:
        raise ValueError("ranking correlation needs the same unique items in both rankings")
    observed_positions = {_canonical(item): index for index, item in enumerate(observed)}
    left = [float(index) for index in range(len(expected))]
    right = [float(observed_positions[_canonical(item)]) for item in expected]
    return _pearson(left, right)


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
    typed_expected = expected_spec(claim["expected"])
    expected_type = typed_expected["type"]
    expected_value = typed_expected["value"]
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
    if not typed_expected.get("legacy"):
        base["expected_type"] = expected_type
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
        policy = claim["comparison"]
        method = policy["method"]
        aggregate = policy.get("aggregate", "mean")
        minimum_runs = int(policy.get("minimum_runs", 1))
        details: dict[str, Any] = {"method": method, "combination": policy["combination"]}

        if method == "exact_match":
            passed = observed_value == expected_value
            details["exact_match"] = passed
        elif method == "artifact_hash":
            if not isinstance(observed_value, str):
                raise ValueError("artifact_hash observation must be a string")
            passed = observed_value.lower() == str(expected_value).lower()
            details["sha256_matches"] = passed
        elif method == "set_equality":
            if not isinstance(expected_value, list) or not isinstance(observed_value, list):
                raise ValueError("set_equality requires array observations")
            passed = _set_matches(expected_value, observed_value)
            details["set_matches"] = passed
        elif method == "distribution_distance":
            expected_flat = _flatten(expected_value)
            observed_flat = _flatten(observed_value)
            distance = _distribution_distance(expected_flat, observed_flat)
            maximum = float(policy["maximum_distance"])
            passed = distance <= maximum
            details.update(
                {
                    "kolmogorov_smirnov_distance": distance,
                    "maximum_distance": maximum,
                    "expected_sample_count": len(expected_flat),
                    "observed_sample_count": len(observed_flat),
                }
            )
        elif expected_type == "ranking" and method in {
            "exact_order",
            "spearman_correlation",
        }:
            if not isinstance(expected_value, list) or not isinstance(observed_value, list):
                raise ValueError("ranking observation must be an array")
            if method == "exact_order":
                passed = observed_value == expected_value
                details["order_matches"] = passed
            else:
                correlation = _ranking_correlation(expected_value, observed_value)
                passed = correlation >= float(policy["minimum_correlation"])
                details.update(
                    {
                        "spearman_correlation": correlation,
                        "minimum_correlation": float(policy["minimum_correlation"]),
                    }
                )
        else:
            numeric_expected = expected_value
            numeric_observed = observed_value
            if expected_type == "table":
                expected_columns, expected_labels, numeric_expected = _table_values(expected_value)
                observed_columns, observed_labels, numeric_observed = _table_values(observed_value)
                if expected_columns != observed_columns:
                    raise ValueError("table column labels do not match")
                if expected_labels != observed_labels:
                    raise ValueError("table row labels do not match")
                details.update(
                    {"columns": expected_columns, "row_labels": expected_labels}
                )
            observed_flat = _flatten(numeric_observed)
            expected_flat = _flatten(numeric_expected)
            if aggregate == "none" or len(expected_flat) > 1:
                if _shape(numeric_observed) != _shape(numeric_expected):
                    raise ValueError(
                        f"shape mismatch: expected {_shape(numeric_expected)}, "
                        f"observed {_shape(numeric_observed)}"
                    )
                if method == "exact_order":
                    passed = sorted(
                        range(len(expected_flat)), key=expected_flat.__getitem__
                    ) == sorted(range(len(observed_flat)), key=observed_flat.__getitem__)
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
                    for expected, observed in zip(expected_flat, observed_flat, strict=True):
                        checks, cell_passed = _tolerance_checks(observed, expected, policy)
                        cell_results.append(
                            {
                                "expected": expected,
                                "observed": observed,
                                "absolute_error": abs(observed - expected),
                                "relative_error": abs(observed - expected)
                                / max(abs(expected), 1e-12),
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
                        "reason": f"minimum_runs={minimum_runs}, but only "
                        f"{len(observed_flat)} value(s) were observed",
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
                        "standard_deviation": statistics.stdev(observed_flat)
                        if len(observed_flat) > 1
                        else 0.0,
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
                    standard_error = statistics.stdev(observed_flat) / math.sqrt(
                        len(observed_flat)
                    )
                    confidence = float(policy.get("confidence", 0.95))
                    if confidence != 0.95:
                        raise ValueError("V1.2 supports confidence=0.95 only")
                    interval = (
                        observed - 1.96 * standard_error,
                        observed + 1.96 * standard_error,
                    )
                    checks, passed = _tolerance_checks(
                        observed, expected, policy, interval=interval
                    )
                    details.update(
                        {"confidence": confidence, "interval": list(interval), "checks": checks}
                    )
                elif method == "non_inferiority":
                    direction = policy.get("direction", "higher_is_better")
                    margins = []
                    if "absolute" in policy:
                        margins.append(float(policy["absolute"]))
                    if "relative" in policy:
                        margins.append(abs(expected) * float(policy["relative"]))
                    if "rounding_absolute" in policy:
                        margins.append(float(policy["rounding_absolute"]))
                    margin = (
                        min(margins) if policy["combination"] == "all" else max(margins)
                    )
                    passed = (
                        observed >= expected - margin
                        if direction == "higher_is_better"
                        else observed <= expected + margin
                    )
                    details.update({"direction": direction, "margin": margin, "passed": passed})
                elif method == "numeric_tolerance":
                    checks, passed = _tolerance_checks(observed, expected, policy)
                    details.update(
                        {
                            "absolute_error": abs(observed - expected),
                            "relative_error": abs(observed - expected)
                            / max(abs(expected), 1e-12),
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
