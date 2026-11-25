import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
geo_orig = os.path.join(piso_dir, "GEO_SUBSOLO 1.DWG")

dwg_src = TQSDwg.Dwg()
dwg_src.file.Open(geo_orig)
it = dwg_src.iterator
it.Begin()

lvl8_in_notes = []
while True:
    if it.GetElementReadPosition():
        if it.level == 8 and it.x1 >= 16000 and it.y1 >= -2350:
            lvl8_in_notes.append((it.elementName, getattr(it, "text", ""), it.x1, it.y1))
    if not it.Next():
        break
dwg_src.file.Close()

print(f"Level 8 elements in notes: {lvl8_in_notes}")
