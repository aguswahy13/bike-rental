import os
import streamlit as st
import pandas as pd
import altair as alt

# Debug — remove once it’s working
print("🔍 CWD:", os.getcwd())
print("📂 Root:", os.listdir(os.getcwd()))
print("📂 dashboard/:", os.listdir(os.path.join(os.getcwd(), "dashboard")))

# Must come first
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    project_root = os.getcwd()
    data_dir     = os.path.join(project_root, "dashboard")

    day_path  = os.path.join(data_dir, "main-day.csv")
    hour_path = os.path.join(data_dir, "main-hour.csv")
    print("Loading:", day_path, os.path.exists(day_path))
    print("Loading:", hour_path, os.path.exists(hour_path))

    df_day  = pd.read_csv(day_path,  parse_dates=["date"])
    df_hour = pd.read_csv(hour_path, parse_dates=["date"])
    df_hour.sort_values("date", inplace=True)
    return df_day, df_hour

df_day, df_hour = load_data()

# Sidebar filters
st.sidebar.header("Filter Options")
# Date range picker
date_min, date_max = st.sidebar.date_input(
    "Select Date Range",
    [df_hour.date.min(), df_hour.date.max()],
    min_value=df_hour.date.min(),
    max_value=df_hour.date.max()
)
# Season multiselect
season_options = st.sidebar.multiselect(
    "Season",
    options=df_day.season.unique(),
    default=list(df_day.season.unique())
)
# Weather mapping and multiselect
weather_map = {1: "Clear", 2: "Mist/Cloudy", 3: "Light Snow/Rain", 4: "Heavy Rain/Ice"}
weather_options = st.sidebar.multiselect(
    "Weather Conditions",
    options=list(weather_map.values()),
    default=list(weather_map.values())
)

# Apply filters to data
start_date, end_date = pd.to_datetime(date_min), pd.to_datetime(date_max)
df_hour_filtered = df_hour[(df_hour.date >= start_date) & (df_hour.date <= end_date)].copy()
df_hour_filtered['weather_desc'] = df_hour_filtered.weather.map(weather_map)
df_hour_filtered = df_hour_filtered[df_hour_filtered.season.isin(season_options) & df_hour_filtered.weather_desc.isin(weather_options)]

df_day_filtered = df_day[(df_day.date >= start_date) & (df_day.date <= end_date)].copy()
df_day_filtered['weather_desc'] = df_day_filtered.weather.map(weather_map)
df_day_filtered = df_day_filtered[df_day_filtered.season.isin(season_options) & df_day_filtered.weather_desc.isin(weather_options)]

# Main title and description
st.markdown("# 🚲 Bike Sharing Insights")
st.markdown("Analyze seasonal trends and the impact of weather and temperature on bike rentals.")

# KPI metrics
col1, col2, col3 = st.columns(3)
col1.metric("Average Temperature", f"{df_hour_filtered.temperature.mean():.1f} °C")
col2.metric("Average Humidity", f"{df_hour_filtered.humidity.mean():.0f} %")
col3.metric("Average Windspeed", f"{df_hour_filtered.windspeed.mean():.1f} km/h")

# ---------------------------------------------
# Case 1: Seasonal Rental Usage
# ---------------------------------------------
st.header("1. Seasonal Usage")
season_summary = (
    df_day_filtered
    .groupby("season")
    .total.sum()
    .reset_index()
    .sort_values("total", ascending=False)
)
bar_season = alt.Chart(season_summary).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
    x=alt.X("season:N", title="Season"),
    y=alt.Y("total:Q", title="Total Rentals"),
    color=alt.Color("season:N", scale=alt.Scale(scheme="tableau10")),
    tooltip=["season", "total"]
).properties(width=700, height=400)

st.altair_chart(bar_season, use_container_width=True)
st.markdown(f"**Top Season:** {season_summary.iloc[0].season} with **{season_summary.iloc[0].total:,}** rentals.")

# ---------------------------------------------
# Case 2: Weather & Temperature Effects
# ---------------------------------------------
st.header("2. Weather & Temperature Effects")

# Temperature vs Hourly Rentals
st.subheader("Temperature vs. Hourly Rentals")
scatter = alt.Chart(df_hour_filtered).mark_circle(size=70, opacity=0.6).encode(
    x=alt.X("temperature:Q", title="Temperature (°C)"),
    y=alt.Y("total:Q", title="Hourly Rentals"),
    color=alt.Color("season:N", legend=alt.Legend(title="Season")),
    tooltip=["date", "hour", "total", "temperature", "weather_desc"]
).interactive().properties(width=700, height=400)

st.altair_chart(scatter, use_container_width=True)
st.markdown("*Observation:* Rentals rise steadily with temperature up to mid-20s °C, then plateau or dip at extreme heat or cold.")

# Weather conditions vs Rentals
st.subheader("Total Rentals by Weather Condition")
weather_summary = (
    df_hour_filtered
    .groupby("weather_desc")
    .total.sum()
    .reset_index()
    .sort_values("total", ascending=False)
)
bar_weather = alt.Chart(weather_summary).mark_bar().encode(
    x=alt.X("weather_desc:N", sort='-y', title="Weather Condition"),
    y=alt.Y("total:Q", title="Total Rentals"),
    tooltip=["weather_desc", "total"],
    color=alt.Color("weather_desc:N", legend=None)
).properties(width=700, height=400)

st.altair_chart(bar_weather, use_container_width=True)
st.markdown("*Observation:* Clear days have the most rentals; severe weather sharply reduces usage.")
