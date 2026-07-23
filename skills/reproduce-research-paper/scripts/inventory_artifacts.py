#!/usr/bin/env python3
"""Inventory a research repository without executing its code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules"}
DEPENDENCY_FILES = {
    "requirements.txt", "requirements-dev.txt", "environment.yml", "environment.yaml",
    "pyproject.toml", "poetry.lock", "Pipfile", "Pipfile.lock", "setup.py",
    "package.json", "package-lock.json", "conda-lock.yml", "Dockerfile",
}
ENTRYPOINT_NAMES = {"train.py", "main.py", "run.py", "experiment.py", "evaluate.py", "test.py"}
DATA_SUFFIXES = {".csv", ".tsv", ".json", ".jsonl", ".parquet", ".h5", ".hdf5", ".npz", ".npy"}
WEIGHT_SUFFIXES = {".pt", ".pth", ".ckpt", ".bin", ".safetensors", ".onnx"}


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def inventory(repository: Path, max_files: int) -> dict:
    root = repository.resolve()
    if not root.is_dir():
        raise ValueError(f"repository is not a directory: {root}")

    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
            if len(files) > max_files:
                raise ValueError(f"repository exceeds --max-files ({max_files})")

    names = {path.name for path in files}
    def selected(predicate):
        return sorted(relative(path, root) for path in files if predicate(path))

    return {
        "repository": str(root),
        "file_count": len(files),
        "dependency_files": selected(lambda p: p.name in DEPENDENCY_FILES),
        "entrypoints": selected(lambda p: p.name in ENTRYPOINT_NAMES or p.name.startswith("run_")),
        "data_files": selected(lambda p: p.suffix.lower() in DATA_SUFFIXES),
        "weight_files": selected(lambda p: p.suffix.lower() in WEIGHT_SUFFIXES),
        "documentation": selected(lambda p: p.name.lower() in {"readme.md", "readme.rst", "citation.cff", "license", "license.md"}),
        "has_license": any(name.lower() in {"license", "license.md", "copying"} for name in names),
        "large_files": [
            {"path": relative(path, root), "bytes": path.stat().st_size}
            for path in sorted(files)
            if path.stat().st_size >= 100 * 1024 * 1024
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--max-files", type=int, default=5000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.max_files < 1:
        parser.error("--max-files must be positive")
    try:
        result = inventory(args.repository, args.max_files)
    except ValueError as exc:
        parser.error(str(exc))
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
