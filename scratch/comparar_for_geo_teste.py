import sys
import os
from collections import Counter

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
for_path = os.path.join(piso_dir, "FOR0003.DWG")
geo_test = os.path.join(piso_dir, "GEO_SUBSOLO 1_TESTE.DWG")

def audit_dwg(dwg_path):
    dwg = TQSDwg.Dwg()
    dwg.file.Open(dwg_path)
    it = dwg.iterator
    it.Begin()
    
    lines = []
    texts_lvl8 = []
    texts_lvl11 = []
    
    while True:
        if it.GetElementReadPosition():
            # Consider only formwork region
            if it.y1 < -2350 and it.level != 100:
                if it.elementName == "Linha":
                    # Exclude the temporary title lines if any in FOR
                    p1 = (round(it.x1, 1), round(it.y1, 1))
                    p2 = (round(it.x2, 1), round(it.y2, 1))
                    lines.append((min(p1, p2), max(p1, p2)))
                elif it.elementName == "Texto":
                    if it.level == 8:
                        texts_lvl8.append(it.text)
                    elif it.level == 11:
                        texts_lvl11.append(it.text)
        if not it.Next():
            break
    dwg.file.Close()
    return lines, texts_lvl8, texts_lvl11

f_lines, f_vigas, f_dims = audit_dwg(for_path)
g_lines, g_vigas, g_dims = audit_dwg(geo_test)

print("--- COMPARATIVO FOR0003 vs GEO_TESTE (ÁREA DE FORMA: Y < -2350) ---")
print(f"Linhas: FOR={len(f_lines)} | GEO={len(g_lines)}")
print(f"Vigas (Nível 8): FOR={len(f_vigas)} | GEO={len(g_vigas)}")
print(f"Dimensões (Nível 11): FOR={len(f_dims)} | GEO={len(g_dims)}")

# Check duplicate lines
c_f = Counter(f_lines)
dups_f = [k for k, v in c_f.items() if v > 1]
c_g = Counter(g_lines)
dups_g = [k for k, v in c_g.items() if v > 1]

print(f"Linhas duplicadas: FOR={len(dups_f)} | GEO={len(dups_g)}")
print(f"Vigas idênticas? {sorted(f_vigas) == sorted(g_vigas)}")
print(f"Linhas idênticas? {sorted(f_lines) == sorted(g_lines)}")

if sorted(f_vigas) == sorted(g_vigas) and sorted(f_lines) == sorted(g_lines):
    print("\n>>> SUCESSO ABSOLUTO: 100% FIDELIDADE ESTRUTURAL ENTRE FOR E GEO!")
