import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def check_elec_aggregates():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("--- ELEC Non-Plant Samples ---")
    # Check for IDs not starting with ELEC.PLANT
    aggs = con.execute("""
        SELECT series_id, name 
        FROM eia_series 
        WHERE dataset='ELEC' 
        AND series_id NOT LIKE 'ELEC.PLANT%' 
        LIMIT 20
    """).fetchall()
    
    if not aggs:
        print("No non-plant series found in ELEC dataset sample.")
    else:
        for s in aggs:
            print(f"ID: {s[0]}")
            print(f"Name: {s[1]}")
            print("-" * 20)

    con.close()

if __name__ == "__main__":
    check_elec_aggregates()
