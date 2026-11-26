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

corte_elements = []
while True:
    if it.GetElementReadPosition():
        txt = getattr(it, "text", "")
        if any(k in txt.upper() for k in ["CORTE", "PRISMA", "RESIST", "MPA", "PAVIMENTO", "COTA"]):
            corte_elements.append((it.level, it.elementName, txt, round(it.x1, 1), round(it.y1, 1)))
        elif it.elementName == "Bloco" and any(k in it.blockName.upper() for k in ["CORTE", "ESQUEM", "PRISMA"]):
            corte_elements.append((it.level, "Bloco", it.blockName, round(it.x1, 1), round(it.y1, 1)))
    if not it.Next():
        break
dwg.file.Close()

print(f"Corte elements in generated PRE_FOR_1aFIADA_TIPO A.DWG: {len(corte_elements)}")
for c in corte_elements[:30]:
    print(f"  {c}")
