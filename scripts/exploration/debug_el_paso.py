import duckdb

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Inspecting 'El Paso' Naming Variations\n")

print("1. dim_pipelines (Capacity Data Source):")
res = con.execute("SELECT pipeline_id, pipeline_name FROM dim_pipelines WHERE pipeline_name ILIKE '%El Paso%'").fetchall()
for r in res:
    print(f"  - ID: {r[0]}, Name: '{r[1]}'")

print("\n2. spatial_pipelines (Map Data Source):")
res = con.execute("SELECT DISTINCT operator FROM spatial_pipelines WHERE operator ILIKE '%El Paso%'").fetchall()
for r in res:
    print(f"  - Operator: '{r[0]}'")

print("\n3. links_pipeline_operators (Current Link Table):")
res = con.execute("SELECT operator_name, company_id FROM links_pipeline_operators WHERE operator_name ILIKE '%El Paso%'").fetchall()
for r in res:
    print(f"  - Key: '{r[0]}', Linked Company ID: {r[1]}")

con.close()
