import duckdb
import pandas as pd
import os
import zipfile
import warnings

warnings.simplefilter(action='ignore', category=UserWarning)

DB_PATH = 'data/commodity_data.duckdb'
DATA_DIR = 'data/raw/eia_bulk'

# Column Mappings
EIA860_MAP = {
    'Utility ID': 'utility_id',
    'Utility Name': 'utility_name',
    'Plant Code': 'plant_code',
    'Plant Name': 'plant_name',
    'State': 'state',
    'Generator ID': 'generator_id',
    'Technology': 'technology',
    'Prime Mover': 'prime_mover',
    'Status': 'status',
    'Nameplate Capacity (MW)': 'nameplate_capacity_mw',
    'Summer Capacity (MW)': 'summer_capacity_mw',
    'Winter Capacity (MW)': 'winter_capacity_mw',
    'Energy Source 1': 'energy_source_1',
    'Operating Year': 'operating_year',
    'Planned Retirement Year': 'planned_retirement_year'
}

EIA923_MAP = {
    'Plant Id': 'plant_id',
    'Plant Name': 'plant_name',
    'Operator Name': 'operator_name',
    'Operator Id': 'operator_id',
    'Plant State': 'state',
    'Census Region': 'census_region',
    'NERC Region': 'nerc_region',
    'NAICS Code': 'naics_code',
    'Sector Number': 'sector_number',
    'Sector Name': 'sector_name',
    'Reported Prime Mover': 'prime_mover',
    'Reported Fuel Type Code': 'energy_source',
    'Net Generation (Megawatthours)': 'net_generation_mwh',
    'Elec Fuel Consumption MMBtu': 'elec_fuel_consumption_mmbtu',
    'Total Fuel Consumption MMBtu': 'total_fuel_consumption_mmbtu',
    'Quantity': 'quantity'
}

def ingest_eia_bulk():
    con = duckdb.connect(DB_PATH)
    
    # 1. Ingest EIA-860 (Generators)
    print("\n=== Ingesting EIA-860 (Generators) ===")
    con.execute("DROP TABLE IF EXISTS eia860_generators")
    con.execute("""
        CREATE TABLE eia860_generators (
            report_year INTEGER,
            utility_id VARCHAR,
            utility_name VARCHAR,
            plant_code VARCHAR,
            plant_name VARCHAR,
            state VARCHAR,
            generator_id VARCHAR,
            technology VARCHAR,
            prime_mover VARCHAR,
            status VARCHAR,
            nameplate_capacity_mw DOUBLE,
            summer_capacity_mw DOUBLE,
            winter_capacity_mw DOUBLE,
            energy_source_1 VARCHAR,
            operating_year INTEGER,
            planned_retirement_year INTEGER
        )
    """)
    
    files = sorted([f for f in os.listdir(DATA_DIR) if f.startswith('eia860') and f.endswith('.zip')])
    for filename in files:
        year = int(filename.replace('eia860', '').replace('.zip', ''))
        print(f"Processing {filename} ({year})...")
        
        try:
            with zipfile.ZipFile(os.path.join(DATA_DIR, filename), 'r') as z:
                # Find Generator file (usually 3_1)
                gen_files = [f for f in z.namelist() if '3_1_Generator' in f]
                if not gen_files:
                    print(f"  No generator file found in {filename}")
                    continue
                
                with z.open(gen_files[0]) as f:
                    df = pd.read_excel(f, sheet_name='Operable', skiprows=1)
                    
                    # Clean column names
                    df.columns = [str(c).replace('\n', ' ').replace('  ', ' ').strip() for c in df.columns]
                    
                    # Normalize columns
                    df = df.rename(columns=EIA860_MAP)
                    df['report_year'] = year
                    
                    # Filter out footer notes (where utility_id is missing or contains "NOTE")
                    if 'utility_id' in df.columns:
                        df = df[pd.to_numeric(df['utility_id'], errors='coerce').notna()]

                    # Select only mapped columns that exist
                    cols = ['report_year'] + [c for c in EIA860_MAP.values() if c in df.columns]
                    df = df[cols]
                    
                    # Clean numeric columns
                    numeric_cols = ['nameplate_capacity_mw', 'summer_capacity_mw', 'winter_capacity_mw', 'operating_year', 'planned_retirement_year']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            
                    # Insert
                    con.execute("INSERT INTO eia860_generators BY NAME SELECT * FROM df")
                    print(f"  Inserted {len(df)} rows.")
                    
        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    # 2. Ingest EIA-923 (Generation)
    print("\n=== Ingesting EIA-923 (Generation) ===")
    con.execute("DROP TABLE IF EXISTS eia923_generation_fuel")
    con.execute("""
        CREATE TABLE eia923_generation_fuel (
            report_year INTEGER,
            plant_id VARCHAR,
            plant_name VARCHAR,
            operator_name VARCHAR,
            operator_id VARCHAR,
            state VARCHAR,
            census_region VARCHAR,
            nerc_region VARCHAR,
            naics_code VARCHAR,
            sector_number VARCHAR,
            sector_name VARCHAR,
            prime_mover VARCHAR,
            energy_source VARCHAR,
            net_generation_mwh DOUBLE,
            elec_fuel_consumption_mmbtu DOUBLE,
            total_fuel_consumption_mmbtu DOUBLE,
            quantity DOUBLE
        )
    """)
    
    files = sorted([f for f in os.listdir(DATA_DIR) if f.startswith('f923_') and f.endswith('.zip')])
    for filename in files:
        year = int(filename.replace('f923_', '').replace('.zip', ''))
        print(f"Processing {filename} ({year})...")
        
        try:
            with zipfile.ZipFile(os.path.join(DATA_DIR, filename), 'r') as z:
                # Find Schedule file
                sched_files = [f for f in z.namelist() if 'Schedules_2_3_4_5' in f]
                if not sched_files:
                    print(f"  No schedule file found in {filename}")
                    continue
                
                with z.open(sched_files[0]) as f:
                    # Header row varies, usually 5 (0-indexed) -> row 6 in Excel
                    df = pd.read_excel(f, sheet_name='Page 1 Generation and Fuel Data', skiprows=5)
                    
                    # Clean column names (remove newlines, extra spaces)
                    df.columns = [str(c).replace('\n', ' ').replace('  ', ' ').strip() for c in df.columns]
                    
                    # Normalize columns
                    df = df.rename(columns=EIA923_MAP)
                    df['report_year'] = year
                    
                    # Filter out footer notes (where plant_id is missing)
                    if 'plant_id' in df.columns:
                        df = df[pd.to_numeric(df['plant_id'], errors='coerce').notna()]
                    
                    # Select only mapped columns that exist
                    cols = ['report_year'] + [c for c in EIA923_MAP.values() if c in df.columns]
                    df = df[cols]
                    
                    # Clean numeric columns
                    numeric_cols = ['net_generation_mwh', 'elec_fuel_consumption_mmbtu', 'total_fuel_consumption_mmbtu', 'quantity']
                    for col in numeric_cols:
                        if col in df.columns:
                            # Replace '.' with NaN before converting
                            if df[col].dtype == object:
                                df[col] = df[col].replace('.', pd.NA)
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Convert all other columns to string (except report_year and numeric_cols)
                    for col in df.columns:
                        if col != 'report_year' and col not in numeric_cols:
                            df[col] = df[col].astype(str).replace(['.', 'nan', '<NA>', 'None'], None)

                    # Insert
                    con.execute("INSERT INTO eia923_generation_fuel BY NAME SELECT * FROM df")
                    print(f"  Inserted {len(df)} rows.")
                    
        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    con.close()
    print("\nIngestion complete.")

if __name__ == "__main__":
    ingest_eia_bulk()
