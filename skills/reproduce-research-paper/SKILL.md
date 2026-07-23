---
name: reproduce-research-paper
description: Reproduce and audit computational research papers that have code, data, experiments, tables, or figures. Use when Codex needs to turn paper claims into an executable reproduction plan; inspect a research repository; run authorized experiments; compare reported and observed metrics; detect missing artifacts, data leakage risks, or undocumented dependencies; or produce an evidence-first reproducibility report. Do not use to invent missing data, fabricate a successful replication, bypass access controls, or run costly experiments without authorization.
---

# Reproduce research paper

Treat reproduction as a claim-by-claim audit, not a binary question of whether a repository starts. Preserve the paper's claim, the exact command, the source artifact, the observed output, and every uncertainty.

Resolve `SKILL_ROOT` as this file's directory. Resolve bundled files relative to it and use absolute paths when invoking a script from another working directory. Use Python 3.10+; on Windows, use UTF-8 mode (`-X utf8`) when needed.

## Scope and safety

1. Establish the paper, repository, requested claims (for example, Table 2 or Figure 4), available data and weights, compute/time budget, and whether network access is allowed.
2. Default to an inventory and a dry-run plan. Do not clone, install dependencies, download data, access private services, spend money, or begin a long/GPU experiment until the user authorizes it.
3. Keep the original repository untouched. Use a copy, worktree, or user-designated working directory; write logs and reports to a separate output directory.
4. Treat missing code, data, licenses, access, seeds, or hardware information as evidence of a blocked or partial reproduction, never as permission to guess.
5. Never bypass a paywall, login, license, CAPTCHA, rate limit, or access restriction. Do not expose tokens, dataset credentials, or unpublished results.

## Workflow

### 1. Inventory the artifacts

Run the deterministic inventory before choosing commands:

```powershell
python <SKILL_ROOT>/scripts/inventory_artifacts.py `
  --repository <working-copy> `
  --output <output-dir>/artifact-inventory.json
```

Read [evidence-policy.md](references/evidence-policy.md) before assigning a reproduction status. Read [failure-taxonomy.md](references/failure-taxonomy.md) when an artifact is incomplete or a run fails.

Check the paper against the inventory: each target claim needs a paper location, a reported metric/figure/table, a command or entry point, inputs, configuration, and an observable output. Record only claims that can be stated precisely.

### 2. Write and validate a reproduction plan

Copy and adapt [reproduction-plan.json](assets/examples/reproduction-plan.json). Plans use argument arrays, not shell strings, so the command and working directory are reviewable.

```powershell
python <SKILL_ROOT>/scripts/validate_reproduction_plan.py `
  --plan <reproduction-plan.json>

python <SKILL_ROOT>/scripts/run_reproduction.py `
  --plan <reproduction-plan.json> `
  --output <output-dir>
```

The second command is a preview: it does not execute the paper's code or write a run record. Fix every validation error before asking the user to authorize execution. In particular, do not permit secrets in a plan, shell command strings, unbounded timeouts, or working directories outside the copied repository.

### 3. Execute only after authorization

After the user approves the exact commands, allowed network use, and expected compute cost, run:

```powershell
python <SKILL_ROOT>/scripts/run_reproduction.py `
  --plan <reproduction-plan.json> `
  --output <output-dir> `
  --execute
```

The runner creates `run-record.json` and per-command stdout/stderr logs. It executes only the reviewed `argv` arrays in the plan; it does not install packages or fetch data by itself. Stop on a failed command unless the user requests a diagnostic continuation.

### 4. Compare reported and observed results

Put extracted results in the documented observed-metrics shape, then compare them against the numeric claims in the plan:

```powershell
python <SKILL_ROOT>/scripts/compare_metrics.py `
  --plan <reproduction-plan.json> `
  --observed <observed-metrics.json> `
  --output <output-dir>/metric-comparison.json
```

Use the paper's stated protocol and predeclare an absolute or relative tolerance. Do not tune seeds, preprocessing, hyperparameters, evaluation subsets, or stopping rules merely to make a result match. If a deviation requires an exploratory change, record it as a separate sensitivity run, not the primary reproduction.

### 5. Build an evidence report

```powershell
python <SKILL_ROOT>/scripts/build_report.py `
  --plan <reproduction-plan.json> `
  --inventory <output-dir>/artifact-inventory.json `
  --comparison <output-dir>/metric-comparison.json `
  --run-record <output-dir>/run-record.json `
  --output <output-dir>/reproduction-report.md
```

Use only these statuses:

- `VERIFIED`: target evidence was executed and all compared claims met predeclared tolerances.
- `PARTIAL`: at least one target claim was verified, but another was blocked, not comparable, or failed.
- `CONTRADICTED`: an executed, comparable claim fell outside its predeclared tolerance.
- `BLOCKED`: required artifacts, access, or execution prerequisites were unavailable.
- `NOT_RUN`: the requested experiment was not executed.

Do not call a claim verified solely because code ran. Do not call an observed correlation proof of a paper's causal explanation. State hardware, software versions, data version, seeds, command IDs, and deviations that materially affect interpretation.

## Diagnosis guidance

- Check data split overlap, test-set reuse, label leakage, preprocessing performed before splitting, and metrics computed on a different sample than the paper describes.
- Check version pins, model checkpoints, licenses, random seeds, hardware assumptions, hidden environment variables, and undocumented manual steps.
- Prefer the smallest smoke test first; expand to the requested full result only after the pipeline is understood and authorized.
- Preserve failed logs and classify the failure using [failure-taxonomy.md](references/failure-taxonomy.md). A failure fixture is a valuable regression case after private data and licensed text are removed.

## Bundled resources

- `scripts/inventory_artifacts.py`: produce a deterministic code/data/environment inventory without executing project code.
- `scripts/validate_reproduction_plan.py`: validate a reviewable, secret-free plan.
- `scripts/run_reproduction.py`: preview or explicitly execute only plan-declared commands.
- `scripts/compare_metrics.py`: compare declared numeric claims with observed metrics.
- `scripts/build_report.py`: render a concise evidence-first Markdown report.
- [report-schema.md](references/report-schema.md): JSON shapes and report contract.
- `assets/examples/`: a self-contained plan, observed metrics, and expected report shape for offline testing.
