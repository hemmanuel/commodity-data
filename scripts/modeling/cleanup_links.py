import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def cleanup_links():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH)
    print("Cleaning up duplicate links...")

    # Identify duplicates based on (company_id, plant_id, match_type)
    # Keep the one with the lowest link_id (first inserted)
    
    con.execute("""
        DELETE FROM links_ownership
        WHERE link_id NOT IN (
            SELECT MIN(link_id)
            FROM links_ownership
            GROUP BY company_id, plant_id, match_type
        )
    """)
    
    # Count remaining
    count = con.execute("SELECT COUNT(*) FROM links_ownership").fetchone()[0]
    print(f"Remaining unique links: {count}")
    
    con.close()

if __name__ == "__main__":
    cleanup_links()
