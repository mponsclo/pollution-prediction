"""Export the DBT presentation layer to a local Parquet snapshot.

Usage: python scripts/export_to_parquet.py

Reads `presentation.dashboard_wide` from the local DuckDB target
(`dbt_pollution/dev.duckdb`, built via `dbt build --target local`) and writes
`data/dashboard_wide.parquet`. Both dashboards can then read this snapshot
offline when the GCP/BigQuery backend is unavailable.

Re-run after any refresh of the DBT models.
"""

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DB = ROOT / "dbt_pollution" / "dev.duckdb"
OUT_PATH = ROOT / "data" / "dashboard_wide.parquet"


def main() -> int:
    if not SOURCE_DB.exists():
        print(
            f"error: {SOURCE_DB} not found. Build it with `cd dbt_pollution && dbt build --target local`.",
            file=sys.stderr,
        )
        return 2

    OUT_PATH.parent.mkdir(exist_ok=True)

    con = duckdb.connect(str(SOURCE_DB), read_only=True)
    # Cast the NUMERIC pollutant columns to DOUBLE so pandas reads floats, not
    # Decimal objects (which would break `.describe()` and ML consumers).
    con.sql(
        """
        SELECT
            measurement_datetime,
            station_code,
            latitude,
            longitude,
            CAST(so2_value  AS DOUBLE) AS so2_value,
            CAST(no2_value  AS DOUBLE) AS no2_value,
            CAST(o3_value   AS DOUBLE) AS o3_value,
            CAST(co_value   AS DOUBLE) AS co_value,
            CAST(pm10_value AS DOUBLE) AS pm10_value,
            CAST(pm2_5_value AS DOUBLE) AS pm2_5_value,
            instrument_status
        FROM main.dashboard_wide
        ORDER BY measurement_datetime, station_code
        """
    ).write_parquet(str(OUT_PATH), compression="zstd")

    rows = con.sql(f"SELECT COUNT(*) AS n FROM read_parquet('{OUT_PATH}')").fetchone()[0]
    size_mb = OUT_PATH.stat().st_size / 1_000_000

    print(f"wrote {OUT_PATH} ({rows:,} rows, {size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
