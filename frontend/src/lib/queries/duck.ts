import { runQuery } from "../duck";
import { POLLUTANT_BY_CODE, type Pollutant } from "../constants";

const TABLE = "dashboard_wide";

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
  // Stations are validated against the STATION_CODES allowlist in params.ts,
  // so inlining them is safe and avoids DuckDB's LIST-binding type ambiguity.
  const stationList = args.stations.map((s) => Math.trunc(s)).join(", ") || "NULL";
  const sql = `
    SELECT
      strftime(measurement_datetime, '%Y-%m-%dT%H:%M:%S') AS measurement_datetime,
      station_code::INTEGER AS station_code,
      CAST(${pollutant.column} AS DOUBLE) AS value,
      instrument_status::INTEGER AS instrument_status
    FROM ${TABLE}
    WHERE measurement_datetime BETWEEN CAST($start AS TIMESTAMP) AND CAST($end AS TIMESTAMP)
      AND station_code IN (${stationList})
    ORDER BY measurement_datetime, station_code
  `;
  return runQuery<TimeSeriesRow>(sql, {
    start: args.start,
    end: args.end,
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
        any_value(latitude) AS latitude,
        any_value(longitude) AS longitude
      FROM ${TABLE}
      GROUP BY station_code
    ),
    windowed AS (
      SELECT
        station_code,
        CAST(${pollutant.column} AS DOUBLE) AS value,
        instrument_status
      FROM ${TABLE}
      WHERE measurement_datetime BETWEEN CAST($start AS TIMESTAMP) AND CAST($end AS TIMESTAMP)
    ),
    agg AS (
      SELECT
        station_code,
        AVG(value) AS value,
        COUNT(value)::INTEGER AS record_count
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
      s.station_code::INTEGER AS station_code,
      s.latitude,
      s.longitude,
      a.value,
      COALESCE(a.record_count, 0)::INTEGER AS record_count,
      d.instrument_status::INTEGER AS dominant_status
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
    WITH scope AS (
      SELECT *
      FROM ${TABLE}
      WHERE measurement_datetime BETWEEN CAST($start AS TIMESTAMP) AND CAST($end AS TIMESTAMP)
    )
    SELECT 'SO₂' AS pollutant,
           (COUNT(*) FILTER (WHERE so2_value IS NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100 AS missing_pct
    FROM scope
    UNION ALL
    SELECT 'NO₂',
           (COUNT(*) FILTER (WHERE no2_value IS NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100
    FROM scope
    UNION ALL
    SELECT 'O₃',
           (COUNT(*) FILTER (WHERE o3_value IS NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100
    FROM scope
    UNION ALL
    SELECT 'CO',
           (COUNT(*) FILTER (WHERE co_value IS NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100
    FROM scope
    UNION ALL
    SELECT 'PM10',
           (COUNT(*) FILTER (WHERE pm10_value IS NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100
    FROM scope
    UNION ALL
    SELECT 'PM2.5',
           (COUNT(*) FILTER (WHERE pm2_5_value IS NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100
    FROM scope
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
      station_code::INTEGER AS station_code,
      (COUNT(*) FILTER (WHERE instrument_status IS NOT NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100 AS availability_pct
    FROM ${TABLE}
    WHERE measurement_datetime BETWEEN CAST($start AS TIMESTAMP) AND CAST($end AS TIMESTAMP)
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
      strftime(measurement_datetime, '%Y-%m') AS month,
      (COUNT(*) FILTER (WHERE instrument_status IS NOT NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100 AS status_pct,
      (COUNT(*) FILTER (WHERE so2_value IS NOT NULL))::DOUBLE / NULLIF(COUNT(*), 0) * 100 AS valid_pct
    FROM ${TABLE}
    WHERE measurement_datetime BETWEEN CAST($start AS TIMESTAMP) AND CAST($end AS TIMESTAMP)
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
      SELECT station_code, CAST(${pollutant.column} AS DOUBLE) AS v
      FROM ${TABLE}
      WHERE measurement_datetime BETWEEN CAST($start AS TIMESTAMP) AND CAST($end AS TIMESTAMP)
    )
    SELECT
      station_code::INTEGER AS station_code,
      COUNT(v)::INTEGER AS n,
      AVG(v) AS mean,
      stddev_samp(v) AS stddev,
      MIN(v) AS min,
      MAX(v) AS max,
      approx_quantile(v, 0.50) AS p50,
      approx_quantile(v, 0.75) AS p75,
      approx_quantile(v, 0.90) AS p90,
      approx_quantile(v, 0.95) AS p95,
      approx_quantile(v, 0.99) AS p99
    FROM src
    GROUP BY station_code
    ORDER BY station_code
  `;
  return runQuery<StatsRow>(sql, {
    start: args.start,
    end: args.end,
  });
}
