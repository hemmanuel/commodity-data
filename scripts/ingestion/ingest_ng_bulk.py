import duckdb
import json
import re
import os
from datetime import datetime

# Database path
db_path = "data/commodity_data.duckdb"
ng_file_path = "data/raw/eia/bulk_ng/NG.txt"

# Connect to DuckDB
con = duckdb.connect(db_path)

# Create tables
con.execute("""
    CREATE TABLE IF NOT EXISTS fact_production_monthly (
        date DATE,
        state VARCHAR,
        value DOUBLE,
        series_id VARCHAR,
        unit VARCHAR,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

con.execute("""
    CREATE TABLE IF NOT EXISTS fact_interstate_flow_annual (
        year INTEGER,
        from_state VARCHAR,
        to_state VARCHAR,
        value DOUBLE,
        series_id VARCHAR,
        unit VARCHAR,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

# Regex patterns
# Marketed Production: NG.N9050{State}2.M
re_production = re.compile(r"^NG\.N9050([A-Z]{2})2\.M$")

# Flow based on NAME
# Pattern: "{State} Natural Gas Interstate Receipts From {FromState}, Annual"
# Also handles "Net Receipts" but we prefer "Interstate Receipts" if available.
# The previous debug showed "Interstate Receipts From" is common.
re_flow_name = re.compile(r"^(.+) Natural Gas Interstate Receipts [Ff]rom (.+), Annual$")

# Helper to map state names to codes
state_map = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC", "Federal Offshore--Gulf of Mexico": "GM",
    "Federal Offshore--Gulf of America": "GM"
}

print("Processing NG.txt...")
count_prod = 0
count_flow = 0
rows_prod = []
rows_flow = []
BATCH_SIZE = 10000

# Clear existing data to avoid duplicates (optional, but good for re-runs)
con.execute("DELETE FROM fact_production_monthly")
con.execute("DELETE FROM fact_interstate_flow_annual")

with open(ng_file_path, 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            series_id = data.get('series_id')
            name = data.get('name')
            
            if not series_id:
                continue
                
            # Check for Production (ID based)
            match_prod = re_production.match(series_id)
            if match_prod:
                state_code = match_prod.group(1)
                unit = data.get('units')
                for d in data.get('data', []):
                    date_str = d[0]
                    val = d[1]
                    if val is not None:
                        dt = datetime.strptime(date_str, "%Y%m").date()
                        rows_prod.append((dt, state_code, val, series_id, unit))
                
                if len(rows_prod) >= BATCH_SIZE:
                    con.executemany("INSERT INTO fact_production_monthly (date, state, value, series_id, unit) VALUES (?, ?, ?, ?, ?)", rows_prod)
                    count_prod += len(rows_prod)
                    rows_prod = []
                continue

            # Check for Flow (Name based)
            # We look for "Interstate Receipts From"
            if "Interstate Receipts" in name and "From" in name:
                match_flow = re_flow_name.match(name)
                if match_flow:
                    to_state_name = match_flow.group(1).strip()
                    from_state_name = match_flow.group(2).strip()
                    
                    # Skip aggregates
                    if "All States" in from_state_name or "Total" in from_state_name:
                        continue
                        
                    # Map to codes if possible
                    to_code = state_map.get(to_state_name, to_state_name)
                    from_code = state_map.get(from_state_name, from_state_name)
                    
                    unit = data.get('units')
                    for d in data.get('data', []):
                        year_str = d[0]
                        val = d[1]
                        if val is not None:
                            try:
                                year = int(year_str)
                                rows_flow.append((year, from_code, to_code, val, series_id, unit))
                            except:
                                pass
                    
                    if len(rows_flow) >= BATCH_SIZE:
                        con.executemany("INSERT INTO fact_interstate_flow_annual (year, from_state, to_state, value, series_id, unit) VALUES (?, ?, ?, ?, ?, ?)", rows_flow)
                        count_flow += len(rows_flow)
                        rows_flow = []

        except json.JSONDecodeError:
            continue
        except Exception as e:
            pass

# Insert remaining
if rows_prod:
    con.executemany("INSERT INTO fact_production_monthly (date, state, value, series_id, unit) VALUES (?, ?, ?, ?, ?)", rows_prod)
    count_prod += len(rows_prod)

if rows_flow:
    con.executemany("INSERT INTO fact_interstate_flow_annual (year, from_state, to_state, value, series_id, unit) VALUES (?, ?, ?, ?, ?, ?)", rows_flow)
    count_flow += len(rows_flow)

print(f"Ingested {count_prod} production records.")
print(f"Ingested {count_flow} flow records.")

con.close()
