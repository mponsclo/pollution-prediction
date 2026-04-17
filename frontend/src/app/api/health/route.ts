import { NextResponse } from "next/server";
import { runQuery as runBq } from "@/lib/bq";
import { runQuery as runDuck } from "@/lib/duck";
import { BQ_PROJECT, BQ_DATASET_PRESENTATION } from "@/lib/constants";

export const dynamic = "force-dynamic";

type Probe = { row_count: number };

export async function GET() {
  const checks: Record<string, string> = {};
  let ok = true;
  const backend = process.env.DATA_BACKEND === "bigquery" ? "bigquery" : "parquet";

  try {
    let rows: Probe[];
    if (backend === "bigquery") {
      rows = await runBq<Probe>(
        `SELECT COUNT(*) AS row_count
         FROM \`${BQ_PROJECT}.${BQ_DATASET_PRESENTATION}.dashboard_wide\`
         LIMIT 1`,
      );
    } else {
      rows = await runDuck<Probe>(
        `SELECT COUNT(*)::INTEGER AS row_count FROM dashboard_wide`,
      );
    }
    checks[backend] = `ok (${rows[0]?.row_count ?? 0} rows in dashboard_wide)`;
  } catch (err) {
    ok = false;
    checks[backend] = `error: ${(err as Error).message}`;
  }

  return NextResponse.json(
    {
      ok,
      backend,
      project: BQ_PROJECT,
      dataset: BQ_DATASET_PRESENTATION,
      checks,
    },
    { status: ok ? 200 : 503 },
  );
}
