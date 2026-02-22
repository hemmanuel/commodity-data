import gridstatus
import inspect

iso = gridstatus.Ercot()
methods = [m for m in dir(iso) if not m.startswith('_')]
print("Available methods in gridstatus.Ercot:")
for m in methods:
    print(f"- {m}")
