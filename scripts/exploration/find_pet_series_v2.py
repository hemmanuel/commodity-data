import duckdb

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Refining PET Series Search\n")

queries = [
    ("SPR", "name ILIKE '%Strategic Petroleum Reserve%'"),
    ("WTI Price", "name ILIKE '%WTI%' AND name ILIKE '%Price%'"),
    ("Brent Price", "name ILIKE '%Brent%' AND name ILIKE '%Price%'"),
    ("Refinery Util", "name ILIKE '%Refinery%' AND name ILIKE '%Utilization%'"),
    ("Crude Stocks US", "name ILIKE '%Crude Oil%' AND name ILIKE '%Stocks%' AND name ILIKE '%U.S.%' AND name NOT ILIKE '%Pipeline%'"),
    ("Distillate Stocks", "name ILIKE '%Distillate%' AND name ILIKE '%Stocks%' AND name ILIKE '%U.S.%'")
]

for label, where_clause in queries:
    print(f"### {label}")
    q = f"""
        SELECT series_id, name, units, frequency, start_date, end_date
        FROM eia_series 
        WHERE series_id LIKE 'PET.%' AND {where_clause}
        ORDER BY frequency DESC, end_date DESC
        LIMIT 5
    """
    res = con.execute(q).fetchdf()
    if not res.empty:
        print(res.to_string(index=False))
    else:
        print("No matches.")
    print("-" * 40)

con.close()
