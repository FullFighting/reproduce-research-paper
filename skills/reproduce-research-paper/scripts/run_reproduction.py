#!/usr/bin/env python3
"""Preview or execute a plan into an indivisible evidence bundle."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_report import render_report  # noqa: E402
from compare_metrics import compare_all  # noqa: E402
from evidence_bundle import create_provenance  # noqa: E402
from evidence_common import (  # noqa: E402
    GENERATOR_NAME,
    GENERATOR_VERSION,
    base_child_environment,
    is_within,
    object_sha256,
    redact_text,
    safe_relative_path,
    sha256_file,
    utc_now,
    write_json,
)
from extract_observations import extract_observations  # noqa: E402
from repository_state import (  # noqa: E402
    DEFAULT_EXCLUSIONS,
    collect_repository_state,
    diff_states,
)
from validate_reproduction_plan import plan_fingerprint, validate  # noqa: E402


def _copy_ignore(exclusions: dict[str, str]):
    excluded_names = set(DEFAULT_EXCLUSIONS) | set(exclusions)

    def ignore(_directory: str, names: list[str]) -> list[str]:
        return [name for name in names if name in excluded_names]

    return ignore


def _prepare_workspace(plan: dict, repository: Path, bundle: Path) -> tuple[Path, dict]:
    execution = plan["execution"]
    mode = execution["workspace_mode"]
    workspace = bundle / "workspace"
    if mode == "copy":
        shutil.copytree(
            repository,
            workspace,
            symlinks=True,
            ignore=_copy_ignore(execution.get("exclude_paths", {})),
        )
        return workspace, {"mode": mode, "isolation": "filesystem copy"}
    if mode == "git_worktree":
        probe = subprocess.run(
            ["git", "-C", str(repository), "status", "--porcelain=v1"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if probe.returncode != 0:
            raise ValueError("git_worktree mode requires a Git repository")
        if probe.stdout:
            raise ValueError("git_worktree mode requires a clean source worktree")
        commit = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if commit.returncode != 0:
            raise ValueError("could not resolve Git commit for worktree")
        added = subprocess.run(
            ["git", "-C", str(repository), "worktree", "add", "--detach", str(workspace), commit.stdout.strip()],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if added.returncode != 0:
            raise ValueError("could not create Git worktree: " + redact_text(added.stderr.strip()))
        return workspace, {"mode": mode, "isolation": "detached Git worktree", "commit": commit.stdout.strip()}
    workspace.mkdir(parents=True)
    return repository, {
        "mode": mode,
        "isolation": "Docker read-only source mount",
        "container_image": execution["container_image"],
    }


def _merge_capabilities(plan: dict, command: dict) -> dict:
    keys = {
        "network",
        "write_paths",
        "max_memory_mb",
        "max_cpu_seconds",
        "max_disk_mb",
        "max_output_files",
        "max_single_file_mb",
        "max_gpus",
    }
    merged = {key: plan["execution"][key] for key in keys if key in plan["execution"]}
    merged.update(command.get("capabilities", {}))
    return merged


def _resolve_command(
    command: dict,
    *,
    allow_argv_secrets: bool = False,
) -> tuple[list[str], list[Any], dict[str, str], list[str]]:
    actual: list[str] = []
    recorded: list[Any] = []
    secrets: list[str] = []
    for argument in command["argv"]:
        if isinstance(argument, str):
            actual.append(argument)
            recorded.append(argument)
        else:
            if not allow_argv_secrets:
                raise ValueError(
                    "argv secret_ref is disabled by default; use secret_bindings"
                )
            name = argument["secret_ref"]
            value = os.environ.get(name)
            if value is None:
                raise ValueError(f"required secret_ref is unavailable: {name}")
            actual.append(value)
            recorded.append(f"[SECRET_REF:{name}]")
            secrets.append(value)
    environment = base_child_environment()
    for binding in command.get("secret_bindings", []):
        reference = binding["secret_ref"]
        value = os.environ.get(reference)
        if value is None:
            raise ValueError(f"required secret_ref is unavailable: {reference}")
        environment[binding["name"]] = value
        secrets.append(value)
    return actual, recorded, environment, secrets


def _posix_limits(capabilities: dict):
    def configure() -> None:
        import resource

        cpu = int(capabilities["max_cpu_seconds"])
        memory = int(capabilities["max_memory_mb"]) * 1024 * 1024
        file_size = int(capabilities["max_single_file_mb"]) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_size, file_size))

    return configure


def _terminate_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _local_argv(
    actual: list[str],
    command_dir: Path,
    capabilities: dict,
    environment: dict[str, str],
    timeout: int,
) -> tuple[int | None, bool, str, str, dict]:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    preexec_fn = _posix_limits(capabilities) if os.name != "nt" else None
    enforcement = {
        "network": "explicitly unrestricted by reviewed plan",
        "memory": "POSIX rlimit" if os.name != "nt" else "recorded only on Windows host",
        "cpu": "POSIX rlimit plus wall timeout" if os.name != "nt" else "wall timeout on Windows host",
        "process_cleanup": "process group/tree termination",
    }
    process = subprocess.Popen(
        actual,
        cwd=command_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        env=environment,
        creationflags=creationflags,
        start_new_session=os.name != "nt",
        preexec_fn=preexec_fn,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, False, stdout, stderr, enforcement
    except subprocess.TimeoutExpired:
        _terminate_tree(process)
        stdout, stderr = process.communicate()
        return None, True, stdout, stderr, enforcement


def _container_argv(
    actual: list[str],
    command: dict,
    capabilities: dict,
    repository: Path,
    outputs: Path,
    image: str,
    timeout: int,
    environment: dict[str, str],
) -> tuple[int | None, bool, str, str, dict]:
    docker = [
        "docker",
        "run",
        "--rm",
        "--read-only",
        "--pids-limit",
        "256",
        "--memory",
        f"{capabilities['max_memory_mb']}m",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=256m",
        "--mount",
        f"type=bind,src={repository},dst=/workspace,readonly",
        "--mount",
        f"type=bind,src={outputs},dst=/outputs",
        "--workdir",
        f"/workspace/{command.get('cwd', '.')}",
    ]
    if capabilities["network"] == "disabled":
        docker.extend(["--network", "none"])
    if int(capabilities.get("max_gpus", 0)) > 0:
        docker.extend(["--gpus", str(capabilities["max_gpus"])])
    docker.extend(["-e", "REPRO_OUTPUT_DIR=/outputs"])
    for binding in command.get("secret_bindings", []):
        docker.extend(["-e", binding["name"]])
    docker.extend([image, *actual])
    result = _local_argv(
        docker,
        repository,
        {**capabilities, "max_memory_mb": max(capabilities["max_memory_mb"], 1024)},
        environment,
        timeout,
    )
    result[4].update(
        {
            "network": "Docker --network none" if capabilities["network"] == "disabled" else "explicitly unrestricted",
            "source_write": "Docker read-only bind mount",
            "memory": "Docker --memory",
            "gpu": "Docker --gpus" if capabilities.get("max_gpus") else "no GPU devices requested",
        }
    )
    return result


def _allowed(path: str, write_paths: list[str]) -> bool:
    normalized = Path(path).as_posix().rstrip("/")
    for item in write_paths:
        prefix = Path(item).as_posix().rstrip("/")
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def _output_budget(state: dict, changed_paths: list[str], capabilities: dict) -> list[str]:
    records = {item["path"]: item for item in state.get("files", [])}
    selected = [records[path] for path in changed_paths if path in records]
    violations = []
    if len(selected) > capabilities["max_output_files"]:
        violations.append(
            f"output file count {len(selected)} exceeds {capabilities['max_output_files']}"
        )
    max_bytes = capabilities["max_single_file_mb"] * 1024 * 1024
    oversized = [item["path"] for item in selected if item["bytes"] > max_bytes]
    if oversized:
        violations.append("single-file size limit exceeded: " + ", ".join(oversized))
    disk_bytes = sum(item["bytes"] for item in selected)
    if disk_bytes > capabilities["max_disk_mb"] * 1024 * 1024:
        violations.append(f"output bytes {disk_bytes} exceed disk budget")
    return violations


def _preserve_outputs(workspace: Path, outputs: Path, write_paths: list[str]) -> None:
    for value in sorted(set(write_paths)):
        relative = safe_relative_path(value, label="write_path")
        source = workspace / relative
        if not source.exists():
            continue
        destination = outputs / relative
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def _environment_artifact(plan: dict) -> dict:
    package_versions = {}
    for name in plan.get("environment", {}).get("packages", []):
        try:
            package_versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            package_versions[name] = None
    return {
        "schema_version": 1,
        "captured_at": utc_now(),
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable_name": Path(sys.executable).name,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "command_secret_refs": sorted(
            {
                argument["secret_ref"]
                for command in plan["commands"]
                for argument in command["argv"]
                if isinstance(argument, dict)
            }
            | {
                binding["secret_ref"]
                for command in plan["commands"]
                for binding in command.get("secret_bindings", [])
            }
        ),
        "declared_package_versions": package_versions,
        "lock_files": plan.get("environment", {}).get("lock_files", []),
        "environment_values_recorded": False,
    }


def _state_summary(state: dict) -> dict:
    return {key: value for key, value in state.items() if key != "files"}


def _external_symlinks(repository: Path, state: dict) -> list[str]:
    external: list[str] = []
    for record in state.get("files", []):
        if record.get("type") != "symlink":
            continue
        link = repository / record["path"]
        target = Path(record["target"])
        resolved = target.resolve() if target.is_absolute() else (link.parent / target).resolve()
        if not is_within(resolved, repository):
            external.append(record["path"])
    return external


def execute(plan: dict, plan_path: Path, bundle: Path) -> tuple[dict, bool]:
    repository_value = Path(plan["repository"])
    repository = (
        repository_value.resolve()
        if repository_value.is_absolute()
        else (plan_path.parent / repository_value).resolve()
    )
    if is_within(bundle, repository):
        raise ValueError("--output must be outside the research repository")
    if bundle.exists() and any(bundle.iterdir()):
        raise ValueError("--output must be a new or empty evidence-bundle directory")
    bundle.mkdir(parents=True, exist_ok=True)
    outputs = bundle / "outputs"
    logs = bundle / "logs"
    outputs.mkdir()
    logs.mkdir()
    write_json(bundle / "plan.json", plan)
    exclusions = plan["execution"].get("exclude_paths", {})
    source_before = collect_repository_state(repository, extra_exclusions=exclusions)
    write_json(bundle / "inventory-before.json", source_before)
    external_symlinks = _external_symlinks(repository, source_before)
    if external_symlinks:
        raise ValueError(
            "research repository contains symlinks that escape its root: "
            + ", ".join(external_symlinks)
        )
    environment = _environment_artifact(plan)
    write_json(bundle / "environment.json", environment)
    workspace, workspace_info = _prepare_workspace(plan, repository, bundle)
    workspace_before = collect_repository_state(
        workspace, extra_exclusions=exclusions, include_git=False
    )
    records = []
    policy_violations: list[str] = []
    deviations: list[str] = []
    allow_argv_secrets = bool(plan["execution"].get("allow_argv_secrets", False))
    if allow_argv_secrets:
        deviations.append(
            "HIGH_RISK_COMPATIBILITY: argv secret_ref values may be visible in process listings"
        )
    all_write_paths = list(plan["execution"].get("write_paths", []))
    for command in plan["commands"]:
        capabilities = _merge_capabilities(plan, command)
        all_write_paths.extend(capabilities.get("write_paths", []))
        started = time.time()
        before = collect_repository_state(
            workspace, extra_exclusions=exclusions, include_git=False
        )
        outputs_before = collect_repository_state(outputs, include_git=False)
        record: dict[str, Any] = {
            "id": command["id"],
            "cwd": command.get("cwd", "."),
            "timeout_seconds": command["timeout_seconds"],
            "capabilities": capabilities,
            "secret_refs": [
                argument["secret_ref"] for argument in command["argv"] if isinstance(argument, dict)
            ],
        }
        try:
            actual, recorded, child_environment, secrets = _resolve_command(
                command,
                allow_argv_secrets=allow_argv_secrets,
            )
            record["argv"] = recorded
            child_environment["REPRO_OUTPUT_DIR"] = str(outputs)
            if capabilities["network"] == "disabled" and plan["execution"]["workspace_mode"] != "container":
                raise ValueError(
                    "network=disabled requires container mode; host copy/worktree execution cannot prove network isolation"
                )
            if plan["execution"]["workspace_mode"] == "container":
                exit_code, timed_out, stdout, stderr, enforcement = _container_argv(
                    actual,
                    command,
                    capabilities,
                    repository,
                    outputs,
                    plan["execution"]["container_image"],
                    command["timeout_seconds"],
                    child_environment,
                )
            else:
                command_dir = (workspace / command.get("cwd", ".")).resolve()
                exit_code, timed_out, stdout, stderr, enforcement = _local_argv(
                    actual,
                    command_dir,
                    capabilities,
                    child_environment,
                    command["timeout_seconds"],
                )
            record.update(
                {
                    "exit_code": exit_code,
                    "timed_out": timed_out,
                    "capability_enforcement": enforcement,
                }
            )
            stdout, stderr = redact_text(stdout, secrets), redact_text(stderr, secrets)
        except (OSError, ValueError) as exc:
            record.update(
                {
                    "argv": record.get("argv", ["[UNRESOLVED]"]),
                    "exit_code": None,
                    "timed_out": False,
                    "capability_enforcement": {},
                    "error": redact_text(str(exc)),
                }
            )
            stdout, stderr = "", redact_text(str(exc))
        stdout_path = logs / f"{command['id']}.stdout.log"
        stderr_path = logs / f"{command['id']}.stderr.log"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        after = collect_repository_state(
            workspace, extra_exclusions=exclusions, include_git=False
        )
        outputs_after = collect_repository_state(outputs, include_git=False)
        difference = diff_states(before, after)
        outputs_difference = diff_states(outputs_before, outputs_after)
        changed = difference["added"] + difference["modified"] + difference["removed"]
        output_changed = (
            outputs_difference["added"]
            + outputs_difference["modified"]
            + outputs_difference["removed"]
        )
        unauthorized = [
            path for path in changed if not _allowed(path, capabilities.get("write_paths", []))
        ]
        unauthorized_outputs = [
            path
            for path in output_changed
            if not _allowed(path, capabilities.get("write_paths", []))
        ]
        command_violations = []
        if unauthorized:
            command_violations.append(
                f"{command['id']} wrote outside declared write_paths: {', '.join(unauthorized)}"
            )
        if unauthorized_outputs:
            command_violations.append(
                f"{command['id']} wrote outside declared output write_paths: "
                + ", ".join(unauthorized_outputs)
            )
        command_violations.extend(_output_budget(after, changed, capabilities))
        command_violations.extend(
            _output_budget(outputs_after, output_changed, capabilities)
        )
        policy_violations.extend(command_violations)
        record.update(
            {
                "duration_seconds": round(time.time() - started, 3),
                "stdout_log": stdout_path.relative_to(bundle).as_posix(),
                "stderr_log": stderr_path.relative_to(bundle).as_posix(),
                "stdout_sha256": sha256_file(stdout_path),
                "stderr_sha256": sha256_file(stderr_path),
                "filesystem_diff": {
                    "workspace": difference,
                    "outputs": outputs_difference,
                },
                "policy_violations": command_violations,
            }
        )
        records.append(record)
        if record["exit_code"] != 0 or record["timed_out"] or record.get("error"):
            break
    workspace_after = collect_repository_state(
        workspace, extra_exclusions=exclusions, include_git=False
    )
    source_after = collect_repository_state(repository, extra_exclusions=exclusions)
    source_diff = diff_states(source_before, source_after)
    workspace_diff = diff_states(workspace_before, workspace_after)
    source_changed = source_diff["tree_changed"]
    unauthorized_workspace = [
        path
        for path in workspace_diff["added"] + workspace_diff["modified"] + workspace_diff["removed"]
        if not _allowed(path, all_write_paths)
    ]
    write_json(bundle / "inventory-after.json", source_after)
    run_record = {
        "schema_version": 1,
        "mode": "execute",
        "created_at": utc_now(),
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "repository": repository.name,
        "plan_sha256": plan_fingerprint(plan),
        "inventory_before_sha256": sha256_file(bundle / "inventory-before.json"),
        "inventory_after_sha256": sha256_file(bundle / "inventory-after.json"),
        "environment_sha256": sha256_file(bundle / "environment.json"),
        "workspace": workspace_info,
        "repository_state": {
            "source_before": _state_summary(source_before),
            "source_after": _state_summary(source_after),
            "workspace_before": _state_summary(workspace_before),
            "workspace_after": _state_summary(workspace_after),
        },
        "repository_integrity": {
            "source_tree_changed": source_changed,
            "source_filesystem_diff": source_diff,
            "workspace_core_changed": bool(unauthorized_workspace),
            "unauthorized_workspace_changes": unauthorized_workspace,
        },
        "network_policy": plan["execution"]["network"],
        "argv_secret_compatibility_mode": allow_argv_secrets,
        "commands": records,
        "policy_violations": policy_violations,
        "deviations": deviations,
        "cost": {"api_tokens": 0, "estimated_cost_usd": 0},
    }
    write_json(bundle / "run-record.json", run_record)
    observations = extract_observations(
        plan,
        run_record,
        run_record_path=bundle / "run-record.json",
        bundle=bundle,
        workspace=workspace,
        outputs=outputs,
    )
    write_json(bundle / "observations.json", observations)
    comparison = compare_all(plan, observations, run_record)
    write_json(bundle / "comparison.json", comparison)
    report = render_report(
        plan,
        source_before,
        source_after,
        environment,
        run_record,
        observations,
        comparison,
    )
    (bundle / "report.md").write_text(report, encoding="utf-8")
    if plan["execution"].get("retain_workspace", False) is False:
        if plan["execution"]["workspace_mode"] != "container":
            _preserve_outputs(workspace, outputs, all_write_paths)
        workspace_path = bundle / "workspace"
        if workspace_path.exists() and is_within(workspace_path, bundle):
            if plan["execution"]["workspace_mode"] == "git_worktree":
                removal = subprocess.run(
                    ["git", "-C", str(repository), "worktree", "remove", "--force", str(workspace_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                if removal.returncode != 0:
                    deviations.append("created Git worktree could not be removed automatically")
            else:
                shutil.rmtree(workspace_path)
    create_provenance(bundle)
    successful = (
        len(records) == len(plan["commands"])
        and all(
            item.get("exit_code") == 0 and not item.get("timed_out") and not item.get("error")
            for item in records
        )
        and not source_changed
        and not policy_violations
    )
    return run_record, successful


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"could not read plan: {exc}")
    if not isinstance(plan, dict):
        parser.error("plan root must be an object")
    errors = validate(plan, args.plan.resolve())
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    preview = {
        "mode": "execute" if args.execute else "preview",
        "plan_sha256": plan_fingerprint(plan),
        "workspace_mode": plan["execution"]["workspace_mode"],
        "network": plan["execution"]["network"],
        "commands": [
            {
                "id": item["id"],
                "argv": [
                    argument if isinstance(argument, str) else f"[SECRET_REF:{argument['secret_ref']}]"
                    for argument in item["argv"]
                ],
                "cwd": item.get("cwd", "."),
                "timeout_seconds": item["timeout_seconds"],
                "capabilities": _merge_capabilities(plan, item),
            }
            for item in plan["commands"]
        ],
    }
    if not args.execute:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0
    try:
        _, successful = execute(plan, args.plan.resolve(), args.output.resolve())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.error(redact_text(str(exc)))
    print(
        json.dumps(
            {
                "evidence_bundle": str(args.output.resolve()),
                "successful": successful,
                "verifier": f"python {Path(__file__).with_name('build_report.py')} --bundle {args.output.resolve()}",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
