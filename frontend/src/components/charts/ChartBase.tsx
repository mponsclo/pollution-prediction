"use client";

import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { useEffect, useRef } from "react";

const BASE_TEXT_STYLE = {
  color: "#ededed",
  fontFamily: "var(--font-inter-tight), ui-sans-serif, system-ui, sans-serif",
  fontSize: 11,
};

const AXIS_DEFAULTS = {
  axisLine: { lineStyle: { color: "rgba(255,255,255,0.14)" } },
  axisTick: { show: false },
  axisLabel: {
    color: "#8a8a8a",
    fontFamily: "var(--font-jetbrains-mono), ui-monospace, monospace",
    fontSize: 10,
  },
  splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
};

export function mergeBaseOption(option: EChartsOption): EChartsOption {
  const { textStyle, xAxis, yAxis, ...rest } = option;

  const apply = (axis: unknown) => {
    if (!axis) return axis;
    if (Array.isArray(axis)) {
      return axis.map((a) => ({ ...AXIS_DEFAULTS, ...(a as object) }));
    }
    return { ...AXIS_DEFAULTS, ...(axis as object) };
  };

  return {
    backgroundColor: "transparent",
    textStyle: { ...BASE_TEXT_STYLE, ...(textStyle as object) },
    xAxis: apply(xAxis) as EChartsOption["xAxis"],
    yAxis: apply(yAxis) as EChartsOption["yAxis"],
    tooltip: {
      backgroundColor: "rgba(17,17,17,0.96)",
      borderColor: "rgba(255,255,255,0.14)",
      borderWidth: 1,
      textStyle: { color: "#ededed", fontFamily: BASE_TEXT_STYLE.fontFamily, fontSize: 11 },
      padding: [8, 10],
      ...option.tooltip,
    },
    ...rest,
  };
}

export function ChartBase({
  option,
  height = 340,
  className,
}: {
  option: EChartsOption;
  height?: number;
  className?: string;
}) {
  const ref = useRef<ReactECharts>(null);

  useEffect(() => {
    const handler = () => ref.current?.getEchartsInstance().resize();
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  return (
    <ReactECharts
      ref={ref}
      option={mergeBaseOption(option)}
      style={{ height, width: "100%" }}
      opts={{ renderer: "canvas" }}
      lazyUpdate
      notMerge={false}
      className={className}
    />
  );
}
