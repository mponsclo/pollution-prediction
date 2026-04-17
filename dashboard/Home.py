import pandas as pd
import streamlit as st

from components.filters import render_sidebar_filters, render_stations_selector
from components.styling import apply_custom_css, apply_page_config

apply_page_config()
apply_custom_css()

st.markdown('<h1 class="main-header">🌬️ Seoul Air Quality Dashboard</h1>', unsafe_allow_html=True)
st.markdown(
    "Forecasting and anomaly detection across **25 stations**, **6 pollutants**, "
    "hourly measurements from **2021–2023**. "
    "Use the sidebar to filter; use the left-hand nav to switch pages."
)

state = render_sidebar_filters()
if state is None:
    st.stop()

all_stations = sorted(state.full_df["station_code"].unique())
selector_col, _ = st.columns([1, 2])
with selector_col:
    selected_stations = render_stations_selector(all_stations)

page_df = state.filtered_df[state.filtered_df["station_code"].isin(selected_stations)]
if page_df.empty:
    st.warning("No data for the selected stations. Pick at least one.")
    st.stop()

st.subheader("📌 At a glance")

total_stations = page_df["station_code"].nunique()
total_records = len(page_df)
date_min = page_df["date"].min()
date_max = page_df["date"].max()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Stations in view", f"{total_stations}")
kpi2.metric("Records in view", f"{total_records:,}")
kpi3.metric("From", f"{pd.Timestamp(date_min):%Y-%m-%d}")
kpi4.metric("To", f"{pd.Timestamp(date_max):%Y-%m-%d}")

st.markdown("**Average concentrations** (filtered stations / dates / hours)")
avg_cols = st.columns(len(state.pollutant_info))
for col, (pollutant_col, meta) in zip(avg_cols, state.pollutant_info.items()):
    series = page_df[page_df[pollutant_col] != -1][pollutant_col]
    avg = series.mean() if not series.empty else None
    decimals = 1 if meta["unit"] == "mg/m³" else 4
    col.metric(
        f"Avg {meta['name']} ({meta['unit']})",
        f"{avg:.{decimals}f}" if avg is not None else "—",
    )

st.divider()

st.subheader("🧭 Explore")

row1 = st.columns(3)
row1[0].page_link("pages/1_📊_Time_Series.py", label="📊 Time Series", help="Concentration over time per station")
row1[1].page_link("pages/2_🗺️_Geographic.py", label="🗺️ Geographic", help="Station map + pollution ranking")
row1[2].page_link("pages/3_📈_Data_Quality.py", label="📈 Data Quality", help="Missing values and status availability")

row2 = st.columns(3)
row2[0].page_link("pages/4_📋_Statistics.py", label="📋 Statistics", help="Distributions and inter-station correlation")
row2[1].page_link("pages/5_🔮_Forecasts.py", label="🔮 Forecasts", help="LightGBM ensemble + 90% prediction intervals")
row2[2].page_link("pages/6_⚠️_Anomalies.py", label="⚠️ Anomalies", help="Supervised anomaly detection results")
