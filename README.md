# Seoul Air Quality Prediction

Hourly pollutant forecasting and instrument anomaly detection for 25 Seoul monitoring stations across 6 pollutants (SO2, NO2, O3, CO, PM10, PM2.5), using 3 years of hourly data (2021-2023).

## Architecture

```
Data Layer          CSV seeds --> DBT / DuckDB --> measurements_clean (3.7M rows)
                                                          |
ML Training         measurements_clean --> src/forecasting/  --> MLflow (experiments)
                    measurements_clean --> src/anomaly/       --> MLflow (experiments)
                                                          |
Model Serving       Trained pipelines --> FastAPI (app/)  --> /predict/forecast
                                                          --> /predict/anomaly
                                                          |
Visualization       DuckDB + CSV outputs --> Streamlit Dashboard (6 tabs)
```

## Quick Start

```bash
make install        # Install all dependencies
make dbt-build      # Build data pipeline (seeds + models + tests)
make predict        # Train and export models
make serve          # Start API at localhost:8080
```

## Data Pipeline (DBT / DuckDB)

```
Seeds (CSV) --> Landing (views) --> Logic (tables) --> Presentation (tables)
```

| Layer | Model | Description |
|-------|-------|-------------|
| Landing | `lnd_measurements` | Wide-format hourly readings (621K rows) |
| Landing | `lnd_instrument_data` | Long-format instrument status per pollutant (3.7M rows) |
| Landing | `lnd_pollutants` | Reference: thresholds for Good/Normal/Bad/Very bad |
| Logic | `measurements_long` | Unpivoted to long format (1 row per station/datetime/pollutant) |
| Logic | `measurements_with_status` | 1:1 join with instrument status |
| Logic | `measurements_clean` | Null handling, temporal features, air quality classification |
| Presentation | `dashboard_wide` | Pivoted back to wide format for Streamlit |

## Models

### Forecasting (LightGBM Ensemble)

Ensemble of LightGBM + Ridge (Fourier) + Seasonal Naive with optimized weights. 57 features: multi-scale Fourier harmonics, anchor lags, Bayesian target encoding, spatial IDW. Log1p target transform, CQR-calibrated 90% prediction intervals.

| Target | nRMSE | vs Naive | PI Coverage |
|--------|-------|---------|-------------|
| SO2 | 0.917 | +14% | 93.8% |
| NO2 | 0.712 | +18% | 91.7% |
| O3 | 0.715 | +9% | 90.5% |
| CO | 0.449 | +26% | 93.6% |
| PM10 | 0.518 | +39% | 93.1% |
| PM2.5 | 0.546 | +27% | 93.5% |

9 experiments tested (XGBoost recursive/direct, LightGBM ensemble, LSTM, global model, weather data, cross-pollutant). See `experiments.md` or MLflow UI for details.

### Anomaly Detection (Supervised LightGBM)

Binary classifier with ~80 features (rolling stats, lag/diff, flatline/spike detectors, XGBOD Isolation Forest scores). F1-optimized threshold per target, adaptive temporal smoothing.

| Target | F1 Score | Improvement vs Isolation Forest |
|--------|----------|--------------------------------|
| SO2 | 1.000 | +100% |
| O3 | 1.000 | +50% |
| CO | 0.956 | +3197% |
| PM2.5 | 0.526 | same |
| PM10 | 0.235 | +77% |

## API Endpoints

Start the server: `make serve`

```bash
# Health check
curl http://localhost:8080/health

# Forecast prediction
curl -X POST http://localhost:8080/predict/forecast \
  -H "Content-Type: application/json" \
  -d '{"station_code": 206, "item_code": 0, "start_date": "2023-07-01", "end_date": "2023-07-31 23:00:00"}'

# Anomaly detection
curl -X POST http://localhost:8080/predict/anomaly \
  -H "Content-Type: application/json" \
  -d '{"station_code": 205, "item_code": 0, "measurements": [{"datetime": "2023-11-01 00:00:00", "value": 0.003}]}'
```

API docs: http://localhost:8080/docs

## Dashboard

Start: `make dashboard` (port 8501)

6 tabs: Time Series Analysis, Geographic Analysis, Data Quality, Statistical Summary, **Forecasts** (with 90% prediction intervals), **Anomaly Detection** (with probability heatmaps).

## Experiment Tracking (MLflow)

```bash
make log-experiments   # Log all historical experiments to MLflow
make mlflow-ui         # Start MLflow UI at localhost:5000
```

## Docker

```bash
make docker-build         # Build image
make docker-run           # Run API container (port 8080)
make docker-compose-up    # Start all services (API + MLflow + Dashboard)
make docker-compose-down  # Stop all services
```

## Project Structure

```
pollution-prediction/
  app/                     # FastAPI prediction service
    main.py, schemas.py, model_loader.py
    routers/               # health, forecast, anomaly endpoints
  src/                     # ML package
    data/                  # loader.py, weather.py
    forecasting/           # train_lgbm_ensemble.py (production), features.py, evaluate.py
                           # train_xgboost.py, train_lstm.py, train_global.py (experiments)
    anomaly/               # detector.py (production), detector_isolation_forest.py (experiment)
    utils/                 # constants.py
  dbt_pollution/           # DBT project
    models/                # landing/, logic/, presentation/
    seeds/                 # CSV data files
  scripts/                 # log_experiments.py, train_with_mlflow.py, export_models.py
  notebooks/               # EDA, forecasting, anomaly detection, LSTM experiment
  tests/                   # API and pipeline tests
  outputs/                 # Predictions CSV, plots, model pickles
  data/                    # Weather cache (Open-Meteo)
  Dockerfile               # Cloud Run-ready container
  docker-compose.yml       # Local dev: API + MLflow + Dashboard
  Makefile                 # All project operations
  experiments.md           # Experiment log (also in MLflow)
  decisions.md             # Architectural decisions
```

## Makefile Targets

```
make help             # Show all targets
make install          # Install dependencies
make dbt-build        # Build data pipeline
make train            # Train models with MLflow
make predict          # Export models for serving
make serve            # Start FastAPI (port 8080)
make dashboard        # Start Streamlit (port 8501)
make mlflow-ui        # Start MLflow UI (port 5000)
make test             # Run tests
make docker-build     # Build Docker image
make docker-compose-up # Start all services
make clean            # Remove caches
```
