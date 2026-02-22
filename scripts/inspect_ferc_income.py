from dbfread import DBF
import os
import zipfile
import pandas as pd

zip_path = 'data/raw/ferc/Form2_2021.zip'
temp_dir = 'data/temp/ferc_inspect_data'
os.makedirs(temp_dir, exist_ok=True)

target_file = 'UPLOADERS/FORM2/working/F2_114_STMT_INCOME.DBF'

with zipfile.ZipFile(zip_path, 'r') as z:
    z.extract(target_file, temp_dir)
    dbf_path = os.path.join(temp_dir, target_file)
    try:
        table = DBF(dbf_path)
        print(f"\nColumns in {os.path.basename(target_file)}:", table.field_names)
        print("\nFirst 3 records:")
        for i, record in enumerate(table):
            if i >= 3: break
            print(dict(record))
    except Exception as e:
        print(f"Error reading {target_file}: {e}")
