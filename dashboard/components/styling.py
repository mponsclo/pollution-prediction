import streamlit as st

PAGE_CONFIG = {
    "page_title": "Seoul Air Quality Dashboard",
    "page_icon": "🌬️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

_CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .status-normal { color: #28a745; font-weight: bold; }
    .status-abnormal { color: #dc3545; font-weight: bold; }
    .status-missing { color: #6c757d; font-weight: bold; }
</style>
"""


def apply_page_config() -> None:
    """Configure page layout — must be the first Streamlit call on every page."""
    st.set_page_config(**PAGE_CONFIG)


def apply_custom_css() -> None:
    """Inject shared CSS. Call after apply_page_config()."""
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)
