# Public claim-level benchmark

This directory contains the 15 public, paper-linked, low-cost, claim-level executable
cases behind [benchmark-report.md](benchmark-report.md). Each case binds one declared
computational claim from a peer-reviewed paper to a deterministic command, a typed
expected value, and a predeclared comparison policy, and produces a complete evidence
bundle under [results/](results/).

The benchmark measures whether the deterministic evidence runtime can execute, extract,
and verify bounded claims. It is not a leaderboard, it does not score any language
model, and it does not claim that the linked papers were reproduced end to end.

## Layout

| Path | Meaning |
|---|---|
| `cases.json` | Case registry: one entry per claim-level case. |
| `harness/` | Shared MIT-licensed adapter (`experiment.py`) plus its dependency lock. |
| `results/<case-id>/` | Published evidence bundle for each case. |
| `benchmark-summary.json` | Single machine-readable source for published counts and costs. |
| `benchmark-report.md` | Human-readable report rendered from the summary. |
| `.work/` | Scratch space for generated plans; not published. |

`benchmark-summary.json` is the only source of truth for published benchmark facts.
`scripts/sync_benchmark_facts.py --check` fails CI when the report or the fact blocks in
the READMEs and the fund application dossier drift from it.

## Running

A full run installs the locked harness dependencies and downloads one live public
finance archive, which is why it stays outside CI:

```bash
python -m pip install -r benchmarks/harness/requirements.lock.txt
python benchmarks/run_benchmarks.py --clean
```

Development helpers that never rewrite the published summary or report:

```bash
# Print the case registry as JSON lines without executing anything.
python benchmarks/run_benchmarks.py --list-cases

# Re-run a single case (repeatable flag) and print its records to stdout.
python benchmarks/run_benchmarks.py --only numpy-broadcasting --clean
```

A subset run still writes the selected bundles under `results/`, so use `--clean`
deliberately and restore published bundles from Git if you did not intend to
regenerate them. Only a full run rewrites `benchmark-summary.json` and
`benchmark-report.md`.

## Case registry schema

Every entry in `cases.json` declares:

| Field | Meaning |
|---|---|
| `id` | Stable case identifier; also the results directory name. |
| `version` | Integer case version; see the comparability policy below. |
| `category` | Domain grouping used by the report's coverage rollup. |
| `venue_tier` | Publication venue description for the linked paper. |
| `title`, `reference`, `paper_url`, `code_url` | Official paper and code identification. |
| `paper_location` | Where the claim appears in the paper. |
| `research_question`, `method`, `data`, `training`, `protocol`, `limitations` | Paper context copied into the generated plan. |
| `metric`, `expected`, `unit` | Typed claim value and unit descriptor key. |
| `comparison` | Predeclared comparison policy (method, tolerance, direction). |
| `packages`, `network`, `timeout_seconds` | Execution requirements and budget. |
| `data_license` | Data source and redistribution terms. |

### Case version policy

`version` starts at 1 and must be bumped whenever a change can alter a case's outcome
or its meaning: the expected value, tolerance or comparison policy, protocol, fixture
data, adapter behavior for that case, or declared budgets. Cosmetic edits (typo fixes in
prose fields) do not require a bump. Results are comparable only between runs of the
same case version; the runner records `case_version` in each run record so future
summaries carry the version they were produced under.

## Contributing a case

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), then:

1. Cite the official paper, code, data, and license sources; link only public artifacts
   that permit the declared use.
2. Keep the case CPU-only, low-cost, deterministic, and bounded by explicit budgets.
3. Declare the claim location, typed expected value, unit, and comparison policy before
   running anything.
4. Set `version` to 1 for a new case and register honest `limitations` describing what
   the case does not show.
5. Run the full suite so the summary, report, and generated fact blocks stay
   consistent, and keep `python -m unittest discover -s tests` green; the test suite
   validates the registry's shape, uniqueness, and link hygiene.

A case that cannot meet the evidence policy (for example, it would require manual
metric transcription) belongs in the evaluation negative-case sets, not in this
benchmark.

## Interpretation limits

These cases are deliberately bounded claim-level checks selected for public data, CPU
execution, and low cost. They do not rerun large-scale training, GPU experiments, or
human studies, and a matched claim never proves a paper's causal explanation or
generalization. See the interpretation section of
[benchmark-report.md](benchmark-report.md).
