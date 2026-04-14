import type { TimeSeriesRow } from "./queries";

export function pearson(a: number[], b: number[]): number {
  const n = Math.min(a.length, b.length);
  if (n === 0) return NaN;
  let sx = 0;
  let sy = 0;
  for (let i = 0; i < n; i++) {
    sx += a[i];
    sy += b[i];
  }
  const mx = sx / n;
  const my = sy / n;
  let num = 0;
  let dx = 0;
  let dy = 0;
  for (let i = 0; i < n; i++) {
    const ax = a[i] - mx;
    const ay = b[i] - my;
    num += ax * ay;
    dx += ax * ax;
    dy += ay * ay;
  }
  const denom = Math.sqrt(dx * dy);
  return denom === 0 ? NaN : num / denom;
}

export type CorrelationResult = {
  stations: number[];
  matrix: number[][];
};

export function correlationByStation(
  rows: TimeSeriesRow[],
  stations: number[],
): CorrelationResult {
  const pivot = new Map<string, Map<number, number>>();
  for (const r of rows) {
    if (r.value == null) continue;
    let byStation = pivot.get(r.measurement_datetime);
    if (!byStation) {
      byStation = new Map();
      pivot.set(r.measurement_datetime, byStation);
    }
    byStation.set(r.station_code, r.value);
  }

  const matrix: number[][] = stations.map(() => new Array(stations.length).fill(NaN));

  for (let i = 0; i < stations.length; i++) {
    for (let j = i; j < stations.length; j++) {
      if (i === j) {
        matrix[i][j] = 1;
        continue;
      }
      const xs: number[] = [];
      const ys: number[] = [];
      for (const byStation of pivot.values()) {
        const a = byStation.get(stations[i]);
        const b = byStation.get(stations[j]);
        if (a != null && b != null) {
          xs.push(a);
          ys.push(b);
        }
      }
      const r = pearson(xs, ys);
      matrix[i][j] = r;
      matrix[j][i] = r;
    }
  }

  return { stations, matrix };
}

export function quantile(sorted: number[], q: number): number {
  if (sorted.length === 0) return NaN;
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  }
  return sorted[base];
}

export type OverallStats = {
  n: number;
  mean: number;
  median: number;
  stddev: number;
  min: number;
  max: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
};

export function overallStats(values: number[]): OverallStats {
  const n = values.length;
  if (n === 0) {
    return {
      n: 0,
      mean: NaN,
      median: NaN,
      stddev: NaN,
      min: NaN,
      max: NaN,
      p75: NaN,
      p90: NaN,
      p95: NaN,
      p99: NaN,
    };
  }
  const sum = values.reduce((a, b) => a + b, 0);
  const mean = sum / n;
  let sq = 0;
  for (const v of values) {
    const d = v - mean;
    sq += d * d;
  }
  const stddev = Math.sqrt(sq / n);
  const sorted = [...values].sort((a, b) => a - b);
  return {
    n,
    mean,
    median: quantile(sorted, 0.5),
    stddev,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    p75: quantile(sorted, 0.75),
    p90: quantile(sorted, 0.9),
    p95: quantile(sorted, 0.95),
    p99: quantile(sorted, 0.99),
  };
}
