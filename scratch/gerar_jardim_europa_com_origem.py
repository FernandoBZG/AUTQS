import sys
import os
sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")

from src.skills.case_01_planta_cargas.skill import PlantaDeCargasSkill
from src.agent.chat_agent import AutqsChatAgent

skill = PlantaDeCargasSkill()
edificio = "Flexinc - [055] Jardim Europa CA"
rx, ry = 17051.5856, -4041.0557

print(f"Executando PlantaDeCargasSkill para '{edificio}' com origem ({rx}, {ry})...")
res = skill.executar(
    edificio_nome=edificio,
    caminho_edificio=r"C:\TQS\Flexinc - [055] Jardim Europa CA",
    origem_cotas=(rx, ry),
    caminho_saida_desenho="GABARITO.DWG"
)

print("Status:", res.get("status"))
print("Arquivo DWG Local:", res.get("arquivo_desenho_gerado"))
print("Arquivo DWG ESPACIAL:", res.get("caminho_espacial"))
print("Backup gerado:", res.get("caminho_backup"))
print("Origem registrada:", res.get("origem_cotas"))
print("Total pilares:", res.get("total_pilares_fundacao"))

pilares = res.get("pilares", [])
print("\nPrimeiros 5 pilares com coordenadas absolutas e relativas:")
for p in pilares[:5]:
    print(f"Pilar {p['pilar']:<5} | Absoluto: X={p['xcg_m']*100:.1f} cm, Y={p['ycg_m']*100:.1f} cm | Relativo: X={p['xcg_rel_cm']:.1f} cm, Y={p['ycg_rel_cm']:.1f} cm (X={p['xcg_rel_m']:.3f} m, Y={p['ycg_rel_m']:.3f} m)")

print("\nÚltimos 5 pilares com coordenadas absolutas e relativas:")
for p in pilares[-5:]:
    print(f"Pilar {p['pilar']:<5} | Absoluto: X={p['xcg_m']*100:.1f} cm, Y={p['ycg_m']*100:.1f} cm | Relativo: X={p['xcg_rel_cm']:.1f} cm, Y={p['ycg_rel_cm']:.1f} cm (X={p['xcg_rel_m']:.3f} m, Y={p['ycg_rel_m']:.3f} m)")
