import duckdb

con = duckdb.connect('data/commodity_data.duckdb')
try:
    sid = con.execute("SELECT series_id FROM eia_series WHERE dataset='ELEC' LIMIT 1").fetchone()[0]
    print(f"Series: {sid}")
    data = con.execute("SELECT date, value FROM eia_data WHERE series_id=? LIMIT 5", [sid]).fetchall()
    print(f"Data: {data}")
except Exception as e:
    print(e)
con.close()
