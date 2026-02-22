import duckdb
con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Checking duplicates for Respondent 48 Year 2021 Row 200")
query = """
    SELECT * 
    FROM ferc_cash_flow 
    WHERE respondent_id = '48' 
    AND year = 2021 
    AND row_number = 200
"""
df = con.execute(query).fetchdf()
print(df)
