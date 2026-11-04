import sys, os, re
sys.path.insert(0, '.')
sys.path.append(r'src/reference')
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg

# 1. Read slab labels from LAJ0291.DWG
d = TQSDwg.Dwg(pedmv=0)
fn = r'C:\TQS\Flexinc - [055] Jardim Europa AE Ceramica\17PV\LAJ0291.DWG'
d.file.Open(fn)
it = d.iterator
it.Begin()
slab_labels = {}
while it.Next():
    txt = it.text.strip()
    if txt.startswith('L') and txt[1:].isdigit():
        slab_labels[txt] = (it.x1, it.y1)
d.file.Close()

# 2. Parse 17PV.LST
lst_fn = r'C:\TQS\Flexinc - [055] Jardim Europa AE Ceramica\17PV\17PV.LST'
with open(lst_fn, 'r', encoding='latin1') as f:
    lst_text = f.read()

loads_match = re.search(r'Cargas sobre as lajes.*?\n(.*?)\n\s*\n\s*Influ', lst_text, re.S)
current_loads = {}
if loads_match:
    for line in loads_match.group(1).splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit():
            current_loads['L' + parts[0]] = (float(parts[1]), float(parts[2]))

chunks = re.split(r'\n(?=Laje\s+\d+\s+Tipo)', lst_text)
slabs_info = {}
for ch in chunks[1:]:
    lines = ch.strip().splitlines()
    m0 = re.match(r'Laje\s+(\d+)\s+Tipo\s+([A-Z])\s+P=\s*([\d\.]+)', lines[0])
    if not m0:
        continue
    lnum, ltipo, ptot = m0.groups()
    m1 = re.search(r'H=\s*(\d+).*?=\s*([\d\.]+)', lines[1])
    h = m1.group(1) if m1 else '16'
    area = float(m1.group(2)) if m1 else 0.0
    beams = sorted(list(set(re.findall(r'V(\d+)', ch))), key=lambda x: int(x))
    s_name = 'L' + lnum
    pos = slab_labels.get(s_name, (0.0, 0.0))
    cd = current_loads.get(s_name, (0.2, 0.4))[0]
    pp = current_loads.get(s_name, (0.2, 0.4))[1]
    slabs_info[s_name] = {
        'num': int(lnum),
        'tipo': ltipo,
        'ptot': float(ptot),
        'h': int(h),
        'area': area,
        'beams': beams,
        'pos': pos,
        'cdist': cd,
        'pp': pp
    }

print(f'Total slabs in 17PV: {len(slabs_info)}')
for k in sorted(slabs_info.keys(), key=lambda x: slabs_info[x]['num']):
    s = slabs_info[k]
    print(f"{k:<4}: Area={s['area']:5.2f}m2, Pos=({s['pos'][0]:7.1f}, {s['pos'][1]:7.1f}), CDist={s['cdist']:.3f}, Beams={s['beams'][:5]}")
