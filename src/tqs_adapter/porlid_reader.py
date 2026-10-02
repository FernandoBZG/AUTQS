import os
import re
from typing import Dict, Any, List, Optional, Tuple

from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
configurar_ambiente_tqs_64()
from TQS import TQSDwg


class TQSPorlidReader:
    """
    Leitor especializado da tabela de cargas oficial do TQS (PORLID).
    Extrai TODOS os casos e combinações críticas ativas no edifício
    (ex: FZ MAX, MX MAX, MY MAX, FZ MIN, MX MIN, MY MIN, etc.)
    e os esforços característicos (Fz, Fx, Fy, Mx, My, Mz) para cada
    elemento de fundação a partir de ESPACIAL/PORLID.TXT ou ESPACIAL/PORLID.DWG.
    """

    def __init__(self, caminho_edificio: str):
        self.caminho_edificio = caminho_edificio
        self.caminho_espacial = os.path.join(caminho_edificio, "ESPACIAL")
        self.caminho_porlid_dwg = os.path.join(self.caminho_espacial, "PORLID.DWG")
        self.caminho_porlid_txt = os.path.join(self.caminho_espacial, "PORLID.TXT")
        self.caminho_porlid3_dat = os.path.join(self.caminho_espacial, "PORLID3.DAT")

    def existe_porlid(self) -> bool:
        return os.path.exists(self.caminho_porlid_dwg) or os.path.exists(self.caminho_porlid_txt)

    def extrair_tabela_porlid(self) -> Dict[str, Any]:
        """
        Lê e estrutura os dados completos de TODOS os casos de ESPACIAL/PORLID.TXT ou ESPACIAL/PORLID.DWG.
        Retorna dicionário contendo:
          - 'num_casos': Quantidade total de casos críticos extraídos
          - 'casos': Lista de dicionários de cada caso contendo:
              - 'id': Número sequencial do caso (1, 2, ...)
              - 'nome': Nome curto (ex: 'CASO 1 - FZ MAX')
              - 'titulo': Título descritivo completo da combinação crítica
              - 'colunas': ['Elem', 'Fz', 'Fx', 'Fy', 'Mx', 'My', 'Mz']
              - 'unidades': ['', 'tf', 'tf', 'tf', 'tfm', 'tfm', 'tfm']
              - 'linhas': Lista de linhas de dados [elem, fz, fx, fy, mx, my, mz]
          - 'titulo': Título do caso 1 (para retrocompatibilidade)
          - 'colunas': ['Elem', 'Fz', 'Fx', 'Fy', 'Mx', 'My', 'Mz']
          - 'unidades': ['', 'tf', 'tf', 'tf', 'tfm', 'tfm', 'tfm']
          - 'linhas': Linhas de dados do caso 1 (para retrocompatibilidade)
          - 'total_elementos': Quantidade de elementos na tabela
        """
        palavras_cabecalho = ["ELEM", "PILAR", "CASO", "FZ", "FX", "FY", "MX", "MY", "MZ", "TF", "TFM"]

        # -------------------------------------------------------------
        # 1. Estratégia Principal: Leitura de PORLID.TXT (quando exportado/gerado)
        # -------------------------------------------------------------
        if os.path.exists(self.caminho_porlid_txt):
            try:
                with open(self.caminho_porlid_txt, "r", encoding="cp1252", errors="replace") as f:
                    raw_lines = [l.rstrip("\r\n") for l in f.readlines() if l.strip()]

                if len(raw_lines) >= 3:
                    line0_parts = [p.strip() for p in raw_lines[0].split("\t")]
                    line1_parts = [p.strip() for p in raw_lines[1].split("\t")]

                    # Identifica todos os índices das colunas Fz na linha 1
                    fzs_in_line1 = [idx for idx, val in enumerate(line1_parts) if val.upper() == "FZ"]
                    num_casos = len(fzs_in_line1)

                    if num_casos == 0:
                        sample_parts = [p.strip() for p in raw_lines[2].split("\t")]
                        num_casos = max(1, (len(sample_parts) - 1) // 6)
                        fzs_in_line1 = [1 + 6 * k for k in range(num_casos)]

                    casos = []
                    for k, col_fz in enumerate(fzs_in_line1):
                        # Título na linha 0
                        title = ""
                        if col_fz < len(line0_parts) and line0_parts[col_fz] and line0_parts[col_fz] != "-":
                            title = line0_parts[col_fz]
                        elif (1 + 6 * k) < len(line0_parts) and line0_parts[1 + 6 * k] and line0_parts[1 + 6 * k] != "-":
                            title = line0_parts[1 + 6 * k]

                        if not title:
                            title = f"CASO {k+1}"

                        # Extrai prefixo curto (ex: 'FZ MAX', 'MX MAX', etc.)
                        prefix = title.split("-")[0].strip() if "-" in title else title
                        if prefix and not prefix.upper().startswith("CASO"):
                            nome_caso = f"CASO {k+1} - {prefix}"
                        else:
                            nome_caso = f"CASO {k+1}"

                        linhas_caso = []
                        for l in raw_lines[2:]:
                            parts = [p.strip() for p in l.split("\t")]
                            if not parts:
                                continue
                            elem = parts[0]
                            # Valida se é um elemento estrutural real
                            if re.search(r'[A-Za-z]', elem) and elem.upper() not in palavras_cabecalho:
                                vals = parts[col_fz : col_fz + 6]
                                while len(vals) < 6:
                                    vals.append("0")
                                linhas_caso.append([elem] + vals[:6])

                        if linhas_caso:
                            casos.append({
                                "id": k + 1,
                                "nome": nome_caso,
                                "titulo": title,
                                "colunas": ["Elem", "Fz", "Fx", "Fy", "Mx", "My", "Mz"],
                                "unidades": ["", "tf", "tf", "tf", "tfm", "tfm", "tfm"],
                                "linhas": linhas_caso,
                            })

                    if casos:
                        return {
                            "sucesso": True,
                            "num_casos": len(casos),
                            "casos": casos,
                            "titulo": casos[0]["titulo"],
                            "colunas": ["Elem", "Fz", "Fx", "Fy", "Mx", "My", "Mz"],
                            "unidades": ["", "tf", "tf", "tf", "tfm", "tfm", "tfm"],
                            "linhas": casos[0]["linhas"],
                            "total_elementos": len(casos[0]["linhas"]),
                        }
            except Exception:
                pass

        # -------------------------------------------------------------
        # 2. Estratégia Vetorial: Leitura direta de ESPACIAL/PORLID.DWG
        # -------------------------------------------------------------
        if not os.path.exists(self.caminho_porlid_dwg):
            return {
                "sucesso": False,
                "erro": f"Arquivo PORLID não encontrado em: {self.caminho_espacial}",
                "num_casos": 0,
                "casos": [],
                "linhas": [],
            }

        dwg = TQSDwg.Dwg(pedmv=0)
        res = dwg.file.Open(self.caminho_porlid_dwg)
        if res != 0:
            return {
                "sucesso": False,
                "erro": f"Falha ao abrir PORLID.DWG (código {res})",
                "num_casos": 0,
                "casos": [],
                "linhas": [],
            }

        texts = []
        it = dwg.iterator
        it.Begin()
        while True:
            pos = it.GetElementReadPosition()
            if pos and it.elementName == "Texto" and it.text and it.text.strip():
                texts.append((round(it.x1, 2), round(it.y1, 2), it.text.strip()))
            if not it.Next():
                break
        dwg.file.Close()

        fz_instances = sorted([t for t in texts if t[2] == 'Fz'], key=lambda t: t[0])
        if not fz_instances:
            return {
                "sucesso": False,
                "erro": "Nenhum cabeçalho 'Fz' detectado em PORLID.DWG",
                "num_casos": 0,
                "casos": [],
                "linhas": [],
            }

        num_casos = len(fz_instances)
        delta_x = 1000.0 if num_casos == 1 else (fz_instances[1][0] - fz_instances[0][0])
        casos = []

        for k, fz in enumerate(fz_instances):
            x_fz = fz[0]
            y_fz = fz[1]
            x_left = -999999.0 if k == 0 else (x_fz - 0.25 * delta_x)
            x_right = 999999.0 if k == num_casos - 1 else (x_fz + 0.75 * delta_x)
            case_texts = [t for t in texts if x_left <= t[0] < x_right]

            # Detecta título do caso crítico acima da linha Fz
            titles = [
                t for t in case_texts
                if t[1] > y_fz and any(kw in t[2].upper() for kw in ["CASO", "MAX", "MIN", "VERIF", "ELU", "ESTADO"])
            ]
            titles_sorted = sorted(titles, key=lambda t: (-t[1], t[0]))
            clean_titles = []
            seen = set()
            for t in titles_sorted:
                txt = t[2].strip()
                if txt not in seen and txt.upper() not in palavras_cabecalho:
                    seen.add(txt)
                    clean_titles.append(txt)

            case_title = " - ".join(clean_titles) if clean_titles else f"CASO {k+1}"
            prefix = case_title.split("-")[0].strip() if "-" in case_title else case_title
            if prefix and not prefix.upper().startswith("CASO"):
                nome_caso = f"CASO {k+1} - {prefix}"
            else:
                nome_caso = case_title

            # Agrupa linhas de dados abaixo do cabeçalho
            y_step = 0.1 if abs(y_fz) < 100 else 2.0
            rows_by_y = {}
            for t in case_texts:
                if t[1] < y_fz - y_step:
                    y_bin = round(round(t[1] / y_step) * y_step, 2)
                    if y_bin not in rows_by_y:
                        rows_by_y[y_bin] = []
                    rows_by_y[y_bin].append(t)

            linhas_caso = []
            for y_val in sorted(rows_by_y.keys(), reverse=True):
                items = sorted(rows_by_y[y_val], key=lambda x: x[0])
                if not items:
                    continue
                elem = items[0][2]
                if re.search(r'[A-Za-z]', elem) and elem.upper() not in palavras_cabecalho:
                    vals = [it[2] for it in items[1:7]]
                    while len(vals) < 6:
                        vals.append("0")
                    linhas_caso.append([elem] + vals[:6])

            if linhas_caso:
                casos.append({
                    "id": k + 1,
                    "nome": nome_caso,
                    "titulo": case_title,
                    "colunas": ["Elem", "Fz", "Fx", "Fy", "Mx", "My", "Mz"],
                    "unidades": ["", "tf", "tf", "tf", "tfm", "tfm", "tfm"],
                    "linhas": linhas_caso,
                })

        if not casos:
            return {
                "sucesso": False,
                "erro": "Falha ao extrair linhas de elementos em PORLID.DWG",
                "num_casos": 0,
                "casos": [],
                "linhas": [],
            }

        return {
            "sucesso": True,
            "num_casos": len(casos),
            "casos": casos,
            "titulo": casos[0]["titulo"],
            "colunas": ["Elem", "Fz", "Fx", "Fy", "Mx", "My", "Mz"],
            "unidades": ["", "tf", "tf", "tf", "tfm", "tfm", "tfm"],
            "linhas": casos[0]["linhas"],
            "total_elementos": len(casos[0]["linhas"]),
        }
