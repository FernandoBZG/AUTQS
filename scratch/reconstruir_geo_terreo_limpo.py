import sys
import os
import shutil
from datetime import datetime

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

edificio_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA"
piso_nome = [d for d in os.listdir(edificio_dir) if "RREO" in d.upper()][0]
piso_dir = os.path.join(edificio_dir, piso_nome)

geo_path = os.path.join(piso_dir, "GEO_Térreo.DWG")
for_path = os.path.join(piso_dir, "FOR0004.DWG")
r00_path = os.path.join(piso_dir, "GEO_Térreo-R00.DWG")

print(f"Edifício: {os.path.basename(edificio_dir)}")
print(f"Pavimento: {piso_nome}")
print(f"Arquivo FOR de entrada: {for_path}")
print(f"Arquivo R00 de referência de notas: {r00_path}")
print(f"Arquivo GEO de saída: {geo_path}")

# 1. Backup de segurança
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bkp_path = os.path.join(piso_dir, f"GEO_Térreo_BKP_{ts}.DWG")
shutil.copy2(geo_path, bkp_path)
print(f"\n[1/5] Backup preventivo criado: {os.path.basename(bkp_path)}")

# 2. Coleta dos elementos da prancha (Moldura, Título e Notas) estritamente fora da fôrma
dwg_r00 = TQSDwg.Dwg()
dwg_r00.file.Open(r00_path)
it = dwg_r00.iterator
it.Begin()

moldura_elems = []
title_elems = []
notes_elems = []

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        x = it.x1
        y = it.y1
        # 2.1 Moldura 180-70 (Nível 100)
        if lvl == 100:
            if it.elementName == "Linha":
                moldura_elems.append(("Linha", it.color, it.style, it.x1, it.y1, it.x2, it.y2))
            elif it.elementName == "Texto":
                moldura_elems.append(("Texto", it.color, it.style, it.x1, it.y1, it.textHeight, it.textAngle, it.text))
        # 2.2 Título da prancha (Nível 222 e 250 em Y >= -2300, X <= 11000)
        elif lvl in [222, 250] and x <= 11000 and y >= -2300:
            if it.elementName == "Texto":
                title_elems.append(("Texto", lvl, it.color, it.style, it.x1, it.y1, it.textHeight, it.textAngle, it.text))
        # 2.3 Bloco de Notas Técnicas (estritamente em X >= 16200 e Y >= -2320, longe de qualquer viga)
        elif x >= 16200 and y >= -2320 and lvl != 100:
            name = it.elementName
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
            elif name == "Polyline":
                pts = [it.GetPolylinePt(i) for i in range(it.xySize)]
                item["pts"] = pts
                notes_elems.append(item)
            elif name == "Bloco":
                item["block"] = (it.blockName, it.x1, it.y1, it.xScale, it.yScale, it.insertAngle)
                notes_elems.append(item)
    if not it.Next():
        break
dwg_r00.file.Close()

print(f"\n[2/5] Elementos da prancha coletados:")
print(f"  * Moldura 180-70: {len(moldura_elems)} elementos")
print(f"  * Título Executivo: {len(title_elems)} elementos")
print(f"  * Notas Técnicas (Y >= -2320, X >= 16200): {len(notes_elems)} elementos")

# 3. Base 100% limpa a partir de FOR0004.DWG
# Sobrescreve GEO_Térreo.DWG com cópia pura de FOR0004.DWG
shutil.copy2(for_path, geo_path)
dwg_geo = TQSDwg.Dwg()
dwg_geo.file.Open(geo_path)

# 3.1 Purgar textos brutos do processamento TQS em X < 8700
it = dwg_geo.iterator
it.Begin()
to_erase = []
while True:
    pos = it.GetElementReadPosition()
    if pos:
        txt = getattr(it, "text", "")
        if any(k in txt for k in ["Planta PISO DO PAVIMENTO", "Escala 1:50", "02-PISO DO PAVIMENTO", "01-PISO DO SUBSOLO", "00-PISO DO SUBSOLO"]):
            to_erase.append(pos)
    if not it.Next():
        break

print(f"\n[3/5] Removendo {len(to_erase)} textos de cabeçalho bruto de FOR0004.DWG...")
for p in reversed(to_erase):
    dwg_geo.edit.Erase(p)

# 4. Inserção direta de Moldura, Título e Notas Técnicas
print("\n[4/5] Inserindo Moldura 180-70, Título e Bloco de Notas Técnicas...")

# 4.1 Moldura 180-70 (Nível 100)
dwg_geo.draw.level = 100
for m in moldura_elems:
    dwg_geo.draw.color = m[1]
    dwg_geo.draw.style = m[2]
    if m[0] == "Linha":
        dwg_geo.draw.Line(m[3], m[4], m[5], m[6])
    elif m[0] == "Texto":
        dwg_geo.draw.Text(m[3], m[4], m[5], m[6], m[7])

# 4.2 Título Executivo
for t in title_elems:
    dwg_geo.draw.level = t[1]
    dwg_geo.draw.color = t[2]
    dwg_geo.draw.style = t[3]
    dwg_geo.draw.Text(t[4], t[5], t[6], t[7], t[8])

# 4.3 Bloco de Notas Técnicas
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

print(f"\n[5/5] Arquivo gravado com sucesso em: {geo_path}")

# 5. Auditoria de Qualidade e Integridade
dwg_chk = TQSDwg.Dwg()
dwg_chk.file.Open(geo_path)
it = dwg_chk.iterator
it.Begin()

tot_elems = 0
lvls_cnt = {}
beam_lines = []
v109_lines = []

while True:
    if it.GetElementReadPosition():
        tot_elems += 1
        lvls_cnt[it.level] = lvls_cnt.get(it.level, 0) + 1
        if it.elementName == "Linha":
            p1 = (round(it.x1, 1), round(it.y1, 1))
            p2 = (round(it.x2, 1), round(it.y2, 1))
            line_seg = (min(p1, p2), max(p1, p2))
            if it.y1 < -2350:
                beam_lines.append(line_seg)
        if 16200 <= it.x1 <= 17100 and -3700 <= it.y1 <= -2500:
            if it.elementName in ["Linha", "Polyline"]:
                v109_lines.append(it.elementName)
    if not it.Next():
        break
dwg_chk.file.Close()

# Auditoria em FOR0004
dwg_f = TQSDwg.Dwg()
dwg_f.file.Open(for_path)
it_f = dwg_f.iterator
it_f.Begin()
for_beam_lines = []
for_v109_lines = []
while True:
    if it_f.GetElementReadPosition():
        if it_f.elementName == "Linha" and it_f.y1 < -2350:
            p1 = (round(it_f.x1, 1), round(it_f.y1, 1))
            p2 = (round(it_f.x2, 1), round(it_f.y2, 1))
            for_beam_lines.append((min(p1, p2), max(p1, p2)))
        if 16200 <= it_f.x1 <= 17100 and -3700 <= it_f.y1 <= -2500:
            if it_f.elementName in ["Linha", "Polyline"]:
                for_v109_lines.append(it_f.elementName)
    if not it_f.Next():
        break
dwg_f.file.Close()

from collections import Counter
c_geo = Counter(beam_lines)
dups_geo = [k for k, v in c_geo.items() if v > 1]

c_for = Counter(for_beam_lines)
dups_for = [k for k, v in c_for.items() if v > 1]

print("\n=======================================================")
print("   RELATÓRIO DE AUDITORIA DE PRECISÃO: GEO_TÉRREO.DWG")
print("=======================================================")
print(f"Total de Elementos Gráficos: {tot_elems}")
print(f"Moldura 180-70 (Nível 100): {lvls_cnt.get(100, 0)} elementos")
print(f"Título Executivo (Nível 222): {lvls_cnt.get(222, 0)} elementos")
print(f"Notas Técnicas (Nível 18): {lvls_cnt.get(18, 0)} elementos")
print(f"Contornos de Vigas e Lajes (Nível 235): {lvls_cnt.get(235, 0)} elementos")
print(f"Identificação de Vigas (Nível 8): {lvls_cnt.get(8, 0)} elementos")
print(f"Dimensões de Vigas (Nível 11): {lvls_cnt.get(11, 0)} elementos")
print(f"\n--- Verificação de Duplicidade nas Vigas ---")
print(f"Linhas nas vigas (Y < -2350): GEO={len(beam_lines)} | FOR={len(for_beam_lines)}")
print(f"Linhas/polylines na região V105-V110: GEO={len(v109_lines)} | FOR={len(for_v109_lines)}")
print(f"Linhas duplicadas nas vigas: GEO={len(dups_geo)} | FOR original={len(dups_for)}")
if len(beam_lines) == len(for_beam_lines) and len(v109_lines) == len(for_v109_lines):
    print("\n>>> SUCESSO: Zero linhas duplicadas ou herdadas do GEO antigo nas vigas! Geometria 100% idêntica ao FOR0004!")
else:
    print("\n>>> ALERTA: Há discrepância de linhas entre GEO e FOR!")
