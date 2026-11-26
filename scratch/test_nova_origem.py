import sys
sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")

from src.skills.case_01_planta_cargas.skill import PlantaDeCargasSkill

skill = PlantaDeCargasSkill()
edificio = "Flexinc - [055] Jardim Europa CA"
rx, ry = 17089.5900, -4041.1600

print(f"Gerando Planta de Cargas para '{edificio}' com nova origem ({rx}, {ry})...")
res = skill.executar(
    edificio_nome=edificio,
    caminho_edificio=r"C:\TQS\Flexinc - [055] Jardim Europa CA",
    origem_cotas=(rx, ry),
    caminho_saida_desenho="GABARITO.DWG"
)

print("Status:", res.get("status"))
print("Origem gravada:", res.get("origem_cotas"))
print("Arquivo DWG Local:", res.get("arquivo_desenho_gerado"))
print("Arquivo DWG ESPACIAL:", res.get("caminho_espacial"))
print("Backup gerado:", res.get("caminho_backup"))

pilares = res.get("pilares", [])
print("\nPilares de destaque com a nova referência (X=17089.59 cm, Y=-4041.16 cm):")
for nome in ["P88", "P87", "P86", "P85", "P84", "P1", "P2", "P30", "P44"]:
    p = next((x for x in pilares if x["pilar"] == nome), None)
    if p:
        print(f"  {p['pilar']:<5} | Absoluto: ({p['xcg_m']*100:.1f}, {p['ycg_m']*100:.1f}) cm | Relativo: X={p['xcg_rel_cm']:.1f} cm, Y={p['ycg_rel_cm']:.1f} cm (X={p['xcg_rel_m']:.3f} m, Y={p['ycg_rel_m']:.3f} m)")
