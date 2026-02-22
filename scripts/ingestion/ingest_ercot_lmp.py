import gridstatus
import duckdb
import pandas as pd
from datetime import datetime, timedelta
import os

# Configuration
DB_PATH = "data/commodity_data.duckdb"
START_DATE = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
END_DATE = datetime.now().strftime('%Y-%m-%d')

print(f"Initializing ERCOT client...")
iso = gridstatus.Ercot()

# 1. Fetch LMP Data (Real-Time 15-min Settlement Point Prices)
print(f"Fetching ERCOT LMP from {START_DATE} to {END_DATE}...")
try:
    # Use get_lmp instead of get_rtm_spp
    # location_type='Settlement Point' is default
    df_lmp = iso.get_lmp(date=START_DATE, end=END_DATE, verbose=True)
    
    # Save raw file
    raw_file = f"data/raw/ercot/rtm_lmp_{START_DATE}_{END_DATE}.parquet"
    if not os.path.exists("data/raw/ercot"):
        os.makedirs("data/raw/ercot")
    df_lmp.to_parquet(raw_file)
    print(f"Saved raw file to {raw_file}")
    
    print(f"Fetched {len(df_lmp)} LMP records.")
    print(df_lmp.head())
    print(df_lmp.columns)
    
    # Ingest into DuckDB
    con = duckdb.connect(DB_PATH)
    
    # Create table if not exists
    con.execute("""
        CREATE TABLE IF NOT EXISTS fact_ercot_rtm_spp (
            interval_start TIMESTAMP,
            interval_end TIMESTAMP,
            settlement_point VARCHAR,
            settlement_point_type VARCHAR,
            price DOUBLE,
            market VARCHAR DEFAULT 'RTM',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clean columns to match schema
    # GridStatus columns usually: 'Interval Start', 'Interval End', 'Location', 'Location Type', 'LMP'
    # Let's map them.
    
    # Rename columns to match DB
    df_lmp = df_lmp.rename(columns={
        'Interval Start': 'interval_start',
        'Interval End': 'interval_end',
        'Location': 'settlement_point',
        'Location Type': 'settlement_point_type',
        'LMP': 'price',
        'Market': 'market'
    })
    
    # Keep only relevant columns
    cols = ['interval_start', 'interval_end', 'settlement_point', 'settlement_point_type', 'price', 'market']
    # Filter columns that exist
    cols = [c for c in cols if c in df_lmp.columns]
    
    df_ingest = df_lmp[cols].copy()
    
    # Insert
    print("Ingesting LMP data...")
    con.execute("INSERT INTO fact_ercot_rtm_spp (interval_start, interval_end, settlement_point, settlement_point_type, price, market) SELECT * FROM df_ingest")
    
    count = con.execute("SELECT COUNT(*) FROM fact_ercot_rtm_spp").fetchone()[0]
    print(f"Total rows in fact_ercot_rtm_spp: {count}")
    
    con.close()

except Exception as e:
    print(f"Error fetching/ingesting LMP: {e}")
