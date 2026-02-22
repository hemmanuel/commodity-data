import duckdb
import pandas as pd

db_path = 'data/commodity_data.duckdb'
con = duckdb.connect(db_path)

file_path = 'data/raw/eia/PIPEintra.xls'

print(f"Reading {file_path}...")
try:
    df = pd.read_excel(file_path, sheet_name='Data 1', skiprows=3)
    
    # Select relevant columns
    # 'Pipeline Name', 'Parent Company', 'Type Pipeline', 'System Capacity (MMcf/d)', 'Miles of Pipe', 'Region', 'State(s) in which it has operations'
    
    # The 'State(s)...' column might be spread across multiple columns if it was merged in Excel?
    # Let's inspect the Unnamed columns to be sure, but for now we'll take the first few.
    
    cols = ['Pipeline Name', 'Parent Company', 'Type Pipeline', 'System Capacity (MMcf/d)', 'Miles of Pipe', 'Region', 'State(s) in which it has operations']
    df = df[cols]
    
    # Rename columns
    df.columns = ['pipeline', 'parent_company', 'type', 'capacity_mmcfd', 'miles', 'region', 'states']
    
    # Clean data
    df = df.dropna(subset=['pipeline']) # Remove rows without pipeline name (e.g. region headers)
    df['capacity_mmcfd'] = pd.to_numeric(df['capacity_mmcfd'], errors='coerce')
    df['miles'] = pd.to_numeric(df['miles'], errors='coerce')
    
    print(f"Ingesting {len(df)} rows...")
    
    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_intrastate_pipelines (
            pipeline VARCHAR,
            parent_company VARCHAR,
            type VARCHAR,
            capacity_mmcfd DOUBLE,
            miles DOUBLE,
            region VARCHAR,
            states VARCHAR
        )
    """)
    
    con.execute("DELETE FROM dim_intrastate_pipelines")
    con.execute("INSERT INTO dim_intrastate_pipelines SELECT * FROM df")
    
    print("Ingestion complete.")
    
    # Verify
    count = con.execute("SELECT COUNT(*) FROM dim_intrastate_pipelines").fetchone()[0]
    print(f"Total intrastate pipelines: {count}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    con.close()
