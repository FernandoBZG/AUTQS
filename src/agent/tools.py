from typing import Dict, Any, List, Optional
from src.skills.case_01_planta_cargas.skill import PlantaDeCargasSkill
from src.skills.case_02_processamento.skill import ProcessamentoEdificioSkill
from src.tqs_adapter.model_editor import TQSModelEditor

class ToolsRegistry:
    """
    Registro centralizado de ferramentas (Tools / Function Calling)
    disponíveis para o Agente Autônomo AUTQS e modelos LLM (Gemini/OpenAI).
    """

    def __init__(self):
        self._skills = {}
        # Registra as habilidades ativas na plataforma
        self.registrar_skill(PlantaDeCargasSkill())
        self.registrar_skill(ProcessamentoEdificioSkill())

    def registrar_skill(self, skill):
        self._skills[skill.nome] = skill

    def listar_ferramentas_para_llm(self) -> List[Dict[str, Any]]:
        """
        Retorna as definições no formato padrão de Function Calling (OpenAI / Gemini).
        """
        catalogo = [
            {
                "type": "function",
                "function": {
                    "name": "gerar_planta_de_cargas",
                    "description": self._skills["gerar_planta_de_cargas"].descricao,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {
                                "type": "string",
                                "description": "Nome ou código do edifício TQS (ex: '054' ou nome completo)."
                            },
                            "pavimento_fundacao": {
                                "type": "string",
                                "description": "Nome do pavimento de fundação (ex: FUNDACAO, BALDRAME)."
                            },
                            "escala": {
                                "type": "integer",
                                "description": "Escala do desenho (50, 75 ou 100). Se omitido, auto-seleciona a ideal."
                            }
                        },
                        "required": ["edificio_nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "processar_edificio",
                    "description": self._skills["processar_edificio"].descricao,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {
                                "type": "string",
                                "description": "Nome ou código do edifício TQS a processar (ex: '051', '049', '054')."
                            },
                            "tipo_processamento": {
                                "type": "string",
                                "enum": ["portico_cargas", "global"],
                                "description": "Tipo de processamento: 'portico_cargas' (formas, grelhas, pórtico e cargas) ou 'global' (completo com armaduras)."
                            },
                            "gerar_planta_apos_processar": {
                                "type": "boolean",
                                "description": "Se verdadeiro, gera imediatamente o GABARITO.DWG da planta de cargas assim que o cálculo terminar."
                            }
                        },
                        "required": ["edificio_nome"]
                    }
                }
            }
        ]

        # Ferramentas do Modelador Estrutural
        catalogo.extend([
            {
                "type": "function",
                "function": {
                    "name": "listar_pavimentos_modelo",
                    "description": "Lista todos os pavimentos do edifício no Modelador Estrutural com o resumo de vigas, lajes e pilares.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {"type": "string", "description": "Nome ou código do edifício (ex: '054')."}
                        },
                        "required": ["edificio_nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_elementos_pavimento",
                    "description": "Lista os elementos estruturais (vigas, lajes, pilares ou cargas) de um pavimento específico do edifício.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {"type": "string", "description": "Nome ou código do edifício."},
                            "pavimento": {"type": "string", "description": "Nome do pavimento (ex: 'terreo', '2 pavimento')."},
                            "tipo_elemento": {
                                "type": "string",
                                "enum": ["vigas", "lajes", "pilares", "cargas", "todos"],
                                "description": "Tipo de elemento estrutural a consultar."
                            }
                        },
                        "required": ["edificio_nome", "pavimento"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "editar_viga_modelo",
                    "description": "Modifica as dimensões da seção transversal (largura b, altura h) e/ou desnível de uma viga no Modelador Estrutural.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {"type": "string", "description": "Nome ou código do edifício."},
                            "pavimento": {"type": "string", "description": "Nome do pavimento onde a viga se encontra."},
                            "identificador_viga": {"type": "string", "description": "Nome ou número da viga (ex: 'V1', 'V12', '12')."},
                            "b_cm": {"type": "number", "description": "Nova largura da viga em centímetros (opcional)."},
                            "h_cm": {"type": "number", "description": "Nova altura da viga em centímetros (opcional)."},
                            "desnivel_cm": {"type": "number", "description": "Novo desnível/rebaixo em centímetros (opcional)."}
                        },
                        "required": ["edificio_nome", "pavimento", "identificador_viga"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "editar_laje_modelo",
                    "description": "Modifica a espessura, desnível e/ou carregamento distribuído de uma laje no Modelador Estrutural.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {"type": "string", "description": "Nome ou código do edifício."},
                            "pavimento": {"type": "string", "description": "Nome do pavimento."},
                            "identificador_laje": {"type": "string", "description": "Nome ou número da laje (ex: 'L1', 'L3', '3')."},
                            "espessura_cm": {"type": "number", "description": "Nova espessura da laje em centímetros (opcional)."},
                            "desnivel_cm": {"type": "number", "description": "Novo desnível/rebaixo em centímetros (opcional)."},
                            "carga_permanente_tf_m2": {"type": "number", "description": "Carga permanente g em tf/m² (opcional)."},
                            "carga_acidental_tf_m2": {"type": "number", "description": "Carga acidental q em tf/m² (opcional)."}
                        },
                        "required": ["edificio_nome", "pavimento", "identificador_laje"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "editar_pilar_modelo",
                    "description": "Modifica as dimensões da seção transversal de um pilar em determinado pavimento do Modelador Estrutural.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {"type": "string", "description": "Nome ou código do edifício."},
                            "pavimento": {"type": "string", "description": "Nome do pavimento."},
                            "identificador_pilar": {"type": "string", "description": "Nome ou número do pilar (ex: 'P1', 'P44')."},
                            "b_cm": {"type": "number", "description": "Dimensão B da seção do pilar em cm (opcional)."},
                            "h_cm": {"type": "number", "description": "Dimensão H da seção do pilar em cm (opcional)."}
                        },
                        "required": ["edificio_nome", "pavimento", "identificador_pilar"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "adicionar_carga_modelo",
                    "description": "Adiciona uma carga por área ou linear em um pavimento do edifício no Modelador Estrutural.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {"type": "string", "description": "Nome ou código do edifício."},
                            "pavimento": {"type": "string", "description": "Nome do pavimento."},
                            "tipo": {"type": "string", "enum": ["area", "linear"], "description": "Tipo de carga distribuída."},
                            "carga_permanente": {"type": "number", "description": "Valor permanente (tf/m² para área, tf/m para linear)."},
                            "carga_acidental": {"type": "number", "description": "Valor acidental (tf/m² para área, tf/m para linear)."},
                            "coordenadas": {
                                "type": "array",
                                "description": "Lista de coordenadas em metros [[x1, y1], [x2, y2], ...]."
                            }
                        },
                        "required": ["edificio_nome", "pavimento", "tipo"]
                    }
                }
            }
        ])
        return catalogo

    def executar_ferramenta(self, nome_funcao: str, argumentos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma ferramenta chamada pela IA ou pelos controladores de UI.
        """
        if nome_funcao in self._skills:
            skill = self._skills[nome_funcao]
            return skill.executar(**argumentos)

        # Roteamento das ferramentas do Modelador Estrutural
        edificio = argumentos.get("edificio_nome", "054")

        try:
            if nome_funcao == "listar_pavimentos_modelo":
                with TQSModelEditor(edificio) as editor:
                    pavs = editor.listar_pavimentos()
                    return {
                        "status": "sucesso",
                        "tipo": "pavimentos_modelo",
                        "edificio": editor.nome_edificio,
                        "pavimentos": pavs,
                    }

            elif nome_funcao == "listar_elementos_pavimento":
                pav = argumentos.get("pavimento", "")
                tipo = argumentos.get("tipo_elemento", "todos").lower()
                with TQSModelEditor(edificio) as editor:
                    resultado = {
                        "status": "sucesso",
                        "tipo": "elementos_pavimento",
                        "edificio": editor.nome_edificio,
                        "pavimento": pav,
                    }
                    if tipo in ["vigas", "todos"]:
                        resultado["vigas"] = editor.listar_vigas(pav)
                    if tipo in ["lajes", "todos"]:
                        resultado["lajes"] = editor.listar_lajes(pav)
                    if tipo in ["pilares", "todos"]:
                        resultado["pilares"] = editor.listar_pilares(pav)
                    if tipo in ["cargas", "todos"]:
                        resultado["cargas"] = editor.listar_cargas(pav)
                    return resultado

            elif nome_funcao == "editar_viga_modelo":
                pav = argumentos.get("pavimento", "")
                viga = argumentos.get("identificador_viga", "")
                b = argumentos.get("b_cm")
                h = argumentos.get("h_cm")
                desn = argumentos.get("desnivel_cm")
                with TQSModelEditor(edificio) as editor:
                    return editor.editar_viga(pav, viga, b_cm=b, h_cm=h, desnivel_cm=desn)

            elif nome_funcao == "editar_laje_modelo":
                pav = argumentos.get("pavimento", "")
                laje = argumentos.get("identificador_laje", "")
                esp = argumentos.get("espessura_cm")
                desn = argumentos.get("desnivel_cm")
                c_perm = argumentos.get("carga_permanente_tf_m2")
                c_acid = argumentos.get("carga_acidental_tf_m2")
                with TQSModelEditor(edificio) as editor:
                    return editor.editar_laje(
                        pav, laje,
                        espessura_cm=esp,
                        desnivel_cm=desn,
                        carga_permanente_tf_m2=c_perm,
                        carga_acidental_tf_m2=c_acid
                    )

            elif nome_funcao == "editar_pilar_modelo":
                pav = argumentos.get("pavimento", "")
                pilar = argumentos.get("identificador_pilar", "")
                b = argumentos.get("b_cm")
                h = argumentos.get("h_cm")
                with TQSModelEditor(edificio) as editor:
                    return editor.editar_pilar(pav, pilar, b_cm=b, h_cm=h)

            elif nome_funcao == "adicionar_carga_modelo":
                pav = argumentos.get("pavimento", "")
                tipo_carga = argumentos.get("tipo", "area").lower()
                c_perm = argumentos.get("carga_permanente", 0.0)
                c_acid = argumentos.get("carga_acidental", 0.0)
                coords = argumentos.get("coordenadas", [])
                with TQSModelEditor(edificio) as editor:
                    if tipo_carga == "linear":
                        if len(coords) >= 2:
                            x1, y1 = coords[0]
                            x2, y2 = coords[1]
                        else:
                            x1 = argumentos.get("x1", 0.0)
                            y1 = argumentos.get("y1", 0.0)
                            x2 = argumentos.get("x2", 10.0)
                            y2 = argumentos.get("y2", 10.0)
                        return editor.adicionar_carga_linear(pav, x1, y1, x2, y2, c_perm, c_acid)
                    else:
                        pts = [(pt[0], pt[1]) for pt in coords]
                        return editor.adicionar_carga_distribuida(pav, pts, c_perm, c_acid)

            return {"erro": f"Ferramenta '{nome_funcao}' não encontrada no registro."}

        except Exception as e:
            return {
                "status": "erro",
                "mensagem": f"Erro ao executar '{nome_funcao}': {str(e)}",
            }
