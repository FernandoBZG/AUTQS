import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
geo_path = os.path.join(piso_dir, "GEO_SUBSOLO 1.DWG")
for_path = os.path.join(piso_dir, "FOR0003.DWG")

# Let's inspect where elements in GEO_SUBSOLO 1 are located when Y >= -2400
dwg_geo = TQSDwg.Dwg()
dwg_geo.file.Open(geo_path)
it = dwg_geo.iterator
it.Begin()

geo_upper_elements = [] # Y >= -2350 or Y > -2400
geo_by_level = {}

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        geo_by_level[lvl] = geo_by_level.get(lvl, 0) + 1
        name = it.elementName
        x = it.x1
        y = it.y1
        # Elements outside the formwork bounding box
        # What is the bounding box of formwork in FOR0003?
        if y >= -2380:
            txt = getattr(it, "text", "")
            geo_upper_elements.append((lvl, name, txt, round(x, 1), round(y, 1), round(it.x2, 1), round(it.y2, 1)))
    if not it.Next():
        break
dwg_geo.file.Close()

print(f"Total upper elements (Y >= -2380) in GEO: {len(geo_upper_elements)}")
# Group upper elements by level
from collections import Counter
c_upper_lvl = Counter([e[0] for e in geo_upper_elements])
print(f"Upper elements by level: {sorted(c_upper_lvl.items())}")

print("\nTexts in upper region:")
upper_texts = [e for e in geo_upper_elements if e[1] == "Texto"]
for t in upper_texts[:30]:
    print(f"  lvl {t[0]}: '{t[2]}' at ({t[3]}, {t[4]})")

print("\nLet's see the extent of Moldura (level 100):")
dwg_geo = TQSDwg.Dwg()
dwg_geo.file.Open(geo_path)
it = dwg_geo.iterator
it.Begin()
moldura = []
while True:
    if it.GetElementReadPosition():
        if it.level == 100:
            moldura.append((it.elementName, getattr(it, "text", ""), round(it.x1, 1), round(it.y1, 1), round(it.x2, 1), round(it.y2, 1)))
    if not it.Next():
        break
dwg_geo.file.Close()

print(f"Moldura elements: {len(moldura)}")
for m in moldura:
    print(f"  {m}")
