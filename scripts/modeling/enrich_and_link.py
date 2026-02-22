import duckdb
import os
from thefuzz import fuzz
import logging

DB_PATH = "data/commodity_data.duckdb"
LOG_FILE = "data/entity_resolution.log"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filemode='w' # Overwrite log each run
)

def enrich_and_link():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH)
    print("Starting enrichment and linking...")

    # 1. ENRICH DIM_PLANTS
    # Add columns if they don't exist
    print("Enriching dim_plants with Fuel and Technology...")
    try:
        con.execute("ALTER TABLE dim_plants ADD COLUMN primary_fuel VARCHAR")
        con.execute("ALTER TABLE dim_plants ADD COLUMN technology VARCHAR")
    except:
        pass # Columns might already exist

    # Extract Fuel and Tech from EIA series names
    # Strategy: Look at the most frequent fuel/tech associated with each plant ID in eia_series
    # Name format: "... : Plant (ID) : Fuel : Tech : ..."
    # We'll use a CTE to rank them by frequency
    con.execute("""
        WITH extracted AS (
            SELECT 
                regexp_extract(name, '\(([0-9]+)\)', 1) as pid_str,
                split_part(name, ' : ', 3) as fuel,
                split_part(name, ' : ', 4) as tech
            FROM eia_series
            WHERE series_id LIKE 'ELEC.PLANT%'
            AND regexp_matches(name, '\([0-9]+\)')
        ),
        ranked AS (
            SELECT 
                CAST(pid_str AS INTEGER) as pid, 
                fuel, 
                tech, 
                COUNT(*) as cnt,
                ROW_NUMBER() OVER (PARTITION BY pid_str ORDER BY COUNT(*) DESC) as rn
            FROM extracted
            WHERE fuel != '' AND tech != '' AND pid_str != ''
            GROUP BY pid_str, fuel, tech
        )
        UPDATE dim_plants
        SET 
            primary_fuel = r.fuel,
            technology = r.tech
        FROM ranked r
        WHERE dim_plants.plant_id = r.pid AND r.rn = 1
    """)
    print("dim_plants enriched.")

    # 2. CREATE LINKS TABLE
    print("Creating links_ownership table...")
    con.execute("DROP TABLE IF EXISTS links_ownership")
    con.execute("""
        CREATE TABLE links_ownership (
            link_id INTEGER PRIMARY KEY,
            company_id VARCHAR,
            plant_id INTEGER,
            match_type VARCHAR, -- 'EXACT', 'FUZZY'
            match_score INTEGER,
            confidence VARCHAR -- 'HIGH', 'MEDIUM', 'LOW'
        )
    """)
    con.execute("CREATE SEQUENCE seq_link_id START 1")

    # 3. ENTITY RESOLUTION
    print("Performing Entity Resolution...")
    
    # Get all Companies and Plants
    companies = con.execute("SELECT company_id, company_name FROM dim_companies").fetchall()
    plants = con.execute("SELECT plant_id, plant_name FROM dim_plants").fetchall()
    
    print(f"Comparing {len(companies)} companies against {len(plants)} plants...")
    
    links = []
    
    # Pre-process for exact match speed
    company_map = {c[1].lower().strip(): c[0] for c in companies if c[1]}
    
    for p in plants:
        p_id = p[0]
        p_name = p[1]
        if not p_name: continue
        
        p_name_clean = p_name.lower().strip()
        
        # A. Exact Match
        # Check if plant name *contains* company name (e.g. "Duke Energy output" contains "Duke Energy")
        # Or if Company name is in Plant name
        
        match_found = False
        
        # Simple Exact Lookup
        if p_name_clean in company_map:
            c_id = company_map[p_name_clean]
            links.append((c_id, p_id, 'EXACT', 100, 'HIGH'))
            logging.info(f"[EXACT] Plant '{p_name}' matched Company '{p_name}' (ID: {c_id})")
            match_found = True
            
        if not match_found:
            # B. Fuzzy Match
            # We only check if we didn't find an exact match
            # This is O(N*M), so we need to be careful. 
            # 242 companies * 15k plants = 3.6M comparisons. Doable but slow in Python loop.
            # Optimization: Only check if plant name starts with same letter?
            
            best_score = 0
            best_company = None
            
            for c in companies:
                c_id = c[0]
                c_name = c[1]
                if not c_name: continue
                
                # Optimization: Length check
                if abs(len(p_name) - len(c_name)) > 20: continue
                
                # Token Set Ratio is good for partial string matches
                score = fuzz.token_set_ratio(p_name_clean, c_name.lower().strip())
                
                if score > best_score:
                    best_score = score
                    best_company = (c_id, c_name)
            
            if best_score >= 85: # Threshold
                links.append((best_company[0], p_id, 'FUZZY', best_score, 'MEDIUM'))
                logging.info(f"[FUZZY] Plant '{p_name}' matched Company '{best_company[1]}' (Score: {best_score})")
            elif best_score >= 70:
                 # Log potential misses but don't link automatically? Or link as LOW confidence?
                 # Let's link as LOW for now so we can review
                 links.append((best_company[0], p_id, 'FUZZY', best_score, 'LOW'))
                 logging.info(f"[FUZZY-LOW] Plant '{p_name}' matched Company '{best_company[1]}' (Score: {best_score})")

    # Bulk Insert
    print(f"Inserting {len(links)} links...")
    con.executemany("""
        INSERT INTO links_ownership (link_id, company_id, plant_id, match_type, match_score, confidence)
        VALUES (nextval('seq_link_id'), ?, ?, ?, ?, ?)
    """, links)
    
    con.close()
    print(f"Enrichment complete. Log written to {LOG_FILE}")

if __name__ == "__main__":
    enrich_and_link()
