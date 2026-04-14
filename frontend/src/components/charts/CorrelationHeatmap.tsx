"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";

export function CorrelationHeatmap({
  labels,
  matrix,
  height = 460,
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
      grid: { left: 60, right: 80, top: 20, bottom: 70, containLabel: false },
      tooltip: {
        formatter: (p: unknown) => {
          const param = p as { value: [number, number, number] };
          const [x, y, v] = param.value;
          return `Station <span class="num">${labels[y]}</span> × <span class="num">${labels[x]}</span><br/>Pearson r · <span class="num">${v.toFixed(3)}</span>`;
        },
      },
      xAxis: {
        type: "category",
        data: labels,
        axisLabel: {
          color: "#8a8a8a",
          fontSize: 10,
          rotate: 60,
          fontFamily: "var(--font-jetbrains-mono), monospace",
          interval: 0,
        },
        splitArea: { show: false },
      },
      yAxis: {
        type: "category",
        data: labels,
        axisLabel: {
          color: "#8a8a8a",
          fontSize: 10,
          fontFamily: "var(--font-jetbrains-mono), monospace",
          interval: 0,
        },
        splitArea: { show: false },
      },
      visualMap: {
        min: -1,
        max: 1,
        calculable: false,
        orient: "vertical",
        right: 8,
        top: "center",
        inRange: {
          color: ["#0891b2", "#0a0a0a", "#ef4444"],
        },
        textStyle: { color: "#8a8a8a", fontSize: 10 },
        itemWidth: 10,
        itemHeight: 160,
        text: ["+1", "-1"],
      },
      series: [
        {
          type: "heatmap",
          data,
          itemStyle: { borderColor: "#0a0a0a", borderWidth: 1 },
          emphasis: {
            itemStyle: { borderColor: "#22d3ee", borderWidth: 1.5 },
          },
          label: {
            show: labels.length <= 10,
            color: "#ededed",
            fontSize: 10,
            fontFamily: "var(--font-jetbrains-mono), monospace",
            formatter: (p: unknown) => {
              const param = p as { value: [number, number, number] };
              return param.value[2].toFixed(2);
            },
          },
        },
      ],
    };
  }, [labels, matrix]);

  return <ChartBase option={option} height={height} />;
}
