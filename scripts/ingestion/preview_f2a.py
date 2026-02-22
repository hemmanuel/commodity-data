import os
from dbfread import DBF

target_file = 'data/temp/UPLOADERS/FORM2/working/F2A_001_IDENT_ATTSTTN.DBF'
if os.path.exists(target_file):
    table = DBF(target_file, load=True)
    print("Columns:", table.field_names)
    print("First record:", dict(table.records[0]))
