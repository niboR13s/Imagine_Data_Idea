from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import ast
import numpy as np
import json

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. In production, be specific.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "../../Blender_Generated_Data/Model"
FILES = {
    "extreme": os.path.join(DATA_DIR, "Analysis_Extreme test.xlsx"),
    "hard": os.path.join(DATA_DIR, "Analysis_Hard test.xlsx"),
}

# Caching
CACHE = {}

def load_and_clean_data(file_path):
    if file_path in CACHE and "overview" in CACHE[file_path]:
        return CACHE[file_path]["overview"]

    if not os.path.exists(file_path):
        # fallback for running directly in backend dir
        file_path = file_path.replace("../../", "../../../")
    
    if not os.path.exists(file_path):
         raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_excel(file_path)
    
    # Clean data
    if 'Sensor' in df.columns:
        df['Sensor'] = df['Sensor'].ffill()
    
    df = df.fillna(0)
    result = df.to_dict(orient="records")
    
    if file_path not in CACHE:
        CACHE[file_path] = {}
    CACHE[file_path]["overview"] = result
    return result

@app.get("/data/{dataset_type}")
async def get_data(dataset_type: str):
    if dataset_type not in FILES:
        raise HTTPException(status_code=404, detail="Dataset not found. Use 'extreme' or 'hard'.")
    
    try:
        data = load_and_clean_data(FILES[dataset_type])
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_rotation_deg(matrix_str):
    if not isinstance(matrix_str, str) or matrix_str == '0':
        return 0.0
    try:
        # matrix_str is like "[[...], [...], [...], [...]]"
        matrix = np.array(ast.literal_eval(matrix_str))
        # Top-left 3x3 is rotation
        R = matrix[:3, :3]
        # Trace of rotation matrix
        trace = np.trace(R)
        # Cosine of angle
        cos_theta = (trace - 1) / 2
        # Clamp for safety
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        theta_rad = np.arccos(cos_theta)
        return float(np.degrees(theta_rad))
    except:
        return 0.0

@app.get("/data-detailed/{dataset_type}")
async def get_detailed_data(dataset_type: str, sensor: str = None):
    if dataset_type not in FILES:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    
    try:
        file_path = FILES[dataset_type]
        
        # Check cache for Raw_Data
        if file_path in CACHE and "raw_data" in CACHE[file_path]:
            df = CACHE[file_path]["raw_data"]
        else:
            df = pd.read_excel(file_path, sheet_name="Raw_Data")
            # Pre-calculate rotation magnitude for all data and cache it
            df['Obj_Rot_Mag'] = df['Matrix_GT'].apply(calculate_rotation_deg)
            if file_path not in CACHE:
                CACHE[file_path] = {}
            CACHE[file_path]["raw_data"] = df
        
        if sensor:
             df_filtered = df[df['Sensor'] == sensor]
        else:
             df_filtered = df
        
        # We need to sample this if it's too large for the frontend
        if len(df_filtered) > 2000:
            df_sample = df_filtered.sample(2000)
        else:
            df_sample = df_filtered
            
        # Select relevant columns including RMSE
        cols = ['Sensor', 'Position', 'Sample_ID', 'Fitness', 'RMSE', 'Error_Rot_Deg', 'Error_Trans_M', 'Obj_Rot_Mag']
        # Filter columns that actually exist
        available_cols = [c for c in cols if c in df_sample.columns]
        result = df_sample[available_cols].to_dict(orient="records")
        return {"data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in data-detailed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to the Data Visualization API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
