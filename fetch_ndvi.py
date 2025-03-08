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
    """Fetch NDVI data from Sentinel-2 imagery"""
    # Function to mask clouds and add NDVI
    def processImage(image):
        # Get cloud probability
        clouds = image.select('MSK_CLDPRB')
        # Make a mask from cloud probability
        cloudMask = clouds.lt(20)  # Less than 20% cloud probability
        
        # Apply cloud mask and calculate NDVI
        masked = image.updateMask(cloudMask).divide(10000)
        ndvi = masked.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # Get the date
        date = ee.Date(image.get('system:time_start'))
        
        # Calculate mean NDVI for the AOI
        mean = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10,
            maxPixels=1e9
        )
        
        # Return a feature with date and NDVI value
        return ee.Feature(None, {
            'date': date.format('YYYY-MM-dd'),
            'NDVI': mean.get('NDVI')
        })

    try:
        # Get Sentinel-2 surface reflectance data
        start_date = '2024-01-01'
        end_date = datetime.today().strftime('%Y-%m-%d')
        
        collection = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(start_date, end_date) \
            .filterBounds(aoi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        
        # Process the collection
        features = collection.map(processImage).getInfo()['features']
        
        # Filter out any null values and create DataFrame
        valid_features = [
            f['properties'] for f in features 
            if f['properties']['NDVI'] is not None and f['properties']['date'] is not None
        ]
        
        if not valid_features:
            return pd.DataFrame()  # Return empty DataFrame if no valid data
        
        df = pd.DataFrame(valid_features)
        df['Date'] = pd.to_datetime(df['date'])
        df = df[['Date', 'NDVI']].sort_values('Date')
        
        return df.dropna()

    except Exception as e:
        print(f"Error processing NDVI data: {str(e)}")
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
