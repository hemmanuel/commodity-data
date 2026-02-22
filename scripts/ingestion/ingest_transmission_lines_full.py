import requests
import json
import os
import duckdb
import time

# Configuration
BASE_URL = "https://services2.arcgis.com/LYMgRMwHfrWWEg3s/arcgis/rest/services/HIFLD_US_Electric_Power_Transmission_Lines/FeatureServer/0/query"
OUTPUT_DIR = "data/raw/eia/spatial"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "transmission_lines_full.geojson")
DB_PATH = "data/commodity_data.duckdb"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_all_features():
    all_features = []
    offset = 0
    limit = 2000 # ArcGIS limit
    
    print("Starting paginated download...")
    
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
    con.execute("DROP TABLE IF EXISTS spatial_transmission_lines")
    con.execute(f"""
        CREATE TABLE spatial_transmission_lines AS 
        SELECT * FROM ST_Read('{OUTPUT_FILE}')
    """)
    
    count = con.execute("SELECT COUNT(*) FROM spatial_transmission_lines").fetchone()[0]
    print(f"Final row count: {count}")
    
    # Create index on VOLTAGE for filtering
    # DuckDB doesn't support spatial indexes in the same way as PostGIS yet, but we can index columns
    # con.execute("CREATE INDEX idx_transmission_voltage ON spatial_transmission_lines(VOLTAGE)")
    
    con.close()
else:
    print("No features downloaded.")
