import json
from typing import Dict, Any, List
from src.agent.tools import ToolsRegistry

SYSTEM_PROMPT_AUTQS = """
Você é o AUTQS Agent, um assistente inteligente e autônomo especialista em engenharia de estruturas de concreto armado e no software TQS V25 (TQS Python).

Suas diretrizes fundamentais:
1. RIGOR DE ENGENHARIA: Nunca invente ou alucine valores de cargas, coordenadas ou armaduras. Todos os dados numéricos devem vir exclusivamente de ferramentas (Tools) do TQS.
2. NORMAS TÉCNICAS: Suas análises devem respeitar rigorosamente a NBR 6118 (estruturas de concreto) e NBR 6122 (fundações).
3. MODULARIDADE: Você utiliza o sistema de Skills para acionar comandos no TQS (Planta de cargas, auditoria, alterações de modelo e emissão de pranchas).
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
        import re
        from src.tqs_adapter.building_reader import TQSBuildingReader

        params = params or {}
        cmd_lower = comando.lower()

        # 1. Comando de listagem de edifícios
        if any(k in cmd_lower for k in ["list", "quais"]) and any(k in cmd_lower for k in ["edif", "projet", "obra"]):
            return {
                "status": "sucesso",
                "tipo": "listagem_edificios",
                "edificios": TQSBuildingReader.listar_edificios_disponiveis(),
            }

        # 2. Extração automática do edifício se não especificado explicitamente
        if "edificio_nome" not in params:
            # Procura por código numérico de 2 a 4 dígitos (ex: "054", "049")
            num_match = re.search(r'\b(\d{2,4})\b', comando)
            if num_match:
                params["edificio_nome"] = num_match.group(1)
            else:
                # Procura por termos-chave dos edifícios do sistema
                eds = TQSBuildingReader.listar_edificios_disponiveis()
                for ed in eds:
                    tokens = [w for w in re.split(r'[\s\-_\[\]]+', ed["nome"].lower()) if len(w) > 3]
                    if any(t in cmd_lower for t in tokens):
                        params["edificio_nome"] = ed["nome"]
                        break

        # 3. Geração de Planta de Cargas
        if "planta" in cmd_lower or "carga" in cmd_lower:
            if not params.get("edificio_nome"):
                params["edificio_nome"] = "054" # fallback
            return self.registry.executar_ferramenta("gerar_planta_de_cargas", params)

        return {
            "status": "info",
            "mensagem": f"Comando '{comando}' registrado. Consultando catálogo de ferramentas..."
        }
