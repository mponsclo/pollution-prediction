# Seoul Air Quality Prediction

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![DBT](https://img.shields.io/badge/dbt-BigQuery-orange.svg)](https://docs.getdbt.com/)
[![FastAPI](https://img.shields.io/badge/serving-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![GCP](https://img.shields.io/badge/infra-GCP%20%2F%20Terraform-4285F4.svg)](https://cloud.google.com/)

End-to-end air quality forecasting and instrument anomaly detection for 25 Seoul monitoring stations. The system ingests 3 years of hourly measurements (2021-2023) across 6 pollutants (SO2, NO2, O3, CO, PM10, PM2.5), transforms them through a reproducible DBT/BigQuery pipeline, and serves predictions through a REST API on Cloud Run backed by a LightGBM ensemble selected from 9 candidate experiments. Infrastructure is managed with Terraform, CI/CD with GitHub Actions, and secrets encrypted with SOPS/KMS.

**Headline results:** Forecast nRMSE 0.45-0.92 across all pollutants with calibrated 90% prediction intervals. Anomaly detection F1 doubled from 0.31 to 0.62 versus the Isolation Forest baseline.

---

## Key Features

- **Reproducible data pipeline** -- DBT models on BigQuery transform 3.7M rows from raw CSV seeds through landing, logic, and presentation layers with schema tests at every stage (54/54 pass)
- **Production forecasting** -- LightGBM + Ridge + Seasonal Naive ensemble with 57 features (Fourier harmonics, anchor lags, Bayesian target encoding, spatial IDW), log1p transform, and Conformalized Quantile Regression for calibrated intervals
- **Supervised anomaly detection** -- LightGBM binary classifier with ~80 features including flatline/spike detectors and XGBOD Isolation Forest scores, with F1-optimized thresholds and adaptive temporal smoothing
- **REST API** -- FastAPI service with forecast and anomaly endpoints, input validation, auto-generated OpenAPI docs, deployed on Cloud Run (scale 0-3)
- **Interactive dashboard** -- Streamlit app with 6 tabs covering time series, geographic, data quality, statistical, forecast, and anomaly views
- **Experiment tracking** -- 9 forecasting and 2 anomaly experiments logged in MLflow with full metrics, parameters, and artifacts
- **Infrastructure as Code** -- Terraform-managed GCP resources (BigQuery, Cloud Run, Artifact Registry, KMS, IAM, Workload Identity Federation)
- **CI/CD** -- GitHub Actions workflows for Terraform validate/plan/apply and Docker build+deploy, with SOPS-encrypted secrets

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.13+ | Runtime |
| pip | latest | Package management |
| GCP account | -- | BigQuery, Cloud Run access |
| gcloud CLI | latest | GCP authentication |
| Terraform | 1.7+ | Infrastructure management |
| Docker | 20+ | Optional, for containerized deployment |

The data pipeline runs on BigQuery (GCP project `mpc-pollution-331382`). Authentication uses `gcloud auth application-default login`.

## Quick Start

```bash
# Clone and set up environment
git clone https://github.com/mponsclo/pollution-prediction.git
cd pollution-prediction
python -m venv venv && source venv/bin/activate

# Install dependencies and build data pipeline
make install
make dbt-build

# Train models, export for serving, and start the API
make predict
make serve            # http://localhost:8080
make dashboard        # http://localhost:8501  (separate terminal)
```

Or start everything with Docker:

```bash
make docker-compose-up   # API :8080, MLflow :5001, Dashboard :8501
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE (Terraform)                                         │
│  GCP Project ──> BigQuery, Cloud Run, Artifact Registry, KMS, IAM  │
│  GitHub Actions ──> Terraform plan/apply, Docker build+deploy       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  DATA LAYER                                                         │
│  CSV seeds ──> DBT / BigQuery ──> measurements_clean (3.7M rows)   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  ML TRAINING                                                        │
│  measurements_clean ──> src/forecasting/ ──> MLflow (9 experiments) │
│  measurements_clean ──> src/anomaly/     ──> MLflow (2 experiments) │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  MODEL SERVING                                                      │
│  Trained pipelines ──> FastAPI (app/) ──> /predict/forecast          │
│                    ──> Cloud Run       ──> /predict/anomaly          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  VISUALIZATION                                                      │
│  BigQuery + predictions CSV ──> Streamlit Dashboard (6 tabs)        │
└─────────────────────────────────────────────────────────────────────┘
```

The **data layer** owns all transformations: raw CSVs are seeded into BigQuery via DBT, unpivoted from wide to long format, joined 1:1 with instrument status, and enriched with temporal features and air quality classifications. Everything downstream reads from `measurements_clean` in the `logic` dataset.

The **ML layer** trains per-station, per-pollutant models. Forecasting and anomaly detection are independent pipelines that share the same cleaned data but produce separate model artifacts.

The **serving layer** loads serialized pipelines at startup and exposes them through typed Pydantic schemas. At prediction time, spatial and cross-pollutant features are computed via live BigQuery queries. The **dashboard** reads directly from BigQuery and the prediction CSV outputs.

---

## Results

### Forecasting

The production model (Experiment 5 of 9) is a weighted ensemble of LightGBM, Ridge regression with Fourier basis, and Seasonal Naive. Prediction intervals are calibrated with Conformalized Quantile Regression to guarantee at least 90% coverage.

| Pollutant | nRMSE | Improvement vs Naive | 90% PI Coverage |
|-----------|-------|---------------------|-----------------|
| SO2       | 0.917 | +14%                | 93.8%           |
| NO2       | 0.712 | +18%                | 91.7%           |
| O3        | 0.715 | +9%                 | 90.5%           |
| CO        | 0.449 | +26%                | 93.6%           |
| PM10      | 0.518 | +39%                | 93.1%           |
| PM2.5     | 0.546 | +27%                | 93.5%           |

nRMSE below 1.0 means the model outperforms predicting the global mean. The largest gains are on particulate matter (PM10, PM2.5) and CO, where the ensemble captures diurnal and weekly cycles that the naive baseline misses. See [`experiments.md`](experiments.md) for the full experiment log including rejected approaches (recursive XGBoost, LSTM, global model, weather features).

### Anomaly Detection

A supervised LightGBM classifier replaced the initial unsupervised Isolation Forest after recognizing that instrument status labels were available in the training data.

| Station / Pollutant | Isolation Forest F1 | LightGBM F1 | Change |
|---------------------|---------------------|-------------|--------|
| 205 / SO2           | 0.500               | 1.000       | +100%  |
| 223 / O3            | 0.667               | 1.000       | +50%   |
| 224 / CO            | 0.029               | 0.956       | +3197% |
| 227 / PM2.5         | 0.529               | 0.526       | ~0%    |
| 226 / PM10          | 0.133               | 0.235       | +77%   |
| **Average**         | **0.310**           | **0.620**   | **+100%** |

The CO result (0.029 to 0.956) is the most dramatic: the validation month was 95% anomalous, which the supervised model detects trivially while Isolation Forest with low contamination could not.

---

## API Reference

Start the server with `make serve` (default: `http://localhost:8080`). Interactive docs at `/docs`.

### `GET /health`

```bash
curl http://localhost:8080/health
# {"status": "healthy", "models_loaded": 12}
```

### `POST /predict/forecast`

Returns hourly point forecasts with 90% prediction intervals. Max date range: 2 months.

```bash
curl -X POST http://localhost:8080/predict/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "station_code": 206,
    "item_code": 0,
    "start_date": "2023-07-01",
    "end_date": "2023-07-31 23:00:00"
  }'
```

### `POST /predict/anomaly`

Classifies each measurement as normal or anomalous. Requires at least 3 consecutive hourly measurements.

```bash
curl -X POST http://localhost:8080/predict/anomaly \
  -H "Content-Type: application/json" \
  -d '{
    "station_code": 205,
    "item_code": 0,
    "measurements": [
      {"datetime": "2023-11-01 00:00:00", "value": 0.003},
      {"datetime": "2023-11-01 01:00:00", "value": 0.004},
      {"datetime": "2023-11-01 02:00:00", "value": 0.005}
    ]
  }'
```

Pollutant item codes: SO2=0, NO2=2, CO=4, O3=5, PM10=7, PM2.5=8.

---

## Dashboard

Start with `make dashboard` (default: `http://localhost:8501`).

1. **Time Series Analysis** -- pollutant trends with instrument status overlay
2. **Geographic Analysis** -- station map with spatial pollution patterns
3. **Data Quality Overview** -- missing data rates, status distributions, coverage metrics
4. **Statistical Summary** -- distributions, correlations, threshold exceedances
5. **Forecasts** -- model predictions with 90% prediction interval bands
6. **Anomaly Detection** -- detected anomalies with probability heatmaps

---

## Infrastructure

### Terraform (`terraform/`)

All GCP resources managed as code. Bootstrap creates the project; main config manages the rest.

```bash
# First-time setup (run once)
cd terraform/bootstrap && terraform apply

# Ongoing changes go through GitHub Actions, or locally:
cd terraform && sops --decrypt terraform.tfvars.enc > terraform.tfvars
terraform plan
```

### CI/CD (`.github/workflows/`)

| Workflow | Trigger | Action |
|----------|---------|--------|
| `terraform-validate` | PR to `terraform/**` | fmt + validate |
| `terraform-plan` | PR to `terraform/**` | Plan posted as PR comment |
| `terraform-apply` | Push to main | Apply with approval gate |
| `docker-build-deploy` | Push to main (app/src changes) | Build + push to AR + deploy to Cloud Run |

Secrets encrypted with SOPS + GCP KMS. GitHub Actions authenticates via Workload Identity Federation (no service account keys).

### Future: Orchestration with Cloud Composer

The current pipeline is manually triggered (`make dbt-build` → `make predict` → CI/CD deploys). In production, this would be orchestrated with **Cloud Composer** (managed Airflow):

```
                         ┌──────────────┐
                         │   Scheduler  │
                         │  (daily/weekly)
                         └──────┬───────┘
                                │
              ┌─────────────────▼─────────────────┐
              │   1. ingest_new_data               │
              │   Cloud Run Job: pull latest        │
              │   measurements from station API     │
              └─────────────────┬─────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │   2. dbt_build                     │
              │   Cloud Run Job: dbt build          │
              │   (seed + transform + test)         │
              └─────────────────┬─────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │   3. retrain_models                │
              │   Cloud Run Job: train + export     │
              │   pkl files → GCS bucket           │
              └─────────────────┬─────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │   4. deploy_api                    │
              │   gcloud run deploy with new        │
              │   model revision                   │
              └─────────────────┬─────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │   5. validate_predictions          │
              │   Run smoke tests against live      │
              │   endpoint, log metrics to BQ      │
              └───────────────────────────────────┘
```

Each step would be an Airflow `GKEStartPodOperator` or `CloudRunJobOperator` with retries, SLA alerts, and Slack/email notifications on failure. Model artifacts would move from baked-into-Docker to stored in GCS and downloaded at startup, enabling retraining without image rebuilds.

**Why it's not implemented:** Cloud Composer's minimum cost (~$300/month for the smallest environment) exceeds the free tier budget. For a cost-effective alternative, a GitHub Actions scheduled workflow (`cron: '0 6 * * 1'`) with the same steps would achieve the same result at zero cost.

### Production Roadmap

The project implements IaC, CI/CD, typed APIs, and data quality testing. The following items would complete the production story:

| Gap | Current State | Production Target |
|-----|--------------|-------------------|
| **Data ingestion** | Static CSV seeds (2021-2023) | Scheduled Cloud Run Job pulling from the [AirKorea Open API](https://www.airkorea.or.kr/) into a BigQuery staging table, with DBT incremental models |
| **Model artifact storage** | pkl files baked into Docker image; retraining requires full rebuild | Store in GCS bucket, download at Cloud Run startup via `MODELS_BUCKET` env var |
| **Model monitoring** | None | Log predictions to a BigQuery `predictions_log` table, run scheduled queries comparing against actuals for drift detection (PSI, KL divergence on feature distributions) |
| **Integration tests** | Unit tests with synthetic data only | CI step that runs `load_series()` against BigQuery and validates row counts and schema |
| **Alerting** | Budget alerts only | Cloud Monitoring uptime checks on `/health`, alert policies on error rate and latency, Slack/PagerDuty integration |

---

## Development

### Training models

```bash
make train              # Train all models with MLflow tracking
make mlflow-ui          # Browse experiments at http://localhost:5001
make log-experiments    # Backfill historical experiment metadata into MLflow
```

### Testing

```bash
make test               # 14 tests: API endpoints, feature engineering, model pipelines
```

### Docker

```bash
make docker-build           # Build image
make docker-run             # Run API container (port 8080)
make docker-compose-up      # Start API + MLflow + Dashboard
make docker-compose-down    # Stop all services
```

---

## Project Structure

```
pollution-prediction/
├── app/                              API service
│   ├── main.py                         FastAPI app with model loading
│   ├── schemas.py                      Pydantic request/response models
│   └── routers/                        health, forecast, anomaly endpoints
├── src/                              ML package
│   ├── forecasting/
│   │   ├── train_lgbm_ensemble.py      Production model (Exp 5)
│   │   ├── features.py                 57-feature engineering pipeline
│   │   ├── evaluate.py                 nRMSE, R2, interval coverage metrics
│   │   ├── train_xgboost.py            Experiments 2-3
│   │   ├── train_lstm.py               Experiment 6
│   │   └── train_global.py             Experiment 8
│   ├── anomaly/
│   │   ├── detector.py                 Supervised LightGBM (production)
│   │   └── detector_isolation_forest.py  Baseline (Exp 1)
│   ├── data/                           BigQuery loader, Open-Meteo weather client
│   └── utils/                          Constants (BQ project, item codes)
├── dbt_pollution/                    DBT project (BigQuery)
│   ├── seeds/                          Raw CSV data (~175 MB)
│   ├── macros/                         generate_schema_name (dataset routing)
│   └── models/
│       ├── landing/                    lnd_measurements, lnd_instrument_data
│       ├── logic/                      measurements_long > _with_status > _clean
│       └── presentation/              dashboard_wide
├── terraform/                        Infrastructure as Code
│   ├── bootstrap/                      GCP project, APIs, state bucket, KMS, WIF
│   ├── modules/                        bigquery, cloud_run, artifact_registry, iam, kms, workload_identity
│   └── terraform.tfvars.enc            SOPS-encrypted variables
├── .github/
│   ├── workflows/                      Terraform + Docker CI/CD
│   └── CODEOWNERS                      Infra review requirements
├── scripts/                          Automation
│   ├── export_models.py                Serialize pipelines for serving
│   ├── train_with_mlflow.py            Train with experiment logging
│   └── log_experiments.py              Backfill experiments to MLflow
├── notebooks/                        EDA, forecasting, anomaly, LSTM experiment
├── tests/                            pytest suite (API + pipeline tests)
├── outputs/                          Prediction CSVs and validation plots
├── .sops.yaml                        SOPS encryption rules (GCP KMS)
├── Dockerfile                        Cloud Run-ready container
├── docker-compose.yml                Local dev: API + MLflow + Dashboard
├── Makefile                          All project operations (make help)
├── experiments.md                    Full experiment log with rationale
└── decisions.md                      Architectural decision records
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
