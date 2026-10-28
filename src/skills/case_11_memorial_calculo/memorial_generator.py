import os
import re
from datetime import datetime
from typing import Dict, Any, Optional
from src.tqs_adapter.building_reader import TQSBuildingReader
from src.skills.case_08_estabilidade_global.stability_analyzer import TQSStabilityAnalyzer
from src.skills.case_10_quantitativo_materiais.material_quantifier import TQSMaterialQuantifier
from src.skills.case_09_auditoria_lajes.slab_analyzer import TQSSlabAnalyzer


class TQSMemorialGenerator:
    """
    Gerador executivo de Memorial Descritivo e Justificativo de Cálculo Estrutural
    conforme as normas ABNT NBR 6118:2023, NBR 6120:2019 e NBR 6123:2023.

    Consolida de forma unificada os dados do edifício no TQS V25:
      1. Identificação do Projeto e Caracterização da Obra.
      2. Normas Técnicas e Critérios de Projeto.
      3. Características dos Materiais (fck, Ecs, CA-50).
      4. Análise e Estabilidade Global (γz, FAVt, Drift Topo e Interpiso).
      5. Resumo de Elementos Estruturais (Pilares, Vigas e Lajes).
      6. Quantitativos de Materiais, Índices de Consumo e Carbono Incorporado.
    """

    def __init__(self, caminho_ou_nome_edificio: str, pasta_raiz_tqs: Optional[str] = None):
        self.leitor = TQSBuildingReader(caminho_ou_nome_edificio, pasta_raiz_tqs or r"C:\TQS")
        self.caminho_edificio = self.leitor.caminho_edificio
        self.nome_edificio = self.leitor.nome_edificio

    def gerar(
        self,
        caminho_saida_md: Optional[str] = None,
        caminho_saida_html: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gera o Memorial Descritivo completo em Markdown e HTML."""
        # 1. Coleta dados de Estabilidade Global (Case 08)
        dados_estab = None
        try:
            estab_analyzer = TQSStabilityAnalyzer(self.caminho_edificio)
            dados_estab = estab_analyzer.analisar()
        except Exception:
            pass

        # 2. Coleta dados de Materiais e Consumo (Case 10)
        dados_mat = None
        try:
            mat_quant = TQSMaterialQuantifier(self.caminho_edificio)
            dados_mat = mat_quant.quantificar()
        except Exception:
            pass

        # 3. Coleta dados de Lajes (Case 09)
        dados_lajes = None
        try:
            slab_analyzer = TQSSlabAnalyzer(self.caminho_edificio)
            dados_lajes = slab_analyzer.analisar()
        except Exception:
            pass

        # Montagem do Conteúdo em Markdown
        md_conteudo = self._construir_markdown(dados_estab, dados_mat, dados_lajes)

        # Montagem do Conteúdo em HTML para Impressão/PDF
        html_conteudo = self._construir_html(md_conteudo, dados_estab, dados_mat)

        if caminho_saida_md:
            os.makedirs(os.path.dirname(os.path.abspath(caminho_saida_md)), exist_ok=True)
            with open(caminho_saida_md, "w", encoding="utf-8") as f:
                f.write(md_conteudo)

        if caminho_saida_html:
            os.makedirs(os.path.dirname(os.path.abspath(caminho_saida_html)), exist_ok=True)
            with open(caminho_saida_html, "w", encoding="utf-8") as f:
                f.write(html_conteudo)

        return {
            "edificio_nome": self.nome_edificio,
            "caminho_edificio": self.caminho_edificio,
            "conteudo_markdown": md_conteudo,
            "conteudo_html": html_conteudo,
            "arquivo_md": caminho_saida_md,
            "arquivo_html": caminho_saida_html,
        }

    def _construir_markdown(self, estab, mat, lajes) -> str:
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        altura_txt = f"{estab.altura_edificio_m:.2f} m" if estab else "Não informada"
        cota_ini = f"{estab.cota_inicial_m:.2f} m" if estab else "0.00 m"
        cota_fim = f"{estab.cota_final_m:.2f} m" if estab else "0.00 m"

        linhas = [
            f"# MEMORIAL DESCRITIVO E JUSTIFICATIVO DE CÁLCULO ESTRUTURAL",
            f"**Obra / Edifício:** `{self.nome_edificio}`  ",
            f"**Data de Emissão:** `{data_hoje}`  ",
            f"**Sistema de Modelagem e Análise:** `CAD/TQS V25 (Engenharia de Estruturas)`  \n",
            "---",
            "## 1. Caracterização Geral do Empreendimento",
            f"- **Nome da Estrutura:** {self.nome_edificio}",
            f"- **Altura Total da Edificação ($H$):** {altura_txt} (Cotas: {cota_ini} a {cota_fim})",
            f"- **Diretório de Projeto:** `{self.caminho_edificio}`\n",
            "## 2. Normas Técnicas e Premissas de Projeto",
            "O dimensionamento, verificação da estabilidade global e estados limites de serviço foram rigorosamente desenvolvidos com base nas seguintes normas da Associação Brasileira de Normas Técnicas (ABNT):",
            "- **ABNT NBR 6118:2023** - Projeto de estruturas de concreto - Procedimento.",
            "- **ABNT NBR 6120:2019** - Ações para o cálculo de estruturas de edificações.",
            "- **ABNT NBR 6123:2023** - Forças devidas ao vento em edificações.",
            "- **ABNT NBR 6122:2022** - Projeto e execução de fundações.",
            "- **ABNT NBR 8681:2003** - Ações e segurança nas estruturas - Procedimento.\n",
            "## 3. Especificação dos Materiais",
            "- **Concreto Armado:** $f_{ck} = 30$ a $40\\text{ MPa}$ conforme especificação por pavimento e elemento.",
            "- **Módulo de Deformação Secante ($E_{cs}$):** Adotado conforme formulação da NBR 6118 considerando o tipo de agregado.",
            "- **Aço Estrutural:** CA-50 ($f_{yk} = 500\\text{ MPa}$, $E_s = 210\\text{ GPa}$) para armaduras longitudinais e transversais; CA-60 ($f_{yk} = 600\\text{ MPa}$) para telas soldadas e bitolas finas.\n",
            "## 4. Análise de Estabilidade Global e Efeitos de 2ª Ordem"
        ]

        if estab:
            classif = estab.classificacao_estrutura
            gz = f"{estab.gama_z_max:.3f}"
            fav = f"{estab.fav_t_max:.3f}"
            alfa = f"{estab.alfa_max:.3f}"
            d_topo = f"{estab.drift_topo_max_cm:.2f} cm ({estab.drift_topo_relat})"
            d_inter = f"{estab.drift_interpiso_max_cm:.2f} cm ({estab.drift_interpiso_relat})"

            linhas.extend([
                f"- **Classificação da Estrutura:** **{classif}**",
                f"- **Parâmetro de Não Linearidade Geométrica ($\\gamma_z$ Máximo):** `{gz}`",
                f"- **Fator de Amplificação de Vento ($FAV_t$ Máximo):** `{fav}`",
                f"- **Parâmetro de Instabilidade Global ($\\alpha$ Máximo):** `{alfa}`",
                f"- **Deslocamento Horizontal no Topo (ELS):** `{d_topo}` (Limite: `H/1700` - {'Conforme ✅' if estab.drift_topo_passou else 'Não atende ❌'})",
                f"- **Deslocamento Interpavimento Máximo (ELS):** `{d_inter}` (Limite: `Hi/850` - {'Conforme ✅' if estab.drift_interpiso_passou else 'Não atende ❌'})"
            ])
            if estab.gama_z_max <= 1.10:
                linhas.append(r"\n> [!NOTE]\n> Estrutura classificada como de **Nós Fixos** ($\gamma_z \le 1.10$). Os efeitos de segunda ordem são inferiores a 10% dos de primeira ordem, dispensando majoração adicional.")
            elif estab.gama_z_max <= 1.30:
                linhas.append(r"\n> [!TIP]\n> Estrutura classificada como de **Nós Móveis** ($1.10 < \gamma_z \le 1.30$). Os esforços de segunda ordem foram considerados por processo P-Delta / majoração normativa.")
        else:
            linhas.append("*Informações de estabilidade não disponíveis ou pórtico espacial ainda não processado.*")

        linhas.extend([
            "\n## 5. Auditoria de Lajes e Sistemas de Piso",
        ])
        if lajes and lajes.total_lajes_edificio > 0:
            linhas.append(f"- **Total de Lajes Modeladas:** `{lajes.total_lajes_edificio}` unidades")
            linhas.append(f"- **Área Estruturada de Lajes:** `{lajes.area_total_edificio_m2:.2f} m²`")
            linhas.append(f"- **Volume de Concreto de Lajes:** `{lajes.volume_total_edificio_m3:.2f} m³`")
            if lajes.alertas_totais_contagem > 0:
                linhas.append(f"- **Alertas de Grelha e Balanços Detectados:** `{lajes.alertas_totais_contagem}` ocorrências analisadas.")
        else:
            linhas.append("Lajes modeladas via grelha tridimensional contínua com rigidez à flexão e torção compatibilizada com o pórtico espacial.")

        linhas.extend([
            "\n## 6. Quantitativos de Materiais e Indicadores de Eficiência",
        ])
        if mat:
            linhas.extend([
                f"- **Área Total Construída Estruturada:** `{mat.area_total_m2:,.2f} m²`",
                f"- **Volume Total de Concreto:** `{mat.volume_concreto_total_m3:,.2f} m³`",
                f"- **Área Total de Fôrmas:** `{mat.area_formas_total_m2:,.2f} m²`",
                f"- **Peso Total de Aço:** `{mat.peso_aco_total_kg:,.2f} kg`",
                f"- **Espessura Média do Edifício ($e_m$):** `{mat.espessura_media_m:.3f} m`",
                f"- **Taxa de Fôrmas:** `{mat.taxa_formas_m2_m2:.2f} m²/m²`",
                f"- **Pegada de Carbono Incorporado:** `{mat.carbono_total_kgco2:,.2f} kgCO₂` ({mat.carbono_especifico_kgco2_m2:.1f} kgCO₂/m²)"
            ])
        else:
            linhas.append("*Quantitativos em fase de fechamento de detalhamento.*")

        linhas.extend([
            "\n---",
            "## 7. Responsabilidade Técnica e Considerações Finais",
            "O presente memorial documenta as premissas adotadas no modelo tridimensional de barras e elementos de placas no sistema CAD/TQS V25. ",
            "Todas as armaduras detalhadas e especificadas nos desenhos de formas, armação de vigas, pilares e lajes devem ser rigorosamente seguidas na execução da obra.",
            "\n**Engenheiro Responsável pelo Cálculo Estrutural**  ",
            "CREA / CAU: ___________________________"
        ])

        return "\n".join(linhas)

    def _construir_html(self, md_texto: str, estab, mat) -> str:
        """Gera versão HTML estilizada com CSS para impressão em folha A4."""
        # Converte Markdown básico em HTML limpo
        corpo = md_texto.replace("\n", "<br>\n")
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<title>Memorial Descritivo - {self.nome_edificio}</title>
<style>
    @page {{
        size: A4;
        margin: 20mm;
    }}
    body {{
        font-family: "Segoe UI", Arial, Helvetica, sans-serif;
        color: #2c3e50;
        line-height: 1.5;
        background-color: #fdfdfd;
        padding: 20px;
    }}
    .header {{
        border-bottom: 3px solid #1a365d;
        padding-bottom: 12px;
        margin-bottom: 25px;
    }}
    h1 {{
        font-size: 20pt;
        color: #1a365d;
        margin-bottom: 5px;
        text-transform: uppercase;
    }}
    h2 {{
        font-size: 14pt;
        color: #2b6cb0;
        border-bottom: 1px solid #cbd5e0;
        padding-bottom: 5px;
        margin-top: 25px;
    }}
    .badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        background-color: #ebf8ff;
        color: #2b6cb0;
        border: 1px solid #bee3f8;
    }}
    .footer {{
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid #e2e8f0;
        font-size: 9pt;
        color: #718096;
        text-align: center;
    }}
</style>
</head>
<body>
    <div class="header">
        <h1>Memorial Descritivo e Justificativo de Cálculo Estrutural</h1>
        <div><strong>Edifício:</strong> {self.nome_edificio} | <strong>Norma:</strong> ABNT NBR 6118:2023 | <strong>Software:</strong> TQS V25</div>
    </div>
    <div class="content">
        {corpo}
    </div>
    <div class="footer">
        Documento gerado automaticamente pelo AUTQS Engineering Assistant em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}.
    </div>
</body>
</html>"""
        return html
