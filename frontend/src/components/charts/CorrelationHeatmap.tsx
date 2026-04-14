"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";

export function CorrelationHeatmap({
  labels,
  matrix,
  height = 400,
}: {
  labels: string[];
  matrix: number[][];
  height?: number;
}) {
  const option = useMemo<EChartsOption>(() => {
    const data: [number, number, number][] = [];
    for (let i = 0; i < labels.length; i++) {
      for (let j = 0; j < labels.length; j++) {
        const v = matrix[i]?.[j];
        if (v != null && Number.isFinite(v)) {
          data.push([j, i, Number(v.toFixed(3))]);
        }
      }
    }
    return {
      grid: { left: 52, right: 52, top: 12, bottom: 52 },
      tooltip: {
        formatter: (p: unknown) => {
          const param = p as { value: [number, number, number] };
          const [x, y, v] = param.value;
          return `${labels[y]} × ${labels[x]}<br/>corr: <span class="num">${v.toFixed(3)}</span>`;
        },
      },
      xAxis: {
        type: "category",
        data: labels,
        axisLabel: { color: "#8a8a8a", fontSize: 9, rotate: 45 },
        splitArea: { show: false },
      },
      yAxis: {
        type: "category",
        data: labels,
        axisLabel: { color: "#8a8a8a", fontSize: 9 },
        splitArea: { show: false },
      },
      visualMap: {
        min: -1,
        max: 1,
        calculable: false,
        orient: "horizontal",
        left: "center",
        bottom: 0,
        inRange: {
          color: ["#0891b2", "#0a0a0a", "#ef4444"],
        },
        textStyle: { color: "#8a8a8a", fontSize: 10 },
        itemWidth: 12,
        itemHeight: 120,
      },
      series: [
        {
          type: "heatmap",
          data,
          itemStyle: { borderColor: "#0a0a0a", borderWidth: 1 },
          emphasis: {
            itemStyle: { borderColor: "#22d3ee", borderWidth: 1 },
          },
        },
      ],
    };
  }, [labels, matrix]);

  return <ChartBase option={option} height={height} />;
}
