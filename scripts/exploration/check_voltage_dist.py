import duckdb

con = duckdb.connect('data/commodity_data.duckdb', read_only=True)
try:
    print("Voltage Distribution:")
    res = con.execute("""
        SELECT 
            CASE 
                WHEN VOLTAGE < 0 THEN 'Unknown (< 0)'
                WHEN VOLTAGE < 69 THEN '< 69'
                WHEN VOLTAGE < 100 THEN '69-99'
                WHEN VOLTAGE < 138 THEN '100-137'
                WHEN VOLTAGE < 230 THEN '138-229'
                WHEN VOLTAGE < 345 THEN '230-344'
                WHEN VOLTAGE < 500 THEN '345-499'
                WHEN VOLTAGE < 765 THEN '500-764'
                ELSE '765+'
            END as range,
            COUNT(*) as count
        FROM spatial_transmission_lines
        GROUP BY 1
        ORDER BY count DESC
    """).fetchall()
    for r in res:
        print(f"{r[0]}: {r[1]}")
        
    print("\nSample Negative Voltages:")
    res = con.execute("SELECT VOLTAGE, COUNT(*) FROM spatial_transmission_lines WHERE VOLTAGE < 0 GROUP BY 1").fetchall()
    for r in res:
        print(f"{r[0]}: {r[1]}")

finally:
    con.close()
