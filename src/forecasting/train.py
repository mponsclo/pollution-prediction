"""Production-ready forecasting pipeline.

Uses LightGBM with Fourier features, anchor lags, target encoding,
and an ensemble of LightGBM + Ridge + seasonal naive.
Includes quantile regression for prediction intervals.
"""

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import Ridge
from scipy.optimize import minimize

from src.forecasting.features import (
    build_train_features,
    build_prediction_features,
    get_feature_columns,
    add_fourier_features,
)


# ---------------------------------------------------------------------------
# Seasonal Naive baseline
# ---------------------------------------------------------------------------

def seasonal_naive_predict(
    train_series: pd.Series,
    prediction_index: pd.DatetimeIndex,
    period: int = 168,
) -> pd.Series:
    """Baseline: value from same hour, `period` hours ago."""
    preds = []
    for dt in prediction_index:
        lookback = dt - pd.Timedelta(hours=period)
        if lookback in train_series.index:
            preds.append(train_series.loc[lookback])
        else:
            same_hour = train_series[train_series.index.hour == dt.hour]
            preds.append(same_hour.mean() if len(same_hour) > 0 else train_series.mean())
    return pd.Series(preds, index=prediction_index, name="seasonal_naive")


# ---------------------------------------------------------------------------
# LightGBM training
# ---------------------------------------------------------------------------

def _lgbm_params(objective: str = "regression", alpha: float | None = None) -> dict:
    params = dict(
        n_estimators=800,
        num_leaves=63,
        max_depth=8,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_samples=20,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    if objective == "quantile" and alpha is not None:
        params["objective"] = "quantile"
        params["alpha"] = alpha
    return params


def train_lgbm(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame | None = None,
    y_val: pd.Series | None = None,
    objective: str = "regression",
    alpha: float | None = None,
) -> LGBMRegressor:
    """Train a single LightGBM model."""
    params = _lgbm_params(objective, alpha)
    model = LGBMRegressor(**params)

    fit_kwargs = {}
    if X_val is not None and y_val is not None:
        fit_kwargs["eval_set"] = [(X_val, y_val)]
        fit_kwargs["callbacks"] = [
            __import__("lightgbm").early_stopping(50, verbose=False),
            __import__("lightgbm").log_evaluation(0),
        ]

    model.fit(X_train, y_train, **fit_kwargs)
    return model


# ---------------------------------------------------------------------------
# Ridge with Fourier features (complementary model)
# ---------------------------------------------------------------------------

def train_ridge(
    train_series: pd.Series,
) -> tuple[Ridge, pd.Timestamp]:
    """Train a Ridge model using only Fourier + temporal features."""
    epoch = train_series.index.min()
    fourier = add_fourier_features(train_series.index, epoch)

    # Add basic temporal
    fourier["hour"] = train_series.index.hour
    fourier["day_of_week"] = train_series.index.dayofweek
    fourier["month"] = train_series.index.month

    model = Ridge(alpha=10.0)
    model.fit(fourier.values, train_series.values)
    return model, epoch


def predict_ridge(
    model: Ridge,
    prediction_index: pd.DatetimeIndex,
    epoch: pd.Timestamp,
) -> pd.Series:
    """Predict with the Ridge Fourier model."""
    fourier = add_fourier_features(prediction_index, epoch)
    fourier["hour"] = prediction_index.hour
    fourier["day_of_week"] = prediction_index.dayofweek
    fourier["month"] = prediction_index.month

    preds = model.predict(fourier.values)
    preds = np.maximum(preds, 0)
    return pd.Series(preds, index=prediction_index, name="ridge_fourier")


# ---------------------------------------------------------------------------
# Ensemble: optimized weighted average
# ---------------------------------------------------------------------------

def optimize_weights(
    y_true: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> dict[str, float]:
    """Find optimal convex combination weights via MSE minimization."""
    names = list(predictions.keys())
    pred_matrix = np.column_stack([predictions[n] for n in names])

    def objective(w):
        combined = pred_matrix @ w
        return np.mean((y_true - combined) ** 2)

    n = len(names)
    constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
    bounds = [(0.0, 1.0)] * n
    x0 = np.ones(n) / n

    result = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    return dict(zip(names, result.x))


# ---------------------------------------------------------------------------
# Walk-forward cross-validation
# ---------------------------------------------------------------------------

def walk_forward_cv(
    train_series: pd.Series,
    n_folds: int = 3,
    test_size: int = 720,
    min_train_size: int = 8760,
) -> list[dict]:
    """Generate walk-forward CV fold indices."""
    total = len(train_series)
    folds = []

    for i in range(n_folds):
        test_end = total - i * test_size
        test_start = test_end - test_size
        train_end = test_start

        if train_end < min_train_size:
            break

        folds.append({
            "train_end": train_end,
            "test_start": test_start,
            "test_end": test_end,
        })

    return list(reversed(folds))


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def train_forecast_pipeline(
    train_series: pd.Series,
    val_series: pd.Series | None = None,
) -> dict:
    """Train the full forecast ensemble.

    Returns a pipeline dict with all models and artifacts needed for prediction.
    """
    # Build training features
    train_feats, context = build_train_features(train_series)
    feat_cols = get_feature_columns(train_feats)

    # Drop rows with NaN (from lags/rolling at start of series)
    valid_mask = train_feats[feat_cols].notna().all(axis=1) & train_series.notna()
    X_train = train_feats.loc[valid_mask, feat_cols]
    y_train = train_series.loc[valid_mask]

    # Validation set (if provided)
    X_val, y_val = None, None
    if val_series is not None:
        val_index = val_series.index
        horizon_steps = np.arange(len(val_index))
        val_feats = build_prediction_features(val_index, context, horizon_steps)
        # Ensure same columns
        for c in feat_cols:
            if c not in val_feats.columns:
                val_feats[c] = 0
        X_val = val_feats[feat_cols].astype(float)
        X_val = X_val.fillna(X_val.median())
        y_val = val_series

    # Handle NaN in training features
    X_train = X_train.fillna(X_train.median())

    # Train LightGBM (point estimate)
    lgbm_model = train_lgbm(X_train, y_train, X_val, y_val, "regression")

    # Train LightGBM quantile models (prediction intervals)
    lgbm_q05 = train_lgbm(X_train, y_train, X_val, y_val, "quantile", 0.05)
    lgbm_q95 = train_lgbm(X_train, y_train, X_val, y_val, "quantile", 0.95)

    # Train Ridge Fourier model
    ridge_model, ridge_epoch = train_ridge(train_series.dropna())

    # Determine ensemble weights using validation if available
    weights = {"lgbm": 0.6, "ridge": 0.2, "naive": 0.2}  # defaults

    if val_series is not None:
        naive_preds = seasonal_naive_predict(train_series, val_index)
        lgbm_preds = lgbm_model.predict(X_val)
        lgbm_preds = np.maximum(lgbm_preds, 0)
        ridge_preds = predict_ridge(ridge_model, val_index, ridge_epoch).values

        candidate_preds = {
            "lgbm": lgbm_preds,
            "ridge": ridge_preds,
            "naive": naive_preds.values,
        }
        weights = optimize_weights(val_series.values, candidate_preds)

    return {
        "lgbm_model": lgbm_model,
        "lgbm_q05": lgbm_q05,
        "lgbm_q95": lgbm_q95,
        "ridge_model": ridge_model,
        "ridge_epoch": ridge_epoch,
        "context": context,
        "feat_cols": feat_cols,
        "weights": weights,
        "train_medians": X_train.median(),
    }


def predict_with_pipeline(
    pipeline: dict,
    prediction_index: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Generate ensemble predictions with prediction intervals."""
    context = pipeline["context"]
    feat_cols = pipeline["feat_cols"]
    train_series = context["train_series"]

    horizon_steps = np.arange(len(prediction_index))
    pred_feats = build_prediction_features(prediction_index, context, horizon_steps)

    # Ensure same columns and fill NaN
    for c in feat_cols:
        if c not in pred_feats.columns:
            pred_feats[c] = 0
    X = pred_feats[feat_cols].astype(float)
    X = X.fillna(pipeline["train_medians"])

    # Individual predictions
    lgbm_preds = np.maximum(pipeline["lgbm_model"].predict(X), 0)
    ridge_preds = predict_ridge(pipeline["ridge_model"], prediction_index, pipeline["ridge_epoch"]).values
    naive_preds = seasonal_naive_predict(train_series, prediction_index).values

    # Quantile predictions
    q05 = np.maximum(pipeline["lgbm_q05"].predict(X), 0)
    q95 = np.maximum(pipeline["lgbm_q95"].predict(X), 0)

    # Enforce monotonicity
    q95 = np.maximum(q95, q05)

    # Ensemble
    w = pipeline["weights"]
    ensemble = (
        w.get("lgbm", 0) * lgbm_preds
        + w.get("ridge", 0) * ridge_preds
        + w.get("naive", 0) * naive_preds
    )
    ensemble = np.maximum(ensemble, 0)

    return pd.DataFrame({
        "ensemble": ensemble,
        "lgbm": lgbm_preds,
        "ridge": ridge_preds,
        "naive": naive_preds,
        "q05": q05,
        "q95": q95,
    }, index=prediction_index)
