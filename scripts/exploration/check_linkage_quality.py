import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Backbone Linkage Quality Check\n")

# 1. Check Corporate Link IDs
print("### 1. Corporate Link ID Resolution")
try:
    # Check if source_id in links_corporate exists in ferc_respondents (assuming they might be respondent_ids or something else)
    # The previous output showed UUIDs. Let's see if we have a mapping table or if these UUIDs are generated hashes.
    # If they are hashes of names, we might need to re-hash names to check.
    # Alternatively, let's check if they match any known ID columns.
    
    links = con.execute("SELECT * FROM links_corporate LIMIT 1").fetchdf()
    sample_id = links.iloc[0]['source_id']
    print(f"Sample Link ID: {sample_id}")
    
    # Check if this ID exists in dim_companies
    # dim_companies IDs looked like integers in the previous step.
    # This suggests links_corporate might be using a different ID scheme (maybe from a different ingestion process).
    
    print("Checking if IDs match dim_companies...")
    match = con.execute(f"SELECT COUNT(*) FROM dim_companies WHERE CAST(company_id AS VARCHAR) = '{sample_id}'").fetchone()[0]
    print(f"Matches in dim_companies: {match}")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "-"*40 + "\n")

# 2. Check Pipeline Operator String Resolution
print("### 2. Pipeline Operator Resolution")
try:
    # Get distinct operators from spatial_pipelines
    operators = con.execute("SELECT DISTINCT operator FROM spatial_pipelines WHERE operator IS NOT NULL").fetchdf()
    print(f"Distinct Pipeline Operators: {len(operators)}")
    
    # Check how many match dim_pipelines names (exact match)
    query = """
    SELECT COUNT(*) 
    FROM spatial_pipelines sp
    JOIN dim_pipelines dp ON sp.operator = dp.pipeline_name
    """
    matches = con.execute(query).fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM spatial_pipelines").fetchone()[0]
    print(f"Direct Name Matches (Spatial -> Dim): {matches} / {total} ({matches/total*100:.1f}%)")
    
    # Check match with dim_companies
    query_comp = """
    SELECT COUNT(*) 
    FROM spatial_pipelines sp
    JOIN dim_companies dc ON sp.operator = dc.company_name
    """
    matches_comp = con.execute(query_comp).fetchone()[0]
    print(f"Direct Name Matches (Spatial -> Company): {matches_comp} / {total} ({matches_comp/total*100:.1f}%)")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "-"*40 + "\n")

# 3. Check EIA Utility -> FERC Company Linkage
print("### 3. EIA Utility -> FERC Company Linkage")
try:
    # links_ownership links company_id (FERC?) to plant_id (EIA?)
    # Let's verify the ID types.
    
    sample_link = con.execute("SELECT * FROM links_ownership LIMIT 1").fetchdf()
    print("Sample Ownership Link:")
    print(sample_link.to_string(index=False))
    
    comp_id = sample_link.iloc[0]['company_id']
    plant_id = sample_link.iloc[0]['plant_id']
    
    # Check if company_id exists in dim_companies
    comp_exists = con.execute(f"SELECT COUNT(*) FROM dim_companies WHERE company_id = {comp_id}").fetchone()[0]
    print(f"Company ID {comp_id} exists in dim_companies: {comp_exists}")
    
    # Check if plant_id exists in dim_plants or eia860
    # Note: plant_id in links_ownership is likely the EIA plant code
    plant_exists = con.execute(f"SELECT COUNT(*) FROM dim_plants WHERE plant_id = {plant_id}").fetchone()[0]
    print(f"Plant ID {plant_id} exists in dim_plants: {plant_exists}")

except Exception as e:
    print(f"Error: {e}")

con.close()
