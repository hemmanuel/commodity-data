import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def analyze_structure():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("--- Distinct Sources ---")
    sources = con.execute("SELECT source, COUNT(*) FROM eia_series GROUP BY source ORDER BY 2 DESC").fetchall()
    for s in sources:
        print(s)

    print("\n--- Distinct Datasets ---")
    datasets = con.execute("SELECT dataset, COUNT(*) FROM eia_series GROUP BY dataset ORDER BY 2 DESC").fetchall()
    for d in datasets:
        print(d)
        
    print("\n--- AEO Series ID Structure (Sample) ---")
    # AEO IDs look like AEO.2015.SCENARIO.METRIC...
    aeo_samples = con.execute("""
        SELECT series_id, name 
        FROM eia_series 
        WHERE series_id LIKE 'AEO.%' 
        LIMIT 10
    """).fetchall()
    for s in aeo_samples:
        print(f"ID: {s[0]}")
        print(f"Name: {s[1]}")
        print("-" * 20)

    print("\n--- Name Structure Analysis (Colon count) ---")
    # Count how many colons are typically in names
    colon_counts = con.execute("""
        SELECT len(name) - len(replace(name, ':', '')) as colons, COUNT(*)
        FROM eia_series
        GROUP BY colons
        ORDER BY 2 DESC
    """).fetchall()
    for c in colon_counts:
        print(f"Colons: {c[0]}, Count: {c[1]}")

    print("\n--- 'Electricity' Name Components (Sample) ---")
    elec_samples = con.execute("""
        SELECT name 
        FROM eia_series 
        WHERE name LIKE 'Electricity%' 
        LIMIT 20
    """).fetchall()
    for s in elec_samples:
        print(s[0])

    con.close()

if __name__ == "__main__":
    analyze_structure()
