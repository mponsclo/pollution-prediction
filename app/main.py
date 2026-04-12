"""Seoul Air Quality Prediction API.

FastAPI application serving forecast and anomaly detection models.
Structured for Google Cloud Run but fully runnable locally.

Usage:
    uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.model_loader import load_models
from app.routers import anomaly, forecast, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup."""
    models = load_models()
    app.state.models = models
    n_forecast = sum(1 for k in models if k[0] == "forecast")
    n_anomaly = sum(1 for k in models if k[0] == "anomaly")
    print(f"Loaded {n_forecast} forecast + {n_anomaly} anomaly models")
    yield


app = FastAPI(
    title="Seoul Air Quality Prediction API",
    description="Hourly pollutant forecasting and instrument anomaly detection for 25 Seoul monitoring stations.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(forecast.router, tags=["Forecast"])
app.include_router(anomaly.router, tags=["Anomaly Detection"])
