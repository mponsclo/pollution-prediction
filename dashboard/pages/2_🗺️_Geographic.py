import folium
import streamlit as st
from streamlit_folium import st_folium

from components.filters import render_pollutant_selector, render_sidebar_filters, render_stations_selector
from components.styling import apply_custom_css, apply_page_config

apply_page_config()
apply_custom_css()

state = render_sidebar_filters()
if state is None:
    st.stop()

pollutant_info = state.pollutant_info
all_stations = sorted(state.full_df["station_code"].unique())

st.header("🗺️ Geographic Analysis")

top1, top2 = st.columns([2, 1])
with top1:
    selected_stations = render_stations_selector(all_stations)
with top2:
    selected_pollutant = render_pollutant_selector(pollutant_info)

filtered_df = state.filtered_df[state.filtered_df["station_code"].isin(selected_stations)]
if filtered_df.empty:
    st.warning("No data for the selected stations. Pick at least one.")
    st.stop()

station_agg = (
    filtered_df.groupby(["station_code", "latitude", "longitude"])
    .agg(
        {
            selected_pollutant: ["mean", "count"],
            "status_label": lambda x: x.mode().iloc[0] if not x.empty else "Unknown",
        }
    )
    .reset_index()
)

station_agg.columns = ["station_code", "latitude", "longitude", "avg_value", "record_count", "dominant_status"]

station_agg = station_agg[station_agg["avg_value"] != -1]

if station_agg.empty:
    st.warning("No valid data available for mapping.")
    st.stop()

center_lat = station_agg["latitude"].mean()
center_lon = station_agg["longitude"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

for _, row in station_agg.iterrows():
    color = "red" if row["avg_value"] > pollutant_info[selected_pollutant]["threshold"] else "green"

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=10 + (row["avg_value"] / station_agg["avg_value"].max() * 20),
        popup=f"""
        <b>Station {row["station_code"]}</b><br>
        Average {pollutant_info[selected_pollutant]["name"]}: {row["avg_value"]:.4f} {pollutant_info[selected_pollutant]["unit"]}<br>
        Records: {row["record_count"]}<br>
        Dominant Status: {row["dominant_status"]}
        """,
        color=color,
        weight=2,
        fillColor=color,
        fillOpacity=0.6,
    ).add_to(m)

st.subheader(f"Station Locations - {pollutant_info[selected_pollutant]['name']} Levels")
st_folium(m, width=700, height=500)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏭 Highest Pollution Stations")
    top_stations = station_agg.nlargest(5, "avg_value")[["station_code", "avg_value", "dominant_status"]]
    top_stations["avg_value"] = top_stations["avg_value"].round(4)
    st.dataframe(top_stations, hide_index=True)

with col2:
    st.subheader("✨ Cleanest Stations")
    clean_stations = station_agg.nsmallest(5, "avg_value")[["station_code", "avg_value", "dominant_status"]]
    clean_stations["avg_value"] = clean_stations["avg_value"].round(4)
    st.dataframe(clean_stations, hide_index=True)
