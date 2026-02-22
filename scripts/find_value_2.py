import duckdb
con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Searching for value 168415543 in ferc_cash_flow")
query = """
    SELECT * 
    FROM ferc_cash_flow 
    WHERE current_year = 168415543 OR prev_year = 168415543
"""
df = con.execute(query).fetchdf()
print(df)
