#!/usr/bin/env python3
"""Report advisory reproducibility-readiness signals for a research repository.

The scan is a planning aid for the Inventory step: it records which
reproduction-relevant artifacts a bounded, read-only walk could find, with the
matching paths as evidence. It never executes repository code, never assigns a
quality grade, and never produces a reproduction status. A missing signal means
this scan found no matching artifact, not that the artifact does not exist.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
from pathlib import Path, PurePosixPath

from evidence_common import utc_now, write_json

SKIP_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".venv",
    "venv",
    "node_modules",
    ".ipynb_checkpoints",
}
MAX_EVIDENCE_PATHS = 5
CONTENT_PROBE_LIMIT_BYTES = 256 * 1024
MAX_CONTENT_PROBE_FILES = 200
SEED_TOKEN = re.compile(r"(?i)(?<![a-z0-9_])seed(?![a-z0-9])")
SEED_PROBE_SUFFIXES = {".py", ".r", ".jl", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini"}
FENCED_BLOCK = re.compile(r"^\s*(```|~~~)", re.MULTILINE)

PATTERN_SIGNALS: list[tuple[str, str, list[str]]] = [
    (
        "dependency_declaration",
        "Machine-readable dependency declaration",
        [
            "requirements*.txt",
            "requirements*.in",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "environment.yml",
            "environment.yaml",
            "Pipfile",
            "package.json",
            "DESCRIPTION",
            "Project.toml",
            "Cargo.toml",
            "go.mod",
        ],
    ),
    (
        "pinned_environment",
        "Lock file or otherwise pinned environment",
        [
            "*.lock",
            "*lock.txt",
            "*lock.yml",
            "*lock.yaml",
            "*lock.json",
            "Manifest.toml",
        ],
    ),
    (
        "license_statement",
        "License or copying statement",
        ["LICENSE*", "LICENCE*", "COPYING*"],
    ),
    (
        "automated_tests",
        "Automated test files or test configuration",
        [
            "test_*.py",
            "*_test.py",
            "tests/*",
            "test/*",
            "pytest.ini",
            "tox.ini",
            "noxfile.py",
        ],
    ),
    (
        "continuous_integration",
        "Continuous-integration configuration",
        [
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
            ".gitlab-ci.yml",
            ".travis.yml",
            "azure-pipelines.yml",
            ".circleci/config.yml",
            "Jenkinsfile",
        ],
    ),
    (
        "containerized_environment",
        "Container or reproducible-environment definition",
        [
            "Dockerfile*",
            "*.dockerfile",
            "docker-compose*.yml",
            "docker-compose*.yaml",
            "*.def",
            ".devcontainer/*",
            "flake.nix",
            "shell.nix",
        ],
    ),
    (
        "data_access_documentation",
        "Data directory, data documentation, or data-pipeline manifest",
        [
            "data/*",
            "datasets/*",
            "DATA*.md",
            "dvc.yaml",
            "dvc.lock",
            "*.dvc",
            "datapackage.json",
        ],
    ),
    (
        "model_artifact_pointers",
        "Committed model artifacts or artifact directories",
        [
            "models/*",
            "checkpoints/*",
            "weights/*",
            "*.ckpt",
            "*.pt",
            "*.pth",
            "*.onnx",
            "*.safetensors",
            "*.h5",
        ],
    ),
    (
        "experiment_configuration",
        "Separated experiment configuration",
        [
            "config/*",
            "configs/*",
            "conf/*",
            "params.yaml",
            "hparams.yaml",
            "hparams.json",
        ],
    ),
    (
        "citation_metadata",
        "Citation or archival metadata",
        ["CITATION*", "codemeta.json", ".zenodo.json"],
    ),
]


def iter_repository_files(repository: Path, max_files: int) -> tuple[list[str], bool]:
    collected: list[str] = []
    truncated = False
    for current_root, directories, files in os.walk(repository, followlinks=False):
        directories[:] = sorted(
            name
            for name in directories
            if name not in SKIP_DIRECTORIES
            and not Path(current_root, name).is_symlink()
        )
        for name in sorted(files):
            path = Path(current_root, name)
            if path.is_symlink():
                continue
            collected.append(path.relative_to(repository).as_posix())
            if len(collected) >= max_files:
                truncated = True
                return collected, truncated
    return collected, truncated


def matches(relative_path: str, pattern: str) -> bool:
    if pattern.endswith("/*"):
        return relative_path.startswith(pattern[:-1])
    if "/" in pattern:
        return fnmatch.fnmatch(relative_path, pattern)
    return fnmatch.fnmatch(PurePosixPath(relative_path).name, pattern)


def pattern_signal(signal_id: str, title: str, patterns: list[str], files: list[str]) -> dict:
    evidence = []
    for relative_path in files:
        if any(matches(relative_path, pattern) for pattern in patterns):
            evidence.append(relative_path)
            if len(evidence) >= MAX_EVIDENCE_PATHS:
                break
    return {
        "id": signal_id,
        "title": title,
        "present": bool(evidence),
        "evidence": evidence,
        "detail": f"matched name patterns: {', '.join(patterns)}",
    }


def read_probe(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            raw = handle.read(CONTENT_PROBE_LIMIT_BYTES)
    except OSError:
        return ""
    return raw.decode("utf-8", errors="replace")


def run_instructions_signal(repository: Path, files: list[str]) -> tuple[dict, int]:
    readmes = [item for item in files if PurePosixPath(item).name.lower().startswith("readme")]
    probes = 0
    evidence: list[str] = []
    fenced = False
    for relative_path in readmes[:MAX_CONTENT_PROBE_FILES]:
        probes += 1
        if FENCED_BLOCK.search(read_probe(repository / relative_path)):
            fenced = True
            evidence = [relative_path]
            break
    if not fenced and readmes:
        evidence = readmes[:1]
    return (
        {
            "id": "run_instructions",
            "title": "README with fenced command examples",
            "present": fenced,
            "evidence": evidence,
            "detail": (
                "a README containing a fenced code block was found"
                if fenced
                else "no README with a fenced code block was found; "
                "a README without one still appears in evidence when present"
            ),
        },
        probes,
    )


def seed_signal(repository: Path, files: list[str]) -> tuple[dict, int]:
    evidence: list[str] = []
    probes = 0
    candidates = [
        item for item in files if PurePosixPath(item).suffix.lower() in SEED_PROBE_SUFFIXES
    ]
    scanned_all = len(candidates) <= MAX_CONTENT_PROBE_FILES
    for relative_path in candidates[:MAX_CONTENT_PROBE_FILES]:
        probes += 1
        if SEED_TOKEN.search(read_probe(repository / relative_path)):
            evidence.append(relative_path)
            if len(evidence) >= MAX_EVIDENCE_PATHS:
                break
    return (
        {
            "id": "seed_control_mentions",
            "title": "Random-seed handling mentioned in code or configuration",
            "present": bool(evidence),
            "evidence": evidence,
            "detail": (
                "heuristic token scan over code and configuration files"
                + ("" if scanned_all else f"; probe capped at {MAX_CONTENT_PROBE_FILES} files")
            ),
        },
        probes,
    )


def assess(repository: Path, max_files: int) -> dict:
    files, truncated = iter_repository_files(repository, max_files)
    signals = [
        pattern_signal(signal_id, title, patterns, files)
        for signal_id, title, patterns in PATTERN_SIGNALS
    ]
    readme_result, readme_probes = run_instructions_signal(repository, files)
    seed_result, seed_probes = seed_signal(repository, files)
    signals.extend([readme_result, seed_result])
    signals.sort(key=lambda item: item["id"])
    return {
        "schema_version": 1,
        "tool": "assess_repository_readiness",
        "generated_at": utc_now(),
        "repository": str(repository),
        "scan": {
            "files_scanned": len(files),
            "max_files": max_files,
            "truncated": truncated,
            "content_probe_limit_bytes": CONTENT_PROBE_LIMIT_BYTES,
            "content_probes": readme_probes + seed_probes,
        },
        "signals": signals,
        "signals_present": sum(item["present"] for item in signals),
        "signals_total": len(signals),
        "interpretation": (
            "Advisory planning signals from a bounded, read-only scan. A missing signal "
            "means no matching artifact was found by this scan, not proof of absence. "
            "Presence is never a reproduction status and never validates a claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--max-files", type=int, default=50_000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repository = args.repository
    if not repository.is_dir():
        parser.error(f"repository is not a directory: {repository}")
    if args.max_files < 1:
        parser.error("--max-files must be at least 1")
    result = assess(repository, args.max_files)
    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
