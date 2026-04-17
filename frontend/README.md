# Next.js Dashboard

Visualization-as-code alternative to the Streamlit app. Same six panels over the same data and prediction CSVs, rendered with Apache ECharts + MapLibre GL instead of Plotly + Folium.

The Streamlit app remains the reference implementation. This exists as an experiment in whether LLM-authored, typed, version-controlled viz code is a viable replacement for the BI-tool middle layer.

> **Read-layer backends** — the dashboard queries are pluggable via `DATA_BACKEND` (default `parquet`). In `parquet` mode, Next.js reads `data/dashboard_wide.parquet` via `@duckdb/node-api` in server components (suitable for Vercel deploys without GCP). Set `DATA_BACKEND=bigquery` to hit BigQuery instead. See the root [README](../README.md) and [docs/9](../docs/9-gcp-exit-plan.md) for the full picture.

## Stack

- **Next.js 16** (App Router) · **TypeScript strict** · **Tailwind CSS v4** · **Turbopack**
- **Apache ECharts** via `echarts-for-react` for all stat charts
- **MapLibre GL** via `react-map-gl/maplibre` with Carto dark-matter tiles for the geo map
- **`@google-cloud/bigquery`** / **`@google-cloud/storage`** over ADC — no service-account keys
- **`date-fns`** · **`papaparse`** (CSV → JSON on the server) · **`lucide-react`** icons

## Routes

| Path | Source | Charts |
|------|--------|--------|
| `/` | — | Landing, links to the six tabs |
| `/timeseries` | `presentation.dashboard_wide` (BQ) | line series per station · status-coloured abnormal scatter · threshold line · status donut |
| `/geo` | `presentation.dashboard_wide` (BQ) | station map (threshold-coloured circles) · top 5 / bottom 5 leaderboards |
| `/quality` | `presentation.dashboard_wide` (BQ) | missing % bars · status availability bars · monthly trend |
| `/stats` | `presentation.dashboard_wide` (BQ) | histogram w/ threshold+mean · inter-station correlation heatmap · per-station percentile table |
| `/forecasts` | `gs://…-artifacts/predictions/forecast_predictions.csv` | predicted line + 90% shaded interval |
| `/anomalies` | `gs://…-artifacts/predictions/anomaly_predictions.csv` | score line + flagged markers · hour×day score heatmap |
| `/api/health` | BQ probe | returns `dashboard_wide` row count |
| `/api/bq/*` | BQ slices | JSON endpoints (`timeseries`, `stations`) |

Pages accept `?pollutant=`, `?start=`, `?end=`, `?stations=` (comma-separated); Forecasts/Anomalies accept `?station=&item=`. State lives in the URL — dashboards are shareable.

## Architecture

```
Browser → Next.js (Vercel, server-rendered)
           ├─ page.tsx → fetchX() → @google-cloud/bigquery (presentation.dashboard_wide)
           ├─ page.tsx → readCsvFromBucket() → @google-cloud/storage (predictions/)
           └─ charts render client-side (ECharts / MapLibre)
```

The existing FastAPI on Cloud Run is **untouched** — the dashboard does not call `/predict/*`. Those endpoints remain for future live-inference features.

## Local development

```bash
cd frontend

# One-time: authenticate so Google SDKs can hit BigQuery and GCS
gcloud auth application-default login

# Install and run
npm install
GCP_PROJECT_ID=mpc-pollution-331382 \
PREDICTIONS_LOCAL_DIR=../outputs \
  npm run dev
# http://localhost:3000
```

`PREDICTIONS_LOCAL_DIR` is a dev convenience — the `/forecasts` and `/anomalies` routes read the CSVs from this directory instead of GCS. Leave it unset to read from `gs://$PREDICTIONS_BUCKET/predictions/`.

### Smoke tests

```bash
curl http://localhost:3000/api/health
# → {"ok":true,"project":"mpc-pollution-331382","dataset":"presentation","checks":{"bq":"ok (NNN rows …)"}}

curl 'http://localhost:3000/api/bq/timeseries?start=2023-12-01T00:00:00&end=2023-12-07T00:00:00&stations=204,205&pollutant=8'
```

### Env vars

| Var | Default | Purpose |
|-----|---------|---------|
| `DATA_BACKEND` | `parquet` | `parquet` reads `data/dashboard_wide.parquet` via DuckDB; `bigquery` hits BQ |
| `DUCKDB_PARQUET_PATH` | `./data/dashboard_wide.parquet` | Override the snapshot path (parquet mode only) |
| `GCP_PROJECT_ID` | `mpc-pollution-331382` | BigQuery + Storage project (bigquery mode) |
| `PREDICTIONS_BUCKET` | `$GCP_PROJECT_ID-artifacts` | GCS bucket for CSV outputs (bigquery mode) |
| `PREDICTIONS_LOCAL_DIR` | `./data/predictions` (copied by `predev`/`prebuild`) | Read CSVs from a local dir instead of GCS |

See `.env.local.example` for the full list.

## Production (Vercel, not yet wired)

The intended deploy path is Vercel with OIDC → GCP Workload Identity Federation (zero SA keys):

1. `terraform apply` creates `mpc-pollution-331382-artifacts` and the `cloud-run-frontend-sa` (dataset-scoped `roles/bigquery.dataViewer` on `presentation`, `roles/bigquery.jobUser`, `roles/storage.objectViewer` on the artifacts bucket).
2. Add a Vercel OIDC provider to the existing WIF pool (`terraform/modules/workload_identity/`).
3. Configure Vercel env vars: `GCP_PROJECT_ID`, `GCP_SA_EMAIL`, `GCP_WIF_PROVIDER`, `VERCEL_OIDC_AUDIENCE`.
4. Upload current CSVs: `python scripts/sync_outputs_to_gcs.py`.
5. Push main → Vercel auto-deploys.

Steps 2–3 (Vercel OIDC ↔ WIF wiring) are deferred until the dashboard is promoted beyond local dev.

## Cost

Default page load runs one parameterised query against `dashboard_wide` (~650k rows, partitioned on `measurement_datetime`). With `unstable_cache` / route `Cache-Control: s-maxage=3600`, BigQuery bytes billed should stay well under $1/month at portfolio traffic. If the default range widens to multi-year, add a materialised view `presentation.dashboard_daily_agg` for the all-time view.

## Layout

```
frontend/
├── src/
│   ├── app/
│   │   ├── (dashboard)/          # Route group — six pages + shared sidebar/topbar
│   │   │   ├── layout.tsx        # Sidebar + TopBar + GlobalFilters
│   │   │   ├── timeseries/page.tsx
│   │   │   ├── geo/page.tsx
│   │   │   ├── quality/page.tsx
│   │   │   ├── stats/page.tsx
│   │   │   ├── forecasts/page.tsx
│   │   │   └── anomalies/page.tsx
│   │   ├── api/
│   │   │   ├── health/route.ts
│   │   │   └── bq/{timeseries,stations}/route.ts
│   │   ├── layout.tsx            # Root: fonts, <html>, <body>
│   │   ├── page.tsx              # Landing
│   │   └── globals.css           # Tailwind v4 @theme tokens
│   ├── components/
│   │   ├── charts/               # ECharts + MapLibre wrappers
│   │   ├── filters/              # URL-driven filter components
│   │   ├── kpi/MetricStrip.tsx
│   │   ├── layout/{Sidebar,TopBar}.tsx
│   │   └── ui/{Panel,StationLeaderboard,PlaceholderPanel}.tsx
│   └── lib/
│       ├── bq.ts                 # BigQuery singleton + runQuery()
│       ├── gcs.ts                # GCS reader with local-dir fallback
│       ├── queries.ts            # Typed SQL functions
│       ├── predictions.ts        # CSV → typed rows
│       ├── stats.ts              # correlation, overall stats, quantiles
│       ├── constants.ts          # Mirrors src/utils/constants.py
│       ├── nav.ts                # Sidebar items
│       ├── params.ts             # searchParams parsing
│       └── cn.ts                 # clsx wrapper
├── next.config.ts
├── package.json
└── tsconfig.json
```
