import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

corte1 = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\GERAIS\CORTE ESQUEMÁTICO.DWG"
corte2 = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\ESPACIAL\FOR_Corte Esquemático com Prismas.DWG"

for path in [corte1, corte2]:
    print(f"\n=======================================================")
    print(f"Arquivo: {path}")
    if not os.path.exists(path):
        print("Arquivo nao existe!")
        continue
    dwg = TQSDwg.Dwg()
    dwg.file.Open(path)
    it = dwg.iterator
    it.Begin()
    tot = 0
    lvls = {}
    texts = []
    min_x, max_x = 1e9, -1e9
    min_y, max_y = 1e9, -1e9
    while True:
        if it.GetElementReadPosition():
            tot += 1
            lvls[it.level] = lvls.get(it.level, 0) + 1
            min_x = min(min_x, it.x1, it.x2)
            max_x = max(max_x, it.x1, it.x2)
            min_y = min(min_y, it.y1, it.y2)
            max_y = max(max_y, it.y1, it.y2)
            txt = getattr(it, "text", "")
            if txt:
                texts.append((it.level, txt, round(it.x1, 1), round(it.y1, 1)))
        if not it.Next():
            break
    dwg.file.Close()
    print(f"Total: {tot}")
    print(f"Bounds: X=[{min_x:.1f}, {max_x:.1f}], Y=[{min_y:.1f}, {max_y:.1f}]")
    print(f"Levels: {sorted(lvls.items())}")
    print(f"Sample texts ({len(texts)}):")
    for t in texts[:15]:
        print(f"  lvl {t[0]}: '{t[1]}' at ({t[2]}, {t[3]})")
