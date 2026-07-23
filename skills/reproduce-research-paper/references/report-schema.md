# Reproduction artifact schema

## Plan

`reproduction-plan.json` contains a local `repository`, target `claims`, and reviewable `commands`. Each command uses an `argv` list, a relative `cwd`, and `timeout_seconds` from 1 to 86,400. Claim tolerances may contain `absolute`, `relative`, or both.

## Observed metrics

Use either a key/value object:

```json
{"test_accuracy": 0.903}
```

or a list of records:

```json
[{"claim_id": "table-1-accuracy", "metric": "test_accuracy", "value": 0.903}]
```

## Run record

`run_reproduction.py --execute` writes command identifiers, argv, resolved working directory, timing, exit code, timeout state, and relative log filenames. It deliberately does not copy log bodies into reports.

## Report contract

The Markdown report must include scope, artifact inventory, command record, claim outcomes, deviations, blocker/failure categories, and limitations. Do not include private paths, tokens, unpublished data values, or full licensed source text.
