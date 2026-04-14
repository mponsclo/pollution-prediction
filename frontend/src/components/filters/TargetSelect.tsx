"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useTransition } from "react";
import { ThemedSelect } from "@/components/ui/ThemedSelect";

export type Target = {
  station_code: number;
  item_code: number;
  item_name: string;
  key: string;
};

export function TargetSelect({
  targets,
  activeKey,
}: {
  targets: Target[];
  activeKey: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [pending, startTransition] = useTransition();

  const onChange = (value: string) => {
    const [stationCode, itemCode] = value.split("-");
    const next = new URLSearchParams(searchParams);
    next.set("station", stationCode);
    next.set("item", itemCode);
    startTransition(() => {
      router.push(`${pathname}?${next.toString()}`);
    });
  };

  return (
    <label className="flex items-center gap-2 text-[0.75rem]">
      <span className="label-eyebrow">Target</span>
      <ThemedSelect
        ariaLabel="Select station and pollutant target"
        value={activeKey}
        disabled={pending}
        onValueChange={onChange}
        items={targets.map((t) => ({
          value: t.key,
          label: (
            <span className="flex items-center gap-2">
              <span className="text-[var(--color-fg-muted)]">Station</span>
              <span className="num text-[var(--color-fg)]">
                {t.station_code}
              </span>
              <span className="text-[var(--color-fg-subtle)]">·</span>
              <span className="text-[var(--color-accent)]">
                {t.item_name.toUpperCase()}
              </span>
            </span>
          ),
        }))}
      />
    </label>
  );
}
