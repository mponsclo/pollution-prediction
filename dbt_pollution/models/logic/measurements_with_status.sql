{{-
  config(
    materialized='table'
  )
-}}

-- Primary analysis table: long-format measurements joined 1:1 with instrument status.
-- Each row represents one pollutant reading at one station at one hour.

SELECT
    m.measurement_datetime
    , m.station_code
    , m.latitude
    , m.longitude
    , m.item_code
    , p.item_name
    , m.value
    , i.instrument_status
FROM {{ ref('measurements_long') }} m
    LEFT JOIN {{ ref('lnd_instrument_data') }} i
        ON m.measurement_datetime = i.measurement_datetime
        AND m.station_code = i.station_code
        AND m.item_code = i.item_code
    LEFT JOIN {{ ref('lnd_pollutants') }} p
        ON m.item_code = p.item_code
