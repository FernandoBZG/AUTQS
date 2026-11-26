import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
geo_path = os.path.join(piso_dir, "GEO_SUBSOLO 1.DWG")

dwg = TQSDwg.Dwg()
dwg.file.Open(geo_path)
it = dwg.iterator
it.Begin()

# Categorizar elementos
# 1. Moldura (lvl 100)
# 2. Título executivo (lvl 222, 250 em X < 12000, Y >= -2350)
# 3. Formwork antigo vs Notas Técnicas
elems_by_zone = {
    "moldura": 0,
    "title": 0,
    "upper_notes": 0,  # Y >= -2400 (fora do título)
    "right_notes": 0,  # X >= 16200 e Y < -2400
    "formwork_area": 0 # X < 16200 e Y < -2400
}

sample_upper = []
sample_right = []
sample_formwork = []

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        x = it.x1
        y = it.y1
        txt = getattr(it, "text", "")
        
        if lvl == 100:
            elems_by_zone["moldura"] += 1
        elif lvl in [222, 250] and x <= 11000 and y >= -2300:
            elems_by_zone["title"] += 1
        elif y >= -2400:
            elems_by_zone["upper_notes"] += 1
            if len(sample_upper) < 10:
                sample_upper.append((lvl, name, txt, round(x, 1), round(y, 1)))
        elif x >= 16200:
            elems_by_zone["right_notes"] += 1
            if len(sample_right) < 10:
                sample_right.append((lvl, name, txt, round(x, 1), round(y, 1)))
        else:
            elems_by_zone["formwork_area"] += 1
            if len(sample_formwork) < 10:
                sample_formwork.append((lvl, name, txt, round(x, 1), round(y, 1)))
    if not it.Next():
        break
dwg.file.Close()

print(f"Zones breakdown in GEO_SUBSOLO 1:")
for k, v in elems_by_zone.items():
    print(f"  {k}: {v}")

print("\nSample Upper (Y >= -2400):")
for s in sample_upper:
    print(f"  lvl {s[0]}: {s[1]} '{s[2]}' at ({s[3]}, {s[4]})")

print("\nSample Right (X >= 16200, Y < -2400):")
for s in sample_right:
    print(f"  lvl {s[0]}: {s[1]} '{s[2]}' at ({s[3]}, {s[4]})")

print("\nSample Formwork Area:")
for s in sample_formwork:
    print(f"  lvl {s[0]}: {s[1]} '{s[2]}' at ({s[3]}, {s[4]})")
