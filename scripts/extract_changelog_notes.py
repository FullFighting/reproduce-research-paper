#!/usr/bin/env python3
"""Extract one version's section from CHANGELOG.md as release notes."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract_notes(changelog_text: str, version: str) -> str:
    pattern = (
        rf"^## {re.escape(version)}(?: - \d{{4}}-\d{{2}}-\d{{2}})?\n"
        r"(.*?)(?=^## |\Z)"
    )
    match = re.search(pattern, changelog_text, re.MULTILINE | re.DOTALL)
    if match is None:
        raise ValueError(f"CHANGELOG.md has no '## {version}' section")
    body = match.group(1).strip()
    if not body:
        raise ValueError(f"CHANGELOG.md section for {version} is empty")
    return body + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--changelog",
        type=Path,
        default=ROOT / "CHANGELOG.md",
        help="path to the changelog (default: repository CHANGELOG.md)",
    )
    parser.add_argument("--version", required=True, help="version section to extract, e.g. 1.4.0")
    parser.add_argument("--output", type=Path, required=True, help="file to write the notes to")
    args = parser.parse_args()

    notes = extract_notes(args.changelog.read_text(encoding="utf-8"), args.version)
    args.output.write_text(notes, encoding="utf-8")
    print(f"wrote release notes for {args.version} to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
