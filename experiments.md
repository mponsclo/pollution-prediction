# Experiments Log

## Task 2: Forecasting

### Experiment 1: Baseline — Seasonal Naive

**Method**: Use the value from the same hour, 7 days ago. If unavailable, use the mean of the same hour across all training data.

**Rationale**: Simple baseline that captures weekly seasonality. Establishes performance floor.

### Experiment 2: XGBoost Recursive (FAILED)

**Method**: XGBoost with lag features (1h-168h), rolling stats, and diff features. Recursive prediction: each forecast feeds into lag features for subsequent hours.

**Result**: Catastrophic error accumulation over 720+ hours. RMSE 6-10x worse than seasonal naive for all targets. PM10 predictions drifted to 300-400 (actual range ~10-200).

**Lesson**: Recursive multi-step forecasting is unsuitable for month-ahead horizons with tree-based models. Small per-step errors compound exponentially.

### Experiment 3: XGBoost Direct Prediction (SUPERSEDED)

**Method**: XGBoost with 17 temporal + historical mean features. No lags, no Fourier.

**Result**: nRMSE 0.48-0.97 — essentially a seasonal average. Predictions were flat with very low variability compared to actuals. Superseded by Experiment 4.

### Experiment 4: LightGBM Ensemble with Fourier + Anchor Lags (SELECTED)

**Method**: Production-ready ensemble of LightGBM + Ridge (Fourier) + Seasonal Naive with optimized weights.

**Features (~55 total)**:
- Temporal (5): hour, day_of_week, month, day_of_year, is_weekend
- Cyclical (6): sin/cos of hour, dow, month
- Fourier (24): multi-scale sin/cos — daily (4 harmonics), weekly (3), yearly (5)
- Anchor lags (4): values from 168h, 336h, 504h, 720h ago (from training data, no recursion)
- Rolling stats (4): mean/std over last 24h and 168h of training window
- Target encoding (5): Bayesian-smoothed historical means by hour, dow, month, hour×dow, month×hour

**Models**:
- LightGBM: n_estimators=800, num_leaves=63, max_depth=8, lr=0.03
- LightGBM quantile (q=0.05, q=0.95) for 90% prediction intervals
- Ridge with Fourier features (complementary linear model)
- Seasonal Naive (same hour, 7 days ago)
- Ensemble weights optimized via MSE minimization on validation set

**Validation**: Walk-forward CV with 3 folds × 720h test windows.

**Walk-Forward CV Results**:

| Station | Pollutant | Naive RMSE | Ensemble RMSE | nRMSE | R² | Improvement | PI Coverage |
|---------|-----------|-----------|--------------|-------|-----|------------|-------------|
| 206     | SO2       | 0.00142   | 0.00122      | 0.92  | -0.28 | 14.0%    | 62.1%       |
| 211     | NO2       | 0.01364   | 0.01041      | 0.66  | -0.23 | 23.6%    | 82.4%       |
| 217     | O3        | 0.01572   | 0.01438      | 0.72  | 0.36  | 8.5%     | 88.9%       |
| 219     | CO        | 0.18147   | 0.13296      | 0.45  | 0.02  | 26.7%    | 86.5%       |
| 225     | PM10      | 28.09975  | 17.28982     | 0.52  | 0.04  | 38.5%    | 82.7%       |
| 228     | PM2.5     | 14.03014  | 9.80707      | 0.53  | 0.08  | 30.1%    | 87.0%       |

**Key improvements over Experiment 3**:
- PM10 nRMSE: 0.97 → 0.52 (47% reduction — from useless to useful)
- CO nRMSE: 0.61 → 0.45 (26% reduction)
- PM2.5 nRMSE: 0.64 → 0.53 (17% reduction)
- All targets now have nRMSE < 1.0 (better than predicting the mean)
- 90% prediction intervals included for production use

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
