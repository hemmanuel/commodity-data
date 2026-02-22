import duckdb
import os
import re

DB_PATH = "data/commodity_data.duckdb"

def demonstrate_graph_potential():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("--- POTENTIAL GRAPH NODES: FUELS ---")
    # Extract Fuel from ELEC.PLANT series (usually 3rd part of name)
    # Name format: Metric : Plant (ID) : Fuel : Prime Mover : Freq
    fuels = con.execute("""
        SELECT 
            split_part(name, ' : ', 3) as fuel, 
            COUNT(*) 
        FROM eia_series 
        WHERE series_id LIKE 'ELEC.PLANT%' 
        GROUP BY fuel 
        ORDER BY 2 DESC 
        LIMIT 10
    """).fetchall()
    for f in fuels:
        print(f"Fuel Node: {f[0]} (connected to {f[1]} series)")

    print("\n--- POTENTIAL GRAPH NODES: PLANTS ---")
    # Extract Plant Name and ID
    # Regex to capture "Name (ID)"
    plants = con.execute("""
        SELECT 
            regexp_extract(name, '(.*) \\(([0-9]+)\\)', 1) as plant_name,
            regexp_extract(name, '(.*) \\(([0-9]+)\\)', 2) as plant_id,
            COUNT(*)
        FROM eia_series
        WHERE series_id LIKE 'ELEC.PLANT%'
        GROUP BY plant_name, plant_id
        ORDER BY 3 DESC
        LIMIT 10
    """).fetchall()
    for p in plants:
        if p[0] and p[1]:
            print(f"Plant Node: {p[0]} [ID: {p[1]}] (connected to {p[2]} series)")

    print("\n--- POTENTIAL GRAPH EDGES: FERC RESPONDENTS ---")
    # Just show we have companies
    companies = con.execute("""
        SELECT respondent_name, COUNT(*) 
        FROM ferc_respondents 
        GROUP BY respondent_name 
        ORDER BY 2 DESC 
        LIMIT 10
    """).fetchall()
    for c in companies:
        print(f"Company Node: {c[0]} (Reports: {c[1]})")

    con.close()

if __name__ == "__main__":
    demonstrate_graph_potential()
