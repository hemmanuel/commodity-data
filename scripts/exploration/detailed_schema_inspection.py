import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

tables_to_inspect = [
    "eia_data",
    "fact_production_monthly",
    "fact_interstate_flow_annual",
    "fact_pipeline_capacity",
    "fact_gas_prices_monthly",
    "ferc1_respondents",
    "ferc1_income_statement",
    "ferc_respondents",
    "ferc_income_statement",
    "ferc_form552_master",
    "spatial_pipelines",
    "spatial_compressors"
]

print("## Detailed Schema Information")
print(f"Database: {db_path}\n")

for table in tables_to_inspect:
    try:
        print(f"### Table: {table}")
        # Get schema
        schema = con.execute(f"DESCRIBE {table}").fetchdf()
        # Get a sample row to see what the data looks like
        sample = con.execute(f"SELECT * FROM {table} LIMIT 1").fetchdf()
        
        print("Columns:")
        for _, row in schema.iterrows():
            col_name = row['column_name']
            col_type = row['column_type']
            print(f"- {col_name} ({col_type})")
            
        print("\nSample Data (First Row):")
        if not sample.empty:
            for col in sample.columns:
                print(f"  {col}: {sample.iloc[0][col]}")
        else:
            print("  (Table is empty)")
        print("\n" + "="*50 + "\n")
        
    except Exception as e:
        print(f"Error inspecting {table}: {e}\n")

con.close()
