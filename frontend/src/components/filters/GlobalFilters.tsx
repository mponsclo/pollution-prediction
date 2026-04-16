"use client";

import { usePathname } from "next/navigation";
import { PollutantSelect } from "./PollutantSelect";
import { DateRangeControl } from "./DateRangeControl";
import { StationMultiSelect } from "./StationMultiSelect";

const HIDDEN_ROUTES = new Set(["/quality", "/anomalies", "/forecasts"]);

export function GlobalFilters() {
  const pathname = usePathname();

  if (HIDDEN_ROUTES.has(pathname)) return null;

  return (
    <div className="hairline-b grid grid-cols-1 gap-3 px-4 py-3 sm:grid-cols-[auto_auto_auto] sm:items-center sm:gap-x-6 md:px-8">
      <PollutantSelect />
      <DateRangeControl />
      <StationMultiSelect />
    </div>
  );
}
