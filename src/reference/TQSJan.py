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
#    TQSJan.PY         Módulo para mostrar desenhos TQS em uma janela Windows
#                      Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import math
import ctypes
from typing import List, Optional, Tuple

import TQS.TQSUtil
import TQS.TQSDwg

#-----------------------------------------------------------------------------
#    Constantes de VISTA.H
#
VIS_DESEN:               int = 0   # Display e desenho
VIS_DESENNAO:            int = 1   # Display sem desenho

VIS_DLEXISTE:            int = 0   # criar e usar display list
VIS_DLINATIVA:           int = 1   # nao existe displau list

VIS_DLINS:               int = 0   # Insere na display list
VIS_DLDEL:               int = 1   # Deleta da display list
VIS_DLIGNORE:            int = 2   # Nao insere na display list

VIS_DISPORI:             int = 0   # Desenhar na cor original
VIS_DISPFOR:             int = 1   # Desenhar na cor fornecida
VIS_DISPAPAG:            int = 2   # Desenhar apagando
VIS_DISPXOR:             int = 3   # Desenhar em XOR
VIS_DISPNAO:             int = 4   # Nao desenhar

VIS_SISLOC:              int = 0   # Sistema local normal
VIS_SISGIR:              int = 1   # Sistema local a 90^

VIS_TABPLT:              int = 0   # Usa tabela de plotagem
VIS_TABNAO:              int = 1   # Nao usa tabela de plotagem

VIS_TEXLENTO:            int = 0   # texto lento
VIS_TEXRAPIDO:           int = 1   # texto rapido

VIS_CURLENTA:            int = 0   # curva lenta
VIS_CURRAPIDA:           int = 1   # curva rapida

VIS_GRADESEM:            int = 0   # Se grade
VIS_GRADECOM:            int = 1   # Com grade

VIS_IACEND:              int = 0   # Acende elemento
VIS_IAPAGA:              int = 1   # Apaga  elemento
VIS_INVERT:              int = -1  # Inverte elemento

VIS_BLONAO:              int = 0   # Display normal
VIS_BLOSIM:              int = 1   # Display exclusivo de um bloco

COR_PRETA:               int = 0   # Cor padrão EAG 0..255
COR_VERMELHA:            int = 1   # Cor padrão EAG 0..255
COR_AMARELA:             int = 2   # Cor padrão EAG 0..255
COR_VERDE:               int = 3   # Cor padrão EAG 0..255
COR_AZULCLARA:           int = 4   # Cor padrão EAG 0..255
COR_AZULESCURA:          int = 5   # Cor padrão EAG 0..255
COR_ROXA:                int = 6   # Cor padrão EAG 0..255
COR_BRANCA:              int = 7   # Cor padrão EAG 0..255
COR_CINZA:               int = 8   # Cor padrão EAG 0..255
COR_VERMELHAFRACA:       int = 9   # Cor padrão EAG 0..255
COR_MARROM:              int = 10  # Cor padrão EAG 0..255
COR_VERDEFRACA:          int = 11  # Cor padrão EAG 0..255
COR_AZULCLARAFRACA:      int = 12  # Cor padrão EAG 0..255
COR_AZULESCURAFRACA:     int = 13  # Cor padrão EAG 0..255
COR_ROXAFRACA:           int = 14  # Cor padrão EAG 0..255
COR_BRANCAFRACA:         int = 15  # Cor padrão EAG 0..255
COR_MAXCORES:            int = (COR_BRANCAFRACA+1)

VIS_STL_CONTINUO:        int = 0   # ___________
VIS_STL_TRACO:           int = 1   # _ _ _ _ _ _
VIS_STL_PONTO:           int = 2   # . . . . . .
VIS_STL_TRACOPONTO:      int = 3   # _ . _ . _ .
VIS_STL_TRACOPONTOPONTO: int = 4   # _ . . _ . .
VIS_STL_MINITRACO:       int = 5   # - - - - - -

RUB_LINEAR:              int = 0   # Rubberband linear
RUB_RETANG:              int = 1   # Rubberband retangular
RUB_NAO:                 int = 2   # Sem rubberband
RUB_PANDIN:              int = 3   # Caso particular: pan dinamico

RUBRET_NAOPREEN:         int = 0   # Não preenche rubber retangular
RUBRET_JANW:             int = 1   # Preenche como janela W
RUBRET_JANC:             int = 2   # Preenche como janela C
RUBRET_JANUSR:           int = 3   # Preenche como W (direita) ou C (esquerda)

INP_ENTER:               int = 0   # apertou ENTER
INP_ESCAPE:              int = 1   # apertou ESCAPE
INP_MOUSE:               int = 2   # Botao do mouse
INP_TECLA:               int = 3   # Uma tecla
INP_MOVE:                int = 4   # O mouse simplesmente se moveu
#-----------------------------------------------------------------------------
class Window ():
    """Janela Windows que renderiza um desenho TQS (DWG).

    Mantém uma "vista" do EAG sobre um ``HWND`` Windows e expõe operações
    de zoom/pan, leitura de pontos e tratamento de eventos básicos
    (paint, resize, teclas, mouse).

    Implementação:
        Os métodos são wrappers finos sobre funções C exportadas pelas DLLs
        ``EAGVISTA.DLL`` (vista/viewport), ``EAGENTRD.DLL`` (entrada de pontos),
        ``EAGPAR.DLL`` (parâmetros de plotagem) e ``ACESSOL.DLL`` (acesso ao
        sistema TQS). O padrão recorrente é: (1) embrulhar handles e valores
        em ``ctypes.c_void_p`` / ``ctypes.c_int`` / ``ctypes.c_double``;
        (2) chamar a função C via handle de DLL; (3) ler de volta as saídas
        via ``.value`` em parâmetros passados por referência.
        A inicialização aceita dois modos distintos: criar uma vista nova a
        partir de um par ``(hwnd, dwg)`` (uso típico em aplicações Python),
        ou recuperar uma vista pré-existente a partir de um handle ``pvistav``
        (uso quando o EAG já abriu a janela e nos dá apenas o ponteiro).

    Attributes:
        KEY_F8: Código wxPython da tecla F8.
        KEY_F9: Código wxPython da tecla F9.
        KEY_F10: Código wxPython da tecla F10.
        KEY_F11: Código wxPython da tecla F11.
        KEY_SHIFT: Código wxPython de Shift.
        KEY_ALT: Código wxPython de Alt.
        KEY_CTRL: Código wxPython de Ctrl.
        m_pvistav: Handle opaco para a estrutura ``CVistaV`` da DLL EAGVISTA.
        m_hWnd: Handle do controle Windows hospedeiro.
        m_dwg: Desenho associado (:class:`TQSDwg.Dwg`).
    """

    KEY_F8:    int = 347
    KEY_F9:    int = 348
    KEY_F10:   int = 349
    KEY_F11:   int = 350
    KEY_SHIFT: int = 306
    KEY_ALT:   int = 307
    KEY_CTRL:  int = 308

    def __init__ (self, hwnd: Optional[int], dwg: Optional["TQS.TQSDwg.Dwg"],
                  pvistav: Optional[int] = None) -> None:
        """Inicialização — dois modos de uso:

        * ``Window(hwnd, dwg)`` — quando já existem o DWG e o ``HWND`` Windows;
          cria uma nova vista englobando o desenho.
        * ``Window(None, None, pvistav)`` — quando a vista já existe (criada
          pelo EAG); recupera o objeto a partir do handle ``pvistav``.

        Args:
            hwnd: Handle da janela Windows hospedeira, ou ``None``.
            dwg: Desenho a exibir (:class:`TQSDwg.Dwg`), ou ``None``.
            pvistav: Handle de uma vista pré-existente, ou ``None``.
        """
        # Carrega as DLLs do EAG e inicializa o subsistema de acesso TQS
        self.m_pvistav   = 0
        self.m_acessol  = TQS.TQSUtil.LoadDll ("ACESSOL.DLL")
        self.m_eagvista = TQS.TQSUtil.LoadDll ("EAGVISTA.DLL")
        self.m_entr     = TQS.TQSUtil.LoadDll ("EAGENTRD.DLL")
        self.m_eagpar   = TQS.TQSUtil.LoadDll ("EAGPAR.DLL")
        self.m_acessol.ACL_INIACESSO ()
        if              pvistav is None:
            # Modo 1: criar uma vista nova a partir do par (hwnd, dwg)
            self.m_eagvista.vis_inicia ()
            self.m_entr.inp_inicia ()
            self.m_hWnd     = hwnd
            self.m_dwg      = dwg
            self._CreateView()
        else:
            # Modo 2: recuperar uma vista já existente — extrai HWND e o ponteiro do DWG
            # do handle pvistav e reconstrói o objeto Dwg correspondente
            self.m_pvistav  = pvistav
            parpvistav     = ctypes.c_void_p (self.m_pvistav)
            self.m_hWnd     = 0
            parhwnd         = ctypes.c_void_p (self.m_hWnd)
            pedmv           = 0
            parpedmv       = ctypes.c_void_p (pedmv)
            self.m_eagvista.vis_lerhandles (parpvistav, ctypes.byref(parhwnd), ctypes.byref(parpedmv))
            self.m_hWnd     = parhwnd.value
            pedmv           = parpedmv.value
            self.m_dwg      = TQS.TQSDwg.Dwg (pedmv)

        # Estado inicial: nenhuma tecla modificadora pressionada e modo ortogonal desligado
        self._LimparBotoes ()
        self._iortogonal = 0
#
#    Limpa botões para interepretar KeyDown
#
    def _LimparBotoes (self) -> None:
        """Reset interno do estado de teclas modificadoras."""
        self.m_ikey_ishif   = 0
        self.m_ikey_alt     = 0
        self.m_ikey_ctrl    = 0

#
#    Criacao da vista default englobando o desenho atual
#
    def _CreateView (self) -> None:
        """Cria a vista default centrada no desenho com 5% de margem."""
        # Etapa 1: lê os limites atuais do desenho e calcula uma margem de 5% para folga visual
        self.m_dwg.limits.UpdateLimits ()
        xmin, ymin, xmax, ymax = self.m_dwg.limits.DwgLimits ()
        deltax          = (xmax - xmin) * 0.05
        deltay          = (ymax - ymin) * 0.05
        # Etapa 2: carrega parâmetros de plotagem (suavização) e cor de fundo do EAG
        npsuav          = 0
        isuprdata       = 0
        parnpsuav       = ctypes.c_int (npsuav)
        parisuprdata    = ctypes.c_int (isuprdata)
        self.m_eagpar.plotdes_lerparam (ctypes.byref(parnpsuav), ctypes.byref(parisuprdata))
        icorfund        = 0
        paricorfund     = ctypes.c_int (icorfund)
        self.m_eagpar.eagpar_lercorfund (ctypes.byref(paricorfund))
        # Etapa 3: inicializa a vista no HWND e guarda o handle pvistav devolvido
        parhwnd         = ctypes.c_void_p (self.m_hWnd)
        paridlist       = ctypes.c_int (VIS_DLINATIVA)
        parpvistav      = ctypes.c_void_p (self.m_pvistav)
        self.m_eagvista.vis_inijan (parhwnd, paridlist, parnpsuav, paricorfund,
                            ctypes.byref (parpvistav))
        self.m_pvistav   = parpvistav.value
        # Etapa 4: define o viewport (janela de visualização) com os limites + margem
        parpedmv        = ctypes.c_void_p (self.m_dwg.settings.handle_pedmv)
        parxmin         = ctypes.c_double (xmin - deltax)
        parymin         = ctypes.c_double (ymin - deltay)
        parxmax         = ctypes.c_double (xmax + deltax)
        parymax         = ctypes.c_double (ymax + deltay)
        self.m_eagvista.vis_defjan (parpvistav, parpedmv, parxmin, parymin, parxmax, parymax)

#------------------------------------------------------------------------------
#    Métodos e propriedades
#
    @property
    def dwg (self) -> "TQS.TQSDwg.Dwg":
        """:class:`TQSDwg.Dwg`: Desenho associado a esta vista."""
        return         self.m_dwg

    def DestroyView (self) -> None:
        """Destrói e desaloca a vista atual.

        ATENÇÃO: a última linha chama ``self.vis_fim()``, um método que esta
        classe não define. A vista É invalidada, mas a chamada levanta
        ``AttributeError`` em seguida — envolva a chamada em ``try/except`` se
        precisar continuar depois de destruir a vista.
        """
        if             self.m_pvistav != None:
            parpvistav  = ctypes.c_void_p (self.m_pvistav)
            self.m_eagvista.vis_fimjan (parpvistav)
        self.m_pvistav = None
        self.vis_fim   ()


    def ChangeDwg (self, dwg: "TQS.TQSDwg.Dwg") -> None:
        """Altera o DWG associado a uma janela.

        A vista atual é destruída e uma nova é criada englobando o novo DWG.

        Args:
            dwg: Novo desenho a exibir.
        """
        self.m_dwg      = dwg
        if             self.m_pvistav != None:
            parpvistav  = ctypes.c_void_p (self.m_pvistav)
            self.m_eagvista.vis_fimjan (parpvistav)
       self._CreateView (self)


    def SetWindow (self, xmin: float, ymin: float, xmax: float, ymax: float) -> None:
        """Define a janela atual de visualização.

        Args:
            xmin: X mínimo do retângulo de visualização (em unidades de desenho).
            ymin: Y mínimo do retângulo de visualização.
            xmax: X máximo do retângulo de visualização.
            ymax: Y máximo do retângulo de visualização.
        """
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parpedmv       = ctypes.c_void_p (self.m_dwg.settings.handle_pedmv)
        parxmin        = ctypes.c_double (xmin)
        parymin        = ctypes.c_double (ymin)
        parxmax        = ctypes.c_double (xmax)
        parymax        = ctypes.c_double (ymax)
        self.m_eagvista.vis_defjan (parpvistav, parpedmv,
             parxmin, parymin, parxmax, parymax)

    def GetWindow (self) -> Tuple[float, float, float, float]:
        """Retorna a janela atual de visualização.

        Returns:
            Tupla ``(xmin, ymin, xmax, ymax)`` em unidades de desenho.
        """
        xmin           = 0.
        ymin           = 0.
        xmax           = 0.
        ymax           = 0.
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parxmin        = ctypes.c_double (xmin)
        parymin        = ctypes.c_double (ymin)
        parxmax        = ctypes.c_double (xmax)
        parymax        = ctypes.c_double (ymax)
        self.m_eagvista.vis_lerjan (parpvistav, ctypes.byref (parxmin),
             ctypes.byref (parymin), ctypes.byref (parxmax), ctypes.byref (parymax))
        xmin           = parxmin.value
        ymin           = parymin.value
        xmax           = parxmax.value
        ymax           = parymax.value
        return         xmin, ymin, xmax, ymax

    def WorldToScreen (self, x: float, y: float) -> Tuple[int, int]:
        """Converte coordenadas do mundo real para coordenadas de tela.

        Args:
            x: X em unidades de desenho.
            y: Y em unidades de desenho.

        Returns:
            Tupla ``(ix, iy)`` em pixels.
        """
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parx           = ctypes.c_double (x)
        pary           = ctypes.c_double (y)
        ix             = 0
        iy             = 0
        parix          = ctypes.c_int (ix)
        pariy          = ctypes.c_int (iy)
        self.m_eagvista.vis_wndwts (parpvistav, parx, pary, ctypes.byref (parix),
                                    ctypes.byref (pariy))
        ix             = parix.value
        iy             = pariy.value
        return         ix, iy

    def ScreenToWorld (self, ix: int, iy: int) -> Tuple[float, float]:
        """Converte coordenadas de tela para coordenadas do mundo real.

        Args:
            ix: X em pixels.
            iy: Y em pixels.

        Returns:
            Tupla ``(x, y)`` em unidades de desenho.
        """
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parix          = ctypes.c_int (ix)
        pariy          = ctypes.c_int (iy)
        x              = 0.
        y              = 0.
        parx           = ctypes.c_double (x)
        pary           = ctypes.c_double (y)
        self.m_eagvista.vis_wndstw (parpvistav, parix, pariy, ctypes.byref (parx),
                                    ctypes.byref (pary))
        x             = parx.value
        y             = pary.value
        return         x, y


    def Regen (self) -> None:
        """Regera o desenho na janela Windows."""
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        self.m_eagvista.vis_viregn (parpvistav)


    def Window2P (self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Redefine a janela atual do desenho por dois pontos.

        Args:
            x1: X do primeiro ponto.
            y1: Y do primeiro ponto.
            x2: X do segundo ponto.
            y2: Y do segundo ponto.
        """
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        self.m_eagvista.vis_vijanl2p (parpvistav, parx1, pary1, parx2, pary2)

    def WindowScale (self, scale: float) -> None:
        """Redefine a janela atual afastando por um fator de escala.

        Args:
            scale: Fator de escala (>1 afasta, <1 aproxima).
        """
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parscale       = ctypes.c_double (scale)
        self.m_eagvista.vis_vizom2 (parpvistav, parscale)

    def WindowPan (self, vx: float, vy: float) -> None:
        """Movimenta a janela atual por um vetor.

        Args:
            vx: Componente X do vetor de translação.
            vy: Componente Y do vetor de translação.
        """
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parx1          = ctypes.c_double (0.)
        pary1          = ctypes.c_double (0.)
        parx2          = ctypes.c_double (vx)
        pary2          = ctypes.c_double (vy)
        self.m_eagvista.vis_vipan2p (parpvistav, parx1, pary1, parx2, pary2)

    def GetPoint (self) -> Tuple[float, float, int]:
        """Lê um ponto do mouse/teclado.

        Returns:
            Tupla ``(x, y, istat)``. ``istat != 0`` se o usuário apertou ``<Esc>``.
        """
        x, y, istat    = self._PrimPonto (0)
        return         x, y, istat


    def GetPointRubberBand (self, x1: float, y1: float) -> Tuple[float, float, int]:
        """Lê um ponto com linha elástica conectada a ``(x1, y1)``.

        Args:
            x1: X do ponto âncora da linha elástica.
            y1: Y do ponto âncora da linha elástica.

        Returns:
            Tupla ``(x, y, istat)``. ``istat != 0`` se o usuário apertou ``<Esc>``.
        """
        x2, y2, istat  = self._SeguPonto (x1, y1, RUB_LINEAR)
        return         x2, y2, istat


    @property
    def orthogonal (self) -> int:
        """int: Flag interno de alinhamento X/Y usado na coleta de pontos deste objeto. NÃO altera o modo ortogonal do editor conectado; use ``eag.state.SetOrtho(tqsjan, iortho, angle)`` (TQSEag.State)."""
        return             self._iortogonal

    @orthogonal.setter
    def orthogonal (self, iorto: int) -> None:
        self._iortogonal   = iorto


#
#    Entra o primeiro ponto de 2 pedindo para o usuario (imod=0) ou
#    na posicao atual do cursor (imod=1)
#    Retorna x,y,istat
#
    def _PrimPonto (self, imod: int, posxy: List[float] = [0., 0.]) -> Tuple[float, float, int]:
        """Lê o primeiro ponto de uma operação de zoom/pan.

        Args:
            imod: ``0`` pede ao usuário, ``1`` usa a posição atual do cursor.
            posxy: Posição do cursor em pixels (usada se ``imod == 1``).

        Returns:
            Tupla ``(x, y, istat)`` com ``istat != 0`` se cancelado.
        """
        # Atalho: imod=1 já traz a posição do cursor — basta converter para coordenadas do mundo
        if             imod != 0:
            x, y       = self.ScreenToWorld (posxy [0], posxy [1])
            return     x, y, 0
        # Caso geral: bloqueia esperando o usuário clicar. Sem rubberband no primeiro ponto.
        irub           = RUB_NAO
        iortogonal     = 0
        x1             = 0.
        y1             = 0.
        x2             = 0.
        y2             = 0.
        itpmsg         = 0
        imudou         = 0
        ibotao         = 0
        nclient        = 0

        parpvistav     = ctypes.c_void_p   (self.m_pvistav)
        parirub        = ctypes.c_int    (irub)
        pariortogonal  = ctypes.c_int    (iortogonal)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        paritpmsg      = ctypes.c_int    (itpmsg)
        parimudou      = ctypes.c_int    (imudou)
        paribotao      = ctypes.c_int    (ibotao)
        parnclient     = ctypes.c_int    (nclient)
        self.m_entr.inp_getptpar (parpvistav, parirub, pariortogonal, parx1, pary1,
            ctypes.byref(parx2), ctypes.byref(pary2), ctypes.byref(paritpmsg),
            ctypes.byref(parimudou), ctypes.byref(paribotao), ctypes.byref(parnclient))
        x2             = parx2.value
        y2             = pary2.value
        itpmsg         = paritpmsg.value
        imudou         = parimudou.value
        ibotao         = paribotao.value
        nclient        = parnclient.value
        # imudou != 0 indica cancelamento (ESC ou perda de foco)
        if             imudou != 0:
             return    0., 0, 1
        return         x2, y2, 0


    def _SeguPonto (self, x1: float, y1: float, irub: int) -> Tuple[float, float, int]:
        """Lê o segundo ponto com rubberband a partir de ``(x1, y1)``.

        Args:
            x1: X do ponto âncora.
            y1: Y do ponto âncora.
            irub: Tipo de rubberband — :data:`RUB_LINEAR`, :data:`RUB_RETANG`,
                :data:`RUB_NAO` ou :data:`RUB_PANDIN`.

        Returns:
            Tupla ``(x, y, istat)`` com ``istat != 0`` se cancelado.
        """
#
#    Pega o segundo ponto, com rubberband linear ou retangular
#    Retorna x,y,istat
#
        # Bloqueia esperando o segundo clique do usuário, repassando o ponto âncora (x1, y1)
        # ao input do EAG para desenhar o rubberband em tempo real
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parirub        = ctypes.c_int    (irub)
        pariortogonal  = ctypes.c_int  (self._iortogonal)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        x2             = 0.
        y2             = 0.
        itpmsg         = 0
        imudou         = 0
        ibotao         = 0
        nclient        = 0
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        paritpmsg      = ctypes.c_int    (itpmsg)
        parimudou      = ctypes.c_int    (imudou)
        paribotao      = ctypes.c_int    (ibotao)
        parnclient     = ctypes.c_int    (nclient)
        self.m_entr.inp_getptpar (parpvistav, parirub, pariortogonal,
            parx1, pary1, ctypes.byref(parx2), ctypes.byref(pary2),
            ctypes.byref(paritpmsg), ctypes.byref(parimudou),
            ctypes.byref(paribotao), ctypes.byref(parnclient))
        x2             = parx2.value
        y2             = pary2.value
        itpmsg         = paritpmsg.value
        imudou         = parimudou.value
        ibotao         = paribotao.value
        nclient        = parnclient.value
        # Aceita apenas o botão 1 do mouse, sem cliente ativo e sem cancelamento
        if             itpmsg != INP_MOUSE or imudou != 0 or ibotao != 1 or nclient != 0:
            return     0., 0., 1
        # Modo ortogonal: força o segundo ponto a estar na horizontal ou vertical em relação ao
        # primeiro, escolhendo o eixo de maior deslocamento (snap a 0° ou 90°)
        if             self._iortogonal != 0:
            if         math.fabs (x2 - x1) > math.fabs (y2 - y1):
                y2     = y1
            else:
                x2     = x1
        return         x2, y2, 0


    def Zoom2P (self, imod: int, posxy: List[float] = [0., 0.]) -> None:
        """Zoom por janela definida por dois pontos.

        Args:
            imod: ``0`` pede dois pontos ao usuário; ``1`` usa o cursor como
                primeiro ponto e pede o segundo.
            posxy: Posição do cursor em pixels, usada quando ``imod == 1``.
        """
        # Etapa 1: lê o primeiro ponto (canto da janela de zoom)
        x1, y1, istat  = self._PrimPonto (imod, posxy)
        if             istat != 0:
            return
        # Etapa 2: lê o segundo ponto com rubberband retangular (define a janela)
        x2, y2, istat  = self._SeguPonto (x1, y1, RUB_RETANG)
        if             istat != 0:
            return
        # Etapa 3: redefine a janela do desenho usando os dois cantos
        parpvistav     = ctypes.c_void_p   (self.m_pvistav)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        self.m_eagvista.vis_vijanl2p (parpvistav, parx1, pary1, parx2, pary2)

    def ZoomTotal (self) -> None:
        """Faz zoom total englobando todo o desenho atual."""
        self.m_dwg.limits.UpdateLimits ()
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        self.m_eagvista.vis_viengl (parpvistav)

    def ZoomPan (self, imod: int, irub: int, posxy: List[float] = [0., 0.]) -> None:
        """Faz pan por dois pontos (1 ou 2 vindos do usuário).

        Args:
            imod: ``0`` lê do usuário, ``1`` usa ``posxy``.
            irub: Tipo de rubberband — :data:`RUB_LINEAR`, :data:`RUB_RETANG`,
                :data:`RUB_NAO` ou :data:`RUB_PANDIN`.
            posxy: Posição do cursor em pixels, usada quando ``imod == 1``.
        """
        # Etapa 1: ponto de partida do pan (origem do vetor de translação)
        x1, y1, istat = self._PrimPonto (imod, posxy)
        if      istat != 0:
            return
        # Etapa 2: ponto destino do pan, com o tipo de rubberband solicitado
        x2, y2, istat = self._SeguPonto (x1, y1, irub)
        if      istat != 0:
            return
        # Etapa 3: aplica a translação de (x1,y1) para (x2,y2) na janela atual
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        self.m_eagvista.vis_vipan2p (parpvistav, parx1, pary1, parx2, pary2)


    def ZoomOut (self) -> None:
        """Afasta a visualização por um fator de escala fixo de ``0.5``."""
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        scale          = 0.5
        parscale       = ctypes.c_double (scale)
        self.m_eagvista.vis_vizom2 (parpvistav, parscale)


    def ZoomPrevious (self) -> int:
        """Mostra a janela anterior do histórico de zoom.

        Returns:
            ``0`` se navegou; ``!= 0`` se não há mais janelas no histórico.
        """
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_eagvista.vis_vijant (parpvistav, ctypes.byref(paristat))
        istat          = paristat.value
        return         istat

#------------------------------------------------------------------------------
#    Eventos
#
    def OnPaint (self, hdc: int) -> None:
        """Regera o desenho dentro de um evento Windows ``WM_PAINT``.

        Args:
            hdc: Handle do device context da operação de pintura.
        """
        parpvistav     = ctypes.c_void_p (self.m_pvistav)
        parhdc         = ctypes.c_void_p (hdc)
        self.m_eagvista.vis_inidc (parpvistav, parhdc)
        self.m_eagvista.vis_viregndc (parpvistav)
        self.m_eagvista.vis_fimdc (parpvistav)


    def OnSize (self, cx: int, cy: int) -> None:
        """Atualiza a vista quando a janela hospedeira muda de tamanho.

        Args:
            cx: Nova largura, em pixels.
            cy: Nova altura, em pixels.
        """
        if             self.m_pvistav != None:
            parpvistav  = ctypes.c_void_p (self.m_pvistav)
            self.m_eagvista.vis_resizejan (parpvistav)


    def OnKey (self, ikeycode: int, posxy: List[float]) -> None:
        """Processa eventos ``EVT_KEY_DOWN`` (wxPython) com :py:meth:`GetKeyCode`.

        Atalhos tratados:

        * ``<F8>`` — Janela por 2 pontos.
        * ``<Shift>+<F8>`` — Janela total.
        * ``<Ctrl>+<F8>`` — Janela anterior.
        * ``<Alt>+<F8>`` — Deslocamento de janela.
        * ``<F11>`` — Zoom out.
        * ``<F10>`` — Liga/desliga modo ortogonal.

        Args:
            ikeycode: Código wxPython da tecla.
            posxy: Posição do cursor em pixels.
        """
        # F8 atua como dispatcher: a ação depende de qual modificador (Shift/Alt/Ctrl)
        # foi memorizado em eventos KEY_DOWN anteriores
        if             ikeycode == Window.KEY_F8:
            if         self.m_ikey_ishif != 0:
                # Shift+F8: zoom englobando todo o desenho
                self.ZoomTotal ()
                self._LimparBotoes ()

            elif       self.m_ikey_alt != 0:
                # Alt+F8: pan por dois pontos
                self.ZoomPan (1, RUB_LINEAR, posxy)
                self._LimparBotoes ()

            elif       self.m_ikey_ctrl != 0:
                # Ctrl+F8: navega para a janela anterior do histórico
                self.ZoomPrevious ()
                self._LimparBotoes ()

            else:
                # F8 puro: zoom por janela definida por dois pontos
                self.Zoom2P (1, posxy)
                self._LimparBotoes ()

        # F10: alterna o modo ortogonal (toggle 0/1)
        elif           ikeycode == Window.KEY_F10:
            self.orthogonal = 1 - self.orthogonal
        # F11: zoom out por fator fixo
        elif           ikeycode == Window.KEY_F11:
            self.ZoomOut ()
            self._LimparBotoes ()

        # Modificadores: apenas memoriza o estado para combinar com a próxima tecla.
        # _LimparBotoes() é chamado pelas ações acima para resetar este estado depois de consumido.
        elif           ikeycode == Window.KEY_SHIFT:
            self.m_ikey_ishif = 1
        elif           ikeycode == Window.KEY_ALT:
            self.m_ikey_alt   = 1
        elif           ikeycode == Window.KEY_CTRL:
            self.m_ikey_ctrl    = 1


    def OnMouseMiddle (self, posxy: List[float]) -> None:
        """Trata botão do meio do mouse com pan dinâmico.

        Args:
            posxy: Posição do cursor em pixels.
        """
        self.ZoomPan   (1, RUB_PANDIN, posxy)



    def OnWheel (self, idelta: int, posxy: List[float]) -> None:
        """Processa N deslocamentos do rolete do mouse (zoom in/out).

        Args:
            idelta: Quantidade de "cliques" do rolete (positivo aproxima,
                negativo afasta).
            posxy: Posição do cursor em pixels (centro do zoom).
        """

        # Fator multiplicativo por clique do rolete; idelta>0 aproxima (escala<1) e
        # idelta<0 afasta (escala>1) — daí o sinal negativo no expoente.
        FATROSCA       = 1.1;                    # Zoom por passo
        escala         = FATROSCA ** float (-idelta)
        # Lê a janela corrente e converte o cursor (pixels) para coordenadas do mundo —
        # é nesse ponto (xp, yp) que o zoom será centrado.
        xmin, ymin, xmax, ymax = self.GetWindow ()
        xp, yp         = self.ScreenToWorld (posxy [0], posxy [1])
        # Reescala cada canto em torno de (xp, yp): novo_canto = pivô + (canto - pivô)*escala.
        # Isto mantém o ponto sob o cursor fixo na tela enquanto a janela contrai/expande.
        xmin           = xp + (xmin - xp)*escala
        ymin           = yp + (ymin - yp)*escala
        xmax           = xp + (xmax - xp)*escala
        ymax           = yp + (ymax - yp)*escala
        # Aplica a nova janela e regera o desenho
        self.SetWindow (xmin, ymin, xmax, ymax)
        self.Regen     ()
