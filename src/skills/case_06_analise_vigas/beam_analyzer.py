import os
import re
import math
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple

from src.tqs_adapter.building_reader import TQSBuildingReader


def _remover_acentos(texto: str) -> str:
    """Remove acentos e converte para minúsculas para comparações flexíveis."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


@dataclass
class VigaVao:
    """Dados estruturais de um vão específico de viga (ELU e ELS)."""
    vao_id: str
    comp_m: float
    bw_cm: float
    h_cm: float
    vsd_max_tf: float = 0.0
    vrd2_tf: float = 0.0
    biela_ratio: float = 0.0
    bitola_estribo_mm: float = 0.0
    espacamento_estribo_cm: float = 0.0
    ramos_estribo: int = 2
    eh_biela_excedida: bool = False
    eh_bitola_invalida: bool = False
    eh_vao_curto_espurio: bool = False

    # ELS (Estado Limite de Serviço - Flechas / Deformações)
    flecha_cm: float = 0.0
    flecha_adm_cm: float = 0.0
    flecha_ratio: float = 0.0
    relacao_l_f: float = 0.0  # L / f (ex: 350)
    eh_flecha_excessiva: bool = False  # f > f_adm
    eh_flecha_alerta: bool = False     # 0.85 <= f / f_adm <= 1.0
    contra_flecha_sugerida_cm: float = 0.0


@dataclass
class VigaDiagnostico:
    """Diagnóstico consolidado de uma viga do pavimento (ELU + ELS)."""
    numero: int
    nome: str
    secao_predominante: str
    num_vaos: int
    vaos: List[VigaVao] = field(default_factory=list)
    m_neg_max_tfm: float = 0.0
    m_pos_max_tfm: float = 0.0
    as_max_cm2: float = 0.0
    detalhes_longitudinais: str = ""
    vsd_max_tf: float = 0.0
    vrd2_tf: float = 0.0
    biela_ratio_max: float = 0.0

    # ELS Consolidado
    flecha_max_cm: float = 0.0
    flecha_adm_cm: float = 0.0
    flecha_ratio_max: float = 0.0
    tem_flecha_excessiva: bool = False
    tem_flecha_alerta: bool = False
    contra_flecha_max_cm: float = 0.0

    status: str = "OK"  # 'CRITICO', 'ALERTA', 'OK'
    falhas: List[str] = field(default_factory=list)
    sugestao_correcao: Optional[str] = None

    @property
    def taxa_armadura_estimada_pct(self) -> float:
        """Taxa estimada de armadura longitudinal principal (As / (bw * h))."""
        if not self.vaos or self.as_max_cm2 <= 0:
            return 0.0
        bw = self.vaos[0].bw_cm
        h = self.vaos[0].h_cm
        if bw * h <= 0:
            return 0.0
        return (self.as_max_cm2 / (bw * h)) * 100.0


@dataclass
class AuditoriaVigasResultado:
    """Resultado estruturado da auditoria de vigas de um pavimento."""
    edificio: str
    pavimento: str
    pasta_vigas: str
    fck_kgf_cm2: float = 300.0
    fyk_kgf_cm2: float = 5000.0
    vigas: List[VigaDiagnostico] = field(default_factory=list)
    erros_tabela_ferros: List[str] = field(default_factory=list)
    avisos_ordcon: List[str] = field(default_factory=list)
    duracao_segundos: float = 0.0

    @property
    def total_vigas(self) -> int:
        return len(self.vigas)

    @property
    def total_criticas(self) -> int:
        return sum(1 for v in self.vigas if v.status == "CRITICO")

    @property
    def total_alertas(self) -> int:
        return sum(1 for v in self.vigas if v.status == "ALERTA")

    @property
    def total_ok(self) -> int:
        return sum(1 for v in self.vigas if v.status == "OK")

    @property
    def total_flechas_excessivas(self) -> int:
        return sum(1 for v in self.vigas if v.tem_flecha_excessiva)

    @property
    def total_flechas_alerta(self) -> int:
        return sum(1 for v in self.vigas if v.tem_flecha_alerta and not v.tem_flecha_excessiva)

    @property
    def status_geral(self) -> str:
        if self.total_criticas > 0:
            return "CRITICO"
        if self.total_alertas > 0:
            return "ALERTA"
        return "OK"

    def para_dict(self) -> Dict[str, Any]:
        return {
            "edificio": self.edificio,
            "pavimento": self.pavimento,
            "pasta_vigas": self.pasta_vigas,
            "fck_kgf_cm2": self.fck_kgf_cm2,
            "fyk_kgf_cm2": self.fyk_kgf_cm2,
            "status_geral": self.status_geral,
            "metricas": {
                "total_vigas": self.total_vigas,
                "vigas_criticas": self.total_criticas,
                "vigas_com_alertas": self.total_alertas,
                "vigas_ok": self.total_ok,
                "flechas_excessivas": self.total_flechas_excessivas,
                "flechas_em_alerta": self.total_flechas_alerta,
                "erros_tabela_ferros": len(self.erros_tabela_ferros),
                "avisos_ordcon": len(self.avisos_ordcon),
            },
            "vigas": [asdict(v) for v in self.vigas],
            "erros_tabela_ferros": self.erros_tabela_ferros,
            "avisos_ordcon": self.avisos_ordcon,
            "duracao_segundos": self.duracao_segundos,
        }

    def para_resumo_executivo(self) -> str:
        """Resumo executivo conciso para respostas de IA com menor consumo de tokens."""
        icones = {
            "CRITICO": "[CRITICO] RUPTURA DE BIELA, FLECHA EXCESSIVA OU ERROS DE DETALHAMENTO",
            "ALERTA": "[ALERTA] VIGAS COM VAOS CURTOS, ALTA ARMADURA OU FLECHA PROXIMA AO LIMITE",
            "OK": "[OK] TODAS AS VIGAS APROVADAS EM ELU E ELS",
        }
        linhas = [
            f"Relatorio Executivo de Vigas TQS - Pavimento: {self.pavimento}",
            f"Edificio: {self.edificio} | Concreto: fck = {self.fck_kgf_cm2 / 10.0:.0f} MPa",
            f"Status: {icones.get(self.status_geral, self.status_geral)}",
            f"Estatisticas: {self.total_vigas} vigas | {self.total_criticas} criticas | {self.total_alertas} com alertas | {self.total_ok} regulares.",
            f"ELS (Deformacoes): {self.total_flechas_excessivas} vigas com flecha excedida | {self.total_flechas_alerta} vigas em atencao (85-100% de f_adm).",
        ]

        criticas = [v for v in self.vigas if v.status == "CRITICO"]
        if criticas:
            linhas.append("\nVigas Criticas (Ajuste Obrigatorio de Secao / ELS / Detalhamento):")
            for v in criticas[:8]:
                excesso_str = f"({(v.biela_ratio_max - 1.0) * 100:+.1f}%)" if v.biela_ratio_max > 1.0 else ""
                fl_str = f" | f={v.flecha_max_cm:.1f}cm (adm={v.flecha_adm_cm:.1f}cm)" if v.flecha_max_cm > 0 else ""
                linhas.append(
                    f"  * [{v.nome}] Secao {v.secao_predominante} | Vsd={v.vsd_max_tf:.1f} tf, VRd2={v.vrd2_tf:.1f} tf {excesso_str}{fl_str} | "
                    f"Falhas: {', '.join(v.falhas[:2])}"
                )
                if v.sugestao_correcao:
                    linhas.append(f"    -> Solucao: {v.sugestao_correcao}")

        alertas = [v for v in self.vigas if v.status == "ALERTA"]
        if alertas:
            linhas.append("\nVigas com Alertas Secundarios (Vaos Curtos / Alta Armadura / Flecha Limite):")
            for v in alertas[:6]:
                fl_info = f" [f={v.flecha_max_cm:.1f}cm/{v.flecha_adm_cm:.1f}cm]" if v.tem_flecha_alerta else ""
                linhas.append(f"  * [{v.nome}] Secao {v.secao_predominante}{fl_info} | {', '.join(v.falhas[:2])}")

        # Top esforços de flexão
        top_flex = sorted(self.vigas, key=lambda x: max(x.m_neg_max_tfm, x.m_pos_max_tfm), reverse=True)[:5]
        if top_flex:
            linhas.append("\nMaiores Esforcos de Flexao e Armaduras:")
            for v in top_flex:
                linhas.append(
                    f"  * [{v.nome}] M-={v.m_neg_max_tfm:.1f} tf.m, M+={v.m_pos_max_tfm:.1f} tf.m | "
                    f"As_max={v.as_max_cm2:.1f} cm2 ({v.taxa_armadura_estimada_pct:.2f}%)"
                )

        if self.erros_tabela_ferros:
            linhas.append(f"\nErros de Detalhamento em RESESTERR.LST: {len(self.erros_tabela_ferros)} ocorrencias (Bitola 50mm sentinela).")

        return "\n".join(linhas)

    def para_tabela_terminal(self, filtro_viga: Optional[str] = None) -> str:
        """Gera relatório completo em tabela ASCII formatada para terminal com ELU e ELS."""
        vigas_alvo = self.vigas
        if filtro_viga:
            alvo_norm = filtro_viga.strip().upper()
            if not alvo_norm.startswith("V") and alvo_norm.isdigit():
                alvo_norm = f"V{alvo_norm}"
            vigas_alvo = [v for v in self.vigas if v.nome.upper() == alvo_norm]

        linhas = [
            "\n" + "=" * 115,
            f"   AUDITORIA ESTRUTURAL DE VIGAS CAD/TQS (ELU + ELS) - PAVIMENTO: {self.pavimento.upper()}",
            "=" * 115,
            f"Edificio:   {self.edificio}",
            f"Pasta:      {self.pasta_vigas}",
            f"Materiais:  fck = {self.fck_kgf_cm2 / 10.0:.0f} MPa (concreto) | fyk = {self.fyk_kgf_cm2 / 10.0:.0f} MPa (aco CA-50)",
            f"Resumo:     {self.total_vigas} Vigas | {self.total_criticas} Criticas | {self.total_alertas} Alertas | {self.total_ok} Regulares",
            f"ELS:        {self.total_flechas_excessivas} com Flecha Excedida (f > f_adm) | {self.total_flechas_alerta} em Atencao (f/adm >= 85%)",
            "-" * 115,
            f"{'Viga':<6} | {'Secao':<10} | {'M- (tf.m)':<9} | {'M+ (tf.m)':<9} | {'As (cm2)':<8} | {'Vsd (tf)':<8} | {'VRd2 (tf)':<9} | {'f (cm)':<7} | {'f.adm':<6} | {'f/adm':<6} | {'Status':<8}",
            "-" * 115,
        ]

        for v in vigas_alvo:
            f_str = f"{v.flecha_max_cm:.1f}" if v.flecha_max_cm > 0 else "-"
            f_adm_str = f"{v.flecha_adm_cm:.1f}" if v.flecha_adm_cm > 0 else "-"
            f_ratio_str = f"{v.flecha_ratio_max * 100:.0f}%" if v.flecha_ratio_max > 0 else "-"

            linhas.append(
                f"{v.nome:<6} | {v.secao_predominante:<10} | {v.m_neg_max_tfm:>9.1f} | {v.m_pos_max_tfm:>9.1f} | "
                f"{v.as_max_cm2:>8.1f} | {v.vsd_max_tf:>8.1f} | {v.vrd2_tf:>9.1f} | {f_str:>7} | {f_adm_str:>6} | {f_ratio_str:>6} | {v.status:<8}"
            )
            if v.falhas:
                linhas.append(f"       -> Falhas: {'; '.join(v.falhas)}")
            if v.sugestao_correcao:
                linhas.append(f"       -> Solucao Sugerida: {v.sugestao_correcao}")

        linhas.append("-" * 115)

        if self.erros_tabela_ferros:
            linhas.append(f"\n[ERROS EM RESESTERR.LST] Total: {len(self.erros_tabela_ferros)} falhas de bitola/detalhamento.")
            for err in self.erros_tabela_ferros[:4]:
                linhas.append(f"  * {err.strip()}")
            if len(self.erros_tabela_ferros) > 4:
                linhas.append(f"  ... e mais {len(self.erros_tabela_ferros) - 4} erros na tabela de ferros.")

        if self.avisos_ordcon:
            linhas.append(f"\n[AVISOS DE MODELAGEM EM ORDCON.LST] Total: {len(self.avisos_ordcon)} ocorrencias.")
            for av in self.avisos_ordcon[:4]:
                linhas.append(f"  * {av.strip()}")

        linhas.append("=" * 115 + "\n")
        return "\n".join(linhas)


class TQSBeamAnalyzer:
    """
    Auditor e diagnosticador avançado de vigas de concreto armado no CAD/TQS V25.
    Lê e processa diretamente:
      - ESTRIB.LST: Verificação de esmagamento de bielas comprimidas (Vsd > VRd2), estribagem e vãos.
      - RELGER.LST: Esforços envolventes de flexão (M-, M+), armaduras calculadas (As),
                    seções, vãos e verificações de ELS (Flechas calculadas vs Flechas admissíveis).
      - RESESTERR.LST: Erros de detalhamento e geração de ferros (bitolas sentinelas).
      - ORDCON.LST: Avisos geométricos de carregamento e consistência de apoios.
    """

    def __init__(self, caminho_ou_nome_edificio: str, pasta_raiz_tqs: Optional[str] = None):
        leitor = TQSBuildingReader(caminho_ou_nome_edificio, pasta_raiz_tqs or r"C:\TQS")
        self.caminho_edificio = leitor.caminho_edificio
        self.nome_edificio = leitor.nome_edificio
        self.pasta_raiz = os.path.dirname(self.caminho_edificio)

    def listar_pastas_vigas(self) -> List[Tuple[str, str]]:
        """
        Localiza todas as pastas de vigas dos pavimentos do edifício.
        Retorna lista de (nome_pavimento, caminho_pasta_vigas).
        """
        pastas = []
        ignorar = ["ESPACIAL", "PILAR", "FUNDAC", "GERAIS", "SISE", "ARQ MODELO", "SELOS", "Alvest", "INFRA", "PREMOLD"]

        if not os.path.exists(self.caminho_edificio):
            return []

        for item in sorted(os.listdir(self.caminho_edificio)):
            p = os.path.join(self.caminho_edificio, item)
            if not os.path.isdir(p) or item in ignorar or "_BKP_" in item:
                continue

            pasta_vigas = os.path.join(p, "VIGAS")
            if os.path.isdir(pasta_vigas):
                tem_lst = (
                    os.path.exists(os.path.join(pasta_vigas, "ESTRIB.LST"))
                    or os.path.exists(os.path.join(pasta_vigas, "RELGER.LST"))
                    or any(f.endswith(".DAT") for f in os.listdir(pasta_vigas))
                )
                if tem_lst:
                    pastas.append((item, pasta_vigas))

        return pastas

    def localizar_pasta_vigas(self, filtro_pavimento: Optional[str] = None) -> List[Tuple[str, str]]:
        """Filtra pastas de vigas correspondentes ao pavimento solicitado."""
        todos = self.listar_pastas_vigas()
        if not filtro_pavimento or filtro_pavimento.lower() in ["todos", "all", "*"]:
            return todos

        filtro_norm = _remover_acentos(filtro_pavimento)
        correspondencias = []
        for nome, caminho in todos:
            nome_norm = _remover_acentos(nome)
            if filtro_norm in nome_norm or nome_norm in filtro_norm:
                correspondencias.append((nome, caminho))

        if not correspondencias:
            for nome, caminho in todos:
                nome_norm = _remover_acentos(nome)
                if "terreo" in filtro_norm and "terreo" in nome_norm:
                    correspondencias.append((nome, caminho))
                elif any(num in filtro_norm for num in ["2", "3", "4", "5", "tipo"]) and any(num in nome_norm for num in ["2", "3", "4", "5", "tipo"]):
                    correspondencias.append((nome, caminho))

        return correspondencias if correspondencias else todos

    def analisar_pavimento(
        self,
        nome_pavimento: str,
        pasta_vigas: str,
        filtro_viga: Optional[str] = None
    ) -> AuditoriaVigasResultado:
        """Executa a auditoria completa de vigas para uma pasta específica."""
        import time
        inicio = time.time()

        res = AuditoriaVigasResultado(
            edificio=self.nome_edificio,
            pavimento=nome_pavimento,
            pasta_vigas=pasta_vigas,
        )

        caminho_estrib = os.path.join(pasta_vigas, "ESTRIB.LST")
        caminho_relger = os.path.join(pasta_vigas, "RELGER.LST")
        caminho_resesterr = os.path.join(pasta_vigas, "RESESTERR.LST")
        caminho_ordcon = os.path.join(pasta_vigas, "ORDCON.LST")

        # 1. Parse de RESESTERR.LST
        if os.path.exists(caminho_resesterr):
            try:
                with open(caminho_resesterr, "r", encoding="latin1", errors="ignore") as f:
                    for l in f:
                        l_str = l.strip()
                        if "ERRO" in l_str or "AVISO" in l_str:
                            res.erros_tabela_ferros.append(l_str)
            except Exception:
                pass

        # 2. Parse de ORDCON.LST
        if os.path.exists(caminho_ordcon):
            try:
                with open(caminho_ordcon, "r", encoding="latin1", errors="ignore") as f:
                    for l in f:
                        l_str = l.strip()
                        if any(k in l_str for k in ["Soma da", "Largura do pilar", "ERRO", "AVISO"]):
                            res.avisos_ordcon.append(l_str)
            except Exception:
                pass

        # 3. Parse de ESTRIB.LST
        mapa_vigas_estrib = {}
        if os.path.exists(caminho_estrib):
            mapa_vigas_estrib = self._parse_estrib_lst(caminho_estrib, res)

        # 4. Parse de RELGER.LST
        mapa_vigas_relger = {}
        if os.path.exists(caminho_relger):
            mapa_vigas_relger = self._parse_relger_lst(caminho_relger)

        # 5. Consolidação e Cruzamento de Dados (ELU + ELS)
        todas_chaves = sorted(list(set(list(mapa_vigas_estrib.keys()) + list(mapa_vigas_relger.keys()))))
        vigas_consolidadas = []

        for k in todas_chaves:
            v_estrib = mapa_vigas_estrib.get(k)
            v_relger = mapa_vigas_relger.get(k)

            v_diag = self._consolidar_viga(k, v_estrib, v_relger, res.fck_kgf_cm2)

            if filtro_viga:
                filtro_clean = filtro_viga.strip().upper()
                if not filtro_clean.startswith("V") and filtro_clean.isdigit():
                    filtro_clean = f"V{filtro_clean}"
                if v_diag.nome.upper() != filtro_clean:
                    continue

            vigas_consolidadas.append(v_diag)

        res.vigas = vigas_consolidadas
        res.duracao_segundos = time.time() - inicio
        return res

    def _parse_estrib_lst(self, caminho_arquivo: str, res_pai: AuditoriaVigasResultado) -> Dict[int, Dict[str, Any]]:
        """Lê ESTRIB.LST e extrai dimensionamento ao cisalhamento e bielas via posições fixas exatas."""
        mapa = {}
        try:
            with open(caminho_arquivo, "r", encoding="latin1", errors="ignore") as f:
                conteudo = f.read()
        except Exception:
            return mapa

        m_mat = re.search(r"CONCRETO\s*-\s*FCK\s*=\s*([\d\.]+)", conteudo)
        if m_mat:
            res_pai.fck_kgf_cm2 = float(m_mat.group(1))

        m_aco = re.search(r"ACO\s*-\s*FYK\s*=\s*([\d\.]+)", conteudo)
        if m_aco:
            res_pai.fyk_kgf_cm2 = float(m_aco.group(1))

        blocos = re.split(r"\n\s*VIGA=\s*", conteudo)
        for bloco in blocos[1:]:
            m_v = re.match(r"(\d+)\s*-\s*(\w+)", bloco)
            if not m_v:
                continue
            v_num = int(m_v.group(1))
            v_nome = m_v.group(2)

            vaos_dados = []
            vaos_blocos = re.split(r"\n\s*VAO=\s*", bloco)
            for vb in vaos_blocos[1:]:
                m_vao = re.match(
                    r"(\w+)\s*-\s*COMPRIMENTO=\s*([\d\.]+)\s*M\s*-\s*LARGURA=\s*([\d\.]+)\s*M\s*-\s*ALTURA=\s*([\d\.]+)\s*M",
                    vb
                )
                if not m_vao:
                    continue
                vao_id = m_vao.group(1)
                comp = float(m_vao.group(2))
                bw = float(m_vao.group(3)) * 100.0  # cm
                h = float(m_vao.group(4)) * 100.0   # cm

                vsd_max = 0.0
                vrd2_max = 0.0
                bit_max = 0.0
                esp_min = 999.0
                nr_max = 2
                tem_biela_excedida = False
                tem_bitola_invalida = False

                for l in vb.split("\n"):
                    if re.match(r"^\s*\d+\s*-\s*\d+", l):
                        try:
                            vsd_s = l[80:86].strip()
                            vrd2_s = l[86:93].strip()
                            bitesc_s = l[93:104].strip()
                            espesc_s = l[104:112].strip()
                            nr_s = l[112:118].strip()

                            if vsd_s:
                                vsd_val = float(vsd_s)
                                if vsd_val > vsd_max:
                                    vsd_max = vsd_val
                            if vrd2_s:
                                vrd2_val = float(vrd2_s)
                                if vrd2_val > vrd2_max:
                                    vrd2_max = vrd2_val
                            if bitesc_s:
                                bit_val = float(bitesc_s)
                                if bit_val > bit_max:
                                    bit_max = bit_val
                                if bit_val >= 50.0:
                                    tem_bitola_invalida = True
                            if espesc_s:
                                esp_val = float(espesc_s)
                                if 0 < esp_val < esp_min:
                                    esp_min = esp_val
                            if nr_s:
                                nr_val = int(re.sub(r"[^\d]", "", nr_s) or 2)
                                if nr_val > nr_max:
                                    nr_max = nr_val
                        except Exception:
                            pass

                m_biela_msg = re.search(
                    r"FORCA CORTANTE CALCULO=\s*([\d\.]+)\s*TF\s*EH > LIMITE COMPRESSAO BIELA =\s*([\d\.]+)",
                    vb
                )
                if m_biela_msg:
                    tem_biela_excedida = True
                    vsd_ex = float(m_biela_msg.group(1))
                    vrd2_ex = float(m_biela_msg.group(2))
                    if vsd_ex > vsd_max:
                        vsd_max = vsd_ex
                    if vrd2_ex > 0:
                        vrd2_max = vrd2_ex

                if "COMPRESSAO DIAGONAL DO CONCRETO" in vb and "EH > QUE A ADMISSIVEL" in vb:
                    tem_biela_excedida = True

                eh_curto = (comp < 0.60)
                biela_ratio = (vsd_max / vrd2_max) if vrd2_max > 0 else 0.0

                vaos_dados.append({
                    "vao_id": vao_id,
                    "comp_m": comp,
                    "bw_cm": bw,
                    "h_cm": h,
                    "vsd_max": vsd_max,
                    "vrd2": vrd2_max,
                    "biela_ratio": biela_ratio,
                    "bitola_estribo": bit_max,
                    "espacamento_estribo": esp_min if esp_min != 999.0 else 0.0,
                    "ramos_estribo": nr_max,
                    "eh_biela_excedida": tem_biela_excedida,
                    "eh_bitola_invalida": tem_bitola_invalida,
                    "eh_vao_curto_espurio": eh_curto,
                })

            mapa[v_num] = {
                "num": v_num,
                "nome": v_nome,
                "vaos": vaos_dados,
            }

        return mapa

    def _parse_relger_lst(self, caminho_arquivo: str) -> Dict[int, Dict[str, Any]]:
        """Lê RELGER.LST e extrai esforços envolventes de flexão, armaduras e ELS (flechas)."""
        mapa = {}
        try:
            with open(caminho_arquivo, "r", encoding="latin1", errors="ignore") as f:
                conteudo = f.read()
        except Exception:
            return mapa

        viga_chunks = re.split(r"\n(?=Viga=\s*\d+)", conteudo)
        for chunk in viga_chunks:
            m_v = re.search(r"Viga=\s*(\d+)\s+([^\n\r]+)", chunk)
            if not m_v:
                continue
            v_num = int(m_v.group(1))
            v_nome = m_v.group(2).strip().split()[0]

            vaos_rel = []
            vaos_blocos = re.split(r"\n(?=Vao=\s*\w+)", chunk)
            for vb in vaos_blocos:
                m_vao = re.search(
                    r"Vao=\s*(\w+)\s*/L=\s*([\d\.]+)\s*/B=\s*([\d\.]+)\s*/H=\s*([\d\.]+)",
                    vb
                )
                if not m_vao:
                    continue
                vao_id = m_vao.group(1)
                comp_m = float(m_vao.group(2))
                bw_cm = float(m_vao.group(3)) * 100.0
                h_cm = float(m_vao.group(4)) * 100.0

                # Extrai ELS (Flechas)
                m_fl = re.search(r"Flecha=\s*([\d\.]+)", vb)
                m_adm = re.search(r"Fle\.?Adm\.?=\s*([\d\.]+)", vb)
                tem_excesso_els = ("< Fl.Calc" in vb)

                flecha_cm = float(m_fl.group(1)) if m_fl else 0.0
                flecha_adm_cm = float(m_adm.group(1)) if m_adm else 0.0
                flecha_ratio = (flecha_cm / flecha_adm_cm) if flecha_adm_cm > 0 else 0.0

                relacao_l_f = (comp_m * 100.0 / flecha_cm) if flecha_cm > 0 else 0.0
                contra_flecha = round(flecha_cm - flecha_adm_cm, 1) if flecha_cm > flecha_adm_cm else 0.0
                eh_excedida = tem_excesso_els or (flecha_cm > flecha_adm_cm > 0.0)
                eh_alerta = (0.85 <= flecha_ratio <= 1.0) and not eh_excedida

                vaos_rel.append({
                    "vao_id": vao_id,
                    "comp_m": comp_m,
                    "bw_cm": bw_cm,
                    "h_cm": h_cm,
                    "flecha_cm": flecha_cm,
                    "flecha_adm_cm": flecha_adm_cm,
                    "flecha_ratio": flecha_ratio,
                    "relacao_l_f": relacao_l_f,
                    "eh_flecha_excessiva": eh_excedida,
                    "eh_flecha_alerta": eh_alerta,
                    "contra_flecha_sugerida": contra_flecha,
                })

            m_negs = [float(x) for x in re.findall(r"M\.\[-\]\s*=\s*([\d\.]+)\s*tf\*\s*m", chunk)]
            m_pos = [float(x) for x in re.findall(r"M\.\[\+\]\s*Max=\s*([\d\.]+)\s*tf\*\s*m", chunk)]
            as_vals = [float(x) for x in re.findall(r"\bAs\s*=\s*([\d\.]+)\s+-\w+-", chunk)]

            barras = re.findall(r"\[\s*(\d+\s*B\s*[\d\.]+mm)\s*\]", chunk)
            det_barras = ", ".join(set(barras[:4])) if barras else ""

            mapa[v_num] = {
                "num": v_num,
                "nome": v_nome,
                "vaos": vaos_rel,
                "m_neg_max": max(m_negs) if m_negs else 0.0,
                "m_pos_max": max(m_pos) if m_pos else 0.0,
                "as_max": max(as_vals) if as_vals else 0.0,
                "detalhes_barras": det_barras,
            }

        return mapa

    def _consolidar_viga(
        self,
        v_num: int,
        v_estrib: Optional[Dict[str, Any]],
        v_relger: Optional[Dict[str, Any]],
        fck_kgf_cm2: float
    ) -> VigaDiagnostico:
        """Cruza dados de cisalhamento, flexão e ELS (flechas) para gerar diagnóstico e soluções."""
        nome = (v_estrib.get("nome") if v_estrib else None) or (v_relger.get("nome") if v_relger else f"V{v_num}")

        vaos_estrib = v_estrib.get("vaos", []) if v_estrib else []
        vaos_rel = v_relger.get("vaos", []) if v_relger else []

        # Mapa de dados ELS por vao_id
        mapa_els = {vr.get("vao_id", str(i + 1)): vr for i, vr in enumerate(vaos_rel)}

        vaos_obj = []
        vaos_fonte = vaos_estrib if vaos_estrib else vaos_rel

        for i, vr in enumerate(vaos_fonte):
            vid = vr.get("vao_id", str(i + 1))
            els_dados = mapa_els.get(vid, {})

            fl_cm = els_dados.get("flecha_cm", 0.0)
            fl_adm = els_dados.get("flecha_adm_cm", 0.0)
            fl_ratio = els_dados.get("flecha_ratio", 0.0)
            rel_l_f = els_dados.get("relacao_l_f", 0.0)
            eh_fl_exc = els_dados.get("eh_flecha_excessiva", False)
            eh_fl_alt = els_dados.get("eh_flecha_alerta", False)
            cf_sug = els_dados.get("contra_flecha_sugerida", 0.0)

            vaos_obj.append(VigaVao(
                vao_id=vid,
                comp_m=vr.get("comp_m", 0.0),
                bw_cm=vr.get("bw_cm", 20.0),
                h_cm=vr.get("h_cm", 60.0),
                vsd_max_tf=vr.get("vsd_max", 0.0),
                vrd2_tf=vr.get("vrd2", 0.0),
                biela_ratio=vr.get("biela_ratio", 0.0),
                bitola_estribo_mm=vr.get("bitola_estribo", 0.0),
                espacamento_estribo_cm=vr.get("espacamento_estribo", 0.0),
                ramos_estribo=vr.get("ramos_estribo", 2),
                eh_biela_excedida=vr.get("eh_biela_excedida", False),
                eh_bitola_invalida=vr.get("eh_bitola_invalida", False),
                eh_vao_curto_espurio=vr.get("eh_vao_curto_espurio", False),
                flecha_cm=fl_cm,
                flecha_adm_cm=fl_adm,
                flecha_ratio=fl_ratio,
                relacao_l_f=rel_l_f,
                eh_flecha_excessiva=eh_fl_exc,
                eh_flecha_alerta=eh_fl_alt,
                contra_flecha_sugerida_cm=cf_sug,
            ))

        sec_predominante = "-"
        if vaos_obj:
            sec_predominante = f"{vaos_obj[0].bw_cm:.0f}x{vaos_obj[0].h_cm:.0f} cm"

        m_neg_max = v_relger.get("m_neg_max", 0.0) if v_relger else 0.0
        m_pos_max = v_relger.get("m_pos_max", 0.0) if v_relger else 0.0
        as_max = v_relger.get("as_max", 0.0) if v_relger else 0.0
        detalhes = v_relger.get("detalhes_barras", "") if v_relger else ""

        vsd_max = max((v.vsd_max_tf for v in vaos_obj), default=0.0)
        vrd2_max = max((v.vrd2_tf for v in vaos_obj), default=0.0)
        biela_ratio_max = max((v.biela_ratio for v in vaos_obj), default=0.0)

        # ELS Máximos
        flecha_max = max((v.flecha_cm for v in vaos_obj), default=0.0)
        flecha_adm = max((v.flecha_adm_cm for v in vaos_obj if v.flecha_cm == flecha_max), default=0.0)
        flecha_ratio_max = max((v.flecha_ratio for v in vaos_obj), default=0.0)
        tem_flecha_excessiva = any(v.eh_flecha_excessiva for v in vaos_obj)
        tem_flecha_alerta = any(v.eh_flecha_alerta for v in vaos_obj)
        contra_flecha_max = max((v.contra_flecha_sugerida_cm for v in vaos_obj), default=0.0)

        falhas = []
        status = "OK"

        # 1. Verificação de Biela (ELU - Cisalhamento)
        tem_biela_excedida = any(v.eh_biela_excedida for v in vaos_obj) or (vsd_max > vrd2_max > 0.0)
        if tem_biela_excedida:
            status = "CRITICO"
            pct_excesso = (biela_ratio_max - 1.0) * 100.0 if biela_ratio_max > 1.0 else 0.0
            falhas.append(f"Ruptura de biela comprimida (Vsd = {vsd_max:.1f} tf > VRd2 = {vrd2_max:.1f} tf, +{pct_excesso:.1f}%)")

        # 2. Verificação de Bitola Sentinela 50mm
        tem_bitola_50 = any(v.eh_bitola_invalida or v.bitola_estribo_mm >= 50.0 for v in vaos_obj)
        if tem_bitola_50:
            status = "CRITICO"
            falhas.append("Bitola de estribo sentinela (50.0mm) atribuida pelo TQS")

        # 3. Verificação de ELS (Flechas Excessivas)
        if tem_flecha_excessiva:
            status = "CRITICO"
            for v in vaos_obj:
                if v.eh_flecha_excessiva:
                    excesso_fl = (v.flecha_ratio - 1.0) * 100.0 if v.flecha_ratio > 1.0 else 0.0
                    falhas.append(
                        f"Flecha excessiva em ELS (f = {v.flecha_cm:.1f} cm > f_adm = {v.flecha_adm_cm:.1f} cm, +{excesso_fl:.1f}%) no Vao {v.vao_id}"
                    )
        elif tem_flecha_alerta:
            if status != "CRITICO":
                status = "ALERTA"
            for v in vaos_obj:
                if v.eh_flecha_alerta:
                    falhas.append(
                        f"Flecha proxima do limite ELS ({v.flecha_cm:.1f} cm de {v.flecha_adm_cm:.1f} cm, {v.flecha_ratio * 100:.0f}%) no Vao {v.vao_id}"
                    )

        # 4. Verificação de Vãos Curtos Espúrios
        vaos_curtos = [v for v in vaos_obj if v.eh_vao_curto_espurio]
        if vaos_curtos:
            if status == "OK":
                status = "ALERTA"
            falhas.append(f"Vao espurio curto ({', '.join(f'Vao {v.vao_id}: {v.comp_m*100:.0f}cm' for v in vaos_curtos)})")

        # 5. Verificação de Armadura Longitudinal Pesada (> 80 cm²)
        if as_max > 80.0:
            if status == "OK":
                status = "ALERTA"
            falhas.append(f"Armadura longitudinal pesada ({as_max:.1f} cm2)")

        # 6. Cálculo das Soluções Sugeridas de Engenharia (ELU + ELS)
        sugestoes = []

        # A) Solução para Biela Comprimida
        if tem_biela_excedida and vaos_obj:
            vao_critico = max(vaos_obj, key=lambda v: v.biela_ratio)
            bw_atual = vao_critico.bw_cm
            h_atual = vao_critico.h_cm
            fck_mpa = fck_kgf_cm2 / 10.0
            alpha_v2 = 1.0 - (fck_mpa / 250.0)
            fcd_tf_m2 = (fck_kgf_cm2 / 1.4) * 10.0
            d_atual_m = 0.9 * (h_atual / 100.0)

            try:
                denominador_bw = 0.27 * alpha_v2 * fcd_tf_m2 * d_atual_m
                if denominador_bw > 0:
                    bw_req_m = (1.10 * vsd_max) / denominador_bw
                    bw_req_cm = math.ceil(bw_req_m * 100.0 / 5.0) * 5.0

                    denominador_h = 0.27 * alpha_v2 * fcd_tf_m2 * (bw_atual / 100.0) * 0.9
                    h_req_m = (1.10 * vsd_max) / denominador_h if denominador_h > 0 else 0
                    h_req_cm = math.ceil(h_req_m * 100.0 / 5.0) * 5.0

                    if bw_req_cm > bw_atual:
                        sugestoes.append(f"Alargar para {bw_req_cm:.0f}x{h_atual:.0f} cm (ou elevar altura para {bw_atual:.0f}x{h_req_cm:.0f} cm)")
                    else:
                        sugestoes.append("Alargar secao em +5 a 10 cm na largura")
            except Exception:
                sugestoes.append(f"Alargar secao para suportar cortante de {vsd_max:.1f} tf")

        # B) Solução para ELS (Flechas Excessivas)
        if tem_flecha_excessiva:
            vao_fl_critico = max(vaos_obj, key=lambda v: v.flecha_ratio)
            h_atual = vao_fl_critico.h_cm
            comp_m = vao_fl_critico.comp_m
            # NBR 6118: estimativa de h_min para flecha aproximada (L / 16 para contínua, L / 12 para biapoiada)
            h_min_estimado_cm = math.ceil((comp_m * 100.0 / 16.0) / 5.0) * 5.0

            if h_min_estimado_cm > h_atual:
                sugestoes.append(
                    f"Aumentar altura para h={h_min_estimado_cm:.0f} cm para vencer vao de {comp_m:.2f}m (ou adotar contra-flecha de {contra_flecha_max:.1f} cm)"
                )
            else:
                sugestoes.append(f"Adotar contra-flecha executiva de {contra_flecha_max:.1f} cm no Vao {vao_fl_critico.vao_id}")

        elif tem_bitola_50 and vaos_curtos:
            sugestoes.append("Unificar nos no modelador para eliminar vaos residuais de poucos centimetros")

        sugestao_final = " | ".join(sugestoes) if sugestoes else None

        return VigaDiagnostico(
            numero=v_num,
            nome=nome,
            secao_predominante=sec_predominante,
            num_vaos=len(vaos_obj),
            vaos=vaos_obj,
            m_neg_max_tfm=m_neg_max,
            m_pos_max_tfm=m_pos_max,
            as_max_cm2=as_max,
            detalhes_longitudinais=detalhes,
            vsd_max_tf=vsd_max,
            vrd2_tf=vrd2_max,
            biela_ratio_max=biela_ratio_max,
            flecha_max_cm=flecha_max,
            flecha_adm_cm=flecha_adm,
            flecha_ratio_max=flecha_ratio_max,
            tem_flecha_excessiva=tem_flecha_excessiva,
            tem_flecha_alerta=tem_flecha_alerta,
            contra_flecha_max_cm=contra_flecha_max,
            status=status,
            falhas=falhas,
            sugestao_correcao=sugestao_final,
        )

    def analisar(
        self,
        pavimento: Optional[str] = None,
        filtro_viga: Optional[str] = None
    ) -> List[AuditoriaVigasResultado]:
        """Audita todos os pavimentos de vigas selecionados do edifício."""
        pastas = self.localizar_pasta_vigas(pavimento)
        resultados = []
        for nome_pav, pasta in pastas:
            res = self.analisar_pavimento(nome_pav, pasta, filtro_viga=filtro_viga)
            resultados.append(res)
        return resultados
