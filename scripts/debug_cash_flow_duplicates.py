import duckdb
con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Checking duplicates in ferc_cash_flow for Respondent 48, Year 2000, Row 200")
query = """
    SELECT * 
    FROM ferc_cash_flow 
    WHERE respondent_id = '48' 
    AND year = 2000 
    AND row_number = 200
"""
df = con.execute(query).fetchdf()
print(df)
