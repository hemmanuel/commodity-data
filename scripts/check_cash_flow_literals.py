import duckdb
con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Searching for 'Net Income' in CASH FLOW literals for 2000")
query = """
    SELECT row_number, row_literal 
    FROM ferc_row_literals 
    WHERE year = 2000 
    AND table_name = 'F2_120_STMNT_CASH_FLOW' 
    AND row_literal LIKE '%Net Income%'
"""
df = con.execute(query).fetchdf()
print(df)

print("\nSearching for Row 200 in CASH FLOW literals for 2000")
query = """
    SELECT row_number, row_literal 
    FROM ferc_row_literals 
    WHERE year = 2000 
    AND table_name = 'F2_120_STMNT_CASH_FLOW' 
    AND row_number = 200
"""
df = con.execute(query).fetchdf()
print(df)
