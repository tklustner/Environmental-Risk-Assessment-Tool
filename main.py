import streamlit as st
st.set_page_config(layout="wide")  # Ensure this is the first Streamlit command

import geemap.foliumap as geemap
import geopandas as gpd
import json
import requests
import matplotlib.pyplot as plt
import pandas as pd
import ee
from datetime import datetime
from streamlit_folium import st_folium
from fetch_era5_soil_moisture import get_era5_soil_moisture

# Authenticate and initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    st.error("Failed to initialize Google Earth Engine. Ensure authentication is set up.")

# Create three columns
col1, col2, col3 = st.columns([1, 2, 1])  # Middle column is wider for the map

with col1:
    st.subheader("Risk Metric 1 - CHIRPS Data")
    placeholder_chart1 = st.empty()
    
with col3:
    st.subheader("Risk Metric 2 - ERA5 Soil Moisture")
    placeholder_chart2 = st.empty()

# Initialize geemap in the middle column
with col2:
    st.subheader("Select Area of Interest")
    m = geemap.Map()
    map_data = st_folium(m, height=500, width=700)

# Function to fetch CHIRPS data from GEE
def get_chirps_data(aoi):
    collection = ee.ImageCollection("UCSB-CHG/CHIRPS/PENTAD")
    
    # Reduce to mean over AOI
    def reduce_region(image):
        mean = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=5000,
            bestEffort=True
        )
        return image.set("mean_precip", mean.get("precipitation"))
    
    start_date = "2024-01-01"
    end_date = datetime.today().strftime('%Y-%m-%d')
    
    filtered = collection.filterDate(start_date, end_date).map(reduce_region)
    time_series = filtered.aggregate_array("mean_precip").getInfo()
    dates = filtered.aggregate_array("system:time_start").map(lambda t: ee.Date(t).format("YYYY-MM-dd")).getInfo()
    
    return pd.DataFrame({"Date": pd.to_datetime(dates), "Rainfall (mm)": time_series})

# Process AOI drawn on the map
if map_data and 'last_active_drawing' in map_data:
    drawn_features = map_data["all_drawings"]
    if drawn_features:
        geojson_data = drawn_features[-1]  # Get the latest drawing
        aoi = ee.Geometry.Polygon(geojson_data["geometry"]["coordinates"])  # Convert AOI to EE format
        st.session_state["aoi"] = aoi  # Store AOI in session state
        
        # Compute AOI area in km^2
        aoi_area = aoi.area().divide(1e6).getInfo()
        
        # Display success message with formatted text
        st.success("AOI captured successfully!")
        st.markdown(f"### Area: {aoi_area:.2f} km²")

        # Fetch CHIRPS Data and display it in col1
        with col1:
            st.caption("Fetching CHIRPS Data from GEE...")
            try:
                df = get_chirps_data(aoi)
                if not df.empty:
                    
                    # Plot CHIRPS rainfall data with standardized style
                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.plot(df['Date'], df['Rainfall (mm)'], marker='o', linestyle='-', color='b', label='Rainfall')
                    ax.set_title("CHIRPS Rainfall Data (Jan 2024 - Present)", fontsize=14)
                    ax.set_xlabel("Date", fontsize=12)
                    ax.set_ylabel("Rainfall (mm)", fontsize=12)
                    ax.grid(True, linestyle='--', alpha=0.6)
                    ax.legend()
                    plt.xticks(rotation=45)
                    
                    st.pyplot(fig)
                else:
                    st.error("No data retrieved for the AOI.")
            except Exception as e:
                st.error(f"Error fetching CHIRPS data from GEE: {e}")

        # Fetch ERA5 Soil Moisture Data and display it in col3
        with col3:
            st.caption("Fetching ERA5 Soil Moisture Data from GEE...")
            try:
                df_soil = get_era5_soil_moisture(aoi)
                if not df_soil.empty:
                    
                    # Plot ERA5 soil moisture data with standardized style
                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.plot(df_soil['Date'], df_soil['Soil Moisture'], marker='o', linestyle='-', color='r', label='Soil Moisture')
                    ax.set_title("ERA5 Soil Moisture (Jan 2024 - Present)", fontsize=14)
                    ax.set_xlabel("Date", fontsize=12)
                    ax.set_ylabel("Soil Moisture (m³/m³)", fontsize=12)
                    ax.grid(True, linestyle='--', alpha=0.6)
                    ax.legend()
                    plt.xticks(rotation=45)
                    
                    st.pyplot(fig)
                else:
                    st.error("No soil moisture data retrieved for the AOI.")
            except Exception as e:
                st.error(f"Error fetching ERA5 soil moisture data from GEE: {e}")

# Placeholder for additional risk metric calculations (to be added later)