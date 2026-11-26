with open("src/agent/chat_agent.py", "r", encoding="utf-8") as f:
    chat_code = f.read()

# 1. Update building regex in chat_agent.py
old_num_match = "num_match = re.search(r'\\b(0\\d{2}|\\d{3,4})\\b', msg)"
new_num_match = "num_match = re.search(r'(?<![\\d.])(0\\d{2}|\\d{3,4})(?![\\d.])', msg)"
if old_num_match in chat_code:
    chat_code = chat_code.replace(old_num_match, new_num_match, 1)

# 2. Update pediu_gerar_planta and origin extraction in chat_agent.py
old_planta_block = '''        # 7. Solicitação de Geração de Planta de Cargas / Gabarito
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
            m_orig = re.search(r'(?:ponto|origem|refer[eê]ncia)[^\d+-]*?([+-]?\d+(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d+(?:\.\d+)?)', msg, re.IGNORECASE)
            if m_orig:
                try:
                    origem_cotas = (float(m_orig.group(1)), float(m_orig.group(2)))
                except Exception:
                    pass'''

new_planta_block = '''        # 7. Solicitação de Geração de Planta de Cargas / Gabarito
        m_coords_avulsas = re.search(
            r'^\s*(?:mudar\s+(?:para\s+)?)?(?:origem\s+(?:para\s+)?)?([+-]?\d{2,}(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d{2,}(?:\.\d+)?)\s*$',
            msg,
            re.IGNORECASE,
        )
        pediu_gerar_planta = (
            ("planta" in msg_lower and any(k in msg_lower for k in ["carga", "loca", "gerar", "desenh", "emitir", "funda"]))
            or any(k in msg_lower for k in ["gerar dwg", "criar dwg", "emitir prancha", "desenhar prancha", "gerar prancha", "gabarito"])
            or "gabarito" in msg_lower
            or ("cota" in msg_lower and any(k in msg_norm for k in ["REFERENC", "ORIGEM", "PONTO", "0,0"]))
            or bool(m_coords_avulsas)
            or ("mudar" in msg_lower and any(k in msg_norm for k in ["ORIGEM", "PONTO", "COTA", "REFERENC"]))
        )
        if pediu_gerar_planta:
            edificio_alvo = self.edificio_ativo or "054"
            # Detecção de origem de cotas
            origem_cotas = None
            if m_coords_avulsas:
                origem_cotas = (float(m_coords_avulsas.group(1)), float(m_coords_avulsas.group(2)))
            else:
                m_orig = re.search(r'(?:ponto|origem|refer[eê]ncia|mudar\s+para)[^\d+-]*?([+-]?\d+(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d+(?:\.\d+)?)', msg, re.IGNORECASE)
                if m_orig:
                    try:
                        origem_cotas = (float(m_orig.group(1)), float(m_orig.group(2)))
                    except Exception:
                        pass'''

assert old_planta_block in chat_code, "old_planta_block not found in chat_agent.py"
chat_code = chat_code.replace(old_planta_block, new_planta_block, 1)

with open("src/agent/chat_agent.py", "w", encoding="utf-8") as f:
    f.write(chat_code)
print("chat_agent.py patched successfully!")

# 3. Update orchestrator.py
with open("src/agent/orchestrator.py", "r", encoding="utf-8") as f:
    orch_code = f.read()

old_orch_num = "num_match = re.search(r'\\b(0\\d{2}|\\d{3,4})\\b', comando)"
new_orch_num = "num_match = re.search(r'(?<![\\d.])(0\\d{2}|\\d{3,4})(?![\\d.])', comando)"
if old_orch_num in orch_code:
    orch_code = orch_code.replace(old_orch_num, new_orch_num, 1)

old_orch_planta = '''        # 8. Geração de Planta de Cargas / Gabarito
        eh_planta_cargas = (
            "planta" in cmd_lower or "carga" in cmd_lower or "gabarito" in cmd_lower
            or ("cota" in cmd_lower and any(k in cmd_norm for k in ["REFERENC", "ORIGEM", "PONTO", "0,0"]))
        )
        if eh_planta_cargas:
            if "caminho_saida_desenho" not in params:
                params["caminho_saida_desenho"] = "GABARITO.DWG"
            if "origem_cotas" not in params:
                m_orig = re.search(r'(?:ponto|origem|refer[eê]ncia)[^\d+-]*?([+-]?\d+(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d+(?:\.\d+)?)', comando, re.IGNORECASE)
                if m_orig:
                    try:
                        params["origem_cotas"] = (float(m_orig.group(1)), float(m_orig.group(2)))
                    except Exception:
                        pass
            return self.registry.executar_ferramenta("gerar_planta_de_cargas", params)'''

new_orch_planta = '''        # 8. Geração de Planta de Cargas / Gabarito
        m_coords_avulsas = re.search(
            r'^\s*(?:mudar\s+(?:para\s+)?)?(?:origem\s+(?:para\s+)?)?([+-]?\d{2,}(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d{2,}(?:\.\d+)?)\s*$',
            comando,
            re.IGNORECASE,
        )
        eh_planta_cargas = (
            "planta" in cmd_lower or "carga" in cmd_lower or "gabarito" in cmd_lower
            or ("cota" in cmd_lower and any(k in cmd_norm for k in ["REFERENC", "ORIGEM", "PONTO", "0,0"]))
            or bool(m_coords_avulsas)
            or ("mudar" in cmd_lower and any(k in cmd_norm for k in ["ORIGEM", "PONTO", "COTA", "REFERENC"]))
        )
        if eh_planta_cargas:
            if "caminho_saida_desenho" not in params:
                params["caminho_saida_desenho"] = "GABARITO.DWG"
            if "origem_cotas" not in params:
                if m_coords_avulsas:
                    params["origem_cotas"] = (float(m_coords_avulsas.group(1)), float(m_coords_avulsas.group(2)))
                else:
                    m_orig = re.search(r'(?:ponto|origem|refer[eê]ncia|mudar\s+para)[^\d+-]*?([+-]?\d+(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d+(?:\.\d+)?)', comando, re.IGNORECASE)
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
print("orchestrator.py patched successfully!")
