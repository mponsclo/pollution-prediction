import pandas as pd
import plotly.colors as pc
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.filters import render_pollutant_selector, render_sidebar_filters, render_stations_selector
from components.styling import apply_custom_css, apply_page_config

apply_page_config()
apply_custom_css()

state = render_sidebar_filters()
if state is None:
    st.stop()

pollutant_info = state.pollutant_info
status_colors = state.status_colors
all_stations = sorted(state.full_df["station_code"].unique())

st.header("📊 Time Series Analysis")

top1, top2, top3, top4 = st.columns([2, 1, 1, 1])

with top1:
    selected_stations = render_stations_selector(all_stations)

with top2:
    selected_pollutant = render_pollutant_selector(pollutant_info)

with top3:
    agg_level = st.selectbox(
        "Aggregation",
        ["Daily Avg", "Hourly Avg", "Raw Data"],
        help="Choose data aggregation level",
    )

with top4:
    show_missing = st.checkbox("Show -1 Values", value=True, help="Display missing values (-1) in the chart")

filtered_df = state.filtered_df[state.filtered_df["station_code"].isin(selected_stations)]
if filtered_df.empty:
    st.warning("No data for the selected stations. Pick at least one.")
    st.stop()

st.subheader(f"{pollutant_info[selected_pollutant]['name']} Levels Over Time")

plot_df = filtered_df.copy()

if not show_missing:
    plot_df = plot_df[plot_df[selected_pollutant] != -1]


def _mode(s: pd.Series) -> str:
    m = s.mode()
    return m.iloc[0] if not m.empty else "Normal"


if agg_level == "Daily Avg":
    plot_df = (
        plot_df.groupby(["date", "station_code"])
        .agg(
            **{
                selected_pollutant: (selected_pollutant, "mean"),
                "measurement_datetime": ("measurement_datetime", "first"),
                "status_label": ("status_label", _mode),
            }
        )
        .reset_index()
    )
elif agg_level == "Hourly Avg":
    plot_df = (
        plot_df.groupby(["measurement_datetime", "station_code"])
        .agg(
            **{
                selected_pollutant: (selected_pollutant, "mean"),
                "status_label": ("status_label", _mode),
            }
        )
        .reset_index()
    )

valid_values = plot_df[plot_df[selected_pollutant] > 0][selected_pollutant].dropna()
y_max = None
if len(valid_values) > 20:
    y_max = valid_values.quantile(0.99) * 1.2

fig = go.Figure()

stations_in_plot = sorted(plot_df["station_code"].unique())
station_palette = pc.qualitative.Set2 + pc.qualitative.Set3
station_colors = {s: station_palette[i % len(station_palette)] for i, s in enumerate(stations_in_plot)}

x_col = "measurement_datetime" if agg_level != "Daily Avg" else "date"
unit = pollutant_info[selected_pollutant]["unit"]
name = pollutant_info[selected_pollutant]["name"]

for station in stations_in_plot:
    station_data = plot_df[plot_df["station_code"] == station].sort_values(x_col)
    if station_data.empty:
        continue

    x_values = pd.to_datetime(station_data[x_col])
    marker_colors = station_data["status_label"].map(status_colors).fillna("#888").tolist()

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=station_data[selected_pollutant],
            mode="lines+markers",
            name=f"Station {station}",
            line=dict(color=station_colors[station], width=1.5),
            marker=dict(size=5, color=marker_colors, line=dict(width=0)),
            customdata=station_data["status_label"],
            hovertemplate=f"<b>Station {station}</b><br>"
            + "Status: %{customdata}<br>"
            + "Time: %{x}<br>"
            + f"{name}: %{{y:.4f}} {unit}<br>"
            + "<extra></extra>",
        )
    )

for status, color in status_colors.items():
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=8, color=color),
            name=status,
            legendgroup="status",
            legendgrouptitle_text="Marker = Status",
            showlegend=True,
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
    yaxis_range=[0, y_max] if y_max is not None else None,
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
