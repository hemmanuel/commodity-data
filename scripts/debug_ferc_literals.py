import duckdb
con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Checking duplicates in ferc_row_literals for 2000, F2_114_STMT_INCOME, row 200")
query = """
    SELECT * 
    FROM ferc_row_literals 
    WHERE year = 2000 
    AND table_name = 'F2_114_STMT_INCOME' 
    AND row_number = 200
"""
df = con.execute(query).fetchdf()
print(df)
