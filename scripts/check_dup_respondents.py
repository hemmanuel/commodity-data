import duckdb
c = duckdb.connect('data/commodity_data.duckdb', read_only=True)
print("Respondent 48, year 2021:")
print(c.execute("SELECT * FROM ferc_respondents WHERE respondent_id='48' AND year=2021").fetchdf())
print("\nCount per respondent/year for 2021 (where count>1):")
print(c.execute("""
    SELECT respondent_id, year, COUNT(*) as cnt 
    FROM ferc_respondents 
    WHERE year=2021 
    GROUP BY respondent_id, year 
    HAVING COUNT(*) > 1
    LIMIT 5
""").fetchdf())
