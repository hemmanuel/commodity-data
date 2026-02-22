import gridstatus
import traceback

iso = gridstatus.Ercot()

print("--- Testing get_hourly_load_post_settlements for 2021 ---")
try:
    # This likely returns a dataframe for the whole year or a specific date range
    # Let's try a year argument if it accepts it, or a date
    # I'll try date first, then year if it fails
    df = iso.get_hourly_load_post_settlements(year=2021, verbose=True)
    print(f"Success! Fetched {len(df)} records.")
    print(df.head(2))
except Exception:
    traceback.print_exc()

print("\n--- Testing get_system_wide_actual_load for 2021 ---")
try:
    df = iso.get_system_wide_actual_load(year=2021, verbose=True)
    print(f"Success! Fetched {len(df)} records.")
    print(df.head(2))
except Exception:
    traceback.print_exc()
