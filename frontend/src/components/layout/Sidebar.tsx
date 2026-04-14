"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS, HOME_NAV } from "@/lib/nav";
import { cn } from "@/lib/cn";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hairline-r hidden w-[220px] shrink-0 flex-col bg-[var(--color-bg)] lg:flex">
      <div className="hairline-b px-5 py-5">
        <Link href={HOME_NAV.href} className="block">
          <div className="label-eyebrow">mpc-pollution-331382</div>
          <div className="mt-1 text-[0.95rem] font-medium tracking-tight text-[var(--color-fg)]">
            Seoul Air Quality
          </div>
        </Link>
      </div>

      <nav className="flex flex-1 flex-col py-3">
        {NAV_ITEMS.map((item) => {
          const active =
            pathname === item.href || pathname?.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 px-5 py-2.5 text-[0.875rem] transition-colors",
                active
                  ? "text-[var(--color-fg)]"
                  : "text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
              )}
            >
              {active && (
                <span className="absolute left-0 top-0 h-full w-[2px] bg-[var(--color-accent)]" />
              )}
              <Icon
                size={15}
                strokeWidth={1.75}
                className={cn(
                  "transition-colors",
                  active ? "text-[var(--color-accent)]" : ""
                )}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="hairline-t px-5 py-4">
        <div className="label-eyebrow">Build</div>
        <div className="mt-1 font-mono text-[0.7rem] text-[var(--color-fg-subtle)]">
          viz-as-code · dev
        </div>
      </div>
    </aside>
  );
}
