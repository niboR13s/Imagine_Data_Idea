import pandas as pd
import os

# Paths relative to project root
files = [
    'Blender_Generated_Data/Model/Analysis_Extreme test.xlsx',
    'Blender_Generated_Data/Model/Analysis_Hard test.xlsx'
]

for f in files:
    # Adjust path if running from scripts directory
    if not os.path.exists(f) and os.path.exists(os.path.join('..', f)):
        f = os.path.join('..', f)
        
    print(f"--- Detailed Analysis of {f} ---")
    try:
        xl = pd.ExcelFile(f)
        print("Sheets:", xl.sheet_names)
        for sheet in xl.sheet_names:
            df = pd.read_excel(f, sheet_name=sheet)
            print(f"Sheet '{sheet}' Shape:", df.shape)
            print("Columns:", df.columns.tolist())
            # Check for rotation data
            possible_rotation_cols = [col for col in df.columns if 'rot' in col.lower() or 'angle' in col.lower()]
            print("Possible rotation columns:", possible_rotation_cols)
            if df.shape[0] > 100:
                 print("First 5 rows of long sheet:")
                 print(df.head())
    except Exception as e:
        print(f"Error reading {f}: {e}")
