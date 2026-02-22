import requests
import os

URL = "https://data.ferc.gov/api/views/3b6k-i9yd/rows.csv?accessType=DOWNLOAD"
OUTPUT_PATH = "data/raw/ferc/Form552_Master.csv"

def download_552():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://data.ferc.gov/eia-data/form-552",
        "Connection": "keep-alive"
    }
    
    print(f"Attempting to download from {URL}...")
    try:
        response = requests.get(URL, headers=headers, stream=True)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            with open(OUTPUT_PATH, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Successfully downloaded to {OUTPUT_PATH}")
            # Check size
            size = os.path.getsize(OUTPUT_PATH)
            print(f"File size: {size / 1024 / 1024:.2f} MB")
        else:
            print("Failed to download.")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_552()
