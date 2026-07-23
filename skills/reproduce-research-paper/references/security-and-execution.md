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
- `container`: mount source read-only, mount outputs separately, require a
  digest-only image reference, refuse implicit pulls, and use Docker
  `--network none` when network is disabled.

Container mode also drops every Linux capability, sets
`no-new-privileges=true`, explicitly selects Docker's built-in restricted
seccomp profile, and runs as numeric non-root user `65532:65532` by default.
Set `execution.container_user` to another reviewed non-zero numeric `UID` or
`UID:GID` only when the output mount requires it. The runner never accepts root.

The image must already exist locally because `--pull never` is enforced. Pull
and inspect it as a separate maintainer-controlled admission step, verify its
publisher and digest, then place only the immutable form in the plan:

```json
{
  "workspace_mode": "container",
  "container_image": "registry.example/research@sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "container_user": "65532:65532"
}
```

Mutable tags, including tag-plus-digest references, are rejected so the evidence
record has one unambiguous image identity. Docker is an isolation layer, not a
proof against kernel or daemon compromise; high-risk adversarial code still
requires a dedicated host or VM and human approval.

Write the bundle outside the research repository. Reject external symlinks and preserve the original source.

## Capabilities

Declare network, write paths, memory, CPU, disk, output count, single-file size, GPU count, timeout, and retained workspace. Commands may narrow capabilities but may not rely on undeclared access.

Host limits differ by platform and must be recorded honestly. Use container mode when an enforced network boundary is required.

## Evidence invalidation

A source-tree change, undeclared workspace write, output-budget violation, unresolved secret, failed command, missing extractor source, or provenance mismatch prevents a positive claim result. Preserve the failed bundle and create a new plan for remediation.
