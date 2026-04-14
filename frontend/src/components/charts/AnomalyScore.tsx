"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";
import type { AnomalyRow } from "@/lib/predictions";

export function AnomalyScore({ rows }: { rows: AnomalyRow[] }) {
  const option = useMemo<EChartsOption>(() => {
    const times = rows.map((r) => r.measurement_datetime);
    const scores = rows.map((r) => r.anomaly_score);
    const anomalies = rows
      .map((r, i) => (r.is_anomaly ? [i, r.anomaly_score] : null))
      .filter((p): p is [number, number] => p != null);

    return {
      grid: { left: 56, right: 24, top: 20, bottom: 48 },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "line",
          lineStyle: { color: "rgba(255,255,255,0.25)", width: 1 },
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
        name: "score",
        nameTextStyle: { color: "#8a8a8a", fontSize: 10, padding: [0, 0, 6, 0] },
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
          name: "Anomaly score",
          type: "line",
          data: scores,
          showSymbol: false,
          smooth: false,
          lineStyle: { color: "#22d3ee", width: 1 },
          itemStyle: { color: "#22d3ee" },
        },
        {
          name: "Flagged",
          type: "scatter",
          data: anomalies,
          symbolSize: 6,
          itemStyle: { color: "#ef4444", borderColor: "#0a0a0a", borderWidth: 1 },
          z: 10,
        },
      ],
    };
  }, [rows]);

  return <ChartBase option={option} height={360} />;
}
