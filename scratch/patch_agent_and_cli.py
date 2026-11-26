import re

# 1. Update src/agent/tools.py
with open("src/agent/tools.py", "r", encoding="utf-8") as f:
    tools_code = f.read()

old_prop = '''                            "escala": {
                                "type": "integer",
                                "description": "Escala do desenho (50, 75 ou 100). Se omitido, auto-seleciona a ideal."
                            }'''

new_prop = '''                            "escala": {
                                "type": "integer",
                                "description": "Escala do desenho (50, 75 ou 100). Se omitido, auto-seleciona a ideal."
                            },
                            "origem_x": {
                                "type": "number",
                                "description": "Coordenada X (cm) de referência da origem (0,0) das cotas relativas."
                            },
                            "origem_y": {
                                "type": "number",
                                "description": "Coordenada Y (cm) de referência da origem (0,0) das cotas relativas."
                            }'''

assert old_prop in tools_code, "old_prop not found in tools.py"
tools_code = tools_code.replace(old_prop, new_prop, 1)

old_exec_tools = '''        if nome_funcao in self._skills:
            skill = self._skills[nome_funcao]
            return skill.executar(**argumentos)'''

new_exec_tools = '''        if nome_funcao in self._skills:
            skill = self._skills[nome_funcao]
            if nome_funcao == "gerar_planta_de_cargas":
                if "origem_cotas" not in argumentos and "origem_x" in argumentos and "origem_y" in argumentos:
                    try:
                        argumentos["origem_cotas"] = (float(argumentos["origem_x"]), float(argumentos["origem_y"]))
                    except Exception:
                        pass
            return skill.executar(**argumentos)'''

assert old_exec_tools in tools_code, "old_exec_tools not found in tools.py"
tools_code = tools_code.replace(old_exec_tools, new_exec_tools, 1)

with open("src/agent/tools.py", "w", encoding="utf-8") as f:
    f.write(tools_code)
print("tools.py updated successfully!")

# 2. Update src/agent/orchestrator.py
with open("src/agent/orchestrator.py", "r", encoding="utf-8") as f:
    orch_code = f.read()

old_orch_planta = '''        # 8. Geração de Planta de Cargas / Gabarito
        if "planta" in cmd_lower or "carga" in cmd_lower or "gabarito" in cmd_lower:
            if "caminho_saida_desenho" not in params:
                params["caminho_saida_desenho"] = "GABARITO.DWG"
            return self.registry.executar_ferramenta("gerar_planta_de_cargas", params)'''

new_orch_planta = '''        # 8. Geração de Planta de Cargas / Gabarito
        eh_planta_cargas = (
            "planta" in cmd_lower or "carga" in cmd_lower or "gabarito" in cmd_lower
            or ("cota" in cmd_lower and any(k in cmd_norm for k in ["REFERENC", "ORIGEM", "PONTO", "0,0"]))
        )
        if eh_planta_cargas:
            if "caminho_saida_desenho" not in params:
                params["caminho_saida_desenho"] = "GABARITO.DWG"
            if "origem_cotas" not in params:
                m_orig = re.search(r'(?:ponto|origem|refer[eê]ncia)[^\\d+-]*?([+-]?\\d+(?:\\.\\d+)?)\\s*[,;\\s]\\s*([+-]?\\d+(?:\\.\\d+)?)', comando, re.IGNORECASE)
                if m_orig:
                    try:
                        params["origem_cotas"] = (float(m_orig.group(1)), float(m_orig.group(2)))
                    except Exception:
                        pass
            return self.registry.executar_ferramenta("gerar_planta_de_cargas", params)'''

assert old_orch_planta in orch_code, "old_orch_planta not found in orchestrator.py"
orch_code = orch_code.replace(old_orch_planta, new_orch_planta, 1)

with open("src/agent/orchestrator.py", "w", encoding="utf-8") as f:
    f.write(orch_code)
print("orchestrator.py updated successfully!")

# 3. Update src/agent/chat_agent.py
with open("src/agent/chat_agent.py", "r", encoding="utf-8") as f:
    chat_code = f.read()

old_chat_planta = '''        # 7. Solicitação de Geração de Planta de Cargas / Gabarito
        pediu_gerar_planta = (
            ("planta" in msg_lower and any(k in msg_lower for k in ["carga", "loca", "gerar", "desenh", "emitir", "funda"]))
            or any(k in msg_lower for k in ["gerar dwg", "criar dwg", "emitir prancha", "desenhar prancha", "gerar prancha", "gabarito"])
            or "gabarito" in msg_lower
        )
        if pediu_gerar_planta:
            edificio_alvo = self.edificio_ativo or "054"
            try:
                res = self.orchestrator.processar_comando_local(
                    "gerar_planta_de_cargas",
                    {"edificio_nome": edificio_alvo, "caminho_saida_desenho": "GABARITO.DWG"}
                )'''

new_chat_planta = '''        # 7. Solicitação de Geração de Planta de Cargas / Gabarito
        pediu_gerar_planta = (
            ("planta" in msg_lower and any(k in msg_lower for k in ["carga", "loca", "gerar", "desenh", "emitir", "funda"]))
            or any(k in msg_lower for k in ["gerar dwg", "criar dwg", "emitir prancha", "desenhar prancha", "gerar prancha", "gabarito"])
            or "gabarito" in msg_lower
            or ("cota" in msg_lower and any(k in msg_norm for k in ["REFERENC", "ORIGEM", "PONTO", "0,0"]))
        )
        if pediu_gerar_planta:
            edificio_alvo = self.edificio_ativo or "054"
            # Detecção de origem de cotas
            origem_cotas = None
            m_orig = re.search(r'(?:ponto|origem|refer[eê]ncia)[^\\d+-]*?([+-]?\\d+(?:\\.\\d+)?)\\s*[,;\\s]\\s*([+-]?\\d+(?:\\.\\d+)?)', msg, re.IGNORECASE)
            if m_orig:
                try:
                    origem_cotas = (float(m_orig.group(1)), float(m_orig.group(2)))
                except Exception:
                    pass

            params_planta = {"edificio_nome": edificio_alvo, "caminho_saida_desenho": "GABARITO.DWG"}
            if origem_cotas:
                params_planta["origem_cotas"] = origem_cotas

            try:
                res = self.orchestrator.processar_comando_local(
                    "gerar_planta_de_cargas",
                    params_planta
                )'''

assert old_chat_planta in chat_code, "old_chat_planta not found in chat_agent.py"
chat_code = chat_code.replace(old_chat_planta, new_chat_planta, 1)

old_chat_resp = '''                    resposta_texto = (
                        f"### 🎯 Planta de Cargas e Locação Gerada com Sucesso!\\n\\n"
                        f"- **Edifício:** `{res.get('edificio')}`\\n"
                        f"- **Total de Pilares na Fundação:** **{total} pilares**\\n"
                        f"{porlid_info}"
                        f"- **Escala:** 1:50 com Projeção de Moldura Oficial TQS\\n"
                        f"- **Arquivo DWG Nativo:** `{dwg_local}`\\n"
                        f"- **Salvo na pasta ESPACIAL do TQS:** `{copia_tqs}`\\n"
                        f"{bkp_info}\\n"
                    )'''

new_chat_resp = '''                    orig_info = ""
                    orig_ret = res.get("origem_cotas")
                    if orig_ret:
                        orig_info = f"- 📍 **Origem das Cotas Relativas (0,0):** `X = {orig_ret['x_cm']:.2f} cm` | `Y = {orig_ret['y_cm']:.2f} cm`\\n"

                    resposta_texto = (
                        f"### 🎯 Planta de Cargas e Locação Gerada com Sucesso!\\n\\n"
                        f"- **Edifício:** `{res.get('edificio')}`\\n"
                        f"- **Total de Pilares na Fundação:** **{total} pilares**\\n"
                        f"{orig_info}"
                        f"{porlid_info}"
                        f"- **Escala:** 1:50 com Projeção de Moldura Oficial TQS\\n"
                        f"- **Arquivo DWG Nativo:** `{dwg_local}`\\n"
                        f"- **Salvo na pasta ESPACIAL do TQS:** `{copia_tqs}`\\n"
                        f"{bkp_info}\\n"
                    )'''

assert old_chat_resp in chat_code, "old_chat_resp not found in chat_agent.py"
chat_code = chat_code.replace(old_chat_resp, new_chat_resp, 1)

with open("src/agent/chat_agent.py", "w", encoding="utf-8") as f:
    f.write(chat_code)
print("chat_agent.py updated successfully!")

# 4. Update src/ui/cli.py
with open("src/ui/cli.py", "r", encoding="utf-8") as f:
    cli_code = f.read()

old_cli_arg = '    parser.add_argument("--desenho", type=str, default=None, help="Caminho do arquivo de desenho de saída (DWG/DXF)")'
new_cli_arg = '''    parser.add_argument("--desenho", type=str, default=None, help="Caminho do arquivo de desenho de saída (DWG/DXF)")
    parser.add_argument("--origem-x", type=float, default=None, help="Coordenada X (cm) da origem (0,0) das cotas relativas")
    parser.add_argument("--origem-y", type=float, default=None, help="Coordenada Y (cm) da origem (0,0) das cotas relativas")'''

assert old_cli_arg in cli_code, "old_cli_arg not found in cli.py"
cli_code = cli_code.replace(old_cli_arg, new_cli_arg, 1)

old_cli_build = '''            caminho_saida = args.desenho or "GABARITO.DWG"
            if caminho_saida.lower().endswith(".dwg"):
                from src.drawing.tqs_dwg_builder import TQSDwgPlantaDeCargasBuilder
                builder = TQSDwgPlantaDeCargasBuilder()
                arquivo_gerado = builder.construir_planta_de_cargas(planta, caminho_saida)'''

new_cli_build = '''            caminho_saida = args.desenho or "GABARITO.DWG"
            origem_cotas = (args.origem_x, args.origem_y) if (args.origem_x is not None and args.origem_y is not None) else None
            if caminho_saida.lower().endswith(".dwg"):
                from src.drawing.tqs_dwg_builder import TQSDwgPlantaDeCargasBuilder
                builder = TQSDwgPlantaDeCargasBuilder()
                arquivo_gerado = builder.construir_planta_de_cargas(planta, caminho_saida, origem_cotas=origem_cotas)'''

assert old_cli_build in cli_code, "old_cli_build not found in cli.py"
cli_code = cli_code.replace(old_cli_build, new_cli_build, 1)

with open("src/ui/cli.py", "w", encoding="utf-8") as f:
    f.write(cli_code)
print("cli.py updated successfully!")
