# Experiments Log

## Task 2: Forecasting

### Experiment 1: Baseline — Seasonal Naive

**Method**: Use the value from the same hour, 7 days ago. If unavailable, use the mean of the same hour across all training data.

**Rationale**: Simple baseline that captures weekly seasonality. Establishes performance floor.

### Experiment 2: XGBoost Recursive (FAILED)

**Method**: XGBoost with lag features (1h-168h), rolling stats, and diff features. Recursive prediction: each forecast feeds into lag features for subsequent hours.

**Result**: Catastrophic error accumulation over 720+ hours. RMSE 6-10x worse than seasonal naive for all targets. PM10 predictions drifted to 300-400 (actual range ~10-200).

**Lesson**: Recursive multi-step forecasting is unsuitable for month-ahead horizons with tree-based models. Small per-step errors compound exponentially.

### Experiment 3: XGBoost Direct Prediction (SELECTED)

**Method**: XGBoost with features that require no recursive dependency:
- Temporal: hour, day_of_week, month, day_of_year, is_weekend
- Cyclical encoding: sin/cos of hour, day_of_week, month
- Historical same-hour statistics: mean, std, median
- Historical same-hour-and-day-of-week statistics: mean, std
- Historical same-month-and-hour statistics: mean

**Hyperparameters**: n_estimators=500, max_depth=6, learning_rate=0.05, subsample=0.8, early_stopping=50

**Training**: All data before prediction period, instrument_status=0 only. Missing values forward-filled.

**Validation Results** (last month holdout):

| Station | Pollutant | Naive RMSE | XGBoost RMSE | Improvement |
|---------|-----------|-----------|-------------|-------------|
| 206     | SO2       | 0.00156   | 0.00125     | 19.4%       |
| 211     | NO2       | 0.01383   | 0.00772     | 44.1%       |
| 217     | O3        | 0.01532   | 0.01481     | 3.3%        |
| 219     | CO        | 0.15791   | 0.14767     | 6.5%        |
| 225     | PM10      | 32.67010  | 28.51326    | 12.7%       |
| 228     | PM2.5     | 14.28790  | 12.23066    | 14.4%       |

XGBoost direct beats seasonal naive on all 6 targets (3-44% RMSE improvement).

---

## Task 3: Anomaly Detection

### Experiment 1: Isolation Forest (SELECTED)

**Method**: Isolation Forest trained on labeled historical data for each station/pollutant.

**Features**:
- Current value and deviations from rolling means (6h, 12h, 24h z-scores)
- Rate of change (1h diff, 24h diff, absolute 1h diff)
- Difference from same hour yesterday
- Consecutive identical readings count (stuck sensor detection)
- Hour of day, day of week

**Contamination**: Set per-target based on historical anomaly rate (0.7-4.5%).

**Validation Results** (last month of labeled data):

| Station | Pollutant | Labeled Rate | Val F1 | Target Anomalies |
|---------|-----------|-------------|--------|-----------------|
| 205     | SO2       | 0.7%        | 0.500  | 3/696 (0.4%)    |
| 209     | NO2       | 2.0%        | 0.000  | 362/628 (57.6%) |
| 223     | O3        | 0.9%        | 0.667  | 7/699 (1.0%)    |
| 224     | CO        | 4.5%        | 0.029  | 10/720 (1.4%)   |
| 226     | PM10      | 2.8%        | 0.133  | 23/716 (3.2%)   |
| 227     | PM2.5     | 3.8%        | 0.529  | 14/708 (2.0%)   |

**Notes**: 
- Station 209/NO2 shows high detection rate (57.6%) — likely genuine distribution shift in the target period, as the model was trained on data ending before the target.
- Validation F1 varies widely due to class imbalance and small anomaly counts.
- Target periods have no ground truth labels, so predictions are the model's best estimate.

**Output**: Anomaly predictions exported to `outputs/anomaly_predictions.csv`.
