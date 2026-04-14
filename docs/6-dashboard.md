# 6. Dashboard (Streamlit & Next.js)

Two dashboards ship side-by-side over the same BigQuery + prediction CSVs:

- **Streamlit** — Plotly + Folium, single-file app. Reference implementation. Entry point: [`streamlit_air_quality_dashboard.py`](../streamlit_air_quality_dashboard.py).
- **Next.js** — Apache ECharts + MapLibre GL, typed TypeScript, visualization-as-code experiment. Entry point: [`frontend/`](../frontend/) — see [`frontend/README.md`](../frontend/README.md) for layout and env vars.

Both render the same 6 tabs against `presentation.dashboard_wide` (live BigQuery) and the prediction CSVs; they are independent deployments.

## Tabs

1. **Time Series Analysis** — pollutant trends with instrument status overlay. Filter by station, pollutant, and date range. Status codes are color-coded (Normal green, Calibration yellow, Abnormal red, Power cut gray).
2. **Geographic Analysis** — Folium map of all 25 stations. Bubble size = mean concentration; color = current class (WHO thresholds).
3. **Data Quality Overview** — missing-data rates by station/pollutant, status distribution histograms, coverage metrics per month.
4. **Statistical Summary** — per-pollutant distributions, inter-pollutant correlations, threshold exceedance counts (WHO 24h guidelines).
5. **Forecasts** — model predictions with 90% prediction interval bands. Overlays historical actuals where available.
6. **Anomaly Detection** — detected anomalies with probability heatmaps by hour-of-day × day-of-week.

## Data Sources

- **Live queries** — [`src.data.loader.bq_to_dataframe`](../src/data/loader.py) reads `logic.measurements_clean` and `presentation.dashboard_wide` on-demand with Streamlit's `@st.cache_data` decorator (TTL 1 hour).
- **Static predictions** — `outputs/forecast_predictions.csv` and `outputs/anomaly_predictions.csv` loaded at startup.

## Running

```bash
make dashboard
# or
streamlit run streamlit_air_quality_dashboard.py
```

Defaults to `http://localhost:8501`. Auth uses `gcloud auth application-default login` credentials.

## Docker

The `docker-compose-up` stack includes the dashboard on port 8501 alongside the API (8080) and MLflow (5001):

```bash
make docker-compose-up
```

## Config

Sidebar controls: station selector (multi-select, 25 stations), pollutant selector (radio, 6 pollutants), date range picker. All filters propagate across tabs via `st.session_state`.
