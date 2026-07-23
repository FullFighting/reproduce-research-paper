# Changelog

## 1.0.0 — 2026-07-23

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
- Publishes 15 real-paper, public, low-cost evidence bundles covering scientific computing, machine learning, operations research, finance, and econometrics.
