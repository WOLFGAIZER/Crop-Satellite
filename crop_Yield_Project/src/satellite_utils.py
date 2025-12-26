import ee
from src.config import GEE_PROJECT_ID

def initialize_satellite_connection():
    """Authenticates and initializes Google Earth Engine."""
    try:
        # Try utilizing existing credentials
        ee.Initialize(project=GEE_PROJECT_ID)
    except Exception:
        try:
            # Trigger authentication flow if needed
            print("Authenticating Google Earth Engine...")
            ee.Authenticate()
            ee.Initialize(project=GEE_PROJECT_ID)
        except Exception as e:
            print(f"⚠️ GEE Init Failed: {e}. Using mock data mode.")

def get_satellite_features(lat, lon, start_date='2023-01-01', end_date='2023-12-31'):
    """
    Fetches Rainfall (CHIRPS) and NDVI (MODIS) data.
    Returns default values if GEE is not authenticated.
    """
    try:
        point = ee.Geometry.Point([lon, lat])
        
        # 1. Fetch Rainfall (CHIRPS Daily)
        rain_dataset = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD') \
                        .filterDate(start_date, end_date) \
                        .filterBounds(point)
        
        total_rainfall = rain_dataset.sum().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=5000
        ).get('precipitation')

        # 2. Fetch NDVI (Vegetation Health - MODIS)
        ndvi_dataset = ee.ImageCollection('MODIS/006/MOD13Q1') \
                        .filterDate(start_date, end_date) \
                        .filterBounds(point)
        
        mean_ndvi = ndvi_dataset.mean().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=250
        ).get('NDVI')

        # Execute Requests
        rain_val = total_rainfall.getInfo()
        ndvi_val = mean_ndvi.getInfo()
        
        # MODIS NDVI is scaled by 0.0001
        final_ndvi = (ndvi_val * 0.0001) if ndvi_val is not None else 0.55
        final_rain = rain_val if rain_val is not None else 1200.0
        
        return {'rainfall': final_rain, 'ndvi': final_ndvi}

    except Exception as e:
        print(f"⚠️ Satellite Fetch Error: {e}. Returning averages.")
        return {'rainfall': 1200.0, 'ndvi': 0.55}