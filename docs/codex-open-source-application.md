# Codex open source application guide — V1

Last verified against the official forms on 2026-07-23.

- [Codex open source fund](https://openai.com/form/codex-open-source-fund/)
- [Codex for Open Source](https://openai.com/form/codex-for-oss/)

The fund is the stronger immediate application for a new project. Codex for Open Source emphasizes active open-source maintainers plus meaningful usage/adoption or ecosystem importance. The public 15-paper benchmark is strong technical evidence, but it is not external adoption. Do not describe stars, users, contributors, downloads, or time savings until they are publicly verifiable.

## Recommended form answers

### Project

`Reproduce Research Paper`

### Repository

`https://github.com/FullFighting/reproduce-research-paper`

### Your role

`Primary maintainer. I designed the evidence model, isolated runner, machine observation extractors, comparison policies, public benchmark, tests, documentation, and release process. I review changes that affect execution safety, provenance, credentials, scientific status, and privacy.`

### Brief project description

`Reproduce Research Paper is a Codex Skill for evidence-first reproduction of computational research. It reads the whole paper, binds each claim to an isolated command and machine extractor, records code/data/environment hashes, and recomputes reports from raw evidence. V1 publishes 15 real-paper CPU cases with 15/15 valid bundles, zero GPUs, zero API tokens, and explicit limits against interpreting metric agreement as proof of a paper.`

### Why it qualifies

`The project provides reusable open infrastructure for a difficult scientific workflow: turning paper claims into reviewable, isolated, machine-traceable evidence. V1 removes hand-written metric trust, prevents manual figures from becoming positive verdicts, detects source mutation and secret leakage, and publishes 15 paper-linked evidence bundles across ML, scientific computing, operations research, finance, and econometrics.`

### How API credits would be used

`Credits would support an open 90-day maintenance program: triage public reproduction failures, review contributed paper plans, build regression fixtures, and develop separately labeled modules for expert peer review, academic-integrity screening, and dataset-quality checks. We would publish prompts, tests, token/cost records, maintainer decisions, and release notes. Credits would not fund private-data ingestion, paywall bypass, fabricated results, or unattended expensive runs.`

### Anything else

`V1 is deliberately conservative. A successful process exit is never scientific evidence; observations must come from run-bound logs/files; unsigned SHA-256 provenance is described as integrity rather than authorship proof; manual tables/images require review; network isolation is claimed only in container mode. The public benchmark records 70.363 seconds total wall time, 0 GPUs, 0 API tokens, and $0 external API cost. External adoption is not claimed.`

## Evidence to link

- [V1 benchmark report](../benchmarks/benchmark-report.md)
- [15 immutable-style evidence bundle reports](../benchmarks/results)
- [Security policy](../SECURITY.md)
- [V1 changelog](../CHANGELOG.md)
- [Contribution policy](../CONTRIBUTING.md)
- [Adopter ledger](../ADOPTERS.md)

## Honest readiness assessment

| Criterion | V1 evidence | Assessment |
|---|---|---|
| Public open-source repository | MIT license, source, tests, CI, V1 release | met |
| Active maintenance | release process, issue template, governance, security policy | met for initial release |
| Technical usefulness | end-to-end bundle, 15 real-paper claim cases | strong initial evidence |
| Meaningful usage/adoption | no verified external users yet | gap |
| Ecosystem importance | plausible research tooling value, not independently established | emerging |

Submit the fund application now. For Codex for Open Source, the form can be submitted honestly, but the application will be materially stronger after independent issues, adopters, citations, forks, or contributed reproduction cases appear.

## 90-day public delivery plan

1. Days 1–30: publish triage outcomes for real user reproduction failures and add at least five contributor-reviewed plans.
2. Days 31–60: release a separately permissioned professional peer-review module and dataset-quality audit module, each with negative tests and no automatic scientific verdict.
3. Days 61–90: prototype academic-integrity screening with source/citation boundaries, publish false-positive analysis, and evaluate signed DSSE/Sigstore or in-toto provenance.

If a target is missed, document it. Never rewrite targets or invent usage after the fact.
