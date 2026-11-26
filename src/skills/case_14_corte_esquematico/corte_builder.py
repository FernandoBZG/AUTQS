import gzip
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import src.tqs_adapter.tqs_env  # noqa: F401
from TQS import TQSDwg
from src.tqs_adapter.model_editor import TQSModelEditor


@dataclass
class DadosPavimentoCorte:
    """Dados estruturais e de materiais de um pavimento para o corte esquemático."""

    nome: str
    cota_m: float
    pe_direito_m: float
    sistema: str  # "AE" (Alvenaria Estrutural) ou "CA" (Concreto Armado)
    fck_concreto: str = "C25"
    fbk_mpa: Optional[float] = None
    fak_mpa: Optional[float] = None
    fgk_mpa: Optional[float] = None
    fpk_mpa: Optional[float] = None
    fpkg_mpa: Optional[float] = None


@dataclass
class DadosEdificioCorte:
    """Metadados consolidados do edifício para geração do corte esquemático."""

    nome_edificio: str
    caminho_edificio: str
    tipo_bloco: str  # "BLOCOS CERÂMICOS" ou "BLOCOS DE CONCRETO"
    fck_lajes_vigas: str
    fck_pilares: str
    cota_base_m: float = 0.0
    arm_graute_mm: float = 12.5
    pavimentos: List[DadosPavimentoCorte] = field(default_factory=list)


def _fmt_mpa(val: Optional[float]) -> str:
    """Formata resistência em MPa no padrão do corte esquemático."""
    if val is None:
        return "-"
    val_r = round(float(val), 1)
    if abs(val_r - round(val_r)) < 0.05:
        return f"{int(round(val_r))}"
    return f"{val_r:.1f}".replace(".", ",")


def _parse_aedimalv_levels(rep_path: Path) -> List[Dict[str, float]]:
    """Extrai resistências (FBK, FAK, FGK, FPK, FPKG) por nível do AEDIMALV.REP."""
    if not rep_path.exists():
        return []
    try:
        xml_text = gzip.decompress(rep_path.read_bytes()).decode("latin-1", errors="replace")
    except Exception:
        return []

    level_blocks = re.findall(
        r"<a:Key>LEVEL\[(\d+)\]</a:Key>(.*?)</separator></a:Value>",
        xml_text,
        flags=re.DOTALL,
    )
    resultados: List[Dict[str, float]] = []
    for idx_str, body in sorted(level_blocks, key=lambda x: int(x[0])):
        item: Dict[str, float] = {"level_idx": float(idx_str)}
        for key in ("FBK", "FAK", "FGK", "FPK", "FPKG"):
            m = re.search(rf"<a:Key>{key}</a:Key><a:Value[^>]*>([^<]+)</a:Value>", body)
            if m:
                try:
                    item[key] = round(float(m.group(1)) / 1e6, 2)
                except ValueError:
                    pass
        if "FBK" in item:
            resultados.append(item)
    return resultados


def _nome_pavimento_expandido(nome_base: str, rep_idx: int, total_rep: int, piso_num: int) -> str:
    """Gera o rótulo do pavimento no corte (ex: 2o PAVTO..14o PAVTO quando há repetições)."""
    if total_rep > 1:
        return f"{piso_num}o PAVTO"
    nome = nome_base.strip().upper()
    nome = nome.replace("PAVIMENTO", "PAVTO").replace("^", "o")
    return nome


class CorteEsquematicoBuilder:
    """
    Extrai dados reais do edifício TQS (pavimentos, cotas, pés-direitos, fck e
    resistências de alvenaria em AEDIMALV.REP) e gera GERAIS\\CORTE ESQUEMÁTICO.DWG
    no padrão visual da referência 054.
    """

    def extrair_dados_edificio(
        self,
        edificio_nome_ou_caminho: str,
        cota_base_m: Optional[float] = None,
        arm_graute_mm: float = 12.5,
        overrides_pavimentos: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> DadosEdificioCorte:
        """Lê pavimentos, alturas e materiais do edifício via TQSBuild + Alvest."""
        overrides = overrides_pavimentos or {}
        with TQSModelEditor(edificio_nome_ou_caminho) as ed:
            b = ed._build
            fl = b.floorsplan
            mat = b.materials

            tipo_bloco = (
                "BLOCOS CERÂMICOS" if getattr(mat, "masonryMaterial", 2) == 2 else "BLOCOS DE CONCRETO"
            )
            fck_lv = str(getattr(mat, "beamConcreteStrength", "") or "C25").strip() or "C25"
            fck_pil = str(getattr(mat, "columnConcreteStrength", "") or fck_lv).strip() or fck_lv

            cota_partida = (
                float(cota_base_m)
                if cota_base_m is not None
                else round(float(getattr(b.project, "floorHeight", 0.0) or 0.0), 2)
            )
            n_plans = fl.floorsPlanNumber
            cota_atual = cota_partida
            piso_corrente = 1
            pavimentos: List[DadosPavimentoCorte] = []

            for i in range(n_plans):
                raw_name = fl.GetName(i) or f"PAV_{i}"
                pd_m = float(fl.GetFloorHeight(i) or 2.70)
                rep = max(1, int(fl.GetRepetition(i) or 1))
                fck_fl = str(mat.GetFloorPlanConcreteStrength(i) or "").strip() or fck_lv

                pasta_pav = Path(ed.caminho_edificio) / raw_name
                alvest_levels = _parse_aedimalv_levels(pasta_pav / "AEDIMALV.REP")

                for r in range(rep):
                    cota_atual = round(cota_atual + pd_m, 2)
                    piso_num = piso_corrente
                    piso_corrente += 1
                    nome_fmt = _nome_pavimento_expandido(raw_name, r, rep, piso_num)

                    alv: Dict[str, float] = {}
                    if alvest_levels:
                        alv = alvest_levels[min(r, len(alvest_levels) - 1)]

                    # Se houver AEDIMALV.REP, é pavimento de Alvenaria Estrutural (exceto se override)
                    sistema = "AE" if alv else "CA"
                    dados_pav = DadosPavimentoCorte(
                        nome=nome_fmt,
                        cota_m=cota_atual,
                        pe_direito_m=round(pd_m, 2),
                        sistema=sistema,
                        fck_concreto=fck_fl,
                        fbk_mpa=alv.get("FBK"),
                        fak_mpa=alv.get("FAK"),
                        fgk_mpa=alv.get("FGK"),
                        fpk_mpa=alv.get("FPK"),
                        fpkg_mpa=alv.get("FPKG"),
                    )

                    if nome_fmt in overrides:
                        ov = overrides[nome_fmt]
                        for k, v in ov.items():
                            if hasattr(dados_pav, k):
                                setattr(dados_pav, k, v)

                    pavimentos.append(dados_pav)

            return DadosEdificioCorte(
                nome_edificio=ed.nome_edificio,
                caminho_edificio=ed.caminho_edificio,
                tipo_bloco=tipo_bloco,
                fck_lajes_vigas=fck_lv,
                fck_pilares=fck_pil,
                cota_base_m=cota_partida,
                arm_graute_mm=arm_graute_mm,
                pavimentos=pavimentos,
            )

    def gerar_dwg(
        self,
        dados: DadosEdificioCorte,
        caminho_saida_dwg: Optional[str] = None,
    ) -> str:
        """Desenha o arquivo CORTE ESQUEMÁTICO.DWG nativo do TQS."""
        gerais_dir = Path(dados.caminho_edificio) / "GERAIS"
        gerais_dir.mkdir(parents=True, exist_ok=True)
        saida = Path(caminho_saida_dwg) if caminho_saida_dwg else (gerais_dir / "CORTE ESQUEMÁTICO.DWG")

        if saida.exists():
            bkp = saida.with_suffix(".BAK")
            shutil.copy2(saida, bkp)

        dwg = TQSDwg.Dwg()
        dwg.file.New()
        # Propriedade oficial do arquivo no TQS: Alvenarias (17) -> Alvenaria em vedação (12)
        dwg.settings.systemId = 17
        dwg.settings.subSystemId = 12
        dwg.settings.scale = 50.0

        # Parâmetros geométricos fiéis ao CORTE ESQUEMÁTICO.DWG de 054
        x_esq = -308.3
        x_dir = 41.1
        x_txt_mat = -141.3
        x_txt_pav = -296.0
        x_cota_ini = 80.7
        x_cota_fim = 186.0
        x_tri = 176.5
        escala_y = 24.0  # unidades por metro de pé-direito

        y_base = -800.0
        y_atual = y_base
        faixas_pav: List[Tuple[DadosPavimentoCorte, float, float]] = []

        # Desenha de baixo para cima (pavimento inferior -> cobertura/reservatório)
        for pav in dados.pavimentos:
            h_box = max(64.0, round(pav.pe_direito_m * escala_y, 2))
            y0 = y_atual
            y1 = y0 + h_box

            # Caixa do pavimento (Nível 249 cor 3 para AE, Nível 248 cor 7 para CA)
            dwg.draw.level = 249 if pav.sistema == "AE" else 248
            dwg.draw.color = 3 if pav.sistema == "AE" else 7
            self._desenhar_retangulo(dwg, x_esq, y0, x_dir, y1)

            # Nome do pavimento
            dwg.draw.level = 0
            dwg.draw.color = 7
            dwg.draw.Text(x_txt_pav, (y0 + y1) * 0.5 + 2.0, 9.5, 0.0, pav.nome)
            dwg.draw.Text(x_txt_pav, (y0 + y1) * 0.5 - 12.0, 7.0, 0.0, f"PD={pav.pe_direito_m:.2f}m")

            # Especificação de materiais do pavimento
            if pav.sistema == "AE" and pav.fbk_mpa is not None:
                dwg.draw.level = 257
                dwg.draw.color = 7
                y_mid = (y0 + y1) * 0.5
                dwg.draw.Text(x_txt_mat, y_mid + 16.0, 10.0, 0.0, f"BLOCO {_fmt_mpa(pav.fbk_mpa)} MPa")
                dwg.draw.Text(x_txt_mat, y_mid + 2.5, 8.0, 0.0, f"ARGAMASSA {_fmt_mpa(pav.fak_mpa)} MPa")
                dwg.draw.Text(x_txt_mat, y_mid - 11.0, 8.0, 0.0, f"GRAUTE {_fmt_mpa(pav.fgk_mpa)} MPa")
                dwg.draw.Text(x_txt_mat, y_mid - 24.5, 8.0, 0.0, f"PRISMA (OCO) {_fmt_mpa(pav.fpk_mpa)} MPa")
            else:
                dwg.draw.level = 257
                dwg.draw.color = 7
                dwg.draw.Text(x_txt_mat, (y0 + y1) * 0.5 - 4.0, 9.5, 0.0, f"CONCRETO ARMADO {pav.fck_concreto}")

            # Linha e símbolo de cota no topo do pavimento (y1)
            dwg.draw.level = 200
            dwg.draw.color = 7
            dwg.draw.Line(x_cota_ini, y1, x_cota_fim, y1)

            dwg.draw.level = 221
            dwg.draw.color = 11
            dwg.draw.Line(x_tri, y1, x_tri + 2.4, y1 + 3.4)
            dwg.draw.Line(x_tri, y1, x_tri - 2.4, y1 + 3.4)
            dwg.draw.Line(x_tri - 2.4, y1 + 3.4, x_tri + 2.4, y1 + 3.4)
            dwg.draw.Line(x_tri, y1 + 3.4, x_tri, y1 + 8.1)
            dwg.draw.Line(x_tri, y1 + 8.1, 150.4, y1 + 8.1)

            dwg.draw.level = 0
            dwg.draw.color = 7
            dwg.draw.Text(150.9, y1 + 11.0, 9.5, 0.0, f"{pav.cota_m:.2f}")

            faixas_pav.append((pav, y0, y1))
            y_atual = y1

        # Título principal
        y_topo = y_atual + 55.0
        dwg.draw.level = 0
        dwg.draw.color = 7
        dwg.draw.Text(-428.0, y_topo, 19.8, 0.0, "CORTE ESQUEMÁTICO COM RESISTÊNCIAS DOS MATERIAIS")
        dwg.draw.Text(-428.0, y_topo - 24.0, 10.0, 0.0, f"EDIFÍCIO: {dados.nome_edificio.upper()}")

        # Faixas laterais de sistema estrutural (Nível 18, cor 2, 90°)
        self._desenhar_faixas_sistema(dwg, faixas_pav, dados)

        # Legenda/Indicador de blocos alinhado verticalmente aos pavimentos de cada fbk
        grupos_fbk: List[Tuple[float, float, float]] = []
        for pav, y0, y1 in faixas_pav:
            if pav.sistema == "AE" and pav.fbk_mpa is not None:
                if grupos_fbk and grupos_fbk[-1][0] == pav.fbk_mpa:
                    grupos_fbk[-1] = (pav.fbk_mpa, grupos_fbk[-1][1], y1)
                else:
                    grupos_fbk.append((pav.fbk_mpa, y0, y1))

        fbks_unicos = sorted({g[0] for g in grupos_fbk})
        for fbk, gy0, gy1 in grupos_fbk:
            y_centro = (gy0 + gy1) * 0.5
            self._desenhar_indicador_bloco(dwg, -537.5, y_centro, fbk)
            # Linha de chamada ligando o indicador de bloco à faixa dos pavimentos
            dwg.draw.level = 0
            dwg.draw.color = 7
            dwg.draw.Line(-418.7, y_centro, -381.9, y_centro)

        # Indicador da armadura do graute e argamassamento à direita da zona de alvenaria
        faixas_ae = [(p, y0, y1) for p, y0, y1 in faixas_pav if p.sistema == "AE"]
        if faixas_ae:
            y_ae_mid = (faixas_ae[0][1] + faixas_ae[-1][2]) * 0.5
            self._desenhar_indicador_arm_graute(dwg, y_ae_mid, dados.arm_graute_mm)

        # Rodapé técnico normativo
        y_rod = y_base - 80.0
        dwg.draw.level = 257
        dwg.draw.color = 7
        if fbks_unicos:
            dwg.draw.Text(-285.0, y_rod, 10.0, 0.0, f"ALVENARIA ESTRUTURAL - {dados.tipo_bloco}")
            y_rod -= 16.0
        dwg.draw.Text(-285.0, y_rod, 10.0, 0.0, f"LAJES, VIGAS E ESCADAS - {dados.fck_lajes_vigas}")
        y_rod -= 22.0
        dwg.draw.Text(-285.0, y_rod, 10.0, 0.0, f"ESTRUTURA DE CONCRETO ARMADO - {dados.fck_pilares}")
        if fbks_unicos:
            y_rod -= 38.0
            dwg.draw.Text(
                -626.0,
                y_rod,
                7.9,
                0.0,
                "PRISMA GRAUTEADO: TODOS OS PRISMAS GRAUTEADOS DEVEM OBTER RESISTÊNCIA IGUAL OU SUPERIOR A 50% DO VALOR DO PRISMA OCO DO PAVIMENTO EM QUESTÃO.",
            )
            y_rod -= 16.0
            dwg.draw.Text(-626.0, y_rod, 7.9, 0.0, "OBS: PRISMAS OBTIDOS CONFORME A NBR 16868-3")

        dwg.file.SaveAs(str(saida))
        dwg.file.Close()
        return str(saida)

    def _desenhar_retangulo(self, dwg: Any, x0: float, y0: float, x1: float, y1: float) -> None:
        dwg.draw.PolyStart()
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for px, py in pts:
            dwg.draw.PolyEnterPoint(px, py)
        dwg.draw.Polyline()

    def _desenhar_faixas_sistema(
        self,
        dwg: Any,
        faixas_pav: List[Tuple[DadosPavimentoCorte, float, float]],
        dados: DadosEdificioCorte,
    ) -> None:
        if not faixas_pav:
            return
        grupos: List[Tuple[str, float, float]] = []
        sis_atual = faixas_pav[0][0].sistema
        y_ini = faixas_pav[0][1]
        y_fim = faixas_pav[0][2]
        for pav, y0, y1 in faixas_pav[1:]:
            if pav.sistema == sis_atual:
                y_fim = y1
            else:
                grupos.append((sis_atual, y_ini, y_fim))
                sis_atual = pav.sistema
                y_ini = y0
                y_fim = y1
        grupos.append((sis_atual, y_ini, y_fim))

        for sis, y0, y1 in grupos:
            dwg.draw.level = 0
            dwg.draw.color = 7
            dwg.draw.Line(-381.9, y0 + 10.0, -381.9, y1 - 10.0)
            dwg.draw.Line(-381.9, y0 + 10.0, -365.0, y0 + 10.0)
            dwg.draw.Line(-381.9, y1 - 10.0, -365.0, y1 - 10.0)

            dwg.draw.level = 18
            dwg.draw.color = 2
            y_mid = (y0 + y1) * 0.5 - 75.0
            if sis == "AE":
                dwg.draw.Text(-615.0, y_mid, 11.8, 90.0, "ALVENARIA ESTRUTURAL")
                dwg.draw.Text(-593.0, y_mid, 11.8, 90.0, f"LAJES E VIGAS - FCK {dados.fck_lajes_vigas.replace('C', '')} MPa")
            else:
                dwg.draw.Text(-615.0, y_mid, 11.8, 90.0, "PÓRTICO DE CONCRETO")
                dwg.draw.Text(-593.0, y_mid, 11.8, 90.0, f"ARMADO - FCK {dados.fck_pilares.replace('C', '')} MPa")

    def _desenhar_indicador_bloco(self, dwg: Any, x_esq: float, y_centro: float, fbk_mpa: float) -> None:
        """Desenha indicador gráfico do bloco estrutural (contorno + furos + texto BLOCO XX MPa)."""
        # Caixa externa (118.8 x 76)
        dwg.draw.level = 0
        dwg.draw.color = 7
        self._desenhar_retangulo(dwg, x_esq, y_centro - 38.0, x_esq + 118.8, y_centro + 38.0)

        # Ícone esquemático de bloco vazado (2 furos) na parte superior da caixa
        cor_bloco = {7.0: 3, 10.0: 4, 15.0: 2, 18.0: 6, 20.0: 1}.get(round(fbk_mpa, 0), 3)
        dwg.draw.level = 249
        dwg.draw.color = cor_bloco
        bx0, by0 = x_esq + 24.0, y_centro + 2.0
        bx1, by1 = x_esq + 94.8, y_centro + 28.0
        self._desenhar_retangulo(dwg, bx0, by0, bx1, by1)
        # Dois furos internos
        self._desenhar_retangulo(dwg, bx0 + 6.0, by0 + 4.5, bx0 + 32.0, by1 - 4.5)
        self._desenhar_retangulo(dwg, bx0 + 38.8, by0 + 4.5, bx1 - 6.0, by1 - 4.5)

        dwg.draw.level = 257
        dwg.draw.color = 7
        dwg.draw.Text(x_esq + 10.9, y_centro - 22.0, 9.5, 0.0, f"BLOCO {_fmt_mpa(fbk_mpa)} MPa")

    def _desenhar_indicador_arm_graute(self, dwg: Any, y_centro: float, arm_graute_mm: float) -> None:
        """Desenha o indicador de armadura do graute e o detalhe de argamassamento total."""
        # Detalhe da barra vertical de armadura do graute (com ganchos nas extremidades)
        dwg.draw.level = 18
        dwg.draw.color = 2
        x_bar = 261.1
        dwg.draw.Line(x_bar, y_centro - 42.0, x_bar, y_centro + 42.0)
        dwg.draw.Line(x_bar, y_centro + 42.0, x_bar + 10.0, y_centro + 34.0)
        dwg.draw.Line(x_bar, y_centro - 42.0, x_bar + 10.0, y_centro - 34.0)
        dwg.draw.Text(282.7, y_centro - 18.0, 9.9, 0.0, "ARM. GRAUTE")
        dwg.draw.Text(298.0, y_centro + 2.0, 9.9, 0.0, f"{{ {arm_graute_mm:g}")

        # Linha de chamada para o detalhe de argamassamento
        dwg.draw.level = 0
        dwg.draw.color = 7
        dwg.draw.Line(253.2, y_centro, 269.1, y_centro)
        dwg.draw.Line(395.0, y_centro - 2.4, 410.0, y_centro - 2.4)

        dwg.draw.level = 257
        dwg.draw.color = 7
        dwg.draw.Text(420.0, y_centro + 22.0, 9.9, 0.0, "ARGAMASSAMENTO TOTAL")
        dwg.draw.Text(420.0, y_centro + 5.0, 9.9, 0.0, "NAS PAREDES LONGITUDINAIS E")
        dwg.draw.Text(420.0, y_centro - 11.0, 9.9, 0.0, "TRANSVERSAIS DO BLOCO")

        # Detalhe gráfico do bloco com argamassamento total + ponto de graute armado
        dx0, dy0 = 420.0, y_centro - 68.0
        dx1, dy1 = 537.0, y_centro - 24.0  # bloco 39x14 em escala 3:1
        dwg.draw.level = 249
        dwg.draw.color = 3
        self._desenhar_retangulo(dwg, dx0, dy0, dx1, dy1)
        # Furos internos
        f1x0, f1x1 = dx0 + 9.0, dx0 + 52.5
        f2x0, f2x1 = dx0 + 64.5, dx1 - 9.0
        fy0, fy1 = dy0 + 7.5, dy1 - 7.5
        self._desenhar_retangulo(dwg, f1x0, fy0, f1x1, fy1)
        self._desenhar_retangulo(dwg, f2x0, fy0, f2x1, fy1)

        # Indicação visual da argamassa nas paredes longitudinais e transversais (cor 4 = Ciano)
        dwg.draw.level = 221
        dwg.draw.color = 4
        for offset in (2.5, 5.0):
            # Paredes longitudinais (superior e inferior)
            dwg.draw.Line(dx0 + 2.0, dy0 + offset, dx1 - 2.0, dy0 + offset)
            dwg.draw.Line(dx0 + 2.0, dy1 - offset, dx1 - 2.0, dy1 - offset)
            # Paredes transversais (esquerda, septo central, direita)
            dwg.draw.Line(dx0 + offset, dy0 + 2.0, dx0 + offset, dy1 - 2.0)
            dwg.draw.Line(f1x1 + offset + 1.0, dy0 + 2.0, f1x1 + offset + 1.0, dy1 - 2.0)
            dwg.draw.Line(dx1 - offset, dy0 + 2.0, dx1 - offset, dy1 - 2.0)

        # Ponto de graute armado no 1º furo (círculo de aço)
        dwg.draw.level = 18
        dwg.draw.color = 2
        dwg.draw.Circle((f1x0 + f1x1) * 0.5, (fy0 + fy1) * 0.5, 4.5)
