import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Checking for PET Data in eia_data\n")

# Check if 'PET' dataset exists in eia_series (assuming dataset column exists or we can infer from ID)
# eia_series schema: series_id, name, units, frequency, description, start_date, end_date, last_updated, geography, dataset
# Let's check a few PET series IDs to see if they are there.
# Common PET IDs start with "PET."

query = """
    SELECT COUNT(*) 
    FROM eia_series 
    WHERE series_id LIKE 'PET.%'
"""
count = con.execute(query).fetchone()[0]
print(f"Total PET Series in DB: {count}")

if count > 0:
    print("\nSample PET Series:")
    sample = con.execute("""
        SELECT series_id, name 
        FROM eia_series 
        WHERE series_id LIKE 'PET.%' 
        LIMIT 5
    """).fetchdf()
    print(sample.to_string(index=False))

con.close()
