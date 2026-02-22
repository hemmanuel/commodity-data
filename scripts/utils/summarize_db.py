import duckdb
import pandas as pd
import os

DB_PATH = 'data/commodity_data.duckdb'

def summarize_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        
        # Get all tables
        tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name").fetchall()
        table_names = [t[0] for t in tables]
        
        print(f"=== Database Summary: {DB_PATH} ===")
        print(f"Total Tables: {len(table_names)}\n")
        
        summary_data = []
        
        for table in table_names:
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                # Get columns
                cols = con.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'").fetchall()
                col_names = [c[0] for c in cols]
                
                summary_data.append({
                    "Table": table,
                    "Rows": count,
                    "Columns": len(col_names),
                    "Column List": ", ".join(col_names[:5]) + ("..." if len(col_names) > 5 else "")
                })
            except Exception as e:
                print(f"Error reading {table}: {e}")

        # Display as DataFrame for nice formatting
        df = pd.DataFrame(summary_data)
        if not df.empty:
            # Sort by Rows desc
            df = df.sort_values('Rows', ascending=False)
            print(df.to_string(index=False))
            
            print("\n=== Detailed Schema for Key Tables ===")
            key_tables = ['dim_plants', 'dim_companies', 'links_ownership', 'eia860_generators', 'eia923_generation_fuel']
            for kt in key_tables:
                if kt in table_names:
                    print(f"\nTable: {kt}")
                    desc = con.execute(f"DESCRIBE {kt}").fetchdf()
                    print(desc[['column_name', 'column_type']].to_string(index=False))

        con.close()

    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    summarize_db()
