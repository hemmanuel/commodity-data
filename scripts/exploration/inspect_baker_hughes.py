import pandas as pd

file_path = "data/raw/baker_hughes/rig_count.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print(f"Sheets: {xl.sheet_names}")
    
    # Preview first sheet
    df = xl.parse(xl.sheet_names[0])
    print("\nFirst Sheet Preview:")
    print(df.head().to_string())
    
    # Look for "US Count by Basin" or similar
    if "US Count by Basin" in xl.sheet_names:
        print("\nBasin Sheet Preview:")
        df_basin = xl.parse("US Count by Basin")
        print(df_basin.head().to_string())
        
except Exception as e:
    print(f"Error reading Excel: {e}")
