import sys
import os
sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")

from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

caminho = r"C:\TQS\Flexinc - [055] Jardim Europa CA\ESPACIAL\GABARITO.DWG"
print(f"Abrindo {caminho} ({os.path.getsize(caminho)} bytes)...")

dwg = TQSDwg.Dwg()
dwg.file.Open(caminho)

it = dwg.iterator
it.Begin()

total_elements = 0
texts = []
while True:
    pos = it.GetElementReadPosition()
    if pos:
        total_elements += 1
        if it.elementName == "Texto":
            txt = getattr(it, "text", getattr(it, "string", ""))
            texts.append((txt, it.x1, it.y1, it.level))
    if not it.Next():
        break

dwg.file.Close()

print(f"Total de elementos no DWG: {total_elements}")
print(f"Total de textos: {len(texts)}")

origem_texts = [t for t in texts if "17051" in str(t[0]) or "ORIGEM" in str(t[0]).upper()]
print("\nTextos encontrados de ORIGEM e REFERÊNCIA:")
for t in origem_texts:
    print(f"  Nível {t[3]} Pos ({t[1]:.1f}, {t[2]:.1f}): {t[0]}")

p88_texts = [t for t in texts if str(t[0]) in ["P88", "23.0", "9.4", "P87", "-291.0"]]
print("\nTextos com 'P88', 'P87' ou coordenadas relativas:")
for t in p88_texts:
    print(f"  Nível {t[3]} Pos ({t[1]:.1f}, {t[2]:.1f}): {t[0]}")
