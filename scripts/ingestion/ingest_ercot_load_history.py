import gridstatus
import duckdb
import pandas as pd
import os

# Database path
DB_PATH = "data/commodity_data.duckdb"
YEARS = [2021, 2022, 2023, 2024] # Adjust as needed

def ingest_historical_load():
    print(f"Connecting to DuckDB at {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    
    # Create table
    con.execute("""
        CREATE TABLE IF NOT EXISTS fact_ercot_load (
            interval_start TIMESTAMP,
            interval_end TIMESTAMP,
            zone VARCHAR,
            load_mwh DOUBLE,
            market VARCHAR DEFAULT 'RTM',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    iso = gridstatus.Ercot()
    
    for year in YEARS:
        print(f"Fetching ERCOT Load for {year}...")
        try:
            # get_hourly_load_post_settlements requires start/end but fetches annual file based on year
            start_date = f"{year}-01-01"
            end_date = f"{year}-01-02" # Dummy end date, library seems to fetch full year
            
            df = iso.get_hourly_load_post_settlements(start=start_date, end=end_date, verbose=True)
            
            # Save raw file
            raw_file = f"data/raw/ercot/load_{year}.parquet"
            if not os.path.exists("data/raw/ercot"):
                os.makedirs("data/raw/ercot")
            df.to_parquet(raw_file)
            print(f"Saved raw file to {raw_file}")
            
            # Rename 'Hour Ending' or 'Interval Start' if needed
            # The previous test output showed: "Interval Start"
            
            # Melt to long format
            # Columns are usually: Interval Start, Interval End, COAST, EAST, FAR_WEST, NORTH, NORTH_C, SOUTH, SOUTH_C, WEST, ERCOT
            id_vars = ['Interval Start', 'Interval End']
            value_vars = [c for c in df.columns if c not in id_vars]
            
            df_long = df.melt(id_vars=id_vars, value_vars=value_vars, var_name='zone', value_name='load_mwh')
            
            # Rename columns to match DB
            df_long = df_long.rename(columns={
                'Interval Start': 'interval_start',
                'Interval End': 'interval_end'
            })
            
            # Insert
            print(f"Inserting {len(df_long)} records for {year}...")
            con.execute("INSERT INTO fact_ercot_load (interval_start, interval_end, zone, load_mwh) SELECT interval_start, interval_end, zone, load_mwh FROM df_long")
            
        except Exception as e:
            print(f"Error fetching {year}: {e}")
            import traceback
            traceback.print_exc()

    # Verify
    count = con.execute("SELECT COUNT(*) FROM fact_ercot_load").fetchone()[0]
    print(f"Total records in fact_ercot_load: {count}")
    
    con.close()

if __name__ == "__main__":
    ingest_historical_load()
