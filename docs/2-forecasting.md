# 2. Forecasting (LightGBM Ensemble + CQR)

Predict hourly pollutant concentrations for 6 station/pollutant/period combinations, each a full month ahead (720+ hours). Production model selected from 9 experiments — see [docs/7-experiments.md](7-experiments.md) for the full log.

## Production Model (Experiment 5)

Weighted ensemble of three learners fit independently per (station, pollutant):

| Component | Role |
|-----------|------|
| **LightGBM (direct)** | Captures non-linear interactions between temporal, cyclical, and spatial features |
| **Ridge + Fourier basis** | Smooth seasonal backbone (daily, weekly, yearly harmonics) |
| **Seasonal Naive** | Anchor to last week's same-hour value — dampens tail-end drift |

Final prediction is a convex combination with weights optimized on validation residuals.

Entry point: [`src/forecasting/train_lgbm_ensemble.py`](../src/forecasting/train_lgbm_ensemble.py).

## Feature Engineering (~57 features)

Defined in [`src/forecasting/features.py`](../src/forecasting/features.py). Grouped by type:

- **Temporal** — hour, day-of-week, month, year, is_weekend, hours-since-epoch.
- **Cyclical** — sin/cos encodings of hour (period 24), day-of-week (period 7), day-of-year (period 365).
- **Fourier harmonics** — multi-scale daily/weekly/yearly basis (3 harmonics each).
- **Anchor lags** — 168h, 336h, 504h, 720h lags computed from *training* data only (no recursion at predict time).
- **Rolling stats** — 24h/168h/720h mean, std, min, max of the same series.
- **Bayesian target encoding** — per (hour, day-of-week) pollutant mean, regularized with a global prior.
- **Cross-station spatial** — IDW-weighted average of the 5 nearest neighbor stations (same pollutant).

## Why Direct, Not Recursive

Experiment 2 (recursive XGBoost) accumulated errors 6-10× over a 720h horizon — PM10 predictions drifted to 300-400 against actuals in [10, 200]. Tree-based models have no mechanism to dampen feedback loops, so each step's error compounds. See [Decision 2](../decisions.md#decision-2-direct-prediction-over-recursive-for-month-ahead-forecasting).

Direct prediction generates every future hour independently from features known at training time. Lags use *anchor* values from the training window, not live predictions.

## Target Transform + Interval Calibration (Decision 4)

Pollutant distributions are right-skewed — most hours are low, with rare high-concentration spikes. Raw regression targets cause the model to over-fit the mean and miss the tail.

1. **Log1p transform** — train in `log1p(y)` space, back-transform predictions with `expm1`. Stabilizes variance, improves optimization.
2. **Quantile regression** — fit LightGBM with `objective='quantile'` at α=0.05 and α=0.95 for lower/upper bounds.
3. **Conformalized Quantile Regression (CQR)** — on a held-out calibration set, compute the correction factor `Q` as the `(1-α)`-quantile of conformity scores `max(q_lo - y, y - q_hi)`. Widen intervals by `Q` to guarantee ≥90% finite-sample coverage.

CQR adds no retraining cost — it's a single quantile computation on calibration residuals.

## Validation

Walk-forward CV with **3 folds × 720h test windows** for every experiment. Single-holdout metrics are only reported when the cost of 3-fold CV is prohibitive (LSTM, global model).

## Results

| Pollutant | Naive nRMSE | Ensemble nRMSE | Improvement | 90% PI Coverage |
|-----------|-------------|----------------|-------------|-----------------|
| SO2       | 1.067       | **0.917**      | +14%        | 93.8%           |
| NO2       | 0.867       | **0.712**      | +18%        | 91.7%           |
| O3        | 0.787       | **0.715**      | +9%         | 90.5%           |
| CO        | 0.610       | **0.449**      | +26%        | 93.6%           |
| PM10      | 0.852       | **0.518**      | +39%        | 93.1%           |
| PM2.5     | 0.751       | **0.546**      | +27%        | 93.5%           |

**All 6 pollutants beat the seasonal-naive baseline · average PI coverage 93% vs 90% target.**

## Accuracy Ceiling

Without access to real weather *forecasts* (Exp 9 only had historical averages), the ceiling is ~nRMSE 0.45. PM10 and CO benefit most from spatial features because particulate and CO dispersion is spatially correlated; SO2 and O3 benefit least because their production is more local.

## Outputs

Predictions written to [`outputs/forecast_predictions.csv`](../outputs/forecast_predictions.csv) with columns: `measurement_datetime`, `station_code`, `item_code`, `item_name`, `predicted_value`, `predicted_lower_90`, `predicted_upper_90`.
