import { runQuery } from "./bq";
import {
  BQ_DATASET_PRESENTATION,
  BQ_PROJECT,
  POLLUTANT_BY_CODE,
  type Pollutant,
} from "./constants";

const TABLE = `\`${BQ_PROJECT}.${BQ_DATASET_PRESENTATION}.dashboard_wide\``;

function resolvePollutant(code: number): Pollutant {
  const pollutant = POLLUTANT_BY_CODE[code];
  if (!pollutant) {
    throw new Error(`Unknown pollutant code: ${code}`);
  }
  return pollutant;
}

export type TimeSeriesRow = {
  measurement_datetime: string;
  station_code: number;
  value: number | null;
  instrument_status: number;
};

export async function fetchTimeSeries(args: {
  pollutantCode: number;
  stations: number[];
  start: string;
  end: string;
}): Promise<TimeSeriesRow[]> {
  const pollutant = resolvePollutant(args.pollutantCode);
  const sql = `
    SELECT
      FORMAT_DATETIME('%Y-%m-%dT%H:%M:%S', measurement_datetime) AS measurement_datetime,
      station_code,
      CAST(${pollutant.column} AS FLOAT64) AS value,
      instrument_status
    FROM ${TABLE}
    WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
      AND station_code IN UNNEST(@stations)
    ORDER BY measurement_datetime, station_code
  `;
  return runQuery<TimeSeriesRow>(sql, {
    start: args.start,
    end: args.end,
    stations: args.stations,
  });
}

export type StationLatestRow = {
  station_code: number;
  latitude: number;
  longitude: number;
  value: number | null;
  record_count: number;
  dominant_status: number;
};

export async function fetchStationsLatest(args: {
  pollutantCode: number;
  start: string;
  end: string;
}): Promise<StationLatestRow[]> {
  const pollutant = resolvePollutant(args.pollutantCode);
  const sql = `
    WITH stations AS (
      SELECT
        station_code,
        ANY_VALUE(latitude) AS latitude,
        ANY_VALUE(longitude) AS longitude
      FROM ${TABLE}
      GROUP BY station_code
    ),
    windowed AS (
      SELECT
        station_code,
        CAST(${pollutant.column} AS FLOAT64) AS value,
        instrument_status
      FROM ${TABLE}
      WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
    ),
    agg AS (
      SELECT
        station_code,
        AVG(value) AS value,
        COUNT(value) AS record_count
      FROM windowed
      GROUP BY station_code
    ),
    dominant AS (
      SELECT
        station_code,
        instrument_status,
        COUNT(*) AS n,
        ROW_NUMBER() OVER (PARTITION BY station_code ORDER BY COUNT(*) DESC) AS rn
      FROM windowed
      GROUP BY station_code, instrument_status
    )
    SELECT
      s.station_code,
      s.latitude,
      s.longitude,
      a.value,
      COALESCE(a.record_count, 0) AS record_count,
      d.instrument_status AS dominant_status
    FROM stations s
    LEFT JOIN agg a ON s.station_code = a.station_code
    LEFT JOIN dominant d ON s.station_code = d.station_code AND d.rn = 1
    ORDER BY s.station_code
  `;
  return runQuery<StationLatestRow>(sql, {
    start: args.start,
    end: args.end,
  });
}

export type MissingByPollutantRow = { pollutant: string; missing_pct: number };
export type StatusAvailabilityRow = {
  station_code: number;
  availability_pct: number;
};
export type MonthlyQualityRow = {
  month: string;
  status_pct: number;
  valid_pct: number;
};

export async function fetchMissingByPollutant(args: {
  start: string;
  end: string;
}): Promise<MissingByPollutantRow[]> {
  const sql = `
    SELECT pollutant, SAFE_DIVIDE(missing, total) * 100 AS missing_pct FROM (
      SELECT
        'SO₂' AS pollutant,
        COUNTIF(so2_value IS NULL) AS missing,
        COUNT(*) AS total
      FROM ${TABLE}
      WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
      UNION ALL
      SELECT 'NO₂', COUNTIF(no2_value IS NULL), COUNT(*) FROM ${TABLE}
      WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
      UNION ALL
      SELECT 'O₃', COUNTIF(o3_value IS NULL), COUNT(*) FROM ${TABLE}
      WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
      UNION ALL
      SELECT 'CO', COUNTIF(co_value IS NULL), COUNT(*) FROM ${TABLE}
      WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
      UNION ALL
      SELECT 'PM10', COUNTIF(pm10_value IS NULL), COUNT(*) FROM ${TABLE}
      WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
      UNION ALL
      SELECT 'PM2.5', COUNTIF(pm2_5_value IS NULL), COUNT(*) FROM ${TABLE}
      WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
    )
  `;
  return runQuery<MissingByPollutantRow>(sql, {
    start: args.start,
    end: args.end,
  });
}

export async function fetchStatusAvailability(args: {
  start: string;
  end: string;
}): Promise<StatusAvailabilityRow[]> {
  const sql = `
    SELECT
      station_code,
      SAFE_DIVIDE(COUNTIF(instrument_status IS NOT NULL), COUNT(*)) * 100 AS availability_pct
    FROM ${TABLE}
    WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
    GROUP BY station_code
    ORDER BY availability_pct
  `;
  return runQuery<StatusAvailabilityRow>(sql, {
    start: args.start,
    end: args.end,
  });
}

export async function fetchMonthlyQuality(args: {
  start: string;
  end: string;
}): Promise<MonthlyQualityRow[]> {
  const sql = `
    SELECT
      FORMAT_DATETIME('%Y-%m', measurement_datetime) AS month,
      SAFE_DIVIDE(COUNTIF(instrument_status IS NOT NULL), COUNT(*)) * 100 AS status_pct,
      SAFE_DIVIDE(COUNTIF(so2_value IS NOT NULL), COUNT(*)) * 100 AS valid_pct
    FROM ${TABLE}
    WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
    GROUP BY month
    ORDER BY month
  `;
  return runQuery<MonthlyQualityRow>(sql, {
    start: args.start,
    end: args.end,
  });
}

export type StatsRow = {
  station_code: number;
  n: number;
  mean: number;
  stddev: number;
  min: number;
  max: number;
  p50: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
};

export async function fetchStats(args: {
  pollutantCode: number;
  start: string;
  end: string;
}): Promise<StatsRow[]> {
  const pollutant = resolvePollutant(args.pollutantCode);
  const sql = `
    WITH src AS (
      SELECT station_code, CAST(${pollutant.column} AS FLOAT64) AS v
      FROM ${TABLE}
      WHERE measurement_datetime BETWEEN DATETIME(@start) AND DATETIME(@end)
    )
    SELECT
      station_code,
      COUNT(v) AS n,
      AVG(v) AS mean,
      STDDEV(v) AS stddev,
      MIN(v) AS min,
      MAX(v) AS max,
      APPROX_QUANTILES(v, 100)[OFFSET(50)] AS p50,
      APPROX_QUANTILES(v, 100)[OFFSET(75)] AS p75,
      APPROX_QUANTILES(v, 100)[OFFSET(90)] AS p90,
      APPROX_QUANTILES(v, 100)[OFFSET(95)] AS p95,
      APPROX_QUANTILES(v, 100)[OFFSET(99)] AS p99
    FROM src
    GROUP BY station_code
    ORDER BY station_code
  `;
  return runQuery<StatsRow>(sql, {
    start: args.start,
    end: args.end,
  });
}
