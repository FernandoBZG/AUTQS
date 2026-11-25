import sys
import os
from collections import Counter

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 2"
geo_path = os.path.join(piso_dir, "GEO_SUBSOLO 2.DWG")
for_path = os.path.join(piso_dir, "FOR0002.DWG")

def audit(path):
    dwg = TQSDwg.Dwg()
    dwg.file.Open(path)
    it = dwg.iterator
    it.Begin()
    
    tot = 0
    lvls = {}
    lines = []
    vigas = []
    titles = []
    
    while True:
        if it.GetElementReadPosition():
            tot += 1
            lvl = it.level
            lvls[lvl] = lvls.get(lvl, 0) + 1
            txt = getattr(it, "text", "")
            
            if lvl in [222, 250] and it.y1 >= -2350 and it.elementName == "Texto":
                titles.append((lvl, txt))
            elif it.y1 < -2350 and lvl != 100:
                if it.elementName == "Linha":
                    p1 = (round(it.x1, 1), round(it.y1, 1))
                    p2 = (round(it.x2, 1), round(it.y2, 1))
                    lines.append((min(p1, p2), max(p1, p2)))
                elif it.elementName == "Texto" and lvl == 8:
                    vigas.append(txt)
        if not it.Next():
            break
    dwg.file.Close()
    return tot, lvls, lines, vigas, titles

tot_g, lvls_g, lines_g, vigas_g, titles_g = audit(geo_path)
tot_f, lvls_f, lines_f, vigas_f, titles_f = audit(for_path)

print("=======================================================")
print("   RELATÓRIO DE AUDITORIA: GEO_SUBSOLO 2.DWG")
print("=======================================================")
print(f"Total de Elementos: {tot_g}")
print(f"Moldura 180-70 (Nível 100): {lvls_g.get(100, 0)} elementos")
print(f"Títulos na Prancha: {titles_g}")
print(f"Vigas Estruturais (Nível 8): GEO={len(vigas_g)} | FOR={len(vigas_f)}")
print(f"Linhas Estruturais (Y < -2350): GEO={len(lines_g)} | FOR={len(lines_f)}")

c_g = Counter(lines_g)
dups_g = [k for k, v in c_g.items() if v > 1]
c_f = Counter(lines_f)
dups_f = [k for k, v in c_f.items() if v > 1]

print(f"Linhas duplicadas: GEO={len(dups_g)} | FOR={len(dups_f)}")
print(f"Vigas idênticas? {sorted(vigas_g) == sorted(vigas_f)}")
print(f"Linhas idênticas? {sorted(lines_g) == sorted(lines_f)}")
print(f"Amostra de vigas (15 primeiras): {sorted(vigas_g)[:15]}")
