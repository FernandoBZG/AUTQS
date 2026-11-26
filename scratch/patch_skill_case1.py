with open("src/skills/case_01_planta_cargas/skill.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update builder_dwg call
old_call = '''            if caminho_alvo.lower().endswith(".dwg"):
                builder_dwg = TQSDwgPlantaDeCargasBuilder()
                arquivo_desenho_gerado = builder_dwg.construir_planta_de_cargas(planta, caminho_alvo, escala=escala_req)'''

new_call = '''            origem_cotas = kwargs.get("origem_cotas")
            if not origem_cotas and kwargs.get("origem_x") is not None and kwargs.get("origem_y") is not None:
                origem_cotas = (float(kwargs["origem_x"]), float(kwargs["origem_y"]))

            if caminho_alvo.lower().endswith(".dwg"):
                builder_dwg = TQSDwgPlantaDeCargasBuilder()
                arquivo_desenho_gerado = builder_dwg.construir_planta_de_cargas(
                    planta, caminho_alvo, escala=escala_req, origem_cotas=origem_cotas
                )'''

assert old_call in code, "old_call not found in skill.py"
code = code.replace(old_call, new_call, 1)

# 2. Update resumo_pilares
old_resumo = '''        # 4. Resumo estruturado para o Agente Cognitivo
        resumo_pilares = [
            {
                "pilar": p.nome,
                "secao_cm": f"{p.geometria.b:.1f}x{p.geometria.h:.1f}",
                "xcg_m": round(p.baricentro.x / 100.0, 3) if p.baricentro else None,
                "ycg_m": round(p.baricentro.y / 100.0, 3) if p.baricentro else None,
                "nk_max_tf": p.esforcos.nk_max if p.esforcos else 0.0,
                "nk_min_tf": p.esforcos.nk_min if p.esforcos else 0.0,
                "mxk_tfm": p.esforcos.mxk if p.esforcos else 0.0,
                "myk_tfm": p.esforcos.myk if p.esforcos else 0.0,
                "hx_tf": p.esforcos.hx if p.esforcos else 0.0,
                "hy_tf": p.esforcos.hy if p.esforcos else 0.0,
            }
            for p in pilares_processados
        ]'''

new_resumo = '''        # 4. Resumo estruturado para o Agente Cognitivo
        rx_m = (origem_cotas[0] / 100.0) if ('origem_cotas' in locals() and origem_cotas) else 0.0
        ry_m = (origem_cotas[1] / 100.0) if ('origem_cotas' in locals() and origem_cotas) else 0.0
        rx_cm = origem_cotas[0] if ('origem_cotas' in locals() and origem_cotas) else 0.0
        ry_cm = origem_cotas[1] if ('origem_cotas' in locals() and origem_cotas) else 0.0

        resumo_pilares = [
            {
                "pilar": p.nome,
                "secao_cm": f"{p.geometria.b:.1f}x{p.geometria.h:.1f}",
                "xcg_m": round(p.baricentro.x / 100.0, 3) if p.baricentro else None,
                "ycg_m": round(p.baricentro.y / 100.0, 3) if p.baricentro else None,
                "xcg_rel_m": round((p.baricentro.x / 100.0) - rx_m, 3) if p.baricentro else None,
                "ycg_rel_m": round((p.baricentro.y / 100.0) - ry_m, 3) if p.baricentro else None,
                "xcg_rel_cm": round(p.baricentro.x - rx_cm, 1) if p.baricentro else None,
                "ycg_rel_cm": round(p.baricentro.y - ry_cm, 1) if p.baricentro else None,
                "nk_max_tf": p.esforcos.nk_max if p.esforcos else 0.0,
                "nk_min_tf": p.esforcos.nk_min if p.esforcos else 0.0,
                "mxk_tfm": p.esforcos.mxk if p.esforcos else 0.0,
                "myk_tfm": p.esforcos.myk if p.esforcos else 0.0,
                "hx_tf": p.esforcos.hx if p.esforcos else 0.0,
                "hy_tf": p.esforcos.hy if p.esforcos else 0.0,
            }
            for p in pilares_processados
        ]'''

assert old_resumo in code, "old_resumo not found in skill.py"
code = code.replace(old_resumo, new_resumo, 1)

# 3. Update resultado dict
old_res_dict = '''        resultado = {
            "status": "sucesso",
            "edificio": edificio_nome,
            "caminho_edificio": caminho_edificio,
            "caminho_espacial": caminho_espacial_gerado,
            "caminho_backup": caminho_backup_gerado,
            "pavimento": pavimento_fundacao,
            "total_pilares_fundacao": len(pilares_processados),
            "pilares": resumo_pilares,
            "dados_porlid": dados_porlid,
            "arquivo_desenho_gerado": arquivo_desenho_gerado,
        }'''

new_res_dict = '''        orig_dict = {"x_cm": float(origem_cotas[0]), "y_cm": float(origem_cotas[1])} if ('origem_cotas' in locals() and origem_cotas) else None
        resultado = {
            "status": "sucesso",
            "edificio": edificio_nome,
            "caminho_edificio": caminho_edificio,
            "caminho_espacial": caminho_espacial_gerado,
            "caminho_backup": caminho_backup_gerado,
            "pavimento": pavimento_fundacao,
            "total_pilares_fundacao": len(pilares_processados),
            "pilares": resumo_pilares,
            "origem_cotas": orig_dict,
            "dados_porlid": dados_porlid,
            "arquivo_desenho_gerado": arquivo_desenho_gerado,
        }'''

assert old_res_dict in code, "old_res_dict not found in skill.py"
code = code.replace(old_res_dict, new_res_dict, 1)

with open("src/skills/case_01_planta_cargas/skill.py", "w", encoding="utf-8") as f:
    f.write(code)

print("skill.py updated successfully!")
