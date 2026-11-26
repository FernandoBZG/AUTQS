import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A"
dwg_path = os.path.join(piso_dir, "PRE_FOR_1aFIADA_TIPO A.DWG")

print(f"Auditando: {dwg_path}")
print(f"Tamanho: {os.path.getsize(dwg_path)} bytes")

dwg = TQSDwg.Dwg()
dwg.file.Open(dwg_path)
it = dwg.iterator
it.Begin()

lvls = {}
types = {}
titles = []
vaos_239 = []
lajes_10 = []
esp_13 = []
lvl237_lines = []

while True:
    if it.GetElementReadPosition():
        lvl = it.level
        name = it.elementName
        lvls[lvl] = lvls.get(lvl, 0) + 1
        types[name] = types.get(name, 0) + 1
        txt = getattr(it, "text", "")
        
        if lvl == 222 and name == "Texto":
            titles.append(txt)
        elif lvl == 239 and name == "Texto":
            vaos_239.append(txt)
        elif lvl == 10 and name == "Texto":
            lajes_10.append(txt)
        elif lvl == 13 and name == "Texto":
            esp_13.append(txt)
        elif lvl == 237 and name == "Linha":
            lvl237_lines.append(((round(it.x1, 1), round(it.y1, 1)), (round(it.x2, 1), round(it.y2, 1))))
    if not it.Next():
        break
dwg.file.Close()

print(f"\nTotal elementos gráficos: {sum(lvls.values())}")
print(f"Distribuição de níveis: {sorted(lvls.items())}")
print(f"Tipos de elementos: {types}")
print(f"Títulos (Nível 222): {titles}")
print(f"Lajes identificadas (Nível 10): {len(lajes_10)} (amostra: {lajes_10[:10]})")
print(f"Espessuras (Nível 13): {len(esp_13)} (amostra: {esp_13[:10]})")
print(f"Dimensões de vãos (Nível 239): {len(vaos_239)} (amostra: {vaos_239[:10]})")
print(f"Linhas no Nível 237 (sacadas/shafts): {len(lvl237_lines)}")

# Verificar backups na pasta
bkps = [f for f in os.listdir(piso_dir) if "PRE_FOR_1aFIADA_TIPO A_BKP" in f]
print(f"\nBackups encontrados: {len(bkps)} (mais recente: {sorted(bkps)[-1] if bkps else 'Nenhum'})")
