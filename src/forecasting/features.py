"""Feature engineering for time-series forecasting."""

import numpy as np
import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add temporal features from the datetime index."""
    df = df.copy()
    idx = df.index

    # Basic temporal features
    df["hour"] = idx.hour
    df["day_of_week"] = idx.dayofweek
    df["month"] = idx.month
    df["day_of_year"] = idx.dayofyear
    df["is_weekend"] = (idx.dayofweek >= 5).astype(int)

    # Cyclical encoding
    df["hour_sin"] = np.sin(2 * np.pi * idx.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * idx.hour / 24)
    df["dow_sin"] = np.sin(2 * np.pi * idx.dayofweek / 7)
    df["dow_cos"] = np.cos(2 * np.pi * idx.dayofweek / 7)
    df["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    df["month_cos"] = np.cos(2 * np.pi * idx.month / 12)

    return df


def add_lag_features(df: pd.DataFrame, col: str = "clean_value") -> pd.DataFrame:
    """Add lag features for the target column."""
    df = df.copy()
    lags = [1, 2, 3, 6, 12, 24, 48, 168]  # hours
    for lag in lags:
        df[f"lag_{lag}h"] = df[col].shift(lag)
    return df


def add_rolling_features(df: pd.DataFrame, col: str = "clean_value") -> pd.DataFrame:
    """Add rolling statistics."""
    df = df.copy()
    windows = [6, 12, 24, 168]  # hours
    for w in windows:
        df[f"rolling_mean_{w}h"] = df[col].shift(1).rolling(w, min_periods=1).mean()
        df[f"rolling_std_{w}h"] = df[col].shift(1).rolling(w, min_periods=1).std()
    return df


def add_diff_features(df: pd.DataFrame, col: str = "clean_value") -> pd.DataFrame:
    """Add difference features."""
    df = df.copy()
    df["diff_1h"] = df[col].diff(1)
    df["diff_24h"] = df[col].diff(24)
    return df


def build_features(df: pd.DataFrame, target_col: str = "clean_value") -> pd.DataFrame:
    """Full feature engineering pipeline."""
    df = add_time_features(df)
    df = add_lag_features(df, target_col)
    df = add_rolling_features(df, target_col)
    df = add_diff_features(df, target_col)
    return df


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """Return list of feature column names (excluding target and metadata)."""
    exclude = {
        "clean_value", "raw_value", "instrument_status", "status_filled",
        "station_code", "latitude", "longitude", "item_code", "item_name",
        "year", "day", "season", "air_quality",
    }
    return [c for c in df.columns if c not in exclude]
