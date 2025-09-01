WITH measurements AS (
    SELECT
        measurement_datetime
        , station_code
        , so2_value
        , no2_value
        , o3_value
        , co_value
        , pm10_value
        , pm2_5_value
    FROM {{ ref('lnd_measurements') }}
),

instrument AS (
    SELECT
        measurement_datetime
        , station_code
        , instrument_status
        , SUM(IF(item_name = 'o3', average_value, null)) AS o3_value
        , SUM(IF(item_name = 'pm10', average_value, null)) AS pm10_value
        , SUM(IF(item_name = 'pm2.5', average_value, null)) AS pm2_5_value
        , SUM(IF(item_name = 'co', average_value, null)) AS co_value
        , SUM(IF(item_name = 'no2', average_value, null)) AS no2_value
        , SUM(IF(item_name = 'so2', average_value, null)) AS so2_value
    FROM {{ ref('lnd_instrument_data') }} i
        LEFT JOIN {{ ref('lnd_pollutants') }} p ON i.item_code = p.item_code
    GROUP BY measurement_datetime, station_code, instrument_status
)

SELECT
    COALESCE(m.measurement_datetime, i.measurement_datetime) AS measurement_datetime
    , COALESCE(m.station_code, i.station_code) AS station_code
    , i.instrument_status AS instrument_status
    , m.so2_value AS so2_value_meas
    , i.so2_value AS so2_value_instr
    , m.no2_value AS no2_value_meas
    , i.no2_value AS no2_value_instr
    , m.o3_value AS o3_value_meas
    , i.o3_value AS o3_value_instr
    , m.co_value AS co_value_meas
    , i.co_value AS co_value_instr
    , m.pm10_value AS pm10_value_meas
    , i.pm10_value AS pm10_value_instr
    , m.pm2_5_value AS pm2_5_value_meas
    , i.pm2_5_value AS pm2_5_value_instr
FROM measurements m
    FULL JOIN instrument i ON m.station_code = i.station_code AND m.measurement_datetime = i.measurement_datetime
WHERE true
    AND ((IFNULL(m.so2_value, 0) <> IFNULL(i.so2_value, 0) AND i.so2_value IS NOT NULL)
        OR (IFNULL(m.no2_value, 0) <> IFNULL(i.no2_value, 0) AND i.no2_value IS NOT NULL)
        OR (IFNULL(m.o3_value, 0) <> IFNULL(i.o3_value, 0) AND i.o3_value IS NOT NULL)
        OR (IFNULL(m.co_value, 0) <> IFNULL(i.co_value, 0) AND i.co_value IS NOT NULL)
        OR (IFNULL(m.pm10_value, 0) <> IFNULL(i.pm10_value, 0) AND i.pm10_value IS NOT NULL)
        OR (IFNULL(m.pm2_5_value, 0) <> IFNULL(i.pm2_5_value, 0)) AND i.pm2_5_value IS NOT NULL)

-- Values -- Measurements have more values than instrument. When in both tables, the values are the same.
-- Values -- Measuremnt/Instruments have several values with -1, not nulls

-- We can skip the values from instruments and only use the instrument status to know the quality of the measurements.
-- Check if there are all the instrument values for all the datetimes in the measurements table.
-- Review -1 values with visualizations/per station. Check if a feed/back-forward filling is enough.