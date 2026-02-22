import duckdb
con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Searching for 'Net Income' in literals for 2000")
query = """
    SELECT row_number, row_literal 
    FROM ferc_row_literals 
    WHERE year = 2000 
    AND table_name = 'F2_114_STMT_INCOME' 
    AND row_literal LIKE '%Net Income%'
"""
df = con.execute(query).fetchdf()
print(df)
