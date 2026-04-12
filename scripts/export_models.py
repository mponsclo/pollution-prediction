"""Export trained model pipelines as pickle files for API serving.

Usage: python scripts/export_models.py
"""

import gc
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import pandas as pd

from src.anomaly.detector import train_anomaly_pipeline
from src.data.loader import load_full_series, load_series
from src.forecasting.train_lgbm_ensemble import train_forecast_pipeline
from src.utils.constants import ANOMALY_TARGETS, FORECAST_TARGETS

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "models")


def export_forecast_models():
    print("Exporting forecast models...")
    for target in FORECAST_TARGETS:
        sc, ic, name = target["station_code"], target["item_code"], target["item_name"]
        pred_start = target["start"]

        raw = load_series(sc, ic, normal_only=True, end_before=pred_start)
        ts = raw["clean_value"].copy()
        full_idx = pd.date_range(ts.index.min(), ts.index.max(), freq="h")
        ts = ts.reindex(full_idx).ffill().bfill()

        # Use last month as val for weight/CQR calibration
        val_start = ts.index.max() - pd.DateOffset(months=1) + pd.Timedelta(hours=1)
        train_ts = ts.loc[: val_start - pd.Timedelta(hours=1)]
        val_ts = ts.loc[val_start:]

        val_pipe = train_forecast_pipeline(train_ts, val_ts, station_code=sc, item_code=ic)
        full_pipe = train_forecast_pipeline(ts, station_code=sc, item_code=ic)
        full_pipe["weights"] = val_pipe["weights"]
        full_pipe["cqr_correction"] = val_pipe["cqr_correction"]

        path = os.path.join(MODELS_DIR, f"forecast_{sc}_{ic}.pkl")
        joblib.dump(full_pipe, path)
        print(f"  {sc}/{name} → {path}")
        del val_pipe, full_pipe
        gc.collect()


def export_anomaly_models():
    print("Exporting anomaly models...")
    for target in ANOMALY_TARGETS:
        sc, ic, name = target["station_code"], target["item_code"], target["item_name"]

        full = load_full_series(sc, ic)
        labeled = full[full["instrument_status"].notna()].copy()
        labeled["clean_value"] = labeled["clean_value"].ffill().bfill()

        pipe = train_anomaly_pipeline(labeled)
        path = os.path.join(MODELS_DIR, f"anomaly_{sc}_{ic}.pkl")
        joblib.dump(pipe, path)
        print(f"  {sc}/{name} → {path}")
        del pipe
        gc.collect()


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    export_forecast_models()
    export_anomaly_models()
    print(f"\nAll models exported to {MODELS_DIR}")


if __name__ == "__main__":
    main()
