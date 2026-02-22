import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def analyze_aeo_metrics():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("--- AEO Metrics (Sample) ---")
    # Extract the 4th part of the ID (Metric?)
    metrics = con.execute("""
        SELECT 
            split_part(series_id, '.', 4) as metric,
            COUNT(*),
            MIN(name) as example_name
        FROM eia_series 
        WHERE series_id LIKE 'AEO.%'
        GROUP BY metric
        ORDER BY COUNT(*) DESC
        LIMIT 20
    """).fetchall()
    
    for m in metrics:
        print(f"Metric: {m[0]}, Count: {m[1]}, Example: {m[2]}")

    con.close()

if __name__ == "__main__":
    analyze_aeo_metrics()
