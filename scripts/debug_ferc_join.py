import duckdb
import pandas as pd

con = duckdb.connect('data/commodity_data.duckdb', read_only=True)

print("--- Sample Respondent (2021) ---")
respondents = con.execute("SELECT respondent_id, respondent_name FROM ferc_respondents WHERE year=2021 LIMIT 1").fetchdf()
print(respondents)

if not respondents.empty:
    resp_id = respondents.iloc[0]['respondent_id']
    print(f"\nChecking data for Respondent ID: {resp_id} in 2021")

    print("\n--- Income Statement Data (First 5) ---")
    income = con.execute(f"SELECT * FROM ferc_income_statement WHERE respondent_id='{resp_id}' AND year=2021 LIMIT 5").fetchdf()
    print(income)

    if not income.empty:
        row_num = income.iloc[0]['row_number']
        print(f"\n--- Row Literal for Row {row_num} (2021) ---")
        literal = con.execute(f"SELECT * FROM ferc_row_literals WHERE row_number={row_num} AND year=2021 AND table_name='F2_114_STMT_INCOME'").fetchdf()
        print(literal)
        
        if literal.empty:
            print("!!! No literal found for this row/year/table !!!")
            print("Checking if any literals exist for this table in 2021:")
            print(con.execute("SELECT COUNT(*) FROM ferc_row_literals WHERE year=2021 AND table_name='F2_114_STMT_INCOME'").fetchdf())

print("\n--- Row Literals Sample (2021) ---")
print(con.execute("SELECT * FROM ferc_row_literals WHERE year=2021 LIMIT 5").fetchdf())
