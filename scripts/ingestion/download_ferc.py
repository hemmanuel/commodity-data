import requests
import os
import time
import zipfile
from urllib.parse import urlparse

# Configuration
DATA_DIR = 'data/raw/ferc'
DELAY_SECONDS = 3  # Respectful delay

# FERC Data Sources — see docs/ferc_forms_roadmap.md for full form list and bulk-availability status
DATASETS = {
    # Form 552: Annual Report of Natural Gas Transactions (data.ferc.gov)
    "Form552_Master": "https://data.ferc.gov/api/views/3b6k-i9yd/rows.csv?accessType=DOWNLOAD",
    # Form 552 Page 3 (Schedule of Reporting Companies / Price Index) — add view ID when confirmed
    # "Form552_Page3": "https://data.ferc.gov/api/views/XXXX/rows.csv?accessType=DOWNLOAD",

    # Form 2: Major Natural Gas Pipeline Annual Report (Historical VFP)
    # 1996–2021 only: FERC has not published 2022+ at https://forms.ferc.gov/f2allyears/
    # For newer years check: https://www.ferc.gov/industries-data/natural-gas/industry-forms/form-2-2a-3-q-gas-historical-vfp-data
    "Form2_2021": "https://forms.ferc.gov/f2allyears/f2_2021.zip",
    "Form2_2020": "https://forms.ferc.gov/f2allyears/f2_2020.zip",
    "Form2_2019": "https://forms.ferc.gov/f2allyears/f2_2019.zip",
    "Form2_2018": "https://forms.ferc.gov/f2allyears/f2_2018.zip",
    "Form2_2017": "https://forms.ferc.gov/f2allyears/f2_2017.zip",
    "Form2_2016": "https://forms.ferc.gov/f2allyears/f2_2016.zip",
    "Form2_2015": "https://forms.ferc.gov/f2allyears/f2_2015.zip",
    "Form2_2014": "https://forms.ferc.gov/f2allyears/f2_2014.zip",
    "Form2_2013": "https://forms.ferc.gov/f2allyears/f2_2013.zip",
    "Form2_2012": "https://forms.ferc.gov/f2allyears/f2_2012.zip",
    "Form2_2011": "https://forms.ferc.gov/f2allyears/f2_2011.zip",
    "Form2_2010": "https://forms.ferc.gov/f2allyears/f2_2010.zip",
    "Form2_2009": "https://forms.ferc.gov/f2allyears/f2_2009.zip",
    "Form2_2008": "https://forms.ferc.gov/f2allyears/f2_2008.zip",
    "Form2_2007": "https://forms.ferc.gov/f2allyears/f2_2007.zip",
    "Form2_2006": "https://forms.ferc.gov/f2allyears/f2_2006.zip",
    "Form2_2005": "https://forms.ferc.gov/f2allyears/f2_2005.zip",
    "Form2_2004": "https://forms.ferc.gov/f2allyears/f2_2004.zip",
    "Form2_2003": "https://forms.ferc.gov/f2allyears/f2_2003.zip",
    "Form2_2002": "https://forms.ferc.gov/f2allyears/f2_2002.zip",
    "Form2_2001": "https://forms.ferc.gov/f2allyears/f2_2001.zip",
    "Form2_2000": "https://forms.ferc.gov/f2allyears/f2_2000.zip",
    "Form2_1999": "https://forms.ferc.gov/f2allyears/f2_1999.zip",
    "Form2_1998": "https://forms.ferc.gov/f2allyears/f2_1998.zip",
    "Form2_1997": "https://forms.ferc.gov/f2allyears/f2_1997.zip",
    "Form2_1996": "https://forms.ferc.gov/f2allyears/f2_1996.zip",
}

def download_file(url, output_path):
    if os.path.exists(output_path):
        print(f"Skipping {os.path.basename(output_path)}: Already exists.")
        return

    print(f"Downloading {os.path.basename(output_path)}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/csv,application/csv,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://data.ferc.gov/',
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
    
    print(f"Starting FERC data download to {DATA_DIR}...")
    print(f"Targeting {len(DATASETS)} files.")
    
    for name, url in DATASETS.items():
        # Determine extension
        if url.endswith('.zip'):
            ext = '.zip'
        elif url.endswith('.csv') or 'rows.csv' in url:
            ext = '.csv'
        else:
            ext = '.dat'
            
        filename = f"{name}{ext}"
        output_path = os.path.join(DATA_DIR, filename)
        
        download_file(url, output_path)

    print("\nDownload batch complete.")

if __name__ == "__main__":
    main()
