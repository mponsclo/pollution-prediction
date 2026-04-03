"""Feature engineering for production-ready time-series forecasting.

Features are designed for direct (non-recursive) prediction over 720+ hour horizons.
No feature depends on predicted values — only on the training history and the
target datetime.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Fourier features
# ---------------------------------------------------------------------------

def add_fourier_features(
    index: pd.DatetimeIndex,
    epoch: pd.Timestamp,
) -> pd.DataFrame:
    """Multi-scale Fourier features for hourly data.

    Uses hours-since-epoch so features are consistent between train and future.
    """
    t = (index - epoch).total_seconds() / 3600.0  # hours since epoch

    periods = {"daily": 24, "weekly": 168, "yearly": 8766}
    n_terms = {"daily": 4, "weekly": 3, "yearly": 5}

    cols = {}
    for name, period in periods.items():
        for k in range(1, n_terms[name] + 1):
            cols[f"four_{name}_sin_{k}"] = np.sin(2 * np.pi * k * t / period)
            cols[f"four_{name}_cos_{k}"] = np.cos(2 * np.pi * k * t / period)

    return pd.DataFrame(cols, index=index)


# ---------------------------------------------------------------------------
# Target encoding with Bayesian smoothing
# ---------------------------------------------------------------------------

def compute_target_encodings(
    train_series: pd.Series,
    smoothing: float = 10.0,
) -> dict:
    """Compute target encoding stats from training data.

    Returns a dict of lookup tables for hour, dow, month, hour×dow, month×hour.
    """
    idx = train_series.index
    global_mean = train_series.mean()

    groups = {
        "hour": idx.hour,
        "dow": idx.dayofweek,
        "month": idx.month,
    }

    stats = {"global_mean": global_mean}

    # Single-key encodings
    for name, keys in groups.items():
        grp = train_series.groupby(keys)
        means = grp.mean()
        counts = grp.count()
        weight = counts / (counts + smoothing)
        stats[f"enc_{name}"] = (weight * means + (1 - weight) * global_mean).to_dict()

    # Composite encodings: hour×dow
    grp = train_series.groupby([idx.hour, idx.dayofweek])
    means = grp.mean()
    counts = grp.count()
    weight = counts / (counts + smoothing)
    stats["enc_hour_dow"] = (weight * means + (1 - weight) * global_mean).to_dict()

    # month×hour
    grp = train_series.groupby([idx.month, idx.hour])
    means = grp.mean()
    counts = grp.count()
    weight = counts / (counts + smoothing)
    stats["enc_month_hour"] = (weight * means + (1 - weight) * global_mean).to_dict()

    return stats


def apply_target_encodings(
    index: pd.DatetimeIndex,
    enc_stats: dict,
) -> pd.DataFrame:
    """Apply pre-computed target encodings to a datetime index."""
    gm = enc_stats["global_mean"]
    df = pd.DataFrame(index=index)

    df["enc_hour"] = pd.Series(index.hour, index=index).map(enc_stats["enc_hour"]).fillna(gm)
    df["enc_dow"] = pd.Series(index.dayofweek, index=index).map(enc_stats["enc_dow"]).fillna(gm)
    df["enc_month"] = pd.Series(index.month, index=index).map(enc_stats["enc_month"]).fillna(gm)

    # Composite keys
    hour_dow_keys = list(zip(index.hour, index.dayofweek))
    df["enc_hour_dow"] = pd.Series(hour_dow_keys, index=index).map(enc_stats["enc_hour_dow"]).fillna(gm)

    month_hour_keys = list(zip(index.month, index.hour))
    df["enc_month_hour"] = pd.Series(month_hour_keys, index=index).map(enc_stats["enc_month_hour"]).fillna(gm)

    return df


# ---------------------------------------------------------------------------
# Anchor lags and last-window statistics
# ---------------------------------------------------------------------------

def compute_anchor_lags(
    train_series: pd.Series,
    prediction_index: pd.DatetimeIndex,
    lag_hours: tuple[int, ...] = (168, 336, 504, 720),
) -> pd.DataFrame:
    """Compute anchor lags from training data for future predictions.

    Anchor lags reference actual values at fixed offsets (1w, 2w, 3w, 30d ago)
    from each prediction timestamp. Only uses training data — no recursion.
    """
    cols = {}
    for lag in lag_hours:
        lookback = prediction_index - pd.Timedelta(hours=lag)
        values = train_series.reindex(lookback)
        cols[f"anchor_lag_{lag}h"] = values.values

    return pd.DataFrame(cols, index=prediction_index)


def compute_last_window_stats(
    train_series: pd.Series,
    windows: tuple[int, ...] = (24, 168, 720),
) -> dict:
    """Compute aggregate statistics from the tail of the training series."""
    stats = {}
    for w in windows:
        tail = train_series.iloc[-w:]
        stats[f"last_{w}h_mean"] = tail.mean()
        stats[f"last_{w}h_std"] = tail.std()
        stats[f"last_{w}h_min"] = tail.min()
        stats[f"last_{w}h_max"] = tail.max()
    return stats


# ---------------------------------------------------------------------------
# Full feature pipeline
# ---------------------------------------------------------------------------

FEATURE_COLS = None  # set dynamically


def build_train_features(
    train_series: pd.Series,
    target_col: str = "clean_value",
) -> tuple[pd.DataFrame, dict]:
    """Build features for training data.

    Returns (feature_df, context) where context holds everything needed to
    build features for future predictions.
    """
    idx = train_series.index
    epoch = idx.min()

    # 1. Temporal
    df = pd.DataFrame(index=idx)
    df["hour"] = idx.hour
    df["day_of_week"] = idx.dayofweek
    df["month"] = idx.month
    df["day_of_year"] = idx.dayofyear
    df["is_weekend"] = (idx.dayofweek >= 5).astype(int)

    # 2. Cyclical (basic)
    df["hour_sin"] = np.sin(2 * np.pi * idx.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * idx.hour / 24)
    df["dow_sin"] = np.sin(2 * np.pi * idx.dayofweek / 7)
    df["dow_cos"] = np.cos(2 * np.pi * idx.dayofweek / 7)
    df["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    df["month_cos"] = np.cos(2 * np.pi * idx.month / 12)

    # 3. Fourier (multi-scale)
    fourier = add_fourier_features(idx, epoch)
    df = pd.concat([df, fourier], axis=1)

    # 4. Target encoding
    enc_stats = compute_target_encodings(train_series)
    enc_df = apply_target_encodings(idx, enc_stats)
    df = pd.concat([df, enc_df], axis=1)

    # 5. Anchor lags (for training: use shifted values from the series itself)
    for lag in (168, 336, 504, 720):
        df[f"anchor_lag_{lag}h"] = train_series.shift(lag).values

    # 6. Rolling stats from recent history (shifted to prevent leakage)
    for w in (24, 168):
        df[f"rolling_mean_{w}h"] = train_series.shift(1).rolling(w, min_periods=1).mean().values
        df[f"rolling_std_{w}h"] = train_series.shift(1).rolling(w, min_periods=1).std().values

    # Store context for prediction
    context = {
        "epoch": epoch,
        "enc_stats": enc_stats,
        "train_series": train_series,
        "last_window_stats": compute_last_window_stats(train_series),
    }

    return df, context


def build_prediction_features(
    prediction_index: pd.DatetimeIndex,
    context: dict,
    horizon_steps: np.ndarray | None = None,
) -> pd.DataFrame:
    """Build features for future predictions using stored context."""
    idx = prediction_index
    epoch = context["epoch"]
    train_series = context["train_series"]
    enc_stats = context["enc_stats"]
    lw = context["last_window_stats"]

    # 1. Temporal
    df = pd.DataFrame(index=idx)
    df["hour"] = idx.hour
    df["day_of_week"] = idx.dayofweek
    df["month"] = idx.month
    df["day_of_year"] = idx.dayofyear
    df["is_weekend"] = (idx.dayofweek >= 5).astype(int)

    # 2. Cyclical
    df["hour_sin"] = np.sin(2 * np.pi * idx.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * idx.hour / 24)
    df["dow_sin"] = np.sin(2 * np.pi * idx.dayofweek / 7)
    df["dow_cos"] = np.cos(2 * np.pi * idx.dayofweek / 7)
    df["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    df["month_cos"] = np.cos(2 * np.pi * idx.month / 12)

    # 3. Fourier
    fourier = add_fourier_features(idx, epoch)
    df = pd.concat([df, fourier], axis=1)

    # 4. Target encoding
    enc_df = apply_target_encodings(idx, enc_stats)
    df = pd.concat([df, enc_df], axis=1)

    # 5. Anchor lags (from actual training data)
    anchor = compute_anchor_lags(train_series, idx)
    df = pd.concat([df, anchor], axis=1)

    # 6. Last-window stats (constant for all prediction rows)
    for w in (24, 168):
        df[f"rolling_mean_{w}h"] = lw[f"last_{w}h_mean"]
        df[f"rolling_std_{w}h"] = lw[f"last_{w}h_std"]

    # 7. Horizon step (if provided)
    if horizon_steps is not None:
        df["horizon_step"] = horizon_steps

    return df


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """Return all feature column names from a feature DataFrame."""
    return list(df.columns)


# ---------------------------------------------------------------------------
# Cross-station spatial features
# ---------------------------------------------------------------------------

def compute_spatial_features(
    station_code: int,
    item_code: int,
    train_index: pd.DatetimeIndex,
    db_path: str | None = None,
    k_neighbors: int = 5,
) -> tuple[pd.DataFrame, dict]:
    """Compute IDW-weighted spatial features from neighboring stations.

    Returns (feature_df, spatial_context) for use on future timestamps.
    """
    import duckdb
    from src.utils.constants import DB_PATH

    path = db_path or DB_PATH
    con = duckdb.connect(path, read_only=True)

    # Get all stations with coordinates
    stations = con.sql("""
        SELECT DISTINCT station_code, latitude, longitude
        FROM measurements_clean
        ORDER BY station_code
    """).df()

    # Get target station coords
    target_row = stations[stations["station_code"] == station_code].iloc[0]
    target_lat, target_lon = target_row["latitude"], target_row["longitude"]

    # Compute distances, find k nearest
    other = stations[stations["station_code"] != station_code].copy()
    other["dist"] = np.sqrt(
        (other["latitude"] - target_lat) ** 2 +
        (other["longitude"] - target_lon) ** 2
    )
    neighbors = other.nsmallest(k_neighbors, "dist")
    neighbor_codes = neighbors["station_code"].tolist()
    dists = neighbors["dist"].values
    idw_weights = (1.0 / np.maximum(dists, 1e-6) ** 2)
    idw_weights /= idw_weights.sum()

    # Load neighbor series for the same pollutant
    placeholders = ",".join(str(c) for c in neighbor_codes)
    neighbor_data = con.sql(f"""
        SELECT measurement_datetime, station_code, clean_value
        FROM measurements_clean
        WHERE item_code = {item_code}
          AND station_code IN ({placeholders})
          AND instrument_status = 0
          AND clean_value IS NOT NULL
        ORDER BY measurement_datetime
    """).df()
    con.close()

    neighbor_data["measurement_datetime"] = pd.to_datetime(neighbor_data["measurement_datetime"])

    # Pivot: rows=timestamps, cols=stations
    pivot = neighbor_data.pivot_table(
        index="measurement_datetime",
        columns="station_code",
        values="clean_value",
    )
    pivot = pivot.reindex(train_index).ffill().bfill()

    # Compute spatial features
    df = pd.DataFrame(index=train_index)

    # IDW-weighted mean of neighbors
    for i, (nc, w) in enumerate(zip(neighbor_codes, idw_weights)):
        if nc in pivot.columns:
            df[f"_n{i}"] = pivot[nc].values * w
    neighbor_cols = [c for c in df.columns if c.startswith("_n")]
    df["spatial_idw_mean"] = df[neighbor_cols].sum(axis=1)
    df.drop(columns=neighbor_cols, inplace=True)

    # Spatial std across neighbors
    if len(pivot.columns) > 1:
        df["spatial_std"] = pivot.std(axis=1).values

    # Spatial context for prediction
    spatial_ctx = {
        "neighbor_codes": neighbor_codes,
        "idw_weights": idw_weights,
        "item_code": item_code,
    }

    return df, spatial_ctx


def compute_spatial_features_for_prediction(
    prediction_index: pd.DatetimeIndex,
    spatial_ctx: dict,
    db_path: str | None = None,
) -> pd.DataFrame:
    """Compute spatial features for future timestamps from latest neighbor data."""
    import duckdb
    from src.utils.constants import DB_PATH

    path = db_path or DB_PATH
    con = duckdb.connect(path, read_only=True)

    neighbor_codes = spatial_ctx["neighbor_codes"]
    idw_weights = spatial_ctx["idw_weights"]
    item_code = spatial_ctx["item_code"]

    placeholders = ",".join(str(c) for c in neighbor_codes)
    neighbor_data = con.sql(f"""
        SELECT measurement_datetime, station_code, clean_value
        FROM measurements_clean
        WHERE item_code = {item_code}
          AND station_code IN ({placeholders})
          AND instrument_status = 0
          AND clean_value IS NOT NULL
        ORDER BY measurement_datetime
    """).df()
    con.close()

    neighbor_data["measurement_datetime"] = pd.to_datetime(neighbor_data["measurement_datetime"])
    pivot = neighbor_data.pivot_table(
        index="measurement_datetime", columns="station_code", values="clean_value"
    )

    # For future timestamps, use last known values per neighbor (grouped by hour)
    df = pd.DataFrame(index=prediction_index)

    # Compute per-hour means from neighbor history for lookup
    pivot_hourly = pivot.groupby(pivot.index.hour).mean()

    weighted_vals = np.zeros(len(prediction_index))
    for nc, w in zip(neighbor_codes, idw_weights):
        if nc in pivot_hourly.columns:
            hourly_lookup = pivot_hourly[nc].to_dict()
            vals = pd.Series(prediction_index.hour, index=prediction_index).map(hourly_lookup).fillna(0)
            weighted_vals += vals.values * w

    df["spatial_idw_mean"] = weighted_vals

    if len(pivot.columns) > 1:
        hourly_std = pivot.groupby(pivot.index.hour).std().mean(axis=1)
        df["spatial_std"] = pd.Series(prediction_index.hour, index=prediction_index).map(hourly_std.to_dict()).fillna(0)

    return df
