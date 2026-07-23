# Codex planning evaluation pilot

This pilot evaluates the semantic planning layer that the deterministic benchmark alone cannot test.

Codex was asked to read whole-paper context, identify one bounded executable claim, connect it to an official code or data source, and draft a preview-only plan. Each case publishes the prompt, first draft, review record, revised-plan binding, deterministic evidence-bundle link, and telemetry record.

## What this pilot does and does not prove

- It contains three real paper/repository pairs spanning scientific computing, machine learning, and finance/econometrics.
- Review in this release is Codex self-review plus deterministic schema/evidence feedback. It is **not** independent human maintainer review.
- The Codex desktop client did not expose per-case token counts or exact model ID to this task. Those values are recorded as `null` with status `UNAVAILABLE`, not as zero.
- The deterministic benchmark consumed zero API tokens. That separate fact must not be misread as zero-token Codex planning.
- The accepted plan is bound by SHA-256 to an existing public evidence bundle. SHA-256 checks bytes; it is not a signature or proof of authorship.

## Cases

| Case | Domain | Planning correction | Evidence |
|---|---|---|---|
| [NumPy broadcasting](paper-01-numpy/) | scientific computing | narrowed an ecosystem-scale idea to a deterministic API invariant | [bundle](../../benchmarks/results/numpy-broadcasting/report.md) |
| [Scikit-learn Iris SVM](paper-02-sklearn/) | machine learning | predeclared split, threshold, no tuning, and package-distributed data | [bundle](../../benchmarks/results/sklearn-iris-svm/report.md) |
| [Fama–French factors](paper-03-fama-french/) | finance/econometrics | separated arithmetic reconstruction from causal claims and documented live unsigned inputs | [bundle](../../benchmarks/results/fama-french-factors/report.md) |

See [evaluation-summary.md](evaluation-summary.md) for the pilot result and [evaluation-methodology.md](../evaluation-methodology.md) for the scoring design. Run `python scripts/validate_codex_evaluation.py` to verify all case-to-evidence bindings.
