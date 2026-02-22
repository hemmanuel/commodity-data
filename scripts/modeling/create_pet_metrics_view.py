import duckdb

db_path = "data/commodity_data.duckdb"
con = duckdb.connect(db_path)

print("## Updating fact_petroleum_metrics View\n")

# Series IDs identified
series_map = {
    'WTI Spot Price': 'PET.RWTC.D',
    'Brent Spot Price': 'PET.RBRTE.D',
    'Refinery Utilization': 'PET.WPULEUS3.W',
    'Crude Stocks Total': 'PET.WCRSTUS1.W',
    'Crude Stocks Excl SPR': 'PET.WCESTUS1.W',
    'SPR Stocks': 'PET.WCSSTUS1.W',
    'Distillate Stocks': 'PET.WDISTUS1.W',
    'Gasoline Stocks': 'PET.WGTSTUS1.W',
    'Cushing Stocks': 'PET.W_EPC0_SAX_YCUOK_MBBL.W',
    'WTI Futures Contract 1': 'PET.RCLC1.D',
    'WTI Futures Contract 2': 'PET.RCLC2.D',
    'WTI Futures Contract 3': 'PET.RCLC3.D',
    'WTI Futures Contract 4': 'PET.RCLC4.D'
}

union_parts = []
for name, sid in series_map.items():
    union_parts.append(f"SELECT '{name}' as metric, series_id, date, value, 'Unknown' as unit FROM eia_data WHERE series_id = '{sid}'")

union_query = " UNION ALL ".join(union_parts)

create_view_query = f"""
    CREATE OR REPLACE VIEW fact_petroleum_metrics AS
    {union_query}
"""

con.execute(create_view_query)
print("View fact_petroleum_metrics updated successfully.")

# Verify
count = con.execute("SELECT COUNT(*) FROM fact_petroleum_metrics").fetchone()[0]
print(f"Total rows in view: {count}")

con.close()
