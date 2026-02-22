import gridstatus
import inspect

iso = gridstatus.Ercot()
print(inspect.signature(iso.get_lmp))
