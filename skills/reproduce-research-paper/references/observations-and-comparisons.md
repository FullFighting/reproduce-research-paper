# Observations, expected values, units, and comparisons

## Contents

- [Typed expected values](#typed-expected-values)
- [Unit descriptors](#unit-descriptors)
- [Observation sources](#observation-sources)
- [Comparison methods](#comparison-methods)
- [Tables and rankings](#tables-and-rankings)
- [Distributions](#distributions)

## Typed expected values

Schema v2 uses:

```json
{"type": "scalar", "value": 0.91}
```

Supported types:

| Type | Value contract | Typical comparison |
|---|---|---|
| `scalar` | finite number | tolerance, equivalence, non-inferiority |
| `array` | non-empty JSON array | tolerance, exact match, set/order/correlation |
| `table` | `columns`, optional `row_labels`, rectangular `rows` | exact or numeric cell comparison |
| `ranking` | unique string/number items | exact order, set equality, Spearman |
| `categorical` | JSON scalar category | exact match |
| `string` | string | exact match |
| `artifact_hash` | 64-character SHA-256 | artifact hash |
| `distribution` | at least two finite samples | empirical distribution distance |

Examples:

```json
{"type": "ranking", "value": ["model-a", "model-b", "model-c"]}
```

```json
{
  "type": "table",
  "value": {
    "columns": ["model", "F1"],
    "row_labels": ["test"],
    "rows": [["model-a", 0.91]]
  }
}
```

```json
{"type": "artifact_hash", "value": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
```

## Unit descriptors

Schema v2 units have exactly:

```json
{
  "symbol": "BLEU",
  "scale": 1,
  "semantic_type": "quality_metric"
}
```

- `symbol` is the displayed metric or physical unit.
- `scale` converts a value to the semantic type's canonical scale.
- `semantic_type` prevents invalid conversions.

This supports BLEU, ROUGE, F1, perplexity, bits/dimension, joules, watts, FLOPs, samples/s, dollars, basis points, degrees, millimeters, log-likelihood, and domain-specific metrics without adding them to source code.

Examples:

```json
{"symbol": "mJ", "scale": 0.001, "semantic_type": "energy"}
```

```json
{"symbol": "basis_point", "scale": 0.0001, "semantic_type": "return"}
```

Source and claim units must have the same `semantic_type`. Scaling non-numeric structures is rejected; exact structures should use equal scale.

## Observation sources

- stdout/stderr: `jsonpath` or `regex`;
- files: `jsonpath`, `regex`, `csv`, `npy`, `parquet`, or `sha256`;
- manual: always `MANUAL_REVIEW_REQUIRED`.

The `sha256` file extractor returns the hash of the preserved run-generated file, making `artifact_hash` comparisons source-bound.

Every machine observation records the run-record hash, command, source path/hash, extractor/version, expression, raw/normalized value, units, and time.

## Comparison methods

- `numeric_tolerance`
- `equivalence_interval`
- `non_inferiority`
- `spearman_correlation`
- `exact_order`
- `exact_match`
- `set_equality`
- `artifact_hash`
- `distribution_distance`

Tolerance policies must state `combination: all|any`; prefer `all`. Predeclare aggregation, direction, minimum runs, rounding, and statistical margin.

`distribution_distance` uses the two-sample empirical Kolmogorov–Smirnov distance and requires `maximum_distance` between 0 and 1. It reports both sample counts and the measured distance.

## Tables and rankings

Table labels are evidence semantics, not decoration. Numeric table comparison requires matching columns, row labels, shapes, and cell policies. Mixed text/numeric tables use `exact_match`.

`exact_order` on a typed ranking compares the declared item sequence. `set_equality` ignores ordering. Spearman requires the same unique items and measures their positional association.

## Distributions

Store declared expected samples under `distribution.value`. Do not use distribution comparison to hide seed-level failures: retain raw runs, justify the distance threshold, and report systematic shifts separately.
