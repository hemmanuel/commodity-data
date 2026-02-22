import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"
CSV_PATH = "data/raw/ferc/Form_552_Master_Table.csv"

def ingest_552():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH)
    print(f"Ingesting {CSV_PATH}...")
    
    # Create table
    con.execute("DROP TABLE IF EXISTS ferc_form552_master")
    con.execute(f"""
        CREATE TABLE ferc_form552_master AS 
        SELECT * FROM read_csv_auto('{CSV_PATH}', all_varchar=True)
    """)
    
    # Get Year Range
    years = con.execute("SELECT MIN(CAST(Year_of_Report_End AS INTEGER)), MAX(CAST(Year_of_Report_End AS INTEGER)) FROM ferc_form552_master").fetchone()
    print(f"Data covers years: {years[0]} to {years[1]}")
    
    # Check for Affiliate Links
    links = con.execute("""
        SELECT COUNT(*) 
        FROM ferc_form552_master 
        WHERE Respondent != Reporting_Company 
        AND Reporting_Company IS NOT NULL 
        AND Reporting_Company != ''
    """).fetchone()[0]
    print(f"Found {links} potential affiliate links (Respondent != Reporting_Company).")

    con.close()

if __name__ == "__main__":
    ingest_552()
