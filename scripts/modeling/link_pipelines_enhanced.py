import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Generating Pipeline Operator Links (Enhanced)\n")

# 1. Get all distinct operators from spatial_pipelines
print("Fetching spatial operators...")
spatial_ops = con.execute("""
    SELECT DISTINCT operator 
    FROM spatial_pipelines 
    WHERE operator IS NOT NULL AND operator != ''
""").fetchdf()

print(f"Found {len(spatial_ops)} distinct operators in spatial layer.")

# 2. Create the links table
print("Creating links_pipeline_operators table...")
con.execute("""
    CREATE TABLE IF NOT EXISTS links_pipeline_operators (
        operator_name VARCHAR,
        company_id VARCHAR,
        match_score DOUBLE,
        match_type VARCHAR, -- 'EXACT', 'FUZZY', 'MANUAL'
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
con.execute("DELETE FROM links_pipeline_operators") 

# 3. Manual Overrides (Dictionary of Spatial Name -> FERC Name)
# We map to the Name, then lookup the ID.
manual_map = {
    "Atmos Pipeline - Texas": "Atmos Energy Corporation",
    "Brooklyn Union Gas Co": "The Brooklyn Union Gas Company",
    "East Ohio Gas Co": "The East Ohio Gas Company",
    "Michcon Gas Co": "Michigan Consolidated Gas Company",
    "Sabal Trail Pipeline": "Sabal Trail Transmission, LLC",
    "Tuscarora Pipeline Co": "Tuscarora Gas Transmission Company",
    "Valley Crossing Pipeline": "Valley Crossing Pipeline, LLC",
    "Rover Pipeline": "Rover Pipeline LLC",
    "Constitution Pipeline": "Constitution Pipeline Company, LLC",
    "Gulf South Pipeline Co": "Gulf South Pipeline Company, LP",
    "Natural Gas Pipeline Co of Am": "Natural Gas Pipeline Company of America LLC",
    "Tennessee Gas Pipeline Co": "Tennessee Gas Pipeline Company, L.L.C.",
    "Transcontinental Gas PL Co": "Transcontinental Gas Pipe Line Company, LLC",
    "Algonquin Gas Trans Co": "Algonquin Gas Transmission, LLC",
    "Iroquois Gas Trans System": "Iroquois Gas Transmission System, L.P.",
    "Portland Natural Gas Trans": "Portland Natural Gas Transmission System",
    "Maritimes & Northeast Pipeline": "Maritimes & Northeast Pipeline, L.L.C.",
    "Alliance Pipeline": "Alliance Pipeline L.P.",
    "Vector Pipeline": "Vector Pipeline L.P.",
    "Guardian Pipeline": "Guardian Pipeline, L.L.C.",
    "Viking Gas Transmission Co": "Viking Gas Transmission Company",
    "Midwestern Gas Trans Co": "Midwestern Gas Transmission Company",
    "Great Lakes Gas Trans": "Great Lakes Gas Transmission Limited Partnership",
    "ANR Pipeline Co": "ANR Pipeline Company",
    "Trunkline Gas Co": "Trunkline Gas Company, LLC",
    "Panhandle Eastern PL Co": "Panhandle Eastern Pipe Line Company, LP",
    "Columbia Gas Transmission": "Columbia Gas Transmission, LLC",
    "Columbia Gulf Transmission": "Columbia Gulf Transmission, LLC",
    "Texas Eastern Trans Co": "Texas Eastern Transmission, LP",
    "Dominion Transmission": "Dominion Energy Transmission, Inc.",
    "National Fuel Gas Supply Co": "National Fuel Gas Supply Corporation",
    "Equitrans": "Equitrans, L.P.",
    "Kern River Gas Trans Co": "Kern River Gas Transmission Company",
    "Northwest Pipeline": "Northwest Pipeline LLC",
    "Gas Transmission Northwest": "Gas Transmission Northwest LLC",
    "Ruby Pipeline LLC": "Ruby Pipeline, LLC",
    "Questar Pipeline Co": "Dominion Energy Questar Pipeline, LLC",
    "Colorado Interstate Gas Co": "Colorado Interstate Gas Company, L.L.C.",
    "Wyoming Interstate Co": "Wyoming Interstate Company, L.L.C.",
    "Cheyenne Plains Gas PL Co": "Cheyenne Plains Gas Pipeline Company, L.L.C.",
    "Southern Star Central Gas": "Southern Star Central Gas Pipeline, Inc.",
    "Northern Natural Gas Co": "Northern Natural Gas Company",
    "Natural Gas Pipeline Co of Am": "Natural Gas Pipeline Company of America LLC",
    "Trailblazer Pipeline Co": "Trailblazer Pipeline Company LLC",
    "Rockies Express Pipeline": "Rockies Express Pipeline LLC",
    "Tallgrass Interstate Gas": "Tallgrass Interstate Gas Transmission, LLC",
    "Enable Gas Transmission": "Enable Gas Transmission, LLC",
    "Enable Mississippi River Trans": "Enable Mississippi River Transmission, LLC",
    "Texas Gas Transmission": "Texas Gas Transmission, LLC",
    "Southern Natural Gas Co": "Southern Natural Gas Company, L.L.C.",
    "Florida Gas Trans Co": "Florida Gas Transmission Company, LLC",
    "Transwestern Pipeline Co": "Transwestern Pipeline Company, LLC",
    "El Paso Natural Gas Co": "El Paso Natural Gas Company, L.L.C.",
    "Mojave Pipeline Co": "Mojave Pipeline Company, L.L.C.",
    "Sierrita Gas Pipeline": "Sierrita Gas Pipeline LLC",
    "Fayetteville Express Pipeline": "Fayetteville Express Pipeline LLC",
    "Midcontinent Express Pipeline": "Midcontinent Express Pipeline LLC",
    "Gulf Crossing Pipeline Co": "Gulf Crossing Pipeline Company LLC",
    "Boardwalk Storage Co": "Boardwalk Storage Company, LLC",
    "Hardy Storage Co": "Hardy Storage Company, LLC",
    "Crossroads Pipeline Co": "Crossroads Pipeline Company",
    "Central Kentucky Trans Co": "Central Kentucky Transmission Company",
    "High Island Offshore System": "High Island Offshore System, L.L.C.",
    "Garden Banks Gas Pipeline": "Garden Banks Gas Pipeline, LLC",
    "Mississippi Canyon Gas PL": "Mississippi Canyon Gas Pipeline, LLC",
    "Nautilus Pipeline Co": "Nautilus Pipeline Company, L.L.C.",
    "Stingray Pipeline Co": "Stingray Pipeline Company, L.L.C.",
    "Sea Robin Pipeline Co": "Sea Robin Pipeline Company, LLC",
    "Kinetica Energy Express": "Kinetica Energy Express, LLC",
    "Chandeleur Pipe Line Co": "Chandeleur Pipe Line, LLC",
    "Discovery Gas Trans": "Discovery Gas Transmission LLC",
    "Destin Pipeline Co": "Destin Pipeline Company, L.L.C.",
    "Okeanos Gas Gathering Co": "Okeanos Gas Gathering Company, LLC",
    "Trans-Union Interstate PL": "Trans-Union Interstate Pipeline, L.P.",
    "KO Transmission Co": "KO Transmission Company",
    "Paiute Pipeline Co": "Paiute Pipeline Company",
    "Tuscarora Gas Trans Co": "Tuscarora Gas Transmission Company",
    "Sierra Pacific Power Co": "Sierra Pacific Power Company",
    "Southwest Gas Corp": "Southwest Gas Corporation",
    "Public Service Co of NM": "Public Service Company of New Mexico",
    "Black Hills Shoshone": "Black Hills Shoshone Pipeline, LLC",
    "NorthWestern Corp": "NorthWestern Corporation",
    "WBI Energy Transmission": "WBI Energy Transmission, Inc.",
    "Bison Pipeline": "Bison Pipeline LLC",
    "Northern Border PL Co": "Northern Border Pipeline Company",
    "Great Lakes Gas Trans": "Great Lakes Gas Transmission Limited Partnership",
    "Vector Pipeline": "Vector Pipeline L.P.",
    "NEXUS Gas Transmission": "NEXUS Gas Transmission, LLC",
    "Rover Pipeline": "Rover Pipeline LLC",
    "Empire Pipeline": "Empire Pipeline, Inc.",
    "Millennium Pipeline Co": "Millennium Pipeline Company, L.L.C.",
    "Iroquois Gas Trans System": "Iroquois Gas Transmission System, L.P.",
    "Algonquin Gas Trans Co": "Algonquin Gas Transmission, LLC",
    "Maritimes & Northeast Pipeline": "Maritimes & Northeast Pipeline, L.L.C.",
    "Portland Natural Gas Trans": "Portland Natural Gas Transmission System",
    "Granite State Gas Trans": "Granite State Gas Transmission, Inc.",
    "Vermont Gas Systems": "Vermont Gas Systems, Inc."
}

# 4. Perform Matching
print("Performing matching against dim_companies...")

THRESHOLD = 0.85
matches_found = 0
manual_matches = 0
exact_matches = 0
fuzzy_matches = 0

for index, row in spatial_ops.iterrows():
    op_name = row['operator']
    safe_op_name = op_name.replace("'", "''")
    
    # A. Try Manual Map
    if op_name in manual_map:
        target_name = manual_map[op_name]
        safe_target = target_name.replace("'", "''")
        
        # Look up ID for manual target
        res = con.execute(f"SELECT company_id FROM dim_companies WHERE company_name = '{safe_target}'").fetchone()
        if res:
            cid = res[0]
            con.execute(f"""
                INSERT INTO links_pipeline_operators (operator_name, company_id, match_score, match_type)
                VALUES ('{safe_op_name}', '{cid}', 1.0, 'MANUAL')
            """)
            manual_matches += 1
            matches_found += 1
            continue
        else:
            print(f"Warning: Manual map target '{target_name}' not found in dim_companies")

    # B. Try Exact Match
    exact_query = f"""
        SELECT company_id, company_name 
        FROM dim_companies 
        WHERE company_name = '{safe_op_name}'
    """
    res = con.execute(exact_query).fetchone()
    
    if res:
        cid, cname = res
        con.execute(f"""
            INSERT INTO links_pipeline_operators (operator_name, company_id, match_score, match_type)
            VALUES ('{safe_op_name}', '{cid}', 1.0, 'EXACT')
        """)
        exact_matches += 1
        matches_found += 1
        continue
        
    # C. Try Fuzzy Match
    fuzzy_query = f"""
        SELECT company_id, company_name, jaro_winkler_similarity(company_name, '{safe_op_name}') as score
        FROM dim_companies
        WHERE score > {THRESHOLD}
        ORDER BY score DESC
        LIMIT 1
    """
    res = con.execute(fuzzy_query).fetchone()
    
    if res:
        cid, cname, score = res
        con.execute(f"""
            INSERT INTO links_pipeline_operators (operator_name, company_id, match_score, match_type)
            VALUES ('{safe_op_name}', '{cid}', {score}, 'FUZZY')
        """)
        fuzzy_matches += 1
        matches_found += 1
    else:
        pass

print(f"\nMatching Complete.")
print(f"Total Operators: {len(spatial_ops)}")
print(f"Matches Found: {matches_found} ({matches_found/len(spatial_ops)*100:.1f}%)")
print(f"  - Manual: {manual_matches}")
print(f"  - Exact: {exact_matches}")
print(f"  - Fuzzy: {fuzzy_matches}")

con.close()
