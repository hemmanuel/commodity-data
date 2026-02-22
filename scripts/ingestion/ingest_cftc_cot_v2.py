import requests
import zipfile
import io
import pandas as pd
import duckdb
import os
import time

# Setup
db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)
raw_dir = "data/raw/cftc"
os.makedirs(raw_dir, exist_ok=True)

# Create table
con.execute("""
    CREATE TABLE IF NOT EXISTS fact_cot_positions (
        report_date DATE,
        market_name VARCHAR,
        open_interest BIGINT,
        prod_merc_long BIGINT,
        prod_merc_short BIGINT,
        managed_money_long BIGINT,
        managed_money_short BIGINT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
# Clear existing data for re-run
con.execute("DELETE FROM fact_cot_positions")

years = range(2006, 2027)
base_url = "https://www.cftc.gov/files/dea/history"

# WTI Physical Code: 067651
target_code = "067651"

for year in years:
    try:
        if year == 2006:
            url = f"{base_url}/fut_disagg_txt_hist_2006_2016.zip"
            print(f"Downloading history file (2006-2016): {url}...")
        elif year <= 2016:
            continue
        else:
            url = f"{base_url}/fut_disagg_txt_{year}.zip"
            print(f"Downloading annual file ({year}): {url}...")
            
        r = requests.get(url)
        if r.status_code == 404:
            print(f"File not found for {year}, skipping.")
            continue
        r.raise_for_status()
        
        z = zipfile.ZipFile(io.BytesIO(r.content))
        file_name = z.namelist()[0]
        z.extract(file_name, raw_dir)
        file_path = os.path.join(raw_dir, file_name)
        
        # Read and filter
        df = pd.read_csv(file_path, low_memory=False)
        
        # Normalize columns
        df.columns = [c.strip() for c in df.columns]
        
        # Identify code column
        code_col = [c for c in df.columns if 'Code' in c and 'Market' in c][0]
        
        # Filter by code
        # Ensure code column is string
        df[code_col] = df[code_col].astype(str)
        # Pad with zeros if needed (e.g. 67651 -> 067651)
        df[code_col] = df[code_col].str.zfill(6)
        
        mask = df[code_col] == target_code
        df_filtered = df[mask].copy()
        
        if df_filtered.empty:
            print(f"No data found for code {target_code} in {year}")
            continue
            
        # Select columns
        cols = {
            'Report_Date_as_YYYY-MM-DD': 'report_date',
            'Market_and_Exchange_Names': 'market_name',
            'Open_Interest_All': 'open_interest',
            'Prod_Merc_Positions_Long_All': 'prod_merc_long',
            'Prod_Merc_Positions_Short_All': 'prod_merc_short',
            'M_Money_Positions_Long_All': 'managed_money_long',
            'M_Money_Positions_Short_All': 'managed_money_short'
        }
        
        available_cols = [c for c in cols.keys() if c in df_filtered.columns]
        df_subset = df_filtered[available_cols].rename(columns=cols)
        
        # Convert date
        df_subset['report_date'] = pd.to_datetime(df_subset['report_date']).dt.date
        
        # Insert
        print(f"Inserting {len(df_subset)} rows for {year}...")
        con.execute("INSERT INTO fact_cot_positions (report_date, market_name, open_interest, prod_merc_long, prod_merc_short, managed_money_long, managed_money_short) SELECT report_date, market_name, open_interest, prod_merc_long, prod_merc_short, managed_money_long, managed_money_short FROM df_subset")
        
        os.remove(file_path)
        
    except Exception as e:
        print(f"Error processing {year}: {e}")

# Verify
count = con.execute("SELECT COUNT(*) FROM fact_cot_positions").fetchone()[0]
print(f"\nTotal rows in fact_cot_positions: {count}")
con.close()
