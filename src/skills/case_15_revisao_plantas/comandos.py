"""
Reconhecimento de pedidos de revisão de plantas em linguagem natural (chat e orquestrador).

Exemplos:
    "emitir revisão da prancha 0601 do 054 AE"
    "nova revisão da 0601 descrição: ajuste do elevador"
    "emitir revisão da prancha 0601 na fase PE"
    "listar revisões das pranchas do 054 AE"
    "conferir revisão da 0601"
    "plotar a prancha 0601 em PDF"
"""
import re
from typing import Any, Dict, Optional

from src.tqs_adapter.model_editor import normalizar_texto

_PALAVRAS_REVISAO = ("REVISA", "REVISO")   # revisão/revisar/revisões (sem acento)
_PALAVRAS_ACAO = ("EMIT", "EMISS", "NOVA", "CONFER", "LIST", "QUAI", "MOSTR", "PRANCH", "REGISTR", "STATUS", "PENDENT")
_PALAVRAS_COMPARACAO = ("COMPAR", "DIFF", "SOBREPOSI", "DIFERENC")

RE_ID_PRANCHA = re.compile(r"\b\d{3}-[A-Z]{2,4}-[A-Z]{2}-\d{4}(?:-[A-Z0-9]+)*\b", re.I)
RE_PRANCHA_CONTEXTO = re.compile(r"(?:prancha|folha|planta)\s+(?:n[º°o.]*\s*)?(\d{3,4})\b", re.I)
RE_NUM_4 = re.compile(r"(?<![\d.-])(\d{4})(?![\d.-])")
RE_EDIFICIO = re.compile(r"(?<![\d.-])(0\d{2})(?![\d.-])(?:\s+(AE|CA)\b)?", re.I)
# Código de fase sempre em maiúsculas (PE, PB...), para não confundir com "fase do projeto"
RE_FASE = re.compile(r"\b(?i:fase)\s+(?:(?i:de|do|da|para)\s+)?([A-Z]{2})\b")
RE_DESCRICAO = re.compile(r"descri[cç][aã]o\s*[:=]?\s*[\"“'«]?(.+?)[\"”'»]?\s*$", re.I)
RE_AUTOR = re.compile(r"\bautor\s*[:=]?\s*[\"“']?([^\"”',;]+)", re.I)
RE_DATA = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")


def _pede_carimbo(cmd: str) -> bool:
    return "PREENCH" in cmd and any(k in cmd for k in ("CARIMB", "SELO", "PRANCH"))


def _pede_plotagem(cmd: str) -> bool:
    return ("PLOT" in cmd or ("PDF" in cmd and any(k in cmd for k in ("GER", "EXPORT", "EMIT")))) \
        and any(k in cmd for k in ("PRANCH", "PDF", "REVIS", "FOLHA"))


def eh_pedido_revisao(comando: str) -> bool:
    cmd = normalizar_texto(comando)
    if _pede_carimbo(cmd) or _pede_plotagem(cmd):
        return True
    return (any(k in cmd for k in _PALAVRAS_REVISAO)
            and any(k in cmd for k in _PALAVRAS_ACAO)
            and not any(k in cmd for k in _PALAVRAS_COMPARACAO))


def extrair_parametros_revisao(comando: str, edificio_padrao: Optional[str] = None) -> Dict[str, Any]:
    cmd = normalizar_texto(comando)
    params: Dict[str, Any] = {}

    if _pede_carimbo(cmd):
        params["acao"] = "preencher"
    elif _pede_plotagem(cmd):
        params["acao"] = "plotar"
    elif any(k in cmd for k in ("CONFER", "VERIFIC", "CHECA")):
        params["acao"] = "conferir"
    elif any(k in cmd for k in ("LIST", "QUAI", "MOSTR", "STATUS", "PENDENT")) and not any(k in cmd for k in ("EMIT", "NOVA", "REGISTR")):
        params["acao"] = "listar"
    else:
        params["acao"] = "emitir"

    # O texto da descrição sai do comando antes da busca por números/fase
    resto = comando
    m_desc = RE_DESCRICAO.search(comando)
    if m_desc:
        params["descricao"] = m_desc.group(1).strip()
        resto = comando[:m_desc.start()]

    m_id = RE_ID_PRANCHA.search(resto)
    if m_id:
        params["prancha"] = m_id.group(0).upper()
    else:
        m_ctx = RE_PRANCHA_CONTEXTO.search(resto)
        if m_ctx:
            params["prancha"] = m_ctx.group(1)
        else:
            m_num = RE_NUM_4.search(resto)
            if m_num:
                params["prancha"] = m_num.group(1)

    sem_prancha = resto.replace(params.get("prancha", "\0"), " ")
    m_ed = RE_EDIFICIO.search(sem_prancha)
    if m_ed:
        params["edificio_nome"] = m_ed.group(1) + (f" {m_ed.group(2).upper()}" if m_ed.group(2) else "")
    elif m_id:
        params["edificio_nome"] = m_id.group(0)[:3]   # o ID começa pelo código do projeto
    elif edificio_padrao:
        params["edificio_nome"] = edificio_padrao

    m_fase = RE_FASE.search(resto)
    if m_fase:
        params["fase"] = m_fase.group(1).upper()
    m_autor = RE_AUTOR.search(resto)
    if m_autor:
        params["autor"] = m_autor.group(1).strip()
    m_data = RE_DATA.search(resto)
    if m_data:
        params["data"] = m_data.group(1)
    if "SIMUL" in cmd:
        params["simular"] = True
    return params
