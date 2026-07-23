#!/usr/bin/env python3
"""Extract claim observations only from recorded command logs or result files."""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
import statistics
from pathlib import Path
from typing import Any

from evidence_common import is_within, sha256_file, utc_now


EXTRACTOR_VERSIONS = {
    "jsonpath": "rrp-jsonpath-1",
    "regex": "python-re-1",
    "csv": "python-csv-1",
    "npy": "numpy-npy-1",
    "parquet": "pyarrow-parquet-1",
    "manual": "manual-1",
}
UNIT_SCALE = {
    "unitless": ("unitless", 1.0),
    "ratio": ("ratio", 1.0),
    "percent": ("ratio", 0.01),
    "percentage_point": ("percentage_point", 1.0),
    "seconds": ("seconds", 1.0),
    "milliseconds": ("seconds", 0.001),
    "bytes": ("bytes", 1.0),
    "kilobytes": ("bytes", 1024.0),
    "megabytes": ("bytes", 1024.0 * 1024.0),
    "gigabytes": ("bytes", 1024.0 * 1024.0 * 1024.0),
}


def _json_document(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for line in reversed(text.splitlines()):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                continue
    raise ValueError("no complete JSON document or JSON line was found")


def _jsonpath_tokens(expression: str) -> list[str | int]:
    if not isinstance(expression, str) or not expression.startswith("$"):
        raise ValueError("JSONPath must start with '$'")
    if expression == "$":
        return []
    tokens: list[str | int] = []
    position = 1
    while position < len(expression):
        if expression[position] == ".":
            match = re.match(r"\.([A-Za-z_][A-Za-z0-9_-]*)", expression[position:])
            if not match:
                raise ValueError("unsupported JSONPath member syntax")
            tokens.append(match.group(1))
            position += len(match.group(0))
        elif expression[position] == "[":
            match = re.match(r"\[(\d+)\]", expression[position:])
            if not match:
                raise ValueError("only numeric JSONPath indexes are supported")
            tokens.append(int(match.group(1)))
            position += len(match.group(0))
        else:
            raise ValueError("unsupported JSONPath syntax")
    return tokens


def extract_jsonpath(value: Any, expression: str) -> Any:
    current = value
    for token in _jsonpath_tokens(expression):
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                raise ValueError(f"JSONPath index {token} was not found")
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                raise ValueError(f"JSONPath member {token!r} was not found")
            current = current[token]
    return current


def _regex_extract(text: str, expression: Any) -> Any:
    if isinstance(expression, str):
        pattern, group, all_matches = expression, 1, False
    elif isinstance(expression, dict):
        pattern = expression.get("pattern")
        group = expression.get("group", 1)
        all_matches = bool(expression.get("all", False))
    else:
        raise ValueError("regex expression must be a pattern string or object")
    if not isinstance(pattern, str) or not pattern:
        raise ValueError("regex pattern must be non-empty")
    compiled = re.compile(pattern, re.MULTILINE)
    matches = list(compiled.finditer(text))
    if not matches:
        raise ValueError("regex did not match")
    try:
        values = [match.group(group) for match in matches]
    except (IndexError, KeyError) as exc:
        raise ValueError(f"regex group was not found: {group}") from exc
    return values if all_matches else values[0]


def _parse_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric observation")
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ValueError("non-finite numeric observation")
        return float(value)
    if isinstance(value, str):
        stripped = value.strip().replace(",", "")
        try:
            parsed = float(stripped)
        except ValueError:
            return value
        if not math.isfinite(parsed):
            raise ValueError("non-finite numeric observation")
        return parsed
    if isinstance(value, list):
        return [_parse_scalar(item) for item in value]
    raise ValueError(f"unsupported extracted value type: {type(value).__name__}")


def _csv_extract(path: Path, expression: Any) -> Any:
    if not isinstance(expression, dict) or not isinstance(expression.get("column"), str):
        raise ValueError("CSV expression needs a column")
    with path.open("r", encoding=expression.get("encoding", "utf-8-sig"), newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=expression.get("delimiter", ",")))
    where = expression.get("where")
    if where is not None:
        if not isinstance(where, dict):
            raise ValueError("CSV where must be an object")
        rows = [
            row for row in rows
            if all(str(row.get(key, "")) == str(expected) for key, expected in where.items())
        ]
    column = expression["column"]
    values = [_parse_scalar(row[column]) for row in rows if column in row and row[column] != ""]
    if not values:
        raise ValueError("CSV selection produced no values")
    aggregate = expression.get("aggregate", "values")
    numeric = [float(value) for value in values]
    if aggregate == "values":
        return numeric
    if aggregate == "first":
        return numeric[0]
    if aggregate == "mean":
        return statistics.fmean(numeric)
    if aggregate == "median":
        return statistics.median(numeric)
    if aggregate == "min":
        return min(numeric)
    if aggregate == "max":
        return max(numeric)
    if aggregate == "sum":
        return sum(numeric)
    raise ValueError(f"unsupported CSV aggregate: {aggregate}")


def _npy_extract(path: Path, expression: Any) -> Any:
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise ValueError("NumPy extractor requires the optional numpy package") from exc
    array = np.load(path, allow_pickle=False)
    operation = expression.get("aggregate", "values") if isinstance(expression, dict) else "values"
    if operation == "values":
        return array.tolist()
    if operation == "mean":
        return float(array.mean())
    if operation == "std":
        return float(array.std())
    if operation == "min":
        return float(array.min())
    if operation == "max":
        return float(array.max())
    raise ValueError(f"unsupported NumPy aggregate: {operation}")


def _parquet_extract(path: Path, expression: Any) -> Any:
    if not isinstance(expression, dict) or not isinstance(expression.get("column"), str):
        raise ValueError("Parquet expression needs a column")
    try:
        import pyarrow.parquet as parquet  # type: ignore
    except ImportError as exc:
        raise ValueError("Parquet extractor requires the optional pyarrow package") from exc
    table = parquet.read_table(path, columns=[expression["column"]])
    values = [_parse_scalar(value) for value in table[expression["column"]].to_pylist()]
    operation = expression.get("aggregate", "values")
    if operation == "values":
        return values
    numeric = [float(value) for value in values]
    if operation == "mean":
        return statistics.fmean(numeric)
    if operation == "median":
        return statistics.median(numeric)
    if operation == "min":
        return min(numeric)
    if operation == "max":
        return max(numeric)
    raise ValueError(f"unsupported Parquet aggregate: {operation}")


def normalize_unit(value: Any, source_unit: str, target_unit: str) -> Any:
    source_base, source_scale = UNIT_SCALE[source_unit]
    target_base, target_scale = UNIT_SCALE[target_unit]
    if source_base != target_base:
        raise ValueError(f"incompatible units: {source_unit} and {target_unit}")
    if isinstance(value, list):
        return [normalize_unit(item, source_unit, target_unit) for item in value]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("unit normalization requires numeric values")
    return float(value) * source_scale / target_scale


def _source_path(
    observation: dict,
    command: dict,
    bundle: Path,
    workspace: Path,
    outputs: Path,
) -> Path:
    source = observation["source"]
    if source == "stdout":
        return bundle / command["stdout_log"]
    if source == "stderr":
        return bundle / command["stderr_log"]
    root = workspace if observation.get("root", "workspace") == "workspace" else outputs
    result = (root / observation["path"]).resolve()
    if not is_within(result, root):
        raise ValueError("observation file escapes its declared evidence root")
    return result


def extract_observations(
    plan: dict,
    run_record: dict,
    *,
    run_record_path: Path,
    bundle: Path,
    workspace: Path,
    outputs: Path,
) -> dict:
    commands = {item.get("id"): item for item in run_record.get("commands", [])}
    observations = []
    evidence_sources: list[str] = []
    run_sha = sha256_file(run_record_path)
    for claim in plan.get("claims", []):
        spec = claim["observation"]
        base = {
            "claim_id": claim["id"],
            "metric": claim["metric"],
            "run_record_sha256": run_sha,
            "source": spec["source"],
            "command_id": spec.get("command_id"),
            "extractor": spec["extractor"],
            "extractor_version": EXTRACTOR_VERSIONS[spec["extractor"]],
            "expression": spec.get("expression"),
            "unit": spec.get("unit", "unitless"),
            "normalized_unit": claim.get("unit", "unitless"),
            "extracted_at": utc_now(),
        }
        if spec["source"] == "manual":
            base.update(
                {
                    "status": "MANUAL_REVIEW_REQUIRED",
                    "reason": spec["reason"],
                    "source_sha256": None,
                    "raw_value": None,
                    "normalized_value": None,
                }
            )
            observations.append(base)
            continue
        command = commands.get(spec["command_id"])
        if not command or command.get("exit_code") != 0 or command.get("timed_out"):
            base.update(
                {
                    "status": "BLOCKED",
                    "reason": "source command did not complete successfully",
                    "source_sha256": None,
                    "raw_value": None,
                    "normalized_value": None,
                }
            )
            observations.append(base)
            continue
        try:
            source_path = _source_path(spec, command, bundle, workspace, outputs)
            if not source_path.is_file():
                raise ValueError(f"source artifact does not exist: {source_path.name}")
            if spec["source"] == "file":
                preserved = bundle / "evidence-sources" / f"{claim['id']}-{source_path.name}"
                preserved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, preserved)
                source_path = preserved
            source_hash = sha256_file(source_path)
            relative_source = source_path.resolve().relative_to(bundle.resolve()).as_posix()
            if spec["extractor"] == "jsonpath":
                raw = extract_jsonpath(
                    _json_document(source_path.read_text(encoding="utf-8")),
                    spec["expression"],
                )
            elif spec["extractor"] == "regex":
                raw = _regex_extract(source_path.read_text(encoding="utf-8"), spec["expression"])
            elif spec["extractor"] == "csv":
                raw = _csv_extract(source_path, spec["expression"])
            elif spec["extractor"] == "npy":
                raw = _npy_extract(source_path, spec["expression"])
            elif spec["extractor"] == "parquet":
                raw = _parquet_extract(source_path, spec["expression"])
            else:
                raise ValueError(f"unsupported extractor: {spec['extractor']}")
            parsed = _parse_scalar(raw)
            normalized = normalize_unit(
                parsed, spec.get("unit", "unitless"), claim.get("unit", "unitless")
            )
            base.update(
                {
                    "status": "EXTRACTED",
                    "source_artifact": relative_source,
                    "source_sha256": source_hash,
                    "raw_value": parsed,
                    "normalized_value": normalized,
                }
            )
            evidence_sources.append(relative_source)
        except (OSError, UnicodeError, ValueError, KeyError) as exc:
            base.update(
                {
                    "status": "BLOCKED",
                    "reason": str(exc),
                    "source_sha256": None,
                    "raw_value": None,
                    "normalized_value": None,
                }
            )
        observations.append(base)
    return {
        "schema_version": 1,
        "run_record_sha256": run_sha,
        "observations": observations,
        "evidence_sources": sorted(set(evidence_sources)),
    }
