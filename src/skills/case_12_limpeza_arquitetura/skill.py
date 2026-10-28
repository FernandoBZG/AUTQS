import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.skills.case_12_limpeza_arquitetura.arch_cleaner import (
    TQSArchCleaner,
    LimpezaArquiteturaResultado,
)


class LimpezaArquiteturaSkill(BaseSkill):
    """
    Case 12: Higienização, purga de elementos pesados e padronização de arquivos
    CAD de arquitetura (DXF/DWG) para criação de bases de referência Geo_*.DWG no TQS V25.

    Processa plantas arquitetônicas brutas:
      - Purga hachuras (HATCH), cotas (DIMENSION) e textos de acabamento desnecessários.
      - Elimina blocos de mobiliário, paisagismo, vegetação, veículos e pessoas.
      - Preserva e isola alvenarias, paredes, pilares, eixos modulares e aberturas essenciais.
      - Converte escala de metros para centímetros (x100) para compatibilidade nativa com o TQS.
      - Opcionalmente centraliza a geometria no ponto de origem (0, 0).
    """

    @property
    def nome(self) -> str:
        return "padronizar_arquitetura_tqs"

    @property
    def descricao(self) -> str:
        return (
            "Limpa e padroniza arquivos CAD de arquitetura (DXF/DWG) para uso como referências externas "
            "(Geo_*.DWG) no TQS V25. Remove hachuras pesadas, cotas, mobiliário, vegetação e converte "
            "a escala de metros para centímetros com alinhamento de origem."
        )

    def executar(
        self,
        caminho_arquivo: str,
        caminho_saida: Optional[str] = None,
        fator_escala: str = "auto",
        centralizar_origem: bool = False,
        formato: str = "resumo",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa a limpeza e padronização do arquivo de arquitetura.
        :param caminho_arquivo: Arquivo CAD de arquitetura (.dxf ou .dwg).
        :param caminho_saida: Opcional arquivo DXF de saída (padrão Geo_<nome>.dxf).
        :param fator_escala: 'auto' (detecta metros vs cm), '100' ou '1'.
        :param centralizar_origem: Se True, translada a geometria para (0, 0).
        :param formato: 'resumo' (markdown executivo), 'json' ou 'completo'.
        """
        try:
            cleaner = TQSArchCleaner()
            res = cleaner.limpar_e_padronizar(
                caminho_entrada=caminho_arquivo,
                caminho_saida=caminho_saida,
                fator_escala=fator_escala,
                centralizar_origem=centralizar_origem,
            )

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
                "arquivo_gerado": res.arquivo_destino,
                "resumo_executivo": resumo_md,
                "fator_escala": res.fator_escala_aplicado,
                "entidades_mantidas": res.entidades_mantidas,
                "hachuras_removidas": res.hachuras_removidas,
                "cotas_removidas": res.cotas_removidas,
                "dados": res_dict,
            }

        except Exception as e:
            return {
                "status": "erro",
                "sucesso": False,
                "mensagem": f"Falha ao limpar e padronizar arquitetura: {str(e)}"
            }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """Valida se o arquivo gerado foi registrado com sucesso."""
        if not isinstance(resultado, dict):
            return False
        if resultado.get("status") != "sucesso":
            return False
        return "arquivo_gerado" in resultado and os.path.exists(resultado["arquivo_gerado"])
