import requests
import os
import time

# Configuration
DATA_DIR = 'data/raw/eia_bulk'
DELAY_SECONDS = 3
YEARS = range(2014, 2025) # 2014 to 2024

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.eia.gov/'
}

def is_valid_zip(filepath):
    """Check if file exists and has a valid ZIP header."""
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            return header == b'PK\x03\x04'
    except:
        return False

def download_file(url, output_path):
    if is_valid_zip(output_path):
        print(f"Skipping {os.path.basename(output_path)}: Already exists and valid.")
        return True

    print(f"Downloading {url}...")
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        
        if response.status_code == 404:
            print(f"404 Not Found: {url}")
            return False
            
        response.raise_for_status()

        # Check content type if available
        ct = response.headers.get('Content-Type', '').lower()
        if 'html' in ct:
            print(f"Skipping: Content-Type is HTML ({ct})")
            return False

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if is_valid_zip(output_path):
            print(f"Successfully downloaded {os.path.basename(output_path)}")
            time.sleep(DELAY_SECONDS)
            return True
        else:
            print(f"Downloaded file {os.path.basename(output_path)} is not a valid ZIP. Removing...")
            os.remove(output_path)
            return False
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # EIA-860 (Generators)
    print("\n=== Downloading EIA-860 (Generators) ===")
    for year in YEARS:
        filename = f"eia860{year}.zip"
        output_path = os.path.join(DATA_DIR, filename)
        
        # Try archive URL first (most likely for historical)
        url_archive = f"https://www.eia.gov/electricity/data/eia860/archive/xls/{filename}"
        # Try current URL (for recent years)
        url_current = f"https://www.eia.gov/electricity/data/eia860/xls/{filename}"
        
        if not download_file(url_archive, output_path):
            print(f"Retrying with current URL for {year}...")
            download_file(url_current, output_path)

    # EIA-923 (Generation & Fuel)
    print("\n=== Downloading EIA-923 (Generation & Fuel) ===")
    for year in YEARS:
        filename = f"f923_{year}.zip"
        output_path = os.path.join(DATA_DIR, filename)
        
        # Try archive URL first
        url_archive = f"https://www.eia.gov/electricity/data/eia923/archive/xls/{filename}"
        # Try current URL
        url_current = f"https://www.eia.gov/electricity/data/eia923/xls/{filename}"
        
        if not download_file(url_archive, output_path):
            print(f"Retrying with current URL for {year}...")
            download_file(url_current, output_path)

    print("\nDownload batch complete.")

if __name__ == "__main__":
    main()
