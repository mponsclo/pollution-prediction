import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bundle the Parquet snapshot, prediction CSVs, and the DuckDB native
  // binding *package* (including the libduckdb.so shared library that
  // duckdb.node dlopens at runtime — the NFT tracer follows the require
  // of .node but misses the dlopen, so we include the whole package).
  // Files under ./data are copied by scripts/sync-data.mjs before build.
  outputFileTracingIncludes: {
    "/*": [
      "./data/**/*.parquet",
      "./data/predictions/**/*.csv",
      "./node_modules/@duckdb/node-bindings-linux-x64/**/*",
      "./node_modules/@duckdb/node-bindings-linux-arm64/**/*",
      "./node_modules/@duckdb/node-bindings-darwin-arm64/**/*",
      "./node_modules/@duckdb/node-bindings-darwin-x64/**/*",
    ],
  },
  // Keep webpack/turbopack from bundling the native bindings — they must
  // be resolved at runtime via Node's normal require so dlopen can find
  // the co-located libduckdb shared library.
  serverExternalPackages: ["@duckdb/node-api", "@duckdb/node-bindings"],
};

export default nextConfig;
