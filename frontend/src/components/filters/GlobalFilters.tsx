"use client";

import { PollutantSelect } from "./PollutantSelect";
import { DateRangeControl } from "./DateRangeControl";
import { StationMultiSelect } from "./StationMultiSelect";

export function GlobalFilters() {
  return (
    <div className="hairline-b flex flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 md:px-8">
      <PollutantSelect />
      <DateRangeControl />
      <StationMultiSelect />
      <div className="ml-auto hidden font-mono text-[0.68rem] text-[var(--color-fg-subtle)] 2xl:block">
        state lives in the URL · shareable
      </div>
    </div>
  );
}
