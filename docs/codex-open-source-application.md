# Codex Open Source application draft

Last reviewed: 2026-07-23.

Use the [Codex open source fund form](https://openai.com/form/codex-open-source-fund/) for this early project. The more established [Codex for Open Source form](https://openai.com/form/codex-for-oss/) asks for meaningful usage, adoption, or clear ecosystem importance plus evidence of active maintenance; apply there once real usage and maintenance signals exist.

Do not invent stars, downloads, adopters, benchmarks, or observed time savings. Replace placeholders only with facts that are publicly verifiable at submission time.

## Codex open source fund

### Which open source project are you representing?

Reproduce Research Paper

### Brief description of the project

Reproduce Research Paper is an open-source Codex Skill for auditing computational research papers with code and experiments. It requires a paper-wide context, maps each reported claim to approved commands and evidence outputs, keeps execution opt-in, compares observed metrics against predeclared tolerances, and produces SHA-256-bound reproducibility reports. It does not fabricate missing artifacts or treat a successful process exit as scientific verification.

### GitHub repository

https://github.com/FullFighting/reproduce-research-paper

### How would you use API credits for your project?

We would use API credits for a 90-day public maintenance program: triage anonymized reproduction failures, turn them into regression cases, review contribution proposals, improve paper-to-plan coverage checks, and publish release notes with measured token use and maintainer decisions. Credits would support open-source maintenance and evaluation artifacts, not private research data, paywalled content, or autonomous scientific claims.

### Is there anything else you'd like us to know?

The project is safety-oriented by design: commands are previewed before execution; external downloads and expensive experiments require user approval; plans prohibit embedded credentials and shell strings; output must remain outside the research repository; common credential patterns are redacted from logs; and report status requires matching plan hashes, command coverage, and metric evidence. Current external adoption is not claimed.

## Codex for Open Source (apply after active-maintenance evidence exists)

### Describe your role

Primary maintainer. I design and maintain the Skill workflow, review command-execution and evidence-classification changes, triage reproduction failures, maintain regression cases, own releases, and protect privacy boundaries.

### Why does this repository qualify? (keep within 500 characters)

Reproduce Research Paper provides reusable, evidence-first infrastructure for computational research reproduction. It turns a paper's complete experimental context into a reviewable plan, binds claims to commands and outputs, and emits auditable verdicts instead of treating code execution as proof. The public repository includes zero-dependency tooling, cross-platform CI, and regression tests. Add verified usage or adoption facts here only when available.

### How will you use API credits? (keep within 500 characters)

Use credits for Codex-assisted issue triage, anonymized regression-case generation, contribution review, release maintenance, and evaluation of paper-to-plan coverage. Publish resulting tests, docs, release notes, token-use records, and maintainer decisions. Do not use credits for private datasets, restricted sources, automated paper claims, or unattended expensive experiments.

### Anything else we should know? (keep within 500 characters)

The project is intentionally conservative: no credential collection, access-control bypass, hidden network activity, automatic dependency installation, or unreviewed execution. Reports distinguish verified, partial, contradicted, blocked, and not-run outcomes. The adopter ledger stays empty until external usage is verifiable, and status rules are protected by regression tests.

## Public 90-day delivery plan after support

- Days 1-30: publish an anonymized reproduction-failure template and at least 10 public regression cases covering plan coverage, path safety, credential redaction, and evidence mismatches.
- Days 31-60: add contributor-reviewed examples for two additional public, lightweight computational-paper formats and publish maintainer triage outcomes.
- Days 61-90: publish a versioned benchmark report, an evidence-classification migration guide, and an API-maintenance transparency note with measured—not estimated—token use.

Each delivery must be evidenced by public commits, issues, pull requests, releases, or benchmark artifacts. If a target is not met, document the reason rather than retrospectively changing the claim.
