"use client";

import { useSearchParams } from "next/navigation";
import {
  DEFAULT_POLLUTANT_CODE,
  POLLUTANTS,
  POLLUTANT_BY_CODE,
} from "@/lib/constants";
import { useUrlFilters } from "@/lib/url";
import { ThemedSelect } from "@/components/ui/ThemedSelect";

export function PollutantSelect() {
  const searchParams = useSearchParams();
  const { update, pending } = useUrlFilters();

  const active =
    POLLUTANT_BY_CODE[
      Number(searchParams.get("pollutant") ?? DEFAULT_POLLUTANT_CODE)
    ] ?? POLLUTANT_BY_CODE[DEFAULT_POLLUTANT_CODE]!;

  return (
    <label className="flex items-center gap-2 text-[0.75rem]">
      <span className="label-eyebrow">Pollutant</span>
      <ThemedSelect
        ariaLabel="Select pollutant"
        value={String(active.code)}
        disabled={pending}
        onValueChange={(v) => update({ pollutant: v })}
        items={POLLUTANTS.map((p) => ({
          value: String(p.code),
          label: (
            <span className="flex items-center gap-2">
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ background: p.color }}
              />
              <span className="text-[var(--color-fg)]">{p.label}</span>
              <span className="text-[0.68rem] text-[var(--color-fg-subtle)]">
                {p.unit}
              </span>
            </span>
          ),
        }))}
      />
    </label>
  );
}
