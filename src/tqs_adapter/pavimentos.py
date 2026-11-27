"""
Descoberta e filtro das pastas de pavimento de um edifício TQS.

Antes cada skill (Cases 03, 05, 06 e 09) tinha a sua própria lista de pastas técnicas
e a sua heurística de filtro, com comportamentos diferentes. Os principais problemas:
- "2" casava com "12 PAVIMENTO" (comparação de dígitos por substring);
- um filtro sem correspondência devolvia TODOS os pavimentos;
- a lista de pastas ignoradas era sensível a maiúsculas ("Alvest" x "ALVEST").
"""
import os
import re
import unicodedata
from typing import List, Optional, Tuple

# Pastas de um edifício TQS que não são pavimentos (comparação sem acento e em maiúsculas)
PASTAS_TECNICAS = {
    "ESPACIAL", "PILAR", "FUNDAC", "GERAIS", "SISE", "ARQ MODELO", "SELOS",
    "ALVEST", "INFRA", "PREMOLD", "MOLDURAS", "TQSDESKTOPB", "BACKUP_CLAUDE", "PLANTAS",
}

FILTROS_TODOS = {"", "todos", "todas", "all", "*"}


def remover_acentos(texto: str) -> str:
    """Remove acentos e converte para minúsculas, para comparações flexíveis."""
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def eh_pasta_tecnica(nome: str) -> bool:
    return remover_acentos(nome).upper() in PASTAS_TECNICAS or "_BKP_" in nome.upper()


def listar_pastas_pavimento(caminho_edificio: str) -> List[Tuple[str, str]]:
    """(nome, caminho) de cada subpasta do edifício que não é pasta técnica nem backup."""
    if not caminho_edificio or not os.path.isdir(caminho_edificio):
        return []
    itens = []
    for nome in sorted(os.listdir(caminho_edificio)):
        caminho = os.path.join(caminho_edificio, nome)
        if os.path.isdir(caminho) and not eh_pasta_tecnica(nome):
            itens.append((nome, caminho))
    return itens


def _contem(texto: str, trecho: str) -> bool:
    """``trecho`` dentro de ``texto`` sem cortar números ("2 pav" não está em "12 pavimento")."""
    trecho = trecho.strip()
    if not trecho:
        return False
    return re.search(r"(?<!\d)" + re.escape(trecho) + r"(?!\d)", texto) is not None


def _numeros(texto: str) -> List[str]:
    return [n.lstrip("0") or "0" for n in re.findall(r"\d+", texto)]


def filtrar_pavimentos(itens: List[Tuple[str, str]], filtro: Optional[str]) -> List[Tuple[str, str]]:
    """
    Pavimentos de ``itens`` (pares (nome, caminho)) que correspondem a ``filtro``.

    - Sem filtro (ou "todos"): todos os itens.
    - Nome igual ou contido (sem acentos/maiúsculas), nos dois sentidos.
    - Pelos números como números inteiros: "2" casa "2 PAVIMENTO", mas não "12 PAVIMENTO".
    - "terreo"/"cobertura"/"tipo" etc. por palavra.
    Sem correspondência devolve lista vazia: quem chama decide o erro (nunca "todos").
    """
    f = remover_acentos(filtro or "").strip()
    f = re.sub(r"^(?:no|do|da|piso|pavimento)\s+", "", f).strip()
    if f in FILTROS_TODOS:
        return list(itens)

    exatos = [(n, c) for n, c in itens if remover_acentos(n).strip() == f]
    if exatos:
        return exatos

    contidos = [(n, c) for n, c in itens if _contem(remover_acentos(n), f) or _contem(f, remover_acentos(n))]
    if contidos:
        return contidos

    nums_f = _numeros(f)
    if nums_f:
        return [(n, c) for n, c in itens if set(nums_f) & set(_numeros(n))]

    palavras = [p for p in re.split(r"[\s_\^\-]+", f) if len(p) > 2]
    return [(n, c) for n, c in itens if any(p in remover_acentos(n).split() or p in remover_acentos(n) for p in palavras)]


def mensagem_pavimento_nao_encontrado(filtro: str, itens: List[Tuple[str, str]]) -> str:
    nomes = ", ".join(n for n, _ in itens) or "(nenhum)"
    return f"Pavimento '{filtro}' não encontrado. Pavimentos disponíveis: {nomes}."
