with open('src/ui/cli.py', 'r', encoding='utf-8') as f:
    content = f.read()

target_arg = '    parser.add_argument("--formas-alvenaria", action="store_true", help="Gera a Planta de Formas de Alvenaria Estrutural (1ª Fiada) executiva")'
new_arg = target_arg + '\n    parser.add_argument("--geometria-ca", "--geo-ca", action="store_true", help="Gera a prancha executiva de Geometria/Formas de Concreto Armado (GEO_<PAVIMENTO>.DWG)")'

target_exec = '    # Geração de Planta de Formas de Alvenaria Estrutural (1ª Fiada)'
new_exec = '''    # Geração de Geometria de Concreto Armado (GEO_<PAVIMENTO>.DWG)
    if getattr(args, "geometria_ca", False):
        ed = args.edificio or "055"
        pav = args.pavimento or "PISO DO SUBSOLO 1"
        print(f"\\n=========================================================")
        print(f"   AUTQS - GEOMETRIA DE CONCRETO ARMADO (GEO)")
        print(f"=========================================================")
        print(f"Edifício:  {ed}")
        print(f"Pavimento: {pav}\\n")
        res = orchestrator.registry.executar_ferramenta("gerar_geometria_concreto_armado", {
            "edificio_nome": ed,
            "pavimento": pav,
            "escala": 50
        })
        if res.get("status") == "sucesso":
            aud = res.get("auditoria", {})
            print(f"[OK] GEOMETRIA DE CONCRETO ARMADO GERADA COM SUCESSO:")
            print(f"     Arquivo:   {res.get('caminho_geo')}")
            print(f"     Vigas:     {aud.get('total_vigas')} vigas identificadas")
            print(f"     Elementos: {aud.get('total_elementos')} elementos gráficos")
            print(f"     Moldura:   180-70 Nível 100 ({aud.get('moldura_elementos')} elementos)")
            print(f"     Notas:     {aud.get('notas_elementos')} elementos de notas técnicas e legendas")
            print(f"\\nAbra o desenho diretamente no TQS (Menu Arquivo > Abrir Desenho) para visualização e plotagem.")
        else:
            print(f"[ERRO] Falha ao gerar geometria: {res.get('erro')}")
        return

    # Geração de Planta de Formas de Alvenaria Estrutural (1ª Fiada)'''

if target_arg in content and target_exec in content:
    content = content.replace(target_arg, new_arg)
    content = content.replace(target_exec, new_exec)
    with open('src/ui/cli.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("CLI patched successfully!")
else:
    print("Targets not found in cli.py!")
