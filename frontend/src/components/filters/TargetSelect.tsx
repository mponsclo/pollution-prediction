"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useTransition } from "react";

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

  const onChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const [stationCode, itemCode] = e.target.value.split("-");
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
      <select
        value={activeKey}
        onChange={onChange}
        disabled={pending}
        className="hairline bg-[var(--color-surface)] px-2 py-1 text-[var(--color-fg)] outline-none focus:border-[var(--color-accent)]"
      >
        {targets.map((t) => (
          <option key={t.key} value={t.key} className="bg-[var(--color-bg)]">
            Station {t.station_code} · {t.item_name.toUpperCase()}
          </option>
        ))}
      </select>
    </label>
  );
}
