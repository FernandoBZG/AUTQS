import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.tqs_adapter.building_processor import TQSBuildingProcessor
from src.skills.case_01_planta_cargas.skill import PlantaDeCargasSkill

class ProcessamentoEdificioSkill(BaseSkill):
    """
    Case 2: Habilidade responsável pelo disparo, acompanhamento e extração
    do Processamento Global / Pórtico Espacial do edifício no TQS V25.
    """

    @property
    def nome(self) -> str:
        return "processar_edificio"

    @property
    def descricao(self) -> str:
        return (
            "Dispara o processamento estrutural em lote do edifício no TQS V25. "
            "Executa a extração de formas do modelador, análise de grelhas, montagem e "
            "cálculo da matriz do Pórtico Espacial 3D, transferência de esforços para as "
            "fundações e geração do relatório PORLID. Se solicitado, emite automaticamente "
            "a Planta de Cargas (GABARITO.DWG) com os novos esforços calculados."
        )

    def executar(
        self,
        edificio_nome: str,
        caminho_edificio: str = "",
        tipo_processamento: str = "portico_cargas",
        gerar_planta_apos_processar: bool = True,
        timeout_segundos: int = 300,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa o pipeline do Case 2:
        1. Inicializa o processador TQS para o edifício alvo.
        2. Dispara o processamento (pórtico_cargas ou global_completo).
        3. Se bem-sucedido e gerar_planta_apos_processar=True, invoca a PlantaDeCargasSkill.
        """
        alvo = caminho_edificio or edificio_nome
        try:
            processor = TQSBuildingProcessor(alvo)
        except Exception as e:
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": edificio_nome,
                "erro": f"Não foi possível inicializar o processador para '{edificio_nome}': {str(e)}",
            }

        # 1. Executa o cálculo batch no TQS
        if tipo_processamento == "global":
            res_proc = processor.processar_global_completo(timeout_segundos=timeout_segundos)
        else:
            res_proc = processor.processar_portico_e_cargas(timeout_segundos=timeout_segundos)

        resultado = {
            "status": res_proc.get("status", "sucesso"),
            "sucesso": res_proc.get("sucesso", False),
            "edificio": processor.nome_edificio,
            "caminho_edificio": processor.caminho_edificio,
            "tipo_processamento": res_proc.get("tipo_processamento"),
            "duracao_segundos": res_proc.get("duracao_segundos"),
            "tem_porlis": res_proc.get("tem_porlis", False),
            "tem_cardwg": res_proc.get("tem_cardwg", False),
            "mensagens_tqs": res_proc.get("mensagens", []),
        }

        # 2. Se o processamento concluiu com sucesso e a opção estiver ativa, emite a prancha
        if res_proc.get("sucesso") and gerar_planta_apos_processar:
            try:
                skill_planta = PlantaDeCargasSkill()
                res_planta = skill_planta.executar(
                    edificio_nome=processor.nome_edificio,
                    caminho_edificio=processor.caminho_edificio,
                    **kwargs
                )
                resultado["planta_gerada"] = {
                    "sucesso": res_planta.get("status") == "sucesso",
                    "caminho_dwg": res_planta.get("caminho_espacial"),
                    "total_pilares": res_planta.get("total_pilares_fundacao"),
                }
            except Exception as e:
                resultado["planta_gerada"] = {
                    "sucesso": False,
                    "erro": f"Erro ao gerar planta de cargas após processamento: {str(e)}"
                }

        # 3. Guardrails de engenharia
        if not self.validar(resultado):
            if resultado.get("sucesso"):
                resultado["status"] = "alerta_consistencia"

        return resultado

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """
        Guardrail de engenharia:
        - Verifica se o processamento concluiu com êxito.
        - Assegura que o pórtico espacial foi calculado e convergiu (PORLIS presente).
        """
        if not resultado.get("sucesso", False):
            return False
        if not resultado.get("tem_porlis", False):
            return False
        return True
