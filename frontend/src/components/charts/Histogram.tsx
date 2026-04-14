"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";

export function Histogram({
  values,
  bins = 40,
  threshold,
  mean,
  unit,
}: {
  values: number[];
  bins?: number;
  threshold?: number;
  mean?: number;
  unit?: string;
}) {
  const option = useMemo<EChartsOption>(() => {
    if (values.length === 0) {
      return { series: [] };
    }
    const min = Math.min(...values);
    const max = Math.max(...values);
    const width = (max - min) / bins || 1;
    const counts = new Array<number>(bins).fill(0);
    for (const v of values) {
      const idx = Math.min(bins - 1, Math.floor((v - min) / width));
      counts[idx] += 1;
    }
    const data = counts.map((c, i) => {
      const lo = min + i * width;
      const hi = lo + width;
      return { value: [lo + width / 2, c], lo, hi };
    });

    const markLines: { xAxis: number; lineStyle: { color: string }; label: { formatter: string; color: string; fontSize: number } }[] = [];
    if (threshold != null) {
      markLines.push({
        xAxis: threshold,
        lineStyle: { color: "#ef4444" },
        label: {
          formatter: `threshold ${threshold}${unit ? " " + unit : ""}`,
          color: "#ef4444",
          fontSize: 10,
        },
      });
    }
    if (mean != null) {
      markLines.push({
        xAxis: mean,
        lineStyle: { color: "#22c55e" },
        label: {
          formatter: `mean ${mean.toFixed(3)}`,
          color: "#22c55e",
          fontSize: 10,
        },
      });
    }

    return {
      grid: { left: 48, right: 16, top: 20, bottom: 32 },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (p: unknown) => {
          const arr = p as { value: [number, number]; data: { lo: number; hi: number } }[];
          const { data, value } = arr[0];
          return `<span class="num">${data.lo.toFixed(4)} – ${data.hi.toFixed(4)}</span><br/>count: <span class="num">${value[1].toLocaleString()}</span>`;
        },
      },
      xAxis: {
        type: "value",
        name: unit ? `value (${unit})` : "value",
        nameTextStyle: { color: "#8a8a8a", fontSize: 10, padding: [6, 0, 0, 0] },
        scale: true,
      },
      yAxis: {
        type: "value",
        name: "count",
        nameTextStyle: { color: "#8a8a8a", fontSize: 10, padding: [0, 0, 6, 0] },
      },
      series: [
        {
          type: "bar",
          data,
          barWidth: "95%",
          itemStyle: { color: "#22d3ee", opacity: 0.7 },
          markLine: markLines.length
            ? {
                silent: true,
                symbol: "none",
                lineStyle: { type: "dashed", width: 1 },
                data: markLines,
              }
            : undefined,
        },
      ],
    };
  }, [values, bins, threshold, mean, unit]);

  return <ChartBase option={option} height={300} />;
}
