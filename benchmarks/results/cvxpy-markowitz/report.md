# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: CVXPY: A Python-Embedded Modeling Language for Convex Optimization
- Reference: Diamond and Boyd, Journal of Machine Learning Research 17(83):1–5 (2016)
- Official paper URL: https://www.jmlr.org/papers/v17/15-408.html
- Official code URL: https://github.com/cvxpy/cvxpy
- Reviewed plan SHA-256: `9d1f50e8e99ba240bcf5fa053ac24e318ec0fe075ddc576481f5afd9ea595512`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Can CVXPY express and solve a two-asset minimum-variance portfolio with an analytic optimum?
- Method: Minimize quadratic portfolio variance subject to long-only fully-invested weights.
- Data and splits: Synthetic diagonal covariance matrix under this repository's MIT license.
- Training or inference: One tiny convex optimization with the open-source Clarabel solver.
- Evaluation protocol: Extract the first portfolio weight and compare with the analytic 0.8 optimum.
- Reported limitations: Small exact optimization, not a solver-performance benchmark.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `8b676e95c906d1f39dfbc66aacc54f5b60b04a99b1470f994a51d0373f78298c`
- Submodules: `{}`
- Recorded exclusions: `[]`

### Artifact categories

| Category | Files | Bytes | SHA-256 |
|---|---:|---:|---|
| code | 1 | 10727 | `36b49b66b81c526d379b13487ffed8ff7f0168e548be33d15101578e442b45b7` |
| data | 0 | 0 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| weights | 0 | 0 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| config | 0 | 0 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| environment | 1 | 685 | `0a0c8227bab23fa3570552b8f2984f1208084baf8898d79d03ab7d85ed2e1119` |

## Claim outcomes

| Claim | Location | Metric | Expected | Observed | Extractor | Source SHA-256 | Status |
|---|---|---|---:|---:|---|---|---|
| cvxpy-markowitz | Convex quadratic modeling capability | first_asset_weight | 0.8 | 0.7999999974932861 | jsonpath@rrp-jsonpath-1 | `28d6a7248e36c8e9f2da952465d5978f192c54dbdc22c121479ffcf97bac943b` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 1.269 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "cvxpy-markowitz"]`
- Standard output: `logs/paper-claim.stdout.log` (`28d6a7248e36c8e9f2da952465d5978f192c54dbdc22c121479ffcf97bac943b`)
- Standard error: `logs/paper-claim.stderr.log` (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`)
- Filesystem changes: `{"workspace":{"added":[],"removed":[],"modified":[],"tree_changed":false},"outputs":{"added":[],"removed":[],"modified":[],"tree_changed":false}}`
- Capability enforcement: `{"network":"explicitly unrestricted by reviewed plan","memory":"recorded only on Windows host","cpu":"wall timeout on Windows host","process_cleanup":"process group/tree termination"}`

## Cost, access, and deviations

- API tokens used: `0`
- Estimated monetary cost: `0` USD
- Network policy: `unrestricted`
- Policy violations: `[]`
- Deviations: `[]`

## Interpretation limits

- This result verifies only the declared computational claim under the recorded environment and protocol.
- A matching number does not prove the paper's causal explanation, scientific validity, or generalizability.
- SHA-256 binds bytes inside this bundle, but does not prove who produced them or prevent a party from rewriting both artifacts and unsigned provenance.
- Manual tables, figures, and images are never promoted to a reproduced claim; they remain `MANUAL_REVIEW_REQUIRED`.
