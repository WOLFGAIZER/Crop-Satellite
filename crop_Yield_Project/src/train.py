import pandas as pd
import os
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

def run_training():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, '..', 'data', 'crop_yield.csv')
    model_save_path = os.path.join(current_dir, '..', 'models', 'crop_model.pkl')

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"❌ Data file not found at {csv_path}. Run generate_data.py first.")

    print("⏳ Loading dataset...")
    df = pd.read_csv(csv_path).dropna()

    # Define Features
    # We dynamically check columns to be safe
    feature_cols = ['State', 'Crop', 'Season', 'Area', 'Annual_Rainfall', 'Fertilizer', 'Pesticide', 'NDVI']
    # Ensure only existing columns are used
    feature_cols = [c for c in feature_cols if c in df.columns]
    
    X = df[feature_cols]
    y = df['Yield']

    # Split Categorical vs Numerical
    categorical_features = ['State', 'Crop', 'Season']
    numerical_features = [c for c in feature_cols if c not in categorical_features]

    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Model: XGBoost Regressor
    model = XGBRegressor(
        n_estimators=200, 
        learning_rate=0.05, 
        max_depth=5, 
        random_state=42
    )
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])

    print("🚀 Training XGBoost Model...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    predictions = pipeline.predict(X_test)
    r2 = r2_score(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    
    print(f"✅ Training Complete.")
    print(f"   - R2 Score: {r2:.4f}")
    print(f"   - RMSE: {rmse:.2f}")

    # Extract Feature Importance for Dashboard
    try:
        ohe_features = pipeline.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out()
        all_features = numerical_features + list(ohe_features)
        importances = pipeline.named_steps['regressor'].feature_importances_
    except Exception as e:
        print(f"⚠️ Could not extract feature importance: {e}")
        all_features = []
        importances = []

    # Save Payload
    model_data = {
        'pipeline': pipeline,
        'score': r2,
        'rmse': rmse,
        'feature_names': all_features,
        'feature_importances': importances
    }

    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    joblib.dump(model_data, model_save_path)
    print(f"💾 Model saved to {model_save_path}")
    
    return model_data

if __name__ == "__main__":
    run_training()