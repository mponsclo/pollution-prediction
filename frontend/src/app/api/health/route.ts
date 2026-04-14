import { NextResponse } from "next/server";
import { runQuery } from "@/lib/bq";
import { BQ_PROJECT, BQ_DATASET_PRESENTATION } from "@/lib/constants";

export const dynamic = "force-dynamic";

type Probe = { row_count: number };

export async function GET() {
  const checks: Record<string, string> = {};
  let ok = true;

  try {
    const rows = await runQuery<Probe>(
      `SELECT COUNT(*) AS row_count
       FROM \`${BQ_PROJECT}.${BQ_DATASET_PRESENTATION}.dashboard_wide\`
       LIMIT 1`,
    );
    checks.bq = `ok (${rows[0]?.row_count ?? 0} rows in dashboard_wide)`;
  } catch (err) {
    ok = false;
    checks.bq = `error: ${(err as Error).message}`;
  }

  return NextResponse.json(
    {
      ok,
      project: BQ_PROJECT,
      dataset: BQ_DATASET_PRESENTATION,
      checks,
    },
    { status: ok ? 200 : 503 },
  );
}
