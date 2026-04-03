{{-
  config(
    materialized='table'
  )
-}}

-- Pivot long-format measurements_clean back to wide format for the Streamlit dashboard.
-- Groups by datetime/station and aggregates each pollutant + status into columns.

SELECT
    m.measurement_datetime
    , m.station_code
    , m.latitude
    , m.longitude
    , MAX(CASE WHEN m.item_code = 0 THEN m.clean_value END) AS so2_value
    , MAX(CASE WHEN m.item_code = 2 THEN m.clean_value END) AS no2_value
    , MAX(CASE WHEN m.item_code = 5 THEN m.clean_value END) AS o3_value
    , MAX(CASE WHEN m.item_code = 4 THEN m.clean_value END) AS co_value
    , MAX(CASE WHEN m.item_code = 7 THEN m.clean_value END) AS pm10_value
    , MAX(CASE WHEN m.item_code = 8 THEN m.clean_value END) AS pm2_5_value
    -- Use worst (highest) status across pollutants as overall status
    , MAX(m.instrument_status) AS instrument_status
FROM {{ ref('measurements_clean') }} m
GROUP BY m.measurement_datetime, m.station_code, m.latitude, m.longitude
ORDER BY m.measurement_datetime, m.station_code
