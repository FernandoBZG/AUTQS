# coding: utf-8
# Copyright (C) 1986-2025 TQS Informatica Ltda
#
#  This software is provided 'as-is', without any express or implied
#  warranty. In no event will the authors be held liable for any damages
#  arising from the use of this software.
#
#  Permission is granted to anyone to use this software exclusively in
#  conjunction with TQS software, subject to the following restrictions:
#
#  1. The origin of this software must not be misrepresented. You must not
#     claim that you wrote the original software. If you use this software
#     in a product, an acknowledgment in the product documentation would be
#     required.
#  2. Altered source versions must be plainly marked as such, and must not be
#     misrepresented as being the original software.
#  3. This notice may not be removed or altered from any source distribution.
#
#  www.tqs.com.br
#  suporte@tqs.com.br
#-----------------------------------------------------------------------------
#    TQSGrid.PY  Módulo para a gravação de tabelas em desenho
#                Interface semelhante às bibliotecas de grid para Windows
#                Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING, Union

import TQS.TQSUtil
import TQS.TQSDwg

if TYPE_CHECKING:
    from TQS.TQSDwg import Dwg

#-----------------------------------------------------------------------------
#       Atributo de grid. É usado nesta ordem:
#               Vem da célula se existir;
#               Senão vem da coluna se existir;
#               Senão vem da linha se existir;
#               Senão vem do grid
#
class GridDwgAttrib ():
    """Atributo de grid aplicável a célula, coluna, linha ou grid inteiro.

    A resolução do atributo segue a ordem: Célula → Coluna → Linha → Grid.
    O primeiro nível em que o atributo for definido prevalece.

    Implementação:
        Os métodos desta classe são wrappers finos sobre funções C++ exportadas
        pela DLL ``NDWGGRID.DLL`` (com auxílio de ``NV3D.DLL`` para nível de desenho).
        O padrão recorrente é: (1) embrulhar o ponteiro opaco do atributo
        (``m_patrgrid``) e ints/doubles/strings em ``ctypes.c_*``; (2) chamar
        ``DWGGRID_ATRIB_GET*`` ou ``DWGGRID_ATRIB_SET*`` através do handle de DLL;
        (3) ler de volta as saídas via ``.value`` em parâmetros passados por
        referência. Comentários inline são adicionados apenas onde a sequência
        foge desse padrão.

    Attributes:
        ALIN_HINVAL: Alinhamento horizontal inválido (sentinel ``-1``).
        ALIN_HESQ: Alinhamento horizontal à esquerda (``0``).
        ALIN_HCEN: Alinhamento horizontal centralizado (``1``).
        ALIN_HDIR: Alinhamento horizontal à direita (``2``).
        ALIN_VINVAL: Alinhamento vertical inválido (sentinel ``-1``).
        ALIN_VINF: Alinhamento vertical inferior (``0``).
        ALIN_VCEN: Alinhamento vertical central (``1``).
        ALIN_VSUP: Alinhamento vertical superior (``2``).
    """

    ALIN_HINVAL: int = -1      # Alinhamento horizontal inválido
    ALIN_HESQ:   int =  0      # Alinhamento horizontal esquerdo
    ALIN_HCEN:   int =  1      # Alinhamento horizontal central
    ALIN_HDIR:   int =  2      # Alinhamento horizontal direito

    ALIN_VINVAL: int = -1      # Alinhamento vertical   inválido
    ALIN_VINF:   int =  0      # Alinhamento vertical   inferior
    ALIN_VCEN:   int =  1      # Alinhamento vertical   central
    ALIN_VSUP:   int =  2      # Alinhamento vertical   superior

    def __init__ (self, griddwg: "GridDwg") -> None:
        """Cria um novo atributo de grid associado a um :class:`GridDwg`.

        Args:
            griddwg: Grid proprietário do atributo.
        """
        self.m_griddwg = griddwg
        self.m_patrgrid= None
        # NV3D.DLL é necessária para resolver níveis de desenho referenciados pelo atributo
        self.m_nv3d     = TQS.TQSUtil.LoadDll ("NV3D.DLL")
        parpdwggrid    = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parpatrgrid    = ctypes.c_void_p (self.m_patrgrid)
        # Aloca um novo atributo no grid e captura o ponteiro opaco devolvido por referência
        self.m_griddwg.m_dwggriddll.DWGGRID_CRIARATRIB (parpdwggrid, ctypes.byref (parpatrgrid))
        self.m_patrgrid = parpatrgrid.value

    @property
    def level (self) -> int:
        """int: Nível de desenho associado ao atributo."""
        parpatrgrid    = ctypes.c_void_p (self.m_patrgrid)
        nivel          = 0;
        parnivel       = ctypes.c_int (nivel)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_GETNIVEL (parpatrgrid, ctypes.byref (parnivel))
        nivel          = parnivel.value
        return         (nivel);

    @level.setter
    def level (self, val: int) -> None:
        """Atribui Nível de desenho associado ao atributo."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        parnivel        = ctypes.c_int (val)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_SETNIVEL (parpatrgrid, parnivel)

    @property
    def hText (self) -> float:
        """float: Altura de texto em cm."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        htex            = 0.
        parhtex         = ctypes.c_double (htex)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_GETHTEX (parpatrgrid, ctypes.byref (parhtex))
        htex            = parhtex.value
        return          (htex);

    @hText.setter
    def hText (self, val: float) -> None:
        """Atribui Altura de texto em cm."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        parhtex         = ctypes.c_double (val)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_SETHTEX (parpatrgrid, parhtex)

    @property
    def iHorizontalAlignment (self) -> int:
        """int: Alinhamento horizontal de texto. Use ``GridDwgAttrib.ALIN_H*``."""
        parpatrgrid = ctypes.c_void_p (self.m_patrgrid)
        ialinh       = 0;
        parialinh    = ctypes.c_int (ialinh)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_GETIALINH (parpatrgrid, ctypes.byref (parialinh))
        ialinh       = parialinh.value
        return          (ialinh);

    @iHorizontalAlignment.setter
    def iHorizontalAlignment (self, val: int) -> None:
        """Atribui Alinhamento horizontal de texto. Use ``GridDwgAttrib.ALIN_H*``."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        parialinh     = ctypes.c_int (val)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_SETIALINH (parpatrgrid, parialinh)

    @property
    def iVerticalAlignment (self) -> int:
        """int: Alinhamento vertical de texto. Use ``GridDwgAttrib.ALIN_V*``."""
        parpatrgrid = ctypes.c_void_p (self.m_patrgrid)
        ialinv       = 0;
        parialinv    = ctypes.c_int (ialinv)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_GETIALINV (parpatrgrid, ctypes.byref (parialinv))
        ialinv       = parialinv.value
        return          (ialinv);

    @iVerticalAlignment.setter
    def iVerticalAlignment (self, val: int) -> None:
        """Atribui Alinhamento vertical de texto. Use ``GridDwgAttrib.ALIN_V*``."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        parialinv     = ctypes.c_int (val)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_SETIALINV (parpatrgrid, parialinv)

    @property
    def cellHeight (self) -> float:
        """float: Altura da célula em cm."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        altur           = 0.;
        paraltur        = ctypes.c_double (altur)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_GETALTUR (parpatrgrid, ctypes.byref (paraltur))
        altur           = paraltur.value
        return          (altur);

    @cellHeight.setter
    def cellHeight (self, val: float) -> None:
        """Atribui Altura da célula em cm."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        paraltur        = ctypes.c_double (val)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_SETALTUR (parpatrgrid, paraltur)

    @property
    def cellWidth (self) -> float:
        """float: Largura da célula em cm."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        alarg           = 0.;
        paralarg        = ctypes.c_double (alarg)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_GETALARG (parpatrgrid, ctypes.byref (paralarg))
        alarg           = paralarg.value
        return          (alarg);

    @cellWidth.setter
    def cellWidth (self, val: float) -> None:
        """Atribui Largura da célula em cm."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        paralarg        = ctypes.c_double (val)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_SETALARG (parpatrgrid, paralarg)

    @property
    def cellFormat (self, format: str) -> str:
        """str: Formato da célula no estilo ``printf`` da família C.

        O especificador deve ser compatível com o tipo do valor armazenado
        na célula (``%d``, ``%f``, ``%s`` etc.).

        ATENÇÃO: na biblioteca TQS este getter declara um parâmetro extra, então
        LER ``attrib.cellFormat`` levanta ``TypeError``. Somente a atribuição
        funciona; guarde o formato em uma variável própria se precisar consultá-lo.
        """
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        parformat       = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_GETFORMAT (parpatrgrid, parformat)
        return          parformat.value.decode(TQS.TQSUtil.CHARSET)

    @cellFormat.setter
    def cellFormat (self, format: str) -> None:
        """Atribui Formato da célula no estilo ``printf`` da família C."""
        parpatrgrid     = ctypes.c_void_p (self.m_patrgrid)
        parformat       = ctypes.c_char_p (format.encode(TQS.TQSUtil.CHARSET))
        self.m_griddwg.m_dwggriddll.DWGGRID_ATRIB_SETFORMAT (parpatrgrid, parformat)

#-----------------------------------------------------------------------------
class GridDwg ():
    """Grid (tabela) gravável em DWG, LST, HTML e PDF.

    Composição de sub-objetos:

    * :attr:`file` — gravação em diferentes formatos.
    * :attr:`attrib` — definição de atributos (grid/linha/coluna/célula).
    * :attr:`format` — dimensões e preenchimento de células.

    Implementação:
        Os métodos desta classe e das suas sub-classes :class:`File`, :class:`Attrib`
        e :class:`Format` são wrappers finos sobre funções C++ exportadas pela DLL
        ``NDWGGRID.DLL``. O padrão recorrente é: (1) embrulhar o ponteiro opaco do
        grid (``m_pdwggrid``) e ints/doubles/strings em ``ctypes.c_*``; (2) chamar
        a função ``DWGGRID_*`` através do handle de DLL; (3) ler de volta as saídas
        via ``.value`` em parâmetros passados por referência. Comentários inline
        são adicionados apenas onde a sequência foge desse padrão.

    Attributes:
        m_dwggriddll: Handle de ``NDWGGRID.DLL``.
        m_pdwggrid: Ponteiro opaco para a estrutura C++ do grid.
        file: Sub-objeto :class:`File` para gravação.
        attrib: Sub-objeto :class:`Attrib` para atributos.
        format: Sub-objeto :class:`Format` para formatação.
    """

    def __init__ (self) -> None:
        """Inicializa um grid vazio carregando ``NDWGGRID.DLL``."""
        self.m_dwggriddll = TQS.TQSUtil.LoadDll ("NDWGGRID.DLL")
        self.m_pdwggrid   = None
        parpdwggrid       = ctypes.c_void_p (self.m_pdwggrid)
        # Aloca a estrutura C++ do grid e captura o ponteiro opaco devolvido por referência
        self.m_dwggriddll.DWGGRID_INICIAR (ctypes.byref (parpdwggrid))
        self.m_pdwggrid   = parpdwggrid.value
        # Sub-objetos compartilham o mesmo handle de DLL e ponteiro de grid via self
        self.file         = File (self)
        self.attrib       = Attrib (self)
        self.format       = Format (self)

#
#    Representação deste objeto
#
    def __str__(self) -> str:
        """Retorna representação textual do grid (debug).

        ATENÇÃO: o corpo lê ``self.m_format``, mas o construtor define
        ``self.format``. Converter esta classe para texto (``str(obj)``,
        ``print(obj)``) levanta ``AttributeError``. Consulte ``obj.format.lines``
        e ``obj.format.columns`` diretamente.
        """
        msg         = "Class TQSGrid"
        msg         += "\n   m_dwggriddll " + str (self.m_dwggriddll)
        msg         += "\n   m_pdwggrid   " + str (self.m_pdwggrid)
        msg         += "\n   linhas       " + str (self.m_format.lines)
        msg         += "\n   colunas      " + str (self.m_format.columns)
        return         msg

#-----------------------------------------------------------------------------
class File ():
    """Operações de gravação do grid em DWG, LST, HTML e PDF."""

    def __init__ (self, griddwg: "GridDwg") -> None:
        """Inicializa o sub-objeto de gravação.

        Args:
            griddwg: Grid proprietário.
        """
        self.m_griddwg = griddwg


    def SaveAndMergeDwg (self, dwg: "Dwg", xorg: float, yorg: float) -> None:
        """Salva o grid mesclando-o em um DWG existente.

        Args:
            dwg: Desenho destino (:class:`TQSDwg.Dwg`).
            xorg: Coordenada X da origem da tabela, em cm.
            yorg: Coordenada Y da origem da tabela, em cm.
        """
        parpdwggrid       = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        # Extrai o handle nativo do Dwg destino (PEDMV) para mesclar a tabela no desenho aberto
        pedmv           = dwg.handle_pedmv
        parpedmv        = ctypes.c_void_p (pedmv)
        parxorg         = ctypes.c_double (xorg)
        paryorg         = ctypes.c_double (yorg)
        self.m_griddwg.m_dwggriddll.DWGGRID_SALVAREMDWG (parpdwggrid, parpedmv, parxorg, paryorg)

    def SaveAsDwg (self, nomdwg: str) -> None:
        """Salva o grid em um arquivo DWG.

        Args:
            nomdwg: Caminho do arquivo DWG de saída.
        """
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parnomdwg       = ctypes.c_char_p (nomdwg.encode(TQS.TQSUtil.CHARSET))
        self.m_griddwg.m_dwggriddll.DWGGRID_SALVARCOMODWG (parpdwggrid, parnomdwg)

    def SaveAsLst (self, nomlst: str) -> None:
        """Salva o grid em um arquivo LST (listagem texto).

        Args:
            nomlst: Caminho do arquivo LST de saída.
        """
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parnomlst       = ctypes.c_char_p (nomlst.encode(TQS.TQSUtil.CHARSET))
        self.m_griddwg.m_dwggriddll.DWGGRID_SALVARCOMOLST (parpdwggrid, parnomlst)

    def SaveAsHtml (self, nomhtm: str) -> None:
        """Salva o grid em um arquivo HTML.

        Args:
            nomhtm: Caminho do arquivo HTML de saída.
        """
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parnomhtm       = ctypes.c_char_p (nomhtm.encode(TQS.TQSUtil.CHARSET))
        self.m_griddwg.m_dwggriddll.DWGGRID_SALVARCOMOHTM (parpdwggrid, parnomhtm)

    def SaveAsPdf (self, nompdf: str) -> None:
        """Salva o grid em um arquivo PDF.

        Args:
            nompdf: Caminho do arquivo PDF de saída.
        """
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parnompdf       = ctypes.c_char_p (nompdf.encode(TQS.TQSUtil.CHARSET))
        self.m_griddwg.m_dwggriddll.DWGGRID_SALVARCOMOPDF (parpdwggrid, parnompdf)

#-----------------------------------------------------------------------------
class Attrib ():
    """Definição de atributos do grid em quatro escopos: grid/linha/coluna/célula."""

    def __init__ (self, griddwg: "GridDwg") -> None:
        """Inicializa o sub-objeto de atributos.

        Args:
            griddwg: Grid proprietário.
        """
        self.m_griddwg = griddwg

    def SetAttribGrid (self, attrgrid: "GridDwgAttrib") -> None:
        """Define os atributos gerais do grid (escopo mais amplo).

        Args:
            attrgrid: Atributo a aplicar a todo o grid.
        """
        parpdwggrid    = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parpatrgrid    = ctypes.c_void_p (attrgrid.m_patrgrid)
        self.m_griddwg.m_dwggriddll.DWGGRID_SETATRIBGRID (parpdwggrid, parpatrgrid)

    def SetAttribLine (self, line: int, attrgrid: "GridDwgAttrib") -> None:
        """Define os atributos de uma linha.

        Args:
            line: Índice da linha (``0..lines-1``).
            attrgrid: Atributo a aplicar à linha.
        """
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parline         = ctypes.c_int (line)
        parpatrgrid     = ctypes.c_void_p (attrgrid.m_patrgrid)
        self.m_griddwg.m_dwggriddll.DWGGRID_SETATRIBLINHA (parpdwggrid, parline, parpatrgrid)

    def SetAttribColumn (self, column: int, attrgrid: "GridDwgAttrib") -> None:
        """Define os atributos de uma coluna.

        Args:
            column: Índice da coluna (``0..columns-1``).
            attrgrid: Atributo a aplicar à coluna.
        """
        parpdwggrid    = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parcolumn         = ctypes.c_int (column)
        parpatrgrid    = ctypes.c_void_p (attrgrid.m_patrgrid)
        self.m_griddwg.m_dwggriddll.DWGGRID_SETATRIBCOLUNA (parpdwggrid, parcolumn, parpatrgrid)

    def SetAttribCell (self, line: int, column: int, attrgrid: "GridDwgAttrib") -> None:
        """Define os atributos de uma célula (escopo mais específico).

        Args:
            line: Índice da linha (``0..lines-1``).
            column: Índice da coluna (``0..columns-1``).
            attrgrid: Atributo a aplicar à célula.
        """
        parpdwggrid    = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parline         = ctypes.c_int (line)
        parcolumn         = ctypes.c_int (column)
        parpatrgrid    = ctypes.c_void_p (attrgrid.m_patrgrid)
        self.m_griddwg.m_dwggriddll.DWGGRID_SETATRIBCEL (parpdwggrid, parline, parcolumn, parpatrgrid)

#-----------------------------------------------------------------------------
class Format ():
    """Formatação do grid (dimensões) e preenchimento de células."""

    def __init__ (self, griddwg: "GridDwg") -> None:
        """Inicializa o sub-objeto de formatação.

        Args:
            griddwg: Grid proprietário.
        """
        self.m_griddwg = griddwg

    @property
    def columns (self) -> int:
        """int: Número de colunas do grid."""
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        numcolunas      = 0;
        parnumcolunas   = ctypes.c_int (numcolunas)
        self.m_griddwg.m_dwggriddll.DWGGRID_GETCOLUNAS (parpdwggrid, ctypes.byref (parnumcolunas))
        numcolunas      = parnumcolunas.value
        return          (numcolunas);

    @columns.setter
    def columns (self, numcolumns: int) -> None:
        """Atribui Número de colunas do grid."""
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parnumcolunas   = ctypes.c_int (numcolumns)
        self.m_griddwg.m_dwggriddll.DWGGRID_SETCOLUNAS (parpdwggrid, parnumcolunas)

    @property
    def lines (self) -> int:
        """int: Número de linhas do grid."""
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        numlinhas      = 0;
        parnumlinhas   = ctypes.c_int (numlinhas)
        self.m_griddwg.m_dwggriddll.DWGGRID_GETLINHAS (parpdwggrid, ctypes.byref (parnumlinhas))
        numlinhas      = parnumlinhas.value
        return          (numlinhas);

    @lines.setter
    def lines (self, numlines: int) -> None:
        """Atribui Número de linhas do grid."""
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parnumlinhas    = ctypes.c_int (numlines)
        self.m_griddwg.m_dwggriddll.DWGGRID_SETLINHAS (parpdwggrid, parnumlinhas)

    def MergeLine (self, line: int, startColumn: int, endColumn: int) -> None:
        """Mescla colunas adjacentes de uma mesma linha (sem linha divisória).

        Args:
            line: Índice da linha cujas colunas serão mescladas.
            startColumn: Coluna inicial (inclusive).
            endColumn: Coluna final (inclusive).
        """
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parilin         = ctypes.c_int (line)
        paricolini      = ctypes.c_int (startColumn)
        paricolfin      = ctypes.c_int (endColumn)
        self.m_griddwg.m_dwggriddll.DWGGRID_MESCLARLINHA (parpdwggrid,
                            parilin, paricolini, paricolfin)

    def MergeColumn (self, column: int, startLine: int, endLine: int) -> None:
        """Mescla linhas adjacentes de uma mesma coluna (sem linha divisória).

        Args:
            column: Índice da coluna cujas linhas serão mescladas.
            startLine: Linha inicial (inclusive).
            endLine: Linha final (inclusive).
        """
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        paricol         = ctypes.c_int (column)
        parilinini      = ctypes.c_int (startLine)
        parilinfin      = ctypes.c_int (endLine)
        self.m_griddwg.m_dwggriddll.DWGGRID_MESCLARCOLUNA (parpdwggrid,
                            paricol, parilinini, parilinfin)

    def SetCell (self, line: int, column: int, val: Union[int, float, str]) -> None:
        """Define o valor de uma célula (inteiro, real ou texto).

        O tipo do valor determina a função C++ chamada — o formato definido
        em :attr:`GridDwgAttrib.cellFormat` deve ser compatível.

        Args:
            line: Índice da linha (``0..lines-1``).
            column: Índice da coluna (``0..columns-1``).
            val: Conteúdo da célula. Tipos suportados: ``int``, ``float``, ``str``.
                Outros tipos são rejeitados com mensagem de erro via :func:`TQSUtil.writef`.
        """
        parpdwggrid     = ctypes.c_void_p (self.m_griddwg.m_pdwggrid)
        parilin         = ctypes.c_int (line)
        paricol         = ctypes.c_int (column)

        # Despacha por tipo: cada variante chama uma função C++ distinta no NDWGGRID
        if              (isinstance (val, int)):
            parival     = ctypes.c_int (val)
            self.m_griddwg.m_dwggriddll.DWGGRID_SETVALORINT (parpdwggrid,
                            parilin, paricol, parival)

        elif            (isinstance (val, float)):
            pardval     = ctypes.c_double (val)
            self.m_griddwg.m_dwggriddll.DWGGRID_SETVALORDOUBLE (parpdwggrid,
                            parilin, paricol, pardval)

        elif            (isinstance (val, str)):
            # Strings vão na codificação configurada do TQS para preservar acentuação
            parsval     = ctypes.c_char_p (val.encode(TQS.TQSUtil.CHARSET))
            self.m_griddwg.m_dwggriddll.DWGGRID_SETVALORSTR (parpdwggrid,
                            parilin, paricol, parsval)

        else:
            # Tipo não suportado: registra mensagem e ignora a célula em vez de falhar
            TQSUtil.writef ("TQSGrid: Valor inválido linha %d coluna %d" % (line, column));
            return
