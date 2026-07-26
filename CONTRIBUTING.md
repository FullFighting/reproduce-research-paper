# Contributing

Contributions are welcome for new extractors, comparison policies, isolation controls, documentation, and public low-cost paper cases.

Never commit credentials, private datasets, paywalled text, proprietary model
weights, or third-party data without redistribution permission.

## Before you open a pull request

Run the full local check suite:

```bash
python -m compileall -q skills/reproduce-research-paper/scripts
python -m compileall -q evaluations scripts
ruff check .
python -m unittest discover -s tests -v
python scripts/sync_benchmark_facts.py --check
python scripts/validate_codex_evaluation.py
python evaluations/run_codex_evaluation.py --validate-cases
```

Linting uses the `ruff` version pinned in `.github/workflows/validate.yml` with
the rule set in `pyproject.toml`; install it with `python -m pip install ruff`.

For schema, release, or execution-boundary changes, also generate a clean `git archive` and run `scripts/verify_release_archive.py`. Container changes must pass `scripts/run_container_e2e.py`.

## Behavior changes

For behavior changes:

1. describe the affected source-to-report path;
2. add a regression test that fails without the change;
3. state whether plan validation, repository binding, observation extraction, status, write/network/resource policy, secrets, or privacy changes;
4. preserve old failed evidence rather than editing it into a passing result;
5. cite official paper, code, data, and license sources for benchmark cases;
6. keep runtime code compatible with Python 3.10+ and the standard library, with optional imports only for optional formats.

Use the five-dimension plan-review rubric in [docs/evaluation-methodology.md](docs/evaluation-methodology.md). A contributed case may be accepted, revised, rejected, or blocked; a rejection is useful evaluation evidence and must not be rewritten into a success.

## API evaluation contributions

For API evaluation contributions, keep the runner local and preview-first. Do not
add a web server, key proxy, automatic paid retry, committed API key,
Organization/Project credential, request header, or environment dump. Publish
only public or authorized inputs and reviewed, redacted results. Bind every
independent review to the exact plan SHA-256 and preserve disagreements and
adjudication as separate records.

## Development workflow

Develop on short-lived topic branches and land them on `main` with squash
merges. Squash commits are created and signed by GitHub, which keeps `main`'s
history linear and its commits verified regardless of where the branch work
was authored. Delete the topic branch after the merge.

## Releasing

Bump `VERSION`, `CITATION.cff`, both README release badges, `GENERATOR_VERSION`
in `evidence_common.py`, and `CHANGELOG.md` together; CI rejects any drift
between them. After the release commit is on `main` and Validate is green, run
the **Publish release** workflow (Actions → Publish release → Run workflow)
with the version number. It creates the annotated `v<version>` tag, publishes
the GitHub Release with notes extracted from the changelog section, and
dispatches the artifacts workflow that attaches checksums, an SPDX SBOM,
provenance, and a GitHub build attestation.
