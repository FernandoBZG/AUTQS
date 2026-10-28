import os
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.tqs_adapter.building_reader import TQSBuildingReader


@dataclass
class ElementoQuantitativo:
    """Quantitativos de uma categoria estrutural em um piso (Pilares, Vigas, Lajes, Fundações)."""
    tipo_elemento: str
    volume_concreto_m3: float = 0.0
    area_forma_m2: float = 0.0
    peso_aco_kg: float = 0.0
    fck_mpa: float = 0.0


@dataclass
class PisoQuantitativo:
    """Consolidação de materiais de um pavimento específico."""
    piso_nome: str
    numero_piso: int = 0
    area_estruturada_m2: float = 0.0
    volume_concreto_m3: float = 0.0
    area_forma_m2: float = 0.0
    peso_aco_kg: float = 0.0
    carbono_kgco2: float = 0.0
    elementos: Dict[str, ElementoQuantitativo] = field(default_factory=dict)

    def para_dict(self) -> Dict[str, Any]:
        return {
            "piso_nome": self.piso_nome,
            "numero_piso": self.numero_piso,
            "area_estruturada_m2": round(self.area_estruturada_m2, 2),
            "volume_concreto_m3": round(self.volume_concreto_m3, 2),
            "area_forma_m2": round(self.area_forma_m2, 2),
            "peso_aco_kg": round(self.peso_aco_kg, 2),
            "carbono_kgco2": round(self.carbono_kgco2, 2),
            "elementos": {
                k: {
                    "volume_concreto_m3": round(v.volume_concreto_m3, 2),
                    "area_forma_m2": round(v.area_forma_m2, 2),
                    "peso_aco_kg": round(v.peso_aco_kg, 2),
                    "fck_mpa": v.fck_mpa,
                }
                for k, v in self.elementos.items()
            }
        }


@dataclass
class EdificioMateriaisResultado:
    """Resultado global de levantamento de quantitativos, consumo e pegada de carbono."""
    edificio_nome: str
    caminho_edificio: str
    pisos: List[PisoQuantitativo] = field(default_factory=list)
    area_total_m2: float = 0.0
    volume_concreto_total_m3: float = 0.0
    area_formas_total_m2: float = 0.0
    peso_aco_total_kg: float = 0.0
    carbono_total_kgco2: float = 0.0
    espessura_media_m: float = 0.0
    taxa_formas_m2_m2: float = 0.0
    taxa_aco_kg_m2: float = 0.0
    taxa_aco_kg_m3: float = 0.0
    carbono_especifico_kgco2_m2: float = 0.0

    def para_dict(self) -> Dict[str, Any]:
        return {
            "edificio_nome": self.edificio_nome,
            "caminho_edificio": self.caminho_edificio,
            "totais": {
                "area_total_m2": round(self.area_total_m2, 2),
                "volume_concreto_total_m3": round(self.volume_concreto_total_m3, 2),
                "area_formas_total_m2": round(self.area_formas_total_m2, 2),
                "peso_aco_total_kg": round(self.peso_aco_total_kg, 2),
                "carbono_total_kgco2": round(self.carbono_total_kgco2, 2),
            },
            "indices_consumo": {
                "espessura_media_m": round(self.espessura_media_m, 3),
                "taxa_formas_m2_m2": round(self.taxa_formas_m2_m2, 2),
                "taxa_aco_kg_m2": round(self.taxa_aco_kg_m2, 2),
                "taxa_aco_kg_m3": round(self.taxa_aco_kg_m3, 2),
                "carbono_especifico_kgco2_m2": round(self.carbono_especifico_kgco2_m2, 2),
            },
            "pisos": [p.para_dict() for p in self.pisos]
        }

    def para_resumo_executivo(self) -> str:
        """Gera resumo executivo em Markdown com tabelas para engenharia e orçamento."""
        linhas = [
            f"# QUANTITATIVO GLOBAL E ÍNDICES DE CONSUMO: {self.edificio_nome.upper()}",
            f"**Área Estruturada Total:** `{self.area_total_m2:,.2f} m²`\n",
            "### 1. Resumo Consolidado de Materiais",
            f"- **Volume Total de Concreto:** `{self.volume_concreto_total_m3:,.2f} m³`",
            f"- **Área Total de Fôrmas:** `{self.area_formas_total_m2:,.2f} m²`",
            f"- **Consumo Total de Aço:** `{self.peso_aco_total_kg:,.2f} kg` ({self.peso_aco_total_kg/1000.0:,.2f} ton)",
            f"- **Emissões de Carbono Incorporado:** `{self.carbono_total_kgco2:,.2f} kgCO₂` ({self.carbono_total_kgco2/1000.0:,.2f} tonCO₂)\n",
            "### 2. Índices de Eficiência Estrutural e Consumo",
            "| Indicador de Consumo | Valor Obtido | Faixa de Referência Econômica | Diagnóstico |",
            "| :--- | :---: | :---: | :---: |"
        ]

        # Diagnóstico de Espessura Média
        diag_em = "Econômico" if self.espessura_media_m <= 0.22 else ("Médio" if self.espessura_media_m <= 0.28 else "Pesado / Lajes Espessas")
        linhas.append(f"| **Espessura Média ($e_m$)** | **`{self.espessura_media_m:.3f} m`** | `0.18 - 0.25 m` | {diag_em} |")

        # Taxa de Fôrmas
        diag_tf = "Excelente" if self.taxa_formas_m2_m2 <= 2.2 else ("Normal" if self.taxa_formas_m2_m2 <= 2.8 else "Alto Recorte")
        linhas.append(f"| **Taxa de Fôrmas** | **`{self.taxa_formas_m2_m2:.2f} m²/m²`** | `1.80 - 2.50 m²/m²` | {diag_tf} |")

        # Taxa de Aço (se houver aço detalhado)
        if self.peso_aco_total_kg > 0:
            diag_aco = "Otimizado" if self.taxa_aco_kg_m3 <= 95.0 else ("Médio" if self.taxa_aco_kg_m3 <= 115.0 else "Taxa Alta")
            linhas.append(f"| **Consumo de Aço / Vol.** | **`{self.taxa_aco_kg_m3:.1f} kg/m³`** | `80 - 110 kg/m³` | {diag_aco} |")
            linhas.append(f"| **Consumo de Aço / Área** | **`{self.taxa_aco_kg_m2:.1f} kg/m²`** | `18 - 25 kg/m²` | Referência |")

        linhas.append(f"| **Pegada de Carbono** | **`{self.carbono_especifico_kgco2_m2:.1f} kgCO₂/m²`** | `120 - 200 kgCO₂/m²` | Sustentabilidade |")

        linhas.append("\n### 3. Distribuição de Materiais por Pavimento")
        linhas.append("| Pavimento | Área (m²) | Concreto (m³) | Fôrmas (m²) | Aço (kg) | Carbono (kgCO₂) |")
        linhas.append("| :--- | :---: | :---: | :---: | :---: | :---: |")

        for p in self.pisos:
            linhas.append(
                f"| **{p.piso_nome}** | {p.area_estruturada_m2:.1f} | {p.volume_concreto_m3:.2f} | "
                f"{p.area_forma_m2:.1f} | {p.peso_aco_kg:.1f} | {p.carbono_kgco2:.0f} |"
            )

        return "\n".join(linhas)


class TQSMaterialQuantifier:
    """
    Extrator de quantitativos oficiais do TQS V25 a partir dos relatórios
    RESEST1..8.TXT localizados na pasta ESPACIAL do edifício.
    """

    def __init__(self, caminho_ou_nome_edificio: str, pasta_raiz_tqs: Optional[str] = None):
        leitor = TQSBuildingReader(caminho_ou_nome_edificio, pasta_raiz_tqs or r"C:\TQS")
        self.caminho_edificio = leitor.caminho_edificio
        self.nome_edificio = leitor.nome_edificio
        self.pasta_espacial = os.path.join(self.caminho_edificio, "ESPACIAL")

    def quantificar(self) -> EdificioMateriaisResultado:
        """Processa RESEST2.TXT, RESEST3.TXT, RESEST4.TXT e RESEST8.TXT."""
        res = EdificioMateriaisResultado(
            edificio_nome=self.nome_edificio,
            caminho_edificio=self.caminho_edificio
        )

        p_resest3 = os.path.join(self.pasta_espacial, "RESEST3.TXT")
        p_resest2 = os.path.join(self.pasta_espacial, "RESEST2.TXT")
        p_resest4 = os.path.join(self.pasta_espacial, "RESEST4.TXT")
        p_resest8 = os.path.join(self.pasta_espacial, "RESEST8.TXT")

        if not os.path.exists(p_resest3) and not os.path.exists(p_resest2):
            raise FileNotFoundError(
                f"Relatórios de resumo estrutural (RESEST3.TXT / RESEST2.TXT) não encontrados em {self.pasta_espacial}."
            )

        # 1. Leitura de Carbono por Piso (RESEST8.TXT)
        carbono_por_piso: Dict[str, float] = {}
        if os.path.exists(p_resest8):
            try:
                with open(p_resest8, "r", encoding="latin1", errors="replace") as f:
                    for line in f:
                        parts = [p.strip() for p in line.split("\t") if p.strip()]
                        if len(parts) >= 6 and parts[0].startswith("Piso"):
                            p_nome = parts[0]
                            try:
                                val_c = float(parts[5].replace(",", "."))
                                carbono_por_piso[p_nome] = val_c
                            except ValueError:
                                pass
                        elif len(parts) >= 2 and parts[0].lower().startswith("total geral"):
                            try:
                                res.carbono_total_kgco2 = float(parts[1].replace(",", "."))
                            except ValueError:
                                pass
            except Exception:
                pass

        # 2. Leitura de RESEST3.TXT (Resumo de materiais por piso)
        # Formato: Bitola \t ... \t Aço \t Concreto \t Forma \t Área
        pisos_map: Dict[str, PisoQuantitativo] = {}
        if os.path.exists(p_resest3):
            with open(p_resest3, "r", encoding="latin1", errors="replace") as f:
                for line in f:
                    parts = [p.strip() for p in line.split("\t")]
                    if not parts or not parts[0]:
                        continue
                    p_label = parts[0]
                    if p_label.startswith("Piso"):
                        # Extrai números das últimas 4 colunas não vazias
                        num_vals = []
                        for p in reversed(parts[1:]):
                            if p:
                                try:
                                    num_vals.append(float(p.replace(",", ".")))
                                except ValueError:
                                    pass
                        # Inverte para ordem: [Aço (kgf), Concreto (m3), Forma (m2), Área (m2)]
                        num_vals.reverse()
                        
                        area_m2 = num_vals[-1] if len(num_vals) >= 1 else 0.0
                        forma_m2 = num_vals[-2] if len(num_vals) >= 2 else 0.0
                        conc_m3 = num_vals[-3] if len(num_vals) >= 3 else 0.0
                        aco_kg = num_vals[-4] if len(num_vals) >= 4 else 0.0

                        # Trata caso de o aço estar vazio
                        if len(num_vals) == 3:
                            area_m2 = num_vals[2]
                            forma_m2 = num_vals[1]
                            conc_m3 = num_vals[0]
                            aco_kg = 0.0

                        carb = carbono_por_piso.get(p_label, 0.0)

                        m_num = re.search(r"Piso\s*(\d+)\s*:\s*(.*)", p_label)
                        n_piso = int(m_num.group(1)) if m_num else len(pisos_map)
                        nome_clean = m_num.group(2).strip() if m_num else p_label

                        piso_obj = PisoQuantitativo(
                            piso_nome=nome_clean,
                            numero_piso=n_piso,
                            area_estruturada_m2=area_m2,
                            volume_concreto_m3=conc_m3,
                            area_forma_m2=forma_m2,
                            peso_aco_kg=aco_kg,
                            carbono_kgco2=carb,
                        )
                        pisos_map[p_label] = piso_obj
                        res.pisos.append(piso_obj)
                        res.area_total_m2 += area_m2
                        res.volume_concreto_total_m3 += conc_m3
                        res.area_formas_total_m2 += forma_m2
                        res.peso_aco_total_kg += aco_kg
                        if res.carbono_total_kgco2 == 0.0:
                            res.carbono_total_kgco2 += carb

        # 3. Leitura de RESEST4.TXT (Índices calculados pelo TQS)
        if os.path.exists(p_resest4):
            try:
                with open(p_resest4, "r", encoding="latin1", errors="replace") as f:
                    for line in f:
                        parts = [p.strip() for p in line.split("\t") if p.strip()]
                        if len(parts) >= 2:
                            chave = parts[0].lower()
                            val_str = parts[1].replace(",", ".")
                            try:
                                val_f = float(val_str)
                                if "espessura" in chave:
                                    res.espessura_media_m = val_f
                                elif "taxa de formas" in chave:
                                    res.taxa_formas_m2_m2 = val_f
                                elif "taxa de aço (kgf/m2)" in chave or "taxa de ao (kgf/m2)" in chave:
                                    res.taxa_aco_kg_m2 = val_f
                                elif "taxa de aço (kgf/m3)" in chave or "taxa de ao (kgf/m3)" in chave:
                                    res.taxa_aco_kg_m3 = val_f
                            except ValueError:
                                pass
            except Exception:
                pass

        # Cálculo de índices caso não estejam presentes em RESEST4
        if res.area_total_m2 > 0:
            if res.espessura_media_m == 0.0:
                res.espessura_media_m = res.volume_concreto_total_m3 / res.area_total_m2
            if res.taxa_formas_m2_m2 == 0.0:
                res.taxa_formas_m2_m2 = res.area_formas_total_m2 / res.area_total_m2
            if res.taxa_aco_kg_m2 == 0.0 and res.peso_aco_total_kg > 0:
                res.taxa_aco_kg_m2 = res.peso_aco_total_kg / res.area_total_m2
            if res.carbono_especifico_kgco2_m2 == 0.0 and res.carbono_total_kgco2 > 0:
                res.carbono_especifico_kgco2_m2 = res.carbono_total_kgco2 / res.area_total_m2

        if res.volume_concreto_total_m3 > 0 and res.peso_aco_total_kg > 0 and res.taxa_aco_kg_m3 == 0.0:
            res.taxa_aco_kg_m3 = res.peso_aco_total_kg / res.volume_concreto_total_m3

        return res
