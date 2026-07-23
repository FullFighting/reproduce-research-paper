#!/usr/bin/env python3
"""Create and verify evidence-bundle provenance."""

from __future__ import annotations

import json
from pathlib import Path

from evidence_common import (
    GENERATOR_NAME,
    GENERATOR_VERSION,
    is_within,
    sha256_file,
    utc_now,
    write_json,
)


CORE_RELATIONSHIPS = {
    "plan.json": [],
    "inventory-before.json": ["plan.json"],
    "environment.json": ["plan.json"],
    "run-record.json": ["plan.json", "inventory-before.json", "environment.json"],
    "inventory-after.json": ["run-record.json"],
    "observations.json": ["plan.json", "run-record.json"],
    "comparison.json": ["plan.json", "run-record.json", "observations.json"],
    "report.md": [
        "plan.json",
        "inventory-before.json",
        "inventory-after.json",
        "environment.json",
        "run-record.json",
        "observations.json",
        "comparison.json",
    ],
}


def artifact_role(path: str) -> str:
    if path in CORE_RELATIONSHIPS:
        return path.rsplit(".", 1)[0]
    if path.startswith("logs/"):
        return "command-log"
    if path.startswith("evidence-sources/"):
        return "observation-source"
    return "supporting-artifact"


def create_provenance(bundle: Path) -> dict:
    artifacts = {}
    for path in sorted(bundle.rglob("*")):
        if not path.is_file() or path.name == "provenance.json":
            continue
        relative = path.relative_to(bundle).as_posix()
        artifacts[relative] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "role": artifact_role(relative),
            "generated_from": CORE_RELATIONSHIPS.get(relative, []),
        }
    payload = {
        "schema_version": 1,
        "bundle_format": "reproduce-research-paper-evidence-bundle",
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "created_at": utc_now(),
        "integrity_scope": (
            "Hashes detect unsynchronized artifact changes; they do not prove authorship or "
            "protect against an attacker who can rewrite both artifacts and provenance."
        ),
        "artifacts": artifacts,
    }
    write_json(bundle / "provenance.json", payload)
    return payload


def verify_provenance(bundle: Path) -> list[str]:
    errors: list[str] = []
    path = bundle / "provenance.json"
    try:
        provenance = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"could not read provenance.json: {exc}"]
    if provenance.get("bundle_format") != "reproduce-research-paper-evidence-bundle":
        errors.append("unexpected bundle_format")
    artifacts = provenance.get("artifacts")
    if not isinstance(artifacts, dict):
        return errors + ["provenance.artifacts must be an object"]
    required = set(CORE_RELATIONSHIPS)
    missing = sorted(required - set(artifacts))
    if missing:
        errors.append("provenance is missing required artifacts: " + ", ".join(missing))
    for relative, record in artifacts.items():
        if not isinstance(relative, str) or not isinstance(record, dict):
            errors.append("invalid provenance artifact entry")
            continue
        artifact = (bundle / relative).resolve()
        if not is_within(artifact, bundle):
            errors.append(f"provenance path escapes bundle: {relative}")
            continue
        if not artifact.is_file():
            errors.append(f"artifact is missing: {relative}")
            continue
        actual = sha256_file(artifact)
        if actual != record.get("sha256"):
            errors.append(f"artifact hash mismatch: {relative}")
        if artifact.stat().st_size != record.get("bytes"):
            errors.append(f"artifact size mismatch: {relative}")
    actual_files = {
        item.relative_to(bundle).as_posix()
        for item in bundle.rglob("*")
        if item.is_file() and item.name != "provenance.json"
    }
    untracked = sorted(actual_files - set(artifacts))
    if untracked:
        errors.append("bundle contains untracked artifacts: " + ", ".join(untracked))
    return errors
