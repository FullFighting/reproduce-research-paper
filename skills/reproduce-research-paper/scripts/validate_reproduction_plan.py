#!/usr/bin/env python3
"""Validate a reviewable, secret-free reproduction plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path


SECRET_PATTERN = re.compile(r"(api[_-]?key|secret|token|password|webhook|credential)", re.I)
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
PAPER_CONTEXT_FIELDS = (
    "research_question",
    "method",
    "data_and_splits",
    "training_or_inference",
    "evaluation_protocol",
    "limitations",
)


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def find_secret_keys(value, prefix="") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            location = f"{prefix}.{key}" if prefix else str(key)
            if SECRET_PATTERN.search(str(key)):
                findings.append(location)
            findings.extend(find_secret_keys(child, location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_secret_keys(child, f"{prefix}[{index}]"))
    return findings


def plan_fingerprint(plan: dict) -> str:
    """Return a stable identifier for the exact reviewed plan content."""
    canonical = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate(plan: dict, plan_path: Path) -> list[str]:
    errors: list[str] = []
    repository = plan.get("repository")
    if not isinstance(repository, str) or not repository.strip():
        return ["repository must be a non-empty relative or absolute path"]
    root = (plan_path.parent / repository).resolve() if not Path(repository).is_absolute() else Path(repository).resolve()
    if not root.is_dir():
        errors.append(f"repository is not a directory: {root}")
    paper_context = plan.get("paper_context")
    if not isinstance(paper_context, dict):
        errors.append("paper_context must summarize the whole paper before execution")
    else:
        for field in PAPER_CONTEXT_FIELDS:
            if not isinstance(paper_context.get(field), str) or not paper_context[field].strip():
                errors.append(f"paper_context.{field} must be a non-empty string")
    commands = plan.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("commands must be a non-empty list")
    else:
        seen_ids: set[str] = set()
        for index, command in enumerate(commands, start=1):
            label = f"commands[{index}]"
            if not isinstance(command, dict):
                errors.append(f"{label} must be an object")
                continue
            command_id = command.get("id")
            if not isinstance(command_id, str) or not command_id.strip():
                errors.append(f"{label}.id must be a non-empty string")
            elif not SAFE_ID_PATTERN.fullmatch(command_id):
                errors.append(f"{label}.id must match {SAFE_ID_PATTERN.pattern}")
            elif command_id in seen_ids:
                errors.append(f"{label}.id duplicates {command_id!r}")
            else:
                seen_ids.add(command_id)
            argv = command.get("argv")
            if not isinstance(argv, list) or not argv or not all(isinstance(part, str) and part for part in argv):
                errors.append(f"{label}.argv must be a non-empty list of strings")
            if "command" in command or "shell" in command:
                errors.append(f"{label} must use argv; shell command strings are not allowed")
            if "env" in command or "environment" in command:
                errors.append(f"{label} must not embed environment variables or credentials")
            cwd = command.get("cwd", ".")
            if not isinstance(cwd, str) or not cwd:
                errors.append(f"{label}.cwd must be a non-empty relative path")
            elif Path(cwd).is_absolute():
                errors.append(f"{label}.cwd must be relative to repository")
            elif root.is_dir() and not is_within(root / cwd, root):
                errors.append(f"{label}.cwd must stay inside repository")
            elif root.is_dir() and not (root / cwd).resolve().is_dir():
                errors.append(f"{label}.cwd is not an existing directory")
            timeout = command.get("timeout_seconds")
            if not isinstance(timeout, int) or not 1 <= timeout <= 86400:
                errors.append(f"{label}.timeout_seconds must be an integer from 1 to 86400")
    claims = plan.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
    else:
        claim_ids: set[str] = set()
        for index, claim in enumerate(claims, start=1):
            label = f"claims[{index}]"
            if not isinstance(claim, dict):
                errors.append(f"{label} must be an object")
                continue
            for key in ("id", "paper_location", "metric"):
                if not isinstance(claim.get(key), str) or not claim[key].strip():
                    errors.append(f"{label}.{key} must be a non-empty string")
            if not isinstance(claim.get("protocol"), str) or not claim["protocol"].strip():
                errors.append(f"{label}.protocol must state the paper's evaluation procedure")
            if not isinstance(claim.get("evidence_output"), str) or not claim["evidence_output"].strip():
                errors.append(f"{label}.evidence_output must name the expected artifact or metric")
            claim_id = claim.get("id")
            if isinstance(claim_id, str):
                if claim_id in claim_ids:
                    errors.append(f"{label}.id duplicates {claim_id!r}")
                claim_ids.add(claim_id)
            if not isinstance(claim.get("expected"), (int, float)) or isinstance(claim.get("expected"), bool) or not math.isfinite(float(claim.get("expected", 0))):
                errors.append(f"{label}.expected must be numeric")
            tolerance = claim.get("tolerance")
            if not isinstance(tolerance, dict) or not tolerance:
                errors.append(f"{label}.tolerance must contain absolute and/or relative")
            elif not any(isinstance(tolerance.get(key), (int, float)) and not isinstance(tolerance.get(key), bool) and math.isfinite(float(tolerance[key])) and tolerance[key] >= 0 for key in ("absolute", "relative")):
                errors.append(f"{label}.tolerance must contain non-negative absolute and/or relative")
            command_ids = claim.get("command_ids")
            if not isinstance(command_ids, list) or not command_ids or not all(isinstance(value, str) and value for value in command_ids):
                errors.append(f"{label}.command_ids must be a non-empty list of command IDs")
            elif len(command_ids) != len(set(command_ids)):
                errors.append(f"{label}.command_ids must not contain duplicates")
            elif isinstance(commands, list):
                known_ids = {item.get("id") for item in commands if isinstance(item, dict)}
                unknown = sorted(set(command_ids) - known_ids)
                if unknown:
                    errors.append(f"{label}.command_ids reference unknown command(s): {', '.join(unknown)}")
    secret_keys = find_secret_keys(plan)
    if secret_keys:
        errors.append("plan must not contain secret-like keys: " + ", ".join(secret_keys))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"could not read plan: {exc}")
    if not isinstance(plan, dict):
        parser.error("plan root must be an object")
    errors = validate(plan, args.plan.resolve())
    output = {"valid": not errors, "errors": errors}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
