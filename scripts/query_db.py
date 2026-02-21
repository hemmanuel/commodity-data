import duckdb
import argparse
import sys
from tabulate import tabulate

DB_PATH = 'data/commodity_data.duckdb'

def query_db(query):
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        result = con.execute(query).fetchall()
        columns = [desc[0] for desc in con.description]
        con.close()
        return result, columns
    except Exception as e:
        return None, str(e)

def show_stats():
    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("\n=== Database Statistics ===")
    
    # Series count
    count_series = con.execute("SELECT COUNT(*) FROM eia_series").fetchone()[0]
    print(f"Total Series: {count_series:,}")
    
    # Data points count
    count_data = con.execute("SELECT COUNT(*) FROM eia_data").fetchone()[0]
    print(f"Total Data Points: {count_data:,}")
    
    # Dataset breakdown
    print("\n--- Series by Dataset ---")
    datasets = con.execute("""
        SELECT dataset, COUNT(*) as count 
        FROM eia_series 
        GROUP BY dataset 
        ORDER BY count DESC
    """).fetchall()
    print(tabulate(datasets, headers=['Dataset', 'Count'], tablefmt='simple'))
    
    con.close()

def interactive_shell():
    print("\n=== DuckDB Interactive Shell ===")
    print(f"Connected to: {DB_PATH}")
    print("Type 'exit' or 'quit' to leave.")
    print("Type 'stats' to see database statistics.")
    
    while True:
        try:
            query = input("\nduckdb> ")
            if query.lower() in ('exit', 'quit'):
                break
            if query.lower() == 'stats':
                show_stats()
                continue
            if not query.strip():
                continue
                
            result, columns = query_db(query)
            
            if isinstance(columns, str): # Error message
                print(f"Error: {columns}")
            else:
                print(tabulate(result, headers=columns, tablefmt='psql'))
                print(f"({len(result)} rows)")
                
        except KeyboardInterrupt:
            print("\nInterrupted")
        except EOFError:
            break

def main():
    parser = argparse.ArgumentParser(description='Query the Commodity Data DuckDB.')
    parser.add_argument('query', nargs='?', help='SQL query to execute')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
    elif args.query:
        result, columns = query_db(args.query)
        if isinstance(columns, str):
            print(f"Error: {columns}")
            sys.exit(1)
        print(tabulate(result, headers=columns, tablefmt='psql'))
    else:
        interactive_shell()

if __name__ == "__main__":
    main()
