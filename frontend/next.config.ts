import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bundle the Parquet snapshot and prediction CSVs into the serverless
  // functions so DuckDB + CSV readers can find them at runtime.
  // (Files are copied into ./data by scripts/sync-data.mjs before build.)
  outputFileTracingIncludes: {
    "/*": ["./data/**/*.parquet", "./data/predictions/**/*.csv"],
  },
  // DuckDB ships a prebuilt native binary; keep webpack from parsing it.
  serverExternalPackages: ["@duckdb/node-api", "@duckdb/node-bindings"],
};

export default nextConfig;
