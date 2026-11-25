import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

p = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A\PRE_FOR_1aFIADA_TIPO A_BKP_20261104_164701.DWG"
dwg = TQSDwg.Dwg()
dwg.file.Open(p)
it = dwg.iterator
it.Begin()

corte_elems = []
min_x, max_x = 1e9, -1e9
min_y, max_y = 1e9, -1e9

while True:
    if it.GetElementReadPosition():
        # Look for elements in the corte region X in [2300, 3300], Y in [-1600, 200]
        if 2300 <= it.x1 <= 3400 and -1600 <= it.y1 <= 300:
            corte_elems.append((it.level, it.elementName, getattr(it, "text", ""), round(it.x1, 1), round(it.y1, 1)))
            min_x = min(min_x, it.x1, it.x2)
            max_x = max(max_x, it.x1, it.x2)
            min_y = min(min_y, it.y1, it.y2)
            max_y = max(max_y, it.y1, it.y2)
    if not it.Next():
        break
dwg.file.Close()

print(f"Original corte elements: {len(corte_elems)}")
print(f"Bounds of original corte: X=[{min_x:.1f}, {max_x:.1f}], Y=[{min_y:.1f}, {max_y:.1f}]")
