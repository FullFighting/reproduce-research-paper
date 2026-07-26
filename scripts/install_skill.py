#!/usr/bin/env python3
"""Install, update, verify, or uninstall the bundled Codex Skill safely."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY / "skills" / "reproduce-research-paper"
VERSION_FILE = REPOSITORY / "VERSION"
SKILL_NAME = "reproduce-research-paper"
MANIFEST_NAME = ".codex-install-manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files() -> dict[str, Path]:
    return {
        path.relative_to(SOURCE).as_posix(): path
        for path in sorted(SOURCE.rglob("*"))
        if path.is_file()
        and path.name != MANIFEST_NAME
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }


def destination_for(scope: str, target: Path | None) -> Path:
    if scope == "user":
        if target is not None:
            raise ValueError("--target is only valid with --scope repository")
        codex_root = os.environ.get("CODEX_HOME")
        base = Path(codex_root).expanduser() if codex_root else Path.home() / ".codex"
        return (base / "skills" / SKILL_NAME).resolve()
    if target is None:
        raise ValueError("--target is required with --scope repository")
    repository = target.expanduser().resolve()
    if not repository.is_dir():
        raise ValueError(f"repository target is not a directory: {repository}")
    return repository / ".codex" / "skills" / SKILL_NAME


def build_manifest() -> dict[str, Any]:
    files = source_files()
    return {
        "schema_version": 1,
        "skill": SKILL_NAME,
        "version": VERSION_FILE.read_text(encoding="utf-8").strip(),
        "source_repository": "https://github.com/FullFighting/reproduce-research-paper",
        "files": {relative: sha256(path) for relative, path in files.items()},
    }


def load_manifest(destination: Path) -> dict[str, Any]:
    path = destination / MANIFEST_NAME
    if not path.is_file():
        raise ValueError(
            f"{destination} is not managed by this installer: missing {MANIFEST_NAME}"
        )
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or value.get("skill") != SKILL_NAME
        or not isinstance(value.get("files"), dict)
    ):
        raise ValueError(f"invalid installer manifest: {path}")
    return value


def drift(destination: Path, manifest: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for relative, expected in manifest["files"].items():
        path = destination / Path(relative)
        if not path.is_file():
            changed.append(f"missing:{relative}")
        elif sha256(path) != expected:
            changed.append(f"modified:{relative}")
    return changed


def remove_empty_directories(destination: Path) -> None:
    directories = sorted(
        (path for path in destination.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            pass
    try:
        destination.rmdir()
    except OSError:
        pass


def syntax_check(destination: Path) -> None:
    for path in destination.joinpath("scripts").glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def post_install_validate(destination: Path) -> None:
    syntax_check(destination)
    plan = destination / "assets" / "examples" / "reproduction-plan.json"
    validator = destination / "scripts" / "validate_reproduction_plan.py"
    result = subprocess.run(
        [sys.executable, "-B", str(validator), "--plan", str(plan)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "post-install validation failed:\n" + result.stdout + result.stderr
        )


def write_manifest(destination: Path, manifest: dict[str, Any]) -> None:
    (destination / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def install(destination: Path, dry_run: bool) -> None:
    if destination.exists():
        entries = list(destination.iterdir())
        if entries:
            if (destination / MANIFEST_NAME).is_file():
                raise ValueError(
                    f"{destination} is already installed; use --action update"
                )
            raise ValueError(f"refusing to overwrite unmanaged directory: {destination}")
    manifest = build_manifest()
    if dry_run:
        print(f"DRY RUN: install {len(manifest['files'])} files to {destination}")
        return
    destination.mkdir(parents=True, exist_ok=True)
    for relative, source in source_files().items():
        target = destination / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    write_manifest(destination, manifest)
    try:
        post_install_validate(destination)
    except Exception:
        print(
            f"WARNING: files were installed but post-install validation failed at {destination}",
            file=sys.stderr,
        )
        raise
    print(
        f"Installed {SKILL_NAME} {manifest['version']} to {destination}; "
        "post-install validation passed."
    )


def update(destination: Path, dry_run: bool, force: bool) -> None:
    old = load_manifest(destination)
    changed = drift(destination, old)
    if changed and not force:
        raise ValueError(
            "installed files have local changes; preserve them or rerun with --force: "
            + ", ".join(changed)
        )
    new = build_manifest()
    new_sources = source_files()
    obsolete = sorted(set(old["files"]) - set(new["files"]))
    if dry_run:
        print(
            f"DRY RUN: update {destination} from {old.get('version')} to "
            f"{new['version']}; remove {len(obsolete)} obsolete managed files"
        )
        return
    for relative in obsolete:
        path = destination / Path(relative)
        if path.is_file():
            if force or sha256(path) == old["files"][relative]:
                path.unlink()
            else:
                raise ValueError(f"refusing to delete modified managed file: {path}")
    for relative, source in new_sources.items():
        target = destination / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    write_manifest(destination, new)
    remove_empty_directories(destination)
    destination.mkdir(parents=True, exist_ok=True)
    post_install_validate(destination)
    print(
        f"Updated {SKILL_NAME} from {old.get('version')} to {new['version']} at "
        f"{destination}; post-install validation passed."
    )


def check(destination: Path) -> None:
    installed = load_manifest(destination)
    changed = drift(destination, installed)
    source = build_manifest()
    state = {
        "skill": SKILL_NAME,
        "destination": str(destination),
        "installed_version": installed.get("version"),
        "source_version": source["version"],
        "integrity": "valid" if not changed else "modified",
        "update_available": installed.get("version") != source["version"],
        "differences": changed,
    }
    print(json.dumps(state, indent=2))
    if changed:
        raise ValueError("installed skill integrity check failed")


def uninstall(destination: Path, dry_run: bool, force: bool) -> None:
    manifest = load_manifest(destination)
    changed = drift(destination, manifest)
    if changed and not force:
        raise ValueError(
            "installed files have local changes; uninstall refused: " + ", ".join(changed)
        )
    if dry_run:
        print(f"DRY RUN: remove {len(manifest['files'])} managed files from {destination}")
        return
    for relative, expected in manifest["files"].items():
        path = destination / Path(relative)
        if not path.exists():
            continue
        if not path.is_file():
            raise ValueError(f"managed path is no longer a file: {path}")
        if force or sha256(path) == expected:
            path.unlink()
        else:
            raise ValueError(f"refusing to remove modified file: {path}")
    (destination / MANIFEST_NAME).unlink(missing_ok=True)
    remove_empty_directories(destination)
    print(
        f"Uninstalled managed {SKILL_NAME} files from {destination}. "
        "Unmanaged files, if any, were preserved."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--action",
        choices=["install", "update", "check", "uninstall", "version"],
        default="install",
    )
    parser.add_argument("--scope", choices=["user", "repository"], default="user")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite or remove modified managed files; unmanaged files stay untouched.",
    )
    args = parser.parse_args()
    try:
        if args.action == "version":
            print(VERSION_FILE.read_text(encoding="utf-8").strip())
            return 0
        destination = destination_for(args.scope, args.target)
        if args.action == "install":
            install(destination, args.dry_run)
        elif args.action == "update":
            update(destination, args.dry_run, args.force)
        elif args.action == "check":
            check(destination)
        else:
            uninstall(destination, args.dry_run, args.force)
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, SyntaxError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
