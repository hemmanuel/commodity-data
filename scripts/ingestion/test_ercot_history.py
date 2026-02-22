import gridstatus
import pandas as pd

iso = gridstatus.Ercot()
test_date = "2021-02-15" # Winter Storm Uri - good test for historical data availability

print(f"Testing historical fetch for {test_date}...")

try:
    print("\n1. Testing LMP (Settlement Point Prices)...")
    # Note: gridstatus might use different methods for history vs realtime
    # get_rtm_spp is likely the right one for history
    df_lmp = iso.get_rtm_spp(year=2021, verbose=True)
    # We won't fetch the whole year, just check if it starts downloading
    # Actually get_rtm_spp downloads by year. That confirms bulk history availability.
    # Let's try a specific date range if possible, or just confirm the method exists.
    # The previous error showed get_rtm_spp takes 'year'.
    print("get_rtm_spp(year=2021) is available (bulk annual download).")
except Exception as e:
    print(f"LMP Error: {e}")

try:
    print("\n2. Testing Load...")
    # get_load usually supports date range
    df_load = iso.get_load(date=test_date, verbose=True)
    print(f"Success! Fetched {len(df_load)} load records.")
    print(df_load.head(2))
except Exception as e:
    print(f"Load Error: {e}")

try:
    print("\n3. Testing Fuel Mix...")
    df_mix = iso.get_fuel_mix(date=test_date, verbose=True)
    print(f"Success! Fetched {len(df_mix)} fuel mix records.")
    print(df_mix.head(2))
except Exception as e:
    print(f"Fuel Mix Error: {e}")
