import requests
import json
import os
import duckdb

# Configuration
URL = "https://services2.arcgis.com/LYMgRMwHfrWWEg3s/arcgis/rest/services/HIFLD_US_Electric_Power_Transmission_Lines/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
OUTPUT_DIR = "data/raw/eia/spatial"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "transmission_lines.geojson")
DB_PATH = "data/commodity_data.duckdb"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Downloading Transmission Lines from {URL}...")

try:
    # ArcGIS limits record count (usually 1000 or 2000). We need to paginate or check if we can get all.
    # Let's try downloading a chunk first to verify schema, then implement pagination if needed.
    # Or use the file download if available.
    # The search result mentioned 94k records. A single GET might fail or truncate.
    
    # Better approach: Check if there's a direct file download from the Hub URL or use the paginated fetch.
    # Let's try fetching the first batch to inspect properties.
    
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()
    
    if 'features' in data:
        count = len(data['features'])
        print(f"Downloaded {count} features in initial batch.")
        
        # Save to file
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(data, f)
            
        print(f"Saved to {OUTPUT_FILE}")
        
        # Ingest into DuckDB
        con = duckdb.connect(DB_PATH)
        con.execute("INSTALL spatial; LOAD spatial;")
        
        # Create table
        # We'll use ST_Read to infer schema
        print("Ingesting into DuckDB...")
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS spatial_transmission_lines AS 
            SELECT * FROM ST_Read('{OUTPUT_FILE}')
        """)
        
        # If table exists, we might want to replace or append. For now, create if not exists.
        # Check count
        db_count = con.execute("SELECT COUNT(*) FROM spatial_transmission_lines").fetchone()[0]
        print(f"Total rows in spatial_transmission_lines: {db_count}")
        
        # Inspect columns
        cols = con.execute("DESCRIBE spatial_transmission_lines").fetchall()
        print("\nColumns:")
        for c in cols:
            print(f"- {c[0]} ({c[1]})")
            
        con.close()
        
    else:
        print("No features found in response.")
        print(data.keys())

except Exception as e:
    print(f"Error: {e}")
