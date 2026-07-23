# Roadmap

## Near term: core Codex planning and deterministic verification

- [x] Add a maintainer-local, instrumented OpenAI API evaluation CLI with
  preview-first spending controls and environment-only credentials.
- [x] Publish five real-source refusal/block/revision cases covering missing
  public code, restricted data redistribution, missing training configuration,
  infeasible compute, and indirect prompt injection without mislabeling them as
  measured model results.
- [x] Publish a repository-scoped malicious-research-material threat model and
  harden container execution with capability dropping, no-new-privileges,
  non-root identity, digest-only images, no implicit pulls, and restricted
  seccomp.
- Evaluate 20–30 public paper/repository pairs with instrumented model, token, cost, review, acceptance, and rejection records.
- Publish at least 30 failed, blocked, or rejected planning cases.
- Add 50 or more negative, security, provenance, extractor, license, and resource-budget fixtures.
- Review at least five externally submitted reproduction plans.
- Publish two releases with complete changelogs.
- Extend the Linux container end-to-end fixture beyond the bundled deterministic case.

## Evaluation maturity

- [x] Publish the independent human-scoring protocol for claim identification,
  command mapping, data/license handling, budget design, and comparison policy.
- [x] Add machine-checkable plan binding, disagreement records, and explicit
  adjudication.
- [ ] Complete at least one independent researcher review of all three pilot
  cases.
- Case stratification by domain, artifact type, access model, compute level, and outcome.
- Measured prompts, model/version metadata when exposed, tokens, cost, latency, human edits, and rejection reasons.

## Longer term

- Mint and publish a Zenodo DOI only after an archived release exists; never use
  a placeholder DOI.
- Extend release build attestations to scientific-run DSSE/Sigstore and in-toto/SLSA-style provenance; add RO-Crate interoperability.
- Separately permissioned professional peer-review support.
- Academic-integrity screening with false-positive analysis and human adjudication.
- Dataset-quality and leakage audits.

Longer-term modules will never silently convert heuristic review signals into a scientific-truth verdict.
