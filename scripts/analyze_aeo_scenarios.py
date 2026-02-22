import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def analyze_aeo():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("--- AEO Scenarios (Sample) ---")
    # Extract the 3rd part of the ID (Scenario)
    # ID format: AEO.<Year>.<Scenario>.<Metric>...
    scenarios = con.execute("""
        SELECT 
            dataset,
            split_part(series_id, '.', 3) as scenario,
            COUNT(*) 
        FROM eia_series 
        WHERE series_id LIKE 'AEO.%'
        GROUP BY dataset, scenario
        ORDER BY dataset DESC, COUNT(*) DESC
        LIMIT 50
    """).fetchall()
    
    for s in scenarios:
        print(f"Dataset: {s[0]}, Scenario: {s[1]}, Count: {s[2]}")

    con.close()

if __name__ == "__main__":
    analyze_aeo()
