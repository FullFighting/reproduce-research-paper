#!/usr/bin/env python3
"""Create a complete content-hashed repository inventory without executing code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_common import write_json
from repository_state import collect_repository_state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--max-files", type=int, default=100_000)
    parser.add_argument("--exclude", action="append", default=[], metavar="NAME=REASON")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    exclusions = {}
    for item in args.exclude:
        if "=" not in item:
            parser.error("--exclude must use NAME=REASON")
        name, reason = item.split("=", 1)
        if not name or not reason:
            parser.error("--exclude must use non-empty NAME=REASON")
        exclusions[name] = reason
    try:
        result = collect_repository_state(
            args.repository, max_files=args.max_files, extra_exclusions=exclusions
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
