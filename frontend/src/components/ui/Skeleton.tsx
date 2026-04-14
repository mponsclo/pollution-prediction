import type { CSSProperties } from "react";
import { cn } from "@/lib/cn";

export function Skeleton({
  className,
  style,
}: {
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div
      style={style}
      className={cn(
        "animate-pulse bg-[var(--color-surface-hover)]",
        className,
      )}
    />
  );
}

export function PanelSkeleton({
  title,
  height = 320,
}: {
  title: string;
  height?: number;
}) {
  return (
    <div className="hairline bg-[var(--color-surface)]">
      <div className="hairline-b flex items-center justify-between px-5 py-3">
        <div>
          <div className="label-eyebrow">Loading</div>
          <div className="mt-0.5 text-[0.9rem] font-medium text-[var(--color-fg)]">
            {title}
          </div>
        </div>
        <Skeleton className="h-3 w-16" />
      </div>
      <div className="px-5 py-4">
        <Skeleton className="w-full" style={{ height }} />
      </div>
    </div>
  );
}

export function MetricStripSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="hairline grid grid-cols-2 divide-x divide-[var(--color-border)] bg-[var(--color-surface)] md:grid-cols-4 lg:grid-cols-5">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex flex-col gap-1.5 px-5 py-4">
          <Skeleton className="h-2 w-20" />
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-2 w-16" />
        </div>
      ))}
    </div>
  );
}
