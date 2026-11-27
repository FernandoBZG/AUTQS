import os
import ctypes
import json
import math
from typing import List, Optional, Tuple, Dict, Any
from TQS import TQSDwg
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
from src.core.models import PlantaDeCargasModel, PilarFundacao

# Garante ambiente TQS 64-bit configurado
configurar_ambiente_tqs_64()

def _corrigir_tqs_draw_level():
    """
    Garante que dwg.draw.level utilize g_desniv para níveis numéricos (0..255),
    evitando que g_desnivalfa falhe e descarte os elementos para o nível 0.
    """
    try:
        def _set_dwg_level(self, level):
            parpedmv = ctypes.c_void_p(self.m_dwg.m_pedmv)
            try:
                parnivel = ctypes.c_int(int(level))
                self.m_dwg.m_mdwg.g_desniv(parpedmv, ctypes.byref(parnivel))
            except (ValueError, TypeError):
                parlevel = ctypes.c_char_p(str(level).encode('latin1'))
                nivel = ctypes.c_int(0)
                self.m_dwg.m_mdwg.g_desnivalfa(parpedmv, parlevel, ctypes.byref(nivel))

        TQSDwg.Draw.level = property(TQSDwg.Draw.level.fget, _set_dwg_level)
    except Exception:
        pass

_corrigir_tqs_draw_level()

# Área do selo nas molduras oficiais do TQS (C:\TQSW\SUPORTE\NGE\MOLDURAS, A0-45, A1, 180-50...):
# largura de 17.5 cm encostada na margem direita; altura da margem inferior (y=1.0) até o topo
# da tabela de revisões (y=29.7, Nível 221), ou seja, carimbo + tabela de revisões = 28.7 cm.
SELO_LARGURA_CM = 17.5
SELO_ALTURA_CM = 28.7

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

        # Conexão com MDWG.DLL e IPOCOTREL.dll para emissão de cotas relativas nativas do TQS
        self._mdwg_dll = None
        for dll_cand in [
            r"C:\TQSW\EXEC\X64\MDWG.DLL",
            r"C:\TQSW\EXEC\MDWG.DLL",
            r"D:\TQSW\EXEC\X64\MDWG.DLL",
            r"D:\TQSW\EXEC\MDWG.DLL",
        ]:
            if os.path.exists(dll_cand):
                try:
                    self._mdwg_dll = ctypes.CDLL(dll_cand)
                    self._mdwg_dll.g_edmexdefcotrel.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double]
                    break
                except Exception:
                    pass

        self._ipo_dll = None
        for dll_cand in [
            r"C:\TQSW\EXEC\X64\IPOCOTREL.dll",
            r"C:\TQSW\EXEC\IPOCOTREL.dll",
            r"D:\TQSW\EXEC\X64\IPOCOTREL.dll",
            r"D:\TQSW\EXEC\IPOCOTREL.dll",
        ]:
            if os.path.exists(dll_cand):
                try:
                    self._ipo_dll = ctypes.CDLL(dll_cand)
                    break
                except Exception:
                    pass

    @staticmethod
    def _assegurar_cotrel_normativo(pasta_execucao: str = ""):
        """
        Garante que o arquivo de critérios de cotas relativas (COTREL.DAT)
        utilize a altura mínima normativa de 0.20 cm no papel (2.0 mm),
        evitando que o IPOCOTREL.dll gere cotas com altura inferior.
        """
        conteudo_cotrel = (
            "    0.2000\tAltura de texto em cm\n"
            "    0.3000\tAltura do bloco em cm\n"
            "         0\t(0) Direita (1) Esquerda\n"
            "         0\t(0) em cima (1) em baixo\n"
            "         0\t(1) valores em modulo\n"
            "        21\tNivel de desenho\n"
            "       100\tNivel invisivel\n"
            "$COTREL\n"
            "         1\tCasas depois da virgula\n"
            "    1.0000\tMultiplic dimensoes\n"
        )
        caminhos = ["COTREL.DAT"]
        if pasta_execucao and os.path.isdir(pasta_execucao):
            caminhos.append(os.path.join(pasta_execucao, "COTREL.DAT"))
        from src.core.backup import criar_backup
        for c in caminhos:
            try:
                if os.path.isfile(c):
                    with open(c, "r", encoding="latin-1") as f:
                        if f.read() == conteudo_cotrel:
                            continue  # já está no padrão: não regrava
                    criar_backup(c)  # preserva os critérios atuais em backup_claude
                with open(c, "w", encoding="latin-1") as f:
                    f.write(conteudo_cotrel)
            except Exception as e:
                print(f"[AVISO] Não foi possível ajustar {c}: {e}")

    def construir_planta_de_cargas(
        self,
        planta: PlantaDeCargasModel,
        arquivo_saida_dwg: str,
        escala: Optional[int] = None,
        origem_cotas: Optional[Tuple[float, float]] = None,
    ) -> str:
        """
        Gera a folha .DWG nativa do TQS adaptada automaticamente a qualquer edifício.
        Garante que a escala do arquivo (dwg.settings.scale) corresponda exatamente à
        escala dos elementos desenhados e que todos os textos tenham altura >= 0.20 cm no papel.
        """
        if not planta.pilares:
            raise ValueError(f"Edifício {planta.edificio_nome} não possui pilares de fundação carregados.")

        # Garante critério de cotas relativas normativo (h >= 0.20 cm no papel)
        pasta_ed = planta.caminho_edificio or os.path.dirname(arquivo_saida_dwg)
        self._assegurar_cotrel_normativo(pasta_ed)

        # 1. Análise Geométrica Dinâmica do Edifício
        bounds_planta = self._calcular_bounding_box_pilares(planta.pilares)
        min_xp, max_xp, min_yp, max_yp = bounds_planta
        larg_locacao = max_xp - min_xp
        alt_locacao = max_yp - min_yp

        dados_porlid = planta.dados_porlid
        num_casos = len(dados_porlid.get("casos", [])) if dados_porlid and dados_porlid.get("casos") else (dados_porlid.get("num_casos", 1) if dados_porlid else 1)
        num_pilares = len(planta.pilares)

        # 2. Definição Prévia da Escala (se não especificada explicitamente)
        if escala is None:
            escala = 50
            for esc_cand in [50, 75, 100]:
                f_esc = esc_cand / 50.0
                w_bar_est = 735.0 * f_esc
                w_cargas_est = (num_casos * 515.0 + (num_casos - 1) * 35.0) * f_esc if num_casos > 1 else 1220.0 * f_esc
                w_notas_est = 2700.0 * f_esc
                h_tab_est = (num_pilares * 22.0 + 100.0) * f_esc
                h_notas_est = 1120.0 * f_esc

                # 1. Verifica se cabe em LAYOUT_ABAIXO (Tabelas e Notas lado a lado sob a locação)
                w_abaixo_tot = max(larg_locacao, w_bar_est + (80.0 * f_esc) + w_cargas_est + (80.0 * f_esc) + w_notas_est)
                h_abaixo_tot = alt_locacao + (260.0 * f_esc) + (160.0 * f_esc) + max(h_tab_est, h_notas_est)
                if (w_abaixo_tot + 7.5 * esc_cand) / esc_cand <= 180.0 and (h_abaixo_tot + 6.0 * esc_cand) / esc_cand <= 84.1:
                    escala = esc_cand
                    break

                # 2. Verifica se cabe em LAYOUT_LATERAL (Baricentro e Cargas no topo direito, Notas abaixo)
                w_lat_tot = larg_locacao + (180.0 * f_esc) + max(w_bar_est + (60.0 * f_esc) + w_cargas_est, w_notas_est)
                h_lat_tot = max(alt_locacao + (260.0 * f_esc), h_tab_est + (70.0 * f_esc) + h_notas_est)
                if (w_lat_tot + 7.5 * esc_cand) / esc_cand <= 180.0 and (h_lat_tot + 6.0 * esc_cand) / esc_cand <= 84.1:
                    escala = esc_cand
                    break

        fator_esc = escala / 50.0

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

        # Configura no cabeçalho nativo do DWG o sistema/subsistema Formas -> Planta de formas
        dwg.settings.systemId = 2  # Formas (IEDFOR)
        dwg.settings.subSystemId = 2  # Planta de formas
        dwg.settings.scale = float(escala)
        dwg.dim.dimtxt = 0.20

        # Redefine a origem das cotas relativas (IPOCOTREL) para a origem especificada (ou 0, 0, 0)
        rx = float(origem_cotas[0]) if origem_cotas else 0.0
        ry = float(origem_cotas[1]) if origem_cotas else 0.0
        if self._mdwg_dll is not None and hasattr(dwg, "m_pedmv") and dwg.m_pedmv:
            try:
                self._mdwg_dll.g_edmexdefcotrel(
                    ctypes.c_void_p(dwg.m_pedmv),
                    ctypes.c_double(rx),
                    ctypes.c_double(ry),
                    ctypes.c_double(0.0),
                )
            except Exception:
                pass

        # 3. Desenha a Planta de Locação dos Pilares nas suas coordenadas originais
        self._desenhar_pilares_locacao(dwg, planta.pilares, bounds_planta, escala=escala, origem_cotas=origem_cotas)

        # 4. Disposição Inteligente das Tabelas para Enquadramento em Molduras Padrão TQS
        w_bar_est = 735.0 * fator_esc
        w_cargas_est = (num_casos * 515.0 + (num_casos - 1) * 35.0) * fator_esc if num_casos > 1 else 1220.0 * fator_esc
        w_notas_est = 2700.0 * fator_esc
        h_tab_est = (num_pilares * 22.0 + 100.0) * fator_esc
        h_notas_est = 1120.0 * fator_esc

        # Teste se cabe em LAYOUT_ABAIXO
        w_abaixo_tot = max(larg_locacao, w_bar_est + (80.0 * fator_esc) + w_cargas_est + (80.0 * fator_esc) + w_notas_est)
        h_abaixo_tot = alt_locacao + (260.0 * fator_esc) + (160.0 * fator_esc) + max(h_tab_est, h_notas_est)
        cabe_abaixo = ((w_abaixo_tot + 7.5 * escala) / escala <= 180.0 and (h_abaixo_tot + 6.0 * escala) / escala <= 84.1)

        # Edifícios horizontalmente alongados ou com altura compatível usam layout ABAIXO
        if cabe_abaixo:
            layout_modo = "abaixo"
        else:
            layout_modo = "lateral"

        if layout_modo == "abaixo":
            # =========================================================================
            # LAYOUT ABAIXO: Locação no topo; Baricentros, Cargas e Notas lado a lado abaixo
            # Perfeito para edifícios horizontais (ex: Jardim Europa), preenchendo a folha
            # de forma contínua e eliminando completamente vazios inferiores ou transbordamentos.
            # =========================================================================
            espaco_v_loc_tab = 160.0 * fator_esc
            y_topo_tabelas = min_yp - espaco_v_loc_tab
            espaco_inter = 80.0 * fator_esc

            larg_total_inferior = w_bar_est + espaco_inter + w_cargas_est + espaco_inter + w_notas_est
            if larg_total_inferior > larg_locacao:
                delta_x = (larg_total_inferior - larg_locacao) / 2.0
                x_base = min_xp - delta_x
            else:
                delta_x = (larg_locacao - larg_total_inferior) / 2.0
                x_base = min_xp + delta_x

            # 1. Tabela de Baricentros
            x_bar = x_base
            y_fim_bar, larg_tabela_bar = self._desenhar_tabela_baricentros(
                dwg, planta.pilares, x_start=x_bar, y_start=y_topo_tabelas, escala=escala, origem_cotas=origem_cotas
            )

            # 2. Tabela de Cargas (ao lado da de baricentros)
            x_cargas = x_bar + larg_tabela_bar + espaco_inter
            y_fim_cargas, larg_tabela_cargas = self._desenhar_tabela_cargas(
                dwg,
                pilares=planta.pilares,
                x_start=x_cargas,
                y_start=y_topo_tabelas,
                dados_porlid=planta.dados_porlid,
                escala=escala,
            )

            # 3. Notas, Convenção de Sinais e Legenda (ao lado da de cargas)
            x_notas = x_cargas + larg_tabela_cargas + espaco_inter
            y_fim_notas = self._desenhar_notas_e_legendas(
                dwg, x_start=x_notas, y_start=y_topo_tabelas, dados_porlid=planta.dados_porlid, escala=escala, origem_cotas=origem_cotas
            )

            larg_notas_real = 2700.0 * fator_esc
            bounds_conteudo = (
                min(min_xp, x_bar),
                max(max_xp, x_notas + larg_notas_real),
                min(y_fim_bar, y_fim_cargas, y_fim_notas),
                max_yp + (260.0 * fator_esc),
            )
        else:
            # =========================================================================
            # LAYOUT LATERAL (2 Colunas): Para edifícios compactos/verticais (ex: Visconde)
            # Locação à esquerda; à direita:
            #   - Topo: Tabela de Baricentros e Tabela de Cargas lado a lado
            #   - Abaixo: Notas, Convenção de Sinais e Legendas
            # Altura do bloco lateral harmoniza perfeitamente com a altura da locação.
            # =========================================================================
            x_start_dir = max_xp + (180.0 * fator_esc)
            y_topo_tabelas = max_yp + (50.0 * fator_esc)
            espaco_inter = 60.0 * fator_esc

            # 1. Tabela de Baricentros (coluna 1 da direita)
            x_bar = x_start_dir
            y_fim_bar, larg_tabela_bar = self._desenhar_tabela_baricentros(
                dwg, planta.pilares, x_start=x_bar, y_start=y_topo_tabelas, escala=escala, origem_cotas=origem_cotas
            )

            # 2. Tabela de Cargas (coluna 2 da direita, alinhada no topo com Baricentros)
            x_cargas = x_bar + larg_tabela_bar + espaco_inter
            y_fim_cargas, larg_tabela_cargas = self._desenhar_tabela_cargas(
                dwg,
                pilares=planta.pilares,
                x_start=x_cargas,
                y_start=y_topo_tabelas,
                dados_porlid=planta.dados_porlid,
                escala=escala,
            )

            # 3. Notas, Convenção de Sinais e Legenda (diretamente abaixo de Baricentros e Cargas)
            y_topo_notas = min(y_fim_bar, y_fim_cargas) - (70.0 * fator_esc)
            x_notas = x_start_dir
            y_fim_notas = self._desenhar_notas_e_legendas(
                dwg, x_start=x_notas, y_start=y_topo_notas, dados_porlid=planta.dados_porlid, escala=escala, origem_cotas=origem_cotas
            )

            larg_notas_real = 2700.0 * fator_esc
            larg_dir_total = max(larg_tabela_bar + espaco_inter + larg_tabela_cargas, larg_notas_real)
            bounds_conteudo = (
                min_xp,
                x_start_dir + larg_dir_total,
                min(min_yp - (70.0 * fator_esc), y_fim_notas),
                max(max_yp + (260.0 * fator_esc), y_topo_tabelas + (60.0 * fator_esc)),
            )

        # 5. Seleção Automática e Desenho da Moldura Catalogada Oficial TQS
        formato_escolhido, escala_final = self._auto_selecionar_e_desenhar_moldura(
            dwg, bounds_conteudo, escala=escala, planta=planta
        )

        # 6. Salva o arquivo nativo TQS .DWG (com backup de segurança se já existir)
        if os.path.exists(arquivo_saida_dwg) and os.path.isfile(arquivo_saida_dwg):
            self._criar_backup_seguranca(arquivo_saida_dwg)

        pasta_destino = os.path.dirname(arquivo_saida_dwg)
        if pasta_destino and not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino, exist_ok=True)

        # Garante propriedades do desenho: Formas -> Planta de formas
        dwg.settings.systemId = 2  # Formas (IEDFOR)
        dwg.settings.subSystemId = 2  # Planta de formas
        dwg.settings.scale = float(escala_final or escala)

        dwg.file.SaveAs(arquivo_saida_dwg)
        dwg.file.Close()

        return arquivo_saida_dwg

    @staticmethod
    def _criar_backup_seguranca(caminho_arquivo: str) -> Optional[str]:
        """
        Cria cópia de backup do arquivo DWG existente antes de sobrescrever.
        Gera uma cópia com timestamp em backup_claude (ex: backup_claude\\GABARITO_BKP_20261002_140728.DWG).
        """
        from src.core.backup import criar_backup
        try:
            return criar_backup(caminho_arquivo)
        except Exception:
            return None

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
        fator_esc: float = 1.0,
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
            x_nome = min_x - (70.0 * fator_esc)
            y_nome = min_y - (20.0 * fator_esc)
        else:
            x_nome = max_x + (20.0 * fator_esc)
            y_nome = min_y - (22.0 * fator_esc)

        x_dim = x_nome
        y_dim = y_nome - (20.0 * fator_esc)

        return x_nome, y_nome, x_dim, y_dim

    def _desenhar_pilares_locacao(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        bounds: Tuple[float, float, float, float],
        escala: int = 50,
        origem_cotas: Optional[Tuple[float, float]] = None,
    ):
        """
        Desenha cada pilar em suas coordenadas espaciais reais:
        - Título Oficial TQS (Padrão GEO_CARGAS / Zuckhan Soledade):
          Nível 222, Altura 60.0: 'GABARITO E CARGAS NAS FUNDAÇÕES'
          Nível 250, Altura 22.5: 'ESCALA 1:50' posicionado diretamente abaixo
        - Contorno retangular ou poligonal fechado (Nível 3)
        - Linhas azuis em cruz cruzando 50 cm do limite do pilar em todas as 4 direções (Nível 21)
        - Cotas relativas das coordenadas X e Y do baricentro com triângulos indicadores (Nível 21)
        - Nome do pilar (Nível 9, H=21.0) posicionado no quadrante inferior direito
        - Dimensões da seção (Nível 12, H=15.0) diretamente abaixo do nome
        """
        min_x, max_x, min_y, max_y = bounds
        cx_planta = (min_x + max_x) / 2.0

        fator_esc = escala / 50.0
        h_min_normativo = 0.20 * escala

        # Título Oficial (Padrão Oficial TQS GEO_CARGAS / Zuckhan Soledade)
        # Nível 222, Tamanho 60.0 * fator_esc: GABARITO E CARGAS NAS FUNDAÇÕES
        y_titulo = max_y + (160.0 * fator_esc)
        larg_titulo_est = 1860.0 * fator_esc
        if (max_x - min_x) > (larg_titulo_est + (400.0 * fator_esc)):
            x_titulo = min_x + (100.0 * fator_esc)
        else:
            x_titulo = max(min_x, cx_planta - (larg_titulo_est / 2.0))

        dwg.draw.level = 222
        dwg.draw.Text(x_titulo, y_titulo, 60.0 * fator_esc, 0.0, "GABARITO E CARGAS NAS FUNDAÇÕES")

        # Texto indicando escala na posição abaixo conforme padrão GEO_CARGAS (Nível 250, Tamanho 22.5 * fator_esc)
        y_escala = y_titulo - (36.8 * fator_esc)
        x_escala = x_titulo + (9.5 * fator_esc)
        dwg.draw.level = 250
        dwg.draw.Text(x_escala, y_escala, 22.5 * fator_esc, 0.0, f"ESCALA 1:{escala}")

        # Precomputa os limites espaciais (faces) de cada pilar para análise de vizinhança
        pilar_bounds = {}
        for p in pilares:
            geom = p.geometria
            cg = p.baricentro
            vts = geom.vertices_poligono
            if vts and len(vts) >= 3:
                min_px = min(pt[0] for pt in vts)
                max_px = max(pt[0] for pt in vts)
                min_py = min(pt[1] for pt in vts)
                max_py = max(pt[1] for pt in vts)
            else:
                w = geom.b if geom.b > 0 else 20.0
                h = geom.h if geom.h > 0 else 20.0
                min_px = cg.x - w / 2.0
                max_px = cg.x + w / 2.0
                min_py = cg.y - h / 2.0
                max_py = cg.y + h / 2.0
            pilar_bounds[p.nome] = (min_px, max_px, min_py, max_py)

        for p in pilares:
            geom = p.geometria
            cg = p.baricentro
            vts = geom.vertices_poligono
            min_px, max_px, min_py, max_py = pilar_bounds[p.nome]

            # 1. Contorno do Pilar (Polilinha fechada de N vértices - Nível 3)
            dwg.draw.level = 3
            if vts and len(vts) >= 3:
                dwg.draw.PolyStart()
                for vx, vy in vts:
                    dwg.draw.PolyEnterPoint(vx, vy)
                dwg.draw.PolyEnterPoint(vts[0][0], vts[0][1])
                dwg.draw.Polyline()
            else:
                dwg.draw.PolyStart()
                dwg.draw.PolyEnterPoint(min_px, min_py)
                dwg.draw.PolyEnterPoint(max_px, min_py)
                dwg.draw.PolyEnterPoint(max_px, max_py)
                dwg.draw.PolyEnterPoint(min_px, max_py)
                dwg.draw.PolyEnterPoint(min_px, min_py)
                dwg.draw.Polyline()

            # Análise geométrica de vizinhança para eixos e cotas (evita embolamento em pilares gêmeos/juntas)
            # A) Vizinhança horizontal no mesmo eixo Y:
            vizinho_dir_y = None
            vizinho_esq_y = None
            # B) Vizinhança vertical no mesmo eixo X:
            vizinho_cima_x = None
            vizinho_baixo_x = None
            for outro in pilares:
                if outro.nome == p.nome:
                    continue
                o_min_px, o_max_px, o_min_py, o_max_py = pilar_bounds[outro.nome]
                if abs(cg.y - outro.baricentro.y) < 2.0:
                    if 0.0 <= (o_min_px - max_px) < 80.0:
                        vizinho_dir_y = outro
                    elif 0.0 <= (min_px - o_max_px) < 80.0:
                        vizinho_esq_y = outro
                if abs(cg.x - outro.baricentro.x) < 2.0:
                    if 0.0 <= (o_min_py - max_py) < 80.0:
                        vizinho_cima_x = outro
                    elif 0.0 <= (min_py - o_max_py) < 80.0:
                        vizinho_baixo_x = outro

            # C) Escalonamento vertical para eixos X próximos (< 60 cm):
            stagger_count_x = 0
            for outro in pilares:
                if outro.nome == p.nome:
                    continue
                o_min_px, o_max_px, o_min_py, o_max_py = pilar_bounds[outro.nome]
                if 0.0 < (cg.x - outro.baricentro.x) < 60.0 and abs(max_py - o_max_py) < 80.0:
                    stagger_count_x += 1
            stagger_dy = stagger_count_x * 115.0

            # D) Escalonamento horizontal para eixos Y próximos (< 60 cm):
            stagger_count_y = 0
            for outro in pilares:
                if outro.nome == p.nome:
                    continue
                o_min_px, o_max_px, o_min_py, o_max_py = pilar_bounds[outro.nome]
                if 0.0 < (cg.y - outro.baricentro.y) < 60.0 and abs(max_px - o_max_px) < 80.0:
                    stagger_count_y += 1
            stagger_dx = stagger_count_y * 115.0

            # 2. Linhas azuis em cruz cruzando 50 cm do limite do pilar (Nível 21)
            dwg.draw.level = 21
            # Eixo horizontal: cruza 50 cm à esquerda se não houver vizinho, ou conecta ao vizinho da esquerda
            x_lin_ini = (min_px - 50.0) if not vizinho_esq_y else min_px
            # Cruza 50 cm à direita se não houver vizinho, ou conecta ao vizinho da direita
            if vizinho_dir_y:
                o_min_px = pilar_bounds[vizinho_dir_y.nome][0]
                x_lin_fim = o_min_px  # conecta os pilares gêmeos cobrindo a junta sem invadir o corpo do vizinho
            else:
                x_lin_fim = max_px + 50.0 + stagger_dx
            dwg.draw.Line(x_lin_ini, cg.y, x_lin_fim, cg.y)

            # Eixo vertical: cruza 50 cm abaixo (ou conecta ao vizinho de baixo) e 50 cm (+ escalonamento) acima
            y_lin_ini = (min_py - 50.0) if not vizinho_baixo_x else min_py
            if vizinho_cima_x:
                o_min_py = pilar_bounds[vizinho_cima_x.nome][2]
                y_lin_topo = o_min_py
            else:
                y_lin_topo = max_py + 50.0 + stagger_dy
            dwg.draw.Line(cg.x, y_lin_ini, cg.x, y_lin_topo)

            # 3. Cotas Relativas Oficiais (Nível 21, Objeto Dinâmico Nativo do TQS: IPOCOTREL)
            # Cota Y: só é emitida se NÃO houver pilar vizinho colado à direita no mesmo eixo
            # (evita que a cota caia dentro do pilar vizinho ou sobreponha o mesmo valor de Y)
            emitir_cota_y = (vizinho_dir_y is None)
            xv_y = max_px + 25.0 + stagger_dx
            yv_y = cg.y

            # Cota X: só é emitida se NÃO houver pilar vizinho colado acima no mesmo eixo
            # escalonada verticalmente por stagger_dy quando houver eixo paralelo colado
            emitir_cota_x = (vizinho_cima_x is None)
            xv_x = cg.x
            yv_x = max_py + 25.0 + stagger_dy

            criou_nativo = False
            if self._ipo_dll is not None and hasattr(dwg, "m_pedmv") and dwg.m_pedmv:
                try:
                    pedmv = ctypes.c_void_p(dwg.m_pedmv)
                    ret_obj = ctypes.c_void_p()
                    ret_status = ctypes.c_int()

                    # 3.1 Cota Y (Horizontal, sobre o prolongamento direito da linha horizontal)
                    if emitir_cota_y:
                        px_y = ctypes.c_double(xv_y)
                        py_y = ctypes.c_double(yv_y)
                        pz_y = ctypes.c_double(0.0)
                        tipo_y = ctypes.c_int(0)
                        self._ipo_dll.IPOCOTREL_CRIARPARATU(
                            ctypes.byref(pedmv),
                            ctypes.byref(px_y),
                            ctypes.byref(py_y),
                            ctypes.byref(pz_y),
                            ctypes.byref(tipo_y),
                            ctypes.byref(ret_obj),
                            ctypes.byref(ret_status),
                        )

                    # 3.2 Cota X (Vertical, sobre o prolongamento superior da linha vertical com escalonamento)
                    if emitir_cota_x:
                        px_x = ctypes.c_double(xv_x)
                        py_x = ctypes.c_double(yv_x)
                        pz_x = ctypes.c_double(90.0)
                        tipo_x = ctypes.c_int(1)
                        self._ipo_dll.IPOCOTREL_CRIARPARATU(
                            ctypes.byref(pedmv),
                            ctypes.byref(px_x),
                            ctypes.byref(py_x),
                            ctypes.byref(pz_x),
                            ctypes.byref(tipo_x),
                            ctypes.byref(ret_obj),
                            ctypes.byref(ret_status),
                        )
                    criou_nativo = True
                except Exception:
                    criou_nativo = False

            if not criou_nativo:
                h_cota = max(13.5 * fator_esc, h_min_normativo)
                # Fallback vetorial idêntico caso IPOCOTREL.dll não esteja acessível no ambiente
                rx = float(origem_cotas[0]) if origem_cotas else 0.0
                ry = float(origem_cotas[1]) if origem_cotas else 0.0
                if emitir_cota_y:
                    val_y_num = round(cg.y - ry, 1)
                    if abs(val_y_num) < 1e-4:
                        val_y_num = 0.0
                    val_y_str = f"{val_y_num:.1f}".rstrip("0").rstrip(".") if "." in f"{val_y_num:.1f}" else f"{val_y_num:.0f}"
                    # Triângulo indicador apontando para baixo sobre a linha horizontal
                    dwg.draw.Line(xv_y, yv_y, xv_y + (7.5 * fator_esc), yv_y + (15.0 * fator_esc))
                    dwg.draw.Line(xv_y + (7.5 * fator_esc), yv_y + (15.0 * fator_esc), xv_y - (7.5 * fator_esc), yv_y + (15.0 * fator_esc))
                    dwg.draw.Line(xv_y - (7.5 * fator_esc), yv_y + (15.0 * fator_esc), xv_y, yv_y)
                    # Haste vertical
                    dwg.draw.Line(xv_y, yv_y + (15.0 * fator_esc), xv_y, yv_y + (22.5 * fator_esc))
                    # Prateleira horizontal à direita com comprimento proporcional ao texto
                    tam_prat_y = max(50.0 * fator_esc, len(val_y_str) * h_cota)
                    dwg.draw.Line(xv_y, yv_y + (22.5 * fator_esc), xv_y + tam_prat_y, yv_y + (22.5 * fator_esc))
                    # Texto da cota Y (horizontal)
                    dwg.draw.Text(xv_y, yv_y + (22.5 * fator_esc) + (3.4 * fator_esc), h_cota, 0.0, val_y_str)

                if emitir_cota_x:
                    val_x_num = round(cg.x - rx, 1)
                    if abs(val_x_num) < 1e-4:
                        val_x_num = 0.0
                    val_x_str = f"{val_x_num:.1f}".rstrip("0").rstrip(".") if "." in f"{val_x_num:.1f}" else f"{val_x_num:.0f}"
                    # Triângulo indicador apontando para a direita sobre a linha vertical
                    dwg.draw.Line(xv_x, yv_x, xv_x - (15.0 * fator_esc), yv_x + (7.5 * fator_esc))
                    dwg.draw.Line(xv_x - (15.0 * fator_esc), yv_x + (7.5 * fator_esc), xv_x - (15.0 * fator_esc), yv_x - (7.5 * fator_esc))
                    dwg.draw.Line(xv_x - (15.0 * fator_esc), yv_x - (7.5 * fator_esc), xv_x, yv_x)
                    # Haste horizontal para a esquerda
                    dwg.draw.Line(xv_x - (15.0 * fator_esc), yv_x, xv_x - (22.5 * fator_esc), yv_x)
                    # Prateleira vertical subindo com comprimento proporcional ao texto
                    tam_prat_x = max(50.0 * fator_esc, len(val_x_str) * h_cota)
                    dwg.draw.Line(xv_x - (22.5 * fator_esc), yv_x, xv_x - (22.5 * fator_esc), yv_x + tam_prat_x)
                    # Texto da cota X (vertical a 90 graus)
                    dwg.draw.Text(xv_x - (22.5 * fator_esc) - (3.4 * fator_esc), yv_x, h_cota, 90.0, val_x_str)

            # 4. Rótulo inteligente: Nome no Nível 9 e Dimensão no Nível 12
            xn, yn, xd, yd = self._calcular_posicao_rotulo_pilar(p, pilares, fator_esc=fator_esc)

            # Padrão: 0.28 cm no nome do pilar e 0.20 cm na dimensão no papel
            h_pilar_nome = 0.28 * escala
            h_pilar_dim = 0.20 * escala

            dwg.draw.level = 9
            dwg.draw.Text(xn, yn, h_pilar_nome, 0.0, p.nome)

            dwg.draw.level = 12
            dim_str = f"{int(round(geom.b))}x{int(round(geom.h))}"
            dwg.draw.Text(xd, yd, h_pilar_dim, 0.0, dim_str)

        # 5. Marcador de Origem (0,0) na planta de locação se especificado
        if origem_cotas:
            rx = float(origem_cotas[0])
            ry = float(origem_cotas[1])
            # Eixos em cruz (Nível 21)
            dwg.draw.level = 21
            tam_cruz = 50.0 * fator_esc
            dwg.draw.Line(rx - tam_cruz, ry, rx + tam_cruz, ry)
            dwg.draw.Line(rx, ry - tam_cruz, rx, ry + tam_cruz)
            dwg.draw.Circle(rx, ry, 12.0 * fator_esc)
            dwg.draw.Circle(rx, ry, 4.0 * fator_esc)
            # Texto identificador da Origem
            dwg.draw.level = 250
            h_orig_txt = max(14.0 * fator_esc, h_min_normativo)
            dwg.draw.Text(rx + (16.0 * fator_esc), ry + (8.0 * fator_esc), h_orig_txt, 0.0, "ORIGEM (0,0)")

    def _desenhar_tabela_baricentros(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        x_start: float,
        y_start: float,
        escala: int = 50,
        origem_cotas: Optional[Tuple[float, float]] = None,
    ) -> Tuple[float, float]:
        """
        Desenha as DUAS tabelas de baricentros de pilares lado a lado:
          1. BARICENTRO DE PILARES (ORDENADO POR COORDENADAS)
             - 4 colunas: PILAR | X (cm) | PILAR | Y (cm)
             - Colunas 1 e 2 ordenadas por X crescente.
             - Colunas 3 e 4 ordenadas por Y crescente.
          2. BARICENTRO DE PILARES (ORDENADO POR PILARES)
             - 3 colunas: PILAR | X (cm) | Y (cm)
             - Ordenado naturalmente pela identificação dos pilares (P1, P2, P3...).

        Regra de altura de texto:
          - Tamanho mínimo de qualquer texto no papel: 0.20 cm (2.0 mm), independente da escala.
          - Na escala 1:50, 0.20 cm no papel corresponde a 10.0 cm no desenho.
          - Todas as grandezas textuais são parametrizadas por (escala / 50.0) garantindo h >= 0.20 * escala.
        Retorna (y_fim, largura_total).
        """
        import re

        def natural_sort_key(p):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", str(p.nome))]

        # Ordenações oficiais
        p_ord_x = sorted(
            pilares,
            key=lambda p: (round(p.baricentro.x, 1) if p.baricentro else 0.0, natural_sort_key(p)),
        )
        p_ord_y = sorted(
            pilares,
            key=lambda p: (round(p.baricentro.y, 1) if p.baricentro else 0.0, natural_sort_key(p)),
        )
        p_ord_nome = sorted(pilares, key=natural_sort_key)

        n_total = len(pilares)

        # =====================================================================
        # ALTURAS DE TEXTO (MÍNIMO RIGOROSO: 0.20 cm NO PAPEL, INDEPENDENTE DA ESCALA)
        # =====================================================================
        fator_esc = escala / 50.0
        h_min_normativo = 0.20 * escala  # 10.0 cm para 1:50, 15.0 cm para 1:75, 20.0 cm para 1:100

        # Alturas de texto no desenho
        # Itens da tabela (nome de pilares, coordenadas) e cabeçalhos com a altura mínima normativa de 0.20 cm no papel
        h_txt_dados = 0.20 * escala  # 10.0 cm para 1:50, 15.0 cm para 1:75 (exatamente 0.20 cm no papel)
        h_txt_cab = 0.20 * escala    # Cabeçalho das colunas com altura mínima de 0.20 cm no papel
        h_txt_tit = max(14.0 * fator_esc, h_min_normativo)
        h_txt_sub = max(11.5 * fator_esc, h_min_normativo)

        h_linha = 22.0 * fator_esc  # Idêntico à tabela de cargas para alinhamento horizontal
        espaco_entre_tabelas = 35.0 * fator_esc

        # =====================================================================
        # GEOMETRIA E LARGURAS DAS COLUNAS (ENQUADRAMENTO DOS TÍTULOS)
        # =====================================================================
        # Tabela 1: ORDENADO POR COORDENADAS (4 colunas)
        # PILAR (85), X (95), PILAR (85), Y (95) -> Total = 360.0 cm (* fator_esc)
        # Subtítulo (26 chars * 11.5 = 299 cm) cabe perfeitamente com 30.5 cm de margem em cada lado
        larguras_tab1 = [w * fator_esc for w in [85.0, 95.0, 85.0, 95.0]]
        largura_tab1 = sum(larguras_tab1)  # 360.0 cm
        x1_0 = x_start
        x1_1 = x1_0 + largura_tab1

        # Tabela 2: ORDENADO POR PILARES (3 colunas)
        # PILAR (90), X (125), Y (125) -> Total = 340.0 cm (* fator_esc)
        # Título principal (21 chars * 14.0 = 294 cm) cabe perfeitamente com 23.0 cm de margem em cada lado
        # Subtítulo (22 chars * 11.5 = 253 cm) cabe perfeitamente com 43.5 cm de margem em cada lado
        larguras_tab2 = [w * fator_esc for w in [90.0, 125.0, 125.0]]
        largura_tab2 = sum(larguras_tab2)  # 340.0 cm
        x2_0 = x1_1 + espaco_entre_tabelas
        x2_1 = x2_0 + largura_tab2

        largura_total = largura_tab1 + espaco_entre_tabelas + largura_tab2  # 735.0 cm (* fator_esc)

        # Nivelamento vertical:
        # y_grid_topo é o topo do cabeçalho das colunas (y_start - 56.0), idêntico à tabela de cargas
        # y_dados_topo é o topo das linhas de dados (y_start - 94.0), idêntico à tabela de cargas
        y_grid_topo = y_start - (56.0 * fator_esc)
        h_caixa_titulo = 56.0 * fator_esc
        y_top_bar = y_grid_topo + h_caixa_titulo
        h_cabecalho_colunas = 38.0 * fator_esc
        y_dados_topo = y_grid_topo - h_cabecalho_colunas

        altura_dados = n_total * h_linha
        y_fim = y_dados_topo - altura_dados

        dwg.draw.level = 0

        # =====================================================================
        # TABELA 1: ORDENADO POR COORDENADAS
        # =====================================================================
        # Linhas horizontais do cabeçalho
        dwg.draw.level = 221
        dwg.draw.Line(x1_0, y_top_bar, x1_1, y_top_bar)
        dwg.draw.Line(x1_0, y_grid_topo, x1_1, y_grid_topo)
        dwg.draw.Line(x1_0, y_dados_topo, x1_1, y_dados_topo)

        # Textos de título da Tabela 1 rigorosamente centralizados e contidos na caixa (Nível 250)
        dwg.draw.level = 250
        tit1 = "BARICENTRO DE PILARES"
        w_tit1 = len(tit1) * h_txt_tit  # 21 * 14.0 = 294.0 cm
        x_tit1 = x1_0 + ((largura_tab1 - w_tit1) / 2.0)
        dwg.draw.Text(x_tit1, y_top_bar - (20.0 * fator_esc), h_txt_tit, 0.0, tit1)

        sub1 = "(ORDENADO POR COORDENADAS)"
        w_sub1 = len(sub1) * h_txt_sub  # 26 * 11.5 = 299.0 cm
        x_sub1 = x1_0 + ((largura_tab1 - w_sub1) / 2.0)
        dwg.draw.Text(x_sub1, y_top_bar - (37.0 * fator_esc), h_txt_sub, 0.0, sub1)

        # Textos dos cabeçalhos das colunas da Tabela 1 (Nível 221)
        dwg.draw.level = 221
        col_x = x1_0
        for c, col_nome in enumerate(["PILAR", "X (cm)", "PILAR", "Y (cm)"]):
            cw = larguras_tab1[c]
            if col_nome == "PILAR":
                dwg.draw.Text(col_x + (15.0 * fator_esc), y_grid_topo - (24.0 * fator_esc), h_txt_cab, 0.0, col_nome)
            else:
                w_lbl = len(col_nome) * h_txt_cab
                off_lbl = max(6.0 * fator_esc, (cw - w_lbl) / 2.0)
                dwg.draw.Text(col_x + off_lbl, y_grid_topo - (24.0 * fator_esc), h_txt_cab, 0.0, col_nome)
            col_x += cw

        # Linhas verticais externas (toda a altura da tabela)
        dwg.draw.level = 221
        dwg.draw.Line(x1_0, y_top_bar, x1_0, y_fim)
        dwg.draw.Line(x1_1, y_top_bar, x1_1, y_fim)

        # Divisores internos de colunas (iniciam na linha de cabeçalho das grandezas)
        col_x = x1_0
        for cw in larguras_tab1[:-1]:
            col_x += cw
            dwg.draw.Line(col_x, y_grid_topo, col_x, y_fim)

        # Dados da Tabela 1
        curr_y = y_dados_topo
        for i in range(n_total):
            curr_y -= h_linha
            dwg.draw.level = 221
            dwg.draw.Line(x1_0, curr_y, x1_1, curr_y)

            rx = float(origem_cotas[0]) if origem_cotas else 0.0
            ry = float(origem_cotas[1]) if origem_cotas else 0.0
            px = p_ord_x[i]
            py = p_ord_y[i]
            nome_px = str(px.nome)
            vx = (px.baricentro.x - rx) if px.baricentro else 0.0
            if abs(vx) < 1e-4:
                vx = 0.0
            val_x = f"{vx:.1f}"
            nome_py = str(py.nome)
            vy = (py.baricentro.y - ry) if py.baricentro else 0.0
            if abs(vy) < 1e-4:
                vy = 0.0
            val_y = f"{vy:.1f}"

            dwg.draw.level = 0
            # Coluna 0: PILAR (ord X) - Alinhado à esquerda com margem +15.0 cm
            c0_x = x1_0
            dwg.draw.Text(c0_x + (15.0 * fator_esc), curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, nome_px)

            # Coluna 1: X (cm) - Centralizado na coluna
            c1_x = c0_x + larguras_tab1[0]
            off_x = max(6.0 * fator_esc, (larguras_tab1[1] - (len(val_x) * (8.5 * fator_esc))) / 2.0)
            dwg.draw.Text(c1_x + off_x, curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, val_x)

            # Coluna 2: PILAR (ord Y) - Alinhado à esquerda com margem +15.0 cm
            c2_x = c1_x + larguras_tab1[1]
            dwg.draw.Text(c2_x + (15.0 * fator_esc), curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, nome_py)

            # Coluna 3: Y (cm) - Centralizado na coluna
            c3_x = c2_x + larguras_tab1[2]
            off_y = max(6.0 * fator_esc, (larguras_tab1[3] - (len(val_y) * (8.5 * fator_esc))) / 2.0)
            dwg.draw.Text(c3_x + off_y, curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, val_y)

        # =====================================================================
        # TABELA 2: ORDENADO POR PILARES
        # =====================================================================
        # Linhas horizontais do cabeçalho
        dwg.draw.level = 221
        dwg.draw.Line(x2_0, y_top_bar, x2_1, y_top_bar)
        dwg.draw.Line(x2_0, y_grid_topo, x2_1, y_grid_topo)
        dwg.draw.Line(x2_0, y_dados_topo, x2_1, y_dados_topo)

        # Textos de título da Tabela 2 rigorosamente centralizados e contidos na caixa (Nível 250)
        dwg.draw.level = 250
        tit2 = "BARICENTRO DE PILARES"
        w_tit2 = len(tit2) * h_txt_tit  # 21 * 14.0 = 294.0 cm
        x_tit2 = x2_0 + ((largura_tab2 - w_tit2) / 2.0)
        dwg.draw.Text(x_tit2, y_top_bar - (20.0 * fator_esc), h_txt_tit, 0.0, tit2)

        sub2 = "(ORDENADO POR PILARES)"
        w_sub2 = len(sub2) * h_txt_sub  # 22 * 11.5 = 253.0 cm
        x_sub2 = x2_0 + ((largura_tab2 - w_sub2) / 2.0)
        dwg.draw.Text(x_sub2, y_top_bar - (37.0 * fator_esc), h_txt_sub, 0.0, sub2)

        # Textos dos cabeçalhos das colunas da Tabela 2 (Nível 221)
        dwg.draw.level = 221
        col_x = x2_0
        for c, col_nome in enumerate(["PILAR", "X (cm)", "Y (cm)"]):
            cw = larguras_tab2[c]
            if col_nome == "PILAR":
                dwg.draw.Text(col_x + (15.0 * fator_esc), y_grid_topo - (24.0 * fator_esc), h_txt_cab, 0.0, col_nome)
            else:
                w_lbl = len(col_nome) * h_txt_cab
                off_lbl = max(6.0 * fator_esc, (cw - w_lbl) / 2.0)
                dwg.draw.Text(col_x + off_lbl, y_grid_topo - (24.0 * fator_esc), h_txt_cab, 0.0, col_nome)
            col_x += cw

        # Linhas verticais externas (toda a altura da tabela)
        dwg.draw.level = 221
        dwg.draw.Line(x2_0, y_top_bar, x2_0, y_fim)
        dwg.draw.Line(x2_1, y_top_bar, x2_1, y_fim)

        # Divisores internos de colunas (iniciam na linha de cabeçalho das grandezas)
        col_x = x2_0
        for cw in larguras_tab2[:-1]:
            col_x += cw
            dwg.draw.Line(col_x, y_grid_topo, col_x, y_fim)

        # Dados da Tabela 2
        curr_y = y_dados_topo
        for i in range(n_total):
            curr_y -= h_linha
            dwg.draw.level = 221
            dwg.draw.Line(x2_0, curr_y, x2_1, curr_y)

            p = p_ord_nome[i]
            nome_p = str(p.nome)
            vx = (p.baricentro.x - rx) if p.baricentro else 0.0
            if abs(vx) < 1e-4:
                vx = 0.0
            val_x = f"{vx:.1f}"
            vy = (p.baricentro.y - ry) if p.baricentro else 0.0
            if abs(vy) < 1e-4:
                vy = 0.0
            val_y = f"{vy:.1f}"

            dwg.draw.level = 0
            # Coluna 0: PILAR - Alinhado à esquerda com margem +15.0 cm
            c0_x = x2_0
            dwg.draw.Text(c0_x + (15.0 * fator_esc), curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, nome_p)

            # Coluna 1: X (cm) - Centralizado na coluna
            c1_x = c0_x + larguras_tab2[0]
            off_x = max(6.0 * fator_esc, (larguras_tab2[1] - (len(val_x) * (8.5 * fator_esc))) / 2.0)
            dwg.draw.Text(c1_x + off_x, curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, val_x)

            # Coluna 2: Y (cm) - Centralizado na coluna
            c2_x = c1_x + larguras_tab2[1]
            off_y = max(6.0 * fator_esc, (larguras_tab2[2] - (len(val_y) * (8.5 * fator_esc))) / 2.0)
            dwg.draw.Text(c2_x + off_y, curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, val_y)

        return y_fim, largura_total

    def _desenhar_tabela_cargas(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        x_start: float,
        y_start: float,
        dados_porlid: Optional[Dict[str, Any]] = None,
        escala: int = 50,
    ) -> Tuple[float, float]:
        """
        Desenha a tabela de cargas nas fundações idêntica ao relatório oficial do TQS (PORLID),
        com os 7 campos oficiais: Elem/Pilar, Fz, Fx, Fy, Mx, My, Mz e suas respectivas unidades (tf, tfm).
        Suporta universalmente:
          - Múltiplos casos (ex: Jardim Europa com 6 casos: FZ MAX, MX MAX, MY MAX, FZ MIN, MX MIN, MY MIN)
            desenhados lado a lado em blocos harmoniosos, exatamente como no GEO_CARGAS.DWG oficial.
          - Caso único (ex: Visconde do Herval 054), auto-dimensionado em 2 colunas para otimizar espaço.

        Regra de altura de texto:
          - Tamanho mínimo normativo no papel: 0.20 cm (2.0 mm), independente da escala.
          - No desenho (espaço do modelo): h >= 0.20 * escala (10.0 cm para 1:50).
        Retorna (y_fim, largura_total).
        """
        fator_esc = escala / 50.0
        h_min_normativo = 0.20 * escala

        # -----------------------------------------------------------------
        # RAMIFICAÇÃO 1: MÚLTIPLOS CASOS DE CARGA (Conforme PORLID oficial)
        # -----------------------------------------------------------------
        if dados_porlid and dados_porlid.get("casos") and len(dados_porlid["casos"]) > 1:
            casos = dados_porlid["casos"]
            num_casos = len(casos)
            colunas = ["PILAR", "Fz", "Fx", "Fy", "Mx", "My", "Mz"]
            unidades = ["", "tf", "tf", "tf", "tfm", "tfm", "tfm"]

            # Cada bloco de caso tem 7 colunas (Pilar + 6 componentes de esforços)
            larguras = [w * fator_esc for w in [75.0, 75.0, 70.0, 70.0, 75.0, 75.0, 75.0]]  # Total por bloco = 515.0 cm * fator_esc
            largura_bloco = sum(larguras)
            espaco_entre_casos = 35.0 * fator_esc
            h_linha = 22.0 * fator_esc
            h_cabecalho = 38.0 * fator_esc

            largura_total = num_casos * largura_bloco + (num_casos - 1) * espaco_entre_casos

            # Título Geral da Tabela de Cargas
            y_titulo = y_start
            dwg.draw.level = 250
            h_txt_tit = max(20.0 * fator_esc, h_min_normativo)
            dwg.draw.Text(x_start + (largura_total / 2.0) - (200.0 * fator_esc), y_titulo, h_txt_tit, 0.0, "TABELA DE CARGAS NAS FUNDAÇÕES")

            # Subtítulo Geral
            y_subtitulo = y_titulo - (26.0 * fator_esc)
            dwg.draw.level = 250
            h_txt_sub = max(13.5 * fator_esc, h_min_normativo)
            dwg.draw.Text(
                x_start + max(10.0 * fator_esc, (largura_total / 2.0) - (260.0 * fator_esc)),
                y_subtitulo,
                h_txt_sub,
                0.0,
                "TABELA DE ESFORÇOS CARACTERÍSTICOS POR CASO CRÍTICO (TQS ESPACIAL)",
            )

            y_grid_topo = y_subtitulo - (30.0 * fator_esc)

            max_linhas = 0
            for k, caso in enumerate(casos):
                bx0 = x_start + k * (largura_bloco + espaco_entre_casos)
                by0 = y_grid_topo
                linhas_caso = caso.get("linhas", [])
                max_linhas = max(max_linhas, len(linhas_caso))

                # Nome do Caso (ex: 'CASO 1 - FZ MAX') acima da grade de cada bloco (Nível 222)
                dwg.draw.level = 222
                nome_caso = caso.get("nome", f"CASO {k+1}")
                h_txt_caso = max(14.0 * fator_esc, h_min_normativo)
                dwg.draw.Text(bx0 + (10.0 * fator_esc), by0 + (10.0 * fator_esc), h_txt_caso, 0.0, nome_caso)

                dwg.draw.level = 221
                # Linha superior do cabeçalho
                dwg.draw.Line(bx0, by0, bx0 + largura_bloco, by0)
                # Linha intermediária (separa grandezas de unidades nas colunas de esforços)
                dwg.draw.Line(bx0 + larguras[0], by0 - (20.0 * fator_esc), bx0 + largura_bloco, by0 - (20.0 * fator_esc))
                # Linha inferior do cabeçalho
                dwg.draw.Line(bx0, by0 - h_cabecalho, bx0 + largura_bloco, by0 - h_cabecalho)

                # Textos do cabeçalho com altura mínima normativa de 0.20 cm no papel (Nível 221)
                h_txt_c0 = 0.20 * escala
                h_txt_cab = 0.20 * escala
                h_txt_un = 0.20 * escala
                dwg.draw.Text(bx0 + (15.0 * fator_esc), by0 - (24.0 * fator_esc), h_txt_c0, 0.0, colunas[0])
                ox = larguras[0]
                for w, tit, un in zip(larguras[1:], colunas[1:], unidades[1:]):
                    dwg.draw.Text(bx0 + ox + (w / 2.0) - (10.0 * fator_esc), by0 - (15.0 * fator_esc), h_txt_cab, 0.0, tit)
                    dwg.draw.Text(bx0 + ox + (w / 2.0) - (12.0 * fator_esc), by0 - (32.0 * fator_esc), h_txt_un, 0.0, un)
                    ox += w

                # Linhas verticais do bloco (Nível 221)
                altura_tabela = h_cabecalho + len(linhas_caso) * h_linha
                dwg.draw.Line(bx0, by0, bx0, by0 - altura_tabela)
                cx = bx0
                for w in larguras:
                    cx += w
                    dwg.draw.Line(cx, by0, cx, by0 - altura_tabela)

                # Linhas de dados de cada elemento (nome de pilares e próprias cargas com h = 0.20 * escala)
                curr_y = by0 - h_cabecalho
                h_txt_dados = 0.20 * escala
                for row in linhas_caso:
                    curr_y -= h_linha
                    dwg.draw.level = 221
                    dwg.draw.Line(bx0, curr_y, bx0 + largura_bloco, curr_y)

                    # Coluna Pilar / Elem (Nível 0)
                    dwg.draw.level = 0
                    dwg.draw.Text(bx0 + (15.0 * fator_esc), curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, str(row[0]))

                    # Colunas de Esforços Fz, Fx, Fy, Mx, My, Mz
                    ox = larguras[0]
                    for w, val in zip(larguras[1:], row[1:]):
                        val_str = str(val).strip()
                        text_offset = max(8.0 * fator_esc, (w / 2.0) - (len(val_str) * (3.5 * fator_esc)))
                        dwg.draw.Text(bx0 + ox + text_offset, curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, val_str)
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
                    f"{esf.nk_max:.1f}" if esf else "-",
                    f"{esf.hx:.1f}" if esf else "-",
                    f"{esf.hy:.1f}" if esf else "-",
                    f"{esf.mxk:.2f}" if esf else "-",
                    f"{esf.myk:.2f}" if esf else "-",
                    f"{esf.mz:.2f}" if esf else "-",
                ])

        n_total = len(linhas)
        num_colunas = max(1, math.ceil(n_total / 30))
        linhas_por_coluna = math.ceil(n_total / num_colunas)

        larguras = [w * fator_esc for w in [85.0, 85.0, 80.0, 80.0, 85.0, 85.0, 85.0]]  # Total por bloco = 585.0 cm * fator_esc
        largura_bloco = sum(larguras)
        espaco_entre_blocos = 50.0 * fator_esc
        h_linha = 22.0 * fator_esc
        h_cabecalho = 38.0 * fator_esc

        largura_total = num_colunas * largura_bloco + (num_colunas - 1) * espaco_entre_blocos

        # Título Geral da Tabela de Cargas (Nível 250)
        y_titulo = y_start
        dwg.draw.level = 250
        h_txt_tit2 = max(18.0 * fator_esc, h_min_normativo)
        dwg.draw.Text(x_start + (largura_total / 2.0) - (200.0 * fator_esc), y_titulo, h_txt_tit2, 0.0, "TABELA DE CARGAS NAS FUNDAÇÕES")

        # Subtítulo (Combinação crítica oficial do TQS - Nível 250)
        y_subtitulo = y_titulo - (28.0 * fator_esc)
        dwg.draw.level = 250
        tam_fonte_sub = max((13.0 if len(titulo_comb) > 40 else 15.0) * fator_esc, h_min_normativo)
        dwg.draw.Text(x_start + max(10.0 * fator_esc, (largura_total / 2.0) - (len(titulo_comb) * (3.8 * fator_esc))), y_subtitulo, tam_fonte_sub, 0.0, titulo_comb)

        # O grid da tabela inicia abaixo do subtítulo
        y_grid_topo = y_subtitulo - (30.0 * fator_esc)

        for col_idx in range(num_colunas):
            sub_linhas = linhas[col_idx * linhas_por_coluna : (col_idx + 1) * linhas_por_coluna]
            if not sub_linhas:
                continue

            bx0 = x_start + col_idx * (largura_bloco + espaco_entre_blocos)
            by0 = y_grid_topo

            dwg.draw.level = 221
            # Linha superior do cabeçalho
            dwg.draw.Line(bx0, by0, bx0 + largura_bloco, by0)
            # Linha intermediária (separa grandezas de unidades nas colunas de esforços)
            dwg.draw.Line(bx0 + larguras[0], by0 - (20.0 * fator_esc), bx0 + largura_bloco, by0 - (20.0 * fator_esc))
            # Linha inferior do cabeçalho
            dwg.draw.Line(bx0, by0 - h_cabecalho, bx0 + largura_bloco, by0 - h_cabecalho)

            # Textos do cabeçalho com altura mínima normativa de 0.20 cm no papel (Nível 221)
            h_txt_c0 = 0.20 * escala
            h_txt_cab = 0.20 * escala
            h_txt_un = 0.20 * escala
            dwg.draw.Text(bx0 + (20.0 * fator_esc), by0 - (24.0 * fator_esc), h_txt_c0, 0.0, colunas[0])
            ox = larguras[0]
            for w, tit, un in zip(larguras[1:], colunas[1:], unidades[1:]):
                dwg.draw.Text(bx0 + ox + (w / 2.0) - (10.0 * fator_esc), by0 - (15.0 * fator_esc), h_txt_cab, 0.0, tit)
                dwg.draw.Text(bx0 + ox + (w / 2.0) - (12.0 * fator_esc), by0 - (32.0 * fator_esc), h_txt_un, 0.0, un)
                ox += w

            # Linhas verticais do bloco (Nível 221)
            altura_tabela = h_cabecalho + len(sub_linhas) * h_linha
            dwg.draw.Line(bx0, by0, bx0, by0 - altura_tabela)
            cx = bx0
            for w in larguras:
                cx += w
                dwg.draw.Line(cx, by0, cx, by0 - altura_tabela)

            # Linhas de dados (nome de pilares e próprias cargas com h = 0.20 * escala)
            curr_y = by0 - h_cabecalho
            h_txt_dados = 0.20 * escala
            for row in sub_linhas:
                curr_y -= h_linha
                dwg.draw.level = 221
                dwg.draw.Line(bx0, curr_y, bx0 + largura_bloco, curr_y)

                # Coluna Elem (Nível 0)
                dwg.draw.level = 0
                dwg.draw.Text(bx0 + (15.0 * fator_esc), curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, str(row[0]))

                # Colunas de Esforços Fz, Fx, Fy, Mx, My, Mz
                ox = larguras[0]
                for w, val in zip(larguras[1:], row[1:]):
                    val_str = str(val).strip()
                    text_offset = max(10.0 * fator_esc, (w / 2.0) - (len(val_str) * (3.5 * fator_esc)))
                    dwg.draw.Text(bx0 + ox + text_offset, curr_y + (6.0 * fator_esc), h_txt_dados, 0.0, val_str)
                    ox += w

        y_fim = y_grid_topo - (h_cabecalho + linhas_por_coluna * h_linha)
        return y_fim, largura_total

    def _desenhar_notas_e_legendas(
        self,
        dwg: TQSDwg.Dwg,
        x_start: float,
        y_start: float,
        dados_porlid: Optional[Dict[str, Any]] = None,
        escala: int = 50,
        origem_cotas: Optional[Tuple[float, float]] = None,
    ) -> float:
        """
        Desenha os 3 blocos informativos rigorosamente iguais ao modelo GEO_CARGAS do Zuckhan Soledade:
          1. OBSERVAÇÕES (variável conforme os casos críticos de carregamento do edifício)
          2. CONVENÇÃO DE SINAIS (esquema isométrico 3D com eixos e esforços)
          3. INCIDÊNCIA DAS CARGAS DE VENTO (retângulo do edifício com setas direcionais a 0°, 90°, 180°, 270°)
          4. CONVENÇÕES (Simbologia dos Pilares, Contenções, Ponto de Carga e Origem 0,0)
        Retorna o Y mínimo (inferior) ocupado pelos blocos.

        Regra de altura de texto:
          - Tamanho mínimo normativo no papel: >= 0.20 cm (2.0 mm), independente da escala.
          - No desenho (espaço do modelo): h >= 0.20 * escala (10.0 cm para 1:50, 15.0 cm para 1:75).
        """
        fator_esc = escala / 50.0
        h_min_normativo = 0.20 * escala

        # =========================================================================
        # BLOCO 1: OBSERVAÇÕES (Alinhado à esquerda: x_start, y_start)
        # =========================================================================
        dwg.draw.level = 250
        h_tit = max(20.0 * fator_esc, h_min_normativo)
        dwg.draw.Text(x_start, y_start, h_tit, 0.0, "OBSERVAÇÕES:")
        dwg.draw.Line(x_start, y_start - (11.26 * fator_esc), x_start + (218.66 * fator_esc), y_start - (11.26 * fator_esc))

        curr_y = y_start - (56.27 * fator_esc)
        dy_linha = 25.01 * fator_esc
        h_txt = max(15.0 * fator_esc, h_min_normativo)

        # Linhas de cabeçalho fixas
        dwg.draw.level = 250
        dwg.draw.Text(x_start, curr_y, h_txt, 0.0, "- Esforços com valores característicos.")
        curr_y -= dy_linha

        if origem_cotas:
            rx = float(origem_cotas[0])
            ry = float(origem_cotas[1])
            dwg.draw.level = 250
            dwg.draw.Text(
                x_start,
                curr_y,
                h_txt,
                0.0,
                f"- Origem (0,0) das cotas e coordenadas de locação referenciada ao ponto (X={rx:.1f}, Y={ry:.1f}) cm.",
            )
            curr_y -= dy_linha

        dwg.draw.level = 250
        dwg.draw.Text(
            x_start,
            curr_y,
            h_txt,
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

                dwg.draw.level = 250
                dwg.draw.Text(x_start, curr_y, h_txt, 0.0, f"- Caso {cid}: {desc}")
                curr_y -= dy_linha

                dwg.draw.Text(
                    x_start,
                    curr_y,
                    h_txt,
                    0.0,
                    "   (incluindo a ação do vento e empuxo do solo, se houver).",
                )
                curr_y -= dy_linha
        else:
            # Fallback caso clássico padrão caso não haja PORLID detalhado
            dwg.draw.level = 250
            dwg.draw.Text(
                x_start,
                curr_y,
                h_txt,
                0.0,
                "- Caso 1: combinação dos carregamentos que produz a máxima força vertical Fz em cada pilar",
            )
            curr_y -= dy_linha
            dwg.draw.Text(
                x_start,
                curr_y,
                h_txt,
                0.0,
                "   (incluindo a ação do vento e empuxo do solo, se houver).",
            )
            curr_y -= dy_linha

        # Linhas de rodapé fixas
        dwg.draw.level = 250
        dwg.draw.Text(
            x_start,
            curr_y,
            h_txt,
            0.0,
            "- A escolha da combinação de carregamentos para elaboração do projeto de fundações é de inteira responsabilidade do",
        )
        curr_y -= dy_linha
        dwg.draw.Text(x_start, curr_y, h_txt, 0.0, "   projetista de fundações.")
        curr_y -= dy_linha

        dwg.draw.level = 250
        dwg.draw.Text(
            x_start,
            curr_y,
            h_txt,
            0.0,
            "- As cargas distribuídas nas estruturas de contenção, quando existirem, compreendem as reações dos pavimentos nessas",
        )
        curr_y -= dy_linha
        dwg.draw.Text(
            x_start,
            curr_y,
            h_txt,
            0.0,
            "   estruturas. Não está incluído o peso próprio das mesmas.",
        )
        curr_y -= dy_linha

        y_fim_obs = curr_y

        # =========================================================================
        # CARREGAMENTO DOS BLOCOS 2, 3 E 4 (GEO_CARGAS do Zuckhan Soledade)
        # =========================================================================
        caminho_blocos = os.path.join(os.path.dirname(__file__), "blocos_informativos_soledade.json")
        if os.path.exists(caminho_blocos):
            with open(caminho_blocos, "r", encoding="utf-8") as f:
                blocos_data = json.load(f)

            # BLOCO 2: CONVENÇÃO DE SINAIS (ΔX = +1436.25 cm, ΔY = 0.00 cm)
            x_conv = x_start + (1436.25 * fator_esc)
            y_conv = y_start
            for e in blocos_data.get("convencao", []):
                etype = e.get("type")
                dwg.draw.level = e.get("level", 250)
                if etype == "line":
                    dwg.draw.Line(
                        x_conv + (e["dx1"] * fator_esc),
                        y_conv + (e["dy1"] * fator_esc),
                        x_conv + (e["dx2"] * fator_esc),
                        y_conv + (e["dy2"] * fator_esc),
                    )
                elif etype == "text":
                    h_txt_elem = max(e["height"] * fator_esc, h_min_normativo)
                    dwg.draw.Text(
                        x_conv + (e["dx"] * fator_esc),
                        y_conv + (e["dy"] * fator_esc),
                        h_txt_elem,
                        e.get("angle", 0.0),
                        e["text"],
                    )
                elif etype == "poly":
                    pts = e.get("pts", [])
                    if len(pts) >= 2:
                        dwg.draw.PolyStart()
                        for pt in pts:
                            dwg.draw.PolyEnterPoint(x_conv + (pt[0] * fator_esc), y_conv + (pt[1] * fator_esc))
                        dwg.draw.Polyline()

            # BLOCO 3: INCIDÊNCIA DAS CARGAS DE VENTO (ΔX = +2178.19 cm, ΔY = +1.68 cm)
            x_vento = x_start + (2178.19 * fator_esc)
            y_vento = y_start + (1.68 * fator_esc)
            for e in blocos_data.get("vento", []):
                etype = e.get("type")
                dwg.draw.level = e.get("level", 250)
                if etype == "line":
                    dwg.draw.Line(
                        x_vento + (e["dx1"] * fator_esc),
                        y_vento + (e["dy1"] * fator_esc),
                        x_vento + (e["dx2"] * fator_esc),
                        y_vento + (e["dy2"] * fator_esc),
                    )
                elif etype == "text":
                    h_txt_elem = max(e["height"] * fator_esc, h_min_normativo)
                    dwg.draw.Text(
                        x_vento + (e["dx"] * fator_esc),
                        y_vento + (e["dy"] * fator_esc),
                        h_txt_elem,
                        e.get("angle", 0.0),
                        e["text"],
                    )
                elif etype == "poly":
                    pts = e.get("pts", [])
                    if len(pts) >= 2:
                        dwg.draw.PolyStart()
                        for pt in pts:
                            dwg.draw.PolyEnterPoint(x_vento + (pt[0] * fator_esc), y_vento + (pt[1] * fator_esc))
                        dwg.draw.Polyline()

            # BLOCO 4: CONVENÇÕES (Simbologia dos Pilares, Contenções, Ponto de Carga e Origem 0,0)
            y_conv_loc = min(y_fim_obs, y_start - (560.0 * fator_esc)) - (70.0 * fator_esc)
            x_conv_loc = x_start
            for e in blocos_data.get("convencoes_locacao", []):
                etype = e.get("type")
                dwg.draw.level = e.get("level", 221)
                # Cor do nível (-1): a cor gravada no JSON é a cor resolvida, não deve virar cor fixa
                dwg.draw.color = -1
                if etype == "line":
                    dwg.draw.Line(
                        x_conv_loc + (e["dx1"] * fator_esc),
                        y_conv_loc + (e["dy1"] * fator_esc),
                        x_conv_loc + (e["dx2"] * fator_esc),
                        y_conv_loc + (e["dy2"] * fator_esc),
                    )
                elif etype == "text":
                    h_txt_elem = max(e["height"] * fator_esc, h_min_normativo)
                    dwg.draw.Text(
                        x_conv_loc + (e["dx"] * fator_esc),
                        y_conv_loc + (e["dy"] * fator_esc),
                        h_txt_elem,
                        e.get("angle", 0.0),
                        e["text"],
                    )
                elif etype == "poly":
                    pts = e.get("pts", [])
                    if len(pts) >= 2:
                        dwg.draw.PolyStart()
                        for pt in pts:
                            dwg.draw.PolyEnterPoint(x_conv_loc + (pt[0] * fator_esc), y_conv_loc + (pt[1] * fator_esc))
                        dwg.draw.Polyline()
                elif etype == "circle":
                    dwg.draw.Circle(
                        x_conv_loc + (e["dxc"] * fator_esc),
                        y_conv_loc + (e["dyc"] * fator_esc),
                        e["radius"] * fator_esc,
                    )

            # Restaura cor do nível (ByLevel = -1)
            dwg.draw.color = -1
            y_fim = y_conv_loc - (495.0 * fator_esc)
            return y_fim

        y_fim = min(y_fim_obs, y_start - (560.0 * fator_esc))
        return y_fim

    def _auto_selecionar_e_desenhar_moldura(
        self,
        dwg: TQSDwg.Dwg,
        bounds_conteudo: Tuple[float, float, float, float],
        escala: int = 50,
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

        formato_selecionado = None
        dim_papel = None

        # Margem esquerda ABNT: 2.5 cm no papel | Demais margens: 1.0 cm
        folga_larg = (2.5 + 1.0 + 4.0) * escala # Margens + folga de respiro
        folga_alt = (1.0 + 1.0 + 4.0) * escala

        larg_min_papel = (larg_desenho + folga_larg) / escala
        alt_min_papel = (alt_desenho + folga_alt) / escala

        # Encontra todas as molduras catalogadas oficiais que atendem na escala fixada
        candidatos = []
        for nome, wp, hp in CATALOGO_MOLDURAS_TQS:
            if wp >= larg_min_papel and hp >= alt_min_papel:
                candidatos.append((nome, wp, hp, wp * hp))

        if candidatos:
            # Escolhe a menor folha oficial por consumo de papel (área mínima)
            candidatos.sort(key=lambda c: c[3])
            formato_selecionado = candidatos[0][0]
            dim_papel = (candidatos[0][1], candidatos[0][2])
        else:
            # Fallback de segurança estritamente para o maior formato padrão oficial do TQS (180-85)
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

        # Margens ABNT / TQS
        mx0 = 2.5 * escala
        my0 = 1.0 * escala
        mx1 = w_proj - (1.0 * escala)
        my1 = h_proj - (1.0 * escala)

        # Área reservada para o selo no canto inferior direito (apenas demarcação, sem detalhes de carimbo)
        larg_selo = SELO_LARGURA_CM * escala
        alt_selo = SELO_ALTURA_CM * escala  # Carimbo + tabela de revisões
        sx0 = mx1 - larg_selo
        sy1 = my0 + alt_selo

        # Criação do Bloco de Projeção da Moldura (Nível 100, cor do nível)
        dwg.draw.level = 100
        dwg.draw.color = -1

        dwg.draw.BlockOpen(formato_selecionado, 0.0, 0.0)
        dwg.draw.level = 100
        dwg.draw.color = -1

        # 1. Borda externa do papel
        dwg.draw.Line(0.0, 0.0, w_proj, 0.0)
        dwg.draw.Line(w_proj, 0.0, w_proj, h_proj)
        dwg.draw.Line(0.0, 0.0, 0.0, h_proj)
        dwg.draw.Line(0.0, h_proj, w_proj, h_proj)

        # 2. Margem interna útil
        dwg.draw.Line(mx0, my0, mx1, my0)
        dwg.draw.Line(mx1, my0, mx1, my1)
        dwg.draw.Line(mx0, my1, mx1, my1)
        dwg.draw.Line(mx0, my1, mx0, my0)

        # 3. Retângulo delimitador da área do selo (sem linhas internas de carimbo nem textos)
        dwg.draw.Line(sx0, 0.0, sx0, sy1)
        dwg.draw.Line(mx1, sy1, sx0, sy1)

        # 4. Marcas de dobra (módulos de 18.5 cm na horizontal e 14.85 cm na vertical)
        mod_x = 18.5 * escala
        x_tick = sx0 - mod_x
        while x_tick > mx0:
            dwg.draw.Line(x_tick, 0.0, x_tick, my0)
            dwg.draw.Line(x_tick, my1, x_tick, h_proj)
            x_tick -= mod_x

        mod_y = 14.85 * escala
        y_tick = mod_y
        while y_tick < my1:
            dwg.draw.Line(0.0, y_tick, mx0, y_tick)
            dwg.draw.Line(mx1, y_tick, w_proj, y_tick)
            y_tick += mod_y

        # 5. Nome do formato em texto simples na margem esquerda
        dwg.draw.Text(mx0 - 0.4 * escala, my0 + 6.0 * escala, 1.8 * escala, 90.0, formato_selecionado)

        dwg.draw.BlockClose()

        # Inserção do bloco no ponto (x0, y0) da prancha no Nível 100
        dwg.draw.level = 100
        dwg.draw.color = -1
        dwg.draw.BlockInsert(formato_selecionado, x0, y0, 1.0, 1.0, 0.0)

        # Restaura níveis e cores normais
        dwg.draw.color = -1
        dwg.draw.level = 0

        return formato_selecionado, escala
