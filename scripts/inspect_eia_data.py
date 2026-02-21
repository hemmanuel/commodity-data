import zipfile
import json
import os

zip_path = 'data/raw/eia/NG.zip'

try:
    with zipfile.ZipFile(zip_path, 'r') as z:
        # List files to confirm structure
        print(f"Files in {zip_path}: {z.namelist()}")
        
        # Read the first file (assuming it's the main data file)
        file_name = z.namelist()[0]
        with z.open(file_name) as f:
            # Read line by line to avoid loading the whole file if it's huge
            for i in range(5):
                line = f.readline()
                if not line:
                    break
                try:
                    data = json.loads(line)
                    print(f"Line {i+1}: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Line {i+1} is not valid JSON: {line}")
except Exception as e:
    print(f"Error inspecting zip: {e}")
