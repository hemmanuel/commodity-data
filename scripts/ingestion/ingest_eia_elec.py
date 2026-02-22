import duckdb
import os
import zipfile
import json
import time

# Configuration
DATA_DIR = 'data/raw/eia'
DB_PATH = 'data/commodity_data.duckdb'
TEMP_DIR = 'data/temp/eia_elec'

def process_zip_file(con, zip_path):
    dataset_name = 'ELEC'
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
            # Delete existing ELEC data to avoid duplicates (though we don't have unique constraint on data table yet)
            # Actually, let's just delete for this dataset first to be clean
            con.execute("DELETE FROM eia_data WHERE series_id IN (SELECT series_id FROM staging_json)")
            
            con.execute("""
                    INSERT INTO eia_data
                    SELECT 
                        t.series_id,
                        CASE 
                            WHEN LENGTH(unnested.d[1]) = 4 THEN TRY_CAST(strptime(unnested.d[1], '%Y') AS DATE)
                            WHEN LENGTH(unnested.d[1]) = 6 AND unnested.d[1] LIKE '%Q%' THEN 
                                -- Handle Quarterly (e.g., 2024Q1)
                                TRY_CAST(strptime(
                                    SUBSTR(unnested.d[1], 1, 4) || '-' || 
                                    CASE SUBSTR(unnested.d[1], 6, 1)
                                        WHEN '1' THEN '01'
                                        WHEN '2' THEN '04'
                                        WHEN '3' THEN '07'
                                        WHEN '4' THEN '10'
                                    END || '-01',
                                    '%Y-%m-%d'
                                ) AS DATE)
                            WHEN LENGTH(unnested.d[1]) = 6 THEN TRY_CAST(strptime(unnested.d[1], '%Y%m') AS DATE)
                            WHEN LENGTH(unnested.d[1]) = 8 THEN TRY_CAST(strptime(unnested.d[1], '%Y%m%d') AS DATE)
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
            return True

    except Exception as e:
        print(f"Error processing {dataset_name}: {e}")
        return False
    finally:
        if os.path.exists(TEMP_DIR):
            try:
                import shutil
                shutil.rmtree(TEMP_DIR)
            except:
                pass

def main():
    con = duckdb.connect(DB_PATH)
    
    zip_path = os.path.join(DATA_DIR, 'ELEC.zip')
    if os.path.exists(zip_path):
        process_zip_file(con, zip_path)
    else:
        print(f"ELEC.zip not found in {DATA_DIR}")
        
    con.close()

if __name__ == "__main__":
    main()
