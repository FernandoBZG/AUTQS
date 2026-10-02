import os
import math
from typing import List, Tuple, Optional
try:
    import ezdxf
    from ezdxf import colors
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    ezdxf = None
    colors = None
    TextEntityAlignment = None
from src.core.models import PlantaDeCargasModel, PilarFundacao, TipoSecao

class PlantaDeCargasDwgBuilder:
    """
    Construtor gráfico de pranchas completas de Planta de Cargas e Locação.
    Gera arquivos vetoriais compatíveis nativamente com TQS V25 e AutoCAD,
    contendo a locação fiel dos pilares com baricentros, cotas e a tabela de cargas diagramada.
    """

    def __init__(self, escala: int = 50):
        self.escala = escala # 1:50
        self.doc = ezdxf.new("R2010", setup=True)
        self.msp = self.doc.modelspace()
        self._configurar_layers()

    def _configurar_layers(self):
        """Cria layers padronizados com cores e tipos de linha de engenharia estrutural."""
        layers = [
            ("PILARES_CONTORNO", colors.CYAN, "Continuous"),
            ("PILARES_HACHURA", colors.LIGHT_GRAY, "Continuous"),
            ("PILARES_TEXTO", colors.WHITE, "Continuous"),
            ("BARICENTRO", colors.RED, "Continuous"),
            ("EIXOS_LOCACAO", colors.MAGENTA, "DASHDOT"),
            ("COTAS", colors.GREEN, "Continuous"),
            ("TABELA_LINHAS", colors.WHITE, "Continuous"),
            ("TABELA_TEXTOS", colors.YELLOW, "Continuous"),
            ("FOLHA_BORDA", colors.BLUE, "Continuous"),
            ("FOLHA_CARIMBO", colors.WHITE, "Continuous"),
        ]
        for nome, cor, linetype in layers:
            if nome not in self.doc.layers:
                self.doc.layers.add(nome, color=cor, linetype=linetype)

    def _adicionar_retangulo(self, x: float, y: float, w: float, h: float, layer: str, lineweight: int = 25):
        """Desenha um retângulo fechado no modelspace a partir do canto inferior esquerdo."""
        vertices = [
            (x, y),
            (x + w, y),
            (x + w, y + h),
            (x, y + h)
        ]
        return self.msp.add_lwpolyline(
            vertices,
            close=True,
            dxfattribs={"layer": layer, "lineweight": lineweight}
        )

    def _desenhar_pilar(self, pilar: PilarFundacao):
        """Desenha o contorno do pilar na base, rotacionado e com baricentro marcado."""
        geom = pilar.geometria
        xcg = pilar.baricentro.x / 100.0
        ycg = pilar.baricentro.y / 100.0

        # Se temos os vértices reais extraídos do TQS (em cm), convertemos para metros
        if geom.vertices_poligono and len(geom.vertices_poligono) >= 3:
            vertices_globais = [(pt[0] / 100.0, pt[1] / 100.0) for pt in geom.vertices_poligono]
        else:
            b_m = geom.b / 100.0
            h_m = geom.h / 100.0
            theta_rad = math.radians(geom.angulo_rotacao_graus)
            dx_locais = [-b_m / 2.0, b_m / 2.0, b_m / 2.0, -b_m / 2.0]
            dy_locais = [-h_m / 2.0, -h_m / 2.0, h_m / 2.0, h_m / 2.0]

            vertices_globais = []
            for dx, dy in zip(dx_locais, dy_locais):
                gx = xcg + dx * math.cos(theta_rad) - dy * math.sin(theta_rad)
                gy = ycg + dx * math.sin(theta_rad) + dy * math.cos(theta_rad)
                vertices_globais.append((gx, gy))

        # Desenha o contorno do pilar
        self.msp.add_lwpolyline(
            vertices_globais,
            close=True,
            dxfattribs={"layer": "PILARES_CONTORNO", "lineweight": 35}
        )

        # Marcação visual do Baricentro (cruz de 30 cm)
        tamanho_cruz = 0.20 # 20 cm
        self.msp.add_line(
            (xcg - tamanho_cruz, ycg),
            (xcg + tamanho_cruz, ycg),
            dxfattribs={"layer": "BARICENTRO", "lineweight": 25}
        )
        self.msp.add_line(
            (xcg, ycg - tamanho_cruz),
            (xcg, ycg + tamanho_cruz),
            dxfattribs={"layer": "BARICENTRO", "lineweight": 25}
        )
        self.msp.add_circle(
            (xcg, ycg),
            radius=0.08,
            dxfattribs={"layer": "BARICENTRO", "lineweight": 20}
        )

        # Identificação do Pilar (P1) e Dimensões (ex: 19x30)
        texto_pilar = f"{pilar.nome} ({geom.b:.0f}x{geom.h:.0f})"
        self.msp.add_text(
            texto_pilar,
            dxfattribs={
                "layer": "PILARES_TEXTO",
                "height": 0.22,
            }
        ).set_placement((xcg + 0.15, ycg + 0.15), align=TextEntityAlignment.BOTTOM_LEFT)

        # Texto do Baricentro com coordenadas
        texto_cg = f"CG({xcg:.3f}; {ycg:.3f})"
        self.msp.add_text(
            texto_cg,
            dxfattribs={
                "layer": "BARICENTRO",
                "height": 0.14,
            }
        ).set_placement((xcg + 0.15, ycg - 0.30), align=TextEntityAlignment.TOP_LEFT)

    def _desenhar_tabela_cargas_multiplas_colunas(
        self,
        planta: PlantaDeCargasModel,
        x_origem: float,
        y_origem: float,
        max_linhas_por_coluna: int = 35
    ) -> Tuple[float, float]:
        """
        Desenha a Tabela de Cargas vetorial dividida em colunas adjacentes
        caso o número de pilares seja elevado (ex: 69 pilares).
        Retorna (largura_ocupada, altura_ocupada).
        """
        cabecalhos = [
            ("Pilar", 1.1),
            ("Seção", 1.4),
            ("Xcg (m)", 1.4),
            ("Ycg (m)", 1.4),
            ("Nk (tf)", 1.4),
            ("Mx", 1.1),
            ("My", 1.1),
            ("Fx", 1.1),
            ("Fy", 1.1),
        ]
        largura_bloco = sum(l for _, l in cabecalhos)
        altura_linha = 0.45
        altura_titulo = 0.65
        espacamento_entre_blocos = 1.0

        # Divide os pilares em blocos
        todos_pilares = planta.pilares
        blocos = [
            todos_pilares[i:i + max_linhas_por_coluna]
            for i in range(0, len(todos_pilares), max_linhas_por_coluna)
        ]

        x_bloco_atual = x_origem
        altura_max_alcancada = 0.0

        for idx_bloco, pilares_bloco in enumerate(blocos):
            y_atual = y_origem

            # 1. Título do Bloco
            self._adicionar_retangulo(
                x_bloco_atual, y_atual - altura_titulo, largura_bloco, altura_titulo,
                layer="TABELA_LINHAS", lineweight=30
            )
            sufixo = f" (PARTE {idx_bloco + 1}/{len(blocos)})" if len(blocos) > 1 else ""
            titulo_texto = f"CARGAS NA FUNDAÇÃO{sufixo}"
            self.msp.add_text(
                titulo_texto,
                dxfattribs={"layer": "TABELA_TEXTOS", "height": 0.22}
            ).set_placement(
                (x_bloco_atual + largura_bloco / 2.0, y_atual - altura_titulo / 2.0),
                align=TextEntityAlignment.MIDDLE_CENTER
            )
            y_atual -= altura_titulo

            # 2. Cabeçalho das Colunas
            x_col = x_bloco_atual
            for texto_cab, larg in cabecalhos:
                self._adicionar_retangulo(
                    x_col, y_atual - altura_linha, larg, altura_linha,
                    layer="TABELA_LINHAS", lineweight=25
                )
                self.msp.add_text(
                    texto_cab,
                    dxfattribs={"layer": "TABELA_TEXTOS", "height": 0.16}
                ).set_placement(
                    (x_col + larg / 2.0, y_atual - altura_linha / 2.0),
                    align=TextEntityAlignment.MIDDLE_CENTER
                )
                x_col += larg
            y_atual -= altura_linha

            # 3. Linhas com Dados dos Pilares
            for p in pilares_bloco:
                xcg = p.baricentro.x / 100.0 if p.baricentro else 0.0
                ycg = p.baricentro.y / 100.0 if p.baricentro else 0.0
                secao_str = f"{p.geometria.b:.0f}x{p.geometria.h:.0f}"
                nk_val = p.esforcos.nk_max if p.esforcos else 0.0
                mx_val = p.esforcos.mxk if p.esforcos else 0.0
                my_val = p.esforcos.myk if p.esforcos else 0.0
                hx_val = p.esforcos.hx if p.esforcos else 0.0
                hy_val = p.esforcos.hy if p.esforcos else 0.0

                valores = [
                    p.nome,
                    secao_str,
                    f"{xcg:.2f}",
                    f"{ycg:.2f}",
                    f"{nk_val:.1f}",
                    f"{mx_val:.2f}",
                    f"{my_val:.2f}",
                    f"{hx_val:.2f}",
                    f"{hy_val:.2f}",
                ]

                x_col = x_bloco_atual
                for val_str, (_, larg) in zip(valores, cabecalhos):
                    self._adicionar_retangulo(
                        x_col, y_atual - altura_linha, larg, altura_linha,
                        layer="TABELA_LINHAS", lineweight=15
                    )
                    self.msp.add_text(
                        val_str,
                        dxfattribs={"layer": "PILARES_TEXTO", "height": 0.16}
                    ).set_placement(
                        (x_col + larg / 2.0, y_atual - altura_linha / 2.0),
                        align=TextEntityAlignment.MIDDLE_CENTER
                    )
                    x_col += larg

                y_atual -= altura_linha

            altura_deste_bloco = y_origem - y_atual
            if altura_deste_bloco > altura_max_alcancada:
                altura_max_alcancada = altura_deste_bloco

            x_bloco_atual += largura_bloco + espacamento_entre_blocos

        # Notas no rodapé da tabela (abaixo do primeiro bloco)
        notas = [
            "NOTAS DE PROJETO:",
            "1. Coordenadas (Xcg, Ycg) em metros no referencial global do TQS.",
            "2. Cargas verticais (Nk) e esforços na base extraídos do Pórtico Espacial TQS V25.",
            "3. Convenção de sinais: Nk positivo indica compressão no apoio da fundação.",
        ]
        y_nota = y_origem - altura_max_alcancada - 0.50
        for nota in notas:
            self.msp.add_text(
                nota,
                dxfattribs={"layer": "TABELA_TEXTOS", "height": 0.16}
            ).set_placement((x_origem, y_nota), align=TextEntityAlignment.BOTTOM_LEFT)
            y_nota -= 0.28

        largura_total_ocupada = x_bloco_atual - x_origem - espacamento_entre_blocos
        return largura_total_ocupada, altura_max_alcancada + 2.0

    def _desenhar_folha_e_carimbo(
        self,
        min_x: float, min_y: float,
        largura: float, altura: float,
        planta: PlantaDeCargasModel
    ):
        """Desenha a margem da folha e o selo / carimbo de projeto."""
        margem = 0.8
        # Margem externa
        self._adicionar_retangulo(min_x, min_y, largura, altura, layer="FOLHA_BORDA", lineweight=50)

        # Margem interna
        self._adicionar_retangulo(
            min_x + margem, min_y + margem,
            largura - 2 * margem, altura - 2 * margem,
            layer="FOLHA_BORDA", lineweight=30
        )

        # Selo / Carimbo no canto inferior direito
        larg_selo = 8.5
        alt_selo = 3.5
        x_selo = min_x + largura - margem - larg_selo
        y_selo = min_y + margem

        self._adicionar_retangulo(
            x_selo, y_selo, larg_selo, alt_selo,
            layer="FOLHA_CARIMBO", lineweight=35
        )

        linhas_carimbo = [
            ("AUTQS - SISTEMA INTELIGENTE DE ESTRUTURAS", 0.24, 2.9),
            (f"EDIFÍCIO: {planta.edificio_nome.upper()}", 0.22, 2.3),
            ("CONTEÚDO: PLANTA DE CARGAS E LOCAÇÃO DE FUNDAÇÕES", 0.22, 1.7),
            (f"PAVIMENTO: {planta.pavimento_fundacao.upper()} | PILARES: {len(planta.pilares)}", 0.20, 1.1),
            (f"ESCALA: 1:{self.escala} | DESENHO: AUTÔNOMO TQS V25", 0.18, 0.5),
        ]
        for txt, h, dy in linhas_carimbo:
            self.msp.add_text(
                txt,
                dxfattribs={"layer": "FOLHA_CARIMBO", "height": h}
            ).set_placement((x_selo + 0.3, y_selo + dy), align=TextEntityAlignment.BOTTOM_LEFT)

    def construir_planta_completa(
        self,
        planta: PlantaDeCargasModel,
        caminho_saida: str
    ) -> str:
        """
        Monta a prancha completa contendo:
        1. Desenho de todos os pilares com contorno real e baricentro
        2. Tabela de cargas diagramada em colunas
        3. Margens e Carimbo da folha
        """
        # Desenha todos os pilares
        for p in planta.pilares:
            self._desenhar_pilar(p)

        # Calcula bounding box de todos os pilares
        xs = [p.baricentro.x / 100.0 for p in planta.pilares if p.baricentro]
        ys = [p.baricentro.y / 100.0 for p in planta.pilares if p.baricentro]

        min_px = min(xs) if xs else 0.0
        max_px = max(xs) if xs else 10.0
        min_py = min(ys) if ys else 0.0
        max_py = max(ys) if ys else 10.0

        # Posiciona a tabela à direita do conjunto de pilares
        x_tabela = max_px + 5.0
        y_tabela = max_py + 1.0

        larg_tab, alt_tab = self._desenhar_tabela_cargas_multiplas_colunas(
            planta,
            x_origem=x_tabela,
            y_origem=y_tabela,
            max_linhas_por_coluna=36
        )

        # Dimensões da folha global
        folha_min_x = min_px - 4.0
        folha_min_y = min(min_py, y_tabela - alt_tab) - 4.0
        folha_max_x = x_tabela + larg_tab + 4.0
        folha_max_y = max_py + 4.0

        largura_folha = folha_max_x - folha_min_x
        altura_folha = folha_max_y - folha_min_y

        # Desenha margem e carimbo
        self._desenhar_folha_e_carimbo(
            folha_min_x, folha_min_y,
            largura_folha, altura_folha,
            planta
        )

        # Salva arquivo
        caminho_final = caminho_saida
        if caminho_saida.lower().endswith(".dwg"):
            caminho_final = caminho_saida[:-4] + ".dxf"

        self.doc.saveas(caminho_final)
        return caminho_final
