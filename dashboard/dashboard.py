import os
import streamlit as st
import pandas as pd
import altair as alt

# —————— page config ——————
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data
def load_data():
    # locate CSVs next to this script
    base_dir   = os.path.dirname(__file__)
    day_path   = os.path.join(base_dir, "main-day.csv")
    hour_path  = os.path.join(base_dir, "main-hour.csv")

    df_day  = pd.read_csv(day_path,  parse_dates=["date"])
    df_hour = pd.read_csv(hour_path, parse_dates=["date"])
    df_hour.sort_values("date", inplace=True)
    return df_day, df_hour

df_day, df_hour = load_data()

# — sidebar filters —
st.sidebar.header("Filter Options")
date_min, date_max = st.sidebar.date_input(
    "Select Date Range",
    [df_hour.date.min(), df_hour.date.max()],
    min_value=df_hour.date.min(),
    max_value=df_hour.date.max(),
)
season_options = st.sidebar.multiselect(
    "Season",
    options=df_day.season.unique(),
    default=list(df_day.season.unique()),
)
weather_map = {1: "Clear", 2: "Mist/Cloudy", 3: "Light Snow/Rain", 4: "Heavy Rain/Ice"}
weather_options = st.sidebar.multiselect(
    "Weather Conditions",
    options=list(weather_map.values()),
    default=list(weather_map.values()),
)

# — apply filters —
start_date, end_date = pd.to_datetime(date_min), pd.to_datetime(date_max)
df_hour_f = df_hour[(df_hour.date >= start_date) & (df_hour.date <= end_date)].copy()
df_hour_f["weather_desc"] = df_hour_f.weather.map(weather_map)
df_hour_f = df_hour_f[
    df_hour_f.season.isin(season_options) &
    df_hour_f.weather_desc.isin(weather_options)
]

df_day_f = df_day[(df_day.date >= start_date) & (df_day.date <= end_date)].copy()
df_day_f["weather_desc"] = df_day_f.weather.map(weather_map)
df_day_f = df_day_f[
    df_day_f.season.isin(season_options) &
    df_day_f.weather_desc.isin(weather_options)
]

# — page content —
st.markdown("# 🚲 Bike Sharing Insights")
st.markdown("Analyze seasonal trends and the impact of weather and temperature on bike rentals.")

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Avg Temp", f"{df_hour_f.temperature.mean():.1f} °C")
c2.metric("Avg Humidity", f"{df_hour_f.humidity.mean():.0f} %")
c3.metric("Avg Windspeed", f"{df_hour_f.windspeed.mean():.1f} km/h")

# 1. Seasonal Usage
st.header("1. Seasonal Usage")
season_summary = (
    df_day_f.groupby("season")
           .total.sum()
           .reset_index()
           .sort_values("total", ascending=False)
)
bar_season = (
    alt.Chart(season_summary)
       .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
       .encode(
           x=alt.X("season:N", title="Season"),
           y=alt.Y("total:Q", title="Total Rentals"),
           color=alt.Color("season:N", scale=alt.Scale(scheme="tableau10")),
           tooltip=["season", "total"],
       )
       .properties(width=700, height=400)
)
st.altair_chart(bar_season, use_container_width=True)
top = season_summary.iloc[0]
st.markdown(f"**Top Season:** {top.season} with **{top.total:,}** rentals.")

# 2. Weather & Temperature Effects
st.header("2. Weather & Temperature Effects")

st.subheader("Temperature vs. Hourly Rentals")
scatter = (
    alt.Chart(df_hour_f)
       .mark_circle(size=70, opacity=0.6)
       .encode(
           x="temperature:Q", y="total:Q",
           color=alt.Color("season:N", legend=alt.Legend(title="Season")),
           tooltip=["date", "hour", "total", "temperature", "weather_desc"],
       )
       .interactive()
       .properties(width=700, height=400)
)
st.altair_chart(scatter, use_container_width=True)
st.markdown(
    "*Observation:* Rentals rise with temperature up to the mid-20s °C, then plateau or dip at extremes."
)

st.subheader("Total Rentals by Weather Condition")
weather_summary = (
    df_hour_f.groupby("weather_desc")
             .total.sum()
             .reset_index()
             .sort_values("total", ascending=False)
)
bar_weather = (
    alt.Chart(weather_summary)
       .mark_bar()
       .encode(
           x=alt.X("weather_desc:N", sort="-y", title="Weather Condition"),
           y="total:Q", tooltip=["weather_desc", "total"],
           color=alt.Color("weather_desc:N", legend=None),
       )
       .properties(width=700, height=400)
)
st.altair_chart(bar_weather, use_container_width=True)
st.markdown("*Observation:* Clear days have the most rentals; severe weather sharply reduces usage.")
