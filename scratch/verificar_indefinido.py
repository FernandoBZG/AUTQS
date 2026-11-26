import sys
import os

sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

piso_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA\PISO DO SUBSOLO 1"
geo_path = os.path.join(piso_dir, "GEO_SUBSOLO 1.DWG")

dwg_geo = TQSDwg.Dwg()
dwg_geo.file.Open(geo_path)
it = dwg_geo.iterator
it.Begin()

while True:
    if it.GetElementReadPosition():
        if it.elementName == "Indefinido":
            print(f"Indefinido: lvl={it.level}, color={it.color}, style={it.style}, pos=({it.x1}, {it.y1}), text='{getattr(it, 'text', '')}'")
            # print all attributes of iterator
            attrs = [a for a in dir(it) if not a.startswith("_")]
            for a in attrs:
                try:
                    v = getattr(it, a)
                    if not callable(v):
                        print(f"  {a}: {v}")
                except:
                    pass
    if not it.Next():
        break
dwg_geo.file.Close()
