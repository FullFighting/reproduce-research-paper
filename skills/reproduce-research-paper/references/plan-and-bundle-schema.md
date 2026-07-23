# Plan and evidence-bundle schema

## Contents

- [Schema versions](#schema-versions)
- [Plan skeleton](#plan-skeleton)
- [Commands and secrets](#commands-and-secrets)
- [Claims](#claims)
- [Evidence bundle](#evidence-bundle)
- [Verification failures](#verification-failures)

## Schema versions

- Schema v2 is the authoring format for V1.2. It requires typed `expected` values and unit descriptors.
- Schema v1 remains readable so published evidence bundles can still be independently verified. Do not author new v1 plans.
- A plan hash covers the exact schema representation; migration creates a new plan and new evidence history.

## Plan skeleton

```json
{
  "schema_version": 2,
  "repository": "official-code",
  "paper": {
    "title": "Paper title",
    "reference": "Authors, venue, year, DOI",
    "paper_url": "https://official.example/paper",
    "code_url": "https://github.com/official/project"
  },
  "paper_context": {
    "research_question": "...",
    "method": "...",
    "data_and_splits": "...",
    "training_or_inference": "...",
    "evaluation_protocol": "...",
    "limitations": "..."
  },
  "environment": {
    "packages": ["numpy"],
    "lock_files": ["requirements.lock.txt"]
  },
  "execution": {
    "workspace_mode": "copy",
    "network": "unrestricted",
    "write_paths": ["outputs"],
    "max_memory_mb": 8192,
    "max_cpu_seconds": 3600,
    "max_disk_mb": 2048,
    "max_output_files": 1000,
    "max_single_file_mb": 512,
    "max_gpus": 0,
    "allow_argv_secrets": false,
    "retain_workspace": false,
    "exclude_paths": {}
  },
  "commands": [],
  "claims": []
}
```

All six `paper_context` fields are required. Network must be explicit. Container images must use an `@sha256:` digest.

## Commands and secrets

```json
{
  "id": "evaluate-model",
  "argv": ["python", "evaluate.py"],
  "secret_bindings": [
    {"name": "DATA_API_KEY", "secret_ref": "PAPER_DATA_API_KEY"}
  ],
  "cwd": ".",
  "timeout_seconds": 3600
}
```

`argv` is an array and never a shell string. Secret values are resolved from the runtime environment. Schema v2 defaults to environment bindings because argv values may be visible in operating-system process listings.

See [security-and-execution.md](security-and-execution.md) before enabling the high-risk argv compatibility mode.

## Claims

```json
{
  "id": "table-2-accuracy",
  "paper_location": "Table 2, test accuracy",
  "metric": "test_accuracy",
  "expected": {"type": "scalar", "value": 0.91},
  "unit": {
    "symbol": "accuracy",
    "scale": 1,
    "semantic_type": "quality_metric"
  },
  "protocol": "Evaluate the fixed official split once.",
  "command_ids": ["evaluate-model"],
  "observation": {
    "source": "stdout",
    "command_id": "evaluate-model",
    "extractor": "jsonpath",
    "expression": "$.test_accuracy",
    "unit": {
      "symbol": "accuracy",
      "scale": 1,
      "semantic_type": "quality_metric"
    }
  },
  "comparison": {
    "method": "numeric_tolerance",
    "absolute": 0.01,
    "relative": 0.02,
    "combination": "all",
    "minimum_runs": 1,
    "aggregate": "mean",
    "direction": "two_sided"
  }
}
```

Read [observations-and-comparisons.md](observations-and-comparisons.md) for every expected type, extractor, unit rule, and comparison method.

## Evidence bundle

```text
plan.json
inventory-before.json
inventory-after.json
environment.json
run-record.json
observations.json
comparison.json
report.md
provenance.json
logs/
evidence-sources/
outputs/
```

`inventory-before.json` and `inventory-after.json` capture Git and full-tree state. `run-record.json` binds the plan, initial inventory, environment, commands, capabilities, redacted logs, costs, and pre/post state. `observations.json` binds each value to its run record and source artifact. `provenance.json` records artifact hashes and generation parents.

The manifest is unsigned byte-integrity evidence, not proof of authorship.

## Verification failures

Reject:

- missing, extra, or hash-mismatched artifacts;
- unbound plan, inventory, environment, run record, observation, or source;
- stored comparisons that differ from fresh computation;
- stored reports that differ from fresh rendering;
- source mutation, undeclared writes, secret-policy violations, or unfulfilled required commands.
