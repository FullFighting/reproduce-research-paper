"""Typed expected-value and extensible unit helpers."""

from __future__ import annotations

import math
from typing import Any

EXPECTED_TYPES = {
    "scalar",
    "array",
    "table",
    "ranking",
    "categorical",
    "string",
    "artifact_hash",
    "distribution",
}

LEGACY_UNITS = {
    "unitless": {"symbol": "1", "scale": 1.0, "semantic_type": "unitless"},
    "ratio": {"symbol": "ratio", "scale": 1.0, "semantic_type": "ratio"},
    "percent": {"symbol": "%", "scale": 0.01, "semantic_type": "ratio"},
    "percentage_point": {
        "symbol": "percentage_point",
        "scale": 1.0,
        "semantic_type": "percentage_point",
    },
    "seconds": {"symbol": "s", "scale": 1.0, "semantic_type": "duration"},
    "milliseconds": {"symbol": "ms", "scale": 0.001, "semantic_type": "duration"},
    "bytes": {"symbol": "B", "scale": 1.0, "semantic_type": "storage"},
    "kilobytes": {"symbol": "KiB", "scale": 1024.0, "semantic_type": "storage"},
    "megabytes": {
        "symbol": "MiB",
        "scale": 1024.0 * 1024.0,
        "semantic_type": "storage",
    },
    "gigabytes": {
        "symbol": "GiB",
        "scale": 1024.0 * 1024.0 * 1024.0,
        "semantic_type": "storage",
    },
}


def finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def numeric_tree(value: Any) -> bool:
    if finite_number(value):
        return True
    return isinstance(value, list) and bool(value) and all(numeric_tree(item) for item in value)


def expected_spec(expected: Any) -> dict[str, Any]:
    """Return a typed view while preserving schema-v1 plans."""
    if (
        isinstance(expected, dict)
        and expected.get("type") in EXPECTED_TYPES
        and "value" in expected
    ):
        return expected
    inferred = "scalar" if finite_number(expected) else "array"
    return {"type": inferred, "value": expected, "legacy": True}


def unit_spec(unit: Any) -> dict[str, Any]:
    """Normalize a legacy unit name or a schema-v2 unit descriptor."""
    if isinstance(unit, str):
        if unit not in LEGACY_UNITS:
            raise ValueError(f"unknown legacy unit: {unit}")
        return dict(LEGACY_UNITS[unit])
    if not isinstance(unit, dict):
        raise ValueError("unit must be a legacy name or descriptor object")
    return {
        "symbol": unit["symbol"],
        "scale": float(unit["scale"]),
        "semantic_type": unit["semantic_type"],
    }


def normalize_unit(value: Any, source_unit: Any, target_unit: Any) -> Any:
    source = unit_spec(source_unit)
    target = unit_spec(target_unit)
    if source["semantic_type"] != target["semantic_type"]:
        raise ValueError(
            "incompatible unit semantic types: "
            f"{source['semantic_type']} and {target['semantic_type']}"
        )
    factor = source["scale"] / target["scale"]
    if factor == 1.0:
        return value
    if isinstance(value, list):
        return [normalize_unit(item, source, target) for item in value]
    if isinstance(value, dict):
        if {"columns", "rows"} <= set(value):
            return {
                **value,
                "rows": normalize_unit(value["rows"], source, target),
            }
        raise ValueError(
            "scaled unit normalization supports numeric values, arrays, or table rows"
        )
    if not finite_number(value):
        raise ValueError("scaled unit normalization requires numeric values")
    return float(value) * factor
