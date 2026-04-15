import plotly.graph_objects as go
import streamlit as st

from components.styling import apply_custom_css, apply_page_config
from data import load_forecast_predictions

apply_page_config()
apply_custom_css()

st.header("🔮 Hourly Pollutant Forecasts")

forecast_df = load_forecast_predictions()
if forecast_df is None:
    st.warning("No forecast predictions found. Run `make predict` first.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    stations = sorted(forecast_df["station_code"].unique())
    selected_station = st.selectbox("Station", stations, key="forecast_station")
with col2:
    pollutants = forecast_df[forecast_df["station_code"] == selected_station]["item_name"].unique()
    selected_pollutant_name = st.selectbox("Pollutant", pollutants, key="forecast_pollutant")

mask = (forecast_df["station_code"] == selected_station) & (forecast_df["item_name"] == selected_pollutant_name)
data = forecast_df[mask].sort_values("measurement_datetime")

if data.empty:
    st.info("No predictions for this combination.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Prediction Hours", len(data))
col2.metric("Mean Value", f"{data['predicted_value'].mean():.5f}")
col3.metric("Min Value", f"{data['predicted_value'].min():.5f}")
col4.metric("Max Value", f"{data['predicted_value'].max():.5f}")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=data["measurement_datetime"],
        y=data["predicted_upper_90"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        name="Upper 90%",
    )
)
fig.add_trace(
    go.Scatter(
        x=data["measurement_datetime"],
        y=data["predicted_lower_90"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(31, 119, 180, 0.2)",
        name="90% Prediction Interval",
    )
)

fig.add_trace(
    go.Scatter(
        x=data["measurement_datetime"],
        y=data["predicted_value"],
        mode="lines",
        line=dict(color="#1f77b4", width=1.5),
        name="Ensemble Prediction",
    )
)

fig.update_layout(
    title=f"Forecast: Station {selected_station} / {selected_pollutant_name.upper()}",
    xaxis_title="Date",
    yaxis_title="Concentration",
    hovermode="x unified",
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

data = data.copy()
data["interval_width"] = data["predicted_upper_90"] - data["predicted_lower_90"]
st.metric("Avg 90% Interval Width", f"{data['interval_width'].mean():.5f}")

with st.expander("View raw predictions"):
    st.dataframe(
        data[["measurement_datetime", "predicted_value", "predicted_lower_90", "predicted_upper_90"]],
        use_container_width=True,
    )
