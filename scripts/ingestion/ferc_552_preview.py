import requests
import re

url = "https://data.ferc.gov/form-no.-552-download-data/form-552-master-table/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

print(f"Fetching {url}...")
resp = requests.get(url, headers=headers)
resp.raise_for_status()

# Look for CSV download links
matches = re.findall(r'href="([^"]+\.csv[^"]*)"', resp.text)
if not matches:
    matches = re.findall(r'href="([^"]*download[^"]*)"', resp.text, re.IGNORECASE)

csv_url = None
if matches:
    # Get the first matching URL that looks like a data download
    for match in matches:
        if "csv" in match.lower() or "dataset" in match.lower() or "download" in match.lower():
            csv_url = match
            if csv_url.startswith('/'):
                csv_url = "https://data.ferc.gov" + csv_url
            break

if csv_url:
    print(f"\nAttempting to stream first 5 lines of: {csv_url}")
    with requests.get(csv_url, headers=headers, stream=True) as r:
        if r.status_code == 200:
            lines = []
            for line in r.iter_lines():
                if line:
                    lines.append(line.decode('utf-8'))
                if len(lines) >= 5:
                    break
            
            print("\n--- HITL PREVIEW (First 5 lines) ---")
            for i, l in enumerate(lines):
                print(f"[{i}] {l[:200]}...")
        else:
            print(f"Error {r.status_code} fetching CSV.")
else:
    print("Could not find a CSV download link.")
