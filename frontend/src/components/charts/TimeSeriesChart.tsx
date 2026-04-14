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
  "#60a5fa", "#fbbf24", "#c084fc", "#4ade80", "#fb7185",
  "#38bdf8", "#e879f9", "#facc15", "#2dd4bf", "#fb923c",
  "#818cf8", "#f87171", "#a3e635", "#0ea5e9", "#8b5cf6",
  "#10b981", "#eab308", "#ec4899", "#06b6d4", "#84cc16",
];

export function stationColor(index: number): string {
  return STATION_PALETTE[index % STATION_PALETTE.length];
}

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
      lineStyle: {
        width: 1,
        color: STATION_PALETTE[i % STATION_PALETTE.length],
      },
      emphasis: {
        focus: "series" as const,
        blurScope: "coordinateSystem" as const,
        lineStyle: { width: 2.5 },
      },
      blur: { lineStyle: { opacity: 0.08 } },
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
      grid: { left: 60, right: 20, top: 16, bottom: 90 },
      tooltip: {
        trigger: "axis",
        confine: true,
        axisPointer: {
          type: "line",
          lineStyle: { color: "rgba(255,255,255,0.25)", width: 1 },
        },
        extraCssText:
          "max-height:220px;overflow-y:auto;backdrop-filter:blur(8px);",
      },
      legend: {
        type: "scroll" as const,
        bottom: 40,
        left: 60,
        right: 20,
        textStyle: {
          color: "#8a8a8a",
          fontSize: 10,
          fontFamily: "var(--font-jetbrains-mono), monospace",
        },
        pageTextStyle: { color: "#8a8a8a", fontSize: 10 },
        pageIconColor: "#22d3ee",
        pageIconInactiveColor: "#3a3a3a",
        selector: [
          { type: "all" as const, title: "all" },
          { type: "inverse" as const, title: "invert" },
        ],
        selectorLabel: {
          color: "#8a8a8a",
          fontSize: 10,
          borderColor: "rgba(255,255,255,0.14)",
          borderWidth: 1,
          padding: [3, 6],
        },
        itemWidth: 14,
        itemHeight: 6,
        itemGap: 12,
        icon: "roundRect",
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
          height: 16,
          bottom: 10,
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
          name: "Threshold",
          type: "line",
          data: [],
          silent: true,
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: {
              color: "#ef4444",
              type: "dashed",
              width: 1.5,
              opacity: 0.95,
            },
            label: {
              formatter: `threshold ${pollutant?.threshold ?? ""} ${pollutant?.unit ?? ""}`,
              color: "#ef4444",
              fontSize: 11,
              fontWeight: "bold",
              position: "insideEndTop",
              backgroundColor: "rgba(10,10,10,0.85)",
              padding: [2, 6],
              borderRadius: 2,
            },
            data: [{ yAxis: pollutant?.threshold ?? 0 }],
          },
        },
      ],
    };
  }, [rows, pollutantCode, stations]);

  return <ChartBase option={option} height={500} />;
}
