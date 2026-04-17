import path from "node:path";
import {
  DuckDBInstance,
  type DuckDBConnection,
  type DuckDBValue,
} from "@duckdb/node-api";

// Singleton — the Parquet is attached as a view on first use.
let connectionPromise: Promise<DuckDBConnection> | undefined;

function parquetPath(): string {
  const fromEnv = process.env.DUCKDB_PARQUET_PATH;
  if (fromEnv) return path.resolve(fromEnv);
  // Scoped to ./data to avoid Turbopack tracing the whole project root.
  return path.join(
    /*turbopackIgnore: true*/ process.cwd(),
    "data",
    "dashboard_wide.parquet",
  );
}

async function initConnection(): Promise<DuckDBConnection> {
  const instance = await DuckDBInstance.create(":memory:");
  const connection = await instance.connect();
  // DuckDB can't bind parameters on DDL — escape + interpolate directly.
  const parquet = parquetPath().replace(/'/g, "''");
  await connection.run(
    `CREATE VIEW dashboard_wide AS SELECT * FROM read_parquet('${parquet}')`,
  );
  return connection;
}

function getConnection(): Promise<DuckDBConnection> {
  if (!connectionPromise) {
    connectionPromise = initConnection().catch((err) => {
      // Reset so a retry can attempt reinitialization.
      connectionPromise = undefined;
      throw err;
    });
  }
  return connectionPromise;
}

export type QueryParams = Record<
  string,
  string | number | boolean | string[] | number[] | null
>;

export async function runQuery<T>(
  sql: string,
  params: QueryParams = {},
): Promise<T[]> {
  const connection = await getConnection();
  const reader = await connection.runAndReadAll(
    sql,
    params as Record<string, DuckDBValue>,
  );
  return reader.getRowObjectsJS() as T[];
}
