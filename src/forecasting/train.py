"""Re-exports from the production LightGBM ensemble pipeline.

This module preserves backward compatibility — notebooks and scripts that
import from `src.forecasting.train` continue to work unchanged.

Individual experiment implementations:
  - train_xgboost.py: Experiment 3 — XGBoost direct prediction
  - train_lgbm_ensemble.py: Experiment 5/7 — LightGBM + CQR + spatial + cross-pollutant (production)
  - train_lstm.py: Experiment 6 — LSTM encoder-decoder
  - train_global.py: Experiment 8 — Global model (all stations × pollutants)
"""

from src.forecasting.train_lgbm_ensemble import (  # noqa: F401
    seasonal_naive_predict,
    train_lgbm,
    train_ridge,
    predict_ridge,
    optimize_weights,
    calibrate_intervals_cqr,
    walk_forward_cv,
    train_forecast_pipeline,
    predict_with_pipeline,
)
