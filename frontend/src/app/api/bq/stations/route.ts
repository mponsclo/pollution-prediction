import { NextRequest, NextResponse } from "next/server";
import { fetchStationsLatest } from "@/lib/queries";
import { parseDashboardParams } from "@/lib/params";

export const revalidate = 3600;

export async function GET(request: NextRequest) {
  const params = parseDashboardParams(request.nextUrl.searchParams);
  try {
    const rows = await fetchStationsLatest(params);
    return NextResponse.json(
      { params, rows },
      {
        headers: {
          "Cache-Control":
            "public, s-maxage=3600, stale-while-revalidate=86400",
        },
      },
    );
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message, params },
      { status: 500 },
    );
  }
}
