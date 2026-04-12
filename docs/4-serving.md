# 4. API Serving (FastAPI + Cloud Run)

FastAPI wraps the trained pipelines behind typed endpoints, deployed on Cloud Run with zero-to-three autoscaling.

## Architecture

- **Startup** — [`app/main.py`](../app/main.py) uses a FastAPI `lifespan` handler to load all serialized pipelines from `outputs/models/` into memory once, avoiding per-request deserialization.
- **Routers** — split by domain in [`app/routers/`](../app/routers/): `health.py`, `forecast.py`, `anomaly.py`.
- **Schemas** — Pydantic models in [`app/schemas.py`](../app/schemas.py) provide request/response validation and auto-generate OpenAPI docs at `/docs`.
- **Live features** — at prediction time, cross-station spatial and cross-pollutant features are computed via BigQuery queries against `measurements_clean`.

## Endpoints

### `GET /health`

Liveness + model-loading check:

```bash
curl http://localhost:8080/health
# {"status": "healthy", "models_loaded": 12}
```

### `POST /predict/forecast`

Hourly point forecast with calibrated 90% prediction intervals. Max range: 2 months.

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

Response: `{station_code, item_code, predictions: [{measurement_datetime, predicted_value, predicted_lower_90, predicted_upper_90}, ...]}`.

### `POST /predict/anomaly`

Classifies each measurement as normal or anomalous. Requires ≥3 consecutive hourly measurements (rolling features need a minimum window).

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

## Container

[`Dockerfile`](../Dockerfile) — `python:3.12-slim` base, installs `build-essential` for LightGBM, copies `src/`, `app/`, and `outputs/models/`, exposes `8080`, starts uvicorn.

Current size: pinned at `python:3.12-slim`. Model pickles are baked into the image — see [README Production Roadmap](../README.md) for how this would move to GCS in a production setup.

## Cloud Run Configuration

- **Region**: `asia-northeast3` (Seoul — co-located with BigQuery data)
- **Scaling**: min 0, max 3 instances
- **Concurrency**: 80 requests per instance (FastAPI async)
- **Auth**: public for the hackathon / portfolio demo; would be `--no-allow-unauthenticated` + IAM in production

Deployed automatically on every push to `main` that touches `app/`, `src/`, `Dockerfile`, or `requirements.txt` via the `docker-build-deploy.yml` workflow.

## Local Dev

```bash
make serve                        # uvicorn with --reload
make docker-build && make docker-run
make docker-compose-up            # API + MLflow + Dashboard
```

Interactive docs at `http://localhost:8080/docs` (Swagger UI) or `/redoc`.

## Tests

[`tests/test_api.py`](../tests/test_api.py) covers health, forecast missing-models, anomaly missing-models, anomaly too-few-measurements, and Pydantic validation on both endpoints. 7 tests, all passing.
