import duckdb

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Checking for Oil Majors in dim_companies\n")

majors = ['Exxon', 'Chevron', 'Shell', 'BP', 'Conoco', 'Phillips 66', 'Marathon', 'Valero']
for m in majors:
    print(f"Searching for {m}...")
    res = con.execute(f"SELECT company_id, company_name FROM dim_companies WHERE company_name ILIKE '%{m}%' LIMIT 5").fetchall()
    for r in res:
        print(f"  - {r[1]} (ID: {r[0]})")

con.close()
