import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { NAV_ITEMS } from "@/lib/nav";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-8 py-24">
      <div className="label-eyebrow">mpc-pollution-331382 · visualization-as-code</div>
      <h1 className="mt-3 text-4xl font-medium leading-tight tracking-tight">
        Seoul Air Quality
      </h1>
      <p className="mt-4 max-w-xl text-[0.95rem] text-[var(--color-fg-muted)]">
        Six panels of hourly readings, forecasts, and anomaly detection across
        25 monitoring stations — rendered from BigQuery and GCS on every
        request. A deliberate alternative to the Streamlit dashboard that ships
        alongside this repo.
      </p>

      <div className="mt-10 flex flex-col divide-y divide-[var(--color-border)]">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="group flex items-start justify-between gap-6 py-4 transition-colors hover:text-[var(--color-fg)]"
            >
              <div className="flex items-start gap-4">
                <Icon
                  size={16}
                  strokeWidth={1.75}
                  className="mt-1 text-[var(--color-accent)]"
                />
                <div>
                  <div className="text-[0.95rem] font-medium">{item.label}</div>
                  <div className="mt-0.5 text-[0.8rem] text-[var(--color-fg-muted)]">
                    {item.description}
                  </div>
                </div>
              </div>
              <ArrowUpRight
                size={16}
                strokeWidth={1.75}
                className="mt-2 text-[var(--color-fg-subtle)] transition-colors group-hover:text-[var(--color-accent)]"
              />
            </Link>
          );
        })}
      </div>
    </main>
  );
}
