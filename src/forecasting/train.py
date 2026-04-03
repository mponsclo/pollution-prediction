"""Training pipeline for time-series forecasting."""

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.forecasting.features import build_features, get_feature_columns


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
            # Fallback to mean of same hour
            same_hour = full[full.index.hour == dt.hour]
            predictions.append(same_hour.mean() if len(same_hour) > 0 else full.mean())

    return pd.Series(predictions, index=prediction_index, name="seasonal_naive")


def train_xgboost(
    train_df: pd.DataFrame,
    target_col: str = "clean_value",
) -> tuple[XGBRegressor, list[str]]:
    """Train an XGBoost model on the feature-engineered training data."""
    df = build_features(train_df)
    feature_cols = get_feature_columns(df)

    # Drop rows with NaN in features (from lag/rolling calculations)
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

    # Use last 10% as eval set for early stopping
    split_idx = int(len(X) * 0.9)
    X_train, X_eval = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_eval = y.iloc[:split_idx], y.iloc[split_idx:]

    model.fit(
        X_train, y_train,
        eval_set=[(X_eval, y_eval)],
        verbose=False,
    )

    return model, feature_cols


def predict_recursive(
    model: XGBRegressor,
    train_df: pd.DataFrame,
    prediction_index: pd.DatetimeIndex,
    feature_cols: list[str],
    target_col: str = "clean_value",
) -> pd.Series:
    """Generate predictions recursively (each prediction feeds into the next)."""
    # Start with a copy of training data
    history = train_df[[target_col]].copy()
    predictions = []

    for dt in prediction_index:
        # Append prediction point
        history.loc[dt] = np.nan

        # Build features for the full history
        featured = build_features(history)

        # Get features for current timestamp
        row = featured.loc[[dt], feature_cols]

        # Predict
        pred = model.predict(row)[0]
        pred = max(pred, 0)  # Pollutant values can't be negative

        # Store prediction and update history for next iteration
        predictions.append(pred)
        history.loc[dt, target_col] = pred

    return pd.Series(predictions, index=prediction_index, name="xgboost")
