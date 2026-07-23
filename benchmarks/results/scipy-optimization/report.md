# Reproduction evidence report

**Status:** `CLAIM_REPRODUCED_WITHIN_TOLERANCE`

> This result verifies only the declared computational claim under the recorded environment and protocol.

## Scope

- Paper: SciPy 1.0: fundamental algorithms for scientific computing in Python
- Reference: Virtanen et al., Nature Methods 17, 261–272 (2020), doi:10.1038/s41592-019-0686-2
- Official paper URL: https://www.nature.com/articles/s41592-019-0686-2
- Official code URL: https://github.com/scipy/scipy
- Reviewed plan SHA-256: `bd550a0877ff9485a1ffe2ac86aad5df1de9e42129b05063745ead5051b67998`
- Workspace mode: `copy`

## Paper-wide reproduction basis

- Research question: Can SciPy's released optimizer solve a standard smooth nonlinear objective to numerical precision on CPU?
- Method: Minimize the two-dimensional Rosenbrock function with BFGS from the conventional starting point.
- Data and splits: Deterministic analytic objective; no dataset.
- Training or inference: No training; one CPU optimization.
- Evaluation protocol: Run once and extract the terminal objective from JSON stdout.
- Reported limitations: Capability-level reproduction; it does not reproduce the paper's project-history figures.

## Repository and environment binding

- Git commit: `c1a61684d8a8c78fff870dc7583bea6e196b55d2`
- Dirty working tree before run: `False`
- Dirty diff SHA-256: `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`
- Source tree before: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Source tree after: `f1cbb6a5b007a645313ca04b09cad5592486ca0abe399ecb16ab682760b5294f`
- Inventory before: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Inventory after: `8db8cca817fe5a57d435380ae5feffd04c1cd2e84e2c667e5445f99a2236f381`
- Environment artifact SHA-256: `e35ccbfeb4b7ee4ecc8e7955af866fefe76c7d7c3bb0d4e817aa5b0f7c852035`
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
| scipy-optimization | Optimization module capability | terminal_objective | 0.0 | 2.0055896490142818e-11 | jsonpath@rrp-jsonpath-1 | `e14f753ba29a7f6e8f1eaa59101ac8b566b8c722bb203893b4bf4c6e6841d668` | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` |

## Execution record

### `paper-claim`

- Result: exit 0 in 0.652 seconds
- Reviewed argv: `["python", "experiment.py", "--case", "scipy-optimization"]`
- Standard output: `logs/paper-claim.stdout.log` (`e14f753ba29a7f6e8f1eaa59101ac8b566b8c722bb203893b4bf4c6e6841d668`)
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
