import pandas as pd
import os

xlsb_path = "data/raw/baker_hughes/North America Rotary Rig Count (Jan 2000 - Mar 2024).xlsb"
xlsx_path = "data/raw/baker_hughes/02-20-2026 North America Rig Count Report.xlsx"

print(f"Inspecting {xlsb_path}...")
try:
    xl = pd.ExcelFile(xlsb_path, engine='pyxlsb')
    print(f"Sheets: {xl.sheet_names}")
    
    # Check for US Count by Basin
    target_sheet = "US Count by Basin"
    if target_sheet in xl.sheet_names:
        print(f"\nPreview of '{target_sheet}':")
        df = pd.read_excel(xlsb_path, sheet_name=target_sheet, engine='pyxlsb')
        print(df.head(10).to_string())
    else:
        print(f"\n'{target_sheet}' not found. Previewing first sheet:")
        df = pd.read_excel(xlsb_path, sheet_name=0, engine='pyxlsb')
        print(df.head(10).to_string())
        
except Exception as e:
    print(f"Error reading xlsb: {e}")

print(f"\nInspecting {xlsx_path}...")
try:
    xl = pd.ExcelFile(xlsx_path, engine='openpyxl')
    print(f"Sheets: {xl.sheet_names}")
    
    # Preview first sheet
    df = pd.read_excel(xlsx_path, sheet_name=0, engine='openpyxl')
    print("\nFirst Sheet Preview:")
    print(df.head(10).to_string())
    
except Exception as e:
    print(f"Error reading xlsx: {e}")
