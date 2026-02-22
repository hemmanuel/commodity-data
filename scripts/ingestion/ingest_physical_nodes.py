import duckdb
import os

# Paths
db_path = "data/commodity_data.duckdb"
compressors_path = os.path.abspath("data/raw/eia/spatial/compressor_stations.geojson")
storage_path = os.path.abspath("data/raw/eia/spatial/storage_fields.geojson")

print(f"Connecting to DB at {db_path}")
con = duckdb.connect(db_path)
con.execute("INSTALL spatial; LOAD spatial;")

# Ingest Compressors
if os.path.exists(compressors_path):
    print(f"Ingesting Compressor Stations from {compressors_path}...")
    con.execute("DROP TABLE IF EXISTS spatial_compressors")
    con.execute(f"""
        CREATE TABLE spatial_compressors AS 
        SELECT * FROM ST_Read('{compressors_path}')
    """)
    count = con.execute("SELECT COUNT(*) FROM spatial_compressors").fetchone()[0]
    print(f"Ingested {count} compressor stations.")
else:
    print(f"Compressor file not found at {compressors_path}")

# Ingest Storage Fields
if os.path.exists(storage_path):
    print(f"Ingesting Storage Fields from {storage_path}...")
    con.execute("DROP TABLE IF EXISTS spatial_storage")
    con.execute(f"""
        CREATE TABLE spatial_storage AS 
        SELECT * FROM ST_Read('{storage_path}')
    """)
    count = con.execute("SELECT COUNT(*) FROM spatial_storage").fetchone()[0]
    print(f"Ingested {count} storage fields.")
else:
    print(f"Storage file not found at {storage_path}")

con.close()
print("Physical nodes ingestion complete.")
