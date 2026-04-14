import { BigQuery } from "@google-cloud/bigquery";
import { BQ_PROJECT } from "./constants";

let client: BigQuery | undefined;

export function getBigQueryClient(): BigQuery {
  if (!client) {
    client = new BigQuery({ projectId: BQ_PROJECT });
  }
  return client;
}

export type QueryParams = Record<string, string | number | boolean | string[] | number[] | null>;

export async function runQuery<T>(
  sql: string,
  params: QueryParams = {},
): Promise<T[]> {
  const [rows] = await getBigQueryClient().query({
    query: sql,
    params,
    location: "asia-northeast3",
  });
  return rows as T[];
}
