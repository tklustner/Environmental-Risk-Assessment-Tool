# 🌍 Environmental Risk Assessment Dashboard

This Streamlit-based tool enables users to assess environmental risks across any selected area of interest (AOI) of up to \~10,000 km². It integrates real-time data from Google Earth Engine and automates NDVI analysis, making remote sensing insights accessible to non-specialist users. With data download functionality and a lightweight design, the tool is well-suited for use in low-connectivity or disaster-prone settings. Its modular structure also supports the integration of additional metrics and predictive models as user needs evolve.

## 🚀 Features

- **Interactive AOI selection** (Geemap-based map with drawing tools)
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

![Risk App Demo](risk_app_demo.gif)

## 📝 Notes

- AOIs over 10,000 km² may result in slow data loads or timeouts.
- All data is aggregated using mean values over the AOI polygon.
- Built for rapid exploratory analysis; not intended for high-resolution modeling.

---

© 2025 • Built with Streamlit + Geemap + Earth Engine
