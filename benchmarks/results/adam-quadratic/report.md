# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: Adam: A Method for Stochastic Optimization
- Reference: Kingma and Ba, ICLR 2015
- Official paper URL: https://arxiv.org/abs/1412.6980
- Official code URL: https://github.com/keras-team/keras/blob/master/keras/src/optimizers/adam.py
- Reviewed plan SHA-256: `e809522bb5fb7049842852a6c5fea41dedce8c327e2594e39fe464ce75fa4af8`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Does a direct implementation of Algorithm 1 converge on a deterministic convex quadratic?
- Method: Apply the paper's bias-corrected first- and second-moment updates for 500 steps.
- Data and splits: Analytic one-dimensional quadratic; no dataset.
- Training or inference: 500 scalar CPU optimization steps.
- Evaluation protocol: Extract absolute distance to the known optimum.
- Reported limitations: Algorithmic invariant, not the paper's neural-network benchmark tables.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `3d8956c3d66e675ddf8a28d16a9023dfddb25f4b65f43e6d9be6e6947095a43c`
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
| adam-quadratic | Algorithm 1 | distance_to_optimum | 0.0 | 2.6802181174839472e-11 | jsonpath@rrp-jsonpath-1 | `7c4a88a5d804c1056214b1578d58093de2f38cb0e5f79c61e6d304903be38e15` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 0.264 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "adam-quadratic"]`
- Standard output: `logs/paper-claim.stdout.log` (`7c4a88a5d804c1056214b1578d58093de2f38cb0e5f79c61e6d304903be38e15`)
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
