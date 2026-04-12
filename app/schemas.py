"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    models_loaded: int


class ForecastRequest(BaseModel):
    station_code: int
    item_code: int
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD HH:MM:SS or YYYY-MM-DD

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "station_code": 206,
                    "item_code": 0,
                    "start_date": "2023-07-01",
                    "end_date": "2023-07-31 23:00:00",
                }
            ]
        }
    }


class ForecastPoint(BaseModel):
    measurement_datetime: str
    predicted_value: float
    predicted_lower_90: float
    predicted_upper_90: float


class ForecastResponse(BaseModel):
    station_code: int
    item_code: int
    predictions: list[ForecastPoint]


class MeasurementInput(BaseModel):
    datetime: str
    value: float


class AnomalyRequest(BaseModel):
    station_code: int
    item_code: int
    measurements: list[MeasurementInput]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "station_code": 205,
                    "item_code": 0,
                    "measurements": [
                        {"datetime": "2023-11-01 00:00:00", "value": 0.003},
                        {"datetime": "2023-11-01 01:00:00", "value": 0.004},
                    ],
                }
            ]
        }
    }


class AnomalyPoint(BaseModel):
    measurement_datetime: str
    is_anomaly: bool
    anomaly_score: float


class AnomalyResponse(BaseModel):
    station_code: int
    item_code: int
    predictions: list[AnomalyPoint]
