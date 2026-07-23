# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: Statsmodels: Econometric and Statistical Modeling with Python
- Reference: Seabold and Perktold, Proceedings of the 9th Python in Science Conference (2010)
- Official paper URL: https://conference.scipy.org/proceedings/scipy2010/seabold.html
- Official code URL: https://github.com/statsmodels/statsmodels
- Reviewed plan SHA-256: `20e13fa7d187717ec1d32b376033f81e69becfcdfbe67430d3403939227e6d43`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Does the released Statsmodels OLS implementation reproduce the deterministic Longley regression fit?
- Method: Fit OLS with an intercept to the package-distributed Longley macroeconomic dataset.
- Data and splits: Longley dataset distributed with Statsmodels; 16 public macroeconomic observations.
- Training or inference: Closed-form OLS estimation on CPU.
- Evaluation protocol: Run once and extract R-squared from JSON stdout.
- Reported limitations: A certified small econometric fit, not every model family described by the software paper.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `35b2dd264428c7a0e03f52a422a0a1205574717aeec760fac55fa2fc68725e30`
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
| statsmodels-longley | Ordinary least squares implementation | r_squared | 0.995479004577296 | 0.9954790045772947 | jsonpath@rrp-jsonpath-1 | `36863270aeb5fec1f0d74253b0fe067573fd38dfd241637dd8435b6c950579bf` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 1.749 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "statsmodels-longley"]`
- Standard output: `logs/paper-claim.stdout.log` (`36863270aeb5fec1f0d74253b0fe067573fd38dfd241637dd8435b6c950579bf`)
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
