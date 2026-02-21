import json
import os
import time
import requests
from urllib.parse import urlparse

# Configuration
MANIFEST_PATH = 'formatted_manifest.json'
OUTPUT_DIR = 'data/raw/eia'
DELAY_SECONDS = 2  # Respect rate limits

def download_file(url, output_dir):
    """Downloads a file from a URL to the specified directory."""
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            print(f"Skipping {url}: Could not determine filename.")
            return

        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            print(f"Skipping {filename}: Already exists.")
            return

        print(f"Downloading {filename} from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded {filename}")
        time.sleep(DELAY_SECONDS)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
    except Exception as e:
        print(f"An error occurred processing {url}: {e}")

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read manifest
    try:
        with open(MANIFEST_PATH, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Manifest file not found at {MANIFEST_PATH}")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {MANIFEST_PATH}")
        return

    datasets = data.get('dataset', {})
    
    print(f"Found {len(datasets)} datasets in manifest.")

    for key, info in datasets.items():
        access_url = info.get('accessURL')
        if access_url:
            download_file(access_url, OUTPUT_DIR)
        else:
            print(f"Warning: No accessURL found for dataset {key}")

if __name__ == "__main__":
    main()
