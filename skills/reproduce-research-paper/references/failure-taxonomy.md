# Reproduction failure taxonomy

Assign one primary category, retain raw redacted evidence, and state whether the result is `BLOCKED`, `INCONCLUSIVE`, or `CLAIM_NOT_REPRODUCED`.

| Category | Signal | Status guidance | Safe next action |
|---|---|---|---|
| `missing_artifact` | code, data, weights, config, or lock absent | `BLOCKED` | request an authorized source |
| `access_or_license` | login, paywall, private bucket, NDA, or unclear redistribution | `BLOCKED` | do not bypass; document access path |
| `environment_drift` | incompatible package, OS, compiler, CUDA, or API | `BLOCKED` or `INCONCLUSIVE` | create a new pinned plan |
| `repository_drift` | source/tree changed between inventory and run | `INCONCLUSIVE` | restore a clean isolated source and rerun |
| `undeclared_write` | workspace/output change outside `write_paths` | `INCONCLUSIVE` | declare a narrow path or fix the command |
| `capability_violation` | network/resource/output policy not enforced or exceeded | `INCONCLUSIVE` | use container mode or revise authorized budget |
| `secret_exposure` | literal key, bearer header, credentialed URL, or leaked log | `BLOCKED` | rotate if necessary; replace with `secret_ref` and regression-test redaction |
| `execution_error` | nonzero exit, timeout, assertion, or exception | `BLOCKED` | preserve logs and diagnose without rewriting history |
| `observation_unbound` | no run/source hash, missing command, or manual metric | `BLOCKED` or `MANUAL_REVIEW_REQUIRED` | add a machine extractor |
| `extractor_error` | JSONPath/regex/CSV/NumPy/Parquet selection fails | `BLOCKED` | fix the declared expression and create a new plan |
| `protocol_ambiguity` | unclear split, seed, preprocessing, metric variant, or rounding | `INCONCLUSIVE` | predeclare alternatives as sensitivity runs |
| `statistical_insufficiency` | too few seeds, undefined interval/correlation, shape mismatch | `INCONCLUSIVE` | run the predeclared minimum or revise scope |
| `metric_mismatch` | valid observation outside policy | `CLAIM_NOT_REPRODUCED` | check protocol/extraction, then report the mismatch |
| `provenance_mismatch` | any tracked artifact hash/size/content changed | `INCONCLUSIVE` | recover original bundle or rerun; do not “repair” verdict fields |

Never delete a failed attempt from the scientific history. If a correction is needed, preserve the old bundle and generate a new one with a new plan hash.
