{{- 
  config(
    materialized='view'
  )
-}}

SELECT
  measurement_date::DATETIME AS measurement_datetime
  , station_code::INT AS station_code
  , latitude
  , longitude
  , SO2::NUMERIC AS so2_value
  , NO2::NUMERIC AS no2_value
  , O3::NUMERIC AS o3_value
  , CO::NUMERIC AS co_value
  , PM10::NUMERIC AS pm10_value
  , "PM2.5"::NUMERIC AS pm2_5_value
FROM {{ ref("measurement_data") }}