import duckdb

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Searching for Futures Contracts in PET\n")

query = """
    SELECT series_id, name, units, frequency, start_date, end_date
    FROM eia_series 
    WHERE series_id LIKE 'PET.%' AND name ILIKE '%Contract%' AND name ILIKE '%1%'
    ORDER BY end_date DESC
    LIMIT 10
"""
res = con.execute(query).fetchdf()
if not res.empty:
    print(res.to_string(index=False))
else:
    print("No matches.")

con.close()
