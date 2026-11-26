import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A"
dwg_path = os.path.join(piso_dir, "TIPO A.DWG")

dwg = TQSDwg.Dwg()
dwg.file.Open(dwg_path)
it = dwg.iterator
it.Begin()

elems_237 = []
while True:
    if it.GetElementReadPosition():
        if it.level == 237:
            txt = getattr(it, "text", "")
            elems_237.append((it.elementName, it.color, round(it.x1, 1), round(it.y1, 1), round(it.x2, 1), round(it.y2, 1), txt))
    if not it.Next():
        break
dwg.file.Close()

print(f"Elements on Level 237 in TIPO A.DWG: {len(elems_237)}")
for e in elems_237[:30]:
    print(f"  {e}")
