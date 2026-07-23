#!/usr/bin/env python3
"""Validate a traceable, secret-reference-only reproduction plan."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

from evidence_common import (
    SECRET_NAME_PATTERN,
    SECRET_REF_PATTERN,
    contains_high_confidence_secret,
    is_within,
    object_sha256,
    safe_relative_path,
)


SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
PAPER_CONTEXT_FIELDS = (
    "research_question",
    "method",
    "data_and_splits",
    "training_or_inference",
    "evaluation_protocol",
    "limitations",
)
SENSITIVE_FLAGS = re.compile(
    r"^(?:--?(?:api[_-]?key|access[_-]?token|auth(?:orization)?|client[_-]?secret|"
    r"password|passwd|secret|token|webhook|credential)|-H|--header)$",
    re.I,
)
SOURCES = {"stdout", "stderr", "file", "manual"}
EXTRACTORS = {
    "stdout": {"jsonpath", "regex"},
    "stderr": {"jsonpath", "regex"},
    "file": {"jsonpath", "regex", "csv", "npy", "parquet"},
    "manual": {"manual"},
}
METHODS = {
    "numeric_tolerance",
    "equivalence_interval",
    "non_inferiority",
    "spearman_correlation",
    "exact_order",
}
UNITS = {
    "unitless", "ratio", "percent", "percentage_point", "seconds", "milliseconds",
    "bytes", "kilobytes", "megabytes", "gigabytes",
}


def plan_fingerprint(plan: dict) -> str:
    return object_sha256(plan)


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _numeric_tree(value: Any) -> bool:
    if _finite_number(value):
        return True
    return isinstance(value, list) and bool(value) and all(_numeric_tree(item) for item in value)


def _validate_relative(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{label} must be a relative path")
        return
    try:
        safe_relative_path(value, label=label)
    except ValueError as exc:
        errors.append(str(exc))


def _find_secret_material(value: Any, prefix: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            location = f"{prefix}.{key}" if prefix else str(key)
            if SECRET_NAME_PATTERN.search(str(key)) and key not in {"secret_ref", "secret_bindings"}:
                findings.append(f"{location} (secret-like key)")
            findings.extend(_find_secret_material(child, location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find_secret_material(child, f"{prefix}[{index}]"))
    elif isinstance(value, str) and contains_high_confidence_secret(value):
        findings.append(f"{prefix} (secret-like value)")
    return findings


def _validate_secret_ref(value: Any, label: str, errors: list[str]) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"secret_ref"}
        or not isinstance(value.get("secret_ref"), str)
        or not SECRET_REF_PATTERN.fullmatch(value["secret_ref"])
    ):
        errors.append(f"{label} must be exactly {{\"secret_ref\": \"UPPER_CASE_NAME\"}}")


def _validate_capabilities(
    capabilities: Any,
    label: str,
    errors: list[str],
    *,
    require_network: bool = False,
) -> None:
    if not isinstance(capabilities, dict):
        errors.append(f"{label} must be an object")
        return
    if require_network and "network" not in capabilities:
        errors.append(f"{label}.network must be explicitly declared")
    if capabilities.get("network", "disabled") not in {"disabled", "unrestricted"}:
        errors.append(f"{label}.network must be disabled or unrestricted")
    write_paths = capabilities.get("write_paths", [])
    if not isinstance(write_paths, list):
        errors.append(f"{label}.write_paths must be a list")
    else:
        for index, value in enumerate(write_paths):
            _validate_relative(value, f"{label}.write_paths[{index}]", errors)
    for key, upper in (
        ("max_memory_mb", 1_048_576),
        ("max_cpu_seconds", 604_800),
        ("max_disk_mb", 10_485_760),
        ("max_output_files", 1_000_000),
        ("max_single_file_mb", 1_048_576),
    ):
        value = capabilities.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= upper:
            errors.append(f"{label}.{key} must be an integer from 1 to {upper}")
    max_gpus = capabilities.get("max_gpus")
    if not isinstance(max_gpus, int) or isinstance(max_gpus, bool) or not 0 <= max_gpus <= 64:
        errors.append(f"{label}.max_gpus must be an integer from 0 to 64")


def _validate_observation(observation: Any, label: str, command_ids: set[str], errors: list[str]) -> None:
    if not isinstance(observation, dict):
        errors.append(f"{label} must be an object")
        return
    source = observation.get("source")
    if source not in SOURCES:
        errors.append(f"{label}.source must be one of {sorted(SOURCES)}")
        return
    extractor = observation.get("extractor")
    if extractor not in EXTRACTORS[source]:
        errors.append(f"{label}.extractor must be one of {sorted(EXTRACTORS[source])}")
    if source == "manual":
        if not isinstance(observation.get("reason"), str) or not observation["reason"].strip():
            errors.append(f"{label}.reason must explain the manual review")
        return
    command_id = observation.get("command_id")
    if command_id not in command_ids:
        errors.append(f"{label}.command_id must reference a declared command")
    if extractor in {"jsonpath", "regex", "csv", "npy", "parquet"} and "expression" not in observation:
        errors.append(f"{label}.expression is required")
    if source == "file":
        _validate_relative(observation.get("path"), f"{label}.path", errors)
        if observation.get("root", "workspace") not in {"workspace", "outputs"}:
            errors.append(f"{label}.root must be workspace or outputs")
    unit = observation.get("unit", "unitless")
    if unit not in UNITS:
        errors.append(f"{label}.unit must be one of {sorted(UNITS)}")


def _validate_comparison(comparison: Any, label: str, errors: list[str]) -> None:
    if not isinstance(comparison, dict):
        errors.append(f"{label} must be an object")
        return
    method = comparison.get("method")
    if method not in METHODS:
        errors.append(f"{label}.method must be one of {sorted(METHODS)}")
    if comparison.get("combination") not in {"all", "any"}:
        errors.append(f"{label}.combination must explicitly be all or any")
    minimum_runs = comparison.get("minimum_runs", 1)
    if not isinstance(minimum_runs, int) or isinstance(minimum_runs, bool) or minimum_runs < 1:
        errors.append(f"{label}.minimum_runs must be a positive integer")
    direction = comparison.get("direction", "two_sided")
    if direction not in {"two_sided", "higher_is_better", "lower_is_better"}:
        errors.append(f"{label}.direction is invalid")
    tolerances = [
        comparison.get("absolute"),
        comparison.get("relative"),
        comparison.get("rounding_absolute"),
    ]
    if method in {"numeric_tolerance", "equivalence_interval", "non_inferiority"}:
        if not any(_finite_number(value) and float(value) >= 0 for value in tolerances):
            errors.append(f"{label} needs a non-negative absolute, relative, or rounding_absolute")
    for key in ("absolute", "relative", "rounding_absolute"):
        value = comparison.get(key)
        if value is not None and (not _finite_number(value) or float(value) < 0):
            errors.append(f"{label}.{key} must be a finite non-negative number")
    threshold = comparison.get("minimum_correlation")
    if method == "spearman_correlation" and (
        not _finite_number(threshold) or not -1 <= float(threshold) <= 1
    ):
        errors.append(f"{label}.minimum_correlation must be between -1 and 1")


def validate(plan: dict, plan_path: Path) -> list[str]:
    errors: list[str] = []
    if plan.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    repository = plan.get("repository")
    if not isinstance(repository, str) or not repository.strip():
        return ["repository must be a non-empty relative or absolute path"]
    root = (
        (plan_path.parent / repository).resolve()
        if not Path(repository).is_absolute()
        else Path(repository).resolve()
    )
    if not root.is_dir():
        errors.append(f"repository is not a directory: {root}")
    environment = plan.get("environment", {})
    if not isinstance(environment, dict):
        errors.append("environment must be an object")
    else:
        packages = environment.get("packages", [])
        if not isinstance(packages, list) or not all(
            isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", item)
            for item in packages
        ):
            errors.append("environment.packages must be a list of package names")
        lock_files = environment.get("lock_files", [])
        if not isinstance(lock_files, list):
            errors.append("environment.lock_files must be a list")
        else:
            for index, value in enumerate(lock_files):
                _validate_relative(value, f"environment.lock_files[{index}]", errors)
                if isinstance(value, str) and root.is_dir() and not (root / value).is_file():
                    errors.append(f"environment.lock_files[{index}] does not exist in repository")
    paper_context = plan.get("paper_context")
    if not isinstance(paper_context, dict):
        errors.append("paper_context must summarize the whole paper before execution")
    else:
        for field in PAPER_CONTEXT_FIELDS:
            if not isinstance(paper_context.get(field), str) or not paper_context[field].strip():
                errors.append(f"paper_context.{field} must be a non-empty string")
    execution = plan.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution must be an object")
    else:
        mode = execution.get("workspace_mode")
        if mode not in {"copy", "git_worktree", "container"}:
            errors.append("execution.workspace_mode must be copy, git_worktree, or container")
        _validate_capabilities(execution, "execution", errors, require_network=True)
        if mode == "container" and (
            not isinstance(execution.get("container_image"), str)
            or not execution["container_image"].strip()
            or "@sha256:" not in execution["container_image"]
        ):
            errors.append("execution.container_image must be pinned by @sha256")
        if not isinstance(execution.get("retain_workspace", False), bool):
            errors.append("execution.retain_workspace must be boolean")
        exclusions = execution.get("exclude_paths", {})
        if not isinstance(exclusions, dict) or not all(
            isinstance(key, str) and key and isinstance(reason, str) and reason.strip()
            for key, reason in exclusions.items()
        ):
            errors.append("execution.exclude_paths must map path components to non-empty reasons")
    commands = plan.get("commands")
    command_ids: set[str] = set()
    if not isinstance(commands, list) or not commands:
        errors.append("commands must be a non-empty list")
    else:
        for index, command in enumerate(commands):
            label = f"commands[{index}]"
            if not isinstance(command, dict):
                errors.append(f"{label} must be an object")
                continue
            command_id = command.get("id")
            if not isinstance(command_id, str) or not SAFE_ID_PATTERN.fullmatch(command_id):
                errors.append(f"{label}.id must match {SAFE_ID_PATTERN.pattern}")
            elif command_id in command_ids:
                errors.append(f"{label}.id duplicates {command_id!r}")
            else:
                command_ids.add(command_id)
            if "command" in command or "shell" in command:
                errors.append(f"{label} must use argv; shell command strings are not allowed")
            argv = command.get("argv")
            if not isinstance(argv, list) or not argv:
                errors.append(f"{label}.argv must be a non-empty list")
            else:
                for arg_index, argument in enumerate(argv):
                    if isinstance(argument, str):
                        if not argument:
                            errors.append(f"{label}.argv[{arg_index}] must not be empty")
                        if contains_high_confidence_secret(argument):
                            errors.append(f"{label}.argv[{arg_index}] contains secret-like material; use secret_ref")
                        if arg_index > 0 and isinstance(argv[arg_index - 1], str) and SENSITIVE_FLAGS.fullmatch(argv[arg_index - 1]):
                            errors.append(f"{label}.argv[{arg_index}] follows a sensitive flag; use secret_ref")
                    else:
                        _validate_secret_ref(argument, f"{label}.argv[{arg_index}]", errors)
            if "env" in command or "environment" in command:
                errors.append(f"{label} must use secret_bindings instead of embedded environment values")
            bindings = command.get("secret_bindings", [])
            if not isinstance(bindings, list):
                errors.append(f"{label}.secret_bindings must be a list")
            else:
                for binding_index, binding in enumerate(bindings):
                    binding_label = f"{label}.secret_bindings[{binding_index}]"
                    if not isinstance(binding, dict) or set(binding) != {"name", "secret_ref"}:
                        errors.append(f"{binding_label} must contain only name and secret_ref")
                        continue
                    if not isinstance(binding["name"], str) or not SECRET_REF_PATTERN.fullmatch(binding["name"]):
                        errors.append(f"{binding_label}.name must be an uppercase environment name")
                    if not isinstance(binding["secret_ref"], str) or not SECRET_REF_PATTERN.fullmatch(binding["secret_ref"]):
                        errors.append(f"{binding_label}.secret_ref must be an uppercase reference")
            cwd = command.get("cwd", ".")
            if not isinstance(cwd, str) or not cwd:
                errors.append(f"{label}.cwd must be a non-empty relative path")
            elif Path(cwd).is_absolute() or ".." in Path(cwd).parts:
                errors.append(f"{label}.cwd must stay inside the execution workspace")
            elif root.is_dir() and not is_within(root / cwd, root):
                errors.append(f"{label}.cwd must stay inside repository")
            elif root.is_dir() and not (root / cwd).resolve().is_dir():
                errors.append(f"{label}.cwd is not an existing directory")
            timeout = command.get("timeout_seconds")
            if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 604_800:
                errors.append(f"{label}.timeout_seconds must be an integer from 1 to 604800")
            if "capabilities" in command:
                merged = dict(execution or {})
                merged.update(command.get("capabilities") or {})
                _validate_capabilities(
                    merged,
                    f"{label}.capabilities (merged)",
                    errors,
                    require_network=True,
                )
    claims = plan.get("claims")
    claim_ids: set[str] = set()
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
    else:
        for index, claim in enumerate(claims):
            label = f"claims[{index}]"
            if not isinstance(claim, dict):
                errors.append(f"{label} must be an object")
                continue
            for key in ("id", "paper_location", "metric", "protocol"):
                if not isinstance(claim.get(key), str) or not claim[key].strip():
                    errors.append(f"{label}.{key} must be a non-empty string")
            claim_id = claim.get("id")
            if isinstance(claim_id, str):
                if not SAFE_ID_PATTERN.fullmatch(claim_id):
                    errors.append(f"{label}.id must match {SAFE_ID_PATTERN.pattern}")
                elif claim_id in claim_ids:
                    errors.append(f"{label}.id duplicates {claim_id!r}")
                claim_ids.add(claim_id)
            if not _numeric_tree(claim.get("expected")):
                errors.append(f"{label}.expected must be a finite number or numeric array")
            unit = claim.get("unit", "unitless")
            if unit not in UNITS:
                errors.append(f"{label}.unit must be one of {sorted(UNITS)}")
            command_refs = claim.get("command_ids")
            if not isinstance(command_refs, list) or not command_refs:
                errors.append(f"{label}.command_ids must be a non-empty list")
            elif len(command_refs) != len(set(command_refs)):
                errors.append(f"{label}.command_ids must not contain duplicates")
            else:
                unknown = sorted(set(command_refs) - command_ids)
                if unknown:
                    errors.append(f"{label}.command_ids reference unknown command(s): {', '.join(unknown)}")
            _validate_observation(claim.get("observation"), f"{label}.observation", command_ids, errors)
            _validate_comparison(claim.get("comparison"), f"{label}.comparison", errors)
    secret_findings = _find_secret_material(plan)
    if secret_findings:
        errors.append("plan must not contain literal or secret-shaped material: " + ", ".join(secret_findings))
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
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
