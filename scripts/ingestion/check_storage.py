import duckdb
con=duckdb.connect('data/commodity_data.duckdb', read_only=True)
df=con.execute("SELECT series_id, name FROM eia_series WHERE dataset='NG_STOR_WKLY'").fetchdf()
print(df)