"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";
import { STATUSES } from "@/lib/constants";

export function StatusPie({
  counts,
}: {
  counts: Record<number, number>;
}) {
  const option = useMemo<EChartsOption>(() => {
    const data = STATUSES.map((s) => ({
      name: s.label,
      value: counts[s.code] ?? 0,
      itemStyle: { color: s.color },
    })).filter((d) => d.value > 0);

    return {
      tooltip: {
        trigger: "item",
        formatter: (p: unknown) => {
          const param = p as { name: string; value: number; percent: number };
          return `${param.name}<br/><span class="num">${param.value.toLocaleString()}</span> · <span class="num">${param.percent.toFixed(1)}%</span>`;
        },
      },
      grid: { bottom: 60 },
      legend: {
        orient: "horizontal",
        bottom: 0,
        left: "center",
        textStyle: { color: "#8a8a8a", fontSize: 10 },
        itemWidth: 8,
        itemHeight: 8,
        itemGap: 10,
        icon: "roundRect",
      },
      series: [
        {
          type: "pie",
          radius: ["40%", "62%"],
          center: ["50%", "36%"],
          avoidLabelOverlap: true,
          label: { show: false },
          labelLine: { show: false },
          itemStyle: {
            borderColor: "#0a0a0a",
            borderWidth: 2,
          },
          data,
        },
      ],
    };
  }, [counts]);

  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  if (total === 0) {
    return (
      <div className="flex h-[200px] items-center justify-center text-[0.8rem] text-[var(--color-fg-subtle)]">
        no readings in window
      </div>
    );
  }

  return <ChartBase option={option} height={260} />;
}
