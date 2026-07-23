"""Low-cost claim-level reproductions for the public V1 benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
import zipfile


def numpy_broadcasting():
    import numpy as np

    matrix = np.arange(12, dtype=float).reshape(3, 4)
    vector = np.array([1.0, 2.0, 3.0, 4.0])
    return {"metric": float((matrix + vector).sum()), "shape": [3, 4]}


def scipy_optimization():
    import numpy as np
    from scipy.optimize import minimize

    def rosenbrock(point):
        return (1 - point[0]) ** 2 + 100 * (point[1] - point[0] ** 2) ** 2

    result = minimize(
        rosenbrock,
        np.array([-1.2, 1.0]),
        method="BFGS",
        options={"gtol": 1e-10, "maxiter": 1000},
    )
    return {
        "metric": float(result.fun),
        "solution": [float(item) for item in result.x],
        "converged": bool(result.success),
    }


def statsmodels_longley():
    import statsmodels.api as sm

    dataset = sm.datasets.longley.load()
    design = sm.add_constant(dataset.exog)
    fitted = sm.OLS(dataset.endog, design).fit()
    return {
        "metric": float(fitted.rsquared),
        "nobs": int(fitted.nobs),
        "parameters": [float(item) for item in fitted.params],
    }


def scikit_image_ssim():
    import numpy as np
    from skimage.metrics import structural_similarity

    image = np.arange(64, dtype=float).reshape(8, 8)
    score = structural_similarity(image, image.copy(), data_range=63.0)
    return {"metric": float(score), "shape": [8, 8]}


def sklearn_iris_svm():
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC

    features, target = load_iris(return_X_y=True)
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.3, random_state=42, stratify=target
    )
    model = make_pipeline(StandardScaler(), SVC(C=1.0, gamma="scale"))
    model.fit(x_train, y_train)
    return {"metric": float(model.score(x_test, y_test)), "test_samples": len(y_test)}


def xgboost_breast_cancer():
    from sklearn.datasets import load_breast_cancer
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier

    features, target = load_breast_cancer(return_X_y=True)
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.25, random_state=7, stratify=target
    )
    model = XGBClassifier(
        n_estimators=40,
        max_depth=3,
        learning_rate=0.1,
        subsample=1.0,
        colsample_bytree=1.0,
        random_state=7,
        n_jobs=1,
        tree_method="hist",
        eval_metric="logloss",
    )
    model.fit(x_train, y_train)
    return {"metric": float(model.score(x_test, y_test)), "test_samples": len(y_test)}


def lightgbm_breast_cancer():
    from lightgbm import LGBMClassifier
    from sklearn.datasets import load_breast_cancer
    from sklearn.model_selection import train_test_split

    features, target = load_breast_cancer(return_X_y=True)
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.25, random_state=7, stratify=target
    )
    model = LGBMClassifier(
        n_estimators=40,
        max_depth=3,
        learning_rate=0.1,
        random_state=7,
        n_jobs=1,
        verbosity=-1,
    )
    model.fit(x_train, y_train)
    return {"metric": float(model.score(x_test, y_test)), "test_samples": len(y_test)}


def shap_additivity():
    import numpy as np
    import shap
    from sklearn.linear_model import LinearRegression

    features = np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 0.0], [3.0, 1.0], [4.0, 3.0]])
    target = 2.0 * features[:, 0] - 0.5 * features[:, 1] + 3.0
    model = LinearRegression().fit(features, target)
    explanation = shap.LinearExplainer(model, features)(features[:1])
    reconstructed = float(explanation.base_values[0] + explanation.values[0].sum())
    predicted = float(model.predict(features[:1])[0])
    return {
        "metric": abs(reconstructed - predicted),
        "prediction": predicted,
        "reconstructed": reconstructed,
    }


def umap_digits():
    import umap
    from sklearn.datasets import load_digits
    from sklearn.manifold import trustworthiness
    from sklearn.preprocessing import StandardScaler

    features = StandardScaler().fit_transform(load_digits().data[:300])
    embedding = umap.UMAP(
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        random_state=42,
        n_jobs=1,
    ).fit_transform(features)
    score = trustworthiness(features, embedding, n_neighbors=10)
    return {"metric": float(score), "samples": len(features), "dimensions": 2}


def adam_quadratic():
    import numpy as np

    value = np.array([5.0], dtype=float)
    first = np.zeros_like(value)
    second = np.zeros_like(value)
    beta1, beta2, rate, epsilon = 0.9, 0.999, 0.1, 1e-8
    for step in range(1, 501):
        gradient = 2.0 * value
        first = beta1 * first + (1.0 - beta1) * gradient
        second = beta2 * second + (1.0 - beta2) * gradient**2
        first_hat = first / (1.0 - beta1**step)
        second_hat = second / (1.0 - beta2**step)
        value -= rate * first_hat / (np.sqrt(second_hat) + epsilon)
    return {"metric": float(abs(value[0])), "steps": 500}


def batch_normalization():
    import numpy as np

    batch = np.array([[1.0, 2.0], [3.0, 6.0], [5.0, 10.0], [7.0, 14.0]])
    normalized = (batch - batch.mean(axis=0)) / np.sqrt(batch.var(axis=0))
    mean_error = float(np.abs(normalized.mean(axis=0)).max())
    variance_error = float(np.abs(normalized.var(axis=0) - 1.0).max())
    return {"metric": max(mean_error, variance_error), "batch_shape": [4, 2]}


def scaled_dot_product_attention():
    import numpy as np

    queries = np.array([[1.0, 0.0], [0.0, 1.0]])
    keys = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    values = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    scores = queries @ keys.T / math.sqrt(keys.shape[1])
    shifted = scores - scores.max(axis=1, keepdims=True)
    weights = np.exp(shifted) / np.exp(shifted).sum(axis=1, keepdims=True)
    output = weights @ values
    return {
        "metric": float(np.abs(weights.sum(axis=1) - 1.0).max()),
        "output_checksum": float(output.sum()),
    }


def cvxpy_markowitz():
    import cvxpy as cp
    import numpy as np

    covariance = np.diag([1.0, 4.0])
    weights = cp.Variable(2)
    problem = cp.Problem(
        cp.Minimize(cp.quad_form(weights, covariance)),
        [cp.sum(weights) == 1.0, weights >= 0.0],
    )
    problem.solve(solver="CLARABEL")
    return {
        "metric": float(weights.value[0]),
        "weights": [float(item) for item in weights.value],
        "status": problem.status,
    }


def highs_linear_program():
    import numpy as np
    from scipy.optimize import linprog

    result = linprog(
        c=np.array([-1.0, -1.0]),
        A_ub=np.array([[1.0, 2.0], [4.0, 2.0]]),
        b_ub=np.array([4.0, 12.0]),
        bounds=[(0, None), (0, None)],
        method="highs",
    )
    return {
        "metric": float(-result.fun),
        "solution": [float(item) for item in result.x],
        "status": int(result.status),
    }


def _zip_csv(payload: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        name = next(item for item in archive.namelist() if item.lower().endswith(".csv"))
        text = archive.read(name).decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(text, newline="")))


def _month_rows(rows: list[list[str]]) -> dict[str, list[float]]:
    result = {}
    for row in rows:
        if row and len(row[0].strip()) == 6 and row[0].strip().isdigit():
            try:
                result.setdefault(
                    row[0].strip(),
                    [float(item.strip()) for item in row[1:] if item.strip()],
                )
            except ValueError:
                continue
    return result


def fama_french_factors():
    base = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    urls = {
        "portfolios": base + "6_Portfolios_2x3_CSV.zip",
        "factors": base + "F-F_Research_Data_Factors_CSV.zip",
    }
    payloads = {}
    hashes = {}
    for name, url in urls.items():
        request = urllib.request.Request(url, headers={"User-Agent": "reproduce-research-paper/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payloads[name] = response.read()
        hashes[name] = hashlib.sha256(payloads[name]).hexdigest()
    portfolios = _month_rows(_zip_csv(payloads["portfolios"]))
    factors = _month_rows(_zip_csv(payloads["factors"]))
    month = "202001"
    values = portfolios[month][:6]
    small_growth, small_neutral, small_value, big_growth, big_neutral, big_value = values
    computed_smb = (
        (small_value + small_neutral + small_growth) / 3.0
        - (big_value + big_neutral + big_growth) / 3.0
    )
    computed_hml = (small_value + big_value) / 2.0 - (small_growth + big_growth) / 2.0
    published_smb, published_hml = factors[month][1], factors[month][2]
    return {
        "metric": max(abs(computed_smb - published_smb), abs(computed_hml - published_hml)),
        "month": month,
        "computed": {"SMB": computed_smb, "HML": computed_hml},
        "published": {"SMB": published_smb, "HML": published_hml},
        "source_sha256": hashes,
        "source_urls": urls,
    }


CASES = {
    "numpy-broadcasting": numpy_broadcasting,
    "scipy-optimization": scipy_optimization,
    "statsmodels-longley": statsmodels_longley,
    "scikit-image-ssim": scikit_image_ssim,
    "sklearn-iris-svm": sklearn_iris_svm,
    "xgboost-breast-cancer": xgboost_breast_cancer,
    "lightgbm-breast-cancer": lightgbm_breast_cancer,
    "shap-additivity": shap_additivity,
    "umap-digits": umap_digits,
    "adam-quadratic": adam_quadratic,
    "batch-normalization": batch_normalization,
    "scaled-dot-product-attention": scaled_dot_product_attention,
    "cvxpy-markowitz": cvxpy_markowitz,
    "highs-linear-program": highs_linear_program,
    "fama-french-factors": fama_french_factors,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=sorted(CASES))
    args = parser.parse_args()
    result = CASES[args.case]()
    print(json.dumps({"case": args.case, **result}, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
