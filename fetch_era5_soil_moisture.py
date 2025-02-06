import streamlit as st
import ee
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Authenticate and initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    st.error("Failed to initialize Google Earth Engine. Ensure authentication is set up.")

# Function to fetch ERA5-Land Soil Moisture data from GEE
def get_era5_soil_moisture(aoi):
    collection = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    
    # Use correct soil moisture band for top layer
    soil_moisture_band = "volumetric_soil_water_layer_1"
    
    # Reduce to mean over AOI
    def reduce_region(image):
        mean = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=5000,
            bestEffort=True
        )
        return image.set("mean_soil_moisture", mean.get(soil_moisture_band))
    
    start_date = "2024-01-01"
    end_date = datetime.today().strftime('%Y-%m-%d')
    
    filtered = collection.filterDate(start_date, end_date).map(reduce_region)
    time_series = filtered.aggregate_array("mean_soil_moisture").getInfo()
    dates = filtered.aggregate_array("system:time_start").map(lambda t: ee.Date(t).format("YYYY-MM-dd")).getInfo()
    
    return pd.DataFrame({"Date": pd.to_datetime(dates), "Soil Moisture": time_series})

# Streamlit UI
st.title("ERA5 Soil Moisture Data Fetcher")

if "aoi" in st.session_state:
    aoi = st.session_state["aoi"]
    
    st.caption("Fetching ERA5 Soil Moisture Data...")
    try:
        df = get_era5_soil_moisture(aoi)
        if not df.empty:
            st.success("ERA5 soil moisture data retrieved successfully!")
            
            # Plot ERA5 soil moisture data
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df['Date'], df['Soil Moisture'], marker='o', linestyle='-', color='b')
            ax.set_title("ERA5 Soil Moisture Data (Jan 2024 - Present)", fontsize=14)
            ax.set_xlabel("Date", fontsize=12)
            ax.set_ylabel("Soil Moisture (m³/m³)", fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.6)
            plt.xticks(rotation=45)
            
            st.pyplot(fig)
        else:
            st.error("No soil moisture data retrieved for the AOI.")
    except Exception as e:
        st.error(f"Error fetching ERA5 soil moisture data from GEE: {e}")
else:
    st.warning("Please draw an AOI on the map first.")