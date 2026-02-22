import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"
OUTPUT_FILE = "data/raw/ercot/ercot_lmp_2026.parquet"

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

print(f"Exporting fact_ercot_rtm_spp to {OUTPUT_FILE}...")
con = duckdb.connect(DB_PATH)
try:
    con.execute(f"COPY fact_ercot_rtm_spp TO '{OUTPUT_FILE}' (FORMAT PARQUET)")
    print("Export successful.")
except Exception as e:
    print(f"Error exporting: {e}")
finally:
    con.close()
