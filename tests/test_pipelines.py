"""Tests for forecasting and anomaly detection pipelines."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_series():
    """Create a small synthetic hourly pollution series for testing."""
    np.random.seed(42)
    n = 2000
    idx = pd.date_range("2022-01-01", periods=n, freq="h")
    # Simple diurnal pattern + noise
    hour = idx.hour
    values = 0.5 + 0.2 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 0.05, n)
    values = np.maximum(values, 0.01)
    return pd.Series(values, index=idx, name="clean_value")


@pytest.fixture
def synthetic_anomaly_df(synthetic_series):
    """Create DataFrame with instrument_status for anomaly detection."""
    df = pd.DataFrame({"clean_value": synthetic_series})
    df["instrument_status"] = 0
    # Inject some anomalies
    df.iloc[500:510, df.columns.get_loc("instrument_status")] = 9
    df.iloc[1000:1005, df.columns.get_loc("instrument_status")] = 4
    return df


class TestForecastFeatures:
    def test_build_train_features(self, synthetic_series):
        from src.forecasting.features import build_train_features

        feats, context = build_train_features(synthetic_series)
        assert len(feats) == len(synthetic_series)
        assert "epoch" in context
        assert "enc_stats" in context
        assert feats.shape[1] > 30  # should have many features

    def test_build_prediction_features(self, synthetic_series):
        from src.forecasting.features import build_train_features, build_prediction_features

        _, context = build_train_features(synthetic_series)
        future_idx = pd.date_range("2022-03-25", periods=24, freq="h")
        pred_feats = build_prediction_features(future_idx, context)
        assert len(pred_feats) == 24
        assert pred_feats.shape[1] > 20


class TestAnomalyDetector:
    def test_build_anomaly_features(self, synthetic_anomaly_df):
        from src.anomaly.detector import build_anomaly_features

        feats = build_anomaly_features(synthetic_anomaly_df)
        assert len(feats) == len(synthetic_anomaly_df)
        assert "value" in feats.columns
        assert "zscore_24" in feats.columns
        assert "consecutive_same" in feats.columns
        assert feats.shape[1] > 50

    def test_train_anomaly_pipeline(self, synthetic_anomaly_df):
        from src.anomaly.detector import train_anomaly_pipeline

        pipeline = train_anomaly_pipeline(synthetic_anomaly_df)
        assert "model" in pipeline
        assert "feat_cols" in pipeline
        assert "threshold" in pipeline
        assert 0 <= pipeline["threshold"] <= 1

    def test_predict_anomalies(self, synthetic_anomaly_df):
        from src.anomaly.detector import train_anomaly_pipeline, predict_anomalies

        pipeline = train_anomaly_pipeline(synthetic_anomaly_df)
        result = predict_anomalies(pipeline, synthetic_anomaly_df.iloc[-100:])

        assert "is_anomaly" in result.columns
        assert "anomaly_probability" in result.columns
        assert result["is_anomaly"].isin([0, 1]).all()
        assert (result["anomaly_probability"] >= 0).all()
        assert (result["anomaly_probability"] <= 1).all()


class TestEvaluateMetrics:
    def test_rmse(self):
        from src.forecasting.evaluate import rmse
        assert rmse(np.array([1, 2, 3]), np.array([1, 2, 3])) == 0.0
        assert rmse(np.array([0, 0]), np.array([1, 1])) == 1.0

    def test_nrmse(self):
        from src.forecasting.evaluate import nrmse
        y = np.array([1, 2, 3, 4, 5])
        # Predicting the mean should give nRMSE ~1.0
        pred_mean = np.full(5, y.mean())
        assert abs(nrmse(y, pred_mean) - 1.0) < 0.1

    def test_evaluate_intervals(self):
        from src.forecasting.evaluate import evaluate_intervals
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        lower = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
        upper = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        result = evaluate_intervals(y, lower, upper)
        assert result["empirical_coverage"] == 1.0  # all within
