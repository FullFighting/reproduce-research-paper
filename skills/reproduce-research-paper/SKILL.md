---
name: reproduce-research-paper
description: Reproduce computational claims from research papers that have code, data, experiments, tables, figures, or model outputs. Use when Codex must read a paper as a whole, inspect its official repository, map claims to executable commands and machine-readable observations, run authorized low-cost or full experiments in an isolated workspace, compare results with explicit statistical policies, or produce a tamper-evident evidence bundle. Do not use to invent missing artifacts, treat a successful process exit as scientific proof, bypass access controls, or promote manually read figures to reproduced claims.
---

# Reproduce research paper

Reproduce a paper claim by claim. A positive result requires a continuous machine-traceable path:

`paper claim → exact plan → repository state → command → source artifact → extractor → normalized observation → comparison policy → report`

Resolve `SKILL_ROOT` as this file's directory. Invoke bundled scripts by absolute path when the working directory differs. The scripts require Python 3.10+ and the standard library; NumPy and Parquet extractors are optional.

## Non-negotiable rules

1. Read the entire paper before planning. Record its research question, method, data and split construction, training or inference procedure, evaluation protocol, relevant ablations, and stated limitations. Do not plan from the abstract alone.
2. Default to static inventory and command preview. Do not clone, install, download, access a private service, spend money, or start a long/GPU run until the user authorizes the exact action and budget.
3. Keep the original repository unchanged. Execute in `copy`, `git_worktree`, or `container` mode. Write the evidence bundle outside the research repository.
4. Never accept a hand-written observed-metrics file. Observations must be extracted from the run's logs or result files. A table, plot, screenshot, or human transcription is `MANUAL_REVIEW_REQUIRED`.
5. Never include a credential in a plan. Use `{"secret_ref": "NAME"}` or `secret_bindings`; the runtime resolves it from the environment and records only the reference.
6. Treat missing code, data, weights, licenses, seeds, hardware, or access as evidence. Do not guess or silently substitute.
7. A matching metric does not establish causality, correctness of the paper's explanation, or generalizability.

Read [evidence-policy.md](references/evidence-policy.md) before assigning status. Read [failure-taxonomy.md](references/failure-taxonomy.md) when a run is blocked, fails, or diverges. Use [report-schema.md](references/report-schema.md) when authoring a plan or inspecting a bundle.

## Workflow

### 1. Establish scope and authority

Identify:

- official paper and code URLs;
- exact target claim locations, such as a table cell, ablation row, statistic, or curve;
- public/private data, weights, and licenses;
- expected CPU, memory, disk, GPU, wall time, network, and monetary/API budget;
- whether the user authorizes a smoke reproduction, full experiment, or both.

If the paper or repository is not supplied, locate official sources. Prefer the publisher/venue page, author/project repository, and official data host. Keep preprints and third-party implementations labeled.

### 2. Inventory without executing

```powershell
python <SKILL_ROOT>/scripts/inventory_artifacts.py `
  --repository <research-repository> `
  --output <output-dir>/inventory.json
```

The inventory hashes every included file, not just README and dependency files. It records the Git commit, dirty diff, submodules, full tree, explicit exclusions and reasons, and separate code/data/weights/config/environment categories.

Do not exclude core model code, preprocessing, evaluation, configuration, data manifests, or environment locks. Exclude only restorable caches, version-control metadata, local environments, or artifacts whose omission has an explicit defensible reason.

### 3. Write a V1 plan

Start from [reproduction-plan.json](assets/examples/reproduction-plan.json). Every claim must have:

- `paper_location`, `metric`, `expected`, `unit`, and `protocol`;
- one or more required `command_ids`;
- a machine-executable `observation`;
- an explicit `comparison` policy.

Supported observation sources:

- `stdout` or `stderr` with `jsonpath` or `regex`;
- `file` with `jsonpath`, `regex`, `csv`, `npy`, or `parquet`;
- `manual`, which can only produce `MANUAL_REVIEW_REQUIRED`.

The safe JSONPath subset supports `$`, dotted members, and numeric indexes, for example `$.evaluation.test_accuracy` or `$.runs[0].score`. CSV expressions support a column, equality filters, delimiter/encoding, and `values`, `first`, `mean`, `median`, `min`, `max`, or `sum` aggregation.

Comparison methods include:

- `numeric_tolerance`;
- `equivalence_interval` with a V1 95% interval;
- `non_inferiority`;
- `spearman_correlation`;
- `exact_order`.

When multiple tolerances are supplied, set `combination` explicitly to `all` or `any`. Prefer `all` unless the paper's protocol justifies another rule. Set `minimum_runs` before execution. Record metric direction, aggregation, unit, and rounding allowance explicitly.

### 4. Validate and preview

```powershell
python <SKILL_ROOT>/scripts/validate_reproduction_plan.py `
  --plan <reproduction-plan.json>

python <SKILL_ROOT>/scripts/run_reproduction.py `
  --plan <reproduction-plan.json> `
  --output <new-evidence-bundle-directory>
```

Preview does not create the output directory. Review:

- exact masked argv arrays and relative working directories;
- isolation mode;
- network decision;
- declared write paths;
- time, memory, disk, file-count, file-size, and GPU limits;
- all secret references;
- every claim's source command and extractor.

Network defaults to disabled. V1 refuses to claim network isolation for host `copy` or `git_worktree` execution. Use `container` mode with a digest-pinned image for enforced `--network none`, or explicitly declare `unrestricted` after user review.

### 5. Execute only after authorization

```powershell
python <SKILL_ROOT>/scripts/run_reproduction.py `
  --plan <reproduction-plan.json> `
  --output <new-evidence-bundle-directory> `
  --execute
```

The runner:

- captures source and workspace state before and after;
- resolves secrets without recording their values;
- uses a narrow child environment and no shell;
- creates a process group and kills descendants on timeout;
- applies POSIX resource limits where available and records weaker Windows host enforcement;
- enforces Docker read-only source/network/memory/GPU controls in container mode;
- detects undeclared filesystem changes and output-budget violations;
- writes redacted logs;
- extracts observations directly from the run;
- computes comparison and report;
- creates provenance over every bundle artifact.

Do not suppress a failed or out-of-tolerance case. Preserve it and diagnose with a new plan or command ID.

### 6. Verify the bundle

```powershell
python <SKILL_ROOT>/scripts/build_report.py `
  --bundle <evidence-bundle-directory>
```

Verification must pass before delivery. It re-hashes every provenance entry, rejects missing or untracked artifacts, validates the observation's run-record and source hashes, recomputes all comparisons from plan + run + observations, and re-renders the report. It does not trust a stored verdict.

Use only:

- `CLAIM_REPRODUCED_WITHIN_TOLERANCE`
- `CLAIM_NOT_REPRODUCED`
- `PARTIALLY_REPRODUCED`
- `INCONCLUSIVE`
- `BLOCKED`
- `NOT_ATTEMPTED`
- `MANUAL_REVIEW_REQUIRED`

Put this sentence near the report status:

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Secret handling

Use an argv secret reference:

```json
["python", "download.py", "--api-key", {"secret_ref": "PAPER_DATA_API_KEY"}]
```

Or bind a secret environment variable:

```json
"secret_bindings": [
  {"name": "API_KEY", "secret_ref": "PAPER_DATA_API_KEY"}
]
```

Literal API keys, bearer headers, credentialed URLs, token query parameters, and secret-shaped plan keys or values are rejected. The run record stores `[SECRET_REF:PAPER_DATA_API_KEY]`. Treat process-list exposure of argv secrets as a reason to prefer `secret_bindings`.

## Interpretation

- An `EXTRACTED` observation is not yet a reproduced claim.
- A successful exit is not evidence that the right metric was computed.
- A SHA-256 match proves byte identity, not who produced the file.
- An unsigned provenance manifest cannot resist an attacker who can rewrite both evidence and provenance.
- Repository mutation, an unbound observation, an extractor failure, or a policy violation prevents a reproduced status.
- Report any version or protocol deviation even if the final number matches.

## Bundled resources

- `scripts/inventory_artifacts.py`: complete repository/Git inventory.
- `scripts/validate_reproduction_plan.py`: schema, path, capability, observation, comparison, and secret validation.
- `scripts/run_reproduction.py`: preview and isolated evidence-bundle execution.
- `scripts/extract_observations.py`: run-bound log/file extraction.
- `scripts/compare_metrics.py`: fresh statistical comparison from traceable observations.
- `scripts/build_report.py`: evidence-bundle verification and report recomputation.
- `assets/examples/`: offline end-to-end fixture.
- `references/`: evidence, schema, and failure contracts.

Professional peer review, plagiarism/academic-integrity checks, and deeper dataset-quality audits are future modules. Do not claim they are implemented in V1.
