import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def analyze_historical():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("--- ELEC Dataset Samples ---")
    elec = con.execute("SELECT series_id, name FROM eia_series WHERE dataset='ELEC' LIMIT 10").fetchall()
    for s in elec:
        print(f"ID: {s[0]}")
        print(f"Name: {s[1]}")
        print("-" * 20)

    print("\n--- NG Dataset Samples ---")
    ng = con.execute("SELECT series_id, name FROM eia_series WHERE dataset='NG' LIMIT 10").fetchall()
    for s in ng:
        print(f"ID: {s[0]}")
        print(f"Name: {s[1]}")
        print("-" * 20)

    print("\n--- PET Dataset Samples ---")
    pet = con.execute("SELECT series_id, name FROM eia_series WHERE dataset='PET' LIMIT 10").fetchall()
    for s in pet:
        print(f"ID: {s[0]}")
        print(f"Name: {s[1]}")
        print("-" * 20)

    con.close()

if __name__ == "__main__":
    analyze_historical()
