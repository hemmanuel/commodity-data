import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Linking Capacity Pipelines (dim_pipelines) to Financials\n")

# 1. Get all names from dim_pipelines
print("Fetching capacity pipeline names...")
cap_pipes = con.execute("""
    SELECT DISTINCT pipeline_name 
    FROM dim_pipelines 
    WHERE pipeline_name IS NOT NULL AND pipeline_name != ''
""").fetchdf()

print(f"Found {len(cap_pipes)} pipelines in capacity dataset.")

# 2. Manual Overrides (Dictionary of Capacity Name -> FERC Name)
# Adding specific capacity names that might differ from spatial names
manual_map = {
    "El Paso Nat Gas Co": "El Paso Natural Gas Company, L.L.C.",
    "Tennessee Gas PL Co": "Tennessee Gas Pipeline Company, L.L.C.",
    "Transcontinental Gas PL": "Transcontinental Gas Pipe Line Company, LLC",
    "Natural Gas PL Co of Am": "Natural Gas Pipeline Company of America LLC",
    "Columbia Gas Trans": "Columbia Gas Transmission, LLC",
    "Florida Gas Trans Co": "Florida Gas Transmission Company, LLC",
    "Northern Natural Gas": "Northern Natural Gas Company",
    "Panhandle Eastern PL": "Panhandle Eastern Pipe Line Company, LP",
    "Texas Eastern Trans": "Texas Eastern Transmission, LP",
    "Southern Nat Gas Co": "Southern Natural Gas Company, L.L.C.",
    "Transwestern PL Co": "Transwestern Pipeline Company, LLC",
    "Northwest Pipeline": "Northwest Pipeline LLC",
    "ANR Pipeline Co": "ANR Pipeline Company",
    "Trunkline Gas Co": "Trunkline Gas Company, LLC",
    "Dominion Transmission": "Dominion Energy Transmission, Inc.",
    "Kern River Gas Trans": "Kern River Gas Transmission Company",
    "Gas Trans Northwest": "Gas Transmission Northwest LLC",
    "Iroquois Gas Trans": "Iroquois Gas Transmission System, L.P.",
    "Algonquin Gas Trans": "Algonquin Gas Transmission, LLC",
    "Great Lakes Gas Trans": "Great Lakes Gas Transmission Limited Partnership",
    "Viking Gas Trans": "Viking Gas Transmission Company",
    "Midwestern Gas Trans": "Midwestern Gas Transmission Company",
    "Guardian Pipeline": "Guardian Pipeline, L.L.C.",
    "Vector Pipeline": "Vector Pipeline L.P.",
    "Alliance Pipeline": "Alliance Pipeline L.P.",
    "Maritimes & Northeast": "Maritimes & Northeast Pipeline, L.L.C.",
    "Portland Natural Gas": "Portland Natural Gas Transmission System",
    "Granite State Gas": "Granite State Gas Transmission, Inc.",
    "Vermont Gas Systems": "Vermont Gas Systems, Inc.",
    "Equitrans": "Equitrans, L.P.",
    "National Fuel Gas": "National Fuel Gas Supply Corporation",
    "Dominion Energy Questar": "Dominion Energy Questar Pipeline, LLC",
    "Questar Pipeline": "Dominion Energy Questar Pipeline, LLC",
    "Colorado Interstate": "Colorado Interstate Gas Company, L.L.C.",
    "Wyoming Interstate": "Wyoming Interstate Company, L.L.C.",
    "Cheyenne Plains": "Cheyenne Plains Gas Pipeline Company, L.L.C.",
    "Southern Star Central": "Southern Star Central Gas Pipeline, Inc.",
    "Trailblazer Pipeline": "Trailblazer Pipeline Company LLC",
    "Rockies Express": "Rockies Express Pipeline LLC",
    "Tallgrass Interstate": "Tallgrass Interstate Gas Transmission, LLC",
    "Enable Gas Trans": "Enable Gas Transmission, LLC",
    "Enable Miss River": "Enable Mississippi River Transmission, LLC",
    "Texas Gas Trans": "Texas Gas Transmission, LLC",
    "Gulf South Pipeline": "Gulf South Pipeline Company, LP",
    "Gulf Crossing Pipeline": "Gulf Crossing Pipeline Company LLC",
    "Midcontinent Express": "Midcontinent Express Pipeline LLC",
    "Fayetteville Express": "Fayetteville Express Pipeline LLC",
    "Sierrita Gas Pipeline": "Sierrita Gas Pipeline LLC",
    "Mojave Pipeline": "Mojave Pipeline Company, L.L.C.",
    "Ruby Pipeline": "Ruby Pipeline, LLC",
    "Bison Pipeline": "Bison Pipeline LLC",
    "Northern Border": "Northern Border Pipeline Company",
    "WBI Energy Trans": "WBI Energy Transmission, Inc.",
    "NorthWestern Corp": "NorthWestern Corporation",
    "Black Hills Shoshone": "Black Hills Shoshone Pipeline, LLC",
    "Public Service of NM": "Public Service Company of New Mexico",
    "Southwest Gas Corp": "Southwest Gas Corporation",
    "Sierra Pacific Power": "Sierra Pacific Power Company",
    "Tuscarora Gas Trans": "Tuscarora Gas Transmission Company",
    "Paiute Pipeline": "Paiute Pipeline Company",
    "KO Transmission": "KO Transmission Company",
    "Trans-Union Interstate": "Trans-Union Interstate Pipeline, L.P.",
    "Destin Pipeline": "Destin Pipeline Company, L.L.C.",
    "Discovery Gas Trans": "Discovery Gas Transmission LLC",
    "Chandeleur Pipe Line": "Chandeleur Pipe Line, LLC",
    "Kinetica Energy": "Kinetica Energy Express, LLC",
    "Sea Robin Pipeline": "Sea Robin Pipeline Company, LLC",
    "Stingray Pipeline": "Stingray Pipeline Company, L.L.C.",
    "Nautilus Pipeline": "Nautilus Pipeline Company, L.L.C.",
    "Mississippi Canyon": "Mississippi Canyon Gas Pipeline, LLC",
    "Garden Banks Gas": "Garden Banks Gas Pipeline, LLC",
    "High Island Offshore": "High Island Offshore System, L.L.C.",
    "Central Kentucky": "Central Kentucky Transmission Company",
    "Crossroads Pipeline": "Crossroads Pipeline Company",
    "Hardy Storage": "Hardy Storage Company, LLC",
    "Boardwalk Storage": "Boardwalk Storage Company, LLC",
    "Rover Pipeline": "Rover Pipeline LLC",
    "Constitution Pipeline": "Constitution Pipeline Company, LLC",
    "NEXUS Gas Trans": "NEXUS Gas Transmission, LLC",
    "Empire Pipeline": "Empire Pipeline, Inc.",
    "Millennium Pipeline": "Millennium Pipeline Company, L.L.C.",
    "Valley Crossing": "Valley Crossing Pipeline, LLC",
    "Sabal Trail": "Sabal Trail Transmission, LLC",
    "Atmos Pipeline": "Atmos Energy Corporation",
    "East Ohio Gas": "The East Ohio Gas Company",
    "Michcon Gas": "Michigan Consolidated Gas Company",
    "Brooklyn Union Gas": "The Brooklyn Union Gas Company"
}

# 3. Perform Matching
print("Performing matching against dim_companies...")

THRESHOLD = 0.85
matches_found = 0
manual_matches = 0
exact_matches = 0
fuzzy_matches = 0
skipped_existing = 0

for index, row in cap_pipes.iterrows():
    op_name = row['pipeline_name']
    safe_op_name = op_name.replace("'", "''")
    
    # Check if already exists in links table
    exists = con.execute(f"SELECT COUNT(*) FROM links_pipeline_operators WHERE operator_name = '{safe_op_name}'").fetchone()[0]
    if exists > 0:
        skipped_existing += 1
        continue

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
print(f"Total Capacity Pipelines: {len(cap_pipes)}")
print(f"Already Linked: {skipped_existing}")
print(f"New Matches Found: {matches_found}")
print(f"  - Manual: {manual_matches}")
print(f"  - Exact: {exact_matches}")
print(f"  - Fuzzy: {fuzzy_matches}")

# 4. Verify El Paso
print("\nVerifying 'El Paso Nat Gas Co' Link:")
res = con.execute("SELECT * FROM links_pipeline_operators WHERE operator_name = 'El Paso Nat Gas Co'").fetchdf()
print(res.to_string(index=False))

con.close()
