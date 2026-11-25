import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
geo_path = os.path.join(piso_dir, "GEO_SUBSOLO 1.DWG")

dwg_geo = TQSDwg.Dwg()
dwg_geo.file.Open(geo_path)
it = dwg_geo.iterator
it.Begin()

middle_upper = []
while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        x = it.x1
        y = it.y1
        # Elements in upper region but not in title (x <= 11000) and not in notes (x >= 16200) and not moldura (lvl 100)
        if y >= -2380 and lvl != 100 and not (x <= 11000 and lvl in [222, 250]) and x < 16200:
            middle_upper.append((lvl, name, getattr(it, "text", ""), round(x, 1), round(y, 1)))
    if not it.Next():
        break
dwg_geo.file.Close()

print(f"Elements in middle upper region (11000 < X < 16200, Y >= -2380, lvl != 100): {len(middle_upper)}")
for m in middle_upper[:20]:
    print(f"  {m}")
