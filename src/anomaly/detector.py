"""Anomaly detection for instrument failures."""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, f1_score


def build_anomaly_features(df: pd.DataFrame, col: str = "clean_value") -> pd.DataFrame:
    """Build features for anomaly detection from a time series.

    Features capture deviations from expected behavior that indicate
    instrument malfunction.
    """
    out = pd.DataFrame(index=df.index)
    values = df[col].copy()

    # Current value
    out["value"] = values

    # Deviation from rolling mean
    for w in [6, 12, 24]:
        rolling_mean = values.shift(1).rolling(w, min_periods=1).mean()
        rolling_std = values.shift(1).rolling(w, min_periods=1).std().clip(lower=1e-10)
        out[f"dev_from_mean_{w}h"] = (values - rolling_mean) / rolling_std

    # Rate of change
    out["diff_1h"] = values.diff(1)
    out["diff_24h"] = values.diff(24)
    out["abs_diff_1h"] = values.diff(1).abs()

    # Value relative to same hour yesterday
    out["diff_from_yesterday"] = values - values.shift(24)

    # Consecutive identical readings (stuck sensor)
    out["same_as_prev"] = (values == values.shift(1)).astype(int)
    out["consecutive_same"] = out["same_as_prev"].groupby(
        (out["same_as_prev"] != out["same_as_prev"].shift()).cumsum()
    ).cumsum()

    # Temporal context
    out["hour"] = df.index.hour
    out["day_of_week"] = df.index.dayofweek

    return out


def train_anomaly_detector(
    train_df: pd.DataFrame,
    contamination: float = 0.02,
) -> tuple[IsolationForest, StandardScaler, list[str]]:
    """Train Isolation Forest on normal data.

    Args:
        train_df: DataFrame with clean_value column and datetime index.
                  Should include both normal and anomalous readings for
                  contamination estimation.
        contamination: Expected anomaly rate.
    """
    features = build_anomaly_features(train_df)
    feature_cols = [c for c in features.columns if c not in {"hour", "day_of_week"}]

    # Include temporal features
    feature_cols += ["hour", "day_of_week"]

    # Drop NaN rows (from rolling/diff calculations)
    clean = features[feature_cols].dropna()

    scaler = StandardScaler()
    X = scaler.fit_transform(clean)

    model = IsolationForest(
        contamination=contamination,
        n_estimators=200,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)

    return model, scaler, feature_cols


def predict_anomalies(
    model: IsolationForest,
    scaler: StandardScaler,
    df: pd.DataFrame,
    feature_cols: list[str],
) -> pd.DataFrame:
    """Predict anomalies on new data.

    Returns DataFrame with columns: is_anomaly (bool), anomaly_score (float).
    """
    features = build_anomaly_features(df)
    clean = features[feature_cols].dropna()

    X = scaler.transform(clean)
    scores = model.decision_function(X)
    labels = model.predict(X)  # 1 = normal, -1 = anomaly

    result = pd.DataFrame(index=clean.index)
    result["is_anomaly"] = (labels == -1)
    result["anomaly_score"] = -scores  # Higher = more anomalous
    result["predicted_status"] = result["is_anomaly"].map({True: 1, False: 0})

    return result


def evaluate_anomaly_detection(
    y_true: pd.Series,
    y_pred: pd.Series,
) -> dict:
    """Evaluate anomaly detection against ground truth labels.

    Args:
        y_true: Series of instrument_status values (0 = normal, else = anomaly)
        y_pred: Series of predicted labels (0 = normal, 1 = anomaly)
    """
    # Binary: normal (0) vs anomaly (any non-zero)
    true_binary = (y_true != 0).astype(int)
    pred_binary = y_pred.astype(int)

    # Align indices
    common = true_binary.index.intersection(pred_binary.index)
    yt = true_binary.loc[common]
    yp = pred_binary.loc[common]

    report = classification_report(yt, yp, target_names=["Normal", "Anomaly"], output_dict=True)
    f1 = f1_score(yt, yp)

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
