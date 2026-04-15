import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.filters import render_sidebar_filters
from components.styling import apply_custom_css, apply_page_config

apply_page_config()
apply_custom_css()

state = render_sidebar_filters()
if state is None:
    st.stop()

filtered_df = state.filtered_df
selected_pollutant = state.selected_pollutant
pollutant_info = state.pollutant_info
status_colors = state.status_colors

st.header("📊 Time Series Analysis")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader(f"{pollutant_info[selected_pollutant]['name']} Levels Over Time")

with col2:
    agg_level = st.selectbox(
        "Aggregation", ["Raw Data", "Hourly Avg", "Daily Avg"], help="Choose data aggregation level"
    )

with col3:
    show_missing = st.checkbox("Show -1 Values", value=True, help="Display missing values (-1) in the chart")

plot_df = filtered_df.copy()

if not show_missing:
    plot_df = plot_df[plot_df[selected_pollutant] != -1]

if agg_level == "Daily Avg":
    plot_df = (
        plot_df.groupby(["date", "station_code", "status_label"])
        .agg({selected_pollutant: "mean", "measurement_datetime": "first"})
        .reset_index()
    )
elif agg_level == "Hourly Avg":
    plot_df = (
        plot_df.groupby(["measurement_datetime", "station_code", "status_label"])
        .agg({selected_pollutant: "mean"})
        .reset_index()
    )

fig = go.Figure()

for station in plot_df["station_code"].unique():
    station_data = plot_df[plot_df["station_code"] == station]

    for status in station_data["status_label"].unique():
        status_data = station_data[station_data["status_label"] == status]

        if len(status_data) > 0:
            fig.add_trace(
                go.Scatter(
                    x=status_data["measurement_datetime"]
                    if agg_level != "Daily Avg"
                    else pd.to_datetime(status_data["date"]),
                    y=status_data[selected_pollutant],
                    mode="lines+markers",
                    name=f"Station {station} - {status}",
                    line=dict(color=status_colors[status], width=2),
                    marker=dict(size=4, color=status_colors[status]),
                    hovertemplate=f"<b>Station {station}</b><br>"
                    + f"Status: {status}<br>"
                    + "Time: %{x}<br>"
                    + f"{pollutant_info[selected_pollutant]['name']}: %{{y:.4f}} {pollutant_info[selected_pollutant]['unit']}<br>"
                    + "<extra></extra>",
                )
            )

threshold = pollutant_info[selected_pollutant]["threshold"]
fig.add_hline(
    y=threshold,
    line_dash="dash",
    line_color="red",
    annotation_text=f"Health Threshold ({threshold} {pollutant_info[selected_pollutant]['unit']})",
    annotation_position="top right",
)

fig.update_layout(
    title=f"{pollutant_info[selected_pollutant]['name']} Concentration with Status Information",
    xaxis_title="Time",
    yaxis_title=f"Concentration ({pollutant_info[selected_pollutant]['unit']})",
    height=600,
    showlegend=True,
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Status Distribution Over Selected Period")

status_dist = filtered_df.groupby(["status_label"]).size().reset_index(name="count")
status_dist["percentage"] = (status_dist["count"] / status_dist["count"].sum() * 100).round(2)

fig_status = px.pie(
    status_dist,
    values="count",
    names="status_label",
    color="status_label",
    color_discrete_map=status_colors,
    title="Distribution of Instrument Status",
)

fig_status.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig_status, use_container_width=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_records = len(filtered_df)
    st.metric("Total Records", f"{total_records:,}")

with col2:
    missing_values = (filtered_df[selected_pollutant] == -1).sum()
    st.metric("Missing Values (-1)", f"{missing_values:,}", delta=f"{missing_values / total_records * 100:.1f}%")

with col3:
    normal_status = (filtered_df["status_label"] == "Normal").sum()
    st.metric("Normal Status", f"{normal_status:,}", delta=f"{normal_status / total_records * 100:.1f}%")

with col4:
    missing_status = (filtered_df["status_label"] == "Missing Status").sum()
    st.metric("Missing Status", f"{missing_status:,}", delta=f"{missing_status / total_records * 100:.1f}%")
