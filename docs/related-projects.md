# Related projects and design comparison

Last reviewed: 2026-07-26.

This page positions the project against adjacent open-source work, records which
community practices it has deliberately adopted, and explains which ones it has
deliberately not adopted. Ideas are credited to their sources; no code or text was
copied from any of them. Descriptions summarize each project's public documentation at
the review date and may age.

## How this project differs in one sentence

Adjacent projects mostly measure **how well an agent or a human can reproduce
research**; this project supplies the **deterministic evidence layer** — reviewed
plans, isolated execution, run-bound machine observations, typed comparisons, and
tamper-evident bundles — that makes any such attempt auditable in the first place.

## Positioning

| Project | What it is | Primary question | Relation to this project |
|---|---|---|---|
| [PaperBench](https://github.com/openai/preparedness/tree/main/project/paperbench) | Benchmark: agents replicate 20 ICML 2024 papers, graded by weighted rubric trees and an LLM judge with published human-agreement scores | How well can agents replicate papers from scratch? | Measures agents; grading rests on an LLM judge. This project measures nothing about agents yet and rejects judge verdicts as positive evidence, requiring machine-extracted observations instead. |
| [CORE-Bench](https://github.com/siegelz/core-bench) | Benchmark: 270 reproducibility tasks from 90 papers with easy/medium/hard information ablation | Can agents set up and run known-reproducible artifacts? | Complementary; its difficulty-tier design is a roadmap candidate here. This project's cases bind claims to typed tolerances rather than question answering. |
| [SUPER](https://github.com/allenai/super-benchmark) | Benchmark: setting up and executing tasks from real research repositories, with partial credit via landmarks | Can agents make under-documented research code run? | Focuses on environment wrangling; this project assumes a reviewed plan and focuses on evidence integrity once something runs. |
| [PaperCoder / Paper2Code](https://github.com/going-doer/Paper2Code) | Multi-agent pipeline generating a code repository from a paper | Can an LLM write the missing implementation? | Generates code; this project refuses to invent missing artifacts and records their absence as evidence. |
| [ML Code Completeness Checklist](https://github.com/paperswithcode/releasing-research-code) | NeurIPS code-release checklist: dependencies, training code, evaluation code, artifacts, README with commands | Is a release complete enough to attempt reproduction? | Direct inspiration for the advisory readiness-signal scan here, generalized beyond ML and kept strictly non-scoring. |
| [showyourwork](https://github.com/showyourwork/showyourwork) | Build system that regenerates an entire article, figure by figure, on CI | Is the article always in sync with its code and data? | Same provenance ethos applied to authoring one's own paper; this project verifies claims in other people's papers. |
| [ReScience C](https://github.com/ReScience/ReScience) | Journal publishing human-authored replications with open GitHub review; failed replications are first-class publications | Did an independent human replicate the study? | Human peer review of full studies; this project produces machine-checkable bundles for single computational claims and likewise keeps failures as first-class outcomes. |
| [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) / [Inspect](https://github.com/UKGovernmentBEIS/inspect_ai) | General LLM benchmark harnesses with versioned task registries and machine-readable results | How do we run and compare model evaluations at scale? | Harness engineering reference; their case-versioning and registry conventions informed this repository's benchmark tooling. |

## Practices adopted, with attribution

- **Per-case versioning with a comparability policy** (after lm-evaluation-harness's
  versioned task registry): every benchmark case now carries a `version` field, runs
  record `case_version`, and [benchmarks/README.md](../benchmarks/README.md) states
  when a bump is required and that results are comparable only within a version.
- **Registry tooling for selective runs** (a common harness convention in
  lm-evaluation-harness and Inspect): `run_benchmarks.py --list-cases` prints the
  registry and `--only <case-id>` re-runs one case without rewriting the published
  summary or report.
- **Composition rollups in the published report** (after CORE-Bench's task metadata
  tags): the benchmark report aggregates cases by category, labeled explicitly as
  composition counts, not quality grades.
- **A documented case-contribution path** (after the ML Code Completeness Checklist's
  README conventions): the benchmark now documents its layout, case schema, and
  contribution requirements in one place.
- **Advisory readiness signals before planning** (after the ML Code Completeness
  Checklist's five items): `assess_repository_readiness.py` scans a target repository
  for dependency declarations, locks, license, tests, CI, container definitions,
  data/configuration/citation artifacts, run instructions, and seed mentions. Unlike a
  checklist score, it emits evidence-linked boolean signals and an explicit
  interpretation limit, because a numeric grade would invite exactly the shortcut this
  project exists to prevent.
- **Public related-work positioning** (a norm across all surveyed projects): this page.

## Roadmap candidates informed by this survey

These are not commitments; they extend the existing [roadmap](../ROADMAP.md).

- **Difficulty tiers by information ablation** (CORE-Bench; SUPER's masked sub-problems):
  offering each case with progressively less scaffolding would turn the benchmark into
  a capability gradient without new paper curation.
- **Gold-label meta-evaluation of plan review** (PaperBench's judge-agreement
  methodology): once independent human reviews of the pilot cases exist, publish
  agreement statistics between reviewers and any automated scoring before trusting it.
- **Measured baselines with uncertainty** (PaperBench's leaderboard discipline): if
  agent planning scores are ever published, they must carry run counts, dispersion, and
  harness/case versions. No baseline table is published today because no measured runs
  exist — publishing one now would be fabrication.
- **Published example trajectories** (SUPER): full transcripts for one or two cases so
  readers can see what a compliant run looks like end to end.
- **Archived, citable benchmark releases** (lm-evaluation-harness, ReScience): already
  on the roadmap as a Zenodo DOI after the first archived release; never a placeholder.

## Practices deliberately not adopted

- **LLM-judge scores as positive evidence** (PaperBench-style grading): a judge with
  measured human agreement is a strong benchmark instrument, but this project's
  evidence policy requires observations extracted from run-generated artifacts;
  semantic scoring can rank plans, never confirm a claim.
- **A README leaderboard today**: with no measured agent results, a leaderboard would
  be theater. The maturity table states this openly instead.
- **Encrypted or withheld test sets** (CORE-Bench's contamination guard): sensible for
  agent benchmarks; this project's cases are meant to be publicly auditable end to end,
  so openness wins over contamination resistance at this stage.
- **Generating missing implementations** (Paper2Code): out of scope by policy; missing
  artifacts are recorded as evidence and reported as `BLOCKED` or `NOT_ATTEMPTED`
  rather than filled in.
- **Checklist scores as repository grades** (ML Code Completeness Checklist): the
  readiness scan reports counts of signals found, with per-signal evidence and explicit
  non-verdict language, instead of a single grade that could be mistaken for a
  reproducibility rating.
