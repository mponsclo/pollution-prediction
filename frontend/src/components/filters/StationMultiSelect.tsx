"use client";

import * as Popover from "@radix-ui/react-popover";
import * as Checkbox from "@radix-ui/react-checkbox";
import { Check, ChevronDown, X } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { STATION_CODES } from "@/lib/constants";
import { useUrlFilters } from "@/lib/url";
import { cn } from "@/lib/cn";

function parseStations(raw: string | null): number[] {
  if (!raw) return STATION_CODES;
  const picked = raw
    .split(",")
    .map((s) => Number(s.trim()))
    .filter((n) => STATION_CODES.includes(n));
  return picked.length > 0 ? picked : STATION_CODES;
}

const PRESETS: { label: string; stations: number[] }[] = [
  { label: "All 25", stations: STATION_CODES },
  { label: "First 5", stations: STATION_CODES.slice(0, 5) },
  { label: "Central (212–216)", stations: [212, 213, 214, 215, 216] },
];

export function StationMultiSelect() {
  const searchParams = useSearchParams();
  const { update, pending } = useUrlFilters();

  const selected = useMemo(
    () => new Set(parseStations(searchParams.get("stations"))),
    [searchParams]
  );
  const [open, setOpen] = useState(false);

  const count = selected.size;
  const total = STATION_CODES.length;
  const label =
    count === total ? `All ${total}` : `${count} / ${total}`;

  const apply = (next: Set<number>) => {
    if (next.size === 0) return;
    const serialized =
      next.size === total
        ? null
        : Array.from(next).sort((a, b) => a - b).join(",");
    update({ stations: serialized });
  };

  const toggle = (code: number) => {
    const next = new Set(selected);
    if (next.has(code)) next.delete(code);
    else next.add(code);
    apply(next);
  };

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <div className="flex items-center gap-2 text-[0.75rem]">
        <span className="label-eyebrow">Stations</span>
        <Popover.Trigger asChild>
          <button
            type="button"
            disabled={pending}
            className="hairline flex items-center gap-2 bg-[var(--color-surface)] px-3 py-1.5 text-[var(--color-fg)] outline-none hover:border-[var(--color-border-strong)] focus:border-[var(--color-accent)]"
          >
            <span className="num">{label}</span>
            <ChevronDown size={12} className="text-[var(--color-fg-subtle)]" />
          </button>
        </Popover.Trigger>
      </div>

      <Popover.Portal>
        <Popover.Content
          align="start"
          sideOffset={6}
          className="hairline z-50 w-[260px] bg-[var(--color-surface)] shadow-2xl"
        >
          <div className="hairline-b flex items-center justify-between px-3 py-2">
            <div className="label-eyebrow">Select stations</div>
            <Popover.Close asChild>
              <button
                type="button"
                className="text-[var(--color-fg-subtle)] hover:text-[var(--color-fg)]"
              >
                <X size={12} />
              </button>
            </Popover.Close>
          </div>

          <div className="hairline-b flex flex-wrap gap-1 px-3 py-2">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => apply(new Set(p.stations))}
                className="hairline bg-[var(--color-bg)] px-2 py-0.5 text-[0.68rem] text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
              >
                {p.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => apply(new Set(STATION_CODES))}
              className="ml-auto text-[0.68rem] text-[var(--color-accent)] hover:underline"
            >
              reset
            </button>
          </div>

          <div className="grid max-h-[260px] grid-cols-2 gap-x-1 gap-y-0.5 overflow-auto p-2">
            {STATION_CODES.map((code) => {
              const checked = selected.has(code);
              return (
                <label
                  key={code}
                  className={cn(
                    "flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1 text-[0.75rem] transition-colors",
                    checked
                      ? "bg-[var(--color-accent-dim)]/20 text-[var(--color-fg)]"
                      : "text-[var(--color-fg-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-fg)]"
                  )}
                >
                  <Checkbox.Root
                    checked={checked}
                    onCheckedChange={() => toggle(code)}
                    className={cn(
                      "flex h-3.5 w-3.5 items-center justify-center border",
                      checked
                        ? "border-[var(--color-accent)] bg-[var(--color-accent)]"
                        : "border-[var(--color-border-strong)] bg-transparent"
                    )}
                  >
                    <Checkbox.Indicator>
                      <Check size={10} strokeWidth={3} className="text-[var(--color-bg)]" />
                    </Checkbox.Indicator>
                  </Checkbox.Root>
                  <span className="num">{code}</span>
                </label>
              );
            })}
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
