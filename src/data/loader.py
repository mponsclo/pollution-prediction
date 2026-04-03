"""Data loading utilities for the air quality prediction project."""

import duckdb
import pandas as pd

from src.utils.constants import DB_PATH, STATUS_NORMAL


def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DB_PATH, read_only=read_only)


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
    con = get_connection()
    where = ["station_code = ?", "item_code = ?"]
    params = [station_code, item_code]

    if normal_only:
        where.append(f"instrument_status = {STATUS_NORMAL}")
    if end_before:
        where.append("measurement_datetime < ?")
        params.append(end_before)

    query = f"""
        SELECT *
        FROM measurements_clean
        WHERE {' AND '.join(where)}
        ORDER BY measurement_datetime
    """
    df = con.execute(query, params).df()
    con.close()

    df["measurement_datetime"] = pd.to_datetime(df["measurement_datetime"])
    df = df.set_index("measurement_datetime")
    return df


def load_full_series(
    station_code: int,
    item_code: int,
) -> pd.DataFrame:
    """Load full series including all statuses (for anomaly detection)."""
    return load_series(station_code, item_code, normal_only=False)
