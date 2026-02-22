import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Investigating links_ownership IDs\n")

# Get sample IDs from links_ownership
sample_ids = con.execute("SELECT DISTINCT company_id FROM links_ownership LIMIT 5").fetchdf()['company_id'].tolist()
print(f"Sample IDs from links_ownership: {sample_ids}")

# Check if these match ferc_respondents (Gas) or ferc1_respondents (Electric)
print("\nChecking matches in FERC Respondents tables...")

for table in ["ferc_respondents", "ferc1_respondents"]:
    try:
        # Check if respondent_id is integer or string
        schema = con.execute(f"DESCRIBE {table}").fetchdf()
        id_type = schema[schema['column_name'] == 'respondent_id']['column_type'].values[0]
        print(f"{table} ID type: {id_type}")
        
        # Check for overlap
        query = f"""
        SELECT COUNT(*) 
        FROM {table} 
        WHERE CAST(respondent_id AS INTEGER) IN ({','.join(map(str, sample_ids))})
        """
        count = con.execute(query).fetchone()[0]
        print(f"Matches in {table}: {count}")
        
    except Exception as e:
        print(f"Error checking {table}: {e}")

print("\n" + "-"*40 + "\n")

# Check dim_companies for name matches with these IDs
# If links_ownership.company_id is a FERC ID, we can find the name in ferc_respondents, 
# then check if that name exists in dim_companies.

print("## Tracing ID -> Name -> UUID")
try:
    # Get a sample ID and its name from ferc1_respondents (assuming it's electric for now)
    test_id = sample_ids[0]
    name_query = f"SELECT respondent_name FROM ferc1_respondents WHERE CAST(respondent_id AS INTEGER) = {test_id}"
    name_res = con.execute(name_query).fetchone()
    
    if name_res:
        name = name_res[0]
        print(f"ID {test_id} corresponds to Name: '{name}'")
        
        # Now check if this name has a UUID in dim_companies
        uuid_query = f"SELECT company_id FROM dim_companies WHERE company_name = '{name}'"
        uuid_res = con.execute(uuid_query).fetchone()
        
        if uuid_res:
            print(f"Found UUID in dim_companies: {uuid_res[0]}")
        else:
            print("No UUID found in dim_companies for this name.")
            # Check fuzzy match
            fuzzy_query = f"SELECT company_name, company_id, jaro_winkler_similarity(company_name, '{name}') as score FROM dim_companies ORDER BY score DESC LIMIT 1"
            fuzzy_res = con.execute(fuzzy_query).fetchone()
            print(f"Closest fuzzy match: {fuzzy_res}")
    else:
        print(f"ID {test_id} not found in ferc1_respondents.")

except Exception as e:
    print(f"Error tracing ID: {e}")

con.close()
