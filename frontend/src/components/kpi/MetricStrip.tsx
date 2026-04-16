import { cn } from "@/lib/cn";

export type Metric = {
  label: string;
  value: string;
  delta?: string;
  tone?: "default" | "accent" | "threshold" | "success";
};

const TONE_COLORS: Record<NonNullable<Metric["tone"]>, string> = {
  default: "text-[var(--color-fg)]",
  accent: "text-[var(--color-accent)]",
  threshold: "text-[var(--color-threshold)]",
  success: "text-[var(--color-success)]",
};

export function MetricStrip({ metrics }: { metrics: Metric[] }) {
  const isOdd = metrics.length % 2 !== 0;
  return (
    <div className="hairline grid grid-cols-2 divide-x divide-[var(--color-border)] bg-[var(--color-surface)] md:grid-cols-4 lg:grid-cols-5">
      {metrics.map((m, i) => (
        <div
          key={m.label}
          className={cn(
            "flex flex-col gap-1.5 px-5 py-4",
            isOdd && i === metrics.length - 1 && "col-span-2 md:col-span-1",
          )}
        >
          <span className="label-eyebrow">{m.label}</span>
          <span
            className={cn(
              "num text-[1.1rem] font-medium leading-tight sm:text-[1.35rem] sm:leading-none",
              TONE_COLORS[m.tone ?? "default"]
            )}
          >
            {m.value}
          </span>
          {m.delta && (
            <span className="num text-[0.72rem] text-[var(--color-fg-muted)]">
              {m.delta}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
