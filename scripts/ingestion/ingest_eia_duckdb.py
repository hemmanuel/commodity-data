import pandas as pd
import requests
import io
import duckdb
import os
import zipfile
import glob
import argparse
import sys
import json
import time

# Configuration
DATA_DIR = 'data/raw/eia'
DB_PATH = 'data/commodity_data.duckdb'
TEMP_DIR = 'data/temp'
STATUS_FILE = 'data/ingestion_status.json'

def update_status(datasets_processed, total_datasets, current_dataset, series_count, rows_count):
    """Writes status to a JSON file for the monitor to read without DB locks."""
    status = {
        "datasets_processed": datasets_processed,
        "total_datasets": total_datasets,
        "current_dataset": current_dataset,
        "series_count": series_count,
        "rows_count": rows_count,
        "last_updated": time.time(),
        "status": "running"
    }
    try:
        # Atomic write (write to temp then rename)
        temp_file = STATUS_FILE + '.tmp'
        with open(temp_file, 'w') as f:
            json.dump(status, f)
        os.replace(temp_file, STATUS_FILE)
    except Exception as e:
        print(f"Warning: Could not update status file: {e}")

def setup_database(con):
    """Creates the necessary tables if they don't exist."""
    print("Setting up database schema...")
    
    con.execute("""
        CREATE TABLE IF NOT EXISTS eia_series (
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
        CREATE TABLE IF NOT EXISTS eia_data (
            series_id VARCHAR,
            date DATE,
            value DOUBLE
        );
    """)
    
    con.execute("CREATE INDEX IF NOT EXISTS idx_eia_data_series_date ON eia_data(series_id, date);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_eia_series_dataset ON eia_series(dataset);")

def process_zip_file(con, zip_path):
    """Processes a single ZIP file and ingests it into DuckDB."""
    dataset_name = os.path.basename(zip_path).replace('.zip', '')
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

def process_eia_storage_xls(con):
    """Downloads and ingests the EIA Weekly Natural Gas Underground Storage XLS directly."""
    print("=== Processing EIA Weekly Underground Storage ===")
    url = "https://www.eia.gov/dnav/ng/xls/NG_STOR_WKLY_S1_W.xls"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    print(f"Downloading {url}...")
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Failed to download EIA data. Status: {resp.status_code}")
            return False
            
        # Save to disk so there is a raw artifact
        raw_path = os.path.join(DATA_DIR, 'NG_STOR_WKLY_S1_W.xls')
        with open(raw_path, 'wb') as f:
            f.write(resp.content)
        print(f"Saved raw file to {raw_path}")
            
        # Parse Excel
        df = pd.read_excel(raw_path, sheet_name='Data 1', skiprows=2)
        if 'Date' not in df.columns:
            print("Invalid format: 'Date' column not found.")
            return False
            
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        
        # Melt to long format
        id_vars = ['Date']
        value_vars = [col for col in df.columns if col != 'Date']
        melted = df.melt(id_vars=id_vars, value_vars=value_vars, var_name='name', value_name='value')
        
        # Generate series metadata
        series_data = []
        for name in value_vars:
            # Generate a cleaner series ID
            short_name = name.replace('Weekly ', '').replace(' Natural Gas Working Underground Storage (Billion Cubic Feet)', '').strip()
            series_id = "EIA_NG_STORAGE_" + short_name.upper().replace(' ', '_').replace('__', '_')
            
            series_data.append({
                'series_id': series_id,
                'name': name,
                'units': 'Billion Cubic Feet',
                'frequency': 'W',
                'description': name,
                'source': 'EIA',
                'dataset': 'NG_STOR_WKLY',
                'last_updated': str(df['Date'].max()),
                'start_date': str(df['Date'].min()),
                'end_date': str(df['Date'].max())
            })
            
            # Update the name in melted to be the series_id
            melted.loc[melted['name'] == name, 'series_id'] = series_id
            
        # Insert metadata
        df_series = pd.DataFrame(series_data)
        con.execute("DELETE FROM eia_series WHERE dataset = 'NG_STOR_WKLY'")
        con.execute("INSERT INTO eia_series SELECT * FROM df_series")
        print(f"Inserted {len(df_series)} series metadata records.")
        
        # Insert data
        melted = melted[['series_id', 'Date', 'value']].rename(columns={'Date': 'date'})
        melted = melted.dropna(subset=['value'])
        con.execute("DELETE FROM eia_data WHERE series_id IN (SELECT series_id FROM df_series)")
        con.execute("INSERT INTO eia_data SELECT * FROM melted")
        print(f"Inserted {len(melted)} data points.")
        return True
        
    except Exception as e:
        print(f"Error processing EIA Storage XLS: {e}")
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
    if args.limit is not None:
        print(f"Limiting processing to {args.limit} files.")
        zip_files = zip_files[:args.limit]
    
    total_files = len(zip_files)
    processed_count = 0
    
    # Initial status update
    update_status(0, total_files, "Starting...", 0, 0)

    for i, zip_path in enumerate(zip_files):
        dataset_name = os.path.basename(zip_path)
        
        # Get current stats for status update
        try:
            series_count = con.execute("SELECT COUNT(*) FROM eia_series").fetchone()[0]
            rows_count = con.execute("SELECT COUNT(*) FROM eia_data").fetchone()[0]
        except:
            series_count = 0
            rows_count = 0
            
        update_status(processed_count, total_files, dataset_name, series_count, rows_count)
        
        if process_zip_file(con, zip_path):
            processed_count += 1
    
    print("\nProcessing batch complete.")
    
    # Process EIA Weekly Storage XLS
    process_eia_storage_xls(con)
    
    # Final status update
    try:
        series_count = con.execute("SELECT COUNT(*) FROM eia_series").fetchone()[0]
        rows_count = con.execute("SELECT COUNT(*) FROM eia_data").fetchone()[0]
        
        print(f"Total Series in DB: {series_count}")
        print(f"Total Data Points in DB: {rows_count}")
        
        # Write "completed" status
        with open(STATUS_FILE, 'w') as f:
            json.dump({
                "datasets_processed": processed_count,
                "total_datasets": total_files,
                "current_dataset": "Done",
                "series_count": series_count,
                "rows_count": rows_count,
                "last_updated": time.time(),
                "status": "completed"
            }, f)
            
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
