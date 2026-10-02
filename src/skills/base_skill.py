from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSkill(ABC):
    """
    Interface base para qualquer Habilidade/Caso de Uso (Skill) da plataforma AUTQS.
    Toda nova funcionalidade do sistema (ex: Planta de Cargas, Auditoria, Alteração)
    herda desta classe, garantindo modularidade e desacoplamento do agente.
    """

    @property
    @abstractmethod
    def nome(self) -> str:
        """Nome único da habilidade (ex: 'planta_de_cargas')."""
        pass

    @property
    @abstractmethod
    def descricao(self) -> str:
        """Descrição detalhada para a IA compreender quando acionar esta ferramenta."""
        pass

    @abstractmethod
    def executar(self, **kwargs) -> Dict[str, Any]:
        """
        Executa a lógica de engenharia da habilidade e retorna
        um dicionário estruturado com o resultado.
        """
        pass

    @abstractmethod
    def validar(self, resultado: Dict[str, Any]) -> bool:
        """
        Guardrail de engenharia: valida se o resultado atende às premissas normativas.
        """
        pass
