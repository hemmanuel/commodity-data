import zipfile
import os
import glob
import pandas as pd
from dbfread import DBF
import shutil

# Configuration
DATA_DIR = 'data/raw/ferc'
TEMP_DIR = 'data/temp/ferc_schema_analysis'

# Tables we care about
TARGET_TABLES = {
    'F1_36.DBF': 'Income Statement',
    'F1_15.DBF': 'Balance Sheet Assets',
    'F1_11.DBF': 'Balance Sheet Liabilities',
    'F1_13.DBF': 'Cash Flow',
    'F1_89.DBF': 'Steam Plants'
}

def analyze_schemas():
    print("Starting comprehensive FERC Form 1 Schema Analysis...")
    
    zip_files = glob.glob(os.path.join(DATA_DIR, 'Form1_*.zip'))
    zip_files.sort(reverse=True)
    
    schema_history = []

    for zip_path in zip_files:
        filename = os.path.basename(zip_path)
        year = filename.replace('Form1_', '').replace('.zip', '')
        
        try:
            if os.path.exists(TEMP_DIR):
                shutil.rmtree(TEMP_DIR)
            os.makedirs(TEMP_DIR, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Only extract target files to save time
                all_files = z.namelist()
                targets_in_zip = []
                for f in all_files:
                    if os.path.basename(f).upper() in TARGET_TABLES:
                        targets_in_zip.append(f)
                
                if targets_in_zip:
                    z.extractall(TEMP_DIR, members=targets_in_zip)
            
            # Find and read headers
            for root, dirs, files in os.walk(TEMP_DIR):
                for f in files:
                    fname_upper = f.upper()
                    if fname_upper in TARGET_TABLES:
                        dbf_path = os.path.join(root, f)
                        try:
                            table = DBF(dbf_path, load=False)
                            fields = table.field_names
                            
                            schema_history.append({
                                'Year': year,
                                'File': fname_upper,
                                'Table': TARGET_TABLES[fname_upper],
                                'Columns': ', '.join(fields)
                            })
                        except Exception as e:
                            print(f"Error reading {f} in {year}: {e}")

        except Exception as e:
            print(f"Error processing {year}: {e}")

    # Output results
    if schema_history:
        df = pd.DataFrame(schema_history)
        # Sort by File then Year
        df = df.sort_values(['File', 'Year'], ascending=[True, False])
        
        print("\n=== Schema Analysis Report ===")
        for file_type in TARGET_TABLES.keys():
            print(f"\n--- {TARGET_TABLES[file_type]} ({file_type}) ---")
            file_df = df[df['File'] == file_type]
            
            # Group by Columns to see distinct schemas
            unique_schemas = file_df.groupby('Columns')['Year'].apply(list).reset_index()
            
            for _, row in unique_schemas.iterrows():
                years = row['Year']
                years.sort(reverse=True)
                year_range = f"{years[-1]}-{years[0]}" if len(years) > 1 else str(years[0])
                print(f"\nYears: {year_range}")
                print(f"Columns: {row['Columns']}")

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    analyze_schemas()
