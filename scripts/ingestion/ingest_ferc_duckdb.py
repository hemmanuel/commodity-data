import duckdb
import os
import zipfile
import glob
import time
from dbfread import DBF
import pandas as pd
import argparse
import shutil

# Configuration
DATA_DIR = 'data/raw/ferc'
DB_PATH = 'data/commodity_data.duckdb'
TEMP_DIR = 'data/temp/ferc'

def setup_database(con):
    """Creates the necessary tables if they don't exist."""
    print("Setting up FERC database schema...")
    
    # FERC Form 2 Respondent Identification (F2_1.DBF)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc_respondents (
            respondent_id VARCHAR,
            respondent_name VARCHAR,
            year INTEGER,
            report_date DATE,
            address VARCHAR,
            city VARCHAR,
            state VARCHAR,
            zip VARCHAR,
            source_file VARCHAR,
            PRIMARY KEY (respondent_id, year, source_file)
        );
    """)
    
    # FERC Form 2 System Map (F2_2.DBF - Assuming structure, need to verify)
    # We will create a generic table for pipeline data for now
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc_pipeline_data (
            respondent_id VARCHAR,
            year INTEGER,
            table_name VARCHAR,
            row_number INTEGER,
            column_name VARCHAR,
            value VARCHAR,
            source_file VARCHAR
        );
    """)

    # FERC Form 2 Income Statement (F2_114_STMT_INCOME.DBF)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc_income_statement (
            respondent_id VARCHAR,
            year INTEGER,
            row_number INTEGER,
            current_year_total DOUBLE,
            prev_year_total DOUBLE,
            current_3mon DOUBLE,
            prev_3mon DOUBLE,
            source_file VARCHAR
        );
    """)

    # FERC Form 2 Row Literals (F2_S0_ROW_LITERALS.DBF)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc_row_literals (
            year INTEGER,
            table_name VARCHAR,
            row_number INTEGER,
            row_literal VARCHAR,
            source_file VARCHAR,
            PRIMARY KEY (year, table_name, row_number)
        );
    """)

    # FERC Form 2 Balance Sheet Assets (F2_110_COMP_BAL_DEBIT.DBF)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc_balance_sheet_assets (
            respondent_id VARCHAR,
            year INTEGER,
            row_number INTEGER,
            current_year_end_balance DOUBLE,
            prev_year_end_balance DOUBLE,
            source_file VARCHAR
        );
    """)

    # FERC Form 2 Balance Sheet Liabilities (F2_112_COMP_BAL_CREDIT.DBF)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc_balance_sheet_liabilities (
            respondent_id VARCHAR,
            year INTEGER,
            row_number INTEGER,
            current_year_end_balance DOUBLE,
            prev_year_end_balance DOUBLE,
            source_file VARCHAR
        );
    """)

    # FERC Form 2 Cash Flow (F2_120_STMNT_CASH_FLOW.DBF)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ferc_cash_flow (
            respondent_id VARCHAR,
            year INTEGER,
            row_number INTEGER,
            description VARCHAR,
            current_year DOUBLE,
            prev_year DOUBLE,
            source_file VARCHAR
        );
    """)

    # Form 552 (Natural Gas Transactions): table created/replaced from CSV in process_form552_csv()

def fix_date(d, file_year):
    """Fixes date objects with invalid years based on file year."""
    if d is None:
        return None
    try:
        # If it's already a date object
        if hasattr(d, 'year'):
            year = d.year
            month = d.month
            day = d.day
            
            # If year is valid (1900-2100), return as is
            if 1900 <= year <= 2100:
                return d
            
            # Try to fix based on file year
            # If year matches last 2 digits of file year
            file_year_int = int(file_year) if file_year and file_year.isdigit() else 2000
            
            # Case: 00XX -> 20XX
            if year < 100:
                if year <= 50:
                    new_year = 2000 + year
                else:
                    new_year = 1900 + year
                return d.replace(year=new_year)
            
            # Case: 0203 -> 2003 (maybe 02 was meant to be 20?)
            # Case: 0914 -> 2014?
            # Heuristic: if last 2 digits match file year last 2 digits, use file year
            if (year % 100) == (file_year_int % 100):
                return d.replace(year=file_year_int)
            
            # Case: 3011 -> 2011
            if year == 3011:
                return d.replace(year=2011)
                
            # Fallback: use file year if it seems reasonable
            # Or just return None to be safe
            return None
            
        return d
    except:
        return None

def find_file(temp_dir, pattern):
    """Finds a file in the temp directory matching the pattern."""
    for root, dirs, files in os.walk(temp_dir):
        for f in files:
            if pattern in f.upper():
                return os.path.join(root, f)
    return None

def process_zip_file(con, zip_path):
    """Processes a single FERC Form 2 ZIP file."""
    filename = os.path.basename(zip_path)
    year = filename.replace('Form2_', '').replace('.zip', '')
    print(f"Processing FERC Form 2 for {year}...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            os.makedirs(TEMP_DIR, exist_ok=True)
            
            # Extract all files to temp
            z.extractall(TEMP_DIR)
            
            # 1. Respondent Identification (F2_001_IDENT_ATTSTTN.DBF & F2A_001_IDENT_ATTSTTN.DBF)
            records = []
            for target_table in ['F2_001_IDENT_ATTSTTN.DBF', 'F2A_001_IDENT_ATTSTTN.DBF']:
                id_table_path = find_file(TEMP_DIR, target_table)
                
                if id_table_path:
                    print(f"  Found Respondent Table: {os.path.basename(id_table_path)}")
                    
                    try:
                        table = DBF(id_table_path, load=True)
                        for record in table:
                            # Map fields
                            # Simple address parsing (very basic)
                            address_full = str(record.get('ADDR_PRIN_', '') or record.get('POC_ADDR', ''))
                            city = ''
                            state = ''
                            zip_code = ''
                            
                            if address_full:
                                parts = address_full.split(',')
                                if len(parts) >= 3:
                                    # Assume "City, State Zip" at the end
                                    state_zip = parts[-1].strip().split(' ')
                                    if len(state_zip) >= 2:
                                        zip_code = state_zip[-1]
                                        state = state_zip[-2]
                                    city = parts[-2].strip()
                            
                            records.append({
                                'respondent_id': str(record.get('RESPONDENT', '')),
                                'respondent_name': str(record.get('RESPONDEN2', '')),
                                'year': int(record.get('REPORT_YR')) if record.get('REPORT_YR') else (int(year) if year.isdigit() else None),
                                'report_date': fix_date(record.get('ATTEST_DAT'), year),
                                'address': address_full,
                                'city': city,
                                'state': state,
                                'zip': zip_code,
                                'report_prd': int(record.get('REPORT_PRD', 0)),
                                'source_file': filename
                            })
                    except Exception as e:
                        print(f"  Error reading {os.path.basename(id_table_path)}: {e}")
                else:
                    print(f"  Could not find Identification Table {target_table} in {filename}")
            
            if records:
                df = pd.DataFrame(records)
                df['report_date'] = pd.to_datetime(df['report_date'], errors='coerce').dt.date
                # Deduplicate: keep one per respondent/year (highest REPORT_PRD = annual)
                df = df.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'year'], keep='last')
                df = df.drop(columns=['report_prd'])
                
                con.execute("DELETE FROM ferc_respondents WHERE source_file = ?", [filename])
                con.execute("INSERT INTO ferc_respondents SELECT * FROM df")
                print(f"  Inserted {len(df)} respondents.")

            # 2. Row Literals (F2_S0_ROW_LITERALS.DBF)
            row_lit_path = find_file(TEMP_DIR, 'F2_S0_ROW_LITERALS.DBF')
            if row_lit_path:
                print(f"  Found Row Literals: {os.path.basename(row_lit_path)}")
                try:
                    table = DBF(row_lit_path, load=True)
                    records = []
                    for record in table:
                        records.append({
                            'year': int(record.get('REPORT_YR')) if record.get('REPORT_YR') else (int(year) if year.isdigit() else None),
                            'table_name': str(record.get('TABLE_NAME', '')),
                            'row_number': int(record.get('ROW_NUM', 0)),
                            'row_literal': str(record.get('ROW_LIT', '')),
                            'source_file': filename
                        })
                    if records:
                        df = pd.DataFrame(records)
                        con.execute("DELETE FROM ferc_row_literals WHERE source_file = ?", [filename])
                        con.execute("INSERT INTO ferc_row_literals SELECT * FROM df")
                        print(f"  Inserted {len(records)} row literals.")
                except Exception as e:
                    print(f"  Error reading {os.path.basename(row_lit_path)}: {e}")

            # 3. Income Statement (F2_114_STMT_INCOME.DBF)
            income_path = find_file(TEMP_DIR, 'F2_114_STMT_INCOME.DBF')
            if income_path:
                print(f"  Found Income Statement: {os.path.basename(income_path)}")
                try:
                    table = DBF(income_path, load=True)
                    records = []
                    for record in table:
                        records.append({
                            'respondent_id': str(record.get('RESPONDENT', '')),
                            'year': int(record.get('REPORT_YR')) if record.get('REPORT_YR') else (int(year) if year.isdigit() else None),
                            'row_number': int(record.get('ROW_NUM', 0)),
                            'current_year_total': float(record.get('TOT_YR', 0) or 0),
                            'prev_year_total': float(record.get('TOT_PREV_Y', 0) or 0),
                            'current_3mon': float(record.get('CUR_3MON', 0) or 0),
                            'prev_3mon': float(record.get('PRI_3MON', 0) or 0),
                            'report_prd': int(record.get('REPORT_PRD', 0)),
                            'source_file': filename
                        })
                    
                    if records:
                        df = pd.DataFrame(records)
                        # Deduplicate: Keep only the record with the highest REPORT_PRD for each respondent/year/row
                        df = df.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'year', 'row_number'], keep='last')
                        
                        con.execute("DELETE FROM ferc_income_statement WHERE source_file = ?", [filename])
                        con.execute("INSERT INTO ferc_income_statement (respondent_id, year, row_number, current_year_total, prev_year_total, current_3mon, prev_3mon, source_file) SELECT respondent_id, year, row_number, current_year_total, prev_year_total, current_3mon, prev_3mon, source_file FROM df")
                        print(f"  Inserted {len(df)} income records.")
                except Exception as e:
                    print(f"  Error reading {os.path.basename(income_path)}: {e}")

            # 4. Balance Sheet Assets (F2_110_COMP_BAL_DEBIT.DBF)
            assets_path = find_file(TEMP_DIR, 'F2_110_COMP_BAL_DEBIT.DBF')
            if assets_path:
                print(f"  Found Balance Sheet Assets: {os.path.basename(assets_path)}")
                try:
                    table = DBF(assets_path, load=True)
                    records = []
                    for record in table:
                        records.append({
                            'respondent_id': str(record.get('RESPONDENT', '')),
                            'year': int(record.get('REPORT_YR')) if record.get('REPORT_YR') else (int(year) if year.isdigit() else None),
                            'row_number': int(record.get('ROW_NUM', 0)),
                            'current_year_end_balance': float(record.get('BAL_END_YR', 0) or 0),
                            'prev_year_end_balance': float(record.get('BAL_PREV_Y', 0) or 0),
                            'report_prd': int(record.get('REPORT_PRD', 0)),
                            'source_file': filename
                        })
                    if records:
                        df = pd.DataFrame(records)
                        # Deduplicate: Keep only the record with the highest REPORT_PRD
                        df = df.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'year', 'row_number'], keep='last')

                        con.execute("DELETE FROM ferc_balance_sheet_assets WHERE source_file = ?", [filename])
                        con.execute("INSERT INTO ferc_balance_sheet_assets (respondent_id, year, row_number, current_year_end_balance, prev_year_end_balance, source_file) SELECT respondent_id, year, row_number, current_year_end_balance, prev_year_end_balance, source_file FROM df")
                        print(f"  Inserted {len(df)} asset records.")
                except Exception as e:
                    print(f"  Error reading {os.path.basename(assets_path)}: {e}")

            # 5. Balance Sheet Liabilities (F2_112_COMP_BAL_CREDIT.DBF)
            liab_path = find_file(TEMP_DIR, 'F2_112_COMP_BAL_CREDIT.DBF')
            if liab_path:
                print(f"  Found Balance Sheet Liabilities: {os.path.basename(liab_path)}")
                try:
                    table = DBF(liab_path, load=True)
                    records = []
                    for record in table:
                        records.append({
                            'respondent_id': str(record.get('RESPONDENT', '')),
                            'year': int(record.get('REPORT_YR')) if record.get('REPORT_YR') else (int(year) if year.isdigit() else None),
                            'row_number': int(record.get('ROW_NUM', 0)),
                            'current_year_end_balance': float(record.get('BAL_END_YR', 0) or 0),
                            'prev_year_end_balance': float(record.get('BAL_PREV_Y', 0) or 0),
                            'report_prd': int(record.get('REPORT_PRD', 0)),
                            'source_file': filename
                        })
                    if records:
                        df = pd.DataFrame(records)
                        # Deduplicate: Keep only the record with the highest REPORT_PRD
                        df = df.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'year', 'row_number'], keep='last')

                        con.execute("DELETE FROM ferc_balance_sheet_liabilities WHERE source_file = ?", [filename])
                        con.execute("INSERT INTO ferc_balance_sheet_liabilities (respondent_id, year, row_number, current_year_end_balance, prev_year_end_balance, source_file) SELECT respondent_id, year, row_number, current_year_end_balance, prev_year_end_balance, source_file FROM df")
                        print(f"  Inserted {len(df)} liability records.")
                except Exception as e:
                    print(f"  Error reading {os.path.basename(liab_path)}: {e}")

            # 6. Cash Flow (F2_120_STMNT_CASH_FLOW.DBF)
            cash_path = find_file(TEMP_DIR, 'F2_120_STMNT_CASH_FLOW.DBF')
            if cash_path:
                print(f"  Found Cash Flow: {os.path.basename(cash_path)}")
                try:
                    table = DBF(cash_path, load=True)
                    records = []
                    for record in table:
                        records.append({
                            'respondent_id': str(record.get('RESPONDENT', '')),
                            'year': int(record.get('REPORT_YR')) if record.get('REPORT_YR') else (int(year) if year.isdigit() else None),
                            'row_number': int(record.get('ROW_NUM', 0)),
                            'description': str(record.get('DESCRIPTIO', '')),
                            'current_year': float(record.get('CURR_YR', 0) or 0),
                            'prev_year': float(record.get('PREV_YR', 0) or 0),
                            'report_prd': int(record.get('REPORT_PRD', 0)),
                            'source_file': filename
                        })
                    if records:
                        df = pd.DataFrame(records)
                        # Deduplicate: Keep only the record with the highest REPORT_PRD
                        df = df.sort_values('report_prd').drop_duplicates(subset=['respondent_id', 'year', 'row_number'], keep='last')

                        con.execute("DELETE FROM ferc_cash_flow WHERE source_file = ?", [filename])
                        con.execute("INSERT INTO ferc_cash_flow (respondent_id, year, row_number, description, current_year, prev_year, source_file) SELECT respondent_id, year, row_number, description, current_year, prev_year, source_file FROM df")
                        print(f"  Inserted {len(df)} cash flow records.")
                except Exception as e:
                    print(f"  Error reading {os.path.basename(cash_path)}: {e}")
            
            # Cleanup
            shutil.rmtree(TEMP_DIR)
            
            return True

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return False

def process_form552_csv(con, csv_path):
    """Load FERC Form 552 Master (Natural Gas Transactions) CSV into DuckDB. Replaces table."""
    filename = os.path.basename(csv_path)
    print(f"Processing FERC Form 552: {filename}...")
    try:
        # Schema from CSV; add source_file for traceability
        con.execute("""
            CREATE OR REPLACE TABLE ferc_form552_master AS
            SELECT *, ?::VARCHAR AS source_file FROM read_csv_auto(?, header=true, ignore_errors=true)
        """, [filename, csv_path])
        n = con.execute("SELECT COUNT(*) FROM ferc_form552_master").fetchone()[0]
        print(f"  Loaded {n} rows into ferc_form552_master")
        return True
    except Exception as e:
        print(f"Error processing Form 552 {filename}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Ingest FERC Form 2 and Form 552 data into DuckDB.')
    parser.add_argument('--all', action='store_true', help='Process all Form 2 ZIPs. If not set, processes only the first Form 2 file for verification.')
    args = parser.parse_args()

    con = duckdb.connect(DB_PATH)
    setup_database(con)

    zip_files = glob.glob(os.path.join(DATA_DIR, 'Form2_*.zip'))
    zip_files.sort(reverse=True)  # Process newest first

    if not zip_files and not os.path.exists(os.path.join(DATA_DIR, 'Form552_Master.csv')):
        print("No FERC Form 2 ZIPs or Form552_Master.csv found in data/raw/ferc.")
        con.close()
        return

    if zip_files:
        if not args.all:
            # HITL Checkpoint - Process first file only
            first_file = zip_files[0]
            if process_zip_file(con, first_file):
                print("\n" + "="*50)
                print(f"HITL CHECKPOINT: Successfully processed {os.path.basename(first_file)}")
                print("Verifying data in database...")
                try:
                    count = con.execute("SELECT COUNT(*) FROM ferc_respondents").fetchone()[0]
                    print(f"Total Respondents: {count}")
                    if count > 0:
                        print("Sample Data:")
                        sample = con.execute("SELECT * FROM ferc_respondents LIMIT 3").fetchdf()
                        print(sample)
                except Exception as e:
                    print(f"Verification failed: {e}")
                print("="*50)
                print("Verification complete. Run with --all to process all files.")
        else:
            # Process all Form 2 ZIPs
            print(f"Processing all {len(zip_files)} Form 2 files...")
            for zip_path in zip_files:
                process_zip_file(con, zip_path)

    form552_csv = os.path.join(DATA_DIR, 'Form552_Master.csv')
    if os.path.exists(form552_csv):
        process_form552_csv(con, form552_csv)

    con.close()
    
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
        except:
            pass

if __name__ == "__main__":
    main()
