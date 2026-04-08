{{-
  config(
    materialized='view'
  )
-}}

SELECT
  CAST(measurement_date AS DATETIME) AS measurement_datetime
  , CAST(station_code AS INT64) AS station_code
  , latitude
  , longitude
  , CAST(SO2 AS NUMERIC) AS so2_value
  , CAST(NO2 AS NUMERIC) AS no2_value
  , CAST(O3 AS NUMERIC) AS o3_value
  , CAST(CO AS NUMERIC) AS co_value
  , CAST(PM10 AS NUMERIC) AS pm10_value
  , CAST(PM2_5 AS NUMERIC) AS pm2_5_value
FROM {{ ref("measurement_data") }}
