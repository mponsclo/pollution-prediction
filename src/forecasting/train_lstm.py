"""LSTM encoder-decoder for hourly pollution forecasting.

Uses a "direct" strategy: the encoder processes a lookback window of actual
values, then a decoder head predicts each future hour independently using
the encoder's context + temporal features. No recursion — no error accumulation.

Experiment 6.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset

from src.forecasting.features import add_fourier_features

# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class PollutionDataset(Dataset):
    """Creates (lookback_window, temporal_features, target) samples.

    Each sample:
      - lookback: last `window` hours of (scaled, log1p) values
      - temporal: Fourier + calendar features for the target hour
      - target: log1p(value) at the target hour
    """

    def __init__(
        self,
        series: np.ndarray,
        timestamps: pd.DatetimeIndex,
        epoch: pd.Timestamp,
        window: int = 168,
    ):
        self.window = window
        self.series = series  # already log1p transformed
        self.n_temporal = self._build_temporal(timestamps[0:1], epoch).shape[1]

        # Pre-compute all temporal features
        self.temporal = self._build_temporal(timestamps, epoch)

        # Valid indices: any position where we have a full lookback window
        self.valid_indices = list(range(window, len(series)))

    def _build_temporal(self, idx: pd.DatetimeIndex, epoch: pd.Timestamp) -> np.ndarray:
        """Build temporal features for given timestamps."""
        fourier = add_fourier_features(idx, epoch)
        fourier["hour"] = idx.hour / 23.0  # normalize to [0, 1]
        fourier["dow"] = idx.dayofweek / 6.0
        fourier["month"] = (idx.month - 1) / 11.0
        fourier["day_of_year"] = (idx.dayofyear - 1) / 365.0
        return fourier.values.astype(np.float32)

    def __len__(self):
        return len(self.valid_indices)

    def __getitem__(self, idx):
        t = self.valid_indices[idx]
        lookback = self.series[t - self.window : t].astype(np.float32)
        temporal = self.temporal[t]
        target = np.float32(self.series[t])
        return (
            torch.tensor(lookback).unsqueeze(-1),  # (window, 1)
            torch.tensor(temporal),  # (n_temporal,)
            torch.tensor(target),  # scalar
        )


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class LSTMForecaster(nn.Module):
    """Encoder-decoder LSTM: encodes lookback window, decodes with temporal context."""

    def __init__(
        self,
        hidden_size: int = 64,
        num_layers: int = 2,
        n_temporal: int = 28,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.encoder = nn.LSTM(
            input_size=1,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
        )
        self.decoder = nn.Sequential(
            nn.Linear(hidden_size + n_temporal, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(self, lookback: torch.Tensor, temporal: torch.Tensor) -> torch.Tensor:
        # lookback: (batch, window, 1)
        # temporal: (batch, n_temporal)
        _, (h_n, _) = self.encoder(lookback)
        context = h_n[-1]  # last layer's hidden state: (batch, hidden)
        combined = torch.cat([context, temporal], dim=1)
        return self.decoder(combined).squeeze(-1)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def train_lstm_model(
    train_series: pd.Series,
    val_series: pd.Series | None = None,
    window: int = 48,
    hidden_size: int = 32,
    num_layers: int = 1,
    epochs: int = 30,
    batch_size: int = 512,
    lr: float = 0.001,
    patience: int = 7,
    max_train_hours: int = 8760,  # use last year only
) -> dict:
    """Train the LSTM forecaster.

    Args:
        train_series: Series with datetime index and clean_value values.
        val_series: Optional validation series for early stopping.
        window: Lookback window in hours.

    Returns:
        dict with model, scaler, epoch, and training metadata.
    """
    device = torch.device("cpu")

    # Use only last N hours for training (recency > volume per M5 findings)
    if len(train_series) > max_train_hours:
        train_series_trimmed = train_series.iloc[-max_train_hours:]
    else:
        train_series_trimmed = train_series

    # Log1p transform
    train_log = np.log1p(train_series_trimmed.values)
    epoch_ts = train_series.index.min()  # keep original epoch for Fourier consistency

    # Scale the log-transformed values
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_log.reshape(-1, 1)).ravel()

    # Create dataset
    train_ds = PollutionDataset(train_scaled, train_series_trimmed.index, epoch_ts, window)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    # Validation dataset
    val_loader = None
    if val_series is not None:
        combined = pd.concat([train_series_trimmed.iloc[-window:], val_series])
        combined_log = np.log1p(combined.values)
        combined_scaled = scaler.transform(combined_log.reshape(-1, 1)).ravel()
        val_ds = PollutionDataset(combined_scaled, combined.index, epoch_ts, window)
        val_ds.valid_indices = list(range(window, len(combined_scaled)))
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # Model
    n_temporal = train_ds.n_temporal
    model = LSTMForecaster(hidden_size, num_layers, n_temporal).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    # Training loop with early stopping
    best_val_loss = float("inf")
    best_state = None
    epochs_no_improve = 0

    for ep in range(epochs):
        model.train()
        train_loss = 0.0
        n_batches = 0
        for lookback, temporal, target in train_loader:
            lookback, temporal, target = (lookback.to(device), temporal.to(device), target.to(device))
            optimizer.zero_grad()
            pred = model(lookback, temporal)
            loss = criterion(pred, target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item()
            n_batches += 1

        # Validation
        if val_loader is not None:
            model.eval()
            val_loss = 0.0
            n_val = 0
            with torch.no_grad():
                for lookback, temporal, target in val_loader:
                    lookback, temporal, target = (lookback.to(device), temporal.to(device), target.to(device))
                    pred = model(lookback, temporal)
                    val_loss += criterion(pred, target).item()
                    n_val += 1

            avg_val = val_loss / max(n_val, 1)

            if avg_val < best_val_loss:
                best_val_loss = avg_val
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                epochs_no_improve = 0
            else:
                epochs_no_improve += 1

            if epochs_no_improve >= patience:
                break
        else:
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    # Load best model
    if best_state is not None:
        model.load_state_dict(best_state)

    return {
        "model": model,
        "scaler": scaler,
        "epoch_ts": epoch_ts,
        "window": window,
        "n_temporal": n_temporal,
        "hidden_size": hidden_size,
        "num_layers": num_layers,
        "train_series": train_series,
    }


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


def predict_lstm(
    pipeline: dict,
    prediction_index: pd.DatetimeIndex,
) -> pd.Series:
    """Generate predictions for future timestamps."""
    model = pipeline["model"]
    scaler = pipeline["scaler"]
    epoch_ts = pipeline["epoch_ts"]
    window = pipeline["window"]
    train_series = pipeline["train_series"]
    device = torch.device("cpu")

    model.eval()

    # Get the last `window` hours of training data as lookback seed
    train_log = np.log1p(train_series.values)
    train_scaled = scaler.transform(train_log.reshape(-1, 1)).ravel()
    seed = train_scaled[-window:]

    # Build temporal features for all prediction timestamps
    fourier = add_fourier_features(prediction_index, epoch_ts)
    fourier["hour"] = prediction_index.hour / 23.0
    fourier["dow"] = prediction_index.dayofweek / 6.0
    fourier["month"] = (prediction_index.month - 1) / 11.0
    fourier["day_of_year"] = (prediction_index.dayofyear - 1) / 365.0
    temporal_all = torch.tensor(fourier.values.astype(np.float32)).to(device)

    # Predict each hour using the SAME lookback seed (direct, no recursion)
    lookback_tensor = torch.tensor(seed.astype(np.float32)).unsqueeze(0).unsqueeze(-1).to(device)
    # (1, window, 1)

    predictions = []
    with torch.no_grad():
        for i in range(len(prediction_index)):
            temporal_i = temporal_all[i : i + 1]  # (1, n_temporal)
            pred_scaled = model(lookback_tensor, temporal_i).item()

            # Inverse transform: unscale → expm1
            pred_log = scaler.inverse_transform([[pred_scaled]])[0, 0]
            pred = np.expm1(max(pred_log, 0))
            predictions.append(max(pred, 0))

    return pd.Series(predictions, index=prediction_index, name="lstm")


# ---------------------------------------------------------------------------
# Full pipeline (matches interface of train_lgbm_ensemble)
# ---------------------------------------------------------------------------


def train_lstm_pipeline(
    train_series: pd.Series,
    val_series: pd.Series | None = None,
    **kwargs,
) -> dict:
    """Train LSTM pipeline with same interface as LightGBM pipeline."""
    return train_lstm_model(train_series, val_series, **kwargs)
