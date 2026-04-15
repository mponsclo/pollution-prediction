import streamlit as st

from components.filters import render_sidebar_filters
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

st.subheader("📌 At a glance")

total_stations = state.filtered_df["station_code"].nunique()
total_records = len(state.filtered_df)
date_min = state.filtered_df["date"].min()
date_max = state.filtered_df["date"].max()
pollutant_meta = state.pollutant_info[state.selected_pollutant]
valid_values = state.filtered_df[state.filtered_df[state.selected_pollutant] != -1][state.selected_pollutant]
avg_value = valid_values.mean() if not valid_values.empty else None

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Stations in view", f"{total_stations}")
kpi2.metric("Records in view", f"{total_records:,}")
kpi3.metric("Date range", f"{date_min} → {date_max}")
kpi4.metric(
    f"Avg {pollutant_meta['name']}",
    f"{avg_value:.4f} {pollutant_meta['unit']}" if avg_value is not None else "—",
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
