import duckdb
from dbfread import DBF
import zipfile
import os
import shutil

DATA_DIR = 'data/raw/ferc'
TEMP_DIR = 'data/temp/debug_prd'
ZIP_PATH = os.path.join(DATA_DIR, 'Form2_2021.zip')

def check_report_prd():
    os.makedirs(TEMP_DIR, exist_ok=True)
    try:
        with zipfile.ZipFile(ZIP_PATH, 'r') as z:
            # Find Income Statement
            target = 'F2_120_STMNT_CASH_FLOW.DBF' # Using Cash Flow as per user example
            extracted_path = None
            for file_info in z.infolist():
                if target in file_info.filename.upper():
                    z.extract(file_info, TEMP_DIR)
                    extracted_path = os.path.join(TEMP_DIR, file_info.filename)
                    break
            
            if extracted_path:
                print(f"Inspecting {target} for Respondent 48, Row 200")
                table = DBF(extracted_path, load=True)
                count = 0
                for record in table:
                    if str(record.get('RESPONDENT')) == '48' and record.get('ROW_NUM') == 200:
                        print(f"Row: {record.get('ROW_NUM')}, Report Prd: {record.get('REPORT_PRD')}, Current Year: {record.get('CURR_YR')}")
                        count += 1
                print(f"Found {count} records.")

    finally:
        shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    check_report_prd()
