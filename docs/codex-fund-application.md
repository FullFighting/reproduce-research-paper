# Codex Open Source Fund application dossier

This document collects, in one place and with source links, the facts a grant
reviewer needs to evaluate this project. Every quantitative statement is either
generated from `benchmarks/benchmark-summary.json` by
`scripts/sync_benchmark_facts.py` (and checked in CI) or linked to the artifact
that backs it. Nothing here claims more maturity than the
[README maturity table](../README.md#maturity) records.

## Project

- **Name:** Research Paper Reproduction for Codex
- **Repository:** <https://github.com/FullFighting/reproduce-research-paper>
- **License:** MIT
- **Runtime requirements:** Python 3.10+ and the standard library; NumPy and
  Parquet support are optional imports
- **Category:** Codex Skill plus a deterministic evidence runtime for
  computational reproducibility

## Problem

Computational results in published research are routinely hard to verify.
The common failure mode is not malice but shortcuts: a script that exits
successfully is treated as a reproduction, a hand-copied metric is treated as
evidence, and an unpinned environment silently drifts away from the one that
produced the paper's numbers. Reviewers, students, and practitioners have no
cheap way to distinguish "the command ran" from "the declared claim was
recomputed from run-bound artifacts under a recorded environment."

## What the project does

Codex performs the semantic work: it reads the whole paper, identifies
executable claims and their exact locations, maps them to official code and
data, drafts a preview-only reproduction plan, and diagnoses failures. A
deterministic, standard-library runtime performs everything that must not
depend on model judgment: isolated execution, machine extraction of
observations from run-generated artifacts, repository and environment binding,
typed comparison against predeclared tolerances, provenance verification, and
report rendering.

The boundary is strict in both directions:

- the model never assigns scientific truth, promotes a manual reading of a
  table or figure to a reproduced claim, or edits failed evidence into success;
- the runtime never executes anything that was not previewed and approved with
  explicit capability budgets (time, memory, disk, GPU count, network policy,
  write paths).

See [SKILL.md](../skills/reproduce-research-paper/SKILL.md), the
[evidence policy](../skills/reproduce-research-paper/references/evidence-policy.md),
and the [threat model for malicious research material](threat-model.md).

## Verified public evidence

<!-- benchmark-facts:start -->
- 15 public, paper-linked, claim-level executable cases.
- 15/15 claims reproduced within their declared tolerance.
- 15/15 evidence bundles pass full artifact re-hashing and report recomputation.
- 0 deterministic-runtime API tokens and $0 estimated external API cost.
<!-- benchmark-facts:end -->

The cases span scientific computing, machine learning, operations research,
finance, and econometrics, with papers from Nature, Nature Methods, JMLR, KDD,
NeurIPS, ICML, Journal of Financial Economics, and Mathematical Programming
Computation. Every bundle publishes its paper/code links, plan, environment
lock, data and license note, raw logs, observations, comparison, report,
provenance, and scope limitations, and is re-verified on every CI run
([benchmark report](../benchmarks/benchmark-report.md)).

These are bounded claim-level checks, not whole-paper reproductions, and they
do not measure Codex planning quality. The
[three-case Codex planning pilot](codex-evaluation/README.md) and the
[five real-source negative cases](../evaluations/cases.jsonl) are documented
with the same honesty: the pilot used self-review, and no paid API result has
been published yet.

## Why Codex specifically

The semantic half of this workflow is exactly what a code-capable model is for:
whole-paper reading, claim localization, mapping prose to official
repositories and commands, and failure diagnosis. The project already ships a
[maintainer-local, preview-first OpenAI API evaluation CLI](../evaluations/README.md)
with versioned prompts, schemas for cases, reviews, and telemetry, a fixed
official endpoint with `store: false`, and hard local cost caps — the
instrumentation exists; what is missing is credit budget to run it at a
meaningful scale and publish the measured results.

## What fund credits would be used for

The scope matches the [roadmap](../ROADMAP.md) and is deliberately narrow and
measurable:

1. **Instrumented planning evaluation:** 20–30 public paper/repository pairs,
   each with recorded prompts, model and version metadata, tokens, estimated
   cost, latency, human edits, review scores under the published
   [five-dimension rubric](evaluation-methodology.md), and accept / revise /
   reject / block outcomes.
2. **Published negative evidence:** at least 30 failed, blocked, or rejected
   planning cases, because refusal quality is a first-class result of this
   project, not an embarrassment to hide.
3. **Regression fixtures:** 50+ negative, security, provenance, extractor,
   license, and resource-budget fixtures derived from what the evaluation
   uncovers.
4. **Community plan review:** independent review of at least five externally
   submitted reproduction plans, with disagreements and adjudication preserved
   as separate records.
5. **Transparency:** per-run telemetry published under
   [`telemetry-schema.json`](../evaluations/telemetry-schema.json), reviewed
   and redacted before release; the OpenAI invoice remains authoritative for
   spend.

## Spending and credential safeguards

- The evaluation runner is a local CLI, not a service; there is no endpoint
  through which third parties can consume grant credits.
- `OPENAI_API_KEY` is read only from the maintainer's process environment and
  is never written to results, logs, or evidence bundles.
- Every paid request requires an explicit model, output-token cap, local cost
  cap, empty output directory, and `--send`; without `--send` the tool only
  validates inputs and prints a spend preview.
- Estimated costs use versioned [pricing inputs](../evaluations/pricing.json)
  committed to the repository.

## Sustainability

The project is MIT-licensed with public
[contribution](../CONTRIBUTING.md), [governance](../GOVERNANCE.md),
[security](../SECURITY.md), and [release](../.github/workflows/release.yml)
processes. Releases ship checksums, an SPDX SBOM, and GitHub build
attestation. CI enforces version consistency, generated-fact freshness,
pinned actions, lint cleanliness, negative security tests, and full
re-verification of all published evidence bundles on Linux and Windows across
Python 3.10–3.13.

## Honest limitations

- No paid API evaluation result has been published yet; the pilot used the
  Codex desktop workflow without per-case token telemetry.
- Independent human review of the pilot cases is not yet completed.
- No verified external adopter is recorded yet.
- Scientific-run signing (DSSE/Sigstore) is planned, not shipped.

These limitations are tracked in the [README maturity table](../README.md#maturity)
and the [roadmap](../ROADMAP.md), and this document must not drift ahead of
them.
