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
        
    print(f"--- Analyzing {f} ---")
    try:
        df = pd.read_excel(f)
        print("Columns:", df.columns.tolist())
        print("First 10 Positions:", df['Position'].head(10).tolist())
        print("Random 10 Positions:", df['Position'].sample(10).tolist())
    except Exception as e:
        print(f"Error reading {f}: {e}")
