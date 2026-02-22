import duckdb
import pandas as pd

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Searching for Key PET Series IDs\n")

search_terms = {
    "Cushing": ["Cushing", "Ending Stocks"],
    "SPR": ["Strategic Petroleum Reserve", "Stocks"],
    "WTI Futures": ["WTI", "Spot Price", "Futures"], # EIA might only have Spot, or Futures if listed
    "Brent Futures": ["Brent", "Spot Price", "Futures"],
    "Refinery Utilization": ["Refinery Utilization", "Operable"],
    "Crude Stocks": ["Crude Oil", "Stocks", "Total", "Commercial"],
    "Gasoline Stocks": ["Gasoline", "Stocks", "Total"],
    "Distillate Stocks": ["Distillate", "Stocks", "Total"]
}

for key, terms in search_terms.items():
    print(f"### Searching for: {key}")
    # Construct ILIKE query
    conditions = [f"name ILIKE '%{t}%'" for t in terms]
    query = f"""
        SELECT series_id, name, units, frequency, start_date, end_date
        FROM eia_series 
        WHERE series_id LIKE 'PET.%' AND {' AND '.join(conditions)}
        ORDER BY end_date DESC
        LIMIT 5
    """
    res = con.execute(query).fetchdf()
    if not res.empty:
        print(res.to_string(index=False))
    else:
        print("No matches found.")
    print("-" * 40)

con.close()
