"""Retroactively log all experiments to MLflow.

Reads the hardcoded results from experiments.md and logs them as MLflow runs
with parameters, metrics, tags, and artifacts.

Usage: python scripts/log_experiments.py
Then view: mlflow ui --port 5000
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mlflow

TRACKING_URI = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mlflow.db')}"
mlflow.set_tracking_uri(TRACKING_URI)

TARGETS = ["SO2", "NO2", "O3", "CO", "PM10", "PM2.5"]


def log_forecast_experiments():
    mlflow.set_experiment("forecasting")

    # --- Exp 1: Seasonal Naive ---
    with mlflow.start_run(run_name="Exp1_Seasonal_Naive"):
        mlflow.set_tag("status", "baseline")
        mlflow.log_param("model_type", "seasonal_naive")
        mlflow.log_param("period_hours", 168)
        mlflow.log_metrics({
            "nrmse_SO2": 1.067, "nrmse_NO2": 0.867, "nrmse_O3": 0.787,
            "nrmse_CO": 0.610, "nrmse_PM10": 0.852, "nrmse_PM2.5": 0.751,
            "avg_nrmse": 0.822,
        })

    # --- Exp 2: XGBoost Recursive ---
    with mlflow.start_run(run_name="Exp2_XGBoost_Recursive"):
        mlflow.set_tag("status", "failed")
        mlflow.log_param("model_type", "xgboost")
        mlflow.log_param("strategy", "recursive")
        mlflow.log_param("n_estimators", 500)
        mlflow.log_param("max_depth", 6)
        mlflow.log_param("learning_rate", 0.05)
        mlflow.log_param("n_features", 30)
        mlflow.log_metric("avg_nrmse", 6.0)  # approximate, 6-10x worse
        mlflow.set_tag("failure_reason", "catastrophic error accumulation over 720+ steps")

    # --- Exp 3: XGBoost Direct ---
    with mlflow.start_run(run_name="Exp3_XGBoost_Direct"):
        mlflow.set_tag("status", "superseded")
        mlflow.log_param("model_type", "xgboost")
        mlflow.log_param("strategy", "direct")
        mlflow.log_param("n_estimators", 500)
        mlflow.log_param("max_depth", 6)
        mlflow.log_param("learning_rate", 0.05)
        mlflow.log_param("n_features", 17)
        mlflow.log_metrics({
            "nrmse_SO2": 0.75, "nrmse_NO2": 0.48, "nrmse_O3": 0.77,
            "nrmse_CO": 0.61, "nrmse_PM10": 0.97, "nrmse_PM2.5": 0.64,
            "avg_nrmse": 0.70,
        })

    # --- Exp 4: LightGBM Ensemble + Fourier ---
    with mlflow.start_run(run_name="Exp4_LightGBM_Ensemble_Fourier"):
        mlflow.set_tag("status", "superseded")
        mlflow.log_param("model_type", "lgbm_ensemble")
        mlflow.log_param("strategy", "direct")
        mlflow.log_param("n_estimators", 800)
        mlflow.log_param("num_leaves", 63)
        mlflow.log_param("max_depth", 8)
        mlflow.log_param("learning_rate", 0.03)
        mlflow.log_param("n_features", 55)
        mlflow.log_param("ensemble", "lgbm+ridge+naive")
        mlflow.log_param("target_transform", "none")
        mlflow.log_param("intervals", "quantile_regression")
        mlflow.log_metrics({
            "nrmse_SO2": 0.92, "nrmse_NO2": 0.66, "nrmse_O3": 0.72,
            "nrmse_CO": 0.45, "nrmse_PM10": 0.52, "nrmse_PM2.5": 0.53,
            "avg_nrmse": 0.63,
            "pi_coverage_SO2": 0.621, "pi_coverage_NO2": 0.824,
            "pi_coverage_O3": 0.889, "pi_coverage_CO": 0.865,
            "pi_coverage_PM10": 0.827, "pi_coverage_PM2.5": 0.870,
        })

    # --- Exp 5: Production — log1p + CQR + Spatial ---
    with mlflow.start_run(run_name="Exp5_Production_Log1p_CQR_Spatial"):
        mlflow.set_tag("status", "production")
        mlflow.log_param("model_type", "lgbm_ensemble")
        mlflow.log_param("strategy", "direct")
        mlflow.log_param("n_estimators", 800)
        mlflow.log_param("num_leaves", 63)
        mlflow.log_param("max_depth", 8)
        mlflow.log_param("learning_rate", 0.03)
        mlflow.log_param("n_features", 57)
        mlflow.log_param("ensemble", "lgbm+ridge+naive")
        mlflow.log_param("target_transform", "log1p")
        mlflow.log_param("intervals", "CQR")
        mlflow.log_param("spatial_features", "IDW_5_nearest")
        mlflow.log_param("validation", "walk_forward_cv_3x720h")
        mlflow.log_metrics({
            "nrmse_SO2": 0.917, "nrmse_NO2": 0.712, "nrmse_O3": 0.715,
            "nrmse_CO": 0.449, "nrmse_PM10": 0.518, "nrmse_PM2.5": 0.546,
            "avg_nrmse": 0.643,
            "r2_SO2": -0.276, "r2_NO2": -0.491, "r2_O3": 0.363,
            "r2_CO": 0.011, "r2_PM10": 0.050, "r2_PM2.5": 0.005,
            "pi_coverage_SO2": 0.938, "pi_coverage_NO2": 0.917,
            "pi_coverage_O3": 0.905, "pi_coverage_CO": 0.936,
            "pi_coverage_PM10": 0.931, "pi_coverage_PM2.5": 0.935,
            "avg_pi_coverage": 0.927,
            "improvement_vs_naive_SO2": 14.0, "improvement_vs_naive_NO2": 18.0,
            "improvement_vs_naive_O3": 9.0, "improvement_vs_naive_CO": 26.0,
            "improvement_vs_naive_PM10": 39.0, "improvement_vs_naive_PM2.5": 27.0,
        })
        # Log artifacts
        for f in ["outputs/forecast_predictions.csv", "outputs/forecast_validation_v3.png"]:
            if os.path.exists(f):
                mlflow.log_artifact(f)

    # --- Exp 6: LSTM ---
    with mlflow.start_run(run_name="Exp6_LSTM_Encoder_Decoder"):
        mlflow.set_tag("status", "not_selected")
        mlflow.log_param("model_type", "lstm")
        mlflow.log_param("hidden_size", 32)
        mlflow.log_param("num_layers", 1)
        mlflow.log_param("window", 48)
        mlflow.log_param("epochs", 30)
        mlflow.log_param("learning_rate", 0.001)
        mlflow.log_metrics({
            "nrmse_SO2": 0.737, "nrmse_NO2": 0.639, "nrmse_O3": 0.907,
            "nrmse_CO": 0.633, "nrmse_PM10": 1.513, "nrmse_PM2.5": 0.718,
            "avg_nrmse": 0.858,
        })

    # --- Exp 7: Cross-Pollutant ---
    with mlflow.start_run(run_name="Exp7_Cross_Pollutant"):
        mlflow.set_tag("status", "mixed")
        mlflow.log_param("model_type", "lgbm_ensemble")
        mlflow.log_param("cross_pollutant", True)
        mlflow.log_metrics({
            "nrmse_SO2": 0.92, "nrmse_NO2": 0.66, "nrmse_O3": 0.71,
            "nrmse_CO": 0.49, "nrmse_PM10": 0.84, "nrmse_PM2.5": 0.69,
            "avg_nrmse": 0.72,
        })

    # --- Exp 8: Global Model ---
    with mlflow.start_run(run_name="Exp8_Global_Model"):
        mlflow.set_tag("status", "not_selected")
        mlflow.log_param("model_type", "lgbm_global")
        mlflow.log_param("train_rows", 500000)
        mlflow.log_metrics({
            "nrmse_SO2": 1.909, "nrmse_NO2": 1.050, "nrmse_O3": 0.978,
            "nrmse_CO": 0.759, "nrmse_PM10": 0.931, "nrmse_PM2.5": 0.636,
            "avg_nrmse": 1.044,
        })

    # --- Exp 9: Weather + xpol(NO2) ---
    with mlflow.start_run(run_name="Exp9_Weather_CrossPollutant_NO2"):
        mlflow.set_tag("status", "not_selected")
        mlflow.log_param("model_type", "lgbm_ensemble")
        mlflow.log_param("weather_features", True)
        mlflow.log_param("cross_pollutant_NO2_only", True)
        mlflow.log_param("weather_source", "open_meteo")
        mlflow.log_metrics({
            "nrmse_SO2": 0.917, "nrmse_NO2": 0.708, "nrmse_O3": 0.713,
            "nrmse_CO": 0.448, "nrmse_PM10": 0.520, "nrmse_PM2.5": 0.544,
            "avg_nrmse": 0.642,
        })


def log_anomaly_experiments():
    mlflow.set_experiment("anomaly-detection")

    # --- Exp 1: Isolation Forest ---
    with mlflow.start_run(run_name="Exp1_Isolation_Forest"):
        mlflow.set_tag("status", "superseded")
        mlflow.log_param("model_type", "isolation_forest")
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("n_features", 11)
        mlflow.log_param("approach", "unsupervised")
        mlflow.log_metrics({
            "f1_205_SO2": 0.500, "f1_209_NO2": 0.000, "f1_223_O3": 0.667,
            "f1_224_CO": 0.029, "f1_226_PM10": 0.133, "f1_227_PM2.5": 0.529,
            "avg_f1": 0.310,
        })

    # --- Exp 2: Supervised LightGBM ---
    with mlflow.start_run(run_name="Exp2_Supervised_LightGBM"):
        mlflow.set_tag("status", "production")
        mlflow.log_param("model_type", "lgbm_classifier")
        mlflow.log_param("n_estimators", 800)
        mlflow.log_param("num_leaves", 63)
        mlflow.log_param("learning_rate", 0.03)
        mlflow.log_param("n_features", 80)
        mlflow.log_param("approach", "supervised")
        mlflow.log_param("threshold_optimization", "f1_precision_recall_curve")
        mlflow.log_param("post_processing", "adaptive_min_run_length")
        mlflow.log_param("xgbod_pattern", True)
        mlflow.log_metrics({
            "f1_205_SO2": 1.000, "f1_209_NO2": 0.000, "f1_223_O3": 1.000,
            "f1_224_CO": 0.956, "f1_226_PM10": 0.235, "f1_227_PM2.5": 0.526,
            "avg_f1": 0.620,
            "precision_205_SO2": 1.000, "precision_223_O3": 1.000,
            "precision_224_CO": 0.916,
            "recall_205_SO2": 1.000, "recall_223_O3": 1.000,
            "recall_224_CO": 1.000,
        })
        for f in ["outputs/anomaly_predictions.csv", "outputs/anomaly_detection.png"]:
            if os.path.exists(f):
                mlflow.log_artifact(f)


def main():
    print("Logging forecast experiments to MLflow...")
    log_forecast_experiments()
    print("Logging anomaly detection experiments to MLflow...")
    log_anomaly_experiments()
    print(f"\nDone. View with: mlflow ui --port 5000")
    print(f"Tracking URI: {TRACKING_URI}")


if __name__ == "__main__":
    main()
