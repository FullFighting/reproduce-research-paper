# Changelog

## 1.4.0 - 2026-07-26

- Adds a repository-wide `ruff` lint gate with a pinned version in CI, a checked-in `pyproject.toml` rule set, and an `.editorconfig`; fixes all existing findings without changing rendered report bytes, so previously published evidence bundles still verify.
- Makes runtime length mismatches explicit by passing `strict=True` to paired `zip()` iterations in metric comparison and the evaluation runner.
- Extends the CI test matrix to Python 3.10, 3.12, and 3.13 on Linux and Windows, adds per-job timeouts, and cancels superseded non-main workflow runs.
- Publishes a source-linked Codex Open Source Fund application dossier whose benchmark facts are generated from `benchmarks/benchmark-summary.json` and rejected by CI when stale, and which restates the project's honest maturity limits instead of overstating them.
- Extends the consistency test suite to enforce the lint gate, the bilingual release badges, and the new generated-facts target.

## 1.3.0 - 2026-07-23

- Adds a maintainer-local OpenAI Responses API evaluation CLI with preview-first `--send`, environment-only credentials, fixed endpoint, structured outputs, explicit token/cost budgets, and public telemetry schemas.
- Publishes five real-source negative planning cases covering unavailable official training code, restricted MIMIC-IV redistribution, missing Llama 2 training configuration, a 512-GPU budget block, and indirect prompt injection without mislabeling them as measured API results.
- Adds a repository-scoped malicious-research-material threat model and hardens Docker execution with `--cap-drop ALL`, `no-new-privileges`, a numeric non-root user, digest-only image validation, `--pull never`, and explicit built-in seccomp.
- Adds independent five-dimension review records, exact plan-hash binding, human modification records, disagreement detection, adjudication, and final evidence-bundle binding.
- Adds a standard-library installer for user or repository scope with install, update, integrity check, uninstall, version reporting, local-change protection, and post-install validation.
- Adds Linux/macOS quick-start commands, an honest maturity table, an end-to-end tamper demo, a reviewer call, and a repository Code of Conduct.
- Keeps maintainer API keys, Organization credentials, request headers, environment dumps, and generated evaluation results out of committed artifacts.

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
