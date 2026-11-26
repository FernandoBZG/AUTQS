import os
import re
import math
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    import ezdxf
    from ezdxf import colors
except ImportError:
    ezdxf = None
    colors = None

try:
    from TQS import TQSDwg
except ImportError:
    TQSDwg = None

from src.tqs_adapter.building_reader import TQSBuildingReader
from src.tqs_adapter.model_editor import TQSModelEditor, normalizar_texto


def parse_dim_pilar(txt: str) -> Optional[Tuple[float, float]]:
    """Extrai dimensões (b, h) em cm de um texto de seção de pilar (ex: '20x50', '20/50')."""
    if not txt:
        return None
    m = re.match(r"^(\d+(?:\.\d+)?)\s*[xX/]\s*(\d+(?:\.\d+)?)$", txt.strip())
    if m:
        b, h = float(m.group(1)), float(m.group(2))
        return (min(b, h), max(b, h))
    return None


def parse_dim_viga(txt: str) -> Optional[Tuple[float, float]]:
    """Extrai dimensões (b, h) em cm de um texto de seção de viga (ex: '19/50', '14x30')."""
    if not txt:
        return None
    m = re.match(r"^(\d+(?:\.\d+)?)\s*[/xX]\s*(\d+(?:\.\d+)?)$", txt.strip())
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


@dataclass
class DiferencaElemento:
    """Registra uma alteração específica em um elemento estrutural entre geometrias/formas."""
    tipo: str  # 'PILAR', 'VIGA', 'LAJE'
    nome: str
    status: str  # 'NOVO', 'REMOVIDO', 'ALTERADO_SECAO', 'ALTERADO_POSICAO', 'ALTERADO_AMBOS', 'INALTERADO'
    valor_anterior: str
    valor_atual: str
    delta: str
    impacto_estrutural: str
    dados_anteriores: Optional[Dict[str, Any]] = None
    dados_atuais: Optional[Dict[str, Any]] = None


@dataclass
class RelatorioComparacaoResultado:
    """Resultado estruturado da comparação entre duas geometrias / plantas de formas."""
    origem_base: str
    origem_comparada: str
    pavimento_base: str
    pavimento_comparado: str
    caminho_diff_dxf: Optional[str] = None
    itens: List[DiferencaElemento] = field(default_factory=list)

    @property
    def total_novos(self) -> int:
        return sum(1 for it in self.itens if it.status == "NOVO")

    @property
    def total_removidos(self) -> int:
        return sum(1 for it in self.itens if it.status == "REMOVIDO")

    @property
    def total_alterados(self) -> int:
        return sum(1 for it in self.itens if it.status.startswith("ALTERADO"))

    @property
    def total_inalterados(self) -> int:
        return sum(1 for it in self.itens if it.status == "INALTERADO")

    @property
    def tem_mudancas(self) -> bool:
        return (self.total_novos + self.total_removidos + self.total_alterados) > 0

    def para_dict(self) -> Dict[str, Any]:
        return {
            "origem_base": self.origem_base,
            "origem_comparada": self.origem_comparada,
            "pavimento_base": self.pavimento_base,
            "pavimento_comparado": self.pavimento_comparado,
            "caminho_diff_dxf": self.caminho_diff_dxf,
            "metricas": {
                "total_elementos": len(self.itens),
                "novos": self.total_novos,
                "removidos": self.total_removidos,
                "alterados": self.total_alterados,
                "inalterados": self.total_inalterados,
            },
            "alteracoes": [asdict(it) for it in self.itens if it.status != "INALTERADO"],
        }

    def para_resumo_executivo(self) -> str:
        """Gera resumo formatado em Markdown para chat e relatórios."""
        linhas = [
            "### Relatório de Comparação de Geometria e Plantas de Formas",
            f"- **Base (Anterior / Referência):** `{self.origem_base}` — Pavimento `{self.pavimento_base}`",
            f"- **Atual (Comparada / Modificada):** `{self.origem_comparada}` — Pavimento `{self.pavimento_comparado}`",
            f"- **Resumo de Alterações:** "
            f"**{self.total_novos}** novos, "
            f"**{self.total_removidos}** removidos, "
            f"**{self.total_alterados}** alterados e "
            f"**{self.total_inalterados}** inalterados.",
        ]

        if not self.tem_mudancas:
            linhas.append("\n✅ **Nenhuma divergência geométrica detectada.** As plantas são 100% idênticas!")
            return "\n".join(linhas)

        # Agrupa alterações por tipo
        pilares_alt = [it for it in self.itens if it.tipo == "PILAR" and it.status != "INALTERADO"]
        vigas_alt = [it for it in self.itens if it.tipo == "VIGA" and it.status != "INALTERADO"]
        lajes_alt = [it for it in self.itens if it.tipo == "LAJE" and it.status != "INALTERADO"]

        if pilares_alt:
            linhas.append("\n#### 🏛️ Pilares Alterados / Novos / Removidos:")
            linhas.append("| Pilar | Status | Valor Anterior | Valor Atual | Diferença (Δ) | Impacto Estrutural |")
            linhas.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for it in pilares_alt:
                linhas.append(f"| **{it.nome}** | `{it.status}` | {it.valor_anterior} | {it.valor_atual} | {it.delta} | {it.impacto_estrutural} |")

        if vigas_alt:
            linhas.append("\n#### 🧱 Vigas Alteradas / Novas / Removidas:")
            linhas.append("| Viga | Status | Valor Anterior | Valor Atual | Diferença (Δ) | Impacto Estrutural |")
            linhas.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for it in vigas_alt:
                linhas.append(f"| **{it.nome}** | `{it.status}` | {it.valor_anterior} | {it.valor_atual} | {it.delta} | {it.impacto_estrutural} |")

        if lajes_alt:
            linhas.append("\n#### 🔲 Lajes Alteradas / Novas / Removidas:")
            linhas.append("| Laje | Status | Valor Anterior | Valor Atual | Diferença (Δ) | Impacto Estrutural |")
            linhas.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for it in lajes_alt:
                linhas.append(f"| **{it.nome}** | `{it.status}` | {it.valor_anterior} | {it.valor_atual} | {it.delta} | {it.impacto_estrutural} |")

        if self.caminho_diff_dxf and os.path.exists(self.caminho_diff_dxf):
            linhas.append(f"\n🎨 **Desenho de Sobreposição Gráfica (Diff DXF) Gerado:**")
            linhas.append(f"👉 `{self.caminho_diff_dxf}`")
            linhas.append("*(Abra diretamente no TQS ou AutoCAD: 🟢 Verde=Novo, 🔴 Vermelho=Removido, 🔵 Ciano=Alterado, ⚪ Cinza=Inalterado)*")

        return "\n".join(linhas)

    def para_tabela_terminal(self) -> str:
        """Gera exibição textual formatada para terminal."""
        div = "=" * 80
        subdiv = "-" * 80
        linhas = [
            "\n" + div,
            "      AUDITORIA DE DIFERENÇAS: GEOMETRIA vs PLANTA DE FORMAS TQS",
            div,
            f"Base:       {self.origem_base} ({self.pavimento_base})",
            f"Comparada:  {self.origem_comparada} ({self.pavimento_comparado})",
            f"Métricas:   {self.total_novos} Novos | {self.total_removidos} Removidos | {self.total_alterados} Alterados | {self.total_inalterados} Iguais",
            subdiv,
        ]

        mudancas = [it for it in self.itens if it.status != "INALTERADO"]
        if not mudancas:
            linhas.append("[OK] Nenhuma alteração detectada. Geometrias perfeitamente coincidentes.")
        else:
            linhas.append(f"{'Tipo':<7} | {'Elemento':<8} | {'Status':<16} | {'Diferença (Δ)':<24} | {'Impacto':<16}")
            linhas.append(subdiv)
            for it in mudancas:
                linhas.append(f"{it.tipo:<7} | {it.nome:<8} | {it.status:<16} | {it.delta[:24]:<24} | {it.impacto_estrutural[:16]}")

        if self.caminho_diff_dxf:
            linhas.append(subdiv)
            linhas.append(f"Prancha de Sobreposição: {self.caminho_diff_dxf}")
        linhas.append(div + "\n")
        return "\n".join(linhas)


class TQSGeometryComparator:
    """
    Motor inteligente de comparação e auditoria geométrica para TQS V25.
    Compara:
      1. Arquivos DWG diretos de arquitetura (Geo_*.DWG) vs Plantas de Formas (FOR*.DWG).
      2. Dois edifícios diferentes no Modelador Estrutural (ex: Revisão R01 vs R00).
      3. Dois pavimentos diferentes no mesmo edifício (ex: Tipo A vs Tipo B).
    Identifica com precisão milimétrica desvios de centro de gravidade (X, Y),
    mudanças de seções (b, h), espessuras de lajes, rebaixos e emite relatório
    analítico acompanhado de desenho DXF de sobreposição com código de cores.
    """

    TOLERANCIA_POSICAO_METROS = 0.005  # 5 mm
    TOLERANCIA_DIMENSAO_CM = 0.5       # 5 mm

    def __init__(self, pasta_raiz_tqs: Optional[str] = None):
        self.pasta_raiz_tqs = pasta_raiz_tqs or r"C:\TQS"

    # =========================================================================
    # EXTRAÇÃO DIRETA DE ARQUIVOS .DWG (NATIVO TQS)
    # =========================================================================

    def extrair_elementos_dwg(
        self,
        caminho_dwg: Union[str, Path],
        bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Dict[str, Any]:
        """
        Extrai elementos estruturais (pilares, vigas, lajes) diretamente de um arquivo .DWG do TQS.
        Calcula dinamicamente a caixa delimitadora da planta para ignorar carimbos, detalhes e cortes.
        """
        caminho = Path(caminho_dwg)
        if not caminho.exists() or TQSDwg is None:
            return {"pilares": {}, "vigas": {}, "lajes": {}}

        dwg = TQSDwg.Dwg(pedmv=0)
        if dwg.file.Open(str(caminho)) != 0:
            return {"pilares": {}, "vigas": {}, "lajes": {}}

        it = dwg.iterator
        it.Begin()
        todos_textos = []

        while True:
            pos = it.GetElementReadPosition()
            if not pos:
                break
            if it.elementName == "Texto":
                lvl = it.level
                t = it.text.strip()
                todos_textos.append((lvl, t, it.x1, it.y1))
            if not it.Next():
                break
        dwg.file.Close()

        # 1. Determina a região útil da planta (bounding box dos elementos reais)
        if bounds:
            min_x, max_x, min_y, max_y = bounds
        else:
            xs_estruturais = []
            ys_estruturais = []
            for lvl, t, x, y in todos_textos:
                if lvl in [2, 8, 9, 10]:
                    if re.match(r"^(P\d{2,}|PP\d+|PL\d+|V\d{2,}|L\d{2,})", t) and t not in ["P1", "V1", "L1"]:
                        xs_estruturais.append(x)
                        ys_estruturais.append(y)

            if xs_estruturais and ys_estruturais:
                min_x = min(xs_estruturais) - 200.0
                max_x = max(xs_estruturais) + 200.0
                min_y = min(ys_estruturais) - 200.0
                max_y = max(ys_estruturais) + 200.0
            else:
                min_x, max_x = -1e9, 1e9
                min_y, max_y = -1e9, 1e9

        textos = [
            (lvl, t, x, y) for lvl, t, x, y in todos_textos
            if min_x <= x <= max_x and min_y <= y <= max_y
        ]

        # 2. Extrai Pilares
        pilares = {}
        pils_nomes = [t for t in textos if t[0] in [2, 9] and re.match(r"^(P\d{2,}|PP\d+|PL\d+)", t[1]) and t[1] != "P1"]
        pils_secoes = [t for t in textos if t[0] in [12] and parse_dim_pilar(t[1])]

        for p in pils_nomes:
            nome = p[1]
            px, py = p[2], p[3]
            melhor_sec = ""
            menor_d = 1e9
            for s in pils_secoes:
                d = ((s[2] - px)**2 + (s[3] - py)**2)**0.5
                if d < menor_d and d < 120.0:
                    menor_d = d
                    melhor_sec = s[1]
            if nome not in pilares or (not pilares[nome]["secao"] and melhor_sec):
                pilares[nome] = {"nome": nome, "secao": melhor_sec, "x": px / 100.0, "y": py / 100.0}

        # 3. Extrai Vigas
        vigas = {}
        vigs_nomes = [t for t in textos if t[0] in [8] and re.match(r"^V\d{2,}", t[1]) and t[1] != "V1"]
        vigs_secoes = [t for t in textos if t[0] in [11] and parse_dim_viga(t[1])]

        for v in vigs_nomes:
            nome = v[1]
            vx, vy = v[2], v[3]
            melhor_sec = ""
            menor_d = 1e9
            for s in vigs_secoes:
                d = ((s[2] - vx)**2 + (s[3] - vy)**2)**0.5
                if d < menor_d and d < 120.0:
                    menor_d = d
                    melhor_sec = s[1]
            if nome not in vigas or (not vigas[nome]["secao"] and melhor_sec):
                vigas[nome] = {"nome": nome, "secao": melhor_sec, "x": vx / 100.0, "y": vy / 100.0}

        # 4. Extrai Lajes
        lajes = {}
        lajs_nomes = [t for t in textos if t[0] in [10] and re.match(r"^L\d+", t[1]) and t[1] != "L1"]
        lajs_esp = [t for t in textos if t[0] in [13]]
        for l in lajs_nomes:
            nome = l[1]
            lx, ly = l[2], l[3]
            melhor_esp = ""
            menor_d = 1e9
            for e in lajs_esp:
                d = ((e[2] - lx)**2 + (e[3] - ly)**2)**0.5
                if d < menor_d and d < 200.0:
                    menor_d = d
                    melhor_esp = e[1]
            if nome not in lajes:
                lajes[nome] = {"nome": nome, "esp": melhor_esp, "x": lx / 100.0, "y": ly / 100.0}

        return {"pilares": pilares, "vigas": vigas, "lajes": lajes, "bounds": (min_x, max_x, min_y, max_y)}

    def comparar_arquivos_dwg(
        self,
        caminhos_geo: Union[str, Path, List[Union[str, Path]]],
        caminho_for: Union[str, Path],
        origem_base: str = "Geometria Arquitetônica",
        origem_comparada: str = "Planta de Formas TQS",
        pavimento: str = "",
        gerar_desenho_diff: bool = True,
        caminho_saida_diff: Optional[str] = None,
    ) -> RelatorioComparacaoResultado:
        """
        Compara um ou mais arquivos de geometria arquitetônica (Geo_*.DWG, incluindo blocos combinados BL1 + BL2)
        com a planta de formas do TQS (FOR*.DWG).
        """
        if not isinstance(caminhos_geo, list):
            caminhos_geo = [caminhos_geo]

        # 1. Extração da Geometria (acumula se houver mais de um bloco)
        d_geo_total = {"pilares": {}, "vigas": {}, "lajes": {}}
        nomes_geos = []
        bounds_comb = [1e9, -1e9, 1e9, -1e9]

        for cg in caminhos_geo:
            p_cg = Path(cg)
            if p_cg.exists():
                nomes_geos.append(p_cg.name)
                d_g = self.extrair_elementos_dwg(p_cg)
                d_geo_total["pilares"].update(d_g.get("pilares", {}))
                d_geo_total["vigas"].update(d_g.get("vigas", {}))
                d_geo_total["lajes"].update(d_g.get("lajes", {}))
                gb = d_g.get("bounds")
                if gb and gb[0] != -1e9:
                    bounds_comb[0] = min(bounds_comb[0], gb[0])
                    bounds_comb[1] = max(bounds_comb[1], gb[1])
                    bounds_comb[2] = min(bounds_comb[2], gb[2])
                    bounds_comb[3] = max(bounds_comb[3], gb[3])

        # 2. Extração da Forma TQS
        path_for = Path(caminho_for)
        b_for = tuple(bounds_comb) if bounds_comb[0] != 1e9 else None
        d_for_total = self.extrair_elementos_dwg(path_for, bounds=b_for)

        itens_diferenca: List[DiferencaElemento] = []

        # 3. Comparação de Pilares
        p_geo = d_geo_total.get("pilares", {})
        p_for = d_for_total.get("pilares", {})
        todos_pilares = sorted(set(list(p_geo.keys()) + list(p_for.keys())))

        for p in todos_pilares:
            in_g = p in p_geo
            in_f = p in p_for

            if in_f and not in_g:
                pf = p_for[p]
                itens_diferenca.append(DiferencaElemento(
                    tipo="PILAR",
                    nome=p,
                    status="NOVO",
                    valor_anterior="--- (Inexistente na arquitetura)",
                    valor_atual=f"Seção {pf['secao']} @ ({pf['x']:.2f}, {pf['y']:.2f})m" if pf['secao'] else f"Forma @ ({pf['x']:.2f}, {pf['y']:.2f})m",
                    delta="Inclusão de pilar na forma estrutural",
                    impacto_estrutural="Importante: Novo elemento de transmissão de carga.",
                    dados_anteriores=None,
                    dados_atuais=pf
                ))
            elif in_g and not in_f:
                pg = p_geo[p]
                itens_diferenca.append(DiferencaElemento(
                    tipo="PILAR",
                    nome=p,
                    status="REMOVIDO",
                    valor_anterior=f"Seção {pg['secao']} @ ({pg['x']:.2f}, {pg['y']:.2f})m" if pg['secao'] else "Geometria arquitetônica",
                    valor_atual="--- (Excluído da forma)",
                    delta="Pilar previsto na arquitetura e ausente na forma",
                    impacto_estrutural="Crítico: Redistribuição de cargas na estrutura.",
                    dados_anteriores=pg,
                    dados_atuais=None
                ))
            else:
                pg = p_geo[p]
                pf = p_for[p]
                sg = pg.get("secao", "")
                sf = pf.get("secao", "")
                dim_g = parse_dim_pilar(sg)
                dim_f = parse_dim_pilar(sf)

                if dim_g and dim_f and dim_g != dim_f:
                    itens_diferenca.append(DiferencaElemento(
                        tipo="PILAR",
                        nome=p,
                        status="ALTERADO_SECAO",
                        valor_anterior=sg,
                        valor_atual=sf,
                        delta=f"Seção alterada: {sg} -> {sf}",
                        impacto_estrutural="Atenção: Variação de rigidez e armadura.",
                        dados_anteriores=pg,
                        dados_atuais=pf
                    ))
                else:
                    itens_diferenca.append(DiferencaElemento(
                        tipo="PILAR",
                        nome=p,
                        status="INALTERADO",
                        valor_anterior=sg or "Definido",
                        valor_atual=sf or "Definido",
                        delta="0.0 cm",
                        impacto_estrutural="Sem impacto.",
                        dados_anteriores=pg,
                        dados_atuais=pf
                    ))

        # 4. Comparação de Vigas
        v_geo = d_geo_total.get("vigas", {})
        v_for = d_for_total.get("vigas", {})
        todas_vigas = sorted(set(list(v_geo.keys()) + list(v_for.keys())))

        for v in todas_vigas:
            in_g = v in v_geo
            in_f = v in v_for

            if in_f and not in_g:
                vf = v_for[v]
                itens_diferenca.append(DiferencaElemento(
                    tipo="VIGA",
                    nome=v,
                    status="NOVO",
                    valor_anterior="---",
                    valor_atual=f"Seção {vf['secao']}" if vf['secao'] else "Inserida na forma",
                    delta="Inclusão de viga na forma",
                    impacto_estrutural="Importante: Novo suporte estrutural.",
                    dados_anteriores=None,
                    dados_atuais=vf
                ))
            elif in_g and not in_f:
                vg = v_geo[v]
                itens_diferenca.append(DiferencaElemento(
                    tipo="VIGA",
                    nome=v,
                    status="REMOVIDO",
                    valor_anterior=f"Seção {vg['secao']}" if vg['secao'] else "Prevista na geometria",
                    valor_atual="---",
                    delta="Exclusão de viga",
                    impacto_estrutural="Crítico: Remoção de apoio de laje.",
                    dados_anteriores=vg,
                    dados_atuais=None
                ))
            else:
                vg = v_geo[v]
                vf = v_for[v]
                sg = vg.get("secao", "")
                sf = vf.get("secao", "")
                dim_g = parse_dim_viga(sg)
                dim_f = parse_dim_viga(sf)

                if dim_g and dim_f and dim_g != dim_f:
                    itens_diferenca.append(DiferencaElemento(
                        tipo="VIGA",
                        nome=v,
                        status="ALTERADO_SECAO",
                        valor_anterior=sg,
                        valor_atual=sf,
                        delta=f"Seção alterada: {sg} -> {sf}",
                        impacto_estrutural="Atenção: Altera inércia à flexão e taxa de armadura.",
                        dados_anteriores=vg,
                        dados_atuais=vf
                    ))
                else:
                    itens_diferenca.append(DiferencaElemento(
                        tipo="VIGA",
                        nome=v,
                        status="INALTERADO",
                        valor_anterior=sg or "Definido",
                        valor_atual=sf or "Definido",
                        delta="0.0 cm",
                        impacto_estrutural="Sem impacto.",
                        dados_anteriores=vg,
                        dados_atuais=vf
                    ))

        # 5. Comparação de Lajes
        l_geo = d_geo_total.get("lajes", {})
        l_for = d_for_total.get("lajes", {})
        todas_lajes = sorted(set(list(l_geo.keys()) + list(l_for.keys())))

        for l in todas_lajes:
            in_g = l in l_geo
            in_f = l in l_for

            if in_f and not in_g:
                lf = l_for[l]
                itens_diferenca.append(DiferencaElemento(
                    tipo="LAJE",
                    nome=l,
                    status="NOVO",
                    valor_anterior="---",
                    valor_atual=f"Espessura {lf['esp']}" if lf['esp'] else "Inserida na forma",
                    delta="Inclusão de laje",
                    impacto_estrutural="Importante: Nova carga sobre vigas de contorno.",
                    dados_anteriores=None,
                    dados_atuais=lf
                ))
            elif in_g and not in_f:
                lg = l_geo[l]
                itens_diferenca.append(DiferencaElemento(
                    tipo="LAJE",
                    nome=l,
                    status="REMOVIDO",
                    valor_anterior=f"Espessura {lg['esp']}" if lg['esp'] else "Prevista na geometria",
                    valor_atual="---",
                    delta="Exclusão de laje (abertura/vazio)",
                    impacto_estrutural="Crítico: Alteração de contorno de laje.",
                    dados_anteriores=lg,
                    dados_atuais=None
                ))
            else:
                lg = l_geo[l]
                lf = l_for[l]
                eg = lg.get("esp", "")
                ef = lf.get("esp", "")

                if eg and ef and eg != ef:
                    itens_diferenca.append(DiferencaElemento(
                        tipo="LAJE",
                        nome=l,
                        status="ALTERADO_ESPESSURA",
                        valor_anterior=eg,
                        valor_atual=ef,
                        delta=f"Espessura alterada: {eg} -> {ef}",
                        impacto_estrutural="Atenção: Altera peso próprio e rigidez da grelha.",
                        dados_anteriores=lg,
                        dados_atuais=lf
                    ))
                else:
                    itens_diferenca.append(DiferencaElemento(
                        tipo="LAJE",
                        nome=l,
                        status="INALTERADO",
                        valor_anterior=eg or "Definido",
                        valor_atual=ef or "Definido",
                        delta="0.0 cm",
                        impacto_estrutural="Sem impacto.",
                        dados_anteriores=lg,
                        dados_atuais=lf
                    ))

        # 6. Emissão do DXF de Sobreposição Gráfica
        caminho_dxf = None
        if gerar_desenho_diff:
            caminho_dxf = self._gerar_desenho_sobreposicao_dwg(
                caminho_for=path_for,
                itens=itens_diferenca,
                pavimento_nome=pavimento or path_for.parent.name,
                caminho_saida=caminho_saida_diff
            )

        origem_g_str = ", ".join(nomes_geos) if nomes_geos else origem_base
        return RelatorioComparacaoResultado(
            origem_base=origem_g_str,
            origem_comparada=path_for.name,
            pavimento_base=pavimento or path_for.parent.name,
            pavimento_comparado=pavimento or path_for.parent.name,
            caminho_diff_dxf=caminho_dxf,
            itens=itens_diferenca
        )

    def _gerar_desenho_sobreposicao_dwg(
        self,
        caminho_for: Path,
        itens: List[DiferencaElemento],
        pavimento_nome: str,
        caminho_saida: Optional[str] = None
    ) -> Optional[str]:
        """
        Gera prancha DXF profissional com a planta de formas base em cinza claro (DIFF_INALTERADO)
        e os elementos novos, alterados e removidos com cores de alto contraste e carimbo técnico oficial.
        """
        if ezdxf is None:
            return None

        doc = ezdxf.new("R2010", setup=True)
        msp = doc.modelspace()

        layers_cfg = [
            ("DIFF_INALTERADO", colors.LIGHT_GRAY, "Continuous"),
            ("DIFF_NOVO", colors.GREEN, "Continuous"),
            ("DIFF_ALTERADO", colors.CYAN, "Continuous"),
            ("DIFF_REMOVIDO", colors.RED, "Continuous"),
            ("DIFF_TEXTOS", colors.WHITE, "Continuous"),
            ("DIFF_LEGENDA", colors.YELLOW, "Continuous"),
        ]
        for lnome, lcor, ltype in layers_cfg:
            if lnome not in doc.layers:
                doc.layers.add(lnome, color=lcor, linetype=ltype)

        min_x, max_x = float("inf"), float("-inf")
        min_y, max_y = float("inf"), float("-inf")

        # 1. Copia o plano de formas base em DIFF_INALTERADO (cinza claro)
        if caminho_for.exists() and TQSDwg is not None:
            dwg = TQSDwg.Dwg(pedmv=0)
            if dwg.file.Open(str(caminho_for)) == 0:
                it = dwg.iterator
                it.Begin()
                while True:
                    pos = it.GetElementReadPosition()
                    if not pos:
                        break
                    en = it.elementName
                    if en == "Linha":
                        x1, y1, x2, y2 = it.x1, it.y1, it.x2, it.y2
                        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "DIFF_INALTERADO", "lineweight": 9})
                        min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                        min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                    elif en == "Polyline":
                        sz = it.xySize
                        if sz >= 2:
                            pts = [it.GetPolylinePt(i) for i in range(sz)]
                            msp.add_lwpolyline(pts, dxfattribs={"layer": "DIFF_INALTERADO", "lineweight": 9})
                            for pt in pts:
                                min_x, max_x = min(min_x, pt[0]), max(max_x, pt[0])
                                min_y, max_y = min(min_y, pt[1]), max(max_y, pt[1])
                    elif en == "Circulo":
                        xc, yc, r = it.x1, it.y1, getattr(it, "radius", 10.0)
                        msp.add_circle((xc, yc), radius=r, dxfattribs={"layer": "DIFF_INALTERADO", "lineweight": 9})
                    if not it.Next():
                        break
                dwg.file.Close()

        # 2. Destaques Analíticos
        for it in itens:
            if it.status == "INALTERADO":
                continue

            # NOVOS (Verde)
            if it.status == "NOVO" and it.dados_atuais:
                x = it.dados_atuais.get("x", 0.0) * 100.0
                y = it.dados_atuais.get("y", 0.0) * 100.0
                sec = it.dados_atuais.get("secao", "") or it.dados_atuais.get("esp", "")
                r = 35.0 if it.tipo == "PILAR" else 30.0
                msp.add_circle((x, y), radius=r, dxfattribs={"layer": "DIFF_NOVO", "lineweight": 35})
                txt = f"{it.nome} [NOVO {sec}]" if sec else f"{it.nome} [NOVO]"
                msp.add_text(txt, dxfattribs={"layer": "DIFF_TEXTOS", "height": 20.0, "insert": (x + 35.0, y + 10.0)})

            # REMOVIDOS (Vermelho)
            elif it.status == "REMOVIDO" and it.dados_anteriores:
                x = it.dados_anteriores.get("x", 0.0) * 100.0
                y = it.dados_anteriores.get("y", 0.0) * 100.0
                sec = it.dados_anteriores.get("secao", "") or it.dados_anteriores.get("esp", "")
                msp.add_circle((x, y), radius=30.0, dxfattribs={"layer": "DIFF_REMOVIDO", "lineweight": 35})
                msp.add_line((x - 30.0, y - 30.0), (x + 30.0, y + 30.0), dxfattribs={"layer": "DIFF_REMOVIDO", "lineweight": 30})
                msp.add_line((x - 30.0, y + 30.0), (x + 30.0, y - 30.0), dxfattribs={"layer": "DIFF_REMOVIDO", "lineweight": 30})
                txt = f"{it.nome} [REMOVIDO {sec}]" if sec else f"{it.nome} [REMOVIDO]"
                msp.add_text(txt, dxfattribs={"layer": "DIFF_TEXTOS", "height": 20.0, "insert": (x + 35.0, y + 10.0)})

            # ALTERADOS (Ciano)
            elif it.status.startswith("ALTERADO") and it.dados_atuais:
                x = it.dados_atuais.get("x", 0.0) * 100.0
                y = it.dados_atuais.get("y", 0.0) * 100.0
                msp.add_circle((x, y), radius=32.0, dxfattribs={"layer": "DIFF_ALTERADO", "lineweight": 35})
                msp.add_text(
                    f"{it.nome} [{it.valor_anterior}->{it.valor_atual}]",
                    dxfattribs={"layer": "DIFF_TEXTOS", "height": 20.0, "insert": (x + 35.0, y + 10.0)}
                )

        # 3. Legenda técnica oficial e carimbo no topo da prancha
        if min_x != float("inf") and max_x != float("-inf"):
            leg_x = min_x
            leg_y = max_y + 150.0
            w = max(max_x - min_x, 3000.0)
            h = 350.0
            moldura = [(leg_x, leg_y), (leg_x + w, leg_y), (leg_x + w, leg_y + h), (leg_x, leg_y + h)]
            msp.add_lwpolyline(moldura, close=True, dxfattribs={"layer": "DIFF_LEGENDA", "lineweight": 35})

            msp.add_text(
                f"AUTQS - AUDITORIA ESTRUTURAL COMPARATIVA (NBR 6118:2023) | PAVIMENTO: {pavimento_nome.upper()}",
                dxfattribs={"layer": "DIFF_LEGENDA", "height": 38.0, "insert": (leg_x + 50.0, leg_y + 260.0)}
            )
            msp.add_text(
                f"FORMA BASE: {caminho_for.name} | COMPARAÇÃO COM GEOMETRIAS DEFINITIVAS SEM REVISÃO",
                dxfattribs={"layer": "DIFF_LEGENDA", "height": 26.0, "insert": (leg_x + 50.0, leg_y + 200.0)}
            )
            msp.add_text(
                "CÓDIGO DE CORES: [VERDE] Novo Elemento na Forma | [CIANO] Seção Alterada | [VERMELHO] Removido | [CINZA] Inalterado",
                dxfattribs={"layer": "DIFF_LEGENDA", "height": 24.0, "insert": (leg_x + 50.0, leg_y + 140.0)}
            )
            novos = sum(1 for it in itens if it.status == "NOVO")
            alts = sum(1 for it in itens if it.status.startswith("ALTERADO"))
            rems = sum(1 for it in itens if it.status == "REMOVIDO")
            iguais = sum(1 for it in itens if it.status == "INALTERADO")
            msp.add_text(
                f"SÍNTESE ANALÍTICA: {iguais} Inalterados | {novos} Novos | {alts} Alterados | {rems} Removidos",
                dxfattribs={"layer": "DIFF_LEGENDA", "height": 22.0, "insert": (leg_x + 50.0, leg_y + 80.0)}
            )

        if not caminho_saida:
            pasta_plantas = caminho_for.parent.parent / "PLANTAS"
            pasta_plantas.mkdir(parents=True, exist_ok=True)
            nome_clean = re.sub(r"[^A-Za-z0-9]+", "_", pavimento_nome).strip("_")
            caminho_saida = str(pasta_plantas / f"DIFF_FORMAS_{nome_clean}.dxf")

        doc.saveas(str(caminho_saida))
        return str(caminho_saida)

    def comparar_edificio_geometrias(
        self,
        edificio_nome_ou_caminho: str,
        gerar_desenhos_diff: bool = True
    ) -> Dict[str, RelatorioComparacaoResultado]:
        """
        Varre todos os pavimentos de um edifício que possuem FOR*.DWG, identifica as últimas
        geometrias sem revisão no título (Geo_*.DWG / BL1 + BL2) e gera a auditoria completa.
        """
        pasta_ed = None
        if os.path.exists(edificio_nome_ou_caminho) and os.path.isdir(edificio_nome_ou_caminho):
            pasta_ed = Path(edificio_nome_ou_caminho)
        else:
            eds = TQSBuildingReader.listar_edificios_disponiveis()
            id_norm = normalizar_texto(edificio_nome_ou_caminho)
            for ed in eds:
                if id_norm in normalizar_texto(ed["nome"]) or edificio_nome_ou_caminho in ed["nome"]:
                    pasta_ed = Path(ed["caminho"])
                    break

        if not pasta_ed or not pasta_ed.exists():
            raise FileNotFoundError(f"Edifício '{edificio_nome_ou_caminho}' não encontrado.")

        resultados = {}
        for subpasta in sorted(pasta_ed.iterdir()):
            if not subpasta.is_dir():
                continue

            for_files = sorted(subpasta.glob("FOR*.DWG"))
            if not for_files:
                continue

            p_for = for_files[0]

            geos_candidatos = []
            for gf in subpasta.glob("*Geo*.DWG"):
                nome_upper = gf.name.upper()
                if re.search(r"[-_ ]R\d+", nome_upper) or "REV" in nome_upper:
                    continue
                geos_candidatos.append(gf)

            if not geos_candidatos:
                geos_all = sorted(subpasta.glob("*Geo*.DWG"), key=lambda f: f.stat().st_mtime, reverse=True)
                if geos_all:
                    geos_candidatos = [geos_all[0]]

            if not geos_candidatos:
                continue

            bl1 = [g for g in geos_candidatos if "BL1" in g.name.upper()]
            bl2 = [g for g in geos_candidatos if "BL2" in g.name.upper()]
            if bl1 and bl2:
                geos_final = [bl1[0], bl2[0]]
            else:
                geos_final = geos_candidatos

            res = self.comparar_arquivos_dwg(
                caminhos_geo=geos_final,
                caminho_for=p_for,
                pavimento=subpasta.name,
                gerar_desenho_diff=gerar_desenhos_diff
            )
            resultados[subpasta.name] = res

        return resultados

    # =========================================================================
    # COMPARAÇÃO VIA MODELADOR ESTRUTURAL (TQSModelEditor)
    # =========================================================================

    def extrair_elementos_pavimento(self, edificio_nome: str, pavimento_nome: str) -> Dict[str, Dict[str, Any]]:
        """
        Extrai todos os pilares, vigas e lajes de um pavimento do TQS.
        Retorna dicionário indexado por tipo de elemento e nome.
        """
        resultado = {
            "pilares": {},
            "vigas": {},
            "lajes": {},
        }

        try:
            with TQSModelEditor(edificio_nome) as editor:
                try:
                    for p in editor.listar_pilares(pavimento_nome):
                        nome = p["nome"].upper()
                        resultado["pilares"][nome] = p
                except Exception:
                    pass

                try:
                    for v in editor.listar_vigas(pavimento_nome):
                        nome = v["nome"].upper()
                        resultado["vigas"][nome] = v
                except Exception:
                    pass

                try:
                    for l in editor.listar_lajes(pavimento_nome):
                        nome = l["nome"].upper()
                        resultado["lajes"][nome] = l
                except Exception:
                    pass
        except Exception:
            pass

        return resultado

    def comparar_pavimentos(
        self,
        edificio_base: str,
        pavimento_base: str,
        edificio_comparado: Optional[str] = None,
        pavimento_comparado: Optional[str] = None,
        gerar_desenho_diff: bool = True,
        caminho_saida_diff: Optional[str] = None,
    ) -> RelatorioComparacaoResultado:
        """
        Executa a comparação completa entre a geometria base e a geometria comparada.
        """
        if not edificio_comparado:
            edificio_comparado = edificio_base
        if not pavimento_comparado:
            pavimento_comparado = pavimento_base

        elementos_base = self.extrair_elementos_pavimento(edificio_base, pavimento_base)
        elementos_comp = self.extrair_elementos_pavimento(edificio_comparado, pavimento_comparado)

        itens_diferenca: List[DiferencaElemento] = []

        # 1. Pilares
        pils_base = elementos_base.get("pilares", {})
        pils_comp = elementos_comp.get("pilares", {})
        todos_pilares = sorted(set(list(pils_base.keys()) + list(pils_comp.keys())))

        for nome in todos_pilares:
            pb = pils_base.get(nome)
            pc = pils_comp.get(nome)

            if pb and not pc:
                itens_diferenca.append(DiferencaElemento(
                    tipo="PILAR",
                    nome=nome,
                    status="REMOVIDO",
                    valor_anterior=f"Seção {pb.get('b_cm')}x{pb.get('h_cm')} cm @ ({pb.get('x_m'):.3f}, {pb.get('y_m'):.3f})m",
                    valor_atual="--- (Excluído)",
                    delta="Exclusão do elemento",
                    impacto_estrutural="Crítico: Redistribuição de cargas verticais e reações.",
                    dados_anteriores=pb,
                    dados_atuais=None
                ))
            elif pc and not pb:
                itens_diferenca.append(DiferencaElemento(
                    tipo="PILAR",
                    nome=nome,
                    status="NOVO",
                    valor_anterior="--- (Inexistente)",
                    valor_atual=f"Seção {pc.get('b_cm')}x{pc.get('h_cm')} cm @ ({pc.get('x_m'):.3f}, {pc.get('y_m'):.3f})m",
                    delta="Inclusão de novo pilar",
                    impacto_estrutural="Importante: Novo ponto de apoio e carga na fundação.",
                    dados_anteriores=None,
                    dados_atuais=pc
                ))
            else:
                xb, yb = pb.get("x_m", 0.0), pb.get("y_m", 0.0)
                xc, yc = pc.get("x_m", 0.0), pc.get("y_m", 0.0)
                dx_m = round(xc - xb, 3)
                dy_m = round(yc - yb, 3)
                dist_pos_cm = round(math.hypot(dx_m, dy_m) * 100, 1)

                bb, hb = pb.get("b_cm", 0.0), pb.get("h_cm", 0.0)
                bc, hc = pc.get("b_cm", 0.0), pc.get("h_cm", 0.0)
                db_cm = round(bc - bb, 1)
                dh_cm = round(hc - hb, 1)

                mudou_pos = dist_pos_cm > (self.TOLERANCIA_POSICAO_METROS * 100)
                mudou_sec = abs(db_cm) > self.TOLERANCIA_DIMENSAO_CM or abs(dh_cm) > self.TOLERANCIA_DIMENSAO_CM

                if mudou_pos and mudou_sec:
                    status = "ALTERADO_AMBOS"
                    delta = f"Δ({dx_m*100:+.1f}, {dy_m*100:+.1f})cm, Seção Δ({db_cm:+.1f}x{dh_cm:+.1f})cm"
                    impacto = "Crítico: Modificação simultânea de excentricidade e rigidez."
                elif mudou_pos:
                    status = "ALTERADO_POSICAO"
                    delta = f"ΔX={dx_m*100:+.1f}cm, ΔY={dy_m*100:+.1f}cm (d={dist_pos_cm:.1f}cm)"
                    impacto = "Importante: Variação de excentricidade e continuidade vertical."
                elif mudou_sec:
                    status = "ALTERADO_SECAO"
                    delta = f"Δb={db_cm:+.1f}cm, Δh={dh_cm:+.1f}cm (Área: {bc*hc - bb*hb:+.0f}cm²)"
                    impacto = "Atenção: Variação de capacidade resistente e esbeltez λ."
                else:
                    status = "INALTERADO"
                    delta = "0.0 cm"
                    impacto = "Sem impacto."

                itens_diferenca.append(DiferencaElemento(
                    tipo="PILAR",
                    nome=nome,
                    status=status,
                    valor_anterior=f"{bb:.0f}x{hb:.0f} cm @ ({xb:.3f}, {yb:.3f})m",
                    valor_atual=f"{bc:.0f}x{hc:.0f} cm @ ({xc:.3f}, {yc:.3f})m",
                    delta=delta,
                    impacto_estrutural=impacto,
                    dados_anteriores=pb,
                    dados_atuais=pc
                ))

        # 2. Vigas
        vigs_base = elementos_base.get("vigas", {})
        vigs_comp = elementos_comp.get("vigas", {})
        todas_vigas = sorted(set(list(vigs_base.keys()) + list(vigs_comp.keys())))

        for nome in todas_vigas:
            vb = vigs_base.get(nome)
            vc = vigs_comp.get(nome)

            if vb and not vc:
                itens_diferenca.append(DiferencaElemento(
                    tipo="VIGA",
                    nome=nome,
                    status="REMOVIDO",
                    valor_anterior=f"Seção {vb.get('b_cm')}x{vb.get('h_cm')} cm",
                    valor_atual="--- (Excluída)",
                    delta="Exclusão de viga",
                    impacto_estrutural="Crítico: Remoção de apoio de lajes adjacentes.",
                    dados_anteriores=vb,
                    dados_atuais=None
                ))
            elif vc and not vb:
                itens_diferenca.append(DiferencaElemento(
                    tipo="VIGA",
                    nome=nome,
                    status="NOVO",
                    valor_anterior="--- (Inexistente)",
                    valor_atual=f"Seção {vc.get('b_cm')}x{vc.get('h_cm')} cm",
                    delta="Inclusão de viga",
                    impacto_estrutural="Importante: Novo suporte e divisão de panos de laje.",
                    dados_anteriores=None,
                    dados_atuais=vc
                ))
            else:
                bb, hb = vb.get("b_cm", 0.0), vb.get("h_cm", 0.0)
                bc, hc = vc.get("b_cm", 0.0), vc.get("h_cm", 0.0)
                db = round(bc - bb, 1)
                dh = round(hc - hb, 1)
                reb_b = vb.get("desnivel_cm", 0.0)
                reb_c = vc.get("desnivel_cm", 0.0)
                d_reb = round(reb_c - reb_b, 1)

                mudou_sec = abs(db) > self.TOLERANCIA_DIMENSAO_CM or abs(dh) > self.TOLERANCIA_DIMENSAO_CM
                mudou_reb = abs(d_reb) > self.TOLERANCIA_DIMENSAO_CM

                if mudou_sec and mudou_reb:
                    status = "ALTERADO_SECAO"
                    delta = f"Δ({db:+.1f}x{dh:+.1f})cm, Rebaixo Δ={d_reb:+.1f}cm"
                    impacto = "Crítico: Afeta flechas, rigidez EI e nível de apoio de lajes."
                elif mudou_sec:
                    status = "ALTERADO_SECAO"
                    delta = f"Δb={db:+.1f}cm, Δh={dh:+.1f}cm"
                    impacto = "Atenção: Altera inércia à flexão e taxa de armadura."
                elif mudou_reb:
                    status = "ALTERADO_REBAIXO"
                    delta = f"Rebaixo {reb_b:.1f} -> {reb_c:.1f} cm (Δ={d_reb:+.1f}cm)"
                    impacto = "Médio: Variação de cota de topo e apoio de alvenaria."
                else:
                    status = "INALTERADO"
                    delta = "0.0 cm"
                    impacto = "Sem impacto."

                itens_diferenca.append(DiferencaElemento(
                    tipo="VIGA",
                    nome=nome,
                    status=status,
                    valor_anterior=f"{bb:.0f}x{hb:.0f} cm (Reb={reb_b:.1f})",
                    valor_atual=f"{bc:.0f}x{hc:.0f} cm (Reb={reb_c:.1f})",
                    delta=delta,
                    impacto_estrutural=impacto,
                    dados_anteriores=vb,
                    dados_atuais=vc
                ))

        # 3. Lajes
        lajs_base = elementos_base.get("lajes", {})
        lajs_comp = elementos_comp.get("lajes", {})
        todas_lajes = sorted(set(list(lajs_base.keys()) + list(lajs_comp.keys())))

        for nome in todas_lajes:
            lb = lajs_base.get(nome)
            lc = lajs_comp.get(nome)

            if lb and not lc:
                itens_diferenca.append(DiferencaElemento(
                    tipo="LAJE",
                    nome=nome,
                    status="REMOVIDO",
                    valor_anterior=f"h={lb.get('espessura_cm')} cm",
                    valor_atual="--- (Excluída)",
                    delta="Exclusão de laje",
                    impacto_estrutural="Crítico: Vão transformado em vazio / shaft.",
                    dados_anteriores=lb,
                    dados_atuais=None
                ))
            elif lc and not lb:
                itens_diferenca.append(DiferencaElemento(
                    tipo="LAJE",
                    nome=nome,
                    status="NOVO",
                    valor_anterior="--- (Vazio)",
                    valor_atual=f"h={lc.get('espessura_cm')} cm",
                    delta="Inclusão de laje",
                    impacto_estrutural="Importante: Nova carga permanente sobre as vigas de contorno.",
                    dados_anteriores=None,
                    dados_atuais=lc
                ))
            else:
                hb = lb.get("espessura_cm", 0.0)
                hc = lc.get("espessura_cm", 0.0)
                dh = round(hc - hb, 1)
                reb_b = lb.get("desnivel_cm", 0.0)
                reb_c = lc.get("desnivel_cm", 0.0)
                d_reb = round(reb_c - reb_b, 1)

                if abs(dh) > self.TOLERANCIA_DIMENSAO_CM:
                    status = "ALTERADO_ESPESSURA"
                    delta = f"Δh={dh:+.1f}cm (h: {hb:.1f} -> {hc:.1f}cm)"
                    impacto = "Atenção: Altera peso próprio e rigidez da grelha."
                elif abs(d_reb) > self.TOLERANCIA_DIMENSAO_CM:
                    status = "ALTERADO_REBAIXO"
                    delta = f"ΔReb={d_reb:+.1f}cm ({reb_b:.1f} -> {reb_c:.1f}cm)"
                    impacto = "Médio: Alteração de rebaixo arquitetônico (área molhada)."
                else:
                    status = "INALTERADO"
                    delta = "0.0 cm"
                    impacto = "Sem impacto."

                itens_diferenca.append(DiferencaElemento(
                    tipo="LAJE",
                    nome=nome,
                    status=status,
                    valor_anterior=f"h={hb:.1f} cm (Reb={reb_b:.1f})",
                    valor_atual=f"h={hc:.1f} cm (Reb={reb_c:.1f})",
                    delta=delta,
                    impacto_estrutural=impacto,
                    dados_anteriores=lb,
                    dados_atuais=lc
                ))

        # Gera desenho de sobreposição visual DXF se solicitado
        caminho_dxf = None
        if gerar_desenho_diff:
            caminho_dxf = self._gerar_desenho_sobreposicao_diff(
                edificio_base=edificio_base,
                pavimento_base=pavimento_base,
                itens=itens_diferenca,
                caminho_saida=caminho_saida_diff
            )

        return RelatorioComparacaoResultado(
            origem_base=edificio_base,
            origem_comparada=edificio_comparado,
            pavimento_base=pavimento_base,
            pavimento_comparado=pavimento_comparado,
            caminho_diff_dxf=caminho_dxf,
            itens=itens_diferenca
        )

    def _gerar_desenho_sobreposicao_diff(
        self,
        edificio_base: str,
        pavimento_base: str,
        itens: List[DiferencaElemento],
        caminho_saida: Optional[str] = None
    ) -> Optional[str]:
        """Gera prancha DXF técnica com sobreposição gráfica e código de cores para TQSModelEditor."""
        if ezdxf is None:
            return None

        doc = ezdxf.new("R2010", setup=True)
        msp = doc.modelspace()

        layers_cfg = [
            ("DIFF_REMOVIDO", colors.RED, "Continuous"),
            ("DIFF_NOVO", colors.GREEN, "Continuous"),
            ("DIFF_ALTERADO", colors.CYAN, "Continuous"),
            ("DIFF_INALTERADO", colors.LIGHT_GRAY, "Continuous"),
            ("DIFF_TEXTOS", colors.WHITE, "Continuous"),
            ("DIFF_LEGENDA", colors.YELLOW, "Continuous"),
        ]
        for lnome, lcor, ltype in layers_cfg:
            if lnome not in doc.layers:
                doc.layers.add(lnome, color=lcor, linetype=ltype)

        min_x, max_x = float("inf"), float("-inf")
        min_y, max_y = float("inf"), float("-inf")

        for it in itens:
            if it.tipo == "PILAR":
                if it.status in ["REMOVIDO", "ALTERADO_POSICAO", "ALTERADO_AMBOS"] and it.dados_anteriores:
                    x = it.dados_anteriores.get("x_m", 0.0)
                    y = it.dados_anteriores.get("y_m", 0.0)
                    b = it.dados_anteriores.get("b_cm", 20.0) / 100.0
                    h = it.dados_anteriores.get("h_cm", 50.0) / 100.0
                    pts = [(x - b/2, y - h/2), (x + b/2, y - h/2), (x + b/2, y + h/2), (x - b/2, y + h/2)]
                    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DIFF_REMOVIDO", "lineweight": 20})
                    min_x, max_x = min(min_x, x - b), max(max_x, x + b)
                    min_y, max_y = min(min_y, y - h), max(max_y, y + h)

                if it.dados_atuais:
                    x = it.dados_atuais.get("x_m", 0.0)
                    y = it.dados_atuais.get("y_m", 0.0)
                    b = it.dados_atuais.get("b_cm", 20.0) / 100.0
                    h = it.dados_atuais.get("h_cm", 50.0) / 100.0
                    pts = [(x - b/2, y - h/2), (x + b/2, y - h/2), (x + b/2, y + h/2), (x - b/2, y + h/2)]

                    lay = "DIFF_INALTERADO"
                    if it.status == "NOVO":
                        lay = "DIFF_NOVO"
                    elif it.status.startswith("ALTERADO"):
                        lay = "DIFF_ALTERADO"

                    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": lay, "lineweight": 35 if lay != "DIFF_INALTERADO" else 15})
                    msp.add_text(
                        f"{it.nome} ({it.delta})",
                        dxfattribs={"layer": "DIFF_TEXTOS", "height": 0.15, "insert": (x + b/2 + 0.05, y)}
                    )
                    min_x, max_x = min(min_x, x - b), max(max_x, x + b)
                    min_y, max_y = min(min_y, y - h), max(max_y, y + h)

            elif it.tipo == "VIGA":
                if it.dados_atuais and "coordenadas" in it.dados_atuais:
                    coords = it.dados_atuais["coordenadas"]
                    if len(coords) >= 2:
                        pts = [(c["x_m"], c["y_m"]) for c in coords]
                        lay = "DIFF_INALTERADO"
                        if it.status == "NOVO":
                            lay = "DIFF_NOVO"
                        elif it.status.startswith("ALTERADO"):
                            lay = "DIFF_ALTERADO"
                        msp.add_lwpolyline(pts, close=False, dxfattribs={"layer": lay, "lineweight": 25})

        if min_x != float("inf"):
            leg_x = min_x
            leg_y = max_y + 1.5
            msp.add_text(
                f"AUTQS: SOBREPOSIÇÃO GEOMÉTRICA - {edificio_base} ({pavimento_base})",
                dxfattribs={"layer": "DIFF_LEGENDA", "height": 0.35, "insert": (leg_x, leg_y + 1.0)}
            )
            msp.add_text(
                "LEGENDA: [VERDE] = Novo elemento  |  [VERMELHO] = Removido  |  [CIANO] = Alterado  |  [CINZA] = Inalterado",
                dxfattribs={"layer": "DIFF_LEGENDA", "height": 0.22, "insert": (leg_x, leg_y + 0.4)}
            )

        if not caminho_saida:
            nome_ed_limpo = "".join(c for c in edificio_base if c.isalnum() or c in "._- ")[:20]
            nome_pav_limpo = "".join(c for c in pavimento_base if c.isalnum() or c in "._- ")[:15]
            pasta_dest = os.path.join(r"C:\TQS", edificio_base, "PLANTAS")
            if not os.path.exists(pasta_dest):
                pasta_dest = os.getcwd()
            caminho_saida = os.path.join(pasta_dest, f"DIFF_FORMAS_{nome_ed_limpo}_{nome_pav_limpo}.dxf")

        try:
            doc.saveas(caminho_saida)
            return caminho_saida
        except Exception:
            return None
