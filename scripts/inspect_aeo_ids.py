import zipfile
import json
import os

files_to_check = ['data/raw/eia/AEO2014.zip', 'data/raw/eia/AEO2015.zip']

for zip_path in files_to_check:
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Find the text/json file
            file_names = z.namelist()
            target_file = next((n for n in file_names if n.endswith('.txt') or n.endswith('.json')), None)
            
            if target_file:
                print(f"--- Inspecting {os.path.basename(zip_path)} ---")
                with z.open(target_file) as f:
                    for _ in range(3):
                        line = f.readline()
                        if not line: break
                        try:
                            data = json.loads(line)
                            print(f"Series ID: {data.get('series_id')}")
                        except:
                            pass
    except Exception as e:
        print(f"Error reading {zip_path}: {e}")
