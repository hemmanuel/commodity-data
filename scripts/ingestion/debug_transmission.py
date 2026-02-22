import requests
import json
import os
import duckdb
import time

# Configuration
BASE_URL = "https://services2.arcgis.com/LYMgRMwHfrWWEg3s/arcgis/rest/services/HIFLD_US_Electric_Power_Transmission_Lines/FeatureServer/0/query"
OUTPUT_DIR = "data/raw/eia/spatial"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "transmission_lines_debug.geojson")
DB_PATH = "data/commodity_data.duckdb"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Testing connection to {BASE_URL}...")

params = {
    "where": "1=1",
    "outFields": "*",
    "f": "geojson",
    "resultOffset": 0,
    "resultRecordCount": 100 # Small batch
}

try:
    response = requests.get(BASE_URL, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    response.raise_for_status()
    
    data = response.json()
    features = data.get('features', [])
    print(f"Downloaded {len(features)} features.")
    
    if features:
        print("Sample feature properties:")
        print(json.dumps(features[0]['properties'], indent=2))
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(data, f)
        print(f"Saved to {OUTPUT_FILE}")
        
        # Test ingestion
        con = duckdb.connect(DB_PATH)
        con.execute("INSTALL spatial; LOAD spatial;")
        con.execute(f"CREATE OR REPLACE TABLE debug_transmission AS SELECT * FROM ST_Read('{OUTPUT_FILE}')")
        count = con.execute("SELECT COUNT(*) FROM debug_transmission").fetchone()[0]
        print(f"Ingested {count} rows into debug table.")
        con.close()
        
except Exception as e:
    print(f"Error: {e}")
