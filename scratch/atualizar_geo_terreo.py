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

for_path = os.path.join(piso_dir, "FOR0004.DWG")
if not os.path.exists(for_path):
    for_path = [os.path.join(piso_dir, f) for f in os.listdir(piso_dir) if f.upper().startswith("FOR") and f.upper().endswith(".DWG")][0]

print(f"Edifício: {os.path.basename(edificio_dir)}")
print(f"Pavimento: {piso_nome}")
print(f"Arquivo FOR de entrada: {for_path} ({os.path.getsize(for_path)} bytes)")
print(f"Arquivo GEO de destino: {geo_path} ({os.path.getsize(geo_path)} bytes)")

# 1. Backup de segurança do GEO_Térreo.DWG atual
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bkp_path = os.path.join(piso_dir, f"GEO_Térreo_BKP_{ts}.DWG")
shutil.copy2(geo_path, bkp_path)
bak_path = os.path.join(piso_dir, "GEO_Térreo.BAK")
shutil.copy2(geo_path, bak_path)
print(f"\n[1/5] Backup criado com sucesso: {os.path.basename(bkp_path)}")

# 2. Extração dos elementos de prancha (moldura 180-70, título PRÉ-GEOMETRIA e notas/legendas)
temp_sheet = os.path.join(piso_dir, f"TEMP_SHEET_{ts}.DWG")

dwg_sheet = TQSDwg.Dwg()
dwg_sheet.file.Open(geo_path)

it = dwg_sheet.iterator
it.Begin()
pos_antigas_forma = []

while True:
    pos = it.GetElementReadPosition()
    if pos:
        lvl = it.level
        x = it.x1
        y = it.y1
        # Entidades da fôrma antiga que devem ser substituídas pela fôrma atual:
        eh_forma_antiga = False
        if lvl in [4, 8, 9, 10, 11, 12, 13, 235, 241, 242]:
            eh_forma_antiga = True
        elif lvl in [0, 221] and (x < 16200 and y < -2300):
            eh_forma_antiga = True
        elif lvl == 250:
            txt_val = getattr(it, "text", getattr(it, "string", ""))
            if "Planta PISO DO PAVIMENTO" in str(txt_val):
                eh_forma_antiga = True

        if eh_forma_antiga:
            pos_antigas_forma.append(pos)

    if not it.Next():
        break

print(f"\n[2/5] Purgando {len(pos_antigas_forma)} elementos da fôrma antiga de 18/09...")
for p in pos_antigas_forma:
    dwg_sheet.edit.Erase(p)

dwg_sheet.file.SaveAs(temp_sheet)
dwg_sheet.file.Close()

# 3. Preparação do FOR0004.DWG (fôrma atualizada)
dwg_final = TQSDwg.Dwg()
dwg_final.file.Open(for_path)

it = dwg_final.iterator
it.Begin()
titulos_raw_apagar = []
while True:
    pos = it.GetElementReadPosition()
    if pos and it.elementName == "Texto":
        t = getattr(it, "text", getattr(it, "string", ""))
        if any(k in str(t) for k in ["Planta PISO DO PAVIMENTO", "Escala 1:50", "02-PISO DO PAVIMENTO"]):
            titulos_raw_apagar.append(pos)
    if not it.Next():
        break

print(f"\n[3/5] Removendo {len(titulos_raw_apagar)} textos brutos de cabeçalho do FOR0004...")
for p in titulos_raw_apagar:
    dwg_final.edit.Erase(p)

# 4. Mistura (DwgMix) da moldura e notas sobre a nova fôrma
print(f"\n[4/5] Misturando moldura oficial 180-70 e bloco de notas executivo via DwgMix...")
ret_mix = dwg_final.draw.DwgMix(temp_sheet, 0.0, 0.0)
if ret_mix != 0:
    raise RuntimeError(f"Falha no DwgMix (código de erro: {ret_mix})")

dwg_final.settings.scale = 50.0
dwg_final.dim.dimtxt = 0.20

# Salva sobre GEO_Térreo.DWG
dwg_final.file.SaveAs(geo_path)
dwg_final.file.Close()

# Limpa temporário
if os.path.exists(temp_sheet):
    os.remove(temp_sheet)

print(f"\n[5/5] Arquivo gravado com sucesso em: {geo_path}")

# 5. Verificação e Auditoria Final do GEO_Térreo.DWG atualizado
dwg_ver = TQSDwg.Dwg()
dwg_ver.file.Open(geo_path)

it = dwg_ver.iterator
it.Begin()
total_elementos = 0
niveis_contagem = {}
textos_auditados = []

while True:
    pos = it.GetElementReadPosition()
    if pos:
        total_elementos += 1
        niveis_contagem[it.level] = niveis_contagem.get(it.level, 0) + 1
        if it.elementName == "Texto":
            t = getattr(it, "text", getattr(it, "string", ""))
            if any(k in str(t).upper() for k in ["GEOMETRIA", "180-70", "V65", "25/100", "P1", "P88", "DE BAIXO PARA CIMA"]):
                textos_auditados.append((t, it.level, it.x1, it.y1))
    if not it.Next():
        break

dwg_ver.file.Close()

print(f"\n=======================================================")
print(f"   AUDITORIA FINAL DE SUCESSO: GEO_TÉRREO.DWG")
print(f"=======================================================")
print(f"Total de Elementos Gráficos: {total_elementos}")
print(f"Níveis de Desenho: {sorted(niveis_contagem.keys())}")
print(f"Contorno de Vigas e Lajes (Nível 235): {niveis_contagem.get(235, 0)} elementos")
print(f"Moldura Oficial TQS (Nível 100): {niveis_contagem.get(100, 0)} elementos")
print(f"Notas Técnicas e Critérios (Nível 18): {niveis_contagem.get(18, 0)} elementos")
print(f"\nTextos Chave Verificados:")
for t in textos_auditados[:15]:
    print(f"  * Nível {t[1]:>3} ({t[2]:>8.1f}, {t[3]:>8.1f}): {t[0]}")
