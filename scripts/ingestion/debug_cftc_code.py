import requests
import zipfile
import io
import pandas as pd
import duckdb
import os

raw_dir = "data/raw/cftc"
os.makedirs(raw_dir, exist_ok=True)

url = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_2024.zip"
print(f"Downloading {url}...")

r = requests.get(url)
z = zipfile.ZipFile(io.BytesIO(r.content))
file_name = z.namelist()[0]
z.extract(file_name, raw_dir)
file_path = os.path.join(raw_dir, file_name)

df = pd.read_csv(file_path, low_memory=False)
print("\nUnique Market Names for code '067651':")
# Check if column is 'CFTC_Contract_Market_Code' or similar
code_col = [c for c in df.columns if 'Code' in c and 'Market' in c][0]
print(f"Using code column: {code_col}")

# 067651 is WTI Physical
mask = df[code_col].astype(str).str.contains('067651')
matches = df[mask]['Market_and_Exchange_Names'].unique()
for m in matches:
    print(m)

if len(matches) == 0:
    print("No matches for 067651. Listing top 10 markets by Open Interest:")
    top = df.groupby('Market_and_Exchange_Names')['Open_Interest_All'].max().sort_values(ascending=False).head(10)
    print(top)

os.remove(file_path)
