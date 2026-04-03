# Experiments Log

## Task 2: Forecasting

### Experiment 1: Baseline — Seasonal Naive

**Method**: Use the value from the same hour, 7 days ago. If unavailable, use the mean of the same hour across all training data.

**Rationale**: Simple baseline that captures weekly seasonality. Establishes performance floor.

*Results pending — will be populated after running the pipeline.*

### Experiment 2: XGBoost with time-series features

**Method**: XGBoost regressor with the following feature groups:
- Temporal: hour, day_of_week, month, day_of_year, is_weekend
- Cyclical encoding: sin/cos of hour (24h), day_of_week (7d), month (12m)
- Lag features: 1h, 2h, 3h, 6h, 12h, 24h, 48h, 168h (1 week)
- Rolling statistics: mean/std over 6h, 12h, 24h, 168h windows
- Diff features: 1h and 24h differences

**Hyperparameters**: n_estimators=500, max_depth=6, learning_rate=0.05, subsample=0.8, early_stopping_rounds=50

**Training**: All data before prediction period, normal status only.

**Prediction strategy**: Recursive — each prediction feeds into lag features for subsequent predictions.

*Results pending.*

---

## Task 3: Anomaly Detection

### Experiment 1: Isolation Forest

*Details and results pending.*

### Experiment 2: Residual-based detection

*Details and results pending.*
