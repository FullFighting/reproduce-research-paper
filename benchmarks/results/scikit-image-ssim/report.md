# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: scikit-image: image processing in Python
- Reference: van der Walt et al., PeerJ 2:e453 (2014), doi:10.7717/peerj.453
- Official paper URL: https://peerj.com/articles/453/
- Official code URL: https://github.com/scikit-image/scikit-image
- Reviewed plan SHA-256: `80e8b233e962cc10646b1414c7a486cd4a4d162a2e10cb3eb6a33dfa327741d4`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Does the released image-metrics implementation return identity similarity for identical images?
- Method: Compute structural similarity for two identical deterministic 8-by-8 arrays.
- Data and splits: Synthetic image under this repository's MIT license.
- Training or inference: No training; one CPU metric evaluation.
- Evaluation protocol: Run once and extract SSIM from JSON stdout.
- Reported limitations: Algorithmic identity check, not a reproduction of every gallery example.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `644111b47e5e196de7e8a98bd06db892013e36cbafe8b456c198248fb1d93b13`
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
| scikit-image-ssim | Image quality metrics capability | ssim | 1.0 | 1.0 | jsonpath@rrp-jsonpath-1 | `a1e7a01352f2e961ec5663bfc0323547157adb572f8f251976e6efb605c443b3` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 0.562 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "scikit-image-ssim"]`
- Standard output: `logs/paper-claim.stdout.log` (`a1e7a01352f2e961ec5663bfc0323547157adb572f8f251976e6efb605c443b3`)
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
