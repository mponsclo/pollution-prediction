"""Data loading utilities for the air quality prediction project."""

import pandas as pd
from google.cloud import bigquery

from src.utils.constants import BQ_PROJECT, BQ_TABLE_CLEAN, STATUS_NORMAL

_client = None


def bq_to_dataframe(query: str, client=None) -> pd.DataFrame:
    """Execute a BigQuery query and return a DataFrame with proper numeric types."""
    c = client or get_bq_client()
    df = c.query(query).to_dataframe()
    # BigQuery NUMERIC returns Decimal objects; convert to float for ML pipelines
    for col in df.columns:
        if df[col].dtype == object:
            try:
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().any():
                    df[col] = converted
            except (ValueError, TypeError):
                pass
    return df


def get_bq_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=BQ_PROJECT)
    return _client


def load_series(
    station_code: int,
    item_code: int,
    normal_only: bool = True,
    end_before: str | None = None,
) -> pd.DataFrame:
    """Load a single time-series for a station/pollutant pair.

    Returns a DataFrame indexed by measurement_datetime with columns:
    clean_value, raw_value, instrument_status, and temporal features.
    """
    where = [
        f"station_code = {station_code}",
        f"item_code = {item_code}",
    ]

    if normal_only:
        where.append(f"instrument_status = {STATUS_NORMAL}")
    if end_before:
        where.append(f"measurement_datetime < '{end_before}'")

    query = f"""
        SELECT *
        FROM {BQ_TABLE_CLEAN}
        WHERE {" AND ".join(where)}
        ORDER BY measurement_datetime
    """
    df = bq_to_dataframe(query)

    df["measurement_datetime"] = pd.to_datetime(df["measurement_datetime"])
    df = df.set_index("measurement_datetime")
    return df


def load_full_series(
    station_code: int,
    item_code: int,
) -> pd.DataFrame:
    """Load full series including all statuses (for anomaly detection)."""
    return load_series(station_code, item_code, normal_only=False)
