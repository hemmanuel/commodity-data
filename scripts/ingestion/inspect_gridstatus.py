import gridstatus
import traceback

iso = gridstatus.Ercot()

print("--- Help for get_load ---")
help(iso.get_load)

print("\n--- Help for get_fuel_mix ---")
help(iso.get_fuel_mix)

print("\n--- Retrying Load Fetch with Traceback ---")
try:
    iso.get_load(date="2021-02-15", verbose=True)
    print("Load fetch success")
except Exception:
    traceback.print_exc()
