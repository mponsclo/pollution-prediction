# Decisions Log

## Decision 1: Unpivot measurements to long format

**Date**: 2026-04-03  
**Status**: Accepted

### Context

The project has two data sources with different formats:
- `measurement_data.csv` (wide format): 1 row per station/datetime, 6 pollutant columns (SO2, NO2, O3, CO, PM10, PM2.5)
- `instrument_data.csv` (long format): 1 row per station/datetime/item_code, with `instrument_status` per pollutant

The existing `measurements_with_status` model joined these on `(station_code, measurement_datetime)` only, **without `item_code`**. Since instrument data has up to 6 rows per (station, datetime) — one per pollutant — this caused a 6x fan-out: ~3.7M rows instead of ~621K.

### Decision

Create a `measurements_long` model that unpivots the wide measurement data into long format using UNION ALL, mapping each pollutant column to its `item_code`:
- so2_value → item_code 0
- no2_value → item_code 2
- co_value → item_code 4
- o3_value → item_code 5
- pm10_value → item_code 7
- pm2_5_value → item_code 8

Then join to instrument data on `(measurement_datetime, station_code, item_code)` for a clean 1:1 relationship.

### Alternatives Considered

**Option B: Pivot instrument status to wide format** — Create 6 status columns (so2_status, no2_status, etc.) to maintain the wide layout. Rejected because every downstream task (EDA, forecasting, anomaly detection) operates on a single pollutant at a time, making long format the natural representation. Wide status columns would also make filtering by status awkward.

### Consequences

- `measurements_long` produces ~3.73M rows (621K × 6)
- `measurements_with_status` becomes a clean 1:1 join
- All downstream queries filter by `item_code` for per-pollutant analysis
- The Streamlit dashboard uses a `dashboard_wide` presentation model that pivots back

## Decision 2: Direct prediction over recursive for month-ahead forecasting

**Date**: 2026-04-03  
**Status**: Accepted

### Context

XGBoost with lag features (1h-168h) using recursive prediction accumulated errors catastrophically over 720+ hour horizons. RMSE was 6-10x worse than a simple seasonal naive baseline.

### Decision

Use **direct prediction** with features that require no recursive dependency: temporal features, cyclical encoding, and historical same-hour/day-of-week/month statistics. Each prediction is independent, avoiding error accumulation.

### Consequences

- XGBoost direct beats seasonal naive on all 6 targets (3-44% improvement)
- Model captures seasonal patterns but cannot capture short-term autocorrelation
- Predictions reflect average behavior for given temporal context

## Decision 3: Isolation Forest for anomaly detection

**Date**: 2026-04-03  
**Status**: Accepted

### Context

Target periods have no instrument_status labels. Need unsupervised detection trained on historical labeled data.

### Decision

Isolation Forest with features: z-score deviations from rolling means, rate of change, stuck-sensor detection. Contamination parameter set per-target based on historical anomaly rate.

### Alternatives Considered

- **Residual-based (using forecasting model)**: Would require accurate per-hour predictions, which direct prediction can't provide.
- **Statistical thresholds (z-score only)**: Too simple, misses complex failure patterns.

### Consequences

- Validation F1 ranges from 0.03 to 0.67 depending on target
- Detection rates in target periods are generally consistent with historical anomaly rates

## Decision 4: Log1p transform + CQR calibration for production forecasting

**Date**: 2026-04-03  
**Status**: Accepted

### Context

v2 forecasting pipeline had prediction intervals under-covering at 62-89% vs 90% target. Raw quantile regression has no finite-sample coverage guarantee. Also, pollutant data is right-skewed (many low values, rare spikes).

### Decision

1. **Log1p target transform**: Train all models in log1p(y) space, back-transform predictions via expm1. Stabilizes variance and improves optimization for skewed distributions.
2. **Conformalized Quantile Regression (CQR)**: Compute correction factor Q from validation residuals. Widen/narrow intervals by Q to guarantee ≥90% coverage.
3. **Cross-station spatial features**: IDW-weighted average of 5 nearest stations as additional features.

### Consequences

- All 6 targets achieve >90% prediction interval coverage (93.8% average)
- Point estimate accuracy maintained (nRMSE 0.45-0.92)
- CQR adds negligible computational cost (a single quantile computation on calibration scores)
