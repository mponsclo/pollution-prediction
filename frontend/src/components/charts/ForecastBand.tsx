"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";
import type { ForecastRow } from "@/lib/predictions";

type TooltipParam = {
  axisValue: string;
  seriesName: string;
  data: unknown;
};

function extractNumber(data: unknown): number | null {
  if (typeof data === "number") return data;
  if (Array.isArray(data) && typeof data[1] === "number") return data[1];
  return null;
}

export function ForecastBand({
  rows,
  unit,
  label,
}: {
  rows: ForecastRow[];
  unit: string;
  label: string;
}) {
  const option = useMemo<EChartsOption>(() => {
    const times = rows.map((r) => r.measurement_datetime);
    const values = rows.map((r) => r.predicted_value);
    const lower = rows.map((r) => r.predicted_lower_90);
    const upper = rows.map((r) => r.predicted_upper_90);
    const upperDelta = rows.map((_, i) => upper[i] - lower[i]);

    return {
      grid: { left: 56, right: 24, top: 28, bottom: 48 },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "line",
          lineStyle: { color: "rgba(255,255,255,0.25)", width: 1 },
        },
        formatter: (p: unknown) => {
          const arr = p as TooltipParam[];
          const axisValue = arr[0]?.axisValue ?? "";
          const idx = times.indexOf(axisValue);
          const predicted = extractNumber(
            arr.find((a) => a.seriesName === "Predicted")?.data,
          );
          const lo = idx >= 0 ? lower[idx] : null;
          const hi = idx >= 0 ? upper[idx] : null;
          const fmt = (v: number | null) => (v == null ? "—" : v.toFixed(4));
          return `<span class="num">${axisValue}</span><br/>
            predicted: <span class="num">${fmt(predicted)}</span><br/>
            90% interval: <span class="num">${fmt(lo)} – ${fmt(hi)}</span>`;
        },
      },
      xAxis: {
        type: "category",
        data: times,
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
          bottom: 10,
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
          areaStyle: { color: "rgba(34,211,238,0.14)" },
          tooltip: { show: false },
        },
        {
          name: "Predicted",
          type: "line",
          data: values,
          showSymbol: false,
          smooth: false,
          lineStyle: { color: "#22d3ee", width: 1.5 },
          itemStyle: { color: "#22d3ee" },
          z: 10,
        },
      ],
      legend: {
        top: 0,
        right: 8,
        data: ["Predicted", "90% interval"],
        itemWidth: 12,
        itemHeight: 6,
        icon: "roundRect",
        textStyle: { color: "#8a8a8a", fontSize: 10 },
      },
      title: {
        text: label,
        left: 0,
        top: 0,
        textStyle: {
          color: "#8a8a8a",
          fontSize: 10,
          fontWeight: "normal",
          fontFamily: "var(--font-inter-tight), sans-serif",
        },
      },
    };
  }, [rows, unit, label]);

  return <ChartBase option={option} height={420} />;
}
