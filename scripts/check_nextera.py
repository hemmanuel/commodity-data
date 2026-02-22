import duckdb

con = duckdb.connect('data/commodity_data.duckdb')
try:
    print("Searching for 'NextEra'...")
    res = con.execute("SELECT respondent_id, respondent_name, year FROM ferc1_respondents WHERE respondent_name ILIKE '%NextEra%' ORDER BY year DESC LIMIT 5").fetchall()
    print(res)

    print("\nSearching for 'Florida Power'...")
    res2 = con.execute("SELECT respondent_id, respondent_name, year FROM ferc1_respondents WHERE respondent_name ILIKE '%Florida Power%' ORDER BY year DESC LIMIT 5").fetchall()
    print(res2)
except Exception as e:
    print(e)
con.close()
