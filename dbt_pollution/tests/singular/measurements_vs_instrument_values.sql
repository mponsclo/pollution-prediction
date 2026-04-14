-- Consistency check: when a (station, datetime) row exists in both
-- lnd_measurements (wide) and lnd_instrument_data (long), the per-pollutant
-- values must agree. -1 (missing) is treated as 0 for this comparison;
-- rows where the instrument side is NULL are ignored because the
-- measurements table is the broader source.
--
-- The test fails if any disagreeing row is returned.

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
        , SUM(IF(item_name = 'o3',    average_value, NULL)) AS o3_value
        , SUM(IF(item_name = 'pm10',  average_value, NULL)) AS pm10_value
        , SUM(IF(item_name = 'pm2.5', average_value, NULL)) AS pm2_5_value
        , SUM(IF(item_name = 'co',    average_value, NULL)) AS co_value
        , SUM(IF(item_name = 'no2',   average_value, NULL)) AS no2_value
        , SUM(IF(item_name = 'so2',   average_value, NULL)) AS so2_value
    FROM {{ ref('lnd_instrument_data') }} i
        LEFT JOIN {{ ref('lnd_pollutants') }} p ON i.item_code = p.item_code
    GROUP BY measurement_datetime, station_code, instrument_status
)

SELECT
    COALESCE(m.measurement_datetime, i.measurement_datetime) AS measurement_datetime
    , COALESCE(m.station_code, i.station_code)               AS station_code
    , i.instrument_status                                    AS instrument_status
    , m.so2_value   AS so2_value_meas,   i.so2_value   AS so2_value_instr
    , m.no2_value   AS no2_value_meas,   i.no2_value   AS no2_value_instr
    , m.o3_value    AS o3_value_meas,    i.o3_value    AS o3_value_instr
    , m.co_value    AS co_value_meas,    i.co_value    AS co_value_instr
    , m.pm10_value  AS pm10_value_meas,  i.pm10_value  AS pm10_value_instr
    , m.pm2_5_value AS pm2_5_value_meas, i.pm2_5_value AS pm2_5_value_instr
FROM measurements m
    FULL JOIN instrument i
        ON m.station_code = i.station_code
       AND m.measurement_datetime = i.measurement_datetime
WHERE
    (i.so2_value   IS NOT NULL AND IFNULL(m.so2_value, 0)   <> IFNULL(i.so2_value, 0))
 OR (i.no2_value   IS NOT NULL AND IFNULL(m.no2_value, 0)   <> IFNULL(i.no2_value, 0))
 OR (i.o3_value    IS NOT NULL AND IFNULL(m.o3_value, 0)    <> IFNULL(i.o3_value, 0))
 OR (i.co_value    IS NOT NULL AND IFNULL(m.co_value, 0)    <> IFNULL(i.co_value, 0))
 OR (i.pm10_value  IS NOT NULL AND IFNULL(m.pm10_value, 0)  <> IFNULL(i.pm10_value, 0))
 OR (i.pm2_5_value IS NOT NULL AND IFNULL(m.pm2_5_value, 0) <> IFNULL(i.pm2_5_value, 0))
