import requests
import zipfile
import io
import pandas as pd
import duckdb
import os

# Setup
db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)
raw_dir = "data/raw/cftc"
os.makedirs(raw_dir, exist_ok=True)

# URL for 2024 Disaggregated Futures Only (Text)
url = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_2024.zip"
print(f"Downloading {url}...")

try:
    r = requests.get(url)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    file_name = z.namelist()[0]
    print(f"Extracting {file_name}...")
    z.extract(file_name, raw_dir)
    
    file_path = os.path.join(raw_dir, file_name)
    
    # Read first few lines to check format
    with open(file_path, 'r') as f:
        print("\nFirst 5 lines:")
        for _ in range(5):
            print(f.readline().strip())
            
    # Try reading with pandas
    # Usually comma delimited
    df = pd.read_csv(file_path, low_memory=False)
    print("\nColumns:", df.columns.tolist())
    print("\nHead:", df.head(2).to_string())
    
    # Filter for Crude Oil
    # Look for "CRUDE OIL, LIGHT SWEET" in "Market_and_Exchange_Names"
    # Column names might be different, let's check
    
except Exception as e:
    print(f"Error: {e}")
