with open('src/agent/tools.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '            {\n                "type": "function",\n                "function": {\n                    "name": "padronizar_arquitetura_tqs",'

tool_def = '''            {
                "type": "function",
                "function": {
                    "name": "gerar_geometria_concreto_armado",
                    "description": self._skills["gerar_geometria_concreto_armado"].descricao,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {
                                "type": "string",
                                "description": "Nome ou código do edifício TQS (ex: '055' ou 'Flexinc - [055] Jardim Europa CA')."
                            },
                            "pavimento": {
                                "type": "string",
                                "description": "Nome do pavimento (ex: 'PISO DO SUBSOLO 1', 'Térreo', 'Tipo')."
                            },
                            "escala": {
                                "type": "integer",
                                "description": "Escala regulamentar do desenho (padrão 50)."
                            }
                        },
                        "required": ["edificio_nome", "pavimento"]
                    }
                }
            },\n''' + target

if target in content:
    content = content.replace(target, tool_def)
    with open('src/agent/tools.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Tool definition added successfully!")
else:
    print("Target not found!")
