import json

file_path = "data/raw/eia/bulk_ng/NG.txt"

print("--- Searching for Citygate Prices ---")
count = 0
with open(file_path, 'r') as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            name = data.get('name', '')
            
            if "Citygate Price" in name and "Annual" not in name:
                print(f"ID: {data.get('series_id')} | Name: {name}")
                count += 1
                if count > 10:
                    break
        except:
            pass
