from typing import List, Optional
import src.tqs_adapter.tqs_env # Garante a configuração do ambiente 64 bits do TQS
from src.core.models import PilarFundacao, PlantaDeCargasModel

try:
    from TQS import TQSGrid
    TQS_GRID_DISPONIVEL = True
except ImportError:
    TQS_GRID_DISPONIVEL = False

class GridTabelaCargasAdapter:
    """
    Adapter para gerar e diagramar a Tabela de Cargas e Locação
    utilizando o módulo nativo TQSGrid (NDWGGRID.DLL) em 64-bit.
    """

    CABECALHOS = [
        "Pilar",
        "Seção (cm)",
        "Xcg (m)",
        "Ycg (m)",
        "Nk,max (tf)",
        "Nk,min (tf)",
        "Mx,k (tf.m)",
        "My,k (tf.m)",
        "Hx (tf)",
        "Hy (tf)"
    ]

    def __init__(self):
        self.disponivel = TQS_GRID_DISPONIVEL

    def criar_grid(self, planta: PlantaDeCargasModel):
        """
        Instancia e preenche o GridDwg do TQS com os dados da planta de cargas.
        """
        if not self.disponivel:
            raise RuntimeError("Módulo TQSGrid não está disponível no ambiente Python atual.")

        grid = TQSGrid.GridDwg()
        
        num_linhas = len(planta.pilares) + 2 # Título + Cabeçalho + Linhas dos pilares
        num_colunas = len(self.CABECALHOS)
        
        grid.format.lines = num_linhas
        grid.format.columns = num_colunas

        # Linha 0: Título principal mesclado
        titulo = f"TABELA DE CARGAS E LOCAÇÃO NA FUNDAÇÃO - {planta.edificio_nome.upper()}"
        grid.format.MergeLine(0, 0, num_colunas - 1)
        grid.format.SetCell(0, 0, titulo)

        # Linha 1: Cabeçalhos das colunas
        for col_idx, cabecalho in enumerate(self.CABECALHOS):
            grid.format.SetCell(1, col_idx, cabecalho)

        # Linhas 2 em diante: Dados de cada pilar
        for row_idx, pilar in enumerate(planta.pilares, start=2):
            secao_str = f"{pilar.geometria.b:.1f}x{pilar.geometria.h:.1f}"
            xcg_str = f"{pilar.baricentro.x / 100.0:.3f}" if pilar.baricentro else "-"
            ycg_str = f"{pilar.baricentro.y / 100.0:.3f}" if pilar.baricentro else "-"
            
            nk_max_str = f"{pilar.esforcos.nk_max:.1f}" if pilar.esforcos else "0.0"
            nk_min_str = f"{pilar.esforcos.nk_min:.1f}" if pilar.esforcos and pilar.esforcos.nk_min is not None else "-"
            mx_str = f"{pilar.esforcos.mxk:.2f}" if pilar.esforcos else "0.00"
            my_str = f"{pilar.esforcos.myk:.2f}" if pilar.esforcos else "0.00"
            hx_str = f"{pilar.esforcos.hx:.2f}" if pilar.esforcos else "0.00"
            hy_str = f"{pilar.esforcos.hy:.2f}" if pilar.esforcos else "0.00"

            valores_linha = [
                pilar.nome,
                secao_str,
                xcg_str,
                ycg_str,
                nk_max_str,
                nk_min_str,
                mx_str,
                my_str,
                hx_str,
                hy_str
            ]

            for col_idx, val in enumerate(valores_linha):
                grid.format.SetCell(row_idx, col_idx, str(val))

        return grid

    def exportar_dwg(self, planta: PlantaDeCargasModel, caminho_dwg_saida: str) -> str:
        """
        Gera um arquivo de desenho .DWG exclusivo com a tabela de cargas.
        """
        grid = self.criar_grid(planta)
        grid.file.SaveAsDwg(caminho_dwg_saida)
        return caminho_dwg_saida

    def exportar_html(self, planta: PlantaDeCargasModel, caminho_html_saida: str) -> str:
        """
        Gera um relatório HTML da tabela de cargas para visualização rápida.
        """
        grid = self.criar_grid(planta)
        grid.file.SaveAsHtml(caminho_html_saida)
        return caminho_html_saida

    def mesclar_em_dwg_existente(self, planta: PlantaDeCargasModel, objeto_dwg, x_org: float, y_org: float):
        """
        Mescla a tabela diretamente dentro da folha/prancha da planta de cargas.
        """
        grid = self.criar_grid(planta)
        grid.file.SaveAndMergeDwg(objeto_dwg, x_org, y_org)
