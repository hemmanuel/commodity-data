import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Unmatched Operators Analysis\n")

query = """
    SELECT DISTINCT operator 
    FROM spatial_pipelines 
    WHERE operator NOT IN (SELECT operator_name FROM links_pipeline_operators)
    AND operator IS NOT NULL
    ORDER BY operator
"""

unmatched = con.execute(query).fetchdf()
print(f"Unmatched Count: {len(unmatched)}")
print(unmatched.to_string(index=False))

con.close()
