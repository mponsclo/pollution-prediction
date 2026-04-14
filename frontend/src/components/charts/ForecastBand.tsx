"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";
import type { ForecastRow } from "@/lib/predictions";

function parseTs(iso: string): number {
  return new Date(iso.replace(" ", "T")).getTime();
}

export function ForecastBand({
  rows,
  unit,
}: {
  rows: ForecastRow[];
  unit: string;
  label?: string;
}) {
  const option = useMemo<EChartsOption>(() => {
    const predicted: [number, number][] = rows.map((r) => [
      parseTs(r.measurement_datetime),
      r.predicted_value,
    ]);
    const lower: [number, number][] = rows.map((r) => [
      parseTs(r.measurement_datetime),
      r.predicted_lower_90,
    ]);
    const upperDelta: [number, number][] = rows.map((r, i) => [
      parseTs(r.measurement_datetime),
      r.predicted_upper_90 - lower[i][1],
    ]);
    const tsToRow = new Map(rows.map((r) => [parseTs(r.measurement_datetime), r]));

    return {
      grid: { left: 64, right: 24, top: 36, bottom: 64 },
      tooltip: {
        trigger: "axis",
        confine: true,
        axisPointer: {
          type: "line",
          lineStyle: { color: "rgba(255,255,255,0.3)", width: 1 },
        },
        formatter: (p: unknown) => {
          const arr = p as { axisValue: number; seriesName: string; data: [number, number] }[];
          const ts = arr[0]?.axisValue;
          const row = ts != null ? tsToRow.get(ts) : undefined;
          if (!row) return "";
          return `<span class="num">${row.measurement_datetime}</span><br/>
            predicted: <span class="num">${row.predicted_value.toFixed(4)}</span><br/>
            90% interval: <span class="num">${row.predicted_lower_90.toFixed(4)} – ${row.predicted_upper_90.toFixed(4)}</span><br/>
            width: <span class="num">${(row.predicted_upper_90 - row.predicted_lower_90).toFixed(4)}</span>`;
        },
      },
      legend: {
        top: 0,
        right: 8,
        data: ["Predicted", "90% interval"],
        itemWidth: 14,
        itemHeight: 6,
        icon: "roundRect",
        textStyle: {
          color: "#8a8a8a",
          fontSize: 10,
          fontFamily: "var(--font-jetbrains-mono), monospace",
        },
      },
      xAxis: {
        type: "time",
        axisLabel: {
          color: "#8a8a8a",
          fontSize: 10,
          fontFamily: "var(--font-jetbrains-mono), monospace",
          hideOverlap: true,
        },
      },
      yAxis: {
        type: "value",
        name: unit,
        nameTextStyle: { color: "#8a8a8a", fontSize: 10, padding: [0, 0, 6, 0] },
        scale: true,
      },
      dataZoom: [
        { type: "inside", throttle: 50 },
        {
          type: "slider",
          height: 18,
          bottom: 12,
          backgroundColor: "rgba(255,255,255,0.02)",
          borderColor: "rgba(255,255,255,0.08)",
          fillerColor: "rgba(34,211,238,0.08)",
          handleStyle: { color: "#22d3ee", borderColor: "#22d3ee" },
          textStyle: { color: "#5c5c5c", fontSize: 10 },
        },
      ],
      series: [
        {
          name: "Lower 90%",
          type: "line",
          data: lower,
          lineStyle: { opacity: 0 },
          symbol: "none",
          stack: "interval",
          silent: true,
          tooltip: { show: false },
        },
        {
          name: "90% interval",
          type: "line",
          data: upperDelta,
          lineStyle: { opacity: 0 },
          symbol: "none",
          stack: "interval",
          areaStyle: { color: "rgba(34,211,238,0.18)" },
          tooltip: { show: false },
        },
        {
          name: "Predicted",
          type: "line",
          data: predicted,
          showSymbol: false,
          smooth: false,
          lineStyle: { color: "#22d3ee", width: 1.5 },
          itemStyle: { color: "#22d3ee" },
          z: 10,
        },
      ],
    };
  }, [rows, unit]);

  return <ChartBase option={option} height={440} />;
}
