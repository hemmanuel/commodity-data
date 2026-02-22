import duckdb

con = duckdb.connect('data/commodity_data.duckdb')
try:
    # Check count of ELEC data
    count = con.execute("""
        SELECT COUNT(*)
        FROM eia_data d
        JOIN eia_series s ON d.series_id = s.series_id
        WHERE s.dataset = 'ELEC'
    """).fetchone()[0]
    print(f"ELEC Data Points: {count}")
    
    if count > 0:
        sid = con.execute("""
            SELECT s.series_id 
            FROM eia_series s
            JOIN eia_data d ON s.series_id = d.series_id
            WHERE s.dataset = 'ELEC'
            LIMIT 1
        """).fetchone()[0]
        print(f"Sample ELEC Series: {sid}")
        
except Exception as e:
    print(e)
con.close()
