"""
Download FERC Form 552 Master Table CSV file.
"""
import requests
import os
import json

def download_ferc_552_master():
    """Download the FERC Form 552 Master Table CSV file."""
    
    # FERC uses a Next.js app with embedded data
    # The dataset ID is pfdp_dataset_id: 0 according to the page metadata
    # Let's try to use selenium or requests to trigger the export
    
    # First, try the direct database export API
    # FERC's new portal uses internal APIs - let's try common patterns
    
    possible_urls = [
        # Try the pfdp (portal) API endpoint
        "https://data.ferc.gov/api/datasets/form-552-master-table/export?format=csv",
        "https://data.ferc.gov/api/export/form-552-master-table?format=csv",
        # Try direct table export
        "https://data.ferc.gov/api/data/form-no.-552-download-data/form-552-master-table/export?format=csv",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/csv,application/csv,*/*',
        'Referer': 'https://data.ferc.gov/form-no.-552-download-data/form-552-master-table/'
    }
    
    for url in possible_urls:
        print(f"\nTrying: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200 and len(response.content) > 1000:
                # Likely got the CSV file
                output_path = "data/raw/ferc/Form552_Master.csv"
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✓ Successfully downloaded to: {output_path}")
                print(f"File size: {len(response.content):,} bytes")
                
                # Read and display first few lines
                with open(output_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]
                    print("\nFirst 5 lines:")
                    for i, line in enumerate(lines, 1):
                        print(f"{i}: {line.rstrip()}")
                
                return output_path
            else:
                print(f"  Status: {response.status_code}, Size: {len(response.content)} bytes")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n⚠ Could not find working download URL")
    print("The FERC portal may require JavaScript/session to export data.")
    print("\nPlease manually download from:")
    print("https://data.ferc.gov/form-no.-552-download-data/form-552-master-table/")
    print("Click 'Download' button, select 'Dataset', choose 'CSV' format")
    
    return None

if __name__ == "__main__":
    download_ferc_552_master()
