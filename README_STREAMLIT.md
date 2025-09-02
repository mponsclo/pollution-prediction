# Seoul Air Quality Dashboard

A comprehensive Streamlit dashboard for analyzing Seoul's air quality data with full data quality visibility.

## 🌟 Features

### 📊 **Time Series Analysis**
- **Color-coded line charts** showing pollutant levels by instrument status
- **Interactive filtering** by station, date range, hour, pollutant, and status
- **Missing data visibility** - option to show/hide -1 values
- **Health threshold indicators** with red dashed lines
- **Multiple aggregation levels** - raw data, hourly average, daily average
- **Status distribution pie charts** for selected periods

### 🗺️ **Geographic Analysis** 
- **Interactive maps** with station locations and pollution levels
- **Color-coded markers** - red for above threshold, green for normal
- **Station rankings** - highest and cleanest pollution stations
- **Popup information** with detailed station statistics

### 📈 **Data Quality Overview**
- **Missing values analysis** - percentage of -1 values by pollutant
- **Status availability by station** - which stations have missing instrument status
- **Temporal quality trends** - data quality changes over time
- **95% quality target lines** for monitoring

### 📋 **Statistical Summary**
- **Comprehensive statistics** for selected pollutant and filters
- **Health analysis** - records above/below thresholds
- **Distribution histograms** with threshold and mean indicators
- **Inter-station correlations** when multiple stations selected
- **Status-based analysis** - statistics grouped by instrument status

## 🔧 **Filter Controls**

- **📍 Stations**: Multi-select station codes (204-228)
- **📅 Date Range**: Start and end date pickers
- **⏰ Time**: Hour range slider (0-23)
- **💨 Pollutant**: SO₂, NO₂, O₃, CO, PM10, PM2.5
- **🔍 Status**: Normal, Need Calibration, Abnormal, Power Cut, Under Repair, Bad Data, Missing Status

## 🎨 **Status Color Coding**

- **🟢 Normal**: Green - instrument working properly
- **🟡 Need Calibration**: Yellow - requires maintenance
- **🔴 Abnormal**: Red - instrument malfunction
- **🟣 Power Cut**: Purple - power supply issues
- **🟠 Under Repair**: Orange - maintenance in progress
- **🔴 Bad Data**: Pink - unreliable measurements
- **⚫ Missing Status**: Gray - no status information available

## 🚀 **Quick Start**

1. **Install dependencies**:
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **Run the dashboard**:
   ```bash
   streamlit run streamlit_air_quality_dashboard.py
   ```

3. **Open your browser** to `http://localhost:8501`

## 📁 **Data Requirements**

The app expects a DuckDB database at `dbt_pollution/dev.duckdb` with the `measurements_with_status` table containing:

- `measurement_datetime`: Timestamp
- `station_code`: Station identifier (204-228)  
- `latitude`, `longitude`: Station coordinates
- `so2_value`, `no2_value`, `o3_value`, `co_value`, `pm10_value`, `pm2_5_value`: Pollutant measurements
- `instrument_status`: Quality status (0-9, null for missing)

## 💡 **Key Insights Available**

- **Data Corruption Visibility**: See exactly where and when data issues occur
- **Status Impact Analysis**: Compare measurements by instrument status
- **Temporal Patterns**: Identify periods with high data quality issues
- **Spatial Patterns**: Find stations with consistent quality problems
- **Health Impact**: Monitor pollution levels against health thresholds
- **Decision Support**: Data-driven insights for data cleaning strategies

## 🔍 **Use Cases**

1. **Data Quality Assessment**: Identify patterns in missing data and instrument failures
2. **Pollution Monitoring**: Track pollutant levels across Seoul with quality context
3. **Station Performance**: Evaluate monitoring station reliability
4. **Health Analysis**: Compare pollution against health thresholds
5. **Research Support**: Export insights for further analysis and modeling

The dashboard preserves all data integrity while providing comprehensive visualization tools to understand both pollution patterns and data quality issues.