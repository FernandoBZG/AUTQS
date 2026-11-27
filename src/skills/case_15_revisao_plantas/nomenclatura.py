"""
Regras de nomenclatura de pranchas do TQS (NMCARQ.DAT) e leitura das variáveis
gravadas pela plotagem do Editor de Plantas (<ID>-Rnn.TXT).

ID de prancha observado no TQS: projeto-agente-fase-nº-pavimento-elemento,
ex.: 054-EST-PB-0601-TP-1FIA. A revisão é anexada como <prefixo><nn> (ex.: -R04).
"""
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

CODIF_TQS = "cp1252"

# Fases padrão, usadas apenas quando o edifício não tem NMCARQ.DAT
FASES_PADRAO = {
    "EP": "Estudo preliminar",
    "AP": "Anteprojeto",
    "PB": "Projeto básico",
    "PE": "Projeto executivo",
}


class ErroNomenclatura(Exception):
    """Erro de interpretação do ID de uma prancha."""


@dataclass
class RegrasNomenclatura:
    fases: Dict[str, str] = field(default_factory=lambda: dict(FASES_PADRAO))
    prefixo_revisao: str = "-R"
    digitos_revisao: int = 2
    origem: str = "padrao"

    def nome_arquivo_revisao(self, id_prancha: str, numero: int) -> str:
        """Nome base que o TQS usa nas saídas da plotagem (ex.: 054-EST-PB-0601-TP-1FIA-R05)."""
        return f"{id_prancha}{self.prefixo_revisao}{numero:0{self.digitos_revisao}d}"

    def rotulo_revisao(self, numero: int) -> str:
        return f"R{numero:0{self.digitos_revisao}d}"


def _ler_texto(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return f.read().decode(CODIF_TQS, errors="replace")


def ler_nmcarq(caminho_edificio: str) -> RegrasNomenclatura:
    """Lê fases e a regra de revisão do NMCARQ.DAT do edifício (fallback: padrões TQS)."""
    caminho = os.path.join(caminho_edificio, "NMCARQ.DAT")
    if not os.path.exists(caminho):
        return RegrasNomenclatura()

    texto = _ler_texto(caminho)
    regras = RegrasNomenclatura(fases={}, origem=caminho)

    bloco_rev = re.search(r"<REVISAO>(.*?)</REVISAO>", texto, re.S | re.I)
    if bloco_rev:
        m_pref = re.search(r"Prefixo=([^\r\n]*)", bloco_rev.group(1))
        m_ncar = re.search(r"NCaract=(\d+)", bloco_rev.group(1))
        if m_pref:
            regras.prefixo_revisao = m_pref.group(1).strip() or regras.prefixo_revisao
        if m_ncar and int(m_ncar.group(1)) > 0:
            regras.digitos_revisao = int(m_ncar.group(1))

    bloco_fases = re.search(r"<Fases>(.*?)</Fases>", texto, re.S | re.I)
    if bloco_fases:
        for codigo, nome in re.findall(r"<([A-Za-z0-9]+)>\s*<([^<>]+)>\s*</\1>", bloco_fases.group(1)):
            regras.fases[codigo.upper()] = nome.strip()

    if not regras.fases:
        regras.fases = dict(FASES_PADRAO)
    return regras


@dataclass
class IdPrancha:
    id: str
    tokens: List[str]
    indice_fase: int

    @property
    def fase(self) -> str:
        return self.tokens[self.indice_fase]

    @property
    def numero(self) -> str:
        """Número da prancha (token logo após a fase, ex.: '0601')."""
        if self.indice_fase + 1 < len(self.tokens):
            return self.tokens[self.indice_fase + 1]
        return ""

    def com_fase(self, nova_fase: str) -> str:
        novos = list(self.tokens)
        novos[self.indice_fase] = nova_fase.upper()
        return "-".join(novos)


def decompor_id(id_prancha: str, regras: RegrasNomenclatura) -> IdPrancha:
    """Separa o ID da prancha em tokens e localiza o código da fase."""
    tokens = id_prancha.split("-")
    codigos = {c.upper() for c in regras.fases}
    for i, tok in enumerate(tokens[1:], start=1):
        if tok.upper() in codigos:
            return IdPrancha(id=id_prancha, tokens=tokens, indice_fase=i)
    raise ErroNomenclatura(
        f"Não encontrei o código de fase ({', '.join(sorted(codigos))}) no ID da prancha '{id_prancha}'."
    )


def trocar_fase(id_prancha: str, nova_fase: str, regras: RegrasNomenclatura) -> str:
    nova = nova_fase.upper()
    if nova not in {c.upper() for c in regras.fases}:
        raise ErroNomenclatura(
            f"Fase '{nova_fase}' não está cadastrada no NMCARQ.DAT ({', '.join(sorted(regras.fases))})."
        )
    return decompor_id(id_prancha, regras).com_fase(nova)


# ---------------------------------------------------------------------------
# Saídas da plotagem do Editor de Plantas (<ID>-Rnn.TXT/.PDF/.DXF/.PLW)
# ---------------------------------------------------------------------------

def ler_variaveis_plotagem(caminho_txt: str) -> Dict[str, str]:
    """Lê o TXT de variáveis gravado pela plotagem (linhas 'VARIAVEL,valor')."""
    variaveis: Dict[str, str] = {}
    for linha in _ler_texto(caminho_txt).splitlines():
        if "," not in linha:
            continue
        chave, valor = linha.split(",", 1)
        variaveis[chave.strip()] = valor.strip()
    return variaveis


def localizar_saida_plotagem(pasta_plantas: str, id_prancha: str, numero: int,
                             regras: RegrasNomenclatura, extensao: str) -> Optional[str]:
    caminho = os.path.join(pasta_plantas, regras.nome_arquivo_revisao(id_prancha, numero) + extensao)
    return caminho if os.path.exists(caminho) else None


def nome_fase_esperado(pasta_plantas: str, codigo_fase: str, regras: RegrasNomenclatura,
                       ignorar: Optional[str] = None) -> str:
    """
    Valor esperado de _FASE para a fase: o último valor usado em pranchas dessa fase
    (aprende, por exemplo, PB = "PROJETO BÁSICO"), ou o nome do NMCARQ em maiúsculas.
    `ignorar`: TXT que não deve servir de referência (o próprio TXT sob conferência).
    """
    codigo = codigo_fase.upper()
    candidatos = []
    # os.listdir (e não glob): pastas do TQS têm colchetes no nome, ex.: "[054]"
    arquivos = os.listdir(pasta_plantas) if os.path.isdir(pasta_plantas) else []
    for arq in arquivos:
        if not arq.upper().endswith(".TXT"):
            continue
        txt = os.path.join(pasta_plantas, arq)
        if ignorar and os.path.normcase(os.path.abspath(txt)) == os.path.normcase(os.path.abspath(ignorar)):
            continue
        nome = os.path.splitext(arq)[0]
        try:
            id_txt = re.sub(re.escape(regras.prefixo_revisao) + r"\d+$", "", nome)
            if decompor_id(id_txt, regras).fase.upper() != codigo:
                continue
        except ErroNomenclatura:
            continue
        candidatos.append((os.path.getmtime(txt), txt))

    for _, txt in sorted(candidatos, reverse=True):
        valor = ler_variaveis_plotagem(txt).get("_FASE", "")
        if valor:
            return valor
    return regras.fases.get(codigo, codigo).upper()
