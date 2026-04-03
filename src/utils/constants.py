"""Project-wide constants for the air quality prediction project."""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "dbt_pollution", "dev.duckdb")

# Pollutant item codes
ITEM_CODES = {
    "so2": 0,
    "no2": 2,
    "co": 4,
    "o3": 5,
    "pm10": 7,
    "pm2.5": 8,
}

ITEM_NAMES = {v: k for k, v in ITEM_CODES.items()}

# Instrument status codes
STATUS_NORMAL = 0
STATUS_CALIBRATION = 1
STATUS_ABNORMAL = 2
STATUS_POWER_CUT = 4
STATUS_UNDER_REPAIR = 8
STATUS_ABNORMAL_DATA = 9

# Forecast targets (Task 2)
FORECAST_TARGETS = [
    {"station_code": 206, "item_code": 0, "item_name": "so2", "start": "2023-07-01", "end": "2023-07-31 23:00:00"},
    {"station_code": 211, "item_code": 2, "item_name": "no2", "start": "2023-08-01", "end": "2023-08-31 23:00:00"},
    {"station_code": 217, "item_code": 5, "item_name": "o3", "start": "2023-09-01", "end": "2023-09-30 23:00:00"},
    {"station_code": 219, "item_code": 4, "item_name": "co", "start": "2023-10-01", "end": "2023-10-31 23:00:00"},
    {"station_code": 225, "item_code": 7, "item_name": "pm10", "start": "2023-11-01", "end": "2023-11-30 23:00:00"},
    {"station_code": 228, "item_code": 8, "item_name": "pm2.5", "start": "2023-12-01", "end": "2023-12-31 23:00:00"},
]

# Anomaly detection targets (Task 3)
ANOMALY_TARGETS = [
    {"station_code": 205, "item_code": 0, "item_name": "so2", "start": "2023-11-01", "end": "2023-11-30 23:00:00"},
    {"station_code": 209, "item_code": 2, "item_name": "no2", "start": "2023-09-01", "end": "2023-09-30 23:00:00"},
    {"station_code": 223, "item_code": 5, "item_name": "o3", "start": "2023-07-01", "end": "2023-07-31 23:00:00"},
    {"station_code": 224, "item_code": 4, "item_name": "co", "start": "2023-10-01", "end": "2023-10-31 23:00:00"},
    {"station_code": 226, "item_code": 7, "item_name": "pm10", "start": "2023-08-01", "end": "2023-08-31 23:00:00"},
    {"station_code": 227, "item_code": 8, "item_name": "pm2.5", "start": "2023-12-01", "end": "2023-12-31 23:00:00"},
]
