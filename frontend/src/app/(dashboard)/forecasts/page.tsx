import { loadForecasts, listTargets, pickTarget } from "@/lib/predictions";
import { POLLUTANT_BY_CODE } from "@/lib/constants";
import { ForecastBand } from "@/components/charts/ForecastBand";
import { TargetSelect } from "@/components/filters/TargetSelect";
import { MetricStrip } from "@/components/kpi/MetricStrip";
import { Panel } from "@/components/ui/Panel";
import { format, parseISO } from "date-fns";

export const dynamic = "force-dynamic";

export default async function ForecastsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const all = await loadForecasts();
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
  const pollutant = POLLUTANT_BY_CODE[itemCode];
  const unit = pollutant?.unit ?? "";

  const values = filtered.map((r) => r.predicted_value);
  const widths = filtered.map((r) => r.predicted_upper_90 - r.predicted_lower_90);
  const hasData = values.length > 0;
  const meanVal = hasData ? values.reduce((a, b) => a + b, 0) / values.length : 0;
  const meanWidth = hasData
    ? widths.reduce((a, b) => a + b, 0) / widths.length
    : 0;
  const minVal = hasData ? Math.min(...values) : 0;
  const maxVal = hasData ? Math.max(...values) : 0;
  const firstTs = filtered[0]?.measurement_datetime;
  const lastTs = filtered[filtered.length - 1]?.measurement_datetime;

  return (
    <div className="flex flex-col gap-px bg-[var(--color-border)]">
      <div className="bg-[var(--color-bg)] p-6">
        <MetricStrip
          metrics={[
            { label: "Horizon", value: `${filtered.length}h` },
            {
              label: "Mean prediction",
              value: meanVal.toFixed(4),
              delta: unit,
            },
            {
              label: "Min / Max",
              value: hasData
                ? `${minVal.toFixed(4)} / ${maxVal.toFixed(4)}`
                : "—",
            },
            {
              label: "Mean 90% width",
              value: meanWidth.toFixed(4),
              tone: "accent",
            },
            {
              label: "Window",
              value: firstTs && lastTs
                ? `${format(parseISO(firstTs.replace(" ", "T")), "MMM d")} → ${format(parseISO(lastTs.replace(" ", "T")), "MMM d")}`
                : "—",
            },
          ]}
        />
      </div>

      <div className="bg-[var(--color-bg)] p-6">
        <Panel
          tag="Forecast"
          title={`Station ${current?.station_code ?? "?"} · ${(current?.item_name ?? "").toUpperCase()}`}
          subtitle="LightGBM ensemble point forecast · CQR 90% prediction interval"
          action={<TargetSelect targets={targets} activeKey={`${stationCode}-${itemCode}`} />}
          contentClassName="px-3 pb-3"
        >
          <ForecastBand rows={filtered} unit={unit} />
        </Panel>
      </div>

      <div className="bg-[var(--color-bg)] p-6">
        <Panel
          tag="Raw"
          title="Prediction rows"
          subtitle={`source: gs://mpc-pollution-331382-artifacts/predictions/forecast_predictions.csv (or local fallback)`}
        >
          <div className="max-h-[320px] overflow-auto">
            <table className="w-full text-[0.78rem]">
              <thead className="sticky top-0 bg-[var(--color-surface)]">
                <tr className="border-b border-[var(--color-border)] text-left text-[var(--color-fg-muted)]">
                  <th className="py-2 font-normal">Datetime</th>
                  <th className="py-2 text-right font-normal">Lower 90</th>
                  <th className="py-2 text-right font-normal">Predicted</th>
                  <th className="py-2 text-right font-normal">Upper 90</th>
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
                    <td className="num py-1.5 text-right text-[var(--color-fg-muted)]">
                      {Number(r.predicted_lower_90).toFixed(4)}
                    </td>
                    <td className="num py-1.5 text-right text-[var(--color-fg)]">
                      {Number(r.predicted_value).toFixed(4)}
                    </td>
                    <td className="num py-1.5 text-right text-[var(--color-fg-muted)]">
                      {Number(r.predicted_upper_90).toFixed(4)}
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
