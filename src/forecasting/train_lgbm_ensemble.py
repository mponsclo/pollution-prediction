"""Production-ready forecasting pipeline.

Uses LightGBM with Fourier features, anchor lags, target encoding, spatial
features, log1p target transform, ensemble of LightGBM + Ridge + seasonal naive,
and conformalized quantile regression for calibrated prediction intervals.
"""

import logging

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy.optimize import minimize
from sklearn.linear_model import Ridge

from src.data.weather import (
    get_weather_features_for_prediction,
    get_weather_for_station,
)
from src.forecasting.features import (
    add_fourier_features,
    build_prediction_features,
    build_train_features,
    compute_cross_pollutant_features,
    compute_cross_pollutant_for_prediction,
    compute_spatial_features,
    compute_spatial_features_for_prediction,
    get_feature_columns,
)

logger = logging.getLogger(__name__)

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
    import lightgbm as lgb

    params = _lgbm_params(objective, alpha)
    model = LGBMRegressor(**params)

    fit_kwargs = {}
    if X_val is not None and y_val is not None:
        fit_kwargs["eval_set"] = [(X_val, y_val)]
        fit_kwargs["callbacks"] = [
            lgb.early_stopping(50, verbose=False),
            lgb.log_evaluation(0),
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
# Conformal calibration (CQR)
# ---------------------------------------------------------------------------


def calibrate_intervals_cqr(
    y_cal: np.ndarray,
    q_lo_cal: np.ndarray,
    q_hi_cal: np.ndarray,
    target_coverage: float = 0.90,
) -> float:
    """Compute conformal correction factor Q for CQR.

    Q is added/subtracted to widen the quantile intervals to achieve
    the target coverage guarantee.
    """
    scores = np.maximum(q_lo_cal - y_cal, y_cal - q_hi_cal)
    n = len(scores)
    q_level = min(np.ceil((target_coverage) * (n + 1)) / n, 1.0)
    return float(np.quantile(scores, q_level, method="higher"))


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

        folds.append(
            {
                "train_end": train_end,
                "test_start": test_start,
                "test_end": test_end,
            }
        )

    return list(reversed(folds))


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------


def _add_spatial(df: pd.DataFrame, spatial_df: pd.DataFrame) -> pd.DataFrame:
    """Merge spatial features into feature DataFrame."""
    for col in spatial_df.columns:
        if col in df.columns:
            df[col] = spatial_df[col].values
        else:
            df[col] = spatial_df.reindex(df.index)[col].values
    return df


def train_forecast_pipeline(
    train_series: pd.Series,
    val_series: pd.Series | None = None,
    station_code: int | None = None,
    item_code: int | None = None,
    station_lat: float | None = None,
    station_lon: float | None = None,
) -> dict:
    """Train the full forecast ensemble.

    Returns a pipeline dict with all models and artifacts needed for prediction.
    """
    # --- Log1p target transform ---
    train_log = np.log1p(train_series)
    val_log = np.log1p(val_series) if val_series is not None else None

    # Build training features
    train_feats, context = build_train_features(train_log)
    feat_cols = get_feature_columns(train_feats)

    # Spatial features (if station info provided)
    spatial_ctx = None
    if station_code is not None and item_code is not None:
        try:
            spatial_train, spatial_ctx = compute_spatial_features(station_code, item_code, train_series.index)
            for c in spatial_train.columns:
                if "mean" in c:
                    spatial_train[c] = np.log1p(spatial_train[c])
            train_feats = _add_spatial(train_feats, spatial_train)
            feat_cols = get_feature_columns(train_feats)
        except Exception as e:
            logger.warning(
                "Spatial training features unavailable for station=%s item=%s: %s", station_code, item_code, e
            )
            spatial_ctx = None

    # Cross-pollutant features (NO2 only — CO↔NO2 correlation of 0.78)
    xpol_ctx = None
    if station_code is not None and item_code == 2:  # NO2 only
        try:
            xpol_train, xpol_ctx = compute_cross_pollutant_features(station_code, item_code, train_series.index)
            for c in xpol_train.columns:
                if "lag" in c or "rmean" in c:
                    xpol_train[c] = np.log1p(xpol_train[c].clip(lower=0))
            train_feats = _add_spatial(train_feats, xpol_train)
            feat_cols = get_feature_columns(train_feats)
        except Exception as e:
            logger.warning("Cross-pollutant training features unavailable for station=%s: %s", station_code, e)
            xpol_ctx = None

    # Weather features
    weather_meta = None
    if station_lat is not None and station_lon is not None:
        try:
            weather_train = get_weather_for_station(station_lat, station_lon, train_series.index)
            train_feats = _add_spatial(train_feats, weather_train)
            feat_cols = get_feature_columns(train_feats)
            weather_meta = {"lat": station_lat, "lon": station_lon}
        except Exception as e:
            logger.warning("Weather training features unavailable for (%s, %s): %s", station_lat, station_lon, e)
            weather_meta = None

    # Drop rows with NaN (from lags/rolling at start of series)
    valid_mask = train_feats[feat_cols].notna().all(axis=1) & train_log.notna()
    X_train = train_feats.loc[valid_mask, feat_cols]
    y_train = train_log.loc[valid_mask]

    # Validation set (if provided)
    X_val, y_val = None, None
    if val_log is not None:
        val_index = val_log.index
        horizon_steps = np.arange(len(val_index))
        val_feats = build_prediction_features(val_index, context, horizon_steps)

        if spatial_ctx is not None:
            try:
                spatial_val = compute_spatial_features_for_prediction(val_index, spatial_ctx)
                for c in spatial_val.columns:
                    if "mean" in c:
                        spatial_val[c] = np.log1p(spatial_val[c])
                val_feats = _add_spatial(val_feats, spatial_val)
            except Exception as e:
                logger.warning("Spatial validation features failed: %s", e)

        if xpol_ctx is not None:
            try:
                xpol_val = compute_cross_pollutant_for_prediction(val_index, xpol_ctx, train_series.index[-1])
                for c in xpol_val.columns:
                    if "lag" in c or "rmean" in c:
                        xpol_val[c] = np.log1p(xpol_val[c].clip(lower=0))
                val_feats = _add_spatial(val_feats, xpol_val)
            except Exception as e:
                logger.warning("Cross-pollutant validation features failed: %s", e)

        if weather_meta is not None:
            try:
                weather_val = get_weather_for_station(weather_meta["lat"], weather_meta["lon"], val_index)
                val_feats = _add_spatial(val_feats, weather_val)
            except Exception as e:
                logger.warning("Weather validation features failed: %s", e)

        for c in feat_cols:
            if c not in val_feats.columns:
                val_feats[c] = 0
        X_val = val_feats[feat_cols].astype(float)
        X_val = X_val.fillna(X_val.median())
        y_val = val_log

    # Handle NaN in training features
    train_medians = X_train.median()
    X_train = X_train.fillna(train_medians)

    # Train LightGBM models (in log space)
    lgbm_model = train_lgbm(X_train, y_train, X_val, y_val, "regression")
    lgbm_q05 = train_lgbm(X_train, y_train, X_val, y_val, "quantile", 0.05)
    lgbm_q95 = train_lgbm(X_train, y_train, X_val, y_val, "quantile", 0.95)

    # Train Ridge Fourier model (in log space)
    ridge_model, ridge_epoch = train_ridge(train_log.dropna())

    # --- Conformal calibration on validation ---
    cqr_correction = 0.0
    weights = {"lgbm": 0.6, "ridge": 0.2, "naive": 0.2}

    if val_series is not None:
        # Predict validation in log space, then back-transform
        lgbm_val_log = lgbm_model.predict(X_val)
        q05_val_log = lgbm_q05.predict(X_val)
        q95_val_log = lgbm_q95.predict(X_val)

        # Back-transform to original scale for ensemble optimization
        lgbm_val = np.expm1(np.maximum(lgbm_val_log, 0))
        ridge_val = predict_ridge(ridge_model, val_index, ridge_epoch).values
        # Ridge was trained on log, predictions are in log space
        # Actually ridge.predict returns log-space. Convert:
        ridge_val_log = ridge_val  # already in log from predict_ridge
        # Re-do ridge prediction properly in log space
        fourier_val = add_fourier_features(val_index, ridge_epoch)
        fourier_val["hour"] = val_index.hour
        fourier_val["day_of_week"] = val_index.dayofweek
        fourier_val["month"] = val_index.month
        ridge_val_log = ridge_model.predict(fourier_val.values)
        ridge_val = np.maximum(np.expm1(ridge_val_log), 0)

        naive_val = seasonal_naive_predict(train_series, val_index).values  # original scale

        candidate_preds = {
            "lgbm": np.maximum(lgbm_val, 0),
            "ridge": ridge_val,
            "naive": naive_val,
        }
        weights = optimize_weights(val_series.values, candidate_preds)

        # CQR calibration on validation (original scale)
        q05_val = np.maximum(np.expm1(q05_val_log), 0)
        q95_val = np.maximum(np.expm1(q95_val_log), 0)
        cqr_correction = calibrate_intervals_cqr(val_series.values, q05_val, q95_val, target_coverage=0.90)

    context["train_series_original"] = train_series  # keep original for naive

    return {
        "lgbm_model": lgbm_model,
        "lgbm_q05": lgbm_q05,
        "lgbm_q95": lgbm_q95,
        "ridge_model": ridge_model,
        "ridge_epoch": ridge_epoch,
        "context": context,
        "feat_cols": feat_cols,
        "weights": weights,
        "train_medians": train_medians,
        "cqr_correction": cqr_correction,
        "spatial_ctx": spatial_ctx,
        "xpol_ctx": xpol_ctx,
        "weather_meta": weather_meta,
    }


def predict_with_pipeline(
    pipeline: dict,
    prediction_index: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Generate ensemble predictions with calibrated prediction intervals."""
    context = pipeline["context"]
    feat_cols = pipeline["feat_cols"]
    train_series_orig = context.get("train_series_original", context["train_series"])

    horizon_steps = np.arange(len(prediction_index))
    pred_feats = build_prediction_features(prediction_index, context, horizon_steps)

    # Spatial features
    if pipeline.get("spatial_ctx") is not None:
        try:
            spatial_pred = compute_spatial_features_for_prediction(prediction_index, pipeline["spatial_ctx"])
            for c in spatial_pred.columns:
                if "mean" in c:
                    spatial_pred[c] = np.log1p(spatial_pred[c])
            pred_feats = _add_spatial(pred_feats, spatial_pred)
        except Exception as e:
            logger.warning("Spatial prediction features failed: %s", e)

    # Cross-pollutant features
    if pipeline.get("xpol_ctx") is not None:
        try:
            xpol_pred = compute_cross_pollutant_for_prediction(
                prediction_index, pipeline["xpol_ctx"], train_series_orig.index[-1]
            )
            for c in xpol_pred.columns:
                if "lag" in c or "rmean" in c:
                    xpol_pred[c] = np.log1p(xpol_pred[c].clip(lower=0))
            pred_feats = _add_spatial(pred_feats, xpol_pred)
        except Exception as e:
            logger.warning("Cross-pollutant prediction features failed: %s", e)

    # Weather features (use historical averages for future timestamps)
    if pipeline.get("weather_meta") is not None:
        try:
            weather_pred = get_weather_features_for_prediction(
                prediction_index,
                pipeline["weather_meta"]["lat"],
                pipeline["weather_meta"]["lon"],
            )
            pred_feats = _add_spatial(pred_feats, weather_pred)
        except Exception as e:
            logger.warning("Weather prediction features failed: %s", e)

    for c in feat_cols:
        if c not in pred_feats.columns:
            pred_feats[c] = 0
    X = pred_feats[feat_cols].astype(float)
    X = X.fillna(pipeline["train_medians"])

    # Predict in log space, back-transform
    lgbm_log = pipeline["lgbm_model"].predict(X)
    lgbm_preds = np.maximum(np.expm1(lgbm_log), 0)

    # Ridge in log space
    fourier_pred = add_fourier_features(prediction_index, pipeline["ridge_epoch"])
    fourier_pred["hour"] = prediction_index.hour
    fourier_pred["day_of_week"] = prediction_index.dayofweek
    fourier_pred["month"] = prediction_index.month
    ridge_log = pipeline["ridge_model"].predict(fourier_pred.values)
    ridge_preds = np.maximum(np.expm1(ridge_log), 0)

    naive_preds = seasonal_naive_predict(train_series_orig, prediction_index).values

    # Quantile predictions (log space → original)
    q05_log = pipeline["lgbm_q05"].predict(X)
    q95_log = pipeline["lgbm_q95"].predict(X)
    q05 = np.maximum(np.expm1(q05_log), 0)
    q95 = np.maximum(np.expm1(q95_log), 0)

    # Apply CQR conformal correction
    cqr = pipeline.get("cqr_correction", 0.0)
    q05_cal = np.maximum(q05 - cqr, 0)
    q95_cal = q95 + cqr

    # Enforce monotonicity
    q95_cal = np.maximum(q95_cal, q05_cal)

    # Ensemble
    w = pipeline["weights"]
    ensemble = w.get("lgbm", 0) * lgbm_preds + w.get("ridge", 0) * ridge_preds + w.get("naive", 0) * naive_preds
    ensemble = np.maximum(ensemble, 0)

    return pd.DataFrame(
        {
            "ensemble": ensemble,
            "lgbm": lgbm_preds,
            "ridge": ridge_preds,
            "naive": naive_preds,
            "q05": q05_cal,
            "q95": q95_cal,
        },
        index=prediction_index,
    )
