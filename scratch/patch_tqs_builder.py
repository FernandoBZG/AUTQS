import re

with open("src/drawing/tqs_dwg_builder.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update construir_planta_de_cargas signature
old_sig = '''    def construir_planta_de_cargas(
        self,
        planta: PlantaDeCargasModel,
        arquivo_saida_dwg: str,
        escala: Optional[int] = None,
    ) -> str:'''

new_sig = '''    def construir_planta_de_cargas(
        self,
        planta: PlantaDeCargasModel,
        arquivo_saida_dwg: str,
        escala: Optional[int] = None,
        origem_cotas: Optional[Tuple[float, float]] = None,
    ) -> str:'''

assert old_sig in code, "old_sig not found"
code = code.replace(old_sig, new_sig, 1)

# 2. Update g_edmexdefcotrel call in construir_planta_de_cargas
old_cotrel = '''        # Redefine a origem das cotas relativas (IPOCOTREL) para a origem global (0, 0, 0)
        if self._mdwg_dll is not None and hasattr(dwg, "m_pedmv") and dwg.m_pedmv:
            try:
                self._mdwg_dll.g_edmexdefcotrel(
                    ctypes.c_void_p(dwg.m_pedmv),
                    ctypes.c_double(0.0),
                    ctypes.c_double(0.0),
                    ctypes.c_double(0.0),
                )
            except Exception:
                pass'''

new_cotrel = '''        # Redefine a origem das cotas relativas (IPOCOTREL) para a origem especificada (ou 0, 0, 0)
        rx = float(origem_cotas[0]) if origem_cotas else 0.0
        ry = float(origem_cotas[1]) if origem_cotas else 0.0
        if self._mdwg_dll is not None and hasattr(dwg, "m_pedmv") and dwg.m_pedmv:
            try:
                self._mdwg_dll.g_edmexdefcotrel(
                    ctypes.c_void_p(dwg.m_pedmv),
                    ctypes.c_double(rx),
                    ctypes.c_double(ry),
                    ctypes.c_double(0.0),
                )
            except Exception:
                pass'''

assert old_cotrel in code, "old_cotrel not found"
code = code.replace(old_cotrel, new_cotrel, 1)

# 3. Update call to _desenhar_pilares_locacao
old_des_pil = "self._desenhar_pilares_locacao(dwg, planta.pilares, bounds_planta, escala=escala)"
new_des_pil = "self._desenhar_pilares_locacao(dwg, planta.pilares, bounds_planta, escala=escala, origem_cotas=origem_cotas)"
assert old_des_pil in code, "old_des_pil not found"
code = code.replace(old_des_pil, new_des_pil, 1)

# 4. Update calls to _desenhar_tabela_baricentros and _desenhar_notas_e_legendas in layout abaixo
old_abaixo_calls = '''            # 1. Tabela de Baricentros
            x_bar = x_base
            y_fim_bar, larg_tabela_bar = self._desenhar_tabela_baricentros(
                dwg, planta.pilares, x_start=x_bar, y_start=y_topo_tabelas, escala=escala
            )

            # 2. Tabela de Cargas (ao lado da de baricentros)
            x_cargas = x_bar + larg_tabela_bar + espaco_inter
            y_fim_cargas, larg_tabela_cargas = self._desenhar_tabela_cargas(
                dwg,
                pilares=planta.pilares,
                x_start=x_cargas,
                y_start=y_topo_tabelas,
                dados_porlid=planta.dados_porlid,
                escala=escala,
            )

            # 3. Notas, Convenção de Sinais e Legenda (ao lado da de cargas)
            x_notas = x_cargas + larg_tabela_cargas + espaco_inter
            y_fim_notas = self._desenhar_notas_e_legendas(
                dwg, x_start=x_notas, y_start=y_topo_tabelas, dados_porlid=planta.dados_porlid, escala=escala
            )'''

new_abaixo_calls = '''            # 1. Tabela de Baricentros
            x_bar = x_base
            y_fim_bar, larg_tabela_bar = self._desenhar_tabela_baricentros(
                dwg, planta.pilares, x_start=x_bar, y_start=y_topo_tabelas, escala=escala, origem_cotas=origem_cotas
            )

            # 2. Tabela de Cargas (ao lado da de baricentros)
            x_cargas = x_bar + larg_tabela_bar + espaco_inter
            y_fim_cargas, larg_tabela_cargas = self._desenhar_tabela_cargas(
                dwg,
                pilares=planta.pilares,
                x_start=x_cargas,
                y_start=y_topo_tabelas,
                dados_porlid=planta.dados_porlid,
                escala=escala,
            )

            # 3. Notas, Convenção de Sinais e Legenda (ao lado da de cargas)
            x_notas = x_cargas + larg_tabela_cargas + espaco_inter
            y_fim_notas = self._desenhar_notas_e_legendas(
                dwg, x_start=x_notas, y_start=y_topo_tabelas, dados_porlid=planta.dados_porlid, escala=escala, origem_cotas=origem_cotas
            )'''

assert old_abaixo_calls in code, "old_abaixo_calls not found"
code = code.replace(old_abaixo_calls, new_abaixo_calls, 1)

# 5. Update calls in layout lateral
old_lateral_calls = '''            # 1. Tabela de Baricentros (coluna 1 da direita)
            x_bar = x_start_dir
            y_fim_bar, larg_tabela_bar = self._desenhar_tabela_baricentros(
                dwg, planta.pilares, x_start=x_bar, y_start=y_topo_tabelas, escala=escala
            )

            # 2. Tabela de Cargas (coluna 2 da direita, alinhada no topo com Baricentros)
            x_cargas = x_bar + larg_tabela_bar + espaco_inter
            y_fim_cargas, larg_tabela_cargas = self._desenhar_tabela_cargas(
                dwg,
                pilares=planta.pilares,
                x_start=x_cargas,
                y_start=y_topo_tabelas,
                dados_porlid=planta.dados_porlid,
                escala=escala,
            )

            # 3. Notas, Convenção de Sinais e Legenda (diretamente abaixo de Baricentros e Cargas)
            y_topo_notas = min(y_fim_bar, y_fim_cargas) - (70.0 * fator_esc)
            x_notas = x_start_dir
            y_fim_notas = self._desenhar_notas_e_legendas(
                dwg, x_start=x_notas, y_start=y_topo_notas, dados_porlid=planta.dados_porlid, escala=escala
            )'''

new_lateral_calls = '''            # 1. Tabela de Baricentros (coluna 1 da direita)
            x_bar = x_start_dir
            y_fim_bar, larg_tabela_bar = self._desenhar_tabela_baricentros(
                dwg, planta.pilares, x_start=x_bar, y_start=y_topo_tabelas, escala=escala, origem_cotas=origem_cotas
            )

            # 2. Tabela de Cargas (coluna 2 da direita, alinhada no topo com Baricentros)
            x_cargas = x_bar + larg_tabela_bar + espaco_inter
            y_fim_cargas, larg_tabela_cargas = self._desenhar_tabela_cargas(
                dwg,
                pilares=planta.pilares,
                x_start=x_cargas,
                y_start=y_topo_tabelas,
                dados_porlid=planta.dados_porlid,
                escala=escala,
            )

            # 3. Notas, Convenção de Sinais e Legenda (diretamente abaixo de Baricentros e Cargas)
            y_topo_notas = min(y_fim_bar, y_fim_cargas) - (70.0 * fator_esc)
            x_notas = x_start_dir
            y_fim_notas = self._desenhar_notas_e_legendas(
                dwg, x_start=x_notas, y_start=y_topo_notas, dados_porlid=planta.dados_porlid, escala=escala, origem_cotas=origem_cotas
            )'''

assert old_lateral_calls in code, "old_lateral_calls not found"
code = code.replace(old_lateral_calls, new_lateral_calls, 1)

# 6. Update _desenhar_pilares_locacao signature and body
old_des_pil_def = '''    def _desenhar_pilares_locacao(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        bounds: Tuple[float, float, float, float],
        escala: int = 50,
    ):'''

new_des_pil_def = '''    def _desenhar_pilares_locacao(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        bounds: Tuple[float, float, float, float],
        escala: int = 50,
        origem_cotas: Optional[Tuple[float, float]] = None,
    ):'''

assert old_des_pil_def in code, "old_des_pil_def not found"
code = code.replace(old_des_pil_def, new_des_pil_def, 1)

# 7. Update vector fallback cotas in _desenhar_pilares_locacao
old_cota_fallback = '''                if emitir_cota_y:
                    val_y_num = round(cg.y, 1)
                    val_y_str = f"{val_y_num:.1f}".rstrip("0").rstrip(".") if "." in f"{val_y_num:.1f}" else f"{val_y_num:.0f}"
                    # Triângulo indicador apontando para baixo sobre a linha horizontal
                    dwg.draw.Line(xv_y, yv_y, xv_y + (7.5 * fator_esc), yv_y + (15.0 * fator_esc))
                    dwg.draw.Line(xv_y + (7.5 * fator_esc), yv_y + (15.0 * fator_esc), xv_y - (7.5 * fator_esc), yv_y + (15.0 * fator_esc))
                    dwg.draw.Line(xv_y - (7.5 * fator_esc), yv_y + (15.0 * fator_esc), xv_y, yv_y)
                    # Haste vertical
                    dwg.draw.Line(xv_y, yv_y + (15.0 * fator_esc), xv_y, yv_y + (22.5 * fator_esc))
                    # Prateleira horizontal à direita com comprimento proporcional ao texto
                    tam_prat_y = max(50.0 * fator_esc, len(val_y_str) * h_cota)
                    dwg.draw.Line(xv_y, yv_y + (22.5 * fator_esc), xv_y + tam_prat_y, yv_y + (22.5 * fator_esc))
                    # Texto da cota Y (horizontal)
                    dwg.draw.Text(xv_y, yv_y + (22.5 * fator_esc) + (3.4 * fator_esc), h_cota, 0.0, val_y_str)

                if emitir_cota_x:
                    val_x_num = round(cg.x, 1)
                    val_x_str = f"{val_x_num:.1f}".rstrip("0").rstrip(".") if "." in f"{val_x_num:.1f}" else f"{val_x_num:.0f}"'''

new_cota_fallback = '''                rx = float(origem_cotas[0]) if origem_cotas else 0.0
                ry = float(origem_cotas[1]) if origem_cotas else 0.0
                if emitir_cota_y:
                    val_y_num = round(cg.y - ry, 1)
                    if abs(val_y_num) < 1e-4:
                        val_y_num = 0.0
                    val_y_str = f"{val_y_num:.1f}".rstrip("0").rstrip(".") if "." in f"{val_y_num:.1f}" else f"{val_y_num:.0f}"
                    # Triângulo indicador apontando para baixo sobre a linha horizontal
                    dwg.draw.Line(xv_y, yv_y, xv_y + (7.5 * fator_esc), yv_y + (15.0 * fator_esc))
                    dwg.draw.Line(xv_y + (7.5 * fator_esc), yv_y + (15.0 * fator_esc), xv_y - (7.5 * fator_esc), yv_y + (15.0 * fator_esc))
                    dwg.draw.Line(xv_y - (7.5 * fator_esc), yv_y + (15.0 * fator_esc), xv_y, yv_y)
                    # Haste vertical
                    dwg.draw.Line(xv_y, yv_y + (15.0 * fator_esc), xv_y, yv_y + (22.5 * fator_esc))
                    # Prateleira horizontal à direita com comprimento proporcional ao texto
                    tam_prat_y = max(50.0 * fator_esc, len(val_y_str) * h_cota)
                    dwg.draw.Line(xv_y, yv_y + (22.5 * fator_esc), xv_y + tam_prat_y, yv_y + (22.5 * fator_esc))
                    # Texto da cota Y (horizontal)
                    dwg.draw.Text(xv_y, yv_y + (22.5 * fator_esc) + (3.4 * fator_esc), h_cota, 0.0, val_y_str)

                if emitir_cota_x:
                    val_x_num = round(cg.x - rx, 1)
                    if abs(val_x_num) < 1e-4:
                        val_x_num = 0.0
                    val_x_str = f"{val_x_num:.1f}".rstrip("0").rstrip(".") if "." in f"{val_x_num:.1f}" else f"{val_x_num:.0f}"'''

assert old_cota_fallback in code, "old_cota_fallback not found"
code = code.replace(old_cota_fallback, new_cota_fallback, 1)

# 8. Update _desenhar_tabela_baricentros signature
old_bar_def = '''    def _desenhar_tabela_baricentros(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        x_start: float,
        y_start: float,
        escala: int = 50,
    ) -> Tuple[float, float]:'''

new_bar_def = '''    def _desenhar_tabela_baricentros(
        self,
        dwg: TQSDwg.Dwg,
        pilares: List[PilarFundacao],
        x_start: float,
        y_start: float,
        escala: int = 50,
        origem_cotas: Optional[Tuple[float, float]] = None,
    ) -> Tuple[float, float]:'''

assert old_bar_def in code, "old_bar_def not found"
code = code.replace(old_bar_def, new_bar_def, 1)

# 9. Update _desenhar_tabela_baricentros coordinate values (Table 1 and Table 2)
old_t1_vals = '''            px = p_ord_x[i]
            py = p_ord_y[i]
            nome_px = str(px.nome)
            val_x = f"{px.baricentro.x:.1f}" if px.baricentro else "0.0"
            nome_py = str(py.nome)
            val_y = f"{py.baricentro.y:.1f}" if py.baricentro else "0.0"'''

new_t1_vals = '''            rx = float(origem_cotas[0]) if origem_cotas else 0.0
            ry = float(origem_cotas[1]) if origem_cotas else 0.0
            px = p_ord_x[i]
            py = p_ord_y[i]
            nome_px = str(px.nome)
            vx = (px.baricentro.x - rx) if px.baricentro else 0.0
            if abs(vx) < 1e-4:
                vx = 0.0
            val_x = f"{vx:.1f}"
            nome_py = str(py.nome)
            vy = (py.baricentro.y - ry) if py.baricentro else 0.0
            if abs(vy) < 1e-4:
                vy = 0.0
            val_y = f"{vy:.1f}"'''

assert old_t1_vals in code, "old_t1_vals not found"
code = code.replace(old_t1_vals, new_t1_vals, 1)

old_t2_vals = '''            p = p_ord_nome[i]
            nome_p = str(p.nome)
            val_x = f"{p.baricentro.x:.1f}" if p.baricentro else "0.0"
            val_y = f"{p.baricentro.y:.1f}" if p.baricentro else "0.0"'''

new_t2_vals = '''            p = p_ord_nome[i]
            nome_p = str(p.nome)
            vx = (p.baricentro.x - rx) if p.baricentro else 0.0
            if abs(vx) < 1e-4:
                vx = 0.0
            val_x = f"{vx:.1f}"
            vy = (p.baricentro.y - ry) if p.baricentro else 0.0
            if abs(vy) < 1e-4:
                vy = 0.0
            val_y = f"{vy:.1f}"'''

assert old_t2_vals in code, "old_t2_vals not found"
code = code.replace(old_t2_vals, new_t2_vals, 1)

# 10. Update _desenhar_notas_e_legendas signature and note for origin
old_not_def = '''    def _desenhar_notas_e_legendas(
        self,
        dwg: TQSDwg.Dwg,
        x_start: float,
        y_start: float,
        dados_porlid: Optional[Dict[str, Any]] = None,
        escala: int = 50,
    ) -> float:'''

new_not_def = '''    def _desenhar_notas_e_legendas(
        self,
        dwg: TQSDwg.Dwg,
        x_start: float,
        y_start: float,
        dados_porlid: Optional[Dict[str, Any]] = None,
        escala: int = 50,
        origem_cotas: Optional[Tuple[float, float]] = None,
    ) -> float:'''

assert old_not_def in code, "old_not_def not found"
code = code.replace(old_not_def, new_not_def, 1)

old_not_top = '''        # Linhas de cabeçalho fixas
        dwg.draw.level = 250
        dwg.draw.Text(x_start, curr_y, h_txt, 0.0, "- Esforços com valores característicos.")
        curr_y -= dy_linha'''

new_not_top = '''        # Linhas de cabeçalho fixas
        dwg.draw.level = 250
        dwg.draw.Text(x_start, curr_y, h_txt, 0.0, "- Esforços com valores característicos.")
        curr_y -= dy_linha

        if origem_cotas:
            rx = float(origem_cotas[0])
            ry = float(origem_cotas[1])
            dwg.draw.level = 250
            dwg.draw.Text(
                x_start,
                curr_y,
                h_txt,
                0.0,
                f"- Origem (0,0) das cotas e coordenadas de locação referenciada ao ponto (X={rx:.1f}, Y={ry:.1f}) cm.",
            )
            curr_y -= dy_linha'''

assert old_not_top in code, "old_not_top not found"
code = code.replace(old_not_top, new_not_top, 1)

# Also in _desenhar_pilares_locacao, draw the origin benchmark marker if origem_cotas is defined
old_fim_pilares = '''            dwg.draw.level = 12
            dim_str = f"{int(round(geom.b))}x{int(round(geom.h))}"
            dwg.draw.Text(xd, yd, h_pilar_dim, 0.0, dim_str)'''

new_fim_pilares = '''            dwg.draw.level = 12
            dim_str = f"{int(round(geom.b))}x{int(round(geom.h))}"
            dwg.draw.Text(xd, yd, h_pilar_dim, 0.0, dim_str)

        # 5. Marcador de Origem (0,0) na planta de locação se especificado
        if origem_cotas:
            rx = float(origem_cotas[0])
            ry = float(origem_cotas[1])
            # Eixos em cruz (Nível 21)
            dwg.draw.level = 21
            tam_cruz = 50.0 * fator_esc
            dwg.draw.Line(rx - tam_cruz, ry, rx + tam_cruz, ry)
            dwg.draw.Line(rx, ry - tam_cruz, rx, ry + tam_cruz)
            dwg.draw.Circle(rx, ry, 12.0 * fator_esc)
            dwg.draw.Circle(rx, ry, 4.0 * fator_esc)
            # Texto identificador da Origem
            dwg.draw.level = 250
            h_orig_txt = max(14.0 * fator_esc, h_min_normativo)
            dwg.draw.Text(rx + (16.0 * fator_esc), ry + (8.0 * fator_esc), h_orig_txt, 0.0, "ORIGEM (0,0)")'''

assert old_fim_pilares in code, "old_fim_pilares not found"
code = code.replace(old_fim_pilares, new_fim_pilares, 1)

with open("src/drawing/tqs_dwg_builder.py", "w", encoding="utf-8") as f:
    f.write(code)

print("tqs_dwg_builder.py updated successfully!")
