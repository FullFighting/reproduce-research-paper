#!/usr/bin/env python3
"""Preview or explicitly execute validated reproduction-plan commands."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_reproduction_plan import validate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true", help="run the reviewed command argv arrays")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"could not read plan: {exc}")
    errors = validate(plan, args.plan.resolve())
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    root_value = Path(plan["repository"])
    repository = root_value.resolve() if root_value.is_absolute() else (args.plan.parent / root_value).resolve()
    preview = {
        "mode": "execute" if args.execute else "preview",
        "repository": str(repository),
        "commands": [
            {"id": item["id"], "argv": item["argv"], "cwd": item.get("cwd", "."), "timeout_seconds": item["timeout_seconds"]}
            for item in plan["commands"]
        ],
    }
    if not args.execute:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0

    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for item in plan["commands"]:
        command_dir = (repository / item.get("cwd", ".")).resolve()
        started = time.time()
        record = {"id": item["id"], "argv": item["argv"], "cwd": str(command_dir), "timeout_seconds": item["timeout_seconds"]}
        try:
            result = subprocess.run(item["argv"], cwd=command_dir, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=item["timeout_seconds"], check=False)
            record.update({"exit_code": result.returncode, "timed_out": False})
            stdout, stderr = result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            record.update({"exit_code": None, "timed_out": True})
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        record["duration_seconds"] = round(time.time() - started, 3)
        stdout_path = args.output / f"{item['id']}.stdout.log"
        stderr_path = args.output / f"{item['id']}.stderr.log"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        record["stdout_log"] = stdout_path.name
        record["stderr_log"] = stderr_path.name
        records.append(record)
    payload = {"mode": "execute", "repository": str(repository), "commands": records}
    record_path = args.output / "run-record.json"
    record_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_record": str(record_path), "successful": all(item["exit_code"] == 0 and not item["timed_out"] for item in records)}, ensure_ascii=False, indent=2))
    return 0 if all(item["exit_code"] == 0 and not item["timed_out"] for item in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
