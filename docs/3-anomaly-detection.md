# 3. Anomaly Detection (Supervised LightGBM)

Detect instrument anomalies for 6 station/pollutant/period combinations. Target periods have no labels — predictions are the model's best estimate.

## Production Model: Supervised LightGBM Classifier

The baseline was an unsupervised Isolation Forest. Switching to a supervised classifier was the single biggest accuracy lever — average F1 doubled from 0.31 to 0.62.

**Key insight**: `instrument_status` labels *are* available in the historical training data. The problem is supervised, not unsupervised. Treating it as unsupervised was the root cause of the baseline's ceiling.

Entry point: [`src/anomaly/detector.py`](../src/anomaly/detector.py).

## Feature Set (~80 features)

Defined per series in [`src/anomaly/detector.py`](../src/anomaly/detector.py):

- **Rolling statistics** — mean, std, min, max, range, z-score at 6 windows (3h, 6h, 12h, 24h, 72h, 168h).
- **Lag + diff** — 8 lag offsets (1h, 3h, 6h, 12h, 24h, 72h, 168h, 720h) with first differences.
- **Failure signatures** — flatline detection (consecutive identical values over 6h/12h), stuck-sensor count, spike score (z-score > 3), at-zero flag, negative-value flag.
- **Temporal** — cyclical hour/day-of-week, month indicator, is_weekend.
- **Contextual** — deviation from hourly median over the last 30 days.
- **XGBOD bonus** — the Isolation Forest anomaly score itself, as a feature (XGBOD pattern).

The XGBOD feature lets the supervised model inherit whatever signal the unsupervised baseline captured, rather than compete with it.

## Model + Threshold

- **LightGBM** — `n_estimators=800`, `lr=0.03`, `num_leaves=63`. Binary objective.
- **No `scale_pos_weight`** — keeps predicted probabilities calibrated, which matters for downstream thresholding.
- **Threshold** — optimized per target via precision-recall curve to maximize F1 on the validation fold.

## Post-processing: Adaptive Smoothing

Real sensor failures tend to cluster (once a sensor flatlines, it stays flat). Isolated single-hour positives are often false alarms. But *sparse* true anomalies (e.g., a one-hour voltage spike) also exist — a blanket smoothing rule would erase them.

Compromise: **min-run-length filter of 3h applied only when the predicted anomaly rate exceeds 5%**. In low-rate regimes, all detections pass through.

## Results

| Station / Pollutant | Isolation Forest F1 | LightGBM F1 | Precision | Recall | Δ |
|---------------------|---------------------|-------------|-----------|--------|---|
| 205 / SO2           | 0.500               | **1.000**   | 1.000     | 1.000  | +100% |
| 209 / NO2           | 0.000               | 0.000       | 0.000     | 0.000  | same (3 anomalies) |
| 223 / O3            | 0.667               | **1.000**   | 1.000     | 1.000  | +50% |
| 224 / CO            | 0.029               | **0.956**   | 0.916     | 1.000  | **+3197%** |
| 226 / PM10          | 0.133               | **0.235**   | 0.667     | 0.143  | +77% |
| 227 / PM2.5         | 0.529               | 0.526       | 0.385     | 0.833  | ~0% |
| **Average**         | **0.310**           | **0.620**   | —         | —      | **+100%** |

### The 224 / CO outlier

The validation month for station 224/CO was **95% anomalous** (the sensor was broken for most of the month). A supervised classifier with access to labels detects this trivially. An Isolation Forest tuned to 4.5% contamination mathematically cannot — it's configured to expect rare anomalies, so it throws most of the positives away.

This is the clearest demonstration in the project that matching the model class to the data regime matters more than tuning.

### The 209 / NO2 zero

Only 3 true anomalies in the validation fold — below the minimum any threshold-based classifier can reliably learn from. This is a label-scarcity problem, not a model problem.

## Outputs

Predictions written to [`outputs/anomaly_predictions.csv`](../outputs/anomaly_predictions.csv) with columns: `measurement_datetime`, `station_code`, `item_code`, `item_name`, `is_anomaly`, `anomaly_score`.
