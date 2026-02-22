import gridstatus
import traceback

iso = gridstatus.Ercot()

print("--- Testing get_hourly_load_post_settlements for 2021-01-01 ---")
try:
    df = iso.get_hourly_load_post_settlements(start="2021-01-01", end="2021-01-02", verbose=True)
    print(f"Success! Fetched {len(df)} records.")
    print(df.head(2))
except Exception:
    traceback.print_exc()

print("\n--- Testing get_system_wide_actual_load for 2021-01-01 ---")
try:
    df = iso.get_system_wide_actual_load(start="2021-01-01", end="2021-01-02", verbose=True)
    print(f"Success! Fetched {len(df)} records.")
    print(df.head(2))
except Exception:
    traceback.print_exc()
