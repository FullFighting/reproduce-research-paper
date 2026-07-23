#!/usr/bin/env python3
"""Run maintainer-controlled OpenAI Responses API planning evaluations locally."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
API_ENDPOINT = "https://api.openai.com/v1/responses"
OUTCOMES = [
    "ACCEPTED_FOR_DETERMINISTIC_EXECUTION",
    "REVISE",
    "REJECTED_SCIENTIFIC_SCOPE",
    "REJECTED_SAFETY_OR_PRIVACY",
    "BLOCKED_DATA_OR_LICENSE",
    "BLOCKED_COMPUTE_OR_ACCESS",
]
FORBIDDEN_SECRET_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "openai_api_key",
    "password",
    "project_credential",
    "secret",
    "secret_key",
    "service_account",
}
SECRET_VALUE = re.compile(
    r"(?:\bBearer\s+[A-Za-z0-9._~+/=-]{12,}|(?:^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{12,})",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            case = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from exc
        if not isinstance(case, dict):
            raise ValueError(f"{path}:{line_number}: case must be an object")
        validate_case(case, f"{path}:{line_number}")
        case_id = case["case_id"]
        if case_id in seen:
            raise ValueError(f"{path}:{line_number}: duplicate case_id {case_id}")
        seen.add(case_id)
        cases.append(case)
    if not cases:
        raise ValueError(f"{path} contains no cases")
    return cases


def find_secret_fields(value: Any, prefix: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            location = f"{prefix}.{key}"
            if normalized in FORBIDDEN_SECRET_KEYS or normalized.endswith("_api_key"):
                findings.append(location)
            findings.extend(find_secret_fields(item, location))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(find_secret_fields(item, f"{prefix}[{index}]"))
    elif isinstance(value, str) and SECRET_VALUE.search(value):
        findings.append(prefix)
    return findings


def validate_case(case: dict[str, Any], source: str = "case") -> None:
    required = {
        "schema_version",
        "case_id",
        "title",
        "expected_outcome",
        "paper",
        "repository",
        "constraints",
        "required_behavior",
        "evidence",
    }
    missing = required - set(case)
    if missing:
        raise ValueError(f"{source}: missing fields {sorted(missing)}")
    if case["schema_version"] != 1:
        raise ValueError(f"{source}: unsupported schema_version")
    case_id = case["case_id"]
    if (
        not isinstance(case_id, str)
        or not case_id
        or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in case_id)
    ):
        raise ValueError(f"{source}: case_id must use lowercase letters, digits, and hyphens")
    if case["expected_outcome"] not in OUTCOMES:
        raise ValueError(f"{source}: invalid expected_outcome")
    for name in ("paper", "repository", "constraints"):
        if not isinstance(case[name], dict):
            raise ValueError(f"{source}: {name} must be an object")
    if not isinstance(case["paper"].get("source_url"), str):
        raise ValueError(f"{source}: paper.source_url is required")
    repository = case["repository"]
    repository_status = repository.get("status")
    if repository_status not in {"IDENTIFIED", "NOT_IDENTIFIED"}:
        raise ValueError(
            f"{source}: repository.status must be IDENTIFIED or NOT_IDENTIFIED"
        )
    if repository_status == "NOT_IDENTIFIED":
        if repository.get("source_url") is not None or repository.get("revision") is not None:
            raise ValueError(
                f"{source}: an unidentified repository must use null source_url and revision"
            )
    elif not isinstance(repository.get("source_url"), str) or not isinstance(
        repository.get("revision"), str
    ):
        raise ValueError(
            f"{source}: an identified repository requires source_url and revision"
        )
    evidence = case["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ValueError(f"{source}: evidence must be a non-empty list")
    for index, item in enumerate(evidence):
        if not isinstance(item, dict) or not all(
            isinstance(item.get(field), str) and item[field].strip()
            for field in ("claim", "url", "retrieved_at", "note")
        ):
            raise ValueError(f"{source}: evidence[{index}] is incomplete")
    secret_fields = find_secret_fields(case)
    if secret_fields:
        raise ValueError(
            f"{source}: secret-like fields are forbidden in evaluation cases: "
            + ", ".join(secret_fields)
        )


def select_cases(
    all_cases: list[dict[str, Any]], selectors: list[str]
) -> list[dict[str, Any]]:
    if not selectors:
        return all_cases
    by_id = {case["case_id"]: case for case in all_cases}
    selected: list[dict[str, Any]] = []
    for selector in selectors:
        candidate = Path(selector)
        if candidate.is_file():
            case = load_object(candidate)
            validate_case(case, str(candidate))
        else:
            if selector not in by_id:
                raise ValueError(f"unknown case id or missing case file: {selector}")
            case = by_id[selector]
        if any(item["case_id"] == case["case_id"] for item in selected):
            raise ValueError(f"case selected more than once: {case['case_id']}")
        selected.append(case)
    return selected


def response_schema() -> dict[str, Any]:
    string_field = {"type": "string"}
    claim_item = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "claim_id": string_field,
            "claim_text": string_field,
            "paper_location": string_field,
            "executable": {"type": "boolean"},
            "scope_limitation": string_field,
        },
        "required": [
            "claim_id",
            "claim_text",
            "paper_location",
            "executable",
            "scope_limitation",
        ],
    }
    command_item = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "claim_id": string_field,
            "repository_revision": string_field,
            "argv": {"type": "array", "items": string_field},
            "observation_source": string_field,
            "extractor": string_field,
        },
        "required": [
            "claim_id",
            "repository_revision",
            "argv",
            "observation_source",
            "extractor",
        ],
    }
    review_area = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {"enum": ["READY", "INCOMPLETE", "BLOCKED", "NOT_APPLICABLE"]},
            "details": string_field,
        },
        "required": ["status", "details"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "case_id": string_field,
            "outcome": {"enum": OUTCOMES},
            "reason": string_field,
            "claim_inventory": {"type": "array", "items": claim_item},
            "command_mapping": {"type": "array", "items": command_item},
            "data_and_license": review_area,
            "budget_and_capabilities": review_area,
            "comparison_policy": review_area,
            "blocking_reasons": {"type": "array", "items": string_field},
            "evidence_requirements": {"type": "array", "items": string_field},
        },
        "required": [
            "case_id",
            "outcome",
            "reason",
            "claim_inventory",
            "command_mapping",
            "data_and_license",
            "budget_and_capabilities",
            "comparison_policy",
            "blocking_reasons",
            "evidence_requirements",
        ],
    }


def build_request(
    case: dict[str, Any],
    prompt: str,
    model: str,
    max_output_tokens: int,
    reasoning_effort: str,
) -> dict[str, Any]:
    return {
        "model": model,
        "store": False,
        "max_output_tokens": max_output_tokens,
        "reasoning": {"effort": reasoning_effort},
        "input": [
            {"role": "developer", "content": prompt},
            {
                "role": "user",
                "content": json.dumps(case, indent=2, ensure_ascii=False),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "claim_reproduction_plan",
                "strict": True,
                "schema": response_schema(),
            }
        },
    }


def extract_output_text(response: dict[str, Any]) -> str:
    direct = response.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    refusals: list[str] = []
    texts: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                texts.append(content["text"])
            if content.get("type") == "refusal" and isinstance(content.get("refusal"), str):
                refusals.append(content["refusal"])
    if texts:
        return "\n".join(texts)
    if refusals:
        raise ValueError("API refusal: " + " ".join(refusals))
    raise ValueError("response did not contain output_text")


def usage_record(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("response did not contain usage telemetry")
    details = usage.get("input_tokens_details")
    if not isinstance(details, dict):
        details = {}
    record = {
        "input_tokens": int(usage.get("input_tokens", 0)),
        "output_tokens": int(usage.get("output_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
        "cached_input_tokens": int(details.get("cached_tokens", 0)),
    }
    if any(value < 0 for value in record.values()):
        raise ValueError("response usage contains a negative token count")
    return record


def load_pricing(path: Path, model: str) -> tuple[dict[str, Any], dict[str, float]]:
    pricing = load_object(path)
    models = pricing.get("models")
    if not isinstance(models, dict) or not isinstance(models.get(model), dict):
        raise ValueError(
            f"{path} has no pricing record for {model}; update the versioned pricing "
            "snapshot before spending credits"
        )
    rates = models[model]
    for key in ("input", "cached_input", "output"):
        if not isinstance(rates.get(key), (int, float)) or rates[key] < 0:
            raise ValueError(f"{path}: invalid {model}.{key} price")
    return pricing, {key: float(rates[key]) for key in rates}


def estimate_cost(usage: dict[str, int], rates: dict[str, float]) -> float:
    cached = min(usage["cached_input_tokens"], usage["input_tokens"])
    uncached = usage["input_tokens"] - cached
    return round(
        (
            uncached * rates["input"]
            + cached * rates["cached_input"]
            + usage["output_tokens"] * rates["output"]
        )
        / 1_000_000,
        8,
    )


def preflight_cost(request_body: dict[str, Any], rates: dict[str, float]) -> float:
    # UTF-8 bytes deliberately overestimate ordinary text tokens. This is a local
    # spend guard, not billing telemetry; actual response usage remains authoritative.
    input_upper = len(canonical_bytes(request_body))
    output_cap = int(request_body["max_output_tokens"])
    return round(
        (input_upper * rates["input"] + output_cap * rates["output"]) / 1_000_000,
        8,
    )


def call_api(
    request_body: dict[str, Any], api_key: str, timeout_seconds: int
) -> tuple[dict[str, Any], int]:
    payload = canonical_bytes(request_body)
    request = urllib.request.Request(
        API_ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(body).get("error", {}).get("message", "API request failed")
        except json.JSONDecodeError:
            message = "API request failed"
        raise RuntimeError(f"OpenAI API returned HTTP {exc.code}: {message}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc.reason}") from None
    latency_ms = round((time.monotonic() - started) * 1000)
    value = json.loads(body)
    if not isinstance(value, dict):
        raise RuntimeError("OpenAI API returned a non-object response")
    return value, latency_ms


def case_output_directory(base: Path, case_id: str, multiple: bool) -> Path:
    return base / case_id if multiple else base


def persist_run(
    output: Path,
    case: dict[str, Any],
    prompt_path: Path,
    prompt: str,
    request_body: dict[str, Any],
    response: dict[str, Any],
    plan: dict[str, Any],
    usage: dict[str, int],
    latency_ms: int,
    model: str,
    pricing_path: Path,
    pricing: dict[str, Any],
    rates: dict[str, float],
    run_id: str,
) -> None:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    input_path = output / "input.json"
    prompt_copy = output / "prompt.md"
    request_path = output / "request.json"
    response_path = output / "api-response.json"
    plan_path = output / "initial-plan.json"
    pricing_copy = output / "pricing.json"
    write_json(input_path, case)
    prompt_copy.write_text(prompt, encoding="utf-8")
    write_json(request_path, request_body)
    write_json(response_path, response)
    write_json(plan_path, plan)
    write_json(pricing_copy, pricing)
    telemetry = {
        "schema_version": 1,
        "run_id": run_id,
        "case_id": case["case_id"],
        "created_at": utc_now(),
        "input": {
            "artifact": input_path.name,
            "sha256": sha256(input_path),
            "paper_source": case["paper"]["source_url"],
            "repository_source": case["repository"]["source_url"],
        },
        "prompt": {
            "version": prompt_path.stem,
            "artifact": prompt_copy.name,
            "sha256": sha256(prompt_copy),
        },
        "api": {
            "endpoint": API_ENDPOINT,
            "response_id": response.get("id"),
            "model_requested": model,
            "model_returned": response.get("model"),
            "store": False,
        },
        "usage": usage,
        "cost": {
            "status": "ESTIMATED",
            "estimated_usd": estimate_cost(usage, rates),
            "pricing_artifact": pricing_copy.name,
            "pricing_sha256": sha256(pricing_copy),
            "notice": (
                "Estimated from API token telemetry and the committed pricing snapshot; "
                "the OpenAI invoice is authoritative."
            ),
        },
        "latency_ms": latency_ms,
        "initial_plan": {
            "artifact": plan_path.name,
            "sha256": sha256(plan_path),
            "model_outcome": plan["outcome"],
            "model_reason": plan["reason"],
        },
        "human_review": {
            "status": "PENDING",
            "decision": None,
            "reason": None,
            "modifications": [],
        },
        "final_evidence_bundle": {
            "status": "UNBOUND",
            "path": None,
            "provenance_sha256": None,
            "reason": (
                "A model-generated initial plan is never bound to a final evidence "
                "bundle before independent review, approval, and deterministic execution."
            ),
        },
    }
    write_json(output / "telemetry.json", telemetry)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Maintainer-only local CLI for instrumented OpenAI API evaluations. "
            "It is not an HTTP service and never writes OPENAI_API_KEY to artifacts."
        )
    )
    parser.add_argument("--cases", type=Path, default=ROOT / "cases.jsonl")
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Case id from --cases or path to one JSON case; repeat to select multiple.",
    )
    parser.add_argument("--prompt", type=Path, default=ROOT / "prompts" / "plan-v2.md")
    parser.add_argument("--pricing", type=Path, default=ROOT / "pricing.json")
    parser.add_argument("--model", help="Explicit OpenAI model id for a paid run.")
    parser.add_argument(
        "--reasoning-effort",
        choices=["none", "low", "medium", "high", "xhigh", "max"],
        default="medium",
    )
    parser.add_argument("--max-output-tokens", type=int, default=5000)
    parser.add_argument("--max-estimated-cost-usd", type=float, default=1.0)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--send",
        action="store_true",
        help="Make paid API requests using OPENAI_API_KEY. Without this flag, preview only.",
    )
    parser.add_argument(
        "--validate-cases",
        action="store_true",
        help="Validate public cases without building or sending an API request.",
    )
    args = parser.parse_args()

    try:
        cases = load_cases(args.cases.resolve())
        selected = select_cases(cases, args.case)
        if args.validate_cases:
            print(json.dumps({"valid": True, "case_count": len(cases)}, indent=2))
            return 0
        if not args.model:
            raise ValueError("--model is required so every run records an explicit model id")
        if args.max_output_tokens <= 0 or args.timeout_seconds <= 0:
            raise ValueError("token and timeout limits must be positive")
        if args.max_estimated_cost_usd <= 0:
            raise ValueError("--max-estimated-cost-usd must be positive")
        prompt_path = args.prompt.resolve()
        prompt = prompt_path.read_text(encoding="utf-8")
        pricing_path = args.pricing.resolve()
        pricing, rates = load_pricing(pricing_path, args.model)
        requests = [
            build_request(
                case,
                prompt,
                args.model,
                args.max_output_tokens,
                args.reasoning_effort,
            )
            for case in selected
        ]
        estimates = [preflight_cost(body, rates) for body in requests]
        total_estimate = round(sum(estimates), 8)
        preview = {
            "mode": "paid-api-run" if args.send else "preview-only",
            "endpoint": API_ENDPOINT,
            "model": args.model,
            "case_ids": [case["case_id"] for case in selected],
            "prompt_version": prompt_path.stem,
            "store": False,
            "api_key_source": "OPENAI_API_KEY environment variable",
            "api_key_recorded": False,
            "preflight_cost_upper_estimate_usd": total_estimate,
            "cost_limit_usd": args.max_estimated_cost_usd,
        }
        print(json.dumps(preview, indent=2))
        if total_estimate > args.max_estimated_cost_usd:
            raise ValueError(
                "preflight estimate exceeds --max-estimated-cost-usd; reduce cases or "
                "token limits, or explicitly raise the local budget"
            )
        if not args.send:
            print("PREVIEW ONLY: no network request was made and no credits were consumed.")
            return 0
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export the maintainer-controlled key in "
                "the current shell; never put it in a case, config, or committed file."
            )
        if not args.output:
            raise ValueError("--output is required with --send")
        output = args.output.resolve()
        multiple = len(selected) > 1
        destinations = [
            case_output_directory(output, case["case_id"], multiple)
            for case in selected
        ]
        for destination in destinations:
            if destination.exists() and (
                not destination.is_dir() or any(destination.iterdir())
            ):
                raise FileExistsError(
                    "refusing a paid request because its output destination is "
                    f"not an empty directory: {destination}"
                )
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        for case, request_body, destination in zip(
            selected, requests, destinations
        ):
            response, latency_ms = call_api(
                request_body, api_key, args.timeout_seconds
            )
            plan = json.loads(extract_output_text(response))
            if not isinstance(plan, dict):
                raise ValueError("structured model output must be an object")
            if plan.get("case_id") != case["case_id"]:
                raise ValueError("structured model output changed case_id")
            if plan.get("outcome") not in OUTCOMES:
                raise ValueError("structured model output has an invalid outcome")
            usage = usage_record(response)
            persist_run(
                destination,
                case,
                prompt_path,
                prompt,
                request_body,
                response,
                plan,
                usage,
                latency_ms,
                args.model,
                pricing_path,
                pricing,
                rates,
                run_id,
            )
            print(
                json.dumps(
                    {
                        "case_id": case["case_id"],
                        "output": str(destination),
                        "tokens": usage,
                        "estimated_cost_usd": estimate_cost(usage, rates),
                        "latency_ms": latency_ms,
                        "model_outcome": plan["outcome"],
                        "expected_outcome": case["expected_outcome"],
                    },
                    indent=2,
                )
            )
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
