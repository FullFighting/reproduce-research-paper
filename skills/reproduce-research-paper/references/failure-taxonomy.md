# Reproduction failure taxonomy

Assign one primary category and retain the raw error and command ID.

| Category | Typical signal | Safe next action |
|---|---|---|
| `missing_artifact` | data, weights, config, or script absent | mark blocked; request an authorized source |
| `access_or_license` | login, terms, private bucket, paywall, or restricted data | mark blocked; do not bypass controls |
| `environment_drift` | incompatible package, OS, CUDA, compiler, or API version | document versions; try a declared compatible environment |
| `execution_error` | syntax, path, assertion, or runtime exception | preserve log; minimize a non-destructive fix proposal |
| `protocol_ambiguity` | unclear split, seed, preprocessing, or metric definition | predeclare alternatives as sensitivity runs |
| `metric_mismatch` | observable result outside tolerance | classify contradicted; check extraction and protocol before diagnosis |
| `resource_limit` | timeout, out-of-memory, quota, or unavailable accelerator | report the limit; request a revised budget or reduced authorized scope |
| `integrity_risk` | leakage, test contamination, suspicious overlap, or hidden manual step | stop interpretive claims; preserve evidence and explain the risk |

Do not remove a failure from the report after finding a workaround. Record the workaround as a deviation and rerun with a new command ID.
