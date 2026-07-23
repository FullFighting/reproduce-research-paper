# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: Scikit-learn: Machine Learning in Python
- Reference: Pedregosa et al., Journal of Machine Learning Research 12:2825–2830 (2011)
- Official paper URL: https://www.jmlr.org/papers/v12/pedregosa11a.html
- Official code URL: https://github.com/scikit-learn/scikit-learn
- Reviewed plan SHA-256: `22eaf68e7643a6db25009bbea2f97f5ab0487737aad6b09792ce704a1dad7900`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Can the released scikit-learn pipeline train and evaluate an SVM on a fixed public split without tuning?
- Method: Standardize Iris features, fit an RBF SVM, and score a stratified fixed test split.
- Data and splits: Iris dataset distributed by scikit-learn; fixed 70/30 split with random_state=42.
- Training or inference: 105 training observations on CPU; no hyperparameter search.
- Evaluation protocol: One predeclared split; require accuracy no worse than 0.90.
- Reported limitations: Low-cost API reproduction, not a paper table or a claim of state-of-the-art accuracy.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `454f9d226dfc6853801bd91ee4b6016a3e9e16d0c5d44a04c44a43c946edea57`
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
| sklearn-iris-svm | Supervised-learning and consistent-estimator API | test_accuracy | 0.9 | 0.9333333333333333 | jsonpath@rrp-jsonpath-1 | `4f4996b20919aeed01513c6e528ba928e31d3f45b391347f1f8d19f9773dbcc3` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 1.673 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "sklearn-iris-svm"]`
- Standard output: `logs/paper-claim.stdout.log` (`4f4996b20919aeed01513c6e528ba928e31d3f45b391347f1f8d19f9773dbcc3`)
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
