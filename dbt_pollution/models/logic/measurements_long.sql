{{-
  config(
    materialized='table'
  )
-}}

-- Unpivot wide-format measurements into long format (one row per station/datetime/pollutant).
-- This enables a clean 1:1 join with instrument_data on (datetime, station, item_code).
-- Item code mapping from pollutant_data.csv:
--   0 = SO2, 2 = NO2, 4 = CO, 5 = O3, 7 = PM10, 8 = PM2.5

SELECT measurement_datetime, station_code, latitude, longitude, 0 AS item_code, so2_value AS value
FROM {{ ref('lnd_measurements') }}

UNION ALL

SELECT measurement_datetime, station_code, latitude, longitude, 2 AS item_code, no2_value AS value
FROM {{ ref('lnd_measurements') }}

UNION ALL

SELECT measurement_datetime, station_code, latitude, longitude, 4 AS item_code, co_value AS value
FROM {{ ref('lnd_measurements') }}

UNION ALL

SELECT measurement_datetime, station_code, latitude, longitude, 5 AS item_code, o3_value AS value
FROM {{ ref('lnd_measurements') }}

UNION ALL

SELECT measurement_datetime, station_code, latitude, longitude, 7 AS item_code, pm10_value AS value
FROM {{ ref('lnd_measurements') }}

UNION ALL

SELECT measurement_datetime, station_code, latitude, longitude, 8 AS item_code, pm2_5_value AS value
FROM {{ ref('lnd_measurements') }}
