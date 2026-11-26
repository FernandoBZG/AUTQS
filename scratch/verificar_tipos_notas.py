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

notes_by_type = {}
notes_items = []

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        x = it.x1
        y = it.y1
        is_zero = (x == 0.0 and y == 0.0 and name in ["Fim de bloco", "Fim de objeto", "Objeto"])
        
        if x >= 16200 and y >= -2350 and lvl != 100 and not is_zero:
            notes_by_type[name] = notes_by_type.get(name, 0) + 1
            notes_items.append((name, lvl, it.color, it.style))
    if not it.Next():
        break
dwg_geo.file.Close()

print(f"Notes by element name: {notes_by_type}")
print(f"Total notes elements: {len(notes_items)}")
