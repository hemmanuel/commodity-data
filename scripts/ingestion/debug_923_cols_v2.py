import pandas as pd
import zipfile
import os

DATA_DIR = 'data/raw/eia_bulk'

def debug_923_cols():
    filename = 'f923_2014.zip'
    path = os.path.join(DATA_DIR, filename)
    
    with zipfile.ZipFile(path, 'r') as z:
        sched_files = [f for f in z.namelist() if 'Schedules_2_3_4_5' in f]
        with z.open(sched_files[0]) as f:
            # Try skiprows=5
            df = pd.read_excel(f, sheet_name='Page 1 Generation and Fuel Data', skiprows=5)
            print("Columns with skiprows=5:")
            print(df.columns.tolist()[:20])
            print("\nRow 0:")
            print(df.iloc[0].tolist()[:20])

if __name__ == "__main__":
    debug_923_cols()
