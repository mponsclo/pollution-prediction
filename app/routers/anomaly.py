"""Anomaly detection endpoint."""

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from app.schemas import AnomalyPoint, AnomalyRequest, AnomalyResponse
from src.anomaly.detector import predict_anomalies

router = APIRouter()


@router.post("/predict/anomaly", response_model=AnomalyResponse)
def predict_anomaly(request: Request, body: AnomalyRequest):
    models = getattr(request.app.state, "models", {})
    key = ("anomaly", body.station_code, body.item_code)

    if key not in models:
        available = [f"{k[1]}/{k[2]}" for k in models if k[0] == "anomaly"]
        raise HTTPException(
            status_code=404,
            detail=f"No anomaly model for station {body.station_code}, "
            f"item_code {body.item_code}. Available: {available}",
        )

    if len(body.measurements) < 3:
        raise HTTPException(status_code=422, detail="Need at least 3 measurements")

    pipeline = models[key]

    # Build DataFrame from input
    df = pd.DataFrame([{"measurement_datetime": m.datetime, "clean_value": m.value} for m in body.measurements])
    df["measurement_datetime"] = pd.to_datetime(df["measurement_datetime"])
    df = df.set_index("measurement_datetime").sort_index()

    # Fill any gaps
    df["clean_value"] = df["clean_value"].ffill().bfill()

    result = predict_anomalies(pipeline, df)

    predictions = [
        AnomalyPoint(
            measurement_datetime=str(dt),
            is_anomaly=bool(result.loc[dt, "is_anomaly"]),
            anomaly_score=round(float(result.loc[dt, "anomaly_probability"]), 6),
        )
        for dt in result.index
    ]

    return AnomalyResponse(
        station_code=body.station_code,
        item_code=body.item_code,
        predictions=predictions,
    )
