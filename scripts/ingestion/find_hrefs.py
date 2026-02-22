import requests
import re

url = "https://data.ferc.gov/form-no.-552-download-data/form-552-master-table/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers)
matches = re.findall(r'href="(.*?)"', resp.text)
for m in set(matches):
    if "data.ferc.gov" in m or "/" in m:
        if "css" not in m and "js" not in m:
            print(m)
