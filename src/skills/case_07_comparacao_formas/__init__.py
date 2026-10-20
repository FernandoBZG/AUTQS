"""
Case 07: Comparação de Geometrias e Plantas de Formas no TQS V25.
Permite auditar alterações entre revisões de projetos, plantas de formas e referências de geometria.
"""

from src.skills.case_07_comparacao_formas.geometry_comparator import (
    TQSGeometryComparator,
    DiferencaElemento,
    RelatorioComparacaoResultado,
)
from src.skills.case_07_comparacao_formas.skill import ComparacaoFormasSkill

__all__ = [
    "TQSGeometryComparator",
    "DiferencaElemento",
    "RelatorioComparacaoResultado",
    "ComparacaoFormasSkill",
]
