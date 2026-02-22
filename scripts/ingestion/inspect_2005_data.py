import zipfile
import os
import shutil
from dbfread import DBF

ZIP_PATH = 'data/raw/ferc/Form1_2005.zip'
TEMP_DIR = 'data/temp/ferc_inspect_2005'

def inspect():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(TEMP_DIR)
        
    # Find F1_36.DBF (Income Statement)
    target = 'F1_36.DBF'
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.upper() == target:
                dbf_path = os.path.join(root, f)
                print(f"Reading {f}...")
                table = DBF(dbf_path, load=True)
                print(f"Fields: {table.field_names}")
                
                print("\nRecords for Respondent 20, Row 2:")
                for r in table:
                    if str(r.get('RESPONDENT')) == '20' and r.get('ROW_NUMBER') == 2:
                        print(f"Row: {r.get('ROW_NUMBER')}, Period: {r.get('REPORT_PRD')}, Amount: {r.get('TOT_AMOUNT')}, Prev: {r.get('TOT_AMOUN2')}")
                        
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    inspect()
