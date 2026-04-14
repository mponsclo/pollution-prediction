"use client";

import { useSearchParams } from "next/navigation";
import { format, parseISO } from "date-fns";
import {
  DEFAULT_POLLUTANT_CODE,
  DEFAULT_RANGE,
  POLLUTANT_BY_CODE,
  STATION_CODES,
} from "@/lib/constants";

export function GlobalFilters() {
  const searchParams = useSearchParams();

  const pollutantCode = Number(
    searchParams.get("pollutant") ?? DEFAULT_POLLUTANT_CODE
  );
  const pollutant =
    POLLUTANT_BY_CODE[pollutantCode] ??
    POLLUTANT_BY_CODE[DEFAULT_POLLUTANT_CODE]!;
  const start = searchParams.get("start") ?? DEFAULT_RANGE.start;
  const end = searchParams.get("end") ?? DEFAULT_RANGE.end;
  const stationsParam = searchParams.get("stations");
  const stationCount = stationsParam
    ? stationsParam.split(",").filter(Boolean).length
    : STATION_CODES.length;

  const fmt = (iso: string) => format(parseISO(iso), "MMM d, yyyy");

  return (
    <div className="hairline-b flex items-center gap-8 px-8 py-3 text-[0.75rem]">
      <FilterSlot label="Pollutant" value={`${pollutant.label} (${pollutant.unit})`} />
      <FilterSlot label="Range" value={`${fmt(start)} → ${fmt(end)}`} />
      <FilterSlot
        label="Stations"
        value={
          stationCount === STATION_CODES.length ? `All ${stationCount}` : `${stationCount}`
        }
      />
      <div className="ml-auto font-mono text-[0.7rem] text-[var(--color-fg-subtle)]">
        override via ?pollutant=&amp;start=&amp;end=&amp;stations=
      </div>
    </div>
  );
}

function FilterSlot({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="label-eyebrow">{label}</span>
      <span className="text-[var(--color-fg)]">{value}</span>
    </div>
  );
}
