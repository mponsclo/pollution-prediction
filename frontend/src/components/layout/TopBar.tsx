"use client";

import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/nav";
import { MobileNav } from "./MobileNav";

export function TopBar() {
  const pathname = usePathname();
  const current = NAV_ITEMS.find(
    (n) => pathname === n.href || pathname?.startsWith(`${n.href}/`),
  );

  return (
    <div className="hairline-b flex items-center justify-between gap-4 px-4 py-4 md:px-8">
      <div className="flex items-center gap-3">
        <MobileNav />
        <div>
          <div className="label-eyebrow">
            {current ? "Dashboard" : "Overview"}
          </div>
          <h1 className="mt-1 text-[1.125rem] font-medium tracking-tight text-[var(--color-fg)]">
            {current?.label ?? "Seoul Air Quality"}
          </h1>
        </div>
      </div>
      <div className="hidden items-center gap-6 text-[0.75rem] md:flex">
        <div>
          <span className="label-eyebrow mr-2">Stations</span>
          <span className="num text-[var(--color-fg)]">25</span>
        </div>
        <div>
          <span className="label-eyebrow mr-2">Pollutants</span>
          <span className="num text-[var(--color-fg)]">6</span>
        </div>
        <div className="hidden xl:block">
          <span className="label-eyebrow mr-2">Source</span>
          <span className="font-mono text-[var(--color-fg-muted)]">
            presentation.dashboard_wide
          </span>
        </div>
      </div>
    </div>
  );
}
