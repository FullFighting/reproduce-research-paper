# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift
- Reference: Ioffe and Szegedy, ICML 2015
- Official paper URL: https://proceedings.mlr.press/v37/ioffe15.html
- Official code URL: https://github.com/tensorflow/tensorflow
- Reviewed plan SHA-256: `2e3596942ccc9a41064ce9319f6cf131e77628267456e0010235a9f1de1c5ec6`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Does the declared mini-batch transform produce zero means and unit variances?
- Method: Apply the paper's normalization transform to a deterministic 4-by-2 batch.
- Data and splits: Synthetic batch under this repository's MIT license.
- Training or inference: No network training; one direct algorithm evaluation.
- Evaluation protocol: Extract the maximum mean/variance invariant error.
- Reported limitations: Algorithmic invariant, not the ImageNet error or training-step speedup.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `b653110445403d03495b378210ac2a001dcd29fa5d12e12f4130aa8770c03640`
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
| batch-normalization | Algorithm 1 mini-batch normalization | normalization_invariant_error | 0.0 | 0.0 | jsonpath@rrp-jsonpath-1 | `ca6a7b5cb4f9a69833ab18635860081abb75eeb2c9ba8f93b353d41ff3ab635d` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 0.258 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "batch-normalization"]`
- Standard output: `logs/paper-claim.stdout.log` (`ca6a7b5cb4f9a69833ab18635860081abb75eeb2c9ba8f93b353d41ff3ab635d`)
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
