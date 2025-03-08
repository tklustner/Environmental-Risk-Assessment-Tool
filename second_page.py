import streamlit as st
import geemap.foliumap as geemap
from streamlit_folium import st_folium
import ee

# Ensure Earth Engine is initialized
try:
    ee.Initialize()
except Exception as e:
    st.error("Failed to initialize Google Earth Engine. Ensure authentication is set up.")

# Page layout setup
st.set_page_config(layout="wide")

# Sidebar Navigation
st.sidebar.page_link("main.py", label="Home", icon="🏠")
st.sidebar.page_link("second_page.py", label="Overlay Mapping", icon="🗺️")

# Page title
st.title("Multi-Hazard Overlay Mapping")

# Create layout with 2/3 map and 1/3 controls
col1, col2 = st.columns([2, 1])

# Initialize geemap in the larger column
with col1:
    st.subheader("Interactive Map with Hazard Layers")
    m = geemap.Map()
    map_data = st_folium(m, height=600, width=900)

# Hazard Layer Controls in the right column
with col2:
    st.subheader("Select Hazard Layers")
    show_flood = st.checkbox("Flood Risk Layer")
    show_drought = st.checkbox("Drought Risk Layer")
    show_fire = st.checkbox("Wildfire Risk Layer")

    # Placeholder logic for adding layers (expand later with GEE data)
    if show_flood:
        st.success("Flood Risk Layer enabled (data to be added)")
    if show_drought:
        st.success("Drought Risk Layer enabled (data to be added)")
    if show_fire:
        st.success("Wildfire Risk Layer enabled (data to be added)")

st.write("### Next Steps: Implement GEE layers for hazards")
