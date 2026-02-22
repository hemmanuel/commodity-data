import requests
import json
import re

url = "https://data.ferc.gov/form-no.-552-download-data/form-552-master-table/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers)

m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    
    # Dump it to a file for inspection
    with open("next_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Dumped next_data.json")
    
    # Recursively find any string containing "csv" or "download"
    def find_strings(obj):
        if isinstance(obj, str) and ("csv" in obj.lower() or "download" in obj.lower() or "api/" in obj.lower() or "dataset" in obj.lower()):
            print("Found:", obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                find_strings(v)
        elif isinstance(obj, list):
            for i in obj:
                find_strings(i)

    find_strings(data)
else:
    print("No __NEXT_DATA__ found")
