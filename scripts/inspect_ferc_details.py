import zipfile
import os
import glob
from dbfread import DBF
import shutil

DATA_DIR = 'data/raw/ferc'
TEMP_DIR = 'data/temp/inspect'

def inspect_dbf_files():
    zip_files = glob.glob(os.path.join(DATA_DIR, 'Form2_*.zip'))
    if not zip_files:
        print("No ZIP files found.")
        return

    zip_path = sorted(zip_files)[-1]
    print(f"Extracting from: {zip_path}")

    os.makedirs(TEMP_DIR, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Extract specific files we want to inspect
            target_files = [
                'F2_S0_ROW_LITERALS.DBF',
                'F2_114_STMT_INCOME.DBF'
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
                    print(f"Record count: {len(table)}")
                    print("First 5 records:")
                    for i, record in enumerate(table):
                        if i >= 5: break
                        print(record)
                except Exception as e:
                    print(f"Error reading DBF: {e}")

    finally:
        shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    inspect_dbf_files()
