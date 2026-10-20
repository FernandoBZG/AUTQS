import os
from typing import Any, Dict, List, Optional, Union
from src.skills.base_skill import BaseSkill
from src.skills.case_07_comparacao_formas.geometry_comparator import (
    TQSGeometryComparator,
    RelatorioComparacaoResultado,
)


class ComparacaoFormasSkill(BaseSkill):
    """
    Case 07: Habilidade de Comparação de Geometrias e Auditoria de Plantas de Formas.
    Compara duas versões/revisões de pavimentos, plantas de formas ou referências de geometria
    no CAD/TQS V25 e detecta:
      - Pilares adicionados, removidos, transladados (ΔX, ΔY) ou redimensionados (Δb, Δh)
      - Vigas novas, excluídas, modificadas em seção ou rebaixo
      - Lajes com alteração de espessura, contorno ou rebaixo
      - Compara DWGs arquitetônicos (Geo_*.DWG) contra plantas de formas (FOR*.DWG)
      - Gera desenho de sobreposição gráfica (Diff DXF) com código de cores padronizado
    """

    @property
    def nome(self) -> str:
        return "comparar_geometrias_formas"

    @property
    def descricao(self) -> str:
        return (
            "Compara geometrias e plantas de formas no TQS V25 para auditar o que mudou no software. "
            "Pode comparar dois edifícios, dois pavimentos, arquiteturas Geo_*.DWG vs FOR*.DWG ou "
            "varrer todas as geometrias do edifício automaticamente. Detecta pilares com desvios "
            "de posição (ΔX, ΔY) ou de seção (Δb, Δh), vigas e lajes modificadas, e gera prancha "
            "de sobreposição gráfica com código de cores (Verde=Novo, Vermelho=Removido, Ciano=Alterado, Cinza=Inalterado)."
        )

    def executar(
        self,
        edificio_base: Optional[str] = None,
        pavimento_base: Optional[str] = None,
        edificio_comparado: Optional[str] = None,
        pavimento_comparado: Optional[str] = None,
        caminho_geo: Optional[Union[str, List[str]]] = None,
        caminho_for: Optional[str] = None,
        modo: str = "auto",
        gerar_desenho_diff: bool = True,
        caminho_saida_diff: Optional[str] = None,
        formato: str = "resumo",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa a comparação geométrica entre as plantas.
        :param edificio_base: Nome ou código do edifício base (ex: 'Zuckhan soledade', '054').
        :param pavimento_base: Nome do pavimento (opcional; se omitido em modo 'auto', varre o edifício).
        :param edificio_comparado: Edifício de destino para comparação entre edifícios/revisões.
        :param pavimento_comparado: Pavimento de destino para comparação.
        :param caminho_geo: Caminho de um ou mais arquivos Geo_*.DWG.
        :param caminho_for: Caminho do arquivo FOR*.DWG.
        :param modo: 'auto', 'dwg', 'edificio_geometrias' ou 'pavimentos'.
        :param gerar_desenho_diff: Se True, emite desenho DXF com sobreposição gráfica.
        :param caminho_saida_diff: Caminho customizado para salvar o DXF.
        :param formato: 'resumo' (Markdown), 'terminal' ou 'json'.
        """
        comparator = TQSGeometryComparator()

        # Caso 1: Comparação direta entre arquivos DWG
        if caminho_for is not None or (caminho_geo is not None and caminho_for is not None) or modo == "dwg":
            if not caminho_geo or not caminho_for:
                return {
                    "status": "erro",
                    "sucesso": False,
                    "erro": "Modo DWG requer 'caminho_geo' e 'caminho_for'."
                }
            resultado = comparator.comparar_arquivos_dwg(
                caminhos_geo=caminho_geo,
                caminho_for=caminho_for,
                pavimento=pavimento_base or "PAVIMENTO",
                gerar_desenho_diff=gerar_desenho_diff,
                caminho_saida_diff=caminho_saida_diff
            )
            texto_saida = resultado.para_tabela_terminal() if formato == "terminal" else resultado.para_resumo_executivo()
            return {
                "status": "sucesso",
                "sucesso": True,
                "tem_mudancas": resultado.tem_mudancas,
                "resumo_executivo": texto_saida,
                "dados_completos": resultado.para_dict(),
                "caminho_diff_dxf": resultado.caminho_diff_dxf
            }

        # Caso 2: Varredura de geometrias de todo o edifício
        if modo == "edificio_geometrias" or (edificio_base and (not pavimento_base or pavimento_base.lower() in ["todos", "todas", "geometrias"])):
            resultados = comparator.comparar_edificio_geometrias(
                edificio_nome_ou_caminho=edificio_base,
                gerar_desenhos_diff=gerar_desenho_diff
            )
            if not resultados:
                return {
                    "status": "erro",
                    "sucesso": False,
                    "erro": f"Nenhum pavimento com FOR*.DWG e Geo_*.DWG encontrado no edifício '{edificio_base}'."
                }

            linhas_resumo = [
                f"# AUDITORIA DE FORMAS VS GEOMETRIAS: {edificio_base.upper()}",
                "Varredura automática comparando a última geometria sem revisão no título com a forma calculada.\n"
            ]
            tem_mudancas_total = False
            dxfs_gerados = []
            dados_dict = {}

            for pav_nome, res in resultados.items():
                if res.tem_mudancas:
                    tem_mudancas_total = True
                if res.caminho_diff_dxf:
                    dxfs_gerados.append(res.caminho_diff_dxf)
                dados_dict[pav_nome] = res.para_dict()
                linhas_resumo.append(f"## Pavimento: {pav_nome}")
                linhas_resumo.append(f"- Pilares Novos: {res.total_novos} | Removidos: {res.total_removidos} | Alterados: {res.total_alterados} | Inalterados: {res.total_inalterados}")
                if res.caminho_diff_dxf:
                    linhas_resumo.append(f"- Prancha Diff DXF: `{res.caminho_diff_dxf}`")
                linhas_resumo.append("")

            return {
                "status": "sucesso",
                "sucesso": True,
                "tem_mudancas": tem_mudancas_total,
                "resumo_executivo": "\n".join(linhas_resumo),
                "dados_completos": dados_dict,
                "caminhos_diff_dxf": dxfs_gerados,
                "caminho_diff_dxf": dxfs_gerados[0] if dxfs_gerados else None
            }

        # Caso 3: Comparação clássica via TQSModelEditor / TQSBuildingReader
        if not edificio_base or not pavimento_base:
            return {
                "status": "erro",
                "sucesso": False,
                "erro": "Para comparação por pavimento, especifique 'edificio_base' e 'pavimento_base'."
            }

        resultado = comparator.comparar_pavimentos(
            edificio_base=edificio_base,
            pavimento_base=pavimento_base,
            edificio_comparado=edificio_comparado,
            pavimento_comparado=pavimento_comparado,
            gerar_desenho_diff=gerar_desenho_diff,
            caminho_saida_diff=caminho_saida_diff
        )

        texto_saida = resultado.para_tabela_terminal() if formato == "terminal" else resultado.para_resumo_executivo()

        return {
            "status": "sucesso",
            "sucesso": True,
            "tem_mudancas": resultado.tem_mudancas,
            "resumo_executivo": texto_saida,
            "dados_completos": resultado.para_dict(),
            "caminho_diff_dxf": resultado.caminho_diff_dxf
        }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """Valida se a comparação produziu resultados válidos."""
        if not resultado or resultado.get("status") != "sucesso":
            return False
        return "dados_completos" in resultado
