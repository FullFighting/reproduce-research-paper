#!/usr/bin/env python3
"""Compare plan-declared numeric claims with observed metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from validate_reproduction_plan import plan_fingerprint


def load_observed(path: Path) -> tuple[dict[str, float], dict[str, float]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    by_metric: dict[str, float] = {}
    by_claim: dict[str, float] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                by_metric[key] = float(value)
        return by_metric, by_claim
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("value"), (int, float)) or isinstance(item.get("value"), bool):
                continue
            if isinstance(item.get("metric"), str):
                by_metric[item["metric"]] = float(item["value"])
            if isinstance(item.get("claim_id"), str):
                by_claim[item["claim_id"]] = float(item["value"])
        return by_metric, by_claim
    raise ValueError("observed metrics must be an object or list")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--observed", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        by_metric, by_claim = load_observed(args.observed)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    results = []
    for claim in plan.get("claims", []):
        expected = float(claim["expected"])
        observed = by_claim.get(claim["id"], by_metric.get(claim["metric"]))
        if observed is None:
            results.append({"claim_id": claim["id"], "metric": claim["metric"], "status": "blocked", "reason": "observed metric missing"})
            continue
        absolute_error = abs(observed - expected)
        relative_error = absolute_error / max(abs(expected), 1e-12)
        tolerance = claim["tolerance"]
        allowed = []
        if isinstance(tolerance.get("absolute"), (int, float)):
            allowed.append(absolute_error <= float(tolerance["absolute"]))
        if isinstance(tolerance.get("relative"), (int, float)):
            allowed.append(relative_error <= float(tolerance["relative"]))
        results.append({
            "claim_id": claim["id"], "metric": claim["metric"], "expected": expected, "observed": observed,
            "absolute_error": absolute_error, "relative_error": relative_error,
            "status": "verified" if any(allowed) else "contradicted",
        })
    summary = {status: sum(item["status"] == status for item in results) for status in ("verified", "contradicted", "blocked")}
    payload = {
        "plan_sha256": plan_fingerprint(plan),
        "observed_sha256": sha256_file(args.observed),
        "claims": results,
        "summary": summary,
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
