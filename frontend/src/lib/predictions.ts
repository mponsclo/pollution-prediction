import { readCsvFromBucket } from "./gcs";

export type ForecastRow = {
  measurement_datetime: string;
  station_code: number;
  item_code: number;
  item_name: string;
  predicted_value: number;
  predicted_lower_90: number;
  predicted_upper_90: number;
};

export type AnomalyRow = {
  measurement_datetime: string;
  station_code: number;
  item_code: number;
  item_name: string;
  is_anomaly: number;
  anomaly_score: number;
};

export async function loadForecasts(): Promise<ForecastRow[]> {
  return readCsvFromBucket<ForecastRow>(
    "predictions/forecast_predictions.csv",
  );
}

export async function loadAnomalies(): Promise<AnomalyRow[]> {
  return readCsvFromBucket<AnomalyRow>(
    "predictions/anomaly_predictions.csv",
  );
}

export function listTargets<T extends { station_code: number; item_code: number; item_name: string }>(
  rows: T[],
): { station_code: number; item_code: number; item_name: string; key: string }[] {
  const seen = new Map<string, { station_code: number; item_code: number; item_name: string; key: string }>();
  for (const r of rows) {
    const key = `${r.station_code}-${r.item_code}`;
    if (!seen.has(key)) {
      seen.set(key, {
        station_code: r.station_code,
        item_code: r.item_code,
        item_name: r.item_name,
        key,
      });
    }
  }
  return Array.from(seen.values()).sort((a, b) =>
    a.station_code - b.station_code || a.item_code - b.item_code,
  );
}

export function pickTarget<T extends { station_code: number; item_code: number }>(
  rows: T[],
  stationCode: number | undefined,
  itemCode: number | undefined,
): T[] {
  if (stationCode == null || itemCode == null) return rows;
  return rows.filter(
    (r) => r.station_code === stationCode && r.item_code === itemCode,
  );
}
