import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.styling import apply_custom_css, apply_page_config
from data import load_anomaly_predictions

apply_page_config()
apply_custom_css()

st.header("⚠️ Instrument Anomaly Detection")

anomaly_df = load_anomaly_predictions()
if anomaly_df is None:
    st.warning("No anomaly predictions found. Run `make predict` first.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    stations = sorted(anomaly_df["station_code"].unique())
    selected_station = st.selectbox("Station", stations, key="anomaly_station")
with col2:
    pollutants = anomaly_df[anomaly_df["station_code"] == selected_station]["item_name"].unique()
    selected_pollutant_name = st.selectbox("Pollutant", pollutants, key="anomaly_pollutant")

mask = (anomaly_df["station_code"] == selected_station) & (anomaly_df["item_name"] == selected_pollutant_name)
data = anomaly_df[mask].sort_values("measurement_datetime")

if data.empty:
    st.info("No predictions for this combination.")
    st.stop()

n_anomalies = data["is_anomaly"].sum()
anomaly_rate = n_anomalies / len(data) * 100

col1, col2, col3 = st.columns(3)
col1.metric("Total Hours", len(data))
col2.metric("Anomalies Detected", int(n_anomalies))
col3.metric("Anomaly Rate", f"{anomaly_rate:.1f}%")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=data["measurement_datetime"],
        y=data["anomaly_score"],
        mode="lines",
        line=dict(color="#636EFA", width=1),
        name="Anomaly Score",
    )
)

anomalies = data[data["is_anomaly"] == 1]
if len(anomalies) > 0:
    fig.add_trace(
        go.Scatter(
            x=anomalies["measurement_datetime"],
            y=anomalies["anomaly_score"],
            mode="markers",
            marker=dict(color="red", size=6, symbol="circle"),
            name="Detected Anomaly",
        )
    )

fig.update_layout(
    title=f"Anomaly Scores: Station {selected_station} / {selected_pollutant_name.upper()}",
    xaxis_title="Date",
    yaxis_title="Anomaly Probability",
    hovermode="x unified",
    height=400,
)
st.plotly_chart(fig, use_container_width=True)

if len(data) > 24:
    data = data.copy()
    data["hour"] = data["measurement_datetime"].dt.hour
    data["date"] = data["measurement_datetime"].dt.date

    pivot = data.pivot_table(index="hour", columns="date", values="anomaly_score", aggfunc="mean")

    fig2 = px.imshow(
        pivot,
        labels=dict(x="Date", y="Hour of Day", color="Anomaly Score"),
        title="Anomaly Score Heatmap (Hour x Day)",
        color_continuous_scale="RdYlGn_r",
        aspect="auto",
    )
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)

with st.expander("View raw predictions"):
    st.dataframe(
        data[["measurement_datetime", "is_anomaly", "anomaly_score"]],
        use_container_width=True,
    )
