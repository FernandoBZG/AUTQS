"""
Leitura e gravação byte a byte das plantas (.CPL) do Editor de Plantas do TQS.

Estrutura observada (TQS V25, texto CP1252):
    linha 1   cabeçalho: formato da folha + campos numéricos; o token 13 é a revisão
              atual (%REVISAO) e o token 14 é a quantidade de revisões
    ---V14.0---
    ---V14.0---
    <projetista>              (NOME_PROJETISTA, normalmente vazio)
    <título da planta>        (TITULO_PLANTA)
    4 linhas por revisão:     "    n" / "dd/mm/aaaa" / autor / descrição
    <linhas finais>           (ex.: "    0")
    --EOC--
    desenhos: caminho / escala+título / janela+inserção+tipo / pavimento /
              3 linhas com a máscara dos 256 níveis / "#"

Toda edição é cirúrgica: o arquivo é lido como latin-1 (um caractere por byte) e
só as linhas tocadas mudam, de modo que ler + salvar sem alterações devolve
exatamente os mesmos bytes.
"""
import copy
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

CODIF_BYTES = "latin-1"   # ida e volta sem perda de nenhum byte
CODIF_TQS = "cp1252"      # codificação dos textos do TQS
MARCA_FIM_CARIMBO = "--EOC--"
IDX_TOKEN_REV_ATUAL = 13
IDX_TOKEN_NUM_REVISOES = 14
LINHA_TITULO = 4          # índice 0-based da linha do título
LINHA_PRIMEIRA_REVISAO = 5
MAX_LINHAS_TABELA = 11    # a moldura oficial tem as linhas 00..10
MAX_CARACTERES_DESCRICAO = 60
# Aceita datas digitadas com ano incompleto no Editor de Plantas (ex.: "25/10/204" no Zuckhan):
# o histórico é só lido e regravado como está; datas novas continuam saindo em dd/mm/aaaa.
RE_DATA = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
RE_DATA_NOVA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_NUMERO = re.compile(r"^\s*\d+\s*$")
TIPO_DESENHO = 0
TIPO_CARIMBO = 2
TIPO_SELO = 5


class ErroCPL(Exception):
    """Arquivo .CPL com estrutura inesperada ou edição inválida."""


def _para_exibicao(texto_bytes_latin1: str) -> str:
    """Converte uma linha lida (latin-1 1:1) para texto legível (CP1252)."""
    return texto_bytes_latin1.encode(CODIF_BYTES).decode(CODIF_TQS, errors="replace")


def _para_arquivo(texto: str) -> str:
    """Converte texto novo para a representação latin-1 dos bytes CP1252."""
    try:
        return texto.encode(CODIF_TQS).decode(CODIF_BYTES)
    except UnicodeEncodeError as e:
        raise ErroCPL(f"O texto '{texto}' tem caracteres que o TQS (CP1252) não grava: {e.object[e.start:e.end]!r}")


@dataclass
class Revisao:
    numero: int
    data: str
    autor: str
    descricao: str

    def linhas_arquivo(self) -> List[str]:
        return [
            f"{self.numero:5d}",
            _para_arquivo(self.data),
            _para_arquivo(self.autor),
            _para_arquivo(self.descricao),
        ]


@dataclass
class DesenhoCPL:
    caminho_relativo: str
    escala: float
    titulo: str
    janela_x0: float
    janela_y0: float
    insercao_x: float
    insercao_y: float
    largura: float
    altura: float
    tipo: int
    pavimento: str
    mascara_niveis: str
    indice_linha: int = -1      # linha do caminho no .CPL (0-based)

    def nivel_visivel(self, nivel: int) -> bool:
        if 0 <= nivel < len(self.mascara_niveis):
            return self.mascara_niveis[nivel] == "1"
        return True

    def para_folha(self, x: float, y: float) -> Tuple[float, float]:
        """Coordenada do desenho (cm de modelo) para a folha (cm de papel)."""
        esc = self.escala or 1.0
        return ((x - self.janela_x0) / esc + self.insercao_x, (y - self.janela_y0) / esc + self.insercao_y)

    def caminho_absoluto(self, pasta_plantas: str) -> str:
        caminho = self.caminho_relativo
        if not os.path.isabs(caminho):
            caminho = os.path.normpath(os.path.join(pasta_plantas, caminho))
        if not os.path.splitext(caminho)[1]:
            caminho += ".DWG"
        return caminho


@dataclass
class PlantaCPL:
    caminho: str
    linhas: List[str]
    separador: str
    revisoes: List[Revisao] = field(default_factory=list)
    indice_fim_revisoes: int = LINHA_PRIMEIRA_REVISAO
    indice_eoc: int = -1

    # ------------------------------------------------------------------ leitura
    @property
    def id(self) -> str:
        return os.path.splitext(os.path.basename(self.caminho))[0]

    @property
    def pasta(self) -> str:
        return os.path.dirname(self.caminho)

    @property
    def formato_folha(self) -> str:
        toks = self._tokens_cabecalho()
        return toks[0][2] if toks else ""

    @property
    def titulo(self) -> str:
        return _para_exibicao(self.linhas[LINHA_TITULO]).strip()

    @property
    def titulo_com_caractere_invalido(self) -> bool:
        return "�" in self.titulo or "ï¿½" in self.linhas[LINHA_TITULO]

    @property
    def revisao_atual(self) -> Optional[int]:
        if not self.revisoes:
            return None
        return int(self._tokens_cabecalho()[IDX_TOKEN_REV_ATUAL][2])

    @property
    def ultima_revisao(self) -> Optional[Revisao]:
        return self.revisoes[-1] if self.revisoes else None

    def proximo_numero(self) -> int:
        return (self.revisoes[-1].numero + 1) if self.revisoes else 0

    def desenhos(self) -> List[DesenhoCPL]:
        """Entradas de desenho após o --EOC-- (desenho, carimbo _CR, selo da empresa)."""
        resultado = []
        i = self.indice_eoc + 1
        while i + 6 < len(self.linhas):
            caminho = self.linhas[i].strip()
            if not caminho or caminho == "#":
                i += 1
                continue
            try:
                linha_escala = self.linhas[i + 1]
                escala = float(linha_escala.split()[0])
                titulo = _para_exibicao(" ".join(linha_escala.split()[5:]))
                nums = self.linhas[i + 2].split()
                mascara = "".join(self.linhas[i + 4 + k].strip() for k in range(3))
                resultado.append(DesenhoCPL(
                    caminho_relativo=_para_exibicao(caminho),
                    escala=escala,
                    titulo=titulo,
                    janela_x0=float(nums[0]),
                    janela_y0=float(nums[1]),
                    insercao_x=float(nums[2]),
                    insercao_y=float(nums[3]),
                    largura=float(nums[4]),
                    altura=float(nums[5]),
                    tipo=int(nums[9]),
                    pavimento=_para_exibicao(self.linhas[i + 3]).strip(),
                    mascara_niveis=mascara,
                    indice_linha=i,
                ))
            except (ValueError, IndexError) as e:
                raise ErroCPL(f"Entrada de desenho inesperada na linha {i + 1} de {self.caminho}: {e}")
            i += 7
            while i < len(self.linhas) and self.linhas[i].strip() == "#":
                i += 1
        return resultado

    def desenhos_conteudo(self) -> List[DesenhoCPL]:
        return [d for d in self.desenhos() if d.tipo == TIPO_DESENHO]

    # ------------------------------------------------------------------ edição
    def _tokens_cabecalho(self) -> List[Tuple[int, int, str]]:
        return [(m.start(), m.end(), m.group(0)) for m in re.finditer(r"\S+", self.linhas[0])]

    def _definir_token_cabecalho(self, indice: int, valor: int) -> None:
        toks = self._tokens_cabecalho()
        inicio_campo = toks[indice - 1][1] if indice > 0 else 0
        fim = toks[indice][1]
        novo = str(valor)
        largura = fim - inicio_campo
        if len(novo) >= largura:
            raise ErroCPL(f"O valor {valor} não cabe no campo {indice} do cabeçalho de {self.caminho}.")
        linha = self.linhas[0]
        self.linhas[0] = linha[:inicio_campo] + novo.rjust(largura) + linha[fim:]

    def validar_revisao(self, rev: Revisao) -> List[str]:
        """Erros impeditivos e avisos (prefixo 'AVISO:') para a revisão proposta."""
        problemas = []
        if rev.numero != self.proximo_numero():
            problemas.append(f"A próxima revisão desta prancha é R{self.proximo_numero():02d}, não R{rev.numero:02d}.")
        if rev.numero >= MAX_LINHAS_TABELA:
            problemas.append(
                f"A tabela de revisões da moldura tem só {MAX_LINHAS_TABELA} linhas (R00 a R{MAX_LINHAS_TABELA - 1:02d}); "
                f"R{rev.numero:02d} não apareceria no selo."
            )
        if not RE_DATA_NOVA.match(rev.data):
            problemas.append(f"Data '{rev.data}' fora do formato dd/mm/aaaa.")
        if not rev.autor.strip():
            problemas.append("Autor da revisão vazio.")
        if not rev.descricao.strip():
            problemas.append("Descrição da revisão vazia.")
        for campo in (rev.autor, rev.descricao):
            try:
                _para_arquivo(campo)
            except ErroCPL as e:
                problemas.append(str(e))
        if len(rev.descricao) > MAX_CARACTERES_DESCRICAO:
            problemas.append(
                f"AVISO: descrição com {len(rev.descricao)} caracteres; acima de {MAX_CARACTERES_DESCRICAO} "
                "ela pode não caber na coluna DESCRIÇÃO do selo."
            )
        return problemas

    def adicionar_revisao(self, rev: Revisao) -> None:
        erros = [p for p in self.validar_revisao(rev) if not p.startswith("AVISO:")]
        if erros:
            raise ErroCPL(" ".join(erros))
        self.linhas[self.indice_fim_revisoes:self.indice_fim_revisoes] = rev.linhas_arquivo()
        self.indice_fim_revisoes += 4
        self.indice_eoc += 4
        self.revisoes.append(rev)
        self._definir_token_cabecalho(IDX_TOKEN_REV_ATUAL, rev.numero)
        self._definir_token_cabecalho(IDX_TOKEN_NUM_REVISOES, len(self.revisoes))

    def zerar_revisoes(self) -> None:
        """Remove todo o histórico (usado ao abrir uma nova fase, que recomeça em R00)."""
        removidas = self.indice_fim_revisoes - LINHA_PRIMEIRA_REVISAO
        del self.linhas[LINHA_PRIMEIRA_REVISAO:self.indice_fim_revisoes]
        self.indice_fim_revisoes = LINHA_PRIMEIRA_REVISAO
        self.indice_eoc -= removidas
        self.revisoes = []
        self._definir_token_cabecalho(IDX_TOKEN_REV_ATUAL, 0)
        self._definir_token_cabecalho(IDX_TOKEN_NUM_REVISOES, 0)

    def renomear_referencias(self, id_antigo: str, id_novo: str) -> int:
        """Troca o ID nas referências após o --EOC-- (ex.: carimbo <ID>_CR). Retorna quantas linhas mudaram."""
        alteradas = 0
        for i in range(self.indice_eoc + 1, len(self.linhas)):
            if id_antigo in self.linhas[i]:
                self.linhas[i] = self.linhas[i].replace(id_antigo, id_novo)
                alteradas += 1
        return alteradas

    def copiar_para(self, novo_caminho: str) -> "PlantaCPL":
        nova = copy.deepcopy(self)
        nova.caminho = novo_caminho
        return nova

    # ------------------------------------------------------------------ gravação
    def serializar(self) -> bytes:
        return self.separador.join(self.linhas).encode(CODIF_BYTES)

    def salvar(self, caminho: Optional[str] = None) -> str:
        destino = caminho or self.caminho
        with open(destino, "wb") as f:
            f.write(self.serializar())
        return destino


def ler_cpl(caminho: str) -> PlantaCPL:
    with open(caminho, "rb") as f:
        bruto = f.read()
    texto = bruto.decode(CODIF_BYTES)
    separador = "\r\n" if "\r\n" in texto else "\n"
    linhas = texto.split(separador)

    if len(linhas) <= LINHA_PRIMEIRA_REVISAO:
        raise ErroCPL(f"{caminho}: arquivo curto demais para uma planta do TQS.")
    try:
        indice_eoc = next(i for i, l in enumerate(linhas) if l.strip() == MARCA_FIM_CARIMBO)
    except StopIteration:
        raise ErroCPL(f"{caminho}: marcador {MARCA_FIM_CARIMBO} não encontrado.")

    planta = PlantaCPL(caminho=caminho, linhas=linhas, separador=separador, indice_eoc=indice_eoc)
    toks = planta._tokens_cabecalho()
    if len(toks) <= IDX_TOKEN_NUM_REVISOES:
        raise ErroCPL(f"{caminho}: cabeçalho com {len(toks)} campos; esperado mais de {IDX_TOKEN_NUM_REVISOES}.")
    try:
        num_revisoes = int(toks[IDX_TOKEN_NUM_REVISOES][2])
        rev_atual = int(toks[IDX_TOKEN_REV_ATUAL][2])
    except ValueError:
        raise ErroCPL(f"{caminho}: campos de revisão do cabeçalho não são números.")

    i = LINHA_PRIMEIRA_REVISAO
    for _ in range(num_revisoes):
        if i + 3 >= indice_eoc:
            raise ErroCPL(f"{caminho}: o cabeçalho indica {num_revisoes} revisões, mas o histórico acaba antes.")
        num, data, autor, desc = linhas[i:i + 4]
        if not RE_NUMERO.match(num) or not RE_DATA.match(data.strip()):
            raise ErroCPL(f"{caminho}: bloco de revisão inesperado na linha {i + 1} ('{num.strip()}', '{data.strip()}').")
        planta.revisoes.append(Revisao(int(num), data.strip(), _para_exibicao(autor).strip(), _para_exibicao(desc).strip()))
        i += 4
    planta.indice_fim_revisoes = i

    if planta.revisoes and rev_atual != planta.revisoes[-1].numero:
        raise ErroCPL(
            f"{caminho}: o cabeçalho marca R{rev_atual:02d} como atual, mas a última revisão do histórico é "
            f"R{planta.revisoes[-1].numero:02d}."
        )
    return planta


def listar_cpls(pasta_plantas: str) -> List[str]:
    if not os.path.isdir(pasta_plantas):
        return []
    return sorted(
        os.path.join(pasta_plantas, f) for f in os.listdir(pasta_plantas) if f.upper().endswith(".CPL")
    )
