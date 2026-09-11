"""
=============================================================================
🚍 PUBLIC TRANSPORT ANALYTICS DASHBOARD
=============================================================================
A comprehensive Data Science Web Application built using Python, Streamlit,
Pandas, NumPy, and Plotly for analyzing public transit operations.

Author: TY BSc Data Science Student Project
Target Platform: Streamlit & GitHub (kshitijavichare2611@gmail.com)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import os

# ---------------------------------------------------------------------------
# 1. APPLICATION CONFIGURATION & THEME
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Public Transport Analytics Dashboard",
    page_icon="🚍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, student-friendly aesthetics
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 16px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .kpi-subtext {
        font-size: 0.78rem;
        color: #94A3B8;
        margin-top: 2px;
    }
    .insight-badge {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 0.95rem;
        color: #1E40AF;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 2. DATA INGESTION & FLEXIBLE COLUMN DETECTION
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(file_source=None):
    """
    Loads dataset from an uploaded file or the default sample dataset.
    Returns:
        pd.DataFrame or None: Loaded raw DataFrame.
    """
    if file_source is not None:
        try:
            if hasattr(file_source, 'name') and file_source.name.endswith('.xlsx'):
                return pd.read_excel(file_source)
            else:
                return pd.read_csv(file_source)
        except Exception as e:
            st.error(f"Error loading uploaded file: {e}")
            return None
    
    # Default fallback to sample data
    sample_path = os.path.join(os.path.dirname(__file__), "data", "public_transport_data.csv")
    if os.path.exists(sample_path):
        return pd.read_csv(sample_path)
    
    # If not found relative to __file__, check current working directory
    cwd_path = os.path.join("data", "public_transport_data.csv")
    if os.path.exists(cwd_path):
        return pd.read_csv(cwd_path)
        
    return None


def detect_columns(df: pd.DataFrame) -> dict:
    """
    Dynamically maps available DataFrame columns to standardized concepts.
    This ensures the app adapts gracefully to any transit dataset without crashing.
    """
    col_map = {
        "date": None,
        "time": None,
        "route": None,
        "route_id": None,
        "vehicle_id": None,
        "transport_type": None,
        "passenger_count": None,
        "ticket_price": None,
        "revenue": None,
        "delay_minutes": None,
        "travel_time": None,
        "distance": None,
        "source": None,
        "destination": None,
        "capacity": None,
        "status": None
    }

    # Normalized column search dictionary (lowercase stripped)
    cols_lower = {str(c).strip().lower(): c for c in df.columns}

    # Synonyms / variations for each attribute
    synonyms = {
        "date": ["date", "trip_date", "travel_date", "journey_date", "day", "service_date", "timestamp"],
        "time": ["time", "trip_time", "departure_time", "start_time", "schedule_time", "hour"],
        "route": ["route_name", "route", "line_name", "corridor", "route_title", "line"],
        "route_id": ["route_id", "route_no", "routeno", "line_id", "route_code", "route_num"],
        "vehicle_id": ["vehicle_id", "bus_no", "train_no", "vehicle_num", "coach_no", "fleet_id", "vehicle"],
        "transport_type": ["transport_type", "vehicle_type", "transit_type", "mode", "transport_mode", "type"],
        "passenger_count": ["passenger_count", "passengers", "ridership", "travellers", "boardings", "pax", "count"],
        "ticket_price": ["ticket_price", "fare", "price", "ticket_fare", "avg_fare", "rate", "cost"],
        "revenue": ["revenue", "total_fare", "earnings", "collection", "fare_collected", "total_revenue"],
        "delay_minutes": ["delay_minutes", "delay", "delay_min", "delay_mins", "punctuality_delay", "late_minutes", "late_mins"],
        "travel_time": ["travel_time_mins", "travel_time", "duration", "duration_mins", "trip_duration", "duration_minutes"],
        "distance": ["distance_km", "distance", "distance_miles", "length_km", "kms", "route_length"],
        "source": ["source_stop", "source", "origin", "start_station", "from_station", "from_stop", "from"],
        "destination": ["destination_stop", "destination", "dest", "end_station", "to_station", "to_stop", "to"],
        "capacity": ["vehicle_capacity", "capacity", "seats", "total_seats", "max_capacity"],
        "status": ["status", "trip_status", "punctuality_status", "schedule_status"]
    }

    for concept, keywords in synonyms.items():
        for kw in keywords:
            if kw in cols_lower:
                col_map[concept] = cols_lower[kw]
                break

    # If route_name was missing but route_id was found, use route_id for route
    if col_map["route"] is None and col_map["route_id"] is not None:
        col_map["route"] = col_map["route_id"]

    return col_map


# ---------------------------------------------------------------------------
# 3. DATA PREPROCESSING PIPELINE
# ---------------------------------------------------------------------------
def preprocess_data(raw_df: pd.DataFrame, col_map: dict):
    """
    Cleans and standardizes the transit data:
    1. Removes duplicates
    2. Strips whitespace from column names and string values
    3. Handles missing values appropriately (numerical vs categorical)
    4. Converts dates and times to datetime types
    5. Extracts temporal helper features (hour, day of week, month)
    6. Sanitizes unrealistic values (negative passengers, impossible delays)
    7. Computes calculated revenue if missing but passenger & price exist

    Returns:
        cleaned_df (pd.DataFrame): The preprocessed dataset.
        audit_info (dict): Before/after statistics for student explanation.
    """
    initial_rows = len(raw_df)
    initial_cols = len(raw_df.columns)
    initial_nulls = int(raw_df.isnull().sum().sum())

    df = raw_df.copy()

    # 1. Clean column names
    df.columns = [str(col).strip() for col in df.columns]

    # 2. Remove duplicate rows
    duplicates_removed = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)

    # 3. Process Date Column
    date_col = col_map["date"]
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        # Drop rows where date failed to parse
        df = df.dropna(subset=[date_col]).reset_index(drop=True)
        # Helper date fields
        df["_extracted_date"] = df[date_col].dt.date
        df["_day_name"] = df[date_col].dt.day_name()
        df["_month_name"] = df[date_col].dt.month_name()
        df["_year_month"] = df[date_col].dt.to_period('M').astype(str)
        df["_is_weekend"] = df[date_col].dt.weekday >= 5
    else:
        df["_extracted_date"] = None
        df["_day_name"] = None
        df["_month_name"] = None
        df["_year_month"] = None
        df["_is_weekend"] = None

    # 4. Process Time Column & Extract Hour
    time_col = col_map["time"]
    if time_col and time_col in df.columns:
        # If time is a string like "08:30:00", extract the hour
        time_series = df[time_col].astype(str).str.strip()
        extracted_hours = []
        for val in time_series:
            try:
                # Try parsing as HH:MM or HH:MM:SS
                parts = val.split(':')
                hr = int(parts[0])
                if 0 <= hr <= 23:
                    extracted_hours.append(hr)
                else:
                    extracted_hours.append(np.nan)
            except Exception:
                extracted_hours.append(np.nan)
        df["_hour"] = extracted_hours
        df["_hour"] = df["_hour"].fillna(df["_hour"].median() if not df["_hour"].isna().all() else 12).astype(int)
    elif date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df["_hour"] = df[date_col].dt.hour
    else:
        df["_hour"] = None

    # 5. Handle Numerical Columns (Passengers, Price, Delays, Travel Time)
    num_clean_specs = [
        ("passenger_count", 0, 5000),
        ("ticket_price", 0.0, 10000.0),
        ("delay_minutes", -30, 480),
        ("travel_time", 1, 1440),
        ("distance", 0.1, 2000.0),
        ("capacity", 1, 5000)
    ]

    for concept, min_val, max_val in num_clean_specs:
        col_name = col_map[concept]
        if col_name and col_name in df.columns:
            # Force numeric conversion
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            # Impute missing values with median or min_val
            median_val = df[col_name].median()
            impute_val = median_val if pd.notnull(median_val) else min_val
            df[col_name] = df[col_name].fillna(impute_val)
            # Clip unrealistic values
            df[col_name] = df[col_name].clip(lower=min_val, upper=max_val)

    # 6. Revenue Calculation / Handling
    rev_col = col_map["revenue"]
    pax_col = col_map["passenger_count"]
    price_col = col_map["ticket_price"]

    if rev_col and rev_col in df.columns:
        df[rev_col] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0.0)
        df[rev_col] = df[rev_col].clip(lower=0.0)
    elif pax_col and price_col and pax_col in df.columns and price_col in df.columns:
        # Calculate estimated revenue: Passenger Count * Ticket Price
        df["calculated_revenue"] = df[pax_col] * df[price_col]
        col_map["revenue"] = "calculated_revenue"

    # 7. Vehicle Utilization Calculation if Capacity is available
    cap_col = col_map["capacity"]
    if pax_col and cap_col and pax_col in df.columns and cap_col in df.columns:
        df["_utilization_rate"] = np.where(
            df[cap_col] > 0,
            (df[pax_col] / df[cap_col]) * 100.0,
            np.nan
        )
        df["_utilization_rate"] = df["_utilization_rate"].clip(lower=0.0, upper=150.0)
    else:
        df["_utilization_rate"] = None

    # 8. Clean Categorical Columns
    cat_concepts = ["route", "route_id", "transport_type", "vehicle_id", "source", "destination", "status"]
    for concept in cat_concepts:
        col_name = col_map[concept]
        if col_name and col_name in df.columns:
            df[col_name] = df[col_name].astype(str).str.strip()
            df[col_name] = df[col_name].replace({"nan": "Unknown", "None": "Unknown", "": "Unknown"})

    final_rows = len(df)
    final_cols = len(df.columns)
    final_nulls = int(df.isnull().sum().sum())

    audit_info = {
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "initial_cols": initial_cols,
        "final_cols": final_cols,
        "duplicates_removed": duplicates_removed,
        "initial_nulls": initial_nulls,
        "final_nulls": final_nulls,
        "date_range": (
            f"{df['_extracted_date'].min()} to {df['_extracted_date'].max()}"
            if df["_extracted_date"] is not None and pd.notnull(df["_extracted_date"].min())
            else "Not Available"
        )
    }

    return df, audit_info


# ---------------------------------------------------------------------------
# 4. KPI COMPUTATION
# ---------------------------------------------------------------------------
def calculate_kpis(df: pd.DataFrame, col_map: dict) -> dict:
    """
    Computes key performance metrics dynamically based on available columns.
    Only computes valid statistics from the actual data without hardcoding.
    """
    kpis = {
        "total_passengers": 0,
        "total_trips": len(df),
        "total_revenue": 0.0,
        "avg_passengers_trip": 0.0,
        "avg_delay": None,
        "total_routes": 0,
        "total_vehicles": 0,
        "avg_utilization": None,
        "on_time_pct": None
    }

    # Total Passengers
    pax_col = col_map["passenger_count"]
    if pax_col and pax_col in df.columns:
        kpis["total_passengers"] = int(df[pax_col].sum())
        kpis["avg_passengers_trip"] = round(df[pax_col].mean(), 1) if len(df) > 0 else 0.0

    # Total Revenue
    rev_col = col_map["revenue"]
    if rev_col and rev_col in df.columns:
        kpis["total_revenue"] = float(df[rev_col].sum())

    # Average Delay
    delay_col = col_map["delay_minutes"]
    if delay_col and delay_col in df.columns:
        kpis["avg_delay"] = round(float(df[delay_col].mean()), 1)
        # On-time percentage (delay <= 3 minutes)
        on_time_trips = (df[delay_col] <= 3).sum()
        kpis["on_time_pct"] = round((on_time_trips / len(df)) * 100.0, 1) if len(df) > 0 else 0.0

    # Routes & Vehicles
    route_col = col_map["route"]
    if route_col and route_col in df.columns:
        kpis["total_routes"] = int(df[route_col].nunique())

    veh_col = col_map["vehicle_id"]
    if veh_col and veh_col in df.columns:
        kpis["total_vehicles"] = int(df[veh_col].nunique())

    if "_utilization_rate" in df.columns and df["_utilization_rate"] is not None and not df["_utilization_rate"].isna().all():
        kpis["avg_utilization"] = round(float(df["_utilization_rate"].mean()), 1)

    return kpis


# ---------------------------------------------------------------------------
# 5. AUTOMATED INSIGHT GENERATOR
# ---------------------------------------------------------------------------
def generate_insights(df: pd.DataFrame, col_map: dict) -> list:
    """
    Generates data-driven executive summary insights based purely on current data.
    """
    insights = []
    
    if len(df) == 0:
        return ["No records available under the selected filters to generate insights."]

    pax_col = col_map["passenger_count"]
    route_col = col_map["route"]
    rev_col = col_map["revenue"]
    delay_col = col_map["delay_minutes"]
    type_col = col_map["transport_type"]

    # 1. Route demand insight
    if pax_col and route_col and route_col in df.columns and pax_col in df.columns:
        route_pax = df.groupby(route_col)[pax_col].sum()
        if not route_pax.empty:
            top_route = route_pax.idxmax()
            top_pax = int(route_pax.max())
            pct_share = round((top_pax / df[pax_col].sum()) * 100, 1) if df[pax_col].sum() > 0 else 0
            insights.append(f"🏆 **Highest Passenger Demand**: Route **'{top_route}'** leads ridership with **{top_pax:,}** passengers ({pct_share}% of total ridership).")

    # 2. Peak hour insight
    if "_hour" in df.columns and df["_hour"] is not None and pax_col and pax_col in df.columns:
        hourly_pax = df.groupby("_hour")[pax_col].sum()
        if not hourly_pax.empty:
            peak_hr = hourly_pax.idxmax()
            peak_val = int(hourly_pax.max())
            am_pm = "AM" if peak_hr < 12 else "PM"
            display_hr = peak_hr if peak_hr <= 12 else peak_hr - 12
            if display_hr == 0: display_hr = 12
            insights.append(f"⏰ **Peak Commute Window**: Maximum passenger rush occurs at **{display_hr}:00 {am_pm}** ({peak_val:,} passengers).")

    # 3. Day of week demand insight
    if "_day_name" in df.columns and df["_day_name"] is not None and pax_col and pax_col in df.columns:
        day_pax = df.groupby("_day_name")[pax_col].sum()
        if not day_pax.empty:
            busiest_day = day_pax.idxmax()
            quietest_day = day_pax.idxmin()
            insights.append(f"📅 **Weekly Trend**: **{busiest_day}** records the highest weekly ridership, while **{quietest_day}** records the lowest.")

    # 4. Revenue insight
    if rev_col and route_col and route_col in df.columns and rev_col in df.columns:
        route_rev = df.groupby(route_col)[rev_col].sum()
        if not route_rev.empty:
            top_rev_route = route_rev.idxmax()
            top_rev_val = route_rev.max()
            insights.append(f"💰 **Top Revenue Contributor**: Route **'{top_rev_route}'** generated the highest fare revenue of **₹{top_rev_val:,.2f}**.")

    # 5. Delay & Reliability insight
    if delay_col and delay_col in df.columns:
        avg_delay = df[delay_col].mean()
        delayed_trips = (df[delay_col] > 3).sum()
        delayed_pct = (delayed_trips / len(df)) * 100 if len(df) > 0 else 0
        
        if route_col and route_col in df.columns:
            route_delay = df.groupby(route_col)[delay_col].mean()
            worst_delay_route = route_delay.idxmax()
            worst_delay_val = route_delay.max()
            insights.append(f"⏱️ **Reliability & Delays**: Average network delay is **{avg_delay:.1f} minutes** ({delayed_pct:.1f}% trips experience delay). Route **'{worst_delay_route}'** experienced the highest average delay (**{worst_delay_val:.1f} mins**).")
        else:
            insights.append(f"⏱️ **Reliability & Delays**: Average delay is **{avg_delay:.1f} minutes**, with **{delayed_pct:.1f}%** of trips running late.")

    # 6. Transport mode insight
    if type_col and pax_col and type_col in df.columns and pax_col in df.columns:
        mode_pax = df.groupby(type_col)[pax_col].sum()
        if not mode_pax.empty and len(mode_pax) > 1:
            top_mode = mode_pax.idxmax()
            insights.append(f"🚆 **Dominant Transport Mode**: **{top_mode}** accounts for the largest share of passenger volume (**{int(mode_pax.max()):,}** passengers).")

    return insights


# ---------------------------------------------------------------------------
# 6. MAIN APPLICATION EXECUTION
# ---------------------------------------------------------------------------
def main():
    # Header & Banner
    st.markdown("<h1 class='main-title'>🚍 Public Transport Analytics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Interactive Data Science Dashboard for Public Transit Performance, Passenger Flow, Route Optimization, and Operational Delays.</p>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # SIDEBAR: DATA INGESTION & CONTROLS
    # -----------------------------------------------------------------------
    st.sidebar.header("📁 Data Source & Controls")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload Custom Transit Dataset",
        type=["csv", "xlsx"],
        help="Upload your own operational transport CSV or Excel file to analyze."
    )

    is_using_sample = uploaded_file is None

    # Load Raw Data
    raw_df = load_data(uploaded_file)

    if raw_df is None or len(raw_df) == 0:
        st.error("⚠️ No dataset could be loaded. Please ensure `data/public_transport_data.csv` exists or upload a valid CSV file.")
        st.stop()

    if is_using_sample:
        st.sidebar.info("ℹ️ **Active Dataset**: Realistic Multi-Modal Transport Sample Data (Buses, Metro, Rail, BRTS).")
    else:
        st.sidebar.success(f"✅ Loaded uploaded dataset: **{uploaded_file.name}**")

    # Detect Columns
    col_map = detect_columns(raw_df)

    # Preprocess Data
    cleaned_df, audit_info = preprocess_data(raw_df, col_map)

    # -----------------------------------------------------------------------
    # SIDEBAR: DYNAMIC FILTERS
    # -----------------------------------------------------------------------
    st.sidebar.subheader("🔍 Filter Records")

    filtered_df = cleaned_df.copy()

    # Filter 1: Date Range
    date_col = col_map["date"]
    if date_col and filtered_df["_extracted_date"] is not None and not filtered_df["_extracted_date"].isna().all():
        min_date = filtered_df["_extracted_date"].min()
        max_date = filtered_df["_extracted_date"].max()
        
        selected_dates = st.sidebar.date_input(
            "Select Date Range",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date,
            help="Filter analytics between specific dates."
        )

        if isinstance(selected_dates, (list, tuple)) and len(selected_dates) == 2:
            start_d, end_d = selected_dates
            filtered_df = filtered_df[
                (filtered_df["_extracted_date"] >= start_d) & 
                (filtered_df["_extracted_date"] <= end_d)
            ]

    # Filter 2: Transport Mode (if available)
    type_col = col_map["transport_type"]
    if type_col and type_col in filtered_df.columns:
        all_modes = sorted(filtered_df[type_col].dropna().unique().tolist())
        selected_modes = st.sidebar.multiselect(
            "Transport Mode",
            options=all_modes,
            default=all_modes,
            help="Filter by transport type (e.g. Bus, Metro, Suburban Rail)."
        )
        if selected_modes:
            filtered_df = filtered_df[filtered_df[type_col].isin(selected_modes)]
        else:
            st.sidebar.warning("Please select at least one transport mode.")

    # Filter 3: Route Selection (if available)
    route_col = col_map["route"]
    if route_col and route_col in filtered_df.columns:
        all_routes = sorted(filtered_df[route_col].dropna().unique().tolist())
        selected_routes = st.sidebar.multiselect(
            "Routes",
            options=all_routes,
            default=all_routes,
            help="Select specific routes to inspect."
        )
        if selected_routes:
            filtered_df = filtered_df[filtered_df[route_col].isin(selected_routes)]
        else:
            st.sidebar.warning("Please select at least one route.")

    # Filter 4: Hour Range (if available)
    if "_hour" in filtered_df.columns and filtered_df["_hour"] is not None and not filtered_df["_hour"].isna().all():
        min_hr = int(filtered_df["_hour"].min())
        max_hr = int(filtered_df["_hour"].max())
        if min_hr < max_hr:
            selected_hour_range = st.sidebar.slider(
                "Operational Hour Range (24h)",
                min_value=min_hr,
                max_value=max_hr,
                value=(min_hr, max_hr),
                step=1
            )
            filtered_df = filtered_df[
                (filtered_df["_hour"] >= selected_hour_range[0]) & 
                (filtered_df["_hour"] <= selected_hour_range[1])
            ]

    # Sidebar Filter Summary
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Filtered Records**: `{len(filtered_df):,}` / `{len(cleaned_df):,}` trips")
    
    # -----------------------------------------------------------------------
    # ERROR & EMPTY DATA HANDLING
    # -----------------------------------------------------------------------
    if len(filtered_df) == 0:
        st.warning("⚠️ No data matches your active filter selection. Please broaden your sidebar filters.")
        st.stop()

    # Calculate KPIs
    kpis = calculate_kpis(filtered_df, col_map)

    # -----------------------------------------------------------------------
    # TOP KPI BANNER CARDS
    # -----------------------------------------------------------------------
    kpi_cols = st.columns(6)
    
    with kpi_cols[0]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">👥 Total Passengers</div>
            <div class="kpi-value">{kpis['total_passengers']:,}</div>
            <div class="kpi-subtext">Across {kpis['total_trips']:,} trips</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[1]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #10B981;">
            <div class="kpi-title">🚌 Total Trips</div>
            <div class="kpi-value">{kpis['total_trips']:,}</div>
            <div class="kpi-subtext">Completed journeys</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[2]:
        rev_display = f"₹{kpis['total_revenue']:,.0f}" if kpis['total_revenue'] > 0 else "N/A"
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #F59E0B;">
            <div class="kpi-title">💰 Total Revenue</div>
            <div class="kpi-value">{rev_display}</div>
            <div class="kpi-subtext">Ticket & fare earnings</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[3]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #6366F1;">
            <div class="kpi-title">📊 Avg Load / Trip</div>
            <div class="kpi-value">{kpis['avg_passengers_trip']}</div>
            <div class="kpi-subtext">Passengers per trip</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[4]:
        delay_display = f"{kpis['avg_delay']} min" if kpis['avg_delay'] is not None else "N/A"
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #EF4444;">
            <div class="kpi-title">⏱️ Average Delay</div>
            <div class="kpi-value">{delay_display}</div>
            <div class="kpi-subtext">Network schedule lag</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[5]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #8B5CF6;">
            <div class="kpi-title">🗺️ Active Routes</div>
            <div class="kpi-value">{kpis['total_routes']}</div>
            <div class="kpi-subtext">{kpis['total_vehicles']} active fleet vehicles</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # TABS NAVIGATION
    # -----------------------------------------------------------------------
    tabs = st.tabs([
        "📊 Overview",
        "👥 Passenger Trends",
        "🗺️ Route Performance",
        "⏰ Peak Hour Analysis",
        "💰 Revenue Analysis",
        "⏱️ Delay & Reliability",
        "🚌 Fleet & Vehicles",
        "💡 Key Insights",
        "🔍 Data Explorer"
    ])

    # =======================================================================
    # TAB 1: OVERVIEW
    # =======================================================================
    with tabs[0]:
        st.subheader("System Overview & Fleet Summary")
        
        ov_col1, ov_col2 = st.columns([3, 2])
        
        with ov_col1:
            pax_col = col_map["passenger_count"]
            date_col = col_map["date"]
            
            if pax_col and date_col and filtered_df["_extracted_date"] is not None:
                # Daily ridership trend preview
                daily_summary = filtered_df.groupby("_extracted_date")[pax_col].sum().reset_index()
                fig_ov_trend = px.area(
                    daily_summary,
                    x="_extracted_date",
                    y=pax_col,
                    title="Daily Passenger Demand Curve",
                    labels={"_extracted_date": "Date", pax_col: "Total Passengers"},
                    color_discrete_sequence=["#3B82F6"]
                )
                fig_ov_trend.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_ov_trend, use_container_width=True)
            else:
                st.info("Daily trend chart requires date and passenger columns.")

        with ov_col2:
            type_col = col_map["transport_type"]
            if type_col and pax_col and type_col in filtered_df.columns:
                mode_share = filtered_df.groupby(type_col)[pax_col].sum().reset_index()
                fig_mode_pie = px.pie(
                    mode_share,
                    names=type_col,
                    values=pax_col,
                    title="Passenger Share by Transport Mode",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_mode_pie.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_mode_pie, use_container_width=True)
            elif route_col and pax_col:
                top_routes = filtered_df.groupby(route_col)[pax_col].sum().nlargest(5).reset_index()
                fig_top_routes = px.bar(
                    top_routes,
                    x=pax_col,
                    y=route_col,
                    orientation='h',
                    title="Top 5 Routes by Ridership",
                    color=pax_col,
                    color_continuous_scale="Blues"
                )
                fig_top_routes.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_top_routes, use_container_width=True)
            else:
                st.info("Transport mode breakdown requires transport_type and passenger columns.")

        # Fleet snapshot table
        st.markdown("#### Operational Summary by Route")
        if route_col and route_col in filtered_df.columns:
            agg_dict = {kpis_col: 'sum' for kpis_col in [pax_col] if kpis_col}
            if col_map["revenue"]: agg_dict[col_map["revenue"]] = 'sum'
            if col_map["delay_minutes"]: agg_dict[col_map["delay_minutes"]] = 'mean'
            agg_dict[route_col] = 'count'

            route_summary = filtered_df.groupby(route_col).agg(agg_dict)
            route_summary = route_summary.rename(columns={route_col: 'Total Trips'})
            if pax_col: route_summary = route_summary.rename(columns={pax_col: 'Total Passengers'})
            if col_map["revenue"]: route_summary = route_summary.rename(columns={col_map["revenue"]: 'Total Revenue (₹)'})
            if col_map["delay_minutes"]: 
                route_summary = route_summary.rename(columns={col_map["delay_minutes"]: 'Avg Delay (mins)'})
                route_summary['Avg Delay (mins)'] = route_summary['Avg Delay (mins)'].round(1)

            st.dataframe(route_summary.sort_values(by='Total Trips', ascending=False), use_container_width=True)

    # =======================================================================
    # TAB 2: PASSENGER ANALYSIS
    # =======================================================================
    with tabs[1]:
        st.subheader("👥 Passenger Demand & Trend Analysis")

        pax_col = col_map["passenger_count"]
        if not pax_col or pax_col not in filtered_df.columns:
            st.warning("Passenger analysis is unavailable because no passenger count column was detected.")
        else:
            # Highlight Cards
            if "_extracted_date" in filtered_df.columns and filtered_df["_extracted_date"] is not None and not filtered_df["_extracted_date"].isna().all():
                daily_pax = filtered_df.groupby("_extracted_date")[pax_col].sum()
                busiest_date = daily_pax.idxmax()
                busiest_count = int(daily_pax.max())
                quietest_date = daily_pax.idxmin()
                quietest_count = int(daily_pax.min())

                pax_stat_cols = st.columns(4)
                pax_stat_cols[0].metric("Highest Passenger Day", f"{busiest_date}", f"{busiest_count:,} passengers")
                pax_stat_cols[1].metric("Lowest Passenger Day", f"{quietest_date}", f"{quietest_count:,} passengers")
                pax_stat_cols[2].metric("Daily Average Ridership", f"{int(daily_pax.mean()):,} / day")
                
                if "_month_name" in filtered_df.columns and filtered_df["_month_name"] is not None:
                    monthly_pax = filtered_df.groupby("_month_name")[pax_col].sum()
                    pax_stat_cols[3].metric("Peak Demand Month", f"{monthly_pax.idxmax()}", f"{int(monthly_pax.max()):,} pax")

            st.markdown("<br>", unsafe_allow_html=True)

            # Visualizations
            pax_row1_col1, pax_row1_col2 = st.columns(2)

            with pax_row1_col1:
                # 1. Timeline Chart
                if "_extracted_date" in filtered_df.columns and filtered_df["_extracted_date"] is not None:
                    daily_timeline = filtered_df.groupby("_extracted_date")[pax_col].sum().reset_index()
                    daily_timeline["7-Day Moving Avg"] = daily_timeline[pax_col].rolling(window=7, min_periods=1).mean()
                    
                    fig_timeline = go.Figure()
                    fig_timeline.add_trace(go.Bar(
                        x=daily_timeline["_extracted_date"],
                        y=daily_timeline[pax_col],
                        name="Daily Volume",
                        marker_color="#93C5FD",
                        opacity=0.7
                    ))
                    fig_timeline.add_trace(go.Scatter(
                        x=daily_timeline["_extracted_date"],
                        y=daily_timeline["7-Day Moving Avg"],
                        mode="lines",
                        name="7-Day Trend (Moving Avg)",
                        line=dict(color="#1E40AF", width=3)
                    ))
                    fig_timeline.update_layout(
                        title="Daily Passenger Volume with 7-Day Trend",
                        xaxis_title="Date",
                        yaxis_title="Total Passengers",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=380
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)

            with pax_row1_col2:
                # 2. Day of Week Pattern
                if "_day_name" in filtered_df.columns and filtered_df["_day_name"] is not None:
                    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    dow_df = filtered_df.groupby("_day_name")[pax_col].agg(['sum', 'mean']).reindex(day_order).reset_index()
                    
                    fig_dow = px.bar(
                        dow_df,
                        x="_day_name",
                        y="sum",
                        title="Passenger Ridership by Day of Week",
                        labels={"_day_name": "Day of Week", "sum": "Total Passengers"},
                        color="sum",
                        color_continuous_scale="Viridis",
                        text_auto=True
                    )
                    fig_dow.update_layout(height=380)
                    st.plotly_chart(fig_dow, use_container_width=True)

            pax_row2_col1, pax_row2_col2 = st.columns(2)

            with pax_row2_col1:
                # 3. Monthly Demand Breakdown
                if "_year_month" in filtered_df.columns and filtered_df["_year_month"] is not None and not filtered_df["_year_month"].isna().all():
                    month_df = filtered_df.groupby("_year_month")[pax_col].sum().reset_index()
                    fig_month = px.bar(
                        month_df,
                        x="_year_month",
                        y=pax_col,
                        title="Monthly Ridership Trend",
                        labels={"_year_month": "Month", pax_col: "Total Passengers"},
                        color=pax_col,
                        color_continuous_scale="Purples"
                    )
                    fig_month.update_layout(height=350)
                    st.plotly_chart(fig_month, use_container_width=True)

            with pax_row2_col2:
                # 4. Distribution of Passengers per Trip
                fig_hist = px.histogram(
                    filtered_df,
                    x=pax_col,
                    nbins=30,
                    title="Distribution of Passenger Loads per Trip",
                    labels={pax_col: "Passenger Count per Trip"},
                    color_discrete_sequence=["#2563EB"],
                    marginal="box"
                )
                fig_hist.update_layout(height=350)
                st.plotly_chart(fig_hist, use_container_width=True)

    # =======================================================================
    # TAB 3: ROUTE PERFORMANCE
    # =======================================================================
    with tabs[2]:
        st.subheader("🗺️ Route Performance & Utilization")

        route_col = col_map["route"]
        pax_col = col_map["passenger_count"]
        rev_col = col_map["revenue"]
        delay_col = col_map["delay_minutes"]

        if not route_col or route_col not in filtered_df.columns:
            st.warning("Route analysis is unavailable because no route column was detected in this dataset.")
        else:
            route_pax_series = filtered_df.groupby(route_col)[pax_col].sum() if pax_col else None
            
            rt_col1, rt_col2 = st.columns(2)
            
            with rt_col1:
                if route_pax_series is not None:
                    # Top Performing Routes (Most used)
                    top_routes = route_pax_series.nlargest(10).reset_index()
                    fig_top = px.bar(
                        top_routes,
                        x=pax_col,
                        y=route_col,
                        orientation='h',
                        title="Top 10 Most Utilized Routes (Total Passengers)",
                        labels={pax_col: "Total Passengers", route_col: "Route"},
                        color=pax_col,
                        color_continuous_scale="Tealgrn"
                    )
                    fig_top.update_layout(yaxis=dict(autorange="reversed"), height=400)
                    st.plotly_chart(fig_top, use_container_width=True)

            with rt_col2:
                if route_pax_series is not None and len(route_pax_series) > 5:
                    # Least Used Routes
                    bottom_routes = route_pax_series.nsmallest(10).reset_index()
                    fig_bot = px.bar(
                        bottom_routes,
                        x=pax_col,
                        y=route_col,
                        orientation='h',
                        title="Bottom Routes by Passenger Volume",
                        labels={pax_col: "Total Passengers", route_col: "Route"},
                        color=pax_col,
                        color_continuous_scale="Reds"
                    )
                    fig_bot.update_layout(yaxis=dict(autorange="reversed"), height=400)
                    st.plotly_chart(fig_bot, use_container_width=True)
                elif rev_col and rev_col in filtered_df.columns:
                    route_rev = filtered_df.groupby(route_col)[rev_col].sum().nlargest(10).reset_index()
                    fig_rt_rev = px.bar(
                        route_rev,
                        x=rev_col,
                        y=route_col,
                        orientation='h',
                        title="Top Routes by Fare Revenue",
                        labels={rev_col: "Total Revenue (₹)", route_col: "Route"},
                        color=rev_col,
                        color_continuous_scale="Blues"
                    )
                    fig_rt_rev.update_layout(yaxis=dict(autorange="reversed"), height=400)
                    st.plotly_chart(fig_rt_rev, use_container_width=True)

            # Route Delay Comparison
            if delay_col and delay_col in filtered_df.columns:
                st.markdown("#### Average Delay per Route (Punctuality Benchmark)")
                route_delays = filtered_df.groupby(route_col)[delay_col].mean().sort_values(ascending=False).reset_index()
                fig_rt_delay = px.bar(
                    route_delays,
                    x=route_col,
                    y=delay_col,
                    title="Average Delay (Minutes) by Route",
                    labels={delay_col: "Average Delay (mins)", route_col: "Route"},
                    color=delay_col,
                    color_continuous_scale="OrRd"
                )
                fig_rt_delay.update_layout(height=350, xaxis_tickangle=-45)
                st.plotly_chart(fig_rt_delay, use_container_width=True)

    # =======================================================================
    # TAB 4: PEAK HOUR ANALYSIS
    # =======================================================================
    with tabs[3]:
        st.subheader("⏰ Peak Hour & Commuter Temporal Analysis")
        
        st.markdown("""
        > **What is Peak Hour Analysis?**  
        > Peak hour analysis studies passenger influx across the 24 hours of a day to identify when transit services 
        > experience extreme crowding vs. idle capacity. This enables transport authorities to optimize fleet schedules, 
        > reduce commuter wait times, and dispatch additional high-capacity vehicles during surge windows.
        """)

        if "_hour" not in filtered_df.columns or filtered_df["_hour"] is None or filtered_df["_hour"].isna().all():
            st.warning("⚠️ Peak-hour analysis requires time data (e.g. HH:MM:SS or timestamp) which is missing or could not be parsed from this dataset.")
        else:
            pax_col = col_map["passenger_count"]
            hourly_agg = filtered_df.groupby("_hour").agg(
                Total_Passengers=(pax_col, 'sum') if pax_col else ('_hour', 'count'),
                Total_Trips=('_hour', 'count')
            ).reset_index()

            # Identify Peak Categories
            # Standard definitions: Morning Peak (8-10), Evening Peak (17-19)
            def categorize_hour(hr):
                if 8 <= hr <= 10: return "Morning Peak (8-10 AM)"
                elif 17 <= hr <= 19: return "Evening Peak (5-7 PM)"
                elif 11 <= hr <= 16: return "Afternoon Normal (11 AM-4 PM)"
                elif 6 <= hr <= 7: return "Early Morning (6-7 AM)"
                else: return "Late Evening / Night"

            hourly_agg["Period"] = hourly_agg["_hour"].apply(categorize_hour)

            # Peak Hour Visualizations
            pk_col1, pk_col2 = st.columns([3, 2])

            with pk_col1:
                fig_peak = px.line(
                    hourly_agg,
                    x="_hour",
                    y="Total_Passengers",
                    title="Hourly Passenger Demand Curve (24-Hour Cycle)",
                    labels={"_hour": "Hour of Day (0 - 23)", "Total_Passengers": "Total Passenger Volume"},
                    markers=True,
                    line_shape="spline"
                )
                # Highlight peak regions
                fig_peak.add_vrect(x0=7.5, x1=10.5, fillcolor="red", opacity=0.15, line_width=0, annotation_text="Morning Peak", annotation_position="top left")
                fig_peak.add_vrect(x0=16.5, x1=19.5, fillcolor="orange", opacity=0.15, line_width=0, annotation_text="Evening Peak", annotation_position="top left")
                fig_peak.update_layout(height=400, xaxis=dict(tickmode='linear', tick0=0, dtick=1))
                st.plotly_chart(fig_peak, use_container_width=True)

            with pk_col2:
                # Demand share by Period
                period_share = hourly_agg.groupby("Period")["Total_Passengers"].sum().reset_index()
                fig_period = px.pie(
                    period_share,
                    names="Period",
                    values="Total_Passengers",
                    title="Passenger Volume Share by Time Window",
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                fig_period.update_layout(height=400)
                st.plotly_chart(fig_period, use_container_width=True)

            # Heatmap: Hour of Day vs Day of Week
            if "_day_name" in filtered_df.columns and filtered_df["_day_name"] is not None and pax_col:
                st.markdown("#### Heatmap: Passenger Demand by Hour & Day of Week")
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                heatmap_data = filtered_df.pivot_table(
                    index="_day_name",
                    columns="_hour",
                    values=pax_col,
                    aggfunc='sum',
                    fill_value=0
                ).reindex(day_order)

                fig_heat = px.imshow(
                    heatmap_data,
                    labels=dict(x="Hour of Day", y="Day of Week", color="Passengers"),
                    title="Hourly Commuter Congestion Heatmap",
                    color_continuous_scale="YlOrRd",
                    aspect="auto"
                )
                fig_heat.update_layout(height=360)
                st.plotly_chart(fig_heat, use_container_width=True)

    # =======================================================================
    # TAB 5: REVENUE ANALYSIS
    # =======================================================================
    with tabs[4]:
        st.subheader("💰 Revenue & Ticket Sales Analysis")

        rev_col = col_map["revenue"]
        pax_col = col_map["passenger_count"]
        price_col = col_map["ticket_price"]
        route_col = col_map["route"]
        type_col = col_map["transport_type"]

        if not rev_col or rev_col not in filtered_df.columns:
            st.warning("⚠️ Revenue data is unavailable in this dataset because no fare, price, or revenue columns were detected.")
        else:
            if "calculated_revenue" in filtered_df.columns and rev_col == "calculated_revenue":
                st.info("ℹ️ **Formula Notice**: Total Revenue was estimated using formula: **Revenue = Passenger Count × Ticket Price**.")

            total_rev = filtered_df[rev_col].sum()
            avg_rev_trip = filtered_df[rev_col].mean()
            avg_fare_pax = total_rev / filtered_df[pax_col].sum() if pax_col and filtered_df[pax_col].sum() > 0 else 0.0

            rev_metric_cols = st.columns(3)
            rev_metric_cols[0].metric("Total Fare Revenue", f"₹{total_rev:,.2f}")
            rev_metric_cols[1].metric("Average Revenue / Trip", f"₹{avg_rev_trip:,.2f}")
            rev_metric_cols[2].metric("Average Fare / Passenger", f"₹{avg_fare_pax:,.2f}")

            st.markdown("<br>", unsafe_allow_html=True)

            rev_row1_col1, rev_row1_col2 = st.columns(2)

            with rev_row1_col1:
                # Revenue by Route
                if route_col and route_col in filtered_df.columns:
                    top_rev_routes = filtered_df.groupby(route_col)[rev_col].sum().nlargest(10).reset_index()
                    fig_rev_rt = px.bar(
                        top_rev_routes,
                        x=rev_col,
                        y=route_col,
                        orientation='h',
                        title="Top 10 Revenue-Generating Routes",
                        labels={rev_col: "Total Revenue (₹)", route_col: "Route"},
                        color=rev_col,
                        color_continuous_scale="Greens"
                    )
                    fig_rev_rt.update_layout(yaxis=dict(autorange="reversed"), height=380)
                    st.plotly_chart(fig_rev_rt, use_container_width=True)

            with rev_row1_col2:
                # Revenue by Transport Type
                if type_col and type_col in filtered_df.columns:
                    rev_by_type = filtered_df.groupby(type_col)[rev_col].sum().reset_index()
                    fig_rev_type = px.pie(
                        rev_by_type,
                        names=type_col,
                        values=rev_col,
                        title="Revenue Contribution by Transport Mode",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_rev_type.update_layout(height=380)
                    st.plotly_chart(fig_rev_type, use_container_width=True)

            # Daily Revenue Trend
            if "_extracted_date" in filtered_df.columns and filtered_df["_extracted_date"] is not None and not filtered_df["_extracted_date"].isna().all():
                daily_rev = filtered_df.groupby("_extracted_date")[rev_col].sum().reset_index()
                fig_daily_rev = px.line(
                    daily_rev,
                    x="_extracted_date",
                    y=rev_col,
                    title="Daily Fare Collection Over Time",
                    labels={"_extracted_date": "Date", rev_col: "Revenue (₹)"},
                    color_discrete_sequence=["#10B981"]
                )
                fig_daily_rev.update_layout(height=350)
                st.plotly_chart(fig_daily_rev, use_container_width=True)

    # =======================================================================
    # TAB 6: DELAY ANALYSIS
    # =======================================================================
    with tabs[5]:
        st.subheader("⏱️ Schedule Delay & Transit Reliability")

        delay_col = col_map["delay_minutes"]
        route_col = col_map["route"]

        if not delay_col or delay_col not in filtered_df.columns:
            st.warning("⚠️ Delay analysis is unavailable because the dataset does not contain a delay column.")
        else:
            avg_delay = filtered_df[delay_col].mean()
            max_delay = filtered_df[delay_col].max()
            ontime_trips = (filtered_df[delay_col] <= 3).sum()
            mod_delays = ((filtered_df[delay_col] > 3) & (filtered_df[delay_col] <= 15)).sum()
            severe_delays = (filtered_df[delay_col] > 15).sum()
            total_trips = len(filtered_df)

            del_cols = st.columns(4)
            del_cols[0].metric("Average Delay", f"{avg_delay:.1f} mins")
            del_cols[1].metric("Maximum Delay Recorded", f"{max_delay} mins")
            del_cols[2].metric("On-Time Performance (≤ 3m)", f"{(ontime_trips/total_trips)*100:.1f}%")
            del_cols[3].metric("Severe Delays (> 15m)", f"{(severe_delays/total_trips)*100:.1f}%")

            st.markdown("<br>", unsafe_allow_html=True)

            del_row1_col1, del_row1_col2 = st.columns(2)

            with del_row1_col1:
                # Delay Distribution Histogram
                fig_del_dist = px.histogram(
                    filtered_df,
                    x=delay_col,
                    nbins=25,
                    title="Delay Distribution (Minutes)",
                    labels={delay_col: "Arrival Delay (minutes)"},
                    color_discrete_sequence=["#EF4444"]
                )
                fig_del_dist.update_layout(height=380)
                st.plotly_chart(fig_del_dist, use_container_width=True)

            with del_row1_col2:
                # Delay by Route
                if route_col and route_col in filtered_df.columns:
                    route_delay_df = filtered_df.groupby(route_col)[delay_col].mean().sort_values(ascending=False).reset_index()
                    fig_rt_del = px.bar(
                        route_delay_df,
                        x=delay_col,
                        y=route_col,
                        orientation='h',
                        title="Average Delay by Route (Highest Lag First)",
                        labels={delay_col: "Average Delay (mins)", route_col: "Route"},
                        color=delay_col,
                        color_continuous_scale="Reds"
                    )
                    fig_rt_del.update_layout(yaxis=dict(autorange="reversed"), height=380)
                    st.plotly_chart(fig_rt_del, use_container_width=True)

            # Delay trend over time
            if "_extracted_date" in filtered_df.columns and filtered_df["_extracted_date"] is not None and not filtered_df["_extracted_date"].isna().all():
                daily_delay = filtered_df.groupby("_extracted_date")[delay_col].mean().reset_index()
                fig_daily_delay = px.line(
                    daily_delay,
                    x="_extracted_date",
                    y=delay_col,
                    title="Daily Average Delay Trend",
                    labels={"_extracted_date": "Date", delay_col: "Avg Delay (mins)"},
                    color_discrete_sequence=["#DC2626"]
                )
                fig_daily_delay.update_layout(height=350)
                st.plotly_chart(fig_daily_delay, use_container_width=True)

    # =======================================================================
    # TAB 7: VEHICLE ANALYSIS
    # =======================================================================
    with tabs[6]:
        st.subheader("🚌 Fleet Utilization & Vehicle Analytics")

        veh_col = col_map["vehicle_id"]
        type_col = col_map["transport_type"]
        pax_col = col_map["passenger_count"]
        rev_col = col_map["revenue"]
        cap_col = col_map["capacity"]

        if not veh_col or veh_col not in filtered_df.columns:
            st.warning("⚠️ Vehicle analysis is unavailable because no vehicle_id or fleet identifier was detected.")
        else:
            veh_stat_cols = st.columns(4)
            veh_stat_cols[0].metric("Total Fleet Vehicles", f"{filtered_df[veh_col].nunique()}")
            veh_stat_cols[1].metric("Avg Trips / Vehicle", f"{len(filtered_df) / filtered_df[veh_col].nunique():.1f}")
            if pax_col:
                veh_stat_cols[2].metric("Avg Passengers / Vehicle", f"{int(filtered_df.groupby(veh_col)[pax_col].sum().mean()):,}")
            if "_utilization_rate" in filtered_df.columns and filtered_df["_utilization_rate"] is not None and not filtered_df["_utilization_rate"].isna().all():
                veh_stat_cols[3].metric("Avg Capacity Utilization", f"{filtered_df['_utilization_rate'].mean():.1f}%")

            st.markdown("<br>", unsafe_allow_html=True)

            veh_col1, veh_col2 = st.columns(2)

            with veh_col1:
                # Top Vehicles by Trips Completed
                top_vehicles = filtered_df[veh_col].value_counts().nlargest(10).reset_index()
                top_vehicles.columns = [veh_col, "Trips_Completed"]
                fig_veh_trips = px.bar(
                    top_vehicles,
                    x="Trips_Completed",
                    y=veh_col,
                    orientation='h',
                    title="Top 10 Most Utilized Fleet Vehicles (Trips Completed)",
                    color="Trips_Completed",
                    color_continuous_scale="Blues"
                )
                fig_veh_trips.update_layout(yaxis=dict(autorange="reversed"), height=380)
                st.plotly_chart(fig_veh_trips, use_container_width=True)

            with veh_col2:
                # Vehicle Utilization Distribution (if capacity available)
                if "_utilization_rate" in filtered_df.columns and filtered_df["_utilization_rate"] is not None and not filtered_df["_utilization_rate"].isna().all():
                    fig_util = px.histogram(
                        filtered_df,
                        x="_utilization_rate",
                        nbins=25,
                        title="Vehicle Capacity Utilization Rate (%) Distribution",
                        labels={"_utilization_rate": "Utilization Rate (%) = (Passengers / Capacity) * 100"},
                        color_discrete_sequence=["#059669"]
                    )
                    fig_util.update_layout(height=380)
                    st.plotly_chart(fig_util, use_container_width=True)
                elif type_col and pax_col and type_col in filtered_df.columns:
                    type_perf = filtered_df.groupby(type_col)[pax_col].mean().reset_index()
                    fig_type_pax = px.bar(
                        type_perf,
                        x=type_col,
                        y=pax_col,
                        title="Average Passenger Load by Transport Mode",
                        labels={pax_col: "Avg Passengers per Trip", type_col: "Mode"},
                        color=type_col
                    )
                    fig_type_pax.update_layout(height=380)
                    st.plotly_chart(fig_type_pax, use_container_width=True)

    # =======================================================================
    # TAB 8: KEY INSIGHTS
    # =======================================================================
    with tabs[7]:
        st.subheader("💡 Automated Data-Driven Insights")
        st.markdown("These insights are dynamically generated by evaluating the mathematical distributions, route aggregates, and delay indices of your current dataset.")

        insights = generate_insights(filtered_df, col_map)

        for ins in insights:
            st.markdown(f"<div class='insight-badge'>{ins}</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Operational Recommendations for Transit Management")
        st.markdown("""
        1. **Dynamic Frequency Scheduling**: Deploy extra buses/trains during the identified 8:00–10:00 AM and 5:00–7:00 PM peak periods to mitigate overcrowding and lower average commuter delay.
        2. **Route Congestion Bottlenecks**: Target priority bus lanes (BRTS) or dedicated signal priority on the top-delayed routes to restore punctuality.
        3. **Fleet Reallocation**: Shift under-utilized fleet vehicles from bottom-ranking routes to top-revenue high-demand corridors.
        4. **Preventative Maintenance**: Vehicles with trip counts exceeding network averages should be flagged for preventative maintenance cycles to prevent roadside breakdowns.
        """)

    # =======================================================================
    # TAB 9: DATA EXPLORER & EXPORT
    # =======================================================================
    with tabs[8]:
        st.subheader("🔍 Data Explorer & Quality Audit")

        st.markdown("#### Preprocessing & Cleaning Audit Report")
        audit_col1, audit_col2, audit_col3, audit_col4 = st.columns(4)
        audit_col1.metric("Rows Cleaned", f"{audit_info['final_rows']:,}", f"from {audit_info['initial_rows']:,}")
        audit_col2.metric("Duplicates Dropped", f"{audit_info['duplicates_removed']:,}")
        audit_col3.metric("Missing Values Handled", f"{audit_info['initial_nulls']:,}")
        audit_col4.metric("Operational Date Range", audit_info['date_range'])

        st.markdown("<br>", unsafe_allow_html=True)

        view_mode = st.radio("Select View:", ["Cleaned Data (Filtered)", "Raw Uploaded Data"], horizontal=True)

        if view_mode == "Cleaned Data (Filtered)":
            display_df = filtered_df
        else:
            display_df = raw_df

        # Search Bar
        search_query = st.text_input("Quick Filter Table (Search route, stop, or vehicle):", placeholder="e.g. Metro, Tech Park, BUS-101...")
        if search_query:
            # Search string across all text columns
            text_cols = display_df.select_dtypes(include=['object', 'string']).columns
            mask = np.column_stack([display_df[col].astype(str).str.contains(search_query, case=False, na=False) for col in text_cols])
            display_df = display_df[mask.any(axis=1)]

        st.dataframe(display_df, use_container_width=True, height=450)

        # Download Cleaned Data
        csv_buffer = io.StringIO()
        filtered_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Cleaned Dataset as CSV",
            data=csv_buffer.getvalue(),
            file_name="cleaned_public_transport_data.csv",
            mime="text/csv",
            help="Click to export the cleaned and preprocessed dataset for your project report."
        )


if __name__ == "__main__":
    main()
