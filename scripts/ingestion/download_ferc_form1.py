import requests
import os
import time

# Configuration
DATA_DIR = 'data/raw/ferc'
DELAY_SECONDS = 3

# FERC Form 1 Data Sources (Electric Utilities)
# URL Pattern: https://forms.ferc.gov/f1allyears/f1_{year}.zip
# Years: 1994-2021 (2022+ is XBRL)

YEARS = [2020]

def download_file(url, output_path):
    if os.path.exists(output_path):
        print(f"Skipping {os.path.basename(output_path)}: Already exists.")
        return

    print(f"Downloading {os.path.basename(output_path)} from {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded {os.path.basename(output_path)}")
        time.sleep(DELAY_SECONDS)
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print(f"Starting FERC Form 1 data download to {DATA_DIR}...")
    
    for year in YEARS:
        url = f"https://forms.ferc.gov/f1allyears/f1_{year}.zip"
        filename = f"Form1_{year}.zip"
        output_path = os.path.join(DATA_DIR, filename)
        
        download_file(url, output_path)

    print("\nDownload batch complete.")

if __name__ == "__main__":
    main()
