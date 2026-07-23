# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: A Unified Approach to Interpreting Model Predictions
- Reference: Lundberg and Lee, NeurIPS 2017
- Official paper URL: https://papers.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html
- Official code URL: https://github.com/shap/shap
- Reviewed plan SHA-256: `1ac172602b3835bf35ab6adc1df932fc67e1117b41935ce4399d4f00d752ba6e`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Do released linear SHAP values reconstruct the explained model prediction?
- Method: Fit a deterministic two-feature linear model and measure SHAP additivity residual.
- Data and splits: Five synthetic observations under this repository's MIT license.
- Training or inference: Closed-form linear regression and one explanation.
- Evaluation protocol: Extract absolute prediction-reconstruction error; require numerical zero.
- Reported limitations: Tests the central additivity invariant, not human-subject or large-model experiments.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `f49b0ad77a96066559efbcbfb714846734da0ae718f856318f6891de495d09dc`
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
| shap-additivity | Additive feature attribution framework | additivity_error | 0.0 | 0.0 | jsonpath@rrp-jsonpath-1 | `36593a5507bf11d0668a4de7ec387afdb1432ce0af938cd9c7a3b9dce46e3353` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 2.06 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "shap-additivity"]`
- Standard output: `logs/paper-claim.stdout.log` (`36593a5507bf11d0668a4de7ec387afdb1432ce0af938cd9c7a3b9dce46e3353`)
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
