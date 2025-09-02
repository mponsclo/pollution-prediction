{{- 
  config(
    materialized='table'
  )
-}}

-- Create the incremental update
WITH measurements AS (
    SELECT *
    FROM {{ ref('lnd_measurements') }}
),

instrument AS (
    SELECT
        measurement_datetime
        , station_code
        , instrument_status
    FROM {{ ref('lnd_instrument_data') }} i
)

SELECT
    m.*
    , i.instrument_status
FROM measurements m
    LEFT JOIN instrument i ON m.station_code = i.station_code AND m.measurement_datetime = i.measurement_datetime
WHERE true
    -- and i.instrument_status is null

-- We can skip the values from instruments and only use the instrument status to know the quality of the measurements.
-- Check if there are all the instrument values for all the datetimes in the measurements table.
-- Review -1 values with visualizations/per station. Check if a feed/back-forward filling is enough.
-- Check periods where the instrument status was null and see how we fill it up. (Add test based on date)