import pandas as pd

xlsb_path = "data/raw/baker_hughes/North America Rotary Rig Count (Jan 2000 - Mar 2024).xlsb"

try:
    print(f"Inspecting rows 8-12 of {xlsb_path}...")
    df = pd.read_excel(xlsb_path, sheet_name="US Count by Basin", header=None, engine='pyxlsb')
    print(df.iloc[8:13].to_string())
except Exception as e:
    print(f"Error: {e}")
