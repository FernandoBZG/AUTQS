import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A"
ep_path = os.path.join(piso_dir, "EP - PRE_FOR_1aFIADA_TIPO A.DWG")

print(f"--- ANALISE DE {ep_path} ---")
if not os.path.exists(ep_path):
    print("Arquivo EP não existe!")
    sys.exit(1)

dwg = TQSDwg.Dwg()
dwg.file.Open(ep_path)
it = dwg.iterator
it.Begin()

lvls = {}
blocks = []
lvl237_diags = []
lvl237_rects = []
corte_texts = []

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        lvls[lvl] = lvls.get(lvl, 0) + 1
        
        if name == "Bloco":
            blocks.append((it.blockName, lvl, round(it.x1, 1), round(it.y1, 1), round(it.xScale, 2), round(it.yScale, 2)))
        
        if lvl == 237 and name == "Linha":
            dx = abs(it.x2 - it.x1)
            dy = abs(it.y2 - it.y1)
            if dx > 5 and dy > 5:
                lvl237_diags.append(((round(it.x1, 1), round(it.y1, 1)), (round(it.x2, 1), round(it.y2, 1))))
            else:
                lvl237_rects.append(((round(it.x1, 1), round(it.y1, 1)), (round(it.x2, 1), round(it.y2, 1))))
        
        txt = getattr(it, "text", "")
        if "CORTE" in txt.upper() or "RESIST" in txt.upper() or "FCA" in txt.upper() or "MPA" in txt.upper():
            corte_texts.append((lvl, txt, round(it.x1, 1), round(it.y1, 1)))

    if not it.Next():
        break
dwg.file.Close()

print(f"Total elements: {sum(lvls.values())}")
print(f"Levels: {sorted(lvls.items())}")
print(f"Blocks ({len(blocks)}):")
for b in set([x[0] for x in blocks]):
    print(f"  Block: {b}")

print(f"\nDiagonais no Nível 237: {len(lvl237_diags)}")
for d in lvl237_diags[:10]:
    print(f"  {d}")

print(f"\nTextos relacionados a corte/resistência ({len(corte_texts)}):")
for t in corte_texts[:10]:
    print(f"  {t}")
