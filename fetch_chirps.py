import streamlit as st
import geopandas as gpd
import requests
import json

# Function to fetch CHIRPS data
def get_chirps_data(aoi_geojson):
    api_url = "https://climateservapi.servirglobal.net/api/chirps/"  
    payload = {
        "geometry": aoi_geojson,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "dataset": "chirps",
        "statistic": "mean"
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(api_url, data=json.dumps(payload), headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch CHIRPS data: {response.status_code}")
        return None

# Streamlit UI
st.title("CHIRPS Data Fetcher")

if "aoi" in st.session_state:
    aoi = st.session_state["aoi"]
    aoi_geojson = aoi.to_json()
    
    st.subheader("Fetching CHIRPS Data...")
    chirps_data = get_chirps_data(aoi_geojson)
    
    if chirps_data:
        st.success("CHIRPS data retrieved successfully!")
        st.json(chirps_data)
else:
    st.warning("Please draw an AOI on the map first.")
