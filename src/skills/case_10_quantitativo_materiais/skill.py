import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.skills.case_10_quantitativo_materiais.material_quantifier import (
    TQSMaterialQuantifier,
    EdificioMateriaisResultado,
)


class QuantitativoMateriaisSkill(BaseSkill):
    """
    Case 10: Extração de quantitativos globais de materiais, índices de consumo
    (em, taxa de formas, taxa de aço) e pegada de carbono incorporado no CAD/TQS V25.

    Processa diretamente os relatórios de resumo estrutural do edifício:
      - RESEST2.TXT: Matriz de materiais por elemento (pilares, vigas, lajes).
      - RESEST3.TXT: Resumo de concreto, formas, aço e área estruturada por piso.
      - RESEST4.TXT: Índices médios consolidados de consumo.
      - RESEST8.TXT: Pegada de carbono incorporado (kgCO2) na estrutura.
    """

    @property
    def nome(self) -> str:
        return "extrair_quantitativo_materiais"

    @property
    def descricao(self) -> str:
        return (
            "Extrai o quantitativo global de materiais do edifício no TQS V25 (volume de concreto m³, "
            "área de formas m², peso de aço kg, área estruturada m² e emissões de carbono kgCO2). "
            "Calcula os índices de eficiência (espessura média em, taxa de formas m²/m² e consumo de aço kg/m³)."
        )

    def executar(
        self,
        edificio_nome: str,
        formato: str = "resumo",
        pasta_raiz_tqs: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa o levantamento de quantitativos e índices de consumo.
        :param edificio_nome: Nome ou código do edifício (ex: '054' ou 'Zuckhan - Soledade').
        :param formato: 'resumo' (markdown executivo), 'json' ou 'completo'.
        :param pasta_raiz_tqs: Opcional diretório raiz do TQS (padrão C:\\TQS).
        """
        try:
            quantifier = TQSMaterialQuantifier(edificio_nome, pasta_raiz_tqs=pasta_raiz_tqs)
            res = quantifier.quantificar()

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
                "area_total_m2": round(res.area_total_m2, 2),
                "volume_concreto_total_m3": round(res.volume_concreto_total_m3, 2),
                "area_formas_total_m2": round(res.area_formas_total_m2, 2),
                "peso_aco_total_kg": round(res.peso_aco_total_kg, 2),
                "carbono_total_kgco2": round(res.carbono_total_kgco2, 2),
                "espessura_media_m": round(res.espessura_media_m, 3),
                "taxa_formas_m2_m2": round(res.taxa_formas_m2_m2, 2),
                "dados": res_dict,
            }

        except Exception as e:
            return {
                "status": "erro",
                "sucesso": False,
                "mensagem": f"Falha ao extrair quantitativos do edifício '{edificio_nome}': {str(e)}"
            }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """Valida se o resultado contém os quantitativos e índices calculados."""
        if not isinstance(resultado, dict):
            return False
        if resultado.get("status") != "sucesso":
            return False
        return "volume_concreto_total_m3" in resultado and "area_total_m2" in resultado
