import json

file_path = "data/raw/eia/bulk_ng/NG.txt"

print("--- Searching for Waha ---")
with open(file_path, 'r') as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            name = data.get('name', '')
            if "Waha" in name:
                print(f"ID: {data.get('series_id')} | Name: {name}")
        except:
            pass
