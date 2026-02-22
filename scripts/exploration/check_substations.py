import duckdb

con = duckdb.connect('data/commodity_data.duckdb', read_only=True)
try:
    # Check sample SUB_1 and SUB_2 values
    print("Sample Substation Names (SUB_1):")
    res = con.execute("""
        SELECT SUB_1, COUNT(*) 
        FROM spatial_transmission_lines 
        WHERE SUB_1 NOT LIKE 'UNKNOWN%' AND SUB_1 NOT LIKE 'TAP%' 
        GROUP BY SUB_1 
        ORDER BY 2 DESC 
        LIMIT 10
    """).fetchall()
    for r in res:
        print(f"- {r[0]}: {r[1]}")

    print("\nSample Substation Names (SUB_2):")
    res = con.execute("""
        SELECT SUB_2, COUNT(*) 
        FROM spatial_transmission_lines 
        WHERE SUB_2 NOT LIKE 'UNKNOWN%' AND SUB_2 NOT LIKE 'TAP%' 
        GROUP BY SUB_2 
        ORDER BY 2 DESC 
        LIMIT 10
    """).fetchall()
    for r in res:
        print(f"- {r[0]}: {r[1]}")
        
finally:
    con.close()
