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
#    TQSM3d.PY         Modelo 3D formato E3D ou E3X para uso no TQS
#                      Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes
import copy
import math
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import TQS.TQSUtil
import TQS.TQSGeo

#-----------------------------------------------------------------------------
#    Tipos de elementos 3D
#
E3DTYPE_INDEFINIDO:      int =-1     # Indefinido
E3DTYPE_PRISMA:          int = 0     # Prisma simples
E3DTYPE_PRISMAC:         int = 1     # Prisma complexo
E3DTYPE_SOLIDO:          int = 2     # Sólido genérico
E3DTYPE_TRILHA:          int = 3     # Trilha
E3DTYPE_SOLIDOT:         int = 4     # Sólido genérico com tab coor
E3DTYPE_BLOCOINS:        int = 5     # Inserção de bloco
#-----------------------------------------------------------------------------
#    Tipos de elementos classificados pelo CAD/Formas
#
E3D_TIPOINVALIDO:     int = -1       # Outros tipos de elementos importados
E3D_TIPOVIGA:         int =  0       # Tipo viga
E3D_TIPOPILAR:        int =  1       # Tipo pilar
E3D_TIPOLAJE:         int =  2       # Tipo laje
E3D_TIPOBUR:          int =  3       # Tipo buraco
E3D_TIPOCAP:          int =  4       # Tipo capitel
E3D_TIPOFUND:         int =  5       # Tipo fundação
E3D_TIPOEST:          int =  6       # Tipo estaca
E3D_TIPOARMLONGVIG:   int =  7       # Armadura longitudinal vigas
E3D_TIPOARMTRANVIG:   int =  8       # Armadura transversal vigas
E3D_TIPOPLANOFU:      int =  9       # Tipo plano de fundo
E3D_TIPOARMLATRVIG:   int = 10       # Armadura lateral vigas
E3D_TIPOARMLFURVIG:   int = 11       # Armadura longit furo vigas
E3D_TIPOARMTFURVIG:   int = 12       # Armadura transv furo vigas
E3D_TIPOARMLONGPIL:   int = 13       # Armadura longit pilares
E3D_TIPOARMTRANPIL:   int = 14       # Armadura transv pilares
E3D_TIPOARMLONGLAP:   int = 15       # Armadura longit lajes pos
E3D_TIPOARMLONGLAN:   int = 16       # Armadura longit lajes neg
E3D_TIPOPREMOLCONS:   int = 17       # Armadura de consolos
E3D_TIPOARMGTANVIG:   int = 18       # Grampos de vigas
E3D_TIPOARMCMPLPIL:   int = 19       # Armadura long compl pilares
E3D_TIPOPROTEND:      int = 20       # Armadura de protens/bainhas
E3D_ALVHORIZ:         int = 21       # Alvenaria dir. predominantemente Horizontal (eixo X, em planta);cor:   51;
E3D_ALVVERTC:         int = 22       # Alvenaria dir. predominantemente Vertical (eixo Y, em planta);  cor: 255;
E3D_ALVCRUZM:         int = 23       # Alvenaria/elemento em cruzamentos;                              cor: 254;
E3D_ALVVERGA:         int = 24       # Alvenaria - Vergas de portas/janelas;                           cor:  61;
E3D_ALVCVERV:         int = 25       # Alvenaria - ContraVergas de janelas;                            cor:   71;
E3D_ALVENCUNH:        int = 26       # Alvenaria - Encunhamentos;                                      cor:   41;
E3D_ALVENXVERT:       int = 27       # Alvenaria - Enchimentos Verticais;                              cor:   31;
E3D_CORTESEC:         int = 28       # Corte da seção
E3D_TIPOESCADA:       int = 29       # Escada
E3D_TIPORAMPA:        int = 30       # Rampa
E3D_BLOCOTRANS:       int = 31       # Bloco de transição
E3D_MISULAVIGA:       int = 32       # Mísula em viga
E3D_ELEMSELEC:        int = 33       # Elemento selecionado
E3D_TIPOVIGAPRE:      int = 34       # Pré-moldado: viga
E3D_TIPOPILARPRE:     int = 35       # Pré-moldado: pilar
E3D_TIPOLAJEPRE:      int = 36       # Pré-moldado: laje
E3D_TIPOOBJETO:       int = 37       # Objeto genérico
E3D_TIPOMATNP:        int = 38       # Material não padrão
E3D_TIPOPILARPAR:     int = 39       # Tipo pilar parede
E3D_ALVGRAUTEVERT:    int = 40       # Alvenaria: Graute Vertical
E3D_ALVGRAUTEHORZ:    int = 41       # Alvenaria: Graute Horizontal
E3D_TIPOARMALVVER:    int = 42       # Alvenaria: Armadura Vertical
E3D_TIPOARMALVHOR:    int = 43       # Alvenaria: Armadura Horizontal
E3D_TIPOINSERTOPRE:   int = 44       # Pré-moldado: Inserto
E3D_TIPOARMFUNDACO:   int = 45       # Armadura de fundações
E3D_TIPOPAINPRE:      int = 46       # Painel pré-moldado
E3D_REFEXT3D:         int = 47       # Referência externa 3D
E3D_TIPOPAREDE:       int = 48       # Paredes
E3D_TIPOTUBULACOES:   int = 49       # Tubulações
E3D_CAPAPRE:          int = 50       # Capa de pré-moldados
E3D_FUNTELA:          int = 51       # Fundo de tela
E3D_CTRAUX:           int = 52       # Contorno auxiliar
E3D_ELEMPRESEL:       int = 53       # Elemento pré-selecionado
E3D_TIPOCARGA:        int = 54       # Carga no Modelador
E3D_INSBLOCO:         int = 55       # Inserção de bloco
E3D_VIGAMATNP:        int = 56       # Viga de material não padrão
E3D_PILARMATNP:       int = 57       # Pilar de material não padrão
E3D_TPARMLNGVIGNEG:   int = 58       # Armadura longitudinal vigas NEGATIVA
E3D_TPARMLNGLAPSEC:   int = 59       # Armadura longit lajes pos SECUNDÁRIA
E3D_ALVBLOINT:        int = 60       # Alvenaria: Bloco INTEIRO
E3D_ALVBLOMEI:        int = 61       # Alvenaria: MEIO Bloco
E3D_ALVBLOT:          int = 62       # Alvenaria: Bloco T (1 ½)
E3D_ALVBLOL:          int = 63       # Alvenaria: Bloco L
E3D_ALVBLOVAR:        int = 64       # Alvenaria: Bloco Variável
E3D_ALVBLOCOMP:       int = 65       # Alvenaria: Bloco Compensador (especial)
E3D_ALVBLOESP:        int = 66       # Alvenaria: Bloco Específco/Hidráulico
E3D_ALVBLOCAN:        int = 67       # Alvenaria: Bloco Canaleta
E3D_ALVBLOCANBAI:     int = 68       # Alvenaria: Bloco Canaleta Baixa
E3D_ALVBLOCANMED:     int = 69       # Alvenaria: Bloco Canaleta Média
E3D_ALVBLOJBAI:       int = 70       # Alvenaria: Bloco J Baixo
E3D_ALVBLOJALT:       int = 71       # Alvenaria: Bloco J Alto
E3D_ALVBLOJMED:       int = 72       # Alvenaria: Bloco J = médio

E3D_NUMTIPOS:         int = 73       # Número total de tipos
#-----------------------------------------------------------------------------
#       Modelo 3D. Concentra todas as chamadas através dos subobjetos
#
class Model3D ():
    """Modelo 3D no formato ``E3D``/``E3X`` usado pelo TQS.

    Concentra todas as chamadas à ``NDXIODLL.DLL`` através de sub-objetos
    especializados (:class:`File`, :class:`Base`, :class:`Solids`,
    :class:`Iterator`, :class:`Blocks`).

    Implementação:
        Esta classe é o ponto de entrada do binding Python para o ``CDxIoMem``
        em ``NDXIODLL.DLL``. O ``__init__`` cria/possui o handle ``CDxIoMem``
        e instancia os sub-objetos que delegam as chamadas C++ para a DLL.
        O padrão recorrente nos sub-objetos e nas classes ``_*`` deste módulo
        é: (1) embrulhar handles e ints/doubles em ``ctypes.c_*``; (2) chamar
        a função C++ correspondente; (3) ler valores de saída via ``.value``
        em parâmetros passados por referência. Comentários inline são
        adicionados apenas onde a sequência foge desse padrão.

    Attributes:
        m_dxiodll: Handle de ``NDXIODLL.DLL``.
        m_nomarq: Nome do arquivo associado ao modelo.
        m_dxiomem: Handle interno do objeto ``CDxIoMem``.
        m_ialoc: ``1`` se o objeto possui ownership e deve liberar a memória.
        file: Sub-objeto de manipulação de arquivos.
        base: Sub-objeto de criação de elementos básicos.
        solids: Sub-objeto de criação de sólidos.
        iterator: Sub-objeto de iteração no modelo.
        blocks: Sub-objeto de manipulação de blocos.
    """

    def __init__ (self) -> None:
        """Inicializa o container de objetos 3D deste módulo."""
        self.m_dxiodll = TQS.TQSUtil.LoadDll ("NDXIODLL.DLL")
        self.m_nomarq   = ""
        self.m_dxiomem  = None
        # Aloca o CDxIoMem na DLL e marca este Python como dono (m_ialoc=1)
        pardxiomem      = ctypes.c_void_p (self.m_dxiomem)
        self.m_dxiodll.CDxIoMem_Create (ctypes.byref(pardxiomem))
        self.m_dxiomem  = pardxiomem.value
        self.m_ialoc    = 1
        # Habilita leitura recursiva para que blocos aninhados sejam expandidos
        pardxiomem      = ctypes.c_void_p (self.m_dxiomem)
        isRecursive     = 1
        parisRecursive  = ctypes.c_int (isRecursive)
        self.m_dxiodll.CDxIoMem_SetRecursiveRead (pardxiomem, parisRecursive)
#
#       Subobjetos
#
        self.file       = File (self)
        self.file.LoadTqsColors ()
        self.base       = Base (self)
        self.solids     = Solids (self)
        self.iterator   = Iterator (self)
        self.blocks     = Blocks (self)
#
#       Destrutor
#
    def __del__(self) -> None:
        """Libera o objeto ``CDxIoMem`` se este instance possui ownership."""
        if              (self.m_dxiomem != None and self.m_ialoc != 0):
            pardxiomem = ctypes.c_void_p (self.m_dxiomem)
            self.m_dxiodll.CDxIoMem_Delete (pardxiomem)
            self.m_dxiomem = None

#
#    Representação deste objeto
#
    def __str__(self) -> str:
        """Retorna representação textual deste :class:`Model3D` para depuração."""
        msg         = "\nClass Model3D"
        msg         += "\n   self.m_dxiodll %s "  % str (self.m_dxiodll)
        msg         += "\n   self.m_dxiomem %x "  % self.m_dxiomem
        return         msg
#
#       Manipulação de arquivos com modelo 3D
#
class File ():
    """Manipulação de arquivos com modelo 3D (E3D/E3X).

    Implementação:
        Sub-objeto de :class:`Model3D`; cada método é um wrapper fino sobre
        funções ``CDxIoMem_*`` / ``CDxIo_*`` de ``NDXIODLL.DLL``. Os métodos
        de leitura/gravação seguem o padrão Open-then-(Read|Close) — abrir
        para leitura ou escrita, executar a operação e ler ``istat`` de volta
        para sinalizar erro.

    Attributes:
        m_model3d: Modelo 3D associado.
    """

    def __init__ (self, model3d: "Model3D") -> None:
        """Inicializa o sub-objeto de manipulação de arquivos.

        Args:
            model3d: Modelo 3D proprietário.
        """
        self.m_model3d = model3d


    def ReadFileE3D (self, nomarq: str) -> int:
        """Carrega um arquivo no formato ``E3D``.

        Args:
            nomarq: Nome do arquivo a ser carregado.

        Returns:
            ``istat``: ``0`` se OK; valor diferente de zero em caso de erro.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        self.m_model3d.m_nomarq = nomarq
        parnomarq       = ctypes.c_char_p (self.m_model3d.m_nomarq.encode(TQS.TQSUtil.CHARSET))
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxIoMem_OpenForReading (pardxiomem, parnomarq, \
                            ctypes.byref(paristat))
        istat           = paristat.value
        return          istat


    def SaveAsE3D (self, nomarq: str) -> int:
        """Salva o modelo num arquivo no formato ``E3D``.

        Args:
            nomarq: Nome do arquivo de destino.

        Returns:
            ``istat``: ``0`` se OK; valor diferente de zero em caso de erro.
        """
        # ATENÇÃO: o status de OpenForWriting não é verificado nem preservado antes
        # de CloseAndWriteE3d ser chamado, e ambos escrevem no mesmo paristat. Uma
        # falha de abertura ainda dispara a gravação e pode ser sobrescrita pelo
        # status do fechamento, então istat == 0 não garante que o arquivo existe.
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        self.m_model3d.m_nomarq = nomarq
        parnomarq       = ctypes.c_char_p (self.m_model3d.m_nomarq.encode(TQS.TQSUtil.CHARSET))
        istat           = 0
        paristat        = ctypes.c_int (istat)
        # Abre para gravação e em seguida fecha persistindo no formato E3D
        self.m_model3d.m_dxiodll.CDxIoMem_OpenForWriting (pardxiomem, parnomarq, \
                            ctypes.byref(paristat))
        self.m_model3d.m_dxiodll.CDxIoMem_CloseAndWriteE3d (pardxiomem, ctypes.byref(paristat))
        istat           = paristat.value
        return          istat


    def CopyTo (self, model3ddest: "Model3D") -> None:
        """Copia o modelo atual para outro :class:`Model3D`.

        Args:
            model3ddest: Modelo destino que receberá a cópia.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        pardxiomemdest  = ctypes.c_void_p (model3ddest.m_dxiomem)
        self.m_model3d.m_dxiodll.CDxIo_Copy (pardxiomem, pardxiomemdest)

    def LoadTqsColors (self) -> None:
        """Carrega tipos e cores padrão TQS no modelo corrente."""
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        self.m_model3d.m_dxiodll.CDxIo_SetDefaultColors (pardxiomem)

    @property
    def tesselator (self) -> int:
        """Indica se objetos são triangularizados na inserção ou em :meth:`CopyTo`.

        Returns:
            ``1`` se a triangulação está habilitada, ``0`` caso contrário.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        itesselador     = 0
        paritesselador  = ctypes.c_int (itesselador)
        self.m_model3d.m_dxiodll.CDxIo_GetTesselator (pardxiomem, ctypes.byref (paritesselador))
        itesselador     = paritesselador.value
        return          itesselador

    @tesselator.setter
    def tesselator (self, itesselador: int) -> None:
        """Atribui Indica se objetos são triangularizados na inserção ou em :meth:`CopyTo`."""
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        paritesselador  = ctypes.c_int (itesselador)
        self.m_model3d.m_dxiodll.CDxIo_SetTesselator (pardxiomem, paritesselador)

    def Print (self) -> None:
        """Impressão de teste do conteúdo do modelo."""
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        self.m_model3d.m_dxiodll.CDxIoMem_Print (pardxiomem)
#
#       Criação de objetos básicos
#
class Base ():
    """Criação de elementos básicos do modelo 3D.

    Funciona como factory para coordenadas, faces, polígonos, transformações e
    atributos.

    Implementação:
        Cada método apenas instancia a classe ``_*`` correspondente, repassando
        o ``Model3D`` proprietário. A alocação efetiva do handle C++ acontece
        no ``__init__`` da classe instanciada.

    Attributes:
        m_model3d: Modelo 3D proprietário.
    """

    def __init__ (self, model3d: "Model3D") -> None:
        """Inicializa o sub-objeto de criação de elementos básicos.

        Args:
            model3d: Modelo 3D proprietário.
        """
        self.m_model3d = model3d

    def Coords (self, x: float = 0., y: float = 0., z: float = 0.) -> "_Coords":
        """Cria um objeto de coordenadas 3D.

        Args:
            x: Coordenada X.
            y: Coordenada Y.
            z: Coordenada Z.

        Returns:
            Objeto :class:`_Coords` com as coordenadas informadas.
        """
        return          _Coords (self.m_model3d, x, y, z)

    def Face (self, vetnorm: Optional["_Coords"] = None) -> "_Face":
        """Cria uma face de sólido com contorno aberto.

        Args:
            vetnorm: Vetor :class:`_Coords` que aponta para fora do sólido.

        Returns:
            Objeto :class:`_Face` recém-criado.
        """
        return          _Face (self.m_model3d, vetnorm)

    def Polyg (self, dxobj: Optional[int] = None) -> "_Polyg":
        """Cria uma poligonal 3D.

        Args:
            dxobj: Handle existente para envelopar (uso interno); se ``None``
                cria-se uma nova poligonal vazia.

        Returns:
            Objeto :class:`_Polyg`.
        """
        return          _Polyg (self.m_model3d, dxobj)

    def Transf3D (self) -> "_Transf3D":
        """Cria uma matriz de transformação geométrica 3D.

        Returns:
            Objeto :class:`_Transf3D` recém-criado.
        """
        return          _Transf3D (self.m_model3d)

    def Attrib (self, titulo: Optional[str] = None, ielem: Optional[int] = None,
                  itrecho: Optional[int] = None, itipelem: Optional[int] = None, \
                  ipiso: Optional[int] = None, icor: Optional[int] = None,
                  nompav: Optional[str] = None, maternp: Optional[str] = None,
                  ietapa: Optional[int] = None, atribident: Optional["_AttribIdent"] = None,
                  transesp: Optional[float] = None) -> "_Attrib":
        """Cria atributos de um elemento gráfico.

        Args:
            titulo: Título do elemento.
            ielem: Número do elemento.
            itrecho: Número do trecho.
            itipelem: Tipo de elemento (constantes ``E3D_TIPO*``).
            ipiso: Piso.
            icor: Cor RGB.
            nompav: Nome do pavimento.
            maternp: Material não padrão.
            ietapa: Etapa construtiva.
            atribident: Aceito e ignorado ao criar um atributo novo — a
                biblioteca substitui o valor informado por um
                :class:`_AttribIdent` recém-criado. Defina os campos de
                identificação no objeto retornado.
            transesp: Opacidade em ``%``, se diferente de ``0``.

        Returns:
            Objeto :class:`_Attrib`.
        """
        return          _Attrib (self.m_model3d, titulo, ielem, itrecho, itipelem, \
                                ipiso, icor, nompav, maternp, ietapa, atribident, transesp)

    def AttribIdent (self, ident1: Optional[int] = None, ident2: Optional[int] = None,
                       ident3: Optional[int] = None, ident4: Optional[int] = None,
                       dxobj: Optional[int] = None) -> "_AttribIdent":
        """Cria um identificador único arbitrário.

        Args:
            ident1: EAGME: Opcional.
            ident2: EAGME: piso.
            ident3: EAGME: identobj.
            ident4: EAGME: itrecho.
            dxobj: Handle existente para envelopar (uso interno).

        Returns:
            Objeto :class:`_AttribIdent`.
        """
        return          _AttribIdent (self.m_model3d, ident1, ident2, ident3, ident4, dxobj)

    def AttribGroup (self, nomgrupo: str) -> "_AttribGroup":
        """Cria um grupo de atributos chave => valor.

        Args:
            nomgrupo: Nome do grupo.

        Returns:
            Objeto :class:`_AttribGroup` recém-criado.
        """
        return          _AttribGroup (self.m_model3d, nomgrupo)

    def AttribKv (self, chave: str, valor: str) -> "_AttribKv":
        """Cria um atributo do tipo chave => valor.

        Args:
            chave: Chave do atributo.
            valor: Valor associado à chave.

        Returns:
            Objeto :class:`_AttribKv`.
        """
        return          _AttribKv (self.m_model3d, chave, valor)

#
#       Criação de sólidos
#
class Solids ():
    """Criação e gerência de sólidos no modelo 3D.

    Implementação:
        As factories (:meth:`Prism`, :meth:`ComplexPrism`, …) instanciam a
        subclasse de :class:`_Elem3D` apropriada. :meth:`EnterSolid` delega
        ao próprio sólido a chamada interna ``_GravarSolido`` que escreve no
        ``CDxIoMem``; :meth:`Delete` remove o objeto pelo seu ``CDxIdent`` e
        em seguida compacta o store via ``CDxIo_RemoveDeleted``.

    Attributes:
        m_model3d: Modelo 3D proprietário.
    """

    def __init__ (self, model3d: "Model3D") -> None:
        """Inicializa o sub-objeto de criação de sólidos.

        Args:
            model3d: Modelo 3D proprietário.
        """
        self.m_model3d = model3d

    def Prism (self, face: Optional["_Face"] = None, vetalt: Optional["_Coords"] = None,
                 atrib: Optional["_Attrib"] = None) -> "_Prism":
        """Cria um prisma simples definido por face base + vetor altura.

        Args:
            face: Face base (:class:`_Face`).
            vetalt: Vetor altura (:class:`_Coords`).
            atrib: Atributos (:class:`_Attrib`).

        Returns:
            Objeto :class:`_Prism`.
        """
        return          _Prism (self.m_model3d, face, vetalt, atrib)

    def ComplexPrism (self, vetalt: Optional["_Coords"] = None,
                        atrib: Optional["_Attrib"] = None) -> "_ComplexPrism":
        """Cria um prisma complexo definido por N faces.

        A primeira face é a base do prisma complexo, orientada para fora; as
        demais, orientadas para dentro do sólido, são furos.

        Args:
            vetalt: Vetor altura (:class:`_Coords`).
            atrib: Atributos (:class:`_Attrib`).

        Returns:
            Objeto :class:`_ComplexPrism`.
        """
        return          _ComplexPrism (self.m_model3d, vetalt, atrib)

    def GenericSolid (self, atrib: Optional["_Attrib"] = None) -> "_GenericSolid":
        """Cria um sólido genérico, descrito por todas as faces.

        Args:
            atrib: Atributos (:class:`_Attrib`).

        Returns:
            Objeto :class:`_GenericSolid`.
        """
        return          _GenericSolid (self.m_model3d, atrib)

    def ExtrusionSolid (self, face: Optional["_Face"] = None, polig: Optional["_Polyg"] = None,
                          raio: Optional[float] = None, nrep: Optional[int] = None,
                          delta: Optional["_Coords"] = None,
                          atrib: Optional["_Attrib"] = None) -> "_ExtrusionSolid":
        """Cria um sólido de extrusão (prismas que seguem uma trilha).

        Usado também para descrever barras de aço com repetição e deslocamento.

        Args:
            face: Face base (:class:`_Face`).
            polig: Linha da trilha (:class:`_Polyg`).
            raio: Raio de curvatura da trilha.
            nrep: Número de repetições do sólido a cada ``delta`` se ``> 1``.
            delta: Translação caso seja aplicada repetição.
            atrib: Atributos (:class:`_Attrib`).

        Returns:
            Objeto :class:`_ExtrusionSolid`.
        """
        return          _ExtrusionSolid (self.m_model3d, face, polig, raio, nrep, delta, atrib)

    def BlockInsert (self, nome: Optional[str] = None, transf3d: Optional["_Transf3D"] = None,
                       atrib: Optional["_Attrib"] = None) -> "_BlockInsert":
        """Cria uma inserção de bloco.

        Blocos são identificados por um nome e devem ser definidos previamente.

        Args:
            nome: Nome do bloco.
            transf3d: Transformação da inserção (:class:`_Transf3D`).
            atrib: Atributos (:class:`_Attrib`).

        Returns:
            Objeto :class:`_BlockInsert`.
        """
        return          _BlockInsert (self.m_model3d, nome, transf3d, atrib)


    def EnterSolid (self, solid: "_Elem3D") -> int:
        """Insere um sólido no modelo 3D.

        Args:
            solid: Sólido a ser inserido (:class:`_Elem3D`).

        Returns:
            ``istat``: ``0`` se OK; valor diferente de zero em caso de erro.
        """
        return          solid._GravarSolido ()

    def Delete (self, elem3d: "_Elem3D") -> int:
        """Apaga um objeto 3D do modelo.

        Args:
            elem3d: Objeto 3D a apagar.

        Returns:
            ``istat``: ``0`` se OK.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        # A remoção é feita pelo CDxIdent do elemento, não pelo seu handle direto
        atribident      = elem3d.attrib.attribIdent
        pardxident      = ctypes.c_void_p (atribident.m_dxobj)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxIoMem_DeleteByIdent (pardxiomem, pardxident, ctypes.byref (paristat))
        istat           = paristat.value
        # Compacta o store removendo entradas marcadas como apagadas
        self.m_model3d.m_dxiodll.CDxIo_RemoveDeleted (pardxiomem)
        return          istat
#
#       Manipulação geométrica do modelo
#
class Geometry ():
    """Manipulação geométrica de elementos do modelo 3D.

    Implementação:
        Cada método aplica uma transformação geométrica global a *todos* os
        elementos do ``CDxIoMem`` chamando a função ``CDxIoMem_*``
        correspondente.

    Attributes:
        m_model3d: Modelo 3D proprietário.
    """

    def __init__ (self, model3d: "Model3D") -> None:
        """Inicializa o sub-objeto de manipulação geométrica.

        Args:
            model3d: Modelo 3D proprietário.
        """
        self.m_model3d = model3d

    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada todos os elementos do modelo.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CDxIoMem_Move (pardxiomem, pardx, pardy, pardz)

    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parcz           = ctypes.c_double (cz)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CDxIoMem_Scale (pardxiomem, parcx, parcy, parcz, \
                            parescx, parescy, parescz)

    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda os elementos do modelo no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CDxIoMem_RotateXY (pardxiomem, parcx, parcy, parang)

    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma todos os elementos usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        partransf3d      = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxIoMem_Transform (pardxiomem, partransf3d)

#
#       Iterator do modelo
#
class Iterator ():
    """Iterator do modelo 3D para leitura sequencial de elementos.

    Implementação:
        Percorre o ``CDxIoMem`` no padrão prepare-then-read: :meth:`ReadBegin`
        chama ``CDxIoMem_PrepareForReading`` e :meth:`ReadNext` itera com
        ``CDxIoMem_ReadNext`` até receber ``None``. Cada handle de objeto C++
        retornado é convertido em uma subclasse concreta de :class:`_Elem3D`
        por :meth:`_ConvertDxobj`, que faz dispatch baseado no tipo
        (``E3DTYPE_*``).

    Attributes:
        m_model3d: Modelo 3D proprietário.
    """

    def __init__ (self, model3d: "Model3D") -> None:
        """Inicializa o iterator.

        Args:
            model3d: Modelo 3D proprietário.
        """
        self.m_model3d = model3d

    def ReadBegin (self) -> None:
        """Prepara o iterator para leitura do modelo desde o início.

        Returns:
            ``None``. ``istat`` interno indica erro se diferente de zero.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxIoMem_PrepareForReading (pardxiomem, ctypes.byref (paristat))
        istat           = paristat.value


    def ReadNext (self) -> Optional["_Elem3D"]:
        """Avança para o próximo elemento do modelo.

        Returns:
            O próximo elemento (:class:`_Elem3D`) ou ``None`` quando não houver
            mais elementos.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        pardxobj        = ctypes.c_void_p (None)
        # Itera até obter um elemento de tipo conhecido ou esgotar o store
        while           (True):
            self.m_model3d.m_dxiodll.CDxIoMem_ReadNext (pardxiomem, ctypes.byref (pardxobj))
            if              (pardxobj == None):
                return      None
            dxobj           = pardxobj.value
            if              (dxobj == None):
                return      None
            # _ConvertDxobj retorna None para tipos não mapeados; nesse caso pulamos para o próximo
            elem3d          = self._ConvertDxobj (dxobj)
            if          (elem3d != None):
                break;
        return          (elem3d)

    def _ConvertDxobj (self, dxobj: int) -> Optional["_Elem3D"]:
        """Converte um handle de objeto 3D no objeto :class:`_Elem3D` correto.

        Args:
            dxobj: Handle interno de objeto 3D.

        Returns:
            Instância concreta de :class:`_Elem3D` (Prism, ComplexPrism,
            GenericSolid, ExtrusionSolid ou BlockInsert), ou ``None`` se o
            tipo for desconhecido.
        """
        itipo           = -1
        pardxobj        = ctypes.c_void_p (dxobj)

        # Recupera o CDxIdent associado para construir o AttribIdent no Python
        pardxident      = ctypes.c_void_p (None)
        self.m_model3d.m_dxiodll.CDxObj_GetDxIdent (pardxobj, ctypes.byref (pardxident))
        dxident         = pardxident.value
        atribident      = self.m_model3d.base.AttribIdent (dxobj=dxident)

        # Lê o tipo concreto do objeto e instancia a subclasse Python correta
        paritipo        = ctypes.c_int (itipo)
        self.m_model3d.m_dxiodll.CDxObj_GetType (pardxobj, ctypes.byref (paritipo))
        itipo           = paritipo.value
        elem3d          = None
        # Dispatch por tipo: cada E3DTYPE_* mapeia para uma subclasse de _Elem3D
        if              (itipo == E3DTYPE_PRISMA):
            elem3d      = _Prism (self.m_model3d, dxobj=dxobj)
        elif            (itipo == E3DTYPE_PRISMAC):
            elem3d      = _ComplexPrism (self.m_model3d, dxobj=dxobj)
        elif            (itipo == E3DTYPE_SOLIDO):
            elem3d      = _GenericSolid (self.m_model3d, dxobj=dxobj)
        elif            (itipo == E3DTYPE_TRILHA):
            elem3d      = _ExtrusionSolid (self.m_model3d, dxobj=dxobj)
        elif            (itipo == E3DTYPE_BLOCOINS):
            elem3d      = _BlockInsert (self.m_model3d, dxobj=dxobj)

        return          elem3d
#
#       Manipulação de blocos
#
class Blocks ():
    """Manipulação de blocos no modelo 3D.

    Implementação:
        Wrapper sobre as funções ``CDxIoMem_*Block*`` da DLL. Use
        :meth:`Open` / :meth:`Close` para delimitar a definição de um bloco;
        objetos inseridos no modelo entre essas chamadas pertencem a esse bloco.

    Attributes:
        m_model3d: Modelo 3D proprietário.
    """

    def __init__ (self, model3d: "Model3D") -> None:
        """Inicializa o sub-objeto de manipulação de blocos.

        Args:
            model3d: Modelo 3D proprietário.
        """
        self.m_model3d = model3d


    def Open (self, nomblo: str) -> None:
        """Abre um bloco para gravação.

        Args:
            nomblo: Nome do bloco.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        parnomblo       = ctypes.c_char_p (nomblo.encode(TQS.TQSUtil.CHARSET))
        self.m_model3d.m_dxiodll.CDxIoMem_OpenBlockForWriting (pardxiomem, parnomblo)

    def Close (self) -> None:
        """Fecha o bloco aberto."""
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        self.m_model3d.m_dxiodll.CDxIoMem_CloseBlockForWriting (pardxiomem)

    def NumBlocks (self) -> int:
        """Retorna o número de blocos definidos no modelo.

        Returns:
            Número total de blocos.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        numblocos       = 0
        parnumblocos    = ctypes.c_int (numblocos)
        self.m_model3d.m_dxiodll.CDxIoMem_GetBlockCount (pardxiomem, ctypes.byref (parnumblocos))
        numblocos       = parnumblocos.value
        return          numblocos

    def BlockName (self, indblo: int) -> str:
        """Retorna o nome do bloco de índice fornecido.

        Args:
            indblo: Índice do bloco no intervalo ``0..NumBlocks()-1``.

        Returns:
            Nome do bloco.
        """
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        parnomblock     = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        parindblo       = ctypes.c_int (indblo)
        bufferSize      = TQS.TQSUtil.MAXNCSTR
        parbufferSize   = ctypes.c_int (bufferSize)
        self.m_model3d.m_dxiodll.CDxIoMem_GetBlockName (pardxiomem, parindblo, \
                            parnomblock, parbufferSize)
        nomblock        = parnomblock.value.decode (TQS.TQSUtil.CHARSET)
        return          nomblock

#-----------------------------------------------------------------------------
#       Objetos que compõem o modelo 3D
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#       Identificador único
#
glb_identd:     int = 333     # Identificador default

class _AttribIdent ():
    """Identificador único arbitrário associado a um elemento 3D.

    Composto por quatro inteiros (``ident1`` a ``ident4``). No EAGME esses
    inteiros costumam mapear opcional/piso/identobj/itrecho.

    Implementação:
        Wrapper fino do objeto ``CDxIdent`` em ``NDXIODLL.DLL``. O construtor
        aloca um novo handle (``m_ialoc=1``) ou apenas envelopa um handle
        existente (``m_ialoc=0``); o destrutor libera somente se este objeto
        for o dono. As properties ``ident1..ident4`` delegam diretamente a
        ``CDxIdent_GetId*`` / ``CDxIdent_SetId*``.

    Attributes:
        m_model3d: Modelo 3D proprietário.
        m_dxobj: Handle interno do objeto ``CDxIdent``.
        m_ialoc: ``1`` se este objeto possui ownership do handle.
    """

    def __init__ (self, model3d: "Model3D", ident1x: Optional[int] = None,
                    ident2x: Optional[int] = None, ident3x: Optional[int] = None,
                    ident4x: Optional[int] = None, dxobj: Optional[int] = None) -> None:
        """Cria um identificador único.

        Args:
            model3d: Modelo 3D proprietário.
            ident1x: EAGME: Opcional.
            ident2x: EAGME: piso.
            ident3x: EAGME: identobj.
            ident4x: EAGME: itrecho.
            dxobj: Handle existente para envelopar (uso interno).
        """
        self.m_model3d  = model3d
        # Sem handle externo: aloca um CDxIdent novo, com defaults para campos faltantes
        if              (dxobj == None):
            global      glb_identd
            # ident1 ausente: serializa um identificador global crescente
            if          (ident1x == None):
                ident1x = glb_identd
                glb_identd = glb_identd + 1
            if          (ident2x == None):
                ident2x = 0
            if          (ident3x == None):
                ident3x = 0
            if          (ident4x == None):
                ident4x = 0
            parident1   = ctypes.c_int (ident1x)
            parident2   = ctypes.c_int (ident2x)
            parident3   = ctypes.c_int (ident3x)
            parident4   = ctypes.c_int (ident4x)
            self.m_dxobj= None
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_ialoc= 1
            self.m_model3d.m_dxiodll.CDxIdent_Create (parident1, parident2, parident3, parident4, \
                                ctypes.byref (pardxobj))
            self.m_dxobj = pardxobj.value
        else:
            # Envelopa handle pré-existente: este objeto não é dono
            self.m_dxobj = dxobj
            self.m_ialoc= 0

    def __del__(self) -> None:
        """Libera o handle ``CDxIdent`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxIdent_Delete (pardxobj)
            self.m_dxobj = None

#
#    Representação deste objeto
#
    def __str__(self) -> str:
        """Retorna representação textual do identificador para depuração."""
        msg         = "\nClass _AttribIdent"
        msg         += "\n   %8d %8d %8d %8d" % (self.ident1, self.ident2, self.ident3, self.ident4)
        return         msg

    @property
    def ident1 (self) -> int:
        """Identificador 1."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        ident1x         = 0
        parident1       = ctypes.c_int (ident1x)
        self.m_model3d.m_dxiodll.CDxIdent_GetId1 (pardxobj, ctypes.byref (parident1))
        ident1x         = parident1.value
        return          ident1x

    @ident1.setter
    def ident1 (self, ident1x: int) -> None:
        """Atribui Identificador 1."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parident1       = ctypes.c_int (ident1x)
        self.m_model3d.m_dxiodll.CDxIdent_SetId1 (pardxobj, parident1)

    @property
    def ident2 (self) -> int:
        """Identificador 2."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        ident2x         = 0
        parident2       = ctypes.c_int (ident2x)
        self.m_model3d.m_dxiodll.CDxIdent_GetId2 (pardxobj, ctypes.byref (parident2))
        ident2x         = parident2.value
        return          ident2x

    @ident2.setter
    def ident2 (self, ident2x: int) -> None:
        """Atribui Identificador 2."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parident2       = ctypes.c_int (ident2x)
        self.m_model3d.m_dxiodll.CDxIdent_SetId2 (pardxobj, parident2)

    @property
    def ident3 (self) -> int:
        """Identificador 3."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        ident3x         = 0
        parident3       = ctypes.c_int (ident3x)
        self.m_model3d.m_dxiodll.CDxIdent_GetId3 (pardxobj, ctypes.byref (parident3))
        ident3x         = parident3.value
        return          ident3x

    @ident3.setter
    def ident3 (self, ident3x: int) -> None:
        """Atribui Identificador 3.

        ATENÇÃO: na biblioteca TQS este setter lê o nome ``ident3`` em vez do
        parâmetro ``ident3x``, então TODA atribuição a ``ident3`` levanta
        ``NameError``. Use ``ident1``, ``ident2`` ou ``ident4`` para identificar
        o objeto até que a biblioteca seja corrigida.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parident3       = ctypes.c_int (ident3)
        self.m_model3d.m_dxiodll.CDxIdent_SetId3 (pardxobj, parident3)

    @property
    def ident4 (self) -> int:
        """Identificador 4."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        ident4x         = 0
        parident4       = ctypes.c_int (ident4x)
        self.m_model3d.m_dxiodll.CDxIdent_GetId4 (pardxobj, ctypes.byref (parident4))
        ident4x         = parident4.value
        return          ident4x

    @ident4.setter
    def ident4 (self, ident4x: int) -> None:
        """Atribui Identificador 4."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parident4       = ctypes.c_int (ident4x)
        self.m_model3d.m_dxiodll.CDxIdent_SetId4 (pardxobj, parident4)

    def Clone (self) -> "_AttribIdent":
        """Duplica o identificador atual.

        Returns:
            Cópia independente deste :class:`_AttribIdent`.
        """
        atribident      = _AttribIdent (self.m_model3d, self.ident1, self.ident2, \
                                        self.ident3, self.ident4)
        return          atribident
#-----------------------------------------------------------------------------
#       Atributo chave => valor
#
class _AttribKv ():
    """Atributo do tipo chave => valor.

    Implementação:
        Wrapper sobre ``CDxAtribCh`` em ``NDXIODLL.DLL``. O construtor segue
        o padrão alocar-ou-envelopar (``m_ialoc``); as properties ``key``
        e ``value`` codificam/decodificam strings em ``TQSUtil.CHARSET`` e
        delegam a ``CDxAtribCh_Get*`` / ``CDxAtribCh_Set*``.

    Attributes:
        m_model3d: Modelo 3D proprietário.
        m_dxobj: Handle interno do objeto ``CDxAtribCh``.
        m_ialoc: ``1`` se este objeto possui ownership do handle.
    """

    def __init__ (self, model3d: "Model3D", chave: str, valor: str,
                    dxobj: Optional[int] = None) -> None:
        """Cria um atributo chave => valor.

        Args:
            model3d: Modelo 3D proprietário.
            chave: Chave do atributo.
            valor: Valor associado à chave.
            dxobj: Handle existente para envelopar (uso interno).
        """
        self.m_model3d  = model3d
        if              (dxobj == None):
            self.m_dxobj= None
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            parkey      = ctypes.c_char_p  (chave.encode(TQS.TQSUtil.CHARSET))
            parvalue    = ctypes.c_char_p  (valor.encode(TQS.TQSUtil.CHARSET))
            self.m_model3d.m_dxiodll.CDxAtribCh_Create (parkey, parvalue, ctypes.byref (pardxobj))
            self.m_dxobj= pardxobj.value
            self.m_ialoc= 1
        else:
            self.m_dxobj= dxobj
            self.m_ialoc= 0


    def __del__(self) -> None:
        """Libera o handle ``CDxAtribCh`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxAtribCh_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

#
#    Representação deste objeto
#
    def __str__(self) -> str:
        """Retorna representação textual do par chave/valor."""
        msg         = "\nClass _AttribKv"
        msg         += "\n   [%s] = [%s]" % (self.key, self.value)
        return         msg

    @property
    def key (self) -> str:
        """Chave do par ``(chave, valor)``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        key             = None
        parkey          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        bufferSize      = TQS.TQSUtil.MAXNCSTR
        parbufferSize   = ctypes.c_int (bufferSize)
        self.m_model3d.m_dxiodll.CDxAtribCh_GetKey (pardxobj, parkey, parbufferSize)
        key             = parkey.value.decode (TQS.TQSUtil.CHARSET)
        return          key

    @key.setter
    def key (self, chave: str) -> None:
        """Atribui Chave do par ``(chave, valor)``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parkey          = ctypes.c_char_p (chave.encode(TQS.TQSUtil.CHARSET))
        self.m_model3d.m_dxiodll.CDxAtribCh_SetKey (pardxobj, parkey)

    @property
    def value (self) -> str:
        """Valor do par ``(chave, valor)``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        value           = None
        parvalue        = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        bufferSize      = TQS.TQSUtil.MAXNCSTR
        parbufferSize   = ctypes.c_int (bufferSize)
        self.m_model3d.m_dxiodll.CDxAtribCh_GetValue (pardxobj, parvalue, parbufferSize)
        value           = parvalue.value.decode (TQS.TQSUtil.CHARSET)
        return          value

    @value.setter
    def value (self, chave: str) -> None:
        """Atribui Valor do par ``(chave, valor)``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parvalue          = ctypes.c_char_p (chave.encode(TQS.TQSUtil.CHARSET))
        self.m_model3d.m_dxiodll.CDxAtribCh_SetValue (pardxobj, parvalue)

    def Clone (self) -> "_AttribKv":
        """Duplica o objeto atual.

        Returns:
            Cópia independente deste :class:`_AttribKv`.
        """
        atribkv         = _AttribKv (self.m_model3d, self.key, self.value)
        return          atribkv

#-----------------------------------------------------------------------------
#       Um grupo de atributos chave => Valor
#
class _AttribGroup ():
    """Grupo de atributos do tipo chave => valor.

    Implementação:
        Wrapper sobre ``CDxAtribGr`` em ``NDXIODLL.DLL``. Internamente é um
        container de :class:`_AttribKv`; :meth:`EnterAttribKv` adiciona,
        :meth:`NumAttribKv` / :meth:`GetAttribKv` iteram. :meth:`Clone`
        replica grupo + atributos via loop sobre ``GetAttribKv``.

    Attributes:
        m_model3d: Modelo 3D proprietário.
        m_dxobj: Handle interno do objeto ``CDxAtribGr``.
        m_ialoc: ``1`` se este objeto possui ownership do handle.
    """

    def __init__ (self, model3d: "Model3D", nomgrupo: Optional[str] = None,
                    dxobj: Optional[int] = None) -> None:
        """Cria um grupo de atributos chave => valor.

        Args:
            model3d: Modelo 3D proprietário.
            nomgrupo: Nome do grupo.
            dxobj: Handle existente para envelopar (uso interno).
        """
        self.m_model3d  = model3d
        # Sem handle externo: aloca um CDxAtribGr e em seguida grava o nome do grupo
        if              (dxobj == None):
            if          (nomgrupo == None):
                nomgrupo    = ""
            self.m_dxobj    = None
            pardxobj        = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxAtribGr_Create (ctypes.byref (pardxobj))
            self.m_dxobj    = pardxobj.value
            self.m_ialoc    = 1
            parnomgrupo     = ctypes.c_char_p  (nomgrupo.encode(TQS.TQSUtil.CHARSET))
            self.m_model3d.m_dxiodll.CDxAtribGr_SetGroupName (pardxobj, parnomgrupo)
        else:
            # Envelopa handle pré-existente: este objeto não é dono
            self.m_dxobj    = dxobj
            self.m_ialoc    = 0

    def __del__(self) -> None:
        """Libera o handle ``CDxAtribGr`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxAtribGr_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

#
#    Representação deste objeto
#
    def __str__(self) -> str:
        """Retorna representação textual do grupo de atributos."""
        msg             = "\nClass _AttribGroup"
        numatribkv      = self.NumAttribKv()
        msg             += "\n   [%s] atributos=%d" % (self.groupName, numatribkv)
        for             iatrib in range (0, numatribkv):
            msg         += "\n   [%s]" % str (self.GetAttribKv (iatrib))
        return         msg

    @property
    def groupName (self) -> str:
        """Nome do grupo."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        nomgrupo        = None
        parnomgrupo     = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        bufferSize      = TQS.TQSUtil.MAXNCSTR
        parbufferSize   = ctypes.c_int (bufferSize)
        self.m_model3d.m_dxiodll.CDxAtribGr_GetGroupName (pardxobj, \
                                parnomgrupo, parbufferSize)
        nomgrupo        = parnomgrupo.value.decode (TQS.TQSUtil.CHARSET)
        return          nomgrupo

    @groupName.setter
    def groupName (self, nomgrupo: str) -> None:
        """Atribui Nome do grupo."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parnomgrupo     = ctypes.c_char_p (nomgrupo.encode(TQS.TQSUtil.CHARSET))
        self.m_model3d.m_dxiodll.CDxAtribGr_SetGroupName (pardxobj, parnomgrupo)

    def EnterAttribKv (self, atribkv: "_AttribKv") -> None:
        """Insere um atributo chave/valor no grupo.

        Args:
            atribkv: Atributo (:class:`_AttribKv`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paratribch      = ctypes.c_void_p (atribkv.m_dxobj)
        self.m_model3d.m_dxiodll.CDxAtribGr_AddAttribute (pardxobj, paratribch)

    def NumAttribKv (self) -> int:
        """Retorna o número de atributos do tipo :class:`_AttribKv` no grupo.

        Returns:
            Quantidade de atributos.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        numatrib        = 0
        parnumatrib     = ctypes.c_int (numatrib)
        self.m_model3d.m_dxiodll.CDxAtribGr_GetNumAttributes (pardxobj, ctypes.byref (parnumatrib))
        numatrib        = parnumatrib.value
        return          numatrib


    def GetAttribKv (self, indatrib: int) -> "_AttribKv":
        """Retorna um atributo do grupo pelo índice.

        Args:
            indatrib: Índice no intervalo ``0..NumAttribKv()-1``.

        Returns:
            Atributo (:class:`_AttribKv`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parindatrib     = ctypes.c_int (indatrib)
        paratribch      = ctypes.c_void_p (None)
        self.m_model3d.m_dxiodll.CDxAtribGr_GetAttribute (pardxobj, parindatrib,
                            ctypes.byref (paratribch))
        dxobj           = paratribch.value
        atribkv         = _AttribKv (self.m_model3d, "", "", dxobj)
        return          atribkv


    def Clone (self) -> "_AttribGroup":
        """Duplica o grupo atual com todos os seus atributos.

        Returns:
            Cópia independente deste :class:`_AttribGroup`.
        """
        atribgroup      = _AttribGroup (self.m_model3d, self.groupName)
        # Replica os pares chave/valor para garantir cópia profunda
        numatribkv      = self.NumAttribKv()
        for             iatrib in range (0, numatribkv):
            atribgroup.EnterAttribKv (self.GetAttribKv (iatrib))
        return          atribgroup
#-----------------------------------------------------------------------------
#       Atributos de um elemento gráfico
#       AtribIdent() não pertence à Attrib em CDxIo, mas colocamos aqui para facilitar
#
class _Attrib ():
    """Atributos de um elemento gráfico do modelo 3D.

    Implementação:
        Wrapper sobre ``CDxAtrib`` em ``NDXIODLL.DLL``. Em ``CDxIo`` o
        ``AttribIdent`` é externo ao ``CDxAtrib``, mas este wrapper Python
        agrega ambos para conveniência (``m_atribident``). As properties
        (``title``, ``number``, ``elemType`` …) são wrappers individuais
        sobre ``CDxAtrib_Get*`` / ``CDxAtrib_Set*``; :meth:`AttribGroupEnter`
        / :meth:`ReadAttribGroup` lidam com grupos chave/valor anexos.

    Attributes:
        m_model3d: Modelo 3D proprietário.
        m_dxobj: Handle interno do objeto ``CDxAtrib``.
        m_ialoc: ``1`` se este objeto possui ownership do handle.
        m_atribident: Identificador único (:class:`_AttribIdent`) associado.
        m_icriouatrib: ``1`` se o ``AttribIdent`` foi criado por este objeto.
    """

    def __init__ (self, model3d: "Model3D", titulo: Optional[str] = None,
                    ielem: Optional[int] = None, itrecho: Optional[int] = None,
                    itipelem: Optional[int] = None, ipiso: Optional[int] = None,
                    icor: Optional[int] = None, nompav: Optional[str] = None,
                    maternp: Optional[str] = None, ietapa: Optional[int] = None,
                    atribident: Optional["_AttribIdent"] = None,
                    transesp: Optional[float] = None, dxobj: Optional[int] = None) -> None:
        """Cria atributos de um elemento gráfico.

        Args:
            model3d: Modelo 3D proprietário.
            titulo: Título do elemento.
            ielem: Número do elemento.
            itrecho: Número do trecho.
            itipelem: Tipo de elemento (constantes ``E3D_TIPO*``).
            ipiso: Piso.
            icor: Cor RGB.
            nompav: Nome do pavimento.
            maternp: Material não padrão.
            ietapa: Etapa construtiva.
            atribident: Identificador único (:class:`_AttribIdent`).
            transesp: Opacidade em ``%`` (se diferente de ``0``).
            dxobj: Handle existente para envelopar (uso interno).
        """
        self.m_model3d  = model3d
        # Defaults para todos os campos opcionais
        if              (titulo == None):
            titulo      = ""
        if              (ielem == None):
            ielem       = 0
        if              (itrecho == None):
            itrecho     = 0
        if              (itipelem == None):
            itipelem    = E3D_TIPOINVALIDO
        if              (ipiso == None):
            ipiso       = 0
        if              (icor == None):
            icor        = 0
        if              (nompav == None):
            nompav      = ""
        if              (maternp == None):
            maternp     = ""
        if              (ietapa == None):
            ietapa      = 0
        if              (transesp == None):
            transesp    = 0.
        self.m_atribident = atribident
        self.m_icriouatrib = 0
        # Sem handle externo: aloca CDxAtrib e popula via setters; cria também AttribIdent default
        if              (dxobj == None):
            self.m_dxobj= None
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxAtrib_Create (ctypes.byref (pardxobj))
            self.m_dxobj= pardxobj.value
            self.m_ialoc= 1
            # Cada atribuição abaixo dispara um setter que chama a DLL
            self.title  = titulo
            self.number = ielem
            self.segment= itrecho
            self.elemType= itipelem
            self.level  = ipiso
            self.color  = icor
            self.floorName= nompav
            self.material = maternp
            self.stage  = ietapa
            self.transparency = transesp
            # AttribIdent criado aqui é dono; m_icriouatrib sinaliza para o destrutor liberá-lo
            self.m_atribident = self.m_model3d.base.AttribIdent ()
            self.m_icriouatrib = 1
        else:
            # Envelopa handle pré-existente: este objeto não é dono
            self.m_dxobj= dxobj
            self.m_ialoc= 0

    def __del__(self) -> None:
        """Libera o handle ``CDxAtrib`` e o ``AttribIdent`` se aplicável."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj  = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxAtrib_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0
        if              (self.m_atribident != None and self.m_icriouatrib != 0):
            del         self.m_atribident
            self.m_atribident = None

#
#    Representação deste objeto
#
    def __str__(self) -> str:
        """Retorna representação textual destes atributos."""
        msg             = "\nClass _Attrib"
        msg             += "\n   dxobj [%x]" % self.m_dxobj
        msg             += "\n   m_ialoc      %d" % self.m_ialoc
        msg             += "\n   title        %s" % self.title
        msg             += "\n   number       %d" % self.number
        msg             += "\n   segment      %d" % self.segment
        msg             += "\n   elemType     %d" % self.elemType
        msg             += "\n   level        %d" % self.level
        msg             += "\n   color        %d" % self.color
        msg             += "\n   floorName    %s" % self.floorName
        msg             += "\n   material     %s" % self.material
        msg             += "\n   stage        %d" % self.stage
        msg             += "\n   transparency %d" % self.transparency
        return         msg

    @property
    def title (self) -> str:
        """Título do elemento."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parident        = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        bufferSize      = TQS.TQSUtil.MAXNCSTR
        parbufferSize   = ctypes.c_int (bufferSize)
        self.m_model3d.m_dxiodll.CDxAtrib_GetIdent (pardxobj, parident, parbufferSize)
        titulo           = parident.value.decode (TQS.TQSUtil.CHARSET)
        return          titulo

    @title.setter
    def title (self, titulo: str) -> None:
        """Atribui Título do elemento."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parident        = ctypes.c_char_p (titulo.encode (TQS.TQSUtil.CHARSET))
        self.m_model3d.m_dxiodll.CDxAtrib_SetIdent (pardxobj, parident)

    @property
    def number (self) -> int:
        """Número do elemento."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        ielem           = 0
        parielem        = ctypes.c_int (ielem)
        self.m_model3d.m_dxiodll.CDxAtrib_GetIelem (pardxobj, ctypes.byref (parielem))
        ielem           = parielem.value
        return          ielem

    @number.setter
    def number (self, ielem: int) -> None:
        """Atribui Número do elemento."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parielem        = ctypes.c_int (ielem)
        self.m_model3d.m_dxiodll.CDxAtrib_SetIelem (pardxobj, parielem)

    @property
    def segment (self) -> int:
        """Número do trecho."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        itrecho         = 0
        paritrecho      = ctypes.c_int (itrecho)
        self.m_model3d.m_dxiodll.CDxAtrib_GetItrecho (pardxobj, ctypes.byref (paritrecho))
        itrecho         = paritrecho.value
        return          itrecho

    @segment.setter
    def segment (self, itrecho: int) -> None:
        """Atribui Número do trecho."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paritrecho      = ctypes.c_int (itrecho)
        self.m_model3d.m_dxiodll.CDxAtrib_SetItrecho (pardxobj, paritrecho)

    @property
    def elemType (self) -> int:
        """Tipo de elemento (constantes ``E3D_TIPO*``)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        itipelem        = 0
        paritipelem     = ctypes.c_int (itipelem)
        self.m_model3d.m_dxiodll.CDxAtrib_GetItipelem (pardxobj, ctypes.byref (paritipelem))
        itipelem        = paritipelem.value
        return          itipelem

    @elemType.setter
    def elemType (self, itipelem: int) -> None:
        """Atribui Tipo de elemento (constantes ``E3D_TIPO*``)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paritipelem     = ctypes.c_int (itipelem)
        self.m_model3d.m_dxiodll.CDxAtrib_SetItipelem (pardxobj, paritipelem)

    @property
    def level (self) -> int:
        """Número do piso."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        ipiso           = 0
        paripiso        = ctypes.c_int (ipiso)
        self.m_model3d.m_dxiodll.CDxAtrib_GetIpiso (pardxobj, ctypes.byref (paripiso))
        ipiso           = paripiso.value
        return          ipiso

    @level.setter
    def level (self, ipiso: int) -> None:
        """Atribui Número do piso."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paripiso        = ctypes.c_int (ipiso)
        self.m_model3d.m_dxiodll.CDxAtrib_SetIpiso (pardxobj, paripiso)

    @property
    def color (self) -> int:
        """Cor RGB do elemento se diferente de ``0``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        icor            = 0
        paricor         = ctypes.c_int (icor)
        self.m_model3d.m_dxiodll.CDxAtrib_GetIcor (pardxobj, ctypes.byref (paricor))
        icor            = paricor.value
        return          icor

    @color.setter
    def color (self, icor: int) -> None:
        """Atribui Cor RGB do elemento se diferente de ``0``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paricor         = ctypes.c_int (icor)
        self.m_model3d.m_dxiodll.CDxAtrib_SetIcor (pardxobj, paricor)

    @property
    def floorName (self) -> str:
        """Nome da planta."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parnompav       = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        bufferSize      = TQS.TQSUtil.MAXNCSTR
        parbufferSize   = ctypes.c_int (bufferSize)
        self.m_model3d.m_dxiodll.CDxAtrib_GetNompav (pardxobj, parnompav, parbufferSize)
        nompav           = parnompav.value.decode (TQS.TQSUtil.CHARSET)
        return          nompav

    @floorName.setter
    def floorName (self, nompav: str) -> None:
        """Atribui Nome da planta."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parnompav       = ctypes.c_char_p (nompav.encode (TQS.TQSUtil.CHARSET))
        self.m_model3d.m_dxiodll.CDxAtrib_SetNompav (pardxobj, parnompav)

    @property
    def material (self) -> str:
        """Nome do material."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parmaternp      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        bufferSize      = TQS.TQSUtil.MAXNCSTR
        parbufferSize   = ctypes.c_int (bufferSize)
        self.m_model3d.m_dxiodll.CDxAtrib_GetMaternp (pardxobj, parmaternp, parbufferSize)
        maternp           = parmaternp.value.decode (TQS.TQSUtil.CHARSET)
        return          maternp

    @material.setter
    def material (self, maternp: str) -> None:
        """Atribui Nome do material."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parmaternp      = ctypes.c_char_p (maternp.encode (TQS.TQSUtil.CHARSET))
        self.m_model3d.m_dxiodll.CDxAtrib_SetMaternp (pardxobj, parmaternp)

    @property
    def stage (self) -> int:
        """Etapa construtiva."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        ietapa          = 0
        parietapa       = ctypes.c_int (ietapa)
        self.m_model3d.m_dxiodll.CDxAtrib_GetIetapa (pardxobj, ctypes.byref (parietapa))
        ietapa          = parietapa.value
        return          ietapa

    @stage.setter
    def stage (self, ietapa: int) -> None:
        """Atribui Etapa construtiva."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parietapa       = ctypes.c_int (ietapa)
        self.m_model3d.m_dxiodll.CDxAtrib_SetIetapa (pardxobj, parietapa)

    @property
    def transparency (self) -> float:
        """Opacidade em ``%`` (se diferente de ``0``)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        transesp        = 0.
        partransesp     = ctypes.c_double (transesp)
        self.m_model3d.m_dxiodll.CDxAtrib_GetTransparency (pardxobj, \
                            ctypes.byref (partransesp))
        transesp        = partransesp.value
        return          transesp

    @transparency.setter
    def transparency (self, transesp: float) -> None:
        """Atribui Opacidade em ``%`` (se diferente de ``0``)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransesp     = ctypes.c_double (transesp)
        self.m_model3d.m_dxiodll.CDxAtrib_SetTransparency (pardxobj, partransesp)

    def AttribGroupEnter (self, atribgroup: "_AttribGroup") -> None:
        """Insere um grupo de atributos.

        Args:
            atribgroup: Grupo de atributos (:class:`_AttribGroup`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        paratribgr      = ctypes.c_void_p (atribgroup.m_dxobj)
        self.m_model3d.m_dxiodll.CDxAtrib_AddAtribGr (pardxobj, pardxiomem, paratribgr)

    def NumAttribGroup (self) -> int:
        """Retorna o número de grupos de atributos.

        Returns:
            Quantidade de grupos.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        numgrupos       = 0
        parnumgrupos    = ctypes.c_int (numgrupos)
        self.m_model3d.m_dxiodll.CDxAtrib_GetNumAtribgr (pardxobj, \
                            ctypes.byref (parnumgrupos))
        numgrupos       = parnumgrupos.value
        return          numgrupos

    def ReadAttribGroup (self, iatrib: int) -> "_AttribGroup":
        """Retorna um grupo de atributos pelo índice.

        Args:
            iatrib: Índice no intervalo ``0..NumAttribGroup()-1``.

        Returns:
            Grupo de atributos (:class:`_AttribGroup`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        pariatrib       = ctypes.c_int (iatrib)
        atribgroup      = _AttribGroup (self.m_model3d)
        paratribgr      = ctypes.c_void_p (atribgroup.m_dxobj)
        self.m_model3d.m_dxiodll.CDxAtrib_GetAtribgr (pardxobj, pardxiomem, \
                                pariatrib, paratribgr)
        return          atribgroup

    @property
    def attribIdent (self) -> "_AttribIdent":
        """Identificador único (:class:`_AttribIdent`)."""
        return          self.m_atribident

    @attribIdent.setter
    def attribIdent (self, atribident: "_AttribIdent") -> None:
        """Atribui Identificador único (:class:`_AttribIdent`)."""
        self.m_atribident = atribident

    def Clone (self) -> "_Attrib":
        """Duplica o objeto atual.

        Returns:
            Cópia independente deste :class:`_Attrib`.
        """
        atribident      = self.attribIdent.Clone ()
        atrib           = _Attrib (self.m_model3d, self.title, self.number, self.segment, \
                                   self.elemType, self.level, self.color, self.floorName, \
                                   self.material, self.stage, atribident, self.transparency)
        return          atrib

#-----------------------------------------------------------------------------
#       Coordenadas homogêneas 3D
#
class _Coords ():
    """Coordenadas homogêneas 3D (vetor/ponto).

    Implementação:
        Wrapper sobre ``CDxXyz`` em ``NDXIODLL.DLL``. As properties ``x``,
        ``y``, ``z`` usam ``CDxXyz_GetX/Y/Z`` e ``CDxXyz_SetX/Y/Z``; as
        operações vetoriais (:meth:`Magnitude`, :meth:`CrossProduct`,
        :meth:`DotProduct`, :meth:`UnitVector`, :meth:`Invert`) e
        geométricas (:meth:`Move`, :meth:`Scale`, :meth:`RotateXY`,
        :meth:`Transform`) delegam aos correspondentes em ``CDxXyz_*``.

    Attributes:
        DEL: Tolerância numérica padrão.
        m_model3d: Modelo 3D proprietário.
        m_dxobj: Handle interno do objeto ``CDxXyz``.
        m_ialoc: ``1`` se este objeto possui ownership do handle.
    """

    DEL: float = 1.E-5         # Tolerância

    def __init__ (self, model3d: "Model3D", x: Optional[float] = None,
                    y: Optional[float] = None, z: Optional[float] = None,
                    dxobj: Optional[int] = None) -> None:
        """Cria coordenadas 3D.

        Args:
            model3d: Modelo 3D proprietário.
            x: Coordenada X.
            y: Coordenada Y.
            z: Coordenada Z.
            dxobj: Handle existente para envelopar (uso interno).
        """
        self.m_model3d  = model3d
        if              (dxobj == None):
            if          (x == None):
                x       = 0.
            if          (y == None):
                y       = 0.
            if          (z == None):
                z       = 0.
            parx        = ctypes.c_double (x)
            pary        = ctypes.c_double (y)
            parz        = ctypes.c_double (z)
            self.m_dxobj= None
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxXyz_Create (parx, pary, parz, ctypes.byref (pardxobj))
            self.m_dxobj= pardxobj.value
            self.m_ialoc= 1
        else:
            self.m_dxobj= dxobj
            self.m_ialoc= 0

    def __del__(self) -> None:
        """Libera o handle ``CDxXyz`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj  = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxXyz_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

    def __str__(self) -> str:
        """Retorna representação textual das coordenadas."""
        msg             = "\nClass _Coords"
        msg             += "\n   %10.3f,%10.3f,%10.3f" % (self.x, self.y, self.z)
        return         msg

    @property
    def x (self) -> float:
        """Valor de ``x``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        x               = 0.
        parx            = ctypes.c_double (x)
        self.m_model3d.m_dxiodll.CDxXyz_GetX (pardxobj, ctypes.byref (parx))
        x               = parx.value
        return          x

    @x.setter
    def x (self, x: float) -> None:
        """Atribui Valor de ``x``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parx            = ctypes.c_double (x)
        self.m_model3d.m_dxiodll.CDxXyz_SetX (pardxobj, parx)

    @property
    def y (self) -> float:
        """Valor de ``y``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        y               = 0.
        pary            = ctypes.c_double (y)
        self.m_model3d.m_dxiodll.CDxXyz_GetY (pardxobj, ctypes.byref (pary))
        y               = pary.value
        return          y

    @y.setter
    def y (self, y: float) -> None:
        """Atribui Valor de ``y``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pary            = ctypes.c_double (y)
        self.m_model3d.m_dxiodll.CDxXyz_SetY (pardxobj, pary)

    @property
    def z (self) -> float:
        """Valor de ``z``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        z               = 0.
        parz            = ctypes.c_double (z)
        self.m_model3d.m_dxiodll.CDxXyz_GetZ (pardxobj, ctypes.byref (parz))
        z               = parz.value
        return          z

    @z.setter
    def z (self, z: float) -> None:
        """Atribui Valor de ``z``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parz            = ctypes.c_double (z)
        self.m_model3d.m_dxiodll.CDxXyz_SetZ (pardxobj, parz)

    def Magnitude (self) -> float:
        """Retorna o módulo (comprimento) do vetor.

        Returns:
            Módulo do vetor.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        modulo          = 0.
        parmodulo       = ctypes.c_double (modulo)
        self.m_model3d.m_dxiodll.CDxXyz_GetMagnitude (pardxobj, ctypes.byref (parmodulo))
        modulo          = parmodulo.value
        return          modulo

    def CrossProduct (self, u: "_Coords") -> "_Coords":
        """Calcula o produto vetorial ``self`` x ``u``.

        Args:
            u: Vetor operando.

        Returns:
            Vetor (:class:`_Coords`) resultante.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxobju       = ctypes.c_void_p (u.m_dxobj)
        v               = _Coords (self.m_model3d)
        pardxobjv       = ctypes.c_void_p (v.m_dxobj)
        self.m_model3d.m_dxiodll.CDxXyz_CrossProduct (pardxobj, pardxobju, pardxobjv)
        return          v

    def DotProduct (self, u: "_Coords") -> float:
        """Calcula o produto escalar ``self`` . ``u``.

        Args:
            u: Vetor operando.

        Returns:
            Produto escalar (``double``).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxobju       = ctypes.c_void_p (u.m_dxobj)
        dotp            = 0.
        pardotp         = ctypes.c_double (dotp)
        self.m_model3d.m_dxiodll.CDxXyz_DotProduct (pardxobj, pardxobju, ctypes.byref (pardotp))
        dotp            = pardotp.value
        return          dotp


    def UnitVector (self) -> None:
        """Transforma o vetor atual em versor (comprimento unitário)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CDxXyz_Normalize (pardxobj)


    def Invert (self) -> None:
        """Inverte o sentido do vetor."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CDxXyz_Invert (pardxobj)


    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada as coordenadas.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CDxXyz_Move (pardxobj, pardx, pardy, pardz)

    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Escala X.
            escy: Escala Y.
            escz: Escala Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parcz           = ctypes.c_double (cz)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CDxXyz_Scale (pardxobj, parcx, parcy, parcz, \
                                parescx, parescy, parescz)

    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda as coordenadas no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CDxXyz_RotateXY (pardxobj, parcx, parcy, parang)

    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma as coordenadas usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransf       = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxXyz_Transform (pardxobj, partransf)

    def Clone (self) -> "_Coords":
        """Duplica o objeto atual.

        Returns:
            Cópia independente deste :class:`_Coords`.
        """
        coords          = _Coords (self.m_model3d)
        coords.x        = self.x
        coords.y        = self.y
        coords.z        = self.z
        return          coords
#-----------------------------------------------------------------------------
#       Polygonal 3D
#
class _Polyg ():
    """Poligonal 3D representada por uma sequência de pontos.

    Implementação:
        Wrapper sobre ``CDxPol`` em ``NDXIODLL.DLL``. Os pontos são adicionados
        via :meth:`EnterPoint` (``CDxPol_AddPoint``) e iterados via
        :meth:`NumPoints` / :meth:`GetPoint`. As transformações geométricas
        delegam às funções ``CDxPol_*``.

    Attributes:
        m_model3d: Modelo 3D proprietário.
        m_dxobj: Handle interno do objeto ``CDxPol``.
        m_ialoc: ``1`` se este objeto possui ownership do handle.
    """

    def __init__ (self, model3d: "Model3D", dxobj: Optional[int] = None) -> None:
        """Cria uma poligonal 3D vazia ou envelopa um handle existente.

        Args:
            model3d: Modelo 3D proprietário.
            dxobj: Handle existente para envelopar (uso interno).
        """
        self.m_model3d  = model3d
        if              (dxobj == None):
            self.m_dxobj = None
            self.m_ialoc = 1
            pardxobj     = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxPol_Create (ctypes.byref (pardxobj))
            self.m_dxobj = pardxobj.value
        else:
            self.m_dxobj = dxobj
            self.m_ialoc = 0

    def __del__(self) -> None:
        """Libera o handle ``CDxPol`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxPol_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

    def __str__(self) -> str:
        """Retorna representação textual da poligonal."""
        msg             = "\nClass _Polyg"
        numpts          = self.NumPoints ()
        for             i in range (0, numpts):
            point       = self.GetPoint (i)
            msg         += "\n   %03d %10.3f,%10.3f,%10.3f" % (i, point.x, point.y, point.z)
        return          msg


    def EnterPoint (self, coords: "_Coords") -> None:
        """Adiciona um ponto à poligonal.

        Args:
            coords: Coordenadas do ponto (:class:`_Coords`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxpt         = ctypes.c_void_p (coords.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPol_AddPoint (pardxobj, pardxpt)

    def NumPoints (self) -> int:
        """Retorna o número de pontos da poligonal.

        Returns:
            Quantidade de pontos.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        numpoints       = 0
        parnumpoints    = ctypes.c_int (numpoints)
        self.m_model3d.m_dxiodll.CDxPol_GetPointCount (pardxobj, ctypes.byref (parnumpoints))
        numpoints       = parnumpoints.value
        return          numpoints

    def GetPoint (self, indpoint: int) -> "_Coords":
        """Retorna um ponto da poligonal pelo índice.

        Args:
            indpoint: Índice no intervalo ``0..NumPoints()-1``.

        Returns:
            Coordenadas (:class:`_Coords`) do ponto.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parindpoint     = ctypes.c_int (indpoint)
        pardxpt      = ctypes.c_void_p (None)
        self.m_model3d.m_dxiodll.CDxPol_GetPoint (pardxobj, parindpoint, ctypes.byref (pardxpt))
        dxobj           = pardxpt.value
        point           = _Coords (self.m_model3d, None, None, None, dxobj)
        return          point

    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada todos os pontos da poligonal.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CDxPol_Move (pardxobj, pardx, pardy, pardz)

    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parcz           = ctypes.c_double (cz)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CDxPol_Scale (pardxobj, parcx, parcy, parcz, \
                                parescx, parescy, parescz)

    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda os pontos da poligonal no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CDxPol_RotateXY (pardxobj, parcx, parcy, parang)

    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma a poligonal usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransf       = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPol_Transform (pardxobj, partransf)

    def Clone (self) -> "_Polyg":
        """Duplica a poligonal atual.

        Returns:
            Cópia independente desta :class:`_Polyg`.
        """
        polig           = _Polyg (self.m_model3d)
        # Replica ponto-a-ponto para garantir poligonal independente
        numpts          = self.NumPoints ()
        for             i in range (0, numpts):
            polig.EnterPoint (self.GetPoint (i))
        return          polig

#-----------------------------------------------------------------------------
#       Transformação geométrica 3D
#
class _Transf3D ():
    """Matriz de transformação geométrica 3D.

    Encapsula uma transformação afim 3D mais um buffer de coordenadas
    homogêneas auxiliar usado em :meth:`Transform`.

    Implementação:
        Wrapper sobre ``CGeo3DTrans`` (matriz 4x4) em ``NDXIODLL.DLL``. Os
        métodos :meth:`Move`, :meth:`RotateX/Y/Z`, :meth:`Scale`, etc.
        acumulam a transformação via ``CGeo3DTrans_*``. :meth:`Transform`
        usa um ``CGeo3DHomog`` auxiliar (``m_dxobj3dhomog``) para evitar
        alocações repetidas a cada chamada.

    Attributes:
        m_model3d: Modelo 3D proprietário.
        m_dxobj: Handle interno do objeto ``CGeo3DTrans``.
        m_dxobj3dhomog: Handle interno auxiliar de ``CGeo3DHomog``.
    """

    def __init__ (self, model3d: "Model3D") -> None:
        """Inicializa a matriz de transformação.

        Args:
            model3d: Modelo 3D proprietário.
        """
        self.m_model3d  = model3d
        self.m_dxobj    = None
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Create (ctypes.byref (pardxobj))
        self.m_dxobj    = pardxobj.value

        self.m_dxobj3dhomog = None                # Coordenada auxiliar para transformação
        pardxobj3dhomog = ctypes.c_void_p (self.m_dxobj3dhomog)
        self.m_model3d.m_dxiodll.CGeo3DHomog_Create (ctypes.byref (pardxobj3dhomog))
        self.m_dxobj3dhomog = pardxobj3dhomog.value

    def __del__(self) -> None:
        """Libera os handles internos da matriz e do buffer auxiliar."""
        if              (self.m_dxobj != None):
            pardxobj = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CGeo3DTrans_Delete (pardxobj)
            self.m_dxobj = None

        if              (self.m_dxobj3dhomog != None):
            pardxobj3dhomog = ctypes.c_void_p (self.m_dxobj3dhomog)
            self.m_model3d.m_dxiodll.CGeo3DHomog_Delete (pardxobj3dhomog)
            self.m_dxobj3dhomog = None

    def Unit (self) -> None:
        """Carrega a transformação identidade."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Unidade (pardxobj)

    def Zero (self) -> None:
        """Zera totalmente a transformação."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Zera (pardxobj)

    def ZeroMove (self) -> None:
        """Zera apenas a parte de translação da transformação."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CGeo3DTrans_ZerarMovimento (pardxobj)

    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Acumula uma translação à transformação.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Translacao (pardxobj, pardx, pardy, pardz)

    def RotateX (self, ang: float) -> None:
        """Acumula uma rotação em torno do eixo X.

        Args:
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CGeo3DTrans_RotacaoX (pardxobj, parang)

    def RotateY (self, ang: float) -> None:
        """Acumula uma rotação em torno do eixo Y.

        Args:
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CGeo3DTrans_RotacaoY (pardxobj, parang)

    def RotateZ (self, ang: float) -> None:
        """Acumula uma rotação em torno do eixo Z.

        Args:
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CGeo3DTrans_RotacaoZ (pardxobj, parang)

    def RotateAxis (self, ang: float, vx: float, vy: float, vz: float) -> None:
        """Acumula rotação anti-horária em torno de eixo passando pelo ``(0,0,0)``.

        Args:
            ang: Ângulo de rotação em graus.
            vx: Versor X do eixo.
            vy: Versor Y do eixo.
            vz: Versor Z do eixo.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parang          = ctypes.c_double (ang)
        parvx           = ctypes.c_double (vx)
        parvy           = ctypes.c_double (vy)
        parvz           = ctypes.c_double (vz)
        self.m_model3d.m_dxiodll.CGeo3DTrans_RotacaoEixo (pardxobj, parang, parvx, parvy, parvz)

    def Scale (self, escx: float, escy: float, escz: float) -> None:
        """Acumula uma escala isótropa por eixos.

        Args:
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Escala (pardxobj, parescx, parescy, parescz)

    def BaseTransform (self, x1: float, y1: float, z1: float,
                         x2: float, y2: float, z2: float) -> None:
        """Transforma seção XY centrada na origem para o ponto 1 de um vetor 1-2.

        Args:
            x1: X do ponto 1.
            y1: Y do ponto 1.
            z1: Z do ponto 1.
            x2: X do ponto 2.
            y2: Y do ponto 2.
            z2: Z do ponto 2.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parx1           = ctypes.c_double (x1)
        pary1           = ctypes.c_double (y1)
        parz1           = ctypes.c_double (z1)
        parx2           = ctypes.c_double (x2)
        pary2           = ctypes.c_double (y2)
        parz2           = ctypes.c_double (z2)
        self.m_model3d.m_dxiodll.CGeo3DTrans_TransfBase (pardxobj, parx1, pary1, parz1, \
                            parx2, pary2, parz2)

    def Multiply (self, transf: "_Transf3D") -> None:
        """Acumula transformação de coordenadas (multiplicação de matrizes).

        Args:
            transf: Matriz a multiplicar (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxobjmul     = ctypes.c_void_p (transf.m_dxobj)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Multiplica (pardxobj, pardxobjmul)

    def Invert (self) -> None:
        """Inverte a transformação."""
        pardxobj         = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Inverter (pardxobj)

    def Transform (self, coords: "_Coords") -> None:
        """Transforma coordenadas in-place.

        Args:
            coords: Coordenadas a serem transformadas (:class:`_Coords`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxobj3dhomog = ctypes.c_void_p (self.m_dxobj3dhomog)
        x               = coords.x
        y               = coords.y
        z               = coords.z
        parx            = ctypes.c_double (x)
        pary            = ctypes.c_double (y)
        parz            = ctypes.c_double (z)
        # Carrega coords no buffer homogêneo, multiplica pela matriz e relê o resultado
        self.m_model3d.m_dxiodll.CGeo3DHomog_Definir (pardxobj3dhomog, parx, pary, parz)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Transforma (pardxobj, pardxobj3dhomog)
        self.m_model3d.m_dxiodll.CGeo3DHomog_LerX (pardxobj3dhomog, ctypes.byref (parx))
        self.m_model3d.m_dxiodll.CGeo3DHomog_LerY (pardxobj3dhomog, ctypes.byref (pary))
        self.m_model3d.m_dxiodll.CGeo3DHomog_LerZ (pardxobj3dhomog, ctypes.byref (parz))
        # Atualiza o objeto _Coords original in-place
        coords.x        = parx.value
        coords.y        = pary.value
        coords.z        = parz.value

    def Clone (self) -> "_Transf3D":
        """Duplica o objeto atual.

        Returns:
            Cópia independente desta :class:`_Transf3D`.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        geo3dtrans2     = _Transf3D (self.m_model3d)
        pardxobj2       = ctypes.c_void_p (geo3dtrans2.m_dxobj)
        self.m_model3d.m_dxiodll.CGeo3DTrans_Clone (pardxobj, pardxobj2)
        geo3dtrans2.m_dxobj = pardxobj2.value
        return          geo3dtrans2

#-----------------------------------------------------------------------------
#       Uma face de sólido
#
class _Face ():
    """Face de sólido (contorno aberto orientado para fora).

    Implementação:
        Wrapper sobre ``CDxFace`` em ``NDXIODLL.DLL``. Vértices são adicionados
        via :meth:`EnterVertex` (com flags de visibilidade e arco) e relidos
        via :meth:`ReadVertex`. As properties (``normalVector``, ``section``,
        ``color``) e operações geométricas mapeiam diretamente para
        ``CDxFace_*``.

    Attributes:
        m_model3d: Modelo 3D proprietário.
        m_dxobj: Handle interno do objeto ``CDxFace``.
        m_ialoc: ``1`` se este objeto possui ownership do handle.
    """

    def __init__ (self, model3d: "Model3D", vetnorm: Optional["_Coords"] = None,
                    dxobj: Optional[int] = None) -> None:
        """Cria uma face de sólido.

        A face deve ser orientada para fora do sólido.

        Args:
            model3d: Modelo 3D proprietário.
            vetnorm: Vetor normal (:class:`_Coords`) que aponta para fora do sólido.
            dxobj: Handle existente para envelopar (uso interno).
        """
        self.m_model3d  = model3d
        # Sem handle externo: cria CDxFace com a normal informada (ou Z=+1 default)
        if              (dxobj == None):
            self.m_ialoc = 1
            icriarnormal = 0
            # Se chamador não forneceu normal, criamos uma temporária e descartamos depois
            if           (vetnorm == None):
                vetnorm = _Coords (self.m_model3d, 0., 0., 1.)
                icriarnormal= 1
            self.m_dxobj= None
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            pardxnormal = ctypes.c_void_p (vetnorm.m_dxobj)
            self.m_model3d.m_dxiodll.CDxFace_CreateWithNormal (pardxnormal, ctypes.byref (pardxobj))
            self.m_dxobj= pardxobj.value
            if          (icriarnormal != 0):
                del     vetnorm
        else:
            # Envelopa handle pré-existente: este objeto não é dono
            self.m_dxobj = dxobj
            self.m_ialoc = 0


    def __str__(self) -> str:
        """Retorna representação textual da face para depuração."""
        numvertices     = self.NumVertices ()
        msg             = "\nClass _Face vértices %d" % numvertices
        msg             += "\n   normalVector %s" % str (self.normalVector)
        msg             += "\n   section      %d" % self.section
        msg             += "\n   color        %X" % self.color

        return          msg

    def __del__(self) -> None:
        """Libera o handle ``CDxFace`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxFace_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

    def EnterVertex (self, vertice: "_Coords", invisivel: Optional[int] = None,
                       iarco: Optional[int] = None) -> None:
        """Adiciona um vértice ao contorno da face.

        Args:
            vertice: Coordenadas do vértice (:class:`_Coords`).
            invisivel: ``1`` se o trecho seguinte é invisível.
            iarco: ``1`` se centro do arco anti-horário, ``-1`` se horário.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parvertice      = ctypes.c_void_p (vertice.m_dxobj)
        if              (invisivel == None):
            invisivel   = 0
        if              (iarco == None):
            iarco       = 0
        parinvisivel    = ctypes.c_int (invisivel)
        pariarco        = ctypes.c_int (iarco)
        self.m_model3d.m_dxiodll.CDxFace_AddVertex (pardxobj, parvertice, parinvisivel, pariarco)

    def NumVertices (self) -> int:
        """Retorna o número de vértices da face.

        Returns:
            Quantidade de vértices.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        numvert         = 0
        parnumvert      = ctypes.c_int (numvert)
        self.m_model3d.m_dxiodll.CDxFace_GetNumVertices (pardxobj, ctypes.byref (parnumvert))
        numvert         = parnumvert.value
        return          numvert

    def ReadVertex (self, ivert: int) -> Tuple["_Coords", int, int]:
        """Retorna um vértice da face com seus flags de visibilidade e arco.

        Args:
            ivert: Índice do vértice no intervalo ``0..NumVertices()-1``.

        Returns:
            Tupla ``(vert, invisivel, iarco)``:

            * ``vert``: Coordenadas (:class:`_Coords`) do vértice.
            * ``invisivel``: ``1`` se final de trecho invisível.
            * ``iarco``: ``1`` se centro de arco entre vértices anterior e posterior.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parivert        = ctypes.c_int (ivert)
        pardxvert       = ctypes.c_void_p (None)
        # Lê o vértice + flags de visibilidade e arco em três chamadas separadas
        self.m_model3d.m_dxiodll.CDxFace_GetVertex (pardxobj, parivert, ctypes.byref (pardxvert))
        dxobj           = pardxvert.value
        vert            = _Coords (self.m_model3d, None, None, None, dxobj)
        vertcopia       = vert.Clone ()
        invisivel       = 0
        parinvisivel    = ctypes.c_int (invisivel)
        self.m_model3d.m_dxiodll.CDxFace_GetIsInvisible (pardxobj, parivert, \
                            ctypes.byref (parinvisivel))
        invisivel       = parinvisivel.value
        iarco           = 0
        pariarco        = ctypes.c_int (iarco)
        self.m_model3d.m_dxiodll.CDxFace_GetArcType (pardxobj, parivert, ctypes.byref (pariarco))
        iarco           = pariarco.value
        return          vert, invisivel, iarco

    @property
    def normalVector (self) -> "_Coords":
        """Vetor normal :class:`_Coords` que aponta para fora do sólido."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxvetnorm    = ctypes.c_void_p (None)
        self.m_model3d.m_dxiodll.CDxFace_GetNormal (pardxobj, ctypes.byref (pardxvetnorm))
        dxobj           = pardxvetnorm.value
        vetnorm         = _Coords (self.m_model3d, None, None, None, dxobj)
        return          vetnorm

    @normalVector.setter
    def normalVector (self, vetnorm: "_Coords") -> None:
        """Atribui Vetor normal :class:`_Coords` que aponta para fora do sólido."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parvetnorm      = ctypes.c_void_p (vetnorm.m_dxobj)
        self.m_model3d.m_dxiodll.CDxFace_SetNormal (pardxobj, parvetnorm)

    @property
    def section (self) -> int:
        """``1`` se face de corte."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        icorte          = 0
        paricorte       = ctypes.c_int (icorte)
        self.m_model3d.m_dxiodll.CDxFace_GetIsCutFace (pardxobj, ctypes.byref (paricorte))
        icorte          = paricorte.value
        return          icorte

    @section.setter
    def section (self, icorte: int) -> None:
        """Atribui ``1`` se face de corte."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paricorte       = ctypes.c_int (icorte)
        self.m_model3d.m_dxiodll.CDxFace_SetIsCutFace (pardxobj, paricorte)

    @property
    def color (self) -> int:
        """Cor RGB opcional da face (se diferente de ``0``)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        icor            = 0
        paricor         = ctypes.c_int (icor)
        self.m_model3d.m_dxiodll.CDxFace_GetColor (pardxobj, ctypes.byref (paricor))
        icor          = paricor.value
        return          icor

    @color.setter
    def color (self, icor: int) -> None:
        """Atribui Cor RGB opcional da face (se diferente de ``0``)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paricor         = ctypes.c_int (icor)
        self.m_model3d.m_dxiodll.CDxFace_SetColor (pardxobj, paricor)

    def ComputeNormals (self, sinal: float) -> None:
        """Calcula a normal a partir dos 3 primeiros vértices.

        Args:
            sinal: Multiplicador da normal (``1.`` ou ``-1.``).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parsinal        = ctypes.c_double (sinal)
        self.m_model3d.m_dxiodll.CDxFace_CalculateNormal (pardxobj, parsinal)


    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma a face usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransf       = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxFace_Transform (pardxobj, partransf)

    def Invert (self) -> None:
        """Inverte a orientação da face."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CDxFace_Invert (pardxobj)

    def CopyFrom (self, face: "_Face") -> None:
        """Torna o objeto atual uma cópia da face fornecida.

        Args:
            face: Objeto :class:`_Face` cujos dados serão copiados.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxface       = ctypes.c_void_p (face.m_dxobj)
        self.m_model3d.m_dxiodll.CDxFace_CopyFrom (pardxobj, pardxface)

    def Tesselate (self) -> "_Face":
        """Triangulariza arcos da face.

        Returns:
            Nova face (:class:`_Face`) com arcos discretizados.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        newface         = _Face (self.m_model3d)
        pardxobjnewface = ctypes.c_void_p (newface.m_dxobj)
        self.m_model3d.m_dxiodll.CDxFace_DiscretizeArc (pardxobj, pardxobjnewface)
        return          newface

    def Clone (self) -> "_Face":
        """Duplica a face atual.

        ATENÇÃO: o corpo instancia ``_face`` (minúsculo), um nome que não existe
        no módulo — a classe é ``_Face``. Toda chamada a ``Clone()`` levanta
        ``NameError``. Para duplicar, crie uma face nova e copie os vértices
        manualmente.

        Returns:
            Cópia independente desta :class:`_Face` — ver ATENÇÃO.
        """
        face            = _face (self.m_model3d, self.normalVector)
        # Replica vértice-a-vértice preservando flags de visibilidade e arco
        numvertices     = self.NumVertices ()
        for             ivert in range (0, numvertices):
            vertice, invisivel, iarco = self.ReadVertex (ivert)
            face.EnterVertex (vertice, invisivel, iarco)
        return          face
#-----------------------------------------------------------------------------
#       Classe base de objetos 3D
#
class _Elem3D (ABC):
    """Classe base abstrata para todos os elementos 3D do modelo.

    Define a interface comum de manipulação geométrica e propriedades comuns
    (tipo, atributos, flags de visibilidade/transparência etc.). Subclasses
    concretas: :class:`_Prism`, :class:`_ComplexPrism`, :class:`_GenericSolid`,
    :class:`_ExtrusionSolid` e :class:`_BlockInsert`.

    Implementação:
        Define a interface comum sobre ``CDxObj``: properties como ``type``,
        ``attrib``, ``erased``, ``invisible`` e ``transparent`` delegam a
        ``CDxObj_Get*`` / ``CDxObj_Set*``. Operações geométricas (``Move``,
        ``Scale``, ``RotateXY``, ``Transform``), :meth:`Clone` e
        :meth:`Tesselate` são abstratas — cada subclasse delega à família
        de funções da sua DLL específica (``CDxPri_*``, ``CDxPriC_*``,
        ``CDxSol_*``, ``CDxTrilha_*``, ``CDxBlocoIns_*``). O método
        :meth:`_AcertarAtribIdent` sincroniza o ``AttribIdent`` Python com
        o ``CDxIdent`` armazenado no objeto C++ após criar a partir de
        handle existente.

    Attributes:
        m_model3d: Modelo 3D proprietário.
        m_itipo: Tipo concreto do elemento (constante ``E3DTYPE_*``).
        m_dxobj: Handle interno do objeto da DLL (definido nas subclasses).
        m_ialoc: ``1`` se este objeto possui ownership do handle.
    """

    def __init__ (self, model3d: "Model3D", itipo: int) -> None:
        """Inicializa a classe base.

        Args:
            model3d: Modelo 3D proprietário.
            itipo: Tipo concreto do elemento (``E3DTYPE_*``).
        """
        self.m_model3d   = model3d
        self.m_itipo     = itipo

    @abstractmethod
    def __del__(self) -> None:
        """Destrutor obrigatório (implementado pelas subclasses)."""

    def _AcertarAtribIdent (self) -> None:
        """Sincroniza o ``AttribIdent`` do elemento com seu handle ``CDxObj``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        dxident         = None
        pardxident      = ctypes.c_void_p (dxident)
        self.m_model3d.m_dxiodll.CDxObj_GetDxIdent (pardxobj, ctypes.byref (pardxident))
        dxident         = pardxident.value
        self.attrib.m_atribident = self.m_model3d.base.AttribIdent (dxobj=dxident)

    @abstractmethod
    def _GravarSolido (self) -> int:
        """Insere o objeto no modelo.

        Returns:
            ``istat``: ``0`` se OK; valor diferente de zero em caso de erro.
        """
        pass

    @property
    def type (self) -> int:
        """Tipo do sólido (constante ``E3DTYPE_*``)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        itipo           = 0
        paritipo        = ctypes.c_int (itipo)
        self.m_model3d.m_dxiodll.CDxObj_GetType (pardxobj, ctypes.byref (paritipo))
        itipo           = paritipo.value
        return          itipo

    @type.setter
    def type (self, itipo: int) -> None:
        """Atribui Tipo do sólido (constante ``E3DTYPE_*``)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paritipo        = ctypes.c_int (itipo)
        self.m_model3d.m_dxiodll.CDxObj_SetType (pardxobj, paritipo)

    @property
    def attrib (self) -> "_Attrib":
        """Atributos do elemento (:class:`_Attrib`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxident      = ctypes.c_void_p (None)
        self.m_model3d.m_dxiodll.CDxObj_GetDxIdent (pardxobj, ctypes.byref (pardxident))
        dxident         = pardxident.value
        atribident      = self.m_model3d.base.AttribIdent (dxobj=dxident)

        pardxatrib      = ctypes.c_void_p (None)
        self.m_model3d.m_dxiodll.CDxObj_GetAtrib (pardxobj, ctypes.byref (pardxatrib))
        dxatrib         = pardxatrib.value
        atrib           = _Attrib (self.m_model3d, atribident=atribident, dxobj=dxatrib)
        return          atrib

    @attrib.setter
    def attrib (self, atrib: "_Attrib") -> None:
        """Atribui Atributos do elemento (:class:`_Attrib`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxatrib      = ctypes.c_void_p (atrib.m_dxobj)
        self.m_model3d.m_dxiodll.CDxObj_SetAtrib (pardxobj, pardxatrib)

    @property
    def erased (self) -> int:
        """``1`` se o elemento está marcado como apagado."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        iapagado        = 0
        pariapagado     = ctypes.c_int (iapagado)
        self.m_model3d.m_dxiodll.CDxObj_GetIsDeleted (pardxobj, ctypes.byref (pariapagado))
        iapagado        = pariapagado.value
        return          iapagado

    @erased.setter
    def erased (self, iapagado: int) -> None:
        """Atribui ``1`` se o elemento está marcado como apagado."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pariapagado     = ctypes.c_int (iapagado)
        self.m_model3d.m_dxiodll.CDxObj_SetIsDeleted (pardxobj, pariapagado)

    @property
    def invisible (self) -> int:
        """``1`` se o elemento está invisível."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        invisivel       = 0
        parinvisivel    = ctypes.c_int (invisivel)
        self.m_model3d.m_dxiodll.CDxObj_GetIsInvisible (pardxobj, ctypes.byref (parinvisivel))
        invisivel       = parinvisivel.value
        return          invisivel

    @invisible.setter
    def invisible (self, invisivel: int) -> None:
        """Atribui ``1`` se o elemento está invisível."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parinvisivel    = ctypes.c_int (invisivel)
        self.m_model3d.m_dxiodll.CDxObj_SetIsInvisible (pardxobj, parinvisivel)

    @property
    def transparent (self) -> int:
        """``1`` se o elemento está transparente."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        itranspar       = 0
        paritranspar    = ctypes.c_int (itranspar)
        self.m_model3d.m_dxiodll.CDxObj_GetIsTransparent (pardxobj, ctypes.byref (paritranspar))
        itranspar       = paritranspar.value
        return          itranspar

    @transparent.setter
    def transparent (self, itranspar: int) -> None:
        """Atribui ``1`` se o elemento está transparente."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        paritranspar    = ctypes.c_int (itranspar)
        self.m_model3d.m_dxiodll.CDxObj_SetIsTransparent (pardxobj, paritranspar)

    def CopyFrom (self, elm3d: "_Elem3D") -> None:
        """Torna o objeto atual uma cópia de outro elemento.

        Args:
            elm3d: Objeto fonte (:class:`_Elem3D`).
        """
        self.m_itipo     = elm3d.m_itipo


    def CSGOperation (self, elm3d: "_Elem3D", operation: int) -> Tuple[int, "_GenericSolid"]:
        """Aplica operação CSG (união, intersecção, subtração ou XOR) com ``elm3d``.

        Args:
            elm3d: Objeto operado com ``self`` (:class:`_Elem3D`).
            operation: ``0`` união, ``1`` intersecção, ``2`` diferença, ``3`` XOR.

        Returns:
            Tupla ``(istat, elm3doper)``:

            * ``istat``: ``1`` falha objeto atual, ``2`` falha ``elm3d``,
              ``3`` falha CSG, ``4`` resultado vazio.
            * ``elm3doper``: :class:`_GenericSolid` resultante da operação.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxelm3d      = ctypes.c_void_p (elm3d.m_dxobj)
        paroperation    = ctypes.c_int (operation)
        gsolid          = _GenericSolid (self.m_model3d)
        pardxgsolid     = ctypes.c_void_p (gsolid.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxObj_CSGOperation (pardxobj, pardxiomem, pardxelm3d, \
                            paroperation, pardxgsolid, ctypes.byref (paristat))
        istat           = paristat.value
        return          istat, gsolid

    def Print (self) -> None:
        """Impressão de conteúdo do elemento, para teste."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        self.m_model3d.m_dxiodll.CDxObj_Print (pardxobj, pardxiomem)

#
#       Operações implementadas pelos objetos - abstractmethod
#
    @abstractmethod
    def Clone (self) -> "_Elem3D":
        """Duplica o objeto atual.

        Returns:
            Cópia independente do elemento.
        """
        pass

    @abstractmethod
    def Tesselate (self) -> "_GenericSolid":
        """Triangulariza o objeto atual.

        Returns:
            Objeto :class:`_GenericSolid` triangularizado.
        """
        pass

    @abstractmethod
    def ComputeNormals (self) -> None:
        """Torna as normais em versores (módulo unitário)."""
        pass

    @abstractmethod
    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada o elemento.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pass

    @abstractmethod
    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pass

    @abstractmethod
    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pass

    @abstractmethod
    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma o elemento usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pass

#-----------------------------------------------------------------------------
#       Prisma simples - base + altura
#       A base precisa ser convexa
#
class _Prism (_Elem3D):
    """Prisma simples definido por uma face base convexa e um vetor altura.

    Implementação:
        Wrapper sobre ``CDxPri`` em ``NDXIODLL.DLL``. O construtor faz auto-
        provisionamento dos componentes ausentes (face, vetor altura,
        atributos): aloca defaults, cria o ``CDxPri`` e libera os defaults
        se foram criados internamente. As operações geométricas e
        :meth:`Tesselate` delegam à família ``CDxPri_*``.

    Attributes:
        m_dxobj: Handle interno do objeto ``CDxPri``.
    """

    def __init__ (self, model3d: "Model3D", face: Optional["_Face"] = None,
                    vetalt: Optional["_Coords"] = None, atrib: Optional["_Attrib"] = None,
                    dxobj: Optional[int] = None) -> None:
        """Cria um prisma simples.

        Args:
            model3d: Modelo 3D proprietário.
            face: Face base convexa (:class:`_Face`).
            vetalt: Vetor altura (:class:`_Coords`).
            atrib: Atributos (:class:`_Attrib`).
            dxobj: Handle existente para envelopar (uso interno).
        """
        super().__init__(model3d, E3DTYPE_PRISMA)
        # Sem handle externo: aloca defaults faltantes, cria CDxPri e descarta defaults temporários
        if              (dxobj == None):
            # Cada flag icriou* sinaliza que aquele componente foi criado aqui e deve ser liberado depois
            icriouface      = 0
            if              (face == None):
                face        = _Face (model3d)
                icriouface  = 1
            icriouvetalt    = 0
            if              (vetalt == None):
                vetalt      = _Coords (model3d, 0., 0., 1.)
                icriouvetalt= 1
            icriouatrib     = 0
            if              (atrib == None):
                atrib       = _Attrib (model3d)
                icriouatrib = 1
            pardxxyzalt     = ctypes.c_void_p (vetalt.m_dxobj)
            pardxface       = ctypes.c_void_p (face.m_dxobj)
            pardxatrib      = ctypes.c_void_p (atrib.m_dxobj)
            pardxident      = ctypes.c_void_p (atrib.m_atribident.m_dxobj)
            iapagado        = 0
            pariapagado     = ctypes.c_int (iapagado)
            self.m_dxobj    = None
            pardxobj        = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxPri_Create (pardxface, pardxxyzalt, pardxatrib, \
                                pardxident, pariapagado, ctypes.byref (pardxobj))
            self.m_dxobj    = pardxobj.value
            self.m_ialoc   = 1
            # Libera apenas os defaults criados aqui (componentes do chamador continuam vivos)
            if              (icriouface != 0):
                del         face
            if              (icriouvetalt != 0):
                del         vetalt
            if              (icriouatrib != 0):
                del         atrib
        else:
            # Envelopa handle pré-existente: sincroniza AttribIdent e marca como não-dono
            self.m_dxobj   = dxobj
            self._AcertarAtribIdent ()
            self.m_ialoc   = 0

    def __del__(self) -> None:
        """Libera o handle ``CDxPri`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxPri_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0


    def __str__(self) -> str:
        """Retorna representação textual do prisma para depuração."""
        msg             = "\nClass _Prism"
        msg             +="\n   face %s" % str (self.face)
        msg             +="\n   heightVector %s" % str (self.heightVector)
        return          msg


    def _GravarSolido (self) -> int:
        """Insere o prisma no modelo.

        Returns:
            ``istat``: ``0`` se OK.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxPri_WriteToSolid (pardxobj, pardxiomem, ctypes.byref (paristat))
        istat           = paristat.value
        return          istat

    @property
    def face (self) -> "_Face":
        """Face base do prisma (:class:`_Face`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        dxobjface       = None
        pardxobjface    = ctypes.c_void_p (dxobjface)
        self.m_model3d.m_dxiodll.CDxPri_GetFace (pardxobj, ctypes.byref (pardxobjface))
        dxobjface       = pardxobjface.value
        face            = _Face (self.m_model3d, None, dxobjface)
        return          face

    @face.setter
    def face (self, face: "_Face") -> None:
        """Atribui Face base do prisma (:class:`_Face`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxface       = ctypes.c_void_p (face.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPri_SetFace (pardxobj, pardxface)

    @property
    def heightVector (self) -> "_Coords":
        """Vetor altura do prisma (:class:`_Coords`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        dxvetalt        = None
        pardxvetalt     = ctypes.c_void_p (dxvetalt)
        self.m_model3d.m_dxiodll.CDxPri_GetHeightVector (pardxobj, ctypes.byref (pardxvetalt))
        dxvetalt        = pardxvetalt.value
        vetalt          = _Coords (self.m_model3d, None, None, None, dxvetalt)
        return          vetalt

    @heightVector.setter
    def heightVector (self, vetalt: "_Coords") -> None:
        """Atribui Vetor altura do prisma (:class:`_Coords`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxvetalt     = ctypes.c_void_p (vetalt.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPri_SetHeightVector (pardxobj, pardxvetalt)


    def CopyFrom (self, elm3d: "_Prism") -> None:
        """Torna o objeto atual uma cópia do prisma fornecido.

        Args:
            elm3d: Prisma fonte.
        """
        super().CopyFrom (elm3d)
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxelm3d      = ctypes.c_void_p (elm3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPri_CopyFrom (pardxobj, pardxelm3d)

    def Clone (self) -> "_Prism":
        """Duplica o prisma atual.

        Returns:
            Cópia independente deste :class:`_Prism`.
        """
        prism           = _Prism (self.m_model3d)
        prism.CopyFrom  (self)
        return          prism

    def Tesselate (self) -> "_GenericSolid":
        """Triangulariza o prisma.

        Returns:
            :class:`_GenericSolid` triangularizado.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        inverterfuros   = 0
        parinverterfuros= ctypes.c_int (inverterfuros)
        gsolid          = _GenericSolid (self.m_model3d)
        pardxgsolid     = ctypes.c_void_p (gsolid.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPri_Tesselate (pardxobj, parinverterfuros, pardxgsolid)
        return          gsolid

    def ComputeNormals (self) -> None:
        """Torna as normais em versores."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPri_NormalizeNormals (pardxobj)

    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada o prisma.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CDxPri_Move (pardxobj, pardx, pardy, pardz)

    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parcz           = ctypes.c_double (cz)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CDxPri_Scale (pardxobj, parcx, parcy, parcz, \
                            parescx, parescy, parescz)

    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda o prisma no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CDxPri_RotateXY (pardxobj, parcx, parcy, parang)

    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma o prisma usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransf       = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPri_Transform (pardxobj, partransf)

#-----------------------------------------------------------------------------
#       Prisma complexo
#
class _ComplexPrism (_Elem3D):
    """Prisma complexo definido por N faces (base + furos) e vetor altura.

    A primeira face é a base do prisma complexo, orientada para fora; as
    demais, orientadas para dentro do sólido, representam furos.

    Implementação:
        Wrapper sobre ``CDxPriC`` em ``NDXIODLL.DLL``. Após o construtor
        criar o handle, faces são adicionadas via :meth:`EnterFace`
        (``CDxPriC_AddFace``); a primeira é a base, as demais são furos.
        :meth:`Tesselate` e operações geométricas delegam à família
        ``CDxPriC_*``.

    Attributes:
        m_dxobj: Handle interno do objeto ``CDxPriC``.
    """

    def __init__ (self, model3d: "Model3D", vetalt: Optional["_Coords"] = None,
                    atrib: Optional["_Attrib"] = None, dxobj: Optional[int] = None) -> None:
        """Cria um prisma complexo.

        Args:
            model3d: Modelo 3D proprietário.
            vetalt: Vetor altura (:class:`_Coords`).
            atrib: Atributos (:class:`_Attrib`).
            dxobj: Handle existente para envelopar (uso interno).
        """
        super().__init__(model3d, E3DTYPE_PRISMAC)
        # Sem handle externo: aloca vetor altura/atributos default se faltantes
        if              (dxobj == None):
            icriouvetalt    = 0
            if              (vetalt == None):
                vetalt      = _Coords (model3d, 0., 0., 1.)
                icriouvetalt= 1
            icriouatrib     = 0
            if              (atrib == None):
                atrib       = _Attrib (model3d)
                icriouatrib = 1
            pardxxyzalt     = ctypes.c_void_p (vetalt.m_dxobj)
            pardxatrib      = ctypes.c_void_p (atrib.m_dxobj)
            pardxident      = ctypes.c_void_p (atrib.m_atribident.m_dxobj)
            iapagado        = 0
            pariapagado     = ctypes.c_int (iapagado)
            self.m_dxobj    = None
            pardxobj        = ctypes.c_void_p (self.m_dxobj)
            # Cria o CDxPriC vazio; faces da base e furos são adicionadas depois via EnterFace
            self.m_model3d.m_dxiodll.CDxPriC_Create (pardxxyzalt, pardxatrib, \
                                pardxident, pariapagado, ctypes.byref (pardxobj))
            self.m_dxobj    = pardxobj.value
            self.m_ialoc   = 1
            # Libera apenas defaults criados aqui
            if              (icriouvetalt != 0):
                del         vetalt
            if              (icriouatrib != 0):
                del         atrib
        else:
            # Envelopa handle pré-existente: sincroniza AttribIdent
            self.m_dxobj    = dxobj
            self._AcertarAtribIdent ()
            self.m_ialoc   = 0


    def __del__(self) -> None:
        """Libera o handle ``CDxPriC`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxPriC_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

    def __str__(self) -> str:
        """Retorna representação textual do prisma complexo para depuração."""
        numfaces        = self.NumFaces ()
        msg             = "\nClass _ComplexPrism faces %d" % numfaces
        msg             +="\n   heightVector %s" % str (self.heightVector)
        for             indface in range (0, numfaces):
            msg         +="\n   face %03d %s" % (indface, self.GetFace (indface))
        return          msg

    def _GravarSolido (self) -> int:
        """Insere o prisma complexo no modelo.

        Returns:
            ``istat``: ``0`` se OK.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxPriC_WriteToSolid (pardxobj, pardxiomem, ctypes.byref (paristat))
        istat           = paristat.value
        return          istat

    @property
    def heightVector (self) -> "_Coords":
        """Vetor altura do prisma (:class:`_Coords`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        dxvetalt        = None
        pardxvetalt     = ctypes.c_void_p (dxvetalt)
        self.m_model3d.m_dxiodll.CDxPriC_GetHeightVector (pardxobj, ctypes.byref (pardxvetalt))
        dxvetalt        = pardxvetalt.value
        vetalt          = _Coords (self.m_model3d, None, None, None, dxvetalt)
        return          vetalt

    @heightVector.setter
    def heightVector (self, vetalt: "_Coords") -> None:
        """Atribui Vetor altura do prisma (:class:`_Coords`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxvetalt     = ctypes.c_void_p (vetalt.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPriC_SetHeightVector (pardxobj, pardxvetalt)

    def EnterFace (self, face: "_Face") -> None:
        """Adiciona uma face ao prisma complexo.

        A primeira face é a base orientada para fora; as demais, orientadas
        para dentro do sólido, representam furos.

        Args:
            face: Face (:class:`_Face`) a adicionar.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxface       = ctypes.c_void_p (face.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPriC_AddFace (pardxobj, pardxface)

    def NumFaces (self) -> int:
        """Retorna o número de faces do prisma complexo.

        Returns:
            Quantidade de faces.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        numfaces        = 0
        parnumfaces     = ctypes.c_int (numfaces)
        self.m_model3d.m_dxiodll.CDxPriC_GetNumFaces (pardxobj, ctypes.byref (parnumfaces))
        numfaces        = parnumfaces.value
        return          numfaces

    def GetFace (self, indface: int) -> "_Face":
        """Retorna uma face do prisma complexo pelo índice.

        Args:
            indface: Índice da face no intervalo ``0..NumFaces()-1``.

        Returns:
            Face (:class:`_Face`) de índice fornecido.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parindface      = ctypes.c_int (indface)
        dxobjface       = None
        pardxobjface    = ctypes.c_void_p (dxobjface)
        self.m_model3d.m_dxiodll.CDxPriC_GetFace (pardxobj, parindface, ctypes.byref (pardxobjface))
        dxobjface       = pardxobjface.value
        face            = _Face (self.m_model3d, None, dxobjface)
        return          face


    def CopyFrom (self, elm3d: "_ComplexPrism") -> None:
        """Torna o objeto atual uma cópia do prisma complexo fornecido.

        Args:
            elm3d: Prisma complexo fonte.
        """
        super().CopyFrom (elm3d)
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxelm3d      = ctypes.c_void_p (elm3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPriC_CopyFrom (pardxobj, pardxelm3d)


    def Clone (self) -> "_ComplexPrism":
        """Duplica o prisma complexo atual.

        Returns:
            Cópia independente deste :class:`_ComplexPrism`.
        """
        cprism          = _ComplexPrism (self.m_model3d)
        cprism.CopyFrom (self)
        return          cprism

    def Tesselate (self) -> "_GenericSolid":
        """Triangulariza o prisma complexo.

        Returns:
            :class:`_GenericSolid` triangularizado.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        inverterfuros   = 0
        parinverterfuros= ctypes.c_int (inverterfuros)
        gsolid          = _GenericSolid (self.m_model3d)
        pardxgsolid     = ctypes.c_void_p (gsolid.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPriC_Tesselate (pardxobj, parinverterfuros, pardxgsolid)
        return          gsolid

    def ComputeNormals (self) -> None:
        """Torna as normais em versores."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPriC_NormalizeNormals (pardxobj)

    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada o prisma complexo.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CDxPriC_Move (pardxobj, pardx, pardy, pardz)

    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parcz           = ctypes.c_double (cz)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CDxPriC_Scale (pardxobj, parcx, parcy, parcz, \
                            parescx, parescy, parescz)

    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda o prisma complexo no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CDxPriC_RotateXY (pardxobj, parcx, parcy, parang)

    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma o prisma complexo usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransf       = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxPriC_Transform (pardxobj, partransf)


#-----------------------------------------------------------------------------
#       Sólido genérico
#
class _GenericSolid (_Elem3D):
    """Sólido genérico descrito por todas as faces (sem restrição de convexidade).

    Implementação:
        Wrapper sobre ``CDxSol`` em ``NDXIODLL.DLL``. Faces são adicionadas
        via :meth:`EnterFace` (``CDxSol_AddFace``) e relidas via
        :meth:`NumFaces` / :meth:`GetFace`. As operações geométricas e
        :meth:`Tesselate` delegam à família ``CDxSol_*``.

    Attributes:
        m_dxobj: Handle interno do objeto ``CDxSol``.
    """

    def __init__ (self, model3d: "Model3D", atrib: Optional["_Attrib"] = None,
                    dxobj: Optional[int] = None) -> None:
        """Cria um sólido genérico.

        Args:
            model3d: Modelo 3D proprietário.
            atrib: Atributos (:class:`_Attrib`).
            dxobj: Handle existente para envelopar (uso interno).
        """
        super().__init__(model3d, E3DTYPE_SOLIDO)
        # Sem handle externo: cria CDxSol vazio (faces serão adicionadas via EnterFace)
        if              (dxobj == None):
            icriouatrib     = 0
            if              (atrib == None):
                atrib       = _Attrib (model3d)
                icriouatrib = 1
            pardxatrib      = ctypes.c_void_p (atrib.m_dxobj)
            pardxident      = ctypes.c_void_p (atrib.m_atribident.m_dxobj)
            iapagado        = 0
            pariapagado     = ctypes.c_int (iapagado)
            self.m_dxobj    = None
            self.m_ialoc   = 1
            pardxobj        = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxSol_Create (pardxatrib, \
                                pardxident, pariapagado, ctypes.byref (pardxobj))
            self.m_dxobj    = pardxobj.value
            # Libera atrib default criado aqui (atrib do chamador continua vivo)
            if              (icriouatrib != 0):
                del         atrib
        else:
            # Envelopa handle pré-existente: sincroniza AttribIdent
            self.m_dxobj    = dxobj
            self._AcertarAtribIdent ()
            self.m_ialoc   = 0


    def __del__(self) -> None:
        """Libera o handle ``CDxSol`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxSol_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

    def __str__(self) -> str:
        """Retorna representação textual do sólido para depuração."""
        numfaces        = self.NumFaces ()
        msg             = "\nClass _GenericSolid faces %d" % numfaces
        for             indface in range (0, numfaces):
            msg         +="\n   face %03d %s" % (indface, self.GetFace (indface))
        return          msg

    def _GravarSolido (self) -> int:
        """Insere o sólido genérico no modelo.

        Returns:
            ``istat``: ``0`` se OK.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxSol_WriteToSolid (pardxobj, pardxiomem, ctypes.byref (paristat))
        istat           = paristat.value
        return          istat

    def EnterFace (self, face: "_Face") -> None:
        """Adiciona uma face ao sólido genérico.

        Args:
            face: Face (:class:`_Face`) a adicionar.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxface       = ctypes.c_void_p (face.m_dxobj)
        self.m_model3d.m_dxiodll.CDxSol_AddFace (pardxobj, pardxface)

    def NumFaces (self) -> int:
        """Retorna o número de faces do sólido.

        Returns:
            Quantidade de faces.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        numfaces        = 0
        parnumfaces     = ctypes.c_int (numfaces)
        self.m_model3d.m_dxiodll.CDxSol_GetNumFaces (pardxobj, ctypes.byref (parnumfaces))
        numfaces        = parnumfaces.value
        return          numfaces

    def GetFace (self, indface: int) -> "_Face":
        """Retorna uma face do sólido genérico pelo índice.

        Args:
            indface: Índice da face no intervalo ``0..NumFaces()-1``.

        Returns:
            Face (:class:`_Face`) de índice fornecido.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parindface        = ctypes.c_int (indface)
        dxobjface       = None
        pardxobjface    = ctypes.c_void_p (dxobjface)
        self.m_model3d.m_dxiodll.CDxSol_GetFace (pardxobj, parindface, ctypes.byref (pardxobjface))
        dxobjface       = pardxobjface.value
        face            = _Face (self.m_model3d, None, dxobjface)
        return          face


    def CopyFrom (self, elm3d: "_GenericSolid") -> None:
        """Torna o objeto atual uma cópia do sólido fornecido.

        Args:
            elm3d: Sólido fonte.
        """
        super().CopyFrom (elm3d)
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxelm3d      = ctypes.c_void_p (elm3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxSol_CopyFrom (pardxobj, pardxelm3d)


    def Clone (self) -> "_GenericSolid":
        """Duplica o sólido atual.

        Returns:
            Cópia independente deste :class:`_GenericSolid`.
        """
        gsolid          = _GenericSolid (self.m_model3d)
        gsolid.CopyFrom (self)
        return          gsolid

    def Tesselate (self) -> "_GenericSolid":
        """Triangulariza o sólido.

        Returns:
            :class:`_GenericSolid` triangularizado.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        inverterfuros   = 0
        parinverterfuros= ctypes.c_int (inverterfuros)
        gsolid          = _GenericSolid (self.m_model3d)
        pardxgsolid     = ctypes.c_void_p (gsolid.m_dxobj)
        self.m_model3d.m_dxiodll.CDxSol_Tesselate (pardxobj, parinverterfuros, pardxgsolid)
        return          gsolid

    def ComputeNormals (self) -> None:
        """Torna as normais em versores."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CDxSol_NormalizeNormals (pardxobj)

    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada o sólido.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CDxSol_Move (pardxobj, pardx, pardy, pardz)

    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parcz           = ctypes.c_double (cz)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CDxSol_Scale (pardxobj, parcx, parcy, parcz, \
                            parescx, parescy, parescz)

    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda o sólido no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CDxSol_RotateXY (pardxobj, parcx, parcy, parang)

    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma o sólido usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransf       = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxSol_Transform (pardxobj, partransf)


#-----------------------------------------------------------------------------
#       Sólido de extrusão por linha arbitrária
#
class _ExtrusionSolid (_Elem3D):
    """Sólido de extrusão (prismas que seguem uma trilha).

    Usado também para descrever barras de aço com repetição e deslocamento.

    Note:
        Não funciona com arcos nas faces; é preciso discretizar primeiro.

    Implementação:
        Wrapper sobre ``CDxTrilha`` em ``NDXIODLL.DLL``. O construtor recebe
        face, polígono da trilha, raio de curvatura, número de repetições e
        vetor de deslocamento, com auto-provisionamento de defaults para
        componentes ausentes. Properties como ``bendingRadius`` e
        ``repetition`` delegam a ``CDxTrilha_*``; :meth:`Tesselate` requer
        face já discretizada.

    Attributes:
        m_dxobj: Handle interno do objeto ``CDxTrilha``.
    """

    def __init__ (self, model3d: "Model3D", face: Optional["_Face"] = None,
                    polig: Optional["_Polyg"] = None, raio: Optional[float] = None,
                    nrep: Optional[int] = None, delta: Optional["_Coords"] = None, \
                    atrib: Optional["_Attrib"] = None, dxobj: Optional[int] = None) -> None:
        """Cria um sólido de extrusão por linha arbitrária.

        Args:
            model3d: Modelo 3D proprietário.
            face: Face base (:class:`_Face`).
            polig: Linha da trilha (:class:`_Polyg`).
            raio: Raio de curvatura da trilha.
            nrep: Número de repetições do sólido a cada ``delta`` se ``> 1``.
            delta: Translação caso seja aplicada repetição (:class:`_Coords`).
            atrib: Atributos (:class:`_Attrib`).
            dxobj: Handle existente para envelopar (uso interno).
        """
        super().__init__(model3d, E3DTYPE_TRILHA)
        # Sem handle externo: provisiona componentes faltantes (face, polig, atrib, delta) com defaults
        if              (dxobj == None):
            icriouface      = 0
            if              (face == None):
                face        = _Face (model3d)
                icriouface  = 1
            icrioupolig     = 0
            if              (polig == None):
                polig       = _Polyg (model3d)
                icrioupolig = 1
            icriouatrib     = 0
            if              (atrib == None):
                atrib       = _Attrib (model3d)
                icriouatrib = 1
            if              (raio == None):
                raio        = 0.
            if              (nrep == None):
                nrep        = 0
            icrioudelta     = 0
            if              (delta == None):
                delta       = _Coords (self.m_model3d, 0., 0., 0.)
                icrioudelta = 1
            pardxface       = ctypes.c_void_p (face.m_dxobj)
            pardxpolig      = ctypes.c_void_p (polig.m_dxobj)
            pardxatrib      = ctypes.c_void_p (atrib.m_dxobj)
            pardxident      = ctypes.c_void_p (atrib.m_atribident.m_dxobj)
            iapagado        = 0
            pariapagado     = ctypes.c_int (iapagado)
            parraio         = ctypes.c_double (raio)
            parnrep         = ctypes.c_int (nrep)
            pardxdelta      = ctypes.c_void_p (delta.m_dxobj)
            self.m_dxobj    = None
            pardxobj        = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxTrilha_Create (pardxface, pardxpolig, pardxatrib, \
                                pardxident, pariapagado, parraio, parnrep, pardxdelta, \
                                ctypes.byref (pardxobj))
            self.m_dxobj    = pardxobj.value
            self.m_ialoc   = 1
            # Libera apenas defaults criados aqui; o resto é responsabilidade do chamador
            if              (icriouface != 0):
                del         face
            if              (icrioupolig != 0):
                del         polig
            if              (icriouatrib != 0):
                del         atrib
            if              (icrioudelta != 0):
                del         delta
        else:
            # Envelopa handle pré-existente: sincroniza AttribIdent
            self.m_dxobj    = dxobj
            self._AcertarAtribIdent ()
            self.m_ialoc   = 0

    def __del__(self) -> None:
        """Libera o handle ``CDxTrilha`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxTrilha_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

    def __str__(self) -> str:
        """Retorna representação textual do sólido de extrusão para depuração."""
        msg             = "\nClass _ExtrusionSolid"
        msg             +="\n   face  %s" % str (self.face)
        msg             +="\n   polyg %s" % str (self.polyg)
        return          msg

    def _GravarSolido (self) -> int:
        """Insere o sólido de extrusão no modelo.

        Returns:
            ``istat``: ``0`` se OK.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxTrilha_WriteToSolid (pardxobj, pardxiomem, ctypes.byref (paristat))
        istat           = paristat.value
        return          istat

    @property
    def face (self) -> "_Face":
        """Face base da extrusão (:class:`_Face`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        dxobjface       = None
        pardxobjface    = ctypes.c_void_p (dxobjface)
        self.m_model3d.m_dxiodll.CDxTrilha_GetFace (pardxobj, ctypes.byref (pardxobjface))
        dxobjface       = pardxobjface.value
        face            = _Face (self.m_model3d, None, dxobjface)
        return          face

    @face.setter
    def face (self, face: "_Face") -> None:
        """Atribui Face base da extrusão (:class:`_Face`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxface       = ctypes.c_void_p (face.m_dxobj)
        self.m_model3d.m_dxiodll.CDxTrilha_SetFace (pardxobj, pardxface)

    @property
    def polyg (self) -> "_Polyg":
        """Polígono da trilha (:class:`_Polyg`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        dxobjpolig      = None
        pardxobjpolig   = ctypes.c_void_p (dxobjpolig)
        self.m_model3d.m_dxiodll.CDxTrilha_GetPolygon (pardxobj, ctypes.byref (pardxobjpolig))
        dxobjpolig      = pardxobjpolig.value
        polig           = _Polyg (self.m_model3d, dxobjpolig)
        return          polig

    @polyg.setter
    def polyg (self, polig: "_Polyg") -> None:
        """Atribui Polígono da trilha (:class:`_Polyg`)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxpolig       = ctypes.c_void_p (polig.m_dxobj)
        self.m_model3d.m_dxiodll.CDxTrilha_SetPolygon (pardxobj, pardxpolig)

    @property
    def bendingRadius (self) -> float:
        """Raio de curvatura da trilha em ``cm``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        raio            = 0.
        parraio         = ctypes.c_double (raio)
        self.m_model3d.m_dxiodll.CDxTrilha_GetCurvatureRadius (pardxobj, ctypes.byref (parraio))
        raio            = parraio.value
        return          raio

    @bendingRadius.setter
    def bendingRadius (self, raio: float) -> None:
        """Atribui Raio de curvatura da trilha em ``cm``."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parraio         = ctypes.c_double (raio)
        self.m_model3d.m_dxiodll.CDxTrilha_SetCurvatureRadius (pardxobj, parraio)

    @property
    def repetition (self) -> int:
        """Número de repetições da trilha (ex: definição de estribos)."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        nrep            = 0
        parnrep         = ctypes.c_int (nrep)
        self.m_model3d.m_dxiodll.CDxTrilha_GetRepetitions (pardxobj, ctypes.byref (parnrep))
        nrep            = parnrep.value
        return          nrep

    @repetition.setter
    def repetition (self, nrep: int) -> None:
        """Atribui Número de repetições da trilha (ex: definição de estribos).

        ATENÇÃO: o valor é enviado como ``c_double`` (8 bytes), enquanto o getter
        e o construtor usam ``c_int``. A DLL recebe tipo/ABI incorretos, o que
        produz contagem de repetições errada ou corrompe a chamada nativa.
        Defina as repetições no construtor em vez de atribuir esta propriedade.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parnrep         = ctypes.c_double (nrep)
        self.m_model3d.m_dxiodll.CDxTrilha_SetRepetitions (pardxobj, parnrep)

    @property
    def displacement (self) -> "_Coords":
        """Vetor de deslocamento (:class:`_Coords`) da trilha para cada repetição."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxdelta      = ctypes.c_void_p (None)
        self.m_model3d.m_dxiodll.CDxTrilha_GetDelta (pardxobj, ctypes.byref (pardxdelta))
        dxdelta         = pardxdelta.value
        delta           = _Coords (self.m_model3d, None, None, None, dxdelta)
        return          delta

    @displacement.setter
    def displacement (self, delta: "_Coords") -> None:
        """Atribui Vetor de deslocamento (:class:`_Coords`) da trilha para cada repetição."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxdelta      = ctypes.c_void_p (delta.m_dxobj)
        self.m_model3d.m_dxiodll.CDxTrilha_SetDelta (pardxobj, pardxdelta)

    def CopyFrom (self, elm3d: "_ExtrusionSolid") -> None:
        """Torna o objeto atual uma cópia do sólido de extrusão fornecido.

        Args:
            elm3d: Sólido de extrusão fonte.
        """
        super().CopyFrom (elm3d)
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxelm3d      = ctypes.c_void_p (elm3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxTrilha_CopyFrom (pardxobj, pardxelm3d)

    def Clone (self) -> "_ExtrusionSolid":
        """Duplica o sólido de extrusão atual.

        Returns:
            Cópia independente deste :class:`_ExtrusionSolid`.
        """
        esolid          = _ExtrusionSolid (self.m_model3d)
        esolid.CopyFrom (self)
        return          esolid

    def Tesselate (self) -> "_GenericSolid":
        """Triangulariza o sólido de extrusão.

        Returns:
            :class:`_GenericSolid` triangularizado.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        inverterfuros   = 0
        parinverterfuros= ctypes.c_int (inverterfuros)
        gsolid          = _GenericSolid (self.m_model3d)
        pardxgsolid     = ctypes.c_void_p (gsolid.m_dxobj)
        self.m_model3d.m_dxiodll.CDxTrilha_Tesselate (pardxobj, parinverterfuros, pardxgsolid)
        return          gsolid

    def ComputeNormals (self) -> None:
        """Torna as normais em versores."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CDxTrilha_NormalizeNormals (pardxobj)

    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada o sólido de extrusão.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CDxTrilha_Move (pardxobj, pardx, pardy, pardz)

    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parcz           = ctypes.c_double (cz)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CDxTrilha_Scale (pardxobj, parcx, parcy, parcz, \
                            parescx, parescy, parescz)

    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda o sólido de extrusão no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CDxTrilha_RotateXY (pardxobj, parcx, parcy, parang)

    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma o sólido de extrusão usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransf       = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxTrilha_Transform (pardxobj, partransf)

#-----------------------------------------------------------------------------
#       Inserção de um bloco
#
class _BlockInsert (_Elem3D):
    """Inserção de um bloco no modelo 3D.

    Blocos são identificados por um nome e devem ser definidos previamente.

    Implementação:
        Wrapper sobre ``CDxBlocoIns`` em ``NDXIODLL.DLL``. Representa uma
        instância de bloco (referência ao bloco previamente definido em
        :class:`Blocks`) com uma transformação 3D e atributos próprios. As
        operações geométricas e :meth:`Tesselate` delegam à família
        ``CDxBlocoIns_*``.

    Attributes:
        m_dxobj: Handle interno do objeto ``CDxBlocoIns``.
    """

    def __init__ (self, model3d: "Model3D", nome: Optional[str] = None,
                    transf3d: Optional["_Transf3D"] = None,
                    atrib: Optional["_Attrib"] = None, dxobj: Optional[int] = None) -> None:
        """Cria uma inserção de bloco.

        ATENÇÃO: quando ``transf3d`` é omitido, o corpo instancia ``Transf3d``,
        um nome que não existe no módulo — a classe é ``_Transf3D``, exposta como
        ``Base.Transf3D``. Criar uma inserção sem transformação explícita, o
        padrão documentado, levanta ``NameError``. Passe sempre uma
        transformação obtida de ``base.Transf3D(...)``.

        Args:
            model3d: Modelo 3D proprietário.
            nome: Nome do bloco.
            transf3d: Transformação da inserção (:class:`_Transf3D`). Obrigatório
                na prática — ver ATENÇÃO.
            atrib: Atributos (:class:`_Attrib`).
            dxobj: Handle existente para envelopar (uso interno).
        """
        super().__init__(model3d, E3DTYPE_BLOCOINS)
        # Sem handle externo: provisiona transformação/atributos default e cria CDxBlocoIns
        if              (dxobj == None):
            if          (nome == None):
                nome    = ""
            icriout3d   = 0
            if          (transf3d == None):
                transf3d= Transf3d (self.m_model3d)
                icriout3d= 1
            parnome      = ctypes.c_char_p (nome.encode(TQS.TQSUtil.CHARSET))
            partransf    = ctypes.c_void_p (transf3d.m_dxobj)
            iapagado     = 0
            pariapagado  = ctypes.c_int (iapagado)
            iselins      = 0
            pariselins   = ctypes.c_int (iselins)
            icriouatrib  = 0
            if           (atrib == None):
                atrib    = _Attrib (model3d)
                icriouatrib = 1
            pardxatrib   = ctypes.c_void_p (atrib.m_dxobj)
            pardxident   = ctypes.c_void_p (atrib.m_atribident.m_dxobj)
            self.m_dxobj = None
            pardxobj     = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxBlocoIns_Create (parnome, partransf, pardxatrib, pardxident, \
                                pariapagado, pariselins, ctypes.byref (pardxobj))
            self.m_dxobj = pardxobj.value
            self.m_ialoc = 1
            # Libera apenas defaults criados aqui
            if           (icriout3d != 0):
                del      transf3d
            if           (icriouatrib != 0):
                del      atrib
        else:
            # Envelopa handle pré-existente: sincroniza AttribIdent
            self.m_dxobj = dxobj
            self._AcertarAtribIdent ()
            self.m_ialoc = 0


    def __del__(self) -> None:
        """Libera o handle ``CDxBlocoIns`` se este objeto possui ownership."""
        if              (self.m_dxobj != None and self.m_ialoc != 0):
            pardxobj    = ctypes.c_void_p (self.m_dxobj)
            self.m_model3d.m_dxiodll.CDxBlocoIns_Delete (pardxobj)
            self.m_dxobj = None
            self.m_ialoc = 0

    def _GravarSolido (self) -> int:
        """Insere a inserção de bloco no modelo.

        Returns:
            ``istat``: ``0`` se OK.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxiomem      = ctypes.c_void_p (self.m_model3d.m_dxiomem)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_model3d.m_dxiodll.CDxBlocoIns_WriteToSolid (pardxobj, pardxiomem, \
                            ctypes.byref (paristat))
        istat           = paristat.value
        return          istat

    def CopyFrom (self, elm3d: "_BlockInsert") -> None:
        """Torna o objeto atual uma cópia da inserção de bloco fornecida.

        Args:
            elm3d: Inserção de bloco fonte.
        """
        super().CopyFrom (elm3d)
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardxelm3d      = ctypes.c_void_p (elm3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxBlocoIns_CopyFrom (pardxobj, pardxelm3d)

    def Clone (self) -> "_BlockInsert":
        """Duplica a inserção de bloco atual.

        Returns:
            Cópia independente deste :class:`_BlockInsert`.
        """
        blockinsert     = _BlockInsert (self.m_model3d)
        blockinsert.CopyFrom (self)
        return          blockinsert

    def Tesselate (self) -> "_GenericSolid":
        """Triangulariza a inserção de bloco.

        Returns:
            :class:`_GenericSolid` triangularizado.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        inverterfuros   = 0
        parinverterfuros= ctypes.c_int (inverterfuros)
        gsolid          = _GenericSolid (self.m_model3d)
        pardxgsolid     = ctypes.c_void_p (gsolid.m_dxobj)
        self.m_model3d.m_dxiodll.CDxBlocoIns_Tesselate (pardxobj, parinverterfuros, pardxgsolid)
        return          gsolid

    def ComputeNormals (self) -> None:
        """Torna as normais em versores."""
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        self.m_model3d.m_dxiodll.CDxBlocoIns_NormalizeNormals (pardxobj)

    def Move (self, dx: float, dy: float, dz: float) -> None:
        """Translada a inserção de bloco.

        Args:
            dx: Deslocamento X.
            dy: Deslocamento Y.
            dz: Deslocamento Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        pardx           = ctypes.c_double (dx)
        pardy           = ctypes.c_double (dy)
        pardz           = ctypes.c_double (dz)
        self.m_model3d.m_dxiodll.CDxBlocoIns_Move (pardxobj, pardx, pardy, pardz)

    def Scale (self, cx: float, cy: float, cz: float, escx: float, escy: float, escz: float) -> None:
        """Aplica escala em torno de um centro.

        Args:
            cx: Centro de escala X.
            cy: Centro de escala Y.
            cz: Centro de escala Z.
            escx: Fator de escala X.
            escy: Fator de escala Y.
            escz: Fator de escala Z.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parcz           = ctypes.c_double (cz)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        parescz         = ctypes.c_double (escz)
        self.m_model3d.m_dxiodll.CDxBlocoIns_Scale (pardxobj, parcx, parcy, parcz, \
                            parescx, parescy, parescz)

    def RotateXY (self, cx: float, cy: float, ang: float) -> None:
        """Roda a inserção de bloco no plano XY.

        Args:
            cx: Centro de rotação X.
            cy: Centro de rotação Y.
            ang: Ângulo de rotação em graus.
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        parcx           = ctypes.c_double (cx)
        parcy           = ctypes.c_double (cy)
        parang          = ctypes.c_double (ang)
        self.m_model3d.m_dxiodll.CDxBlocoIns_RotateXY (pardxobj, parcx, parcy, parang)

    def Transform (self, transf3d: "_Transf3D") -> None:
        """Transforma a inserção de bloco usando a matriz fornecida.

        Args:
            transf3d: Matriz de transformação (:class:`_Transf3D`).
        """
        pardxobj        = ctypes.c_void_p (self.m_dxobj)
        partransf       = ctypes.c_void_p (transf3d.m_dxobj)
        self.m_model3d.m_dxiodll.CDxBlocoIns_Transform (pardxobj, partransf)
