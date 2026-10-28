import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.skills.case_09_auditoria_lajes.slab_analyzer import (
    TQSSlabAnalyzer,
    EdificioLajesResultado,
)


class AuditoriaLajesSkill(BaseSkill):
    """
    Case 09: Auditoria técnica, quantitativo e verificação de consistência
    de lajes, grelhas e flechas (ELS) no CAD/TQS V25 conforme a NBR 6118:2023.

    Processa diretamente os relatórios de pavimentos e grelha:
      - <PAV>.LST: Quantitativo por laje (área, fôrmas, volume), espessura média.
      - GREEXT.LST: Avisos de barras hipostáticas, nós e balanços.
      - GREFOR.LST: Parâmetros de fck, inércias e apoios elásticos de pilares.
      - MENAVI.LST: Inconsistências de bordo livre em concavidade e nivelamento com vigas.
    """

    @property
    def nome(self) -> str:
        return "auditar_lajes_edificio"

    @property
    def descricao(self) -> str:
        return (
            "Audita as lajes, modelos de grelha e flechas do edifício no TQS V25. "
            "Extrai quantitativos detalhados (área m², volume m³, formas m²), espessuras, "
            "detecta balanços não travados, bordos livres em concavidade, desníveis incoerentes "
            "e alerta para riscos de flecha excessiva conforme a NBR 6118."
        )

    def executar(
        self,
        edificio_nome: str,
        pavimento: Optional[str] = None,
        formato: str = "resumo",
        pasta_raiz_tqs: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa a auditoria de lajes do edifício ou pavimento.
        :param edificio_nome: Nome ou código do edifício (ex: '054' ou 'Zuckhan - Soledade').
        :param pavimento: Opcional nome/filtro do pavimento (ex: '2', 'tipo', 'terreo').
        :param formato: 'resumo' (markdown executivo), 'json' ou 'completo'.
        :param pasta_raiz_tqs: Opcional diretório raiz do TQS (padrão C:\\TQS).
        """
        try:
            analyzer = TQSSlabAnalyzer(edificio_nome, pasta_raiz_tqs=pasta_raiz_tqs)
            res = analyzer.analisar(pavimento_filtro=pavimento)

            if not res.pavimentos:
                return {
                    "status": "erro",
                    "sucesso": False,
                    "mensagem": f"Nenhum dado de laje ou grelha encontrado para o edifício '{edificio_nome}'."
                }

            res_dict = res.para_dict()
            resumo_md = res.para_resumo_executivo()

            if formato == "json":
                return {
                    "status": "sucesso",
                    "sucesso": True,
                    "dados": res_dict,
                }

            return {
                "status": "sucesso",
                "sucesso": True,
                "edificio": res.edificio_nome,
                "resumo_executivo": resumo_md,
                "total_lajes": res.total_lajes_edificio,
                "area_total_m2": round(res.area_total_edificio_m2, 2),
                "volume_total_m3": round(res.volume_total_edificio_m3, 2),
                "alertas_totais": res.alertas_totais_contagem,
                "dados": res_dict,
            }

        except Exception as e:
            return {
                "status": "erro",
                "sucesso": False,
                "mensagem": f"Falha na auditoria de lajes do edifício '{edificio_nome}': {str(e)}"
            }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """Valida se a auditoria retornou com sucesso e com métricas de lajes."""
        if not isinstance(resultado, dict):
            return False
        if resultado.get("status") != "sucesso":
            return False
        return "total_lajes" in resultado and "area_total_m2" in resultado
