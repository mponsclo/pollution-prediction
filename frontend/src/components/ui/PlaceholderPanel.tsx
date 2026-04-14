import type { ReactNode } from "react";

export function PlaceholderPanel({
  title,
  summary,
  children,
}: {
  title: string;
  summary: string;
  children?: ReactNode;
}) {
  return (
    <div className="hairline bg-[var(--color-surface)]">
      <div className="hairline-b flex items-center justify-between px-5 py-3">
        <div>
          <div className="label-eyebrow">Panel</div>
          <div className="mt-0.5 text-[0.9rem] font-medium text-[var(--color-fg)]">
            {title}
          </div>
        </div>
        <div className="font-mono text-[0.7rem] text-[var(--color-fg-subtle)]">
          stub
        </div>
      </div>
      <div className="flex min-h-[220px] flex-col justify-between px-5 py-4 text-[0.8rem] text-[var(--color-fg-muted)]">
        <p>{summary}</p>
        {children}
      </div>
    </div>
  );
}
