# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Air quality prediction project analyzing South Korean pollution data (25 stations, 2021-2023, 6 pollutants). Uses DBT/DuckDB for data transformation and Python for ML.

## Architecture

### DBT Models (`dbt_pollution/models/`)

```
Seeds (CSV) → Landing (views) → Logic (tables) → Presentation (tables)
```

- **Landing**: `lnd_measurements` (wide), `lnd_instrument_data` (long), `lnd_pollutants` (reference)
- **Logic**:
  - `measurements_long`: Unpivoted measurements (1 row per station/datetime/pollutant)
  - `measurements_with_status`: Long-format measurements joined 1:1 with instrument status
  - `measurements_clean`: Cleaned data with temporal features and air quality classification
- **Presentation**: `dashboard_wide` — pivoted back to wide format for Streamlit

### Python Package (`src/`)

- `src/data/loader.py`: Load data from DuckDB into pandas
- `src/forecasting/`: XGBoost direct prediction pipeline
- `src/anomaly/`: Isolation Forest anomaly detection
- `src/utils/constants.py`: Item codes, targets, DB path

### Key Tables

| Table | Format | Use |
|-------|--------|-----|
| `measurements_clean` | Long | All analysis and ML tasks |
| `measurements_with_status` | Long | Data exploration with status |
| `dashboard_wide` | Wide | Streamlit dashboard |

### Data Schema
- **Stations**: 25 (codes 204-228)
- **Pollutants**: SO2 (0), NO2 (2), CO (4), O3 (5), PM10 (7), PM2.5 (8)
- **Status**: 0=Normal, 1=Calibration, 2=Abnormal, 4=Power cut, 8=Under repair, 9=Abnormal data
- **Missing values**: -1 in raw data → NULL in `clean_value`

## Common Commands

```bash
cd dbt_pollution && dbt build      # Run + test all models
source venv/bin/activate           # Activate Python env
pip install -r requirements.txt    # Install dependencies
```

## Project Status

- **Task 1** (EDA): Complete — answers in `notebooks/01_eda_answers.ipynb`
- **Task 2** (Forecasting): Complete — XGBoost direct prediction, results in `outputs/forecast_predictions.csv`
- **Task 3** (Anomaly Detection): Complete — Isolation Forest, results in `outputs/anomaly_predictions.csv`

## Dependencies

- **Python**: pandas, numpy, matplotlib, duckdb, scikit-learn, xgboost
- **DBT**: dbt-duckdb
- **Dashboard**: streamlit, plotly, folium
