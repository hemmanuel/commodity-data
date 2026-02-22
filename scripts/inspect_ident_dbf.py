"""Inspect F2_001_IDENT_ATTSTTN.DBF to find why we get 4 duplicates per respondent/year."""
import zipfile
import os
from dbfread import DBF
import shutil

DATA_DIR = 'data/raw/ferc'
TEMP_DIR = 'data/temp/inspect_ident'
ZIP_PATH = os.path.join(DATA_DIR, 'Form2_2021.zip')

os.makedirs(TEMP_DIR, exist_ok=True)
try:
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for info in z.infolist():
            if 'F2_001_IDENT_ATTSTTN.DBF' in info.filename.upper() and 'F2A' not in info.filename.upper():
                z.extract(info, TEMP_DIR)
                path = os.path.join(TEMP_DIR, info.filename)
                table = DBF(path, load=True)
                print("Fields:", table.field_names)
                # Count records for respondent 48
                count_48 = 0
                for r in table:
                    if str(r.get('RESPONDENT')) == '48':
                        count_48 += 1
                        if count_48 <= 5:
                            print(f"  Record {count_48}: {dict(r)}")
                print(f"\nTotal records for respondent 48: {count_48}")
                break
finally:
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
