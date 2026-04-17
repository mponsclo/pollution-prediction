// Dispatches dashboard queries to the backend selected by DATA_BACKEND.
// Default is `parquet` (DuckDB reading the committed snapshot), which lets the
// app run locally and on Vercel without GCP. Set DATA_BACKEND=bigquery to hit
// BigQuery instead when the GCP project is reachable.

import * as bq from "./queries/bq";
import * as duck from "./queries/duck";

const impl = process.env.DATA_BACKEND === "bigquery" ? bq : duck;

export const fetchTimeSeries = impl.fetchTimeSeries;
export const fetchStationsLatest = impl.fetchStationsLatest;
export const fetchMissingByPollutant = impl.fetchMissingByPollutant;
export const fetchStatusAvailability = impl.fetchStatusAvailability;
export const fetchMonthlyQuality = impl.fetchMonthlyQuality;
export const fetchStats = impl.fetchStats;

export type {
  TimeSeriesRow,
  StationLatestRow,
  MissingByPollutantRow,
  StatusAvailabilityRow,
  MonthlyQualityRow,
  StatsRow,
} from "./queries/duck";
