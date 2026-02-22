import duckdb
import os

db_path = "data/commodity_data.duckdb"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit()

con = duckdb.connect(db_path)

# Get all tables
tables = con.execute("SHOW TABLES").fetchall()

print("## Database Statistics")
print(f"Database Path: {db_path}")
print("-" * 60)
print(f"{'Table Name':<40} | {'Row Count':<15}")
print("-" * 60)

total_rows = 0
for table in tables:
    table_name = table[0]
    try:
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"{table_name:<40} | {count:<15,}")
        total_rows += count
    except Exception as e:
        print(f"{table_name:<40} | Error: {e}")

print("-" * 60)
print(f"{'Total Rows':<40} | {total_rows:<15,}")
