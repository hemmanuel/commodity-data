import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def enrich_ferc1():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH)
    print("Enriching Graph with FERC Form 1 Data...")

    # 1. Add FERC Form 1 Respondents to dim_companies
    print("Adding FERC Form 1 Respondents...")
    
    # Check if column 'source' exists in dim_companies, or if it's named differently
    # Based on previous DESCRIBE, it is 'source'.
    
    # We use 'F1_' prefix for ID to distinguish from Form 2 (numeric) and Form 552 (MD5)
    # But wait, Form 2 IDs are just numbers in string format.
    # Form 1 IDs are also numbers.
    # If respondent 123 exists in Form 2 and Form 1, are they the same company?
    # Likely yes (e.g. Duke Energy might file both).
    # But to be safe and avoid collision if they are different, I'll prefix.
    # Actually, let's check if we can link them later.
    
    con.execute("""
        INSERT INTO dim_companies (company_id, company_name, source)
        SELECT 
            'F1_' || CAST(respondent_id AS VARCHAR),
            arg_max(respondent_name, year), -- Pick name from latest year
            'FERC_FORM1'
        FROM ferc1_respondents
        WHERE 'F1_' || CAST(respondent_id AS VARCHAR) NOT IN (SELECT company_id FROM dim_companies)
        GROUP BY respondent_id
    """)
    
    # 2. Add FERC Form 1 Plants to dim_plants
    print("Adding FERC Form 1 Plants...")
    
    # Get max plant_id to start sequence if needed
    max_id = con.execute("SELECT MAX(plant_id) FROM dim_plants").fetchone()[0] or 0
    print(f"Current Max Plant ID: {max_id}")
    
    # Create a sequence starting from max_id + 1
    con.execute(f"CREATE SEQUENCE IF NOT EXISTS seq_ferc1_plant_id START {max_id + 1}")
    
    # Create a temp table for new plants to assign IDs
    con.execute("""
        CREATE OR REPLACE TEMP TABLE new_ferc1_plants AS
        SELECT 
            TRIM(plant_name) as plant_name,
            TRIM(plant_kind) as plant_kind,
            MIN(year) as start_year,
            MAX(year) as end_year
        FROM ferc1_steam_plants
        GROUP BY 1, 2
    """)
    
    # Filter out plants that might already exist (fuzzy match? or just name match?)
    # For now, we assume they are new if name doesn't match exactly.
    # But wait, we need to assign IDs.
    
    # We'll just insert them. Entity resolution is a separate step.
    # But we need to avoid inserting duplicates if we run this script multiple times.
    # We can check if (plant_name, source='FERC_FORM1') exists.
    
    # Insert new plants
    con.execute("""
        INSERT INTO dim_plants (plant_id, plant_name, extracted_from_source, start_year, end_year, technology)
        SELECT 
            nextval('seq_ferc1_plant_id'),
            plant_name,
            'FERC_FORM1',
            start_year,
            end_year,
            plant_kind
        FROM new_ferc1_plants
        WHERE plant_name NOT IN (SELECT plant_name FROM dim_plants WHERE extracted_from_source = 'FERC_FORM1')
    """)
    
    # 3. Create Ownership Links
    print("Creating Ownership Links...")
    
    # We need to link the newly inserted plants to their respondents.
    # We need the plant_id we just assigned.
    # This is tricky because we generated IDs on the fly.
    # We can join dim_plants back on name and source.
    
    con.execute("""
        INSERT INTO links_ownership (link_id, company_id, plant_id, match_type, match_score, confidence)
        SELECT DISTINCT
            nextval('seq_link_id'),
            'F1_' || CAST(r.respondent_id AS VARCHAR),
            dp.plant_id,
            'EXACT_FERC1',
            100,
            'HIGH'
        FROM ferc1_steam_plants fsp
        JOIN ferc1_respondents r ON fsp.respondent_id = r.respondent_id AND fsp.year = r.year
        JOIN dim_plants dp ON TRIM(fsp.plant_name) = dp.plant_name AND dp.extracted_from_source = 'FERC_FORM1'
        WHERE NOT EXISTS (
            SELECT 1 FROM links_ownership 
            WHERE company_id = 'F1_' || CAST(r.respondent_id AS VARCHAR)
            AND plant_id = dp.plant_id
        )
    """)
    
    # Count results
    n_companies = con.execute("SELECT COUNT(*) FROM dim_companies WHERE source = 'FERC_FORM1'").fetchone()[0]
    n_plants = con.execute("SELECT COUNT(*) FROM dim_plants WHERE extracted_from_source = 'FERC_FORM1'").fetchone()[0]
    n_links = con.execute("SELECT COUNT(*) FROM links_ownership WHERE match_type = 'EXACT_FERC1'").fetchone()[0]
    
    print(f"Total FERC Form 1 Entities: {n_companies} Companies, {n_plants} Plants.")
    print(f"Total FERC Form 1 Links: {n_links} Ownership Links.")
    
    con.close()

if __name__ == "__main__":
    enrich_ferc1()
