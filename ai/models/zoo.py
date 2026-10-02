"""Explainable model zoo (scikit-learn).  Deliberately small: linear/logistic regression, random forest, gradient boosting,
Gaussian-process regression.  No deep networks.  Each model exposes an `explain()` (coefficients or importances)."""
from __future__ import annotations

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, RandomForestClassifier
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

REGRESSORS = {
    "linear": lambda seed: make_pipeline(StandardScaler(), LinearRegression()),
    "random_forest": lambda seed: RandomForestRegressor(n_estimators=200, max_depth=6, random_state=seed),
    "gradient_boosting": lambda seed: GradientBoostingRegressor(n_estimators=150, max_depth=2, random_state=seed),
    "gaussian_process": lambda seed: make_pipeline(
        StandardScaler(), GaussianProcessRegressor(RBF(1.0) + WhiteKernel(0.1), normalize_y=True, random_state=seed)),
}
CLASSIFIERS = {
    "logistic": lambda seed: make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    "random_forest_clf": lambda seed: RandomForestClassifier(n_estimators=200, max_depth=6, random_state=seed),
}
MODEL_TYPES = sorted(list(REGRESSORS) + list(CLASSIFIERS))


def make(model_type: str, seed: int = 0):
    if model_type in REGRESSORS:
        return REGRESSORS[model_type](seed)
    if model_type in CLASSIFIERS:
        return CLASSIFIERS[model_type](seed)
    raise ValueError(f"unknown model type {model_type!r}; choose from {MODEL_TYPES}")


def explain(model, feature_names) -> dict:
    """Feature -> weight (standardised coefficient, or impurity importance).  Gaussian process: None (use predictive std)."""
    est = model[-1] if hasattr(model, "steps") else model
    if hasattr(est, "coef_"):
        c = est.coef_
        c = c[0] if getattr(c, "ndim", 1) > 1 else c
        return dict(zip(feature_names, [float(x) for x in c]))
    if hasattr(est, "feature_importances_"):
        return dict(zip(feature_names, [float(x) for x in est.feature_importances_]))
    return {n: None for n in feature_names}
