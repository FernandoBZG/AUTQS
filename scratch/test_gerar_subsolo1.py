import sys
import os
import shutil
from datetime import datetime
from collections import Counter

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
geo_orig = os.path.join(piso_dir, "GEO_SUBSOLO 1.DWG")
for_path = os.path.join(piso_dir, "FOR0003.DWG")
geo_test = os.path.join(piso_dir, "GEO_SUBSOLO 1_TESTE.DWG")

print("--- [TESTE] GERANDO GEO_SUBSOLO 1 ---")
print(f"Origem GEO: {geo_orig}")
print(f"Origem FOR: {for_path}")
print(f"Destino Teste: {geo_test}")

# 1. Coleta dos elementos de prancha de GEO_SUBSOLO 1.DWG original
dwg_src = TQSDwg.Dwg()
dwg_src.file.Open(geo_orig)
it = dwg_src.iterator
it.Begin()

moldura_elems = []
title_elems = []
notes_elems = []

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        x = it.x1
        y = it.y1
        is_zero = (x == 0.0 and y == 0.0 and name in ["Fim de bloco", "Fim de objeto", "Objeto"])
        
        # Moldura 180-70 (Nível 100)
        if lvl == 100:
            if name == "Linha":
                moldura_elems.append(("Linha", it.color, it.style, it.x1, it.y1, it.x2, it.y2))
            elif name == "Texto":
                moldura_elems.append(("Texto", it.color, it.style, it.x1, it.y1, it.textHeight, it.textAngle, it.text))
        
        # Título Executivo
        elif lvl in [222, 250] and x <= 11000 and y >= -2300:
            if name == "Texto":
                title_elems.append(("Texto", lvl, it.color, it.style, it.x1, it.y1, it.textHeight, it.textAngle, it.text))
        
        # Notas Técnicas e Legendas (X >= 16200 e Y >= -2350)
        elif x >= 16200 and y >= -2350 and lvl != 100 and not is_zero:
            item = {"name": name, "level": lvl, "color": it.color, "style": it.style}
            if name == "Linha":
                item["coords"] = (it.x1, it.y1, it.x2, it.y2)
                notes_elems.append(item)
            elif name == "Texto":
                item["coords"] = (it.x1, it.y1, it.textHeight, it.textAngle, it.text)
                notes_elems.append(item)
            elif name == "Circulo":
                item["coords"] = (it.xc, it.yc, it.radius)
                notes_elems.append(item)
            elif name in ["Polyline", "Indefinido"]:
                item["name"] = "Polyline"
                pts = [it.GetPolylinePt(i) for i in range(it.xySize)]
                item["pts"] = pts
                notes_elems.append(item)
            elif name == "Bloco":
                item["block"] = (it.blockName, it.x1, it.y1, it.xScale, it.yScale, it.insertAngle)
                notes_elems.append(item)
    if not it.Next():
        break
dwg_src.file.Close()

print(f"\nElementos coletados:")
print(f"  * Moldura: {len(moldura_elems)}")
print(f"  * Título: {len(title_elems)}")
for t in title_elems:
    print(f"    - Nível {t[1]}: '{t[8]}' at ({t[4]:.1f}, {t[5]:.1f})")
print(f"  * Notas e Legendas: {len(notes_elems)}")

# 2. Copiar FOR0003 para geo_test
shutil.copy2(for_path, geo_test)
dwg_dest = TQSDwg.Dwg()
dwg_dest.file.Open(geo_test)

# 3. Purgar cabeçalho provisório em X < 11000 e Y >= -2450
it_d = dwg_dest.iterator
it_d.Begin()
to_erase = []
while True:
    pos = it_d.GetElementReadPosition()
    if pos:
        txt = getattr(it_d, "text", "")
        if any(k in txt for k in ["Planta PISO DO SUBSOLO", "Escala 1:50"]) and it_d.x1 < 11000 and it_d.y1 >= -2450:
            to_erase.append(pos)
    if not it_d.Next():
        break

print(f"\nRemovendo {len(to_erase)} elementos de cabeçalho provisório...")
for p in reversed(to_erase):
    dwg_dest.edit.Erase(p)

# 4. Inserir elementos de prancha
print("\nInserindo Moldura 180-70...")
dwg_dest.draw.level = 100
for m in moldura_elems:
    dwg_dest.draw.color = m[1]
    dwg_dest.draw.style = m[2]
    if m[0] == "Linha":
        dwg_dest.draw.Line(m[3], m[4], m[5], m[6])
    elif m[0] == "Texto":
        dwg_dest.draw.Text(m[3], m[4], m[5], m[6], m[7])

print("Inserindo Título Executivo...")
for t in title_elems:
    dwg_dest.draw.level = t[1]
    dwg_dest.draw.color = t[2]
    dwg_dest.draw.style = t[3]
    dwg_dest.draw.Text(t[4], t[5], t[6], t[7], t[8])

print("Inserindo Notas Técnicas e Legendas...")
for n in notes_elems:
    dwg_dest.draw.level = n["level"]
    dwg_dest.draw.color = n["color"]
    dwg_dest.draw.style = n["style"]
    if n["name"] == "Linha":
        x1, y1, x2, y2 = n["coords"]
        dwg_dest.draw.Line(x1, y1, x2, y2)
    elif n["name"] == "Texto":
        x, y, h, ang, txt = n["coords"]
        dwg_dest.draw.Text(x, y, h, ang, txt)
    elif n["name"] == "Circulo":
        xc, yc, r = n["coords"]
        dwg_dest.draw.Circle(xc, yc, r)
    elif n["name"] == "Polyline":
        dwg_dest.draw.PolyStart()
        dwg_dest.draw.PolyEnterXY([list(p) for p in n["pts"]])
        dwg_dest.draw.Polyline()
    elif n["name"] == "Bloco":
        bname, bx, by, escx, escy, bang = n["block"]
        dwg_dest.draw.BlockInsert(bname, bx, by, escx, escy, bang)

dwg_dest.settings.scale = 50.0
dwg_dest.file.Save()
dwg_dest.file.Close()

print(f"\nSalvo com sucesso em: {geo_test}")

# 5. Auditoria completa do arquivo gerado
dwg_chk = TQSDwg.Dwg()
dwg_chk.file.Open(geo_test)
it_c = dwg_chk.iterator
it_c.Begin()

tot = 0
lvls = {}
vigas = []
vigas_coords = {}

while True:
    if it_c.GetElementReadPosition():
        tot += 1
        lvl = it_c.level
        lvls[lvl] = lvls.get(lvl, 0) + 1
        if lvl == 8 and it_c.elementName == "Texto":
            vigas.append(it_c.text)
            vigas_coords[it_c.text] = (round(it_c.x1, 1), round(it_c.y1, 1))
    if not it_c.Next():
        break
dwg_chk.file.Close()

print("\n--- RESULTADO DA AUDITORIA DO TESTE ---")
print(f"Total de elementos: {tot}")
print(f"Moldura (lvl 100): {lvls.get(100, 0)}")
print(f"Título (lvl 222): {lvls.get(222, 0)}")
print(f"Escala título (lvl 250): {lvls.get(250, 0)}")
print(f"Vigas identificadas (lvl 8): {len(vigas)}")
print(f"Contornos (lvl 235): {lvls.get(235, 0)}")
print(f"Vigas (primeiras 10): {sorted(vigas)[:10]}")
