import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A"
dwg_path = os.path.join(piso_dir, "PRE_FOR_1aFIADA_TIPO A.DWG")

dwg = TQSDwg.Dwg()
dwg.file.Open(dwg_path)
it = dwg.iterator
it.Begin()

diagonais_shaft = []
retas_237 = []

while True:
    if it.GetElementReadPosition():
        if it.level == 237 and it.elementName == "Linha":
            dx = abs(it.x2 - it.x1)
            dy = abs(it.y2 - it.y1)
            # Se a linha não é perfeitamente ortogonal (dx > 5 e dy > 5), é uma diagonal de 'X' de shaft
            if dx > 5.0 and dy > 5.0:
                diagonais_shaft.append(((round(it.x1, 1), round(it.y1, 1)), (round(it.x2, 1), round(it.y2, 1))))
            else:
                retas_237.append(((round(it.x1, 1), round(it.y1, 1)), (round(it.x2, 1), round(it.y2, 1))))
    if not it.Next():
        break
dwg.file.Close()

print(f"Linhas diagonais ('X' de shafts): {len(diagonais_shaft)}")
print(f"Linhas de contorno externo/balanço: {len(retas_237)}")
for d in diagonais_shaft[:10]:
    print(f"  Diagonal: {d[0]} -> {d[1]}")
