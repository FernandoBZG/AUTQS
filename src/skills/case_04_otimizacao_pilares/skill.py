import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.skills.case_04_otimizacao_pilares.pilar_analyzer import TQSColumnAnalyzer

class OtimizacaoPilaresSkill(BaseSkill):
    """
    Case 4: Habilidade de auditoria estrutural, diagnostico e otimizacao
    automatica de pilares do edificio TQS.
    """

    @property
    def nome(self) -> str:
        return "analisar_pilares_edificio"

    @property
    def descricao(self) -> str:
        return (
            "Audita e analisa o dimensionamento de todos os pilares do edificio TQS em milissegundos. "
            "Identifica lances nao dimensionados (erros de calculo), lances hiper-armados (rho >= 2.5%, "
            "congestionamento de armadura) e lances superdimensionados (capacidade ociosa > 70%). "
            "Fornece redimensionamento sugerido e projecao de economia de aco (kg) e concreto (m3)."
        )

    def executar(
        self,
        edificio_nome: str,
        pilar: Optional[str] = None,
        formato: str = "resumo",
        largura_fixa: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa a analise de pilares do edificio.
        :param edificio_nome: Nome ou codigo do edificio TQS (ex: '054').
        :param pilar: (Opcional) Filtrar por um pilar especifico (ex: 'P4').
        :param formato: 'resumo' (padrao compacto para LLM), 'terminal' (tabela) ou 'json'.
        :param largura_fixa: Se True, as sugestoes mantem a largura b e alteram so o comprimento h.
        """
        analyzer = TQSColumnAnalyzer(edificio_nome, largura_fixa=bool(largura_fixa))
        resumo = analyzer.analisar(pilar_filtro=pilar)

        if formato == "terminal":
            texto = resumo.para_tabela_terminal()
        else:
            texto = resumo.para_resumo_executivo()

        return {
            "status": "sucesso",
            "edificio": resumo.edificio_nome,
            "caminho": resumo.caminho_edificio,
            "resumo_executivo": texto,
            "metricas": {
                "total_pilares": resumo.total_pilares,
                "total_lances": resumo.total_lances,
                "nao_dimensionados": resumo.total_nao_dimensionados,
                "hiper_armados": resumo.total_hiper_armados,
                "superdimensionados": resumo.total_superdimensionados,
                "esbeltos": resumo.total_esbeltos,
                "taxa_media_armadura_pct": round(resumo.taxa_media_armadura, 2),
                "economia_potencial_aco_kg": round(resumo.economia_potencial_aco_kg, 1),
                "economia_potencial_concreto_m3": round(resumo.economia_potencial_concreto_m3, 2),
            },
            "sugestoes_prioritarias": resumo.sugestoes_prioritarias[:10],
            "dados_completos": resumo.para_dict() if formato == "json" else None
        }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """Valida se a analise foi executada com sucesso e com pilares encontrados."""
        if not resultado or resultado.get("status") != "sucesso":
            return False
        metricas = resultado.get("metricas", {})
        return metricas.get("total_lances", 0) > 0
