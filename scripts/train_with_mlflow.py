"""Train models with MLflow experiment tracking.

Wraps the existing training pipelines with MLflow logging for parameters,
metrics, and model artifacts.

Usage:
    python scripts/train_with_mlflow.py --task forecast --all
    python scripts/train_with_mlflow.py --task anomaly --all
    python scripts/train_with_mlflow.py --task forecast --target 206/0
"""

import argparse
import gc
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import mlflow
import numpy as np
import pandas as pd

from src.anomaly.detector import (
    evaluate_anomaly_detection,
    predict_anomalies,
    train_anomaly_pipeline,
)
from src.data.loader import load_full_series, load_series
from src.forecasting.evaluate import evaluate_intervals, evaluate_predictions
from src.forecasting.train_lgbm_ensemble import (
    predict_with_pipeline,
    train_forecast_pipeline,
    walk_forward_cv,
)
from src.utils.constants import ANOMALY_TARGETS, FORECAST_TARGETS

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKING_URI = f"sqlite:///{os.path.join(PROJECT_ROOT, 'mlflow.db')}"
MODELS_DIR = os.path.join(PROJECT_ROOT, "outputs", "models")


def train_forecast(target: dict):
    """Train and log a single forecast target."""
    sc, ic, name = target["station_code"], target["item_code"], target["item_name"]
    pred_start, pred_end = target["start"], target["end"]

    raw = load_series(sc, ic, normal_only=True, end_before=pred_start)
    ts = raw["clean_value"].copy()
    full_idx = pd.date_range(ts.index.min(), ts.index.max(), freq="h")
    ts = ts.reindex(full_idx).ffill().bfill()
    overall_std = ts.std()

    with mlflow.start_run(run_name=f"forecast_{sc}_{name}"):
        mlflow.log_params(
            {
                "station_code": sc,
                "item_code": ic,
                "pollutant": name,
                "prediction_period": f"{pred_start} to {pred_end}",
                "model_type": "lgbm_ensemble",
                "n_estimators": 800,
                "num_leaves": 63,
                "learning_rate": 0.03,
                "target_transform": "log1p",
                "intervals": "CQR",
            }
        )

        # Walk-forward CV
        folds = walk_forward_cv(ts, n_folds=3, test_size=720, min_train_size=8760)
        cv_nrmse, cv_r2, cv_cov = [], [], []

        for i, fold in enumerate(folds):
            ft = ts.iloc[: fold["train_end"]]
            fv = ts.iloc[fold["test_start"] : fold["test_end"]]

            pipe = train_forecast_pipeline(ft, fv, station_code=sc, item_code=ic)
            preds = predict_with_pipeline(pipe, fv.index)

            m = evaluate_predictions(fv, preds["ensemble"])
            iv = evaluate_intervals(fv.values, preds["q05"].values, preds["q95"].values)
            nrmse = m["rmse"] / overall_std

            mlflow.log_metrics(
                {
                    f"fold{i}_nrmse": round(nrmse, 4),
                    f"fold{i}_r2": round(m["r2"], 4),
                    f"fold{i}_coverage": round(iv["empirical_coverage"], 4),
                },
                step=i,
            )

            cv_nrmse.append(nrmse)
            cv_r2.append(m["r2"])
            cv_cov.append(iv["empirical_coverage"])
            del pipe, preds
            gc.collect()

        mlflow.log_metrics(
            {
                "cv_nrmse": round(np.mean(cv_nrmse), 4),
                "cv_r2": round(np.mean(cv_r2), 4),
                "cv_coverage": round(np.mean(cv_cov), 4),
            }
        )

        # Train final model and export
        val_start = ts.index.max() - pd.DateOffset(months=1) + pd.Timedelta(hours=1)
        train_final = ts.loc[: val_start - pd.Timedelta(hours=1)]
        val_final = ts.loc[val_start:]

        final_pipe = train_forecast_pipeline(train_final, val_final, station_code=sc, item_code=ic)
        full_pipe = train_forecast_pipeline(ts, station_code=sc, item_code=ic)
        full_pipe["weights"] = final_pipe["weights"]
        full_pipe["cqr_correction"] = final_pipe["cqr_correction"]

        # Save model artifact
        os.makedirs(MODELS_DIR, exist_ok=True)
        model_path = os.path.join(MODELS_DIR, f"forecast_{sc}_{ic}.pkl")
        joblib.dump(full_pipe, model_path)
        mlflow.log_artifact(model_path)

        mlflow.log_params({f"weight_{k}": round(v, 3) for k, v in full_pipe["weights"].items()})
        mlflow.set_tag("status", "production")

        print(f"  {sc}/{name}: nRMSE={np.mean(cv_nrmse):.3f}, coverage={np.mean(cv_cov):.3f}")
        del final_pipe, full_pipe
        gc.collect()


def train_anomaly(target: dict):
    """Train and log a single anomaly target."""
    sc, ic, name = target["station_code"], target["item_code"], target["item_name"]
    pred_start, pred_end = target["start"], target["end"]

    full = load_full_series(sc, ic)
    labeled = full[full["instrument_status"].notna()].copy()
    target_data = full[(full.index >= pred_start) & (full.index <= pred_end)].copy()
    labeled["clean_value"] = labeled["clean_value"].ffill().bfill()
    target_data["clean_value"] = target_data["clean_value"].ffill().bfill()

    with mlflow.start_run(run_name=f"anomaly_{sc}_{name}"):
        mlflow.log_params(
            {
                "station_code": sc,
                "item_code": ic,
                "pollutant": name,
                "model_type": "lgbm_classifier",
                "n_features": 80,
                "approach": "supervised",
                "xgbod_pattern": True,
            }
        )

        # Validation split
        val_start = labeled.index.max() - pd.DateOffset(months=1) + pd.Timedelta(hours=1)
        train_data = labeled.loc[: val_start - pd.Timedelta(hours=1)]
        val_data = labeled.loc[val_start:]

        pipe = train_anomaly_pipeline(train_data, val_data)
        val_preds = predict_anomalies(pipe, val_data)
        m = evaluate_anomaly_detection(val_data["instrument_status"], val_preds["is_anomaly"])

        mlflow.log_metrics(
            {
                "val_f1": round(m["f1_anomaly"], 4),
                "val_precision": round(m["precision_anomaly"], 4),
                "val_recall": round(m["recall_anomaly"], 4),
                "threshold": round(pipe["threshold"], 4),
            }
        )

        # Retrain on all labeled data and export
        final_pipe = train_anomaly_pipeline(labeled)
        os.makedirs(MODELS_DIR, exist_ok=True)
        model_path = os.path.join(MODELS_DIR, f"anomaly_{sc}_{ic}.pkl")
        joblib.dump(final_pipe, model_path)
        mlflow.log_artifact(model_path)
        mlflow.set_tag("status", "production")

        print(f"  {sc}/{name}: F1={m['f1_anomaly']:.3f}")
        del pipe, final_pipe
        gc.collect()


def main():
    parser = argparse.ArgumentParser(description="Train models with MLflow tracking")
    parser.add_argument("--task", choices=["forecast", "anomaly"], required=True)
    parser.add_argument("--target", help="e.g. 206/0 for station 206, item_code 0")
    parser.add_argument("--all", action="store_true", help="Train all targets")
    args = parser.parse_args()

    mlflow.set_tracking_uri(TRACKING_URI)

    if args.task == "forecast":
        mlflow.set_experiment("forecasting")
        targets = FORECAST_TARGETS
        train_fn = train_forecast
    else:
        mlflow.set_experiment("anomaly-detection")
        targets = ANOMALY_TARGETS
        train_fn = train_anomaly

    if args.all:
        print(f"Training all {len(targets)} {args.task} targets...")
        for t in targets:
            train_fn(t)
    elif args.target:
        sc, ic = args.target.split("/")
        t = next(t for t in targets if t["station_code"] == int(sc) and t["item_code"] == int(ic))
        train_fn(t)
    else:
        parser.error("Specify --all or --target")


if __name__ == "__main__":
    main()
