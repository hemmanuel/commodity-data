import zipfile
import os
import glob
import pandas as pd
from dbfread import DBF
import shutil

DATA_DIR = 'data/raw/ferc'
TEMP_DIR = 'data/temp/ferc_literal_analysis'

def analyze_literals():
    print("Analyzing F1_84 (Row Literals) SCHED_TABL values...")
    
    zip_files = glob.glob(os.path.join(DATA_DIR, 'Form1_*.zip'))
    zip_files.sort(reverse=True)
    
    sched_tables = set()

    for zip_path in zip_files:
        try:
            if os.path.exists(TEMP_DIR):
                shutil.rmtree(TEMP_DIR)
            os.makedirs(TEMP_DIR, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Extract only F1_84.DBF
                targets = [f for f in z.namelist() if os.path.basename(f).upper() == 'F1_84.DBF']
                if targets:
                    z.extractall(TEMP_DIR, members=targets)
            
            # Read DBF
            for root, dirs, files in os.walk(TEMP_DIR):
                for f in files:
                    if f.upper() == 'F1_84.DBF':
                        dbf_path = os.path.join(root, f)
                        table = DBF(dbf_path, load=False)
                        for record in table:
                            sched_tables.add(record.get('SCHED_TABL'))
                            
        except Exception as e:
            print(f"Error reading {zip_path}: {e}")

    print("\nDistinct SCHED_TABL values found in F1_84:")
    for s in sorted(list(sched_tables)):
        print(s)

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    analyze_literals()
