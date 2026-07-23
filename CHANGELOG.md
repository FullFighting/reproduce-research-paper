# Changelog

## 1.1.0 - 2026-07-23

- Makes `benchmarks/benchmark-summary.json` the single source for published benchmark counts and costs; CI rejects stale reports, README facts, and application facts.
- Reframes the benchmark as 15 public, paper-linked, claim-level executable cases rather than whole-paper reproductions.
- Adds a three-case Codex planning-evaluation pilot with prompts, draft/revised plans, review records, evidence bindings, and explicit unavailable telemetry.
- Documents why Codex handles semantic interpretation while deterministic tooling handles execution and verification.
- Narrows the proposed API-credit program to measurable planning evaluation, failure analysis, regression fixtures, community plans, transparency, and releases.
- Adds public issue forms, pull-request template, CODEOWNERS, roadmap, maintainer disclosure, and evaluation methodology.
- Links the release badge to the immutable GitHub release flow and records the public maintainer handle without inventing personal identity fields.

## 1.0.1 - 2026-07-23

- Preserve published evidence-bundle bytes across Windows and Linux Git checkouts so provenance hashes remain portable.

## 1.0.0 - 2026-07-23

First stable release.

- Removes the hand-written `observed-metrics.json` trust path.
- Extracts observations from run-bound stdout, stderr, JSON, CSV, NumPy, or Parquet artifacts.
- Marks manual tables and images `MANUAL_REVIEW_REQUIRED`; they cannot become reproduced claims.
- Adds complete repository tree hashes, Git commit/dirty/submodule state, category hashes, and pre/post snapshots.
- Adds copy, Git worktree, and Docker container execution modes with declared capability budgets.
- Uses secret references, a narrow child environment, masked argv, and unified log/URL/header redaction.
- Generates a complete evidence bundle and verifies every artifact before recomputing comparisons and reports.
- Replaces ambiguous `VERIFIED` with claim-scoped reproduction statuses.
- Adds explicit comparison policies, multi-run statistics, unit conversion, arrays/tables, correlation, order, equivalence intervals, and non-inferiority.
- Publishes 15 public, paper-linked, low-cost, claim-level evidence bundles covering scientific computing, machine learning, operations research, finance, and econometrics.
