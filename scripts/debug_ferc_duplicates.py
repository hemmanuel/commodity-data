import duckdb
import pandas as pd

con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

# Pick a respondent and year that has data
resp_id = '48' # ANR Pipeline from user query
year = 2000

print(f"Checking duplicates for Respondent {resp_id} Year {year}")

# Check count of rows for a specific row_number
row_num = 200
query = f"""
    SELECT * 
    FROM ferc_income_statement 
    WHERE respondent_id = '{resp_id}' 
    AND year = {year} 
    AND row_number = {row_num}
"""
print(f"\nQuery: {query}")
df = con.execute(query).fetchdf()
print(df)

# Check if we have multiple source files?
print("\nUnique source files for this respondent/year:")
print(con.execute(f"SELECT DISTINCT source_file FROM ferc_income_statement WHERE respondent_id = '{resp_id}' AND year = {year}").fetchdf())

# Check total count vs distinct row numbers
total = con.execute(f"SELECT COUNT(*) FROM ferc_income_statement WHERE respondent_id = '{resp_id}' AND year = {year}").fetchone()[0]
distinct = con.execute(f"SELECT COUNT(DISTINCT row_number) FROM ferc_income_statement WHERE respondent_id = '{resp_id}' AND year = {year}").fetchone()[0]
print(f"\nTotal rows: {total}")
print(f"Distinct row numbers: {distinct}")
