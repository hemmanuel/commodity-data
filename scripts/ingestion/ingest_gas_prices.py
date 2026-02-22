import duckdb
import json
import re
from datetime import datetime

# Database path
db_path = "data/commodity_data.duckdb"
ng_file_path = "data/raw/eia/bulk_ng/NG.txt"

# Connect to DuckDB
con = duckdb.connect(db_path)

# Create table
con.execute("""
    CREATE TABLE IF NOT EXISTS fact_gas_prices_monthly (
        date DATE,
        location VARCHAR,
        type VARCHAR, -- 'Citygate', 'Hub'
        value DOUBLE,
        series_id VARCHAR,
        unit VARCHAR,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

con.execute("DELETE FROM fact_gas_prices_monthly")

# Regex patterns
# Citygate: NG.N3050{State}3.M
re_citygate = re.compile(r"^NG\.N3050([A-Z]{2})3\.M$")
# Henry Hub: NG.RNGWHHD.M
re_henry = re.compile(r"^NG\.RNGWHHD\.M$")

print("Processing NG.txt for Prices...")
rows = []
BATCH_SIZE = 10000

with open(ng_file_path, 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            series_id = data.get('series_id')
            
            if not series_id:
                continue
                
            # Check for Citygate
            match_cg = re_citygate.match(series_id)
            if match_cg:
                state = match_cg.group(1)
                unit = data.get('units')
                for d in data.get('data', []):
                    date_str = d[0]
                    val = d[1]
                    if val is not None:
                        dt = datetime.strptime(date_str, "%Y%m").date()
                        rows.append((dt, state, 'Citygate', val, series_id, unit))
                continue

            # Check for Henry Hub
            if re_henry.match(series_id):
                unit = data.get('units')
                for d in data.get('data', []):
                    date_str = d[0]
                    val = d[1]
                    if val is not None:
                        dt = datetime.strptime(date_str, "%Y%m").date()
                        rows.append((dt, 'Henry Hub', 'Hub', val, series_id, unit))
                continue

            if len(rows) >= BATCH_SIZE:
                con.executemany("INSERT INTO fact_gas_prices_monthly (date, location, type, value, series_id, unit) VALUES (?, ?, ?, ?, ?, ?)", rows)
                rows = []

        except json.JSONDecodeError:
            continue
        except Exception as e:
            pass

if rows:
    con.executemany("INSERT INTO fact_gas_prices_monthly (date, location, type, value, series_id, unit) VALUES (?, ?, ?, ?, ?, ?)", rows)

print("Ingestion complete.")
con.close()
