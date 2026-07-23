# Governance

The primary maintainer owns releases, issue triage, security response, and changes to evidence classification.

Changes that affect `VERIFIED`, `PARTIAL`, `CONTRADICTED`, `BLOCKED`, or `NOT_RUN` require a regression test and a documented rationale. A release must pass the repository validation workflow. Security-sensitive changes require an explicit review of command execution, path handling, log redaction, and private-data exposure.

Project claims about adoption, reproducibility performance, time saved, or API use must be backed by a public artifact or labeled as a plan.
