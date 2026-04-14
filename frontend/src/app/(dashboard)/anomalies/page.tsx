import { loadAnomalies, listTargets, pickTarget } from "@/lib/predictions";
import { AnomalyScore } from "@/components/charts/AnomalyScore";
import { AnomalyHeatmap } from "@/components/charts/AnomalyHeatmap";
import { TargetSelect } from "@/components/filters/TargetSelect";
import { MetricStrip } from "@/components/kpi/MetricStrip";
import { Panel } from "@/components/ui/Panel";
import { format, parseISO } from "date-fns";

export const dynamic = "force-dynamic";

export default async function AnomaliesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const all = await loadAnomalies();
  const targets = listTargets(all);
  const get = (k: string) => {
    const v = sp[k];
    return Array.isArray(v) ? v[0] : v;
  };
  const stationCode = Number(get("station") ?? targets[0]?.station_code);
  const itemCode = Number(get("item") ?? targets[0]?.item_code);
  const filtered = pickTarget(all, stationCode, itemCode);

  const current = targets.find(
    (t) => t.station_code === stationCode && t.item_code === itemCode,
  );

  const n = filtered.length;
  const anomalies = filtered.filter((r) => r.is_anomaly === 1).length;
  const rate = n > 0 ? (100 * anomalies) / n : 0;
  const maxScore = filtered.reduce(
    (a, r) => (r.anomaly_score > a ? r.anomaly_score : a),
    0,
  );
  const firstTs = filtered[0]?.measurement_datetime;
  const lastTs = filtered[filtered.length - 1]?.measurement_datetime;

  return (
    <div className="flex flex-col gap-px bg-[var(--color-border)]">
      <div className="bg-[var(--color-bg)] p-6">
        <MetricStrip
          metrics={[
            { label: "Total hours", value: n.toString() },
            {
              label: "Anomalies",
              value: anomalies.toString(),
              tone: anomalies > 0 ? "threshold" : "success",
            },
            {
              label: "Rate",
              value: `${rate.toFixed(2)}%`,
              tone: rate > 5 ? "threshold" : "default",
            },
            {
              label: "Max score",
              value: maxScore.toFixed(4),
              tone: "accent",
            },
            {
              label: "Window",
              value:
                firstTs && lastTs
                  ? `${format(parseISO(firstTs.replace(" ", "T")), "MMM d")} → ${format(parseISO(lastTs.replace(" ", "T")), "MMM d")}`
                  : "—",
            },
          ]}
        />
      </div>

      <div className="bg-[var(--color-bg)] p-6">
        <Panel
          tag="Score timeline"
          title={`Station ${current?.station_code ?? "?"} · ${(current?.item_name ?? "").toUpperCase()}`}
          subtitle="supervised LightGBM · detected anomalies highlighted"
          action={<TargetSelect targets={targets} activeKey={`${stationCode}-${itemCode}`} />}
          contentClassName="px-3 pb-3"
        >
          <AnomalyScore rows={filtered} />
        </Panel>
      </div>

      <div className="bg-[var(--color-bg)] p-6">
        <Panel
          tag="Temporal pattern"
          title="Hour × day heatmap"
          subtitle="mean anomaly score binned by hour of day and day of month"
          contentClassName="px-3 pb-3"
        >
          <AnomalyHeatmap rows={filtered} />
        </Panel>
      </div>

      <div className="bg-[var(--color-bg)] p-6">
        <Panel
          tag="Raw"
          title="Prediction rows"
          subtitle="source: gs://mpc-pollution-331382-artifacts/predictions/anomaly_predictions.csv (or local fallback)"
        >
          <div className="max-h-[320px] overflow-auto">
            <table className="w-full text-[0.78rem]">
              <thead className="sticky top-0 bg-[var(--color-surface)]">
                <tr className="border-b border-[var(--color-border)] text-left text-[var(--color-fg-muted)]">
                  <th className="py-2 font-normal">Datetime</th>
                  <th className="py-2 text-right font-normal">Anomaly</th>
                  <th className="py-2 text-right font-normal">Score</th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 100).map((r) => (
                  <tr
                    key={r.measurement_datetime}
                    className="border-b border-[var(--color-border)] last:border-b-0"
                  >
                    <td className="num py-1.5 text-[var(--color-fg)]">
                      {r.measurement_datetime}
                    </td>
                    <td className="py-1.5 text-right">
                      {r.is_anomaly ? (
                        <span className="text-[var(--color-threshold)]">1</span>
                      ) : (
                        <span className="text-[var(--color-fg-subtle)]">0</span>
                      )}
                    </td>
                    <td className="num py-1.5 text-right text-[var(--color-fg)]">
                      {Number(r.anomaly_score).toFixed(5)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length > 100 && (
              <div className="px-2 py-2 text-center text-[0.7rem] text-[var(--color-fg-subtle)]">
                showing first 100 of {filtered.length.toLocaleString()} rows
              </div>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
