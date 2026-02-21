import duckdb
import os
import zipfile
import glob
import argparse
import sys

# Configuration
DATA_DIR = 'data/raw/eia'
DB_PATH = 'data/commodity_data.duckdb'
TEMP_DIR = 'data/temp'

def setup_database(con):
    """Creates the necessary tables if they don't exist."""
    print("Setting up database schema...")
    
    con.execute("DROP TABLE IF EXISTS eia_data")
    con.execute("DROP TABLE IF EXISTS eia_series")
    
    con.execute("""
        CREATE TABLE eia_series (
            series_id VARCHAR PRIMARY KEY,
            name VARCHAR,
            units VARCHAR,
            frequency VARCHAR,
            description VARCHAR,
            source VARCHAR,
            dataset VARCHAR,
            last_updated VARCHAR,
            start_date VARCHAR,
            end_date VARCHAR
        );
    """)
    
    con.execute("""
        CREATE TABLE eia_data (
            series_id VARCHAR,
            date DATE,
            value DOUBLE
            -- FOREIGN KEY (series_id) REFERENCES eia_series(series_id) -- Disabled for speed/flexibility
        );
    """)
    
    con.execute("CREATE INDEX IF NOT EXISTS idx_eia_data_series_date ON eia_data(series_id, date);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_eia_series_dataset ON eia_series(dataset);")

def process_zip_file(con, zip_path):
    """Processes a single ZIP file and ingests it into DuckDB."""
    dataset_name = os.path.basename(zip_path).replace('.zip', '')
    
    # Check if already processed (simple check: do we have series from this dataset?)
    # This is optional, but good for resuming.
    # count = con.execute(f"SELECT COUNT(*) FROM eia_series WHERE dataset = '{dataset_name}'").fetchone()[0]
    # if count > 0:
    #     print(f"Skipping {dataset_name}: Already appears to be processed ({count} series found).")
    #     return True

    print(f"Processing dataset: {dataset_name}...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            file_names = z.namelist()
            target_file = None
            for name in file_names:
                if name.endswith('.txt') or name.endswith('.json'):
                    target_file = name
                    break
            
            if not target_file:
                print(f"Skipping {dataset_name}: No suitable text/json file found.")
                return False

            print(f"Extracting {target_file}...")
            os.makedirs(TEMP_DIR, exist_ok=True)
            extracted_path = os.path.join(TEMP_DIR, target_file)
            
            with z.open(target_file) as source, open(extracted_path, "wb") as target:
                target.write(source.read())
            
            print(f"Ingesting {target_file} into staging...")
            
            con.execute(f"""
                CREATE OR REPLACE TEMP TABLE staging_json AS 
                SELECT * FROM read_json('{extracted_path}',
                    columns={{
                        'series_id': 'VARCHAR',
                        'name': 'VARCHAR',
                        'units': 'VARCHAR',
                        'f': 'VARCHAR',
                        'description': 'VARCHAR',
                        'source': 'VARCHAR',
                        'last_updated': 'VARCHAR',
                        'start': 'VARCHAR',
                        'end': 'VARCHAR',
                        'data': 'VARCHAR[][]'
                    }},
                    format='newline_delimited',
                    ignore_errors=true
                );
            """)
            
            print("Inserting metadata...")
            con.execute(f"""
                INSERT INTO eia_series 
                SELECT 
                    series_id, 
                    name, 
                    units, 
                    f as frequency, 
                    description, 
                    source, 
                    '{dataset_name}' as dataset,
                    last_updated,
                    "start" as start_date,
                    "end" as end_date
                FROM staging_json
                WHERE series_id IS NOT NULL
                ON CONFLICT (series_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    units = EXCLUDED.units,
                    description = EXCLUDED.description,
                    last_updated = EXCLUDED.last_updated;
            """)
            
            print("Inserting time series data...")
            # We use distinct to avoid duplicates if re-running
            # But for speed, we might skip distinct if we trust the source.
            # Let's just insert.
            
            con.execute("""
                    INSERT INTO eia_data
                    SELECT 
                        t.series_id,
                        CASE LENGTH(unnested.d[1])
                            WHEN 4 THEN TRY_CAST(strptime(unnested.d[1], '%Y') AS DATE)
                            WHEN 6 THEN TRY_CAST(strptime(unnested.d[1], '%Y%m') AS DATE)
                            WHEN 8 THEN TRY_CAST(strptime(unnested.d[1], '%Y%m%d') AS DATE)
                            ELSE NULL
                        END as date,
                        TRY_CAST(unnested.d[2] AS DOUBLE) as value
                    FROM staging_json t,
                UNNEST(t.data) AS unnested(d)
                WHERE t.series_id IS NOT NULL 
                  AND unnested.d[2] IS NOT NULL
            """)
            
            count = con.execute("SELECT COUNT(*) FROM staging_json WHERE series_id IS NOT NULL").fetchone()[0]
            print(f"Completed {dataset_name}. Processed {count} series.")
            
            con.execute("DROP TABLE IF EXISTS staging_json")
            os.remove(extracted_path)
            return True

    except Exception as e:
        print(f"Error processing {dataset_name}: {e}")
        try:
            if 'extracted_path' in locals() and os.path.exists(extracted_path):
                os.remove(extracted_path)
        except:
            pass
        return False

def main():
    parser = argparse.ArgumentParser(description='Ingest EIA data into DuckDB.')
    parser.add_argument('--limit', type=int, help='Limit the number of files to process')
    parser.add_argument('--skip', type=int, default=0, help='Number of files to skip')
    args = parser.parse_args()

    con = duckdb.connect(DB_PATH)
    setup_database(con)
    
    zip_files = glob.glob(os.path.join(DATA_DIR, '*.zip'))
    if not zip_files:
        print("No zip files found.")
        return

    zip_files.sort()
    
    # Apply skip
    if args.skip > 0:
        print(f"Skipping first {args.skip} files.")
        zip_files = zip_files[args.skip:]
    
    # Apply limit
    if args.limit:
        print(f"Limiting processing to {args.limit} files.")
        zip_files = zip_files[:args.limit]
    
    for zip_path in zip_files:
        process_zip_file(con, zip_path)
    
    print("\nProcessing batch complete.")
    
    # Verification stats
    try:
        count_series = con.execute("SELECT COUNT(*) FROM eia_series").fetchone()[0]
        count_data = con.execute("SELECT COUNT(*) FROM eia_data").fetchone()[0]
        print(f"Total Series in DB: {count_series}")
        print(f"Total Data Points in DB: {count_data}")
    except:
        pass

    if os.path.exists(TEMP_DIR):
        try:
            os.rmdir(TEMP_DIR)
        except:
            pass
            
    con.close()

if __name__ == "__main__":
    main()
