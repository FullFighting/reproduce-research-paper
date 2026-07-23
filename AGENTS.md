# Repository guidance

## Scope

Maintain an evidence-first Codex Skill for computational paper reproduction. Protect the continuous chain from paper claim to run-bound observation and freshly computed report.

## Constraints

- Keep `skills/reproduce-research-paper/scripts/` compatible with Python 3.10+ and the standard library.
- Keep NumPy and Parquet support optional.
- Never restore a hand-written observed-metrics input.
- Never treat process success, a README assertion, or a manual figure as a reproduced claim.
- Preserve full repository/Git/environment binding and pre/post checks.
- Keep external writes and expensive execution behind reviewed plans and explicit `--execute`.
- Keep network isolation claims limited to controls actually enforced.
- Never commit secrets or raw data without redistribution permission.
- Preserve the disclaimer that a matched computational claim does not verify a paper's causal explanation or generalizability.

## Validation

```powershell
python -m compileall -q skills/reproduce-research-paper/scripts
python -m compileall -q scripts
python -m unittest discover -s tests -v
python skills/reproduce-research-paper/scripts/validate_reproduction_plan.py --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json
python scripts/sync_benchmark_facts.py --check
python scripts/validate_codex_evaluation.py
```

CI additionally runs the README offline demo, focused negative/security tests, a clean release-archive verification, and a digest-pinned Docker `--network none` end-to-end case.

When the Codex `skill-creator` package is available, also run its `quick_validate.py` against `skills/reproduce-research-paper/`.

## Pull requests

Explain the evidence boundary being changed, include a negative regression test and a legitimate control, and list any impact on repository state, capability enforcement, observation lineage, status semantics, secrets, cost, or privacy.
