import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.skills.case_08_estabilidade_global.stability_analyzer import (
    TQSStabilityAnalyzer,
    RelatorioEstabilidadeResultado,
)


class EstabilidadeGlobalSkill(BaseSkill):
    """
    Case 08: Habilidade de auditoria de estabilidade global e deslocamentos
    em serviço (ELS) de edifícios no CAD/TQS V25 conforme a NBR 6118:2023.

    Processa os relatórios oficiais do pórtico espacial:
      - PORALF.LST / PORGAMZ.LST: Parâmetros GamaZ (γz), FAVt, Alfa (α) e deslocamentos.
      - ELS Topo: Verificação do deslocamento limite global de topo (H/1700).
      - ELS Interpiso: Verificação de deslocamento relativo entre pisos vizinhos (Hi/850).
    """

    @property
    def nome(self) -> str:
        return "auditar_estabilidade_global"

    @property
    def descricao(self) -> str:
        return (
            "Audita a estabilidade global de 2ª ordem (GamaZ, FAVt, Alfa) e os deslocamentos "
            "horizontais em ELS (drift de topo H/1700 e interpiso Hi/850) do edifício no TQS V25 "
            "conforme a NBR 6118. Classifica a estrutura em Nós Fixos ou Móveis e emite diagnóstico."
        )

    def executar(
        self,
        edificio_nome: str,
        formato: str = "resumo",
        pasta_raiz_tqs: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa a auditoria de estabilidade global do edifício.
        :param edificio_nome: Código ou nome da pasta do edifício no TQS (ex: '054').
        :param formato: 'resumo' (markdown executivo), 'json' ou 'completo'.
        :param pasta_raiz_tqs: Opcional caminho raiz do TQS (padrão C:\\TQS).
        """
        try:
            analyzer = TQSStabilityAnalyzer(edificio_nome, pasta_raiz_tqs=pasta_raiz_tqs)
            res = analyzer.analisar()

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
                "classificacao": res.classificacao_estrutura,
                "gama_z_max": round(res.gama_z_max, 3),
                "fav_t_max": round(res.fav_t_max, 3),
                "alfa_max": round(res.alfa_max, 3),
                "drift_topo_passou": res.drift_topo_passou,
                "drift_interpiso_passou": res.drift_interpiso_passou,
                "dados": res_dict,
            }

        except Exception as e:
            return {
                "status": "erro",
                "sucesso": False,
                "mensagem": f"Falha ao auditar estabilidade global do edifício '{edificio_nome}': {str(e)}"
            }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """Valida se a resposta contém os campos normativos essenciais."""
        if not isinstance(resultado, dict):
            return False
        if resultado.get("status") != "sucesso":
            return False
        if "dados" not in resultado:
            return False
        dados = resultado["dados"]
        return "gama_z_max" in dados and "drift_topo" in dados and "drift_interpiso" in dados
