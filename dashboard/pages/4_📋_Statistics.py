import plotly.express as px
import streamlit as st

from components.filters import render_pollutant_selector, render_sidebar_filters, render_stations_selector
from components.styling import apply_custom_css, apply_page_config

apply_page_config()
apply_custom_css()

state = render_sidebar_filters()
if state is None:
    st.stop()

pollutant_info = state.pollutant_info
all_stations = sorted(state.full_df["station_code"].unique())

st.header("📋 Statistical Summary")

top1, top2 = st.columns([2, 1])
with top1:
    selected_stations = render_stations_selector(all_stations)
with top2:
    selected_pollutant = render_pollutant_selector(pollutant_info)

filtered_df = state.filtered_df[state.filtered_df["station_code"].isin(selected_stations)]
if filtered_df.empty:
    st.warning("No data for the selected stations. Pick at least one.")
    st.stop()

clean_data = filtered_df[(filtered_df[selected_pollutant] != -1) & (filtered_df["instrument_status"].notna())]

if clean_data.empty:
    st.warning("No clean data available for statistical analysis.")
    st.stop()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 Basic Statistics")

    stats = clean_data[selected_pollutant].describe()

    st.metric("Count", f"{stats['count']:.0f}")
    st.metric("Mean", f"{stats['mean']:.4f}")
    st.metric("Median", f"{stats['50%']:.4f}")
    st.metric("Std Dev", f"{stats['std']:.4f}")
    st.metric("Min", f"{stats['min']:.4f}")
    st.metric("Max", f"{stats['max']:.4f}")

with col2:
    st.subheader("🎯 Health Analysis")

    threshold = pollutant_info[selected_pollutant]["threshold"]
    above_threshold = (clean_data[selected_pollutant] > threshold).sum()
    total_records = len(clean_data)

    st.metric("Health Threshold", f"{threshold} {pollutant_info[selected_pollutant]['unit']}")
    st.metric("Above Threshold", f"{above_threshold:,}", delta=f"{above_threshold / total_records * 100:.1f}%")

    percentiles = clean_data[selected_pollutant].quantile([0.75, 0.9, 0.95, 0.99])
    st.metric("75th Percentile", f"{percentiles[0.75]:.4f}")
    st.metric("90th Percentile", f"{percentiles[0.9]:.4f}")
    st.metric("95th Percentile", f"{percentiles[0.95]:.4f}")
    st.metric("99th Percentile", f"{percentiles[0.99]:.4f}")

with col3:
    st.subheader("📈 Distribution")

    fig_hist = px.histogram(
        clean_data,
        x=selected_pollutant,
        nbins=50,
        title=f"{pollutant_info[selected_pollutant]['name']} Distribution",
        color_discrete_sequence=["skyblue"],
    )

    mean_value = clean_data[selected_pollutant].mean()
    fig_hist.add_vline(
        x=threshold,
        line_dash="dash",
        line_color="#ef4444",
        line_width=2,
        annotation_text="Health Threshold",
        annotation_position="top right",
        annotation_font_color="#ef4444",
    )
    fig_hist.add_vline(
        x=mean_value,
        line_dash="dash",
        line_color="#f59e0b",
        line_width=2.5,
        annotation_text=f"Mean ({mean_value:.4f})",
        annotation_position="top left",
        annotation_font_color="#f59e0b",
    )

    fig_hist.update_layout(height=400)
    st.plotly_chart(fig_hist, use_container_width=True)

stations_in_data = clean_data["station_code"].nunique()
if stations_in_data > 1:
    st.subheader("🔗 Inter-Station Correlation")

    correlation_data = clean_data.pivot_table(
        index="measurement_datetime", columns="station_code", values=selected_pollutant, aggfunc="mean"
    )

    if correlation_data.shape[1] > 1:
        corr_matrix = correlation_data.corr()

        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title=f"{pollutant_info[selected_pollutant]['name']} Correlation Between Stations",
            color_continuous_scale="RdBu_r",
        )

        st.plotly_chart(fig_corr, use_container_width=True)

st.subheader("🔍 Analysis by Instrument Status")

status_stats = (
    clean_data.groupby("status_label")[selected_pollutant].agg(["count", "mean", "std", "min", "max"]).round(4)
)

status_stats.columns = ["Count", "Mean", "Std Dev", "Min", "Max"]
st.dataframe(status_stats)
