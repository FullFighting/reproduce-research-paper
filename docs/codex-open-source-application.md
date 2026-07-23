# Codex for Open Source application guide

Official status checked on 2026-07-23:

- The [Codex for Open Source form](https://openai.com/form/codex-for-oss/) is live, accepts submissions, and says applications are reviewed on a rolling basis.
- The [official program page](https://developers.openai.com/community/codex-for-oss) says “Apply today.”
- The separate [Codex Open Source Fund form](https://openai.com/form/codex-open-source-fund/) is also live and describes grants of up to $25,000 in API credits.
- OpenAI does **not** publish a remaining-dollar balance or available-slot counter. The [program terms](https://learn.chatgpt.com/docs/codex-for-oss-terms) say benefits depend on program capacity and may be modified, paused, or discontinued.

Therefore, the evidence supports “applications are still open,” not a claim that a specific amount remains. Apply promptly and do not write a made-up remaining quota in the form.

## Current eligibility and fields

The current form asks for the applicant's name, ChatGPT account email, public GitHub username, public repository URL, maintainer role, a qualification explanation (500 characters), selected program interests, OpenAI organization ID when requesting API credits, intended credit use (500 characters), and an optional final note (500 characters).

OpenAI describes the target applicant as a primary or core maintainer of an active open-source project. Selection considers meaningful usage, broad adoption or clear ecosystem importance, plus public evidence of active maintenance. An application is not a guarantee of benefits.

## Repository facts

<!-- benchmark-facts:start -->
- Published cases: 15 public, paper-linked, claim-level executable checks.
- Claim results: 15/15 reproduced within predeclared tolerance.
- Evidence integrity: 15/15 bundles pass re-hashing and report recomputation.
- Deterministic runtime: 0 API tokens and $0 estimated external API cost.
<!-- benchmark-facts:end -->

The benchmark runtime and the Codex planning pilot answer different questions:

- [Public benchmark](../benchmarks/benchmark-report.md): can deterministic tooling execute, extract, bind, compare, and verify claim-scoped evidence?
- [Codex planning pilot](codex-evaluation/README.md): can Codex turn whole-paper context into a reviewable plan and improve it after review?

The pilot currently has three transparent cases. The desktop client did not expose per-case token telemetry, and the pilot did not receive independent human paper-plan review. Both limitations are recorded rather than replaced with zeroes or invented feedback.

## Suggested form answers

Replace only the bracketed personal fields. Keep every answer truthful on submission day.

### Public GitHub username

`FullFighting`

### Public repository

`https://github.com/FullFighting/reproduce-research-paper`

### Role

`Primary maintainer. I design and maintain the Skill workflow, isolated deterministic runtime, evidence model, extractors, comparison policies, security boundaries, public evaluation cases, tests, documentation, and releases.`

### Why this project qualifies (under 500 characters)

`Reproduce Research Paper is an evidence-first Codex Skill for computational research. Codex reads whole papers and drafts reviewable claim-to-code plans; deterministic tooling isolates execution, extracts run-bound observations, verifies provenance, and recomputes claim-scoped reports. The public repository includes 15 paper-linked executable cases, three transparent Codex planning pilots, cross-platform CI, security tests, and an open contribution workflow.`

### Program interests

Select `API credits` and, if genuinely desired, `Codex Security`. Do not select a benefit only to make the application look broader.

### OpenAI organization ID

Enter the organization ID belonging to the account that should receive credits. Do not put a project ID, API key, ChatGPT workspace name, or placeholder.

### How credits would be used (under 500 characters)

`Credits would fund a 90-day public Codex planning evaluation: 20–30 paper/repository pairs scored on claim identification, command mapping, data/license handling, budget design, and comparison policy; at least 30 published failed or blocked cases; 50+ negative/security fixtures; and review of 5+ external plans. We will publish prompts, model/version metadata when exposed, tokens, cost, acceptance/rejection reasons, two releases, and a complete changelog.`

### Anything else (under 500 characters)

`The project separates semantic planning from deterministic verification. A successful process exit is never scientific evidence; observations must be run-bound; manual tables/images require review; unsigned SHA-256 is described as integrity, not authorship proof; and metric agreement never verifies an entire paper. Current external adoption is not claimed. The three-case Codex pilot records unavailable token telemetry and absent independent human review explicitly.`

## Honest readiness assessment

| Criterion | Public evidence | Assessment |
|---|---|---|
| Public open-source repository | MIT license, source, tests, CI, releases | met |
| Active maintenance | roadmap, issue forms, governance, security policy, changelog | met for an early project |
| Technical usefulness | deterministic evidence runtime and 15 claim-level cases | strong initial evidence |
| Codex-specific value | three transparent planning cases; deterministic execution boundary | credible pilot, not yet a benchmark |
| Meaningful external adoption | no verified external adopters yet | material gap |
| Maintainer identity | public GitHub handle; private identity fields supplied directly in the form | minimally public |

Submit now because the program is open, but describe adoption as a gap. Stars, users, contributors, downloads, citations, time savings, token totals, and independent reviews must never be invented.

## Focused 90-day delivery plan

| Work package | Public deliverable |
|---|---|
| Codex planning evaluation | 20–30 public paper/repository pairs |
| Human review benchmark | five scores: claim identification, command mapping, data/license, budget, comparison policy |
| Failure analysis | at least 30 public failed or blocked cases |
| Regression fixtures | at least 50 negative and security tests |
| Community contribution | review 5 or more externally submitted reproduction plans |
| Transparency | prompts, model/version metadata when exposed, tokens, cost, and acceptance/rejection reasons |
| Releases | at least two releases with complete changelog entries |

Professional peer review, academic-integrity screening, and dataset-quality auditing remain long-term roadmap items. They are not the primary API-credit promise for this application.

## Before submitting

- Verify the GitHub profile and repository are public.
- Verify the latest immutable tag, GitHub Release, CI run, and release notes.
- Add the applicant's real first/last name and ChatGPT email only in the official form.
- Add an OpenAI organization ID only if requesting API credits.
- Recheck the official form on submission day because fields and benefits can change.
