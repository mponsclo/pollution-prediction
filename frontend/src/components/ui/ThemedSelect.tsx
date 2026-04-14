"use client";

import * as Select from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type ThemedSelectItem = {
  value: string;
  label: ReactNode;
  hint?: string;
};

export function ThemedSelect({
  value,
  onValueChange,
  items,
  ariaLabel,
  disabled,
  triggerClassName,
  placeholder,
}: {
  value: string;
  onValueChange: (v: string) => void;
  items: ThemedSelectItem[];
  ariaLabel: string;
  disabled?: boolean;
  triggerClassName?: string;
  placeholder?: string;
}) {
  return (
    <Select.Root value={value} onValueChange={onValueChange} disabled={disabled}>
      <Select.Trigger
        aria-label={ariaLabel}
        className={cn(
          "hairline group inline-flex items-center gap-2 bg-[var(--color-surface)] px-3 py-1.5 text-[0.78rem] text-[var(--color-fg)] outline-none transition-colors hover:border-[var(--color-border-strong)] focus-visible:border-[var(--color-accent)] disabled:opacity-60",
          triggerClassName,
        )}
      >
        <Select.Value placeholder={placeholder} />
        <Select.Icon>
          <ChevronDown
            size={12}
            className="text-[var(--color-fg-subtle)] transition-transform group-data-[state=open]:rotate-180"
          />
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content
          position="popper"
          sideOffset={6}
          className="hairline z-50 min-w-[var(--radix-select-trigger-width)] bg-[var(--color-surface)] shadow-2xl"
        >
          <Select.Viewport className="p-1">
            {items.map((item) => (
              <Select.Item
                key={item.value}
                value={item.value}
                className="relative flex cursor-pointer select-none items-center gap-2 rounded-sm px-3 py-1.5 pr-8 text-[0.78rem] text-[var(--color-fg-muted)] outline-none data-[highlighted]:bg-[var(--color-surface-hover)] data-[highlighted]:text-[var(--color-fg)] data-[state=checked]:text-[var(--color-fg)]"
              >
                <Select.ItemText>{item.label}</Select.ItemText>
                {item.hint && (
                  <span className="text-[0.68rem] text-[var(--color-fg-subtle)]">
                    {item.hint}
                  </span>
                )}
                <Select.ItemIndicator className="absolute right-2 top-1/2 -translate-y-1/2">
                  <Check size={12} className="text-[var(--color-accent)]" />
                </Select.ItemIndicator>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}
