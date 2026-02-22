import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Tracing Ownership IDs (Corrected)\n")

# Get sample IDs
sample_ids = con.execute("SELECT DISTINCT company_id FROM links_ownership LIMIT 5").fetchdf()['company_id'].tolist()
print(f"Sample IDs: {sample_ids}")

for cid in sample_ids:
    try:
        prefix, rid = cid.split('_')
        table = "ferc1_respondents" if prefix == "F1" else "ferc_respondents"
        
        print(f"\nChecking ID {cid} -> Table {table}, ID {rid}")
        
        # Get Name from Respondent Table
        query = f"SELECT respondent_name FROM {table} WHERE CAST(respondent_id AS INTEGER) = {rid}"
        res = con.execute(query).fetchone()
        
        if res:
            name = res[0]
            print(f"  -> Found Name: '{name}'")
            
            # Check dim_companies
            # Escape single quotes in name for SQL
            safe_name = name.replace("'", "''")
            uuid_query = f"SELECT company_id FROM dim_companies WHERE company_name = '{safe_name}'"
            uuid_res = con.execute(uuid_query).fetchone()
            
            if uuid_res:
                print(f"  -> Linked to UUID: {uuid_res[0]}")
            else:
                print("  -> NO UUID match in dim_companies")
        else:
            print("  -> ID not found in respondent table")
            
    except Exception as e:
        print(f"Error processing {cid}: {e}")

con.close()
