import duckdb
import os

# Database path
DB_PATH = "data/commodity_data.duckdb"
OUTPUT_DIR = "data/raw/ercot"

def export_ercot_data():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Connecting to DuckDB at {DB_PATH}...")
    con = duckdb.connect(DB_PATH, read_only=True)
    
    tables = [
        "fact_ercot_load",
        "fact_ercot_dam_spp",
        "fact_ercot_rtm_spp"
    ]
    
    for table in tables:
        output_file = os.path.join(OUTPUT_DIR, f"{table}.parquet")
        print(f"Exporting {table} to {output_file}...")
        try:
            con.execute(f"COPY {table} TO '{output_file}' (FORMAT PARQUET)")
            print(f"Successfully exported {table}")
        except Exception as e:
            print(f"Error exporting {table}: {e}")
            
    con.close()

if __name__ == "__main__":
    export_ercot_data()
