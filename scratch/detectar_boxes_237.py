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

lines_237 = []
while True:
    if it.GetElementReadPosition():
        if it.level == 237 and it.elementName == "Linha":
            p1 = (round(it.x1, 1), round(it.y1, 1))
            p2 = (round(it.x2, 1), round(it.y2, 1))
            lines_237.append((p1, p2))
    if not it.Next():
        break
dwg.file.Close()

print(f"Total lines on Level 237 in TIPO A.DWG: {len(lines_237)}")

# Let's detect closed rectangles or connected boxes in lines_237!
# Group connected segments
from collections import defaultdict
graph = defaultdict(list)
for p1, p2 in lines_237:
    graph[p1].append(p2)
    graph[p2].append(p1)

# Find loops / cycles
print(f"Nodes in graph: {len(graph)}")
isolated_boxes = []
# Check horizontal and vertical segments
horiz = []
vert = []
for p1, p2 in lines_237:
    x1, y1 = p1
    x2, y2 = p2
    if abs(y1 - y2) < 0.5:
        horiz.append((min(x1, x2), max(x1, x2), y1))
    elif abs(x1 - x2) < 0.5:
        vert.append((x1, min(y1, y2), max(y1, y2)))

print(f"Horizontal lines: {len(horiz)}, Vertical lines: {len(vert)}")

# Find rectangular boxes formed by 2 horiz and 2 vert
boxes = []
for h1 in horiz:
    for h2 in horiz:
        if h1 != h2 and abs(h1[0] - h2[0]) < 2.0 and abs(h1[1] - h2[1]) < 2.0:
            y_min, y_max = min(h1[2], h2[2]), max(h1[2], h2[2])
            x_min, x_max = min(h1[0], h2[0]), max(h1[1], h2[1])
            w = x_max - x_min
            h = y_max - y_min
            if 10.0 <= w <= 300.0 and 10.0 <= h <= 300.0:
                box = (round(x_min, 1), round(x_max, 1), round(y_min, 1), round(y_max, 1))
                if box not in boxes:
                    boxes.append(box)

print(f"\nShaft boxes detected in TIPO A.DWG: {len(boxes)}")
for b in boxes:
    print(f"  Box: X=[{b[0]}, {b[1]}], Y=[{b[2]}, {b[3]}], W={b[1]-b[0]:.1f}, H={b[3]-b[2]:.1f}")
