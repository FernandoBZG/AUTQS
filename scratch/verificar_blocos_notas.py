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

blocks = []
while True:
    if it.GetElementReadPosition():
        if it.elementName == "Bloco" and it.x1 >= 16200 and it.y1 >= -2350:
            blocks.append((it.blockName, it.level, it.color, it.style, it.x1, it.y1, it.xScale, it.yScale, it.insertAngle))
    if not it.Next():
        break
dwg_geo.file.Close()

print(f"Blocks in notes: {len(blocks)}")
for b in blocks:
    print(f"  {b}")
