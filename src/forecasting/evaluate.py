"""Evaluation metrics for forecasting models."""

import numpy as np
import pandas as pd


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if mask.sum() == 0:
        return float("inf")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1 - ss_res / ss_tot)


def nrmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Normalized RMSE: RMSE / std(y_true). <1 = better than predicting the mean."""
    std = y_true.std()
    if std == 0:
        return float("inf")
    return rmse(y_true, y_pred) / std


def evaluate_predictions(y_true: pd.Series, y_pred: pd.Series | np.ndarray) -> dict:
    """Compute all evaluation metrics."""
    if isinstance(y_pred, pd.Series):
        common = y_true.index.intersection(y_pred.index)
        yt = y_true.loc[common].values
        yp = y_pred.loc[common].values
    else:
        yt = y_true.values
        yp = y_pred

    return {
        "rmse": rmse(yt, yp),
        "mae": mae(yt, yp),
        "mape": mape(yt, yp),
        "r2": r_squared(yt, yp),
        "nrmse": nrmse(yt, yp),
        "n_samples": len(yt),
    }


def evaluate_intervals(
    y_true: np.ndarray,
    q_lower: np.ndarray,
    q_upper: np.ndarray,
    nominal: float = 0.90,
) -> dict:
    """Evaluate prediction interval quality."""
    in_interval = (y_true >= q_lower) & (y_true <= q_upper)
    coverage = in_interval.mean()
    avg_width = (q_upper - q_lower).mean()
    median_width = np.median(q_upper - q_lower)

    return {
        "nominal_coverage": nominal,
        "empirical_coverage": float(coverage),
        "calibration_error": float(abs(coverage - nominal)),
        "avg_interval_width": float(avg_width),
        "median_interval_width": float(median_width),
    }
