import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
for_path = os.path.join(piso_dir, "FOR0003.DWG")

dwg_f = TQSDwg.Dwg()
dwg_f.file.Open(for_path)
it_f = dwg_f.iterator
it_f.Begin()

upper_for = []
while True:
    if it_f.GetElementReadPosition():
        if it_f.y1 >= -2460 or it_f.y2 >= -2460:
            upper_for.append((it_f.level, it_f.elementName, getattr(it_f, "text", ""), round(it_f.x1, 1), round(it_f.y1, 1), round(it_f.x2, 1), round(it_f.y2, 1)))
    if not it_f.Next():
        break
dwg_f.file.Close()

print(f"Elements in FOR0003 with Y >= -2460: {len(upper_for)}")
for u in upper_for:
    print(f"  {u}")
