# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an air quality prediction project analyzing South Korean pollution data. The project uses DBT (data build tool) with DuckDB for data transformation and processing, along with Python for analysis and machine learning tasks.

## Architecture

### Data Layer
- **Seeds**: Raw CSV data files in `dbt_pollution/seeds/`
  - `pollutant_data.csv`: Reference data with pollutant thresholds
  - `instrument_data.csv`: Monitoring instrument information
  - `measurement_data.csv`: Time-series pollution measurements
- **Landing Models**: Clean and standardize raw data (`dbt_pollution/models/landing/`)
  - `lnd_pollutants`: Pollutant reference data with standardized units
  - `lnd_measurements`: Main measurements data with hourly readings
  - `lnd_instrument_data`: Instrument readings with status codes

### DBT Project Structure
- **Profile**: `dbt_schneider` with dev/prod targets
- **Materialization Strategy**:
  - Landing: Views for data cleaning
  - Logic: Tables for business logic
  - Presentation: Tables for final output
- **Database**: DuckDB files (`dev.duckdb`, `prod.duckdb`)

### Data Schema
- **Stations**: 25 monitoring stations in South Korea (codes 204-228)
- **Time Range**: 2021-2023 with hourly measurements
- **Pollutants**: SO2, NO2, O3, CO, PM10, PM2.5
- **Instrument Status Codes**:
  - 0: Normal
  - 1: Need for calibration
  - 2: Abnormal
  - 4: Power cut off
  - 8: Under repair
  - 9: Abnormal data

## Common Development Tasks

### DBT Operations
```bash
# Navigate to DBT project
cd dbt_pollution

# Run all models
dbt run

# Run specific model
dbt run --select lnd_measurements

# Test data quality
dbt test

# Generate documentation
dbt docs generate

# Build everything (run + test)
dbt build

# Run for production target
dbt run --target prod
```

### Data Analysis
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Jupyter for analysis
jupyter notebook dbt_pollution/analysis/
```

### Working with DuckDB
- Development database: `dbt_pollution/dev.duckdb`
- Production database: `dbt_pollution/prod.duckdb`
- Access via Python: `duckdb.connect('dbt_pollution/dev.duckdb')`

## Key Project Tasks

The project addresses three main analytical challenges:

1. **Exploratory Data Analysis**: Answer specific questions about pollution patterns
2. **Forecasting Model**: Predict hourly pollutant concentrations for specified periods
3. **Anomaly Detection**: Identify instrument failures and data quality issues

## Dependencies

- **Python**: pandas, numpy, matplotlib, duckdb, folium
- **DBT**: dbt-duckdb for DuckDB adapter
- **Database**: DuckDB for local analytics database