import duckdb

db_path = 'data/commodity_data.duckdb'
con = duckdb.connect(db_path)

print("Updating dim_plants state from eia860_generators...")

try:
    # Check if state column exists in eia860_generators
    # It should, as it's part of EIA860_MAP
    
    # Update dim_plants.state where it is NULL, using eia860_generators
    # We use arg_max to get the most recent state for each plant_code
    con.execute("""
        UPDATE dim_plants
        SET state = (
            SELECT arg_max(state, report_year)
            FROM eia860_generators
            WHERE CAST(plant_code AS INTEGER) = dim_plants.plant_id
            GROUP BY CAST(plant_code AS INTEGER)
        )
        WHERE state IS NULL
    """)
    
    # Verify
    count = con.execute("SELECT COUNT(*) FROM dim_plants WHERE state IS NOT NULL").fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM dim_plants").fetchone()[0]
    print(f"Plants with state: {count} / {total}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    con.close()
