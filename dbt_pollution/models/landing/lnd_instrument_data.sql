{{- 
  config(
    materialized='view'
  )
-}}

SELECT
  measurement_date::DATETIME AS measurement_datetime
  , station_code::INT AS station_code
  , item_code::INT AS item_code
  , average_value::NUMERIC AS average_value
  , instrument_status::INT AS instrument_status
FROM {{ ref("instrument_data") }}