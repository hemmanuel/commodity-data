import requests
import json

# Rutgers URL
URL = "https://oceandata.rad.rutgers.edu/arcgis/rest/services/RenewableEnergy/HIFLD_Electric_SubstationsTransmissionLines/MapServer/0/query"

print(f"Checking {URL}...")
try:
    params = {
        "where": "1=1",
        "returnCountOnly": "true",
        "f": "json"
    }
    res = requests.get(URL, params=params)
    data = res.json()
    print(data)
except Exception as e:
    print(f"Error: {e}")
