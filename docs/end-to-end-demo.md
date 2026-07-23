# End-to-end evidence and tamper demo

This is a reproducible 3–5 minute local walkthrough captured on 2026-07-23
against the bundled synthetic fixture. It uses no network, private data, GPU, or
API credits.

The fixture begins at the reviewed-plan boundary, so it does not fabricate a
Codex conversation or API telemetry. To record the semantic planning stage, use
the separate maintainer-local CLI in `evaluations/`; only publish a real measured
run.

## 1. User request and claim inventory

A normal user starts with:

```text
Use $reproduce-research-paper to read this paper as a whole, identify executable
claims, inventory the official repository, and create a preview-only plan. Do not
download data or execute experiments until I approve the plan and budget.
```

For this offline demonstration, the already-reviewed plan declares one bounded
claim:

- claim: `table-1-accuracy`;
- paper location: `Table 1, test split`;
- command: `python run_experiment.py`;
- observation: JSONPath `$.test_accuracy` from that command's stdout;
- expected value: `0.9`;
- absolute tolerance: `0.02`;
- budget: 60 CPU seconds, 512 MB memory, 32 MB disk, zero GPUs, no write paths;
- limitation: this fixture validates evidence handling only and is not a
  scientific result.

## 2. Validate the reviewed plan

```bash
python skills/reproduce-research-paper/scripts/validate_reproduction_plan.py \
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json
```

Observed output:

```json
{
  "valid": true,
  "errors": []
}
```

## 3. Preview before approval

```bash
python skills/reproduce-research-paper/scripts/run_reproduction.py \
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json \
  --output reproduction-output
```

Observed preview:

```json
{
  "mode": "preview",
  "plan_sha256": "f7c972e269efda78efcc4b4dd3129db973f89b89baa4ab7faee1e0a012a3734c",
  "workspace_mode": "copy",
  "network": "unrestricted",
  "commands": [
    {
      "id": "smoke-experiment",
      "argv": ["python", "run_experiment.py"],
      "cwd": ".",
      "timeout_seconds": 60,
      "capabilities": {
        "max_cpu_seconds": 60,
        "network": "unrestricted",
        "max_gpus": 0,
        "max_disk_mb": 32,
        "max_single_file_mb": 8,
        "max_output_files": 20,
        "max_memory_mb": 512,
        "write_paths": []
      }
    }
  ]
}
```

This command does not execute the experiment. The user can still reject or
narrow the command, network decision, isolation mode, or budget.

## 4. Approve the exact plan and execute in isolation

After reviewing the preview, add `--execute`:

```bash
python skills/reproduce-research-paper/scripts/run_reproduction.py \
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json \
  --output reproduction-output \
  --execute
```

Observed output, with the machine-specific absolute path normalized:

```json
{
  "evidence_bundle": "<repo>/reproduction-output",
  "successful": true,
  "verifier": "python <repo>/skills/reproduce-research-paper/scripts/build_report.py --bundle <repo>/reproduction-output"
}
```

The bound stdout artifact contained:

```json
{"seed": 7, "test_accuracy": 0.905}
```

## 5. Verify the evidence bundle and render the report

```bash
python skills/reproduce-research-paper/scripts/build_report.py \
  --bundle reproduction-output
```

Observed output:

```json
{
  "valid": true,
  "errors": []
}
```

The generated report records:

```text
Status: CLAIM_REPRODUCED_WITHIN_TOLERANCE
Expected: {"type":"scalar","value":0.9}
Observed: 0.905
Extractor: jsonpath@rrp-jsonpath-1
API tokens used: 0
Estimated monetary cost: 0 USD
```

The bundle includes the reviewed plan, pre/post inventories, environment,
run-record, raw logs, extracted observation, fresh comparison, report, and
provenance manifest.

## 6. Tamper with a bound log and verify failure

For the negative test only, change the recorded stdout from `0.905` to `0.999`
without rebuilding provenance, then rerun the same verifier:

```bash
python skills/reproduce-research-paper/scripts/build_report.py \
  --bundle reproduction-output
```

Observed output and process exit status:

```json
{
  "valid": false,
  "errors": [
    "artifact hash mismatch: logs/smoke-experiment.stdout.log",
    "artifact size mismatch: logs/smoke-experiment.stdout.log"
  ]
}
```

```text
exit code: 1
```

This negative result is the intended behavior. Process success, a rewritten
metric, or a hand-edited report cannot preserve a positive evidence verdict.
