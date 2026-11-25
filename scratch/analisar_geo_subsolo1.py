import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
geo_path = os.path.join(piso_dir, "GEO_SUBSOLO 1.DWG")
for_path = os.path.join(piso_dir, "FOR0003.DWG")

print("--- ANALISE DE GEO_SUBSOLO 1.DWG ---")
dwg = TQSDwg.Dwg()
dwg.file.Open(geo_path)
it = dwg.iterator
it.Begin()

lvls = {}
types = {}
titles = []
moldura_cnt = 0
notes_cnt = 0
other_elems = []

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        lvls[lvl] = lvls.get(lvl, 0) + 1
        types[name] = types.get(name, 0) + 1
        
        if lvl == 100:
            moldura_cnt += 1
        elif lvl in [222, 250] and it.y1 >= -2350:
            txt = getattr(it, "text", "")
            titles.append((lvl, name, txt, round(it.x1, 1), round(it.y1, 1)))
        elif it.x1 >= 16000 or it.y1 >= -2400:
            notes_cnt += 1
            if lvl not in [100, 222, 250]:
                other_elems.append((lvl, name, getattr(it, "text", ""), round(it.x1, 1), round(it.y1, 1)))
    if not it.Next():
        break
dwg.file.Close()

print(f"Total elements: {sum(lvls.values())}")
print(f"Levels: {sorted(lvls.items())}")
print(f"Types: {types}")
print(f"Moldura (lvl 100): {moldura_cnt}")
print(f"Titles: {titles}")
print(f"Notes/Legends count: {notes_cnt}")
print(f"Sample notes/other elems (lvl not 100,222,250): {len(other_elems)}")
for e in other_elems[:15]:
    print(f"  lvl {e[0]}: {e[1]} '{e[2]}' at ({e[3]}, {e[4]})")

print("\n--- ANALISE DE FOR0003.DWG ---")
dwg_f = TQSDwg.Dwg()
dwg_f.file.Open(for_path)
it_f = dwg_f.iterator
it_f.Begin()

lvls_f = {}
types_f = {}
raw_titles_f = []
while True:
    if it_f.GetElementReadPosition():
        lvl = it_f.level
        name = it_f.elementName
        lvls_f[lvl] = lvls_f.get(lvl, 0) + 1
        types_f[name] = types_f.get(name, 0) + 1
        txt = getattr(it_f, "text", "")
        if "Planta" in txt or "Escala" in txt or "00-" in txt or "01-" in txt or "02-" in txt:
            raw_titles_f.append((lvl, name, txt, round(it_f.x1, 1), round(it_f.y1, 1)))
    if not it_f.Next():
        break
dwg_f.file.Close()

print(f"Total elements FOR: {sum(lvls_f.values())}")
print(f"Levels FOR: {sorted(lvls_f.items())}")
print(f"Raw titles in FOR: {raw_titles_f}")
