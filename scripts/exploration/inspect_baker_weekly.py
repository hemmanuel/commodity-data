import pandas as pd

xlsx_path = "data/raw/baker_hughes/02-20-2026 North America Rig Count Report.xlsx"

try:
    print(f"Inspecting 'NAM Weekly' sheet in {xlsx_path}...")
    df = pd.read_excel(xlsx_path, sheet_name='NAM Weekly', engine='openpyxl')
    print(df.head(20).to_string())
except Exception as e:
    print(f"Error: {e}")
