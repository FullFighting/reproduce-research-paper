# V1 plan and evidence-bundle contract

## Plan

The plan has `schema_version: 1`, a repository, paper metadata, six paper-wide context fields, environment declarations, execution capabilities, commands, and claims.

```json
{
  "schema_version": 1,
  "repository": "official-code",
  "paper": {
    "title": "Paper title",
    "reference": "Authors, venue, year, DOI",
    "paper_url": "https://official-venue.example/paper",
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
    "retain_workspace": false,
    "exclude_paths": {
      "download-cache": "restorable external cache, not research input"
    }
  },
  "commands": [
    {
      "id": "evaluate-model",
      "argv": ["python", "evaluate.py"],
      "cwd": ".",
      "timeout_seconds": 3600
    }
  ],
  "claims": [
    {
      "id": "table-2-accuracy",
      "paper_location": "Table 2, test accuracy",
      "metric": "test_accuracy",
      "expected": 0.91,
      "unit": "ratio",
      "protocol": "Evaluate the fixed official test split once.",
      "command_ids": ["evaluate-model"],
      "observation": {
        "source": "stdout",
        "command_id": "evaluate-model",
        "extractor": "jsonpath",
        "expression": "$.test_accuracy",
        "unit": "ratio"
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
  ]
}
```

## Observation

Every non-manual observation records:

- claim and metric;
- run-record SHA-256;
- source command;
- relative source artifact and SHA-256;
- extractor name and version;
- extraction expression;
- raw and normalized values;
- source and normalized units;
- extraction timestamp.

An observation without a source artifact and extractor cannot become `CLAIM_REPRODUCED_WITHIN_TOLERANCE`.

Manual observations contain no value and remain `MANUAL_REVIEW_REQUIRED`.

## Repository state

`inventory-before.json` and `inventory-after.json` include:

- Git commit, dirty state, scoped dirty-diff hash, and submodules;
- full content tree SHA-256 and inventory SHA-256;
- every included file path, size, category, and SHA-256;
- separate category hashes for code, data, weights, config, and environment;
- excluded path components and their reasons.

The run record binds the exact inventory and environment files by file hash and records source/workspace pre/post state.

## Evidence bundle

Required artifacts:

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

`provenance.json` records every file's SHA-256, size, role, and generation parents. It is an unsigned integrity manifest, not proof of authorship.

The verifier rejects:

- a missing, extra, or hash-mismatched artifact;
- a plan, inventory, environment, run record, or observation that is not bound to the next stage;
- an observation source whose current hash differs;
- a stored comparison that differs from a fresh computation;
- a stored report that differs from a fresh rendering.
