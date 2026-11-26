with open("src/agent/chat_agent.py", "r", encoding="utf-8") as f:
    chat_lines = f.readlines()

new_chat_lines = []
for line in chat_lines:
    if 'tokens = [w for w in re.split(' in line and 'ed["nome"].lower())' in line:
        indent = line[:line.find('tokens')]
        new_chat_lines.append(indent + 'PALAVRAS_RESERVADAS_EDIFICIO = {"pilar", "pilares", "viga", "vigas", "laje", "lajes", "pavimento", "pavimentos", "piso", "pisos", "edificio", "edificios", "modelo", "modelos", "carga", "cargas", "planta", "plantas", "forma", "formas", "projeto", "projetos", "obra", "obras", "modificacao", "modificacoes", "alteracao", "alteracoes", "terreo"}\n')
        new_chat_lines.append(indent + 'tokens = [w for w in re.split(r\'[\\s\\-_[\\]]+\', ed["nome"].lower()) if len(w) > 3 and w not in PALAVRAS_RESERVADAS_EDIFICIO]\n')
    else:
        new_chat_lines.append(line)

with open("src/agent/chat_agent.py", "w", encoding="utf-8") as f:
    f.writelines(new_chat_lines)
print("chat_agent.py rewritten")

with open("src/agent/orchestrator.py", "r", encoding="utf-8") as f:
    orch_lines = f.readlines()

new_orch_lines = []
for line in orch_lines:
    if 'tokens = [w for w in re.split(' in line and 'ed["nome"].lower())' in line:
        indent = line[:line.find('tokens')]
        new_orch_lines.append(indent + 'PALAVRAS_RESERVADAS_EDIFICIO = {"pilar", "pilares", "viga", "vigas", "laje", "lajes", "pavimento", "pavimentos", "piso", "pisos", "edificio", "edificios", "modelo", "modelos", "carga", "cargas", "planta", "plantas", "forma", "formas", "projeto", "projetos", "obra", "obras", "modificacao", "modificacoes", "alteracao", "alteracoes", "terreo"}\n')
        new_orch_lines.append(indent + 'tokens = [w for w in re.split(r\'[\\s\\-_[\\]]+\', ed["nome"].lower()) if len(w) > 3 and w not in PALAVRAS_RESERVADAS_EDIFICIO]\n')
    else:
        new_orch_lines.append(line)

with open("src/agent/orchestrator.py", "w", encoding="utf-8") as f:
    f.writelines(new_orch_lines)
print("orchestrator.py rewritten")
