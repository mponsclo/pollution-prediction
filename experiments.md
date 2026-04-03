# Experiments Log

## Task 2: Forecasting

**Goal**: Predict hourly pollutant concentrations for 6 station/pollutant/period combinations, each a full month ahead (720+ hours).

**Validation**: Walk-forward CV with 3 folds × 720h test windows unless noted otherwise.

**Key metric**: nRMSE (RMSE / std). Values < 1.0 mean the model beats predicting the global mean.

---

### Exp 1: Seasonal Naive (BASELINE)

Value from the same hour, 7 days ago. Establishes the performance floor.

### Exp 2: XGBoost Recursive (FAILED)

XGBoost with lag features (1h-168h) and rolling stats. Each prediction feeds back as input for the next.

**Result**: Catastrophic error accumulation over 720+ steps. RMSE 6-10x worse than naive. PM10 predictions drifted to 300-400 (actual range ~10-200).

**Lesson**: Recursive multi-step prediction is unsuitable for month-ahead horizons with tree models.

### Exp 3: XGBoost Direct (SUPERSEDED)

XGBoost with 17 features (temporal + historical means). No lags, no Fourier. Each future hour predicted independently — no recursion.

**Result**: nRMSE 0.48-0.97. Predictions were flat with low variability — essentially a fancy seasonal average.

### Exp 4: LightGBM Ensemble + Fourier (SUPERSEDED)

Ensemble of LightGBM + Ridge (Fourier) + Seasonal Naive with optimized weights. ~55 features: temporal, cyclical, multi-scale Fourier (daily/weekly/yearly), anchor lags (168-720h from training data), rolling stats, Bayesian target encoding.

**Result**: nRMSE 0.45-0.92. Major improvement over Exp 3, especially PM10 (0.97→0.52). But prediction intervals under-covered at 62-89% vs 90% target.

### Exp 5: + Log1p + CQR + Spatial (PRODUCTION MODEL)

Exp 4 plus three production improvements:
1. **Log1p target transform** — stabilizes variance for right-skewed pollutant data
2. **Conformalized Quantile Regression (CQR)** — calibrates intervals to guarantee ≥90% coverage
3. **Cross-station spatial features** — IDW-weighted average of 5 nearest neighbor stations

| Target | Naive nRMSE | Ensemble nRMSE | Improvement | PI Coverage |
|--------|------------|---------------|------------|-------------|
| SO2    | 1.067      | **0.917**     | 14%        | 93.8%       |
| NO2    | 0.867      | **0.712**     | 18%        | 91.7%       |
| O3     | 0.787      | **0.715**     | 9%         | 90.5%       |
| CO     | 0.610      | **0.449**     | 26%        | 93.6%       |
| PM10   | 0.852      | **0.518**     | 39%        | 93.1%       |
| PM2.5  | 0.751      | **0.546**     | 27%        | 93.5%       |

**Why this is the production model**: Best balance of accuracy, calibrated uncertainty, and simplicity. No external API dependencies.

### Exp 6: LSTM Encoder-Decoder (NOT SELECTED)

PyTorch LSTM (1 layer, hidden=32) encodes 48h lookback → context + Fourier features → FC decoder. Direct strategy (no recursion). CPU-only, trained on last year of data.

**Result** (single holdout):

| Target | LSTM nRMSE | LightGBM nRMSE | Winner |
|--------|-----------|---------------|--------|
| SO2    | 0.737     | 0.917         | LSTM   |
| NO2    | 0.639     | 0.712         | LSTM   |
| O3     | 0.907     | 0.715         | LightGBM |
| CO     | 0.633     | 0.449         | LightGBM |
| PM10   | 1.513     | 0.518         | LightGBM |
| PM2.5  | 0.718     | 0.546         | LightGBM |

LSTM wins 2/6 on single holdout but loses decisively on PM10/CO. Limited by small dataset, CPU training, and inability to leverage 57 engineered features.

### Exp 7: Cross-Pollutant Features (MIXED)

Add other pollutants' anchor lags (168h, 336h) and rolling means as features. Motivated by strong correlations: CO↔NO2 (0.78), PM10↔PM2.5 (0.84).

**Result** (single holdout): Helps NO2 (-8.3% nRMSE via CO correlation) but hurts PM10 (+61.5%) and PM2.5 (+25.5%). Selectively useful — enabled only for NO2 in Exp 9.

### Exp 8: Global Model (NOT SELECTED)

Single LightGBM trained on 500K rows across all 25 stations × 6 pollutants. Station and pollutant codes as features.

**Result** (single holdout): Worse than naive on 4/6 targets. Only PM2.5 improves (0.64 vs 0.77 naive). The model can't specialize per-series when pollutant types are too diverse.

### Exp 9: Weather + Cross-Pollutant NO2 (NOT SELECTED)

Hourly weather from Open-Meteo API (temperature, humidity, pressure, wind, precipitation, cloud cover, radiation). IDW-interpolated from 3 Seoul weather points. Cross-pollutant features enabled for NO2 only.

**Walk-Forward CV Results (definitive)**:

| Target | No Weather | + Weather | Delta |
|--------|-----------|----------|-------|
| SO2    | 0.917     | 0.917    | 0.0%  |
| NO2    | 0.712     | 0.708    | -0.6% |
| O3     | 0.715     | 0.713    | -0.3% |
| CO     | 0.449     | 0.448    | -0.2% |
| PM10   | 0.518     | 0.520    | +0.4% |
| PM2.5  | 0.546     | 0.544    | -0.4% |

**Conclusion**: Negligible improvement (0.0-0.6% deltas). Weather helps during training (actual values) but we only have historical averages for prediction, which are redundant with temporal features. With access to actual weather *forecasts*, this would be transformative.

---

### Final Verdict

**Production model: Experiment 5**. 9 experiments tested, 4 rejected. The accuracy ceiling without exogenous weather forecasts is ~nRMSE 0.45.

---

## Task 3: Anomaly Detection

**Goal**: Detect instrument anomalies for 6 station/pollutant/period combinations. Target periods have no labels — predictions are the model's best estimate.

### Exp 1: Isolation Forest (SELECTED)

Trained on labeled historical data per station/pollutant. Features: z-score deviations from rolling means (6h/12h/24h), rate of change, stuck-sensor detection, temporal context.

Contamination parameter set per-target based on historical anomaly rate (0.7-4.5%).

| Target | Historical Rate | Val F1 | Detected Anomalies |
|--------|----------------|--------|-------------------|
| 205/SO2 | 0.7%          | 0.500  | 3/696 (0.4%)      |
| 209/NO2 | 2.0%          | 0.000  | 362/628 (57.6%)   |
| 223/O3  | 0.9%          | 0.667  | 7/699 (1.0%)      |
| 224/CO  | 4.5%          | 0.029  | 10/720 (1.4%)     |
| 226/PM10 | 2.8%         | 0.133  | 23/716 (3.2%)     |
| 227/PM2.5 | 3.8%        | 0.529  | 14/708 (2.0%)     |

Station 209/NO2 shows high detection rate (57.6%) — likely genuine distribution shift in the unlabeled target period. Validation F1 varies due to class imbalance and small anomaly counts.

**Output**: `outputs/anomaly_predictions.csv`
