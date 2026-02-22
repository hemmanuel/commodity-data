import duckdb
con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Searching for value 87703890 in ferc_cash_flow")
query = """
    SELECT * 
    FROM ferc_cash_flow 
    WHERE current_year = 87703890 OR prev_year = 87703890
"""
df = con.execute(query).fetchdf()
print(df)
