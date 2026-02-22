import duckdb
import os

DB_PATH = "data/commodity_data.duckdb"

def check_552():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH, read_only=True)
    
    # Check if table exists
    exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='ferc_form552_master'").fetchone()[0]
    
    if exists:
        count = con.execute("SELECT count(*) FROM ferc_form552_master").fetchone()[0]
        print(f"Table 'ferc_form552_master' EXISTS. Row count: {count}")
    else:
        print("Table 'ferc_form552_master' DOES NOT EXIST.")

    con.close()

if __name__ == "__main__":
    check_552()
