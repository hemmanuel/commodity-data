import zipfile
import os
import glob

DATA_DIR = 'data/raw/ferc'

def inspect_zip_contents():
    zip_files = glob.glob(os.path.join(DATA_DIR, 'Form2_*.zip'))
    if not zip_files:
        print("No FERC Form 2 ZIP files found.")
        return

    # Pick the most recent one
    zip_path = sorted(zip_files)[-1] 
    print(f"Inspecting contents of: {zip_path}")

    with zipfile.ZipFile(zip_path, 'r') as z:
        file_list = z.namelist()
        
        # Sort and print
        for f in sorted(file_list):
            print(f)

if __name__ == "__main__":
    inspect_zip_contents()
