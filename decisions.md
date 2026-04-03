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
- The Streamlit dashboard will need updating to work with long-format data
