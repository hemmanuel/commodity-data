import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def inspect_eia():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("Columns in eia_series:")
    cols = con.execute("DESCRIBE eia_series").fetchall()
    for c in cols:
        print(c)

    print("\nSample Series IDs and Names:")
    samples = con.execute("SELECT series_id, name FROM eia_series LIMIT 20").fetchall()
    for s in samples:
        print(s)
        
    print("\nDistinct prefixes (first part of series_id):")
    # Assuming series_id format like SOURCE_CATEGORY_...
    # Let's try to split by underscore and count
    prefixes = con.execute("""
        SELECT split_part(series_id, '_', 2) as cat, COUNT(*) 
        FROM eia_series 
        GROUP BY cat 
        ORDER BY COUNT(*) DESC
    """).fetchall()
    for p in prefixes:
        print(p)

    con.close()

if __name__ == "__main__":
    inspect_eia()
