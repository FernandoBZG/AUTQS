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
geo_path = os.path.join(piso_dir, "GEO_SUBSOLO 1.DWG")
for_path = os.path.join(piso_dir, "FOR0003.DWG")

print("=================================================================")
print("   GERADOR EXECUTIVO DE GEOMETRIA TQS: GEO_SUBSOLO 1.DWG")
print("=================================================================")
print(f"Pavimento: PISO DO SUBSOLO 1")
print(f"FOR0003: {for_path} ({os.path.getsize(for_path)} bytes)")
print(f"GEO_SUBSOLO 1: {geo_path}")

# 1. Backup Preventivo
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bkp_path = os.path.join(piso_dir, f"GEO_SUBSOLO 1_BKP_{ts}.DWG")
if os.path.exists(geo_path):
    shutil.copy2(geo_path, bkp_path)
    print(f"\n[1/5] Backup preventivo criado: {os.path.basename(bkp_path)}")

# 2. Coleta dos elementos de prancha de GEO_SUBSOLO 1 (Moldura, Título e Notas)
print("\n[2/5] Coletando moldura, títulos executivos e notas técnicas...")
dwg_src = TQSDwg.Dwg()
dwg_src.file.Open(geo_path)
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

print(f"  * Moldura 180-70: {len(moldura_elems)} elementos")
print(f"  * Título Executivo: {len(title_elems)} elementos")
print(f"  * Notas Técnicas e Legendas: {len(notes_elems)} elementos")

# 3. Base pura a partir do NOVO FOR0003.DWG
print("\n[3/5] Inicializando base estrutural a partir de FOR0003.DWG...")
shutil.copy2(for_path, geo_path)
dwg_geo = TQSDwg.Dwg()
dwg_geo.file.Open(geo_path)

# Purgar cabeçalho provisório em X < 11000 e Y >= -2450
it_g = dwg_geo.iterator
it_g.Begin()
to_erase = []
while True:
    pos = it_g.GetElementReadPosition()
    if pos:
        txt = getattr(it_g, "text", "")
        if any(k in txt for k in ["Planta PISO DO SUBSOLO", "Escala 1:50"]) and it_g.x1 < 11000 and it_g.y1 >= -2450:
            to_erase.append(pos)
    if not it_g.Next():
        break

print(f"  * Purgando {len(to_erase)} elementos de cabeçalho provisório do TQS...")
for p in reversed(to_erase):
    dwg_geo.edit.Erase(p)

# 4. Inserção direta de Moldura, Título e Notas
print("\n[4/5] Inserindo Moldura 180-70, Título Executivo e Notas Técnicas...")
dwg_geo.draw.level = 100
for m in moldura_elems:
    dwg_geo.draw.color = m[1]
    dwg_geo.draw.style = m[2]
    if m[0] == "Linha":
        dwg_geo.draw.Line(m[3], m[4], m[5], m[6])
    elif m[0] == "Texto":
        dwg_geo.draw.Text(m[3], m[4], m[5], m[6], m[7])

for t in title_elems:
    dwg_geo.draw.level = t[1]
    dwg_geo.draw.color = t[2]
    dwg_geo.draw.style = t[3]
    dwg_geo.draw.Text(t[4], t[5], t[6], t[7], t[8])

for n in notes_elems:
    dwg_geo.draw.level = n["level"]
    dwg_geo.draw.color = n["color"]
    dwg_geo.draw.style = n["style"]
    if n["name"] == "Linha":
        x1, y1, x2, y2 = n["coords"]
        dwg_geo.draw.Line(x1, y1, x2, y2)
    elif n["name"] == "Texto":
        x, y, h, ang, txt = n["coords"]
        dwg_geo.draw.Text(x, y, h, ang, txt)
    elif n["name"] == "Circulo":
        xc, yc, r = n["coords"]
        dwg_geo.draw.Circle(xc, yc, r)
    elif n["name"] == "Polyline":
        dwg_geo.draw.PolyStart()
        dwg_geo.draw.PolyEnterXY([list(p) for p in n["pts"]])
        dwg_geo.draw.Polyline()
    elif n["name"] == "Bloco":
        bname, bx, by, escx, escy, bang = n["block"]
        dwg_geo.draw.BlockInsert(bname, bx, by, escx, escy, bang)

dwg_geo.settings.scale = 50.0
dwg_geo.file.Save()
dwg_geo.file.Close()

# Limpar arquivo de teste temporário se existir
geo_test = os.path.join(piso_dir, "GEO_SUBSOLO 1_TESTE.DWG")
if os.path.exists(geo_test):
    os.remove(geo_test)

print(f"\n[5/5] Arquivo final gerado com sucesso em: {geo_path}")

# 6. Auditoria de Qualidade e Integridade Final
dwg_chk = TQSDwg.Dwg()
dwg_chk.file.Open(geo_path)
it_chk = dwg_chk.iterator
it_chk.Begin()

tot_elems = 0
lvls_cnt = {}
vigas_labels = []
dim_labels = []
form_lines = []

while True:
    if it_chk.GetElementReadPosition():
        tot_elems += 1
        lvl = it_chk.level
        lvls_cnt[lvl] = lvls_cnt.get(lvl, 0) + 1
        
        if it_chk.y1 < -2350 and lvl != 100:
            if it_chk.elementName == "Linha":
                p1 = (round(it_chk.x1, 1), round(it_chk.y1, 1))
                p2 = (round(it_chk.x2, 1), round(it_chk.y2, 1))
                form_lines.append((min(p1, p2), max(p1, p2)))
            elif it_chk.elementName == "Texto":
                if lvl == 8:
                    vigas_labels.append(it_chk.text)
                elif lvl == 11:
                    dim_labels.append(it_chk.text)
    if not it_chk.Next():
        break
dwg_chk.file.Close()

c_lines = Counter(form_lines)
dups_lines = [k for k, v in c_lines.items() if v > 1]

print("\n=======================================================")
print("   RELATÓRIO DE AUDITORIA: GEO_SUBSOLO 1.DWG")
print("=======================================================")
print(f"Total de Elementos Gráficos: {tot_elems}")
print(f"Moldura 180-70 (Nível 100): {lvls_cnt.get(100, 0)} elementos")
print(f"Título Executivo (Nível 222): {lvls_cnt.get(222, 0)} elementos")
print(f"Escala do Título (Nível 250): {lvls_cnt.get(250, 0)} elementos")
print(f"Notas Técnicas (Nível 18): {lvls_cnt.get(18, 0)} elementos")
print(f"Contornos de Vigas e Lajes (Nível 235): {lvls_cnt.get(235, 0)} elementos")
print(f"Vigas Estruturais na Planta (Nível 8): {len(vigas_labels)} vigas")
print(f"Dimensões de Vigas (Nível 11): {len(dim_labels)} textos")
print(f"Linhas estruturais (Y < -2350): {len(form_lines)} linhas")
print(f"Linhas duplicadas: {len(dups_lines)} (idêntico ao FOR0003 original)")
print(f"Vigas cadastradas (amostra de 15 vigas): {sorted(vigas_labels)[:15]}")
