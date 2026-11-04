import json
import re
from typing import Dict, Any, List, Optional
from src.agent.tools import ToolsRegistry

SYSTEM_PROMPT_AUTQS = """
Você é o AUTQS Agent, um assistente inteligente e autônomo especialista em engenharia de estruturas de concreto armado e no software TQS V25 (TQS Python).

Suas diretrizes fundamentais:
1. RIGOR DE ENGENHARIA: Nunca invente ou alucine valores de cargas, coordenadas ou armaduras. Todos os dados numéricos devem vir exclusivamente de ferramentas (Tools) do TQS.
2. NORMAS TÉCNICAS: Suas análises devem respeitar rigorosamente a NBR 6118 (estruturas de concreto) e NBR 6122 (fundações).
3. MODULARIDADE E OPERAÇÃO: Você utiliza ferramentas especializadas para consultar e editar elementos do Modelador Estrutural (Vigas, Lajes, Pilares e Cargas), além de emitir pranchas completas e gabaritos de locação no TQS.
4. COMUNICAÇÃO: Seja objetivo, técnico e claro, utilizando a terminologia consagrada da engenharia estrutural brasileira (Nk, ELS, ELU, Ponto Fixo, Baricentro, Baldrame).
"""

class AutqsAgentOrchestrator:
    """
    Orquestrador do Agente de IA para interação com o TQS.
    Interpreta intenções, despacha tools e valida resultados.
    """

    def __init__(self):
        self.registry = ToolsRegistry()
        self.historico = []

    def obter_prompt_sistema(self) -> str:
        return SYSTEM_PROMPT_AUTQS

    def listar_ferramentas(self) -> List[Dict[str, Any]]:
        return self.registry.listar_ferramentas_para_llm()

    def processar_comando_local(self, comando: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executa diretamente uma intenção mapeada ou despacha a tool adequada
        com extração inteligente de parâmetros em linguagem natural.
        """
        params = dict(params or {})
        from src.tqs_adapter.building_reader import TQSBuildingReader

        from src.tqs_adapter.model_editor import normalizar_texto

        cmd_lower = comando.lower()
        cmd_norm = normalizar_texto(comando)

        # 1. Comando de listagem de edifícios
        if any(k in cmd_norm for k in ["LIST", "QUAI", "MOSTR", "EXIB"]) and any(k in cmd_norm for k in ["EDIF", "PROJET", "OBRA"]) and not any(k in cmd_norm for k in ["PAVIMENT", "PISO", "VIGA", "LAJE", "PILAR", "CARGA"]):
            return {
                "status": "sucesso",
                "tipo": "listagem_edificios",
                "edificios": TQSBuildingReader.listar_edificios_disponiveis(),
            }

        # 2. Extração automática do edifício se não especificado explicitamente
        if "edificio_nome" not in params:
            num_match = re.search(r'(?<![\d.])(0\d{2}|\d{3,4})(?![\d.])', comando)
            if num_match:
                params["edificio_nome"] = num_match.group(1)
            else:
                eds = TQSBuildingReader.listar_edificios_disponiveis()
                for ed in eds:
                    PALAVRAS_RESERVADAS_EDIFICIO = {"pilar", "pilares", "viga", "vigas", "laje", "lajes", "pavimento", "pavimentos", "piso", "pisos", "edificio", "edificios", "modelo", "modelos", "carga", "cargas", "planta", "plantas", "forma", "formas", "projeto", "projetos", "obra", "obras", "modificacao", "modificacoes", "alteracao", "alteracoes", "terreo"}
                    tokens = [w for w in re.split(r'[\s\-_[\]]+', ed["nome"].lower()) if len(w) > 3 and w not in PALAVRAS_RESERVADAS_EDIFICIO]
                    if any(t in cmd_lower for t in tokens):
                        params["edificio_nome"] = ed["nome"]
                        break

        # Fallback de edifício
        if not params.get("edificio_nome"):
            params["edificio_nome"] = "054"

        # 3. Processamento Estrutural do Edifício (Pórtico Espacial ou Global)
        # Ex: "processe o edifício 051", "calcular pórtico espacial", "rodar processamento global"
        if not any(k in cmd_norm for k in ["MEMORIAL", "RELATORI", "JUSTIFICATIV"]) and any(k in cmd_norm for k in ["PROCESS", "CALCUL", "ROD", "EXECUT", "PORTIC", "RECALCUL"]) and any(k in cmd_norm for k in ["EDIFIC", "OBRA", "PROJET", "PORTIC", "ESTRUTUR", "MODEL"]):
            if "global" in cmd_lower or "completo" in cmd_lower or "armadur" in cmd_lower:
                params["tipo_processamento"] = "global"
            else:
                params["tipo_processamento"] = "portico_cargas"
            return self.registry.executar_ferramenta("processar_edificio", params)

        # 4. Listagem de pavimentos do modelador
        if any(k in cmd_norm for k in ["PAVIMENT", "PISO", "PLANTA", "NIVEL", "NIVEIS"]) and any(k in cmd_norm for k in ["LIST", "QUAI", "MOSTR", "VER", "EXIB", "QUANT"]):
            if not any(k in cmd_norm for k in ["VIGA", "LAJE", "PILAR"]):
                return self.registry.executar_ferramenta("listar_pavimentos_modelo", params)

        # 4. Edição de Elementos no Modelador (Vigas, Lajes, Pilares)
        mut = self.extrair_intencao_mutacao(comando, params)
        if mut:
            return self.registry.executar_ferramenta(mut["funcao"], mut["parametros"])

        # 6. Listagem de elementos de um pavimento (vigas, lajes, pilares)
        if any(k in cmd_norm for k in ["LIST", "QUAI", "MOSTR", "VER", "EXIB"]) and any(k in cmd_norm for k in ["VIGA", "LAJE", "PILAR", "CARGA"]):
            if "pavimento" not in params:
                pav_match = re.search(r'(?:no|do|pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                params["pavimento"] = pav_match.group(1) if pav_match else "terreo"

            if "viga" in cmd_lower:
                params["tipo_elemento"] = "vigas"
            elif "laje" in cmd_lower:
                params["tipo_elemento"] = "lajes"
            elif "pilar" in cmd_lower:
                params["tipo_elemento"] = "pilares"
            elif "carga" in cmd_lower:
                params["tipo_elemento"] = "cargas"
            else:
                params["tipo_elemento"] = "todos"

        # 6.5. Análise e Auditoria Estrutural de Vigas (Esforços, Dimensionamento e Bielas)
        if any(k in cmd_norm for k in ["ANALIS", "VERIFIC", "AUDIT", "DIMENSION", "ESFORC", "BIELA", "CORTANT"]) and any(k in cmd_norm for k in ["VIGA"]):
            if "pavimento" not in params:
                pav_match = re.search(r'(?:no|do|pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                if pav_match:
                    params["pavimento"] = pav_match.group(1)
            v_match = re.search(r'\b[vV](\d+)\b', comando)
            if v_match:
                params["viga"] = f"V{v_match.group(1)}"
            params["formato"] = "resumo"
            return self.registry.executar_ferramenta("analisar_vigas_pavimento", params)

        # 6.8. Comparação de Geometrias e Plantas de Formas (Diff / O que alterou no software)
        if any(k in cmd_norm for k in ["COMPAR", "DIFF", "ALTERO", "MUDO", "DIFERENC", "SOBREPOSIC", "REVISA"]) and any(k in cmd_norm for k in ["GEOMETR", "FORMA", "PLANTA", "PROJET", "MODEL", "ARQUITETUR", "DESENH"]):
            params["edificio_base"] = params.get("edificio_nome", "054")
            if "pavimento" not in params and "pavimento_base" not in params:
                pav_match = re.search(r'(?:no|do|pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                params["pavimento_base"] = pav_match.group(1) if pav_match else "terreo"
            else:
                params["pavimento_base"] = params.get("pavimento", params.get("pavimento_base", "terreo"))
            params["formato"] = "resumo"
            return self.registry.executar_ferramenta("comparar_geometrias_formas", params)

        # 7. Verificação de Consistência da Planta de Formas
        if any(k in cmd_norm for k in ["CONSIST", "VERIFIC"]) and any(k in cmd_norm for k in ["PLANTA", "FORMA", "MODEL", "APOIO", "ESTRUTUR"]):
            if "pavimento" not in params:
                pav_match = re.search(r'(?:no|do|pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                if pav_match:
                    params["pavimento"] = pav_match.group(1)
            params["formato"] = "resumo"
            return self.registry.executar_ferramenta("verificar_consistencia_planta", params)

        # 6.9. Estabilidade Global e ELS (GamaZ, FAVt, Alfa e Deslocamentos de Vento)
        if any(k in cmd_norm for k in ["ESTABILID", "GAMAZ", "GAMA_Z", "ALFA", "DRIFT"]) or (
            any(k in cmd_norm for k in ["DESLOCAMENT", "VENT"]) and any(k in cmd_norm for k in ["TOPO", "INTERPISO", "ELS", "GLOBAL"])
        ):
            params["formato"] = "resumo"
            return self.registry.executar_ferramenta("auditar_estabilidade_global", params)

        # 6.10. Auditoria de Lajes, Grelha e Flechas
        if any(k in cmd_norm for k in ["LAJE", "GRELH", "FLECH", "PUNCA"]) and any(k in cmd_norm for k in ["AUDIT", "VERIFIC", "ANALIS", "ESBELTEZ", "MODEL"]):
            if "pavimento" not in params:
                pav_match = re.search(r'(?:no|do|pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                if pav_match:
                    params["pavimento"] = pav_match.group(1)
            params["formato"] = "resumo"
            return self.registry.executar_ferramenta("auditar_lajes_edificio", params)

        # 6.11. Quantitativo Global de Materiais e Índices de Consumo
        if any(k in cmd_norm for k in ["QUANTITATIV", "CONSUM", "MATERIA"]) or (
            any(k in cmd_norm for k in ["VOLUME", "TAXA"]) and any(k in cmd_norm for k in ["CONCRET", "FORMA", "ACO", "CARBON"])
        ):
            params["formato"] = "resumo"
            return self.registry.executar_ferramenta("extrair_quantitativo_materiais", params)

        # 6.12. Memorial Descritivo e de Cálculo Estrutural
        if any(k in cmd_norm for k in ["MEMORIAL", "JUSTIFICATIV"]) or (
            any(k in cmd_norm for k in ["RELATORI", "DOCUMENT"]) and any(k in cmd_norm for k in ["EXECUTIV", "CALCUL", "OBRA", "PROJET"])
        ):
            return self.registry.executar_ferramenta("gerar_memorial_descritivo", params)

        # 6.13. Limpeza e Padronização de Arquitetura CAD (Geo_*.DWG)
        if any(k in cmd_norm for k in ["LIMPEZA", "PADRONIZ", "HIGIENIZ"]) and any(k in cmd_norm for k in ["ARQUITETUR", "DWG", "DXF", "GEO_"]):
            if "caminho_arquivo" not in params:
                # busca caminho de arquivo no comando
                m_arq = re.search(r'["\']?([a-zA-Z0-9_\-/\\]+\.(?:dwg|dxf))["\']?', comando, re.IGNORECASE)
                if m_arq:
                    params["caminho_arquivo"] = m_arq.group(1)
            if "caminho_arquivo" in params:
                return self.registry.executar_ferramenta("padronizar_arquitetura_tqs", params)

        # 8. Geração de Planta de Formas de Alvenaria Estrutural (1ª Fiada)
        if any(k in cmd_norm for k in ["FORMA", "ALVENAR", "FIADA", "DESFIAD", "PRE_FOR", "MODULAC"]):
            if "pavimento" not in params:
                pav_match = re.search(r'(?:pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                params["pavimento"] = pav_match.group(1).upper() if pav_match else "TIPO A"
            return self.registry.executar_ferramenta("gerar_planta_formas_alvenaria", params)

        # 8. Geração de Planta de Cargas / Gabarito
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
            return self.registry.executar_ferramenta("gerar_planta_de_cargas", params)

        return {
            "status": "info",
            "mensagem": f"Comando '{comando}' registrado. Consultando catálogo de ferramentas..."
        }

    def extrair_intencao_mutacao(
        self, comando: str, params_iniciais: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analisa um comando de usuário e, se for uma solicitação de modificação
        geométrica ou estrutural no modelo (viga, laje, pilar), extrai os parâmetros
        sem executar a alteração diretamente.
        """
        from src.tqs_adapter.model_editor import normalizar_texto
        cmd_norm = normalizar_texto(comando)
        cmd_lower = comando.lower()
        params = dict(params_iniciais or {})

        eh_mutacao = any(k in cmd_norm for k in ["MUD", "ALTER", "EDIT", "DEFIN", "TROC", "APLIC", "ADIC"])
        if not eh_mutacao:
            return None

        # Viga
        if any(k in cmd_norm for k in ["VIGA"]):
            v_match = re.search(r'\b[vV](\d+)\b', comando)
            sec_match = re.search(r'(\d+)\s*[xX]\s*(\d+)', comando)
            b_match = re.search(r'\bb\s*[:=]\s*(\d+)', cmd_lower)
            h_match = re.search(r'\bh\s*[:=]\s*(\d+)', cmd_lower)

            if v_match:
                params["identificador_viga"] = f"V{v_match.group(1)}"
            if sec_match:
                params["b_cm"] = float(sec_match.group(1))
                params["h_cm"] = float(sec_match.group(2))
            else:
                if b_match:
                    params["b_cm"] = float(b_match.group(1))
                if h_match:
                    params["h_cm"] = float(h_match.group(1))

            if "pavimento" not in params:
                pav_match = re.search(r'(?:no|do|pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                params["pavimento"] = pav_match.group(1) if pav_match else "terreo"

            return {
                "tipo_elemento": "viga",
                "funcao": "editar_viga_modelo",
                "parametros": params,
            }

        # Laje
        if any(k in cmd_norm for k in ["LAJE"]):
            l_match = re.search(r'\b[lL](\d+)\b', comando)
            if l_match:
                params["identificador_laje"] = f"L{l_match.group(1)}"

            esp_match = re.search(r'(?:espessura|h|esp)\s*(?:=|de|para)?\s*(\d+(?:[.,]\d+)?)', cmd_lower)
            if esp_match:
                params["espessura_cm"] = float(esp_match.group(1).replace(",", "."))

            c_acid = re.search(r'(?:acidental|sobrecarga|acid|q)\s*(?:=|de|para)?\s*(\d+(?:[.,]\d+)?)', cmd_lower)
            if c_acid:
                params["carga_acidental_tf_m2"] = float(c_acid.group(1).replace(",", "."))

            c_perm = re.search(r'(?:permanente|perm|g)\s*(?:=|de|para)?\s*(\d+(?:[.,]\d+)?)', cmd_lower)
            if c_perm:
                params["carga_permanente_tf_m2"] = float(c_perm.group(1).replace(",", "."))

            if "pavimento" not in params:
                pav_match = re.search(r'(?:no|do|pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                params["pavimento"] = pav_match.group(1) if pav_match else "2"

            return {
                "tipo_elemento": "laje",
                "funcao": "editar_laje_modelo",
                "parametros": params,
            }

        # Pilar
        if any(k in cmd_norm for k in ["PILAR"]):
            p_match = re.search(r'\b[pP](\d+)\b', comando)
            sec_match = re.search(r'(\d+)\s*[xX]\s*(\d+)', comando)
            b_match = re.search(r'\bb\s*[:=]\s*(\d+)', cmd_lower)
            h_match = re.search(r'\bh\s*[:=]\s*(\d+)', cmd_lower)

            if p_match:
                params["identificador_pilar"] = f"P{p_match.group(1)}"
            if sec_match:
                params["b_cm"] = float(sec_match.group(1))
                params["h_cm"] = float(sec_match.group(2))
            else:
                if b_match:
                    params["b_cm"] = float(b_match.group(1))
                if h_match:
                    params["h_cm"] = float(h_match.group(1))

            if "pavimento" not in params:
                pav_match = re.search(r'(?:no|do|pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', cmd_lower)
                params["pavimento"] = pav_match.group(1) if pav_match else "terreo"

            return {
                "tipo_elemento": "pilar",
                "funcao": "editar_pilar_modelo",
                "parametros": params,
            }

        return None
