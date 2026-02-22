import duckdb
import os
import shutil
import time

DB_PATH = "data/commodity_data.duckdb"
DB_VIEW_PATH = "data/commodity_data_view.duckdb"

print(f"Checking DB at {DB_PATH}")
if os.path.exists(DB_PATH):
    print(f"Main DB exists, size: {os.path.getsize(DB_PATH)}")
else:
    print("Main DB does not exist!")

try:
    print("Attempting to connect to MAIN DB (read_only)...")
    con = duckdb.connect(DB_PATH, read_only=True)
    print("Success connecting to MAIN DB")
    con.close()
except Exception as e:
    print(f"Failed to connect to MAIN DB: {e}")

print("\nAttempting snapshot logic...")
try:
    if os.path.exists(DB_VIEW_PATH):
        print(f"Removing existing snapshot {DB_VIEW_PATH}")
        os.remove(DB_VIEW_PATH)
    
    print(f"Copying {DB_PATH} to {DB_VIEW_PATH}...")
    shutil.copy2(DB_PATH, DB_VIEW_PATH)
    print("Copy successful")
    
    print("Connecting to SNAPSHOT...")
    con = duckdb.connect(DB_VIEW_PATH, read_only=True)
    print("Success connecting to SNAPSHOT")
    
    print("Running test query...")
    res = con.execute("SELECT COUNT(*) FROM eia_series").fetchone()
    print(f"Row count: {res[0]}")
    con.close()
except Exception as e:
    print(f"Snapshot logic failed: {e}")
