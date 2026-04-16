"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";

export type HBar = {
  label: string;
  value: number;
  color?: string;
};

export function HorizontalBars({
  bars,
  unit = "%",
  targetLine,
  height = 340,
  maxValue,
}: {
  bars: HBar[];
  unit?: string;
  targetLine?: { value: number; label?: string };
  height?: number;
  maxValue?: number;
}) {
  const option = useMemo<EChartsOption>(() => {
    const sorted = [...bars].sort((a, b) => a.value - b.value);
    return {
      grid: { left: 12, right: 60, top: 18, bottom: 24, containLabel: true },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (p: unknown) => {
          const arr = p as { name: string; value: number }[];
          const { name, value } = arr[0];
          return `${name}<br/><span class="num">${value.toFixed(2)}${unit}</span>`;
        },
      },
      xAxis: {
        type: "value",
        max: maxValue ?? "dataMax",
      },
      yAxis: {
        type: "category",
        data: sorted.map((b) => b.label),
        axisLabel: { color: "#8a8a8a", fontSize: 10 },
      },
      series: [
        {
          type: "bar",
          data: sorted.map((b) => ({
            value: b.value,
            itemStyle: { color: b.color ?? "#22d3ee", borderRadius: [0, 1, 1, 0] },
          })),
          barMaxWidth: 14,
          label: {
            show: true,
            position: "right",
            color: "#8a8a8a",
            fontSize: 10,
            fontFamily: "var(--font-jetbrains-mono), monospace",
            formatter: (p: unknown) => {
              const v = (p as { value: number }).value;
              return `${v.toFixed(1)}${unit}`;
            },
          },
          markLine: targetLine
            ? {
                silent: true,
                symbol: "none",
                lineStyle: {
                  color: "#ef4444",
                  type: "dashed",
                  width: 1,
                },
                label: {
                  formatter: targetLine.label ?? `target ${targetLine.value}${unit}`,
                  color: "#ef4444",
                  fontSize: 10,
                  position: "insideEndTop",
                  backgroundColor: "rgba(10,10,10,0.85)",
                  padding: [2, 4],
                  borderRadius: 2,
                },
                data: [{ xAxis: targetLine.value }],
              }
            : undefined,
        },
      ],
    };
  }, [bars, unit, targetLine, maxValue]);

  return <ChartBase option={option} height={height} />;
}
