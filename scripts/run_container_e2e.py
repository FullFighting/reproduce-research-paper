#!/usr/bin/env python3
"""Run the bundled demo in a digest-pinned, network-disabled Docker container."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "reproduce-research-paper"
RUNNER = SKILL / "scripts" / "run_reproduction.py"
VERIFIER = SKILL / "scripts" / "build_report.py"
EXAMPLE = SKILL / "assets" / "examples" / "reproduction-plan.json"
TOY_REPOSITORY = SKILL / "assets" / "examples" / "toy-repository"


def command(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    return result


def digest_reference(image: str) -> str:
    if "@sha256:" in image:
        return image
    result = command(
        ["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", image]
    )
    reference = result.stdout.strip()
    if "@sha256:" not in reference:
        raise RuntimeError(f"Docker image has no repository digest: {image}")
    return reference


def failed_bundle_diagnostics(bundle: Path) -> dict:
    diagnostics: dict = {}
    record_path = bundle / "run-record.json"
    if record_path.is_file():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        diagnostics["policy_violations"] = record.get("policy_violations", [])
        diagnostics["commands"] = [
            {
                "id": item.get("id"),
                "exit_code": item.get("exit_code"),
                "timed_out": item.get("timed_out"),
                "error": item.get("error"),
                "policy_violations": item.get("policy_violations", []),
                "stderr": (
                    (bundle / item["stderr_log"]).read_text(
                        encoding="utf-8", errors="replace"
                    )
                    if item.get("stderr_log")
                    and (bundle / item["stderr_log"]).is_file()
                    else None
                ),
            }
            for item in record.get("commands", [])
        ]
    comparison_path = bundle / "comparison.json"
    if comparison_path.is_file():
        diagnostics["comparison"] = json.loads(
            comparison_path.read_text(encoding="utf-8")
        ).get("claims", [])
    return diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="python:3.12-alpine")
    parser.add_argument("--pull", action="store_true")
    args = parser.parse_args()
    if args.pull:
        command(["docker", "pull", args.image])
    image = digest_reference(args.image)
    plan = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    plan["repository"] = str(TOY_REPOSITORY.resolve())
    plan["execution"].update(
        {
            "workspace_mode": "container",
            "network": "disabled",
            "container_image": image,
        }
    )
    with tempfile.TemporaryDirectory(prefix="rrp-container-e2e-") as temp:
        root = Path(temp)
        plan_path = root / "plan.json"
        bundle = root / "bundle"
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        runner = command(
            [
                sys.executable,
                str(RUNNER),
                "--plan",
                str(plan_path),
                "--output",
                str(bundle),
                "--execute",
            ],
            check=False,
        )
        if runner.returncode != 0:
            raise RuntimeError(
                json.dumps(
                    {
                        "runner_stdout": runner.stdout,
                        "runner_stderr": runner.stderr,
                        "bundle": failed_bundle_diagnostics(bundle),
                    },
                    indent=2,
                )
            )
        command([sys.executable, str(VERIFIER), "--bundle", str(bundle)])
        record = json.loads((bundle / "run-record.json").read_text(encoding="utf-8"))
        execution = record["commands"][0]["capability_enforcement"]
        if execution.get("network") != "Docker --network none":
            raise RuntimeError("container did not record Docker --network none")
        if execution.get("source_write") != "Docker read-only bind mount":
            raise RuntimeError("container did not record a read-only source mount")
        if execution.get("capabilities") != "Docker --cap-drop ALL":
            raise RuntimeError("container did not record all capabilities dropped")
        if execution.get("privilege_escalation") != "Docker no-new-privileges=true":
            raise RuntimeError("container did not record no-new-privileges")
        if execution.get("syscalls") != "Docker built-in restricted seccomp profile":
            raise RuntimeError("container did not record restricted seccomp")
        if "non-root user" not in execution.get("identity", ""):
            raise RuntimeError("container did not record a non-root identity")
        if execution.get("image") != "digest-only plan reference with Docker --pull never":
            raise RuntimeError("container did not record digest-only no-pull policy")
        if record["repository_integrity"]["source_tree_changed"]:
            raise RuntimeError("container changed the source tree")
    print(json.dumps({"valid": True, "image": image, "network": "none"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
