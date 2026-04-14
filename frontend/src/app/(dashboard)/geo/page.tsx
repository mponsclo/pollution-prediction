import { fetchStationsLatest } from "@/lib/queries";
import { parseDashboardParams } from "@/lib/params";
import { POLLUTANT_BY_CODE } from "@/lib/constants";
import { StationMapClient } from "@/components/charts/StationMapClient";
import { StationLeaderboard } from "@/components/ui/StationLeaderboard";
import { MetricStrip } from "@/components/kpi/MetricStrip";
import { Panel } from "@/components/ui/Panel";
import { format, parseISO } from "date-fns";

export const dynamic = "force-dynamic";

export default async function GeoPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = parseDashboardParams(await searchParams);
  const rows = await fetchStationsLatest(params);
  const pollutant = POLLUTANT_BY_CODE[params.pollutantCode]!;

  const withValue = rows.filter(
    (r): r is typeof r & { value: number } => r.value != null && r.record_count > 0,
  );
  const sorted = [...withValue].sort((a, b) => b.value - a.value);
  const highest = sorted.slice(0, 5);
  const cleanest = sorted.slice(-5).reverse();
  const above = withValue.filter((r) => r.value > pollutant.threshold).length;
  const noData = rows.length - withValue.length;
  const meanOfMeans =
    withValue.length > 0
      ? withValue.reduce((a, r) => a + r.value, 0) / withValue.length
      : 0;

  return (
    <div className="flex flex-col gap-px bg-[var(--color-border)]">
      <div className="bg-[var(--color-bg)] p-6">
        <MetricStrip
          metrics={[
            { label: "Stations", value: rows.length.toString() },
            {
              label: "With data",
              value: withValue.length.toString(),
              delta: noData > 0 ? `${noData} no-data` : undefined,
              tone: noData === 0 ? "success" : "default",
            },
            {
              label: "Above threshold",
              value: above.toString(),
              delta: `${pollutant.threshold} ${pollutant.unit}`,
              tone: above > 0 ? "threshold" : "success",
            },
            {
              label: "Mean of means",
              value: withValue.length > 0 ? meanOfMeans.toFixed(4) : "—",
              delta: pollutant.unit,
            },
            {
              label: "Window",
              value: `${format(parseISO(params.start), "MMM d")} – ${format(parseISO(params.end), "MMM d")}`,
            },
          ]}
        />
      </div>

      <div className="grid grid-cols-12 gap-px bg-[var(--color-border)]">
        <div className="col-span-12 bg-[var(--color-bg)] p-6 xl:col-span-8">
          <Panel
            tag="Map"
            title={`${pollutant.label} — station locations`}
            subtitle="circle radius scales with mean concentration; colour switches on threshold breach"
            contentClassName="p-0"
          >
            <StationMapClient rows={rows} pollutantCode={params.pollutantCode} />
          </Panel>
        </div>
        <div className="col-span-12 flex flex-col gap-px bg-[var(--color-border)] xl:col-span-4">
          <div className="bg-[var(--color-bg)] p-6 pb-3">
            <Panel
              tag="Top 5"
              title="Highest concentrations"
              subtitle="ranked by mean over window"
            >
              <StationLeaderboard rows={highest} unit={pollutant.unit} />
            </Panel>
          </div>
          <div className="bg-[var(--color-bg)] p-6 pt-3">
            <Panel
              tag="Bottom 5"
              title="Cleanest stations"
              subtitle="ranked by mean over window"
            >
              <StationLeaderboard rows={cleanest} unit={pollutant.unit} />
            </Panel>
          </div>
        </div>
      </div>
    </div>
  );
}
