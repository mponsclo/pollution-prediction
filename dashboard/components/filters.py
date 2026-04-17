from dataclasses import dataclass

import pandas as pd
import streamlit as st

from data import create_status_color_map, get_pollutant_info, load_data

CENTRAL_STATIONS = [212, 214, 216]


@dataclass(frozen=True)
class FilterState:
    """Filter selections applied to the full dataset, shared across pages.

    `filtered_df` is filtered by date/hour/status only — stations are picked
    inline per page via `render_stations_selector`.
    """

    full_df: pd.DataFrame
    filtered_df: pd.DataFrame
    pollutant_info: dict
    status_colors: dict


def render_pollutant_selector(pollutant_info: dict, key: str = "flt_pollutant", label: str = "💨 Pollutant") -> str:
    """Inline pollutant selectbox. Call at the top of any page that needs a pollutant pick."""
    pollutants = list(pollutant_info.keys())
    return st.selectbox(
        label,
        options=pollutants,
        format_func=lambda x: f"{pollutant_info[x]['name']} ({pollutant_info[x]['unit']})",
        key=key,
    )


def render_stations_selector(
    all_stations: list[int],
    key: str = "flt_stations",
    label: str = "📍 Stations",
) -> list[int]:
    """Inline stations multiselect. Call at the top of any page that needs a station pick."""
    defaults = [s for s in CENTRAL_STATIONS if s in all_stations] or all_stations[:3]
    return st.multiselect(
        label,
        options=all_stations,
        default=defaults,
        help="Choose monitoring stations to analyze",
        key=key,
    )


def render_sidebar_filters() -> FilterState | None:
    """Render sidebar filter widgets and return the filtered state.

    Returns None if the current selection yields an empty dataframe —
    callers should short-circuit and surface a warning in that case.
    """
    df = load_data()
    pollutant_info = get_pollutant_info()
    status_colors = create_status_color_map()

    st.sidebar.header("🔧 Filter Controls")

    min_date = df["date"].min()
    max_date = df["date"].max()
    default_start = max(min_date, max_date - pd.Timedelta(days=30))

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date", value=default_start, min_value=min_date, max_value=max_date, key="flt_start_date"
        )
    with col2:
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key="flt_end_date")

    st.sidebar.subheader("⏰ Time Filters")
    hours = st.sidebar.slider("Hours", 0, 23, (0, 23), help="Select hour range", key="flt_hours")

    status_options = ["All"] + list(status_colors.keys())
    selected_status = st.sidebar.multiselect(
        "🔍 Filter by Status",
        options=status_options,
        default=["All"],
        help="Filter by instrument status (select 'All' for no filter)",
        key="flt_status",
    )

    filtered_df = df[
        (df["date"] >= start_date) & (df["date"] <= end_date) & (df["hour"] >= hours[0]) & (df["hour"] <= hours[1])
    ].copy()

    if "All" not in selected_status and selected_status:
        filtered_df = filtered_df[filtered_df["status_label"].isin(selected_status)]

    if filtered_df.empty:
        st.warning("No data available for the selected filters. Please adjust your selection.")
        return None

    return FilterState(
        full_df=df,
        filtered_df=filtered_df,
        pollutant_info=pollutant_info,
        status_colors=status_colors,
    )
