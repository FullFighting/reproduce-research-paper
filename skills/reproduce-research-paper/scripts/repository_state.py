#!/usr/bin/env python3
"""Hash a complete repository tree and record its Git state."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path

from evidence_common import object_sha256, sha256_file, utc_now

DEFAULT_EXCLUSIONS = {
    ".git": "Git object database and worktree metadata",
    ".hg": "Mercurial metadata",
    ".svn": "Subversion metadata",
    "__pycache__": "interpreter cache",
    ".pytest_cache": "test cache",
    ".mypy_cache": "type-checker cache",
    ".venv": "local virtual environment",
    "venv": "local virtual environment",
    "node_modules": "restorable dependency tree",
}
DATA_SUFFIXES = {
    ".csv", ".tsv", ".jsonl", ".parquet", ".arrow", ".h5", ".hdf5", ".npy", ".npz",
    ".wav", ".flac", ".jpg", ".jpeg", ".png",
}
WEIGHT_SUFFIXES = {".pt", ".pth", ".ckpt", ".bin", ".safetensors", ".onnx", ".pb"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".toml", ".ini", ".cfg"}
ENVIRONMENT_NAMES = {
    "requirements.txt", "requirements-dev.txt", "environment.yml", "environment.yaml",
    "pyproject.toml", "poetry.lock", "pipfile", "pipfile.lock", "setup.py",
    "package.json", "package-lock.json", "conda-lock.yml", "dockerfile",
}


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _category(path: Path) -> str:
    lower_name = path.name.lower()
    suffix = path.suffix.lower()
    if (
        lower_name in ENVIRONMENT_NAMES
        or (
            lower_name.startswith("requirements")
            and lower_name.endswith((".txt", ".in"))
        )
        or lower_name.endswith((".lock", ".lock.txt"))
    ):
        return "environment"
    if suffix in WEIGHT_SUFFIXES:
        return "weights"
    if suffix in DATA_SUFFIXES:
        return "data"
    if suffix in CONFIG_SUFFIXES or lower_name.endswith(".config.json"):
        return "config"
    return "code"


def _category_hash(records: Iterable[dict]) -> str:
    return object_sha256(
        [{"path": item["path"], "sha256": item["sha256"], "bytes": item["bytes"]} for item in records]
    )


def collect_repository_state(
    repository: Path,
    *,
    max_files: int = 100_000,
    extra_exclusions: dict[str, str] | None = None,
    include_git: bool = True,
) -> dict:
    root = repository.resolve()
    if not root.is_dir():
        raise ValueError(f"repository is not a directory: {root}")
    exclusions = dict(DEFAULT_EXCLUSIONS)
    exclusions.update(extra_exclusions or {})
    records: list[dict] = []
    excluded: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        excluded_part = next((part for part in relative.parts if part in exclusions), None)
        if excluded_part:
            excluded[excluded_part] = exclusions[excluded_part]
            continue
        if path.is_symlink():
            target = str(path.readlink())
            records.append(
                {
                    "path": relative.as_posix(),
                    "type": "symlink",
                    "target": target,
                    "bytes": len(target.encode("utf-8")),
                    "sha256": hashlib.sha256(target.encode("utf-8")).hexdigest(),
                    "category": "code",
                }
            )
        elif path.is_file():
            records.append(
                {
                    "path": relative.as_posix(),
                    "type": "file",
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "category": _category(path),
                }
            )
        if len(records) > max_files:
            raise ValueError(f"repository exceeds max_files ({max_files})")
    categories = {}
    for name in ("code", "data", "weights", "config", "environment"):
        selected = [item for item in records if item["category"] == name]
        categories[name] = {
            "file_count": len(selected),
            "bytes": sum(item["bytes"] for item in selected),
            "sha256": _category_hash(selected),
        }
    tree_sha256 = object_sha256(records)
    git_commit = None
    git_dirty = None
    dirty_diff_sha256 = None
    submodules: dict[str, str] = {}
    probe = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if include_git and probe.returncode == 0 and probe.stdout.strip() == "true":
        commit = _run_git(root, ["rev-parse", "HEAD"])
        git_commit = commit.stdout.strip() if commit.returncode == 0 else None
        status = _run_git(root, ["status", "--porcelain=v1", "--untracked-files=all", "--", "."])
        if status.returncode == 0:
            git_dirty = bool(status.stdout)
            diff = _run_git(root, ["diff", "--binary", "HEAD", "--", "."])
            dirty_material = (status.stdout + "\n" + (diff.stdout if diff.returncode == 0 else "")).encode("utf-8")
            dirty_diff_sha256 = hashlib.sha256(dirty_material).hexdigest()
        module_status = _run_git(root, ["submodule", "status", "--recursive"])
        if module_status.returncode == 0:
            for line in module_status.stdout.splitlines():
                stripped = line.strip()
                parts = stripped.lstrip("-+U").split()
                if len(parts) >= 2:
                    submodules[parts[1]] = stripped[0:1] + parts[0]
    state = {
        "schema_version": 1,
        "captured_at": utc_now(),
        "repository": root.name,
        "file_count": len(records),
        "bytes": sum(item["bytes"] for item in records),
        "tree_sha256": tree_sha256,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "dirty_diff_sha256": dirty_diff_sha256,
        "submodules": submodules,
        "exclusions": [{"path_component": key, "reason": exclusions[key]} for key in sorted(excluded)],
        "categories": categories,
        "files": records,
    }
    state["inventory_sha256"] = object_sha256(
        {key: value for key, value in state.items() if key not in {"captured_at", "inventory_sha256"}}
    )
    return state


def file_map(state: dict) -> dict[str, str]:
    return {item["path"]: item["sha256"] for item in state.get("files", [])}


def diff_states(before: dict, after: dict) -> dict:
    left, right = file_map(before), file_map(after)
    return {
        "added": sorted(set(right) - set(left)),
        "removed": sorted(set(left) - set(right)),
        "modified": sorted(path for path in set(left) & set(right) if left[path] != right[path]),
        "tree_changed": before.get("tree_sha256") != after.get("tree_sha256"),
    }


def write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
