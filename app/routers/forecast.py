"""Forecast prediction endpoint."""

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from app.schemas import ForecastPoint, ForecastRequest, ForecastResponse
from src.forecasting.train_lgbm_ensemble import predict_with_pipeline

router = APIRouter()


@router.post("/predict/forecast", response_model=ForecastResponse)
def predict_forecast(request: Request, body: ForecastRequest):
    models = getattr(request.app.state, "models", {})
    key = ("forecast", body.station_code, body.item_code)

    if key not in models:
        available = [f"{k[1]}/{k[2]}" for k in models if k[0] == "forecast"]
        raise HTTPException(
            status_code=404,
            detail=f"No forecast model for station {body.station_code}, "
            f"item_code {body.item_code}. Available: {available}",
        )

    pipeline = models[key]
    pred_index = pd.date_range(body.start_date, body.end_date, freq="h")

    if len(pred_index) == 0:
        raise HTTPException(status_code=422, detail="Invalid date range (0 hours)")

    if len(pred_index) > 744 * 2:
        raise HTTPException(status_code=422, detail="Date range too large (max ~2 months)")

    result = predict_with_pipeline(pipeline, pred_index)

    predictions = [
        ForecastPoint(
            measurement_datetime=str(dt),
            predicted_value=round(float(result.loc[dt, "ensemble"]), 6),
            predicted_lower_90=round(float(result.loc[dt, "q05"]), 6),
            predicted_upper_90=round(float(result.loc[dt, "q95"]), 6),
        )
        for dt in pred_index
    ]

    return ForecastResponse(
        station_code=body.station_code,
        item_code=body.item_code,
        predictions=predictions,
    )
