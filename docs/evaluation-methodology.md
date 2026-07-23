# Codex planning evaluation methodology

## Architecture under evaluation

Codex performs semantic interpretation: whole-paper reading, claim selection, paper-location mapping, official repository/data mapping, preview-only plan drafting, and failure diagnosis. Deterministic tooling performs execution, extraction, provenance checks, comparison recomputation, and report rendering.

The evaluation never asks the language model to assign scientific truth.

## Unit of evaluation

One public paper/repository pair produces:

1. initial prompt and paper/code citations;
2. Codex draft plan;
3. review record;
4. revised plan or explicit rejection/block;
5. deterministic validator result;
6. evidence bundle when execution is approved;
7. model/version metadata when exposed, token/cost record, latency, human edits, and failure reason.

## Human scoring rubric

Each dimension is scored independently from 0 to 2:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Claim identification | wrong or non-executable | partly bounded | correct, located, executable |
| Command mapping | unrelated/unsafe | plausible but incomplete | official, executable, fully bound |
| Data and license | missing/unsafe | incomplete | source, access, redistribution, privacy clear |
| Budget and capabilities | missing | partial | compute, time, disk, network, writes, cost explicit |
| Comparison policy | post hoc or wrong | partly specified | metric, unit, direction, tolerance/statistics predeclared |

A plan cannot be accepted when it uses manual observations for a positive status, lacks a source-bound extractor, requests prohibited access, hides licensing uncertainty, or implies whole-paper verification.

## Outcome labels

- `ACCEPTED_FOR_DETERMINISTIC_EXECUTION`
- `REVISE`
- `REJECTED_SCIENTIFIC_SCOPE`
- `REJECTED_SAFETY_OR_PRIVACY`
- `BLOCKED_DATA_OR_LICENSE`
- `BLOCKED_COMPUTE_OR_ACCESS`

## Pilot limitation

The V1.1.0 three-case pilot uses Codex self-review and deterministic feedback. It has no independent human scoring and no per-case token telemetry because those values were not exposed by the desktop client. The pilot validates transparency and evidence binding, not population-level planning accuracy.
