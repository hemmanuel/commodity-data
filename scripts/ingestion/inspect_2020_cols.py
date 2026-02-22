import zipfile
import os
import shutil
from dbfread import DBF

ZIP_PATH = 'data/raw/ferc/Form1_2020.zip'
TEMP_DIR = 'data/temp/ferc_inspect_2020'

def inspect():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(TEMP_DIR)
        
    # Find F1_36.DBF (Income Statement)
    targets = ['F1_15.DBF', 'F1_11.DBF', 'F1_13.DBF']
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.upper() in targets:
                dbf_path = os.path.join(root, f)
                print(f"Reading {f}...")
                table = DBF(dbf_path, load=False)
                print(f"Fields: {table.field_names}")
                        
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    inspect()
