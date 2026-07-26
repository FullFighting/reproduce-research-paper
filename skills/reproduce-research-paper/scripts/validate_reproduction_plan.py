#!/usr/bin/env python3
"""Validate a traceable, secret-reference-only reproduction plan."""

from __future__ import annotations

import argparse
import json
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
from value_contract import (
    EXPECTED_TYPES,
    LEGACY_UNITS,
    expected_spec,
    finite_number,
    numeric_tree,
    unit_spec,
)

SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
CONTAINER_IMAGE_PATTERN = re.compile(
    r"^(?:[a-z0-9]+(?:[._-][a-z0-9]+)*(?::[0-9]+)?/)?"
    r"(?:[a-z0-9]+(?:[._-][a-z0-9]+)*/)*"
    r"[a-z0-9]+(?:[._-][a-z0-9]+)*@sha256:[0-9a-f]{64}$"
)
CONTAINER_USER_PATTERN = re.compile(r"^[1-9][0-9]*(?::[1-9][0-9]*)?$")
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
    "file": {"jsonpath", "regex", "csv", "npy", "parquet", "sha256"},
    "manual": {"manual"},
}
METHODS = {
    "numeric_tolerance",
    "equivalence_interval",
    "non_inferiority",
    "spearman_correlation",
    "exact_order",
    "exact_match",
    "set_equality",
    "artifact_hash",
    "distribution_distance",
}


def plan_fingerprint(plan: dict) -> str:
    return object_sha256(plan)


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
            if SECRET_NAME_PATTERN.search(str(key)) and key not in {
                "secret_ref",
                "secret_bindings",
                "allow_argv_secrets",
            }:
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


def _json_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, bool)) or finite_number(value)


def _json_value(value: Any) -> bool:
    if _json_scalar(value):
        return True
    if isinstance(value, list):
        return all(_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _json_value(item) for key, item in value.items()
        )
    return False


def _validate_expected(
    expected: Any,
    label: str,
    errors: list[str],
    *,
    schema_version: int,
) -> tuple[str, Any]:
    if schema_version == 1 and not isinstance(expected, dict):
        if not numeric_tree(expected):
            errors.append(f"{label} must be a finite number or numeric array in schema v1")
        spec = expected_spec(expected)
        return spec["type"], spec["value"]
    if not isinstance(expected, dict) or set(expected) != {"type", "value"}:
        errors.append(f"{label} must contain exactly type and value in schema v2")
        return "invalid", None
    expected_type = expected.get("type")
    value = expected.get("value")
    if not isinstance(expected_type, str) or expected_type not in EXPECTED_TYPES:
        errors.append(f"{label}.type must be one of {sorted(EXPECTED_TYPES)}")
        return "invalid", value
    if expected_type == "scalar" and not finite_number(value):
        errors.append(f"{label}.value must be a finite number for scalar")
    elif expected_type == "array":
        if not isinstance(value, list) or not value or not _json_value(value):
            errors.append(f"{label}.value must be a non-empty JSON array")
    elif expected_type == "table":
        if not isinstance(value, dict) or not {"columns", "rows"} <= set(value):
            errors.append(f"{label}.value must contain columns and rows")
        else:
            columns, rows = value.get("columns"), value.get("rows")
            if (
                not isinstance(columns, list)
                or not columns
                or not all(isinstance(item, str) and item for item in columns)
                or len(columns) != len(set(columns))
            ):
                errors.append(f"{label}.value.columns must be unique non-empty strings")
            if (
                not isinstance(rows, list)
                or not rows
                or not all(
                    isinstance(row, list)
                    and len(row) == len(columns or [])
                    and all(_json_scalar(cell) for cell in row)
                    for row in rows
                )
            ):
                errors.append(f"{label}.value.rows must be a non-empty rectangular scalar table")
            row_labels = value.get("row_labels")
            if row_labels is not None and (
                not isinstance(row_labels, list)
                or len(row_labels) != len(rows or [])
                or not all(isinstance(item, str) and item for item in row_labels)
                or len(row_labels) != len(set(row_labels))
            ):
                errors.append(f"{label}.value.row_labels must be unique strings matching rows")
            extra = set(value) - {"columns", "rows", "row_labels"}
            if extra:
                errors.append(f"{label}.value has unsupported table fields: {sorted(extra)}")
    elif expected_type == "ranking":
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) or finite_number(item) for item in value)
            or len({json.dumps(item, sort_keys=True) for item in value}) != len(value)
        ):
            errors.append(f"{label}.value must be a non-empty ranking of unique strings or numbers")
    elif expected_type == "categorical" and not (
        isinstance(value, (str, bool))
        or (isinstance(value, int) and not isinstance(value, bool))
        or finite_number(value)
    ):
        errors.append(f"{label}.value must be a JSON category scalar")
    elif expected_type == "string" and not isinstance(value, str):
        errors.append(f"{label}.value must be a string")
    elif expected_type == "artifact_hash" and not (
        isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value)
    ):
        errors.append(f"{label}.value must be a 64-character SHA-256 hex digest")
    elif expected_type == "distribution" and not (
        isinstance(value, list) and len(value) >= 2 and all(finite_number(item) for item in value)
    ):
        errors.append(f"{label}.value must contain at least two finite numeric samples")
    return expected_type, value


def _validate_unit(
    unit: Any,
    label: str,
    errors: list[str],
    *,
    schema_version: int,
) -> dict[str, Any] | None:
    if schema_version == 1 and isinstance(unit, str):
        if unit not in LEGACY_UNITS:
            errors.append(f"{label} must be one of {sorted(LEGACY_UNITS)}")
            return None
        return unit_spec(unit)
    if not isinstance(unit, dict) or set(unit) != {"symbol", "scale", "semantic_type"}:
        errors.append(f"{label} must contain exactly symbol, scale, and semantic_type")
        return None
    if not isinstance(unit.get("symbol"), str) or not 1 <= len(unit["symbol"]) <= 64:
        errors.append(f"{label}.symbol must be a string from 1 to 64 characters")
    if not finite_number(unit.get("scale")) or float(unit["scale"]) <= 0:
        errors.append(f"{label}.scale must be a positive finite number")
    if not isinstance(unit.get("semantic_type"), str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_.-]{0,63}", unit["semantic_type"]
    ):
        errors.append(f"{label}.semantic_type must be a stable identifier")
    try:
        return unit_spec(unit)
    except (KeyError, TypeError, ValueError):
        return None


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
    network = capabilities.get("network", "disabled")
    if not isinstance(network, str) or network not in {"disabled", "unrestricted"}:
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


def _validate_observation(
    observation: Any,
    label: str,
    command_ids: set[str],
    errors: list[str],
    *,
    schema_version: int,
) -> dict[str, Any] | None:
    if not isinstance(observation, dict):
        errors.append(f"{label} must be an object")
        return None
    source = observation.get("source")
    if not isinstance(source, str) or source not in SOURCES:
        errors.append(f"{label}.source must be one of {sorted(SOURCES)}")
        return None
    extractor = observation.get("extractor")
    if not isinstance(extractor, str) or extractor not in EXTRACTORS[source]:
        errors.append(f"{label}.extractor must be one of {sorted(EXTRACTORS[source])}")
    if source == "manual":
        if not isinstance(observation.get("reason"), str) or not observation["reason"].strip():
            errors.append(f"{label}.reason must explain the manual review")
        return None
    command_id = observation.get("command_id")
    if command_id not in command_ids:
        errors.append(f"{label}.command_id must reference a declared command")
    if extractor in {"jsonpath", "regex", "csv", "npy", "parquet"} and "expression" not in observation:
        errors.append(f"{label}.expression is required")
    if source == "file":
        _validate_relative(observation.get("path"), f"{label}.path", errors)
        observation_root = observation.get("root", "workspace")
        if (
            not isinstance(observation_root, str)
            or observation_root not in {"workspace", "outputs"}
        ):
            errors.append(f"{label}.root must be workspace or outputs")
    default_unit: Any = (
        "unitless"
        if schema_version == 1
        else {"symbol": "1", "scale": 1, "semantic_type": "unitless"}
    )
    return _validate_unit(
        observation.get("unit", default_unit),
        f"{label}.unit",
        errors,
        schema_version=schema_version,
    )


def _validate_comparison(
    comparison: Any,
    label: str,
    errors: list[str],
    *,
    expected_type: str,
    expected_value: Any,
) -> None:
    if not isinstance(comparison, dict):
        errors.append(f"{label} must be an object")
        return
    method = comparison.get("method")
    method_valid = isinstance(method, str) and method in METHODS
    if not method_valid:
        errors.append(f"{label}.method must be one of {sorted(METHODS)}")
    combination = comparison.get("combination")
    if not isinstance(combination, str) or combination not in {"all", "any"}:
        errors.append(f"{label}.combination must explicitly be all or any")
    minimum_runs = comparison.get("minimum_runs", 1)
    if not isinstance(minimum_runs, int) or isinstance(minimum_runs, bool) or minimum_runs < 1:
        errors.append(f"{label}.minimum_runs must be a positive integer")
    direction = comparison.get("direction", "two_sided")
    if (
        not isinstance(direction, str)
        or direction not in {"two_sided", "higher_is_better", "lower_is_better"}
    ):
        errors.append(f"{label}.direction is invalid")
    tolerances = [
        comparison.get("absolute"),
        comparison.get("relative"),
        comparison.get("rounding_absolute"),
    ]
    if method_valid and method in {
        "numeric_tolerance",
        "equivalence_interval",
        "non_inferiority",
    }:
        if not any(finite_number(value) and float(value) >= 0 for value in tolerances):
            errors.append(f"{label} needs a non-negative absolute, relative, or rounding_absolute")
    for key in ("absolute", "relative", "rounding_absolute"):
        value = comparison.get(key)
        if value is not None and (not finite_number(value) or float(value) < 0):
            errors.append(f"{label}.{key} must be a finite non-negative number")
    threshold = comparison.get("minimum_correlation")
    if method_valid and method == "spearman_correlation" and (
        not finite_number(threshold) or not -1 <= float(threshold) <= 1
    ):
        errors.append(f"{label}.minimum_correlation must be between -1 and 1")
    maximum_distance = comparison.get("maximum_distance")
    if method_valid and method == "distribution_distance" and (
        not finite_number(maximum_distance) or not 0 <= float(maximum_distance) <= 1
    ):
        errors.append(f"{label}.maximum_distance must be between 0 and 1")
    compatible = {
        "numeric_tolerance": {"scalar", "array", "table", "distribution"},
        "equivalence_interval": {"scalar"},
        "non_inferiority": {"scalar"},
        "spearman_correlation": {"array", "ranking"},
        "exact_order": {"array", "ranking"},
        "exact_match": EXPECTED_TYPES,
        "set_equality": {"array", "ranking"},
        "artifact_hash": {"artifact_hash"},
        "distribution_distance": {"distribution"},
    }
    method_types = compatible.get(method) if isinstance(method, str) else None
    if method_types is not None and expected_type not in method_types:
        errors.append(f"{label}.method {method} is incompatible with expected type {expected_type}")
    if method_valid and method in {
        "numeric_tolerance",
        "equivalence_interval",
        "non_inferiority",
    }:
        numeric_value = (
            expected_value.get("rows")
            if expected_type == "table" and isinstance(expected_value, dict)
            else expected_value
        )
        if not numeric_tree(numeric_value):
            errors.append(f"{label}.method {method} requires numeric expected values")


def validate(plan: dict, plan_path: Path) -> list[str]:
    errors: list[str] = []
    schema_version = plan.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version not in {1, 2}
    ):
        errors.append("schema_version must be 1 or 2")
        schema_version = 2
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
        if not isinstance(mode, str) or mode not in {
            "copy",
            "git_worktree",
            "container",
        }:
            errors.append("execution.workspace_mode must be copy, git_worktree, or container")
        _validate_capabilities(execution, "execution", errors, require_network=True)
        if mode == "container":
            image = execution.get("container_image")
            if not isinstance(image, str) or not CONTAINER_IMAGE_PATTERN.fullmatch(
                image
            ):
                errors.append(
                    "execution.container_image must be a lowercase digest-only "
                    "reference such as registry.example/research@sha256:<64 hex>; "
                    "tags and unpinned images are forbidden"
                )
            container_user = execution.get("container_user", "65532:65532")
            if (
                not isinstance(container_user, str)
                or not CONTAINER_USER_PATTERN.fullmatch(container_user)
            ):
                errors.append(
                    "execution.container_user must be a non-root numeric UID or "
                    "UID:GID (default 65532:65532)"
                )
        if not isinstance(execution.get("retain_workspace", False), bool):
            errors.append("execution.retain_workspace must be boolean")
        if not isinstance(execution.get("allow_argv_secrets", False), bool):
            errors.append("execution.allow_argv_secrets must be boolean")
        exclusions = execution.get("exclude_paths", {})
        if not isinstance(exclusions, dict) or not all(
            isinstance(key, str) and key and isinstance(reason, str) and reason.strip()
            for key, reason in exclusions.items()
        ):
            errors.append("execution.exclude_paths must map path components to non-empty reasons")
    allow_argv_secrets = bool(
        isinstance(execution, dict) and execution.get("allow_argv_secrets", False)
    )
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
                            errors.append(
                                f"{label}.argv[{arg_index}] contains secret-like material; "
                                "use secret_bindings"
                            )
                        previous_argument = argv[arg_index - 1] if arg_index > 0 else None
                        if isinstance(previous_argument, str) and SENSITIVE_FLAGS.fullmatch(
                            previous_argument
                        ):
                            errors.append(
                                f"{label}.argv[{arg_index}] follows a sensitive flag; "
                                "use secret_bindings"
                            )
                    else:
                        _validate_secret_ref(argument, f"{label}.argv[{arg_index}]", errors)
                        if not allow_argv_secrets:
                            errors.append(
                                f"{label}.argv[{arg_index}] uses an argv secret_ref, which is "
                                "disabled by default; use secret_bindings or explicitly set "
                                "execution.allow_argv_secrets=true for high-risk compatibility"
                            )
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
                    if not isinstance(binding["secret_ref"], str) or not (
                        SECRET_REF_PATTERN.fullmatch(binding["secret_ref"])
                    ):
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
            expected_type, expected_value = _validate_expected(
                claim.get("expected"),
                f"{label}.expected",
                errors,
                schema_version=schema_version,
            )
            default_unit: Any = (
                "unitless"
                if schema_version == 1
                else {"symbol": "1", "scale": 1, "semantic_type": "unitless"}
            )
            claim_unit = _validate_unit(
                claim.get("unit", default_unit),
                f"{label}.unit",
                errors,
                schema_version=schema_version,
            )
            command_refs = claim.get("command_ids")
            if not isinstance(command_refs, list) or not command_refs:
                errors.append(f"{label}.command_ids must be a non-empty list")
            elif not all(isinstance(item, str) for item in command_refs):
                errors.append(f"{label}.command_ids must contain only command IDs")
            elif len(command_refs) != len(set(command_refs)):
                errors.append(f"{label}.command_ids must not contain duplicates")
            else:
                unknown = sorted(set(command_refs) - command_ids)
                if unknown:
                    errors.append(f"{label}.command_ids reference unknown command(s): {', '.join(unknown)}")
            observation_unit = _validate_observation(
                claim.get("observation"),
                f"{label}.observation",
                command_ids,
                errors,
                schema_version=schema_version,
            )
            if (
                claim_unit is not None
                and observation_unit is not None
                and claim_unit["semantic_type"] != observation_unit["semantic_type"]
            ):
                errors.append(
                    f"{label}.observation.unit semantic_type must match {label}.unit"
                )
            _validate_comparison(
                claim.get("comparison"),
                f"{label}.comparison",
                errors,
                expected_type=expected_type,
                expected_value=expected_value,
            )
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
