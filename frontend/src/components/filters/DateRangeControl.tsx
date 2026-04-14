"use client";

import * as Popover from "@radix-ui/react-popover";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { DayPicker, type DateRange } from "react-day-picker";
import "react-day-picker/style.css";
import { Calendar, X } from "lucide-react";
import { format, parseISO } from "date-fns";
import { DATA_WINDOW, DEFAULT_RANGE } from "@/lib/constants";
import { useUrlFilters } from "@/lib/url";
import { cn } from "@/lib/cn";

type Preset = {
  label: string;
  start: string;
  end: string;
};

const PRESETS: Preset[] = [
  { label: "Dec 2023", start: "2023-12-01T00:00:00", end: "2023-12-31T23:00:00" },
  { label: "Q4 2023", start: "2023-10-01T00:00:00", end: "2023-12-31T23:00:00" },
  { label: "2023", start: "2023-01-01T00:00:00", end: "2023-12-31T23:00:00" },
  { label: "2022", start: "2022-01-01T00:00:00", end: "2022-12-31T23:00:00" },
  { label: "2021", start: "2021-01-01T00:00:00", end: "2021-12-31T23:00:00" },
  { label: "All", start: DATA_WINDOW.start, end: DATA_WINDOW.end },
];

function isoDate(iso: string): Date {
  return parseISO(iso);
}

function toIsoStart(d: Date): string {
  return `${format(d, "yyyy-MM-dd")}T00:00:00`;
}

function toIsoEnd(d: Date): string {
  return `${format(d, "yyyy-MM-dd")}T23:00:00`;
}

export function DateRangeControl() {
  const searchParams = useSearchParams();
  const { update, pending } = useUrlFilters();

  const start = searchParams.get("start") ?? DEFAULT_RANGE.start;
  const end = searchParams.get("end") ?? DEFAULT_RANGE.end;

  const minDay = isoDate(DATA_WINDOW.start);
  const maxDay = isoDate(DATA_WINDOW.end);

  const activePreset = useMemo(
    () => PRESETS.find((p) => p.start === start && p.end === end),
    [start, end],
  );

  const [open, setOpen] = useState(false);
  const [range, setRange] = useState<DateRange | undefined>({
    from: isoDate(start),
    to: isoDate(end),
  });

  const applyPreset = (p: Preset) => {
    setRange({ from: isoDate(p.start), to: isoDate(p.end) });
    update({ start: p.start, end: p.end });
  };

  const applyRange = (r: DateRange | undefined) => {
    setRange(r);
    if (r?.from && r?.to) {
      update({ start: toIsoStart(r.from), end: toIsoEnd(r.to) });
    }
  };

  const buttonLabel = activePreset
    ? activePreset.label
    : `${format(isoDate(start), "MMM d, yyyy")} → ${format(isoDate(end), "MMM d, yyyy")}`;

  return (
    <div className="flex items-center gap-2 text-[0.75rem]">
      <span className="label-eyebrow">Range</span>

      <Popover.Root open={open} onOpenChange={setOpen}>
        <Popover.Trigger asChild>
          <button
            type="button"
            disabled={pending}
            className="hairline inline-flex items-center gap-2 bg-[var(--color-surface)] px-3 py-1.5 text-[var(--color-fg)] outline-none hover:border-[var(--color-border-strong)] focus-visible:border-[var(--color-accent)] disabled:opacity-60"
          >
            <Calendar size={13} className="text-[var(--color-fg-muted)]" />
            <span className="num text-[0.78rem]">{buttonLabel}</span>
          </button>
        </Popover.Trigger>

        <Popover.Portal>
          <Popover.Content
            align="start"
            sideOffset={6}
            className="hairline z-50 bg-[var(--color-surface)] shadow-2xl"
          >
            <div className="hairline-b flex items-center justify-between px-3 py-2">
              <div className="label-eyebrow">Select date range</div>
              <Popover.Close asChild>
                <button
                  type="button"
                  className="text-[var(--color-fg-subtle)] hover:text-[var(--color-fg)]"
                >
                  <X size={12} />
                </button>
              </Popover.Close>
            </div>

            <div className="flex">
              <div className="hairline-r flex flex-col gap-1 p-3">
                <div className="label-eyebrow mb-1">Presets</div>
                {PRESETS.map((p) => (
                  <button
                    key={p.label}
                    type="button"
                    onClick={() => applyPreset(p)}
                    className={cn(
                      "px-2.5 py-1 text-left text-[0.72rem] transition-colors",
                      activePreset?.label === p.label
                        ? "bg-[var(--color-accent-dim)]/20 text-[var(--color-accent)]"
                        : "text-[var(--color-fg-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-fg)]",
                    )}
                  >
                    {p.label}
                  </button>
                ))}
              </div>

              <div className="p-3">
                <DayPicker
                  mode="range"
                  numberOfMonths={2}
                  selected={range}
                  onSelect={applyRange}
                  disabled={{ before: minDay, after: maxDay }}
                  startMonth={minDay}
                  endMonth={maxDay}
                  defaultMonth={range?.to ?? maxDay}
                  classNames={DAYPICKER_CLASSES}
                />
              </div>
            </div>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    </div>
  );
}

const DAYPICKER_CLASSES = {
  root: "rdp relative text-[0.75rem]",
  months: "flex gap-6",
  month: "space-y-2",
  month_caption: "flex items-center justify-center py-1 font-medium text-[var(--color-fg)]",
  caption_label: "text-[0.78rem]",
  nav: "absolute top-1 left-0 right-0 flex items-center justify-between pointer-events-none",
  button_previous:
    "hairline pointer-events-auto h-6 w-6 inline-flex items-center justify-center bg-[var(--color-surface)] text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]",
  button_next:
    "hairline pointer-events-auto h-6 w-6 inline-flex items-center justify-center bg-[var(--color-surface)] text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]",
  month_grid: "mt-1 w-full border-collapse",
  weekdays: "flex",
  weekday:
    "w-8 text-center text-[0.65rem] font-normal uppercase tracking-wider text-[var(--color-fg-subtle)]",
  week: "flex w-full mt-1",
  day: "h-8 w-8 text-center p-0",
  day_button:
    "h-8 w-8 inline-flex items-center justify-center rounded-sm text-[var(--color-fg)] hover:bg-[var(--color-surface-hover)] focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-accent)] disabled:text-[var(--color-fg-subtle)]/40 disabled:hover:bg-transparent",
  selected: "",
  range_start:
    "[&>button]:bg-[var(--color-accent)] [&>button]:text-[var(--color-bg)] [&>button]:font-medium",
  range_end:
    "[&>button]:bg-[var(--color-accent)] [&>button]:text-[var(--color-bg)] [&>button]:font-medium",
  range_middle:
    "[&>button]:bg-[var(--color-accent-dim)]/25 [&>button]:text-[var(--color-fg)] [&>button]:rounded-none",
  today: "[&>button]:ring-1 [&>button]:ring-[var(--color-accent)]/40",
  outside: "[&>button]:text-[var(--color-fg-subtle)]/40",
  disabled: "[&>button]:text-[var(--color-fg-subtle)]/30 [&>button]:cursor-not-allowed",
  hidden: "invisible",
};
