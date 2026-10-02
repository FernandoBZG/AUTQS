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
#    TQSEag3d.py        Acesso à API do EAG3DBUILDER - Editor de objetos 3D
#                       Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING, Optional

from TQS import TQSUtil, TQSJan, TQSM3d

if TYPE_CHECKING:
    from TQS.TQSEag import Eag

#-----------------------------------------------------------------------------
#       Constantes de seleção
#
EAG3D_INORM:  int = 0             # Normal
EAG3D_IMULTP: int = 1             # Múltipla
#-----------------------------------------------------------------------------
#       Classe Eag3d - Interação com o N3DBUILDER.DLL
#
class Eag3d ():
    """Interface Python para o ``N3DBUILDER.DLL`` (Editor de objetos 3D).

    Encapsula handles de DLL e expõe sub-objetos :class:`Oper` (operações
    de edição) e :class:`Locate` (seleção/localização).

    Implementação:
        Os métodos das sub-classes são wrappers finos sobre funções C++ exportadas
        pelas DLLs ``EAGW.EXE``, ``N3DBUILDER.DLL``, ``EAGVISTA.DLL`` e ``MDWG.DLL``.
        O padrão recorrente é: (1) embrulhar ponteiros e ints/doubles em ``ctypes.c_*``;
        (2) chamar a função C++ através do handle de DLL apropriado; (3) ler de
        volta as saídas via ``.value`` em parâmetros passados por referência.
        Comentários inline são adicionados apenas onde a sequência foge desse padrão.

    Attributes:
        eag3dSingleton: Instância singleton do editor (compartilhada entre chamadas).
        m_eagdll: Handle de ``EAGW.EXE``.
        m_n3dbuilder: Handle de ``N3DBUILDER.DLL``.
        m_eagvista: Handle de ``EAGVISTA.DLL``.
        m_mdwg: Handle de ``MDWG.DLL``.
        m_tqseag: Editor gráfico básico TQS (:class:`TQSEag.Eag`).
        m_model3d: Modelo 3D ativo (:class:`TQSM3d.Model3D`) ou ``None``.
        oper: Sub-objeto de operações de edição.
        locate: Sub-objeto de seleção e localização.
    """

    eag3dSingleton: Optional["Eag3d"] = None       # Objeto Singleton

    def __init__ (self, tqseag: "Eag") -> None:
        """Inicializa o editor 3D carregando as DLLs e criando sub-objetos.

        Args:
            tqseag: Instância do editor gráfico básico TQS (:class:`TQSEag.Eag`).
        """
        self.m_eagdll   = TQSUtil.LoadDll ("EAGW.EXE")
        self.m_n3dbuilder=TQSUtil.LoadDll ("N3DBUILDER.DLL")
        self.m_eagvista = TQSUtil.LoadDll ("EAGVISTA.DLL")
        self.m_mdwg     = TQSUtil.LoadDll ("MDWG.DLL")

        self.m_tqseag   = tqseag
        self.m_model3d  = None

        self.oper       = Oper (self)
        self.locate     = Locate (self)

#
#    Objeto Singleton de acesso ao editor
#
    @classmethod
    def GetEag3d (self, tqseag: "Eag") -> "Eag3d":
        """Retorna a instância única :class:`Eag3d` do editor (Singleton).

        Use este método em vez de chamar ``Eag3d()`` diretamente para evitar
        alocar recursos redundantes.

        Args:
            tqseag: Editor gráfico básico TQS (:class:`TQSEag.Eag`).

        Returns:
            Instância singleton de :class:`Eag3d`.
        """
        if             self.eag3dSingleton is None:
            self.eag3dSingleton = Eag3d (tqseag)
        return         self.eag3dSingleton

#-----------------------------------------------------------------------------
#       Operações com objetos 3D
#
class Oper ():
    """Operações de edição em modelo 3D do EAG3DBUILDER.

    Use o par :meth:`Begin` / :meth:`End` para abrir uma sessão de edição:
    ``Begin`` devolve um :class:`TQSM3d.Model3D` editável que permanece
    válido até a chamada de ``End``.

    Attributes:
        m_eag3d: Editor 3D associado.
        m_tqsjan: Janela atual do editor (:class:`TQSJan.Window`) ou ``None``.
    """

    def __init__ (self, eag3d: "Eag3d") -> None:
        """Inicializa o sub-objeto de operações.

        Args:
            eag3d: Instância de :class:`Eag3d` proprietária.
        """
        self.m_eag3d    = eag3d
        self.m_tqsjan   = None

    def Begin (self, tqsjan: "TQSJan.Window") -> Optional[TQSM3d.Model3D]:
        """Inicia uma sessão de edição e devolve um modelo 3D editável.

        O objeto retornado permanece válido até a chamada de :meth:`End`.

        Args:
            tqsjan: Janela do EAG (:class:`TQSJan.Window`).

        Returns:
            Modelo espacial editável (:class:`TQSM3d.Model3D`), ou ``None`` se
            uma sessão anterior não foi finalizada com :meth:`End`.
        """
        self.m_tqsjan   = tqsjan
        # Begin/End são re-entrantes: rejeita um Begin() sem End() prévio
        if              (self.m_eag3d.m_model3d != None):
            self.m_eag3d.m_tqseag.Print ("ERRO: Begin() foi chamado sem End() anterior");
            return      None
        # Cria um modelo 3D Python e copia o ponteiro CDxIo do N3DBUILDER para dentro dele,
        # de modo que mutações no modelo refletem no editor até a chamada de End().
        self.m_eag3d.m_model3d  = TQSM3d.Model3D ()
        parpvistav      = ctypes.c_void_p (self.m_tqsjan.m_pvistav)
        pardxiomem      = ctypes.c_void_p (self.m_eag3d.m_model3d.m_dxiomem)
        self.m_eag3d.m_n3dbuilder.EAG3D_GET_CDXIO (parpvistav, pardxiomem)
        return          self.m_eag3d.m_model3d

    def End (self) -> None:
        """Finaliza a sessão iniciada em :meth:`Begin`.

        Marca o modelo como modificado, devolve-o ao N3DBUILDER e libera o
        objeto :class:`TQSM3d.Model3D` corrente.
        """
        if              (self.m_eag3d.m_model3d == None):
            self.m_eag3d.m_tqseag.Print ("ERRO: End() foi chamado sem Begin() anterior");
            return
        # Marca o CDxIo como modificado para que o N3DBUILDER persista as alterações
        ismodif         = 1
        parismodif      = ctypes.c_int (ismodif)
        pardxiomem      = ctypes.c_void_p (self.m_eag3d.m_model3d.m_dxiomem)
        self.m_eag3d.m_model3d.m_dxiodll.CDxIo_SetModified (pardxiomem, parismodif)
        # Devolve o CDxIo modificado ao editor 3D
        parpvistav      = ctypes.c_void_p (self.m_tqsjan.m_pvistav)
        self.m_eag3d.m_n3dbuilder.EAG3D_SET_CDXIO (parpvistav, pardxiomem)
        # Libera o modelo Python: subsequente Begin() poderá criar um novo
        del             self.m_eag3d.m_model3d
        self.m_eag3d.m_model3d = None

#-----------------------------------------------------------------------------
#       Locação de objetos 3D
#
class Locate ():
    """Seleção e localização interativa de objetos 3D.

    Attributes:
        m_eag3d: Editor 3D associado.
        m_tqsjan: Janela ativa para a operação corrente.
    """

    def __init__ (self, eag3d: "Eag3d") -> None:
        """Inicializa o sub-objeto de localização.

        Args:
            eag3d: Instância de :class:`Eag3d` proprietária.
        """
        self.m_eag3d    = eag3d
        self.m_tqsjan   = None

    def Select (self, tqsjan: "TQSJan.Window", msg: str, itploc: int) -> int:
        """Realiza seleção interativa de elementos 3D.

        Args:
            tqsjan: Janela do EAG (:class:`TQSJan.Window`).
            msg: Mensagem exibida ao usuário durante a seleção.
            itploc: Tipo de seleção. Use uma das constantes ``TQSEag3d.EAG3D_*``:
                :data:`EAG3D_INORM` (normal) ou :data:`EAG3D_IMULTP` (múltipla).

        Returns:
            Número de elementos selecionados.
        """
        self.m_tqsjan   = tqsjan
        self.m_eag3d.m_tqseag.msg.Print (msg)
        # Mapeia o tipo de seleção da API Python para o flag binário esperado pelo N3DBUILDER
        imultiplo       = 0
        if              (itploc == EAG3D_IMULTP):
            imultiplo   = 1
        parimultiplo    = ctypes.c_int (imultiplo)
        parpvistav      = ctypes.c_void_p (self.m_tqsjan.m_pvistav)
        # Bloqueia até o usuário concluir a seleção interativa
        self.m_eag3d.m_n3dbuilder.EAG3D_SELECTION_INTERACTIVE (parpvistav, parimultiplo)
        # Lê quantos elementos foram selecionados
        numselec        = 0
        parnumselec     = ctypes.c_int (numselec)
        self.m_eag3d.m_n3dbuilder.EAG3D_GET_SELECTION_SIZE (parpvistav, ctypes.byref (parnumselec))
        numselec        = parnumselec.value
        # Pre-aquece a estrutura de busca CDxIoMem para que GetSelection() seja rápido
        pardxiomem      = ctypes.c_void_p (self.m_eag3d.m_model3d.m_dxiomem)
        self.m_eag3d.m_model3d.m_dxiodll.CDxIoMem_PrepareForSearch (pardxiomem);
        return          numselec

    def GetSelection (self, isel: int) -> Optional[object]:
        """Retorna o objeto 3D selecionado de índice ``isel``.

        Deve ser chamado após :meth:`Select`. Reconstrói o identificador
        ``CDxIdent`` a partir dos quatro ints do N3DBUILDER e localiza o
        objeto no modelo.

        Args:
            isel: Índice da seleção (``0..Select()-1``).

        ATENÇÃO: três problemas nesta rotina na biblioteca TQS. (1)
        ``CDxIoMem_PrepareForSearch`` recebe ``pardxobj``, um ponteiro nulo, em vez
        de ``pardxiomem`` — o estado de busca do modelo não é preparado, embora a
        busca seguinte use ``pardxiomem`` corretamente. (2) O teste
        ``if pardxobj == None`` compara o wrapper ctypes, nunca ``None``, então o
        caminho "não encontrado" jamais é tomado e um ponteiro nulo segue para a
        conversão. (3) ``base.AttribIdent`` recebe o próprio ``Model3D`` como
        primeiro argumento posicional (``ident1``). Valide o retorno antes de usá-lo.

        Returns:
            Objeto 3D (``_Elem3D``) localizado — ver ATENÇÃO quanto ao caso
            "não encontrado".
        """
        parpvistav      = ctypes.c_void_p (self.m_tqsjan.m_pvistav)
        parisel         = ctypes.c_int (isel)
        # Identidade de objeto 3D no TQS é uma quádrupla de inteiros
        id1             = 0
        parid1          = ctypes.c_int (id1)
        id2             = 0
        parid2          = ctypes.c_int (id2)
        id3             = 0
        parid3          = ctypes.c_int (id3)
        id4             = 0
        parid4          = ctypes.c_int (id4)
        # Lê os 4 ints da seleção no índice ``isel``
        self.m_eag3d.m_n3dbuilder.EAG3D_GET_SELECTION_ID (parpvistav, parisel, \
                ctypes.byref (parid1), ctypes.byref (parid2), ctypes.byref (parid3), \
                ctypes.byref (parid4))
        # Constrói uma instância CDxIdent a partir da quádrupla; será usada como chave de busca
        dxident         = None
        pardxident      = ctypes.c_void_p (dxident)
        self.m_eag3d.m_model3d.m_dxiodll.CDxIdent_Create (parid1, parid2, parid3, parid4, \
                            ctypes.byref (pardxident))
        dxident         = pardxident.value
        atribident      = self.m_eag3d.m_model3d.base.AttribIdent ( \
                                self.m_eag3d.m_model3d, dxobj=dxident)
        # Localiza o objeto correspondente dentro do CDxIoMem do modelo
        dxobj           = None
        pardxobj        = ctypes.c_void_p (dxobj)
        self.m_eag3d.m_model3d.m_dxiodll.CDxIoMem_PrepareForSearch (pardxobj)
        pardxiomem      = ctypes.c_void_p (self.m_eag3d.m_model3d.m_dxiomem)
        self.m_eag3d.m_model3d.m_dxiodll.CDxIoMem_SearchIdent (pardxiomem, pardxident, \
                                                               ctypes.byref (pardxobj))
        if              (pardxobj == None):
            return      None
        # Converte o ponteiro ``dxobj`` para uma instância _Elem3D de Python
        dxobj           = pardxobj.value
        elem3d          = self.m_eag3d.m_model3d.iterator._ConvertDxobj (dxobj)
        # Libera o CDxIdent alocado: o objeto Python carrega seu próprio identificador
        self.m_eag3d.m_model3d.m_dxiodll.CDxIdent_Delete (pardxident)
        return          elem3d

    def AddSelection (self, elem3d: object) -> None:
        """Adiciona um elemento à seleção corrente.

        Args:
            elem3d: Objeto 3D (``_Elem3D``) a adicionar à seleção atual.
        """
        parpvistav      = ctypes.c_void_p (self.m_tqsjan.m_pvistav)
        atrib           = elem3d.attrib
        attribident     = atrib.attribIdent
        parid1          = ctypes.c_int (attribident.ident1)
        parid2          = ctypes.c_int (attribident.ident2)
        parid3          = ctypes.c_int (attribident.ident3)
        parid4          = ctypes.c_int (attribident.ident4)
        self.m_eag3d.m_n3dbuilder.EAG3D_SELECTION_ADD (parpvistav, parid1, parid2, parid3, parid4)

    def ClearSelection (self) -> None:
        """Limpa a seleção atual."""
        parpvistav      = ctypes.c_void_p (self.m_tqsjan.m_pvistav)
        self.m_eag3d.m_n3dbuilder.EAG3D_SELECTION_CLEAR (parpvistav);
