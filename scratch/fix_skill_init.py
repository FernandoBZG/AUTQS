with open("src/skills/case_01_planta_cargas/skill.py", "r", encoding="utf-8") as f:
    code = f.read()

old_block = '''        # 3. Passo: Geração da Prancha de Desenho com Pilares + Tabela
        arquivo_desenho_gerado = None
        caminho_espacial_gerado = None
        if gerar_desenho and len(pilares_processados) > 0:
            caminho_alvo = caminho_saida_desenho or "GABARITO.DWG"
            escala_req = kwargs.get("escala")
            origem_cotas = kwargs.get("origem_cotas")
            if not origem_cotas and kwargs.get("origem_x") is not None and kwargs.get("origem_y") is not None:
                origem_cotas = (float(kwargs["origem_x"]), float(kwargs["origem_y"]))

            if caminho_alvo.lower().endswith(".dwg"):
                builder_dwg = TQSDwgPlantaDeCargasBuilder()
                arquivo_desenho_gerado = builder_dwg.construir_planta_de_cargas(
                    planta, caminho_alvo, escala=escala_req, origem_cotas=origem_cotas
                )
            else:
                builder_dxf = PlantaDeCargasDwgBuilder(escala=escala_req or 50)
                arquivo_desenho_gerado = builder_dxf.construir_planta_completa(planta, caminho_alvo)

            # A planta de cargas SEMPRE deve ficar na pasta ESPACIAL do edifício no TQS como GABARITO.DWG
            caminho_backup_gerado = None'''

new_block = '''        # 3. Passo: Geração da Prancha de Desenho com Pilares + Tabela
        origem_cotas = kwargs.get("origem_cotas")
        if not origem_cotas and kwargs.get("origem_x") is not None and kwargs.get("origem_y") is not None:
            origem_cotas = (float(kwargs["origem_x"]), float(kwargs["origem_y"]))

        arquivo_desenho_gerado = None
        caminho_espacial_gerado = None
        caminho_backup_gerado = None
        if gerar_desenho and len(pilares_processados) > 0:
            caminho_alvo = caminho_saida_desenho or "GABARITO.DWG"
            escala_req = kwargs.get("escala")

            if caminho_alvo.lower().endswith(".dwg"):
                builder_dwg = TQSDwgPlantaDeCargasBuilder()
                arquivo_desenho_gerado = builder_dwg.construir_planta_de_cargas(
                    planta, caminho_alvo, escala=escala_req, origem_cotas=origem_cotas
                )
            else:
                builder_dxf = PlantaDeCargasDwgBuilder(escala=escala_req or 50)
                arquivo_desenho_gerado = builder_dxf.construir_planta_completa(planta, caminho_alvo)

            # A planta de cargas SEMPRE deve ficar na pasta ESPACIAL do edifício no TQS como GABARITO.DWG'''

assert old_block in code, "old_block not found in skill.py"
code = code.replace(old_block, new_block, 1)

with open("src/skills/case_01_planta_cargas/skill.py", "w", encoding="utf-8") as f:
    f.write(code)

print("skill.py fixed successfully!")
