import { fetchTimeSeries } from "@/lib/queries";
import { parseDashboardParams } from "@/lib/params";
import { POLLUTANT_BY_CODE, STATUS_BY_CODE } from "@/lib/constants";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";
import { StatusPie } from "@/components/charts/StatusPie";
import { MetricStrip } from "@/components/kpi/MetricStrip";
import { Panel } from "@/components/ui/Panel";
import { format, parseISO } from "date-fns";

export const dynamic = "force-dynamic";

export default async function TimeSeriesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = parseDashboardParams(await searchParams);
  const rows = await fetchTimeSeries(params);
  const pollutant = POLLUTANT_BY_CODE[params.pollutantCode]!;

  const nRows = rows.length;
  const valid = rows.filter((r) => r.value != null);
  const missingPct = nRows > 0 ? (100 * (nRows - valid.length)) / nRows : 0;
  const statusCounts: Record<number, number> = {};
  for (const r of rows) {
    statusCounts[r.instrument_status] =
      (statusCounts[r.instrument_status] ?? 0) + 1;
  }
  const normalPct =
    nRows > 0 ? (100 * (statusCounts[0] ?? 0)) / nRows : 0;
  const mean =
    valid.length > 0
      ? valid.reduce((a, r) => a + (r.value ?? 0), 0) / valid.length
      : 0;
  const above = valid.filter((r) => (r.value ?? 0) > pollutant.threshold).length;

  return (
    <div className="flex flex-col gap-px bg-[var(--color-border)]">
      <div className="bg-[var(--color-bg)] p-6">
        <MetricStrip
          metrics={[
            { label: "Readings", value: nRows.toLocaleString() },
            {
              label: "Missing",
              value: `${missingPct.toFixed(1)}%`,
              tone: missingPct > 5 ? "threshold" : "default",
            },
            {
              label: "Normal status",
              value: `${normalPct.toFixed(1)}%`,
              tone: normalPct > 95 ? "success" : "default",
            },
            {
              label: `Mean ${pollutant.label}`,
              value: mean.toFixed(4),
              delta: pollutant.unit,
            },
            {
              label: "Above threshold",
              value: above.toLocaleString(),
              delta: `of ${valid.length.toLocaleString()} valid`,
              tone: above > 0 ? "threshold" : "default",
            },
          ]}
        />
      </div>

      <div className="grid grid-cols-12 gap-px bg-[var(--color-border)]">
        <div className="col-span-12 bg-[var(--color-bg)] p-6 xl:col-span-9">
          <Panel
            tag="Series"
            title={`${pollutant.label} concentration`}
            subtitle={`${format(parseISO(params.start), "MMM d, yyyy")} – ${format(parseISO(params.end), "MMM d, yyyy")} · ${params.stations.length} stations`}
            action={
              <span className="font-mono text-[0.68rem] text-[var(--color-fg-subtle)]">
                threshold {pollutant.threshold} {pollutant.unit}
              </span>
            }
            contentClassName="px-2 pb-2"
          >
            <TimeSeriesChart
              rows={rows}
              pollutantCode={params.pollutantCode}
              stations={params.stations}
            />
          </Panel>
        </div>

        <div className="col-span-12 flex flex-col gap-px bg-[var(--color-border)] xl:col-span-3">
          <div className="bg-[var(--color-bg)] p-6 pb-3">
            <Panel tag="Distribution" title="Status mix">
              <StatusPie counts={statusCounts} />
            </Panel>
          </div>
          <div className="bg-[var(--color-bg)] p-6 pt-3">
            <Panel tag="Breakdown" title="By status">
              <table className="w-full text-[0.78rem]">
                <tbody>
                  {Object.entries(statusCounts)
                    .map(([code, n]) => [Number(code), n] as const)
                    .sort((a, b) => b[1] - a[1])
                    .map(([code, n]) => {
                      const s = STATUS_BY_CODE[code];
                      return (
                        <tr
                          key={code}
                          className="border-b border-[var(--color-border)] last:border-b-0"
                        >
                          <td className="py-1.5">
                            <span
                              className="inline-block h-[8px] w-[8px] rounded-sm align-middle"
                              style={{
                                background: s?.color ?? "#737373",
                              }}
                            />
                            <span className="ml-2 text-[var(--color-fg)]">
                              {s?.label ?? `code ${code}`}
                            </span>
                          </td>
                          <td className="py-1.5 text-right">
                            <span className="num text-[var(--color-fg-muted)]">
                              {n.toLocaleString()}
                            </span>
                          </td>
                          <td className="py-1.5 pl-3 text-right">
                            <span className="num text-[var(--color-fg-subtle)]">
                              {((100 * n) / nRows).toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </Panel>
          </div>
        </div>
      </div>
    </div>
  );
}
