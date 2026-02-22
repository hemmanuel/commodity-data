import zipfile
import os
import shutil
from dbfread import DBF

ZIP_PATH = 'data/raw/ferc/Form1_2020.zip'
TEMP_DIR = 'data/temp/ferc_inspect_84'

def inspect():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(TEMP_DIR)
        
    # Find F1_84.DBF
    target = 'F1_84.DBF'
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.upper() == target:
                dbf_path = os.path.join(root, f)
                print(f"Reading {f}...")
                table = DBF(dbf_path, load=False)
                print(f"Fields: {table.field_names}")
                
                # Print first 20 records
                print("First 20 records:")
                count = 0
                for record in table:
                    print(record)
                    count += 1
                    if count >= 20: break
    
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    inspect()
