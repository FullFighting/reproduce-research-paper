# Maintainer-local Codex API evaluation

This directory contains a local command-line evaluation tool. It is not an HTTP
API, hosted service, API-key proxy, or free paper-reproduction endpoint. Only a
maintainer who controls an OpenAI Organization/Project and exports their own key
can spend that Organization/Project's credits.

## Safety boundary

- `OPENAI_API_KEY` is read only from the current process environment.
- The key, request headers, environment variables, and Organization credentials
  are never written to an evaluation result.
- Cases containing secret-like fields are rejected before any request.
- Requests use the fixed official `https://api.openai.com/v1/responses` endpoint,
  set `store: false`, and require an explicit model, output-token cap, local cost
  cap, output path, and `--send`.
- Without `--send`, the command only validates inputs and prints a spend preview.
- `.env` and generated results are ignored by Git.

Do not share a maintainer key, accept keys through a plan, deploy this CLI behind
a public endpoint, or let third parties consume grant credits.

## Quick start

Validate all public cases and preview one request without a key or network call:

```bash
python evaluations/run_codex_evaluation.py --validate-cases

python evaluations/run_codex_evaluation.py \
  --case mimic-iv-redistribution-prohibited \
  --model gpt-5.6-terra
```

For a maintainer-controlled paid run:

```bash
export OPENAI_API_KEY="your-maintainer-key"

python evaluations/run_codex_evaluation.py \
  --case mimic-iv-redistribution-prohibited \
  --model gpt-5.6-terra \
  --max-estimated-cost-usd 0.50 \
  --output evaluations/results/mimic-iv-run \
  --send
```

PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-maintainer-key"

python evaluations/run_codex_evaluation.py `
  --case mimic-iv-redistribution-prohibited `
  --model gpt-5.6-terra `
  --max-estimated-cost-usd 0.50 `
  --output evaluations/results/mimic-iv-run `
  --send
```

Delete the shell variable after the run. Never put the value in `.env`, JSON,
shell history shared with others, screenshots, Issues, CI logs, or evidence
bundles.

## Published artifacts

Each successful local API run writes:

- `input.json`: the public paper/repository case snapshot;
- `prompt.md`: the exact prompt version;
- `request.json`: the request body without headers or credentials;
- `api-response.json`: the model response and API usage object;
- `initial-plan.json`: the structured model-generated reproduction plan;
- `pricing.json`: the versioned rates used for the estimate;
- `telemetry.json`: model IDs, tokens, estimated cost, latency, initial-plan
  binding, pending human-review fields, and evidence-bundle status.

The OpenAI invoice is authoritative. The repository estimate covers text-token
usage represented in the response and does not claim to include future pricing
changes or unrelated tool fees.

`score_plan.py` validates independent reviews against the exact plan SHA-256,
records scores and modifications, exposes decision disagreements, and requires a
separate adjudication record when reviewers materially disagree. See
[protocol.md](protocol.md).

For an existing pilot plan:

```bash
python evaluations/score_plan.py \
  --plan docs/codex-evaluation/paper-01-numpy/codex-plan.json \
  --review /path/to/independent-review.json \
  --output /path/to/numpy-review-summary.json
```

Review files must follow
[`reviewer-score.schema.json`](reviewer-score.schema.json); cases and run
telemetry follow [`case-schema.json`](case-schema.json) and
[`telemetry-schema.json`](telemetry-schema.json).

Generated `results/` content is private by default. Publish only reviewed,
redacted artifacts from public cases after checking licenses, privacy, response
content, and cost metadata.

The five public cases are real-source reference decisions with retrieved dates
and official evidence URLs. They remain BLOCKED or REVISE by design. Never
rewrite a case into success to improve an evaluation result; resolving a blocker
requires a new, versioned case and plan.
