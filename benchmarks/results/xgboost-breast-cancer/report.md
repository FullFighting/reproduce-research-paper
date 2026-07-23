# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: XGBoost: A Scalable Tree Boosting System
- Reference: Chen and Guestrin, KDD 2016, doi:10.1145/2939672.2939785
- Official paper URL: https://dl.acm.org/doi/10.1145/2939672.2939785
- Official code URL: https://github.com/dmlc/xgboost
- Reviewed plan SHA-256: `0802f88d5b8f1985c9eccd13cd1b0c03a4a4e1b223283d499044675e9084805c`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Can the released CPU histogram implementation learn a fixed small public classification task?
- Method: Fit 40 depth-three boosted trees on a fixed Breast Cancer Wisconsin split.
- Data and splits: Breast Cancer Wisconsin dataset distributed by scikit-learn; fixed stratified split.
- Training or inference: 426 training observations, one CPU thread, no tuning.
- Evaluation protocol: One predeclared split; require accuracy no worse than 0.90.
- Reported limitations: Smoke reproduction of the released learning system, not the billion-example scalability or original benchmark tables.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `5c89904e844687b1ccce888580594f56ab88fbb29c1b2659e4893818a1878f4e`
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
| xgboost-breast-cancer | End-to-end tree boosting system | test_accuracy | 0.9 | 0.9440559440559441 | jsonpath@rrp-jsonpath-1 | `265c99e2a717333c602860d2134aba55f81585f8814e86fa36eef78e651e47b7` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 1.748 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "xgboost-breast-cancer"]`
- Standard output: `logs/paper-claim.stdout.log` (`265c99e2a717333c602860d2134aba55f81585f8814e86fa36eef78e651e47b7`)
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
