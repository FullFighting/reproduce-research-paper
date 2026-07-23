#!/usr/bin/env python3
"""Extract a Git archive safely and run release-critical checks from the archive."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path, PurePosixPath


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}{result.stderr}"
        )


def safe_extract(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, "r:*") as handle:
        members = handle.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"archive member escapes extraction root: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"release archive contains a link: {member.name}")
            if not member.isdir() and not member.isfile():
                raise ValueError(
                    f"release archive contains a special file: {member.name}"
                )
        for member in members:
            target = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = handle.extractfile(member)
            if source is None:
                raise ValueError(f"could not read archive member: {member.name}")
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    children = [path for path in destination.iterdir()]
    return children[0] if len(children) == 1 and children[0].is_dir() else destination


def verify_archive(archive: Path, temp_root: Path) -> None:
    repository = safe_extract(archive, temp_root / "source")
    python = sys.executable
    skill_scripts = repository / "skills" / "reproduce-research-paper" / "scripts"
    example = (
        repository
        / "skills"
        / "reproduce-research-paper"
        / "assets"
        / "examples"
        / "reproduction-plan.json"
    )
    run(
        [
            python,
            "-m",
            "compileall",
            "-q",
            "skills/reproduce-research-paper/scripts",
            "scripts",
        ],
        repository,
    )
    run([python, "scripts/sync_benchmark_facts.py", "--check"], repository)
    run([python, "scripts/validate_codex_evaluation.py"], repository)
    run([python, "-m", "unittest", "discover", "-s", "tests", "-v"], repository)
    run(
        [
            python,
            str(skill_scripts / "validate_reproduction_plan.py"),
            "--plan",
            str(example),
        ],
        repository,
    )
    bundle = temp_root / "offline-demo-bundle"
    run(
        [
            python,
            str(skill_scripts / "run_reproduction.py"),
            "--plan",
            str(example),
            "--output",
            str(bundle),
            "--execute",
        ],
        repository,
    )
    run(
        [python, str(skill_scripts / "build_report.py"), "--bundle", str(bundle)],
        repository,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument(
        "--work-directory",
        type=Path,
        help="optional parent for temporary verification files",
    )
    args = parser.parse_args()
    archive = args.archive.resolve()
    if args.work_directory is None:
        with tempfile.TemporaryDirectory(prefix="rrp-release-verify-") as temp:
            verify_archive(archive, Path(temp))
    else:
        temporary_parent = args.work_directory.resolve()
        temporary_parent.mkdir(parents=True, exist_ok=True)
        temp_root = temporary_parent / f"rrp-release-verify-{uuid.uuid4().hex}"
        temp_root.mkdir()
        try:
            verify_archive(archive, temp_root)
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)
    print(
        json.dumps(
            {
                "valid": True,
                "archive": archive.name,
                "checks": [
                    "compile",
                    "benchmark-facts",
                    "codex-evaluation",
                    "unit-tests",
                    "offline-demo",
                    "bundle-verification",
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
