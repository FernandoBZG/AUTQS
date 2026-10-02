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
#    TQSEagSM.py        Acesso à API do EAGME - Modelador Estrutural
#                       EAGME.DLL
#                       Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING, Optional, Tuple

from TQS import TQSUtil, TQSJan, TQSModel, TQSEagSM

if TYPE_CHECKING:
    from TQS.TQSEag import Eag
    from TQS.TQSModel import Model, Floor

#-----------------------------------------------------------------------------
#       Constantes de seleção de elementos estruturais
#
#       Janela de seleção
#
SEL_JAN_SELECPONTO:  int = 0     # Seleção por pontos
SEL_JAN_SELECW:      int = 1     # Seleção por janela W
SEL_JAN_SELECC:      int = 2     # Seleção por janela C
SEL_JAN_SELECD:      int = 3     # Seleção por janela D
SEL_JAN_SELECR:      int = 4     # Seleção por janela R
#
#       Seleciona um ou vários até <Enter>
#
SEL_MUL_UMELEM:      int = 0     # Seleciona um, mas pode mudar p/varios
SEL_MUL_MULTIP:      int = 1     # Selecao múltipla
SEL_MUL_SOUMEL:      int = 2     # Seleciona somente um
#
#       Tipo de cursor
#
SEL_CUR_CURNORMAL:   int = 0     # Clique do mouse
SEL_CUR_CURPRIMEI:   int = 1     # Usa posição do cursor atual
#
#       Lista de objetos
#
SEL_LIS_OBJQUALQUER: int = -2    # Objeto de qualquer lista
SEL_LIS_OBJMESMALIS: int = -1    # Qualquer lista, mas todos objetos da mesma
#
#       Textos identificadores
#
SEL_TXT_TEXTONAO:    int = 0     # Somente objeto inteiro
SEL_TXT_TEXTOSIM:    int = 1     # Pode selecionar somente texto identificador
#
#       Seleção parcial de um objeto
#
SEL_SPR_INTEIRONAO:  int = 0     # Pode selecionar trecho ou todo objeto
SEL_SPR_INTEIROSIM:  int = 1     # Somente seleção do objeto inteiro
#
#       Elementos inclinados
#
SEL_INC_INCLIQQ:     int = 0     # Inclinados ou não
SEL_INC_INCLINAO:    int = 1     # Todos menos inclinados
SEL_INC_INCLISIM:    int = 2     # Somente inclinados
#
#       Pisos auxiliares
#
SEL_AUX_PISOAUXQQ:   int = -1    # Qualquer piso auxiliar
#-----------------------------------------------------------------------------
#       Classe SM (Structural Modeler) - Interação no Modelador Estrutural
#
class SM ():
    """Interface Python para o ``EAGME.DLL`` (Modelador Estrutural).

    Encapsula handles de DLL e expõe sub-objetos :class:`Locate`, :class:`Undo`
    e :class:`View`.

    Implementação:
        Os métodos das sub-classes são wrappers finos sobre funções C++ exportadas
        pelas DLLs ``EAGW.EXE``, ``EAGME.DLL``, ``EAGVISTA.DLL`` e ``MDWG.DLL``.
        O padrão recorrente é: (1) embrulhar ponteiros e ints/doubles em ``ctypes.c_*``;
        (2) chamar a função C++ através do handle de DLL apropriado; (3) ler de
        volta as saídas via ``.value`` em parâmetros passados por referência.
        Comentários inline são adicionados apenas onde a sequência foge desse padrão.

    Attributes:
        SMSingleton: Instância singleton (compartilhada entre chamadas).
        m_eagdll: Handle de ``EAGW.EXE``.
        m_eagme: Handle de ``EAGME.DLL``.
        m_eagvista: Handle de ``EAGVISTA.DLL``.
        m_mdwg: Handle de ``MDWG.DLL``.
        m_tqseag: Editor gráfico básico (:class:`TQSEag.Eag`).
        m_model: Modelo estrutural (:class:`TQSModel.Model`).
        m_floor: Planta atual (:class:`TQSModel.Floor`).
        m_edif: Estrutura interna do Modelador (handle ``CEdif*``).
        m_lisedi: Estrutura interna do Modelador (handle ``CListaEdif*``).
        locate: Sub-objeto de seleção/localização.
        undo: Sub-objeto de gerência de undo.
        view: Sub-objeto de visualização.
    """

    SMSingleton: Optional["SM"] = None                          # Objeto Singleton

    def __init__ (self, tqseag: "Eag", model: "Model", floor: "Floor",
                  edif: int, lisedi: int) -> None:
        """Inicializa o modelador estrutural.

        Args:
            tqseag: Editor gráfico básico (:class:`TQSEag.Eag`).
            model: Modelo estrutural (:class:`TQSModel.Model`).
            floor: Planta atual (:class:`TQSModel.Floor`).
            edif: Handle opaco para a estrutura ``CEdif`` interna.
            lisedi: Handle opaco para a estrutura ``CListaEdif`` interna.
        """
        # Carrega as DLLs do Modelador Estrutural; falhas são detectadas em LoadDll
        self.m_eagdll   = TQSUtil.LoadDll ("EAGW.EXE")
        self.m_eagme    = TQSUtil.LoadDll ("EAGME.DLL")
        self.m_eagvista = TQSUtil.LoadDll ("EAGVISTA.DLL")
        self.m_mdwg     = TQSUtil.LoadDll ("MDWG.DLL")
        self.m_tqseag   = tqseag                        # Objeto TQSEag
        self.m_model    = model                         # Objeto PY que mexe no modelo estrutural
        self.m_floor    = floor                         # Container da planta atual
        self.m_edif     = edif                          # Estrutura interna do Modelador
        self.m_lisedi   = lisedi                        # Estrutura interna do Modelador
        # Instancia sub-objetos delegando seleção, undo e visualização
        self.locate     = Locate (self, tqseag, model, floor)
        self.undo       = Undo (self, tqseag, model)
        self.view       = View (self, tqseag, model)


        # Registra na EAGME.DLL os handles internos de edifício e lista de edifícios
        paredif         = ctypes.c_void_p (edif)
        parlisedi       = ctypes.c_void_p (lisedi)
        self.m_eagme.INTME_ESTRUTURASMODELO_DEF (paredif, parlisedi)
#
#    Objeto Singleton de acesso ao editor
#
    @classmethod
    def GetSM (self, tqseag: "Eag", model: "Model", floor: "Floor",
               edif: int, lisedi: int) -> "SM":
        """Retorna a instância única :class:`SM` do Modelador (Singleton).

        Use este método em vez de chamar ``SM()`` diretamente para evitar
        alocar recursos redundantes.

        Args:
            tqseag: Editor gráfico básico.
            model: Modelo estrutural.
            floor: Planta atual.
            edif: Handle ``CEdif`` interno.
            lisedi: Handle ``CListaEdif`` interno.

        Returns:
            Instância singleton de :class:`SM`.
        """
        # Cria a instância singleton apenas na primeira chamada; reaproveita nas seguintes
        if             self.SMSingleton is None:
            self.SMSingleton = SM (tqseag, model, floor, edif, lisedi)
        return         self.SMSingleton

#-----------------------------------------------------------------------------
#    Localização de elementos gráficos e leitura de coordenadas
#
class LocateOptions ():
    """Opções de seleção para :meth:`Locate.Select`.

    Cada propriedade aceita uma das constantes ``SEL_*`` deste módulo.
    """

    def __init__ (self) -> None:
        """Inicializa as opções com valores default razoáveis."""
        self.m_itpjan       = TQSEagSM.SEL_JAN_SELECPONTO
        self.m_iselmulti    = TQSEagSM.SEL_MUL_UMELEM
        self.m_itpcur       = TQSEagSM.SEL_CUR_CURNORMAL
        self.m_itplis       = TQSEagSM.SEL_LIS_OBJQUALQUER
        self.m_iseltexto    = TQSEagSM.SEL_TXT_TEXTOSIM
        self.m_iselglobal   = TQSEagSM.SEL_SPR_INTEIRONAO
        self.m_iselinclinado= TQSEagSM.SEL_INC_INCLIQQ
        self.m_iselpisoaux  = TQSEagSM.SEL_AUX_PISOAUXQQ

    @property
    def windowType (self) -> int:
        """int: Tipo de janela de seleção. Use uma das constantes ``SEL_JAN_*``."""
        return          self.m_itpjan
    @windowType.setter
    def windowType (self, itpjan: int) -> None:
        """Atribui Tipo de janela de seleção. Use uma das constantes ``SEL_JAN_*``."""
        self.m_itpjan       = itpjan

    @property
    def multiElement (self) -> int:
        """int: Quantidade de seleções (uma ou várias). Use ``SEL_MUL_*``."""
        return          self.m_iselmulti
    @multiElement.setter
    def multiElement (self, iselmulti: int) -> None:
        """Atribui Quantidade de seleções (uma ou várias). Use ``SEL_MUL_*``."""
        self.m_iselmulti    = iselmulti

    @property
    def mousePosition (self, itpcur: int) -> int:
        """int: Origem do primeiro ponto: clique ou cursor atual. Use ``SEL_CUR_*``.

        ATENÇÃO: na biblioteca TQS este getter declara um parâmetro extra, então
        LER ``options.mousePosition`` levanta ``TypeError``. Somente a atribuição
        funciona; guarde o valor em uma variável própria se precisar consultá-lo.
        """
        return          self.m_itpcur
    @mousePosition.setter
    def mousePosition (self, itpcur: int) -> None:
        """Atribui Origem do primeiro ponto: clique ou cursor atual. Use ``SEL_CUR_*``."""
        self.m_itpcur       = itpcur

    @property
    def objectType (self) -> int:
        """int: Restringe a seleção a um tipo. Use ``SEL_LIS_*`` ou ``TQSModel.TYPE_*``."""
        return          self.m_itplis
    @objectType.setter
    def objectType (self, itplis: int) -> None:
        """Atribui Restringe a seleção a um tipo. Use ``SEL_LIS_*`` ou ``TQSModel.TYPE_*``."""
        self.m_itplis       = itplis

    @property
    def allowIdent (self, iseltexto: int) -> int:
        """int: Permite seleção parcial de identificadores. Use ``SEL_TXT_*``.

        ATENÇÃO: na biblioteca TQS este getter declara um parâmetro extra, então
        LER ``options.allowIdent`` levanta ``TypeError``. Somente a atribuição
        funciona; guarde o valor em uma variável própria se precisar consultá-lo.
        """
        return          self.m_iseltexto
    @allowIdent.setter
    def allowIdent (self, iseltexto: int) -> None:
        """Atribui Permite seleção parcial de identificadores. Use ``SEL_TXT_*``."""
        self.m_iseltexto    = iseltexto

    @property
    def partialSelect (self) -> int:
        """int: Permite seleção parcial do objeto ou somente completo. Use ``SEL_SPR_*``."""
        return          self.m_iselglobal
    @partialSelect.setter
    def partialSelect (self, iselglobal: int) -> None:
        """Atribui Permite seleção parcial do objeto ou somente completo. Use ``SEL_SPR_*``."""
        self.m_iselglobal   = iselglobal

    @property
    def slopedOnly (self) -> int:
        """int: Filtro de inclinação dos elementos. Use ``SEL_INC_*``."""
        return          self.m_iselinclinado
    @slopedOnly.setter
    def slopedOnly (self, iselinclinado: int) -> None:
        """Atribui Filtro de inclinação dos elementos. Use ``SEL_INC_*``."""
        self.m_iselinclinado= iselinclinado

    @property
    def auxiliaryFloor (self) -> int:
        """int: Filtro por piso auxiliar (base zero) ou ``SEL_AUX_PISOAUXQQ`` para qualquer."""
        return          self.m_iselpisoaux
    @auxiliaryFloor.setter
    def auxiliaryFloor (self, iselpisoaux: int) -> None:
        """Atribui Filtro por piso auxiliar (base zero) ou ``SEL_AUX_PISOAUXQQ`` para qualquer."""
        self.m_iselpisoaux  = iselpisoaux

class Locate ():
    """Seleção interativa de elementos estruturais.

    Implementação:
        Os métodos são wrappers finos sobre funções ``BASME_SELEC_*`` exportadas
        pela ``EAGME.DLL``. O padrão é: (1) embrulhar handles e parâmetros em
        ``ctypes.c_*``; (2) chamar a função C++ por referência; (3) ler as saídas
        via ``.value``. Comentários inline são adicionados apenas onde a sequência
        envolve várias chamadas ou decisões não triviais.
    """

    def __init__ (self, sm: "SM", tqseag: "Eag", model: "Model", floor: "Floor") -> None:
        """Inicializa o sub-objeto de localização.

        Args:
            sm: Modelador estrutural proprietário.
            tqseag: Editor gráfico básico.
            model: Modelo estrutural.
            floor: Planta atual.
        """
        self.m_sm       = sm
        self.m_tqseag   = tqseag
        self.m_model    = model
        self.m_floor    = floor

    def Select (self, tqsjan: "TQSJan.Window", msg: str,
                locateOptions: "LocateOptions") -> Tuple[float, float, int]:
        """Faz a seleção interativa de elementos estruturais.

        Args:
            tqsjan: Janela do EAG (:class:`TQSJan.Window`).
            msg: Mensagem exibida ao usuário durante a seleção.
            locateOptions: Configuração da seleção (:class:`LocateOptions`).

        Returns:
            Tupla ``(xsel, ysel, istat)``:

            * ``xsel`` (``float``): X da seleção quando por ponto, em cm.
            * ``ysel`` (``float``): Y da seleção quando por ponto, em cm.
            * ``istat`` (``int``): ``0`` se Ok, ``!= 0`` em caso de erro.
        """
        # Exibe a mensagem de prompt antes de iniciar a captura
        self.m_tqseag.msg.Print (msg)
        # Empacota handles da janela e a string de mensagem (codificada no charset do TQS)
        parpedmv        = ctypes.c_void_p (tqsjan.m_dwg.m_pedmv)
        parpvistav      = ctypes.c_void_p (tqsjan.m_pvistav)
        parmsg          = ctypes.c_char_p (msg.encode(TQSUtil.CHARSET))
        # Converte os filtros do LocateOptions para o conjunto de flags esperado pela EAGME
        paritpjan       = ctypes.c_int (locateOptions.m_itpjan)
        pariselmulti    = ctypes.c_int (locateOptions.m_iselmulti)
        paritpcur       = ctypes.c_int (locateOptions.m_itpcur)
        paritplis       = ctypes.c_int (locateOptions.m_itplis)
        pariseltexto    = ctypes.c_int (locateOptions.m_iseltexto)
        pariselglobal   = ctypes.c_int (locateOptions.m_iselglobal)
        pariselinclinado= ctypes.c_int (locateOptions.m_iselinclinado)
        pariselpisoaux  = ctypes.c_int (locateOptions.m_iselpisoaux)
        # Saídas: ponto selecionado e status retornados por referência
        xsel            = 0.
        ysel            = 0.
        istat           = 0
        parxsel         = ctypes.c_double (xsel)
        parysel         = ctypes.c_double (ysel)
        paristat        = ctypes.c_int (istat)
        # Bloqueia até o usuário concluir a seleção interativa
        self.m_sm.m_eagme.BASME_SELEC_SELECIONAR (ctypes.byref (parpedmv),
                            ctypes.byref (parpvistav),                                          \
                            parmsg, ctypes.byref (paritpjan), ctypes.byref (pariselmulti),      \
                            ctypes.byref (paritpcur), ctypes.byref (paritplis),                 \
                            ctypes.byref (pariseltexto), ctypes.byref (pariselglobal),          \
                            ctypes.byref (pariselinclinado), ctypes.byref (pariselpisoaux),     \
                            ctypes.byref (parxsel), ctypes.byref (parysel), ctypes.byref (paristat))
        # Lê de volta o ponto clicado e o código de status
        xsel            = parxsel.value
        ysel            = parysel.value
        istat           = paristat.value
        return         xsel, ysel, istat


    def NumSelections (self) -> int:
        """Retorna o número de seleções da última operação :meth:`Select`.

        Returns:
            Quantidade de elementos atualmente selecionados.
        """
        numsel          = 0
        parnumsel       = ctypes.c_int (numsel)
        self.m_sm.m_eagme.BASME_SELEC_NUMSEL_LER (ctypes.byref (parnumsel))
        numsel          = parnumsel.value
        return          numsel


    def GetSelection (self, index: int) -> Tuple[object, int, int, int, int, int, float, float]:
        """Lê uma seleção feita com :meth:`Select`.

        Args:
            index: Índice da seleção (``0..NumSelections()-1``).

        Returns:
            Tupla ``(smobject, iponto, itrecho, indponto, ielem, itexto, x, y)``:

            * ``smobject``: Objeto estrutural selecionado (``SMObject`` derivado).
            * ``iponto`` (``int``): ``1`` se seleção pontual.
            * ``itrecho`` (``int``): trecho da poligonal (válido se ``iponto==1``).
            * ``indponto`` (``int``): índice do ponto próximo (válido se ``iponto==1``).
            * ``ielem`` (``int``): tipo de sub-elemento (válido se ``iponto==1``).
            * ``itexto`` (``int``): ``1`` se foi texto identificador (válido se ``iponto==1``).
            * ``x`` (``float``): X da seleção pontual (válido se ``iponto==1``).
            * ``y`` (``float``): Y da seleção pontual (válido se ``iponto==1``).
        """
        # Aloca todas as saídas que a EAGME preencherá: ponteiro do objeto + dados auxiliares
        parindex        = ctypes.c_int (index)
        objme           = None
        parobjme        = ctypes.c_void_p (objme)
        iponto          = 0
        pariponto       = ctypes.c_int (iponto)
        itrecho         = 0
        paritrecho      = ctypes.c_int (itrecho)
        indponto        = 0
        parindponto     = ctypes.c_int (indponto)
        ielem           = 0
        parielem        = ctypes.c_int (ielem)
        itexto          = 0
        paritexto       = ctypes.c_int (itexto)
        x               = 0.
        parx            = ctypes.c_double (x)
        y               = 0.
        pary            = ctypes.c_double (y)
        # Recupera os dados da i-ésima seleção armazenada pela última chamada a Select()
        self.m_sm.m_eagme.BASME_SELEC_SEL_LER (ctypes.byref (parindex),
                        ctypes.byref (parobjme), ctypes.byref (pariponto),              \
                        ctypes.byref (paritrecho), ctypes.byref (parindponto),          \
                        ctypes.byref (parielem), ctypes.byref (paritexto),              \
                        ctypes.byref (parx), ctypes.byref (pary))
        # Converte o ponteiro CObjMe* em um objeto Python derivado (Pilar, Viga, ...)
        objme           = parobjme.value
        smobject        = self.m_floor.iterator.DerivedObject (objme)
        iponto          = pariponto.value
        itrecho         = paritrecho.value
        indponto        = parindponto.value
        ielem           = parielem.value
        itexto          = paritexto.value
        x               = parx.value
        y               = pary.value
        return          smobject, iponto, itrecho, indponto, ielem, itexto, x, y


    def ClearSelection (self) -> None:
        """Limpa todos os elementos da seleção atual."""
        self.m_sm.m_eagme.BASME_SELEC_LIMPAR ()


    def EnterSelection (self, floor: "Floor", smobject: object) -> None:
        """Entra um objeto na lista de seleção (simula uma seleção interativa).

        Args:
            floor: Planta atual onde o objeto reside.
            smobject: Objeto estrutural a adicionar à seleção.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varsmobject     = ctypes.c_void_p (smobject.m_objme)
        self.m_sm.m_eagme.BASME_SELEC_ENTRAR (ctypes.byref (varfabrica), ctypes.byref (varsmobject))

#-----------------------------------------------------------------------------
#    Operações de Undo
#
class Undo ():
    """Gerência de operações de undo no Modelador Estrutural.

    Cada tipo de operação (criação, alteração, remoção) é demarcado por um
    par ``Begin``/``End``. Operações podem ser agrupadas via
    :meth:`GroupBegin`/:meth:`GroupEnd` para que sejam desfeitas juntas.

    Implementação:
        Os métodos são wrappers finos sobre funções ``BASME_UNDO_*`` exportadas
        pela ``EAGME.DLL``. Cada par ``Begin``/``End`` mantém estado interno
        (``m_floor``, ``m_smobject``, ``m_itipo``) para impedir aninhamento
        indevido e garantir que a DLL receba uma sequência simétrica de chamadas.

    Attributes:
        INDEF: Marcador de tipo indefinido.
        CREATE: Operação de criação.
        CHANGE: Operação de alteração.
        ERASE: Operação de remoção.
        GRUPO: Marcador de grupo aberto.
        MSGUNDOABERTO: Mensagem de erro: undo já estava aberto.
        MSGUNDOFECHADO: Mensagem de erro: undo não estava aberto.
    """

    INDEF:           int = -1
    CREATE:          int = 0
    CHANGE:          int = 1
    ERASE:           int = 2
    GRUPO:           int = 3
    MSGUNDOABERTO:   str = "ERRO: Undo aberto "
    MSGUNDOFECHADO:  str = "ERRO: Undo fechado "

    def __init__ (self, sm: "SM", tqseag: "Eag", model: "Model") -> None:
        """Inicializa o sub-objeto de undo.

        Args:
            sm: Modelador estrutural proprietário.
            tqseag: Editor gráfico básico.
            model: Modelo estrutural.
        """
        self.m_sm       = sm
        self.m_tqseag   = tqseag
        self.m_model    = model
        self.m_floor    = None
        self.m_smobject = None
        self.m_itipo    = self.INDEF
        self.m_floorgrupo=None
        self.m_igrupo   = self.INDEF

    def CreateBegin (self, floor: "Floor", smobject: object) -> None:
        """Inicia armazenamento de undo para criação de um objeto.

        Args:
            floor: Planta atual.
            smobject: Objeto recém-criado.
        """
        # Begin/End não são re-entrantes: rejeita se já houver um par em aberto
        if              (self.m_floor != None or self.m_smobject != None or
                         self.m_itipo != self.INDEF):
            self.m_sm.m_tqseag.msg.Print (self.MSGUNDOABERTO + "CreateBegin")#!NTR
            return
        # Memoriza o par (planta, objeto) para validação no End correspondente
        self.m_floor    = floor
        self.m_smobject = smobject
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varobjme     = ctypes.c_void_p (self.m_smobject.m_objme)
        # Sinaliza à EAGME para começar a registrar a operação de criação no buffer de undo
        self.m_sm.m_eagme.BASME_UNDO_CRIAR_INI (ctypes.byref (varfabrica), ctypes.byref (varobjme))
        self.m_itipo    = self.CREATE

    def CreateEnd (self) -> None:
        """Finaliza armazenamento de undo iniciado em :meth:`CreateBegin`."""
        # Confirma que existe um CreateBegin em aberto e que o tipo bate
        if              (self.m_floor == None or self.m_smobject == None or \
                         self.m_itipo != self.CREATE):
            self.m_sm.m_tqseag.msg.Print (self.MSGUNDOFECHADO + "CreateEnd")#!NTR
            return
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varobjme     = ctypes.c_void_p (self.m_smobject.m_objme)
        # Fecha o registro de undo da criação na EAGME
        self.m_sm.m_eagme.BASME_UNDO_CRIAR_FIM (ctypes.byref (varfabrica), ctypes.byref (varobjme))
        # Restaura o estado para permitir um novo par Begin/End
        self.m_floor    = None
        self.m_smobject = None
        self.m_itipo    = self.INDEF

    def ChangeBegin (self, floor: "Floor", smobject: object) -> None:
        """Inicia armazenamento de undo para alteração de um objeto.

        Args:
            floor: Planta atual.
            smobject: Objeto que vai ser alterado (snapshot do estado anterior).
        """
        # Begin/End não são re-entrantes: rejeita se já houver um par em aberto
        if              (self.m_floor != None or self.m_smobject != None or \
                         self.m_itipo != self.INDEF):
            self.m_sm.m_tqseag.msg.Print (self.MSGUNDOABERTO + "ChangeBegin")#!NTR
            return
        # Memoriza o par (planta, objeto) para validação no ChangeEnd
        self.m_floor    = floor
        self.m_smobject = smobject
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_smobject.m_objme)
        # Captura snapshot do estado anterior do objeto antes da edição
        self.m_sm.m_eagme.BASME_UNDO_ALTERAR_INI (ctypes.byref (varfabrica), ctypes.byref (varobjme))
        self.m_itipo    = self.CHANGE

    def ChangeEnd (self, smobject: object) -> None:
        """Finaliza armazenamento de undo iniciado em :meth:`ChangeBegin`.

        Args:
            smobject: Objeto após a modificação.
        """
        # Confirma que existe um ChangeBegin em aberto e que o tipo bate
        if              (self.m_floor == None or self.m_smobject == None or \
                         self.m_itipo != self.CHANGE):
            self.m_sm.m_tqseag.msg.Print (self.MSGUNDOFECHADO + "ChangeEnd")#!NTR
            return
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        # Usa o objeto pós-edição passado como argumento (não o memorizado no Begin)
        varobjme        = ctypes.c_void_p (smobject.m_objme)
        # Registra o estado final na EAGME, fechando o snapshot da alteração
        self.m_sm.m_eagme.BASME_UNDO_ALTERAR_FIM (ctypes.byref (varfabrica), ctypes.byref (varobjme))
        # Restaura o estado para permitir um novo par Begin/End
        self.m_floor    = None
        self.m_smobject = None
        self.m_itipo    = self.INDEF

    def EraseBegin (self, floor: "Floor", smobject: object) -> None:
        """Inicia armazenamento de undo para eliminação de um objeto.

        Args:
            floor: Planta atual.
            smobject: Objeto antes de ser apagado.
        """
        # Begin/End não são re-entrantes: rejeita se já houver um par em aberto
        if              (self.m_floor != None or self.m_smobject != None or \
                         self.m_itipo != self.INDEF):
            self.m_sm.m_tqseag.msg.Print (self.MSGUNDOABERTO + "EraseBegin")#!NTR
            return
        # Memoriza o par (planta, objeto) para validação no EraseEnd
        self.m_floor    = floor
        self.m_smobject = smobject
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_smobject.m_objme)
        # EAGME guarda uma cópia do objeto para permitir reconstruí-lo em caso de undo
        self.m_sm.m_eagme.BASME_UNDO_APAGAR_INI (ctypes.byref (varfabrica), ctypes.byref (varobjme))
        self.m_itipo    = self.ERASE

    def EraseEnd (self) -> None:
        """Finaliza armazenamento de undo iniciado em :meth:`EraseBegin`."""
        # Confirma que existe um EraseBegin em aberto e que o tipo bate
        if              (self.m_floor == None or self.m_smobject == None or \
                         self.m_itipo != self.ERASE):
            self.m_sm.m_tqseag.msg.Print (self.MSGUNDOFECHADO + "EraseEnd")#!NTR
            return
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_smobject.m_objme)
        # Conclui a remoção: a partir daqui o objeto é efetivamente apagado do modelo
        self.m_sm.m_eagme.BASME_UNDO_APAGAR_FIM (ctypes.byref (varfabrica), ctypes.byref (varobjme))
        # Restaura o estado para permitir um novo par Begin/End
        self.m_floor    = None
        self.m_smobject = None
        self.m_itipo    = self.INDEF

    def GroupBegin (self, floor: "Floor") -> None:
        """Inicia um grupo de operações para undo simultâneo.

        Todas as operações até :meth:`GroupEnd` serão tratadas como uma única
        unidade de undo.

        Args:
            floor: Planta atual.
        """
        # Memoriza a planta do grupo: o GroupEnd usará o mesmo handle de fábrica
        self.m_floorgrupo= floor
        varfabrica      = ctypes.c_void_p (self.m_floorgrupo.m_fabrica)
        # Marca o início de um grupo: pares Begin/End subsequentes serão atomicamente desfeitos
        self.m_sm.m_eagme.BASME_UNDO_GRUPO_INI (ctypes.byref (varfabrica))
        self.m_igrupo   = self.GRUPO

    def GroupEnd (self) -> None:
        """Finaliza o grupo iniciado em :meth:`GroupBegin`."""
        varfabrica      = ctypes.c_void_p (self.m_floorgrupo.m_fabrica)
        # Fecha o grupo na EAGME e restaura o marcador para permitir um novo grupo
        self.m_sm.m_eagme.BASME_UNDO_GRUPO_FIM (ctypes.byref (varfabrica))
        self.m_igrupo   = self.INDEF

#-----------------------------------------------------------------------------
#    Operações envolvendo visualização de elementos
#
class View ():
    """Operações de visualização e navegação entre plantas.

    Implementação:
        Os métodos são wrappers finos sobre funções ``INTME_*`` exportadas pela
        ``EAGME.DLL``. O padrão é: (1) embrulhar handles em ``ctypes.c_void_p``;
        (2) chamar a função C++ por referência. Comentários inline são adicionados
        apenas onde a sequência envolve passos auxiliares (ex.: refazer
        intersecções antes de regerar a tela).
    """

    def __init__ (self, sm: "SM", tqseag: "Eag", model: "Model") -> None:
        """Inicializa o sub-objeto de visualização.

        Args:
            sm: Modelador estrutural proprietário.
            tqseag: Editor gráfico básico.
            model: Modelo estrutural.
        """
        self.m_sm       = sm
        self.m_tqseag   = tqseag
        self.m_model    = model

    def UpdateGeometry (self, tqsjan: "TQSJan.Window", floor: "Floor") -> None:
        """Refaz intersecções na planta e regera a tela.

        Args:
            tqsjan: Janela do EAG.
            floor: Planta atual.
        """
        # Recalcula intersecções entre elementos antes de regerar a tela
        floor.util.DoIntersections ()
        varpvistav      = ctypes.c_void_p (tqsjan.m_pvistav)
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        # Regera a vista atual para refletir a geometria atualizada
        self.m_sm.m_eagme.INTME_VIREGN (ctypes.byref (varpvistav), ctypes.byref (varfabrica))

    def GoToFloor (self, tqsjan: "TQSJan.Window", floor: "Floor", ipisoaux: int) -> None:
        """Leva o Modelador para a planta fornecida.

        Args:
            tqsjan: Janela do EAG.
            floor: Planta de destino.
            ipisoaux: Piso auxiliar (``0..auxiliaryFloors-1``) ou ``-1`` para ignorar.
        """
        varpvistav      = ctypes.c_void_p (tqsjan.m_pvistav)
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_sm.m_eagme.INTME_MUDARPLANTA (ctypes.byref (varpvistav), \
                            ctypes.byref (varfabrica), ctypes.byref (varipisoaux))
