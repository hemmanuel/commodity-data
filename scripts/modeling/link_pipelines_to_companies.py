import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Generating Pipeline Operator Links\n")

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
con.execute("DELETE FROM links_pipeline_operators") # Clear for fresh run

# 3. Perform Matching
print("Performing matching against dim_companies...")

# We'll use a threshold for fuzzy matching
THRESHOLD = 0.85

matches_found = 0
exact_matches = 0
fuzzy_matches = 0

for index, row in spatial_ops.iterrows():
    op_name = row['operator']
    # Escape single quotes
    safe_op_name = op_name.replace("'", "''")
    
    # A. Try Exact Match
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
        
    # B. Try Fuzzy Match
    # We want the best match above threshold
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
        # print(f"  Fuzzy Match: '{op_name}' -> '{cname}' ({score:.2f})")
    else:
        # print(f"  No match found for: '{op_name}'")
        pass

print(f"\nMatching Complete.")
print(f"Total Operators: {len(spatial_ops)}")
print(f"Matches Found: {matches_found} ({matches_found/len(spatial_ops)*100:.1f}%)")
print(f"  - Exact: {exact_matches}")
print(f"  - Fuzzy: {fuzzy_matches}")

# 4. Verify the link to Financials
print("\nVerifying Link to Financials (FERC Form 2)...")
verify_query = """
    SELECT 
        l.operator_name,
        c.company_name,
        COUNT(f.respondent_id) as financial_records
    FROM links_pipeline_operators l
    JOIN dim_companies c ON l.company_id = c.company_id
    LEFT JOIN ferc_respondents fr ON c.company_name = fr.respondent_name
    LEFT JOIN ferc_income_statement f ON fr.respondent_id = f.respondent_id
    GROUP BY 1, 2
    HAVING financial_records > 0
    ORDER BY financial_records DESC
    LIMIT 5
"""
verification = con.execute(verify_query).fetchdf()
print(verification.to_string())

con.close()
