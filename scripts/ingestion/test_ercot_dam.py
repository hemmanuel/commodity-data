import gridstatus
import traceback

iso = gridstatus.Ercot()

print("--- Testing get_dam_spp for 2021 ---")
try:
    # get_dam_spp likely takes year
    df = iso.get_dam_spp(year=2021, verbose=True)
    print(f"Success! Fetched {len(df)} records.")
    print(df.head(2))
except Exception:
    traceback.print_exc()
