import pandas as pd
import requests
import io
import zipfile
from dbfread import DBF
import os

print("=== 1. PREVIEWING EIA WEEKLY UNDERGROUND STORAGE ===")
url = "https://www.eia.gov/dnav/ng/xls/NG_STOR_WKLY_S1_W.xls"
headers = {"User-Agent": "Mozilla/5.0"}

print(f"Downloading {url}...")
resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    # EIA XLS files usually have the data on sheet 'Data 1' starting at row 3
    df = pd.read_excel(io.BytesIO(resp.content), sheet_name='Data 1', skiprows=2)
    print("\nColumns found:", df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head(5).to_string())
else:
    print(f"Failed to download EIA data. Status: {resp.status_code}")

print("\n\n=== 2. PREVIEWING FERC FORM 2A DATA (Inside Form2_2021.zip) ===")
zip_path = "data/raw/ferc/Form2_2021.zip"
if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Extract a Form 2A file to temp (including FPT/CDX if present)
        base_name = 'UPLOADERS/FORM2/working/F2A_001_IDENT_ATTSTTN'
        for ext in ['.DBF', '.FPT', '.CDX']:
            if base_name + ext in z.namelist():
                z.extract(base_name + ext, 'data/temp')
        
        target_file = base_name + '.DBF'
        if target_file in z.namelist():
            print(f"Extracted {target_file} and associated files...")
            
            # Read with DBF
            table = DBF(os.path.join('data/temp', target_file), load=True)
            print(f"Total Form 2A Respondents in 2021: {len(table.records)}")
            print("\nFirst 3 Form 2A Respondents:")
            for i, rec in enumerate(table.records[:3]):
                print(f"[{i}] {rec.get('RESPONDENT', '')} (ID: {rec.get('RESPOND_ID', '')})")
else:
    print(f"Zip file not found: {zip_path}")
