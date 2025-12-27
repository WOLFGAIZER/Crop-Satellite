An AI-Powered application that leverage GOOGLE EARTH ENGINE (GEE) satellite imagery and machine learning 
to Monitor crop health and predict agriculture Yields. This tool provides real-time insights into health 
using spectral indices like NDVI.

OVERVIEW:

Traditional crop montioring requires manual surveys which are time-consuming and expensive. This project 
automates the process by analyzing historical and real-time satellite data. By correlating signatures with 
historical yield data, the systems estimates current crop productivity for regions like India.

TECHNICAL METHODOLOGIES USED:

1) NDVI (NORMAL DIFFERENCE VEGETATION INDEX):
   We utilize NDVI as our primary feature for assessing crop health.
   - Healthy plants absorbs RED Light( For photosynthesis ) and strongly reflect near-Infrared (NIR) light.
     stressed ro sparse vegetation reflects less NIR.
         The Formula: (NIR - Red) / (NIR + Red)

  - Interpretation:

      Values > 0.6: Dense, healthy vegetation (High Yield potential).
      Values 0.2 to 0.4: Sparse vegetation or early growth stages.
      Values < 0.1: Barren rock, sand, or snow.

2) GEE (Google Earth Engine)
- Because we cannot transfer TERABYTES of geospatial data on our laptops. To make the project robust and less
  power consuming.
- Allows us to calculate  vegetative indices indices over large temporal ranges in seconds, handling the
  " BIG DATA " processing on google's servers.

FEATURES: 
a) Real-time Satellite Data Fetching: Connects dynamically to Google Earth Engine API.

b) Interactive Dashboard: Built with Streamlit for easy visualization of maps and data.

c) Yield Prediction: Uses a Random Forest/Regression model trained on historical agricultural data.

d) Visual Analytics: Displays NDVI time-series trends and correlation heatmaps.
