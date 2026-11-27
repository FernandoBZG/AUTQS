import os
from typing import Any, Dict, Optional, List
from src.skills.base_skill import BaseSkill
from src.skills.case_05_consistencia_planta.consistency_analyzer import (
    TQSConsistencyAnalyzer,
    ConsistenciaPavimentoResultado,
)

class ConsistenciaPlantaSkill(BaseSkill):
    """
    Case 5: Habilidade responsável pela verificação, auditoria e diagnóstico
    de consistência geométrica e estrutural de plantas de formas no CAD/TQS V25.
    
    Dispara a extração gráfica de formas (FXEXTME/FEXTDWG) e o processamento de consistência
    (FXFORMAS) do TQS, auditando:
      - Vigas sem apoio / apoios nulos (iniciais e finais)
      - Eixos de vigas que não caem sobre a seção dos pilares
      - Interferências entre apoios adjacentes
      - Barras em balanço imprevistas
      - Incompatibilidades de discretização de lajes
      - Alertas de estabilidade lateral de vigas (NBR 6118 item 15.10)
    """

    @property
    def nome(self) -> str:
        return "verificar_consistencia_planta"

    @property
    def descricao(self) -> str:
        return (
            "Verifica e audita a consistência de uma planta de formas através do TQS V25. "
            "Dispara a extração de formas e processamento do pavimento (FXEXTME/FXFORMAS) "
            "e analisa relatórios de modelagem (MENAVI.LST, *.LST, ERROS.DAT, ERROS.TXT). "
            "Identifica vigas sem apoio, apoios nulos, nós fora da seção do pilar, "
            "interferências entre apoios, balanços indesejados e fornece sugestões de correção."
        )

    def executar(
        self,
        edificio_nome: str,
        pavimento: Optional[str] = None,
        executar_tqs: bool = False,
        desenhar_formas: bool = True,
        formato: str = "resumo",
        timeout_segundos: int = 240,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa a verificação de consistência da planta de formas.
        :param edificio_nome: Nome ou código do edifício TQS (ex: '054').
        :param pavimento: Pavimento específico (ex: 'terreo', '2 pavimento') ou None para todos.
        :param executar_tqs: Se True, dispara 'PROC FORMAS 2 1' no motor do TQS (exige aprovação do
            usuário quando chamado pelo ToolsRegistry). Padrão False: analisa relatórios já gerados.
        :param desenhar_formas: Se True, gera desenho FOR00xx.DWG durante a consistência.
        :param formato: 'resumo' (compacto para chat/LLM), 'terminal' (tabela) ou 'json'.
        :param timeout_segundos: Timeout para o lote do TQS.
        """
        analyzer = TQSConsistencyAnalyzer(edificio_nome)
        resultados_pav = analyzer.analisar(
            pavimento=pavimento,
            executar_tqs=executar_tqs,
            desenhar_formas=desenhar_formas,
            timeout_segundos=timeout_segundos
        )

        if not resultados_pav:
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": edificio_nome,
                "erro": f"Nenhum pavimento estrutural encontrado para '{pavimento or 'todos'}' no edifício '{edificio_nome}'."
            }

        # Status consolidado do edifício / pavimentos
        tem_inconsistente = any(r.status == "inconsistente" for r in resultados_pav)
        tem_avisos = any(r.status == "com_avisos" for r in resultados_pav)

        if tem_inconsistente:
            status_geral = "inconsistente"
        elif tem_avisos:
            status_geral = "com_avisos"
        else:
            status_geral = "consistente"

        total_criticos = sum(r.total_erros_criticos for r in resultados_pav)
        total_importantes = sum(r.total_avisos_importantes for r in resultados_pav)
        total_normativos = sum(r.total_avisos_normativos for r in resultados_pav)
        total_informativos = sum(r.total_informativos for r in resultados_pav)

        if formato == "terminal":
            texto_saida = "\n".join(r.para_tabela_terminal() for r in resultados_pav)
        else:
            texto_saida = "\n\n".join(r.para_resumo_executivo() for r in resultados_pav)

        resultado = {
            "status": status_geral,
            "sucesso": (status_geral != "inconsistente"),
            "edificio": analyzer.nome_edificio,
            "caminho_edificio": analyzer.caminho_edificio,
            "pavimentos_analisados": [r.pavimento for r in resultados_pav],
            "resumo_executivo": texto_saida,
            "metricas": {
                "total_pavimentos": len(resultados_pav),
                "erros_criticos": total_criticos,
                "avisos_importantes": total_importantes,
                "avisos_normativos": total_normativos,
                "informativos": total_informativos,
            },
            "dados_pavimentos": [r.para_dict() for r in resultados_pav] if formato == "json" else None
        }

        return resultado

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """
        Guardrail de engenharia:
        A planta é considerada válida apenas se não possuir erros críticos bloqueantes
        (ex: vigas sem apoio ou erro de extração gráfica).
        """
        if not resultado or resultado.get("status") == "erro":
            return False
        if resultado.get("status") == "inconsistente":
            return False
        metricas = resultado.get("metricas", {})
        if metricas.get("erros_criticos", 0) > 0:
            return False
        return True
