import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def inspect_eia_names():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("Distinct Categories (First part of Name):")
    cats = con.execute("""
        SELECT split_part(name, ':', 1) as cat, COUNT(*) 
        FROM eia_series 
        GROUP BY cat 
        ORDER BY COUNT(*) DESC
        LIMIT 50
    """).fetchall()
    
    for c in cats:
        print(c)

    con.close()

if __name__ == "__main__":
    inspect_eia_names()
