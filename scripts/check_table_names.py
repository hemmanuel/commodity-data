import duckdb
con = duckdb.connect('data/commodity_data.duckdb')
print("Income tables:")
print(con.execute("SELECT DISTINCT table_name FROM ferc_row_literals WHERE table_name LIKE '%INCOME%'").fetchdf())
print("\nBalance Sheet tables:")
print(con.execute("SELECT DISTINCT table_name FROM ferc_row_literals WHERE table_name LIKE '%BAL%'").fetchdf())
print("\nCash Flow tables:")
print(con.execute("SELECT DISTINCT table_name FROM ferc_row_literals WHERE table_name LIKE '%CASH%'").fetchdf())
