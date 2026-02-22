import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Inspecting Fuzzy Matches for Accuracy\n")

# Get a sample of fuzzy matches to manually verify
query = """
    SELECT 
        l.operator_name,
        c.company_name,
        l.match_score
    FROM links_pipeline_operators l
    JOIN dim_companies c ON l.company_id = c.company_id
    WHERE l.match_type = 'FUZZY'
    ORDER BY l.match_score DESC
    LIMIT 20
"""

matches = con.execute(query).fetchdf()
print(matches.to_string(index=False))

print("\n" + "-"*40 + "\n")

# Check for potential false positives (low scores)
print("Potential False Positives (Lowest Scores):")
query_low = """
    SELECT 
        l.operator_name,
        c.company_name,
        l.match_score
    FROM links_pipeline_operators l
    JOIN dim_companies c ON l.company_id = c.company_id
    WHERE l.match_type = 'FUZZY'
    ORDER BY l.match_score ASC
    LIMIT 10
"""
matches_low = con.execute(query_low).fetchdf()
print(matches_low.to_string(index=False))

con.close()
