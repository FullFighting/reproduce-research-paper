# Security and execution boundaries

## Contents

- [Secret invariant](#secret-invariant)
- [High-risk argv compatibility](#high-risk-argv-compatibility)
- [Workspace modes](#workspace-modes)
- [Capabilities](#capabilities)
- [Evidence invalidation](#evidence-invalidation)

## Secret invariant

Secret values must not appear in a plan, recorded argv, URL, header, exception, or log. Bind environment variables:

```json
{
  "argv": ["python", "download.py"],
  "secret_bindings": [
    {"name": "API_KEY", "secret_ref": "PAPER_DATA_API_KEY"}
  ]
}
```

The runtime reads `PAPER_DATA_API_KEY` from its environment, exposes it to the child as `API_KEY`, records only the reference, and applies the same redaction to logs and errors.

Literal secrets and values following sensitive flags are rejected.

## High-risk argv compatibility

Schema v2 rejects this by default:

```json
["python", "download.py", "--api-key", {"secret_ref": "PAPER_DATA_API_KEY"}]
```

The value could be visible in process listings. Only when a legacy tool cannot read an environment variable may a reviewed plan set:

```json
"allow_argv_secrets": true
```

The runner independently enforces the default, records `argv_secret_compatibility_mode: true`, masks the recorded value, and adds a `HIGH_RISK_COMPATIBILITY` deviation. Prefer a narrowly permissioned temporary credential and rotate it after use.

## Workspace modes

- `copy`: run in a temporary copy; host network isolation is not claimed.
- `git_worktree`: require a clean Git source and run in a detached worktree.
- `container`: mount source read-only, mount outputs separately, pin the image digest, and use Docker `--network none` when network is disabled.

Write the bundle outside the research repository. Reject external symlinks and preserve the original source.

## Capabilities

Declare network, write paths, memory, CPU, disk, output count, single-file size, GPU count, timeout, and retained workspace. Commands may narrow capabilities but may not rely on undeclared access.

Host limits differ by platform and must be recorded honestly. Use container mode when an enforced network boundary is required.

## Evidence invalidation

A source-tree change, undeclared workspace write, output-budget violation, unresolved secret, failed command, missing extractor source, or provenance mismatch prevents a positive claim result. Preserve the failed bundle and create a new plan for remediation.
