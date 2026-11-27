import os
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from src.tqs_adapter.building_reader import TQSBuildingReader


@dataclass
class CasoEstabilidade:
    """Dados de estabilidade para um caso simples de vento ou combinação ELU."""
    caso: int
    ang: float
    c_tot: float
    m2: float
    c_hor: float
    m1: float
    gama_z: Optional[float]  # None nas combinações de ELU: lá o TQS informa FAVt, que não é γz
    alfa: float
    fav_t: Optional[float] = None
    mult_h: Optional[float] = None
    obs: str = ""
    tipo: str = "SIMPLES"  # 'SIMPLES', 'ELU_VIGAS', 'ELU_PILARES'


@dataclass
class DeslocamentoELS:
    """Deslocamento de topo ou interpavimento verificado em ELS."""
    caso: int
    desl_h_cm: float
    desl_hc_cm: float
    relat_denominador: float  # Ex: 1931 para H/1931
    relat_texto: str         # Ex: 'H/1931' ou 'Hi/339'
    obs: str = ""
    piso: Optional[int] = None
    limite_denominador: float = 1700.0  # 1700 para topo, 850 para interpavimento
    passou: bool = True


@dataclass
class RelatorioEstabilidadeResultado:
    """Resultado estruturado e completo da análise de estabilidade global."""
    edificio_nome: str
    caminho_edificio: str
    altura_edificio_m: float
    cota_inicial_m: float
    cota_final_m: float
    modulo_elasticidade_tf_m2: float
    casos_simples: List[CasoEstabilidade] = field(default_factory=list)
    combinacoes_elu: List[CasoEstabilidade] = field(default_factory=list)
    deslocamentos_topo: List[DeslocamentoELS] = field(default_factory=list)
    deslocamentos_interpiso: List[DeslocamentoELS] = field(default_factory=list)
    
    # Métricas consolidadas
    gama_z_max: float = 1.0
    fav_t_max: float = 1.0
    alfa_max: float = 0.0
    classificacao_estrutura: str = "NÓS FIXOS"  # 'NÓS FIXOS', 'NÓS MÓVEIS', 'CRÍTICO'
    drift_topo_max_cm: float = 0.0
    drift_topo_relat: str = "H/1700"
    drift_topo_passou: bool = True
    drift_interpiso_max_cm: float = 0.0
    drift_interpiso_relat: str = "Hi/850"
    drift_interpiso_piso_critico: Optional[int] = None
    drift_interpiso_passou: bool = True
    alertas_normativos: List[str] = field(default_factory=list)

    def para_dict(self) -> Dict[str, Any]:
        return {
            "edificio_nome": self.edificio_nome,
            "caminho_edificio": self.caminho_edificio,
            "altura_edificio_m": self.altura_edificio_m,
            "cota_inicial_m": self.cota_inicial_m,
            "cota_final_m": self.cota_final_m,
            "modulo_elasticidade_tf_m2": self.modulo_elasticidade_tf_m2,
            "gama_z_max": round(self.gama_z_max, 3),
            "fav_t_max": round(self.fav_t_max, 3),
            "alfa_max": round(self.alfa_max, 3),
            "classificacao_estrutura": self.classificacao_estrutura,
            "drift_topo": {
                "max_cm": round(self.drift_topo_max_cm, 2),
                "relat": self.drift_topo_relat,
                "limite": "H/1700",
                "passou": self.drift_topo_passou,
            },
            "drift_interpiso": {
                "max_cm": round(self.drift_interpiso_max_cm, 2),
                "relat": self.drift_interpiso_relat,
                "piso_critico": self.drift_interpiso_piso_critico,
                "limite": "Hi/850",
                "passou": self.drift_interpiso_passou,
            },
            "alertas_normativos": self.alertas_normativos,
            "metricas": {
                "total_casos_simples": len(self.casos_simples),
                "total_combinacoes_elu": len(self.combinacoes_elu),
                "total_deslocamentos_els": len(self.deslocamentos_topo) + len(self.deslocamentos_interpiso),
            }
        }

    def para_resumo_executivo(self) -> str:
        """Gera relatório executivo em Markdown técnico conforme NBR 6118."""
        status_global = "✅ CONFORME" if (self.drift_topo_passou and self.drift_interpiso_passou and self.gama_z_max <= 1.30) else "⚠️ ATENÇÃO ESTRUTURAL"
        
        linhas = [
            f"# AUDITORIA DE ESTABILIDADE GLOBAL E ELS: {self.edificio_nome.upper()}",
            f"**Status Geral da Análise:** {status_global}",
            f"- **Altura Total ($H$):** `{self.altura_edificio_m:.2f} m` (Cotas: `{self.cota_inicial_m:.2f} m` a `{self.cota_final_m:.2f} m`)",
            f"- **Classificação da Estrutura (NBR 6118):** **{self.classificacao_estrutura}**",
            f"- **$\\gamma_z$ Máximo:** `{self.gama_z_max:.3f}` | **$FAV_t$ Máximo:** `{self.fav_t_max:.3f}` | **$\\alpha$ Máximo:** `{self.alfa_max:.3f}`\n",
            "### 1. Parâmetros de Instabilidade Global (ELU)"
        ]

        if self.gama_z_max <= 1.10:
            linhas.append("> [!NOTE]\n> **Estrutura de Nós Fixos ($\\gamma_z \\le 1.10$):** Os efeitos globais de 2ª ordem são desprezíveis (inferiores a 10% dos de 1ª ordem). O dimensionamento pode ser feito considerando apenas 1ª ordem.")
        elif self.gama_z_max <= 1.30:
            linhas.append(f"> [!TIP]\n> **Estrutura de Nós Móveis ($1.10 < \\gamma_z \\le 1.30$):** Os efeitos globais de 2ª ordem devem ser considerados. No TQS, a consideração pode ser realizada por majoração dos esforços de vento pelo coeficiente $0.95 \\cdot \\gamma_z$ ou via análise P-Delta.")
        else:
            linhas.append(f"> [!CAUTION]\n> **Estrutura com $\\gamma_z > 1.30$ ({self.gama_z_max:.3f}):** Instabilidade excessiva! A NBR 6118 proíbe a estimativa simplificada por $\\gamma_z$. Recomenda-se aumentar a inércia dos pilares ou núcleos rígidos de contraventamento.")

        linhas.append("\n| Caso/Combinação | Ângulo | C.Tot (tf) | M1 (tf.m) | M2 (tf.m) | $\\gamma_z$ / $FAV_t$ | $\\alpha$ | Status |")
        linhas.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        
        casos_destaque = self.casos_simples + [c for c in self.combinacoes_elu if (c.fav_t and c.fav_t >= 1.09) or (c.gama_z and c.gama_z >= 1.09)][:6]
        for c in casos_destaque:
            val_z = c.fav_t if c.fav_t is not None else c.gama_z
            stat = "Nós Fixos" if val_z <= 1.10 else ("Nós Móveis" if val_z <= 1.30 else "Excessivo")
            linhas.append(f"| Caso {c.caso} ({c.tipo}) | {c.ang:.0f}° | {c.c_tot:.1f} | {c.m1:.1f} | {c.m2:.1f} | **`{val_z:.3f}`** | `{c.alfa:.3f}` | {stat} |")

        linhas.append("\n### 2. Deslocamentos Horizontais de Vento em ELS (Drift)")
        linhas.append("| Verificação | Desloc. Calculado | Relação | Limite Normativo | Conformidade |")
        linhas.append("| :--- | :---: | :---: | :---: | :---: |")
        
        conf_topo = "✅ Atende" if self.drift_topo_passou else "❌ Não Atende"
        linhas.append(f"| **Topo do Edifício (Global)** | `{self.drift_topo_max_cm:.2f} cm` | **`{self.drift_topo_relat}`** | `H/1700` | **{conf_topo}** |")
        
        conf_inter = "✅ Atende" if self.drift_interpiso_passou else "❌ Não Atende"
        piso_info = f" (Piso {self.drift_interpiso_piso_critico})" if self.drift_interpiso_piso_critico else ""
        linhas.append(f"| **Entre Pavimentos (Interpiso)** | `{self.drift_interpiso_max_cm:.2f} cm`{piso_info} | **`{self.drift_interpiso_relat}`** | `Hi/850` | **{conf_inter}** |")

        if not self.drift_interpiso_passou:
            linhas.append(f"\n> [!WARNING]\n> **Atenção aos Deslocamentos Interpavimento:** O deslocamento horizontal relativo no **Piso {self.drift_interpiso_piso_critico}** ({self.drift_interpiso_relat}) supera o limite de conforto e proteção das alvenarias ($H_i/850$) estabelecido pela NBR 6118. Recomenda-se enrijecer vigas e pilares nessa prumada.")

        if self.alertas_normativos:
            linhas.append("\n### 3. Notas e Alertas Oficiais Emitidos pelo TQS")
            for al in self.alertas_normativos:
                linhas.append(f"- ⚠️ {al}")

        return "\n".join(linhas)


class TQSStabilityAnalyzer:
    """
    Motor de extração e auditoria de parâmetros de estabilidade global (γz, α, drift)
    a partir dos relatórios do pórtico espacial do TQS V25.
    """

    def __init__(self, caminho_ou_nome_edificio: str, pasta_raiz_tqs: Optional[str] = None):
        leitor = TQSBuildingReader(caminho_ou_nome_edificio, pasta_raiz_tqs or r"C:\TQS")
        self.caminho_edificio = leitor.caminho_edificio
        self.nome_edificio = leitor.nome_edificio
        self.pasta_espacial = os.path.join(self.caminho_edificio, "ESPACIAL")

    def analisar(self) -> RelatorioEstabilidadeResultado:
        """Lê os relatórios em ESPACIAL e consolida os parâmetros de estabilidade e ELS."""
        p_poralf = os.path.join(self.pasta_espacial, "PORALF.LST")
        if not os.path.exists(p_poralf):
            p_poralf = os.path.join(self.pasta_espacial, "PORGAMZ.LST")

        if not os.path.exists(p_poralf):
            raise FileNotFoundError(
                f"Relatório de estabilidade (PORALF.LST / PORGAMZ.LST) não encontrado em {self.pasta_espacial}. "
                "Certifique-se de que o pórtico espacial foi calculado no TQS."
            )

        with open(p_poralf, "r", encoding="latin1", errors="replace") as f:
            conteudo = f.read()

        altura_m = 0.0
        cota_ini = 0.0
        cota_fim = 0.0
        mod_elas = 0.0

        # Altura e cotas
        m_alt = re.search(r"Altura do edif[íi]cio\s*:\s*H=\s*(\d+(?:\.\d+)?)\s*m", conteudo, re.IGNORECASE)
        if m_alt:
            altura_m = float(m_alt.group(1))

        m_cfim = re.search(r"Cota final\s*\.*\s*(-?\d+(?:\.\d+)?)", conteudo, re.IGNORECASE)
        if m_cfim:
            cota_fim = float(m_cfim.group(1))

        m_cini = re.search(r"Cota inicial\s*\.*\s*(-?\d+(?:\.\d+)?)", conteudo, re.IGNORECASE)
        if m_cini:
            cota_ini = float(m_cini.group(1))

        if altura_m == 0.0 and cota_fim > cota_ini:
            altura_m = cota_fim - cota_ini

        m_mod = re.search(r"M[óo]dulo de elasticidade\s*\(CONCR\)\s*\.*\s*(\d+(?:\.\d+)?)", conteudo, re.IGNORECASE)
        if m_mod:
            mod_elas = float(m_mod.group(1))

        casos_simples: List[CasoEstabilidade] = []
        combinacoes_elu: List[CasoEstabilidade] = []
        desloc_topo: List[DeslocamentoELS] = []
        desloc_inter: List[DeslocamentoELS] = []
        alertas: List[str] = []

        # 1. Tabela de Casos Simples de Vento (GamaZ)
        bloco_simples = re.search(
            r"Par[âa]metro de estabilidade \(GamaZ\) para os carregamentos simples de vento\s*={5,}\s*(.*?)(?=\n\s*\n\s*[A-Z]|\Z)",
            conteudo, re.DOTALL | re.IGNORECASE
        )
        if bloco_simples:
            for lin in bloco_simples.group(1).splitlines():
                tokens = lin.strip().split()
                if len(tokens) >= 9 and tokens[0].isdigit():
                    try:
                        casos_simples.append(CasoEstabilidade(
                            caso=int(tokens[0]),
                            ang=float(tokens[1].rstrip(".")),
                            c_tot=float(tokens[2]),
                            m2=float(tokens[3]),
                            c_hor=float(tokens[4]),
                            m1=float(tokens[5]),
                            gama_z=float(tokens[7]),
                            alfa=float(tokens[8]),
                            obs=" ".join(tokens[9:]) if len(tokens) > 9 else "",
                            tipo="SIMPLES"
                        ))
                    except ValueError:
                        continue

        # 2. Tabela de Combinações ELU (FAVt / RM2M1)
        bloco_elu = re.search(
            r"Par[âa]metro de estabilidade \((?:FAVt|RM2M1)\s*\) para combina[çc][õo]es de ELU.*?\s*={5,}\s*(.*?)(?=\n\s*\n\s*[A-Z]|\Z)",
            conteudo, re.DOTALL | re.IGNORECASE
        )
        if bloco_elu:
            for lin in bloco_elu.group(1).splitlines():
                tokens = lin.strip().split()
                if len(tokens) >= 9 and tokens[0].isdigit():
                    try:
                        fav_val = float(tokens[7])
                        combinacoes_elu.append(CasoEstabilidade(
                            caso=int(tokens[0]),
                            ang=float(tokens[1].rstrip(".")),
                            c_tot=float(tokens[2]),
                            m2=float(tokens[3]),
                            c_hor=float(tokens[4]),
                            m1=float(tokens[5]),
                            mult_h=float(tokens[6]),
                            fav_t=fav_val,
                            gama_z=None,
                            alfa=float(tokens[8]),
                            obs=" ".join(tokens[9:]) if len(tokens) > 9 else "",
                            tipo="COMBINAÇÃO_ELU"
                        ))
                    except ValueError:
                        continue

        # 3. Deslocamentos máximos de Topo (ELS)
        bloco_desl_topo = re.search(
            r"Deslocamentos m[áa]ximos\s*={5,}\s*(.*?)(?=\n\s*\n\s*Deslocamentos m[áa]ximos entre pisos|\Z)",
            conteudo, re.DOTALL | re.IGNORECASE
        )
        if bloco_desl_topo:
            for lin in bloco_desl_topo.group(1).splitlines():
                tokens = lin.strip().split()
                if len(tokens) >= 3 and tokens[0].isdigit():
                    t_rel = next((t for t in tokens if "H/" in t.upper()), None)
                    if t_rel:
                        try:
                            idx_r = tokens.index(t_rel)
                            caso = int(tokens[0])
                            dhc = float(tokens[idx_r - 1])
                            dh = float(tokens[1])
                            m_rel = re.search(r"H/(\d+)", t_rel, re.IGNORECASE)
                            den = float(m_rel.group(1)) if m_rel else 1700.0
                            obs = " ".join(tokens[idx_r + 1:])
                            desloc_topo.append(DeslocamentoELS(
                                caso=caso,
                                desl_h_cm=dh,
                                desl_hc_cm=dhc,
                                relat_denominador=den,
                                relat_texto=f"H/{int(den)}",
                                obs=obs,
                                limite_denominador=1700.0,
                                passou=den >= 1700.0
                            ))
                        except (ValueError, IndexError):
                            continue

        # 4. Deslocamentos máximos entre pisos (Interpiso / ELS)
        bloco_desl_inter = re.search(
            r"Deslocamentos m[áa]ximos entre pisos\s*={5,}\s*(.*?)(?=\n\s*\n\s*Observa[çc][õo]es|\Z)",
            conteudo, re.DOTALL | re.IGNORECASE
        )
        if bloco_desl_inter:
            for lin in bloco_desl_inter.group(1).splitlines():
                tokens = lin.strip().split()
                if len(tokens) >= 4 and tokens[0].isdigit() and tokens[1].isdigit():
                    t_rel = next((t for t in tokens if "HI/" in t.upper()), None)
                    if t_rel:
                        try:
                            idx_r = tokens.index(t_rel)
                            caso = int(tokens[0])
                            piso = int(tokens[1])
                            dhpc = float(tokens[idx_r - 1])
                            dhp = float(tokens[2])
                            m_rel = re.search(r"Hi/(\d+)", t_rel, re.IGNORECASE)
                            den = float(m_rel.group(1)) if m_rel else 850.0
                            obs = " ".join(tokens[idx_r + 1:])
                            desloc_inter.append(DeslocamentoELS(
                                caso=caso,
                                piso=piso,
                                desl_h_cm=dhp,
                                desl_hc_cm=dhpc,
                                relat_denominador=den,
                                relat_texto=f"Hi/{int(den)}",
                                obs=obs,
                                limite_denominador=850.0,
                                passou=den >= 850.0
                            ))
                        except (ValueError, IndexError):
                            continue

        # Alertas de observações
        if "Obs=\"C\"" in conteudo or 'Obs="C"' in conteudo:
            alertas.append("Os deslocamentos horizontais entre pisos são superiores aos limites admitidos pela NBR 6118 (Hi/850). Recomenda-se enrijecer a estrutura.")
        if "Obs=\"B\"" in conteudo or 'Obs="B"' in conteudo:
            alertas.append("O parâmetro Alfa e GamaZ indicam estrutura de nós móveis.")

        # Consolidação de métricas
        # γz (NBR 6118, 15.5.3) vem dos casos simples de vento; FAVt das combinações de ELU
        # é o fator de amplificação do TQS e é relatado à parte, sem entrar na classificação.
        # γz = 0.000 significa "não calculado" (ex.: Obs="G", vento < 30% do desaprumo).
        gz_simples = [c.gama_z for c in casos_simples if c.gama_z]
        favs = [c.fav_t for c in combinacoes_elu if c.fav_t is not None]
        if gz_simples:
            gz_max = max(gz_simples)
        else:
            gz_max = max(favs) if favs else 1.0
            if favs:
                alertas.append("O PORALF não traz γz calculado para os casos simples de vento: classificação feita pelo FAVt.")
        fav_max = max(favs) if favs else gz_max
        alfa_max = max([c.alfa for c in casos_simples + combinacoes_elu] or [0.0])

        classif = "NÓS FIXOS"
        if gz_max > 1.30:
            classif = "CRÍTICO - INSTABILIDADE EXCESSIVA"
        elif gz_max > 1.10:
            classif = "NÓS MÓVEIS"
        if fav_max > 1.30 and gz_max <= 1.30:
            alertas.append(f"FAVt máximo das combinações de ELU = {fav_max:.3f} (> 1,30), embora γz = {gz_max:.3f}.")

        # Drift topo
        d_topo_max = 0.0
        d_topo_relat = "H/1700"
        d_topo_passou = True
        if desloc_topo:
            crit_t = min(desloc_topo, key=lambda x: x.relat_denominador)
            d_topo_max = crit_t.desl_hc_cm
            d_topo_relat = crit_t.relat_texto
            d_topo_passou = crit_t.passou

        # Drift interpiso
        d_inter_max = 0.0
        d_inter_relat = "Hi/850"
        d_inter_piso = None
        d_inter_passou = True
        if desloc_inter:
            crit_i = min(desloc_inter, key=lambda x: x.relat_denominador)
            d_inter_max = crit_i.desl_hc_cm
            d_inter_relat = crit_i.relat_texto
            d_inter_piso = crit_i.piso
            d_inter_passou = crit_i.passou

        return RelatorioEstabilidadeResultado(
            edificio_nome=self.nome_edificio,
            caminho_edificio=self.caminho_edificio,
            altura_edificio_m=altura_m,
            cota_inicial_m=cota_ini,
            cota_final_m=cota_fim,
            modulo_elasticidade_tf_m2=mod_elas,
            casos_simples=casos_simples,
            combinacoes_elu=combinacoes_elu,
            deslocamentos_topo=desloc_topo,
            deslocamentos_interpiso=desloc_inter,
            gama_z_max=gz_max,
            fav_t_max=fav_max,
            alfa_max=alfa_max,
            classificacao_estrutura=classif,
            drift_topo_max_cm=d_topo_max,
            drift_topo_relat=d_topo_relat,
            drift_topo_passou=d_topo_passou,
            drift_interpiso_max_cm=d_inter_max,
            drift_interpiso_relat=d_inter_relat,
            drift_interpiso_piso_critico=d_inter_piso,
            drift_interpiso_passou=d_inter_passou,
            alertas_normativos=alertas,
        )
