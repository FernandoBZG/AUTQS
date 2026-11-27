import os
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.tqs_adapter.building_reader import TQSBuildingReader
from src.tqs_adapter.pavimentos import filtrar_pavimentos, listar_pastas_pavimento


@dataclass
class LajeInfo:
    """Informações geométricas e estruturais de uma laje individual."""
    id_laje: str
    area_m2: float
    forma_m2: float
    volume_m3: float
    espessura_cm: float = 0.0
    tipo: str = "Maciça"
    cargas_concentradas: List[float] = field(default_factory=list)
    alertas: List[str] = field(default_factory=list)
    risco_flecha: bool = False


@dataclass
class PavimentoLajesResumo:
    """Consolidação das lajes de um pavimento específico."""
    pavimento_nome: str
    pasta_pavimento: str
    total_lajes: int = 0
    area_total_m2: float = 0.0
    forma_total_m2: float = 0.0
    volume_total_m3: float = 0.0
    espessura_media_cm: float = 0.0
    fck_mpa: float = 0.0
    pe_direito_m: float = 0.0
    lajes: Dict[str, LajeInfo] = field(default_factory=dict)
    alertas_grelha: List[str] = field(default_factory=list)
    balancos_detectados: List[str] = field(default_factory=list)
    lajes_criticas_flecha: List[str] = field(default_factory=list)

    def para_dict(self) -> Dict[str, Any]:
        return {
            "pavimento_nome": self.pavimento_nome,
            "total_lajes": self.total_lajes,
            "area_total_m2": round(self.area_total_m2, 2),
            "forma_total_m2": round(self.forma_total_m2, 2),
            "volume_total_m3": round(self.volume_total_m3, 2),
            "espessura_media_cm": round(self.espessura_media_cm, 1),
            "fck_mpa": self.fck_mpa,
            "pe_direito_m": round(self.pe_direito_m, 2),
            "alertas_grelha": self.alertas_grelha,
            "balancos_detectados": self.balancos_detectados,
            "lajes_criticas_flecha": self.lajes_criticas_flecha,
            "lajes": {
                k: {
                    "area_m2": round(v.area_m2, 2),
                    "forma_m2": round(v.forma_m2, 2),
                    "volume_m3": round(v.volume_m3, 2),
                    "espessura_cm": round(v.espessura_cm, 1),
                    "tipo": v.tipo,
                    "cargas_concentradas": v.cargas_concentradas,
                    "alertas": v.alertas,
                    "risco_flecha": v.risco_flecha,
                }
                for k, v in self.lajes.items()
            }
        }


@dataclass
class EdificioLajesResultado:
    """Resultado global da auditoria de lajes em todos os pavimentos do edifício."""
    edificio_nome: str
    caminho_edificio: str
    pavimentos: Dict[str, PavimentoLajesResumo] = field(default_factory=dict)
    total_lajes_edificio: int = 0
    area_total_edificio_m2: float = 0.0
    volume_total_edificio_m3: float = 0.0
    alertas_totais_contagem: int = 0

    def para_dict(self) -> Dict[str, Any]:
        return {
            "edificio_nome": self.edificio_nome,
            "caminho_edificio": self.caminho_edificio,
            "total_lajes_edificio": self.total_lajes_edificio,
            "area_total_edificio_m2": round(self.area_total_edificio_m2, 2),
            "volume_total_edificio_m3": round(self.volume_total_edificio_m3, 2),
            "alertas_totais_contagem": self.alertas_totais_contagem,
            "pavimentos": {k: v.para_dict() for k, v in self.pavimentos.items()}
        }

    def para_resumo_executivo(self) -> str:
        """Gera relatório em Markdown técnico com conformidade à NBR 6118."""
        status = "✅ CONFORME" if self.alertas_totais_contagem == 0 else f"⚠️ {self.alertas_totais_contagem} ALERTAS DETECTADOS"
        linhas = [
            f"# AUDITORIA DE LAJES, GRELHA E FLECHAS: {self.edificio_nome.upper()}",
            f"**Status Geral da Análise:** {status}",
            f"- **Total de Lajes Auditadas:** `{self.total_lajes_edificio}` em `{len(self.pavimentos)}` pavimentos",
            f"- **Área Estruturada Total:** `{self.area_total_edificio_m2:.2f} m²`",
            f"- **Volume de Concreto Estimado:** `{self.volume_total_edificio_m3:.2f} m³`\n",
            "### 1. Resumo por Pavimento"
        ]

        linhas.append("| Pavimento | Lajes | Área (m²) | Fôrmas (m²) | Vol. Conc. (m³) | Espessura Média | Alertas |")
        linhas.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

        for nome, pav in self.pavimentos.items():
            tot_al = len(pav.alertas_grelha) + len(pav.balancos_detectados) + len(pav.lajes_criticas_flecha)
            al_txt = f"⚠️ {tot_al}" if tot_al > 0 else "✅ 0"
            linhas.append(
                f"| **{nome}** | {pav.total_lajes} | {pav.area_total_m2:.1f} | {pav.forma_total_m2:.1f} | "
                f"{pav.volume_total_m3:.1f} | {pav.espessura_media_cm:.1f} cm | {al_txt} |"
            )

        # Seção de Alertas Críticos
        alertas_existentes = False
        for nome, pav in self.pavimentos.items():
            if pav.alertas_grelha or pav.balancos_detectados or pav.lajes_criticas_flecha:
                if not alertas_existentes:
                    linhas.append("\n### 2. Diagnóstico de Alertas Estruturais e Geométricos")
                    alertas_existentes = True

                linhas.append(f"\n#### Pavimento: {nome}")
                for b in pav.balancos_detectados:
                    linhas.append(f"- ⚠️ **Balanço não travado:** {b}")
                for a in pav.alertas_grelha:
                    linhas.append(f"- ⚠️ **Grelha / Apoio:** {a}")
                for f_crit in pav.lajes_criticas_flecha:
                    linhas.append(f"- 🔍 **Risco de Flecha Excessiva:** Laje `{f_crit}` possui espessura delgada em relação à área/vão. Verificar flecha diferida no tempo conforme item 17.3 da NBR 6118.")

        if not alertas_existentes:
            linhas.append("\n> [!NOTE]\n> Nenhuma inconsistência grave de bordos livres, balanços soltos ou desníveis foi detectada nos modelos de grelha.")

        return "\n".join(linhas)


class TQSSlabAnalyzer:
    """
    Motor de extração e auditoria técnica de lajes e grelha no CAD/TQS V25.
    Lê relatórios LDF/LST de pavimento, GREEXT, GREFOR e MENAVI.
    """

    def __init__(self, caminho_ou_nome_edificio: str, pasta_raiz_tqs: Optional[str] = None):
        leitor = TQSBuildingReader(caminho_ou_nome_edificio, pasta_raiz_tqs or r"C:\TQS")
        self.caminho_edificio = leitor.caminho_edificio
        self.nome_edificio = leitor.nome_edificio

    def analisar(self, pavimento_filtro: Optional[str] = None) -> EdificioLajesResultado:
        """Executa a análise de lajes em todos os pavimentos ou em um filtrado."""
        resultado = EdificioLajesResultado(
            edificio_nome=self.nome_edificio,
            caminho_edificio=self.caminho_edificio
        )

        pastas = filtrar_pavimentos(listar_pastas_pavimento(self.caminho_edificio), pavimento_filtro)

        for d, caminho_pav in pastas:
            pav_res = self._analisar_pavimento(d, caminho_pav)
            if pav_res and pav_res.total_lajes > 0:
                resultado.pavimentos[d] = pav_res
                resultado.total_lajes_edificio += pav_res.total_lajes
                resultado.area_total_edificio_m2 += pav_res.area_total_m2
                resultado.volume_total_edificio_m3 += pav_res.volume_total_m3
                resultado.alertas_totais_contagem += (
                    len(pav_res.alertas_grelha) + len(pav_res.balancos_detectados) + len(pav_res.lajes_criticas_flecha)
                )

        return resultado

    def _analisar_pavimento(self, nome_pav: str, pasta_pav: str) -> Optional[PavimentoLajesResumo]:
        """Extrai dados de lajes de um pavimento a partir dos relatórios disponíveis."""
        pav = PavimentoLajesResumo(pavimento_nome=nome_pav, pasta_pavimento=pasta_pav)

        # 1. Leitura de GREFOR.LST (fck, pé-direito, critérios)
        p_grefor = os.path.join(pasta_pav, "GREFOR.LST")
        if os.path.exists(p_grefor):
            try:
                with open(p_grefor, "r", encoding="latin1", errors="replace") as f:
                    txt = f.read()
                m_fck = re.search(r"fck do concreto.*?=\s*(\d+(?:\.\d+)?)", txt, re.IGNORECASE)
                if m_fck:
                    pav.fck_mpa = float(m_fck.group(1))
                m_pd = re.search(r"P[ée]\s*direito do piso.*?,?\s*m\s*\.*\s*(\d+(?:\.\d+)?)", txt, re.IGNORECASE)
                if m_pd:
                    pav.pe_direito_m = float(m_pd.group(1))
            except Exception:
                pass

        # 2. Leitura de GREEXT.LST e MENAVI.LST (Avisos de balanços e barras hipostáticas)
        p_greext = os.path.join(pasta_pav, "GREEXT.LST")
        if os.path.exists(p_greext):
            try:
                with open(p_greext, "r", encoding="latin1", errors="replace") as f:
                    for line in f:
                        line_str = line.strip()
                        if "AVISO:" in line_str:
                            if "balanço" in line_str.lower() or "balano" in line_str.lower():
                                pav.balancos_detectados.append(line_str)
                            else:
                                pav.alertas_grelha.append(line_str)
            except Exception:
                pass

        p_menavi = os.path.join(pasta_pav, "MENAVI.LST")
        if os.path.exists(p_menavi):
            try:
                with open(p_menavi, "r", encoding="latin1", errors="replace") as f:
                    for line in f:
                        line_str = line.strip()
                        if "AVISO:" in line_str:
                            if "balanço" in line_str.lower() or "balano" in line_str.lower():
                                pav.balancos_detectados.append(line_str)
                            else:
                                pav.alertas_grelha.append(line_str)
            except Exception:
                pass

        # 3. Leitura do relatório principal do pavimento (<NOME_PAV>.LST ou *.LST)
        lst_candidatos = [
            os.path.join(pasta_pav, f"{nome_pav}.lst"),
            os.path.join(pasta_pav, f"{nome_pav}.LST"),
        ]
        # Se não encontrar com nome exato, pega qualquer .lst do diretório que não seja GRE*
        if not any(os.path.exists(p) for p in lst_candidatos):
            outros = [
                os.path.join(pasta_pav, f) for f in os.listdir(pasta_pav)
                if f.upper().endswith(".LST") and not f.upper().startswith("GRE") and not f.upper().startswith("MEN") and not f.upper().startswith("TAB")
            ]
            lst_candidatos.extend(outros)

        p_pav_lst = next((p for p in lst_candidatos if os.path.exists(p)), None)
        if not p_pav_lst:
            return pav if pav.total_lajes > 0 else None

        with open(p_pav_lst, "r", encoding="latin1", errors="replace") as f:
            conteudo = f.read()

        # Espessura média
        m_esp = re.search(r"Espessura m[ée]dia das lajes\s*=\s*(\d+(?:\.\d+)?)\s*cm", conteudo, re.IGNORECASE)
        if m_esp:
            pav.espessura_media_cm = float(m_esp.group(1))

        # Avisos no relatório do pavimento (ex: bordo livre em concavidade, viga e laje desniveladas)
        for line in conteudo.splitlines():
            line_s = line.strip()
            if "AVISO:" in line_s and ("Laje" in line_s or "laje" in line_s):
                pav.alertas_grelha.append(line_s)

        # Tabela de quantitativos de lajes (L1, L2, ...)
        # Ex: L1   6.95   6.95   .83
        linhas = conteudo.splitlines()
        em_quantitativos = False
        for line in linhas:
            if "Quantitativos" in line:
                em_quantitativos = True
                continue
            if em_quantitativos and ("Espessura média" in line or "Volume de concreto" in line or "Cargas sobre" in line):
                em_quantitativos = False

            if em_quantitativos:
                tokens = line.strip().split()
                if len(tokens) >= 4 and re.match(r"^L\d+$", tokens[0], re.IGNORECASE):
                    try:
                        id_l = tokens[0].upper()
                        area = float(tokens[1])
                        forma = float(tokens[2])
                        vol = float(tokens[3])
                        # Estimativa de espessura h = volume / area (em cm)
                        h_est = (vol / area * 100.0) if area > 0 else (pav.espessura_media_cm or 12.0)
                        
                        risco = False
                        # Critério NBR 6118: laje maciça com vão/área expressiva e h < 10cm
                        if area > 15.0 and h_est < 10.0:
                            risco = True
                            pav.lajes_criticas_flecha.append(id_l)

                        laje_info = LajeInfo(
                            id_laje=id_l,
                            area_m2=area,
                            forma_m2=forma,
                            volume_m3=vol,
                            espessura_cm=h_est,
                            risco_flecha=risco,
                        )
                        pav.lajes[id_l] = laje_info
                        pav.total_lajes += 1
                        pav.area_total_m2 += area
                        pav.forma_total_m2 += forma
                        pav.volume_total_m3 += vol
                    except ValueError:
                        continue

        if pav.total_lajes > 0 and pav.espessura_media_cm == 0.0:
            pav.espessura_media_cm = (pav.volume_total_m3 / pav.area_total_m2 * 100.0) if pav.area_total_m2 > 0 else 12.0

        return pav
