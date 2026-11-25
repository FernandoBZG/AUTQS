import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A"
bkp_path = os.path.join(piso_dir, "PRE_FOR_1aFIADA_TIPO A_BKP_20261104_164701.DWG")

dwg = TQSDwg.Dwg()
dwg.file.Open(bkp_path)
it = dwg.iterator
it.Begin()

blocks = []
texts = []
while True:
    if it.GetElementReadPosition():
        if it.elementName == "Bloco":
            blocks.append((it.blockName, it.level, round(it.x1, 1), round(it.y1, 1), round(it.xScale, 2), round(it.yScale, 2)))
        txt = getattr(it, "text", "")
        if any(k in txt.upper() for k in ["CORTE", "PRISMA", "RESIST", "MPA", "ESQUEM"]):
            texts.append((it.level, txt, round(it.x1, 1), round(it.y1, 1)))
    if not it.Next():
        break
dwg.file.Close()

print(f"Blocks in BKP ({len(blocks)}):")
for b in set([x[0] for x in blocks]):
    print(f"  {b}")
print(f"Texts in BKP ({len(texts)}):")
for t in texts:
    print(f"  {t}")
