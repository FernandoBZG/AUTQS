import os
import math
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any

from src.tqs_adapter.building_reader import TQSBuildingReader

@dataclass
class LanceAnalise:
    """Informacoes e diagnostico de engenharia de um lance de pilar."""
    pilar: str
    lance: int
    pavimento: str
    b_cm: float
    h_cm: float
    area_cm2: float
    status: str  # 'CALCULADO' ou 'NAO_DIMENSIONADO'
    num_barras: Optional[int] = None
    bitola_mm: Optional[float] = None
    pdd_x: str = "N"
    pdd_y: str = "N"
    as_efet_cm2: Optional[float] = None
    as_nec_cm2: Optional[float] = None
    taxa_armadura_pct: Optional[float] = None
    estribo_bitola_mm: Optional[float] = None
    estribo_espacamento_cm: Optional[float] = None
    fck_mpa: Optional[float] = 30.0
    cobrimento_cm: Optional[float] = 2.5
    tensao_t_kgf_cm2: Optional[float] = None
    lambda_max: Optional[float] = None
    lambda_lim: Optional[float] = None
    ni: Optional[float] = None  # esforco normal adimensional nu
    folga_capacidade_pct: Optional[float] = None
    nk_tf: Optional[float] = None
    fnd_tf: Optional[float] = None
    mxd_tf_cm: Optional[float] = None
    myd_tf_cm: Optional[float] = None
    metodo_2ord: str = ""
    classificacao: str = "NORMAL"  # 'NAO_DIMENSIONADO', 'HIPER_ARMADO', 'SUPERDIMENSIONADO', 'ESBELTO', 'NORMAL'
    motivo_critico: Optional[str] = None
    sugestao_otimizacao: Optional[str] = None
    b_sugerido_cm: Optional[float] = None
    h_sugerido_cm: Optional[float] = None
    taxa_projetada_pct: Optional[float] = None
    economia_aco_kg: float = 0.0
    economia_concreto_m3: float = 0.0

@dataclass
class PilarAnalise:
    """Conjunto de lances de um pilar do edificio."""
    nome: str
    numero: int
    lances: List[LanceAnalise] = field(default_factory=list)

    @property
    def tem_nao_dimensionado(self) -> bool:
        return any(l.status == "NAO_DIMENSIONADO" for l in self.lances)

    @property
    def tem_hiper_armado(self) -> bool:
        return any(l.classificacao == "HIPER_ARMADO" for l in self.lances)

    @property
    def tem_superdimensionado(self) -> bool:
        return any(l.classificacao == "SUPERDIMENSIONADO" for l in self.lances)

@dataclass
class EdificioPilaresResumo:
    """Sumario executivo e metricas completas dos pilares do edificio."""
    edificio_nome: str
    caminho_edificio: str
    total_pilares: int
    total_lances: int
    total_calculados: int
    total_nao_dimensionados: int
    total_hiper_armados: int
    total_superdimensionados: int
    total_esbeltos: int
    taxa_media_armadura: float
    volume_total_concreto_m3: float
    peso_total_aco_kg: float
    economia_potencial_aco_kg: float
    economia_potencial_concreto_m3: float
    lances_nao_dimensionados: List[LanceAnalise] = field(default_factory=list)
    lances_hiper_armados: List[LanceAnalise] = field(default_factory=list)
    lances_superdimensionados: List[LanceAnalise] = field(default_factory=list)
    lances_esbeltos: List[LanceAnalise] = field(default_factory=list)
    todos_pilares: Dict[str, PilarAnalise] = field(default_factory=dict)
    sugestoes_prioritarias: List[Dict[str, Any]] = field(default_factory=list)

    def para_dict(self) -> Dict[str, Any]:
        """Converte para dicionario serializavel em JSON."""
        return {
            "edificio_nome": self.edificio_nome,
            "caminho_edificio": self.caminho_edificio,
            "total_pilares": self.total_pilares,
            "total_lances": self.total_lances,
            "metricas": {
                "calculados": self.total_calculados,
                "nao_dimensionados": self.total_nao_dimensionados,
                "hiper_armados": self.total_hiper_armados,
                "superdimensionados": self.total_superdimensionados,
                "esbeltos": self.total_esbeltos,
                "taxa_media_armadura_pct": round(self.taxa_media_armadura, 2),
                "volume_total_concreto_m3": round(self.volume_total_concreto_m3, 2),
                "peso_total_aco_kg": round(self.peso_total_aco_kg, 1),
                "economia_potencial_aco_kg": round(self.economia_potencial_aco_kg, 1),
                "economia_potencial_concreto_m3": round(self.economia_potencial_concreto_m3, 2),
            },
            "lances_criticos": [asdict(l) for l in self.lances_nao_dimensionados],
            "lances_hiper_armados": [asdict(l) for l in self.lances_hiper_armados],
            "lances_superdimensionados": [asdict(l) for l in self.lances_superdimensionados],
            "sugestoes_prioritarias": self.sugestoes_prioritarias,
        }

    def para_resumo_executivo(self) -> str:
        """
        Gera um resumo executivo ultra-compacto em texto para o Agente LLM
        consumir o minimo absoluto de tokens sem perder nenhum dado essencial.
        """
        linhas = [
            f"=== RELATORIO EXECUTIVO DE PILARES: {self.edificio_nome} ===",
            f"Pilares: {self.total_pilares} | Lances: {self.total_lances} | Taxa Media: {self.taxa_media_armadura:.2f}% | Concreto: {self.volume_total_concreto_m3:.1f} m3 | Aco: {self.peso_total_aco_kg:.0f} kg",
            f"Diagnostico: {self.total_nao_dimensionados} Nao Dimensionados | {self.total_hiper_armados} Hiper-armados (rho >= 2.5%) | {self.total_superdimensionados} Superdimensionados | {self.total_esbeltos} Esbeltos (lambda > 90)",
            f"Economia Estimada: {self.economia_potencial_aco_kg:.0f} kg de aco | {self.economia_potencial_concreto_m3:.1f} m3 de concreto",
        ]

        if self.lances_nao_dimensionados:
            linhas.append("\n[AVISO CRITICO] LANCES NAO DIMENSIONADOS:")
            for l in self.lances_nao_dimensionados:
                linhas.append(
                    f" - {l.pilar} L{l.lance} ({l.pavimento}): {l.b_cm:.0f}x{l.h_cm:.0f} cm | T={l.tensao_t_kgf_cm2 or 0:.0f} kgf/cm2 | nu={l.ni or 0:.3f} | Motivo: {l.motivo_critico} -> Sugestao: {l.sugestao_otimizacao}"
                )

        if self.lances_hiper_armados:
            linhas.append("\n[ALERTA] LANCES HIPER-ARMADOS (TAXA >= 2.5%):")
            for l in self.lances_hiper_armados:
                barras = f"{l.num_barras}phi{l.bitola_mm:.1f}" if l.num_barras else "-"
                linhas.append(
                    f" - {l.pilar} L{l.lance} ({l.pavimento}): {l.b_cm:.0f}x{l.h_cm:.0f} cm | rho={l.taxa_armadura_pct:.2f}% ({barras}) | As={l.as_efet_cm2:.1f} cm2 -> Sugestao: {l.sugestao_otimizacao}"
                )

        if self.lances_superdimensionados:
            linhas.append(f"\n[OPORTUNIDADE] LANCES SUPERDIMENSIONADOS (TAXA <= 0.7% E nu <= 0.28, Total: {len(self.lances_superdimensionados)}):")
            for l in self.lances_superdimensionados[:10]:
                linhas.append(
                    f" - {l.pilar} L{l.lance} ({l.pavimento}): {l.b_cm:.0f}x{l.h_cm:.0f} cm | rho={l.taxa_armadura_pct:.2f}% | nu={l.ni or 0:.3f} (Folga {l.folga_capacidade_pct or 0:.0f}%) -> Sugestao: {l.sugestao_otimizacao}"
                )
            if len(self.lances_superdimensionados) > 10:
                linhas.append(f"   ... e mais {len(self.lances_superdimensionados) - 10} lances com capacidade subutilizada.")

        # Se for um filtro de pilar especifico, lista os lances do pilar
        if len(self.todos_pilares) == 1:
            p_nome = list(self.todos_pilares.keys())[0]
            linhas.append(f"\nDETALHAMENTO DE LANCES DO PILAR {p_nome}:")
            for l in self.todos_pilares[p_nome].lances:
                arm = f"{l.num_barras}phi{l.bitola_mm:.1f}" if l.num_barras else "-"
                linhas.append(
                    f" - {l.pilar} L{l.lance} ({l.pavimento}): {l.b_cm:.0f}x{l.h_cm:.0f} cm | rho={l.taxa_armadura_pct or 0:.2f}% ({arm}) | Status: {l.status} | Classificacao: {l.classificacao}"
                )

        return "\n".join(linhas)

    def para_tabela_terminal(self) -> str:
        """Gera saida formatada e visual para o terminal CLI."""
        linhas = []
        div = "=" * 80
        linhas.append(div)
        linhas.append(f"   AUTQS - DIAGNOSTICO E OTIMIZACAO DE PILARES TQS: {self.edificio_nome}")
        linhas.append(div)
        linhas.append(f"Diretorio: {self.caminho_edificio}")
        linhas.append(
            f"Pilares: {self.total_pilares} | Lances: {self.total_lances} | "
            f"Taxa Media: {self.taxa_media_armadura:.2f}% | Concreto Total: {self.volume_total_concreto_m3:.1f} m3"
        )
        linhas.append(
            f"Diagnostico: [ {self.total_nao_dimensionados} NAO DIMENSIONADOS ] [ {self.total_hiper_armados} HIPER-ARMADOS ] "
            f"[ {self.total_superdimensionados} SUPERDIMENSIONADOS ] [ {self.total_esbeltos} ESBELTOS ]"
        )
        linhas.append(
            f"Potencial de Otimizacao: {self.economia_potencial_aco_kg:.0f} kg de aco e {self.economia_potencial_concreto_m3:.1f} m3 de concreto"
        )
        linhas.append(div)

        if self.lances_nao_dimensionados:
            linhas.append("\n[X] 1. LANCES NAO DIMENSIONADOS (ACAO IMEDIATA NECESSARIA):")
            linhas.append(f"{'Pilar':<6} | {'Lance':<5} | {'Pavimento':<10} | {'Secao (cm)':<12} | {'T (kgf/cm2)':<12} | {'nu (Ni)':<8} | {'Diagnostico & Acao Recomendada'}")
            linhas.append("-" * 80)
            for l in self.lances_nao_dimensionados:
                secao = f"{l.b_cm:.0f}x{l.h_cm:.0f}"
                t_str = f"{l.tensao_t_kgf_cm2:.1f}" if l.tensao_t_kgf_cm2 else "-"
                ni_str = f"{l.ni:.3f}" if l.ni is not None else "-"
                diag = f"{l.motivo_critico} -> {l.sugestao_otimizacao}"
                linhas.append(f"{l.pilar:<6} | {l.lance:<5} | {l.pavimento:<10} | {secao:<12} | {t_str:<12} | {ni_str:<8} | {diag}")

        if self.lances_hiper_armados:
            linhas.append("\n[!] 2. LANCES HIPER-ARMADOS (rho >= 2.5% - CONGESTIONAMENTO E CUSTO ELEVADO):")
            linhas.append(f"{'Pilar':<6} | {'Lance':<5} | {'Pavimento':<10} | {'Secao (cm)':<12} | {'Armadura':<12} | {'Taxa rho':<8} | {'As (cm2)':<10} | {'Secao Sugerida & Economia'}")
            linhas.append("-" * 80)
            for l in self.lances_hiper_armados:
                secao = f"{l.b_cm:.0f}x{l.h_cm:.0f}"
                arm = f"{l.num_barras}phi{l.bitola_mm:.1f}" if l.num_barras else "-"
                taxa = f"{l.taxa_armadura_pct:.2f}%" if l.taxa_armadura_pct else "-"
                as_str = f"{l.as_efet_cm2:.1f}" if l.as_efet_cm2 else "-"
                sug = f"{l.b_sugerido_cm:.0f}x{l.h_sugerido_cm:.0f} cm (rho~{l.taxa_projetada_pct:.1f}%, -{l.economia_aco_kg:.0f}kg aco)" if l.b_sugerido_cm else l.sugestao_otimizacao
                linhas.append(f"{l.pilar:<6} | {l.lance:<5} | {l.pavimento:<10} | {secao:<12} | {arm:<12} | {taxa:<8} | {as_str:<10} | {sug}")

        if self.lances_superdimensionados:
            linhas.append("\n[*] 3. LANCES SUPERDIMENSIONADOS (rho <= 0.7% E nu <= 0.28 - EXCESSO DE CONCRETO):")
            linhas.append(f"{'Pilar':<6} | {'Lance':<5} | {'Pavimento':<10} | {'Secao Atual':<12} | {'Nk (tf)':<8} | {'nu (Ni)':<8} | {'Taxa rho':<8} | {'Secao Otimizada Sugerida'}")
            linhas.append("-" * 80)
            for l in self.lances_superdimensionados:
                secao = f"{l.b_cm:.0f}x{l.h_cm:.0f}"
                nk_str = f"{l.nk_tf:.1f}" if l.nk_tf else "-"
                ni_str = f"{l.ni:.3f}" if l.ni is not None else "-"
                taxa = f"{l.taxa_armadura_pct:.2f}%" if l.taxa_armadura_pct else "-"
                sug = f"{l.b_sugerido_cm:.0f}x{l.h_sugerido_cm:.0f} cm (Eco: {l.economia_concreto_m3:.2f} m3)" if l.b_sugerido_cm else l.sugestao_otimizacao
                linhas.append(f"{l.pilar:<6} | {l.lance:<5} | {l.pavimento:<10} | {secao:<12} | {nk_str:<8} | {ni_str:<8} | {taxa:<8} | {sug}")

        if self.lances_esbeltos:
            linhas.append("\n[#] 4. LANCES ESBELTOS (lambda > 90 - EFEITOS DE 2a ORDEM RELEVANTES):")
            linhas.append(f"{'Pilar':<6} | {'Lance':<5} | {'Pavimento':<10} | {'Secao (cm)':<12} | {'Lambda':<10} | {'Alerta & Recomendacao'}")
            linhas.append("-" * 80)
            for l in self.lances_esbeltos:
                secao = f"{l.b_cm:.0f}x{l.h_cm:.0f}"
                linhas.append(f"{l.pilar:<6} | {l.lance:<5} | {l.pavimento:<10} | {secao:<12} | {l.lambda_max:<10.1f} | {l.sugestao_otimizacao}")

        if len(self.todos_pilares) == 1:
            p_nome = list(self.todos_pilares.keys())[0]
            linhas.append(f"\nDETALHAMENTO DO PILAR {p_nome}:")
            linhas.append(f"{'Lance':<6} | {'Pavimento':<10} | {'Secao (cm)':<12} | {'Armadura':<12} | {'Taxa rho':<8} | {'Status':<18} | {'Classificacao'}")
            linhas.append("-" * 80)
            for l in self.todos_pilares[p_nome].lances:
                secao = f"{l.b_cm:.0f}x{l.h_cm:.0f}"
                arm = f"{l.num_barras}phi{l.bitola_mm:.1f}" if l.num_barras else "-"
                taxa = f"{l.taxa_armadura_pct:.2f}%" if l.taxa_armadura_pct else "-"
                linhas.append(f"{l.lance:<6} | {l.pavimento:<10} | {secao:<12} | {arm:<12} | {taxa:<8} | {l.status:<18} | {l.classificacao}")

        linhas.append("\n" + div)
        linhas.append("DICA: Use 'python -m src.ui.cli --edificio " + self.edificio_nome + " --editar-pilar <Nome> --b <cm> --h <cm>' para aplicar as alteracoes.")
        linhas.append(div)
        return "\n".join(linhas)


class TQSColumnAnalyzer:
    """
    Motor analitico ultra-rapido de extracao, auditoria e otimizacao de pilares TQS.
    Le e processa SELEC.LST, LISPIL.LST, CARPIL.LST e METGERAL.LST em milissegundos.
    """

    def __init__(self, caminho_ou_nome_edificio: str, largura_fixa: bool = False):
        reader = TQSBuildingReader(caminho_ou_nome_edificio)
        self.largura_fixa = largura_fixa
        self.caminho_edificio = reader.caminho_edificio
        self.nome_edificio = reader.nome_edificio
        self.pasta_pilar = os.path.join(self.caminho_edificio, "PILAR")
        self.pasta_espacial = os.path.join(self.caminho_edificio, "ESPACIAL")

    def analisar(self, pilar_filtro: Optional[str] = None) -> EdificioPilaresResumo:
        """
        Executa a analise integral dos pilares e retorna o EdificioPilaresResumo.
        """
        # 1. Carrega dados basicos de SELEC.LST
        lances_map = self._parse_selec_lst()

        # 2. Enriquece com esforcos e As_nec de LISPIL.LST
        self._enriquecer_com_lispil(lances_map)

        # 3. Enriquece com esforcos normais de portico de CARPIL.LST
        self._enriquecer_com_carpil(lances_map)

        # 4. Enriquece com avisos especificos de METGERAL.LST
        avisos_metgeral = self._parse_metgeral_lst()

        # 5. Aplica regras normativas de engenharia e otimizacao
        pilares_agrupados: Dict[str, PilarAnalise] = {}
        todos_lances: List[LanceAnalise] = []

        for (p_name, lance_num), lance in lances_map.items():
            if pilar_filtro and pilar_filtro.upper() != p_name.upper():
                continue

            # Injeta avisos de METGERAL se existirem
            if p_name in avisos_metgeral and not lance.motivo_critico:
                lance.motivo_critico = "; ".join(avisos_metgeral[p_name])

            # Classifica e gera diagnostico
            self._classificar_lance(lance)

            if p_name not in pilares_agrupados:
                m_num = re.search(r'\d+', p_name)
                p_num = int(m_num.group(0)) if m_num else len(pilares_agrupados) + 1
                pilares_agrupados[p_name] = PilarAnalise(nome=p_name, numero=p_num)

            pilares_agrupados[p_name].lances.append(lance)
            todos_lances.append(lance)

        # 6. Agrega metricas globais do edificio
        resumo = self._construir_resumo_global(todos_lances, pilares_agrupados)
        return resumo

    def _parse_selec_lst(self) -> Dict[Tuple[str, int], LanceAnalise]:
        """Extrai os lances tabulados em PILAR/SELEC.LST."""
        caminho = os.path.join(self.pasta_pilar, "SELEC.LST")
        if not os.path.exists(caminho):
            return {}

        with open(caminho, "r", encoding="latin1", errors="replace") as f:
            conteudo = f.read()

        lances_dict: Dict[Tuple[str, int], LanceAnalise] = {}
        blocos = re.split(r"PILAR:\s*([A-Za-z0-9_]+)", conteudo)

        for i in range(1, len(blocos), 2):
            p_name = blocos[i].strip()
            texto_bloco = blocos[i + 1]

            for linha in texto_bloco.split("\n"):
                linha_s = linha.strip()
                if not re.match(r"^\d+\s+[A-Za-z0-9_À-ú]", linha_s):
                    continue

                try:
                    lance_idx = int(linha[0:5].strip())
                    pav = linha[5:21].strip()
                    secao_raw = linha[21:35].strip()
                    area = float(linha[35:44].strip())

                    # Parse b e h da secao (ex: "19.x  30." ou "19.0 x 30.0")
                    m_secao = re.findall(r"[\d\.]+", secao_raw)
                    b_cm = float(m_secao[0]) if len(m_secao) >= 1 else 19.0
                    h_cm = float(m_secao[1]) if len(m_secao) >= 2 else round(area / b_cm, 1)

                    if "LANCE SEM DIM" in linha:
                        t_val = None
                        lbd_val = None
                        ni_val = None
                        m_nums = re.findall(r"[-+]?\d*\.\d+|\d+", linha[60:])
                        if len(m_nums) >= 3:
                            try:
                                t_val = float(m_nums[-3])
                                lbd_val = float(m_nums[-2])
                                ni_val = float(m_nums[-1])
                            except Exception:
                                pass

                        lance_obj = LanceAnalise(
                            pilar=p_name,
                            lance=lance_idx,
                            pavimento=pav,
                            b_cm=b_cm,
                            h_cm=h_cm,
                            area_cm2=area,
                            status="NAO_DIMENSIONADO",
                            tensao_t_kgf_cm2=t_val,
                            lambda_max=lbd_val,
                            ni=ni_val,
                            motivo_critico="Nao convergiu no TQS Pilar (LANCE SEM DIM)"
                        )
                    else:
                        nfer = int(linha[44:48].strip())
                        bit = float(linha[48:55].strip())
                        pdd = linha[55:61].strip()
                        pdd_x = pdd[0] if len(pdd) >= 1 else "N"
                        pdd_y = pdd[-1] if len(pdd) >= 2 else "N"
                        as_val = float(linha[61:69].strip())
                        taxa = float(linha[69:76].strip())

                        estr = float(linha[76:81].strip()) if len(linha) > 81 and linha[76:81].strip() else None
                        c_estr = float(linha[81:86].strip()) if len(linha) > 86 and linha[81:86].strip() else None
                        fck = float(linha[89:96].strip()) if len(linha) > 96 and linha[89:96].strip() else 30.0
                        cobr = float(linha[96:102].strip()) if len(linha) > 102 and linha[96:102].strip() else 2.5
                        t_val = float(linha[102:108].strip()) if len(linha) > 108 and linha[102:108].strip() else None
                        lbd = float(linha[108:113].strip().replace(".", "")) if len(linha) > 113 and linha[108:113].strip() else None
                        ni = float(linha[113:120].strip()) if len(linha) > 120 and linha[113:120].strip() else None
                        ord2 = linha[120:].strip() if len(linha) > 120 else ""

                        folga = round((1.0 - ni) * 100.0, 1) if ni is not None else None

                        lance_obj = LanceAnalise(
                            pilar=p_name,
                            lance=lance_idx,
                            pavimento=pav,
                            b_cm=b_cm,
                            h_cm=h_cm,
                            area_cm2=area,
                            status="CALCULADO",
                            num_barras=nfer,
                            bitola_mm=bit,
                            pdd_x=pdd_x,
                            pdd_y=pdd_y,
                            as_efet_cm2=as_val,
                            taxa_armadura_pct=taxa,
                            estribo_bitola_mm=estr,
                            estribo_espacamento_cm=c_estr,
                            fck_mpa=fck,
                            cobrimento_cm=cobr,
                            tensao_t_kgf_cm2=t_val,
                            lambda_max=lbd,
                            ni=ni,
                            folga_capacidade_pct=folga,
                            metodo_2ord=ord2
                        )

                    lances_dict[(p_name, lance_idx)] = lance_obj
                except Exception:
                    continue

        return lances_dict

    def _enriquecer_com_lispil(self, lances_map: Dict[Tuple[str, int], LanceAnalise]):
        """Le PILAR/LISPIL.LST para extrair As_nec, FNd, Mxd, Myd e limites de esbeltez."""
        caminho = os.path.join(self.pasta_pilar, "LISPIL.LST")
        if not os.path.exists(caminho):
            return

        with open(caminho, "r", encoding="latin1", errors="replace") as f:
            conteudo = f.read()

        blocos = re.split(r"PILAR:\s*([A-Za-z0-9_]+)", conteudo)
        for i in range(1, len(blocos), 2):
            p_name = blocos[i].strip()
            texto_bloco = blocos[i + 1]

            for linha in texto_bloco.split("\n"):
                if not linha.startswith("|L."):
                    continue

                m_uncalc = re.search(r"\|L\.\s*(\d+)\s+\*\*AVISO\*\.\.LANCE NAO DIMENSIONADO", linha)
                if m_uncalc:
                    lance_idx = int(m_uncalc.group(1))
                    if (p_name, lance_idx) in lances_map:
                        lances_map[(p_name, lance_idx)].status = "NAO_DIMENSIONADO"
                    continue

                m_calc = re.search(
                    r"\|L\.\s*(\d+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)(?:\|\s*([\d\.]*)\s+([\d\.]*)\s*\|\s*([\d\.-]*)\s+([\d\.-]*)\s+([\d\.-]*))?",
                    linha
                )
                if m_calc:
                    lance_idx = int(m_calc.group(1))
                    key = (p_name, lance_idx)
                    as_nec = float(m_calc.group(13))

                    if key in lances_map:
                        l = lances_map[key]
                        l.as_nec_cm2 = as_nec
                        if m_calc.group(14) and m_calc.group(14).strip():
                            try:
                                l.lambda_lim = float(m_calc.group(14))
                            except ValueError:
                                pass
                        if m_calc.group(16) and m_calc.group(16).strip():
                            try:
                                l.fnd_tf = float(m_calc.group(16))
                            except ValueError:
                                pass
                        if m_calc.group(17) and m_calc.group(17).strip():
                            try:
                                l.mxd_tf_cm = float(m_calc.group(17))
                            except ValueError:
                                pass
                        if m_calc.group(18) and m_calc.group(18).strip():
                            try:
                                l.myd_tf_cm = float(m_calc.group(18))
                            except ValueError:
                                pass

    def _enriquecer_com_carpil(self, lances_map: Dict[Tuple[str, int], LanceAnalise]):
        """Le ESPACIAL/CARPIL.LST para extrair esforco normal caracteristico Nk."""
        caminho = os.path.join(self.pasta_espacial, "CARPIL.LST")
        if not os.path.exists(caminho):
            return

        with open(caminho, "r", encoding="latin1", errors="replace") as f:
            conteudo = f.read()

        current_pilar = None
        for linha in conteudo.split("\n"):
            linha_s = linha.strip()
            if re.match(r"^P\d+$", linha_s):
                current_pilar = linha_s
            elif current_pilar and linha_s:
                parts = linha_s.split()
                try:
                    piso = None
                    nk_val = None
                    if len(parts) >= 12:
                        piso = int(parts[1])
                        n_ini = float(parts[6])
                        n_fim = float(parts[10])
                        nk_val = max(abs(n_ini), abs(n_fim))
                    elif len(parts) >= 11:
                        piso = int(parts[0])
                        n_ini = float(parts[5])
                        n_fim = float(parts[9])
                        nk_val = max(abs(n_ini), abs(n_fim))

                    if piso is not None and nk_val is not None:
                        key = (current_pilar, piso)
                        if key in lances_map:
                            lances_map[key].nk_tf = nk_val
                except (ValueError, IndexError):
                    pass

    def _parse_metgeral_lst(self) -> Dict[str, List[str]]:
        """Le PILAR/METGERAL.LST para identificar restricoes normativas de bitola."""
        caminho = os.path.join(self.pasta_pilar, "METGERAL.LST")
        if not os.path.exists(caminho):
            return {}

        with open(caminho, "r", encoding="latin1", errors="replace") as f:
            conteudo = f.read()

        avisos: Dict[str, List[str]] = {}
        blocos = re.split(r"Pilar:\s*([A-Za-z0-9_]+)", conteudo)
        for i in range(1, len(blocos), 2):
            p_name = blocos[i].strip()
            texto = blocos[i + 1]
            motivos = []
            for l in texto.split("\n"):
                l_s = l.strip()
                if "Bit" in l_s and "> 1/8" in l_s:
                    motivos.append("Bitola excede b/8 (NBR 6118 18.4.2.1)")
                    break
                elif "LANCE sem dimensionamento" in l_s:
                    motivos.append("Secao insuficiente para armadura")
                    break
            if motivos:
                avisos[p_name] = motivos
        return avisos

    def _classificar_lance(self, lance: LanceAnalise):
        """Aplica regras normativas e gera sugestoes de redimensionamento e economia."""
        comprimento_lance_m = 3.0

        if lance.status == "NAO_DIMENSIONADO":
            lance.classificacao = "NAO_DIMENSIONADO"
            if not lance.motivo_critico:
                lance.motivo_critico = "Lance nao dimensionado pelo TQS"

            # Sugestao de correcao
            if lance.b_cm < 19.0:
                lance.b_sugerido_cm = 19.0
                lance.h_sugerido_cm = max(lance.h_cm, 35.0)
                lance.sugestao_otimizacao = (
                    f"Aumentar largura de {lance.b_cm:.0f} para 19 cm e h para {lance.h_sugerido_cm:.0f} cm "
                    f"(elimina penalidade gamma_n e permite bitolas ate 25mm)"
                )
            elif lance.ni and lance.ni >= 0.50:
                # Comprime alem do limite ideal, aumentar dimensao
                delta_h = 15.0
                lance.b_sugerido_cm = lance.b_cm
                lance.h_sugerido_cm = lance.h_cm + delta_h
                lance.sugestao_otimizacao = (
                    f"Aumentar secao de {lance.b_cm:.0f}x{lance.h_cm:.0f} para {lance.b_sugerido_cm:.0f}x{lance.h_sugerido_cm:.0f} cm "
                    f"para descarregar a tensao de compressao (T={lance.tensao_t_kgf_cm2 or 0:.0f} kgf/cm2, nu={lance.ni:.2f})"
                )
            else:
                lance.b_sugerido_cm = lance.b_cm
                lance.h_sugerido_cm = lance.h_cm + 10.0
                lance.sugestao_otimizacao = (
                    f"Aumentar h de {lance.h_cm:.0f} para {lance.h_sugerido_cm:.0f} cm para viabilizar convergencia"
                )
            return

        taxa = lance.taxa_armadura_pct or 0.0
        ni = lance.ni if lance.ni is not None else 0.0
        lbd = lance.lambda_max if lance.lambda_max is not None else 0.0

        # Caso 1: Hiper-armado (rho >= 2.5%, e critico se >= 4.0%)
        if taxa >= 2.5:
            lance.classificacao = "HIPER_ARMADO"
            lance.motivo_critico = f"Taxa de armadura alta (rho={taxa:.2f}%) gerando congestionamento de barras"
            
            as_atual = lance.as_efet_cm2 or (lance.area_cm2 * taxa / 100.0)
            area_alvo = lance.area_cm2 * 1.35
            if self.largura_fixa:
                # Restricao de projeto: b nao pode mudar, so h
                b_sug = lance.b_cm
                h_sug = min(120.0, math.ceil((lance.h_cm * 1.35) / 5.0) * 5.0)
                h_sug = max(h_sug, lance.h_cm + 10.0)
            else:
                # Secoes alongadas (h/b > 3) tambem ganham largura (min. 25 cm)
                b_sug = max(lance.b_cm, 25.0) if lance.h_cm / lance.b_cm > 3.0 else lance.b_cm
                h_sug = max(lance.h_cm + 5.0, math.ceil((area_alvo / b_sug) / 5.0) * 5.0)

            lance.b_sugerido_cm = b_sug
            lance.h_sugerido_cm = h_sug
            nova_area = b_sug * h_sug

            # Estimativa: As necessario cai mais que proporcionalmente ao aumento de Ac
            as_novo = max(nova_area * 0.008, as_atual * (lance.area_cm2 / nova_area) ** 2)
            as_economizado = max(0.0, as_atual - as_novo)

            lance.taxa_projetada_pct = round((as_novo / nova_area) * 100.0, 2)
            lance.economia_aco_kg = as_economizado * comprimento_lance_m * 0.785 * 1.15
            lance.sugestao_otimizacao = (
                f"Alterar {lance.b_cm:.0f}x{lance.h_cm:.0f} -> {b_sug:.0f}x{h_sug:.0f} cm "
                f"(rho {taxa:.1f}% -> ~{lance.taxa_projetada_pct:.1f}%, ~{lance.economia_aco_kg:.0f} kg aco; estimativa, reprocessar)"
            )

        # Caso 2: Superdimensionado (rho <= 0.70% e nu <= 0.28 e area >= 1200 cm2)
        elif taxa <= 0.70 and ni <= 0.28 and lance.area_cm2 >= 1200.0:
            lance.classificacao = "SUPERDIMENSIONADO"
            lance.motivo_critico = f"Secao com folga excessiva de capacidade (rho={taxa:.2f}%, nu={ni:.3f})"

            # Reducao ate nu ~ 0.40
            if self.largura_fixa:
                b_alvo = lance.b_cm
                h_alvo = max(30.0, b_alvo, math.ceil((lance.h_cm * ni / 0.40) / 5.0) * 5.0)
            else:
                s = math.sqrt(ni / 0.40)
                b_alvo = max(19.0, math.ceil(lance.b_cm * s)) if lance.b_cm > 25.0 else lance.b_cm
                h_alvo = max(30.0, b_alvo, math.ceil((lance.h_cm * s) / 5.0) * 5.0)
            if b_alvo * h_alvo > lance.area_cm2 * 0.9:
                lance.classificacao = "NORMAL"
                return
            lance.b_sugerido_cm = b_alvo
            lance.h_sugerido_cm = h_alvo

            vol_atual = (lance.b_cm * lance.h_cm * comprimento_lance_m) / 10000.0
            vol_novo = (b_alvo * h_alvo * comprimento_lance_m) / 10000.0
            lance.economia_concreto_m3 = max(0.0, vol_atual - vol_novo)
            lance.sugestao_otimizacao = (
                f"Reduzir {lance.b_cm:.0f}x{lance.h_cm:.0f} -> {b_alvo:.0f}x{h_alvo:.0f} cm (nu~0.40; "
                f"-{lance.economia_concreto_m3:.2f} m3; verificar lambda/estabilidade)"
            )

        # Caso 3: Esbelto (lambda > 90)
        elif lbd > 90.0:
            lance.classificacao = "ESBELTO"
            lance.motivo_critico = f"Alta esbeltez (lambda={lbd:.1f} > 90)"
            lance.sugestao_otimizacao = (
                f"Adicionar viga de travamento no pe-direito ou aumentar b de {lance.b_cm:.0f} cm para reduzir efeitos de 2a ordem"
            )

        else:
            lance.classificacao = "NORMAL"

    def _construir_resumo_global(
        self, todos_lances: List[LanceAnalise], pilares_map: Dict[str, PilarAnalise]
    ) -> EdificioPilaresResumo:
        """Calcula totais, taxas medias e compoe listas prioritarias."""
        lances_nao_dim = [l for l in todos_lances if l.classificacao == "NAO_DIMENSIONADO"]
        lances_hiper = [l for l in todos_lances if l.classificacao == "HIPER_ARMADO"]
        lances_super = [l for l in todos_lances if l.classificacao == "SUPERDIMENSIONADO"]
        lances_esbeltos = [l for l in todos_lances if l.classificacao == "ESBELTO"]
        lances_calc = [l for l in todos_lances if l.status == "CALCULADO"]

        taxas = [l.taxa_armadura_pct for l in lances_calc if l.taxa_armadura_pct is not None]
        taxa_media = sum(taxas) / len(taxas) if taxas else 0.0

        vol_total = sum((l.b_cm * l.h_cm * 3.0) / 10000.0 for l in todos_lances)
        peso_aco = sum(
            (l.as_efet_cm2 or 0.0) * 3.0 * 0.785 * 1.15
            for l in lances_calc
        )

        eco_aco = sum(l.economia_aco_kg for l in lances_hiper)
        eco_conc = sum(l.economia_concreto_m3 for l in lances_super)

        sugestoes = []
        for l in lances_nao_dim:
            sugestoes.append({
                "prioridade": "ALTA",
                "tipo": "ERRO_DIMENSIONAMENTO",
                "pilar": l.pilar,
                "lance": l.lance,
                "pavimento": l.pavimento,
                "secao_atual": f"{l.b_cm:.0f}x{l.h_cm:.0f}",
                "secao_sugerida": f"{l.b_sugerido_cm:.0f}x{l.h_sugerido_cm:.0f}" if l.b_sugerido_cm else None,
                "acao": l.sugestao_otimizacao
            })

        for l in lances_hiper:
            sugestoes.append({
                "prioridade": "MEDIA",
                "tipo": "REDUCAO_ACO",
                "pilar": l.pilar,
                "lance": l.lance,
                "pavimento": l.pavimento,
                "secao_atual": f"{l.b_cm:.0f}x{l.h_cm:.0f}",
                "secao_sugerida": f"{l.b_sugerido_cm:.0f}x{l.h_sugerido_cm:.0f}" if l.b_sugerido_cm else None,
                "economia_aco_kg": round(l.economia_aco_kg, 1),
                "acao": l.sugestao_otimizacao
            })

        for l in lances_super:
            sugestoes.append({
                "prioridade": "BAIXA",
                "tipo": "REDUCAO_CONCRETO",
                "pilar": l.pilar,
                "lance": l.lance,
                "pavimento": l.pavimento,
                "secao_atual": f"{l.b_cm:.0f}x{l.h_cm:.0f}",
                "secao_sugerida": f"{l.b_sugerido_cm:.0f}x{l.h_sugerido_cm:.0f}" if l.b_sugerido_cm else None,
                "economia_concreto_m3": round(l.economia_concreto_m3, 2),
                "acao": l.sugestao_otimizacao
            })

        return EdificioPilaresResumo(
            edificio_nome=self.nome_edificio,
            caminho_edificio=self.caminho_edificio,
            total_pilares=len(pilares_map),
            total_lances=len(todos_lances),
            total_calculados=len(lances_calc),
            total_nao_dimensionados=len(lances_nao_dim),
            total_hiper_armados=len(lances_hiper),
            total_superdimensionados=len(lances_super),
            total_esbeltos=len(lances_esbeltos),
            taxa_media_armadura=taxa_media,
            volume_total_concreto_m3=vol_total,
            peso_total_aco_kg=peso_aco,
            economia_potencial_aco_kg=eco_aco,
            economia_potencial_concreto_m3=eco_conc,
            lances_nao_dimensionados=lances_nao_dim,
            lances_hiper_armados=lances_hiper,
            lances_superdimensionados=lances_super,
            lances_esbeltos=lances_esbeltos,
            todos_pilares=pilares_map,
            sugestoes_prioritarias=sugestoes
        )
