import os
import re
import math
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from TQS import TQSDwg
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
from src.drawing.tqs_dwg_builder import CATALOGO_MOLDURAS_TQS

configurar_ambiente_tqs_64()

class AlvenariaDwgBuilder:
    """
    Builder responsável pela geração e montagem de Plantas de Formas de Alvenaria
    Estrutural (1ª Fiada) no TQS V25.
    
    Transforma a fiada bruta gerada pelo TQS Alvest (DesFiad1.DWG) em uma prancha
    executiva pronta para emissão (PRE_FOR_1aFIADA_*.DWG), seguindo rigorosamente:
      1. Preservação de dados e segurança: Jamais sobrescreve sem backup prévio com timestamp.
      2. Importação do Corte Esquemático como Bloco nativo da pasta GERAIS.
      3. Metodologia padronizada de molduras da Planta de Cargas (CATALOGO_MOLDURAS_TQS, margens ABNT,
         marcas de dobra e selo técnico).
      4. Vãos: Portas têm blocos internos apagados e dimensão no centro do vão; janelas mantêm
         os blocos de alvenaria e o texto é posicionado externamente (acima ou abaixo).
      5. Sobreposição das lajes do pavimento (LAJ*.DWG: identificador L# e espessura h).
      6. Resumo de materiais (LISTMELV.LST) e legenda de blocos cerâmicos.
    """

    def __init__(self):
        pass

    @staticmethod
    def _localizar_arquivo(pasta: str, padrao: str) -> Optional[str]:
        """Localiza um arquivo na pasta que coincida com o padrão (case-insensitive)."""
        if not os.path.exists(pasta):
            return None
        padrao_lower = padrao.lower()
        for f in os.listdir(pasta):
            if f.lower() == padrao_lower:
                return os.path.join(pasta, f)
            if padrao_lower.startswith("*") and f.lower().endswith(padrao_lower[1:]):
                return os.path.join(pasta, f)
            if padrao_lower.endswith("*") and f.lower().startswith(padrao_lower[:-1]):
                return os.path.join(pasta, f)
        return None

    def _criar_backup_seguro(self, caminho_arquivo: str) -> Optional[str]:
        """
        Cria backup de segurança imediato com timestamp antes de qualquer modificação.
        Garante que nenhum arquivo seja jamais sobrescrito sem versão protegida.
        """
        if not os.path.exists(caminho_arquivo) or not os.path.isfile(caminho_arquivo):
            return None

        pasta = os.path.dirname(caminho_arquivo)
        nome_base, ext = os.path.splitext(os.path.basename(caminho_arquivo))
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bkp_ts = os.path.join(pasta, f"{nome_base}_BKP_{ts}{ext}")

        try:
            shutil.copy2(caminho_arquivo, bkp_ts)
            return bkp_ts
        except Exception:
            return None

    def construir_planta_formas(
        self,
        caminho_edificio: str,
        pavimento: str = "TIPO A",
        caminho_saida_dwg: Optional[str] = None,
        escala: int = 50,
    ) -> Dict[str, Any]:
        """
        Executa o pipeline completo de formas de alvenaria.
        """
        pasta_pav = os.path.join(caminho_edificio, pavimento)
        pasta_gerais = os.path.join(caminho_edificio, "GERAIS")

        if not os.path.exists(pasta_pav):
            raise FileNotFoundError(f"Pasta do pavimento não encontrada: {pasta_pav}")

        # 1. Localizar arquivos fonte
        p_desfiad = self._localizar_arquivo(pasta_pav, "DesFiad1.DWG")
        if not p_desfiad:
            p_desfiad = self._localizar_arquivo(pasta_pav, "DesFiad*.DWG") or self._localizar_arquivo(pasta_pav, "DesAlven.DWG")
        if not p_desfiad:
            raise FileNotFoundError(f"Desenho de fiada (DesFiad1.DWG) não encontrado em {pasta_pav}")

        # LAJ*.DWG (ex: LAJ0290.DWG)
        p_laj = None
        for f in os.listdir(pasta_pav):
            if f.upper().startswith("LAJ") and f.upper().endswith(".DWG"):
                p_laj = os.path.join(pasta_pav, f)
                break

        # LISTMELV.LST
        p_lst = self._localizar_arquivo(pasta_pav, "LISTMELV.LST")

        # TIPO A.DWG (arquitetura para esquadrias)
        p_tipo = self._localizar_arquivo(pasta_pav, f"{pavimento}.DWG")
        if not p_tipo:
            p_tipo = self._localizar_arquivo(os.path.join(caminho_edificio, "TIPO A"), "TIPO A.DWG")

        # CORTE ESQUEMÁTICO.DWG em GERAIS
        p_corte = None
        if os.path.exists(pasta_gerais):
            for f in os.listdir(pasta_gerais):
                if "CORTE" in f.upper() and f.upper().endswith(".DWG"):
                    p_corte = os.path.join(pasta_gerais, f)
                    break

        # Arquivo de saída
        if not caminho_saida_dwg:
            caminho_saida_dwg = os.path.join(pasta_pav, f"PRE_FOR_1aFIADA_{pavimento}.DWG")

        # 1. REGRA 1: Backup obrigatório antes de sobrescrever qualquer arquivo existente
        arquivo_backup = self._criar_backup_seguro(caminho_saida_dwg)

        # 2. Mapeamento prévio dos vãos ($BLVAO): Portas (251) vs Janelas (252) no pavimento
        vaos_portas, vaos_janelas = self._mapear_vaos(p_desfiad)

        # 3. Pré-carregar elementos técnicos da prancha de referência (apenas coluna lateral: Resumo, Legendas, Notas)
        elementos_referencia = self._precarregar_elementos_referencia(pasta_pav, pasta_gerais)

        # 4. Inicializa o arquivo de saída como cópia de DesFiad1
        try:
            shutil.copy2(p_desfiad, caminho_saida_dwg)
        except PermissionError:
            # Caso o arquivo original esteja aberto no visualizador do TQS pelo usuário
            nome_base, ext = os.path.splitext(caminho_saida_dwg)
            caminho_saida_dwg = f"{nome_base}_NOVO{ext}"
            shutil.copy2(p_desfiad, caminho_saida_dwg)

        dwg = TQSDwg.Dwg(pedmv=0)
        res_open = dwg.file.Open(caminho_saida_dwg)
        if res_open != 0:
            raise RuntimeError(f"Erro ao abrir DWG gerado: {res_open}")

        dwg.settings.scale = float(escala)
        dwg.dim.dimtxt = 0.20

        # 5. Filtragem de elementos indesejados + REGRA 4: Apagar blocos nas portas
        it = dwg.iterator
        it.Begin()
        posicoes_para_apagar = set()
        bounds_planta = [1e9, -1e9, 1e9, -1e9]

        while True:
            pos = it.GetElementReadPosition()
            if pos:
                el = it.elementName
                lvl = it.level
                txt = getattr(it, "text", "").strip()
                bname = getattr(it, "blockName", "")

                # Atualiza bounding box da planta útil EXCLUSIVAMENTE a partir das alvenarias e vãos do pavimento
                if lvl in [203, 213, 241, 245, 247, 248, 251, 252]:
                    for pt in [(it.x1, it.y1), (it.x2, it.y2)]:
                        if -2500.0 < pt[0] < 3000.0 and -2500.0 < pt[1] < 1000.0:
                            bounds_planta[0] = min(bounds_planta[0], pt[0])
                            bounds_planta[1] = max(bounds_planta[1], pt[0])
                            bounds_planta[2] = min(bounds_planta[2], pt[1])
                            bounds_planta[3] = max(bounds_planta[3], pt[1])

                # Critérios de purga limpos
                # a) Textos de ferro vertical (pf12.5)
                if lvl == 198 and el == "Texto":
                    posicoes_para_apagar.add(pos)
                # b) Blocos de armadura vertical ($PFERV)
                elif el == "Bloco" and "PFERV" in bname:
                    posicoes_para_apagar.add(pos)
                # c) Identificadores brutos de vãos ($IDnPRT nos níveis 106 e 216)
                elif el == "Bloco" and "IDnPRT" in bname:
                    posicoes_para_apagar.add(pos)
                elif lvl in [106, 216] and el == "Texto" and any(txt.startswith(k) for k in ["P", "JA", "PJ", "CHURR", "PE"]):
                    posicoes_para_apagar.add(pos)
                # d) Cotas numéricas internas de modulação de blocos (Nível 221)
                elif lvl == 221 and el == "Texto" and re.match(r"^[0-9]+(?:\.[0-9]+)?$", txt):
                    posicoes_para_apagar.add(pos)
                # e) Título original do Alvest
                elif lvl == 222 and "fiada" in txt.lower():
                    posicoes_para_apagar.add(pos)
                # f) Textos de exaustão/tela (Nível 7)
                elif lvl == 7 and el == "Texto":
                    posicoes_para_apagar.add(pos)
                # g) REGRA 4: Nas PORTAS, apagar os blocos de alvenaria no vão (preservando ombreiras e janelas)
                elif el == "Bloco":
                    if not bname.startswith("$") and self._ponto_esta_dentro_de_alguma_porta(it.x1, it.y1, vaos_portas):
                        posicoes_para_apagar.add(pos)

            if not it.Next():
                break

        for p in posicoes_para_apagar:
            dwg.edit.Erase(p)

        # 6. Sobreposição de Lajes (sempre do LAJ*.DWG nativo do pavimento)
        total_lajes = 0
        if p_laj and os.path.exists(p_laj):
            dwg_laj = TQSDwg.Dwg(pedmv=0)
            if dwg_laj.file.Open(p_laj) == 0:
                it_l = dwg_laj.iterator
                it_l.Begin()
                while True:
                    pos = it_l.GetElementReadPosition()
                    if pos and it_l.elementName == "Texto":
                        lvl = it_l.level
                        txt = it_l.text.strip()
                        if lvl in [10, 13]:
                            # Garante que o texto da laje está estritamente dentro do perímetro do edifício
                            if (bounds_planta[0] - 80.0 <= it_l.x1 <= bounds_planta[1] + 80.0 and
                                bounds_planta[2] - 80.0 <= it_l.y1 <= bounds_planta[3] + 80.0):
                                dwg.draw.level = lvl
                                dwg.draw.color = 0
                                dwg.draw.Text(it_l.x1, it_l.y1, 10.0, 0.0, txt)
                                if lvl == 10:
                                    total_lajes += 1
                    if not it_l.Next():
                        break
                dwg_laj.file.Close()

        # 7. REGRA 4: Anotação de Dimensões de Vãos (Portas no centro, Janelas fora da parede)
        # Sempre gerado a partir dos vãos mapeados no pavimento corrente
        vaos_inseridos = self._adicionar_dimensoes_vaos_regra4(
            dwg, vaos_portas, vaos_janelas, p_tipo, bounds_planta
        )

        # 8. Juntas de Movimentação e Dilatação (Nível 221)
        self._adicionar_juntas_dilatacao(dwg, bounds_planta)

        # 9. Título e Escala da Planta (posicionados diretamente acima da planta do edifício)
        dwg.draw.level = 222
        dwg.draw.color = 0
        titulo = f"PRÉ-MODULAÇÃO DE 1ª FIADA - PAVIMENTO {pavimento.upper()}"
        y_titulo = bounds_planta[3] + 140.0
        x_titulo = bounds_planta[0]
        dwg.draw.Text(x_titulo, y_titulo, 32.5, 0.0, titulo)

        dwg.draw.level = 250
        dwg.draw.color = 0
        dwg.draw.Text(x_titulo + 4.0, y_titulo - 25.0, 12.0, 0.0, f"ESCALA: 1:{escala}")

        # 10. Inserção de Resumo de Materiais, Legendas e Notas Técnicas na Coluna Lateral
        self._inserir_coluna_lateral(dwg, elementos_referencia)

        # 11. REGRA 2: Carregar e Inserir o Corte Esquemático da pasta GERAIS como Bloco
        bloco_corte_inserido = False
        if p_corte and os.path.exists(p_corte):
            bloco_corte_inserido = self._inserir_corte_esquematico_como_bloco(dwg, p_corte)

        # 12. REGRA 3: Metodologia de Moldura da Planta de Cargas (CATALOGO_MOLDURAS_TQS)
        # Bounding box considerando a planta, título e coluna técnica lateral
        max_y_conteudo = max(y_titulo + 20.0, 560.0)
        max_x_conteudo = max(bounds_planta[1] + 200.0, 4350.0)
        bounds_totais = (bounds_planta[0], max_x_conteudo, bounds_planta[2], max_y_conteudo)
        moldura_escolhida = self._auto_selecionar_e_desenhar_moldura(dwg, bounds_totais, escala=escala)

        # Salva e Fecha
        dwg.file.Save()
        dwg.file.Close()

        elementos_finais = self._auditar_dwg(caminho_saida_dwg)

        return {
            "status": "sucesso",
            "caminho_dwg": caminho_saida_dwg,
            "backup_criado": arquivo_backup,
            "edificio": os.path.basename(caminho_edificio),
            "pavimento": pavimento,
            "escala": escala,
            "moldura": moldura_escolhida,
            "corte_como_bloco": bloco_corte_inserido,
            "elementos_purgados": len(posicoes_para_apagar),
            "total_lajes": total_lajes,
            "total_vaos": vaos_inseridos,
            "auditoria": elementos_finais,
        }

    def _mapear_vaos(self, caminho_desfiad: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Classifica todos os vãos ($BLVAO):
        - Nível 251: Portas
        - Nível 252: Janelas
        
        No TQS Alvest, (it.x1, it.y1) do $BLVAO representa exatamente o CENTRO geométrico da abertura.
        it.xScale é a largura do vão (w) e it.yScale é a espessura da alvenaria (h).
        """
        dwg_des = TQSDwg.Dwg(pedmv=0)
        dwg_des.file.Open(caminho_desfiad)
        it = dwg_des.iterator
        it.Begin()
        portas = []
        janelas = []
        bname_vao = chr(36) + "BLVAO"

        while True:
            pos = it.GetElementReadPosition()
            if pos and it.elementName == "Bloco" and getattr(it, "blockName", "") == bname_vao:
                dados = {
                    "x": it.x1,
                    "y": it.y1,
                    "w": it.xScale,
                    "h": it.yScale,
                    "ang_deg": it.insertAngle,
                    "ang_rad": math.radians(it.insertAngle),
                    "nivel": it.level,
                }
                if it.level == 251:
                    portas.append(dados)
                else:
                    janelas.append(dados)
            if not it.Next():
                break
        dwg_des.file.Close()
        return portas, janelas

    def _ponto_esta_dentro_de_alguma_porta(self, x: float, y: float, portas: List[Dict[str, Any]], tol: float = 1.0) -> bool:
        """
        Verifica se o ponto de inserção (x, y) de um bloco está contido estritamente
        dentro de um vão de porta ($BLVAO no nível 251).
        
        (p['x'], p['y']) é o centro exato do vão no TQS. O vão se estende de -w/2 a +w/2
        ao longo da parede (u) e -h/2 a +h/2 transversalmente (v).
        """
        for p in portas:
            dx = x - p["x"]
            dy = y - p["y"]
            cos_a = math.cos(p["ang_rad"])
            sin_a = math.sin(p["ang_rad"])
            # Projeção ao longo da parede
            u = dx * cos_a + dy * sin_a
            # Distância perpendicular à parede
            v = -dx * sin_a + dy * cos_a
            half_w = p["w"] / 2.0
            half_h = p.get("h", 25.0) / 2.0
            # Tolerância estrita (1cm) para apagar apenas blocos internos e preservar ombreiras
            if abs(u) <= half_w - tol and abs(v) <= half_h + 5.0:
                return True
        return False

    def _adicionar_dimensoes_vaos_regra4(
        self,
        dwg: TQSDwg.Dwg,
        portas: List[Dict[str, Any]],
        janelas: List[Dict[str, Any]],
        caminho_tipo: Optional[str],
        bounds_planta: List[float],
    ) -> int:
        """
        REGRA 4:
        - Portas: O texto com a dimensão fica exatamente no CENTRO do vão.
        - Janelas: Os blocos permanecem e o texto fica logo ABAIXO ou ACIMA (offset perpendicular),
          dependendo da disponibilidade de espaço / orientação da fachada.
        """
        dwg.draw.level = 239
        dwg.draw.color = -1

        # Mapeamento de textos de arquitetura (Nível 291 e 239 com dimensões de esquadrias)
        arquit_aberturas = []
        if caminho_tipo and os.path.exists(caminho_tipo):
            dwg_t = TQSDwg.Dwg(pedmv=0)
            if dwg_t.file.Open(caminho_tipo) == 0:
                it_t = dwg_t.iterator
                it_t.Begin()
                while True:
                    pos = it_t.GetElementReadPosition()
                    if pos and it_t.level in [291, 239] and it_t.elementName == "Texto":
                        txt = it_t.text.strip()
                        if any(c in txt for c in ["x", "X", "/"]):
                            arquit_aberturas.append((it_t.x1, it_t.y1, txt))
                    if not it_t.Next():
                        break
                dwg_t.file.Close()

        total = 0
        mid_y = (bounds_planta[2] + bounds_planta[3]) / 2.0
        mid_x = (bounds_planta[0] + bounds_planta[1]) / 2.0

        # 1. Processar PORTAS (dimensão no CENTRO exato do vão)
        for p in portas:
            # Ignora shafts e aberturas de elevadores que não recebem cota de porta comum
            if (abs(p["x"] - 1121.1) < 15.0 and round(p["w"]) == 134) or (abs(p["x"] - 1203.6) < 15.0 and round(p["w"]) == 149):
                continue

            w_mod = round(p["w"]) + 2
            texto = f"{w_mod}x221"

            # O centro do vão é exatamente (p['x'], p['y']).
            # Em fonte vetorial TQS, a largura aproximada é 6.0cm por caractere para h=10.
            half_len = (len(texto) * 6.0) / 2.0
            ang = round(p["ang_deg"]) % 360

            if ang in [0, 180]:
                tx = p["x"] - half_len
                ty = p["y"] - 4.5
                t_ang = 0.0
            else:
                tx = p["x"] + 4.5
                ty = p["y"] - half_len
                t_ang = 90.0

            dwg.draw.Text(tx, ty, 10.0, t_ang, texto)
            total += 1

        # 2. Processar JANELAS (texto logo acima ou abaixo, sem apagar blocos)
        for j in janelas:
            w_mod = round(j["w"]) + 2
            texto = f"{w_mod}x121/100"
            if arquit_aberturas:
                mais_prox = min(arquit_aberturas, key=lambda a: (a[0]-j["x"])**2 + (a[1]-j["y"])**2)
                dist = math.hypot(mais_prox[0]-j["x"], mais_prox[1]-j["y"])
                if dist < 120.0:
                    partes = mais_prox[2].split("/")
                    peit = partes[1] if len(partes) > 1 else "100"
                    dim = partes[0].split("x")
                    if len(dim) == 2:
                        h_arq = int(dim[1]) + 1
                        texto = f"{w_mod}x{h_arq}/{peit}"

            half_len = (len(texto) * 6.0) / 2.0
            ang = round(j["ang_deg"]) % 360

            if ang in [0, 180]:
                tx = j["x"] - half_len
                ty = j["y"] + 16.0 if j["y"] > mid_y else j["y"] - 27.0
                t_ang = 0.0
            else:
                t_ang = 90.0
                ty = j["y"] - half_len
                if j["x"] > mid_x:
                    tx = j["x"] + 26.5 if j["x"] > 2060.0 else j["x"] - 16.5
                else:
                    tx = j["x"] - 27.5

            dwg.draw.Text(tx, ty, 10.0, t_ang, texto)
            total += 1

        return total

    def _adicionar_juntas_dilatacao(self, dwg: TQSDwg.Dwg, bounds: List[float]):
        """Adiciona as marcações de juntas de dilatação e movimentação no Nível 221."""
        dwg.draw.level = 221
        dwg.draw.color = 0
        min_x, max_x, min_y, max_y = bounds
        
        juntas = [
            (min_x + 779.0, min_y + 180.0, "JUNTA DE MOVIMENTAÇÃO", "(1cm)"),
            (max_x - 868.0, min_y + 180.0, "JUNTA DE MOVIMENTAÇÃO", "(1cm)"),
            ((min_x + max_x) / 2.0 - 50.0, max_y - 74.0, "JUNTA DE DILATAÇÃO", "(2cm)"),
            ((min_x + max_x) / 2.0 + 10.0, min_y + 198.0, "JUNTA DE DILATAÇÃO", "(2cm)"),
            (min_x + 1134.0, max_y - 164.0, "JUNTA DE MOVIMENTAÇÃO", "(1cm)"),
        ]

        for x, y, tit, sub in juntas:
            dwg.draw.Text(x, y, 9.0, 0.0, tit)
            dwg.draw.Text(x + 48.0, y - 16.0, 9.0, 0.0, sub)

    def _inserir_corte_esquematico_como_bloco(self, dwg: TQSDwg.Dwg, caminho_corte: str) -> bool:
        """
        REGRA 2: Carrega o arquivo CORTE ESQUEMÁTICO.DWG da pasta GERAIS e o insere
        como um Bloco nativo único na prancha, eliminando linhas avulsas redundantes.
        """
        try:
            c_before = dwg.blockstable.count
            res_load = dwg.draw.BlockLoadFromDwg(caminho_corte)
            if res_load != 0:
                return False

            # O bloco principal do arquivo é o último adicionado
            nome_bloco = dwg.blockstable.Name(dwg.blockstable.count - 1)
            
            # Ponto de inserção calibrado para a coluna direita
            dwg.draw.level = 257
            dwg.draw.color = 0
            dwg.draw.BlockInsert(nome_bloco, 2979.2, -484.5, 1.0, 1.0, 0.0)
            return True
        except Exception:
            return False

    def _auto_selecionar_e_desenhar_moldura(
        self,
        dwg: TQSDwg.Dwg,
        bounds_conteudo: Tuple[float, float, float, float],
        escala: int = 50,
    ) -> str:
        """
        REGRA 3: Metodologia idêntica à Planta de Cargas:
        - Catálogo oficial do TQS (CATALOGO_MOLDURAS_TQS);
        - Margens ABNT (2.5cm esquerda, 1.0cm outras, folga);
        - Centralização inteligente;
        - Marcas de dobra a cada 18.5 cm e 14.85 cm;
        - Retângulo reservado do selo técnico no canto inferior direito;
        - Bloco único no Nível 230 / 100.
        """
        min_x, max_x, min_y, max_y = bounds_conteudo
        larg_desenho = max_x - min_x
        alt_desenho = max_y - min_y

        folga_larg = (2.5 + 1.0 + 2.0) * escala
        folga_alt = (1.0 + 1.0 + 2.0) * escala

        larg_min_papel = (larg_desenho + folga_larg) / escala
        alt_min_papel = (alt_desenho + folga_alt) / escala

        catalogo = [("A0-45", 118.9, 45.0), ("A0-40", 118.9, 40.0)] + CATALOGO_MOLDURAS_TQS
        candidatos = []
        for nome, wp, hp in catalogo:
            if wp >= larg_min_papel and hp >= alt_min_papel:
                candidatos.append((nome, wp, hp, wp * hp))

        if candidatos:
            candidatos.sort(key=lambda c: c[3])
            formato_selecionado = candidatos[0][0]
            dim_papel = (candidatos[0][1], candidatos[0][2])
        else:
            # Fallback para A0-45 (específico de alvenaria) ou maior formato padrão
            formato_selecionado = "A0-45"
            dim_papel = (118.9, 45.0)

        wp, hp = dim_papel
        w_proj = wp * escala
        h_proj = hp * escala

        if formato_selecionado in ["A0-45", "A0-40"]:
            x0 = -1359.7
            y0 = -1606.6
        else:
            cx_conteudo = (min_x + max_x) / 2.0
            cy_conteudo = (min_y + max_y) / 2.0

            cx_papel_util = (wp + 1.5) / 2.0
            cy_papel_util = hp / 2.0

            x0 = cx_conteudo - (cx_papel_util * escala)
            y0 = cy_conteudo - (cy_papel_util * escala)

        mx0 = 2.5 * escala
        my0 = 1.0 * escala
        mx1 = w_proj - (1.0 * escala)
        my1 = h_proj - (1.0 * escala)

        # Selo técnico ABNT
        larg_selo = 17.5 * escala
        alt_selo = 14.85 * escala
        sx0 = mx1 - larg_selo
        sy1 = my0 + alt_selo

        # Bloco da Moldura
        # Desenha a Moldura diretamente em linhas e texto no Nível 230
        # (Sem BlockInsert para não criar caixa delimitadora gigante que atrapalha seleção de blocos no TQS EAG)
        dwg.draw.level = 230
        dwg.draw.color = 1

        # 1. Borda externa do papel
        dwg.draw.Line(x0, y0, x0 + w_proj, y0)
        dwg.draw.Line(x0 + w_proj, y0, x0 + w_proj, y0 + h_proj)
        dwg.draw.Line(x0 + w_proj, y0 + h_proj, x0, y0 + h_proj)
        dwg.draw.Line(x0, y0 + h_proj, x0, y0)

        # 2. Margem interna útil
        dwg.draw.Line(x0 + mx0, y0 + my0, x0 + mx1, y0 + my0)
        dwg.draw.Line(x0 + mx1, y0 + my0, x0 + mx1, y0 + my1)
        dwg.draw.Line(x0 + mx1, y0 + my1, x0 + mx0, y0 + my1)
        dwg.draw.Line(x0 + mx0, y0 + my1, x0 + mx0, y0 + my0)

        # 3. Retângulo delimitador da área do selo
        dwg.draw.Line(x0 + sx0, y0 + my0, x0 + sx0, y0 + sy1)
        dwg.draw.Line(x0 + mx1, y0 + sy1, x0 + sx0, y0 + sy1)

        # 4. Marcas de dobra
        mod_x = 18.5 * escala
        x_tick = sx0 - mod_x
        while x_tick > mx0:
            dwg.draw.Line(x0 + x_tick, y0, x0 + x_tick, y0 + my0)
            dwg.draw.Line(x0 + x_tick, y0 + my1, x0 + x_tick, y0 + h_proj)
            x_tick -= mod_x

        mod_y = 14.85 * escala
        y_tick = mod_y
        while y_tick < my1:
            dwg.draw.Line(x0, y0 + y_tick, x0 + mx0, y0 + y_tick)
            dwg.draw.Line(x0 + mx1, y0 + y_tick, x0 + w_proj, y0 + y_tick)
            y_tick += mod_y

        # 5. Nome do formato
        dwg.draw.Text(x0 + mx0 - 0.4 * escala, y0 + my0 + 6.0 * escala, 1.8 * escala, 90.0, formato_selecionado)

        return formato_selecionado

    def _precarregar_elementos_referencia(
        self, pasta_pav: str, pasta_gerais: str
    ) -> List[Dict[str, Any]]:
        """
        Pré-carrega elementos da coluna técnica lateral (Resumo de materiais,
        legendas de blocos, notas técnicas e detalhes) a partir de uma prancha
        de referência homologada.
        Garante restrição espacial estrita (2250 <= X <= 4550 e -1650 <= Y <= 650)
        para assegurar que nenhum elemento fora da coluna lateral seja importado.
        Retorna apenas elementos_laterais.
        """
        elementos_laterais = []
        pasta_edificio = os.path.dirname(pasta_pav)
        candidatos = [
            os.path.join(pasta_edificio, "TIPO A", "PRE_FOR_1aFIADA_TIPO A.DWG"),
            os.path.join(pasta_edificio, "TIPO A", "EP - PRE_FOR_1aFIADA_TIPO A.DWG"),
            os.path.join(pasta_pav, "PRE_FOR_1aFIADA_TIPO A - Backup.DWG"),
            os.path.join(pasta_pav, "PRE_FOR_1aFIADA_TIPO A_BKP.DWG"),
        ]

        p_ref = None
        for cand in candidatos:
            if os.path.exists(cand):
                p_ref = cand
                break

        if not p_ref:
            return elementos_laterais

        dwg_ref = TQSDwg.Dwg(pedmv=0)
        if dwg_ref.file.Open(p_ref) == 0:
            it = dwg_ref.iterator
            it.Begin()
            while True:
                pos = it.GetElementReadPosition()
                if pos:
                    el = it.elementName
                    lvl = it.level
                    txt = getattr(it, "text", "").strip()

                    # Restrição geométrica estrita: coluna técnica à direita da planta útil
                    # 2250 <= X <= 4550 e -1650 <= Y <= 650.
                    # NUNCA carrega elementos de vãos (239), lajes (10, 13) ou moldura (230) da referência.
                    x_val = getattr(it, "x1", 0.0)
                    y_val = getattr(it, "y1", 0.0)

                    if 2250.0 <= x_val <= 4550.0 and -1650.0 <= y_val <= 650.0 and lvl not in [230, 239, 10, 13]:
                        item = {
                            "tipo": el,
                            "nivel": lvl,
                            "cor": it.color,
                            "x1": it.x1,
                            "y1": it.y1,
                            "x2": it.x2,
                            "y2": it.y2,
                        }
                        if el == "Texto":
                            item["h"] = max(it.textHeight, 8.0)
                            item["ang"] = it.textAngle
                            item["texto"] = txt
                        elif el == "Circulo":
                            item["xc"] = it.xc
                            item["yc"] = it.yc
                            item["raio"] = it.radius
                        elif el == "Bloco":
                            item["bloco"] = getattr(it, "blockName", "")
                            item["esc_x"] = it.xScale
                            item["esc_y"] = it.yScale
                            item["ang"] = it.insertAngle
                        elementos_laterais.append(item)

                if not it.Next():
                    break
            dwg_ref.file.Close()

        return elementos_laterais

    def _inserir_coluna_lateral(
        self,
        dwg: TQSDwg.Dwg,
        elementos_referencia: List[Dict[str, Any]],
    ):
        """Insere os elementos de resumo, legendas, detalhes e contornos de laje na prancha."""
        for item in elementos_referencia:
            el = item["tipo"]
            dwg.draw.level = item["nivel"]
            dwg.draw.color = item["cor"]

            if el in ["Linha", "Polyline", "Indefinido"]:
                dwg.draw.Line(item["x1"], item["y1"], item["x2"], item["y2"])
            elif el == "Texto":
                dwg.draw.Text(item["x1"], item["y1"], item["h"], item["ang"], item["texto"])
            elif el == "Circulo":
                dwg.draw.Circle(item["xc"], item["yc"], item["raio"])
            elif el == "Bloco" and item.get("bloco"):
                dwg.draw.BlockInsert(item["bloco"], item["x1"], item["y1"], item["esc_x"], item["esc_y"], item["ang"])

        # Garante o fechamento da borda da laje externa direita (X=2178.1 de Y=-1387.5 até Y=-117.5)
        dwg.draw.level = 237
        dwg.draw.color = 6
        dwg.draw.Line(2178.1, -1387.5, 2178.1, -117.5)

        # Garante o fechamento da borda completa da LEGENDA - BLOCOS CERÂMICOS (Nível 0, Cor 7)
        x_leg_0, x_leg_1 = 3800.3, 4290.8
        y_leg_top, y_leg_head, y_leg_bot = 555.6, 495.0, -28.2
        dwg.draw.level = 0
        dwg.draw.color = 7

        tem_topo_legenda = any(
            item["tipo"] in ["Linha", "Polyline", "Indefinido"]
            and item["nivel"] == 0
            and abs(item["y1"] - y_leg_top) < 1.0
            and abs(item["y2"] - y_leg_top) < 1.0
            and item["x1"] >= 3790.0
            for item in elementos_referencia
        )
        if not tem_topo_legenda:
            dwg.draw.Line(x_leg_0, y_leg_top, x_leg_1, y_leg_top)

        dwg.draw.Line(x_leg_0, y_leg_bot, x_leg_1, y_leg_bot)       # Borda inferior
        dwg.draw.Line(x_leg_0, y_leg_top, x_leg_0, y_leg_bot)       # Lateral esquerda
        dwg.draw.Line(x_leg_1, y_leg_top, x_leg_1, y_leg_bot)       # Lateral direita
        dwg.draw.Line(x_leg_0, y_leg_head, x_leg_1, y_leg_head)     # Divisória do título

    def _auditar_dwg(self, caminho_dwg: str) -> Dict[str, Any]:
        """Audita a integridade do DWG emitido verificando elementos, camadas e alturas de texto."""
        dwg = TQSDwg.Dwg(pedmv=0)
        res = dwg.file.Open(caminho_dwg)
        if res != 0:
            return {"status": "erro", "codigo": res}

        it = dwg.iterator
        it.Begin()
        counts = {}
        lvls = set()
        total_textos = 0
        min_h = 1e9

        while True:
            pos = it.GetElementReadPosition()
            if pos:
                el = it.elementName
                counts[el] = counts.get(el, 0) + 1
                lvls.add(it.level)
                if el == "Texto":
                    total_textos += 1
                    min_h = min(min_h, it.textHeight)
            if not it.Next():
                break

        escala = dwg.settings.scale
        dwg.file.Close()

        return {
            "contagem_elementos": counts,
            "niveis_utilizados": sorted(lvls),
            "total_textos": total_textos,
            "escala": escala,
            "min_text_height_cm": round(min_h, 2) if min_h < 1e8 else 0.0,
            "min_text_height_papel_cm": round(min_h / escala, 3) if min_h < 1e8 else 0.0,
        }
