{{-
  config(
    materialized='view'
  )
-}}

SELECT
  CAST(measurement_date AS DATETIME) AS measurement_datetime
  , CAST(station_code AS INT64) AS station_code
  , CAST(item_code AS INT64) AS item_code
  , CAST(average_value AS NUMERIC) AS average_value
  , CAST(instrument_status AS INT64) AS instrument_status
FROM {{ ref("instrument_data") }}
