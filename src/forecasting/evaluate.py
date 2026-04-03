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


def evaluate_predictions(y_true: pd.Series, y_pred: pd.Series) -> dict:
    """Compute all evaluation metrics."""
    # Align on common index
    common = y_true.index.intersection(y_pred.index)
    yt = y_true.loc[common].values
    yp = y_pred.loc[common].values

    return {
        "rmse": rmse(yt, yp),
        "mae": mae(yt, yp),
        "mape": mape(yt, yp),
        "n_samples": len(common),
    }
