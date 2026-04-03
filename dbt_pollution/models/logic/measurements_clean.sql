{{-
  config(
    materialized='table'
  )
-}}

-- Cleaned measurements with nulls handled, temporal features, and air quality classification.

SELECT
    m.measurement_datetime
    , m.station_code
    , m.latitude
    , m.longitude
    , m.item_code
    , m.item_name
    , m.value AS raw_value
    , CASE WHEN m.value = -1 THEN NULL ELSE m.value END AS clean_value
    , m.instrument_status
    , COALESCE(m.instrument_status, -1) AS status_filled

    -- Temporal features
    , EXTRACT(YEAR FROM m.measurement_datetime)::INT AS year
    , EXTRACT(MONTH FROM m.measurement_datetime)::INT AS month
    , EXTRACT(DAY FROM m.measurement_datetime)::INT AS day
    , EXTRACT(HOUR FROM m.measurement_datetime)::INT AS hour
    , EXTRACT(DOW FROM m.measurement_datetime)::INT AS day_of_week
    , EXTRACT(DOY FROM m.measurement_datetime)::INT AS day_of_year
    , CASE
        WHEN EXTRACT(MONTH FROM m.measurement_datetime) IN (12, 1, 2) THEN 'Winter'
        WHEN EXTRACT(MONTH FROM m.measurement_datetime) IN (3, 4, 5) THEN 'Spring'
        WHEN EXTRACT(MONTH FROM m.measurement_datetime) IN (6, 7, 8) THEN 'Summer'
        WHEN EXTRACT(MONTH FROM m.measurement_datetime) IN (9, 10, 11) THEN 'Fall'
      END AS season

    -- Air quality classification based on pollutant thresholds
    , CASE
        WHEN m.value = -1 THEN NULL
        WHEN m.value <= p.good THEN 'Good'
        WHEN m.value <= p.normal THEN 'Normal'
        WHEN m.value <= p.bad THEN 'Bad'
        ELSE 'Very bad'
      END AS air_quality
FROM {{ ref('measurements_with_status') }} m
    LEFT JOIN {{ ref('lnd_pollutants') }} p
        ON m.item_code = p.item_code
