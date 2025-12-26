import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib
import plotly.express as px
from datetime import datetime

# Custom Modules
from src.train import run_training
from src.satellite_utils import initialize_satellite_connection, get_satellite_features
from src.config import STATE_COORDINATES, CROPS, SEASONS

initialize_satellite_connection()

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SatYield AI Pro",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING (Fixes Dark Mode Issues) ---
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    /* Force metrics to look good in both Light/Dark mode */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE SETUP (The Fix for NameError) ---
# We initialize these variables so the app doesn't crash on load
if 'predicted' not in st.session_state:
    st.session_state.predicted = False
    st.session_state.yield_val = 0
    st.session_state.production = 0
    st.session_state.gross_revenue = 0
    st.session_state.ndvi = 0
    st.session_state.rainfall = 0

# --- 4. SIDEBAR INPUTS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2518/2518048.png", width=80)
    st.title("🚜 Farm Config")
    st.markdown("---")
    
    state = st.selectbox("Region", list(STATE_COORDINATES.keys()))
    crop = st.selectbox("Crop", CROPS)
    season = st.selectbox("Season", SEASONS)
    
    st.markdown("### Field Details")
    area = st.number_input("Field Area (Ha)", 0.1, 500.0, 2.5)
    fertilizer = st.slider("Fertilizer (kg/Ha)", 0, 500, 150)
    pesticide = st.slider("Pesticide (kg/Ha)", 0, 100, 5)

# --- 5. MAIN APP LOGIC ---
st.title("🛰️ SatYield: Enterprise Crop Forecasting")
st.markdown(f"**Region:** {state} | **Season:** {season} 2024")

tab1, tab2, tab3 = st.tabs(["📊 Forecast", "🛰️ Satellite Data", "⚙️ Model Logic"])

# === TAB 1: PREDICTION ===
with tab1:
    col_main, col_fin = st.columns([2, 1])
    
    with col_main:
        st.subheader("Yield Prediction")
        
        # Always fetch satellite data so the map works
        lat, lon = STATE_COORDINATES[state]
        with st.spinner("📡 Syncing with Satellite..."):
            sat_data = get_satellite_features(lat, lon)
            
        if st.button("🚀 Run Forecast", type="primary", use_container_width=True):
            # 1. Load/Train Model
            model_path = "models/crop_model.pkl"
            if os.path.exists(model_path):
                payload = joblib.load(model_path)
                pipeline = payload['pipeline']
            else:
                st.warning("Calibrating model...")
                payload = run_training()
                pipeline = payload['pipeline']
            
            # 2. Prepare Data
            input_df = pd.DataFrame([{
                'State': state, 'Crop': crop, 'Season': season,
                'Area': area, 'Annual_Rainfall': sat_data['rainfall'],
                'Fertilizer': fertilizer, 'Pesticide': pesticide,
                'NDVI': sat_data['ndvi']
            }])
            
            # 3. Predict
            pred_yield = pipeline.predict(input_df)[0]
            total_prod = pred_yield * area
            
            # 4. Calculate Financials
            # (Approx MSP Prices for demo)
            price_map = {'Rice': 2200, 'Wheat': 2125, 'Cotton': 6600, 'Sugarcane': 315, 'Maize': 2090}
            price = price_map.get(crop, 1500)
            revenue = total_prod * price
            
            # 5. SAVE TO SESSION STATE (Crucial Step)
            st.session_state.predicted = True
            st.session_state.yield_val = pred_yield
            st.session_state.production = total_prod
            st.session_state.gross_revenue = revenue
            st.session_state.ndvi = sat_data['ndvi']
            st.session_state.rainfall = sat_data['rainfall']

        # --- DISPLAY RESULTS (Only if predicted) ---
        if st.session_state.predicted:
            rev_lakhs = st.session_state.gross_revenue / 100000
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Predicted Yield", f"{st.session_state.yield_val:.2f} Q/Ha")
            m2.metric("Total Harvest", f"{st.session_state.production:.1f} Quintals")
            m3.metric("Est. Revenue", f"₹{rev_lakhs:.2f} Lakhs")
            
            # Download Report
            report = f"""SatYield Report\nLocation: {state}\nYield: {st.session_state.yield_val:.2f} Q/Ha\nRevenue: Rs {rev_lakhs:.2f} Lakhs"""
            st.download_button("📄 Download Report", report, file_name="SatYield_Report.txt")

    with col_fin:
        st.info("💡 **Financials**")
        
        # Only show chart IF we have a prediction
        if st.session_state.predicted:
            rev = st.session_state.gross_revenue
            cost = rev * 0.4  # Assume 40% cost
            profit = rev * 0.6 # Assume 60% profit
            
            df_fin = pd.DataFrame({
                'Type': ['Cost', 'Profit'],
                'Amount': [cost, profit]
            })
            
            fig = px.pie(df_fin, values='Amount', names='Type', hole=0.5, color_discrete_sequence=['#ff9999', '#66b3ff'])
            fig.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Run forecast to see financial breakdown.")

# === TAB 2: SATELLITE ===
with tab2:
    st.subheader("Live Satellite Feed")
    c1, c2 = st.columns([3, 1])
    lat, lon = STATE_COORDINATES[state]
    
    with c1:
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=6)
        
    with c2:
        # Use session state data if available, else live fetch
        ndvi_val = st.session_state.ndvi if st.session_state.predicted else sat_data['ndvi']
        rain_val = st.session_state.rainfall if st.session_state.predicted else sat_data['rainfall']
        
        st.metric("NDVI (Health)", f"{ndvi_val:.2f}")
        st.progress(ndvi_val)
        st.metric("Rainfall", f"{rain_val:.0f} mm")

# === TAB 3: EXPLAINABILITY ===
with tab3:
    st.subheader("Model Insights")
    model_path = "models/crop_model.pkl"
    
    if os.path.exists(model_path):
        payload = joblib.load(model_path)
        
        # Extract features
        imp = payload['feature_importances']
        names = payload['feature_names']
        df_imp = pd.DataFrame({'Feature': names, 'Importance': imp}).sort_values('Importance', ascending=True).tail(8)
        
        fig = px.bar(df_imp, x='Importance', y='Feature', orientation='h', title="Top Yield Drivers")
        st.plotly_chart(fig)
    else:
        st.info("Train model to see insights.")