import duckdb
import json
import os

db_path = 'data/commodity_data.duckdb'
geojson_path = 'data/raw/eia/spatial/pipelines.geojson'

print(f"Ingesting {geojson_path}...")

con = duckdb.connect(db_path)

try:
    # Install spatial extension if not exists
    print("Installing spatial extension...")
    con.execute("INSTALL spatial; LOAD spatial;")
    
    # Create table
    con.execute("""
        CREATE TABLE IF NOT EXISTS spatial_pipelines (
            operator VARCHAR,
            typepipe VARCHAR,
            status VARCHAR,
            shape_leng DOUBLE,
            geom GEOMETRY
        )
    """)
    
    # Clear existing
    con.execute("DELETE FROM spatial_pipelines")
    
    # Ingest using ST_Read
    print("Reading GeoJSON...")
    con.execute(f"""
        INSERT INTO spatial_pipelines 
        SELECT 
            operator,
            typepipe,
            status,
            shape_leng,
            geom
        FROM ST_Read('{geojson_path}')
    """)
    
    count = con.execute("SELECT COUNT(*) FROM spatial_pipelines").fetchone()[0]
    print(f"Ingested {count} pipeline segments.")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    con.close()
