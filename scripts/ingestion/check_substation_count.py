import requests
import json

URLS = [
    "https://services.arcgis.com/G4S1dGvn7PIgYd6Y/arcgis/rest/services/HIFLD_electric_power_substations/FeatureServer/0/query",
    "https://services5.arcgis.com/caWDr9qv9f34KIAZ/arcgis/rest/services/ElectricSubstations/FeatureServer/0/query"
]

for url in URLS:
    print(f"Checking {url}...")
    try:
        params = {
            "where": "1=1",
            "returnCountOnly": "true",
            "f": "json"
        }
        res = requests.get(url, params=params)
        data = res.json()
        print(data)
    except Exception as e:
        print(f"Error: {e}")
