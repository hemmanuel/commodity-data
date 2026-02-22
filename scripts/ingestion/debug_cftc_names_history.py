import requests
import zipfile
import io
import pandas as pd
import duckdb
import os

raw_dir = "data/raw/cftc"
os.makedirs(raw_dir, exist_ok=True)

# Check 2016 (History)
url = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_hist_2006_2016.zip"
print(f"Downloading {url}...")
r = requests.get(url)
z = zipfile.ZipFile(io.BytesIO(r.content))
file_name = z.namelist()[0]
z.extract(file_name, raw_dir)
file_path = os.path.join(raw_dir, file_name)

df = pd.read_csv(file_path, low_memory=False)
print("\nUnique Market Names containing 'CRUDE' in 2006-2016:")
crude_markets = df[df['Market_and_Exchange_Names'].str.contains('CRUDE', case=False, na=False)]['Market_and_Exchange_Names'].unique()
for m in crude_markets:
    print(m)

os.remove(file_path)
