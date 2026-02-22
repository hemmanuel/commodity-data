import pandas as pd

xlsx_path = "data/raw/baker_hughes/02-20-2026 North America Rig Count Report.xlsx"

try:
    print(f"Checking date range in {xlsx_path}...")
    # header=9 means row index 9 (10th row) is the header
    df = pd.read_excel(xlsx_path, sheet_name='NAM Weekly', header=9, engine='openpyxl')
    
    print("Columns:", df.columns.tolist())
    
    if 'US_PublishDate' in df.columns:
        df['US_PublishDate'] = pd.to_datetime(df['US_PublishDate'], errors='coerce')
        print(f"Min Date: {df['US_PublishDate'].min()}")
        print(f"Max Date: {df['US_PublishDate'].max()}")
        print(f"Total Rows: {len(df)}")
    else:
        print("US_PublishDate column not found.")
        
except Exception as e:
    print(f"Error: {e}")
