import duckdb

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Checking for Contracts 2-4\n")

ids = ['PET.RCLC1.D', 'PET.RCLC2.D', 'PET.RCLC3.D', 'PET.RCLC4.D']
placeholders = ', '.join([f"'{id}'" for id in ids])

query = f"""
    SELECT series_id, name, end_date
    FROM eia_series 
    WHERE series_id IN ({placeholders})
"""
res = con.execute(query).fetchdf()
print(res.to_string(index=False))

con.close()
