import duckdb
import pandas as pd

con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Total count:")
print(con.execute("SELECT COUNT(*) FROM ferc_respondents").fetchone()[0])

print("\nFirst 120 rows sorted by name:")
query = """
SELECT respondent_id, respondent_name, year 
FROM ferc_respondents 
ORDER BY COALESCE(respondent_name,'') ASC, year DESC NULLS LAST
LIMIT 120
"""
df = con.execute(query).fetchdf()
print(df.to_string())
