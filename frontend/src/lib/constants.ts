export const BQ_PROJECT = process.env.GCP_PROJECT_ID ?? "mpc-pollution-331382";
export const BQ_DATASET_PRESENTATION = "presentation";
export const BQ_DATASET_LOGIC = "logic";
export const PREDICTIONS_BUCKET =
  process.env.PREDICTIONS_BUCKET ?? "mpc-pollution-331382-artifacts";

export type Pollutant = {
  code: number;
  name: string;
  label: string;
  column: string;
  unit: string;
  threshold: number;
  color: string;
};

export const POLLUTANTS: Pollutant[] = [
  { code: 0, name: "so2", label: "SO₂", column: "so2_value", unit: "ppm", threshold: 0.02, color: "#22d3ee" },
  { code: 2, name: "no2", label: "NO₂", column: "no2_value", unit: "ppm", threshold: 0.03, color: "#a78bfa" },
  { code: 4, name: "co", label: "CO", column: "co_value", unit: "ppm", threshold: 2.0, color: "#f59e0b" },
  { code: 5, name: "o3", label: "O₃", column: "o3_value", unit: "ppm", threshold: 0.03, color: "#34d399" },
  { code: 7, name: "pm10", label: "PM10", column: "pm10_value", unit: "mg/m³", threshold: 30.0, color: "#f472b6" },
  { code: 8, name: "pm2.5", label: "PM2.5", column: "pm2_5_value", unit: "mg/m³", threshold: 15.0, color: "#ef4444" },
];

export const POLLUTANT_BY_CODE: Record<number, Pollutant> = Object.fromEntries(
  POLLUTANTS.map((p) => [p.code, p])
);

export const STATION_CODES: number[] = Array.from(
  { length: 25 },
  (_, i) => 204 + i
);

export const DATA_WINDOW = {
  start: "2021-01-01T00:00:00",
  end: "2023-12-31T23:00:00",
} as const;

export const DEFAULT_RANGE = {
  start: "2023-12-01T00:00:00",
  end: "2023-12-31T23:00:00",
} as const;

export const DEFAULT_POLLUTANT_CODE = 8;

export type InstrumentStatus = {
  code: number;
  label: string;
  color: string;
};

export const STATUSES: InstrumentStatus[] = [
  { code: 0, label: "Normal", color: "#22c55e" },
  { code: 1, label: "Calibration", color: "#eab308" },
  { code: 2, label: "Abnormal", color: "#f97316" },
  { code: 4, label: "Power cut", color: "#6b7280" },
  { code: 8, label: "Under repair", color: "#3b82f6" },
  { code: 9, label: "Abnormal data", color: "#ef4444" },
];

export const STATUS_BY_CODE: Record<number, InstrumentStatus> = Object.fromEntries(
  STATUSES.map((s) => [s.code, s])
);
