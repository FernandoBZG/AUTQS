import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [054] Visconde do Herval AE\TIPO A"

for fname in ["LAJ0290.DWG", "DesFiad1.DWG", "DesGeom.DWG", "DesAlven.DWG"]:
    fpath = os.path.join(piso_dir, fname)
    if not os.path.exists(fpath):
        continue
    print(f"\n==========================================")
    print(f"Arquivo: {fname}")
    dwg = TQSDwg.Dwg()
    dwg.file.Open(fpath)
    it = dwg.iterator
    it.Begin()
    lvls = {}
    furos = []
    texts = []
    polys = []
    while True:
        if it.GetElementReadPosition():
            lvls[it.level] = lvls.get(it.level, 0) + 1
            txt = getattr(it, "text", "")
            if any(k in txt.upper() for k in ["SHAFT", "FUR", "ABERT", "VAZ", "SEC"]):
                texts.append((it.level, txt, round(it.x1, 1), round(it.y1, 1)))
            if it.elementName == "Polyline":
                # Check small closed polylines (potential shafts)
                polys.append((it.level, it.xySize, round(it.x1, 1), round(it.y1, 1)))
        if not it.Next():
            break
    dwg.file.Close()
    print(f"Levels: {sorted(lvls.items())}")
    print(f"Texts with shaft/furo: {texts}")
    print(f"Total polylines: {len(polys)}")
