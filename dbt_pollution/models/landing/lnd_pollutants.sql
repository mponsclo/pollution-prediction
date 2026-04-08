{{-
  config(
    materialized='table'
  )
-}}

SELECT
  CAST(item_code AS INT64) AS item_code
  , LOWER(item_name) AS item_name
  , CASE
      WHEN unit_of_measurement = 'Mircrogram/m3' THEN 'mg/m3'
      ELSE unit_of_measurement
    END AS unit_of_measurement
  , CAST(good AS NUMERIC) AS good
  , CAST(normal AS NUMERIC) AS normal
  , CAST(bad AS NUMERIC) AS bad
  , CAST(very_bad AS NUMERIC) AS very_bad
FROM {{ ref('pollutant_data') }}
