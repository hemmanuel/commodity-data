import zipfile
import os
import shutil
from dbfread import DBF

ZIP_PATH = 'data/raw/ferc/Form1_2020.zip'
TEMP_DIR = 'data/temp/ferc_inspect'

def inspect():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(TEMP_DIR)
        
    # Find all DBF files
    dbf_files = []
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.lower().endswith('.dbf'):
                dbf_files.append(os.path.join(root, f))
    
    # Search for columns
    target_cols = ['OP_REV', 'OP_EXP', 'NET_INC', 'ASSETS', 'LIABILITIES', 'CASH', 'PLANT']
    
    print(f"Scanning {len(dbf_files)} files for columns: {target_cols}...")
    
    for dbf_path in dbf_files:
        try:
            table = DBF(dbf_path, load=False)
            fields = [f.upper() for f in table.field_names]
            
            matches = [c for c in target_cols if any(c in f for f in fields)]
            
            if matches:
                print(f"\nFile: {os.path.basename(dbf_path)}")
                print(f"Matches: {matches}")
                print(f"Fields: {fields}")
                
        except Exception as e:
            pass
            
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    inspect()
