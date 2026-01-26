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

@app.get("/scan-points/{dataset_type}/{sensor}/{setup}/{filename}")
async def get_scan_points(dataset_type: str, sensor: str, setup: str, filename: str):
    if dataset_type not in FILES:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    
    # Construct path: Blender_Generated_Data/Model/{Hard test}/{cam_d435}/{setup_front}/{scan_0000.csv}
    # dataset_type is 'hard' or 'extreme', but dir names are 'Hard test' and 'Extreme test'
    dir_map = {"hard": "Hard test", "extreme": "Extreme test"}
    dir_name = dir_map.get(dataset_type, dataset_type)
    
    file_path = os.path.join(DATA_DIR, dir_name, sensor, setup, filename)
    
    if not os.path.exists(file_path):
         # Try fallback
         file_path_fallback = file_path.replace("../../", "../../../")
         if os.path.exists(file_path_fallback):
             file_path = file_path_fallback
         else:
             raise HTTPException(status_code=404, detail=f"Scan file not found: {file_path}")
             
    try:
        df = pd.read_csv(file_path)
        # Assuming CSV has X,Y,Z columns
        points = df[['X', 'Y', 'Z']].values.tolist()
        return {"points": points}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ground-truth-detail/{dataset_type}/{sensor}/{setup}/{sample_id}")
async def get_gt_detail(dataset_type: str, sensor: str, setup: str, sample_id: int):
    if dataset_type not in FILES:
        raise HTTPException(status_code=404, detail="Dataset not found.")
        
    dir_map = {"hard": "Hard test", "extreme": "Extreme test"}
    dir_name = dir_map.get(dataset_type, dataset_type)
    gt_path = os.path.join(DATA_DIR, dir_name, sensor, setup, "ground_truth.csv")
    
    if not os.path.exists(gt_path):
        gt_path = gt_path.replace("../../", "../../../")
        
    if not os.path.exists(gt_path):
        raise HTTPException(status_code=404, detail="Ground truth file not found.")
        
    try:
        # 1. Get raw transformation from CSV
        df_csv = pd.read_csv(gt_path, comment='#')
        row_csv = df_csv[df_csv['sample_id'] == sample_id]
        if row_csv.empty:
            raise HTTPException(status_code=404, detail="Sample ID not found in ground truth CSV.")
            
        result = row_csv.to_dict(orient="records")[0]

        # 2. Get performance metrics from Excel
        excel_path = FILES[dataset_type]
        if excel_path in CACHE and "raw_data" in CACHE[excel_path]:
            df_excel = CACHE[excel_path]["raw_data"]
        else:
            df_excel = pd.read_excel(excel_path, sheet_name="Raw_Data")
            if excel_path not in CACHE:
                CACHE[excel_path] = {}
            CACHE[excel_path]["raw_data"] = df_excel

        # Column names in Excel: Sensor, Position, Sample_ID, Fitness, RMSE
        # Position in main.py is "setup" in the directory structure
        excel_row = df_excel[
            (df_excel['Sensor'] == sensor) & 
            (df_excel['Position'] == setup) & 
            (df_excel['Sample_ID'] == sample_id)
        ]
        
        if not excel_row.empty:
            metrics = excel_row.iloc[0].to_dict()
            result.update({
                "Fitness": metrics.get("Fitness", 0),
                "RMSE": metrics.get("RMSE", 0),
                "Error_Rot_Deg": metrics.get("Error_Rot_Deg", 0),
                "Error_Trans_M": metrics.get("Error_Trans_M", 0),
                "Time_Total": metrics.get("Time_Total", 0)
            })

        return {"data": result}
    except Exception as e:
        print(f"Error in gt-detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to the Data Visualization API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
