import duckdb

con = duckdb.connect('data/commodity_data.duckdb')

print("=== EIA-860 Generators Sample ===")
print(con.execute("SELECT * FROM eia860_generators LIMIT 1").fetchdf().to_string())

print("\n=== EIA-923 Generation Sample ===")
print(con.execute("SELECT * FROM eia923_generation_fuel LIMIT 1").fetchdf().to_string())

print("\n=== Count Check ===")
print(con.execute("SELECT COUNT(*) FROM eia860_generators").fetchone())
print(con.execute("SELECT COUNT(*) FROM eia923_generation_fuel").fetchone())
