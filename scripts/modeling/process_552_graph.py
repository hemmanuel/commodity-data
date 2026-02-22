import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"
CSV_PATH = "data/raw/ferc/Form_552_Master_Table.csv"

def process_552_graph():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH)
    print("Processing Form 552 for Graph...")

    # 1. Ingest CSV
    con.execute(f"CREATE OR REPLACE TABLE ferc_form552_master AS SELECT * FROM read_csv_auto('{CSV_PATH}', all_varchar=True)")

    # 2. Add new companies to dim_companies
    print("Adding new companies from Form 552...")
    
    # Create temp table of unique names
    con.execute("CREATE OR REPLACE TEMP TABLE temp_552_companies AS SELECT DISTINCT TRIM(Respondent) as name FROM ferc_form552_master WHERE Respondent IS NOT NULL UNION SELECT DISTINCT TRIM(Reporting_Company) as name FROM ferc_form552_master WHERE Reporting_Company IS NOT NULL")
    
    # Insert new companies
    con.execute("""
        INSERT INTO dim_companies (company_id, company_name, source)
        SELECT 
            md5(UPPER(TRIM(t.name))) as cid,
            MAX(t.name) as cname,
            'FERC_552'
        FROM temp_552_companies t
        LEFT JOIN dim_companies d ON md5(UPPER(TRIM(t.name))) = d.company_id
        WHERE d.company_id IS NULL
        GROUP BY md5(UPPER(TRIM(t.name)))
    """)
    
    # 3. Create Corporate Links Table
    con.execute("CREATE TABLE IF NOT EXISTS links_corporate (link_id INTEGER, source_id VARCHAR, target_id VARCHAR, relation_type VARCHAR, confidence VARCHAR)")
    try:
        con.execute("CREATE SEQUENCE seq_corp_link_id START 1")
    except:
        pass
    
    # 4. Populate Affiliate Links
    print("Creating Affiliate Links...")
    con.execute("DELETE FROM links_corporate WHERE relation_type = 'AFFILIATE_552'")
    
    con.execute("""
        INSERT INTO links_corporate (link_id, source_id, target_id, relation_type, confidence)
        SELECT DISTINCT
            nextval('seq_corp_link_id'),
            md5(UPPER(TRIM(f.Reporting_Company))),
            md5(UPPER(TRIM(f.Respondent))),
            'AFFILIATE_552',
            'HIGH'
        FROM ferc_form552_master f
        WHERE f.Reporting_Company != f.Respondent
          AND f.Reporting_Company IS NOT NULL
          AND f.Respondent IS NOT NULL
          AND md5(UPPER(TRIM(f.Reporting_Company))) IN (SELECT company_id FROM dim_companies)
          AND md5(UPPER(TRIM(f.Respondent))) IN (SELECT company_id FROM dim_companies)
    """)
    
    aff_count = con.execute("SELECT COUNT(*) FROM links_corporate WHERE relation_type = 'AFFILIATE_552'").fetchone()[0]
    print(f"Created {aff_count} affiliate links.")

    # 5. Populate Name Change Links (SAME_AS)
    print("Creating Name Change Links...")
    con.execute("DELETE FROM links_corporate WHERE relation_type = 'SAME_AS_552'")
    
    # Link: Respondent (New Name) -> Previous Name (Old Name)
    # But first, ensure Previous Name exists as a node?
    # If Previous Name was a Respondent in the past, it exists.
    # If not, we might want to add it?
    # Let's check if Previous Name exists in dim_companies
    
    con.execute("""
        INSERT INTO links_corporate (link_id, source_id, target_id, relation_type, confidence)
        SELECT DISTINCT
            nextval('seq_corp_link_id'),
            md5(UPPER(TRIM(f.Respondent))), -- Current Name
            md5(UPPER(TRIM(f.Respondent_Previous_Name))), -- Old Name
            'SAME_AS_552',
            'HIGH'
        FROM ferc_form552_master f
        WHERE f.Respondent_Previous_Name IS NOT NULL
          AND f.Respondent_Previous_Name != ''
          AND f.Respondent != f.Respondent_Previous_Name
          -- Ensure both exist
          AND md5(UPPER(TRIM(f.Respondent))) IN (SELECT company_id FROM dim_companies)
          AND md5(UPPER(TRIM(f.Respondent_Previous_Name))) IN (SELECT company_id FROM dim_companies)
    """)
    
    same_count = con.execute("SELECT COUNT(*) FROM links_corporate WHERE relation_type = 'SAME_AS_552'").fetchone()[0]
    print(f"Created {same_count} name change links.")
    
    con.close()

if __name__ == "__main__":
    process_552_graph()
