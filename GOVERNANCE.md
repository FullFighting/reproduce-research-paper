# Governance

The primary maintainer listed in [MAINTAINERS.md](MAINTAINERS.md) owns releases, issue triage, security response, and changes to evidence classification.

Changes that affect claim statuses, observation lineage, repository binding, capability enforcement, comparison policy, or bundle verification require a negative regression test, a legitimate control, and a documented rationale. A release must pass the repository validation workflow. Security-sensitive changes require an explicit review of command execution, path handling, process cleanup, log redaction, provenance, and private-data exposure.

Project claims about adoption, reproducibility performance, time saved, API use, model version, token cost, or human review must be backed by a public artifact or labeled as unavailable/planned. Benchmark facts in README and application materials are generated from `benchmarks/benchmark-summary.json`; CI rejects drift.
