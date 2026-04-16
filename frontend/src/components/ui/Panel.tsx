import type { ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  tag,
  action,
  children,
  contentClassName,
}: {
  title: string;
  subtitle?: string;
  tag?: string;
  action?: ReactNode;
  children: ReactNode;
  contentClassName?: string;
}) {
  return (
    <div className="hairline bg-[var(--color-surface)]">
      <div className="hairline-b flex flex-col gap-3 px-5 py-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div className="min-w-0">
          {tag && <div className="label-eyebrow">{tag}</div>}
          <div className="mt-0.5 text-[0.9rem] font-medium text-[var(--color-fg)]">
            {title}
          </div>
          {subtitle && (
            <div className="mt-0.5 text-[0.72rem] text-[var(--color-fg-muted)]">
              {subtitle}
            </div>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      <div className={contentClassName ?? "px-5 py-4"}>{children}</div>
    </div>
  );
}
