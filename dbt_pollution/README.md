# dbt_pollution

dbt project for the air-quality pipeline. Three layers, two targets, one custom macro. For the why behind the model shapes (unpivot, per-row status join, clean-vs-raw split), read [../docs/1-data-pipeline.md](../docs/1-data-pipeline.md); this README is the operational reference.

## Layout

```
models/
  landing/       → views    lnd_measurements, lnd_instrument_data, lnd_pollutants
  logic/         → tables   measurements_long, measurements_with_status, measurements_clean
  presentation/  → table    dashboard_wide
seeds/           → CSVs committed to the repo (pollutants, raw measurements)
macros/          → generate_schema_name override (maps +schema to BQ dataset name)
```

## Targets

| Target | Engine   | When to use                                                  |
|--------|----------|--------------------------------------------------------------|
| `dev`  | BigQuery | The production target. Needs GCP ADC (`gcloud auth login`).  |
| `local`| DuckDB   | Offline development, CI, and the Parquet snapshot source.    |

Profile is `dbt_schneider`, defined in [profiles.yml](profiles.yml). BigQuery uses OAuth by default.

## Commands

```bash
dbt deps                               # install packages
dbt seed                               # load CSVs into landing
dbt build                              # run + test all models (dev target)
dbt build --target local               # same, against dev.duckdb
dbt build --select measurements_clean  # just one model (plus tests)
dbt docs generate && dbt docs serve    # browse the model graph
```

`dbt build` runs models then tests, which is what you want. Plain `dbt run` skips tests.

## Key models

- `measurements_long` — unpivots the six pollutant columns into one row per `(station, datetime, item_code)`. This is the shape that lets the instrument-status join stay 1:1 instead of fanning out 6x.
- `measurements_with_status` — joins long measurements to instrument status on all three keys.
- `measurements_clean` — feature engineering (temporal, air-quality class from pollutant thresholds) and NULL handling. Everything downstream (ML, EDA, dashboards) reads from here.
- `dashboard_wide` — pivots back to wide format for the Streamlit / Next.js dashboards.

## Notes

- `dev.duckdb` and `prod.duckdb` are gitignored; `scripts/export_to_parquet.py` reads from `dev.duckdb` to produce the committed `data/dashboard_wide.parquet` snapshot.
- BigQuery datasets (`landing`, `logic`, `presentation`) are provisioned by Terraform, not by dbt.
