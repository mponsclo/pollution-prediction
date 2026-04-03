"""Global forecasting model — single LightGBM trained across all stations × pollutants.

Instead of training 6 separate models, trains ONE model on ~3.7M rows from all
25 stations and 6 pollutants, with station_code and item_code as features.
The model learns transferable patterns across the entire network.

Experiment 8.
"""

import numpy as np
import pandas as pd
import duckdb
from lightgbm import LGBMRegressor

from src.utils.constants import DB_PATH, ITEM_NAMES, STATUS_NORMAL
from src.forecasting.features import (
    add_fourier_features,
    compute_target_encodings,
    apply_target_encodings,
)


def load_all_series(end_before: str | None = None) -> pd.DataFrame:
    """Load all station×pollutant series from the database."""
    con = duckdb.connect(DB_PATH, read_only=True)

    where = "instrument_status = 0 AND clean_value IS NOT NULL"
    if end_before:
        where += f" AND measurement_datetime < '{end_before}'"

    df = con.sql(f"""
        SELECT
            measurement_datetime, station_code, item_code, clean_value,
            latitude, longitude
        FROM measurements_clean
        WHERE {where}
        ORDER BY station_code, item_code, measurement_datetime
    """).df()
    con.close()

    df["measurement_datetime"] = pd.to_datetime(df["measurement_datetime"])
    return df


def build_global_features(df: pd.DataFrame, epoch: pd.Timestamp) -> pd.DataFrame:
    """Build features for the global model.

    Adds station/pollutant identifiers, temporal, Fourier, and per-group
    historical statistics.
    """
    out = pd.DataFrame(index=df.index)
    idx = pd.DatetimeIndex(df["measurement_datetime"])

    # Identifiers (categorical)
    out["station_code"] = df["station_code"].values
    out["item_code"] = df["item_code"].values

    # Temporal
    out["hour"] = idx.hour
    out["day_of_week"] = idx.dayofweek
    out["month"] = idx.month
    out["day_of_year"] = idx.dayofyear
    out["is_weekend"] = (idx.dayofweek >= 5).astype(int)

    # Cyclical
    out["hour_sin"] = np.sin(2 * np.pi * idx.hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * idx.hour / 24)
    out["dow_sin"] = np.sin(2 * np.pi * idx.dayofweek / 7)
    out["dow_cos"] = np.cos(2 * np.pi * idx.dayofweek / 7)
    out["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    out["month_cos"] = np.cos(2 * np.pi * idx.month / 12)

    # Fourier
    fourier = add_fourier_features(idx, epoch)
    fourier.index = out.index
    out = pd.concat([out, fourier], axis=1)

    # Spatial
    out["latitude"] = df["latitude"].values
    out["longitude"] = df["longitude"].values

    return out


def compute_global_stats(df: pd.DataFrame) -> dict:
    """Compute per-group historical statistics for the global model."""
    stats = {}

    for (sc, ic), grp in df.groupby(["station_code", "item_code"]):
        series = grp.set_index("measurement_datetime")["clean_value"]
        key = (int(sc), int(ic))

        # Hourly means
        hourly = series.groupby(series.index.hour).mean().to_dict()

        # Hour×dow means
        hour_dow = series.groupby([series.index.hour, series.index.dayofweek]).mean().to_dict()

        # Month×hour means
        month_hour = series.groupby([series.index.month, series.index.hour]).mean().to_dict()

        # Overall stats
        stats[key] = {
            "hourly": hourly,
            "hour_dow": hour_dow,
            "month_hour": month_hour,
            "mean": float(series.mean()),
            "std": float(series.std()),
        }

    return stats


def add_group_stats(
    features: pd.DataFrame,
    df: pd.DataFrame,
    stats: dict,
) -> pd.DataFrame:
    """Add per-station/pollutant historical statistics as features."""
    idx = pd.DatetimeIndex(df["measurement_datetime"])

    enc_hour = []
    enc_hour_dow = []
    enc_month_hour = []
    group_mean = []
    group_std = []

    for i in range(len(df)):
        key = (int(df.iloc[i]["station_code"]), int(df.iloc[i]["item_code"]))
        s = stats.get(key, {})
        h = idx[i].hour
        dow = idx[i].dayofweek
        m = idx[i].month

        enc_hour.append(s.get("hourly", {}).get(h, s.get("mean", 0)))
        enc_hour_dow.append(s.get("hour_dow", {}).get((h, dow), s.get("mean", 0)))
        enc_month_hour.append(s.get("month_hour", {}).get((m, h), s.get("mean", 0)))
        group_mean.append(s.get("mean", 0))
        group_std.append(s.get("std", 1))

    features["enc_hour"] = enc_hour
    features["enc_hour_dow"] = enc_hour_dow
    features["enc_month_hour"] = enc_month_hour
    features["group_mean"] = group_mean
    features["group_std"] = group_std

    return features


def train_global_model(
    end_before: str | None = None,
    max_rows: int | None = None,
) -> dict:
    """Train the global LightGBM model."""
    print("  Loading all series...")
    df = load_all_series(end_before)

    # Optional: subsample for speed
    if max_rows and len(df) > max_rows:
        # Keep most recent data (recency > volume)
        df = df.groupby(["station_code", "item_code"]).tail(
            max_rows // df[["station_code", "item_code"]].drop_duplicates().shape[0]
        ).reset_index(drop=True)

    epoch = df["measurement_datetime"].min()
    print(f"  Building features for {len(df)} rows...")

    # Log transform target
    y = np.log1p(df["clean_value"].values)

    # Build features
    features = build_global_features(df, epoch)
    stats = compute_global_stats(df)
    features = add_group_stats(features, df, stats)

    feat_cols = [c for c in features.columns]
    X = features[feat_cols].astype(float)
    X = X.fillna(X.median())

    # Train/eval split (last 10%)
    split = int(len(X) * 0.9)
    X_train, X_eval = X.iloc[:split], X.iloc[split:]
    y_train, y_eval = y[:split], y[split:]

    print(f"  Training LightGBM ({len(X_train)} train, {len(X_eval)} eval)...")
    import lightgbm as lgb

    model = LGBMRegressor(
        n_estimators=1000,
        num_leaves=127,
        max_depth=10,
        learning_rate=0.03,
        subsample=0.7,
        colsample_bytree=0.7,
        min_child_samples=50,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_eval, y_eval)],
        callbacks=[
            lgb.early_stopping(50, verbose=False),
            lgb.log_evaluation(0),
        ],
    )

    train_medians = X.median()

    return {
        "model": model,
        "epoch": epoch,
        "stats": stats,
        "feat_cols": feat_cols,
        "train_medians": train_medians,
    }


def predict_global(
    pipeline: dict,
    station_code: int,
    item_code: int,
    prediction_index: pd.DatetimeIndex,
) -> pd.Series:
    """Generate predictions for a specific station/pollutant."""
    model = pipeline["model"]
    epoch = pipeline["epoch"]
    stats = pipeline["stats"]
    feat_cols = pipeline["feat_cols"]

    con = duckdb.connect(DB_PATH, read_only=True)
    coords = con.sql(f"""
        SELECT DISTINCT latitude, longitude
        FROM measurements_clean
        WHERE station_code = {station_code}
        LIMIT 1
    """).fetchone()
    con.close()

    lat, lon = coords[0], coords[1]

    # Build a dummy df for feature generation
    n = len(prediction_index)
    df = pd.DataFrame({
        "measurement_datetime": prediction_index,
        "station_code": station_code,
        "item_code": item_code,
        "clean_value": 0.0,
        "latitude": lat,
        "longitude": lon,
    })

    features = build_global_features(df, epoch)
    features = add_group_stats(features, df, stats)

    X = features[feat_cols].astype(float)
    X = X.fillna(pipeline["train_medians"])

    preds_log = model.predict(X)
    preds = np.maximum(np.expm1(preds_log), 0)

    return pd.Series(preds, index=prediction_index, name="global_lgbm")
