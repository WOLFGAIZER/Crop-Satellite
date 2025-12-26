from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os
from src.satellite_utils import get_satellite_features # Your existing util
from src.config import STATE_COORDINATES

app = FastAPI(title="SatYield Inference Engine")

# 1. Load Model Once at Startup (Efficient)
MODEL_PATH = "models/crop_model.pkl"
if os.path.exists(MODEL_PATH):
    payload = joblib.load(MODEL_PATH)
    pipeline = payload['pipeline']
else:
    pipeline = None # Handle gracefully

# 2. Define Input Schema (Data Validation)
class CropInput(BaseModel):
    state: str
    crop: str
    season: str
    area: float
    fertilizer: float
    pesticide: float

@app.get("/")
def health_check():
    return {"status": "active", "model_loaded": pipeline is not None}

@app.post("/predict")
def predict_yield(data: CropInput):
    if not pipeline:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # 1. Get Satellite Data (Backend Logic)
    if data.state in STATE_COORDINATES:
        lat, lon = STATE_COORDINATES[data.state]
        # In production, we pass credentials via ENV variables
        sat_data = get_satellite_features(lat, lon) 
    else:
        sat_data = {'rainfall': 1000.0, 'ndvi': 0.5}

    # 2. Prepare DataFrame
    input_df = pd.DataFrame([{
        'State': data.state,
        'Crop': data.crop,
        'Season': data.season,
        'Area': data.area,
        'Annual_Rainfall': sat_data['rainfall'],
        'Fertilizer': data.fertilizer,
        'Pesticide': data.pesticide,
        'NDVI': sat_data['ndvi']
    }])

    # 3. Predict
    prediction = pipeline.predict(input_df)[0]
    
    return {
        "yield": float(prediction),
        "production": float(prediction * data.area),
        "satellite_data": sat_data
    }