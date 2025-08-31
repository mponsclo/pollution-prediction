{{- 
  config(
    materialized='table'
  )
-}}

SELECT
  item_code::INT AS item_code
  , LOWER(item_name) AS item_name
  , CASE
      WHEN unit_of_measurement = 'Mircrogram/m3' THEN 'mg/m3'
      ELSE unit_of_measurement
    END AS unit_of_measurement
  , good::NUMERIC AS good
  , normal::NUMERIC AS normal
  , bad::NUMERIC AS bad
  , very_bad::NUMERIC AS very_bad
FROM {{ ref('pollutant_data') }}