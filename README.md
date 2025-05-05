# 🌍 Environmental Risk Assessment Dashboard

This Streamlit-based tool allows users to explore environmental risks for any selected area of interest (AOI) under 10,000 km². It integrates live Earth Engine data sources to monitor rainfall, soil moisture, and vegetation health, and automatically calculates a simple environmental risk score.

## 🚀 Features

- **Interactive AOI selection** (Leaflet-based map with drawing tools)
- **Time series plots** of:
  - 🌧️ CHIRPS Rainfall (Jan 2024–Present)
  - 🌱 ERA5 Soil Moisture
  - 🌿 NDVI Vegetation Health
- **Environmental Risk Score** using simple thresholds
- **Downloadable CSV** of merged time series data

## 📊 Risk Scoring Criteria

| Metric           | Threshold               | Condition Considered Risky |
|------------------|-------------------------|-----------------------------|
| NDVI             | Mean < 0.3              | Vegetation stress           |
| Rainfall         | Mean < 10 mm            | Low rainfall                |
| Soil Moisture    | Mean < 0.15 m³/m³       | Dry conditions              |

Final risk score is:
- 🟢 Low Risk (0 flags)
- 🟡 Moderate Risk (1 flag)
- 🔴 High Risk (2+ flags)

## 🧰 Requirements

- Python 3.9+
- Google Earth Engine Python API
- Streamlit
- `geemap`, `pandas`, `matplotlib`, `streamlit_folium`

Install dependencies via:

```bash
pip install -r requirements.txt
```

## 🔐 Authentication

You must authenticate Google Earth Engine before use:

```bash
earthengine authenticate
```

## 📂 Project Structure

```
├── main.py
├── README.md
├── fetch_era5_soil_moisture.py
├── fetch_ndvi.py
├── requirements.txt
```

## 📸 Example Output

![Example Output](Screenshot-2025-05-05-at-3.04.50-PM.png)

## 📝 Notes

- AOIs over 10,000 km² may result in slow data loads or timeouts.
- All data is aggregated using mean values over the AOI polygon.
- Built for rapid exploratory analysis; not intended for high-resolution modeling.

---

© 2025 • Built with Streamlit + Earth Engine
