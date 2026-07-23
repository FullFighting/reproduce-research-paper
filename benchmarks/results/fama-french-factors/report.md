# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: Common Risk Factors in the Returns on Stocks and Bonds
- Reference: Fama and French, Journal of Financial Economics 33:3–56 (1993), doi:10.1016/0304-405X(93)90023-5
- Official paper URL: https://doi.org/10.1016/0304-405X(93)90023-5
- Official code URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html
- Reviewed plan SHA-256: `6a5ffaaf22363bd4a17ac93fa5e2b9a291cbb62ede8aa81d8a2c6bb6e6304c5e`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Do the published six size/book-to-market portfolio returns reconstruct the official SMB and HML factors for a fixed historical month?
- Method: Download both official CSV archives, hash them, and recompute January 2020 SMB and HML from the documented equations.
- Data and splits: Kenneth French Data Library public monthly factor and 2x3 portfolio archives; January 2020 only is evaluated.
- Training or inference: No training; two small HTTPS downloads and arithmetic.
- Evaluation protocol: Compare reconstructed and published factors, allowing one basis point for source rounding.
- Reported limitations: The official archives are live and unsigned; response SHA-256 values are recorded, raw archives are not redistributed, and no causal asset-pricing claim is tested.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `70e44c29004caef5b6a8237f59cfc9e5823e34632a898bee100fbbac6a0423de`
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
| fama-french-factors | SMB and HML factor-construction equations | max_factor_reconstruction_error | 0.0 | 0.00456666666666683 | jsonpath@rrp-jsonpath-1 | `6538164ee2a7e97ec84b63b087901fc9aa54481295940443086655078c7721f4` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 32.108 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "fama-french-factors"]`
- Standard output: `logs/paper-claim.stdout.log` (`6538164ee2a7e97ec84b63b087901fc9aa54481295940443086655078c7721f4`)
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
