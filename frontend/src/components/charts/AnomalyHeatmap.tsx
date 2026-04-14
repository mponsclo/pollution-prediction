"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartBase } from "./ChartBase";
import type { AnomalyRow } from "@/lib/predictions";

export function AnomalyHeatmap({ rows }: { rows: AnomalyRow[] }) {
  const option = useMemo<EChartsOption>(() => {
    const byHourDay = new Map<string, { sum: number; n: number }>();
    const days = new Set<string>();
    for (const r of rows) {
      const dt = new Date(r.measurement_datetime.replace(" ", "T"));
      const day = `${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
      const hour = dt.getHours();
      const k = `${day}|${hour}`;
      days.add(day);
      const cur = byHourDay.get(k) ?? { sum: 0, n: 0 };
      cur.sum += r.anomaly_score;
      cur.n += 1;
      byHourDay.set(k, cur);
    }
    const dayList = Array.from(days).sort();
    const hours = Array.from({ length: 24 }, (_, i) => i);

    const data: [number, number, number][] = [];
    let max = 0;
    for (let x = 0; x < dayList.length; x++) {
      for (let y = 0; y < hours.length; y++) {
        const cell = byHourDay.get(`${dayList[x]}|${hours[y]}`);
        const v = cell ? cell.sum / cell.n : 0;
        data.push([x, y, Number(v.toFixed(4))]);
        if (v > max) max = v;
      }
    }

    return {
      grid: { left: 52, right: 16, top: 12, bottom: 64 },
      tooltip: {
        formatter: (p: unknown) => {
          const param = p as { value: [number, number, number] };
          const [x, y, v] = param.value;
          return `day ${dayList[x]} · hour ${y}<br/>mean score <span class="num">${v.toFixed(4)}</span>`;
        },
      },
      xAxis: {
        type: "category",
        data: dayList,
        axisLabel: {
          color: "#8a8a8a",
          fontSize: 9,
          rotate: 45,
          fontFamily: "var(--font-jetbrains-mono), monospace",
        },
        splitArea: { show: false },
      },
      yAxis: {
        type: "category",
        data: hours.map(String),
        axisLabel: {
          color: "#8a8a8a",
          fontSize: 9,
          fontFamily: "var(--font-jetbrains-mono), monospace",
        },
        splitArea: { show: false },
      },
      visualMap: {
        min: 0,
        max: max > 0 ? max : 1,
        calculable: false,
        orient: "horizontal",
        left: "center",
        bottom: 6,
        inRange: { color: ["#0a0a0a", "#0891b2", "#ef4444"] },
        textStyle: { color: "#8a8a8a", fontSize: 10 },
        itemWidth: 12,
        itemHeight: 100,
      },
      series: [
        {
          type: "heatmap",
          data,
          itemStyle: { borderColor: "#0a0a0a", borderWidth: 1 },
        },
      ],
    };
  }, [rows]);

  return <ChartBase option={option} height={360} />;
}
