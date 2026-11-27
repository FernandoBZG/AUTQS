"""
Preenchimento do carimbo da prancha (<ID>_CR.DWG), equivalente ao botão "Preencher" do
Editor de Plantas do TQS.

Regra observada no _CR.DWG gerado pelo próprio TQS (054 AE, prancha 0601):
- parte da moldura oficial do formato (PLANTAS.DAT → C:\\TQSW\\SUPORTE\\NGE\\MOLDURAS\\<formato>.DWG);
- cada texto "%VARIAVEL" vira o valor, no mesmo nível, posição, altura, ângulo e alinhamento;
- variáveis sem valor são apagadas (ex.: linhas de revisão ainda não usadas, %ESCALA vazia);
- %PECASDET é quebrado em linhas de até ~40 caracteres, começando 0,3 cm abaixo da variável
  e descendo 0,3 cm por linha (o TQS agrupa essas linhas num objeto IPOCOT; aqui elas são
  textos simples, que plotam igual).

Valores: os do carimbo preenchido anterior (inclui as variáveis digitadas no editor, como
_FASE, _PAVIMENTO e _DISCIPLINA), com fallback no último TXT da plotagem; por cima, os que
vêm do .CPL (tabela de revisões, %REVISAO, %PLANTA, %NUM_PLANTA) e os títulos dos desenhos
(%PECASDET).
"""
import os
import re
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.skills.case_15_revisao_plantas.cpl import PlantaCPL, TIPO_CARIMBO
from src.skills.case_15_revisao_plantas.nomenclatura import (
    ErroNomenclatura, RegrasNomenclatura, decompor_id, ler_variaveis_plotagem, localizar_saida_plotagem,
)

PASTA_MOLDURAS_PADRAO = r"C:\TQSW\SUPORTE\NGE\MOLDURAS"
NIVEL_TITULO_DESENHO = 222
VAR_PECASDET = "PECASDET"
ESPACO_LINHAS = 0.3
MAX_CARACTERES_LINHA = 40
TOLERANCIA_POSICAO = 0.02
LINHAS_TABELA = 11
# Não ler iterator.textAlignment: na DLL do TQS V25 a variável "ialintxt" não existe e cada
# leitura escreve "g_extgra_ler_int [ialintxt] indefinido" na janela de mensagens do TQS aberto.
# Todas as variáveis das molduras oficiais são alinhadas à esquerda (0).
ALINHAMENTO_ESQUERDA = 0


@dataclass
class VariavelMoldura:
    nome: str
    x: float
    y: float
    altura: float
    angulo: float
    nivel: int
    alinhamento: int
    cor: int


def _tqsdwg():
    import src.tqs_adapter.tqs_env  # noqa: F401
    from TQS import TQSDwg
    return TQSDwg


def _definir_alinhamento(dwg, alinhamento: int) -> None:
    """Alinhamento esquerdo (0) é o padrão; o setter falha em algumas versões da DLL do TQS."""
    if not alinhamento:
        return
    try:
        dwg.draw.textAlignment = alinhamento
    except AttributeError:
        pass


def caminho_moldura(caminho_edificio: str, formato: str) -> str:
    """Moldura do formato conforme o PLANTAS.DAT do edifício (fallback: pasta padrão do TQS)."""
    caminho_dat = os.path.join(caminho_edificio, "PLANTAS.DAT")
    if os.path.exists(caminho_dat):
        with open(caminho_dat, "rb") as f:
            linhas = [l.strip() for l in f.read().decode("cp1252", errors="replace").splitlines()]
        for i, linha in enumerate(linhas):
            if linha.upper() == formato.upper() and i + 2 < len(linhas):
                candidato = linhas[i + 2]
                if not os.path.splitext(candidato)[1]:
                    candidato += ".DWG"
                if os.path.exists(candidato):
                    return candidato
    padrao = os.path.join(PASTA_MOLDURAS_PADRAO, formato + ".DWG")
    if os.path.exists(padrao):
        return padrao
    raise FileNotFoundError(f"Moldura do formato '{formato}' não encontrada (PLANTAS.DAT nem {PASTA_MOLDURAS_PADRAO}).")


def _ler_textos(caminho_dwg: str) -> List[Tuple[int, float, float, float, float, int, int, str]]:
    """(endereço, x, y, altura, ângulo, nível, alinhamento, texto) de todos os textos do desenho."""
    TQSDwg = _tqsdwg()
    dwg = TQSDwg.Dwg(pedmv=0)
    if dwg.file.Open(caminho_dwg) != 0:
        raise FileNotFoundError(f"Não consegui abrir {caminho_dwg}")
    textos = []
    it = dwg.iterator
    it.Begin()
    try:
        while True:
            pos = it.GetElementReadPosition()
            if pos and it.elementName == "Texto":
                textos.append((pos, it.x1, it.y1, it.textHeight, it.textAngle, it.level,
                               ALINHAMENTO_ESQUERDA, it.text or ""))
            if not it.Next():
                break
    finally:
        dwg.file.Close()
    return textos


def ler_variaveis_moldura(caminho: str) -> List[VariavelMoldura]:
    TQSDwg = _tqsdwg()
    dwg = TQSDwg.Dwg(pedmv=0)
    if dwg.file.Open(caminho) != 0:
        raise FileNotFoundError(f"Não consegui abrir {caminho}")
    variaveis = []
    it = dwg.iterator
    it.Begin()
    try:
        while True:
            pos = it.GetElementReadPosition()
            if pos and it.elementName == "Texto" and (it.text or "").strip().startswith("%"):
                try:
                    cor = dwg.edit._Edit__LerAtribElem(pos)[0]
                except Exception:
                    cor = -1
                variaveis.append(VariavelMoldura(
                    nome=it.text.strip()[1:], x=it.x1, y=it.y1, altura=it.textHeight, angulo=it.textAngle,
                    nivel=it.level, alinhamento=ALINHAMENTO_ESQUERDA, cor=cor))
            if not it.Next():
                break
    finally:
        dwg.file.Close()
    return variaveis


def quebrar_linhas(texto: str, maximo: int = MAX_CARACTERES_LINHA) -> List[str]:
    """Quebra por palavras como o TQS: cada linha (exceto a última) mantém o espaço final."""
    linhas, atual = [], ""
    for palavra in texto.split(" "):
        candidato = f"{atual}{palavra}" if not atual else f"{atual} {palavra}"
        if atual and len(candidato) > maximo:
            linhas.append(atual + " ")
            atual = palavra
        else:
            atual = candidato
    if atual:
        linhas.append(atual)
    return linhas


def valores_do_carimbo_existente(caminho_cr: str, variaveis: List[VariavelMoldura]) -> Dict[str, str]:
    """Valor de cada variável no carimbo já preenchido (texto na mesma posição da variável)."""
    textos = _ler_textos(caminho_cr)
    valores: Dict[str, str] = {}
    for v in variaveis:
        if v.nome == VAR_PECASDET:
            partes = []
            for k in range(1, 6):
                y = v.y - k * ESPACO_LINHAS
                achado = next((t[7] for t in textos
                               if abs(t[1] - v.x) <= TOLERANCIA_POSICAO and abs(t[2] - y) <= TOLERANCIA_POSICAO), None)
                if achado is None:
                    break
                partes.append(achado)
            valores[v.nome] = " ".join("".join(partes).split())
            continue
        achado = next((t[7] for t in textos
                       if abs(t[1] - v.x) <= TOLERANCIA_POSICAO and abs(t[2] - v.y) <= TOLERANCIA_POSICAO
                       and not t[7].strip().startswith("%")), None)
        valores[v.nome] = achado.strip() if achado else ""
    return valores


def titulos_dos_desenhos(pl: PlantaCPL) -> str:
    titulos = []
    for d in pl.desenhos_conteudo():
        caminho = d.caminho_absoluto(pl.pasta)
        if not os.path.exists(caminho):
            continue
        for t in _ler_textos(caminho):
            if t[5] == NIVEL_TITULO_DESENHO and t[7].strip() and t[7].strip() not in titulos:
                titulos.append(t[7].strip())
    return " / ".join(titulos)


def _caminho_carimbo(pl: PlantaCPL) -> Optional[str]:
    for d in pl.desenhos():
        if d.tipo == TIPO_CARIMBO:
            return d.caminho_absoluto(pl.pasta)
    return None


def montar_valores(pl: PlantaCPL, regras: RegrasNomenclatura, variaveis: List[VariavelMoldura]) -> Dict[str, str]:
    valores: Dict[str, str] = {}

    # 1) Último TXT de plotagem desta prancha (fallback para o que não estiver no carimbo)
    if pl.revisao_atual is not None:
        for n in range(pl.revisao_atual, -1, -1):
            txt = localizar_saida_plotagem(pl.pasta, pl.id, n, regras, ".TXT")
            if txt:
                valores.update(ler_variaveis_plotagem(txt))
                break

    # 2) Carimbo preenchido anterior: traz as variáveis digitadas no editor (_FASE etc.)
    cr = _caminho_carimbo(pl)
    if cr and os.path.exists(cr):
        for nome, valor in valores_do_carimbo_existente(cr, variaveis).items():
            if valor or nome not in valores:
                valores[nome] = valor

    # 3) O que vem do .CPL e dos desenhos sempre prevalece
    revs = {r.numero: r for r in pl.revisoes}
    for n in range(LINHAS_TABELA):
        sufixo = f"{n:02d}"
        r = revs.get(n)
        valores[f"REVISAO_TXT{sufixo}"] = r.descricao if r else ""
        valores[f"REVISAO_AUT{sufixo}"] = r.autor if r else ""
        valores["REVISAO_DAT010" if n == 10 else f"REVISAO_DAT{sufixo}"] = r.data if r else ""
    if pl.revisao_atual is not None:
        valores["REVISAO"] = f"{pl.revisao_atual:0{regras.digitos_revisao}d}"
        valores["PLANTA"] = regras.nome_arquivo_revisao(pl.id, pl.revisao_atual)
    try:
        valores["NUM_PLANTA"] = decompor_id(pl.id, regras).numero
    except ErroNomenclatura:
        pass
    valores["TITULO_PLANTA"] = pl.titulo
    titulos = titulos_dos_desenhos(pl)
    if titulos:
        valores[VAR_PECASDET] = titulos
    return valores


def preencher_carimbo(pl: PlantaCPL, regras: RegrasNomenclatura, caminho_edificio: str,
                      destino: str) -> Dict[str, object]:
    """Gera o carimbo preenchido em `destino` a partir da moldura do formato da prancha."""
    moldura = caminho_moldura(caminho_edificio, pl.formato_folha)
    variaveis = ler_variaveis_moldura(moldura)
    valores = montar_valores(pl, regras, variaveis)

    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
    shutil.copy2(moldura, destino)
    TQSDwg = _tqsdwg()
    dwg = TQSDwg.Dwg(pedmv=0)
    if dwg.file.Open(destino) != 0:
        raise FileNotFoundError(f"Não consegui abrir a cópia da moldura {destino}")

    preenchidas, apagadas = {}, []
    try:
        enderecos = []
        it = dwg.iterator
        it.Begin()
        while True:
            pos = it.GetElementReadPosition()
            if pos and it.elementName == "Texto" and (it.text or "").strip().startswith("%"):
                enderecos.append((pos, it.text.strip()[1:], it.x1, it.y1))
            if not it.Next():
                break
        props = {(round(v.x, 3), round(v.y, 3), v.nome): v for v in variaveis}

        for pos, nome, x, y in enderecos:
            dwg.edit.Erase(pos)
            v = props.get((round(x, 3), round(y, 3), nome))
            valor = (valores.get(nome) or "").strip()
            if v is None or not valor:
                apagadas.append(nome)
                continue
            dwg.draw.level = v.nivel
            dwg.draw.color = v.cor
            _definir_alinhamento(dwg, v.alinhamento)
            if nome == VAR_PECASDET:
                for k, linha in enumerate(quebrar_linhas(valor), start=1):
                    dwg.draw.Text(v.x, v.y - k * ESPACO_LINHAS, v.altura, v.angulo, linha)
            else:
                dwg.draw.Text(v.x, v.y, v.altura, v.angulo, valor)
            preenchidas[nome] = valor
            _definir_alinhamento(dwg, 0)
        dwg.file.Save()
    finally:
        dwg.file.Close()

    return {"caminho": destino, "moldura": moldura, "preenchidas": preenchidas,
            "apagadas": sorted(set(apagadas)), "valores": valores}
