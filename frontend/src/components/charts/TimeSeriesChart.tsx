"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";
import {
  POLLUTANT_BY_CODE,
  STATUS_BY_CODE,
} from "@/lib/constants";
import type { TimeSeriesRow } from "@/lib/queries";

const STATION_PALETTE = [
  "#22d3ee", "#a78bfa", "#34d399", "#f59e0b", "#f472b6",
  "#60a5fa", "#fbbf24", "#c084fc", "#4ade80", "#f87171",
  "#38bdf8", "#e879f9", "#facc15", "#2dd4bf", "#fb923c",
  "#818cf8", "#fb7185", "#a3e635", "#0ea5e9", "#8b5cf6",
  "#10b981", "#eab308", "#ec4899", "#06b6d4", "#84cc16",
];

export function TimeSeriesChart({
  rows,
  pollutantCode,
  stations,
}: {
  rows: TimeSeriesRow[];
  pollutantCode: number;
  stations: number[];
}) {
  const option = useMemo<EChartsOption>(() => {
    const pollutant = POLLUTANT_BY_CODE[pollutantCode];
    const byStation = new Map<number, [string, number | null][]>();
    for (const s of stations) byStation.set(s, []);
    for (const r of rows) {
      const arr = byStation.get(r.station_code);
      if (arr) arr.push([r.measurement_datetime, r.value]);
    }

    const lineSeries = stations.map((code, i) => ({
      name: `Station ${code}`,
      type: "line" as const,
      data: byStation.get(code) ?? [],
      showSymbol: false,
      smooth: false,
      sampling: "lttb" as const,
      lineStyle: { width: 1, color: STATION_PALETTE[i % STATION_PALETTE.length] },
      emphasis: { lineStyle: { width: 2 } },
    }));

    const abnormalPoints = rows
      .filter((r) => r.instrument_status !== 0 && r.value != null)
      .map((r) => ({
        value: [r.measurement_datetime, r.value],
        itemStyle: {
          color:
            STATUS_BY_CODE[r.instrument_status]?.color ??
            STATUS_BY_CODE[9]!.color,
        },
        status: r.instrument_status,
      }));

    const scatterSeries = {
      name: "Abnormal readings",
      type: "scatter" as const,
      data: abnormalPoints,
      symbolSize: 4,
      z: 10,
      tooltip: {
        formatter: (p: unknown) => {
          const param = p as {
            data: { value: [string, number]; status: number };
          };
          const status = STATUS_BY_CODE[param.data.status]?.label ?? "Unknown";
          const [ts, val] = param.data.value;
          return `<span class="num">${ts}</span><br/>status: ${status}<br/>value: <span class="num">${val}</span>`;
        },
      },
    };

    return {
      grid: { left: 52, right: 16, top: 28, bottom: 56 },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "line",
          lineStyle: { color: "rgba(255,255,255,0.25)", width: 1 },
        },
      },
      xAxis: {
        type: "time",
      },
      yAxis: {
        type: "value",
        name: `${pollutant?.label ?? ""} (${pollutant?.unit ?? ""})`,
        nameTextStyle: { color: "#8a8a8a", fontSize: 10, padding: [0, 0, 6, 0] },
        scale: true,
      },
      dataZoom: [
        {
          type: "inside",
          throttle: 50,
        },
        {
          type: "slider",
          height: 18,
          bottom: 12,
          backgroundColor: "rgba(255,255,255,0.02)",
          borderColor: "rgba(255,255,255,0.08)",
          fillerColor: "rgba(34,211,238,0.08)",
          handleStyle: { color: "#22d3ee", borderColor: "#22d3ee" },
          moveHandleStyle: { color: "#22d3ee" },
          textStyle: { color: "#5c5c5c", fontSize: 10 },
        },
      ],
      series: [
        ...lineSeries,
        scatterSeries,
        {
          name: "threshold",
          type: "line",
          data: [],
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: {
              color: "#ef4444",
              type: "dashed",
              width: 1,
            },
            label: {
              formatter: `threshold ${pollutant?.threshold ?? ""} ${pollutant?.unit ?? ""}`,
              color: "#ef4444",
              fontSize: 10,
              position: "insideEndTop",
            },
            data: [{ yAxis: pollutant?.threshold ?? 0 }],
          },
        },
      ],
    };
  }, [rows, pollutantCode, stations]);

  return <ChartBase option={option} height={420} />;
}
