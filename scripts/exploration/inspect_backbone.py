import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

# Tables focused on entities and relationships
tables = [
    "dim_companies",
    "dim_pipelines",
    "links_ownership",
    "links_corporate",
    "ferc_respondents",
    "ferc1_respondents",
    "ferc_form552_master",
    "spatial_pipelines",
    "eia860_generators"
]

print("## Deterministic Backbone Inspection\n")

for table in tables:
    try:
        print(f"### {table}")
        # Get schema
        schema = con.execute(f"DESCRIBE {table}").fetchdf()
        cols = schema['column_name'].tolist()
        print(f"Columns: {', '.join(cols)}")
        
        # Get row count
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"Row Count: {count}")

        # Sample data to see the quality of identifiers
        if count > 0:
            sample = con.execute(f"SELECT * FROM {table} LIMIT 3").fetchdf()
            print("Sample Data:")
            print(sample.to_string(index=False))
        else:
            print("Status: EMPTY")
            
        print("\n" + "-"*40 + "\n")

    except Exception as e:
        print(f"### {table}: Error - {e}\n")

# Specific checks for connectivity

# 1. Check if FERC 552 connects buyers and sellers
print("### Connectivity Check: FERC 552 Transactions")
try:
    # Check if we can link respondents to companies
    query = """
    SELECT 
        Reporting_Company, 
        Respondent, 
        Reporting_Co_Is_Affiliate,
        COUNT(*) as records
    FROM ferc_form552_master 
    GROUP BY 1, 2, 3
    ORDER BY 4 DESC
    LIMIT 5
    """
    print(con.execute(query).fetchdf().to_string())
except Exception as e:
    print(f"Error: {e}")

print("\n" + "-"*40 + "\n")

# 2. Check Ownership Links (Plant -> Utility)
print("### Connectivity Check: Plant Ownership (EIA 860)")
try:
    query = """
    SELECT 
        utility_id, 
        utility_name, 
        plant_code, 
        plant_name, 
        ownership_percent
    FROM eia860_generators 
    WHERE ownership_percent IS NOT NULL 
    LIMIT 5
    """
    # Note: eia860_generators might not have ownership_percent directly if it's in a separate table, checking schema first is better but I'll try this.
    # Actually, let's just check the columns of eia860_generators first in the loop above.
    # I'll write a safer query based on standard EIA 860 columns usually present.
    query = """
    SELECT 
        utility_id, 
        utility_name, 
        plant_code, 
        plant_name
    FROM eia860_generators 
    LIMIT 5
    """
    print(con.execute(query).fetchdf().to_string())
except Exception as e:
    print(f"Error: {e}")

con.close()
