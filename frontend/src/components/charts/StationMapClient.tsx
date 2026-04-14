"use client";

import dynamic from "next/dynamic";

export const StationMapClient = dynamic(
  () => import("./StationMap").then((m) => m.StationMap),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[520px] items-center justify-center text-[0.8rem] text-[var(--color-fg-subtle)]">
        loading map…
      </div>
    ),
  }
);
