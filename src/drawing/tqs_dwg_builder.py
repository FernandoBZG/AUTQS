import os
import json
import math
from typing import List, Optional, Tuple, Dict, Any
from TQS import TQSDwg
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
from src.core.models import PlantaDeCargasModel, PilarFundacao

# Garante ambiente TQS 64-bit configurado
configurar_ambiente_tqs_64()

# Catálogo oficial de formatos/molduras padronizados do TQS (D:\TQSW\SUPORTE\NGE\MOLDURAS)
# Todos os arquivos .DWG abaixo existem na instalação nativa do TQS. Largura máxima é rigorosamente 180.0 cm.
# (Nome, Largura_papel_cm, Altura_papel_cm)
CATALOGO_MOLDURAS_TQS = [
    # Formatos ISO Padronizados
    ("A3", 42.0, 29.7),
    ("A2", 59.4, 42.0),
    ("A1", 84.1, 59.4),
    ("A1L", 118.9, 59.4),
    ("A0", 118.9, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (95 cm)
    ("95-40", 95.0, 40.0),
    ("95-50", 95.0, 50.0),
    ("95-60", 95.0, 59.4),
    ("95-70", 95.0, 70.0),
    ("95-80", 95.0, 80.0),
    ("95-85", 95.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (105 cm)
    ("105-40", 105.0, 40.0),
    ("105-50", 105.0, 50.0),
    ("105-60", 105.0, 59.4),
    ("105-70", 105.0, 70.0),
    ("105-80", 105.0, 80.0),
    ("105-85", 105.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (130 cm)
    ("130-40", 130.0, 40.0),
    ("130-50", 130.0, 50.0),
    ("130-60", 130.0, 59.4),
    ("130-70", 130.0, 70.0),
    ("130-80", 130.0, 80.0),
    ("130-85", 130.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (140 cm)
    ("140-40", 140.0, 40.0),
    ("140-50", 140.0, 50.0),
    ("140-60", 140.0, 59.4),
    ("140-70", 140.0, 70.0),
    ("140-80", 140.0, 80.0),
    ("140-85", 140.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (150 cm)
    ("150-40", 150.0, 40.0),
    ("150-50", 150.0, 50.0),
    ("150-60", 150.0, 59.4),
    ("150-70", 150.0, 70.0),
    ("150-80", 150.0, 80.0),
    ("150-85", 150.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (160 cm)
    ("160-40", 160.0, 40.0),
    ("160-50", 160.0, 50.0),
    ("160-60", 160.0, 59.4),
    ("160-70", 160.0, 70.0),
    ("160-80", 160.0, 80.0),
    ("160-85", 160.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (170 cm)
    ("170-40", 170.0, 40.0),
    ("170-50", 170.0, 50.0),
    ("170-60", 170.0, 59.4),
    ("170-70", 170.0, 70.0),
    ("170-80", 170.0, 80.0),
    ("170-85", 170.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (180 cm - Formato Máximo Oficial)
    ("180-50", 180.0, 50.0),
    ("180-55", 180.0, 55.0),
    ("180-60", 180.0, 59.4),
    ("180-65", 180.0, 65.0),
    ("180-70", 180.0, 70.0),
    ("180-75", 180.0, 75.0),
    ("180-80", 180.0, 80.0),
    ("180-85", 180.0, 84.1),
]

class TQSDwgPlantaDeCargasBuilder:
    """
    Construtor UNIVERSAL de pranchas de Planta de Cargas e Locação de Fundações
    em formato binário .DWG nativo do TQS V25 (AC1006).
    
    Capacidades Universais:
      - Aceita QUALQUER edifício do TQS (pequeno, médio ou gigante).
      - Auto-diagramação: calcula a caixa delimitadora real dos pilares e posiciona
        as tabelas de baricentro e cargas dinamicamente, sem sobreposições.
      - Auto-seleção de moldura: calcula a área total e escolhe automaticamente
        o menor formato catalogado oficial do TQS (A1, A0, 130-60, 150-70, etc.)
        que enquadre perfeitamente o projeto com as margens ABNT.
      - Desenha a projeção da moldura no desenho (níveis 18 e 32), deixando
        a área do carimbo reservada para montagem no TQS.
      - Padrão gráfico fiel a GEO_CARGAS.DWG: Níveis 3, 9, 12, 21, 0, 18, 32, 222, 250.
    """

    def __init__(self, template_dwg: Optional[str] = None):
        if template_dwg:
            self.template_dwg = template_dwg
        else:
            raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            caminho_geo = os.path.join(raiz_projeto, "GEO_CARGAS.DWG")
            if os.path.exists(caminho_geo):
                self.template_dwg = caminho_geo
            else:
                from src.tqs_adapter.tqs_env import PASTA_SUPORTE
                seed = os.path.join(PASTA_SUPORTE, "NGE", "SEED.DWG") if PASTA_SUPORTE else ""
                if not os.path.exists(seed):
                    for d in ["C", "D", "E", "F"]:
                        cand = fr"{d}:\TQSW\SUPORTE\NGE\SEED.DWG"
                        if os.path.exists(cand):
                            seed = cand
                            break
                self.template_dwg = seed

    def construir_planta_de_cargas(
        self,
        planta: PlantaDeCargasModel,
        arquivo_saida_dwg: str,
        escala: int = 50,
    ) -> str:
        """
        Gera a folha .DWG nativa do TQS adaptada automaticamente a qualquer edifício.
        """
        if not planta.pilares:
            raise ValueError(f"Edifício {planta.edificio_nome} não possui pilares de fundação carregados.")

        dwg = TQSDwg.Dwg(pedmv=0)
        
        # Abre o template base (com níveis, estilos e penas configurados)
        if os.path.exists(self.template_dwg):
            dwg.file.Open(self.template_dwg)
        else:
            raise FileNotFoundError(f"Template TQS não encontrado em: {self.template_dwg}")

        # Se for o template GEO_CARGAS.DWG, limpa elementos antigos mantendo estilos e camadas
        if "GEO_CARGAS" in os.path.basename(self.template_dwg).upper():
            it = dwg.iterator
            it.Begin()
            posicoes = []
            while True:
                pos = it.GetElementReadPosition()
                if pos:
                    posicoes.append(pos)
                if not it.Next():
                    break
            for p in posicoes:
                dwg.edit.Erase(p)

        # 1. Análise Geométrica Dinâmica do Edifício
        bounds_planta = self._calcular_bounding_box_pilares(planta.pilares)
        min_xp, max_xp, min_yp, max_yp = bounds_planta
        larg_locacao = max_xp - min_xp
        alt_locacao = max_yp - min_yp

        # 2. Desenha a Planta de Locação dos Pilares nas suas coordenadas originais
        self._desenhar_pilares_locacao(dwg, planta.pilares, bounds_planta, escala=escala)

        # 3. Disposição Inteligente das Tabelas para Enquadramento em Molduras Padrão TQS
        dados_porlid = planta.dados_porlid
        num_casos = dados_porlid.get("num_casos", 1) if dados_porlid else 1
        larg_tabela_cargas_est = (num_casos * 515.0 + (num_casos - 1) * 35.0) if num_casos > 1 else 1220.0
        alt_tabela_est = len(planta.pilares) * 22.0 + 180.0

        larg_total_lado = larg_locacao + 250.0 + max(larg_tabela_cargas_est, 1260.0)
        alt_total_abaixo = alt_locacao + 180.0 + alt_tabela_est

        # Verifica se o arranjo lateral (lado a lado) cabe na folha máxima do TQS (180 cm de largura) na escala inicial
        if (larg_total_lado / escala) <= 172.0:
            layout_modo = "lado_a_lado"
        elif (larg_locacao / escala) <= 172.0 and (alt_total_abaixo / escala) <= 80.0:
            # Edifício muito extenso em X (como Jardim Europa): dispõe as tabelas horizontalmente abaixo da locação
            layout_modo = "abaixo"
        else:
            layout_modo = "lado_a_lado"

        if layout_modo == "lado_a_lado":
            x_tabelas = max_xp + 250.0 # 2.5 m de afastamento lateral
            y_topo_tabelas = max_yp + 50.0

            # Tabela de Baricentros
            y_fim_bar, larg_tabela_bar = self._desenhar_tabela_baricentros(
                dwg, planta.pilares, x_start=x_tabelas, y_start=y_topo_tabelas
            )

            # Tabela de Cargas (logo abaixo da de baricentros)
            y_topo_cargas = y_fim_bar - 70.0
            y_fim_cargas, larg_tabela_cargas = self._desenhar_tabela_cargas(
                dwg,
                pilares=planta.pilares,
                x_start=x_tabelas,
                y_start=y_topo_cargas,
                dados_porlid=planta.dados_porlid,
            )

            # Notas, Convenção de Sinais e Legenda (logo abaixo das cargas)
            y_topo_notas = y_fim_cargas - 70.0
            y_fim_notas = self._desenhar_notas_e_legendas(
                dwg, x_start=x_tabelas, y_start=y_topo_notas, dados_porlid=planta.dados_porlid
            )

            largura_max_tabelas = max(larg_tabela_bar, larg_tabela_cargas, 2720.0)
            bounds_conteudo = (
                min_xp,
                x_tabelas + largura_max_tabelas,
                min(min_yp, y_fim_notas),
                max(max_yp + 260.0, y_topo_tabelas + 100.0),
            )
        else:
            # layout_modo == "abaixo" (Tabelas dispostas lado a lado horizontalmente sob a locação)
            y_topo_tabelas = min_yp - 120.0
            x_cargas = min_xp

            # 1. Tabela de Cargas (alinhada à esquerda)
            y_fim_cargas, larg_tabela_cargas = self._desenhar_tabela_cargas(
                dwg,
                pilares=planta.pilares,
                x_start=x_cargas,
                y_start=y_topo_tabelas,
                dados_porlid=planta.dados_porlid,
            )

            # 2. Tabela de Baricentros (ao lado direito da de cargas)
            x_bar = x_cargas + larg_tabela_cargas + 80.0
            y_fim_bar, larg_tabela_bar = self._desenhar_tabela_baricentros(
                dwg, planta.pilares, x_start=x_bar, y_start=y_topo_tabelas
            )

            # 3. Notas, Convenção de Sinais e Legenda (ao lado da de baricentros)
            x_notas = x_bar + larg_tabela_bar + 80.0
            y_fim_notas = self._desenhar_notas_e_legendas(
                dwg, x_start=x_notas, y_start=y_topo_tabelas, dados_porlid=planta.dados_porlid
            )

            x_max_conteudo = max(max_xp, x_notas + 2720.0)
            y_min_conteudo = min(y_fim_cargas, y_fim_bar, y_fim_notas)
            bounds_conteudo = (
                min_xp,
                x_max_conteudo,
                y_min_conteudo,
                max_yp + 260.0,
            )

        # 4. Seleção Automática e Desenho da Moldura Catalogada Oficial TQS
        formato_escolhido, escala_final = self._auto_selecionar_e_desenhar_moldura(
            dwg, bounds_conteudo, escala_inicial=escala, planta=planta
        )

        # 5. Salva o arquivo nativo TQS .DWG
        pasta_destino = os.path.dirname(arquivo_saida_dwg)
        if pasta_destino and not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino, exist_ok=True)

        dwg.file.SaveAs(arquivo_saida_dwg)
        dwg.file.Close()

        return arquivo_saida_dwg

    def _calcular_bounding_box_pilares(self, pilares: List[PilarFundacao]) -> Tuple[float, float, float, float]:
        """Calcula os limites espaciais reais [min_x, max_x, min_y, max_y] do conjunto de pilares."""
        xs, ys = [], []
        for p in pilares:
            if p.geometria.vertices_poligono:
                for vx, vy in p.geometria.vertices_poligono:
                    xs.append(vx)
                    ys.append(vy)
            elif p.baricentro:
                xs.append(p.baricentro.x)
                ys.append(p.baricentro.y)
        return min(xs), max(xs), min(ys), max(ys)

    def _calcular_posicao_rotulo_pilar(
        self,
        pilar: PilarFundacao,
        todos_pilares: List[PilarFundacao],
    ) -> Tuple[float, float, float, float]:
        """
        Calcula a posição do bloco de rótulo (Título + Dimensão logo abaixo)
        garantindo que:
        1. O texto NUNCA fique sobreposto ao polígono do pilar.
        2. A dimensão acompanhe o título diretamente abaixo dele (como no GEO_CARGAS.DWG).
        3. Em pilares gêmeos de junta (distância < 65 cm), um rótulo fique à esquerda e o outro à direita.
        """
        geom = pilar.geometria
        vts = geom.vertices_poligono
        if vts and len(vts) >= 3:
            min_x = min(pt[0] for pt in vts)
            max_x = max(pt[0] for pt in vts)
            min_y = min(pt[1] for pt in vts)
            max_y = max(pt[1] for pt in vts)
        else:
            w = geom.b if geom.b > 0 else 20.0
            h = geom.h if geom.h > 0 else 20.0
            min_x = pilar.baricentro.x - w / 2.0
            max_x = pilar.baricentro.x + w / 2.0
            min_y = pilar.baricentro.y - h / 2.0
            max_y = pilar.baricentro.y + h / 2.0

        # Verifica se há pilar vizinho colado à direita (junta de dilatação < 65 cm)
        tem_vizinho_direita = False
        for outro in todos_pilares:
            if outro.nome == pilar.nome:
                continue
            vo = outro.geometria.vertices_poligono
            if not vo:
                continue
            min_xo = min(pt[0] for pt in vo)
            min_yo = min(pt[1] for pt in vo)
            max_yo = max(pt[1] for pt in vo)
            if 0.0 <= (min_xo - max_x) < 65.0 and not (max_y < min_yo or min_y > max_yo):
                tem_vizinho_direita = True
                break

        if tem_vizinho_direita:
            x_nome = min_x - 55.0
            y_nome = min_y - 12.0
        else:
            x_nome = max_x + 8.0
            y_nome = min_y - 12.0

        x_dim = x_nome
        y_dim = y_nome - 22.0

        return x_nome, y_nome, x_dim, y_dim

    def _desenhar_pilares_locacao(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        bounds: Tuple[float, float, float, float],
        escala: int = 50,
    ):
        """
        Desenha cada pilar em suas coordenadas espaciais reais:
        - Título Oficial TQS (Padrão GEO_CARGAS / Zuckhan Soledade):
          Nível 222, Altura 60.0: 'GABARITO E CARGAS NAS FUNDAÇÕES'
          Nível 250, Altura 22.5: 'ESCALA 1:50' posicionado diretamente abaixo
        - Contorno retangular ou poligonal fechado (Nível 3)
        - Cruz de baricentro (Nível 21)
        - Nome do pilar (Nível 9, H=18.0) fora do contorno
        - Dimensões da seção (Nível 12, H=13.5) diretamente abaixo do nome
        """
        min_x, max_x, min_y, max_y = bounds
        cx_planta = (min_x + max_x) / 2.0

        # Título Oficial (Padrão Oficial TQS GEO_CARGAS / Zuckhan Soledade)
        # Nível 222, Tamanho 60.0: GABARITO E CARGAS NAS FUNDAÇÕES
        y_titulo = max_y + 160.0
        larg_titulo_est = 1860.0
        if (max_x - min_x) > (larg_titulo_est + 400.0):
            x_titulo = min_x + 100.0
        else:
            x_titulo = max(min_x, cx_planta - (larg_titulo_est / 2.0))

        dwg.draw.level = 222
        dwg.draw.Text(x_titulo, y_titulo, 60.0, 0.0, "GABARITO E CARGAS NAS FUNDAÇÕES")

        # Texto indicando escala na posição abaixo conforme padrão GEO_CARGAS (Nível 250, Tamanho 22.5)
        y_escala = y_titulo - 36.8
        x_escala = x_titulo + 9.5
        dwg.draw.level = 250
        dwg.draw.Text(x_escala, y_escala, 22.5, 0.0, f"ESCALA 1:{escala}")

        raio_cruz = 18.0

        for p in pilares:
            geom = p.geometria
            cg = p.baricentro
            vts = geom.vertices_poligono

            # 1. Contorno do Pilar (Polilinha fechada de N vértices - Nível 3)
            dwg.draw.level = 3
            if vts and len(vts) >= 3:
                dwg.draw.PolyStart()
                for vx, vy in vts:
                    dwg.draw.PolyEnterPoint(vx, vy)
                dwg.draw.PolyEnterPoint(vts[0][0], vts[0][1])
                dwg.draw.Polyline()
            else:
                w = geom.b if geom.b > 0 else 20.0
                h = geom.h if geom.h > 0 else 20.0
                x0 = cg.x - w / 2.0
                y0 = cg.y - h / 2.0
                dwg.draw.PolyStart()
                dwg.draw.PolyEnterPoint(x0, y0)
                dwg.draw.PolyEnterPoint(x0 + w, y0)
                dwg.draw.PolyEnterPoint(x0 + w, y0 + h)
                dwg.draw.PolyEnterPoint(x0, y0 + h)
                dwg.draw.PolyEnterPoint(x0, y0)
                dwg.draw.Polyline()

            # 2. Baricentro - Ponto de Carga (Cruz no Nível 21)
            dwg.draw.level = 21
            dwg.draw.Line(cg.x - raio_cruz, cg.y, cg.x + raio_cruz, cg.y)
            dwg.draw.Line(cg.x, cg.y - raio_cruz, cg.x, cg.y + raio_cruz)
            dwg.draw.Circle(cg.x, cg.y, 3.0)

            # 3. Rótulo inteligente: Nome no Nível 9 e Dimensão no Nível 12 embaixo
            xn, yn, xd, yd = self._calcular_posicao_rotulo_pilar(p, pilares)

            dwg.draw.level = 9
            dwg.draw.Text(xn, yn, 18.0, 0.0, p.nome)

            dwg.draw.level = 12
            dim_str = f"{int(round(geom.b))}x{int(round(geom.h))}"
            dwg.draw.Text(xd, yd, 13.5, 0.0, dim_str)

    def _desenhar_tabela_baricentros(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        x_start: float,
        y_start: float,
    ) -> Tuple[float, float]:
        """
        Desenha a tabela de baricentros auto-dimensionada em N blocos paralelos.
        Retorna (y_fim, largura_total).
        """
        n_total = len(pilares)
        # Calcula número de colunas dinamicamente (máximo de 25 linhas por coluna)
        num_colunas = max(1, math.ceil(n_total / 25))
        linhas_por_coluna = math.ceil(n_total / num_colunas)

        largura_col_pilar = 110.0
        largura_col_coord = 140.0
        largura_bloco = largura_col_pilar + 2 * largura_col_coord # 390 cm
        espaco_entre_blocos = 45.0
        h_linha = 26.0
        h_cabecalho = 30.0

        largura_total = num_colunas * largura_bloco + (num_colunas - 1) * espaco_entre_blocos

        dwg.draw.level = 0
        dwg.draw.Text(x_start + (largura_total / 2.0) - 100.0, y_start + 45.0, 16.0, 0.0, "BARICENTRO DE PILARES")
        dwg.draw.Text(x_start + (largura_total / 2.0) - 110.0, y_start + 25.0, 14.0, 0.0, "(ORDENADO POR PILARES)")

        for col_idx in range(num_colunas):
            sub_pilares = pilares[col_idx * linhas_por_coluna : (col_idx + 1) * linhas_por_coluna]
            if not sub_pilares:
                continue

            bx0 = x_start + col_idx * (largura_bloco + espaco_entre_blocos)
            by0 = y_start

            dwg.draw.level = 0
            dwg.draw.Line(bx0, by0, bx0 + largura_bloco, by0)
            dwg.draw.Line(bx0, by0 - h_cabecalho, bx0 + largura_bloco, by0 - h_cabecalho)
            
            dwg.draw.Text(bx0 + 25.0, by0 - 21.0, 14.0, 0.0, "PILAR")
            dwg.draw.Text(bx0 + largura_col_pilar + 35.0, by0 - 21.0, 14.0, 0.0, "X (cm)")
            dwg.draw.Text(bx0 + largura_col_pilar + largura_col_coord + 35.0, by0 - 21.0, 14.0, 0.0, "Y (cm)")

            altura_tabela = h_cabecalho + len(sub_pilares) * h_linha
            dwg.draw.Line(bx0, by0, bx0, by0 - altura_tabela)
            dwg.draw.Line(bx0 + largura_col_pilar, by0, bx0 + largura_col_pilar, by0 - altura_tabela)
            dwg.draw.Line(bx0 + largura_col_pilar + largura_col_coord, by0, bx0 + largura_col_pilar + largura_col_coord, by0 - altura_tabela)
            dwg.draw.Line(bx0 + largura_bloco, by0, bx0 + largura_bloco, by0 - altura_tabela)

            curr_y = by0 - h_cabecalho
            for p in sub_pilares:
                curr_y -= h_linha
                dwg.draw.Line(bx0, curr_y, bx0 + largura_bloco, curr_y)

                dwg.draw.Text(bx0 + 25.0, curr_y + 7.0, 14.0, 0.0, p.nome)
                dwg.draw.Text(bx0 + largura_col_pilar + 30.0, curr_y + 7.0, 14.0, 0.0, f"{p.baricentro.x:.1f}")
                dwg.draw.Text(bx0 + largura_col_pilar + largura_col_coord + 30.0, curr_y + 7.0, 14.0, 0.0, f"{p.baricentro.y:.1f}")

        y_fim = y_start - (h_cabecalho + linhas_por_coluna * h_linha)
        return y_fim, largura_total

    def _desenhar_tabela_cargas(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        x_start: float,
        y_start: float,
        dados_porlid: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float]:
        """
        Desenha a tabela de cargas nas fundações idêntica ao relatório oficial do TQS (PORLID),
        com os 7 campos oficiais: Elem/Pilar, Fz, Fx, Fy, Mx, My, Mz e suas respectivas unidades (tf, tfm).
        Suporta universalmente:
          - Múltiplos casos (ex: Jardim Europa com 6 casos: FZ MAX, MX MAX, MY MAX, FZ MIN, MX MIN, MY MIN)
            desenhados lado a lado em blocos harmoniosos, exatamente como no GEO_CARGAS.DWG oficial.
          - Caso único (ex: Visconde do Herval 054), auto-dimensionado em 2 colunas para otimizar espaço.
        Retorna (y_fim, largura_total).
        """
        # -----------------------------------------------------------------
        # RAMIFICAÇÃO 1: MÚLTIPLOS CASOS DE CARGA (Conforme PORLID oficial)
        # -----------------------------------------------------------------
        if dados_porlid and dados_porlid.get("casos") and len(dados_porlid["casos"]) > 1:
            casos = dados_porlid["casos"]
            num_casos = len(casos)
            colunas = ["PILAR", "Fz", "Fx", "Fy", "Mx", "My", "Mz"]
            unidades = ["", "tf", "tf", "tf", "tfm", "tfm", "tfm"]

            # Cada bloco de caso tem 7 colunas (Pilar + 6 componentes de esforços)
            larguras = [75.0, 75.0, 70.0, 70.0, 75.0, 75.0, 75.0]  # Total por bloco = 515.0 cm
            largura_bloco = sum(larguras)
            espaco_entre_casos = 35.0
            h_linha = 22.0
            h_cabecalho = 38.0

            largura_total = num_casos * largura_bloco + (num_casos - 1) * espaco_entre_casos

            # Título Geral da Tabela de Cargas
            y_titulo = y_start
            dwg.draw.level = 250
            dwg.draw.Text(x_start + (largura_total / 2.0) - 200.0, y_titulo, 20.0, 0.0, "TABELA DE CARGAS NAS FUNDAÇÕES")

            # Subtítulo Geral
            y_subtitulo = y_titulo - 26.0
            dwg.draw.level = 0
            dwg.draw.Text(
                x_start + max(10.0, (largura_total / 2.0) - 260.0),
                y_subtitulo,
                13.5,
                0.0,
                "TABELA DE ESFORÇOS CARACTERÍSTICOS POR CASO CRÍTICO (TQS ESPACIAL)",
            )

            y_grid_topo = y_subtitulo - 30.0

            max_linhas = 0
            for k, caso in enumerate(casos):
                bx0 = x_start + k * (largura_bloco + espaco_entre_casos)
                by0 = y_grid_topo
                linhas_caso = caso.get("linhas", [])
                max_linhas = max(max_linhas, len(linhas_caso))

                # Nome do Caso (ex: 'CASO 1 - FZ MAX') acima da grade de cada bloco
                dwg.draw.level = 222
                nome_caso = caso.get("nome", f"CASO {k+1}")
                dwg.draw.Text(bx0 + 10.0, by0 + 10.0, 14.0, 0.0, nome_caso)

                dwg.draw.level = 0
                # Linha superior do cabeçalho
                dwg.draw.Line(bx0, by0, bx0 + largura_bloco, by0)
                # Linha intermediária (separa grandezas de unidades nas colunas de esforços)
                dwg.draw.Line(bx0 + larguras[0], by0 - 20.0, bx0 + largura_bloco, by0 - 20.0)
                # Linha inferior do cabeçalho
                dwg.draw.Line(bx0, by0 - h_cabecalho, bx0 + largura_bloco, by0 - h_cabecalho)

                # Textos do cabeçalho
                dwg.draw.Text(bx0 + 15.0, by0 - 24.0, 12.5, 0.0, colunas[0])
                ox = larguras[0]
                for w, tit, un in zip(larguras[1:], colunas[1:], unidades[1:]):
                    dwg.draw.Text(bx0 + ox + (w / 2.0) - 10.0, by0 - 15.0, 12.0, 0.0, tit)
                    dwg.draw.Text(bx0 + ox + (w / 2.0) - 12.0, by0 - 32.0, 11.0, 0.0, un)
                    ox += w

                # Linhas verticais do bloco
                altura_tabela = h_cabecalho + len(linhas_caso) * h_linha
                dwg.draw.Line(bx0, by0, bx0, by0 - altura_tabela)
                cx = bx0
                for w in larguras:
                    cx += w
                    dwg.draw.Line(cx, by0, cx, by0 - altura_tabela)

                # Linhas de dados de cada elemento
                curr_y = by0 - h_cabecalho
                for row in linhas_caso:
                    curr_y -= h_linha
                    dwg.draw.Line(bx0, curr_y, bx0 + largura_bloco, curr_y)

                    # Coluna Pilar / Elem
                    dwg.draw.Text(bx0 + 15.0, curr_y + 6.0, 12.0, 0.0, str(row[0]))

                    # Colunas de Esforços Fz, Fx, Fy, Mx, My, Mz
                    ox = larguras[0]
                    for w, val in zip(larguras[1:], row[1:]):
                        val_str = str(val).strip()
                        text_offset = max(8.0, (w / 2.0) - (len(val_str) * 3.5))
                        dwg.draw.Text(bx0 + ox + text_offset, curr_y + 6.0, 12.0, 0.0, val_str)
                        ox += w

            y_fim = y_grid_topo - (h_cabecalho + max_linhas * h_linha)
            return y_fim, largura_total

        # -----------------------------------------------------------------
        # RAMIFICAÇÃO 2: CASO ÚNICO OU FALLBACK (Auto-diagramado em 2 colunas)
        # -----------------------------------------------------------------
        if dados_porlid and dados_porlid.get("linhas"):
            titulo_comb = dados_porlid.get("titulo", "FZ MAX-ELU2-Verificações de estado limite último - Pilares e fundações")
            linhas = dados_porlid["linhas"]
            colunas = dados_porlid.get("colunas", ["Elem", "Fz", "Fx", "Fy", "Mx", "My", "Mz"])
            unidades = dados_porlid.get("unidades", ["", "tf", "tf", "tf", "tfm", "tfm", "tfm"])
        else:
            titulo_comb = "CASO 1 - FZ MÁXIMO (PÓRTICO ESPACIAL)"
            colunas = ["Elem", "Fz", "Fx", "Fy", "Mx", "My", "Mz"]
            unidades = ["", "tf", "tf", "tf", "tfm", "tfm", "tfm"]
            linhas = []
            for p in pilares:
                esf = p.esforcos
                linhas.append([
                    p.nome,
                    f"{esf.nk_max:.1f}" if esf else "0.0",
                    f"{esf.hx:.1f}" if esf else "0.0",
                    f"{esf.hy:.1f}" if esf else "0.0",
                    f"{esf.mxk:.2f}" if esf else "0.00",
                    f"{esf.myk:.2f}" if esf else "0.00",
                    f"{esf.mz:.2f}" if esf else "0.00",
                ])

        n_total = len(linhas)
        num_colunas = max(1, math.ceil(n_total / 30))
        linhas_por_coluna = math.ceil(n_total / num_colunas)

        larguras = [85.0, 85.0, 80.0, 80.0, 85.0, 85.0, 85.0]  # Total por bloco = 585.0 cm
        largura_bloco = sum(larguras)
        espaco_entre_blocos = 50.0
        h_linha = 22.0
        h_cabecalho = 38.0

        largura_total = num_colunas * largura_bloco + (num_colunas - 1) * espaco_entre_blocos

        # Título Geral da Tabela de Cargas (com espaçamento seguro abaixo da tabela superior)
        y_titulo = y_start
        dwg.draw.level = 250
        dwg.draw.Text(x_start + (largura_total / 2.0) - 200.0, y_titulo, 18.0, 0.0, "TABELA DE CARGAS NAS FUNDAÇÕES")

        # Subtítulo (Combinação crítica oficial do TQS)
        y_subtitulo = y_titulo - 28.0
        dwg.draw.level = 0
        tam_fonte_sub = 13.0 if len(titulo_comb) > 40 else 15.0
        dwg.draw.Text(x_start + max(10.0, (largura_total / 2.0) - (len(titulo_comb) * 3.8)), y_subtitulo, tam_fonte_sub, 0.0, titulo_comb)

        # O grid da tabela inicia abaixo do subtítulo
        y_grid_topo = y_subtitulo - 30.0

        for col_idx in range(num_colunas):
            sub_linhas = linhas[col_idx * linhas_por_coluna : (col_idx + 1) * linhas_por_coluna]
            if not sub_linhas:
                continue

            bx0 = x_start + col_idx * (largura_bloco + espaco_entre_blocos)
            by0 = y_grid_topo

            dwg.draw.level = 0
            # Linha superior do cabeçalho
            dwg.draw.Line(bx0, by0, bx0 + largura_bloco, by0)
            # Linha intermediária (separa grandezas de unidades nas colunas de esforços)
            dwg.draw.Line(bx0 + larguras[0], by0 - 20.0, bx0 + largura_bloco, by0 - 20.0)
            # Linha inferior do cabeçalho
            dwg.draw.Line(bx0, by0 - h_cabecalho, bx0 + largura_bloco, by0 - h_cabecalho)

            # Textos do cabeçalho
            dwg.draw.Text(bx0 + 20.0, by0 - 24.0, 13.0, 0.0, colunas[0])
            ox = larguras[0]
            for w, tit, un in zip(larguras[1:], colunas[1:], unidades[1:]):
                dwg.draw.Text(bx0 + ox + (w / 2.0) - 10.0, by0 - 15.0, 12.5, 0.0, tit)
                dwg.draw.Text(bx0 + ox + (w / 2.0) - 12.0, by0 - 32.0, 11.5, 0.0, un)
                ox += w

            # Linhas verticais do bloco
            altura_tabela = h_cabecalho + len(sub_linhas) * h_linha
            dwg.draw.Line(bx0, by0, bx0, by0 - altura_tabela)
            cx = bx0
            for w in larguras:
                cx += w
                dwg.draw.Line(cx, by0, cx, by0 - altura_tabela)

            # Linhas de dados
            curr_y = by0 - h_cabecalho
            for row in sub_linhas:
                curr_y -= h_linha
                dwg.draw.Line(bx0, curr_y, bx0 + largura_bloco, curr_y)

                # Coluna Elem
                dwg.draw.Text(bx0 + 15.0, curr_y + 6.0, 12.5, 0.0, str(row[0]))

                # Colunas de Esforços Fz, Fx, Fy, Mx, My, Mz
                ox = larguras[0]
                for w, val in zip(larguras[1:], row[1:]):
                    val_str = str(val).strip()
                    text_offset = max(10.0, (w / 2.0) - (len(val_str) * 3.5))
                    dwg.draw.Text(bx0 + ox + text_offset, curr_y + 6.0, 12.5, 0.0, val_str)
                    ox += w

        y_fim = y_grid_topo - (h_cabecalho + linhas_por_coluna * h_linha)
        return y_fim, largura_total

    def _desenhar_notas_e_legendas(
        self,
        dwg: TQSDwg.Dwg,
        x_start: float,
        y_start: float,
        dados_porlid: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Desenha os 3 blocos informativos rigorosamente iguais ao modelo GEO_CARGAS do Zuckhan Soledade:
          1. OBSERVAÇÕES (variável conforme os casos críticos de carregamento do edifício)
          2. CONVENÇÃO DE SINAIS (esquema isométrico 3D com eixos e esforços)
          3. INCIDÊNCIA DAS CARGAS DE VENTO (retângulo do edifício com setas direcionais a 0°, 90°, 180°, 270°)
        Retorna o Y mínimo (inferior) ocupado pelos blocos.
        """
        # =========================================================================
        # BLOCO 1: OBSERVAÇÕES (Alinhado à esquerda: x_start, y_start)
        # =========================================================================
        dwg.draw.level = 250
        dwg.draw.Text(x_start, y_start, 20.0, 0.0, "OBSERVAÇÕES:")
        dwg.draw.Line(x_start, y_start - 11.26, x_start + 218.66, y_start - 11.26)

        curr_y = y_start - 56.27
        dy_linha = 25.01

        # Linhas de cabeçalho fixas
        dwg.draw.level = 250
        dwg.draw.Text(x_start, curr_y, 15.0, 0.0, "- Esforços com valores característicos.")
        curr_y -= dy_linha

        dwg.draw.level = 0
        dwg.draw.Text(
            x_start,
            curr_y,
            15.0,
            0.0,
            "- Forças em tonelada-força (tf) e momentos fletores em tonelada-força metro (tf.m).",
        )
        curr_y -= dy_linha

        # Linhas dinâmicas de combinações críticas extraídas de PORLID
        casos = dados_porlid.get("casos", []) if dados_porlid else []
        if casos:
            for idx, c in enumerate(casos):
                cid = c.get("id", idx + 1)
                nome_upper = c.get("nome", "").upper()
                tit_upper = c.get("titulo", "").upper()
                combined = f"{nome_upper} {tit_upper}"

                if "FZ MAX" in combined or ("FZ" in combined and "MAX" in combined):
                    desc = "combinação dos carregamentos que produz a máxima força vertical Fz em cada pilar"
                elif "MX MAX" in combined:
                    desc = "combinação dos carregamentos que produz o máximo momento fletor Mx, na direção positiva do eixo x, em cada pilar"
                elif "MY MAX" in combined:
                    desc = "combinação dos carregamentos que produz o máximo momento fletor My, na direção positiva do eixo y, em cada pilar"
                elif "FZ MIN" in combined or ("FZ" in combined and "MIN" in combined):
                    desc = "combinação dos carregamentos que produz a mínima força vertical Fz em cada pilar"
                elif "MX MIN" in combined:
                    desc = "combinação dos carregamentos que produz o máximo momento fletor Mx, na direção negativa do eixo x, em cada pilar"
                elif "MY MIN" in combined:
                    desc = "combinação dos carregamentos que produz o máximo momento fletor My, na direção negativa do eixo y, em cada pilar"
                else:
                    desc = f"combinação dos carregamentos: {c.get('titulo') or c.get('nome')}"

                dwg.draw.level = 0
                dwg.draw.Text(x_start, curr_y, 15.0, 0.0, f"- Caso {cid}: {desc}")
                curr_y -= dy_linha

                dwg.draw.Text(
                    x_start,
                    curr_y,
                    15.0,
                    0.0,
                    "   (incluindo a ação do vento e empuxo do solo, se houver).",
                )
                curr_y -= dy_linha
        else:
            # Fallback caso clássico padrão caso não haja PORLID detalhado
            dwg.draw.level = 0
            dwg.draw.Text(
                x_start,
                curr_y,
                15.0,
                0.0,
                "- Caso 1: combinação dos carregamentos que produz a máxima força vertical Fz em cada pilar",
            )
            curr_y -= dy_linha
            dwg.draw.Text(
                x_start,
                curr_y,
                15.0,
                0.0,
                "   (incluindo a ação do vento e empuxo do solo, se houver).",
            )
            curr_y -= dy_linha

        # Linhas de rodapé fixas
        dwg.draw.level = 0
        dwg.draw.Text(
            x_start,
            curr_y,
            15.0,
            0.0,
            "- A escolha da combinação de carregamentos para elaboração do projeto de fundações é de inteira responsabilidade do",
        )
        curr_y -= dy_linha
        dwg.draw.Text(x_start, curr_y, 15.0, 0.0, "   projetista de fundações.")
        curr_y -= dy_linha

        dwg.draw.level = 250
        dwg.draw.Text(
            x_start,
            curr_y,
            15.0,
            0.0,
            "- As cargas distribuídas nas estruturas de contenção, quando existirem, compreendem as reações dos pavimentos nessas",
        )
        curr_y -= dy_linha
        dwg.draw.Text(
            x_start,
            curr_y,
            15.0,
            0.0,
            "   estruturas. Não está incluído o peso próprio das mesmas.",
        )
        curr_y -= dy_linha

        y_fim_obs = curr_y

        # =========================================================================
        # CARREGAMENTO DOS BLOCOS 2 E 3 (GEO_CARGAS do Zuckhan Soledade)
        # =========================================================================
        caminho_blocos = os.path.join(os.path.dirname(__file__), "blocos_informativos_soledade.json")
        if os.path.exists(caminho_blocos):
            with open(caminho_blocos, "r", encoding="utf-8") as f:
                blocos_data = json.load(f)

            # BLOCO 2: CONVENÇÃO DE SINAIS (ΔX = +1436.25 cm, ΔY = 0.00 cm)
            x_conv = x_start + 1436.25
            y_conv = y_start
            for e in blocos_data.get("convencao", []):
                etype = e.get("type")
                dwg.draw.level = e.get("level", 0)
                if etype == "line":
                    dwg.draw.Line(
                        x_conv + e["dx1"],
                        y_conv + e["dy1"],
                        x_conv + e["dx2"],
                        y_conv + e["dy2"],
                    )
                elif etype == "text":
                    dwg.draw.Text(
                        x_conv + e["dx"],
                        y_conv + e["dy"],
                        e["height"],
                        e.get("angle", 0.0),
                        e["text"],
                    )
                elif etype == "poly":
                    pts = e.get("pts", [])
                    if len(pts) >= 2:
                        dwg.draw.PolyStart()
                        for pt in pts:
                            dwg.draw.PolyEnterPoint(x_conv + pt[0], y_conv + pt[1])
                        dwg.draw.Polyline()

            # BLOCO 3: INCIDÊNCIA DAS CARGAS DE VENTO (ΔX = +2178.19 cm, ΔY = +1.68 cm)
            x_vento = x_start + 2178.19
            y_vento = y_start + 1.68
            for e in blocos_data.get("vento", []):
                etype = e.get("type")
                dwg.draw.level = e.get("level", 0)
                if etype == "line":
                    dwg.draw.Line(
                        x_vento + e["dx1"],
                        y_vento + e["dy1"],
                        x_vento + e["dx2"],
                        y_vento + e["dy2"],
                    )
                elif etype == "text":
                    dwg.draw.Text(
                        x_vento + e["dx"],
                        y_vento + e["dy"],
                        e["height"],
                        e.get("angle", 0.0),
                        e["text"],
                    )
                elif etype == "poly":
                    pts = e.get("pts", [])
                    if len(pts) >= 2:
                        dwg.draw.PolyStart()
                        for pt in pts:
                            dwg.draw.PolyEnterPoint(x_vento + pt[0], y_vento + pt[1])
                        dwg.draw.Polyline()

            # BLOCO 4: CONVENÇÕES (Simbologia dos Pilares, Contenções, Ponto de Carga e Origem 0,0)
            # Posicionado abaixo das Observações e Convenção de Sinais
            y_conv_loc = min(y_fim_obs, y_start - 560.0) - 70.0
            x_conv_loc = x_start
            for e in blocos_data.get("convencoes_locacao", []):
                etype = e.get("type")
                dwg.draw.level = e.get("level", 0)
                if "color" in e:
                    dwg.draw.color = e["color"]
                if etype == "line":
                    dwg.draw.Line(
                        x_conv_loc + e["dx1"],
                        y_conv_loc + e["dy1"],
                        x_conv_loc + e["dx2"],
                        y_conv_loc + e["dy2"],
                    )
                elif etype == "text":
                    dwg.draw.Text(
                        x_conv_loc + e["dx"],
                        y_conv_loc + e["dy"],
                        e["height"],
                        e.get("angle", 0.0),
                        e["text"],
                    )
                elif etype == "poly":
                    pts = e.get("pts", [])
                    if len(pts) >= 2:
                        dwg.draw.PolyStart()
                        for pt in pts:
                            dwg.draw.PolyEnterPoint(x_conv_loc + pt[0], y_conv_loc + pt[1])
                        dwg.draw.Polyline()
                elif etype == "circle":
                    dwg.draw.Circle(
                        x_conv_loc + e["dxc"],
                        y_conv_loc + e["dyc"],
                        e["radius"],
                    )

            # Restaura cor padrão ByLevel
            dwg.draw.color = 0
            y_fim = y_conv_loc - 495.0
            return y_fim

        # O Y inferior ocupado é o menor entre as observações e a convenção de sinais (-555 cm)
        y_fim = min(y_fim_obs, y_start - 560.0)
        return y_fim

    def _auto_selecionar_e_desenhar_moldura(
        self,
        dwg: TQSDwg.Dwg,
        bounds_conteudo: Tuple[float, float, float, float],
        escala_inicial: int = 50,
        planta: Optional[PlantaDeCargasModel] = None,
    ) -> Tuple[str, int]:
        r"""
        Algoritmo inteligente de seleção da menor moldura catalogada OFICIAL do TQS
        (armazenadas em D:\TQSW\SUPORTE\NGE\MOLDURAS) que enquadre perfeitamente
        todo o conteúdo do desenho com as margens ABNT/TQS.
        Carrega e insere o bloco nativo .DWG oficial do TQS.
        """
        min_x, max_x, min_y, max_y = bounds_conteudo
        larg_desenho = max_x - min_x
        alt_desenho = max_y - min_y

        escala = escala_inicial
        formato_selecionado = None
        dim_papel = None

        # Testa as escalas 1:50, 1:75 ou 1:100 caso o edifício seja colossal
        for esc in [escala_inicial, 75, 100]:
            # Margem esquerda ABNT: 2.5 cm no papel | Demais margens: 1.0 cm
            folga_larg = (2.5 + 1.0 + 4.0) * esc # Margens + folga de respiro
            folga_alt = (1.0 + 1.0 + 4.0) * esc

            larg_min_papel = (larg_desenho + folga_larg) / esc
            alt_min_papel = (alt_desenho + folga_alt) / esc

            # Encontra todas as molduras catalogadas oficiais que atendem
            candidatos = []
            for nome, wp, hp in CATALOGO_MOLDURAS_TQS:
                if wp >= larg_min_papel and hp >= alt_min_papel:
                    candidatos.append((nome, wp, hp, wp * hp))

            if candidatos:
                # Escolhe a menor folha oficial por consumo de papel (área mínima)
                candidatos.sort(key=lambda c: c[3])
                formato_selecionado = candidatos[0][0]
                dim_papel = (candidatos[0][1], candidatos[0][2])
                escala = esc
                break

        # Fallback de segurança estritamente para o maior formato padrão oficial do TQS (180-85)
        if not formato_selecionado:
            formato_selecionado = "180-85"
            dim_papel = (180.0, 84.1)

        wp, hp = dim_papel
        w_proj = wp * escala
        h_proj = hp * escala

        # Centraliza o conteúdo útil da prancha dentro das margens da moldura
        cx_conteudo = (min_x + max_x) / 2.0
        cy_conteudo = (min_y + max_y) / 2.0

        # Margem esquerda da folha é 2.5cm e direita é 1.0cm -> centro útil do papel em X é (wp + 1.5)/2
        cx_papel_util = (wp + 1.5) / 2.0
        cy_papel_util = hp / 2.0

        x0 = cx_conteudo - (cx_papel_util * escala)
        y0 = cy_conteudo - (cy_papel_util * escala)
        x1 = x0 + w_proj
        y1 = y0 + h_proj

        # Carrega e insere a moldura oficial do TQS diretamente da pasta SUPORTE/NGE/MOLDURAS
        from src.tqs_adapter.tqs_env import PASTA_SUPORTE
        pasta_molduras = os.path.join(PASTA_SUPORTE, "NGE", "MOLDURAS") if PASTA_SUPORTE else ""
        if not os.path.exists(pasta_molduras):
            for drive in ["C", "D", "E", "F"]:
                cand_mold = fr"{drive}:\TQSW\SUPORTE\NGE\MOLDURAS"
                if os.path.exists(cand_mold):
                    pasta_molduras = cand_mold
                    break
        caminho_moldura = os.path.join(pasta_molduras, f"{formato_selecionado}.DWG") if pasta_molduras else ""
        bloco_inserido = False

        if os.path.exists(caminho_moldura):
            try:
                dwg.draw.BlockLoadFromDwg(caminho_moldura)
                dwg.draw.BlockInsert(formato_selecionado, x0, y0, float(escala), float(escala), 0.0)
                bloco_inserido = True
            except Exception:
                bloco_inserido = False

        if not bloco_inserido:
            # Fallback gráfico caso a pasta de suporte do TQS não esteja disponível
            dwg.draw.level = 18
            dwg.draw.Line(x0, y0, x1, y0)
            dwg.draw.Line(x1, y0, x1, y1)
            dwg.draw.Line(x1, y1, x0, y1)
            dwg.draw.Line(x0, y1, x0, y0)

            # Margem interna útil ABNT / TQS
            mx0 = x0 + 2.5 * escala
            my0 = y0 + 1.0 * escala
            mx1 = x1 - 1.0 * escala
            my1 = y1 - 1.0 * escala

            dwg.draw.level = 32
            dwg.draw.Line(mx0, my0, mx1, my0)
            dwg.draw.Line(mx1, my0, mx1, my1)
            dwg.draw.Line(mx1, my1, mx0, my1)
            dwg.draw.Line(mx0, my1, mx0, my0)

            # Área reservada para o Selo / Carimbo TQS no canto inferior direito
            larg_selo = 17.5 * escala
            alt_selo = 15.0 * escala
            sx0 = mx1 - larg_selo
            sy0 = my0
            sx1 = mx1
            sy1 = my0 + alt_selo

            dwg.draw.level = 0
            dwg.draw.Line(sx0, sy0, sx0, sy1)
            dwg.draw.Line(sx0, sy1, sx1, sy1)

            dwg.draw.Text(sx0 + 40.0, sy1 - 50.0, 18.0, 0.0, "ÁREA RESERVADA PARA O SELO / CARIMBO TQS")
            dwg.draw.Text(sx0 + 40.0, sy1 - 85.0, 14.0, 0.0, f"MOLDURA OFICIAL TQS: {formato_selecionado} ({wp:.1f} x {hp:.1f} cm)")
            dwg.draw.Text(sx0 + 40.0, sy1 - 115.0, 14.0, 0.0, f"ESCALA 1:{escala} | RESERVADO PARA MONTAGEM DE PRANCHAS")

            # Marcas de centro / dobra da folha
            cx = (x0 + x1) / 2.0
            cy = (y0 + y1) / 2.0
            dwg.draw.Line(cx, y1 - 25.0, cx, y1 + 25.0)
            dwg.draw.Line(cx, y0 - 25.0, cx, y0 + 25.0)
            dwg.draw.Line(x0 - 25.0, cy, x0 + 25.0, cy)
            dwg.draw.Line(x1 - 25.0, cy, x1 + 25.0, cy)

        # Informações complementares de identificação no carimbo oficial TQS
        fator_esc = escala / 50.0
        sx_carimbo = x0 + (wp - 18.2) * escala
        sy_carimbo = y0 + 1.0 * escala
        nome_obra = planta.edificio_nome if planta else "PROJETO ESTRUTURAL"

        dwg.draw.level = 18
        # Título da prancha sobre o selo
        dwg.draw.Text(sx_carimbo + 30.0 * fator_esc, sy_carimbo + 5.2 * escala, 12.0 * fator_esc, 0.0, "PLANTA DE CARGAS E LOCAÇÃO")
        dwg.draw.Text(sx_carimbo + 30.0 * fator_esc, sy_carimbo + 4.4 * escala, 10.0 * fator_esc, 0.0, "FUNDAÇÕES")
        # Escala da prancha
        dwg.draw.Text(sx_carimbo + 137.0 * fator_esc, sy_carimbo + 1.1 * escala, 11.0 * fator_esc, 0.0, f"1:{escala}")

        # Título identificador no topo da folha
        dwg.draw.level = 0
        mx0_proj = x0 + 2.5 * escala
        my1_proj = y1 - 1.0 * escala
        dwg.draw.Text(
            mx0_proj + 40.0,
            my1_proj + 15.0,
            16.0,
            0.0,
            f"MOLDURA PADRÃO TQS: FORMATO {formato_selecionado} ({int(wp*10)} x {int(hp*10)} mm)  |  ESCALA 1:{escala}",
        )

        return formato_selecionado, escala
