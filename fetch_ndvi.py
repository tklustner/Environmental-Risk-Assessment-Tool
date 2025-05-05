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

def get_ndvi_data(aoi):
    """Try Sentinel-2 NDVI with cloud masking; fallback to MODIS if empty."""
    import ee
    import pandas as pd
    from datetime import datetime

    def sentinel_ndvi(aoi):
        def process_image(image):
            clouds = image.select('MSK_CLDPRB')
            cloud_mask = clouds.lt(20)
            masked = image.updateMask(cloud_mask).divide(10000)
            ndvi = masked.normalizedDifference(['B8', 'B4']).rename('NDVI')

            mean_ndvi = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=10,
                maxPixels=1e9
            )

            return ee.Feature(None, {
                'NDVI': mean_ndvi.get('NDVI'),
                'Date': ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
            })

        start_date = '2024-01-01'
        end_date = datetime.today().strftime('%Y-%m-%d')

        collection = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(start_date, end_date) \
            .filterBounds(aoi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

        features = collection.map(process_image)
        feature_collection = ee.FeatureCollection(features)
        props = feature_collection.getInfo()["features"]

        df = pd.DataFrame([f["properties"] for f in props if f["properties"].get("NDVI") is not None])
        if df.empty:
            return pd.DataFrame()

        df['Date'] = pd.to_datetime(df['Date'])
        return df[['Date', 'NDVI']].dropna().sort_values('Date')

    def modis_ndvi(aoi):
        collection = ee.ImageCollection("MODIS/061/MOD13Q1") \
            .select("NDVI") \
            .filterDate("2024-01-01", datetime.today().strftime('%Y-%m-%d')) \
            .filterBounds(aoi)

        def process(image):
            mean = image.reduceRegion(
                ee.Reducer.mean(), aoi, 250, bestEffort=True)
            return ee.Feature(None, {
                "NDVI": ee.Number(mean.get("NDVI")).multiply(0.0001),
                "Date": ee.Date(image.get("system:time_start")).format("YYYY-MM-dd")
            })

        features = collection.map(process_image)
        feature_collection = ee.FeatureCollection(features)
        props = feature_collection.getInfo()["features"]

        df = pd.DataFrame([f["properties"] for f in props if f["properties"].get("NDVI") is not None])
        if df.empty:
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(df["Date"])
        return df[["Date", "NDVI"]].dropna().sort_values("Date")
    
    try:
        df = sentinel_ndvi(aoi)
        if not df.empty:
            print("✅ Using Sentinel-2 NDVI")
            return df
        print("⚠️ Sentinel-2 NDVI empty. Falling back to MODIS.")

        df = modis_ndvi(aoi)
        if not df.empty:
            print("✅ Using MODIS NDVI")
            return df
        print("❌ MODIS NDVI also returned empty.")
        return pd.DataFrame()

    except Exception as e:
        print(f"NDVI fetch error: {e}")
        return pd.DataFrame()

   

# Streamlit UI
st.title("Vegetation Health Monitor (NDVI)")

if "aoi" in st.session_state:
    aoi = st.session_state["aoi"]
    
    st.caption("Fetching NDVI Data...")
    try:
        df = get_ndvi_data(aoi)
        if not df.empty:
            st.success("NDVI data retrieved successfully!")
            
            # Plot NDVI data
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df['Date'], df['NDVI'], marker='o', linestyle='-', color='g')
            ax.set_title("Vegetation Health Index (NDVI) Trend", fontsize=14)
            ax.set_xlabel("Date", fontsize=12)
            ax.set_ylabel("NDVI", fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.set_ylim(-1, 1)  # NDVI ranges from -1 to 1
            plt.xticks(rotation=45)
            
            # Add a horizontal line at NDVI = 0
            ax.axhline(y=0, color='r', linestyle='--', alpha=0.3)
            
            # Add color bands for NDVI interpretation
            ax.axhspan(-1, 0, alpha=0.2, color='brown', label='Water/Non-vegetation')
            ax.axhspan(0, 0.2, alpha=0.2, color='yellow', label='Bare Soil')
            ax.axhspan(0.2, 0.4, alpha=0.2, color='yellowgreen', label='Sparse Vegetation')
            ax.axhspan(0.4, 1, alpha=0.2, color='green', label='Dense Vegetation')
            
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # Display statistics
            st.subheader("Vegetation Health Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average NDVI", f"{df['NDVI'].mean():.2f}")
            with col2:
                st.metric("Max NDVI", f"{df['NDVI'].max():.2f}")
            with col3:
                st.metric("Min NDVI", f"{df['NDVI'].min():.2f}")
            
            # Export data option
            st.download_button(
                label="Download NDVI Data",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='ndvi_data.csv',
                mime='text/csv'
            )
        else:
            st.error("No NDVI data retrieved for the AOI.")
    except Exception as e:
        st.error(f"Error fetching NDVI data: {e}")
else:
    st.warning("Please draw an AOI on the map first.")
