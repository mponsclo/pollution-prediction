"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";
import type { AnomalyRow } from "@/lib/predictions";

function parseTs(iso: string): number {
  return new Date(iso.replace(" ", "T")).getTime();
}

export function AnomalyScore({ rows }: { rows: AnomalyRow[] }) {
  const option = useMemo<EChartsOption>(() => {
    const scores: [number, number][] = rows.map((r) => [
      parseTs(r.measurement_datetime),
      r.anomaly_score,
    ]);
    const anomalies: [number, number][] = rows
      .filter((r) => r.is_anomaly === 1)
      .map((r) => [parseTs(r.measurement_datetime), r.anomaly_score]);
    const tsToRow = new Map(rows.map((r) => [parseTs(r.measurement_datetime), r]));

    return {
      grid: { left: 60, right: 24, top: 32, bottom: 64 },
      tooltip: {
        trigger: "axis",
        confine: true,
        axisPointer: {
          type: "line",
          lineStyle: { color: "rgba(255,255,255,0.3)", width: 1 },
        },
        formatter: (p: unknown) => {
          const arr = p as { axisValue: number }[];
          const ts = arr[0]?.axisValue;
          const row = ts != null ? tsToRow.get(ts) : undefined;
          if (!row) return "";
          return `<span class="num">${row.measurement_datetime}</span><br/>
            score: <span class="num">${row.anomaly_score.toFixed(5)}</span><br/>
            flagged: ${row.is_anomaly ? '<span class="num" style="color:#ef4444">yes</span>' : '<span class="num">no</span>'}`;
        },
      },
      legend: {
        top: 0,
        right: 8,
        data: ["Anomaly score", "Flagged"],
        itemWidth: 12,
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
        name: "score",
        nameTextStyle: { color: "#8a8a8a", fontSize: 10, padding: [0, 0, 6, 0] },
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
          name: "Anomaly score",
          type: "line",
          data: scores,
          showSymbol: false,
          smooth: false,
          lineStyle: { color: "#22d3ee", width: 1 },
          itemStyle: { color: "#22d3ee" },
          areaStyle: {
            color: "rgba(34,211,238,0.06)",
          },
        },
        {
          name: "Flagged",
          type: "scatter",
          data: anomalies,
          symbolSize: 8,
          itemStyle: {
            color: "#ef4444",
            borderColor: "#0a0a0a",
            borderWidth: 1.5,
            shadowColor: "#ef4444",
            shadowBlur: 8,
          },
          z: 10,
        },
      ],
    };
  }, [rows]);

  return <ChartBase option={option} height={380} />;
}
