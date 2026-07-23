# Reproduce Research Paper

An evidence-first Codex Skill for reproducing computational research papers with code and experiments.

It turns a reported result into a reviewable chain of paper claim, repository artifact, approved command, captured log, observed metric, and verdict. A process exit alone is never called a successful reproduction.

## What it does

- inventories code, data, weights, dependency files, entry points, licenses, and large artifacts without executing project code;
- requires a paper-wide context covering the question, method, data/splits, training/inference, evaluation protocol, and stated limitations before a plan can run;
- converts target tables, figures, and metrics into a secret-free, reviewable plan that maps every claim to commands and expected evidence;
- previews commands by default and executes them only with `--execute`;
- compares observed metrics against predeclared absolute and/or relative tolerances;
- binds plans, comparison results, and execution records with SHA-256 fingerprints, then produces an auditable report with `VERIFIED`, `PARTIAL`, `CONTRADICTED`, `BLOCKED`, or `NOT_RUN` status.

## Install as a Codex Skill

Copy `skills/reproduce-research-paper` into the repository or personal Skills directory used by Codex, then invoke it:

```text
Use $reproduce-research-paper to reproduce Table 2 from this paper and repository. Start with an artifact inventory and command preview; do not run downloads or expensive experiments without asking me.
```

## Offline demo

Python 3.10+ and the standard library are the only runtime requirements. The commands below do not access the network.

```powershell
python skills/reproduce-research-paper/scripts/validate_reproduction_plan.py `
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json

python skills/reproduce-research-paper/scripts/run_reproduction.py `
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json `
  --output reproduction-output

python skills/reproduce-research-paper/scripts/inventory_artifacts.py `
  --repository skills/reproduce-research-paper/assets/examples/toy-repository `
  --output reproduction-output/artifact-inventory.json

python skills/reproduce-research-paper/scripts/compare_metrics.py `
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json `
  --observed skills/reproduce-research-paper/assets/examples/observed-metrics.json `
  --output reproduction-output/metric-comparison.json
```

The execution command above is a preview. Add `--execute` only after reviewing the exact command list and authorizing the expected compute, data access, and network use.

## Quality contract

A `VERIFIED` claim requires: the same reviewed plan hash in the command record and metric comparison, successful execution of every command mapped to that claim, and a result within the plan's predeclared tolerance. Missing data, weights, licensing, seeds, environment details, or access is evidence of a blocker; it is not a gap to be guessed away.

The project does not bypass access controls, download restricted data, expose credentials, alter original research repositories, or make causal claims from a matching metric.

## Development

```powershell
python -m compileall -q skills/reproduce-research-paper/scripts
python -m unittest discover -s tests -v
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change and [SECURITY.md](SECURITY.md) before reporting a vulnerability.

The transparent adopter ledger is in [ADOPTERS.md](ADOPTERS.md), maintainer responsibilities are in [GOVERNANCE.md](GOVERNANCE.md), and the evidence-backed application draft is in [docs/codex-open-source-application.md](docs/codex-open-source-application.md).

## Why this exists

Agentic science is advancing quickly, but reliable research assistance depends on being able to check existing computational results rather than merely generate plausible experiments. This Skill focuses on that verification layer: transparent runs, predeclared comparisons, and failure evidence that can become regression cases.

MIT License. See [LICENSE](LICENSE).
