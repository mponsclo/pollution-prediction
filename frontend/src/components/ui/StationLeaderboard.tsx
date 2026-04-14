import type { StationLatestRow } from "@/lib/queries";

export function StationLeaderboard({
  rows,
  unit,
  decimals = 4,
}: {
  rows: StationLatestRow[];
  unit: string;
  decimals?: number;
}) {
  if (rows.length === 0) {
    return (
      <div className="py-4 text-[0.75rem] text-[var(--color-fg-subtle)]">
        no data in window
      </div>
    );
  }
  return (
    <table className="w-full text-[0.78rem]">
      <tbody>
        {rows.map((r) => (
          <tr
            key={r.station_code}
            className="border-b border-[var(--color-border)] last:border-b-0"
          >
            <td className="py-2 text-[var(--color-fg-muted)]">
              <span className="num">{r.station_code}</span>
            </td>
            <td className="py-2 text-right">
              <span className="num text-[var(--color-fg)]">
                {r.value != null ? r.value.toFixed(decimals) : "—"}
              </span>
              <span className="ml-1 text-[0.68rem] text-[var(--color-fg-subtle)]">
                {unit}
              </span>
            </td>
            <td className="py-2 pl-3 text-right font-mono text-[0.68rem] text-[var(--color-fg-subtle)]">
              {r.record_count?.toLocaleString()}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
