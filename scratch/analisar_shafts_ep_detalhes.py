import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A"
ep_path = os.path.join(piso_dir, "EP - PRE_FOR_1aFIADA_TIPO A.DWG")

dwg = TQSDwg.Dwg()
dwg.file.Open(ep_path)
it = dwg.iterator
it.Begin()

diags = []
while True:
    if it.GetElementReadPosition():
        if it.level == 237 and it.elementName == "Linha":
            dx = abs(it.x2 - it.x1)
            dy = abs(it.y2 - it.y1)
            if dx > 5 and dy > 5:
                p1 = (round(it.x1, 1), round(it.y1, 1))
                p2 = (round(it.x2, 1), round(it.y2, 1))
                diags.append((min(p1, p2), max(p1, p2)))
    if not it.Next():
        break
dwg.file.Close()

print(f"Total diags in EP: {len(diags)}")

# Group diagonals that share approximately the same bounding box
boxes = []
used = set()
for i, d1 in enumerate(diags):
    if i in used:
        continue
    p1, p2 = d1
    x_min, x_max = min(p1[0], p2[0]), max(p1[0], p2[0])
    y_min, y_max = min(p1[1], p2[1]), max(p1[1], p2[1])
    for j in range(i + 1, len(diags)):
        if j in used:
            continue
        q1, q2 = diags[j]
        qx_min, qx_max = min(q1[0], q2[0]), max(q1[0], q2[0])
        qy_min, qy_max = min(q1[1], q2[1]), max(q1[1], q2[1])
        if abs(x_min - qx_min) < 2 and abs(x_max - qx_max) < 2 and abs(y_min - qy_min) < 2 and abs(y_max - qy_max) < 2:
            used.add(i)
            used.add(j)
            boxes.append((x_min, x_max, y_min, y_max, round(x_max - x_min, 1), round(y_max - y_min, 1)))
            break

print(f"Shaft boxes with 'X' in EP: {len(boxes)}")
for b in sorted(boxes):
    print(f"  Shaft: X=[{b[0]}, {b[1]}], Y=[{b[2]}, {b[3]}], Dim={b[4]}x{b[5]}")
