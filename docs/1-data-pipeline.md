# 1. Data Pipeline (dbt + BigQuery)

Three years of Seoul air-quality monitoring data flow through a dbt project materialized on BigQuery. The pipeline enforces a landing → logic → presentation layering with schema tests at every stage.

## Inputs

Two CSV sources, seeded into BigQuery as the `landing` dataset:

- **`measurement_data.csv`** — wide format, 1 row per station/datetime with 6 pollutant columns (SO2, NO2, O3, CO, PM10, PM2.5). ~621K rows.
- **`instrument_data.csv`** — long format, 1 row per station/datetime/`item_code` with an `instrument_status` code (0=Normal, 1=Calibration, 2=Abnormal, 4=Power cut, 8=Under repair, 9=Abnormal data). ~3.7M rows.

A third seed, `measurement_item_info.csv`, provides the pollutant reference table (`lnd_pollutants`).

## Model Layers

| Layer | Dataset | Materialization | Purpose |
|-------|---------|-----------------|---------|
| Landing | `landing` | view | 1:1 mirror of the seeds, column renames only |
| Logic | `logic` | table | Shape + clean + feature-engineer |
| Presentation | `presentation` | table | Pivot back to wide for the dashboard |

### Logic layer

1. **`measurements_long`** — unpivots the wide measurement CSV with `UNION ALL`, mapping each pollutant column to its `item_code`. Output: ~3.73M rows (621K × 6).
2. **`measurements_with_status`** — 1:1 join of `measurements_long` with `lnd_instrument_data` on `(measurement_datetime, station_code, item_code)`. See [Decision 1](../decisions.md#decision-1-unpivot-measurements-to-long-format) for why this join key matters — the original 2-key join caused a 6× fan-out.
3. **`measurements_clean`** — replaces raw `-1` sentinels with `NULL` in `clean_value`, adds temporal features (hour, day-of-week, month), and attaches an air-quality class label.

### Presentation layer

- **`dashboard_wide`** — pivots `measurements_clean` back to wide format for the Streamlit dashboard, keeping both raw and clean values per pollutant.

## Schema Routing

A custom macro in [`dbt_pollution/macros/generate_schema_name.sql`](../dbt_pollution/macros/generate_schema_name.sql) maps dbt `+schema` config directly to BigQuery dataset names (not the default `{profile}_{schema}` prefix). This lets `landing`, `logic`, `presentation` map to the identically-named datasets.

## Profiles

- **`dev`** — BigQuery (project `mpc-pollution-331382`, region `asia-northeast3`). The canonical target.
- **`local`** — DuckDB, kept for offline development on flights and in poor connectivity.

Switch via `dbt build --target local`.

## Tests

Every layer has schema and referential tests. Current run: **54/54 pass**. Key tests include:

- `not_null` + `unique` on primary keys at the logic layer.
- `relationships` between `measurements_long.item_code` and `lnd_pollutants.item_code`.
- Custom `dbt_expectations` assertions for value ranges (e.g., PM2.5 ∈ [0, 1000]) and expected row counts.

## Commands

```bash
cd dbt_pollution
dbt deps                  # install dbt-utils, dbt-date, dbt-expectations
dbt build                 # seed + run + test against BigQuery
dbt build --target local  # same pipeline, against DuckDB
dbt docs generate && dbt docs serve
```
