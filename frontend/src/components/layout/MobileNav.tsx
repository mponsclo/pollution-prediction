"use client";

import * as Popover from "@radix-ui/react-popover";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { HOME_NAV, NAV_ITEMS } from "@/lib/nav";
import { cn } from "@/lib/cn";

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Open navigation"
          className="hairline flex h-8 w-8 items-center justify-center bg-[var(--color-surface)] text-[var(--color-fg)] hover:border-[var(--color-border-strong)] lg:hidden"
        >
          {open ? <X size={14} /> : <Menu size={14} />}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="start"
          sideOffset={8}
          className="hairline z-50 w-[240px] bg-[var(--color-surface)] shadow-2xl"
        >
          <div className="hairline-b px-4 py-3">
            <Link
              href={HOME_NAV.href}
              onClick={() => setOpen(false)}
              className="block"
            >
              <div className="label-eyebrow">mpc-pollution-331382</div>
              <div className="mt-1 text-[0.95rem] font-medium tracking-tight">
                Seoul Air Quality
              </div>
            </Link>
          </div>
          <nav className="flex flex-col py-2">
            {NAV_ITEMS.map((item) => {
              const active =
                pathname === item.href || pathname?.startsWith(`${item.href}/`);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-2 text-[0.875rem]",
                    active
                      ? "text-[var(--color-fg)]"
                      : "text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]",
                  )}
                >
                  <Icon
                    size={14}
                    strokeWidth={1.75}
                    className={cn(
                      active ? "text-[var(--color-accent)]" : "",
                    )}
                  />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
