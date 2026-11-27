"""
Roteador único de intenções em linguagem natural do AUTQS.

Antes as palavras-chave de cada pedido estavam copiadas no chat_agent e no orchestrator e já
tinham divergido (ex.: "ALTERA" x "ALTERO"; "carga" sozinha gerando planta no orchestrator).
Aqui fica uma definição só, usada pelos dois. Cada intenção é testada de forma independente
(``intencoes`` devolve todas as que casam); a ordem de prioridade continua sendo a de quem chama.

Onde as duas versões antigas divergiam, valeu a mais restritiva, para não disparar geração
de desenho ou processamento por engano:
- planta de cargas: exige "planta" + carga/locação/gerar..., "gabarito" ou origem de cotas
  ("carga" sozinha não gera mais planta);
- formas de alvenaria: exige também um verbo/objeto de desenho (planta, gerar, emitir...);
- processamento: não dispara quando o pedido é de memorial/relatório.
"""
import re
from typing import Callable, Dict, List

from src.tqs_adapter.model_editor import normalizar_texto

RE_COORDS_AVULSAS = re.compile(
    r"^\s*(?:mudar\s+(?:para\s+)?)?(?:origem\s+(?:para\s+)?)?([+-]?\d{2,}(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d{2,}(?:\.\d+)?)\s*$",
    re.IGNORECASE,
)


def _tem(texto: str, chaves) -> bool:
    return any(k in texto for k in chaves)


def _listar_edificios(n: str, l: str) -> bool:
    return (_tem(n, ["QUAI", "LIST", "MOSTR", "EXIB"]) and _tem(n, ["EDIF", "PROJET", "OBRA"])
            and not _tem(n, ["PAVIMENT", "PISO", "VIGA", "LAJE", "PILAR", "CARGA"]))


def _consulta_modelo(n: str, l: str) -> bool:
    return _tem(n, ["LIST", "QUAI", "MOSTR", "VER", "EXIB"]) and _tem(n, ["PAVIMENT", "PISO", "VIGA", "LAJE", "PILAR", "CARGA"])


# Pedidos de análise/comparação/ranking têm rotas próprias ("VER" também casa com "VERIFIC").
_TERMOS_OUTRAS_ROTAS = ["ANALIS", "VERIFIC", "AUDIT", "DIMENSION", "ESFORC", "BIELA", "CORTANT",
                        "COMPAR", "DIFF", "MAIS", "MAIOR", "MENOR", "CARREGAD", "TRAC", "OTIMIZ"]


def _listar_pavimentos(n: str, l: str) -> bool:
    return (_tem(n, ["PAVIMENT", "PISO", "PLANTA", "NIVEL", "NIVEIS"]) and _tem(n, ["LIST", "QUAI", "MOSTR", "VER", "EXIB", "QUANT"])
            and not _tem(n, ["VIGA", "LAJE", "PILAR", "CONSIST"] + _TERMOS_OUTRAS_ROTAS))


def _listar_elementos(n: str, l: str) -> bool:
    return (_tem(n, ["LIST", "QUAI", "MOSTR", "VER", "EXIB"]) and _tem(n, ["VIGA", "LAJE", "PILAR", "CARGA"])
            and not _tem(n, _TERMOS_OUTRAS_ROTAS))


def _processamento(n: str, l: str) -> bool:
    return (not _tem(n, ["MEMORIAL", "RELATORI", "JUSTIFICATIV"])
            and _tem(n, ["PROCESS", "CALCUL", "ROD", "EXECUT", "PORTIC", "RECALCUL"])
            and _tem(n, ["EDIFIC", "OBRA", "PROJET", "PORTIC", "ESTRUTUR", "MODEL"]))


def _comparacao(n: str, l: str) -> bool:
    return (_tem(n, ["COMPAR", "DIFF", "ALTERA", "ALTERO", "MUDO", "DIFERENC", "SOBREPOSI", "REVISA"])
            and _tem(n, ["GEOMETR", "FORMA", "PLANTA", "ARQUITETUR", "DESENH", "PROJET", "MODEL"]))


def _pilares(n: str, l: str) -> bool:
    return _tem(n, ["DIMENSION", "OTIMIZ", "AUDIT"]) and _tem(n, ["PILAR"])


def _consistencia(n: str, l: str) -> bool:
    return _tem(n, ["CONSIST", "ERRO", "INCONFORM", "AUDIT", "VERIFIC"]) and _tem(n, ["FORMA", "PLANTA", "APOIO"])


def _vigas(n: str, l: str) -> bool:
    return _tem(n, ["ANALIS", "VERIFIC", "AUDIT", "DIMENSION", "ESFORC", "BIELA", "CORTANT"]) and _tem(n, ["VIGA"])


def _estabilidade(n: str, l: str) -> bool:
    return _tem(n, ["ESTABILID", "GAMAZ", "GAMA_Z", "ALFA", "DRIFT"]) or (
        _tem(n, ["DESLOCAMENT", "VENT"]) and _tem(n, ["TOPO", "INTERPISO", "ELS", "GLOBAL"]))


def _lajes(n: str, l: str) -> bool:
    return _tem(n, ["LAJE", "GRELH", "FLECH", "PUNCA"]) and _tem(n, ["AUDIT", "VERIFIC", "ANALIS", "ESBELTEZ", "MODEL"])


def _materiais(n: str, l: str) -> bool:
    return _tem(n, ["QUANTITATIV", "CONSUM", "MATERIA"]) or (
        _tem(n, ["VOLUME", "TAXA"]) and _tem(n, ["CONCRET", "FORMA", "ACO", "CARBON"]))


def _memorial(n: str, l: str) -> bool:
    return _tem(n, ["MEMORIAL", "JUSTIFICATIV"]) or (
        _tem(n, ["RELATORI", "DOCUMENT"]) and _tem(n, ["EXECUTIV", "CALCUL", "OBRA", "PROJET"]))


def _limpeza(n: str, l: str) -> bool:
    return _tem(n, ["LIMPEZA", "PADRONIZ", "HIGIENIZ"]) and _tem(n, ["ARQUITETUR", "DWG", "DXF", "GEO_"])


def _formas_alvenaria(n: str, l: str) -> bool:
    return (_tem(n, ["FORMA", "ALVENAR", "FIADA", "DESFIAD", "PRE_FOR", "MODULAC"])
            and _tem(n, ["PLANTA", "DESENH", "GERAR", "EMITIR", "CRIAR", "FAZER", "TRANSFORM"]))


def _planta_cargas(n: str, l: str, original: str = "") -> bool:
    return (
        ("planta" in l and _tem(l, ["carga", "loca", "gerar", "desenh", "emitir", "funda"]))
        or _tem(l, ["gerar dwg", "criar dwg", "emitir prancha", "desenhar prancha", "gerar prancha", "gabarito"])
        or ("cota" in l and _tem(n, ["REFERENC", "ORIGEM", "PONTO", "0,0"]))
        or bool(RE_COORDS_AVULSAS.search(original or l))
        or ("mudar" in l and _tem(n, ["ORIGEM", "PONTO", "COTA", "REFERENC"]))
    )


def _ranking(n: str, l: str) -> bool:
    return _tem(l, ["maior", "pesado", "mais carregado", "critico", "ranking"])


def _tracao(n: str, l: str) -> bool:
    return _tem(l, ["tracao", "tração", "arrancamento", "negativo"])


INTENCOES: Dict[str, Callable[..., bool]] = {
    "listar_edificios": _listar_edificios,
    "consulta_modelo": _consulta_modelo,
    "listar_pavimentos": _listar_pavimentos,
    "listar_elementos": _listar_elementos,
    "processamento": _processamento,
    "comparacao": _comparacao,
    "pilares": _pilares,
    "consistencia": _consistencia,
    "vigas": _vigas,
    "estabilidade": _estabilidade,
    "lajes": _lajes,
    "materiais": _materiais,
    "memorial": _memorial,
    "limpeza": _limpeza,
    "formas_alvenaria": _formas_alvenaria,
    "planta_cargas": _planta_cargas,
    "ranking": _ranking,
    "tracao": _tracao,
}


def intencoes(texto: str) -> List[str]:
    """Todas as intenções reconhecidas em ``texto`` (a ordem de prioridade é de quem chama)."""
    n = normalizar_texto(texto)
    l = (texto or "").lower()
    achadas = []
    for nome, pred in INTENCOES.items():
        ok = pred(n, l, texto) if nome == "planta_cargas" else pred(n, l)
        if ok:
            achadas.append(nome)
    return achadas
