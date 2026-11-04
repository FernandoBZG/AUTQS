import sys, os
sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

ed = r"C:\TQS\Flexinc - [055] Jardim Europa CA"
piso = [d for d in os.listdir(ed) if "RREO" in d.upper()][0]
piso_dir = os.path.join(ed, piso)
geo_f = os.path.join(piso_dir, "GEO_Térreo.DWG")
for_f = os.path.join(piso_dir, "FOR0004.DWG")

# 1. Let's create a temporary DWG with only the sheet framing and notes from GEO_Térreo.DWG
temp_sheet = os.path.join(piso_dir, "TEMP_SHEET.DWG")

# Open geo_f and collect elements to erase (the old fôrma)
dwg_sheet = TQSDwg.Dwg()
dwg_sheet.file.Open(geo_f)

it = dwg_sheet.iterator
it.Begin()
posicoes_apagar = []

while True:
    pos = it.GetElementReadPosition()
    if pos:
        lvl = it.level
        x = it.x1
        y = it.y1
        # Elements to ERASE (old fôrma):
        eh_forma = False
        if lvl in [4, 8, 9, 10, 11, 12, 13, 235, 241, 242]:
            eh_forma = True
        elif lvl == 221 and (x < 16200 or y < -2300):
            eh_forma = True
        elif lvl == 0 and (x < 16200 or y < -2300):
            eh_forma = True
        elif lvl == 250:
            txt_val = getattr(it, "text", getattr(it, "string", ""))
            if "Planta PISO DO PAVIMENTO" in str(txt_val):
                eh_forma = True

        if eh_forma:
            posicoes_apagar.append(pos)

    if not it.Next():
        break

print(f"Total elements to erase from old fôrma: {len(posicoes_apagar)}")
for p in posicoes_apagar:
    dwg_sheet.edit.Erase(p)

dwg_sheet.file.SaveAs(temp_sheet)
dwg_sheet.file.Close()

# Verify temp_sheet
dwg_chk = TQSDwg.Dwg()
dwg_chk.file.Open(temp_sheet)
it = dwg_chk.iterator
it.Begin()
cnt = 0
lvls = {}
while True:
    pos = it.GetElementReadPosition()
    if pos:
        cnt += 1
        lvls[it.level] = lvls.get(it.level, 0) + 1
    if not it.Next():
        break
dwg_chk.file.Close()
print(f"TEMP_SHEET remaining elements: {cnt}, levels: {sorted(lvls.items())}")

# 2. Now open FOR0004.DWG, erase the default title at X=8620.6, and DwgMix temp_sheet!
test_geo_out = os.path.join(piso_dir, "TESTE_GEO_TERREO.DWG")

dwg_final = TQSDwg.Dwg()
dwg_final.file.Open(for_f)

# Erase default title at X < 9000
it = dwg_final.iterator
it.Begin()
pos_erase_for = []
while True:
    pos = it.GetElementReadPosition()
    if pos:
        if it.x1 < 9000 and it.elementName == "Texto":
            pos_erase_for.append(pos)
    if not it.Next():
        break

print(f"Erasing {len(pos_erase_for)} default title texts from FOR0004 (X < 9000)")
for p in pos_erase_for:
    dwg_final.edit.Erase(p)

# Mix temp_sheet into FOR0004
ret_mix = dwg_final.draw.DwgMix(temp_sheet, 0.0, 0.0)
print(f"DwgMix result: {ret_mix} (0=OK)")

dwg_final.file.SaveAs(test_geo_out)
dwg_final.file.Close()

# Clean temp_sheet
if os.path.exists(temp_sheet):
    os.remove(temp_sheet)

# Verify TESTE_GEO_TERREO.DWG
dwg_ver = TQSDwg.Dwg()
dwg_ver.file.Open(test_geo_out)
it = dwg_ver.iterator
it.Begin()
cnt_final = 0
final_lvls = {}
key_texts = []
while True:
    pos = it.GetElementReadPosition()
    if pos:
        cnt_final += 1
        final_lvls[it.level] = final_lvls.get(it.level, 0) + 1
        if it.elementName == "Texto":
            t = getattr(it, "text", getattr(it, "string", ""))
            if "V65" in t or "25/100" in t or "30/80" in t or "GEOMETRIA" in t.upper() or "180-70" in t:
                key_texts.append((t, it.level, it.x1, it.y1))
    if not it.Next():
        break
dwg_ver.file.Close()

print(f"\n=== TESTE_GEO_TERREO.DWG VERIFICATION ===")
print(f"Total elements: {cnt_final}")
print(f"Levels: {sorted(final_lvls.items())}")
print(f"Key texts found:")
for t in key_texts:
    print(f"  Level {t[1]} Pos ({t[2]:.1f}, {t[3]:.1f}): {t[0]}")
