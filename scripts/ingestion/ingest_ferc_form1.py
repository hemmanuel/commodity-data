import duckdb
import os
import zipfile
import glob
import shutil
import pandas as pd
from dbfread import DBF
import argparse

# Configuration
DATA_DIR = 'data/raw/ferc'
DB_PATH = 'data/commodity_data.duckdb'
TEMP_DIR = 'data/temp/ferc1_ingest'

def setup_database(con):
    """Creates the necessary tables for FERC Form 1."""
    print("Setting up FERC Form 1 database schema...")
    
    # Respondents
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc1_respondents (
            respondent_id VARCHAR,
            respondent_name VARCHAR,
            year INTEGER,
            status VARCHAR,
            source_file VARCHAR,
            PRIMARY KEY (respondent_id, year)
        );
    """)

    # Income Statement (F1_36)
    # Note: DBF columns are cryptic (AMOUNTS, PREV_AMOUN, etc. depending on table)
    # We will need to map them carefully.
    # F1_36 has: RESPONDENT, REPORT_YEA, ROW_NUMBER, ROW_SEQ, ROW_PRVLG, 
    #            TOT_AMOUNT (Current Year), TOT_AMOUN2 (Previous Year), ...
    # Wait, let's verify F1_36 columns from my inspection or just dump them.
    # PUDL says F1_36 is "Statement of Income".
    
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc1_income_statement (
            respondent_id VARCHAR,
            year INTEGER,
            row_number INTEGER,
            current_year_amount DOUBLE,
            prev_year_amount DOUBLE,
            source_file VARCHAR
        );
    """)

    # Balance Sheet Assets (F1_15)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc1_balance_sheet_assets (
            respondent_id VARCHAR,
            year INTEGER,
            row_number INTEGER,
            begin_year_balance DOUBLE,
            end_year_balance DOUBLE,
            source_file VARCHAR
        );
    """)

    # Balance Sheet Liabilities (F1_11)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc1_balance_sheet_liabilities (
            respondent_id VARCHAR,
            year INTEGER,
            row_number INTEGER,
            begin_year_balance DOUBLE,
            end_year_balance DOUBLE,
            source_file VARCHAR
        );
    """)

    # Cash Flow (F1_13)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc1_cash_flow (
            respondent_id VARCHAR,
            year INTEGER,
            row_number INTEGER,
            amount DOUBLE,
            prev_amount DOUBLE,
            source_file VARCHAR
        );
    """)
    
    # Row Literals (F1_84) - To map row numbers to descriptions
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc1_row_literals (
            year INTEGER,
            row_number INTEGER,
            row_literal VARCHAR,
            table_name VARCHAR,
            source_file VARCHAR
        );
    """)

    # Steam Plants (F1_89)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc1_steam_plants (
            respondent_id VARCHAR,
            year INTEGER,
            plant_name VARCHAR,
            plant_kind VARCHAR,
            year_constructed INTEGER,
            capacity_mw DOUBLE,
            net_generation_mwh DOUBLE,
            plant_cost DOUBLE,
            fuel_cost DOUBLE,
            source_file VARCHAR
        );
    """)

def find_file(temp_dir, filename):
    """Finds a file in the temp directory (case-insensitive)."""
    for root, dirs, files in os.walk(temp_dir):
        for f in files:
            if f.upper() == filename.upper():
                return os.path.join(root, f)
    return None

def safe_int(val):
    try:
        if val is None: return 0
        if isinstance(val, (int, float)): return int(val)
        # Handle strings like '0.00'
        return int(float(str(val)))
    except:
        return 0

def process_zip_file(con, zip_path):
    filename = os.path.basename(zip_path)
    year_str = filename.replace('Form1_', '').replace('.zip', '')
    year = int(year_str) if year_str.isdigit() else None
    
    print(f"Processing {filename} (Year: {year})...")
    
    try:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(TEMP_DIR)
            
        # 1. Respondents (F1_1.DBF)
        f1_1 = find_file(TEMP_DIR, 'F1_1.DBF')
        if f1_1:
            records = []
            for r in DBF(f1_1, load=True):
                records.append({
                    'respondent_id': str(r.get('RESPONDENT', '')),
                    'respondent_name': str(r.get('RESPONDEN2', '')), # Name seems to be RESPONDEN2
                    'year': year,
                    'status': str(r.get('STATUS', '')),
                    'source_file': filename
                })
            if records:
                df = pd.DataFrame(records)
                con.execute("DELETE FROM ferc1_respondents WHERE source_file = ?", [filename])
                con.execute("INSERT INTO ferc1_respondents SELECT * FROM df")
                print(f"  Loaded {len(records)} respondents.")

        # 2. Row Literals (F1_84.DBF)
        f1_84 = find_file(TEMP_DIR, 'F1_84.DBF')
        if f1_84:
            records = []
            
            # Map FERC table names to our table names
            table_map = {
                'f1_income_stmnt': 'ferc1_income_statement',
                'f1_comp_balance_db': 'ferc1_balance_sheet_assets',
                'f1_bal_sheet_cr': 'ferc1_balance_sheet_liabilities',
                'f1_cash_flow': 'ferc1_cash_flow'
            }
            
            for r in DBF(f1_84, load=True):
                sched_table = str(r.get('SCHED_TABL', '')).lower()
                our_table = table_map.get(sched_table)
                
                if our_table:
                    records.append({
                        'year': year,
                        'row_number': safe_int(r.get('ROW_NUMBER', 0)),
                        'row_literal': str(r.get('ROW_LITERA', '')),
                        'table_name': our_table,
                        'source_file': filename
                    })
            
            if records:
                df = pd.DataFrame(records)
                con.execute("DELETE FROM ferc1_row_literals WHERE source_file = ?", [filename])
                con.execute("INSERT INTO ferc1_row_literals SELECT * FROM df")
                print(f"  Loaded {len(records)} row literals.")

        # 3. Income Statement (F1_36.DBF)
        f1_36 = find_file(TEMP_DIR, 'F1_36.DBF')
        if f1_36:
            records = []
            # Deduplicate by (respondent, row_number) keeping the one with max REPORT_PRD
            raw_data = []
            for r in DBF(f1_36, load=True):
                raw_data.append({
                    'respondent_id': str(r.get('RESPONDENT', '')),
                    'year': year,
                    'row_number': safe_int(r.get('ROW_NUMBER', 0)),
                    'current_year_amount': float(r.get('CURRENT_YR') or r.get('TOT_AMOUNT') or 0),
                    'prev_year_amount': float(r.get('PREVIOUS_Y') or r.get('TOT_AMOUN2') or 0),
                    'report_prd': safe_int(r.get('REPORT_PRD', 0)),
                    'source_file': filename
                })
            
            if raw_data:
                df_raw = pd.DataFrame(raw_data)
                # Sort by REPORT_PRD ascending, then drop duplicates keeping last (max period)
                df_dedup = df_raw.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'row_number'], keep='last')
                # Drop the report_prd column before inserting
                df = df_dedup.drop(columns=['report_prd'])
                
                con.execute("DELETE FROM ferc1_income_statement WHERE source_file = ?", [filename])
                con.execute("INSERT INTO ferc1_income_statement SELECT * FROM df")
                print(f"  Loaded {len(df)} income statement rows (deduplicated).")

        # 4. Balance Sheet Assets (F1_15.DBF)
        f1_15 = find_file(TEMP_DIR, 'F1_15.DBF')
        if f1_15:
            raw_data = []
            for r in DBF(f1_15, load=True):
                raw_data.append({
                    'respondent_id': str(r.get('RESPONDENT', '')),
                    'year': year,
                    'row_number': safe_int(r.get('ROW_NUMBER', 0)),
                    'begin_year_balance': float(r.get('BEGIN_YR_B', 0) or 0),
                    'end_year_balance': float(r.get('END_YR_BAL', 0) or 0),
                    'report_prd': safe_int(r.get('REPORT_PRD', 0)),
                    'source_file': filename
                })
            
            if raw_data:
                df_raw = pd.DataFrame(raw_data)
                df_dedup = df_raw.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'row_number'], keep='last')
                df = df_dedup.drop(columns=['report_prd'])
                
                con.execute("DELETE FROM ferc1_balance_sheet_assets WHERE source_file = ?", [filename])
                con.execute("INSERT INTO ferc1_balance_sheet_assets SELECT * FROM df")
                print(f"  Loaded {len(df)} asset rows (deduplicated).")

        # 5. Balance Sheet Liabilities (F1_11.DBF)
        f1_11 = find_file(TEMP_DIR, 'F1_11.DBF')
        if f1_11:
            raw_data = []
            for r in DBF(f1_11, load=True):
                raw_data.append({
                    'respondent_id': str(r.get('RESPONDENT', '')),
                    'year': year,
                    'row_number': safe_int(r.get('ROW_NUMBER', 0)),
                    'begin_year_balance': float(r.get('BEGIN_YR_B', 0) or 0),
                    'end_year_balance': float(r.get('END_YR_BAL', 0) or 0),
                    'report_prd': safe_int(r.get('REPORT_PRD', 0)),
                    'source_file': filename
                })
            
            if raw_data:
                df_raw = pd.DataFrame(raw_data)
                df_dedup = df_raw.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'row_number'], keep='last')
                df = df_dedup.drop(columns=['report_prd'])
                
                con.execute("DELETE FROM ferc1_balance_sheet_liabilities WHERE source_file = ?", [filename])
                con.execute("INSERT INTO ferc1_balance_sheet_liabilities SELECT * FROM df")
                print(f"  Loaded {len(df)} liability rows (deduplicated).")

        # 6. Cash Flow (F1_13.DBF)
        f1_13 = find_file(TEMP_DIR, 'F1_13.DBF')
        if f1_13:
            raw_data = []
            for r in DBF(f1_13, load=True):
                raw_data.append({
                    'respondent_id': str(r.get('RESPONDENT', '')),
                    'year': year,
                    'row_number': safe_int(r.get('ROW_NUMBER', 0)),
                    'amount': float(r.get('AMOUNTS', 0) or 0),
                    'prev_amount': float(r.get('PREV_AMOUN', 0) or 0),
                    'report_prd': safe_int(r.get('REPORT_PRD', 0)),
                    'source_file': filename
                })
            
            if raw_data:
                df_raw = pd.DataFrame(raw_data)
                df_dedup = df_raw.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'row_number'], keep='last')
                df = df_dedup.drop(columns=['report_prd'])
                
                con.execute("DELETE FROM ferc1_cash_flow WHERE source_file = ?", [filename])
                con.execute("INSERT INTO ferc1_cash_flow SELECT * FROM df")
                print(f"  Loaded {len(df)} cash flow rows (deduplicated).")

        # 7. Steam Plants (F1_89.DBF)
        f1_89 = find_file(TEMP_DIR, 'F1_89.DBF')
        if f1_89:
            records = []
            for r in DBF(f1_89, load=True):
                records.append({
                    'respondent_id': str(r.get('RESPONDENT', '')),
                    'year': year,
                    'plant_name': str(r.get('PLANT_NAME', '')),
                    'plant_kind': str(r.get('PLANT_KIND', '')),
                    'year_constructed': safe_int(r.get('YR_CONST', 0)),
                    'capacity_mw': float(r.get('TOT_CAPACI', 0) or 0),
                    'net_generation_mwh': float(r.get('NET_GENERA', 0) or 0),
                    'plant_cost': float(r.get('COST_OF_PL', 0) or 0),
                    'fuel_cost': float(r.get('EXPNS_FUEL', 0) or 0),
                    'source_file': filename
                })
            if records:
                df = pd.DataFrame(records)
                con.execute("DELETE FROM ferc1_steam_plants WHERE source_file = ?", [filename])
                con.execute("INSERT INTO ferc1_steam_plants SELECT * FROM df")
                print(f"  Loaded {len(records)} steam plants.")

    except Exception as e:
        print(f"Error processing {filename}: {e}")
    finally:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)

def main():
    con = duckdb.connect(DB_PATH)
    setup_database(con)
    
    zip_files = glob.glob(os.path.join(DATA_DIR, 'Form1_*.zip'))
    zip_files.sort(reverse=True)
    
    if not zip_files:
        print("No Form 1 ZIP files found.")
        return

    for zip_path in zip_files:
        process_zip_file(con, zip_path)
        
    con.close()

if __name__ == "__main__":
    main()
