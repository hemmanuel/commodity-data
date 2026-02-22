import json

file_path = "data/raw/eia/bulk_ng/NG.txt"

print("--- Searching for Spot Prices ---")
with open(file_path, 'r') as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            name = data.get('name', '')
            series_id = data.get('series_id', '')
            
            if "Spot Price" in name and ("Henry Hub" in name or "Waha" in name or "Dominion" in name):
                print(f"ID: {series_id} | Name: {name} | Units: {data.get('units')}")
                
        except:
            pass
