import os
import re
from typing import List, Dict, Optional, Tuple, Any
from src.core.models import (
    PilarFundacao,
    GeometriaPilar,
    TipoSecao,
    Baricentro,
    EsforcosFundacao,
    PlantaDeCargasModel,
)
from src.skills.case_01_planta_cargas.geometry import (
    calcular_baricentro_poligono,
    calcular_baricentro_pilar,
)

class TQSBuildingReader:
    """
    Leitor de dados e esforços reais de edifícios do TQS V25.
    Extrai geometria dos pilares na fundação (CARDWG2.LST) e esforços
    característicos do pórtico espacial (PORLIS2.LST).
    """

    @classmethod
    def listar_edificios_disponiveis(cls, pastas_raiz: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Varre todos os diretórios padrão do TQS (C:\\TQS, D:\\TQS, etc.)
        e retorna uma lista detalhada dos edifícios disponíveis e seu status de processamento.
        """
        if not pastas_raiz:
            pastas_raiz = [r"C:\TQS", r"D:\TQS"]
        
        resultado = []
        vistos = set()

        for raiz in pastas_raiz:
            if not os.path.exists(raiz):
                continue
            try:
                itens = os.listdir(raiz)
            except Exception:
                continue

            for item in itens:
                caminho = os.path.join(raiz, item)
                if not os.path.isdir(caminho) or item.startswith("000"):
                    continue
                if caminho.lower() in vistos:
                    continue
                vistos.add(caminho.lower())

                espacial_path = os.path.join(caminho, "ESPACIAL")
                tem_espacial = os.path.exists(espacial_path)
                tem_cardwg = tem_espacial and (
                    os.path.exists(os.path.join(espacial_path, "CARDWG2.LST"))
                    or os.path.exists(os.path.join(espacial_path, "CARDWG.LST"))
                )
                tem_porlis = tem_espacial and (
                    os.path.exists(os.path.join(espacial_path, "PORLIS2.LST"))
                    or os.path.exists(os.path.join(espacial_path, "PORLIS.LST"))
                )

                resultado.append({
                    "nome": item,
                    "caminho": caminho,
                    "disco": os.path.splitdrive(caminho)[0],
                    "processado": tem_cardwg and tem_porlis,
                    "tem_espacial": tem_espacial,
                })
        return resultado

    def __init__(self, caminho_ou_nome_edificio: str, pasta_raiz_tqs: str = r"C:\TQS"):
        # Resolve o caminho completo da pasta do edifício
        if os.path.isabs(caminho_ou_nome_edificio) and os.path.exists(caminho_ou_nome_edificio):
            self.caminho_edificio = caminho_ou_nome_edificio
            self.nome_edificio = os.path.basename(caminho_ou_nome_edificio)
        else:
            # Busca dentro de C:\TQS ou D:\TQS
            caminho_direto = os.path.join(pasta_raiz_tqs, caminho_ou_nome_edificio)
            if os.path.exists(caminho_direto):
                self.caminho_edificio = caminho_direto
                self.nome_edificio = caminho_ou_nome_edificio
            else:
                # Busca por substring (ex: "054")
                self.caminho_edificio = self._localizar_por_termo(caminho_ou_nome_edificio, pasta_raiz_tqs)
                self.nome_edificio = os.path.basename(self.caminho_edificio)

    def _localizar_por_termo(self, termo: str, pasta_raiz: str) -> str:
        termo_limpo = termo.strip().lower()
        disponiveis = self.listar_edificios_disponiveis([pasta_raiz, r"D:\TQS", r"C:\TQS"])

        # 1. Procura match exato no nome
        for ed in disponiveis:
            if termo_limpo == ed["nome"].lower():
                return ed["caminho"]

        # 2. Procura por substring no nome
        for ed in disponiveis:
            if termo_limpo in ed["nome"].lower():
                return ed["caminho"]

        nomes = [ed["nome"] for ed in disponiveis]
        raise FileNotFoundError(
            f"Edifício correspondente a '{termo}' não foi localizado no TQS.\n"
            f"Edifícios detectados no sistema:\n" +
            "\n".join([f"  - {n}" for n in nomes])
        )

    def _ler_reacoes_porlis2(self) -> Dict[str, EsforcosFundacao]:
        """
        Lê as reações nos apoios da fundação (Fx, Fy, Fz=Nk, Mx, My, Mz) a partir de PORLIS2.LST.
        """
        reacoes: Dict[str, EsforcosFundacao] = {}
        caminho_porlis2 = os.path.join(self.caminho_edificio, "ESPACIAL", "PORLIS2.LST")
        
        if not os.path.exists(caminho_porlis2):
            return reacoes

        with open(caminho_porlis2, "r", encoding="latin1", errors="ignore") as f:
            lines = f.readlines()

        em_tabela = False
        for l in lines:
            if "sistema GLOBAL" in l:
                em_tabela = True
                continue
            if em_tabela and "====" in l:
                continue
            if em_tabela:
                # Se encontrar linha em branco após ter lido linhas, sai
                if not l.strip() and len(reacoes) > 0:
                    break
                m = re.match(
                    r"^\s*(P\d+)\s+(\d+)\s+(\d+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)",
                    l,
                )
                if m:
                    nome_pilar = m.group(1)
                    fx = float(m.group(4))
                    fy = float(m.group(5))
                    fz = float(m.group(6)) # Carga vertical de compressão (Nk)
                    mx = float(m.group(7))
                    my = float(m.group(8))
                    
                    reacoes[nome_pilar] = EsforcosFundacao(
                        nk_max=fz,
                        nk_min=fz * 0.85, # Estimativa conservadora de alívio se caso único
                        mxk=mx,
                        myk=my,
                        hx=fx,
                        hy=fy,
                        caso_critico="Caso 1 - Pórtico Espacial (Global)",
                    )
        return reacoes

    def _ler_pilares_cardwg2(self) -> List[PilarFundacao]:
        """
        Lê a geometria e coordenadas dos pilares na fundação a partir de CARDWG2.LST
        ou CARDWG.LST de forma universal.
        """
        pilares: List[PilarFundacao] = []
        caminho_cardwg2 = os.path.join(self.caminho_edificio, "ESPACIAL", "CARDWG2.LST")
        if not os.path.exists(caminho_cardwg2):
            caminho_cardwg2 = os.path.join(self.caminho_edificio, "ESPACIAL", "CARDWG.LST")
        
        if not os.path.exists(caminho_cardwg2):
            return pilares

        with open(caminho_cardwg2, "r", encoding="latin1", errors="ignore") as f:
            lines = f.readlines()

        curr_pilar = None
        lendo_fundacao = False
        pavimento_detectado = "FUNDAÇÃO"

        for l in lines:
            parts = [p.strip() for p in l.split(",")]
            if parts[0] == "PLANTA":
                nome_planta = parts[2].replace("'", "").strip().upper()
                if any(k in nome_planta for k in ["FUNDA", "BALDRAME", "BLOCO", "ESTACA", "INF"]):
                    lendo_fundacao = True
                    pavimento_detectado = parts[2].replace("'", "").strip()
                elif len(pilares) == 0 and not lendo_fundacao:
                    lendo_fundacao = True
                    pavimento_detectado = parts[2].replace("'", "").strip()
                else:
                    if len(pilares) > 0:
                        break # Fim da planta de fundação
            
            if not lendo_fundacao:
                continue

            if parts[0] == "PILAR":
                num = int(parts[1])
                tipo_str = parts[2].replace("'", "").strip()
                b = float(parts[3])
                h = float(parts[4])
                curr_pilar = {
                    "nome": f"P{num}",
                    "tipo": TipoSecao.RETANGULAR if tipo_str == "R" else TipoSecao.POLIGONAL,
                    "b": b,
                    "h": h,
                    "pts": [],
                    "np": 5,
                }
            elif parts[0] == "NP" and curr_pilar is not None:
                try:
                    curr_pilar["np"] = int(parts[1])
                except (ValueError, IndexError):
                    curr_pilar["np"] = 5
            elif parts[0] == "XY" and curr_pilar is not None:
                x = float(parts[1])
                y = float(parts[2])
                curr_pilar["pts"].append((x, y))

                # Se o pilar acumulou todos os seus vértices (especificado por NP)
                if len(curr_pilar["pts"]) >= curr_pilar["np"]:
                    pts = curr_pilar["pts"]
                    if len(pts) > 1 and pts[0] == pts[-1]:
                        pts_sem_fechamento = pts[:-1]
                    else:
                        pts_sem_fechamento = pts

                    # Baricentro calculado a partir dos vértices reais da seção
                    cx_cm, cy_cm = calcular_baricentro_poligono(pts_sem_fechamento)
                    
                    # Ponto fixo aproximado pelo primeiro vértice
                    pf = pts_sem_fechamento[0]

                    geom = GeometriaPilar(
                        tipo=curr_pilar["tipo"],
                        b=curr_pilar["b"],
                        h=curr_pilar["h"],
                        angulo_rotacao_graus=0.0,
                        ponto_fixo_coord=(pf[0], pf[1]),
                        vertices_poligono=pts_sem_fechamento,
                    )

                    pilares.append(
                        PilarFundacao(
                            nome=curr_pilar["nome"],
                            pavimento_origem="FUNDACAO",
                            geometria=geom,
                            baricentro=Baricentro(x=round(cx_cm, 3), y=round(cy_cm, 3)),
                        )
                    )
                    curr_pilar = None
            elif parts[0] == "PISO":
                continue

        return pilares

    def carregar_planta_de_cargas(self) -> PlantaDeCargasModel:
        """
        Carrega e une os pilares da fundação com seus respectivos esforços reais.
        """
        pilares = self._ler_pilares_cardwg2()
        reacoes = self._ler_reacoes_porlis2()

        if not pilares:
            espacial_path = os.path.join(self.caminho_edificio, "ESPACIAL")
            if not os.path.exists(espacial_path):
                raise FileNotFoundError(
                    f"O edifício '{self.nome_edificio}' foi localizado em '{self.caminho_edificio}', "
                    f"mas a pasta 'ESPACIAL' ainda não foi gerada.\n"
                    f"Para gerar a Planta de Cargas deste edifício, é necessário executar o "
                    f"'Processamento Global' ou o 'Pórtico Espacial' no TQS V25."
                )
            cardwg_exists = os.path.exists(os.path.join(espacial_path, "CARDWG2.LST")) or os.path.exists(os.path.join(espacial_path, "CARDWG.LST"))
            if not cardwg_exists:
                raise FileNotFoundError(
                    f"O edifício '{self.nome_edificio}' possui a pasta ESPACIAL, mas os arquivos de malha "
                    f"gráfica dos pilares (CARDWG2.LST / CARDWG.LST) ainda não foram gerados.\n"
                    f"Execute o processamento do Pórtico Espacial no TQS V25."
                )
            raise ValueError(
                f"No edifício '{self.nome_edificio}', os arquivos espaciais existem mas nenhum pilar "
                f"foi detectado na planta de fundação. Verifique se o edifício possui pilares ou se é estruturado em paredes/alvenaria."
            )

        # Vincula os esforços lidos a cada pilar
        for p in pilares:
            if p.nome in reacoes:
                p.esforcos = reacoes[p.nome]
            else:
                p.esforcos = EsforcosFundacao(nk_max=0.0, nk_min=0.0)

        # Ordena pilares por número (P1, P2, ..., P10, ...)
        def extrair_numero(pilar: PilarFundacao) -> int:
            nums = re.findall(r"\d+", pilar.nome)
            return int(nums[0]) if nums else 0

        pilares.sort(key=extrair_numero)

        # Tenta ler a tabela oficial PORLID da pasta ESPACIAL (TQS Oficial)
        dados_porlid = None
        try:
            from src.tqs_adapter.porlid_reader import TQSPorlidReader
            porlid_reader = TQSPorlidReader(self.caminho_edificio)
            if porlid_reader.existe_porlid():
                res_porlid = porlid_reader.extrair_tabela_porlid()
                if res_porlid.get("sucesso", False):
                    dados_porlid = res_porlid
        except Exception:
            dados_porlid = None

        return PlantaDeCargasModel(
            edificio_nome=self.nome_edificio,
            caminho_edificio=self.caminho_edificio,
            pavimento_fundacao="FUNDAÇÃO",
            pilares=pilares,
            escala_locacao=50,
            notas_projeto=[
                "Edifício lido nativamente do TQS V25.",
                "Cargas e tabela de fundações extraídas de ESPACIAL/PORLID.DWG (TQS Oficial)." if dados_porlid else "Cargas extraídas do Pórtico Espacial (PORLIS2.LST - Caso 1).",
                "Geometria e baricentros extraídos da malha de fundação (CARDWG2.LST).",
            ],
            dados_porlid=dados_porlid,
        )

