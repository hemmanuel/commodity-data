import os
import pandas as pd
import duckdb

# Database connection
db_path = 'data/commodity_data.duckdb'
con = duckdb.connect(db_path)

# File path
file_path = 'data/raw/eia/StatetoState.xlsx'
sheet_name = 'Pipeline State2State Capacity'

print(f"Reading {file_path}...")
try:
    # Read the Excel file
    # Skip the first row (header is in the second row, index 1)
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
    
    # Clean column names
    df.columns = [c.strip().lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '') for c in df.columns]
    
    # Rename specific columns for clarity
    df = df.rename(columns={
        'capacity_mmcfd': 'capacity_mmcfd',
        'region_from': 'region_from',
        'region_to': 'region_to',
        'state_from': 'state_from',
        'county_from': 'county_from',
        'state_to': 'state_to',
        'county_to': 'county_to'
    })

    # Convert year to integer
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)

    # Convert capacity to numeric
    df['capacity_mmcfd'] = pd.to_numeric(df['capacity_mmcfd'], errors='coerce')

    # Normalize state names to codes
    state_map = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
        'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH',
        'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
        'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
        'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN',
        'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
        'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY', 'District of Columbia': 'DC',
        'Gulf of America': 'GOM', 'Gulf of America - Deepwater': 'GOM_Deep',
        'Mexico': 'MX', 'Canada': 'CAN',
        'Alberta': 'AB', 'British Columbia': 'BC', 'Manitoba': 'MB', 'New Brunswick': 'NB',
        'Ontario': 'ON', 'Quebec': 'QC', 'Saskatchewan': 'SK'
    }
    
    df['state_from'] = df['state_from'].map(state_map).fillna(df['state_from'])
    df['state_to'] = df['state_to'].map(state_map).fillna(df['state_to'])

    print(f"Ingesting {len(df)} rows into DuckDB...")
    
    # Create table if not exists
    con.execute("""
        CREATE TABLE IF NOT EXISTS fact_pipeline_capacity (
            year INTEGER,
            pipeline VARCHAR,
            region_from VARCHAR,
            region_to VARCHAR,
            state_from VARCHAR,
            county_from VARCHAR,
            state_to VARCHAR,
            county_to VARCHAR,
            capacity_mmcfd DOUBLE,
            notes VARCHAR
        )
    """)
    
    # Clear existing data
    con.execute("DELETE FROM fact_pipeline_capacity")
    
    # Insert data
    con.execute("INSERT INTO fact_pipeline_capacity SELECT * FROM df")
    
    print("Ingestion complete.")
    
    # Verify
    count = con.execute("SELECT COUNT(*) FROM fact_pipeline_capacity").fetchone()[0]
    print(f"Total rows in fact_pipeline_capacity: {count}")

except Exception as e:
    print(f"Error: {e}")
finally:
    con.close()
