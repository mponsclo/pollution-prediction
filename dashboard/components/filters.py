from dataclasses import dataclass

import pandas as pd
import streamlit as st

from data import create_status_color_map, get_pollutant_info, load_data


@dataclass(frozen=True)
class FilterState:
    """Filter selections applied to the full dataset, shared across pages."""

    full_df: pd.DataFrame
    filtered_df: pd.DataFrame
    selected_pollutant: str
    selected_stations: list[int]
    pollutant_info: dict
    status_colors: dict


def render_sidebar_filters() -> FilterState | None:
    """Render sidebar filter widgets and return the filtered state.

    Returns None if the current selection yields an empty dataframe —
    callers should short-circuit and surface a warning in that case.
    """
    df = load_data()
    pollutant_info = get_pollutant_info()
    status_colors = create_status_color_map()

    st.sidebar.header("🔧 Filter Controls")

    stations = sorted(df["station_code"].unique())
    selected_stations = st.sidebar.multiselect(
        "📍 Select Stations",
        options=stations,
        default=stations[:5],
        help="Choose monitoring stations to analyze",
        key="flt_stations",
    )

    min_date = df["date"].min()
    max_date = df["date"].max()
    default_end = min(min_date + pd.Timedelta(days=30), max_date)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date", value=min_date, min_value=min_date, max_value=max_date, key="flt_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date", value=default_end, min_value=min_date, max_value=max_date, key="flt_end_date"
        )

    st.sidebar.subheader("⏰ Time Filters")
    hours = st.sidebar.slider("Hours", 0, 23, (0, 23), help="Select hour range", key="flt_hours")

    pollutants = list(pollutant_info.keys())
    selected_pollutant = st.sidebar.selectbox(
        "💨 Select Pollutant",
        options=pollutants,
        format_func=lambda x: f"{pollutant_info[x]['name']} ({pollutant_info[x]['unit']})",
        help="Choose pollutant to analyze",
        key="flt_pollutant",
    )

    status_options = ["All"] + list(status_colors.keys())
    selected_status = st.sidebar.multiselect(
        "🔍 Filter by Status",
        options=status_options,
        default=["All"],
        help="Filter by instrument status (select 'All' for no filter)",
        key="flt_status",
    )

    filtered_df = df[
        (df["station_code"].isin(selected_stations))
        & (df["date"] >= start_date)
        & (df["date"] <= end_date)
        & (df["hour"] >= hours[0])
        & (df["hour"] <= hours[1])
    ].copy()

    if "All" not in selected_status and selected_status:
        filtered_df = filtered_df[filtered_df["status_label"].isin(selected_status)]

    if filtered_df.empty:
        st.warning("No data available for the selected filters. Please adjust your selection.")
        return None

    return FilterState(
        full_df=df,
        filtered_df=filtered_df,
        selected_pollutant=selected_pollutant,
        selected_stations=selected_stations,
        pollutant_info=pollutant_info,
        status_colors=status_colors,
    )
