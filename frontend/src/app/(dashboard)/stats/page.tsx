import { fetchStats, fetchTimeSeries } from "@/lib/queries";
import { parseDashboardParams } from "@/lib/params";
import { POLLUTANT_BY_CODE } from "@/lib/constants";
import { correlationByStation, overallStats } from "@/lib/stats";
import { Histogram } from "@/components/charts/Histogram";
import { CorrelationHeatmap } from "@/components/charts/CorrelationHeatmap";
import { MetricStrip } from "@/components/kpi/MetricStrip";
import { Panel } from "@/components/ui/Panel";

export const dynamic = "force-dynamic";

export default async function StatsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = parseDashboardParams(await searchParams);
  const pollutant = POLLUTANT_BY_CODE[params.pollutantCode]!;

  const [perStation, rawSeries] = await Promise.all([
    fetchStats(params),
    fetchTimeSeries(params),
  ]);

  const values: number[] = [];
  for (const r of rawSeries) {
    if (r.value != null) values.push(r.value);
  }
  const stats = overallStats(values);
  const above = values.filter((v) => v > pollutant.threshold).length;
  const abovePct =
    values.length > 0 ? (100 * above) / values.length : 0;

  const { stations, matrix } = correlationByStation(rawSeries, params.stations);

  return (
    <div className="flex flex-col gap-px bg-[var(--color-border)]">
      <div className="bg-[var(--color-bg)] p-6">
        <MetricStrip
          metrics={[
            { label: "Count", value: stats.n.toLocaleString() },
            {
              label: "Mean",
              value: Number.isFinite(stats.mean) ? stats.mean.toFixed(4) : "—",
              delta: pollutant.unit,
            },
            {
              label: "Median",
              value: Number.isFinite(stats.median) ? stats.median.toFixed(4) : "—",
            },
            {
              label: "Std dev",
              value: Number.isFinite(stats.stddev) ? stats.stddev.toFixed(4) : "—",
            },
            {
              label: `Above ${pollutant.threshold}${pollutant.unit}`,
              value: above.toLocaleString(),
              delta: `${abovePct.toFixed(1)}%`,
              tone: abovePct > 0 ? "threshold" : "success",
            },
          ]}
        />
      </div>

      <div className="bg-[var(--color-bg)] p-6">
        <div className="hairline bg-[var(--color-surface)]">
          <div className="grid grid-cols-2 divide-x divide-[var(--color-border)] md:grid-cols-6">
            {[
              ["Min", stats.min],
              ["P75", stats.p75],
              ["P90", stats.p90],
              ["P95", stats.p95],
              ["P99", stats.p99],
              ["Max", stats.max],
            ].map(([label, v]) => (
              <div key={String(label)} className="px-5 py-3">
                <div className="label-eyebrow">{label}</div>
                <div className="num mt-1 text-[1rem] text-[var(--color-fg)]">
                  {Number.isFinite(v as number)
                    ? (v as number).toFixed(4)
                    : "—"}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-px bg-[var(--color-border)]">
        <div className="col-span-12 bg-[var(--color-bg)] p-6 lg:col-span-7">
          <Panel
            tag="Distribution"
            title={`${pollutant.label} histogram`}
            subtitle="overlaid with health threshold (red) and mean (green)"
            contentClassName="px-3 pb-3"
          >
            <Histogram
              values={values}
              bins={40}
              threshold={pollutant.threshold}
              mean={stats.mean}
              unit={pollutant.unit}
            />
          </Panel>
        </div>
        <div className="col-span-12 bg-[var(--color-bg)] p-6 lg:col-span-5">
          <Panel
            tag="Correlation"
            title="Inter-station correlation"
            subtitle={`Pearson r on ${pollutant.label} across ${stations.length} stations`}
            contentClassName="px-3 pb-3"
          >
            <CorrelationHeatmap
              labels={stations.map(String)}
              matrix={matrix}
              height={420}
            />
          </Panel>
        </div>
      </div>

      <div className="bg-[var(--color-bg)] p-6">
        <Panel
          tag="Per-station"
          title="Percentile breakdown"
          subtitle="BigQuery APPROX_QUANTILES per station"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-[0.78rem]">
              <thead>
                <tr className="border-b border-[var(--color-border)] text-left text-[var(--color-fg-muted)]">
                  <th className="py-2 font-normal">Station</th>
                  <th className="py-2 text-right font-normal">n</th>
                  <th className="py-2 text-right font-normal">mean</th>
                  <th className="py-2 text-right font-normal">std</th>
                  <th className="py-2 text-right font-normal">p50</th>
                  <th className="py-2 text-right font-normal">p90</th>
                  <th className="py-2 text-right font-normal">p95</th>
                  <th className="py-2 text-right font-normal">p99</th>
                  <th className="py-2 text-right font-normal">max</th>
                </tr>
              </thead>
              <tbody>
                {perStation.map((r) => (
                  <tr
                    key={r.station_code}
                    className="border-b border-[var(--color-border)] last:border-b-0"
                  >
                    <td className="py-1.5 text-[var(--color-fg)]">
                      <span className="num">{r.station_code}</span>
                    </td>
                    <td className="num py-1.5 text-right text-[var(--color-fg-muted)]">
                      {r.n?.toLocaleString?.() ?? "—"}
                    </td>
                    <td className="num py-1.5 text-right">
                      {Number(r.mean ?? 0).toFixed(4)}
                    </td>
                    <td className="num py-1.5 text-right text-[var(--color-fg-muted)]">
                      {Number(r.stddev ?? 0).toFixed(4)}
                    </td>
                    <td className="num py-1.5 text-right">{Number(r.p50 ?? 0).toFixed(4)}</td>
                    <td className="num py-1.5 text-right">{Number(r.p90 ?? 0).toFixed(4)}</td>
                    <td className="num py-1.5 text-right">{Number(r.p95 ?? 0).toFixed(4)}</td>
                    <td className="num py-1.5 text-right">{Number(r.p99 ?? 0).toFixed(4)}</td>
                    <td
                      className={`num py-1.5 text-right ${Number(r.max) > pollutant.threshold ? "text-[var(--color-threshold)]" : ""}`}
                    >
                      {Number(r.max ?? 0).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}
