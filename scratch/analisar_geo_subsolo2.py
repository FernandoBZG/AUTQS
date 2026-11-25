import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 2"
geo_path = os.path.join(piso_dir, "GEO_SUBSOLO 2.DWG")
for_path = os.path.join(piso_dir, "FOR0002.DWG")

print("--- ANALISE DE GEO_SUBSOLO 2.DWG ---")
dwg = TQSDwg.Dwg()
dwg.file.Open(geo_path)
it = dwg.iterator
it.Begin()

lvls = {}
titles = []
moldura_cnt = 0
notes_cnt = 0

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        x = it.x1
        y = it.y1
        lvls[lvl] = lvls.get(lvl, 0) + 1
        
        is_zero = (x == 0.0 and y == 0.0 and name in ["Fim de bloco", "Fim de objeto", "Objeto"])

        if lvl == 100:
            moldura_cnt += 1
        elif lvl in [222, 250] and x <= 11000 and y >= -2300:
            titles.append((lvl, name, getattr(it, "text", ""), round(x, 1), round(y, 1)))
        elif x >= 16200 and y >= -2350 and lvl != 100 and not is_zero:
            notes_cnt += 1
    if not it.Next():
        break
dwg.file.Close()

print(f"Total elements: {sum(lvls.values())}")
print(f"Levels: {sorted(lvls.items())}")
print(f"Moldura (lvl 100): {moldura_cnt}")
print(f"Titles: {titles}")
print(f"Notes/Legends count: {notes_cnt}")

print("\n--- ANALISE DE FOR0002.DWG ---")
dwg_f = TQSDwg.Dwg()
dwg_f.file.Open(for_path)
it_f = dwg_f.iterator
it_f.Begin()

lvls_f = {}
vigas_f = []
raw_titles_f = []
while True:
    if it_f.GetElementReadPosition():
        lvl = it_f.level
        name = it_f.elementName
        x = it_f.x1
        y = it_f.y1
        lvls_f[lvl] = lvls_f.get(lvl, 0) + 1
        txt = getattr(it_f, "text", "")
        if lvl == 8 and name == "Texto" and y < -2350:
            vigas_f.append(txt)
        if any(k in txt for k in ["Planta", "Escala"]) and y >= -2450:
            raw_titles_f.append((lvl, name, txt, round(x, 1), round(y, 1)))
    if not it_f.Next():
        break
dwg_f.file.Close()

print(f"Total elements FOR: {sum(lvls_f.values())}")
print(f"Levels FOR: {sorted(lvls_f.items())}")
print(f"Vigas no FOR: {len(vigas_f)} vigas: {sorted(vigas_f)[:15]}")
print(f"Raw titles in FOR: {raw_titles_f}")
