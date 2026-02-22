import json

file_path = "data/raw/eia/bulk_ng/NG.txt"

print("--- Searching for ALL Spot Prices ---")
count = 0
with open(file_path, 'r') as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            name = data.get('name', '')
            
            if "Spot Price" in name:
                print(f"ID: {data.get('series_id')} | Name: {name}")
                count += 1
                if count > 20:
                    break
        except:
            pass
