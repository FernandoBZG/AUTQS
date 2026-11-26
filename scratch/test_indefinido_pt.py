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
            print("Testing GetPolylinePt on Indefinido:")
            try:
                for i in range(min(5, it.xySize)):
                    print(f"  pt {i}: {it.GetPolylinePt(i)}")
            except Exception as e:
                print(f"  Error: {e}")
            print(f"Direct it.xy[:5]: {it.xy[:5]}")
    if not it.Next():
        break
dwg_geo.file.Close()
