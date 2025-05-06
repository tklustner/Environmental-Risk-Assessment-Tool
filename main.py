import streamlit as st
st.set_page_config(layout="wide")

from geemap.foliumap import Map
import geopandas as gpd
import json
import requests
import matplotlib.pyplot as plt
import pandas as pd
import ee
from datetime import datetime
from streamlit_folium import st_folium
from fetch_era5_soil_moisture import get_era5_soil_moisture
from fetch_ndvi import get_ndvi_data

# Authenticate EE
try:
    ee.Initialize()
except Exception as e:
    st.error("Failed to initialize Google Earth Engine. Ensure authentication is set up.")

# Layout configuration
col1, col2, col3 = st.columns([1, 2.4, 1])

with col1:
    st.subheader("🌧️ 12-Month Precipitation Data", anchor=False)
    placeholder_chart1 = st.empty()

with col3:
    st.subheader("🌿 Vegetation Health (NDVI)", anchor=False)
    placeholder_chart2 = st.empty()

with col2:
    st.subheader("🗺️ Select Area of Interest (≤ 10000 km² recommended)", anchor=False)
    st.write("E.g. Bangkok Metropolitan Area | Sundarbans Mangrove Forest | Gulf of Honduras")
    m = Map()
    map_data = st_folium(m, height=600, width=800)

# Fetch CHIRPS rainfall data
def get_chirps_data(aoi):
    collection = ee.ImageCollection("UCSB-CHG/CHIRPS/PENTAD")
    def reduce_region(image):
        mean = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=aoi, scale=5000, bestEffort=True)
        return image.set("mean_precip", mean.get("precipitation"))

    start_date = "2024-01-01"
    end_date = datetime.today().strftime('%Y-%m-%d')
    filtered = collection.filterDate(start_date, end_date).map(reduce_region)
    time_series = filtered.aggregate_array("mean_precip").getInfo()
    dates = filtered.aggregate_array("system:time_start").map(lambda t: ee.Date(t).format("YYYY-MM-dd")).getInfo()
    return pd.DataFrame({"Date": pd.to_datetime(dates), "Rainfall (mm)": time_series})

# Classify risk based on thresholds
def classify_risk(ndvi_df=None, rain_df=None, soil_df=None):
    score, checks = 0, 0
    if ndvi_df is not None and not ndvi_df.empty:
        checks += 1
        if ndvi_df['NDVI'].mean() < 0.3:
            score += 1
    if rain_df is not None and not rain_df.empty:
        checks += 1
        if rain_df['Rainfall (mm)'].mean() < 10:
            score += 1
    if soil_df is not None and not soil_df.empty:
        checks += 1
        if soil_df['Soil Moisture'].mean() < 0.15:
            score += 1
    if checks == 0:
        return "⚠️ Insufficient Data"
    return ["🟢 Low Risk", "🟡 Moderate Risk", "🔴 High Risk"][min(score, 2)]

# Initialize dataframes
df, df_ndvi, df_soil, merged_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

if map_data and 'last_active_drawing' in map_data:
    drawn_features = map_data["all_drawings"]
    if drawn_features:
        geojson_data = drawn_features[-1]
        aoi = ee.Geometry.Polygon(geojson_data["geometry"]["coordinates"])
        st.session_state["aoi"] = aoi

        aoi_area = aoi.area().divide(1e6).getInfo()

        with col1:
            st.spinner("Fetching CHIRPS Data from GEE...")
            try:
                df = get_chirps_data(aoi)
                if not df.empty:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    fig.subplots_adjust(top=0.88)
                    ax.plot(df['Date'], df['Rainfall (mm)'], marker='o', linestyle='-', color='b')
                    ax.set_title("CHIRPS Rainfall Data", fontsize=16, pad=20)
                    ax.set_xlabel("Date", fontsize=12)
                    ax.set_ylabel("Rainfall (mm)", fontsize=12)
                    ax.grid(True, linestyle='--', alpha=0.6)
                    plt.xticks(rotation=45)
                    st.pyplot(fig, clear_figure=True, use_container_width=True)
                else:
                    st.error("No data retrieved for the AOI.")
            except Exception as e:
                st.error(f"Error fetching CHIRPS data: {e}")

        with col3:
            st.spinner('Loading NDVI Data...')
            try:
                df_ndvi = get_ndvi_data(aoi)
                if not df_ndvi.empty:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    fig.subplots_adjust(top=0.88)
                    ax.plot(df_ndvi['Date'], df_ndvi['NDVI'], marker='o', linestyle='-', color='g')
                    ax.set_title("Vegetation Health Index (NDVI)", fontsize=16, pad=20)
                    ax.set_xlabel("Date", fontsize=12)
                    ax.set_ylabel("NDVI", fontsize=12)
                    ax.axhspan(-1, 0, alpha=0.2, color='brown')
                    ax.axhspan(0, 0.2, alpha=0.2, color='yellow')
                    ax.axhspan(0.2, 0.4, alpha=0.2, color='yellowgreen')
                    ax.axhspan(0.4, 1, alpha=0.2, color='green')
                    ax.grid(True, linestyle='--', alpha=0.6)
                    plt.xticks(rotation=45)
                    st.pyplot(fig, clear_figure=True, use_container_width=True)

                    
                    cols = st.columns(3)
                    cols[0].metric("Average NDVI", f"{df_ndvi['NDVI'].mean():.2f}")
                    cols[1].metric("Max NDVI", f"{df_ndvi['NDVI'].max():.2f}")
                    cols[2].metric("Min NDVI", f"{df_ndvi['NDVI'].min():.2f}")

                    st.success("AOI captured successfully!")
                    st.markdown(f"""
                        <div style='font-size: 1.2rem; padding: 0.5rem 0;'>
                        <strong>📏 Area:</strong> {aoi_area:.2f} km²
                        </div>
                    """, unsafe_allow_html=True)

                    risk_level = classify_risk(df_ndvi, df, df_soil)
                    st.subheader("⚠️ Environmental Risk Score")
                    st.markdown(f"**Predicted Risk Level:** {risk_level}")

                else:
                    st.error("No NDVI data retrieved for the AOI.")
            except Exception as e:
                st.error(f"Error fetching NDVI data: {e}")

        with col1:
            st.markdown("---")
            st.subheader("🌱 Soil Moisture")
            st.spinner("Fetching ERA5 Soil Moisture Data...")
            try:
                df_soil = get_era5_soil_moisture(aoi)
                if not df_soil.empty:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    fig.subplots_adjust(top=0.88)
                    ax.plot(df_soil['Date'], df_soil['Soil Moisture'], marker='o', linestyle='-', color='blue')
                    ax.set_title("ERA5 Soil Moisture", fontsize=16, pad=20)
                    ax.set_xlabel("Date", fontsize=12)
                    ax.set_ylabel("Soil Moisture (m³/m³)", fontsize=12)
                    ax.grid(True, linestyle='--', alpha=0.6)
                    plt.xticks(rotation=45)
                    st.pyplot(fig, clear_figure=True, use_container_width=True)

                    st.caption("Soil Moisture Statistics")
                    cols = st.columns(3)
                    cols[0].metric("Average", f"{df_soil['Soil Moisture'].mean():.3f} m³/m³")
                    cols[1].metric("Max", f"{df_soil['Soil Moisture'].max():.3f} m³/m³")
                    cols[2].metric("Min", f"{df_soil['Soil Moisture'].min():.3f} m³/m³")
                else:
                    st.error("No soil moisture data retrieved for the AOI.")
            except Exception as e:
                st.error(f"Error fetching ERA5 soil moisture data: {e}")
# Merged dataset download
with col2:
    if not df.empty and not df_soil.empty and not df_ndvi.empty:
        try:
            merged_df = pd.merge(df, df_soil, on='Date', how='outer')
            merged_df = pd.merge(merged_df, df_ndvi, on='Date', how='outer').sort_values("Date")
            st.subheader("📥 Download Combined Environmental Data")
            st.download_button(
                label="Download Merged CSV",
                data=merged_df.to_csv(index=False).encode('utf-8'),
                file_name='environmental_metrics.csv',
                mime='text/csv'
            )
        except Exception as e:
            st.error(f"Failed to prepare combined CSV: {e}")