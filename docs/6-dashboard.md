# 6. Dashboard (Streamlit & Next.js)

Two dashboards ship side-by-side over the same BigQuery + prediction CSVs:

- **Streamlit** — Plotly + Folium, multi-page app (Streamlit `pages/` convention). Reference implementation. Entry point: [`dashboard/Home.py`](../dashboard/Home.py); individual pages live in [`dashboard/pages/`](../dashboard/pages/); shared widgets and data loaders in [`dashboard/components/`](../dashboard/components/) and [`dashboard/data.py`](../dashboard/data.py).
- **Next.js** — Apache ECharts + MapLibre GL, typed TypeScript, visualization-as-code experiment. Entry point: [`frontend/`](../frontend/) — see [`frontend/README.md`](../frontend/README.md) for layout and env vars.

Both render the same 6 pages against `presentation.dashboard_wide` (live BigQuery) and the prediction CSVs; they are independent deployments.

## Pages

1. **Time Series Analysis** — pollutant trends with instrument status overlay. Filter by station, pollutant, and date range. Status codes are color-coded (Normal green, Calibration yellow, Abnormal red, Power cut gray).
2. **Geographic Analysis** — Folium map of all 25 stations. Bubble size = mean concentration; color = current class (WHO thresholds).
3. **Data Quality Overview** — missing-data rates by station/pollutant, status distribution histograms, coverage metrics per month.
4. **Statistical Summary** — per-pollutant distributions, inter-pollutant correlations, threshold exceedance counts (WHO 24h guidelines).
5. **Forecasts** — model predictions with 90% prediction interval bands. Overlays historical actuals where available.
6. **Anomaly Detection** — detected anomalies with probability heatmaps by hour-of-day × day-of-week.

## Data Sources

- **Live queries** — [`src.data.loader.bq_to_dataframe`](../src/data/loader.py) reads `logic.measurements_clean` and `presentation.dashboard_wide` on-demand via [`dashboard/data.py`](../dashboard/data.py) with Streamlit's `@st.cache_data` decorator (TTL 1 hour).
- **Static predictions** — `outputs/forecast_predictions.csv` and `outputs/anomaly_predictions.csv` loaded at startup.

## Running

```bash
make dashboard
# or
PYTHONPATH=. streamlit run dashboard/Home.py
```

Defaults to `http://localhost:8501`. Auth uses `gcloud auth application-default login` credentials. `PYTHONPATH=.` is required so pages can `from src.data.loader import …` (the entry script sits under `dashboard/`, not the repo root).

## Docker

The `docker-compose-up` stack includes the dashboard on port 8501 alongside the API (8080) and MLflow (5001):

```bash
make docker-compose-up
```

## Config

Sidebar controls are rendered by [`dashboard/components/filters.py`](../dashboard/components/filters.py): station multi-select (25 stations), pollutant selector (6 pollutants), date range picker, hour slider, status filter. Selections persist across pages via stable widget keys (`flt_*`). Pages 5–6 (Forecasts, Anomalies) keep their own inline station/pollutant selectors since they read from CSV predictions rather than the live BigQuery table.
