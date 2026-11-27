"""
Plotagem em PDF de uma prancha do Editor de Plantas sem abrir o TQS.

O Editor de Plantas (e o TQSDwg.file.SaveAs(".PDF")) plota com o NCVRPLD.EXE, o motor
de plotagem do TQS: ele roda na pasta de trabalho e lê nela o SELDWG.TMP (lista de
plantas a plotar) e o NCVRPLD.TMP; ao terminar, grava "OK" no EXTDWG.TMP e o PDF
<ID>-Rnn.PDF ao lado do .CPL. O motor não preenche as variáveis da moldura: o carimbo
<ID>_CR.DWG precisa estar preenchido antes (o botão "Preencher" do editor), o que aqui é
feito por carimbo.preencher_carimbo.

Para não tocar no edifício, tudo acontece numa pasta temporária:
    <trabalho>\\edif\\PLANTAS\\<ID>.CPL      cópia do .CPL com caminhos absolutos
    <trabalho>\\edif\\PLANTAS\\<ID>_CR.DWG   carimbo preenchido pelo AUTQS
    <trabalho>\\edif\\desenho\\              pasta de trabalho do motor (*.TMP)
Os desenhos do edifício são só lidos. Na R05 da 054-EST-PB-0601-TP-1FIA o PDF gerado
assim ficou idêntico ao do Editor de Plantas (1200 dpi), exceto a hora no carimbo de plotagem.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
import winreg
from typing import Any, Dict, List, Optional

from src.skills.case_15_revisao_plantas.cpl import TIPO_CARIMBO, PlantaCPL, _para_arquivo
from src.skills.case_15_revisao_plantas.nomenclatura import RegrasNomenclatura

EXECUTAVEL_MOTOR = "NCVRPLD.EXE"
ARQUIVOS_CONFIG_EDIFICIO = ("PLANTAS.DAT", "NMCARQ.DAT")
TIMEOUT_PADRAO_S = 600
CM = 72 / 2.54
TOLERANCIA_PAGINA_CM = 0.1


class ErroPlotagem(Exception):
    """Falha ao plotar a prancha com o motor do TQS."""


def _norm(texto: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn")
    return " ".join(sem_acento.upper().split())


def localizar_motor() -> str:
    """Caminho do NCVRPLD.EXE (64 bits) da instalação do TQS."""
    pastas = []
    for hroot in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for fv in (winreg.KEY_READ | winreg.KEY_WOW64_64KEY, winreg.KEY_READ | winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hroot, r"SOFTWARE\TQS", 0, fv) as chave:
                    pastas.append(winreg.QueryValueEx(chave, "Programas")[0])
            except OSError:
                pass
    pastas += [fr"{d}:\TQSW\EXEC" for d in "CDEF"]
    for pasta in pastas:
        for cand in (os.path.join(pasta, "X64", EXECUTAVEL_MOTOR), os.path.join(pasta, EXECUTAVEL_MOTOR)):
            if os.path.isfile(cand):
                return cand
    raise ErroPlotagem(f"{EXECUTAVEL_MOTOR} (motor de plotagem do TQS) não encontrado na instalação do TQS.")


def _dimensoes_folha(pl: PlantaCPL) -> Optional[tuple]:
    toks = pl.linhas[0].split()
    try:
        return float(toks[7]), float(toks[8])
    except (IndexError, ValueError):
        return None


def montar_pasta_plotagem(pl: PlantaCPL, regras: RegrasNomenclatura, caminho_edificio: str,
                          pasta_trabalho: str) -> Dict[str, Any]:
    """Monta a cópia da prancha (carimbo preenchido + .CPL com caminhos absolutos) na pasta de trabalho."""
    from src.skills.case_15_revisao_plantas import carimbo as cb

    desenho = os.path.join(pasta_trabalho, "edif", "desenho")
    plantas = os.path.join(pasta_trabalho, "edif", "PLANTAS")
    os.makedirs(desenho, exist_ok=True)
    os.makedirs(plantas, exist_ok=True)
    for nome in ARQUIVOS_CONFIG_EDIFICIO:
        origem = os.path.join(caminho_edificio, nome)
        if os.path.isfile(origem):
            shutil.copy2(origem, os.path.join(pasta_trabalho, "edif", nome))

    copia = pl.copiar_para(os.path.join(plantas, pl.id + ".CPL"))
    carimbo = None
    faltando = []
    for d in pl.desenhos():
        alvo = d.caminho_absoluto(pl.pasta)
        if d.tipo == TIPO_CARIMBO:
            carimbo = cb.preencher_carimbo(pl, regras, caminho_edificio, os.path.join(plantas, os.path.basename(alvo)))
            alvo = carimbo["caminho"]
        elif not os.path.isfile(alvo):
            faltando.append(alvo)
        copia.linhas[d.indice_linha] = _para_arquivo(os.path.splitext(alvo)[0])
    if faltando:
        raise ErroPlotagem("Desenho(s) da prancha não encontrado(s): " + "; ".join(faltando))
    copia.salvar()
    return {"pasta_trabalho": pasta_trabalho, "pasta_desenho": desenho, "pasta_plantas": plantas,
            "cpl": copia.caminho, "carimbo": carimbo}


def executar_motor(cpl: str, pasta_desenho: str, timeout: int = TIMEOUT_PADRAO_S) -> str:
    """Roda o NCVRPLD.EXE sobre um .CPL; devolve o conteúdo do EXTDWG.TMP ("OK" em caso de sucesso)."""
    nome = os.path.splitext(cpl)[0]
    sel = f"{1:>10}\n{1.0:>10.3f}\n{nome}\n*{nome}\n\n{0:>10}\n{1:>10}\n\n{1:>10}\n"
    with open(os.path.join(pasta_desenho, "SELDWG.TMP"), "w", encoding="cp1252") as f:
        f.write(sel)
    with open(os.path.join(pasta_desenho, "NCVRPLD.TMP"), "w", encoding="cp1252") as f:
        f.write("1\n1\n")
    status_arq = os.path.join(pasta_desenho, "EXTDWG.TMP")
    if os.path.exists(status_arq):
        os.remove(status_arq)
    try:
        subprocess.run([localizar_motor()], cwd=pasta_desenho, capture_output=True, timeout=timeout,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise ErroPlotagem(f"O motor de plotagem não terminou em {timeout} s.")
    if not os.path.exists(status_arq):
        return ""
    with open(status_arq, encoding="cp1252", errors="replace") as f:
        return f.read().strip()


def _textos_pdf(caminho: str) -> List[Dict[str, Any]]:
    import fitz
    with fitz.open(caminho) as doc:
        pg = doc[0]
        spans = [{"texto": s["text"], "origem": s["origin"]}
                 for b in pg.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
        return [{"pagina_cm": (pg.rect.width / CM, pg.rect.height / CM)}] + spans


def verificar_pdf(pdf: str, pl: PlantaCPL, regras: RegrasNomenclatura, numero: int) -> List[Dict[str, Any]]:
    """Checagens do PDF plotado: carimbo de plotagem, tamanho da folha, variáveis e tabela de revisões."""
    try:
        dados = _textos_pdf(pdf)
    except ImportError:
        return [{"item": "Leitura do PDF", "ok": True, "detalhe": "PyMuPDF não instalado; conteúdo não conferido"}]
    pagina, spans = dados[0]["pagina_cm"], dados[1:]
    textos = [s["texto"] for s in spans]
    normal = {_norm(t) for t in textos}
    checagens = []

    def checar(item: str, ok: bool, detalhe: str):
        checagens.append({"item": item, "ok": bool(ok), "detalhe": detalhe})

    nome = regras.nome_arquivo_revisao(pl.id, numero)
    carimbo_plot = next((t for t in textos if ".PLT" in t.upper()), "")
    checar("Carimbo de plotagem", f"{nome}.PLT".upper() in carimbo_plot.upper(), carimbo_plot or "(não encontrado)")
    folha = _dimensoes_folha(pl)
    if folha:
        ok = all(abs(a - b) <= TOLERANCIA_PAGINA_CM for a, b in zip(pagina, folha))
        checar("Tamanho da página", ok, f"{pagina[0]:.2f} x {pagina[1]:.2f} cm / folha {folha[0]:.2f} x {folha[1]:.2f} cm")
    variaveis = sorted({t.strip() for t in textos if re.match(r"\s*%[A-Z_]", t)})
    checar("Variáveis da moldura substituídas", not variaveis, ", ".join(variaveis[:8]) or "nenhuma %VARIÁVEL no PDF")
    faltam = [r for r in pl.revisoes if _norm(r.descricao) not in normal or r.data not in textos]
    checar("Tabela de revisões", not faltam,
           f"{len(pl.revisoes)} linha(s) no PDF" if not faltam else
           "faltam: " + ", ".join(regras.rotulo_revisao(r.numero) for r in faltam))
    return checagens


def plotar_prancha(pl: PlantaCPL, regras: RegrasNomenclatura, caminho_edificio: str,
                   pasta_trabalho: Optional[str] = None, timeout: int = TIMEOUT_PADRAO_S) -> Dict[str, Any]:
    """Plota a revisão atual da prancha em PDF numa pasta temporária (nada é gravado no edifício)."""
    numero = pl.revisao_atual
    if numero is None:
        raise ErroPlotagem(f"{pl.id} não tem revisões registradas; emita a R00 antes de plotar.")
    trabalho = pasta_trabalho or tempfile.mkdtemp(prefix="AUTQS_plot_")
    montagem = montar_pasta_plotagem(pl, regras, caminho_edificio, trabalho)
    status = executar_motor(montagem["cpl"], montagem["pasta_desenho"], timeout)
    nome = regras.nome_arquivo_revisao(pl.id, numero)
    pdf = os.path.join(montagem["pasta_plantas"], nome + ".PDF")
    if status.upper() != "OK" or not os.path.isfile(pdf):
        gerados = [f for f in os.listdir(montagem["pasta_plantas"]) if f.upper().endswith(".PDF")]
        raise ErroPlotagem(f"O motor de plotagem do TQS não gerou {nome}.PDF (status: {status or 'vazio'}; "
                           f"PDFs gerados: {', '.join(gerados) or 'nenhum'}). Pasta de trabalho: {trabalho}")
    return {"pdf": pdf, "nome_saida": nome, "numero": numero, "checagens": verificar_pdf(pdf, pl, regras, numero),
            **montagem}
