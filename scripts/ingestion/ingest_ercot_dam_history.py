import gridstatus
import duckdb
import pandas as pd
import os

# Database path
DB_PATH = "data/commodity_data.duckdb"
YEARS = [2021, 2022, 2023, 2024]

def ingest_historical_dam():
    print(f"Connecting to DuckDB at {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    
    # Create table
    con.execute("""
        CREATE TABLE IF NOT EXISTS fact_ercot_dam_spp (
            interval_start TIMESTAMP,
            interval_end TIMESTAMP,
            settlement_point VARCHAR,
            settlement_point_type VARCHAR,
            price DOUBLE,
            market VARCHAR DEFAULT 'DAM',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    iso = gridstatus.Ercot()
    
    for year in YEARS:
        print(f"Fetching ERCOT Day-Ahead Market (DAM) Prices for {year}...")
        try:
            # get_dam_spp returns a dataframe with columns: Time, Interval Start, Interval End, Location, Location Type, Market, SPP
            df = iso.get_dam_spp(year=year, verbose=True)
            
            # Save raw file
            raw_file = f"data/raw/ercot/dam_spp_{year}.parquet"
            if not os.path.exists("data/raw/ercot"):
                os.makedirs("data/raw/ercot")
            df.to_parquet(raw_file)
            print(f"Saved raw file to {raw_file}")
            
            # Rename columns to match DB
            # Note: gridstatus columns might vary slightly, but usually:
            # 'Location' -> settlement_point, 'Location Type' -> settlement_point_type, 'SPP' -> price
            
            df_ingest = df.rename(columns={
                'Interval Start': 'interval_start',
                'Interval End': 'interval_end',
                'Location': 'settlement_point',
                'Location Type': 'settlement_point_type',
                'SPP': 'price'
            })[['interval_start', 'interval_end', 'settlement_point', 'settlement_point_type', 'price']].copy()
            
            # Insert
            print(f"Inserting {len(df_ingest)} records for {year}...")
            con.execute("INSERT INTO fact_ercot_dam_spp (interval_start, interval_end, settlement_point, settlement_point_type, price) SELECT interval_start, interval_end, settlement_point, settlement_point_type, price FROM df_ingest")
            
        except Exception as e:
            print(f"Error fetching {year}: {e}")
            import traceback
            traceback.print_exc()

    # Verify
    count = con.execute("SELECT COUNT(*) FROM fact_ercot_dam_spp").fetchone()[0]
    print(f"Total records in fact_ercot_dam_spp: {count}")
    
    con.close()

if __name__ == "__main__":
    ingest_historical_dam()
