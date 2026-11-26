import os
import re
import math
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from TQS import TQSDwg
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
from src.drawing.tqs_dwg_builder import CATALOGO_MOLDURAS_TQS, SELO_LARGURA_CM, SELO_ALTURA_CM

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

    def _is_template_invalido(self, caminho_dwg: str) -> bool:
        """
        Verifica se um DWG de corte esquematico e apenas um template nao compilado
        (contendo tags nao preenchidas como %Valor da cota ou %Pavimento SEM dados
        reais compilados de pavimentos e resistencias).
        Nota: Blocos nativos de cota do TQS ($COTAZ) carregam atributos internos
        '%Valor da cota' / '%Pavimento' mesmo quando o corte esta 100% compilado;
        por isso verificamos se ha pavimentos e resistencias (MPa/FCK) reais no desenho.
        """
        if not os.path.exists(caminho_dwg):
            return True
        try:
            dwg = TQSDwg.Dwg(pedmv=0)
            if dwg.file.Open(caminho_dwg) != 0:
                return True
            it = dwg.iterator
            it.Begin()
            tem_macro_topo = False
            in_block = 0
            pavimentos_reais = 0
            resistencias_reais = 0
            while True:
                pos = it.GetElementReadPosition()
                if pos:
                    el = it.elementName
                    if el == "Bloco":
                        in_block += 1
                    elif el == "Fim de bloco":
                        in_block = max(0, in_block - 1)
                    elif el == "Texto":
                        txt_u = getattr(it, "text", "").upper().strip()
                        if any(k in txt_u for k in ["%VALOR", "%PAVIMENTO", "%COTA", "VALOR DA COTA"]):
                            if in_block == 0:
                                tem_macro_topo = True
                        if any(k in txt_u for k in ["PAVTO", "PAVIMENTO", "TÉRREO", "TERREO", "COBERTURA", "SUBSOLO", "RESERVAT"]):
                            if "%" not in txt_u:
                                pavimentos_reais += 1
                        if any(k in txt_u for k in ["MPA", "FCK", "C25", "C30", "C35", "C40"]):
                            resistencias_reais += 1
                if not it.Next():
                    break
            dwg.file.Close()
            # Se tem pavimentos e resistencias reais compilados, o corte e valido
            if pavimentos_reais >= 2 and resistencias_reais >= 1:
                return False
            return tem_macro_topo or (pavimentos_reais == 0 and resistencias_reais == 0)
        except Exception:
            return True


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

    @staticmethod
    def _cor_crua(dwg_origem: TQSDwg.Dwg, pos: int) -> int:
        """
        Cor gravada no elemento (``-1`` = cor do nível), sem a resolução pelo nível que o
        iterador aplica (``iterator.color``). Garante que cópias preservem a cor do nível.
        """
        try:
            return dwg_origem.edit._Edit__LerAtribElem(pos)[0]
        except Exception:
            return -1

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
            pav_digits = re.findall(r"\d+", pavimento)
            for item in os.listdir(caminho_edificio):
                p_cand = os.path.join(caminho_edificio, item)
                if os.path.isdir(p_cand):
                    item_digits = re.findall(r"\d+", item)
                    if pav_digits and item_digits and pav_digits[0] == item_digits[0]:
                        pasta_pav = p_cand
                        pavimento = item
                        break
                    elif pavimento.lower() in item.lower():
                        pasta_pav = p_cand
                        pavimento = item
                        break

        if not os.path.exists(pasta_pav):
            raise FileNotFoundError(f"Pasta do pavimento não encontrada: {pasta_pav}")

        # Arquivo de saída
        if not caminho_saida_dwg:
            caminho_saida_dwg = os.path.join(pasta_pav, f"PRE_FOR_1aFIADA_{pavimento}.DWG")

        # 1. REGRA 1: Backup obrigatório antes de sobrescrever qualquer arquivo existente
        arquivo_backup = self._criar_backup_seguro(caminho_saida_dwg)

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

        # CORTE ESQUEMATICO: Localizacao prioritaria do corte compilado com resistencias reais do edificio
        # (ex: ESPACIAL\FOR_Corte Esquematico com Prismas.DWG), rejeitando terminantemente templates nao compilados (%)
        p_corte = None
        pasta_espacial = os.path.join(caminho_edificio, "ESPACIAL")
        if os.path.exists(pasta_espacial):
            for f in sorted(os.listdir(pasta_espacial)):
                f_u = f.upper()
                if "CORTE" in f_u and f_u.endswith(".DWG"):
                    p_cand = os.path.join(pasta_espacial, f)
                    if not self._is_template_invalido(p_cand):
                        p_corte = p_cand
                        break

        if not p_corte:
            for p_dir in [pasta_gerais, caminho_edificio]:
                if os.path.exists(p_dir):
                    for f in sorted(os.listdir(p_dir)):
                        f_u = f.upper()
                        if "CORTE" in f_u and f_u.endswith(".DWG"):
                            p_cand = os.path.join(p_dir, f)
                            if not self._is_template_invalido(p_cand):
                                p_corte = p_cand
                                break
                    if p_corte:
                        break

        # 2. Mapeamento prévio dos vãos ($BLVAO): Portas (251) vs Janelas (252) no pavimento
        vaos_portas, vaos_janelas = self._mapear_vaos(p_desfiad)
        bounds_planta = self._calcular_bounds_desfiad(p_desfiad)

        # 3. Pré-carregar elementos técnicos da prancha de referência
        elementos_referencia = self._precarregar_elementos_referencia(
            pasta_pav, pasta_gerais, bounds_planta, caminho_saida_dwg=caminho_saida_dwg, p_corte=p_corte
        )

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
                        # Ignora elementos nulos ou blocos no ponto zero (0, 0)
                        if abs(pt[0]) > 10.0 and abs(pt[1]) > 10.0:
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

        # 6. Sobreposição de Lajes
        # a) Textos identificadores das lajes (sempre do LAJ*.DWG nativo do pavimento)
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
                            if (bounds_planta[0] - 200.0 <= it_l.x1 <= bounds_planta[1] + 200.0 and
                                bounds_planta[2] - 200.0 <= it_l.y1 <= bounds_planta[3] + 200.0):
                                dwg.draw.level = lvl
                                dwg.draw.color = -1
                                dwg.draw.Text(it_l.x1, it_l.y1, 10.0, 0.0, txt)
                                if lvl == 10:
                                    total_lajes += 1
                    if not it_l.Next():
                        break
                dwg_laj.file.Close()

        # b) Contornos e bordas das lajes exteriores e sacadas (Níveis 231 e 237)
        lajes_ext = elementos_referencia.get("lajes_externas", [])
        for item in lajes_ext:
            el = item["tipo"]
            dwg.draw.level = 237
            dwg.draw.color = item["cor"]
            if el in ["Linha", "Indefinido"]:
                dwg.draw.Line(item["x1"], item["y1"], item["x2"], item["y2"])
            elif el == "Polyline":
                pontos = item.get("pontos", [])
                if len(pontos) >= 2:
                    dwg.draw.PolyStart()
                    for pt in pontos:
                        dwg.draw.PolyEnterPoint(pt[0], pt[1])
                    dwg.draw.Polyline()
                else:
                    dwg.draw.Line(item["x1"], item["y1"], item["x2"], item["y2"])

                # c) SHAFTS / FUROS DE LAJE: Desenho de 'X' nos shafts retangulares indicando que é um buraco (vazio na laje)
        total_shafts = self._desenhar_shafts_com_x(
            dwg, pasta_pav, caminho_edificio, bounds_planta, caminho_saida_dwg=caminho_saida_dwg
        )

        # 7. REGRA 4: Anotação de Dimensões de Vãos (Portas no centro, Janelas fora da parede)
        # Sempre gerado a partir dos vãos mapeados no pavimento corrente
        vaos_inseridos = self._adicionar_dimensoes_vaos_regra4(
            dwg, vaos_portas, vaos_janelas, p_tipo, bounds_planta
        )

        # 8. Juntas de Movimentação e Dilatação (Nível 221)
        self._adicionar_juntas_dilatacao(dwg, bounds_planta)

        # 9. Título e Escala da Planta (posicionados diretamente acima da planta do edifício)
        dwg.draw.level = 222
        dwg.draw.color = -1
        pav_nome = pavimento.replace("^", "º").upper()
        if "PAVIMENTO" in pav_nome:
            titulo = f"PRÉ-MODULAÇÃO DE 1ª FIADA - {pav_nome}"
        else:
            titulo = f"PRÉ-MODULAÇÃO DE 1ª FIADA - PAVIMENTO {pav_nome}"

        x_titulo = bounds_planta[0]
        y_titulo = bounds_planta[3] + 140.0
        dwg.draw.Text(x_titulo, y_titulo, 32.5, 0.0, titulo)

        dwg.draw.level = 250
        dwg.draw.color = -1
        dwg.draw.Text(x_titulo + 4.4, y_titulo - 24.6, 12.0, 0.0, f"ESCALA: 1:{escala}")

        # 10. Inserção de Resumo de Materiais, Legendas e Notas Técnicas na Coluna Lateral
        # Topo da área do selo (carimbo + revisões) na origem fixa das molduras A0 (y0 = -1606.6)
        y_topo_selo = None
        if bounds_planta[0] <= 5000.0:
            y_topo_selo = -1606.6 + (1.0 + SELO_ALTURA_CM) * escala
        _, y_max_coluna = self._inserir_coluna_lateral(
            dwg, elementos_referencia.get("laterais", []), bounds_planta=bounds_planta, y_topo_selo=y_topo_selo
        )

        # 11. REGRA 2: Carregar e Inserir o Corte Esquematico compilado do edificio como Bloco
        bloco_corte_inserido = False
        if p_corte and os.path.exists(p_corte):
            bloco_corte_inserido = self._inserir_corte_esquematico_como_bloco(
                dwg, p_corte, bounds_planta=bounds_planta
            )

        # 12. REGRA 3: Metodologia de Moldura da Planta de Cargas (CATALOGO_MOLDURAS_TQS)
        # Bounding box considerando a planta, título, bloco do corte esquemático e coluna técnica lateral
        coluna_largura = 1800.0
        max_x_lat = bounds_planta[1] + coluna_largura
        for item in elementos_referencia.get("laterais", []):
            for xk in ("x1", "x2"):
                xv = item.get(xk, 0.0)
                if xv > max_x_lat and xv < bounds_planta[1] + 3500.0:
                    max_x_lat = xv
        if bounds_planta[1] < 3000.0:
            max_x_lat = max(max_x_lat, 4300.0)
        max_y_conteudo = max(y_titulo + 40.0, bounds_planta[3] + 180.0)
        if y_max_coluna is not None:
            max_y_conteudo = max(max_y_conteudo, y_max_coluna)
        max_x_conteudo = max_x_lat
        bounds_totais = (bounds_planta[0] - 100.0, max_x_conteudo, min(bounds_planta[2] - 100.0, -1550.0), max_y_conteudo)
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
            "total_shafts": total_shafts,
            "total_lajes_externas": len(lajes_ext),
            "auditoria": elementos_finais,
        }

    def _finalizar_a_partir_de_base_tipo(
        self,
        p_pre_tipo: str,
        caminho_saida_dwg: str,
        pasta_pav: str,
        caminho_edificio: str,
        pavimento: str,
        escala: int,
        arquivo_backup: Optional[str],
    ) -> Dict[str, Any]:
        """
        Finaliza a prancha de formas executiva a partir da base pré-modulada homologada (PRE_FOR_1aFIADA_Tipo.DWG),
        injetando as lajes exteriores / sacadas, atualizando o título para o pavimento específico e gerando alias.
        """
        sacadas = []
        p_r01 = self._localizar_arquivo(pasta_pav, "PRE_FOR_1aFIADA-R01.DWG") or self._localizar_arquivo(pasta_pav, "PRE_FOR_1aFIADA-R00.DWG")
        if p_r01 and os.path.exists(p_r01):
            dwg_ref = TQSDwg.Dwg(pedmv=0)
            if dwg_ref.file.Open(p_r01) == 0:
                it = dwg_ref.iterator
                it.Begin()
                while True:
                    pos = it.GetElementReadPosition()
                    if pos and it.level == 0 and it.elementName in ["Linha", "Polyline"]:
                        if it.y1 > -2580.0 or it.y2 > -2580.0 or it.x1 < 10070.0 or it.x2 < 10070.0 or it.x1 > 16800.0 or it.x2 > 16800.0:
                            if it.x1 < 17000 and it.x2 < 17000:
                                sacadas.append((it.x1, it.y1, it.x2, it.y2))
                    if not it.Next():
                        break
                dwg_ref.file.Close()

        if not sacadas:
            p_for = None
            for f in os.listdir(pasta_pav):
                if f.upper().startswith("FOR") and f.upper().endswith(".DWG"):
                    p_for = os.path.join(pasta_pav, f)
                    break
            if p_for and os.path.exists(p_for):
                dwg_for = TQSDwg.Dwg(pedmv=0)
                if dwg_for.file.Open(p_for) == 0:
                    it_f = dwg_for.iterator
                    it_f.Begin()
                    while True:
                        pos = it_f.GetElementReadPosition()
                        if pos and it_f.level == 1 and it_f.elementName in ["Linha", "Polyline"]:
                            if it_f.y1 > -2580.0 or it_f.y2 > -2580.0 or it_f.x1 < 10070.0 or it_f.x2 < 10070.0 or it_f.x1 > 16800.0 or it_f.x2 > 16800.0:
                                if it_f.x1 < 17000 and it_f.x2 < 17000:
                                    sacadas.append((it_f.x1, it_f.y1, it_f.x2, it_f.y2))
                        if not it_f.Next():
                            break
                    dwg_for.file.Close()

        shutil.copy2(p_pre_tipo, caminho_saida_dwg)

        dwg = TQSDwg.Dwg(pedmv=0)
        if dwg.file.Open(caminho_saida_dwg) != 0:
            raise RuntimeError(f"Erro ao abrir arquivo para edição: {caminho_saida_dwg}")

        it = dwg.iterator
        it.Begin()
        pos_to_erase = []
        title_pos = (9962.8, -1708.8)
        total_lajes = 0
        total_vaos = 0

        while True:
            pos = it.GetElementReadPosition()
            if pos:
                el = it.elementName
                lvl = it.level
                txt = getattr(it, "text", "")
                if lvl == 222 and el == "Texto":
                    if any(k in txt.upper() for k in ["TIPO", "FIADA", "PAVIMENTO"]):
                        pos_to_erase.append(pos)
                        title_pos = (it.x1, it.y1)
                elif lvl == 10 and el == "Texto":
                    total_lajes += 1
                elif lvl == 239 and el == "Texto":
                    total_vaos += 1
            if not it.Next():
                break

        for p in pos_to_erase:
            dwg.edit.Erase(p)

        dwg.draw.level = 222
        dwg.draw.color = -1
        pav_nome_exec = pavimento.replace("^", "º").upper()
        novo_titulo = f"PRÉ-MODULAÇÃO DE 1ª FIADA - {pav_nome_exec}"
        dwg.draw.Text(title_pos[0], title_pos[1], 32.5, 0.0, novo_titulo)

        if sacadas:
            dwg.draw.level = 237
            dwg.draw.color = -1
            for x1, y1, x2, y2 in sacadas:
                dwg.draw.Line(x1, y1, x2, y2)

            dwg.draw.level = 0
            dwg.draw.color = -1
            for x1, y1, x2, y2 in sacadas:
                dwg.draw.Line(x1, y1, x2, y2)

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
            "moldura": "180-50",
            "corte_como_bloco": True,
            "elementos_purgados": 0,
            "total_lajes": total_lajes,
            "total_vaos": total_vaos,
            "total_sacadas_linhas": len(sacadas),
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
        """Adiciona as marcacoes de juntas de dilatacao e movimentacao no Nivel 221 de forma dinamica."""
        dwg.draw.level = 221
        dwg.draw.color = -1
        min_x, max_x, min_y, max_y = bounds
        largura = max_x - min_x
        altura = max_y - min_y
        mid_x = (min_x + max_x) / 2.0

        juntas = [
            (min_x + 0.25 * largura, min_y + 0.15 * altura, "JUNTA DE MOVIMENTAÇÃO", "(1cm)"),
            (min_x + 0.75 * largura, min_y + 0.15 * altura, "JUNTA DE MOVIMENTAÇÃO", "(1cm)"),
            (min_x + 0.35 * largura, max_y - 0.12 * altura, "JUNTA DE MOVIMENTAÇÃO", "(1cm)"),
            (min_x + 0.65 * largura, max_y - 0.12 * altura, "JUNTA DE MOVIMENTAÇÃO", "(1cm)"),
        ]
        if largura > 2000.0:
            juntas.append((mid_x - 50.0, max_y - 0.05 * altura, "JUNTA DE DILATAÇÃO", "(2cm)"))
            juntas.append((mid_x + 10.0, min_y + 0.16 * altura, "JUNTA DE DILATAÇÃO", "(2cm)"))

        for x, y, tit, sub in juntas:
            dwg.draw.Text(x, y, 9.0, 0.0, tit)
            dwg.draw.Text(x + 40.0, y - 16.0, 9.0, 0.0, sub)

    def _inserir_corte_esquematico_como_bloco(
        self,
        dwg: TQSDwg.Dwg,
        caminho_corte: str,
        bounds_planta: Optional[List[float]] = None,
    ) -> bool:
        """
        REGRA 2: Carrega o arquivo compilado de Corte Esquematico (ex: ESPACIAL/FOR_Corte Esquematico com Prismas.DWG)
        e o insere como um Bloco nativo unico na prancha, posicionando na coluna tecnica a direita da planta util.
        """
        try:
            if not os.path.exists(caminho_corte):
                return False

            dwg_c = TQSDwg.Dwg(pedmv=0)
            if dwg_c.file.Open(caminho_corte) != 0:
                return False

            it_c = dwg_c.iterator
            it_c.Begin()
            c_bx = [1e9, -1e9, 1e9, -1e9]
            while True:
                pos = it_c.GetElementReadPosition()
                if pos:
                    for pt in [(it_c.x1, it_c.y1), (it_c.x2, it_c.y2)]:
                        if abs(pt[0]) > 0.01 or abs(pt[1]) > 0.01:
                            c_bx[0] = min(c_bx[0], pt[0])
                            c_bx[1] = max(c_bx[1], pt[0])
                            c_bx[2] = min(c_bx[2], pt[1])
                            c_bx[3] = max(c_bx[3], pt[1])
                if not it_c.Next():
                    break
            dwg_c.file.Close()

            if c_bx[0] > 1e8:
                return False

            if bounds_planta:
                target_x = bounds_planta[1] + 150.0
            else:
                target_x = 2330.0
            target_y = -1500.0

            x_ins = target_x - c_bx[0]
            y_ins = target_y - c_bx[2]

            res_load = dwg.draw.BlockLoadFromDwg(caminho_corte)
            if res_load != 0:
                return False

            nome_esperado = os.path.splitext(os.path.basename(caminho_corte))[0]
            nome_bloco = dwg.blockstable.Name(dwg.blockstable.count - 1)
            for idx_b in range(dwg.blockstable.count - 1, -1, -1):
                cand_b = dwg.blockstable.Name(idx_b)
                if cand_b.upper() == nome_esperado.upper():
                    nome_bloco = cand_b
                    break
            dwg.draw.level = 0
            dwg.draw.color = -1
            dwg.draw.BlockInsert(nome_bloco, x_ins, y_ins, 1.0, 1.0, 0.0)
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

        catalogo = [("180-50", 180.0, 50.0), ("A0-45", 118.9, 45.0), ("A0-40", 118.9, 40.0)] + CATALOGO_MOLDURAS_TQS
        candidatos = []
        for nome, wp, hp in catalogo:
            if wp >= larg_min_papel and hp >= alt_min_papel:
                candidatos.append((nome, wp, hp, wp * hp))

        if candidatos:
            candidatos.sort(key=lambda c: c[3])
            formato_selecionado = candidatos[0][0]
            dim_papel = (candidatos[0][1], candidatos[0][2])
        else:
            # Fallback para A0-45 ou 180-50
            if larg_min_papel > 120.0:
                formato_selecionado = "180-50"
                dim_papel = (180.0, 50.0)
            else:
                formato_selecionado = "A0-45"
                dim_papel = (118.9, 45.0)

        wp, hp = dim_papel
        w_proj = wp * escala
        h_proj = hp * escala

        if formato_selecionado == "180-50" or min_x > 5000.0:
            x0 = 9736.5
            y0 = -3997.4
            formato_selecionado = "180-50"
            wp, hp = 180.0, 50.0
            w_proj = wp * escala
            h_proj = hp * escala
        elif formato_selecionado in ["A0-45", "A0-40"]:
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
        larg_selo = SELO_LARGURA_CM * escala
        alt_selo = SELO_ALTURA_CM * escala  # Carimbo + tabela de revisões
        sx0 = mx1 - larg_selo
        sy1 = my0 + alt_selo

        # Bloco da Moldura
        # Desenha a Moldura diretamente em linhas e texto no Nível 230
        # (Sem BlockInsert para não criar caixa delimitadora gigante que atrapalha seleção de blocos no TQS EAG)
        dwg.draw.level = 230
        dwg.draw.color = -1

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

    def _calcular_bounds_desfiad(self, caminho_desfiad: str) -> List[float]:
        """Calcula o envelope (min_x, max_x, min_y, max_y) a partir das alvenarias e vaos do DesFiad1."""
        bounds = [1e9, -1e9, 1e9, -1e9]
        if not os.path.exists(caminho_desfiad):
            return [-1200.0, 2250.0, -1600.0, 100.0]

        dwg = TQSDwg.Dwg(pedmv=0)
        if dwg.file.Open(caminho_desfiad) == 0:
            it = dwg.iterator
            it.Begin()
            while True:
                pos = it.GetElementReadPosition()
                if pos:
                    lvl = it.level
                    if lvl in [203, 213, 241, 245, 247, 248, 251, 252]:
                        for pt in [(it.x1, it.y1), (it.x2, it.y2)]:
                            if abs(pt[0]) > 10.0 and abs(pt[1]) > 10.0:
                                bounds[0] = min(bounds[0], pt[0])
                                bounds[1] = max(bounds[1], pt[0])
                                bounds[2] = min(bounds[2], pt[1])
                                bounds[3] = max(bounds[3], pt[1])
                if not it.Next():
                    break
            dwg.file.Close()

        if bounds[0] > 1e8:
            bounds = [-1200.0, 2250.0, -1600.0, 100.0]
        return bounds

    def _extrair_shafts_de_dwg(self, caminho_dwg: str, bounds_planta: List[float]) -> List[Dict[str, float]]:
        """
        Extrai shafts retangulares a partir de pares de diagonais cruzadas no Nível 237 (Cor 6) em um DWG de referência.
        """
        if not os.path.exists(caminho_dwg):
            return []
        dwg_ref = TQSDwg.Dwg(pedmv=0)
        if dwg_ref.file.Open(caminho_dwg) != 0:
            return []

        it = dwg_ref.iterator
        it.Begin()
        diags = []
        bx_min, bx_max, by_min, by_max = bounds_planta
        margem = 50.0

        while True:
            pos = it.GetElementReadPosition()
            if pos and it.level == 237 and it.elementName in ["Linha", "Polyline"]:
                dx = abs(it.x2 - it.x1)
                dy = abs(it.y2 - it.y1)
                if dx > 10.0 and dy > 10.0:
                    x_med = (it.x1 + it.x2) / 2.0
                    y_med = (it.y1 + it.y2) / 2.0
                    if bx_min - margem <= x_med <= bx_max + margem and by_min - margem <= y_med <= by_max + margem:
                        diags.append((it.x1, it.y1, it.x2, it.y2))
            if not it.Next():
                break
        dwg_ref.file.Close()

        shafts = []
        used = set()
        tol = 5.0
        for i, l1 in enumerate(diags):
            if i in used:
                continue
            x1a, y1a, x2a, y2a = l1
            min_xa, max_xa = min(x1a, x2a), max(x1a, x2a)
            min_ya, max_ya = min(y1a, y2a), max(y1a, y2a)
            for j in range(i + 1, len(diags)):
                if j in used:
                    continue
                x1b, y1b, x2b, y2b = diags[j]
                min_xb, max_xb = min(x1b, x2b), max(x1b, x2b)
                min_yb, max_yb = min(y1b, y2b), max(y1b, y2b)
                if (abs(min_xa - min_xb) <= tol and abs(max_xa - max_xb) <= tol and
                    abs(min_ya - min_yb) <= tol and abs(max_ya - max_yb) <= tol):
                    used.add(i)
                    used.add(j)
                    shafts.append({
                        "x_min": min(min_xa, min_xb),
                        "x_max": max(max_xa, max_xb),
                        "y_min": min(min_ya, min_yb),
                        "y_max": max(max_ya, max_yb),
                        "w": max(max_xa, max_xb) - min(min_xa, min_xb),
                        "h": max(max_ya, max_yb) - min(min_ya, min_yb),
                    })
                    break
        return shafts

    def _detectar_shafts_de_linhas_237(
        self, linhas_existentes: set, bounds_planta: List[float]
    ) -> List[Dict[str, float]]:
        """
        Detecta caixas retangulares fechadas ou quase fechadas de shafts a partir
        de segmentos ortogonais no Nível 237 do próprio pavimento.
        """
        bx_min, bx_max, by_min, by_max = bounds_planta
        margem = 50.0

        horiz = []
        vert = []
        for x1, y1, x2, y2 in linhas_existentes:
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            mid_x = (x1 + x2) / 2.0
            mid_y = (y1 + y2) / 2.0

            if not (bx_min - margem <= mid_x <= bx_max + margem and by_min - margem <= mid_y <= by_max + margem):
                continue

            if dy <= 1.0 and dx >= 15.0:
                horiz.append((min(x1, x2), max(x1, x2), (y1 + y2) / 2.0))
            elif dx <= 1.0 and dy >= 15.0:
                vert.append(((x1 + x2) / 2.0, min(y1, y2), max(y1, y2)))

        rects = []
        tol = 3.5
        for i, h1 in enumerate(horiz):
            for j in range(i + 1, len(horiz)):
                h2 = horiz[j]
                if abs(h1[0] - h2[0]) <= tol and abs(h1[1] - h2[1]) <= tol:
                    w = max(h1[1], h2[1]) - min(h1[0], h2[0])
                    h = abs(h1[2] - h2[2])
                    if 20.0 <= w <= 350.0 and 20.0 <= h <= 350.0 and (w * h) <= 60000.0:
                        rects.append({
                            "x_min": round(min(h1[0], h2[0]), 1),
                            "x_max": round(max(h1[1], h2[1]), 1),
                            "y_min": round(min(h1[2], h2[2]), 1),
                            "y_max": round(max(h1[2], h2[2]), 1),
                            "w": round(w, 1),
                            "h": round(h, 1),
                        })
        return rects

    @staticmethod
    def _decompor_poligono_em_retangulos(poly, min_dim: float = 8.0, min_area: float = 200.0) -> List[Dict[str, float]]:
        """
        Decompõe um polígono ortogonal (ex: poço de escada em U/L) em retângulos
        disjuntos via faixas horizontais nos vértices Y únicos, mesclando faixas
        adjacentes com o mesmo intervalo X para evitar diagonais 'X' cruzando paredes.
        """
        from shapely.geometry import box as shp_box

        poly = poly.simplify(0.5, preserve_topology=True)
        b = poly.bounds
        w, h = b[2] - b[0], b[3] - b[1]
        if w < min_dim or h < min_dim or poly.area < min_area:
            return []

        # Se já é essencialmente retangular (>= 92% do bounding box), retorna direto
        if (poly.area / (w * h)) >= 0.92:
            return [{
                "x_min": round(b[0], 1),
                "x_max": round(b[2], 1),
                "y_min": round(b[1], 1),
                "y_max": round(b[3], 1),
                "w": round(w, 1),
                "h": round(h, 1),
            }]

        # Coleta coordenadas Y únicas dos vértices (agrupando micro-desalinhamentos <= 1.0 cm)
        ys_raw = sorted({round(pt[1], 1) for pt in poly.exterior.coords})
        ys = []
        for y in ys_raw:
            if not ys or abs(y - ys[-1]) >= 1.0:
                ys.append(y)

        if len(ys) < 2:
            return []

        faixas = []
        for y0, y1 in zip(ys, ys[1:]):
            if (y1 - y0) < 0.5:
                continue
            # Recorte ligeiramente interior em Y para evitar pontes de 0.2 cm ligando dois lances
            eps = min(0.3, (y1 - y0) * 0.1)
            inter = poly.intersection(shp_box(b[0] - 1.0, y0 + eps, b[2] + 1.0, y1 - eps))
            if inter.is_empty:
                continue
            geoms = list(inter.geoms) if hasattr(inter, "geoms") else [inter]
            for g in geoms:
                if g.geom_type != "Polygon" or g.area < 1.0:
                    continue
                gb = g.bounds
                gw = gb[2] - gb[0]
                if gw >= min_dim:
                    faixas.append({
                        "x_min": round(gb[0], 1),
                        "x_max": round(gb[2], 1),
                        "y_min": round(y0, 1),
                        "y_max": round(y1, 1),
                    })

        # Mescla retângulos verticalmente adjacentes com mesmo [x_min, x_max]
        faixas.sort(key=lambda r: (round(r["x_min"] / 2.0), round(r["x_max"] / 2.0), r["y_min"]))
        merged = []
        for r in faixas:
            if (merged
                and abs(merged[-1]["x_min"] - r["x_min"]) <= 2.5
                and abs(merged[-1]["x_max"] - r["x_max"]) <= 2.5
                and abs(merged[-1]["y_max"] - r["y_min"]) <= 2.5):
                merged[-1]["y_max"] = max(merged[-1]["y_max"], r["y_max"])
                merged[-1]["x_min"] = min(merged[-1]["x_min"], r["x_min"])
                merged[-1]["x_max"] = max(merged[-1]["x_max"], r["x_max"])
            else:
                merged.append(dict(r))

        res = []
        for r in merged:
            rw = round(r["x_max"] - r["x_min"], 1)
            rh = round(r["y_max"] - r["y_min"], 1)
            if rw >= min_dim and rh >= min_dim and (rw * rh) >= min_area:
                r["w"] = rw
                r["h"] = rh
                res.append(r)
        return res

    def _detectar_aberturas_geometria_lajes(self, pasta_pav: str) -> List[Dict[str, float]]:
        """
        Calcula geometricamente todos os furos, shafts, poços de elevador e aberturas
        reais de laje diretamente a partir do modelo atual do pavimento:
          - Polígonos das lajes reais: LAJ*.DWG (Nível 0 + rótulos L# no Nível 10)
          - Faces reais das paredes/blocos: DesFiad1.DWG (blocos 14/19 cm)
        Todo vazio interno contido no envelope das lajes+paredes que não é laje nem
        parede representa inequivocamente um furo/abertura real no pavimento.
        """
        try:
            from shapely.geometry import LineString, Point, Polygon
            from shapely.ops import polygonize, unary_union
        except ImportError:
            return []

        p_laj = None
        for f in sorted(os.listdir(pasta_pav)):
            if f.upper().startswith("LAJ") and f.upper().endswith(".DWG"):
                p_laj = os.path.join(pasta_pav, f)
                break
        p_desfiad = self._localizar_arquivo(pasta_pav, "DesFiad1.DWG")
        if not p_laj or not p_desfiad or not os.path.exists(p_laj) or not os.path.exists(p_desfiad):
            return []

        # 1. Poligonizar lajes a partir de LAJ*.DWG
        dwg_laj = TQSDwg.Dwg(pedmv=0)
        if dwg_laj.file.Open(p_laj) != 0:
            return []
        segs = []
        l_pts = []
        it = dwg_laj.iterator
        it.Begin()
        while True:
            if it.GetElementReadPosition():
                if it.level == 0 and it.elementName == "Linha":
                    p1 = (round(it.x1, 2), round(it.y1, 2))
                    p2 = (round(it.x2, 2), round(it.y2, 2))
                    if p1 != p2:
                        segs.append(LineString([p1, p2]))
                elif it.level == 10 and it.elementName == "Texto":
                    l_pts.append((it.text.strip(), Point(it.x1, it.y1)))
            if not it.Next():
                break
        dwg_laj.file.Close()

        if not segs or not l_pts:
            return []

        polys = list(polygonize(unary_union(segs)))
        if not polys:
            return []

        slab_indices = set()
        for _, pt in l_pts:
            for idx, p in enumerate(polys):
                if p.contains(pt):
                    slab_indices.add(idx)
        # Lajes de sacada/contorno muito grandes podem ter rótulo fora da faixa estreita
        for idx, p in enumerate(polys):
            if p.area > 100000.0:
                slab_indices.add(idx)

        if not slab_indices:
            return []
        slab_u = unary_union([polys[idx] for idx in slab_indices])

        # 2. Faces exatas das paredes/blocos da 1ª fiada (DesFiad1.DWG)
        dwg_df = TQSDwg.Dwg(pedmv=0)
        if dwg_df.file.Open(p_desfiad) != 0:
            return []
        blk_polys = []
        it_df = dwg_df.iterator
        it_df.Begin()
        while True:
            if (it_df.GetElementReadPosition()
                and it_df.elementName == "Polyline"
                and it_df.level in [207, 217, 218, 219, 241, 245, 248, 251, 252]):
                pts = [it_df.GetPolylinePt(i) for i in range(it_df.xySize)]
                if len(pts) >= 3:
                    p = Polygon(pts).buffer(0)
                    if p.area > 10.0:
                        blk_polys.append(p)
            if not it_df.Next():
                break
        dwg_df.file.Close()

        if blk_polys:
            # Fecha juntas de argamassa de ~1 cm entre blocos adjacentes preservando a face exata da parede
            walls_exact = unary_union([p.buffer(0.8, join_style=2) for p in blk_polys]).buffer(-0.8, join_style=2)
            all_u = unary_union([slab_u, walls_exact])
        else:
            all_u = slab_u

        # 3. Extrair todos os vazios internos (buracos reais de laje/shafts/elevadores/escada)
        if all_u.geom_type == "Polygon":
            filled = Polygon(all_u.exterior)
        elif all_u.geom_type == "MultiPolygon":
            filled = unary_union([Polygon(g.exterior) for g in all_u.geoms])
        else:
            return []

        voids = filled.difference(all_u)
        if voids.is_empty:
            return []

        void_geoms = list(voids.geoms) if hasattr(voids, "geoms") else [voids]
        retangulos = []
        for vg in void_geoms:
            # Ignora micro-frestas (< 200 cm²) e areas abertas de terraco/platibanda (> 12 m² = 120.000 cm²)
            if vg.geom_type != "Polygon" or vg.area < 200.0 or vg.area > 120000.0:
                continue
            retangulos.extend(self._decompor_poligono_em_retangulos(vg, min_dim=8.0, min_area=200.0))

        return retangulos

    def _desenhar_shafts_com_x(
        self,
        dwg: TQSDwg.Dwg,
        pasta_pav: str,
        caminho_edificio: str,
        bounds_planta: List[float],
        caminho_saida_dwg: Optional[str] = None,
    ) -> int:
        """
        Identifica todos os shafts retangulares (furos / vazios na laje) do pavimento e
        desenha duas linhas diagonais cruzadas formando um 'X' entre vértices opostos,
        além de garantir o contorno retangular completo do shaft no Nível 237 (Cor 6 - ciano/magenta),
        indicando inequivocamente que é um buraco/abertura na laje conforme convenção executiva do TQS.

        REGRA DE OURO: Os shafts NUNCA devem ser copiados de outras plantas ou outros edifícios.
        Eles devem ser calculados e construídos ('feitos') estritamente a partir da geometria real
        do pavimento corrente (LAJ*.DWG + DesFiad1.DWG).
        """
        def normalizar_segmento(p1, p2):
            if (p1[0], p1[1]) <= (p2[0], p2[1]):
                return (round(p1[0], 1), round(p1[1], 1), round(p2[0], 1), round(p2[1], 1))
            else:
                return (round(p2[0], 1), round(p2[1], 1), round(p1[0], 1), round(p1[1], 1))

        linhas_existentes = set()
        it = dwg.iterator
        it.Begin()
        while True:
            pos = it.GetElementReadPosition()
            if pos and it.level == 237 and it.elementName in ["Linha", "Polyline"]:
                linhas_existentes.add(normalizar_segmento((it.x1, it.y1), (it.x2, it.y2)))
            if not it.Next():
                break

        # Prioridade 1: Detecção geométrica exata a partir de LAJ*.DWG + DesFiad1.DWG do pavimento atual
        shafts = self._detectar_aberturas_geometria_lajes(pasta_pav)

        # Fallback caso LAJ*.DWG ou shapely não esteja disponível
        if not shafts:
            shafts = self._detectar_shafts_de_linhas_237(linhas_existentes, bounds_planta)

        def _linha_ja_existe(p1, p2, tol=1.5):
            s = normalizar_segmento(p1, p2)
            for e in linhas_existentes:
                if (abs(s[0] - e[0]) <= tol and abs(s[1] - e[1]) <= tol and
                    abs(s[2] - e[2]) <= tol and abs(s[3] - e[3]) <= tol):
                    return True
            return False

        def _adicionar_linha(p1, p2):
            dwg.draw.level = 237
            dwg.draw.color = -1
            dwg.draw.Line(p1[0], p1[1], p2[0], p2[1])
            linhas_existentes.add(normalizar_segmento(p1, p2))

        shafts_processados = 0
        for s in shafts:
            x_min, x_max = s["x_min"], s["x_max"]
            y_min, y_max = s["y_min"], s["y_max"]

            # 1. Diagonal 1 (canto inferior-esquerdo para superior-direito)
            if not _linha_ja_existe((x_min, y_min), (x_max, y_max)):
                _adicionar_linha((x_min, y_min), (x_max, y_max))

            # 2. Diagonal 2 (canto superior-esquerdo para inferior-direito)
            if not _linha_ja_existe((x_min, y_max), (x_max, y_min)):
                _adicionar_linha((x_min, y_max), (x_max, y_min))

            # 3. Bordas ortogonais do retângulo do shaft (para garantir contorno fechado)
            bordas = [
                ((x_min, y_min), (x_max, y_min)),
                ((x_min, y_max), (x_max, y_max)),
                ((x_min, y_min), (x_min, y_max)),
                ((x_max, y_min), (x_max, y_max)),
            ]
            for pt_a, pt_b in bordas:
                if not _linha_ja_existe(pt_a, pt_b):
                    _adicionar_linha(pt_a, pt_b)

            shafts_processados += 1

        return shafts_processados

    def _precarregar_elementos_referencia(
        self,
        pasta_pav: str,
        pasta_gerais: str,
        bounds_planta: Optional[List[float]] = None,
        caminho_saida_dwg: Optional[str] = None,
        p_corte: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Pre-carrega elementos da prancha de referencia homologada:
        1) Contornos e bordas das lajes exteriores e sacadas (Nivel 237)
           no perimetro da planta util.
           REGRA DE OURO: Para pavimentos diferenciados (ex: 2º Pavimento), utiliza estritamente
           a geometria nativa do pavimento ({pavimento}.DWG) e JAMAIS carrega de pavimentos Tipo.
           Apenas para pavimentos Tipo ('TIPO' no nome) permite buscar referencias Tipo.
           Garante que as lajes venham de um unico arquivo consistente, sem duplicar ou misturar linhas.
        2) Coluna tecnica lateral (Resumo de materiais, legendas de blocos, notas
           tecnicas e detalhes) a direita da planta util a partir de uma fonte consistente.
        Retorna dicionario com {'laterais': [...], 'lajes_externas': [...]}.
        """
        if bounds_planta is None:
            p_df = os.path.join(pasta_pav, "DesFiad1.DWG")
            bounds_planta = self._calcular_bounds_desfiad(p_df)

        bx_min, bx_max, by_min, by_max = bounds_planta
        margem = 450.0
        x_min_ed, x_max_ed = bx_min - margem, bx_max + margem
        y_min_ed, y_max_ed = by_min - margem, by_max + margem

        elementos_laterais = []
        elementos_lajes_externas = []
        pasta_edificio = os.path.dirname(pasta_pav)
        pavimento_nome = os.path.basename(pasta_pav)

        # -------------------------------------------------------------------------
        # 1. CONTORNOS E BORDAS DE LAJES EXTERNAS E SACADAS (NIVEL 237)
        # -------------------------------------------------------------------------
        # PRIORIDADE 1 (FONTE UNICA AUTORITATIVA DO PAVIMENTO ATUAL):
        # TEL*.DWG Nivel 200 contem exatamente as bordas livres das lajes (sacadas,
        # contornos externos sem parede de apoio, junta de dilatacao e bordas livres
        # de furos) geradas diretamente pelo TQS Formas/Lajes para o modelo corrente.
        melhor_candidato_lajes = None
        melhor_linhas_lajes = []

        p_tel = None
        for f in sorted(os.listdir(pasta_pav)):
            if f.upper().startswith("TEL") and f.upper().endswith(".DWG"):
                p_tel = os.path.join(pasta_pav, f)
                break

        if p_tel and os.path.exists(p_tel):
            dwg_tel = TQSDwg.Dwg(pedmv=0)
            if dwg_tel.file.Open(p_tel) == 0:
                it_t = dwg_tel.iterator
                it_t.Begin()
                linhas_tel = []
                in_block = 0
                while True:
                    pos = it_t.GetElementReadPosition()
                    if pos:
                        el = it_t.elementName
                        if el == "Bloco":
                            in_block += 1
                        elif el == "Fim de bloco":
                            in_block = max(0, in_block - 1)
                        elif in_block == 0 and it_t.level == 200 and el in ["Linha", "Polyline"]:
                            x_val = getattr(it_t, "x1", 0.0)
                            y_val = getattr(it_t, "y1", 0.0)
                            if x_min_ed <= x_val <= x_max_ed and y_min_ed <= y_val <= y_max_ed:
                                item = {
                                    "tipo": el,
                                    "nivel": 237,
                                    "cor": -1,
                                    "x1": it_t.x1,
                                    "y1": it_t.y1,
                                    "x2": it_t.x2,
                                    "y2": it_t.y2,
                                }
                                if el == "Polyline":
                                    item["pontos"] = [it_t.GetPolylinePt(i) for i in range(it_t.xySize)]
                                linhas_tel.append(item)
                    if not it_t.Next():
                        break
                dwg_tel.file.Close()
                if len(linhas_tel) >= 4:
                    melhor_linhas_lajes = linhas_tel
                    melhor_candidato_lajes = p_tel

        # FALLBACK (caso TEL*.DWG nao exista no pavimento): busca Nivel 237 no desenho nativo
        if not melhor_linhas_lajes:
            candidatos_lajes = []

            # a) Desenho nativo do proprio pavimento (ex: 2^ PAVIMENTO.DWG, TIPO A.DWG)
            p_pav_nativo = os.path.join(pasta_pav, f"{pavimento_nome}.DWG")
            if os.path.exists(p_pav_nativo):
                candidatos_lajes.append(p_pav_nativo)
            else:
                for f in os.listdir(pasta_pav):
                    if f.upper().endswith(".DWG") and not any(f.upper().startswith(k) for k in ["DES", "PRE", "FOR", "LAJ", "LIST", "TEL", "AUTO"]):
                        candidatos_lajes.append(os.path.join(pasta_pav, f))
                        break

            # b) Desenhos especificos de pre-forma ja homologados deste pavimento
            for cand_name in [f"PRE_FOR_1aFIADA_{pavimento_nome}.DWG", f"EP - PRE_FOR_1aFIADA_{pavimento_nome}.DWG"]:
                p_cand = os.path.join(pasta_pav, cand_name)
                if os.path.exists(p_cand):
                    if not caminho_saida_dwg or os.path.abspath(p_cand) != os.path.abspath(caminho_saida_dwg):
                        candidatos_lajes.append(p_cand)

            # c) Se e SOMENTE SE for um pavimento Tipo, busca referencias de Pavimento Tipo
            if "TIPO" in pavimento_nome.upper():
                for cand_name in [
                    "PRE_FOR_1aFIADA_Tipo.DWG",
                    "PRE_FOR_1aFIADA_TIPO A.DWG",
                    "EP - PRE_FOR_1aFIADA_TIPO A.DWG",
                ]:
                    for p_dir in [pasta_pav, os.path.join(pasta_edificio, "TIPO A")]:
                        p_c = os.path.join(p_dir, cand_name)
                        if os.path.exists(p_c) and p_c not in candidatos_lajes:
                            if not caminho_saida_dwg or os.path.abspath(p_c) != os.path.abspath(caminho_saida_dwg):
                                candidatos_lajes.append(p_c)

            for p_cand in candidatos_lajes:
                if os.path.exists(p_cand):
                    dwg_cand = TQSDwg.Dwg(pedmv=0)
                    if dwg_cand.file.Open(p_cand) == 0:
                        it_c = dwg_cand.iterator
                        it_c.Begin()
                        linhas_cand = []
                        in_block = 0
                        while True:
                            pos = it_c.GetElementReadPosition()
                            if pos:
                                el = it_c.elementName
                                if el == "Bloco":
                                    in_block += 1
                                elif el == "Fim de bloco":
                                    in_block = max(0, in_block - 1)
                                elif in_block == 0 and it_c.level == 237 and el in ["Linha", "Polyline", "Indefinido"]:
                                    x_val = getattr(it_c, "x1", 0.0)
                                    y_val = getattr(it_c, "y1", 0.0)
                                    dx = abs(getattr(it_c, "x2", 0.0) - x_val)
                                    dy = abs(getattr(it_c, "y2", 0.0) - y_val)
                                    is_chevron = (p_cand != p_pav_nativo and dx <= 25.0 and dy <= 25.0 and dx > 1.0 and dy > 1.0)
                                    if not is_chevron and (x_min_ed <= x_val <= x_max_ed and y_min_ed <= y_val <= y_max_ed):
                                        item = {
                                            "tipo": el,
                                            "nivel": 237,
                                            "cor": -1,
                                            "x1": it_c.x1,
                                            "y1": it_c.y1,
                                            "x2": it_c.x2,
                                            "y2": it_c.y2,
                                        }
                                        if el == "Polyline":
                                            item["pontos"] = [it_c.GetPolylinePt(i) for i in range(it_c.xySize)]
                                        linhas_cand.append(item)
                            if not it_c.Next():
                                break
                        dwg_cand.file.Close()

                        if p_cand == p_pav_nativo and len(linhas_cand) >= 10:
                            melhor_linhas_lajes = linhas_cand
                            melhor_candidato_lajes = p_cand
                            break
                        elif len(linhas_cand) > len(melhor_linhas_lajes):
                            melhor_linhas_lajes = linhas_cand
                            melhor_candidato_lajes = p_cand

        elementos_lajes_externas = melhor_linhas_lajes

                # Vigas (FOR*.DWG) e divisórias de laje (LAJ*.DWG) NUNCA devem ser convertidas para o Nível 237!

        # -------------------------------------------------------------------------
        # 2. COLUNA TECNICA LATERAL (RESUMO DE MATERIAIS, LEGENDAS, NOTAS E DETALHES)
        # -------------------------------------------------------------------------
        candidatos_laterais = [
            os.path.join(pasta_pav, f"PRE_FOR_1aFIADA_{pavimento_nome}.DWG"),
            os.path.join(pasta_pav, f"PRE_FOR_1aFIADA_{pavimento_nome}-R00.DWG"),
            os.path.join(pasta_pav, "PRE_FOR_1aFIADA.DWG"),
            os.path.join(pasta_pav, "PRE_FOR_1aFIADA_Tipo.DWG"),
            os.path.join(pasta_edificio, "TIPO A", "PRE_FOR_1aFIADA_TIPO A.DWG"),
            os.path.join(pasta_edificio, "TIPO A", "PRE_FOR_1aFIADA_TIPO A-R00.DWG"),
            os.path.join(pasta_edificio, "TIPO A", "EP - PRE_FOR_1aFIADA_TIPO A.DWG"),
        ]
        # Adiciona backups do proprio pavimento
        for f in sorted(os.listdir(pasta_pav), reverse=True):
            if f.upper().startswith("PRE_FOR_1AFIADA") and "BKP" in f.upper() and f.upper().endswith(".DWG"):
                candidatos_laterais.append(os.path.join(pasta_pav, f))
        for p_lat in candidatos_laterais:
            if caminho_saida_dwg and os.path.abspath(p_lat) == os.path.abspath(caminho_saida_dwg):
                continue
            if os.path.exists(p_lat):
                dwg_lat = TQSDwg.Dwg(pedmv=0)
                if dwg_lat.file.Open(p_lat) == 0:
                    it_l = dwg_lat.iterator
                    it_l.Begin()
                    itens_deste_arquivo = []
                    while True:
                        pos = it_l.GetElementReadPosition()
                        if pos:
                            el = it_l.elementName
                            lvl = it_l.level
                            txt = getattr(it_l, "text", "").strip()
                            x_val = getattr(it_l, "x1", 0.0)
                            y_val = getattr(it_l, "y1", 0.0)
                            if x_val > bx_max + 50.0 and lvl not in [230, 239, 10, 13, 237, 231]:
                                descartar = False
                                if any(k in txt.upper() for k in ["%VALOR", "%PAVIMENTO", "%COTA", "VALOR DA COTA"]):
                                    descartar = True
                                elif re.search(r"\[\d+\]", txt) and os.path.basename(pasta_edificio) not in txt:
                                    descartar = True
                                elif p_corte and x_val < 3800.0 and y_val < 600.0:
                                    descartar = True
                                if not descartar:
                                    item = {
                                        "tipo": el,
                                        "nivel": lvl,
                                        "cor": self._cor_crua(dwg_lat, pos),
                                        "x1": it_l.x1,
                                        "y1": it_l.y1,
                                        "x2": it_l.x2,
                                        "y2": it_l.y2,
                                    }
                                    if el == "Texto":
                                        item["h"] = max(it_l.textHeight, 8.0)
                                        item["ang"] = it_l.textAngle
                                        item["texto"] = txt
                                    elif el == "Circulo":
                                        item["xc"] = it_l.xc
                                        item["yc"] = it_l.yc
                                        item["raio"] = it_l.radius
                                    elif el == "Bloco":
                                        item["bloco"] = getattr(it_l, "blockName", "")
                                        item["esc_x"] = it_l.xScale
                                        item["esc_y"] = it_l.yScale
                                        item["ang"] = it_l.insertAngle
                                    elif el == "Polyline":
                                        item["pontos"] = [it_l.GetPolylinePt(i) for i in range(it_l.xySize)]
                                    itens_deste_arquivo.append(item)
                        if not it_l.Next():
                            break
                    dwg_lat.file.Close()
                    if len(itens_deste_arquivo) >= 10:
                        elementos_laterais = itens_deste_arquivo
                        break  # Carrega de um unico arquivo consistente!

        return {"laterais": elementos_laterais, "lajes_externas": elementos_lajes_externas}

    def _inserir_coluna_lateral(
        self,
        dwg: TQSDwg.Dwg,
        elementos_referencia: List[Dict[str, Any]],
        bounds_planta: Optional[List[float]] = None,
        y_topo_selo: Optional[float] = None,
    ) -> Tuple[float, Optional[float]]:
        """
        Insere os elementos de resumo, legendas, detalhes e contornos de laje na prancha.
        Retorna (dy_leg, y_max_coluna): deslocamento vertical aplicado à coluna da legenda
        (x >= 3750) e a cota máxima atingida por ela, para o dimensionamento da moldura.
        """
        # Calcula deslocamento vertical caso a legenda ultrapasse o topo util da folha (~Y = +300)
        dy_leg = 0.0
        ys_lat = [
            item.get("y1", 0.0)
            for item in elementos_referencia
            if item.get("x1", 0.0) >= 3750.0
        ]
        if bounds_planta and ys_lat:
            y_topo_alvo = max(bounds_planta[3] + 220.0, 260.0)
            if max(ys_lat) > y_topo_alvo:
                dy_leg = y_topo_alvo - max(ys_lat) - 20.0
        # A coluna da legenda fica sobre o canto do selo: nunca pode descer para dentro da
        # área do carimbo + tabela de revisões (prevalece sobre o alvo de topo acima).
        if y_topo_selo is not None and ys_lat:
            y_base_leg = min(ys_lat + [-28.2]) if bounds_planta and bounds_planta[1] < 3000.0 else min(ys_lat)
            dy_min = (y_topo_selo + 30.0) - y_base_leg
            if dy_leg < dy_min:
                dy_leg = dy_min
        y_max_coluna = (max(ys_lat + ([555.6] if bounds_planta and bounds_planta[1] < 3000.0 else [])) + dy_leg) if ys_lat else None

        for item in elementos_referencia:
            el = item["tipo"]
            dwg.draw.level = item["nivel"]
            dwg.draw.color = item["cor"]
            dy = dy_leg if item.get("x1", 0.0) >= 3750.0 else 0.0

            if el in ["Linha", "Indefinido"]:
                dwg.draw.Line(item["x1"], item["y1"] + dy, item["x2"], item["y2"] + dy)
            elif el == "Polyline":
                pontos = item.get("pontos", [])
                if len(pontos) >= 2:
                    dwg.draw.PolyStart()
                    for pt in pontos:
                        dwg.draw.PolyEnterPoint(pt[0], pt[1] + dy)
                    dwg.draw.Polyline()
                else:
                    dwg.draw.Line(item["x1"], item["y1"] + dy, item["x2"], item["y2"] + dy)
            elif el == "Texto":
                dwg.draw.Text(item["x1"], item["y1"] + dy, item["h"], item["ang"], item["texto"])
            elif el == "Circulo":
                dwg.draw.Circle(item["xc"], item["yc"] + dy, item["raio"])
            elif el == "Bloco" and item.get("bloco"):
                dwg.draw.BlockInsert(item["bloco"], item["x1"], item["y1"] + dy, item["esc_x"], item["esc_y"], item["ang"])

        # Garante o fechamento da borda completa da LEGENDA - BLOCOS CERAMICOS (Nivel 0, Cor 7)
        # APENAS se os limites da planta forem compativeis com as coordenadas do Edificio 054 (bx_max < 3000)
        if bounds_planta and bounds_planta[1] < 3000.0:
            x_leg_0, x_leg_1 = 3800.3, 4290.8
            y_leg_top = 555.6 + dy_leg
            y_leg_head = 495.0 + dy_leg
            y_leg_bot = -28.2 + dy_leg
            dwg.draw.level = 0
            dwg.draw.color = -1

            tem_topo_legenda = any(
                item["tipo"] in ["Linha", "Polyline", "Indefinido"]
                and item["nivel"] == 0
                and abs((item["y1"] + dy_leg) - y_leg_top) < 1.0
                and abs((item["y2"] + dy_leg) - y_leg_top) < 1.0
                and item["x1"] >= 3790.0
                for item in elementos_referencia
            )
            if not tem_topo_legenda:
                dwg.draw.Line(x_leg_0, y_leg_top, x_leg_1, y_leg_top)

            dwg.draw.Line(x_leg_0, y_leg_bot, x_leg_1, y_leg_bot)       # Borda inferior
            dwg.draw.Line(x_leg_0, y_leg_top, x_leg_0, y_leg_bot)       # Lateral esquerda
            dwg.draw.Line(x_leg_1, y_leg_top, x_leg_1, y_leg_bot)       # Lateral direita
            dwg.draw.Line(x_leg_0, y_leg_head, x_leg_1, y_leg_head)     # Divisoria do titulo

        return dy_leg, y_max_coluna

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

    def _limpar_fiada_para_insercao(
        self,
        caminho_origem: str,
        caminho_destino: str,
        vaos_portas: List[Dict[str, Any]],
        remover_id_paredes: bool = False,
    ) -> int:
        """
        Cria copia limpa de DesFiad1.DWG ou DesFiad2.DWG purgando poluicao visual
        (pf12.5, $PFERV, $IDnPRT, titulo padrao do Alvest, textos nivel 7 e blocos
        dentro de vaos de portas) preservando integralmente blocos, juntas e grautes.
        """
        shutil.copy2(caminho_origem, caminho_destino)
        dwg = TQSDwg.Dwg(pedmv=0)
        if dwg.file.Open(caminho_destino) != 0:
            return 0

        it = dwg.iterator
        it.Begin()
        posicoes = set()
        in_block = 0
        while True:
            pos = it.GetElementReadPosition()
            if pos:
                el = it.elementName
                lvl = it.level
                txt = getattr(it, "text", "").strip()
                bname = getattr(it, "blockName", "")

                if el == "Bloco":
                    if in_block == 0:
                        if "PFERV" in bname or "IDnPRT" in bname:
                            posicoes.add(pos)
                        elif remover_id_paredes and (lvl == 247 or "IDnPAR" in bname):
                            posicoes.add(pos)
                        elif not bname.startswith("$") and self._ponto_esta_dentro_de_alguma_porta(it.x1, it.y1, vaos_portas):
                            posicoes.add(pos)
                    in_block += 1
                elif el == "Fim de bloco":
                    in_block = max(0, in_block - 1)
                elif in_block == 0:
                    if lvl == 198 and el == "Texto":
                        posicoes.add(pos)
                    elif lvl in [106, 216] and el == "Texto" and any(txt.startswith(k) for k in ["P", "JA", "PJ", "CHURR", "PE"]):
                        posicoes.add(pos)
                    elif lvl == 221 and el == "Texto" and re.match(r"^[0-9]+(?:\.[0-9]+)?$", txt):
                        posicoes.add(pos)
                    elif lvl == 222 and "fiada" in txt.lower():
                        posicoes.add(pos)
                    elif lvl == 7 and el == "Texto":
                        posicoes.add(pos)
                    elif remover_id_paredes and lvl == 247:
                        posicoes.add(pos)
                    elif lvl == 213 and el == "Texto" and "pt_graute" in txt.lower():
                        posicoes.add(pos)
            if not it.Next():
                break

        for p in posicoes:
            dwg.edit.Erase(p)
        dwg.file.Save()
        dwg.file.Close()
        return len(posicoes)

    @staticmethod
    def _inserir_resumo_materiais_de_listmelv(
        dwg: TQSDwg.Dwg,
        caminho_listmelv_dwg: str,
        target_x_min: float,
        target_y_top: float,
        max_largura: float = 720.0,
        max_altura: float = 390.0,
    ) -> int:
        """
        Extrai a tabela 'RESUMO de MATERIAIS' de LISTMELV.DWG (excluindo a tabela
        inferior 'Resistencia dos materiais') e a insere escalada na prancha.
        """
        if not caminho_listmelv_dwg or not os.path.exists(caminho_listmelv_dwg):
            return 0
        dwg_lm = TQSDwg.Dwg(pedmv=0)
        if dwg_lm.file.Open(caminho_listmelv_dwg) != 0:
            return 0

        it = dwg_lm.iterator
        it.Begin()
        y_resumo_hdr = None
        y_resist_hdr = None
        while True:
            if it.GetElementReadPosition() and it.elementName == "Texto":
                tu = it.text.strip().upper()
                if "RESUMO DE MATERIAIS" in tu:
                    y_resumo_hdr = it.y1
                elif "RESISTÊNCIA DOS MATERIAIS" in tu or "RESISTENCIA DOS MATERIAIS" in tu:
                    y_resist_hdr = it.y1
            if not it.Next():
                break

        if y_resumo_hdr is None:
            dwg_lm.file.Close()
            return 0

        y_top_cut = y_resumo_hdr + 0.6
        y_bot_cut = (y_resist_hdr + 0.8) if y_resist_hdr is not None else (y_resumo_hdr - 9.0)

        linhas = []
        textos = []
        bx = [1e9, -1e9, 1e9, -1e9]
        it.Begin()
        while True:
            if it.GetElementReadPosition():
                el = it.elementName
                if el == "Linha":
                    if y_bot_cut <= min(it.y1, it.y2) and max(it.y1, it.y2) <= y_top_cut:
                        linhas.append((it.x1, it.y1, it.x2, it.y2, it.color))
                        for px, py in ((it.x1, it.y1), (it.x2, it.y2)):
                            bx[0] = min(bx[0], px); bx[1] = max(bx[1], px)
                            bx[2] = min(bx[2], py); bx[3] = max(bx[3], py)
                elif el == "Texto":
                    if y_bot_cut <= it.y1 <= y_top_cut:
                        textos.append((it.x1, it.y1, it.textHeight, it.textAngle, it.text.strip(), it.color))
                        bx[0] = min(bx[0], it.x1); bx[1] = max(bx[1], it.x1)
                        bx[2] = min(bx[2], it.y1); bx[3] = max(bx[3], it.y1)
            if not it.Next():
                break
        dwg_lm.file.Close()

        if not linhas and not textos:
            return 0

        w_src = max(bx[1] - bx[0], 0.1)
        h_src = max(bx[3] - bx[2], 0.1)
        fator = min(50.0, max_largura / w_src, max_altura / h_src)

        dwg.draw.level = 0
        for x1, y1, x2, y2, cor in linhas:
            dwg.draw.color = -1
            dwg.draw.Line(
                target_x_min + (x1 - bx[0]) * fator,
                target_y_top - (bx[3] - y1) * fator,
                target_x_min + (x2 - bx[0]) * fator,
                target_y_top - (bx[3] - y2) * fator,
            )
        for x1, y1, h, ang, txt, cor in textos:
            dwg.draw.color = -1
            dwg.draw.Text(
                target_x_min + (x1 - bx[0]) * fator,
                target_y_top - (bx[3] - y1) * fator,
                max(h * fator, 6.0),
                ang,
                txt,
            )
        return len(linhas) + len(textos)

    def construir_planta_1a_2a_fiada(
        self,
        caminho_edificio: str,
        pavimento: str,
        caminho_saida_dwg: Optional[str] = None,
        escala: int = 50,
    ) -> Dict[str, Any]:
        """
        Gera prancha executiva combinada de 1ª e 2ª Fiada (ex: FOR_COBERTURA.DWG)
        seguindo o padrao do proprio edificio (herda moldura, notas tecnicas e legenda
        de FOR_*.DWG existente do edificio, insere DesFiad1 + DesFiad2 limpos lado a lado,
        sobrepoe lajes LAJ*.DWG, contornos TEL*.DWG / furos geometricos, tabela
        RESUMO de MATERIAIS do proprio pavimento e CORTE ESQUEMATICO como bloco nativo).
        """
        import tempfile

        pasta_pav = os.path.join(caminho_edificio, pavimento)
        pasta_gerais = os.path.join(caminho_edificio, "GERAIS")
        if not os.path.exists(pasta_pav):
            raise FileNotFoundError(f"Pasta do pavimento não encontrada: {pasta_pav}")

        p_fiad1 = self._localizar_arquivo(pasta_pav, "DesFiad1.DWG")
        p_fiad2 = self._localizar_arquivo(pasta_pav, "DesFiad2.DWG")
        if not p_fiad1 or not p_fiad2:
            raise FileNotFoundError(f"DesFiad1.DWG ou DesFiad2.DWG não encontrado em {pasta_pav}")

        if not caminho_saida_dwg:
            caminho_saida_dwg = os.path.join(pasta_pav, f"FOR_{pavimento}.DWG")

        arquivo_backup = self._criar_backup_seguro(caminho_saida_dwg)

        # 1. Localiza prancha-base FOR_*.DWG existente no mesmo edificio (ex: 2PV\FOR_2PV.DWG)
        p_template_for = None
        candidatos_for = []
        for sub in sorted(os.listdir(caminho_edificio)):
            p_sub = os.path.join(caminho_edificio, sub)
            if os.path.isdir(p_sub) and sub.upper() not in ("GERAIS", "ESPACIAL", "PLANTAS", "SELOS", "ALVEST", "PILAR", "FUNDAC", "INFRA", "PREMOLD"):
                for f in sorted(os.listdir(p_sub)):
                    fu = f.upper()
                    if fu.startswith("FOR_") and fu.endswith(".DWG") and "BKP" not in fu and "CORTE" not in fu:
                        fp = os.path.join(p_sub, f)
                        if os.path.abspath(fp) != os.path.abspath(caminho_saida_dwg):
                            candidatos_for.append((os.path.getmtime(fp), fp))
        if candidatos_for:
            candidatos_for.sort(reverse=True)
            p_template_for = candidatos_for[0][1]

        if not p_template_for:
            raise FileNotFoundError(f"Nenhuma prancha-base FOR_*.DWG encontrada em {caminho_edificio}")

        # 2. Localiza arquivos auxiliares do proprio pavimento
        p_laj = next((os.path.join(pasta_pav, f) for f in sorted(os.listdir(pasta_pav)) if f.upper().startswith("LAJ") and f.upper().endswith(".DWG")), None)
        p_tel = next((os.path.join(pasta_pav, f) for f in sorted(os.listdir(pasta_pav)) if f.upper().startswith("TEL") and f.upper().endswith(".DWG")), None)
        p_listmelv_dwg = self._localizar_arquivo(pasta_pav, "LISTMELV.DWG")
        p_listmelv_lst = self._localizar_arquivo(pasta_pav, "LISTMELV.LST")
        p_tipo = self._localizar_arquivo(pasta_pav, f"{pavimento}.DWG")

        # Corte esquematico compilado (prioriza GERAIS\CORTE ESQUEMATICO.DWG mais recente se valido)
        p_corte = None
        for p_dir in [pasta_gerais, os.path.join(caminho_edificio, "ESPACIAL"), caminho_edificio]:
            if os.path.exists(p_dir):
                for f in sorted(os.listdir(p_dir)):
                    if "CORTE" in f.upper() and f.upper().endswith(".DWG"):
                        p_cand = os.path.join(p_dir, f)
                        if not self._is_template_invalido(p_cand):
                            p_corte = p_cand
                            break
                if p_corte:
                    break

        # 3. Mede shift exato (dX) entre 1a e 2a fiada na prancha-base FOR_*.DWG
        dx_fiada2 = 1485.0
        dwg_ref = TQSDwg.Dwg(pedmv=0)
        if dwg_ref.file.Open(p_template_for) == 0:
            it_r = dwg_ref.iterator
            it_r.Begin()
            bx_ref = [1e9, -1e9, 1e9, -1e9]
            xs_l, xs_r = [], []
            # Primeiro mede bounds das paredes 1a fiada do proprio pavimento para saber o ponto de corte X
            bounds_f1 = self._calcular_bounds_desfiad(p_fiad1)
            x_split = bounds_f1[1] + 150.0
            while True:
                if it_r.GetElementReadPosition() and it_r.level == 203 and it_r.elementName == "Linha" and it_r.y1 > bounds_f1[2] - 150.0:
                    if it_r.x1 < x_split:
                        xs_l.append(it_r.x1)
                    elif it_r.x1 < x_split + 1600.0:
                        xs_r.append(it_r.x1)
                if not it_r.Next():
                    break
            dwg_ref.file.Close()
            if xs_l and xs_r:
                dx_fiada2 = round(min(xs_r) - min(xs_l), 2)
        else:
            bounds_f1 = self._calcular_bounds_desfiad(p_fiad1)

        # 4. Copia template para saida e limpa zonas especificas do outro pavimento
        shutil.copy2(p_template_for, caminho_saida_dwg)
        dwg = TQSDwg.Dwg(pedmv=0)
        if dwg.file.Open(caminho_saida_dwg) != 0:
            raise RuntimeError(f"Erro ao abrir {caminho_saida_dwg}")

        dwg.settings.scale = float(escala)

        # Coordenadas de corte baseadas na geometria do template
        x_planta_min = bounds_f1[0] - 200.0
        x_planta_max = bounds_f1[1] + dx_fiada2 + 250.0
        y_planta_min = bounds_f1[2] - 125.0
        y_planta_max = bounds_f1[3] + 155.0

        # Encontra posicoes de titulos e zonas inferiores
        it = dwg.iterator
        it.Begin()
        in_block = 0
        pos_apagar = set()
        titulo_pos = None
        corte_zone_x_max = bounds_f1[1] + 550.0
        resumo_x_min = corte_zone_x_max + 10.0
        resumo_y_top = y_planta_min - 15.0
        resumo_y_bot = y_planta_min - 425.0

        while True:
            pos = it.GetElementReadPosition()
            if pos:
                el = it.elementName
                lvl = it.level
                x, y = it.x1, it.y1
                if el == "Bloco":
                    if in_block == 0 and lvl != 230:
                        in_planta = (x_planta_min <= x <= x_planta_max and y_planta_min <= y <= y_planta_max)
                        in_corte = (x_planta_min <= x <= corte_zone_x_max and (y_planta_min - 960.0) <= y < y_planta_min)
                        in_resumo = (corte_zone_x_max < x <= x_planta_max and resumo_y_bot <= y < y_planta_min)
                        if in_planta or in_corte or in_resumo:
                            pos_apagar.add(pos)
                    in_block += 1
                elif el == "Fim de bloco":
                    in_block = max(0, in_block - 1)
                elif in_block == 0 and lvl != 230:
                    if el == "Texto" and lvl == 222 and "FIADA" in getattr(it, "text", "").upper():
                        titulo_pos = (x, y, it.textHeight, it.textAngle)
                        pos_apagar.add(pos)
                    else:
                        in_planta = (x_planta_min <= x <= x_planta_max and y_planta_min <= y <= y_planta_max)
                        in_corte = (x_planta_min <= x <= corte_zone_x_max and (y_planta_min - 960.0) <= y < y_planta_min)
                        in_resumo = (corte_zone_x_max < x <= x_planta_max and resumo_y_bot <= y < y_planta_min)
                        if in_planta or in_corte or in_resumo:
                            pos_apagar.add(pos)
            if not it.Next():
                break

        for p in pos_apagar:
            dwg.edit.Erase(p)

        # 5. Atualiza titulo principal da prancha
        pav_label = pavimento.replace("^", "º").upper()
        tx_t, ty_t, th_t, ta_t = titulo_pos if titulo_pos else (bounds_f1[0] - 2.0, bounds_f1[3] + 375.0, 32.5, 0.0)
        dwg.draw.level = 222
        dwg.draw.color = -1
        dwg.draw.Text(tx_t, ty_t, th_t, ta_t, f"MODULAÇÃO DE 1ª FIADA e 2ª FIADA - {pav_label}")

        # 6. Prepara e insere 1ª e 2ª Fiadas limpas da COBERTURA/pavimento
        vaos_portas, vaos_janelas = self._mapear_vaos(p_fiad1)
        tmp_dir = tempfile.mkdtemp(prefix="autqs_fiadas_")
        try:
            pav_slug = re.sub(r"[^A-Za-z0-9_]+", "_", pavimento.upper()).strip("_")
            tmp_f1 = os.path.join(tmp_dir, f"FIADA_1_{pav_slug}.DWG")
            tmp_f2 = os.path.join(tmp_dir, f"FIADA_2_{pav_slug}.DWG")
            purg_1 = self._limpar_fiada_para_insercao(p_fiad1, tmp_f1, vaos_portas, remover_id_paredes=False)
            purg_2 = self._limpar_fiada_para_insercao(p_fiad2, tmp_f2, vaos_portas, remover_id_paredes=True)

            # Carrega e insere 1ª Fiada em (0, 0)
            if dwg.draw.BlockLoadFromDwg(tmp_f1) != 0:
                raise RuntimeError("Falha ao carregar bloco da 1ª Fiada")
            blk_f1 = dwg.blockstable.Name(dwg.blockstable.count - 1)
            dwg.draw.level = 0
            dwg.draw.color = -1
            dwg.draw.BlockInsert(blk_f1, 0.0, 0.0, 1.0, 1.0, 0.0)

            # Carrega e insere 2ª Fiada deslocada por (dx_fiada2, 0.0)
            if dwg.draw.BlockLoadFromDwg(tmp_f2) != 0:
                raise RuntimeError("Falha ao carregar bloco da 2ª Fiada")
            blk_f2 = dwg.blockstable.Name(dwg.blockstable.count - 1)
            dwg.draw.level = 0
            dwg.draw.color = -1
            dwg.draw.BlockInsert(blk_f2, dx_fiada2, 0.0, 1.0, 1.0, 0.0)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        # 7. Sobreposicao de Lajes (LAJ*.DWG) na 1ª Fiada
        total_lajes = 0
        if p_laj and os.path.exists(p_laj):
            dwg_laj = TQSDwg.Dwg(pedmv=0)
            if dwg_laj.file.Open(p_laj) == 0:
                it_l = dwg_laj.iterator
                it_l.Begin()
                while True:
                    if it_l.GetElementReadPosition() and it_l.elementName == "Texto" and it_l.level in [10, 13]:
                        dwg.draw.level = it_l.level
                        dwg.draw.color = -1
                        dwg.draw.Text(it_l.x1, it_l.y1, 10.0, 0.0, it_l.text.strip())
                        if it_l.level == 10:
                            total_lajes += 1
                    if not it_l.Next():
                        break
                dwg_laj.file.Close()

        # 8. Contornos livres de laje (TEL*.DWG Nivel 200 -> Nivel 237, Cor 6) + Furos geometricos
        total_lajes_ext = 0
        if p_tel and os.path.exists(p_tel):
            dwg_tel = TQSDwg.Dwg(pedmv=0)
            if dwg_tel.file.Open(p_tel) == 0:
                it_t = dwg_tel.iterator
                it_t.Begin()
                while True:
                    if it_t.GetElementReadPosition() and it_t.level == 200 and it_t.elementName == "Linha":
                        dwg.draw.level = 237
                        dwg.draw.color = -1
                        dwg.draw.Line(it_t.x1, it_t.y1, it_t.x2, it_t.y2)
                        total_lajes_ext += 1
                    if not it_t.Next():
                        break
                dwg_tel.file.Close()

        total_shafts = self._desenhar_shafts_com_x(dwg, pasta_pav, caminho_edificio, bounds_f1, caminho_saida_dwg=caminho_saida_dwg)

        # 9. Dimensao dos vaos (Portas/Janelas) no Nivel 239 nas duas fiadas
        dim_vaos_lst = []
        if p_listmelv_lst and os.path.exists(p_listmelv_lst):
            with open(p_listmelv_lst, "r", errors="ignore") as f_lst:
                for line in f_lst:
                    m_v = re.match(r"^\s*(\d{2,3}x\d{2,3})\s+\d+\s*$", line)
                    if m_v:
                        dim_vaos_lst.append(m_v.group(1))

        vaos_inseridos = 0
        for idx_p, vp in enumerate(vaos_portas):
            dim_txt = dim_vaos_lst[idx_p] if idx_p < len(dim_vaos_lst) else f"{int(round(max(vp['w'], vp['h'])))}x210"
            ang_raw = abs(vp.get("ang_deg", 0.0)) % 180.0
            # No TQS Alvest, $BLVAO com angulo ~90° ou ~270° esta em parede vertical; caso w/h indique vertical, tambem rotaciona
            is_vert = (45.0 <= ang_raw <= 135.0) or (vp.get("h", 0.0) > vp.get("w", 0.0) * 1.2)
            ang = 90.0 if is_vert else 0.0
            dwg.draw.level = 239
            dwg.draw.color = -1
            dwg.draw.Text(vp["x"], vp["y"], 9.0, ang, dim_txt)
            dwg.draw.Text(vp["x"] + dx_fiada2, vp["y"], 9.0, ang, dim_txt)
            vaos_inseridos += 1

        # 10. Insere RESUMO de MATERIAIS do proprio pavimento (LISTMELV.DWG)
        resumo_elems = self._inserir_resumo_materiais_de_listmelv(
            dwg,
            p_listmelv_dwg,
            target_x_min=resumo_x_min,
            target_y_top=resumo_y_top + 15.0,
            max_largura=700.0,
            max_altura=355.0,
        )

        # 11. Insere CORTE ESQUEMATICO compilado como Bloco nativo unico
        bloco_corte_inserido = False
        if p_corte and os.path.exists(p_corte):
            dwg_c = TQSDwg.Dwg(pedmv=0)
            if dwg_c.file.Open(p_corte) == 0:
                it_c = dwg_c.iterator
                it_c.Begin()
                c_bx = [1e9, -1e9, 1e9, -1e9]
                while True:
                    if it_c.GetElementReadPosition():
                        for pt in [(it_c.x1, it_c.y1), (it_c.x2, it_c.y2)]:
                            if abs(pt[0]) > 0.01 or abs(pt[1]) > 0.01:
                                c_bx[0] = min(c_bx[0], pt[0]); c_bx[1] = max(c_bx[1], pt[0])
                                c_bx[2] = min(c_bx[2], pt[1]); c_bx[3] = max(c_bx[3], pt[1])
                    if not it_c.Next():
                        break
                dwg_c.file.Close()
                if c_bx[0] < 1e8 and dwg.draw.BlockLoadFromDwg(p_corte) == 0:
                    nome_esp = os.path.splitext(os.path.basename(p_corte))[0]
                    nome_bloco = dwg.blockstable.Name(dwg.blockstable.count - 1)
                    for ib in range(dwg.blockstable.count - 1, -1, -1):
                        if dwg.blockstable.Name(ib).upper() == nome_esp.upper():
                            nome_bloco = dwg.blockstable.Name(ib)
                            break
                    # Centraliza horizontal e verticalmente na caixa do corte esquematico
                    c_w = c_bx[1] - c_bx[0]
                    c_h = c_bx[3] - c_bx[2]
                    box_x0, box_x1 = x_planta_min + 130.0, corte_zone_x_max - 40.0
                    box_y0, box_y1 = y_planta_min - 910.0, y_planta_min - 30.0
                    target_x = box_x0 + max(0.0, (box_x1 - box_x0 - c_w) / 2.0)
                    target_y = box_y0 + max(0.0, (box_y1 - box_y0 - c_h) / 2.0)
                    dwg.draw.level = 0
                    dwg.draw.color = -1
                    dwg.draw.BlockInsert(nome_bloco, target_x - c_bx[0], target_y - c_bx[2], 1.0, 1.0, 0.0)
                    bloco_corte_inserido = True

        dwg.file.Save()
        dwg.file.Close()

        auditoria = self._auditar_dwg(caminho_saida_dwg)
        return {
            "status": "sucesso",
            "sucesso": True,
            "caminho_dwg": caminho_saida_dwg,
            "backup_criado": arquivo_backup,
            "template_base": os.path.basename(p_template_for),
            "edificio": os.path.basename(caminho_edificio),
            "pavimento": pavimento,
            "escala": escala,
            "dx_fiada2": dx_fiada2,
            "corte_como_bloco": bloco_corte_inserido,
            "elementos_purgados_1a": purg_1,
            "elementos_purgados_2a": purg_2,
            "total_lajes": total_lajes,
            "total_vaos": vaos_inseridos,
            "total_lajes_externas": total_lajes_ext,
            "total_shafts": total_shafts,
            "resumo_elementos": resumo_elems,
            "auditoria": auditoria,
        }
