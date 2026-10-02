from typing import Dict, Any, List
from src.skills.case_01_planta_cargas.skill import PlantaDeCargasSkill
from src.core.models import PilarFundacao, GeometriaPilar, TipoSecao, EsforcosFundacao

class ToolsRegistry:
    """
    Registro centralizado de ferramentas (Tools / Function Calling)
    disponíveis para o Agente Autônomo AUTQS.
    """

    def __init__(self):
        self._skills = {}
        # Registra as habilidades ativas na plataforma
        self.registrar_skill(PlantaDeCargasSkill())

    def registrar_skill(self, skill):
        self._skills[skill.nome] = skill

    def listar_ferramentas_para_llm(self) -> List[Dict[str, Any]]:
        """
        Retorna as definições no formato padrão de Function Calling (OpenAI / Gemini).
        """
        catalogo = []
        for nome, skill in self._skills.items():
            catalogo.append({
                "type": "function",
                "function": {
                    "name": nome,
                    "description": skill.descricao,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edificio_nome": {
                                "type": "string",
                                "description": "Nome ou identificador do edifício TQS."
                            },
                            "pavimento_fundacao": {
                                "type": "string",
                                "description": "Nome do pavimento de fundação (ex: FUNDACAO, BALDRAME)."
                            },
                            "exportar_tabela_dwg": {
                                "type": "boolean",
                                "description": "Se verdadeiro, gera arquivo .DWG com a tabela de cargas."
                            }
                        },
                        "required": ["edificio_nome"]
                    }
                }
            })
        return catalogo

    def executar_ferramenta(self, nome_funcao: str, argumentos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma ferramenta chamada pela IA.
        """
        if nome_funcao not in self._skills:
            return {"erro": f"Ferramenta '{nome_funcao}' não encontrada no registro."}

        skill = self._skills[nome_funcao]
        return skill.executar(**argumentos)
