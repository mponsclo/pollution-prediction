"""Training pipeline for time-series forecasting."""

import numpy as np
import pandas as pd
from xgboost import XGBRegressor


def seasonal_naive_predict(
    train_df: pd.DataFrame,
    prediction_index: pd.DatetimeIndex,
    col: str = "clean_value",
    period: int = 168,  # 7 days in hours
) -> pd.Series:
    """Baseline: use value from same hour, 7 days ago."""
    predictions = []
    full = train_df[col].copy()

    for dt in prediction_index:
        lookback = dt - pd.Timedelta(hours=period)
        if lookback in full.index:
            predictions.append(full.loc[lookback])
        else:
            same_hour = full[full.index.hour == dt.hour]
            predictions.append(same_hour.mean() if len(same_hour) > 0 else full.mean())

    return pd.Series(predictions, index=prediction_index, name="seasonal_naive")


def build_direct_features(train_df: pd.DataFrame, col: str = "clean_value") -> pd.DataFrame:
    """Build features for direct prediction (no recursive dependency).

    These features can be computed for any future datetime without knowing
    intermediate predictions, avoiding error accumulation.
    """
    df = train_df[[col]].copy()
    idx = df.index

    # Temporal features
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

    # Historical same-hour statistics (computed from the training set)
    hourly_stats = df.groupby("hour")[col].agg(["mean", "std", "median"]).rename(
        columns={"mean": "hour_mean", "std": "hour_std", "median": "hour_median"}
    )
    df = df.merge(hourly_stats, left_on="hour", right_index=True, how="left")

    # Historical same-hour-and-dow statistics
    hour_dow_stats = df.groupby(["hour", "day_of_week"])[col].agg(["mean", "std"]).rename(
        columns={"mean": "hour_dow_mean", "std": "hour_dow_std"}
    )
    df = df.merge(hour_dow_stats, left_on=["hour", "day_of_week"], right_index=True, how="left")

    # Historical same-month-and-hour statistics
    month_hour_stats = df.groupby(["month", "hour"])[col].agg(["mean"]).rename(
        columns={"mean": "month_hour_mean"}
    )
    df = df.merge(month_hour_stats, left_on=["month", "hour"], right_index=True, how="left")

    return df


def get_direct_feature_cols() -> list[str]:
    """Return feature column names for direct prediction."""
    return [
        "hour", "day_of_week", "month", "day_of_year", "is_weekend",
        "hour_sin", "hour_cos", "dow_sin", "dow_cos", "month_sin", "month_cos",
        "hour_mean", "hour_std", "hour_median",
        "hour_dow_mean", "hour_dow_std",
        "month_hour_mean",
    ]


def train_xgboost_direct(
    train_df: pd.DataFrame,
    target_col: str = "clean_value",
) -> tuple[XGBRegressor, dict]:
    """Train XGBoost with direct features (no lag dependencies).

    Returns the model and the historical statistics needed for prediction.
    """
    df = build_direct_features(train_df, target_col)
    feature_cols = get_direct_feature_cols()

    df_clean = df.dropna(subset=feature_cols + [target_col])
    X = df_clean[feature_cols]
    y = df_clean[target_col]

    model = XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        early_stopping_rounds=50,
        random_state=42,
        n_jobs=-1,
    )

    split_idx = int(len(X) * 0.9)
    X_train, X_eval = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_eval = y.iloc[:split_idx], y.iloc[split_idx:]

    model.fit(
        X_train, y_train,
        eval_set=[(X_eval, y_eval)],
        verbose=False,
    )

    # Store stats for prediction on new data
    stats = {
        "hourly": train_df.groupby(train_df.index.hour)[target_col].agg(["mean", "std", "median"]),
        "hour_dow": train_df.groupby([train_df.index.hour, train_df.index.dayofweek])[target_col].agg(["mean", "std"]),
        "month_hour": train_df.groupby([train_df.index.month, train_df.index.hour])[target_col].agg(["mean"]),
    }

    return model, stats


def predict_direct(
    model: XGBRegressor,
    prediction_index: pd.DatetimeIndex,
    stats: dict,
) -> pd.Series:
    """Generate predictions using direct features (no recursion)."""
    df = pd.DataFrame(index=prediction_index)

    # Temporal features
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["month"] = df.index.month
    df["day_of_year"] = df.index.dayofyear
    df["is_weekend"] = (df.index.dayofweek >= 5).astype(int)

    # Cyclical
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # Historical statistics
    hourly = stats["hourly"]
    df["hour_mean"] = df["hour"].map(hourly["mean"])
    df["hour_std"] = df["hour"].map(hourly["std"])
    df["hour_median"] = df["hour"].map(hourly["median"])

    hour_dow = stats["hour_dow"]
    for i, row in df.iterrows():
        key = (row["hour"], row["day_of_week"])
        if key in hour_dow.index:
            df.loc[i, "hour_dow_mean"] = hour_dow.loc[key, "mean"]
            df.loc[i, "hour_dow_std"] = hour_dow.loc[key, "std"]
        else:
            df.loc[i, "hour_dow_mean"] = hourly.loc[row["hour"], "mean"]
            df.loc[i, "hour_dow_std"] = hourly.loc[row["hour"], "std"]

    month_hour = stats["month_hour"]
    for i, row in df.iterrows():
        key = (row["month"], row["hour"])
        if key in month_hour.index:
            df.loc[i, "month_hour_mean"] = month_hour.loc[key, "mean"]
        else:
            df.loc[i, "month_hour_mean"] = hourly.loc[row["hour"], "mean"]

    feature_cols = get_direct_feature_cols()
    df = df[feature_cols].astype(float)

    preds = model.predict(df)
    preds = np.maximum(preds, 0)  # Pollutant values can't be negative

    return pd.Series(preds, index=prediction_index, name="xgboost_direct")
