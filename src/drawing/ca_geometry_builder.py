import os
import shutil
from datetime import datetime
from collections import Counter
from typing import Dict, Any, Optional, List, Tuple

from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64

class CAGeometryBuilder:
    """
    Construtor e montador executivo de pranchas de Geometria de Concreto Armado (TQS CA).
    Combina a forma estrutural recém-processada (FOR000x.DWG) com a prancha executiva
    (Moldura ABNT Nível 100, Título Executivo Níveis 222/250 e Notas/Legendas Técnicas),
    gerando o GEO_<PAVIMENTO>.DWG final com fidelidade estrutural de 100%.
    """

    def __init__(self):
        configurar_ambiente_tqs_64()
        from TQS import TQSDwg
        self.TQSDwg = TQSDwg

    def montar_geometria(
        self,
        pasta_pavimento: str,
        nome_pavimento: str,
        nome_edificio: str = "",
        for_dwg_nome: Optional[str] = None,
        geo_dwg_nome: Optional[str] = None,
        escala: float = 50.0
    ) -> Dict[str, Any]:
        """
        Executa a montagem completa da geometria executiva do pavimento:
        1. Localiza FOR000x.DWG e GEO_*.DWG na pasta do pavimento.
        2. Realiza backup preventivo de GEO_*.DWG.
        3. Extrai moldura, título e notas técnicas da prancha de referência existente.
        4. Clona a base pura de FOR000x.DWG para GEO_*.DWG.
        5. Purga os cabeçalhos provisórios do TQS.
        6. Insere a moldura, o título executivo e as notas/legendas técnicas.
        7. Ajusta a escala e audita a integridade geométrica.
        """
        if not os.path.exists(pasta_pavimento):
            raise FileNotFoundError(f"Pasta do pavimento não encontrada: {pasta_pavimento}")

        # Localiza arquivo FOR*.DWG
        if not for_dwg_nome:
            cand_for = [f for f in os.listdir(pasta_pavimento) if f.upper().startswith("FOR") and f.upper().endswith(".DWG") and not f.upper().endswith("M.DWG")]
            if not cand_for:
                raise FileNotFoundError(f"Nenhum arquivo FOR*.DWG encontrado em {pasta_pavimento}")
            for_dwg_nome = sorted(cand_for)[0]
        
        caminho_for = os.path.join(pasta_pavimento, for_dwg_nome)
        if not os.path.exists(caminho_for):
            raise FileNotFoundError(f"Arquivo FOR não encontrado: {caminho_for}")

        # Determina candidatos de GEO_*.DWG na pasta
        cand_geo = [f for f in os.listdir(pasta_pavimento) if f.upper().startswith("GEO") and f.upper().endswith(".DWG") and "BKP" not in f.upper() and "TEST" not in f.upper()]
        ativos = [f for f in cand_geo if not any(r in f.upper() for r in ["-R", "_R"])]

        # Determina arquivo de referência existente para extrair Moldura, Título e Notas
        caminho_ref = None
        if ativos:
            caminho_ref = os.path.join(pasta_pavimento, ativos[0])
        elif cand_geo:
            caminho_ref = os.path.join(pasta_pavimento, cand_geo[0])

        if not geo_dwg_nome:
            if ativos:
                geo_dwg_nome = ativos[0]
            elif cand_geo:
                geo_dwg_nome = cand_geo[0]
            else:
                geo_dwg_nome = f"GEO_{nome_pavimento.replace('PISO DO ', '')}.DWG"

        caminho_geo = os.path.join(pasta_pavimento, geo_dwg_nome)
        if not caminho_ref:
            caminho_ref = caminho_geo

        # 1. Backup Preventivo
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bkp_path = os.path.join(pasta_pavimento, f"{os.path.splitext(geo_dwg_nome)[0]}_BKP_{ts}.DWG")
        backup_criado = False
        if os.path.exists(caminho_geo):
            shutil.copy2(caminho_geo, bkp_path)
            backup_criado = True

        # 2. Coleta de elementos de prancha (Moldura, Título, Notas) da prancha de referência
        moldura_elems = []
        title_elems = []
        notes_elems = []

        if os.path.exists(caminho_ref):
            dwg_src = self.TQSDwg.Dwg()
            dwg_src.file.Open(caminho_ref)
            it = dwg_src.iterator
            it.Begin()

            while True:
                if it.GetElementReadPosition():
                    lvl = it.level
                    name = it.elementName
                    x = it.x1
                    y = it.y1
                    is_zero = (x == 0.0 and y == 0.0 and name in ["Fim de bloco", "Fim de objeto", "Objeto"])

                    # Moldura 180-70 (Nível 100)
                    if lvl == 100:
                        if name == "Linha":
                            moldura_elems.append(("Linha", it.color, it.style, it.x1, it.y1, it.x2, it.y2))
                        elif name == "Texto":
                            moldura_elems.append(("Texto", it.color, it.style, it.x1, it.y1, it.textHeight, it.textAngle, it.text))

                    # Título Executivo
                    elif lvl in [222, 250] and x <= 11000 and y >= -2300:
                        if name == "Texto":
                            title_elems.append(("Texto", lvl, it.color, it.style, it.x1, it.y1, it.textHeight, it.textAngle, it.text))

                    # Notas Técnicas e Legendas (X >= 16200 e Y >= -2350)
                    elif x >= 16200 and y >= -2350 and lvl != 100 and not is_zero:
                        item = {"name": name, "level": lvl, "color": it.color, "style": it.style}
                        if name == "Linha":
                            item["coords"] = (it.x1, it.y1, it.x2, it.y2)
                            notes_elems.append(item)
                        elif name == "Texto":
                            item["coords"] = (it.x1, it.y1, it.textHeight, it.textAngle, it.text)
                            notes_elems.append(item)
                        elif name == "Circulo":
                            item["coords"] = (it.xc, it.yc, it.radius)
                            notes_elems.append(item)
                        elif name in ["Polyline", "Indefinido"]:
                            item["name"] = "Polyline"
                            pts = [it.GetPolylinePt(i) for i in range(it.xySize)]
                            item["pts"] = pts
                            notes_elems.append(item)
                        elif name == "Bloco":
                            item["block"] = (it.blockName, it.x1, it.y1, it.xScale, it.yScale, it.insertAngle)
                            notes_elems.append(item)
                if not it.Next():
                    break
            dwg_src.file.Close()

        # 3. Base pura a partir do FOR000x.DWG
        shutil.copy2(caminho_for, caminho_geo)
        dwg_geo = self.TQSDwg.Dwg()
        dwg_geo.file.Open(caminho_geo)

        # 4. Purgar cabeçalho provisório do TQS
        it_g = dwg_geo.iterator
        it_g.Begin()
        to_erase = []
        while True:
            pos = it_g.GetElementReadPosition()
            if pos:
                txt = getattr(it_g, "text", "")
                if any(k in txt for k in ["Planta PISO", "Escala 1:50", "00-PISO", "01-PISO", "02-PISO", "03-PISO"]) and it_g.x1 < 11000 and it_g.y1 >= -2450:
                    to_erase.append(pos)
                elif 8600 <= it_g.x1 <= 9250 and -3360 <= it_g.y1 <= -3200:
                    to_erase.append(pos)
            if not it_g.Next():
                break

        for p in reversed(to_erase):
            dwg_geo.edit.Erase(p)

        # 5. Inserir elementos de prancha
        if moldura_elems:
            dwg_geo.draw.level = 100
            for m in moldura_elems:
                dwg_geo.draw.color = m[1]
                dwg_geo.draw.style = m[2]
                if m[0] == "Linha":
                    dwg_geo.draw.Line(m[3], m[4], m[5], m[6])
                elif m[0] == "Texto":
                    dwg_geo.draw.Text(m[3], m[4], m[5], m[6], m[7])

        if title_elems:
            for t in title_elems:
                dwg_geo.draw.level = t[1]
                dwg_geo.draw.color = t[2]
                dwg_geo.draw.style = t[3]
                dwg_geo.draw.Text(t[4], t[5], t[6], t[7], t[8])

        if notes_elems:
            for n in notes_elems:
                dwg_geo.draw.level = n["level"]
                dwg_geo.draw.color = n["color"]
                dwg_geo.draw.style = n["style"]
                if n["name"] == "Linha":
                    x1, y1, x2, y2 = n["coords"]
                    dwg_geo.draw.Line(x1, y1, x2, y2)
                elif n["name"] == "Texto":
                    x, y, h, ang, txt = n["coords"]
                    dwg_geo.draw.Text(x, y, h, ang, txt)
                elif n["name"] == "Circulo":
                    xc, yc, r = n["coords"]
                    dwg_geo.draw.Circle(xc, yc, r)
                elif n["name"] == "Polyline":
                    dwg_geo.draw.PolyStart()
                    dwg_geo.draw.PolyEnterXY([list(p) for p in n["pts"]])
                    dwg_geo.draw.Polyline()
                elif n["name"] == "Bloco":
                    bname, bx, by, escx, escy, bang = n["block"]
                    dwg_geo.draw.BlockInsert(bname, bx, by, escx, escy, bang)

        # Garante propriedades do desenho: Formas -> Planta de formas
        dwg_geo.settings.systemId = 2  # Formas (IEDFOR)
        dwg_geo.settings.subSystemId = 2  # Planta de formas
        dwg_geo.settings.scale = escala
        dwg_geo.file.Save()
        dwg_geo.file.Close()

        # 6. Auditoria de Integridade e Qualidade
        dwg_chk = self.TQSDwg.Dwg()
        dwg_chk.file.Open(caminho_geo)
        it_chk = dwg_chk.iterator
        it_chk.Begin()

        tot_elems = 0
        lvls_cnt = {}
        vigas_labels = []
        dim_labels = []
        form_lines = []

        while True:
            if it_chk.GetElementReadPosition():
                tot_elems += 1
                lvl = it_chk.level
                lvls_cnt[lvl] = lvls_cnt.get(lvl, 0) + 1

                if it_chk.y1 < -2350 and lvl != 100:
                    if it_chk.elementName == "Linha":
                        p1 = (round(it_chk.x1, 1), round(it_chk.y1, 1))
                        p2 = (round(it_chk.x2, 1), round(it_chk.y2, 1))
                        form_lines.append((min(p1, p2), max(p1, p2)))
                    elif it_chk.elementName == "Texto":
                        if lvl == 8:
                            vigas_labels.append(it_chk.text)
                        elif lvl == 11:
                            dim_labels.append(it_chk.text)
            if not it_chk.Next():
                break
        dwg_chk.file.Close()

        c_lines = Counter(form_lines)
        dups_lines = [k for k, v in c_lines.items() if v > 1]

        return {
            "status": "sucesso",
            "sucesso": True,
            "caminho_geo": caminho_geo,
            "caminho_for": caminho_for,
            "backup_criado": bkp_path if backup_criado else None,
            "escala": escala,
            "auditoria": {
                "total_elementos": tot_elems,
                "niveis": lvls_cnt,
                "total_vigas": len(vigas_labels),
                "vigas_amostra": sorted(vigas_labels)[:15],
                "total_dimensoes": len(dim_labels),
                "linhas_estruturais": len(form_lines),
                "linhas_duplicadas": len(dups_lines),
                "moldura_elementos": lvls_cnt.get(100, 0),
                "notas_elementos": len(notes_elems),
            }
        }
