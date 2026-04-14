import {
  fetchMissingByPollutant,
  fetchStatusAvailability,
  fetchMonthlyQuality,
} from "@/lib/queries";
import { parseDashboardParams } from "@/lib/params";
import { HorizontalBars } from "@/components/charts/HorizontalBars";
import { MonthlyTrend } from "@/components/charts/MonthlyTrend";
import { Panel } from "@/components/ui/Panel";
import { MetricStrip } from "@/components/kpi/MetricStrip";

export const dynamic = "force-dynamic";

export default async function QualityPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = parseDashboardParams(await searchParams);
  const [missing, availability, monthly] = await Promise.all([
    fetchMissingByPollutant(params),
    fetchStatusAvailability(params),
    fetchMonthlyQuality(params),
  ]);

  const worst = [...missing].sort((a, b) => b.missing_pct - a.missing_pct)[0];
  const belowTarget = availability.filter((a) => a.availability_pct < 95).length;
  const overallAvail =
    availability.length > 0
      ? availability.reduce((a, b) => a + b.availability_pct, 0) /
        availability.length
      : 0;

  return (
    <div className="flex flex-col gap-px bg-[var(--color-border)]">
      <div className="bg-[var(--color-bg)] p-6">
        <MetricStrip
          metrics={[
            {
              label: "Worst pollutant",
              value: worst ? `${worst.pollutant}` : "—",
              delta: worst ? `${worst.missing_pct.toFixed(1)}% missing` : undefined,
              tone: worst && worst.missing_pct > 5 ? "threshold" : "default",
            },
            {
              label: "Avg availability",
              value: `${overallAvail.toFixed(1)}%`,
              tone: overallAvail >= 95 ? "success" : "default",
            },
            {
              label: "Stations < 95%",
              value: belowTarget.toString(),
              delta: `of ${availability.length}`,
              tone: belowTarget > 0 ? "threshold" : "success",
            },
            {
              label: "Months observed",
              value: monthly.length.toString(),
            },
          ]}
        />
      </div>

      <div className="grid grid-cols-12 gap-px bg-[var(--color-border)]">
        <div className="col-span-12 bg-[var(--color-bg)] p-6 lg:col-span-6">
          <Panel
            tag="Missingness"
            title="Missing values by pollutant"
            subtitle="share of readings with NULL clean_value"
            contentClassName="px-3 pb-3"
          >
            <HorizontalBars
              bars={missing.map((m) => ({
                label: m.pollutant,
                value: m.missing_pct,
                color: m.missing_pct > 5 ? "#ef4444" : "#a78bfa",
              }))}
              unit="%"
              height={260}
            />
          </Panel>
        </div>
        <div className="col-span-12 bg-[var(--color-bg)] p-6 lg:col-span-6">
          <Panel
            tag="Availability"
            title="Status availability by station"
            subtitle="share of readings with non-null instrument status"
            contentClassName="px-3 pb-3"
          >
            <HorizontalBars
              bars={availability.map((a) => ({
                label: String(a.station_code),
                value: a.availability_pct,
                color: a.availability_pct >= 95 ? "#22c55e" : "#ef4444",
              }))}
              unit="%"
              targetLine={{ value: 95, label: "target 95%" }}
              maxValue={100}
              height={Math.max(260, availability.length * 14)}
            />
          </Panel>
        </div>
      </div>

      <div className="bg-[var(--color-bg)] p-6">
        <Panel
          tag="Trend"
          title="Monthly quality trend"
          subtitle="availability and valid-value rates month by month"
          contentClassName="px-3 pb-3"
        >
          <MonthlyTrend rows={monthly} />
        </Panel>
      </div>
    </div>
  );
}
