"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";
import type { MonthlyQualityRow } from "@/lib/queries";

export function MonthlyTrend({ rows }: { rows: MonthlyQualityRow[] }) {
  const option = useMemo<EChartsOption>(() => {
    return {
      grid: { left: 44, right: 16, top: 28, bottom: 32 },
      legend: {
        top: 0,
        right: 8,
        itemWidth: 10,
        itemHeight: 8,
        icon: "roundRect",
        textStyle: { color: "#8a8a8a", fontSize: 10 },
      },
      tooltip: {
        trigger: "axis",
        formatter: (p: unknown) => {
          const arr = p as { seriesName: string; value: [string, number] }[];
          const [month] = arr[0].value;
          const body = arr
            .map(
              (a) =>
                `${a.seriesName}: <span class="num">${a.value[1].toFixed(1)}%</span>`,
            )
            .join("<br/>");
          return `${month}<br/>${body}`;
        },
      },
      xAxis: {
        type: "category",
        data: rows.map((r) => r.month),
      },
      yAxis: { type: "value", min: 0, max: 100 },
      series: [
        {
          name: "Status availability",
          type: "line",
          data: rows.map((r) => [r.month, r.status_pct]),
          smooth: true,
          symbol: "circle",
          symbolSize: 4,
          lineStyle: { color: "#22d3ee", width: 1.5 },
          itemStyle: { color: "#22d3ee" },
        },
        {
          name: "Valid SO₂ values",
          type: "line",
          data: rows.map((r) => [r.month, r.valid_pct]),
          smooth: true,
          symbol: "circle",
          symbolSize: 4,
          lineStyle: { color: "#a78bfa", width: 1.5 },
          itemStyle: { color: "#a78bfa" },
        },
      ],
    };
  }, [rows]);

  return <ChartBase option={option} height={260} />;
}
