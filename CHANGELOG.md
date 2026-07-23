# Changelog

## 1.2.0 - 2026-07-23

- Adds schema v2 typed expected values: scalar, array, labeled table, ranking, categorical, string, artifact hash, and distribution.
- Replaces the closed unit enum with validated `{symbol, scale, semantic_type}` descriptors while retaining schema-v1 verification.
- Adds exact, set, artifact-hash, labeled-table, string-ranking, and empirical distribution comparisons.
- Adds a source-bound file `sha256` extractor.
- Rejects argv secret references by default at validation and runtime; environment `secret_bindings` remain the safe default and an explicit high-risk compatibility mode is recorded.
- Refactors `SKILL.md` into a concise six-step workflow and moves schema, comparison, unit, and execution detail into conditional references.
- Adds direct offline-demo, tamper, dirty-source, undeclared-write, secret-redaction, release-archive, and Docker `--network none` CI checks.
- Pins GitHub Actions to full commit SHAs, adds Dependabot and CodeQL, and generates release checksums, an SPDX SBOM, unsigned provenance, and a GitHub build attestation.

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
