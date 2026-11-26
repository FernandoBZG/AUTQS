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

moldura = []
titles = []
notes = []
other = []

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        x = it.x1
        y = it.y1
        
        # Ignora marcadores neutros em (0,0) a menos que façam parte de bloco
        is_zero = (x == 0.0 and y == 0.0 and name in ["Fim de bloco", "Fim de objeto", "Objeto"])
        
        if lvl == 100:
            moldura.append((name, lvl, it.color, it.style, x, y))
        elif lvl in [222, 250] and x <= 11000 and y >= -2300:
            titles.append((name, lvl, it.color, it.style, getattr(it, "text", ""), x, y))
        elif x >= 16200 and y >= -2350 and not is_zero:
            notes.append((name, lvl, it.color, it.style, getattr(it, "text", ""), x, y))
        elif not is_zero and y >= -2380:
            other.append((name, lvl, it.color, it.style, getattr(it, "text", ""), x, y))
    if not it.Next():
        break
dwg_geo.file.Close()

print(f"Moldura (lvl 100): {len(moldura)}")
print(f"Titles: {len(titles)}")
for t in titles:
    print(f"  {t}")
print(f"Notes (X >= 16200, Y >= -2350): {len(notes)}")
print(f"Other elements with Y >= -2380 (excluding (0,0)): {len(other)}")
for o in other:
    print(f"  {o}")
