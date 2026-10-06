import os
from typing import Any, Dict, Optional, List
from src.skills.base_skill import BaseSkill
from src.skills.case_06_analise_vigas.beam_analyzer import (
    TQSBeamAnalyzer,
    AuditoriaVigasResultado,
)


class AnaliseVigasSkill(BaseSkill):
    """
    Case 6: Habilidade de auditoria, análise e diagnóstico estrutural avançado
    de vigas de concreto armado no CAD/TQS V25.

    Processa diretamente as listagens de cálculo e dimensionamento do TQS:
      - RELGER.LST: Esforços envolventes de flexão (M-, M+), armaduras calculadas (As), seções e vãos.
      - ESTRIB.LST: Cisalhamento e verificação de bielas comprimidas (Vsd > VRd2), estribos e vãos espúrios.
      - RESESTERR.LST: Erros de detalhamento de armaduras e bitolas sentinelas (50mm).
      - ORDCON.LST: Consistência geométrica e carregamento de vigas.

    Gera diagnóstico automatizado de patologias de bielas e propostas de redimensionamento
    com folga de segurança baseada na NBR 6118.
    """

    @property
    def nome(self) -> str:
        return "analisar_vigas_pavimento"

    @property
    def descricao(self) -> str:
        return (
            "Audita, analisa e diagnostica os esforços envolventes (M-, M+, Vsd), "
            "dimensionamento à flexão e compressão diagonal de bielas (Vsd vs VRd2) "
            "das vigas do edifício no CAD/TQS V25. Identifica rupturas de biela, "
            "bitolas sentinelas de 50mm, vãos curtos espúrios (<60cm), armaduras pesadas "
            "e propõe redimensionamento de seções de concreto."
        )

    def executar(
        self,
        edificio_nome: str,
        pavimento: Optional[str] = None,
        viga: Optional[str] = None,
        formato: str = "resumo",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa a auditoria das vigas do edifício/pavimento.
        :param edificio_nome: Código ou nome do edifício TQS (ex: '054').
        :param pavimento: Pavimento específico (ex: '2', 'terreo') ou None para todos.
        :param viga: Opcional: filtrar para uma viga específica (ex: 'V21' ou '21').
        :param formato: 'resumo' (padrão conciso para IA), 'terminal' (tabela) ou 'json'.
        """
        analyzer = TQSBeamAnalyzer(edificio_nome)
        resultados_pav = analyzer.analisar(pavimento=pavimento, filtro_viga=viga)

        if not resultados_pav:
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": edificio_nome,
                "erro": f"Nenhuma pasta de vigas calculada encontrada para '{pavimento or 'todos'}' no edifício '{edificio_nome}'."
            }

        # Status consolidado
        tem_critico = any(r.total_criticas > 0 for r in resultados_pav)
        tem_alerta = any(r.total_alertas > 0 for r in resultados_pav)

        if tem_critico:
            status_geral = "CRITICO"
        elif tem_alerta:
            status_geral = "ALERTA"
        else:
            status_geral = "OK"

        total_vigas = sum(r.total_vigas for r in resultados_pav)
        total_criticas = sum(r.total_criticas for r in resultados_pav)
        total_alertas = sum(r.total_alertas for r in resultados_pav)
        total_ok = sum(r.total_ok for r in resultados_pav)

        if formato == "terminal":
            texto_saida = "\n".join(r.para_tabela_terminal(filtro_viga=viga) for r in resultados_pav)
        else:
            texto_saida = "\n\n".join(r.para_resumo_executivo() for r in resultados_pav)

        return {
            "status": status_geral.lower(),
            "sucesso": True,
            "edificio": analyzer.nome_edificio,
            "caminho_edificio": analyzer.caminho_edificio,
            "pavimentos_analisados": [r.pavimento for r in resultados_pav],
            "resumo_executivo": texto_saida,
            "dados_completos": [r.para_dict() for r in resultados_pav],
            "metricas": {
                "total_vigas": total_vigas,
                "vigas_criticas": total_criticas,
                "vigas_com_alertas": total_alertas,
                "vigas_regulares": total_ok,
            }
        }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """
        Guardrail de engenharia:
        O dimensionamento das vigas é considerado estruturalmente válido
        se não possuir vigas com ruptura de biela comprimida (Vsd > VRd2) ou
        erros de detalhamento com bitolas sentinelas (50mm).
        """
        if not resultado or resultado.get("status") == "erro":
            return False
        if resultado.get("status") == "critico":
            return False
        metricas = resultado.get("metricas", {})
        if metricas.get("vigas_criticas", 0) > 0:
            return False
        return True
