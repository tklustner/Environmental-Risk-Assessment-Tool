import streamlit as st
st.set_page_config(layout="wide")  

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
from fetch_ndvi import get_ndvi_data  # Add import for NDVI function

# Authenticate EE 
try:
    ee.Initialize()
except Exception as e:
    st.error("Failed to initialize Google Earth Engine. Ensure authentication is set up.")

# 3 col view
col1, col2, col3 = st.columns([1, 2, 1])  

with col1:
    st.subheader("Risk Metric 1 - CHIRPS Data")
    placeholder_chart1 = st.empty()
    # Sidebar Navigation
st.sidebar.page_link("main.py", label="Home", icon="🏠")
#st.sidebar.page_link("second_page.py", label="Overlay Mapping", icon="🗺️")

with col3:
    st.subheader("Vegetation Health (NDVI)")
    placeholder_chart2 = st.empty()

# Place map in middle col
with col2:
    st.subheader("Select Area of Interest")
    m = geemap.Map()
    map_data = st_folium(m, height=500, width=700)

# Fetch CHIRPS
def get_chirps_data(aoi):
    collection = ee.ImageCollection("UCSB-CHG/CHIRPS/PENTAD")
    
    # Reducer for mean over AOI
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

# Process drawn
if map_data and 'last_active_drawing' in map_data:
    drawn_features = map_data["all_drawings"]
    if drawn_features:
        geojson_data = drawn_features[-1]  # Get the latest drawing
        aoi = ee.Geometry.Polygon(geojson_data["geometry"]["coordinates"])  # Convert AOI to EE format
        st.session_state["aoi"] = aoi  # Store AOI in session state
        
        # Get AOI area in km^2
        aoi_area = aoi.area().divide(1e6).getInfo()
        
        # Display AOI
        st.success("AOI captured successfully!")
        st.markdown(f"### Area: {aoi_area:.2f} km²")

        # Fetch CHIRPS Data and display it in col1
        with col1:
            st.caption("Fetching CHIRPS Data from GEE...")
            try:
                df = get_chirps_data(aoi)
                if not df.empty:
                    
                    # Plot CHIRPS rainfall data 
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

        # Fetch NDVI Data and display it in col3
        with col3:
            st.caption("Fetching NDVI Data...")
            try:
                df_ndvi = get_ndvi_data(aoi)
                if not df_ndvi.empty:
                    # Plot NDVI data  
                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.plot(df_ndvi['Date'], df_ndvi['NDVI'], marker='o', linestyle='-', color='g')
                    ax.set_title("Vegetation Health Index (NDVI)", fontsize=14)
                    ax.set_xlabel("Date", fontsize=12)
                    ax.set_ylabel("NDVI", fontsize=12)
                    ax.grid(True, linestyle='--', alpha=0.6)
                    ax.set_ylim(-1, 1)
                    
                    # Add color bands for NDVI interpretation
                    ax.axhspan(-1, 0, alpha=0.2, color='brown', label='Water/Non-vegetation')
                    ax.axhspan(0, 0.2, alpha=0.2, color='yellow', label='Bare Soil')
                    ax.axhspan(0.2, 0.4, alpha=0.2, color='yellowgreen', label='Sparse Vegetation')
                    ax.axhspan(0.4, 1, alpha=0.2, color='green', label='Dense Vegetation')
                    
                    plt.xticks(rotation=45)
                    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                    
                    # Display NDVI statistics
                    st.caption("NDVI Statistics")
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Average NDVI", f"{df_ndvi['NDVI'].mean():.2f}")
                    with cols[1]:
                        st.metric("Max NDVI", f"{df_ndvi['NDVI'].max():.2f}")
                    with cols[2]:
                        st.metric("Min NDVI", f"{df_ndvi['NDVI'].min():.2f}")
                else:
                    st.error("No NDVI data retrieved for the AOI.")
            except Exception as e:
                st.error(f"Error fetching NDVI data: {e}")

        # Add ERA5 Soil Moisture visualization
        with col1:
            st.markdown("---")  # Add a visual separator
            st.subheader("Soil Moisture")
            st.caption("Fetching ERA5 Soil Moisture Data...")
            try:
                df_soil = get_era5_soil_moisture(aoi)
                if not df_soil.empty:
                    
                    # Plot ERA5 soil moisture data 
                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.plot(df_soil['Date'], df_soil['Soil Moisture'], 
                           marker='o', linestyle='-', color='blue')
                    ax.set_title("ERA5 Soil Moisture", fontsize=14)
                    ax.set_xlabel("Date", fontsize=12)
                    ax.set_ylabel("Soil Moisture (m³/m³)", fontsize=12)
                    ax.grid(True, linestyle='--', alpha=0.6)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                    
                    # Show soil moisture stats
                    st.caption("Soil Moisture Statistics")
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Average", f"{df_soil['Soil Moisture'].mean():.3f} m³/m³")
                    with cols[1]:
                        st.metric("Max", f"{df_soil['Soil Moisture'].max():.3f} m³/m³")
                    with cols[2]:
                        st.metric("Min", f"{df_soil['Soil Moisture'].min():.3f} m³/m³")
                else:
                    st.error("No soil moisture data retrieved for the AOI.")
            except Exception as e:
                st.error(f"Error fetching ERA5 soil moisture data: {e}")


# Placeholder for additional risk metric calculations (to be added later)



