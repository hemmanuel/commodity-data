import requests
import json
import os
import duckdb
import time

# Configuration
# Using Rutgers mirror which seems to have a more complete dataset (8712 records)
BASE_URL = "https://oceandata.rad.rutgers.edu/arcgis/rest/services/RenewableEnergy/HIFLD_Electric_SubstationsTransmissionLines/MapServer/0/query"
OUTPUT_DIR = "data/raw/eia/spatial"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "substations.geojson")
DB_PATH = "data/commodity_data.duckdb"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_all_features():
    all_features = []
    offset = 0
    limit = 1000 # MapServer might have lower limits
    
    print("Starting paginated download for Substations...")
    
    while True:
        print(f"Fetching offset {offset}...")
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": limit
        }
        
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            if not features:
                break
                
            all_features.extend(features)
            count = len(features)
            print(f"Got {count} features. Total: {len(all_features)}")
            
            if count < limit:
                break
                
            offset += limit
            time.sleep(1) # Be nice
            
        except Exception as e:
            print(f"Error fetching offset {offset}: {e}")
            break
            
    return {
        "type": "FeatureCollection",
        "features": all_features
    }

# Run download
full_data = fetch_all_features()

if full_data['features']:
    print(f"Saving {len(full_data['features'])} features to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(full_data, f)
        
    # Ingest
    print("Ingesting into DuckDB...")
    con = duckdb.connect(DB_PATH)
    con.execute("INSTALL spatial; LOAD spatial;")
    
    # Replace table
    con.execute("DROP TABLE IF EXISTS spatial_substations")
    con.execute(f"""
        CREATE TABLE spatial_substations AS 
        SELECT * FROM ST_Read('{OUTPUT_FILE}')
    """)
    
    count = con.execute("SELECT COUNT(*) FROM spatial_substations").fetchone()[0]
    print(f"Final row count: {count}")
    
    # Inspect columns
    cols = con.execute("DESCRIBE spatial_substations").fetchall()
    print("\nColumns:")
    for c in cols:
        print(f"- {c[0]} ({c[1]})")
    
    con.close()
else:
    print("No features downloaded.")
