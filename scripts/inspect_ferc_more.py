import zipfile
import os
import glob
from dbfread import DBF
import shutil

DATA_DIR = 'data/raw/ferc'
TEMP_DIR = 'data/temp/inspect_more'

def inspect_more_dbfs():
    zip_files = glob.glob(os.path.join(DATA_DIR, 'Form2_*.zip'))
    if not zip_files: return

    zip_path = sorted(zip_files)[-1]
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            target_files = [
                'F2_110_COMP_BAL_DEBIT.DBF',
                'F2_120_STMNT_CASH_FLOW.DBF'
            ]
            
            extracted_paths = []
            for file_info in z.infolist():
                for target in target_files:
                    if target in file_info.filename.upper():
                        z.extract(file_info, TEMP_DIR)
                        extracted_paths.append(os.path.join(TEMP_DIR, file_info.filename))
            
            for path in extracted_paths:
                print(f"\nInspecting: {os.path.basename(path)}")
                try:
                    table = DBF(path, load=True)
                    print(f"Fields: {table.field_names}")
                    # Print one record to see data types
                    for i, record in enumerate(table):
                        print(record)
                        break
                except Exception as e:
                    print(f"Error: {e}")

    finally:
        shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    inspect_more_dbfs()
