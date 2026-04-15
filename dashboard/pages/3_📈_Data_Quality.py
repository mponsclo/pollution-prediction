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

full_df = state.full_df
pollutant_info = state.pollutant_info

st.header("📈 Data Quality Overview")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Missing Values by Pollutant (-1 values)")

    pollutant_cols = list(pollutant_info.keys())
    missing_data = []

    for col in pollutant_cols:
        missing_count = (full_df[col] == -1).sum()
        missing_pct = (missing_count / len(full_df)) * 100
        missing_data.append(
            {"Pollutant": pollutant_info[col]["name"], "Missing Count": missing_count, "Missing %": missing_pct}
        )

    missing_df = pd.DataFrame(missing_data)

    fig_missing = px.bar(
        missing_df,
        x="Pollutant",
        y="Missing %",
        title="Percentage of Missing Values by Pollutant",
        color="Missing %",
        color_continuous_scale="Reds",
    )

    st.plotly_chart(fig_missing, use_container_width=True)

with col2:
    st.subheader("Status Availability by Station")

    station_quality = (
        full_df.groupby("station_code")
        .agg({"instrument_status": lambda x: x.notna().sum() / len(x) * 100})
        .reset_index()
    )
    station_quality.columns = ["station_code", "status_availability"]
    station_quality = station_quality.sort_values("status_availability")

    fig_quality = px.bar(
        station_quality,
        x="status_availability",
        y="station_code",
        orientation="h",
        title="Instrument Status Availability by Station (%)",
        color="status_availability",
        color_continuous_scale="RdYlGn",
    )

    fig_quality.add_vline(x=95, line_dash="dash", line_color="red", annotation_text="95% Target")

    st.plotly_chart(fig_quality, use_container_width=True)

st.subheader("📅 Data Quality Over Time")

monthly_quality = full_df.copy()
monthly_quality["year_month"] = monthly_quality["measurement_datetime"].dt.to_period("M")

monthly_stats = (
    monthly_quality.groupby("year_month")
    .agg(
        {
            "instrument_status": lambda x: x.notna().sum() / len(x) * 100,
            "so2_value": lambda x: (x != -1).sum() / len(x) * 100,
        }
    )
    .reset_index()
)

monthly_stats["year_month_str"] = monthly_stats["year_month"].astype(str)

fig_temporal = go.Figure()

fig_temporal.add_trace(
    go.Scatter(
        x=monthly_stats["year_month_str"],
        y=monthly_stats["instrument_status"],
        mode="lines+markers",
        name="Status Available (%)",
        line=dict(color="green", width=2),
        marker=dict(size=6),
    )
)

fig_temporal.add_trace(
    go.Scatter(
        x=monthly_stats["year_month_str"],
        y=monthly_stats["so2_value"],
        mode="lines+markers",
        name="Valid SO2 Values (%)",
        line=dict(color="blue", width=2),
        marker=dict(size=6),
    )
)

fig_temporal.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="95% Target")

fig_temporal.update_layout(
    title="Data Quality Trends Over Time",
    xaxis_title="Month",
    yaxis_title="Percentage (%)",
    height=400,
    showlegend=True,
)

fig_temporal.update_xaxes(
    tickvals=monthly_stats["year_month_str"][::3].tolist(),
    ticktext=monthly_stats["year_month_str"][::3].tolist(),
    tickangle=45,
)

st.plotly_chart(fig_temporal, use_container_width=True)
