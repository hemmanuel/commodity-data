import duckdb

con = duckdb.connect('data/commodity_data.duckdb')
try:
    # Find a series_id that exists in BOTH tables
    sid = con.execute("""
        SELECT s.series_id 
        FROM eia_series s
        JOIN eia_data d ON s.series_id = d.series_id
        LIMIT 1
    """).fetchone()
    
    if sid:
        print(f"Valid Series: {sid[0]}")
        data = con.execute("SELECT date, value FROM eia_data WHERE series_id=? LIMIT 5", [sid[0]]).fetchall()
        print(f"Data: {data}")
    else:
        print("No overlapping series found!")
        
except Exception as e:
    print(e)
con.close()
