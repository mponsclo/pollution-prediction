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
