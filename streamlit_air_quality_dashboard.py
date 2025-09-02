import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import os

# Configure page
st.set_page_config(
    page_title="Seoul Air Quality Dashboard",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
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
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load data from DuckDB"""
    db_path = 'dbt_pollution/dev.duckdb'
    if not os.path.exists(db_path):
        st.error(f"Database not found at {db_path}. Please check the path.")
        st.stop()
    
    conn = duckdb.connect(db_path)
    
    # Load the complete dataset (including corrupted data)
    query = """
    SELECT 
        measurement_datetime,
        station_code,
        latitude,
        longitude,
        so2_value,
        no2_value,
        o3_value,
        co_value,
        pm10_value,
        pm2_5_value,
        instrument_status
    FROM measurements_with_status
    ORDER BY measurement_datetime, station_code
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    # Add temporal features
    df['year'] = df['measurement_datetime'].dt.year
    df['month'] = df['measurement_datetime'].dt.month
    df['day'] = df['measurement_datetime'].dt.day
    df['hour'] = df['measurement_datetime'].dt.hour
    df['date'] = df['measurement_datetime'].dt.date
    df['day_of_week'] = df['measurement_datetime'].dt.day_name()
    
    # Status labels
    df['status_label'] = df['instrument_status'].map({
        0: 'Normal',
        1: 'Need Calibration',
        2: 'Abnormal',
        4: 'Power Cut',
        8: 'Under Repair',
        9: 'Bad Data'
    })
    df['status_label'] = df['status_label'].fillna('Missing Status')
    
    return df

@st.cache_data
def get_pollutant_info():
    """Get pollutant information and thresholds"""
    return {
        'so2_value': {'name': 'SO₂', 'unit': 'ppm', 'threshold': 0.02, 'color': '#1f77b4'},
        'no2_value': {'name': 'NO₂', 'unit': 'ppm', 'threshold': 0.03, 'color': '#ff7f0e'},
        'o3_value': {'name': 'O₃', 'unit': 'ppm', 'threshold': 0.03, 'color': '#2ca02c'},
        'co_value': {'name': 'CO', 'unit': 'ppm', 'threshold': 2.0, 'color': '#d62728'},
        'pm10_value': {'name': 'PM10', 'unit': 'mg/m³', 'threshold': 30.0, 'color': '#9467bd'},
        'pm2_5_value': {'name': 'PM2.5', 'unit': 'mg/m³', 'threshold': 15.0, 'color': '#8c564b'}
    }

def create_status_color_map():
    """Create color mapping for status"""
    return {
        'Normal': '#28a745',
        'Need Calibration': '#ffc107', 
        'Abnormal': '#dc3545',
        'Power Cut': '#6f42c1',
        'Under Repair': '#fd7e14',
        'Bad Data': '#e83e8c',
        'Missing Status': '#6c757d'
    }

def main():
    # Header
    st.markdown('<h1 class="main-header">🌬️ Seoul Air Quality Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("**Interactive analysis of air quality measurements with data quality indicators**")
    
    # Load data
    with st.spinner("Loading air quality data..."):
        df = load_data()
        pollutant_info = get_pollutant_info()
        status_colors = create_status_color_map()
    
    # Sidebar filters
    st.sidebar.header("🔧 Filter Controls")
    
    # Station filter
    stations = sorted(df['station_code'].unique())
    selected_stations = st.sidebar.multiselect(
        "📍 Select Stations",
        options=stations,
        default=stations[:5],  # Default to first 5 stations
        help="Choose monitoring stations to analyze"
    )
    
    # Date range filter
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=min(min_date + pd.Timedelta(days=30), max_date),  # Default to 30 days
            min_value=min_date,
            max_value=max_date
        )
    
    # Time filters
    st.sidebar.subheader("⏰ Time Filters")
    hours = st.sidebar.slider("Hours", 0, 23, (0, 23), help="Select hour range")
    
    # Pollutant filter
    pollutants = list(pollutant_info.keys())
    selected_pollutant = st.sidebar.selectbox(
        "💨 Select Pollutant",
        options=pollutants,
        format_func=lambda x: f"{pollutant_info[x]['name']} ({pollutant_info[x]['unit']})",
        help="Choose pollutant to analyze"
    )
    
    # Status filter
    status_options = ['All'] + list(status_colors.keys())
    selected_status = st.sidebar.multiselect(
        "🔍 Filter by Status",
        options=status_options,
        default=['All'],
        help="Filter by instrument status (select 'All' for no filter)"
    )
    
    # Apply filters
    filtered_df = df[
        (df['station_code'].isin(selected_stations)) &
        (df['date'] >= start_date) &
        (df['date'] <= end_date) &
        (df['hour'] >= hours[0]) &
        (df['hour'] <= hours[1])
    ].copy()
    
    # Apply status filter
    if 'All' not in selected_status and selected_status:
        filtered_df = filtered_df[filtered_df['status_label'].isin(selected_status)]
    
    if filtered_df.empty:
        st.warning("No data available for the selected filters. Please adjust your selection.")
        return
    
    # Main dashboard layout
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Time Series Analysis", "🗺️ Geographic Analysis", "📈 Data Quality Overview", "📋 Statistical Summary"])
    
    with tab1:
        show_time_series_analysis(filtered_df, selected_pollutant, pollutant_info, status_colors)
    
    with tab2:
        show_geographic_analysis(filtered_df, selected_pollutant, pollutant_info, status_colors)
    
    with tab3:
        show_data_quality_overview(filtered_df, df, pollutant_info)
    
    with tab4:
        show_statistical_summary(filtered_df, selected_pollutant, pollutant_info)

def show_time_series_analysis(filtered_df, selected_pollutant, pollutant_info, status_colors):
    st.header("📊 Time Series Analysis")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"{pollutant_info[selected_pollutant]['name']} Levels Over Time")
    
    with col2:
        # Aggregation level
        agg_level = st.selectbox(
            "Aggregation",
            ["Raw Data", "Hourly Avg", "Daily Avg"],
            help="Choose data aggregation level"
        )
    
    with col3:
        # Show missing values toggle
        show_missing = st.checkbox("Show -1 Values", value=True, help="Display missing values (-1) in the chart")
    
    # Prepare data for plotting
    plot_df = filtered_df.copy()
    
    if not show_missing:
        plot_df = plot_df[plot_df[selected_pollutant] != -1]
    
    # Aggregation
    if agg_level == "Daily Avg":
        plot_df = plot_df.groupby(['date', 'station_code', 'status_label']).agg({
            selected_pollutant: 'mean',
            'measurement_datetime': 'first'
        }).reset_index()
    elif agg_level == "Hourly Avg":
        plot_df = plot_df.groupby(['measurement_datetime', 'station_code', 'status_label']).agg({
            selected_pollutant: 'mean'
        }).reset_index()
    
    # Create time series plot
    fig = go.Figure()
    
    # Add traces for each station and status combination
    for station in plot_df['station_code'].unique():
        station_data = plot_df[plot_df['station_code'] == station]
        
        for status in station_data['status_label'].unique():
            status_data = station_data[station_data['status_label'] == status]
            
            if len(status_data) > 0:
                fig.add_trace(go.Scatter(
                    x=status_data['measurement_datetime'] if agg_level != "Daily Avg" else pd.to_datetime(status_data['date']),
                    y=status_data[selected_pollutant],
                    mode='lines+markers',
                    name=f"Station {station} - {status}",
                    line=dict(color=status_colors[status], width=2),
                    marker=dict(size=4, color=status_colors[status]),
                    hovertemplate=f"<b>Station {station}</b><br>" +
                                f"Status: {status}<br>" +
                                f"Time: %{{x}}<br>" +
                                f"{pollutant_info[selected_pollutant]['name']}: %{{y:.4f}} {pollutant_info[selected_pollutant]['unit']}<br>" +
                                "<extra></extra>"
                ))
    
    # Add threshold line
    threshold = pollutant_info[selected_pollutant]['threshold']
    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Health Threshold ({threshold} {pollutant_info[selected_pollutant]['unit']})",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title=f"{pollutant_info[selected_pollutant]['name']} Concentration with Status Information",
        xaxis_title="Time",
        yaxis_title=f"Concentration ({pollutant_info[selected_pollutant]['unit']})",
        height=600,
        showlegend=True,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Status distribution over time
    st.subheader("📊 Status Distribution Over Selected Period")
    
    status_dist = filtered_df.groupby(['status_label']).size().reset_index(name='count')
    status_dist['percentage'] = (status_dist['count'] / status_dist['count'].sum() * 100).round(2)
    
    fig_status = px.pie(
        status_dist,
        values='count',
        names='status_label',
        color='status_label',
        color_discrete_map=status_colors,
        title="Distribution of Instrument Status"
    )
    
    fig_status.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_status, use_container_width=True)
    
    # Show data summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_records = len(filtered_df)
        st.metric("Total Records", f"{total_records:,}")
    
    with col2:
        missing_values = (filtered_df[selected_pollutant] == -1).sum()
        st.metric("Missing Values (-1)", f"{missing_values:,}", delta=f"{missing_values/total_records*100:.1f}%")
    
    with col3:
        normal_status = (filtered_df['status_label'] == 'Normal').sum()
        st.metric("Normal Status", f"{normal_status:,}", delta=f"{normal_status/total_records*100:.1f}%")
    
    with col4:
        missing_status = (filtered_df['status_label'] == 'Missing Status').sum()
        st.metric("Missing Status", f"{missing_status:,}", delta=f"{missing_status/total_records*100:.1f}%")

def show_geographic_analysis(filtered_df, selected_pollutant, pollutant_info, status_colors):
    st.header("🗺️ Geographic Analysis")
    
    # Create station-level aggregations
    station_agg = filtered_df.groupby(['station_code', 'latitude', 'longitude']).agg({
        selected_pollutant: ['mean', 'count'],
        'status_label': lambda x: x.mode().iloc[0] if not x.empty else 'Unknown'
    }).reset_index()
    
    # Flatten column names
    station_agg.columns = ['station_code', 'latitude', 'longitude', 'avg_value', 'record_count', 'dominant_status']
    
    # Remove stations with only -1 values
    station_agg = station_agg[station_agg['avg_value'] != -1]
    
    if station_agg.empty:
        st.warning("No valid data available for mapping.")
        return
    
    # Create map
    center_lat = station_agg['latitude'].mean()
    center_lon = station_agg['longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11)
    
    # Add markers for each station
    for _, row in station_agg.iterrows():
        color = 'red' if row['avg_value'] > pollutant_info[selected_pollutant]['threshold'] else 'green'
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=10 + (row['avg_value'] / station_agg['avg_value'].max() * 20),
            popup=f"""
            <b>Station {row['station_code']}</b><br>
            Average {pollutant_info[selected_pollutant]['name']}: {row['avg_value']:.4f} {pollutant_info[selected_pollutant]['unit']}<br>
            Records: {row['record_count']}<br>
            Dominant Status: {row['dominant_status']}
            """,
            color=color,
            weight=2,
            fillColor=color,
            fillOpacity=0.6
        ).add_to(m)
    
    # Display map
    st.subheader(f"Station Locations - {pollutant_info[selected_pollutant]['name']} Levels")
    st_folium(m, width=700, height=500)
    
    # Station ranking
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏭 Highest Pollution Stations")
        top_stations = station_agg.nlargest(5, 'avg_value')[['station_code', 'avg_value', 'dominant_status']]
        top_stations['avg_value'] = top_stations['avg_value'].round(4)
        st.dataframe(top_stations, hide_index=True)
    
    with col2:
        st.subheader("✨ Cleanest Stations")
        clean_stations = station_agg.nsmallest(5, 'avg_value')[['station_code', 'avg_value', 'dominant_status']]
        clean_stations['avg_value'] = clean_stations['avg_value'].round(4)
        st.dataframe(clean_stations, hide_index=True)

def show_data_quality_overview(filtered_df, full_df, pollutant_info):
    st.header("📈 Data Quality Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Missing Values by Pollutant (-1 values)")
        
        pollutant_cols = list(pollutant_info.keys())
        missing_data = []
        
        for col in pollutant_cols:
            missing_count = (full_df[col] == -1).sum()
            missing_pct = (missing_count / len(full_df)) * 100
            missing_data.append({
                'Pollutant': pollutant_info[col]['name'],
                'Missing Count': missing_count,
                'Missing %': missing_pct
            })
        
        missing_df = pd.DataFrame(missing_data)
        
        fig_missing = px.bar(
            missing_df,
            x='Pollutant',
            y='Missing %',
            title="Percentage of Missing Values by Pollutant",
            color='Missing %',
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig_missing, use_container_width=True)
    
    with col2:
        st.subheader("Status Availability by Station")
        
        station_quality = full_df.groupby('station_code').agg({
            'instrument_status': lambda x: x.notna().sum() / len(x) * 100
        }).reset_index()
        station_quality.columns = ['station_code', 'status_availability']
        station_quality = station_quality.sort_values('status_availability')
        
        fig_quality = px.bar(
            station_quality,
            x='status_availability',
            y='station_code',
            orientation='h',
            title="Instrument Status Availability by Station (%)",
            color='status_availability',
            color_continuous_scale='RdYlGn'
        )
        
        fig_quality.add_vline(x=95, line_dash="dash", line_color="red", 
                             annotation_text="95% Target")
        
        st.plotly_chart(fig_quality, use_container_width=True)
    
    # Temporal quality patterns
    st.subheader("📅 Data Quality Over Time")
    
    # Monthly quality trends
    monthly_quality = full_df.copy()
    monthly_quality['year_month'] = monthly_quality['measurement_datetime'].dt.to_period('M')
    
    monthly_stats = monthly_quality.groupby('year_month').agg({
        'instrument_status': lambda x: x.notna().sum() / len(x) * 100,
        'so2_value': lambda x: (x != -1).sum() / len(x) * 100
    }).reset_index()
    
    monthly_stats['year_month_str'] = monthly_stats['year_month'].astype(str)
    
    fig_temporal = go.Figure()
    
    fig_temporal.add_trace(go.Scatter(
        x=monthly_stats['year_month_str'],
        y=monthly_stats['instrument_status'],
        mode='lines+markers',
        name='Status Available (%)',
        line=dict(color='green', width=2),
        marker=dict(size=6)
    ))
    
    fig_temporal.add_trace(go.Scatter(
        x=monthly_stats['year_month_str'],
        y=monthly_stats['so2_value'],
        mode='lines+markers', 
        name='Valid SO2 Values (%)',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))
    
    fig_temporal.add_hline(y=95, line_dash="dash", line_color="red",
                          annotation_text="95% Target")
    
    fig_temporal.update_layout(
        title="Data Quality Trends Over Time",
        xaxis_title="Month",
        yaxis_title="Percentage (%)",
        height=400,
        showlegend=True
    )
    
    # Show every 3rd month to avoid crowding
    fig_temporal.update_xaxes(
        tickvals=monthly_stats['year_month_str'][::3].tolist(),
        ticktext=monthly_stats['year_month_str'][::3].tolist(),
        tickangle=45
    )
    
    st.plotly_chart(fig_temporal, use_container_width=True)

def show_statistical_summary(filtered_df, selected_pollutant, pollutant_info):
    st.header("📋 Statistical Summary")
    
    # Clean data (no -1 values, has status)
    clean_data = filtered_df[
        (filtered_df[selected_pollutant] != -1) &
        (filtered_df['instrument_status'].notna())
    ]
    
    if clean_data.empty:
        st.warning("No clean data available for statistical analysis.")
        return
    
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
        
        threshold = pollutant_info[selected_pollutant]['threshold']
        above_threshold = (clean_data[selected_pollutant] > threshold).sum()
        total_records = len(clean_data)
        
        st.metric("Health Threshold", f"{threshold} {pollutant_info[selected_pollutant]['unit']}")
        st.metric("Above Threshold", f"{above_threshold:,}", 
                 delta=f"{above_threshold/total_records*100:.1f}%")
        
        # Percentiles
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
            color_discrete_sequence=['skyblue']
        )
        
        fig_hist.add_vline(x=threshold, line_dash="dash", line_color="red",
                          annotation_text="Health Threshold")
        fig_hist.add_vline(x=clean_data[selected_pollutant].mean(), 
                          line_dash="dash", line_color="green",
                          annotation_text="Mean")
        
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Correlation analysis if multiple stations selected
    stations_in_data = clean_data['station_code'].nunique()
    if stations_in_data > 1:
        st.subheader("🔗 Inter-Station Correlation")
        
        # Pivot data for correlation
        correlation_data = clean_data.pivot_table(
            index='measurement_datetime',
            columns='station_code', 
            values=selected_pollutant,
            aggfunc='mean'
        )
        
        if correlation_data.shape[1] > 1:
            corr_matrix = correlation_data.corr()
            
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                title=f"{pollutant_info[selected_pollutant]['name']} Correlation Between Stations",
                color_continuous_scale='RdBu_r'
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
    
    # Status-based analysis
    st.subheader("🔍 Analysis by Instrument Status")
    
    status_stats = clean_data.groupby('status_label')[selected_pollutant].agg([
        'count', 'mean', 'std', 'min', 'max'
    ]).round(4)
    
    status_stats.columns = ['Count', 'Mean', 'Std Dev', 'Min', 'Max']
    st.dataframe(status_stats)

if __name__ == "__main__":
    main()

# First show the aggregate of the stations. Otherwise if we show all the stations everything is convoluted.
# Do not use pie charts for the status distribution. Use a bar chart.
# Don't join the data points for not normal measurements as joining them clutters the visualizations. Just show the data points so they are visual.
# Use the health threshold from pollutants info
# Plot different pollutants at the same time to check correlations
# Show better the seasonality (Take the whole month of December as part of winter, March as spring, and so on.)