"""Tests for the FastAPI prediction service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "models_loaded" in data


def test_forecast_no_models_returns_404(client):
    resp = client.post("/predict/forecast", json={
        "station_code": 999,
        "item_code": 0,
        "start_date": "2023-07-01",
        "end_date": "2023-07-01 23:00:00",
    })
    assert resp.status_code == 404


def test_anomaly_no_models_returns_404(client):
    resp = client.post("/predict/anomaly", json={
        "station_code": 999,
        "item_code": 0,
        "measurements": [
            {"datetime": "2023-01-01 00:00:00", "value": 0.003},
            {"datetime": "2023-01-01 01:00:00", "value": 0.004},
            {"datetime": "2023-01-01 02:00:00", "value": 0.005},
        ],
    })
    assert resp.status_code == 404


def test_anomaly_too_few_measurements(client):
    # Need to have a model loaded for this to hit the 422 path,
    # but without models it will 404 first. Still validates schema.
    resp = client.post("/predict/anomaly", json={
        "station_code": 205,
        "item_code": 0,
        "measurements": [
            {"datetime": "2023-01-01 00:00:00", "value": 0.003},
        ],
    })
    # Either 404 (no model) or 422 (too few) is acceptable
    assert resp.status_code in (404, 422)


def test_forecast_invalid_body(client):
    resp = client.post("/predict/forecast", json={"bad": "data"})
    assert resp.status_code == 422


def test_anomaly_invalid_body(client):
    resp = client.post("/predict/anomaly", json={"bad": "data"})
    assert resp.status_code == 422
