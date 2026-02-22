import duckdb

con = duckdb.connect('data/commodity_data.duckdb')
try:
    print('ELEC Data:', con.execute("SELECT COUNT(*) FROM eia_data d JOIN eia_series s ON d.series_id=s.series_id WHERE s.dataset='ELEC'").fetchone())
    print('Row Literals:', con.execute('SELECT table_name, COUNT(*) FROM ferc1_row_literals GROUP BY table_name').fetchall())
except Exception as e:
    print(e)
con.close()
