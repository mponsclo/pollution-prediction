import os
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
PARQUET_PATH = REPO_ROOT / "data" / "dashboard_wide.parquet"
DATA_BACKEND = os.environ.get("DATA_BACKEND", "parquet").lower()

STATUS_LABELS = {
    0: "Normal",
    1: "Need Calibration",
    2: "Abnormal",
    4: "Power Cut",
    8: "Under Repair",
    9: "Bad Data",
}


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load measurements from the configured backend and derive temporal features.

    Selects between BigQuery and a local Parquet snapshot via the DATA_BACKEND
    env var (default: `parquet`). The Parquet snapshot is produced by
    `scripts/export_to_parquet.py`.
    """
    if DATA_BACKEND == "bigquery":
        # Lazy-imported so free-tier deploys (Streamlit Cloud in parquet mode)
        # don't need `src/` on PYTHONPATH or google-cloud-bigquery at import time.
        from src.data.loader import bq_to_dataframe
        from src.utils.constants import BQ_PROJECT

        df = bq_to_dataframe(f"""
            SELECT
                measurement_datetime,
                station_code,
                latitude,
                longitude,
                so2_value,
                no2_value,
                o3_value,
                co_value,
                pm10_value,
                pm2_5_value,
                instrument_status
            FROM `{BQ_PROJECT}.presentation.dashboard_wide`
            ORDER BY measurement_datetime, station_code
        """)
    else:
        df = pd.read_parquet(PARQUET_PATH)
        df["measurement_datetime"] = pd.to_datetime(df["measurement_datetime"])

    df["year"] = df["measurement_datetime"].dt.year
    df["month"] = df["measurement_datetime"].dt.month
    df["day"] = df["measurement_datetime"].dt.day
    df["hour"] = df["measurement_datetime"].dt.hour
    df["date"] = df["measurement_datetime"].dt.date
    df["day_of_week"] = df["measurement_datetime"].dt.day_name()

    df["status_label"] = df["instrument_status"].map(STATUS_LABELS).fillna("Missing Status")

    return df


@st.cache_data
def get_pollutant_info() -> dict:
    """Pollutant display metadata: name, unit, health threshold, series color."""
    return {
        "so2_value": {"name": "SO₂", "unit": "ppm", "threshold": 0.02, "color": "#1f77b4"},
        "no2_value": {"name": "NO₂", "unit": "ppm", "threshold": 0.03, "color": "#ff7f0e"},
        "o3_value": {"name": "O₃", "unit": "ppm", "threshold": 0.03, "color": "#2ca02c"},
        "co_value": {"name": "CO", "unit": "ppm", "threshold": 2.0, "color": "#d62728"},
        "pm10_value": {"name": "PM10", "unit": "mg/m³", "threshold": 30.0, "color": "#9467bd"},
        "pm2_5_value": {"name": "PM2.5", "unit": "mg/m³", "threshold": 15.0, "color": "#8c564b"},
    }


def create_status_color_map() -> dict:
    """Color mapping for instrument status labels."""
    return {
        "Normal": "#28a745",
        "Need Calibration": "#ffc107",
        "Abnormal": "#dc3545",
        "Power Cut": "#6f42c1",
        "Under Repair": "#fd7e14",
        "Bad Data": "#e83e8c",
        "Missing Status": "#6c757d",
    }


@st.cache_data
def load_forecast_predictions() -> pd.DataFrame | None:
    """Load pre-computed forecast predictions from outputs/."""
    path = OUTPUTS_DIR / "forecast_predictions.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["measurement_datetime"] = pd.to_datetime(df["measurement_datetime"])
    return df


@st.cache_data
def load_anomaly_predictions() -> pd.DataFrame | None:
    """Load pre-computed anomaly predictions from outputs/."""
    path = OUTPUTS_DIR / "anomaly_predictions.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["measurement_datetime"] = pd.to_datetime(df["measurement_datetime"])
    return df
