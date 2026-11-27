"""
Descrição sugerida para uma nova revisão: compara os desenhos atuais da prancha com o
DXF gravado pelo TQS na última plotagem (<ID>-Rnn.DXF), que é a "foto" do que foi emitido.

- Base (emitido): DXF da plotagem, já explodido, em cm de papel, camadas = penas.
- Atual: desenhos tipo 0 do .CPL lidos com TQSDwg (o iterador expande os blocos em
  coordenadas globais), levados para a folha com a janela/escala do .CPL e filtrados pela
  máscara de níveis da planta.
- Ficam de fora a área do selo/carimbo e a faixa de margens da folha, que mudam a cada
  emissão. Macros do TQS (%Valor da cota, %Pavimento) são substituídas na plotagem e
  também são ignoradas, assim como microtraços (< 0,05 cm de papel).

Calibração (054 AE, prancha 0601): o DWG salvo no instante da R04 contra o R04.DXF
resulta em zero diferenças com esses filtros.
"""
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.skills.case_15_revisao_plantas.cpl import DesenhoCPL, PlantaCPL
from src.skills.case_15_revisao_plantas.nomenclatura import RegrasNomenclatura, localizar_saida_plotagem

DESCRICAO_PADRAO = "MODIFICAÇÕES GERAIS"
DESCRICAO_SEM_ALTERACAO = "REEMISSÃO SEM ALTERAÇÕES NO DESENHO"
MAX_CARACTERES = 60

# Áreas da folha (cm de papel) que mudam a cada emissão e não entram na comparação
SELO_X_MIN, SELO_Y_MAX = 100.3, 29.8
MARGEM_ESQ, MARGEM_INF, MARGEM_DIR, MARGEM_SUP = 2.6, 1.05, 1.0, 1.05
COMPRIMENTO_MINIMO = 0.05        # microtraços (cm de papel)
TOLERANCIA_SEGMENTO = 0.03       # 2ª passada de casamento (cm de papel)
TOLERANCIA_TEXTO = 1.0
RAIO_MACRO = 0.6
RAIO_AGRUPAMENTO = 1.5
MIN_ELEMENTOS_REGIAO = 5          # regiões só de geometria menores que isso são ruído

CATEGORIA_POR_NIVEL: Dict[int, str] = {
    # Alvenaria estrutural (1ª/2ª fiada, pré-modulação)
    203: "MODULAÇÃO", 213: "MODULAÇÃO", 224: "MODULAÇÃO", 241: "MODULAÇÃO", 245: "MODULAÇÃO",
    247: "PAREDES", 251: "VÃOS", 252: "VÃOS", 239: "VÃOS", 221: "JUNTAS",
    # Comuns
    10: "LAJES", 13: "LAJES", 237: "LAJES",
    222: "TÍTULO", 250: "TÍTULO",
    0: "LEGENDA", 18: "NOTAS", 257: "NOTAS",
    200: "CORTE ESQUEMÁTICO", 248: "CORTE ESQUEMÁTICO", 249: "CORTE ESQUEMÁTICO",
    # Formas de concreto armado
    2: "PILARES", 9: "PILARES", 12: "PILARES", 8: "VIGAS", 11: "VIGAS",
}
CATEGORIA_DESCONHECIDA = "GEOMETRIA"
# Só entram na descrição quando não há mudança em categoria principal
CATEGORIAS_SECUNDARIAS = {"TÍTULO", "LEGENDA", "NOTAS", CATEGORIA_DESCONHECIDA}
FRACAO_VOTO_REGIAO = 0.2           # categoria com >= 20% dos elementos de uma região recebe o voto dela

PALAVRAS_GENERICAS = {
    # termos de desenho (comparados sem acento)
    "BLOCO", "BLOCOS", "MEIO", "INTEIRO", "CANALETA", "JUNTA", "JUNTAS", "LEGENDA", "ESCALA",
    "PAVIMENTO", "TIPO", "FIADA", "ALVENARIA", "ESTRUTURAL", "CONCRETO", "ARMADO", "GRAUTE",
    "DILATAO", "MOVIMENTAO", "PRANCHA", "PLANTA", "NIVEL", "COTA", "COMPENSADOR", "GRAUTEADO",
    "ARMADURA", "VERGA", "CONTRAVERGA", "TELA", "GRAMPO", "PRUMO", "CINTA", "LAJE", "LAJES",
    "VIGA", "VIGAS", "PILAR", "PILARES", "PAREDE", "PAREDES",
    # palavras funcionais
    "PARA", "COMO", "ENTRE", "SOBRE", "SOBRA", "CONFORME", "VIDE", "DETALHE", "NOTA", "NOTAS",
}
RE_PALAVRA = re.compile(r"[A-ZÀ-Ý]{4,}")


@dataclass
class Primitiva:
    tipo: str                         # "L" segmento, "T" texto, "C" círculo
    chave: tuple
    pontos: List[Tuple[float, float]]
    nivel: Optional[int] = None       # lado DWG
    camada: Optional[str] = None      # lado DXF (pena)
    texto: str = ""

    @property
    def centro(self) -> Tuple[float, float]:
        xs = [p[0] for p in self.pontos]
        ys = [p[1] for p in self.pontos]
        return (sum(xs) / len(xs), sum(ys) / len(ys))


RE_CODIGO_DXF = re.compile(r"%%[cdpCDP]")
RE_CAMINHO = re.compile(r"^[A-Za-z]:\\|\.(jpe?g|png|bmp|tiff?|dwg)$", re.I)


def _norm_texto(texto: str) -> str:
    """
    Só ASCII: o DWG (latin-1) e o DXF podem divergir na decodificação de acentos.
    Símbolos também diferem: o DXF usa %%c/%%d/%%p e o DWG do TQS usa '{' (Ø) e '^' (º).
    """
    t = RE_CODIGO_DXF.sub("", texto or "").replace("{", "").replace("^", "")
    return " ".join("".join(c for c in t if ord(c) < 128).upper().split())


def _excluido(x: float, y: float, largura: float = 118.9, altura: float = 45.0) -> bool:
    if x > SELO_X_MIN and y < SELO_Y_MAX:
        return True
    return x < MARGEM_ESQ or y < MARGEM_INF or x > largura - MARGEM_DIR or y > altura - MARGEM_SUP


def _segmento(a, b, **kw) -> Optional[Primitiva]:
    if math.dist(a, b) < COMPRIMENTO_MINIMO:
        return None
    p1 = (round(a[0], 2), round(a[1], 2))
    p2 = (round(b[0], 2), round(b[1], 2))
    return Primitiva("L", ("L",) + tuple(sorted([p1, p2])), [a, b], **kw)


def _texto(texto: str, x: float, y: float, **kw) -> Optional[Primitiva]:
    # Caminhos de imagens (blocos $BMP) viram texto de forma diferente no DWG e na plotagem
    if RE_CAMINHO.search((texto or "").strip()):
        return None
    norm = _norm_texto(texto)
    if not norm:
        return None
    return Primitiva("T", ("T", norm, round(x, 1), round(y, 1)), [(x, y)], texto=texto.strip(), **kw)


def _circulo(xc: float, yc: float, r: float, **kw) -> Primitiva:
    return Primitiva("C", ("C", round(xc, 2), round(yc, 2), round(r, 2)), [(xc - r, yc - r), (xc + r, yc + r)], **kw)


def _filtrar(prims: Iterable[Optional[Primitiva]], largura: float, altura: float) -> List[Primitiva]:
    return [p for p in prims if p is not None and not all(_excluido(x, y, largura, altura) for x, y in p.pontos)]


# ---------------------------------------------------------------------------
# Extração
# ---------------------------------------------------------------------------
def primitivas_dxf(caminho_dxf: str, largura: float = 118.9, altura: float = 45.0) -> List[Primitiva]:
    import ezdxf
    doc = ezdxf.readfile(caminho_dxf)
    prims: List[Optional[Primitiva]] = []
    for e in doc.modelspace():
        t = e.dxftype()
        camada = e.dxf.layer
        if t == "LINE":
            prims.append(_segmento((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y), camada=camada))
        elif t in ("POLYLINE", "LWPOLYLINE"):
            pts = [(p[0], p[1]) for p in (e.points() if t == "POLYLINE" else e.get_points("xy"))]
            fechada = e.is_closed if t == "POLYLINE" else e.closed
            if fechada and len(pts) > 2 and pts[0] != pts[-1]:
                pts.append(pts[0])
            prims += [_segmento(pts[i], pts[i + 1], camada=camada) for i in range(len(pts) - 1)]
        elif t == "TEXT":
            prims.append(_texto(e.dxf.text, e.dxf.insert.x, e.dxf.insert.y, camada=camada))
        elif t == "MTEXT":
            prims.append(_texto(e.plain_text(), e.dxf.insert.x, e.dxf.insert.y, camada=camada))
        elif t == "CIRCLE":
            prims.append(_circulo(e.dxf.center.x, e.dxf.center.y, e.dxf.radius, camada=camada))
    return _filtrar(prims, largura, altura)


def primitivas_dwg(desenho: DesenhoCPL, caminho_dwg: str, largura: float = 118.9,
                   altura: float = 45.0) -> Tuple[List[Primitiva], List[Tuple[float, float]]]:
    """Primitivas do desenho atual em cm de papel + posições das macros (%...) substituídas na plotagem."""
    import src.tqs_adapter.tqs_env  # noqa: F401
    from TQS import TQSDwg

    dwg = TQSDwg.Dwg(pedmv=0)
    if dwg.file.Open(caminho_dwg) != 0:
        raise FileNotFoundError(f"Não consegui abrir {caminho_dwg}")
    prims: List[Optional[Primitiva]] = []
    macros: List[Tuple[float, float]] = []
    f = desenho.para_folha
    it = dwg.iterator
    it.Begin()
    try:
        while True:
            if it.GetElementReadPosition():
                nome, nivel = it.elementName, it.level
                if desenho.nivel_visivel(nivel):
                    if nome == "Linha":
                        prims.append(_segmento(f(it.x1, it.y1), f(it.x2, it.y2), nivel=nivel))
                    elif nome == "Polyline":
                        pts = [f(*it.GetPolylinePt(i)[:2]) for i in range(it.xySize)]
                        prims += [_segmento(pts[i], pts[i + 1], nivel=nivel) for i in range(len(pts) - 1)]
                    elif nome == "Texto":
                        texto = it.text or ""
                        pos = f(it.x1, it.y1)
                        if texto.strip().startswith("%"):
                            macros.append(pos)
                        else:
                            prims.append(_texto(texto, pos[0], pos[1], nivel=nivel))
                    elif nome == "Circulo":
                        xc, yc = f(it.xc, it.yc)
                        prims.append(_circulo(xc, yc, it.radius / (desenho.escala or 1.0), nivel=nivel))
            if not it.Next():
                break
    finally:
        dwg.file.Close()
    return _filtrar(prims, largura, altura), macros


# ---------------------------------------------------------------------------
# Comparação e agrupamento
# ---------------------------------------------------------------------------
@dataclass
class ResultadoComparacao:
    so_atual: List[Primitiva]
    so_base: List[Primitiva]
    casados: int
    pena_para_nivel: Dict[str, int] = field(default_factory=dict)


def comparar(base: List[Primitiva], atual: List[Primitiva],
             macros: Optional[List[Tuple[float, float]]] = None) -> ResultadoComparacao:
    idx_b: Dict[tuple, List[Primitiva]] = defaultdict(list)
    idx_a: Dict[tuple, List[Primitiva]] = defaultdict(list)
    for p in base:
        idx_b[p.chave].append(p)
    for p in atual:
        idx_a[p.chave].append(p)

    # Comparação por presença (conjunto), não por contagem: elementos idênticos sobrepostos
    # (ex.: linha + polilinha no mesmo lugar) não mudam nada no papel.
    so_a, so_b = [], []
    casados = 0
    pena_nivel: Dict[str, Counter] = defaultdict(Counter)
    for chave in set(idx_a) | set(idx_b):
        la, lb = idx_a.get(chave, []), idx_b.get(chave, [])
        if la and lb:
            casados += 1
            for pa, pb in zip(la, lb):
                if pb.camada is not None and pa.nivel is not None:
                    pena_nivel[pb.camada][pa.nivel] += 1
        else:
            so_a += la
            so_b += lb

    so_a, so_b, extra = _casar_com_tolerancia(so_a, so_b)
    casados += extra

    if macros:
        def perto_de_macro(p: Primitiva) -> bool:
            return p.tipo == "T" and any(math.dist(p.pontos[0], m) <= RAIO_MACRO for m in macros)
        so_b = [p for p in so_b if not perto_de_macro(p)]

    mapa = {pena: cont.most_common(1)[0][0] for pena, cont in pena_nivel.items() if cont}
    return ResultadoComparacao(so_atual=so_a, so_base=so_b, casados=casados, pena_para_nivel=mapa)


def _casar_com_tolerancia(so_a: List[Primitiva], so_b: List[Primitiva]):
    """2ª passada: arredondamento na fronteira (segmentos) e alinhamento de texto (mesmo conteúdo, perto)."""
    celula = 0.1
    grade: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for i, p in enumerate(so_b):
        cx, cy = p.centro
        grade[(int(cx // celula), int(cy // celula))].append(i)
    usados_b = set()
    restantes_a = []
    for pa in so_a:
        cx, cy = pa.centro
        gx, gy = int(cx // celula), int(cy // celula)
        achou = None
        raio_celulas = int(TOLERANCIA_TEXTO // celula) + 1 if pa.tipo == "T" else 1
        for dx in range(-raio_celulas, raio_celulas + 1):
            for dy in range(-raio_celulas, raio_celulas + 1):
                for i in grade.get((gx + dx, gy + dy), []):
                    pb = so_b[i]
                    if i in usados_b or pb.tipo != pa.tipo:
                        continue
                    if _equivalentes(pa, pb):
                        achou = i
                        break
                if achou is not None:
                    break
            if achou is not None:
                break
        if achou is None:
            restantes_a.append(pa)
        else:
            usados_b.add(achou)
    restantes_b = [p for i, p in enumerate(so_b) if i not in usados_b]
    return restantes_a, restantes_b, len(usados_b)


def _equivalentes(a: Primitiva, b: Primitiva) -> bool:
    if a.tipo == "T":
        return a.chave[1] == b.chave[1] and math.dist(a.pontos[0], b.pontos[0]) <= TOLERANCIA_TEXTO
    if a.tipo == "L":
        (a1, a2), (b1, b2) = a.pontos, b.pontos
        tol = TOLERANCIA_SEGMENTO
        return ((math.dist(a1, b1) <= tol and math.dist(a2, b2) <= tol) or
                (math.dist(a1, b2) <= tol and math.dist(a2, b1) <= tol))
    if a.tipo == "C":
        return all(abs(x - y) <= TOLERANCIA_SEGMENTO for x, y in zip(a.chave[1:], b.chave[1:]))
    return False


def agrupar(prims: List[Primitiva], raio: float = RAIO_AGRUPAMENTO) -> List[List[Primitiva]]:
    """Agrupa por proximidade (união de conjuntos sobre uma grade de células do tamanho do raio)."""
    pai = list(range(len(prims)))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    grade: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for i, p in enumerate(prims):
        cx, cy = p.centro
        grade[(int(cx // raio), int(cy // raio))].append(i)
    for (gx, gy), membros in grade.items():
        vizinhos = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                vizinhos += grade.get((gx + dx, gy + dy), [])
        for i in membros:
            for j in vizinhos:
                if i < j and math.dist(prims[i].centro, prims[j].centro) <= raio:
                    ri, rj = raiz(i), raiz(j)
                    if ri != rj:
                        pai[rj] = ri
    grupos: Dict[int, List[Primitiva]] = defaultdict(list)
    for i, p in enumerate(prims):
        grupos[raiz(i)].append(p)
    return sorted(grupos.values(), key=len, reverse=True)


# ---------------------------------------------------------------------------
# Descrição
# ---------------------------------------------------------------------------
def _categoria(p: Primitiva, pena_para_nivel: Dict[str, int]) -> str:
    nivel = p.nivel if p.nivel is not None else pena_para_nivel.get(p.camada or "")
    return CATEGORIA_POR_NIVEL.get(nivel, CATEGORIA_DESCONHECIDA) if nivel is not None else CATEGORIA_DESCONHECIDA


def _rotulos_proximos(regiao: List[Primitiva], textos_atuais: List[Primitiva]) -> List[str]:
    """
    Nomes de lugares perto da região (ex.: ELEVADOR, ESCADA). Só textos de níveis sem
    categoria conhecida (referências de arquitetura): legenda, notas, título, cotas,
    juntas e identificação de paredes/lajes não servem como "lugar".
    """
    xs = [x for p in regiao for x, _ in p.pontos]
    ys = [y for p in regiao for _, y in p.pontos]
    x0, x1, y0, y1 = min(xs) - 2.0, max(xs) + 2.0, min(ys) - 2.0, max(ys) + 2.0
    cont = Counter()
    for t in textos_atuais:
        if CATEGORIA_POR_NIVEL.get(t.nivel, CATEGORIA_DESCONHECIDA) != CATEGORIA_DESCONHECIDA:
            continue
        x, y = t.pontos[0]
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        for palavra in RE_PALAVRA.findall(t.texto.upper()):
            if _norm_texto(palavra) not in PALAVRAS_GENERICAS:
                cont[palavra] += 1
    return [p for p, _ in cont.most_common(2)]


def _lista_pt(itens: List[str]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " E " + itens[-1]


def montar_descricao(resultado: ResultadoComparacao, textos_atuais: List[Primitiva]) -> Tuple[str, List[Dict[str, Any]]]:
    diffs = resultado.so_atual + resultado.so_base
    if not diffs:
        return DESCRICAO_SEM_ALTERACAO, []

    # Cada região vota nas categorias que mudaram nela (contar linhas favoreceria sempre os
    # blocos, que têm muitas linhas por elemento)
    regioes = []
    votos: Counter = Counter()
    rotulos: Counter = Counter()
    for grupo in agrupar(diffs):
        textos_mudados = [p for p in grupo if p.tipo == "T"]
        if len(grupo) < MIN_ELEMENTOS_REGIAO and not textos_mudados:
            continue
        cats = Counter(_categoria(p, resultado.pena_para_nivel) for p in grupo)
        votadas = {c for c, n in cats.items() if n >= FRACAO_VOTO_REGIAO * len(grupo)}
        votadas |= {_categoria(p, resultado.pena_para_nivel) for p in textos_mudados}
        for cat in votadas:
            votos[cat] += 1
        rots = _rotulos_proximos(grupo, textos_atuais)
        for r in rots:
            rotulos[r] += len(grupo)
        xs = [x for p in grupo for x, _ in p.pontos]
        ys = [y for p in grupo for _, y in p.pontos]
        novos = sum(1 for p in grupo if p.nivel is not None)
        removidos = len(grupo) - novos
        antes = [p.texto for p in textos_mudados if p.nivel is None][:3]
        depois = [p.texto for p in textos_mudados if p.nivel is not None][:3]
        trecho_txt = ""
        if antes or depois:
            trecho_txt = f"; textos: {', '.join(antes) or '-'} → {', '.join(depois) or '-'}"
        regioes.append({
            "bbox_folha_cm": [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)],
            "categorias": [c for c, _ in cats.most_common()],
            "adicionados": novos, "removidos": removidos, "rotulos": rots,
            "resumo": (f"Folha x {min(xs):.0f}–{max(xs):.0f} / y {min(ys):.0f}–{max(ys):.0f} cm: "
                       f"{', '.join(c for c, _ in cats.most_common(3))} (+{novos} −{removidos})"
                       + (f" perto de {', '.join(rots)}" if rots else "") + trecho_txt),
        })

    if not regioes:
        return DESCRICAO_SEM_ALTERACAO, []

    candidatas = [(c, v) for c, v in votos.most_common() if c not in CATEGORIAS_SECUNDARIAS]
    if not candidatas:
        candidatas = votos.most_common()
    maior = candidatas[0][1]
    principais = [c for c, v in candidatas if v >= max(1, 0.3 * maior)][:3]
    prefixo = "ALTERAÇÕES GERAIS DE " if len(regioes) >= 6 else "ALTERAÇÃO DE "
    descricao = prefixo + _lista_pt(principais)
    locais = [r for r, _ in rotulos.most_common(2)]
    if locais:
        com_local = f"{descricao} - {'/'.join(locais)}"
        if len(com_local) <= MAX_CARACTERES:
            descricao = com_local
    while len(descricao) > MAX_CARACTERES and len(principais) > 1:
        principais = principais[:-1]
        descricao = prefixo + _lista_pt(principais)
    return descricao, regioes


def sugerir_descricao_revisao(pl: PlantaCPL, regras: RegrasNomenclatura) -> Tuple[str, Dict[str, Any]]:
    """Compara a prancha com o DXF da última plotagem e devolve (descrição, detalhes)."""
    n = pl.revisao_atual
    if n is None:
        return "EMISSÃO INICIAL", {}
    dxf = localizar_saida_plotagem(pl.pasta, pl.id, n, regras, ".DXF")
    if not dxf:
        nome = regras.nome_arquivo_revisao(pl.id, n) + ".DXF"
        return DESCRICAO_PADRAO, {"aviso": f"Sem {nome} da última plotagem para comparar; usei a descrição padrão."}

    largura, altura = 118.9, 45.0
    try:
        toks = pl.linhas[0].split()
        largura, altura = float(toks[7]), float(toks[8])
    except (ValueError, IndexError):
        pass

    base = primitivas_dxf(dxf, largura, altura)
    atual: List[Primitiva] = []
    macros: List[Tuple[float, float]] = []
    for d in pl.desenhos_conteudo():
        caminho = d.caminho_absoluto(pl.pasta)
        if not os.path.exists(caminho):
            return DESCRICAO_PADRAO, {"aviso": f"Desenho {caminho} da prancha não encontrado; usei a descrição padrão."}
        prims, mac = primitivas_dwg(d, caminho, largura, altura)
        atual += prims
        macros += mac

    resultado = comparar(base, atual, macros)
    textos_atuais = [p for p in atual if p.tipo == "T"]
    descricao, regioes = montar_descricao(resultado, textos_atuais)
    info: Dict[str, Any] = {
        "base": dxf, "revisao_base": n,
        "elementos_casados": resultado.casados,
        "somente_atual": len(resultado.so_atual), "somente_emitido": len(resultado.so_base),
        "regioes": regioes,
    }
    if descricao == DESCRICAO_SEM_ALTERACAO:
        info["aviso"] = f"Nenhuma diferença no desenho desde a R{n:02d} (fora do selo); confira se a revisão é necessária."
    return descricao, info
