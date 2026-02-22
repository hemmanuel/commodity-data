import pandas as pd
import duckdb
import os
import numpy as np

# Setup
db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

# Paths
xlsb_path = "data/raw/baker_hughes/North America Rotary Rig Count (Jan 2000 - Mar 2024).xlsb"
xlsx_path = "data/raw/baker_hughes/02-20-2026 North America Rig Count Report.xlsx"

# Create Table
con.execute("""
    CREATE TABLE IF NOT EXISTS fact_baker_hughes_rig_count (
        report_date DATE,
        basin VARCHAR,
        total_rigs INTEGER,
        oil_rigs INTEGER,
        gas_rigs INTEGER,
        misc_rigs INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
con.execute("DELETE FROM fact_baker_hughes_rig_count")

print("## Processing Historical Data (.xlsb)...")
try:
    # Read the sheet "US Count by Basin"
    # We need to read header rows separately or just read all and parse
    # Row 8 (index 8) has Basin names. Row 9 (index 9) has Oil/Gas/Misc/Total
    # Data starts at row 10 (index 10)
    
    df_raw = pd.read_excel(xlsb_path, sheet_name="US Count by Basin", header=None, engine='pyxlsb')
    
    # Extract Basin Names from Row 8
    # Basin names are merged or sparse. e.g. "Ardmore Woodford" at col 1, then NaNs until col 5 "Arkoma Woodford"
    # Col 0 is Date.
    
    basin_row = df_raw.iloc[9]
    type_row = df_raw.iloc[10]
    data_start_idx = 11
    
    # Identify Basin columns
    # Basins start at col 1. Each basin has 4 columns: Oil, Gas, Misc, Total
    # We can iterate from col 1 to end in steps of 4
    
    frames = []
    
    # The first column is Date
    dates = df_raw.iloc[data_start_idx:, 0]
    # Convert serial dates if necessary, or check format
    # pyxlsb might return serial dates or datetime objects
    
    # Check first date value to see type
    first_date = dates.iloc[0]
    print(f"First date value in xlsb: {first_date} (Type: {type(first_date)})")
    
    # If it's a number (serial date), convert. If it's already datetime, good.
    # Excel serial date: days since 1899-12-30
    if isinstance(first_date, (int, float)):
        dates = pd.to_numeric(dates, errors='coerce')
        dates = pd.to_datetime(dates, unit='D', origin='1899-12-30')
    else:
        dates = pd.to_datetime(dates)

    num_cols = df_raw.shape[1]
    
    for i in range(1, num_cols, 4):
        if i+3 >= num_cols:
            break
            
        basin_name = basin_row.iloc[i]
        if pd.isna(basin_name):
            continue
            
        # Check if sub-columns match expected pattern (Oil, Gas, Misc, Total)
        # type_row.iloc[i] should be 'Oil'
        
        chunk = df_raw.iloc[data_start_idx:, i:i+4].copy()
        chunk.columns = ['oil_rigs', 'gas_rigs', 'misc_rigs', 'total_rigs']
        chunk['report_date'] = dates
        chunk['basin'] = basin_name
        
        # Filter out rows where date is NaT (empty rows at end)
        chunk = chunk.dropna(subset=['report_date'])
        
        frames.append(chunk)
        
    df_hist = pd.concat(frames)
    
    # Clean up
    df_hist['oil_rigs'] = pd.to_numeric(df_hist['oil_rigs'], errors='coerce').fillna(0)
    df_hist['gas_rigs'] = pd.to_numeric(df_hist['gas_rigs'], errors='coerce').fillna(0)
    df_hist['misc_rigs'] = pd.to_numeric(df_hist['misc_rigs'], errors='coerce').fillna(0)
    df_hist['total_rigs'] = pd.to_numeric(df_hist['total_rigs'], errors='coerce').fillna(0)
    
    print(f"Processed {len(df_hist)} rows from historical file.")
    
except Exception as e:
    print(f"Error processing xlsb: {e}")
    df_hist = pd.DataFrame()


print("\n## Processing Recent Data (.xlsx)...")
try:
    # Read "NAM Weekly" sheet
    # Header is at row index 10 (based on previous inspection)
    df_recent_raw = pd.read_excel(xlsx_path, sheet_name='NAM Weekly', header=10, engine='openpyxl')
    
    # Columns: Country, County, Basin, DrillFor, US_PublishDate, Rig Count Value
    # Filter for US only? The historical file was "US Count by Basin".
    # Let's check 'Country' column
    if 'Country' in df_recent_raw.columns:
        df_recent_raw = df_recent_raw[df_recent_raw['Country'] == 'UNITED STATES']
    
    # Pivot to get Oil/Gas/Misc columns
    # Index: US_PublishDate, Basin
    # Columns: DrillFor
    # Values: Rig Count Value
    
    pivot = df_recent_raw.pivot_table(
        index=['US_PublishDate', 'Basin'],
        columns='DrillFor',
        values='Rig Count Value',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Rename columns
    pivot.columns.name = None # Remove 'DrillFor' name
    
    # Ensure columns exist
    for col in ['Oil', 'Gas', 'Misc']:
        if col not in pivot.columns:
            pivot[col] = 0
            
    pivot = pivot.rename(columns={
        'US_PublishDate': 'report_date',
        'Basin': 'basin',
        'Oil': 'oil_rigs',
        'Gas': 'gas_rigs',
        'Misc': 'misc_rigs'
    })
    
    pivot['total_rigs'] = pivot['oil_rigs'] + pivot['gas_rigs'] + pivot['misc_rigs']
    
    df_recent = pivot
    print(f"Processed {len(df_recent)} rows from recent file.")
    
except Exception as e:
    print(f"Error processing xlsx: {e}")
    df_recent = pd.DataFrame()

# Merge
print("\n## Merging Data...")
if not df_hist.empty and not df_recent.empty:
    # Combine
    combined = pd.concat([df_hist, df_recent])
    
    # Remove duplicates: sort by date desc, drop duplicates on [date, basin], keep first (recent)
    combined['report_date'] = pd.to_datetime(combined['report_date'])
    combined = combined.sort_values('report_date', ascending=False)
    combined = combined.drop_duplicates(subset=['report_date', 'basin'], keep='first')
    
    print(f"Total rows after merge: {len(combined)}")
    
    # Insert into DuckDB
    con.execute("INSERT INTO fact_baker_hughes_rig_count (report_date, basin, total_rigs, oil_rigs, gas_rigs, misc_rigs) SELECT report_date, basin, total_rigs, oil_rigs, gas_rigs, misc_rigs FROM combined")
    print("Data ingested successfully.")
    
elif not df_hist.empty:
    print("Only historical data available.")
    con.execute("INSERT INTO fact_baker_hughes_rig_count (report_date, basin, total_rigs, oil_rigs, gas_rigs, misc_rigs) SELECT report_date, basin, total_rigs, oil_rigs, gas_rigs, misc_rigs FROM df_hist")
elif not df_recent.empty:
    print("Only recent data available.")
    con.execute("INSERT INTO fact_baker_hughes_rig_count (report_date, basin, total_rigs, oil_rigs, gas_rigs, misc_rigs) SELECT report_date, basin, total_rigs, oil_rigs, gas_rigs, misc_rigs FROM df_recent")

con.close()
