"use client";

import { useMemo, useState } from "react";
import type { EChartsOption } from "echarts";
import type { MarkLine1DDataItemOption } from "echarts/types/src/component/marker/MarkLineModel.js";
import { ChartBase } from "./ChartBase";
import { cn } from "@/lib/cn";

export function Histogram({
  values,
  bins = 50,
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
  const [logScale, setLogScale] = useState(false);

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

    const markLines: MarkLine1DDataItemOption[] = [];
    if (threshold != null) {
      markLines.push({
        xAxis: threshold,
        lineStyle: { color: "#ef4444", width: 1.5 },
        label: {
          formatter: `threshold ${threshold}${unit ? " " + unit : ""}`,
          color: "#ef4444",
          fontSize: 11,
          fontWeight: "bold",
          position: "insideEndTop",
          backgroundColor: "rgba(10,10,10,0.85)",
          padding: [2, 6],
        },
      });
    }
    if (mean != null && Number.isFinite(mean)) {
      markLines.push({
        xAxis: mean,
        lineStyle: { color: "#22c55e", width: 1.5 },
        label: {
          formatter: `mean ${mean.toFixed(3)}`,
          color: "#22c55e",
          fontSize: 11,
          fontWeight: "bold",
          position: "insideStartTop",
          backgroundColor: "rgba(10,10,10,0.85)",
          padding: [2, 6],
        },
      });
    }

    return {
      grid: { left: 52, right: 16, top: 28, bottom: 36 },
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
        type: logScale ? "log" : "value",
        name: `count${logScale ? " (log)" : ""}`,
        nameTextStyle: { color: "#8a8a8a", fontSize: 10, padding: [0, 0, 6, 0] },
        min: logScale ? 1 : 0,
      },
      series: [
        {
          type: "bar",
          data,
          barWidth: "95%",
          itemStyle: { color: "#22d3ee", opacity: 0.75 },
          markLine: markLines.length
            ? {
                silent: true,
                symbol: "none",
                lineStyle: { type: "dashed", width: 1.5 },
                data: markLines,
              }
            : undefined,
        },
      ],
    };
  }, [values, bins, threshold, mean, unit, logScale]);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setLogScale((v) => !v)}
        className={cn(
          "hairline absolute right-2 top-0 z-10 px-2 py-0.5 text-[0.65rem] transition-colors",
          logScale
            ? "border-[var(--color-accent)] bg-[var(--color-accent-dim)]/20 text-[var(--color-accent)]"
            : "bg-[var(--color-surface)] text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]",
        )}
      >
        {logScale ? "linear" : "log scale"}
      </button>
      <ChartBase option={option} height={320} />
    </div>
  );
}
