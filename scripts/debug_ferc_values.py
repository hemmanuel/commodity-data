import duckdb
con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("Checking Respondent 48 (ANR Pipeline) Row 200 values for multiple years")

for year in [2000, 2001, 2002]:
    print(f"\n--- Year {year} ---")
    query = f"""
        SELECT year, row_number, current_year_total, prev_year_total
        FROM ferc_income_statement 
        WHERE respondent_id = '48' 
        AND row_number = 200
        AND year = {year}
    """
    df = con.execute(query).fetchdf()
    print(df)
