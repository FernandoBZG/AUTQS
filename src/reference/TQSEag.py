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
#    TQSEag.py         Acesso à API do EAG - Editor de Aplicações Gráficas
#                      EAGW.EXE - Módulo básico
#                      Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING, List, Optional, Tuple

from TQS import TQSUtil, TQSJan, TQSModel, TQSEagSM, TQSEag3d

if TYPE_CHECKING:
    from TQS.TQSDwg import Dwg
    from TQS.TQSJan import Window

#-----------------------------------------------------------------------------
#    Constantes usadas em TQSEag.py
#    Rubberband
#
EAG_RUBNAO:          int = -1       # Sem rubberband
EAG_RUBLINEAR:       int =  0       # Rubberband linear
EAG_RUBRETANG:       int =  1       # Rubberband retangular
EAG_RUBPANDIN:       int =  2       # Rubberband p/pan dinamico
#
#    Tipo de Rubberband
#
EAG_RUBRET_NAOPREEN: int = 0        # Não preenche rubber retangular
EAG_RUBRET_JANW:     int = 1        # Preenche como janela W
EAG_RUBRET_JANC:     int = 2        # Preenche como janela C
EAG_RUBRET_JANUSR:   int = 3        # W (direita) ou C (esquerda)
#
#    Constantes de selecao de elementos
#
EAG_INORM:           int = 0        # Seleção normal
EAG_IJANEL:          int = 1        # Seleção por janela entre 2 pts
EAG_ICURS:           int = 2        # Seleção na posicao do cursor
EAG_IMULTP:          int = 4        # Seleção múltipla
EAG_IALTJAN:         int = 8        # Primeiro cursor, depois janela
EAG_IJANELC:         int = 16       # Janela <C>
EAG_IJANELD:         int = 32       # Janela <D>

#-----------------------------------------------------------------------------
class Eag ():
    """Interface Python para o ``EAGW.EXE`` (Editor de Aplicações Gráficas).

    Encapsula handles das DLLs do editor e expõe sub-objetos
    :class:`Entry`, :class:`Exec`, :class:`Msg`, :class:`State` e
    :class:`Locate`.

    Implementação:
        Os métodos das sub-classes são wrappers finos sobre funções C++ exportadas
        pelas DLLs ``EAGW.EXE``, ``EAGVISTA.DLL`` e ``MDWG.DLL``. O padrão recorrente
        é: (1) embrulhar ponteiros e ints/doubles em ``ctypes.c_*``; (2) chamar a
        função C++ através do handle de DLL apropriado; (3) ler de volta as saídas
        via ``.value`` em parâmetros passados por referência. Comentários inline são
        adicionados apenas onde a sequência foge desse padrão.

    Attributes:
        eagSingleton: Instância singleton compartilhada entre chamadas.
        m_eagwexe: Handle de ``EAGW.EXE``.
        m_eagvista: Handle de ``EAGVISTA.DLL``.
        m_mdwg: Handle de ``MDWG.DLL``.
        entry: Sub-objeto de pré-entrada de dados.
        exec: Sub-objeto de execução de comandos.
        msg: Sub-objeto de mensagens.
        state: Sub-objeto de variáveis de estado.
        locate: Sub-objeto de localização e leitura de coordenadas.
    """

    eagSingleton: Optional["Eag"] = None                 # Objeto Singleton

    def __init__ (self) -> None:
        """Carrega as DLLs do editor e cria os sub-objetos."""
        self.m_eagwexe = TQSUtil.LoadDll ("EAGW.EXE")
        self.m_eagvista= TQSUtil.LoadDll ("EAGVISTA.DLL")
        self.m_mdwg    = TQSUtil.LoadDll ("MDWG.DLL")
        self.entry     = Entry  (self)
        self.exec      = Exec   (self)
        self.msg       = Msg    (self)
        self.state     = State  (self)
        self.locate    = Locate (self)
#
#    Objeto Singleton de acesso ao editor
#
    @classmethod
    def GetEag (self) -> "Eag":
        """Retorna a instância única :class:`Eag` do editor (Singleton).

        Use este método em vez de chamar ``Eag()`` diretamente para evitar
        alocar recursos redundantes.

        Returns:
            Instância singleton de :class:`Eag`.
        """
        if             self.eagSingleton is None:
            self.eagSingleton = Eag ()
        return         self.eagSingleton
#
#    Retorna pedmv dado tqsjan
#
    def _GetPedmv (self, tqsjan: "Window") -> int:
        """Retorna o handle ``pedmv`` (PEDIT/MV) interno do desenho da janela."""
        return     tqsjan.m_dwg.m_pedmv;
#
#       Se o editor for o Modelador, retorna um objeto TQSModel
#
    def GetTQSModel (self, tqsjan: "Window") -> Tuple[Optional[TQSEagSM.SM],
                                                       Optional[TQSModel.Model],
                                                       Optional[TQSModel.Floor]]:
        """Recupera os objetos do Modelador Estrutural se o editor for o Modelador.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Tupla ``(sm, model, floor)``:

            * ``sm``: :class:`TQSEagSM.SM` com acesso ao Modelador, ou ``None``.
            * ``model``: :class:`TQSModel.Model` (modelo estrutural), ou ``None``.
            * ``floor``: :class:`TQSModel.Floor` (planta atual), ou ``None``.

            Todos os elementos são ``None`` se o editor corrente não for o
            Modelador Estrutural.
        """
        # Lê três ponteiros C++ do EAGW: fábrica de planta, edifício e lista de edições
        fabrica         = None
        parfabrica      = ctypes.c_void_p (fabrica)
        edif            = None
        paredif         = ctypes.c_void_p (edif)
        lisedi          = None
        parlisedi       = ctypes.c_void_p (lisedi)
        self.m_eagwexe.eag_LerDadosModelador (ctypes.byref (parfabrica), \
                            ctypes.byref (paredif), ctypes.byref (parlisedi))
        fabrica         = parfabrica.value
        edif            = paredif.value
        lisedi          = parlisedi.value
        sm              = None
        model           = None
        floor           = None
        # Se ``fabrica`` veio nulo, o editor corrente não é o Modelador: devolve a tripla None
        if              (fabrica != None):
            # Constrói os wrappers Python (Model/Floor/SM) por cima dos ponteiros C++ lidos
            model       = TQSModel.Model (tqsjan)
            floor       = TQSModel.Floor (model, None, fabrica)
            sm          = TQSEagSM.SM.GetSM (self, model, floor, edif, lisedi)
        return          sm, model, floor
#
#       Se o editor for o N3BUILDER, retorna um objeto TQSEag3d
#
    def GetTQSEag3d (self) -> Optional[TQSEag3d.Eag3d]:
        """Recupera o editor 3D se o editor corrente for o N3DBUILDER.

        Returns:
            :class:`TQSEag3d.Eag3d` com acesso ao EAG3DBUILDER de objetos 3D,
            ou ``None`` se o editor corrente não for o N3DBUILDER.
        """
        eag3d           = None
        # Tenta obter o ponteiro C++ do N3DBUILDER carregado no editor corrente
        self.m_n3dbuilder= None
        parn3dbuilder   = ctypes.c_void_p (self.m_n3dbuilder)
        self.m_eagwexe.eag_LerDadosN3DBuilder (ctypes.byref (parn3dbuilder))
        self.m_n3dbuilder= parn3dbuilder.value
        # Só constrói o wrapper Eag3d se o editor de fato for o N3DBUILDER
        if              (self.m_n3dbuilder != None):
            eag3d       = TQSEag3d.Eag3d.GetEag3d (self)
        return          eag3d
#
#    Comparador de desenhos
#
    def Compare (self, dwg1: "Dwg", dwg2: "Dwg") -> int:
        """Compara dois desenhos elemento a elemento.

        Args:
            dwg1: Primeiro desenho a comparar.
            dwg2: Segundo desenho a comparar.

        Returns:
            Número de diferenças encontradas.
        """
        # Extrai os ponteiros internos (PEDIT/MV) de cada desenho para passar ao comparador C++
        parpedmv1       = ctypes.c_void_p (dwg1.m_pedmv)
        parpedmv2       = ctypes.c_void_p (dwg2.m_pedmv)
        numdif          = 0
        parnumdif       = ctypes.c_int (numdif)
        # eag_comparardifer faz a comparação elemento a elemento e devolve a contagem de diferenças
        self.m_eagwexe.eag_comparardifer (parpedmv1, parpedmv2, ctypes.byref (parnumdif))
        numdif          = parnumdif.value
        return          numdif


#-----------------------------------------------------------------------------
#    Pré-entrada de dados do editor.
#
class Entry ():
    """Pré-entrada de dados (teclas, coordenadas, strings) para o editor EAG.

    Os comandos do EAG acionados após estas chamadas consomem as entradas
    enfileiradas, permitindo automatizar interações que normalmente seriam
    feitas pelo usuário.

    Implementação:
        Cada método empacota os parâmetros (tipo, código, x, y, string) em
        ``ctypes.c_*`` e chama ``eag_FilaEntrada`` da ``EAGW.EXE``, que enfileira
        o evento na fila de entrada do editor. Os métodos públicos são apenas
        açúcar para o método interno :meth:`_Entrar`, fixando o ``itipo`` e o
        ``icod`` adequados a cada tipo de evento (tecla, coordenada, string).

    Attributes:
        ENTR_TECLA: Tipo de entrada — tecla.
        ENTR_COORD: Tipo de entrada — coordenadas.
        ENTR_STRIN: Tipo de entrada — string.
    """
    ENTR_TECLA: int = 0
    ENTR_COORD: int = 1
    ENTR_STRIN: int = 2

    def __init__ (self, eag: "Eag") -> None:
        """Inicializa o sub-objeto de pré-entrada.

        Args:
            eag: Instância de :class:`Eag` proprietária.
        """
        self.m_eag     = eag

    def _Entrar (self, itipo: int, icod: int, x: float, y: float, str: str) -> None:
        """Enfileira uma entrada genérica na fila de entrada do EAG."""
        paritipo       = ctypes.c_int (itipo)
        paricod        = ctypes.c_int (icod)
        parx           = ctypes.c_double (x)
        pary           = ctypes.c_double (y)
        parstr         = ctypes.c_char_p (str.encode(TQSUtil.CHARSET))
        self.m_eag.m_eagwexe.eag_FilaEntrada (paritipo, paricod, parx, pary, parstr)


    def KeyEscape (self) -> None:
        """Enfileira a tecla ``<Escape>`` na fila de entrada."""
        itipo          = Entry.ENTR_TECLA
        icod           = -1
        x              = 0.
        y              = 0.
        str            = ""
        self._Entrar   (itipo, icod, x, y, str)

    def KeyEnter (self) -> None:
        """Enfileira a tecla ``<Enter>`` na fila de entrada."""
        itipo          = Entry.ENTR_TECLA
        icod           = 0
        x              = 0.
        y              = 0.
        str            = ""
        self._Entrar   (itipo, icod, x, y, str)

    def KeyFunction (self, ishift: int, icontrol: int, ialt: int, ifn: int) -> None:
        """Enfileira uma tecla de função ``Fn`` com modificadores opcionais.

        Args:
            ishift: ``!= 0`` se ``<Shift>`` deve estar acionado.
            icontrol: ``!= 0`` se ``<Control>`` deve estar acionado.
            ialt: ``!= 0`` se ``<Alt>`` deve estar acionado.
            ifn: Número da tecla de função (1..N).
        """
        itipo          = Entry.ENTR_TECLA
        # Codifica Fn + modificadores num único int conforme a convenção do EAG:
        # base = ifn + 20 (F1..F10 ocupam 21..30; F11+ pula 40 posições)
        icod           = ifn + 20
        if             ifn >= 11:
            icod       = icod + 40
        # Cada modificador adiciona um offset fixo: Shift +10, Ctrl +20, Alt +30
        if             ishift != 0:
            icod       = icod + 10
        if             icontrol  != 0:
            icod       = icod + 20
        if             ialt   != 0:
            icod       = icod + 30
        x              = 0.
        y              = 0.
        str            = ""
        self._Entrar   (itipo, icod, x, y, str)

    def String (self, str: str) -> None:
        """Enfileira um string que será interpretado conforme o comando ativo.

        Args:
            str: Texto a enfileirar.
        """
        itipo          = Entry.ENTR_STRIN
        icod           = 0
        x              = 0.
        y              = 0.
        self._Entrar   (itipo, icod, x, y, str)

    def Point (self, x: float, y: float) -> None:
        """Enfileira um par de coordenadas como entrada gráfica.

        Args:
            x: Coordenada X.
            y: Coordenada Y.
        """
        itipo          = Entry.ENTR_COORD
        icod           = 1
        str            = ""
        self._Entrar   (itipo, icod, x, y, str)

#-----------------------------------------------------------------------------
#    Execução de comandos
#
class Exec ():
    """Execução e habilitação de comandos do editor.

    Implementação:
        Os comandos do editor são identificados por strings ``ID_xxx`` declaradas
        no arquivo ``.MEN`` do menu. Os métodos desta classe são wrappers finos
        sobre as funções ``menu_*`` e ``eag_*`` da ``EAGW.EXE``: codificam o
        identificador como ``ctypes.c_char_p`` (com encoding ``TQSUtil.CHARSET``)
        e delegam o disparo, habilitação ou marcação ao motor C++ do editor.
    """

    def __init__ (self, eag: "Eag") -> None:
        """Inicializa o sub-objeto de execução.

        Args:
            eag: Instância de :class:`Eag` proprietária.
        """
        self.m_eag     = eag

    def Command (self, ident: str) -> None:
        """Executa um comando do editor identificado pelo ``ID_xxx`` do ``.MEN``.

        Args:
            ident: Identificador ``ID_xxx`` declarado no arquivo de menu.
        """
        parident       = ctypes.c_char_p (ident.encode(TQSUtil.CHARSET))
        self.m_eag.m_eagwexe.menu_acionamenu (parident)
        self.m_eag.m_eagwexe.eag_LimparEntrada ()

    def EnableCommand (self, ident: str, ienable: int) -> None:
        """Habilita ou desabilita um comando do editor.

        Args:
            ident: Identificador ``ID_xxx`` declarado no arquivo de menu.
            ienable: ``0`` desabilita, ``1`` habilita.
        """
        parident       = ctypes.c_char_p (ident.encode(TQSUtil.CHARSET))
        parienable     = ctypes.c_int (ienable)
        self.m_eag.m_eagwexe.menu_enable (parident, parienable)

    def CheckCommand (self, ident: str, icheck: int) -> None:
        """Marca ou desmarca um comando como "Check" quando aplicável.

        Args:
            ident: Identificador ``ID_xxx`` declarado no arquivo de menu.
            icheck: ``0`` não marca, ``1`` marca.
        """
        parident       = ctypes.c_char_p (ident.encode(TQSUtil.CHARSET))
        paricheck      = ctypes.c_int (icheck)
        self.m_eag.m_eagwexe.menu_check (parident, paricheck)

    def EditW (self, name: str) -> int:
        """Abre um arquivo ASCII no editor ``EDITW.EXE``.

        Args:
            name: Nome do arquivo, com ou sem caminho.

        Returns:
            ``0`` se editou com sucesso, ``!= 0`` em caso de erro.
        """
        parname        = ctypes.c_char_p (name.encode(TQSUtil.CHARSET))
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_eag.m_eagwexe.eag_editw (parname, ctypes.byref (paristat))
        istat          = paristat.value
        return         istat


#-----------------------------------------------------------------------------
#    Mensagens na janela do editor
#
class Msg ():
    """Mensagens na janela do editor (área de mensagens, status, título).

    Implementação:
        Cada método concatena os argumentos em uma string única (estilo ``print``),
        codifica em ``TQSUtil.CHARSET`` e repassa para a função correspondente da
        ``EAGW.EXE`` (``eag_msgs``, ``eag_statusmsg``, ``eag_titjan``…). Não há
        formatação especial: o destino — área de mensagens, barra de status ou
        título da janela — é definido apenas pela função C++ chamada.
    """

    def __init__ (self, eag: "Eag") -> None:
        """Inicializa o sub-objeto de mensagens.

        Args:
            eag: Instância de :class:`Eag` proprietária.
        """
        self.m_eag     = eag

    def Print (self, *args: object) -> None:
        """Emite mensagens (estilo ``print`` do Python) na janela do editor.

        Args:
            *args: Objetos convertidos via ``str()`` e concatenados.
        """
        txt                 = ""
        for                 msg in args:
            txt             += str (msg)
        par                 = ctypes.c_char_p (txt.encode(TQSUtil.CHARSET))
        self.m_eag.m_eagwexe.eag_msgs (par)

    def ClearMessageWindow (self) -> None:
        """Limpa a janela de mensagens do editor."""
        self.m_eag.m_eagwexe.eag_msglimpa ()

    def PrintStatus (self, *args: object) -> None:
        """Emite mensagens (estilo ``print``) na área de status do editor.

        Args:
            *args: Objetos convertidos via ``str()`` e concatenados.
        """
        txt                 = ""
        for                 msg in args:
            txt             += str (msg)
        par                 = ctypes.c_char_p (txt.encode(TQSUtil.CHARSET))
        self.m_eag.m_eagwexe.eag_statusmsg (par)

    def WindowTitle (self, tqsjan: "Window", title: str) -> None:
        """Define o título da janela atual de desenho.

        Args:
            tqsjan: Janela do EAG.
            title: Novo título.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        partitle       = ctypes.c_char_p (title.encode(TQSUtil.CHARSET))
        self.m_eag.m_eagwexe.eag_titjan (parpvistav, partitle)

#-----------------------------------------------------------------------------
#    Localização de elementos gráficos e leitura de coordenadas
#
class Locate ():
    """Localização de elementos gráficos e leitura de coordenadas/valores.

    Implementação:
        Os métodos bloqueiam o fluxo Python até o usuário concluir a interação
        no editor (clique, digitação, seleção). Para entrada de pontos/valores,
        o padrão é montar buffers ``ctypes`` para cada saída e chamar a função
        ``eag_*`` correspondente da ``EAGW.EXE``, que devolve o código de saída
        (Enter/Esc/botão/tecla) junto com os dados lidos. Para seleção de elementos
        DWG, ``Select`` produz uma lista interna no MDWG que é depois iterada por
        :meth:`BeginSelection` / :meth:`NextSelection` (padrão "rewind + next" via
        ``g_wstrew`` / ``g_wstler``).
    """

    def __init__ (self, eag: "Eag") -> None:
        """Inicializa o sub-objeto de localização.

        Args:
            eag: Instância de :class:`Eag` proprietária.
        """
        self.m_eag     = eag

    def GetPoint (self, tqsjan: "Window", msg: str) -> Tuple[int, float, float]:
        """Lê um ponto via mouse/teclado.

        Args:
            tqsjan: Janela do EAG.
            msg: Mensagem para o usuário.

        Returns:
            Tupla ``(icod, x, y)``:

            * ``icod``: ``0`` Enter / ``-1`` Esc / ``1..3`` Botões 1-3 do mouse /
              ``> 20`` Teclas de função / ``< -1`` código ASCII negativo
              (ex.: ``"A" = -65``).
            * ``x``, ``y``: coordenadas do ponto.
        """
        # Mostra a mensagem na área de prompts antes de bloquear esperando o ponto
        self.m_eag.msg.Print (msg)
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        icod           = 0
        x              = 0.
        y              = 0.
        paricod        = ctypes.c_int (icod)
        parx           = ctypes.c_double (x)
        pary           = ctypes.c_double (y)
        # eag_getpt bloqueia até o usuário responder; devolve código + coordenadas
        self.m_eag.m_eagwexe.eag_getpt (parpvistav, ctypes.byref (paricod),
                        ctypes.byref (parx), ctypes.byref (pary))
        icod           = paricod.value
        x              = parx.value
        y              = pary.value
        return         icod, x, y

    def GetSecondPoint (self, tqsjan: "Window", x1: float, y1: float,
                        irubber: int, itprubret: int, msg: str) -> Tuple[int, float, float]:
        """Lê um segundo ponto com rubberband ancorado em ``(x1, y1)``.

        Args:
            tqsjan: Janela do EAG.
            x1: X do ponto âncora do rubberband.
            y1: Y do ponto âncora do rubberband.
            irubber: Tipo de rubberband:

                * :data:`EAG_RUBNAO` — sem rubberband.
                * :data:`EAG_RUBLINEAR` — linear.
                * :data:`EAG_RUBRETANG` — retangular.
                * :data:`EAG_RUBPANDIN` — para pan dinâmico.

            itprubret: Preenchimento do rubberband retangular:

                * :data:`EAG_RUBRET_NAOPREEN` — sem preenchimento.
                * :data:`EAG_RUBRET_JANW` — preenche como janela W.
                * :data:`EAG_RUBRET_JANC` — preenche como janela C.
                * :data:`EAG_RUBRET_JANUSR` — W (direita) ou C (esquerda).

            msg: Mensagem para o usuário.

        Returns:
            Tupla ``(icod, x, y)`` análoga a :meth:`GetPoint`.
        """
        # Empacota o ponto âncora e o tipo de rubberband; o EAG cuida da renderização interativa
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parirubbet     = ctypes.c_int (irubber)
        paritprubret   = ctypes.c_int (itprubret)
        parmsg         = ctypes.c_char_p (msg.encode(TQSUtil.CHARSET))
        icod           = 0
        x2             = 0.
        y2             = 0.
        paricod        = ctypes.c_int (icod)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        # eag_get1px desenha o rubberband ancorado em (x1,y1) e bloqueia até o segundo ponto
        self.m_eag.m_eagwexe.eag_get1px (parpvistav, ctypes.byref (paricod),
                       parx1, pary1, ctypes.byref (parx2), ctypes.byref (pary2),
                       parirubbet, paritprubret, parmsg)
        icod           = paricod.value
        x2             = parx2.value
        y2             = pary2.value
        return         icod, x2, y2

    def SetNextZ (self, z: float) -> None:
        """Define a coordenada Z para a próxima entrada gráfica.

        A coordenada é zerada após o próximo :meth:`GetPoint`.

        Args:
            z: Valor de Z em unidades de desenho.
        """
        parz           = ctypes.c_double (z)
        self.m_eag.m_eagwexe.eag_get1p_defz (parz)

    def GetLastZ (self) -> Tuple[int, float]:
        """Retorna a cota Z da última entrada gráfica, se disponível.

        Returns:
            Tupla ``(idisp, z)``:

            * ``idisp`` (``int``): ``1`` se a cota Z está disponível, ``0`` senão.
            * ``z`` (``float``): valor de Z (significativo apenas se ``idisp == 1``).
        """
        idisp          = 0
        paridisp       = ctypes.c_int (idisp)
        z              = 0.
        parz           = ctypes.c_double (z)
        self.m_eag.m_eagwexe.eag_zinput (ctypes.byref (paridisp), ctypes.byref (parz))
        idisp          = paridisp.value
        z              = parz.value
        return         idisp, z

    def GetLabel (self, tqsjan: "Window", msg: str) -> Tuple[str, int]:
        """Lê texto do usuário com mensagem.

        Args:
            tqsjan: Janela do EAG.
            msg: Mensagem para o usuário.

        Returns:
            Tupla ``(str, istat)``:

            * ``str``: Texto lido.
            * ``istat``: ``0`` Ok / ``1`` Enter / ``2`` Esc.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parmsg         = ctypes.c_char_p (msg.encode(TQSUtil.CHARSET))
        parstr         = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_eag.m_eagwexe.eag_peglab (parpvistav, parmsg, parstr, ctypes.byref (paristat))
        str            = parstr.value.decode(TQSUtil.CHARSET)
        istat          = paristat.value
        return         str, istat

    def GetValue (self, tqsjan: "Window", msg: str, valmin: float,
                  valmax: float, valdef: float) -> Tuple[float, int]:
        """Lê um número em ponto flutuante com validação de intervalo.

        Args:
            tqsjan: Janela do EAG.
            msg: Mensagem para o usuário.
            valmin: Valor mínimo aceito.
            valmax: Valor máximo aceito.
            valdef: Valor default sugerido.

        Returns:
            Tupla ``(val, istat)``:

            * ``val``: Valor lido.
            * ``istat``: ``0`` Ok, ``1`` não leu.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parmsg         = ctypes.c_char_p (msg.encode(TQSUtil.CHARSET))
        parvalmin      = ctypes.c_double (valmin)
        parvalmax      = ctypes.c_double (valmax)
        parvaldef      = ctypes.c_double (valdef)
        dadunid        = 0
        pardadunid     = ctypes.c_void_p (dadunid)
        val            = 0.
        parval         = ctypes.c_double (val)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_eag.m_eagwexe.eag_grream (parpvistav, parmsg, ctypes.byref (parval),
                         parvalmin, parvalmax, parvaldef, pardadunid,
                         ctypes.byref (paristat))
        val            = parval.value
        istat          = paristat.value
        return         val, istat

    def GetAngle (self, tqsjan: "Window", msg: str, angdef: float) -> Tuple[float, int]:
        """Lê um ângulo em graus, aceitando ``<R>`` (3 pontos) e ``<L>`` (linha).

        Args:
            tqsjan: Janela do EAG.
            msg: Mensagem para o usuário.
            angdef: Valor default em graus.

        Returns:
            Tupla ``(ang, istat)``:

            * ``ang``: Ângulo lido em graus.
            * ``istat``: ``0`` Ok, ``1`` não leu.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parmsg         = ctypes.c_char_p (msg.encode(TQSUtil.CHARSET))
        parangdef      = ctypes.c_double (angdef)
        ang            = 0.
        istat          = 0
        parang         = ctypes.c_double (ang)
        paristat       = ctypes.c_int (istat)
        self.m_eag.m_eagwexe.eag_girang (parpvistav, parmsg, ctypes.byref (parang),
                       parangdef, ctypes.byref (paristat))
        ang            = parang.value
        istat          = paristat.value
        return         ang, istat

    def GetEntryType (self) -> int:
        """Retorna o tipo da última entrada do usuário.

        Returns:
            ``0`` para entrada alfanumérica, ``1`` para gráfica.
        """
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_eag.m_eagwexe.eag_gregra (ctypes.byref (paristat))
        istat          = paristat.value
        return         istat

    def GetYesNo (self, tqsjan: "Window", msg: str, r1: str, r2: str) -> int:
        """Mostra ``msg`` e lê resposta tipo Sim/Não.

        Args:
            tqsjan: Janela do EAG.
            msg: Mensagem para o usuário.
            r1: Texto da primeira resposta.
            r2: Texto da segunda resposta.

        Returns:
            ``0`` se selecionou ``r1``, ``1`` se ``r2``, ``2`` se ``<Escape>``.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parmsg         = ctypes.c_char_p (msg.encode(TQSUtil.CHARSET))
        parr1          = ctypes.c_char_p (r1.encode(TQSUtil.CHARSET))
        parr2          = ctypes.c_char_p (r2.encode(TQSUtil.CHARSET))
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_eag.m_eagwexe.eag_pegsix (parpvistav, parmsg, parr1, parr2,
                       ctypes.byref (paristat))
        istat          = paristat.value
        return         istat

    def GetCursor (self, tqsjan: "Window") -> Tuple[float, float]:
        """Retorna a posição atual do cursor no mundo real.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Tupla ``(x, y)`` em unidades de desenho.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        x              = 0.
        y              = 0.
        parx           = ctypes.c_double (x)
        pary           = ctypes.c_double (y)
        self.m_eag.m_eagwexe.eag_lercursor (parpvistav, ctypes.byref (parx),
                        ctypes.byref (pary))
        x              = parx.value
        y              = pary.value
        return         x, y

    def SetRubberIdle (self, tqsjan: "Window", irubberidle: int,
                       xrubbidle: float, yrubbidle: float) -> None:
        """Liga linha elástica idle a partir de um ponto âncora.

        A linha permanece visível até o próximo comando ou ``<Escape>``.

        Args:
            tqsjan: Janela do EAG.
            irubberidle: ``1`` liga, ``0`` desliga.
            xrubbidle: X do ponto de referência.
            yrubbidle: Y do ponto de referência.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parirubberidle = ctypes.c_int (irubberidle)
        parxrubbidle   = ctypes.c_double (xrubbidle)
        paryrubbidle   = ctypes.c_double (yrubbidle)
        self.m_eag.m_eagwexe.eag_rubberidle (parpvistav, parirubberidle,
                       parxrubbidle, paryrubbidle)

    def GetPolyline (self, tqsjan: "Window") -> List[List[float]]:
        """Lê uma poligonal interativamente.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Matriz de pontos ``[[x1, y1], [x2, y2], ...]``. Lista vazia
            se a poligonal tiver menos de 3 pontos.
        """
        # Bloqueia até o usuário concluir a poligonal; o EAG acumula os vértices internamente
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        self.m_eag.m_eagwexe.eag_getplnAcum (parpvistav)
        # Lê quantos pontos foram acumulados antes de iterar
        npt            = 0
        parnpt         = ctypes.c_int (npt)
        self.m_eag.m_eagwexe.eag_getplnAcumNpt (ctypes.byref (parnpt))
        npt            = parnpt.value
        xy             = []
        # Poligonais com menos de 3 pontos são consideradas inválidas: devolve lista vazia
        if             npt < 3:
            return     xy
        # Lê cada vértice por índice e empilha em ``xy`` no formato [[x,y], ...]
        for            ipt in range (0, npt):
            paript     = ctypes.c_int (ipt)
            x          = 0.
            parx       = ctypes.c_double (x)
            y          = 0.
            pary       = ctypes.c_double (y)
            self.m_eag.m_eagwexe.eag_getplnAcumLerPt (paript, ctypes.byref (parx), ctypes.byref (pary))
            xy.append  ([parx.value, pary.value])

        return         xy

    def Select (self, tqsjan: "Window", msg: str,
                itploc: int) -> Tuple[int, float, float, int, int]:
        """Seleciona um elemento gráfico DWG conforme o tipo de seleção.

        Para iterar pelos demais elementos da seleção use
        :meth:`BeginSelection` e :meth:`NextSelection`.

        Args:
            tqsjan: Janela do EAG.
            msg: Mensagem para o usuário.
            itploc: Tipo de seleção (combinável com ``|``):

                * :data:`EAG_INORM` — Normal.
                * :data:`EAG_IJANEL` — Por janela entre 2 pontos.
                * :data:`EAG_ICURS` — Coordenada do cursor.
                * :data:`EAG_IMULTP` — Múltipla.
                * :data:`EAG_IALTJAN` — Tenta ponto, depois janela.

        Returns:
            Tupla ``(addr, x, y, np, istat)``:

            * ``addr`` (``int``): handle do primeiro elemento DWG selecionado.
            * ``x``, ``y`` (``float``): coordenadas de seleção.
            * ``np`` (``int``): índice do ponto se poligonal.
            * ``istat`` (``int``): ``0`` Ok, ``!= 0`` se não selecionou.
        """
        # Mostra a mensagem de prompt antes da operação interativa
        self.m_eag.msg.Print (msg)
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parmsg         = ctypes.c_char_p (msg.encode(TQSUtil.CHARSET))
        paritploc      = ctypes.c_int (itploc)
        # Saídas: handle do elemento (void*), coordenadas, índice de ponto e status
        iadr           = 0
        pariadr        = ctypes.c_void_p (iadr)
        x              = 0.
        y              = 0.
        np             = 0
        istat          = 0
        parx           = ctypes.c_double (x)
        pary           = ctypes.c_double (y)
        parnp          = ctypes.c_int (np)
        paristat       = ctypes.c_int (istat)
        # eag_locelm bloqueia até a seleção; em modo múltiplo a lista é guardada no MDWG
        # para iteração posterior por BeginSelection / NextSelection
        self.m_eag.m_eagwexe.eag_locelm (parpvistav, ctypes.byref (pariadr),
                       ctypes.byref (parx), ctypes.byref (pary),
                       ctypes.byref (parnp), parmsg, paritploc, ctypes.byref (paristat))
        iadr          = pariadr.value
        x              = parx.value
        y              = pary.value
        np             = parnp.value
        istat          = paristat.value
        return         iadr, x, y, np, istat


    def BeginSelection (self, tqsjan: "Window") -> int:
        """Prepara para iterar pelos elementos selecionados em :meth:`Select`.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            ``0`` se há elementos para iterar, ``1`` se a seleção está vazia.
        """
        # Acessa a lista de seleção do desenho via PEDIT/MV (ponteiro interno do MDWG)
        pedmv          = self.m_eag._GetPedmv (tqsjan)
        parpedmv       = ctypes.c_void_p (pedmv)
        # g_wstnum devolve quantos elementos estão na lista de seleção corrente
        nwst           = 0
        parnwst        = ctypes.c_int (nwst)
        self.m_eag.m_mdwg.g_wstnum (parpedmv, ctypes.byref (parnwst))
        nwst           = parnwst.value
        if             nwst == 0:
            return     1
        # g_wstrew posiciona o cursor de iteração no início da lista (rewind)
        self.m_eag.m_mdwg.g_wstrew (parpedmv)
        return         0

    def NextSelection (self, tqsjan: "Window") -> Optional[int]:
        """Retorna o handle do próximo elemento selecionado, ou ``None``.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Handle do próximo elemento DWG, ou ``None`` ao fim da iteração.
        """

        addr           = 0
        pedmv          = self.m_eag._GetPedmv (tqsjan)
        parpedmv       = ctypes.c_void_p (pedmv)
        paradr         = ctypes.c_void_p (addr)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        # g_wstler avança o cursor de iteração e devolve o handle do próximo elemento;
        # istat != 0 sinaliza fim da lista
        self.m_eag.m_mdwg.g_wstler (parpedmv, ctypes.byref (paradr), ctypes.byref (paristat))
        addr           = paradr.value
        istat          = paristat.value
        if             istat != 0:
            return     None
        return         addr

    def DragSelection (self, tqsjan: "Window", xref: float, yref: float) -> None:
        """Acende os elementos selecionados e os arrasta junto com o cursor.

        Args:
            tqsjan: Janela do EAG.
            xref: X do ponto de inserção inicial da lista.
            yref: Y do ponto de inserção inicial da lista.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parxref        = ctypes.c_double (xref)
        paryref        = ctypes.c_double (yref)
        self.m_eag.m_eagwexe.eag_dragws (parpvistav, parxref, paryref)

    def DragOff (self, tqsjan: "Window") -> None:
        """Desliga o realce dos elementos ligado em :meth:`DragSelection`.

        Args:
            tqsjan: Janela do EAG.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        self.m_eag.m_eagwexe.eag_desligressaltowst (parpvistav)


#-----------------------------------------------------------------------------
#    Controle de variáveis de estado do editor
#
class State ():
    """Acesso às variáveis de estado do editor (modo ortogonal, grade, níveis…).

    Implementação:
        A classe expõe pares getter/setter (``GetXxx`` / ``SetXxx``) para cada
        variável de estado do editor. Cada par é um wrapper fino sobre uma função
        ``eag_*ler`` (leitura) ou ``eag_*grv`` (gravação) da ``EAGW.EXE`` /
        ``EAGVISTA.DLL`` / ``MDWG.DLL``. Para variáveis compostas (grade, distâncias
        de offset/fillet/chanfragem, inserção de bloco) a leitura/gravação é
        atômica — todas as componentes vão e voltam numa única chamada C++.
    """

    def __init__ (self, eag: "Eag") -> None:
        """Inicializa o sub-objeto de estado.

        Args:
            eag: Instância de :class:`Eag` proprietária.
        """
        self.m_eag     = eag

    def GetOrtho (self, tqsjan: "Window") -> Tuple[int, float]:
        """Lê o estado do modo ortogonal.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Tupla ``(iortho, angle)``:

            * ``iortho`` (``int``): ``0`` desligado, ``1`` modo ortogonal.
            * ``angle`` (``float``): Ângulo em graus do modo ortogonal.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        iorto          = 0
        pariorto       = ctypes.c_int (iorto)
        angle          = 0
        parangle       = ctypes.c_double (angle)
        self.m_eag.m_eagwexe.eag_ortoler (parpvistav, ctypes.byref (pariorto),
                         ctypes.byref (parangle))
        iorto          = pariorto.value
        angle          = parangle.value
        return         iorto, angle

    def SetOrtho (self, tqsjan: "Window", iortho: int, angle: float) -> None:
        """Define o estado do modo ortogonal.

        Args:
            tqsjan: Janela do EAG.
            iortho: ``0`` desligado, ``1`` modo ortogonal.
            angle: Ângulo em graus do modo ortogonal — é o giro/rotação do sistema local ortogonal.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        pariorto       = ctypes.c_int (iortho)
        parangle       = ctypes.c_double (angle)
        self.m_eag.m_eagwexe.eag_ortogrv (parpvistav, pariorto, parangle)

    def GetLevelLock (self, tqsjan: "Window") -> int:
        """Lê o flag global de nível travado.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            ``0`` desligado, ``1`` há ao menos um nível travado.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        ilevellock     = 0
        parilevellock  = ctypes.c_int (ilevellock)
        self.m_eag.m_eagwexe.eag_levllk (parpvistav, ctypes.byref (parilevellock))
        ilevellock     = parilevellock.value
        return         ilevellock

    def SetLevelLock (self, tqsjan: "Window", ilevellock: int) -> None:
        """Define o flag global de nível travado.

        Args:
            tqsjan: Janela do EAG.
            ilevellock: ``0`` desligado, ``1`` ativa travas.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parilevellock  = ctypes.c_int (ilevellock)
        self.m_eag.m_eagwexe.eag_grvllk (parpvistav, parilevellock)

    def ClearAllLevelsLock (self, tqsjan: "Window") -> None:
        """Limpa as travas individuais de todos os níveis.

        Args:
            tqsjan: Janela do EAG.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        self.m_eag.m_eagwexe.eag_limpatrava (parpvistav)

    def GetOneLevelLock (self, tqsjan: "Window", ilevel: int) -> int:
        """Lê a trava de um nível específico.

        Args:
            tqsjan: Janela do EAG.
            ilevel: Índice do nível considerado.

        Returns:
            ``1`` se o nível está travado, ``0`` caso contrário.
        """
        pedmv          = self.m_eag._GetPedmv (tqsjan)
        parpedmv       = ctypes.c_void_p (pedmv)
        parilevel      = ctypes.c_int (ilevel)
        ilock          = 0
        parilock       = ctypes.c_int (ilock)
        self.m_eag.m_mdwg.g_lertravanivel (parpedmv, parilevel, ctypes.byref (parilock))
        ilock          = parilock.value
        return         ilock

    def SetOneLevelLock (self, tqsjan: "Window", ilevel: int, ilock: int) -> None:
        """Define a trava de um nível específico.

        Args:
            tqsjan: Janela do EAG.
            ilevel: Índice do nível considerado.
            ilock: ``1`` trava, ``0`` destrava.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parilevel      = ctypes.c_int (ilevel)
        parilock       = ctypes.c_int (ilock)
        self.m_eag.m_eagwexe.eag_definetrava (parpvistav, parilevel, parilock)

    def GetActiveLevel (self, tqsjan: "Window") -> int:
        """Retorna o nível atual (em que novos elementos serão criados).

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Índice do nível atual.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        iactivelevel   = 0
        pariactivelevel= ctypes.c_int (iactivelevel)
        self.m_eag.m_eagwexe.eag_iatnivler (parpvistav, ctypes.byref (pariactivelevel))
        iactivelevel   = pariactivelevel.value
        return         iactivelevel

    def SetActiveLevel (self, tqsjan: "Window", iactivelevel: int) -> None:
        """Define o nível atual.

        Args:
            tqsjan: Janela do EAG.
            iactivelevel: Índice do nível dos elementos a serem criados.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        pariactivelevel= ctypes.c_int (iactivelevel)
        self.m_eag.m_eagwexe.eag_iatnivgrv (parpvistav, pariactivelevel)

    def GetFastCurve (self, tqsjan: "Window") -> int:
        """Lê o flag de modo "curva rápida".

        Args:
            tqsjan: Janela do EAG.

        Returns:
            ``0`` modo normal, ``1`` curva rápida (curvas mostradas como linhas).
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        ifastcurve     = 0
        parifastcurve  = ctypes.c_int (ifastcurve)
        self.m_eag.m_eagvista.vis_lericurvar (parpvistav, ctypes.byref (parifastcurve))
        ifastcurve    = parifastcurve.value
        return         ifastcurve

    def SetFastCurve (self, tqsjan: "Window", ifastcurve: int) -> None:
        """Define o flag de modo "curva rápida".

        Args:
            tqsjan: Janela do EAG.
            ifastcurve: ``0`` modo normal, ``1`` curva rápida.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parifastcurve  = ctypes.c_int (ifastcurve)
        self.m_eag.m_eagvista.vis_grvicurvar (parpvistav, parifastcurve)
        ifastcurve    = parifastcurve.value

    def GetGrid (self, tqsjan: "Window") -> Tuple[int, float, float, float, float, float, int, int]:
        """Lê os parâmetros da grade do desenho.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Tupla ``(igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber)``:

            * ``igrade`` (``int``): ``0`` Não / ``1`` Grade ligada.
            * ``grdorx`` (``float``): X origem da grade em cm.
            * ``grdory`` (``float``): Y origem da grade em cm.
            * ``grdesx`` (``float``): X espaçamento da grade em cm.
            * ``grdesy`` (``float``): Y espaçamento da grade em cm.
            * ``grdang`` (``float``): Ângulo da grade em graus.
            * ``iespacponto`` (``int``): Espaçamentos por ponto da grade.
            * ``igraderubber`` (``int``): ``1`` se grade ativa em rubberband.
        """
        pedmv          = self.m_eag._GetPedmv (tqsjan)
        parpedmv     = ctypes.c_void_p (pedmv)
        # Pré-aloca buffers ctypes para todos os parâmetros da grade (flag, origem,
        # espaçamento, ângulo, espaçamentos por ponto e flag de rubberband):
        # uma única chamada C++ preenche o conjunto inteiro
        igrade        = 0
        parigrade    = ctypes.c_int (igrade)
        grdorx        = 0.
        pargrdorx    = ctypes.c_double (grdorx)
        grdory        = 0.
        pargrdory    = ctypes.c_double (grdory)
        grdesx        = 0.
        pargrdesx    = ctypes.c_double (grdesx)
        grdesy        = 0.
        pargrdesy    = ctypes.c_double (grdesy)
        grdang        = 0.
        pargrdang    = ctypes.c_double (grdang)
        iespacponto    = 0
        pariespacponto    = ctypes.c_int (iespacponto)
        igraderubber    = 0
        parigraderubber    = ctypes.c_int (igraderubber)
        self.m_eag.m_mdwg.g_exlerigrade (parpedmv, ctypes.byref (parigrade),
            ctypes.byref (pargrdorx), ctypes.byref (pargrdory),
            ctypes.byref (pargrdesx), ctypes.byref (pargrdesy),
            ctypes.byref (pargrdang), ctypes.byref (pariespacponto),
            ctypes.byref (parigraderubber))
        # Desempacota todos os valores lidos via .value
        igrade        = parigrade.value
        grdorx        = pargrdorx.value
        grdory        = pargrdory.value
        grdesx        = pargrdesx.value
        grdesy        = pargrdesy.value
        grdang        = pargrdang.value
        iespacponto    = pariespacponto.value
        igraderubber    = parigraderubber.value
        return        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber

    def SetGrid (self, tqsjan: "Window", igrade: int, grdorx: float, grdory: float,
                 grdesx: float, grdesy: float, grdang: float,
                 iespacponto: int, igraderubber: int) -> None:
        """Define os parâmetros da grade do desenho.

        Args:
            tqsjan: Janela do EAG.
            igrade: ``0`` Não / ``1`` Grade ligada.
            grdorx: X origem da grade em cm.
            grdory: Y origem da grade em cm.
            grdesx: X espaçamento da grade em cm.
            grdesy: Y espaçamento da grade em cm.
            grdang: Ângulo da grade em graus.
            iespacponto: Espaçamentos por ponto da grade.
            igraderubber: ``1`` se grade ativa em rubberband.
        """
        pedmv          = self.m_eag._GetPedmv (tqsjan)
        parpedmv     = ctypes.c_void_p (pedmv)
        # Empacota o conjunto inteiro de parâmetros da grade num único bloco de
        # ctypes para gravar tudo de uma vez via g_exgrvigrade
        parigrade    = ctypes.c_int (igrade)
        pargrdorx    = ctypes.c_double (grdorx)
        pargrdory    = ctypes.c_double (grdory)
        pargrdesx    = ctypes.c_double (grdesx)
        pargrdesy    = ctypes.c_double (grdesy)
        pargrdang    = ctypes.c_double (grdang)
        pariespacponto    = ctypes.c_int (iespacponto)
        parigraderubber    = ctypes.c_int (igraderubber)
        self.m_eag.m_mdwg.g_exgrvigrade (parpedmv, parigrade,
            pargrdorx, pargrdory, pargrdesx, pargrdesy, pargrdang, pariespacponto,
            parigraderubber)

    def InvertCapture (self, tqsjan: "Window") -> None:
        """Inverte o estado da captura de coordenadas (ligada↔desligada).

        Args:
            tqsjan: Janela do EAG.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        self.m_eag.m_eagwexe.eag_capinv (parpvistav)

    def GetFastText (self, tqsjan: "Window") -> int:
        """Lê o flag de modo de texto rápido.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            ``1`` se modo de texto rápido, ``0`` caso contrário.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        ifast          = 0
        parifast       = ctypes.c_int (ifast)
        self.m_eag.m_eagvista.vis_leritextor (parpvistav, ctypes.byref (parifast))
        ifast          = parifast.value
        return         ifast

    def SetFastText  (self, tqsjan: "Window", ifast: int) -> None:
        """Define o modo de texto rápido.

        Args:
            tqsjan: Janela do EAG.
            ifast: ``1`` modo de texto rápido, ``0`` caso contrário.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parifast       = ctypes.c_int (ifast)
        self.m_eag.m_eagvista.vis_grvitextor (parpvistav, parifast)

    def GetBlockInsertion (self, tqsjan: "Window") -> Tuple[float, float, float]:
        """Lê os parâmetros default de inserção de bloco.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Tupla ``(xscale, yscale, angle)``:

            * ``xscale`` (``float``): Escala em X.
            * ``yscale`` (``float``): Escala em Y.
            * ``angle`` (``float``): Ângulo de inserção em graus.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        xscale         = 0.
        yscale         = 0.
        angle          = 0.
        parxscale      = ctypes.c_double (xscale)
        paryscale      = ctypes.c_double (yscale)
        parangle       = ctypes.c_double (angle)
        self.m_eag.m_eagwexe.eag_iatbloler (parpvistav, ctypes.byref (parxscale),
                        ctypes.byref (paryscale), ctypes.byref (parangle))
        xscale         = parxscale.value
        yscale         = paryscale.value
        angle          = parangle.value
        return         xscale, yscale, angle

    def SetBlockInsertion (self, tqsjan: "Window", xscale: float,
                           yscale: float, angle: float) -> None:
        """Define os parâmetros default de inserção de bloco.

        Args:
            tqsjan: Janela do EAG.
            xscale: Escala em X.
            yscale: Escala em Y.
            angle: Ângulo de inserção em graus.
        """
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        parxscale      = ctypes.c_double (xscale)
        paryscale      = ctypes.c_double (yscale)
        parangle       = ctypes.c_double (angle)
        self.m_eag.m_eagwexe.eag_iatblogrv (parpvistav, parxscale, paryscale, parangle)

    def _PegarDistArr (self, tqsjan: "Window") -> Tuple[float, float, float, float]:
        """Lê (interno) as 4 distâncias de offset/fillet/chanfragem do editor."""
        # As 4 distâncias compartilham um único registro no EAG; getters/setters
        # de Parallel, Fillet e Chanfragem usam este método para ler todas e
        # depois sobrescrever apenas a componente de interesse via _DefDistArr
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        atoffs         = 0.
        paratoffs      = ctypes.c_double (atoffs)
        atrfil         = 0.
        paratrfil      = ctypes.c_double (atrfil)
        atcrd1         = 0.
        paratcrd1      = ctypes.c_double (atcrd1)
        atcrd2         = 0.
        paratcrd2      = ctypes.c_double (atcrd2)
        # Lê em um só bloco: distância de paralela (offs), raio de fillet (rfil)
        # e distâncias 1/2 de chanfragem (crd1/crd2)
        self.m_eag.m_eagwexe.eag_iatoffler (parpvistav, ctypes.byref (paratoffs),
                       ctypes.byref (paratrfil), ctypes.byref (paratcrd1),
                       ctypes.byref (paratcrd2))
        atoffs         = paratoffs.value
        atrfil         = paratrfil.value
        atcrd1         = paratcrd1.value
        atcrd2         = paratcrd2.value
        return        atoffs, atrfil, atcrd1, atcrd2

    def _DefDistArr (self, tqsjan: "Window", atoffs: float, atrfil: float,
                     atcrd1: float, atcrd2: float) -> None:
        """Grava (interno) as 4 distâncias de offset/fillet/chanfragem do editor."""
        parpvistav     = ctypes.c_void_p (tqsjan.m_pvistav)
        paratoffs      = ctypes.c_double (atoffs)
        paratrfil      = ctypes.c_double (atrfil)
        paratcrd1      = ctypes.c_double (atcrd1)
        paratcrd2      = ctypes.c_double (atcrd2)
        self.m_eag.m_eagwexe.eag_iatoffgrv (parpvistav, paratoffs, paratrfil,
                        paratcrd1, paratcrd2)

    def GetParallelDist (self, tqsjan: "Window") -> float:
        """Retorna a distância padrão do comando "Paralela a elemento".

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Distância em cm.
        """
        atoffs, atrfil, atcrd1, atcrd2 = self._PegarDistArr (tqsjan)
        return         atoffs

    def SetParallelDist (self, tqsjan: "Window", distance: float) -> None:
        """Define a distância padrão do comando "Paralela a elemento".

        Args:
            tqsjan: Janela do EAG.
            distance: Nova distância em cm.
        """
        atoffs, atrfil, atcrd1, atcrd2 = self._PegarDistArr (tqsjan)
        self._DefDistArr (tqsjan, distance, atrfil, atcrd1, atcrd2)

    def GetFilletRadius (self, tqsjan: "Window") -> float:
        """Retorna o raio padrão de arredondamento de arcos (fillet).

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Raio em cm.
        """
        atoffs, atrfil, atcrd1, atcrd2 = self._PegarDistArr (tqsjan)
        return         atrfil

    def SetFilletRadius (self, tqsjan: "Window", radius: float) -> None:
        """Define o raio padrão de arredondamento de arcos (fillet).

        Args:
            tqsjan: Janela do EAG.
            radius: Novo raio em cm.
        """
        atoffs, atrfil, atcrd1, atcrd2 = self._PegarDistArr (tqsjan)
        self._DefDistArr (tqsjan, atoffs, radius, atcrd1, atcrd2)

    def GetFilletlDist (self, tqsjan: "Window") -> Tuple[float, float]:
        """Retorna as distâncias padrão de chanfragem.

        Args:
            tqsjan: Janela do EAG.

        Returns:
            Tupla ``(dist1, dist2)`` em cm.
        """
        atoffs, atrfil, atcrd1, atcrd2 = self._PegarDistArr (tqsjan)
        return         atcrd1, atcrd2

    def SetFilletlDist (self, tqsjan: "Window", dist1: float, dist2: float) -> None:
        """Define as distâncias padrão de chanfragem.

        Args:
            tqsjan: Janela do EAG.
            dist1: Distância 1 em cm.
            dist2: Distância 2 em cm.
        """
        atoffs, atrfil, atcrd1, atcrd2 = self._PegarDistArr (tqsjan)
        self._DefDistArr (tqsjan, atoffs, atrfil, dist1, dist2)
