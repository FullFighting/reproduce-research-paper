# Security policy

Report a vulnerability through GitHub Security Advisories rather than a public issue when it could expose credentials, escape a declared workspace, bypass evidence integrity, or produce a false positive scientific status.

## Protected invariants

- no shell command strings;
- no literal plan credentials;
- no positive claim without a run-bound machine observation;
- no manual image/table promoted to a reproduced claim;
- no execution in the original source tree;
- no unreported original-source mutation or undeclared write;
- no report that trusts a stored verdict without recomputation;
- no claim that unsigned SHA-256 provenance proves authorship.

## Known V1 limits

- Copy/worktree mode cannot enforce host network isolation. `network=disabled` therefore requires container mode.
- Windows host mode records memory/CPU budgets but only enforces wall timeout and process-tree cleanup; use container mode for stronger controls.
- Secret values passed as argv may be visible to the operating-system process list. Prefer `secret_bindings`.
- Regex redaction is defense in depth, not a substitute for never emitting secrets.
- Unsigned provenance detects unsynchronized changes, not a malicious rewrite of both evidence and manifest.
- NumPy and Parquet extractors require optional third-party packages.

Please include the smallest safe reproducer, affected version, platform, and which invariant fails. Do not include a real credential or restricted research data.
