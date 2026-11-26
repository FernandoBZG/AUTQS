import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A"
dwg_path = os.path.join(piso_dir, "TIPO A.DWG")

dwg = TQSDwg.Dwg()
dwg.file.Open(dwg_path)
it = dwg.iterator
it.Begin()

shaft_texts = []
while True:
    if it.GetElementReadPosition():
        txt = getattr(it, "text", "")
        if any(k in txt.upper() for k in ["SHAFT", "DUTO", "PRUM", "ABERT", "VAZIO", "SEC", "INST"]):
            shaft_texts.append((it.level, txt, round(it.x1, 1), round(it.y1, 1)))
    if not it.Next():
        break
dwg.file.Close()

print(f"Shaft texts in TIPO A.DWG: {len(shaft_texts)}")
for s in shaft_texts:
    print(f"  {s}")
