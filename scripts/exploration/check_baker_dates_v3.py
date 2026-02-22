import pandas as pd

xlsx_path = "data/raw/baker_hughes/02-20-2026 North America Rig Count Report.xlsx"

try:
    print(f"Finding header row in {xlsx_path}...")
    df = pd.read_excel(xlsx_path, sheet_name='NAM Weekly', header=None, engine='openpyxl')
    
    # Find row index where 'US_PublishDate' is present
    header_idx = None
    for idx, row in df.iterrows():
        if 'US_PublishDate' in row.values:
            header_idx = idx
            break
            
    if header_idx is not None:
        print(f"Header found at index: {header_idx}")
        # Reload with correct header
        df = pd.read_excel(xlsx_path, sheet_name='NAM Weekly', header=header_idx, engine='openpyxl')
        print("Columns:", df.columns.tolist())
        
        if 'US_PublishDate' in df.columns:
            df['US_PublishDate'] = pd.to_datetime(df['US_PublishDate'], errors='coerce')
            print(f"Min Date: {df['US_PublishDate'].min()}")
            print(f"Max Date: {df['US_PublishDate'].max()}")
            print(f"Total Rows: {len(df)}")
    else:
        print("Header 'US_PublishDate' not found.")
        
except Exception as e:
    print(f"Error: {e}")
