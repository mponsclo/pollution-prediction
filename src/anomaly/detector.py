"""Supervised anomaly detection for instrument failures.

Uses LightGBM binary classifier with rich feature engineering,
F1-optimized threshold tuning, and temporal post-processing.

Replaces the unsupervised Isolation Forest approach (preserved in
detector_isolation_forest.py).
"""

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_recall_curve,
)

# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------


def build_anomaly_features(df: pd.DataFrame, col: str = "clean_value") -> pd.DataFrame:
    """Build rich features for anomaly detection.

    ~80 features capturing statistical, temporal, and instrument failure signatures.
    """
    out = pd.DataFrame(index=df.index)
    v = df[col].copy()

    # --- Value features ---
    out["value"] = v
    out["log_value"] = np.log1p(v.clip(lower=0))

    # --- Rolling statistics at multiple windows ---
    for w in [3, 6, 12, 24, 48, 168]:
        rm = v.shift(1).rolling(w, min_periods=1)
        out[f"rmean_{w}"] = rm.mean()
        out[f"rstd_{w}"] = rm.std()
        out[f"rmin_{w}"] = rm.min()
        out[f"rmax_{w}"] = rm.max()
        out[f"rrange_{w}"] = rm.max() - rm.min()
        std_safe = rm.std().clip(lower=1e-10)
        out[f"zscore_{w}"] = (v - rm.mean()) / std_safe

    # --- Lag and diff features ---
    for lag in [1, 2, 3, 6, 12, 24, 48, 168]:
        out[f"lag_{lag}"] = v.shift(lag)
        out[f"diff_{lag}"] = v.diff(lag)
        out[f"abs_diff_{lag}"] = v.diff(lag).abs()

    # --- Instrument failure signatures ---
    # Stuck sensor: consecutive identical readings
    same = v == v.shift(1)
    out["consecutive_same"] = same.groupby((~same).cumsum()).cumsum()

    # Flatline detection (rolling std near zero)
    out["flatline_6h"] = (v.rolling(6, min_periods=3).std() < 1e-10).astype(int)
    out["flatline_12h"] = (v.rolling(12, min_periods=6).std() < 1e-10).astype(int)

    # Value at zero or negative (missing value sentinel)
    out["at_zero"] = (v == 0).astype(int)
    out["at_negative"] = (v < 0).astype(int)

    # Spike score: deviation from neighbors
    neighbor_mean = (v.shift(1) + v.shift(-1)) / 2
    out["spike_score"] = (v - neighbor_mean).abs()

    # --- Temporal context ---
    out["hour_sin"] = np.sin(2 * np.pi * df.index.hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * df.index.hour / 24)
    out["dow_sin"] = np.sin(2 * np.pi * df.index.dayofweek / 7)
    out["dow_cos"] = np.cos(2 * np.pi * df.index.dayofweek / 7)
    out["month"] = df.index.month
    out["is_weekend"] = (df.index.dayofweek >= 5).astype(int)

    # --- Deviation from hourly median (contextual anomaly) ---
    hourly_median = v.groupby(df.index.hour).transform("median")
    hourly_std = v.groupby(df.index.hour).transform("std").clip(lower=1e-10)
    out["dev_from_hourly_median"] = (v - hourly_median) / hourly_std

    return out


def _get_feature_cols(df: pd.DataFrame) -> list[str]:
    return list(df.columns)


# ---------------------------------------------------------------------------
# Threshold optimization
# ---------------------------------------------------------------------------


def optimize_threshold_f1(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """Find the decision threshold that maximizes F1 score."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    f1s = 2 * (precisions[:-1] * recalls[:-1]) / (precisions[:-1] + recalls[:-1] + 1e-10)
    if len(f1s) == 0:
        return 0.5
    return float(thresholds[np.argmax(f1s)])


# ---------------------------------------------------------------------------
# Temporal post-processing
# ---------------------------------------------------------------------------


def filter_min_run_length(preds: np.ndarray, min_length: int = 3) -> np.ndarray:
    """Remove anomaly runs shorter than min_length hours."""
    filtered = preds.copy()
    in_run = False
    run_start = 0

    for i in range(len(filtered)):
        if filtered[i] == 1 and not in_run:
            in_run = True
            run_start = i
        elif filtered[i] == 0 and in_run:
            if i - run_start < min_length:
                filtered[run_start:i] = 0
            in_run = False

    if in_run and len(filtered) - run_start < min_length:
        filtered[run_start:] = 0

    return filtered


# ---------------------------------------------------------------------------
# Training pipeline
# ---------------------------------------------------------------------------


def train_anomaly_pipeline(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame | None = None,
) -> dict:
    """Train the supervised anomaly detection pipeline.

    Args:
        train_df: DataFrame with clean_value and instrument_status columns,
                  datetime index.
        val_df: Optional validation DataFrame for threshold tuning.

    Returns pipeline dict with model, threshold, feature info.
    """
    # Build labels
    y_train = (train_df["instrument_status"] != 0).astype(int)

    # Build features
    train_feats = build_anomaly_features(train_df)
    feat_cols = _get_feature_cols(train_feats)

    # Add Isolation Forest anomaly score as bonus feature (XGBOD pattern)
    iso = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1)
    iso_input_cols = list(feat_cols)  # save before adding iso_score
    clean_train = train_feats[iso_input_cols].fillna(0).values
    iso.fit(clean_train)
    train_feats["iso_score"] = -iso.decision_function(clean_train)
    feat_cols.append("iso_score")

    # Drop NaN rows
    valid = train_feats[feat_cols].notna().all(axis=1)
    X_train = train_feats.loc[valid, feat_cols].astype(float).fillna(0)
    y_train = y_train.loc[valid]

    # Train LightGBM (no scale_pos_weight — keep calibrated probabilities)
    model = LGBMClassifier(
        n_estimators=800,
        learning_rate=0.03,
        num_leaves=63,
        max_depth=8,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    # Validation for early stopping
    if val_df is not None:
        y_val = (val_df["instrument_status"] != 0).astype(int)
        val_feats_es = build_anomaly_features(val_df)
        val_feats_es["iso_score"] = -iso.decision_function(val_feats_es[iso_input_cols].fillna(0).values)
        X_val_es = val_feats_es[feat_cols].astype(float).fillna(0)

        import lightgbm as lgb

        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val_es, y_val)],
            callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)],
        )
    else:
        model.fit(X_train, y_train)

    # Optimize threshold on validation set
    threshold = 0.5
    if val_df is not None:
        y_val_true = (val_df["instrument_status"] != 0).astype(int)
        val_feats = build_anomaly_features(val_df)
        val_feats["iso_score"] = -iso.decision_function(val_feats[iso_input_cols].fillna(0).values)
        X_val = val_feats[feat_cols].astype(float).fillna(0)
        y_val_proba = model.predict_proba(X_val)[:, 1]
        threshold = optimize_threshold_f1(y_val_true.values, y_val_proba)

    return {
        "model": model,
        "iso_forest": iso,
        "iso_input_cols": iso_input_cols,
        "feat_cols": feat_cols,
        "threshold": threshold,
    }


def predict_anomalies(
    pipeline: dict,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Predict anomalies with adaptive temporal post-processing."""
    model = pipeline["model"]
    iso = pipeline["iso_forest"]
    iso_input_cols = pipeline["iso_input_cols"]
    feat_cols = pipeline["feat_cols"]
    threshold = pipeline["threshold"]

    feats = build_anomaly_features(df)
    feats["iso_score"] = -iso.decision_function(feats[iso_input_cols].fillna(0).values)
    X = feats[feat_cols].astype(float).fillna(0)

    proba = model.predict_proba(X)[:, 1]

    # Raw predictions with optimized threshold
    raw_preds = (proba >= threshold).astype(int)

    # Adaptive post-processing: only filter if enough anomalies to form runs
    raw_anomaly_rate = raw_preds.mean()
    if raw_anomaly_rate > 0.05:  # enough anomalies for meaningful runs
        smoothed_preds = filter_min_run_length(raw_preds, min_length=3)
    else:
        smoothed_preds = raw_preds  # sparse anomalies — keep all

    result = pd.DataFrame(index=df.index)
    result["anomaly_probability"] = proba
    result["is_anomaly_raw"] = raw_preds
    result["is_anomaly"] = smoothed_preds
    result["predicted_status"] = smoothed_preds

    return result


def evaluate_anomaly_detection(
    y_true: pd.Series,
    y_pred: pd.Series,
) -> dict:
    """Evaluate anomaly detection against ground truth labels."""
    true_binary = (y_true != 0).astype(int)
    pred_binary = y_pred.astype(int)

    common = true_binary.index.intersection(pred_binary.index)
    yt = true_binary.loc[common]
    yp = pred_binary.loc[common]

    report = classification_report(yt, yp, target_names=["Normal", "Anomaly"], output_dict=True)
    f1 = f1_score(yt, yp, zero_division=0)

    return {
        "f1_anomaly": f1,
        "precision_anomaly": report["Anomaly"]["precision"],
        "recall_anomaly": report["Anomaly"]["recall"],
        "accuracy": report["accuracy"],
        "n_true_anomalies": int(yt.sum()),
        "n_predicted_anomalies": int(yp.sum()),
        "n_total": len(common),
        "report": classification_report(yt, yp, target_names=["Normal", "Anomaly"]),
    }
