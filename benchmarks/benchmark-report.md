# Public paper-linked claim-level benchmark

Generated: 2026-07-23T07:37:13+00:00

This benchmark contains 15 public, paper-linked, low-cost, claim-level executable cases. It does not claim that the papers themselves were independently replicated. Each linked evidence bundle contains its plan, repository/environment inventory, raw logs, machine-extracted observation, recomputed comparison, report, and provenance manifest.

- Cases executed: **15**
- Reproduced within declared tolerance: **15**
- Cryptographically self-consistent bundles: **15**
- Total wall time: **86.262 seconds**
- API tokens: **0**
- Estimated external API cost: **$0**

## Results

| Case | Category | Venue level | Claim status | Observed | Seconds | Bundle valid |
|---|---|---|---|---:|---:|---|
| [numpy-broadcasting](results/numpy-broadcasting/report.md) | deterministic_scientific_computing | top multidisciplinary journal | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 96.0 | 1.897 | yes |
| [scipy-optimization](results/scipy-optimization/report.md) | deterministic_scientific_computing | top methods journal | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 2.0055896490142818e-11 | 2.207 | yes |
| [statsmodels-longley](results/statsmodels-longley/report.md) | econometrics | peer-reviewed scientific computing proceedings | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.9954790045772947 | 3.298 | yes |
| [scikit-image-ssim](results/scikit-image-ssim/report.md) | deterministic_scientific_computing | peer-reviewed general science journal | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 1.0 | 2.152 | yes |
| [sklearn-iris-svm](results/sklearn-iris-svm/report.md) | small_machine_learning | top machine-learning journal | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.9333333333333333 | 3.224 | yes |
| [xgboost-breast-cancer](results/xgboost-breast-cancer/report.md) | small_machine_learning | top data-mining conference | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.9440559440559441 | 3.263 | yes |
| [lightgbm-breast-cancer](results/lightgbm-breast-cancer/report.md) | small_machine_learning | top machine-learning conference | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.951048951048951 | 3.218 | yes |
| [shap-additivity](results/shap-additivity/report.md) | small_machine_learning | top machine-learning conference | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.0 | 3.711 | yes |
| [umap-digits](results/umap-digits/report.md) | small_machine_learning | peer-reviewed research-software journal | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.9614212067955478 | 19.139 | yes |
| [adam-quadratic](results/adam-quadratic/report.md) | small_machine_learning | top machine-learning conference | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 2.6802181174839472e-11 | 1.799 | yes |
| [batch-normalization](results/batch-normalization/report.md) | small_machine_learning | top machine-learning conference | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.0 | 1.801 | yes |
| [scaled-dot-product-attention](results/scaled-dot-product-attention/report.md) | small_machine_learning | top machine-learning conference | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.0 | 1.859 | yes |
| [cvxpy-markowitz](results/cvxpy-markowitz/report.md) | operations_research_and_finance | top machine-learning software journal | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.7999999974932861 | 2.819 | yes |
| [highs-linear-program](results/highs-linear-program/report.md) | operations_research_and_finance | top optimization-computing journal | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 3.3333333333333335 | 2.243 | yes |
| [fama-french-factors](results/fama-french-factors/report.md) | finance_and_econometrics | top finance journal | `CLAIM_REPRODUCED_WITHIN_TOLERANCE` | 0.00456666666666683 | 33.632 | yes |

## Interpretation

These are deliberately bounded claim-level reproductions selected for public data, CPU execution, and low cost. Software papers are tested through deterministic API or algorithm invariants; small machine-learning cases use fixed public splits without tuning; the finance case recomputes official Fama–French factors from the official portfolio archive. Original large-scale speedups, GPU training, human studies, and causal/generalization claims remain outside this benchmark.

SHA-256 detects unsynchronized changes inside each bundle but is not a signature and does not prove authorship. The report generator re-hashes every tracked artifact and recomputes comparisons from logs.

## Case notes

### numpy-broadcasting

- Paper: [Array programming with NumPy](https://www.nature.com/articles/s41586-020-2649-2)
- Code/reference implementation: [https://github.com/numpy/numpy](https://github.com/numpy/numpy)
- Data/license: Synthetic fixture under this repository's MIT license.
- Expected / observed: `96.0` / `96.0` unitless
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Claim-level API reproduction, not a rerun of the paper's ecosystem-scale adoption analysis.

### scipy-optimization

- Paper: [SciPy 1.0: fundamental algorithms for scientific computing in Python](https://www.nature.com/articles/s41592-019-0686-2)
- Code/reference implementation: [https://github.com/scipy/scipy](https://github.com/scipy/scipy)
- Data/license: Analytic fixture under this repository's MIT license.
- Expected / observed: `0.0` / `2.0055896490142818e-11` unitless
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Capability-level reproduction; it does not reproduce the paper's project-history figures.

### statsmodels-longley

- Paper: [Statsmodels: Econometric and Statistical Modeling with Python](https://conference.scipy.org/proceedings/scipy2010/seabold.html)
- Code/reference implementation: [https://github.com/statsmodels/statsmodels](https://github.com/statsmodels/statsmodels)
- Data/license: Public Longley data as redistributed by the BSD-licensed Statsmodels project.
- Expected / observed: `0.995479004577296` / `0.9954790045772947` ratio
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: A certified small econometric fit, not every model family described by the software paper.

### scikit-image-ssim

- Paper: [scikit-image: image processing in Python](https://peerj.com/articles/453/)
- Code/reference implementation: [https://github.com/scikit-image/scikit-image](https://github.com/scikit-image/scikit-image)
- Data/license: Synthetic fixture under this repository's MIT license.
- Expected / observed: `1.0` / `1.0` ratio
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Algorithmic identity check, not a reproduction of every gallery example.

### sklearn-iris-svm

- Paper: [Scikit-learn: Machine Learning in Python](https://www.jmlr.org/papers/v12/pedregosa11a.html)
- Code/reference implementation: [https://github.com/scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn)
- Data/license: Package-distributed public Iris dataset; no dataset files are republished.
- Expected / observed: `0.9` / `0.9333333333333333` ratio
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Low-cost API reproduction, not a paper table or a claim of state-of-the-art accuracy.

### xgboost-breast-cancer

- Paper: [XGBoost: A Scalable Tree Boosting System](https://dl.acm.org/doi/10.1145/2939672.2939785)
- Code/reference implementation: [https://github.com/dmlc/xgboost](https://github.com/dmlc/xgboost)
- Data/license: Package-distributed public Wisconsin dataset; no dataset files are republished.
- Expected / observed: `0.9` / `0.9440559440559441` ratio
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Smoke reproduction of the released learning system, not the billion-example scalability or original benchmark tables.

### lightgbm-breast-cancer

- Paper: [LightGBM: A Highly Efficient Gradient Boosting Decision Tree](https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html)
- Code/reference implementation: [https://github.com/microsoft/LightGBM](https://github.com/microsoft/LightGBM)
- Data/license: Package-distributed public Wisconsin dataset; no dataset files are republished.
- Expected / observed: `0.9` / `0.951048951048951` ratio
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Smoke reproduction, not the paper's 20-times speedup or large-data benchmark.

### shap-additivity

- Paper: [A Unified Approach to Interpreting Model Predictions](https://papers.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html)
- Code/reference implementation: [https://github.com/shap/shap](https://github.com/shap/shap)
- Data/license: Synthetic fixture under this repository's MIT license.
- Expected / observed: `0.0` / `0.0` unitless
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Tests the central additivity invariant, not human-subject or large-model experiments.

### umap-digits

- Paper: [UMAP: Uniform Manifold Approximation and Projection](https://joss.theoj.org/papers/10.21105/joss.00861)
- Code/reference implementation: [https://github.com/lmcinnes/umap](https://github.com/lmcinnes/umap)
- Data/license: Package-distributed public digits dataset; no dataset files are republished.
- Expected / observed: `0.9` / `0.9614212067955478` ratio
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Reduced public-data probe, not the full paper benchmark suite.

### adam-quadratic

- Paper: [Adam: A Method for Stochastic Optimization](https://arxiv.org/abs/1412.6980)
- Code/reference implementation: [https://github.com/keras-team/keras/blob/master/keras/src/optimizers/adam.py](https://github.com/keras-team/keras/blob/master/keras/src/optimizers/adam.py)
- Data/license: Analytic fixture under this repository's MIT license.
- Expected / observed: `0.0` / `2.6802181174839472e-11` unitless
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Algorithmic invariant, not the paper's neural-network benchmark tables.

### batch-normalization

- Paper: [Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift](https://proceedings.mlr.press/v37/ioffe15.html)
- Code/reference implementation: [https://github.com/tensorflow/tensorflow](https://github.com/tensorflow/tensorflow)
- Data/license: Synthetic fixture under this repository's MIT license.
- Expected / observed: `0.0` / `0.0` unitless
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Algorithmic invariant, not the ImageNet error or training-step speedup.

### scaled-dot-product-attention

- Paper: [Attention Is All You Need](https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html)
- Code/reference implementation: [https://github.com/tensorflow/tensor2tensor](https://github.com/tensorflow/tensor2tensor)
- Data/license: Synthetic fixture under this repository's MIT license.
- Expected / observed: `0.0` / `0.0` unitless
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Equation-level reproduction, not WMT translation quality or training cost.

### cvxpy-markowitz

- Paper: [CVXPY: A Python-Embedded Modeling Language for Convex Optimization](https://www.jmlr.org/papers/v17/15-408.html)
- Code/reference implementation: [https://github.com/cvxpy/cvxpy](https://github.com/cvxpy/cvxpy)
- Data/license: Synthetic fixture under this repository's MIT license.
- Expected / observed: `0.8` / `0.7999999974932861` ratio
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Small exact optimization, not a solver-performance benchmark.

### highs-linear-program

- Paper: [Parallelizing the Dual Revised Simplex Method](https://doi.org/10.1007/s12532-017-0130-5)
- Code/reference implementation: [https://github.com/ERGO-Code/HiGHS](https://github.com/ERGO-Code/HiGHS)
- Data/license: Synthetic fixture under this repository's MIT license.
- Expected / observed: `3.3333333333333335` / `3.3333333333333335` unitless
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: Correctness probe, not the paper's parallel speedup experiments.

### fama-french-factors

- Paper: [Common Risk Factors in the Returns on Stocks and Bonds](https://doi.org/10.1016/0304-405X(93)90023-5)
- Code/reference implementation: [https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)
- Data/license: Publicly downloadable academic data; no explicit redistribution license was found, so raw archives are not committed.
- Expected / observed: `0.0` / `0.00456666666666683` percentage_point
- Status: `CLAIM_REPRODUCED_WITHIN_TOLERANCE`; bundle verification: `PASS`
- Cost: 0 API tokens; $0 estimated external API cost
- Scope limit: The official archives are live and unsigned; response SHA-256 values are recorded, raw archives are not redistributed, and no causal asset-pricing claim is tested.
