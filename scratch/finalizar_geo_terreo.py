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
if not os.path.exists(geo_path):
    geo_path = [os.path.join(piso_dir, f) for f in os.listdir(piso_dir) if f.upper() == "GEO_TÉRREO.DWG"][0]

bkp_path = os.path.join(piso_dir, "GEO_Térreo_BKP_20261028_143438.DWG")

print(f"Edifício: {os.path.basename(edificio_dir)}")
print(f"Pavimento: {piso_nome}")
print(f"Arquivo BKP de referência: {bkp_path}")
print(f"Arquivo GEO alvo: {geo_path}")

# 1. Extração dos 32 elementos de moldura (Nível 100) do BKP
dwg_bkp = TQSDwg.Dwg()
dwg_bkp.file.Open(bkp_path)
it = dwg_bkp.iterator
it.Begin()
lvl100_elems = []
while True:
    if it.GetElementReadPosition() and it.level == 100:
        if it.elementName == "Linha":
            lvl100_elems.append({
                "type": "Linha",
                "color": it.color,
                "style": it.style,
                "x1": it.x1, "y1": it.y1,
                "x2": it.x2, "y2": it.y2
            })
        elif it.elementName == "Texto":
            lvl100_elems.append({
                "type": "Texto",
                "color": it.color,
                "style": it.style,
                "x1": it.x1, "y1": it.y1,
                "h": it.textHeight,
                "ang": it.textAngle,
                "text": it.text
            })
    if not it.Next():
        break
dwg_bkp.file.Close()

print(f"\n[1/3] Elementos de moldura extraídos do Nível 100: {len(lvl100_elems)}")

# 2. Inserção no GEO_Térreo.DWG
dwg_geo = TQSDwg.Dwg()
dwg_geo.file.Open(geo_path)
dwg_geo.draw.level = 100

for elem in lvl100_elems:
    dwg_geo.draw.color = elem["color"]
    dwg_geo.draw.style = elem["style"]
    if elem["type"] == "Linha":
        dwg_geo.draw.Line(elem["x1"], elem["y1"], elem["x2"], elem["y2"])
    elif elem["type"] == "Texto":
        dwg_geo.draw.Text(elem["x1"], elem["y1"], elem["h"], elem["ang"], elem["text"])

dwg_geo.settings.scale = 50.0
dwg_geo.file.SaveAs(geo_path)
dwg_geo.file.Close()

print(f"[2/3] Elementos de moldura inseridos e arquivo salvo.")

# 3. Auditoria completa do GEO_Térreo.DWG
dwg_aud = TQSDwg.Dwg()
dwg_aud.file.Open(geo_path)
it = dwg_aud.iterator
it.Begin()

total_elementos = 0
niveis_contagem = {}
textos_auditados = []

while True:
    if it.GetElementReadPosition():
        total_elementos += 1
        niveis_contagem[it.level] = niveis_contagem.get(it.level, 0) + 1
        if it.elementName == "Texto":
            t = getattr(it, "text", "")
            if any(k in str(t).upper() for k in ["GEOMETRIA", "180-70", "V65", "25/100", "DE BAIXO PARA CIMA", "RESERVATÓRIO"]):
                textos_auditados.append((t, it.level, it.x1, it.y1))
    if not it.Next():
        break
dwg_aud.file.Close()

print(f"\n=======================================================")
print(f"   RELATÓRIO DE AUDITORIA: GEO_TÉRREO.DWG")
print(f"=======================================================")
print(f"Total de Elementos Gráficos: {total_elementos}")
print(f"Nível 100 (Moldura 180-70): {niveis_contagem.get(100, 0)} elementos")
print(f"Nível 222 (Título Oficial): {niveis_contagem.get(222, 0)} elementos")
print(f"Nível 235 (Contornos de Vigas/Lajes Atualizados): {niveis_contagem.get(235, 0)} elementos")
print(f"Nível 18 (Notas Técnicas da Obra): {niveis_contagem.get(18, 0)} elementos")
print(f"Nível 224 (Legendas e Convenções): {niveis_contagem.get(224, 0)} elementos")
print(f"Nível 251 (Detalhes e Armações Tipológicas): {niveis_contagem.get(251, 0)} elementos")

print(f"\nTextos Chave Verificados no Desenho:")
for t in textos_auditados[:15]:
    print(f"  * Nível {t[1]:>3} ({t[2]:>8.1f}, {t[3]:>8.1f}): {t[0]}")

print(f"\n[3/3] Concluído com sucesso absoluto!")
