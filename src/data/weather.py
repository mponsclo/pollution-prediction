"""Weather data fetcher and loader using Open-Meteo Historical API.

Downloads hourly weather for 3 representative points in Seoul, caches to CSV,
and provides IDW-interpolated weather features per station.
"""

import os
import time

import numpy as np
import pandas as pd
import requests

from src.utils.constants import PROJECT_ROOT

CACHE_PATH = os.path.join(PROJECT_ROOT, "data", "weather_cache.csv")

# 3 representative weather points covering the Seoul station network
WEATHER_POINTS = [
    {"name": "center", "lat": 37.55, "lon": 127.00},
    {"name": "nw", "lat": 37.65, "lon": 126.90},
    {"name": "se", "lat": 37.47, "lon": 127.10},
]

HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "pressure_msl",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
    "cloud_cover",
    "shortwave_radiation",
]


def fetch_weather(
    start_date: str = "2021-01-01",
    end_date: str = "2023-12-31",
) -> pd.DataFrame:
    """Fetch hourly weather from Open-Meteo for all representative points."""
    all_data = []

    for point in WEATHER_POINTS:
        print(f"  Fetching weather for {point['name']} ({point['lat']}, {point['lon']})...")

        # Split into yearly chunks to avoid timeouts
        for year_start, year_end in [
            ("2021-01-01", "2021-12-31"),
            ("2022-01-01", "2022-12-31"),
            ("2023-01-01", "2023-12-31"),
        ]:
            # Clip to requested range
            ys = max(year_start, start_date)
            ye = min(year_end, end_date)
            if ys > ye:
                continue

            url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": point["lat"],
                "longitude": point["lon"],
                "start_date": ys,
                "end_date": ye,
                "hourly": ",".join(HOURLY_PARAMS),
                "timezone": "Asia/Seoul",
            }

            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            hourly = data["hourly"]
            df = pd.DataFrame(hourly)
            df["time"] = pd.to_datetime(df["time"])
            df["point_name"] = point["name"]
            df["point_lat"] = point["lat"]
            df["point_lon"] = point["lon"]
            all_data.append(df)

            time.sleep(0.5)  # rate limit courtesy

    result = pd.concat(all_data, ignore_index=True)
    return result


def download_and_cache() -> pd.DataFrame:
    """Download weather data and save to CSV cache."""
    print("Downloading weather data from Open-Meteo...")
    df = fetch_weather()
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    df.to_csv(CACHE_PATH, index=False)
    print(f"Cached {len(df)} rows to {CACHE_PATH}")
    return df


def load_weather_cache() -> pd.DataFrame:
    """Load cached weather data, downloading if necessary."""
    if not os.path.exists(CACHE_PATH):
        return download_and_cache()

    df = pd.read_csv(CACHE_PATH)
    df["time"] = pd.to_datetime(df["time"])
    return df


def get_weather_for_station(
    station_lat: float,
    station_lon: float,
    index: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Get IDW-interpolated weather features for a specific station location.

    Uses inverse-distance weighting across the 3 representative weather points.
    """
    weather = load_weather_cache()

    # Compute IDW weights for this station
    dists = []
    for point in WEATHER_POINTS:
        d = np.sqrt((station_lat - point["lat"]) ** 2 + (station_lon - point["lon"]) ** 2)
        dists.append(max(d, 1e-6))
    dists = np.array(dists)
    weights = 1.0 / dists**2
    weights /= weights.sum()

    # Pivot weather data: one column per point per variable
    result = pd.DataFrame(index=index)

    for param in HOURLY_PARAMS:
        weighted_sum = np.zeros(len(index))

        for i, point in enumerate(WEATHER_POINTS):
            point_data = weather[weather["point_name"] == point["name"]].copy()
            point_data = point_data.set_index("time")[param]
            # Reindex to match the requested timestamps
            aligned = point_data.reindex(index).ffill().bfill()
            weighted_sum += aligned.values * weights[i]

        result[f"weather_{param}"] = weighted_sum

    return result


def get_weather_stats_for_prediction(
    station_lat: float,
    station_lon: float,
) -> dict:
    """Compute monthly×hourly weather averages for future prediction.

    Since we don't have weather forecasts for the prediction period,
    we use historical averages as the best available proxy.
    """
    weather = load_weather_cache()

    # Compute IDW weights
    dists = []
    for point in WEATHER_POINTS:
        d = np.sqrt((station_lat - point["lat"]) ** 2 + (station_lon - point["lon"]) ** 2)
        dists.append(max(d, 1e-6))
    dists = np.array(dists)
    weights = 1.0 / dists**2
    weights /= weights.sum()

    # Compute IDW-weighted weather at this station for all historical timestamps
    center = weather[weather["point_name"] == "center"].copy()
    center = center.set_index("time")

    combined = pd.DataFrame(index=center.index)
    for param in HOURLY_PARAMS:
        weighted_sum = np.zeros(len(center))
        for i, point in enumerate(WEATHER_POINTS):
            point_data = weather[weather["point_name"] == point["name"]].set_index("time")[param]
            aligned = point_data.reindex(center.index).ffill().bfill()
            weighted_sum += aligned.values * weights[i]
        combined[param] = weighted_sum

    # Compute month×hour averages
    combined["month"] = combined.index.month
    combined["hour"] = combined.index.hour
    stats = combined.groupby(["month", "hour"]).mean().to_dict()

    return stats


def get_weather_features_for_prediction(
    prediction_index: pd.DatetimeIndex,
    station_lat: float,
    station_lon: float,
) -> pd.DataFrame:
    """Get weather features for future timestamps using historical averages."""
    stats = get_weather_stats_for_prediction(station_lat, station_lon)

    result = pd.DataFrame(index=prediction_index)
    for param in HOURLY_PARAMS:
        param_stats = stats.get(param, {})
        values = []
        for dt in prediction_index:
            key = (dt.month, dt.hour)
            values.append(param_stats.get(key, 0))
        result[f"weather_{param}"] = values

    return result
