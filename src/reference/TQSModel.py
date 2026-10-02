# coding: utf-8
# Copyright (C) 1986-2025 TQS Informatica Ltda
#
#  This software is provided 'as-is', without any express or implied
#  warranty.  In no event will the authors be held liable for any damages
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
#       TQSMoldel.py    06-12-2023 Leitura e gravação de modelo estrutural
#                       Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes, os
from TQS import TQSUtil, TQSBuild, TQSJan
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

if TYPE_CHECKING:
    from TQS.TQSJan import Window


#-----------------------------------------------------------------------------
#      Lista tipos de objetos do Modelador
#
TYPE_INDEF:                   int = -1  # Indefinido
TYPE_VIGAS:                   int =  0  # Vigas
TYPE_PILARES:                 int =  1  # Pilares
TYPE_LAJES:                   int =  2  # Lajes
TYPE_FUNDAC:                  int =  3  # Fundações
TYPE_FUROS:                   int =  4  # Furos
TYPE_CAPITEIS:                int =  5  # Capiteis
TYPE_FORNER:                  int =  6  # Formas de lajes nervuradas
TYPE_CTRAUX:                  int =  7  # Contorno auxiliar
TYPE_EIXOS:                   int =  8  # Eixos rotulados
TYPE_COTAGENS:                int =  9  # Cotagens
TYPE_CORTES:                  int = 10  # Cortes
TYPE_DADPAV:                  int = 11  # Dados comuns do pavimento
TYPE_DADEDI:                  int = 12  # Dados comuns do edificio
TYPE_SECPIL:                  int = 13  # Secoes de pilares
TYPE_LISMAL:                  int = 14  # Lista de malhas de lajes
TYPE_CARCON:                  int = 15  # Cargas concentradas
TYPE_CARLIN:                  int = 16  # Cargas distribuidas lineares
TYPE_CARARE:                  int = 17  # Carga distribuída por área
TYPE_BARICEN:                 int = 18  # Tabela de baricentros de pil
TYPE_CARADI:                  int = 19  # Carga adicional em laje
TYPE_RAMPAS:                  int = 20  # TIPO FALSO: laje inclinada
TYPE_ORIEIX:                  int = 21  # Origem do sistema de eixos
TYPE_TABNP:                   int = 22  # Tabela de seções não padrão
TYPE_IDCLI:                   int = 23  # Identificação do cliente
TYPE_CONSBIB:                 int = 24  # Biblioteca de consolos
TYPE_FUROVIG:                 int = 25  # Furo em viga
TYPE_ELMLJP:                  int = 26  # Elemento de laje pré-moldada
TYPE_TABELEM:                 int = 27  # Tabela c/lista de elementos
TYPE_COTDIA:                  int = 28  # Cotagem de raio/diâmetro
TYPE_COTANG:                  int = 29  # Cotagem angular
TYPE_COTNOT:                  int = 30  # Cotagem de notas
TYPE_VENDST:                  int = 31  # Tabela de distribuição de vento
TYPE_CENTOR:                  int = 32  # Centro de torção Túnel de vento
TYPE_CONSIND:                 int = 33  # Consolos Independentes
TYPE_CAREMP:                  int = 34  # Cargas de empuxo
TYPE_TABNIVPAV:               int = 35  # Tabela de níveis de pavimentos
TYPE_LEGDESNIV:               int = 36  # Tabela de legenda de desníveis
TYPE_SIMDESNIV:               int = 37  # Símbolo de desnível de pav
TYPE_ELM3D:                   int = 38  # Elemento 3D
TYPE_INSRBLO:                 int = 39  # Inserto (de biblioteca)
TYPE_INSRPOS:                 int = 40  # Inserto (inserção)
TYPE_FACHADA:                 int = 41  # Fachada de painél pré-moldado
TYPE_TUBOS:                   int = 42  # Tubos de instalações
TYPE_FUROPIL:                 int = 43  # Furo em pilar
TYPE_LAJESSOVOL:              int = 44  # Container CLajes somente volume
TYPE_ESTACRAD:                int = 45  # Estaca sob Radier
TYPE_VIGASINC:                int = 46  # TIPO FALSO: viga inclinada
TYPE_PILARETES:               int = 47  # TIPO FALSO: pilaretes
TYPE_ESCADAS:                 int = 48  # TIPO FALSO: escada
TYPE_PATAMARES:               int = 49  # TIPO FALSO: patamar
TYPE_ORIBARI:                 int = 50  # Origem de baricentros
TYPE_EDIEDI:                  int = 51  # Dados do edifício (mesmo que ACESSOL)
TYPE_PTBAS:                   int = 52  # Ponto base do projeto
TYPE_PTLVT:                   int = 53  # Ponto de levantamento topográfico
TYPE_CERCATOR:                int = 54  # Cerca de torre (separa torre e periferia)
TYPE_CARTRM:                  int = 55  # Trem tipo
TYPE_LEGCORCAR:               int = 56  # Legenda de cores de cargas
#------------------------------------------------------------------------------
#      Modos de visualização (VisModes)
#
VISMODE_MATUAL:               int = 0  # Modo de visualização atual
VISMODE_FORMAS:               int = 1  # Desenho de formas FORnnnn.DWG
VISMODE_VERIFI:               int = 2  # Modo de verificação
VISMODE_MODELO:               int = 3  # Desenho MODELO.DWG
VISMODE_GRUPOA:               int = 4  # Grupo A de visualização do usuário
VISMODE_GRUPOB:               int = 5  # Grupo B de visualização do usuário
#------------------------------------------------------------------------------
#      Dados gloais de pilares e fundações
#
COLUMNDATA_PILARS:            int = 0  # Dados de pilares
COLUMNDATA_FUNDAC:            int = 1  # Dados de fundações
COLUMNDATA_PILRTE:            int = 2  # Dados de pilaretes
#------------------------------------------------------------------------------
#      Tipo de carga dos dados atuais
#
TPLOAD_CARVIG:                int =  0 # Carga linear para toda a viga
TPLOAD_CARLAJ:                int =  1 # Carga distribuída para toda a laje
TPLOAD_FORCFX:                int =  2 # Forca concentrada X
TPLOAD_FORCFY:                int =  3 # Forca concentrada Y
TPLOAD_FORCFZ:                int =  4 # Forca concentrada Z
TPLOAD_FORCMX:                int =  5 # Momento concentrado X
TPLOAD_FORCMY:                int =  6 # Momento concentrado Y
TPLOAD_CMVCFX:                int =  7 # Carga móvel: Forca concentrada   X
TPLOAD_CMVCFY:                int =  8 # Carga móvel: Forca concentrada   Y
TPLOAD_CMVCFZ:                int =  9 # Carga móvel: Forca concentrada   Z
TPLOAD_CMVCMX:                int = 10 # Carga móvel: Momento concentrado X
TPLOAD_CMVCMY:                int = 11 # Carga móvel: Momento concentrado Y
TPLOAD_CARLIN:                int = 12 # Carga distribuída linear
TPLOAD_CARARE:                int = 13 # Carga distribuída por área
TPLOAD_CARADI:                int = 14 # Carga adicional em laje
#
#      Tipo de uma carga
#
LOADTYPE_DISARE:               int = 0  # Distribuída por area
LOADTYPE_DISLIN:               int = 1  # Distribuída linear
LOADTYPE_CONCEN:               int = 2  # Concentrada
LOADTYPE_MOMCON:               int = 3  # Momento concentrado
#-----------------------------------------------------------------------------
#       Como o pilar nasce
#
COLUMNSTART_NASCEDIRT:        int = 0  # Nasce no solo/fundação do próprio pilar — opção "Vinculado na fundação / solo" do Modelador (sem elemento de apoio definido)
COLUMNSTART_NASCEVIGA:        int = 1  # Nasce em viga — opção "Em viga" do Modelador
COLUMNSTART_NASCEPIFU:        int = 2  # Nasce apoiado em outro pilar ou elemento de fundação existente — opção "Em pilar/bloco/sapata/tubulão" do Modelador
COLUMNSTART_NASCELAJE:        int = 3  # Nasce em laje — opção "Sobre laje" do Modelador
#------------------------------------------------------------------------------
#      Tipo de uso do pilar: compressão ou tração
#
COLUMNUSE_COMPRESSAO:         int = 0  # Padrão - forças de compressão
COLUMNUSE_TRACAO:             int = 1  # Principalmente tração, pode compressão
COLUMNUSE_COMPAT:             int = 2  # Pilar de compatibilização
COLUMNUSE_ESCORA:             int = 3  # Escora (só compressão)
COLUMNUSE_TIRANTE:            int = 4  # Tirante (só tração)
#------------------------------------------------------------------------------
#       Definição de molas de pilares no pórtico
#
COLUMNCOIL_IRES_IRX:          int = 0  # Rotação X
COLUMNCOIL_IRES_IRY:          int = 1  # Rotação Y
COLUMNCOIL_IRES_IRZ:          int = 2  # Rotação Z
COLUMNCOIL_IRES_ITX:          int = 3  # Translação X
COLUMNCOIL_IRES_ITY:          int = 4  # Translação Y
COLUMNCOIL_IRES_ITZ:          int = 5  # Translação Z
#
#       Tipo de engaste
#
COLUMNCOIL_IAPOPOR_DEFAULT:    int = 0  # Engaste ou padrão
COLUMNCOIL_IAPOPOR_ARTICULADO: int = 1  # Articulado
COLUMNCOIL_IAPOPOR_ELASTICO:   int = 2  # Elástico
COLUMNCOIL_IAPOPOR_RECALQUE:   int = 3  # Recalque
#
#       Gap de restrição de apoio
#
COLUMNCOIL_IGAP_XPOS:          int = 0  # Gap Tx+
COLUMNCOIL_IGAP_XNEG:          int = 1  # Gap Tx-
COLUMNCOIL_IGAP_YPOS:          int = 2  # Gap Ty+
COLUMNCOIL_IGAP_YNEG:          int = 3  # Gap Ty-
COLUMNCOIL_IGAP_ZPOS:          int = 4  # Gap Tz+
COLUMNCOIL_IGAP_ZNEG:          int = 5  # Gap Tz-
#
#       Tipos de seção de pilar
#
COLUMNTYPE_R:                  int = 0  # Seção Retangular
COLUMNTYPE_L:                  int = 1  # Seção L
COLUMNTYPE_U:                  int = 2  # Seção U
COLUMNTYPE_C:                  int = 3  # Seção Circular
COLUMNTYPE_P:                  int = 4  # Seção Poligonal
COLUMNTYPE_N:                  int = 5  # Seção Outras não padrão
#
#       Condições de contorno de grelha
#
COLUMNBEARING_DEFAULT:         int = 0  # Default
COLUMNBEARING_ARTCONT:         int = 1  # Articulado contínuo
COLUMNBEARING_ARTINDP:         int = 2  # Articulado independente
COLUMNBEARING_ELACONT:         int = 3  # Elástico continuo
COLUMNBEARING_ELAINDP:         int = 4  # Elástico independente
#
#       Coeficientes de mola na grelha
#
COLUMNSPRING_IRX:              int = 0  # Rx
COLUMNSPRING_IRY:              int = 1  # Ry
COLUMNSPRING_ITZ:              int = 2  # Tz
COLUMNSPRING_ITX:              int = 3  # Tx
COLUMNSPRING_ITY:              int = 4  # Ty

#------------------------------------------------------------------------------
#       Fundações
#
FOUNDATION_ITIPOFUNDAC_SAPATA: int = 0  # Sapata
FOUNDATION_ITIPOFUNDAC_BLOCO:  int = 1  # Bloco sobre estacas
FOUNDATION_ITIPOFUNDAC_TUBULAO: int = 2  # Tubulão
#
#      Dados de cálice
#
FOUNDATION_FORM_RETANGULAR:    int = 0  # Cálice: Formato retangular
FOUNDATION_FORM_CIRCULAR:      int = 1  # Cálice: Formato circular
#
#       Rugosidade do cálice
#
FOUNDATION_RUGO_PADRAO:        int = 0  # Cálice: Rugosidade conforme critérios
FOUNDATION_RUGO_SULISA:        int = 1  # Cálice: Superfície lisa
FOUNDATION_RUGO_RUGOSA:        int = 2  # Cálice: Superfíce rugosa, pilar também
FOUNDATION_RUGO_CHAVECIS:      int = 3  # Cálice: Chave de cisalhamento
#------------------------------------------------------------------------------
#      Atributos BIM do usuário - estrutura global
#
BIM_USRATRTP_PILAR:            int = 0  # Pilar
BIM_USRATRTP_FUNDC:            int = 1  # Fundações
BIM_USRATRTP_VIGAS:            int = 2  # Vigas
BIM_USRATRTP_LAJES:            int = 3  # Lajes
BIM_USRATRTP_ELM3D:            int = 4  # Elementos 3D
#
#       Atributos BIM globais
#
BIM_GLBA_GLOBAL:               int = 0  # Todos do edifício
BIM_GLBA_PLANTA:               int = 1  # Todos de uma planta
BIM_GLBA_UMPISO:               int = 2  # Todos de um piso
#------------------------------------------------------------------------------
#      Tipos de cruzamento de vigas
#
BEAMCROSSING_INDEFINIDO:       int = 0  # Indefinido
BEAMCROSSING_RECEBE:           int = 1  # Recebe carga
BEAMCROSSING_CRUZAMENTO:       int = 2  # Cruzamento sem apoio identificado
BEAMCROSSING_APOIAVIGA:        int = 3  # Apoia em viga
BEAMCROSSING_APOIAPILAR:       int = 4  # Apoia em pilar
BEAMCROSSING_N:                int = 5  # Neutro
#------------------------------------------------------------------------------
#      Vinculação de viga com laje
#
BEAMCONNECTION_DEFAULT:        int = 0  # Default
BEAMCONNECTION_ENLIVRE:        int = 1  # Livre
BEAMCONNECTION_ARTCMXY:        int = 2  # Articulado mx,my
BEAMCONNECTION_ARTMXYF:        int = 3  # Articulado mx,my,fx
BEAMCONNECTION_FATEMGS:        int = 4  # Engastado com fatengast
#------------------------------------------------------------------------------
#      Furo em viga
#
BEAMOPENINGREFERENCE_TOPO:     int = 0  # Rebaixo em relação ao topo
BEAMOPENINGREFERENCE_EIXO:     int = 1  # Rebaixo em relação ao eixo
BEAMOPENINGREFERENCE_BASE:     int = 2  # Rebaixo em relação à base
#------------------------------------------------------------------------------
#      Tipos de laje
#
SLABTYPE_MACICA:                int = 0  # Maciça
SLABTYPE_NERVUR:                int = 1  # Nervurada retangular
SLABTYPE_NERVUT:                int = 2  # Nervurada trapezoidal
SLABTYPE_VIGOTA:                int = 3  # Vigotas treliçadas
SLABTYPE_TRELIC:                int = 4  # Treliçada
SLABTYPE_PREFAB:                int = 5  # Pré-fabricada
SLABTYPE_MISNER:                int = 6  # Mista nervurada (ex: TUPER)
#------------------------------------------------------------------------------
#       Modelo estrutural
#
class Model ():
    """Modelo estrutural TQS.

    Implementação:
        Hub central da API: carrega ``EAGME.DLL`` (modo interativo, com janela) ou
        ``FINTME.DLL`` (modo batch, sem janela) e instancia os sub-objetos de acesso
        aos dados globais, plantas e tipos de objeto. Todos os demais wrappers desta
        biblioteca recebem este objeto e usam ``self.m_eagme`` para chamar funções C++.
    """

    def __init__ (self, tqsjan: Optional["Window"] = None) -> None:
        """Modelo estrutural.

        Args:
            tqsjan: Parâmetro ``tqsjan``.
        """
        # Sem janela TQSJan: roda em modo batch (FINTME.DLL); com janela: modo interativo (EAGME.DLL)
        if              (tqsjan == None):
            self.m_eagme= TQSUtil.LoadDll ("FINTME.DLL")
        else:
            self.m_eagme= TQSUtil.LoadDll ("EAGME.DLL")
        # Sub-objetos de acesso aos dados globais e plantas; todos compartilham self.m_eagme
        self.file       = File (self)
        self.type       = Type (self)
        self.floors     = FloorsList (self)
        self.current    = CurGlobalData (self)
        self.visData    = VisData (self)
        self.m_tqsjan   = tqsjan

#        dllmetalcheck   = "C:\\TQSWV26\\TQSW\\EXEC\\X64\\FMETALCHECK.DLL"
#        import clr
#        clr.AddReference (dllmetalcheck)

    def __str__ (self) -> str:
        """Operação ``__str__``.

        Returns:
            Cadeia de caracteres.
        """
        msg             = "TQSModel"
        msg             += "\n   self.m_eagme      " + str (self.m_eagme)
        msg             += "\n   self.file         " + str (self.file)
        msg             += "\n   self.type         " + str (self.type)
        msg             += "\n   self.floorslist   " + str (self.floors)
        msg             += "\n   self.current      " + str (self.current)
        msg             += "\n   self.m_tqsjan     " + str (self.m_tqsjan)
        return          msg

#------------------------------------------------------------------------------
#       Lista dos tipos de objeto do Modelador
#
class Type ():

    """Tipos de objetos do Modelador.

    Implementação:
        Tabela de classes/descrições do Modelador. ``GetTypeClass`` e ``GetTypeDescription``
        lêem o mesmo registro em C++ (``BASME_PLANTA_NOMELISTA``) decodificando campos
        distintos (nome de classe vs. descrição do objeto).
    """
    def __init__ (self, model: "Model") -> None:
        """Inicialização de objeto do Modelador.

        Args:
            model: Modelo estrutural (:class:`Model`).
        """
        self.m_model    = model

    def GetNumTypes (self) -> int:
        """Retorna num types.

        Returns:
            Valor inteiro.
        """
        numlistas       = 0
        varnumlistas    = ctypes.c_int (numlistas)
        self.m_model.m_eagme.BASME_PLANTA_NUMLISTAS (ctypes.byref (varnumlistas))
        numlistas       = varnumlistas.value
        return          numlistas

    def GetTypeClass (self, itype: int) -> str:
        """itype.

        Args:
            itype: TYPE_xxxx.

        Returns:
            itype       <- (int) TYPE_xxxx.
        """
        varitype        = ctypes.c_int (itype)
        varnomeclasse   = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        varnomeobjeto   = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        argfan          = ctypes.c_int (0)
        # Mesma chamada lê dois campos: aqui retornamos só o nome de classe (varnomeclasse)
        self.m_model.m_eagme.BASME_PLANTA_NOMELISTA (ctypes.byref (varitype),
                        varnomeclasse, argfan, varnomeobjeto, argfan)
        nomeclasse      = varnomeclasse.value.decode(TQSUtil.CHARSET)
        return         nomeclasse

    def GetTypeDescription (self, itype: int) -> str:
        """itype.

        Args:
            itype: TYPE_xxxx.

        Returns:
            itype       <- (int) TYPE_xxxx.
        """
        varitype        = ctypes.c_int (itype)
        varnomeclasse   = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        varnomeobjeto   = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        argfan          = ctypes.c_int (0)
        self.m_model.m_eagme.BASME_PLANTA_NOMELISTA (ctypes.byref (varitype),
                        varnomeclasse, argfan, varnomeobjeto, argfan)
        nomeobjeto      = varnomeobjeto.value.decode(TQSUtil.CHARSET)
        return         nomeobjeto

#------------------------------------------------------------------------------
#       Operações de leitura e gravação do modelo
#
class File ():

    """Operações de leitura/gravação do modelo.

    Implementação:
        Operações de arquivo do modelo (``INTME_*``). ``Save`` propaga o ponteiro da
        janela quando o modelo foi aberto em modo interativo (com ``TQSJan.Window``).
    """
    def __init__ (self, model: "Model") -> None:
        """Inicialização da classe de arquivos.

        Args:
            model: Modelo estrutural (:class:`Model`).
        """
        self.m_model    = model

    def OpenModel (self) -> int:
        """Abre modelo existente ou cria novo.

        Returns:
            Valor inteiro.
        """
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.INTME_ABRIRMODELOESP (ctypes.byref (varistat))
        istat           = varistat.value
        return          istat

    def OpenNewModel (self) -> int:
        """Abre modelo novo, apaga velho se já existir.

        Returns:
            Valor inteiro.
        """
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.INTME_ABRIRMODELONOVOESP (ctypes.byref (varistat))
        istat           = varistat.value
        return          istat

    def Save (self) -> int:
        """Salva o modelo estrutural.

        Returns:
            Valor inteiro.
        """
        # Em modo interativo, propaga o ponteiro da janela para que a DLL atualize a vista
        pvistav         = None
        if              (self.m_model.m_tqsjan != None):
            pvistav     = self.m_model.m_tqsjan.m_pvistav
        varpvistav      = ctypes.c_void_p (pvistav)
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.INTME_SALVARMODELO (ctypes.byref (varpvistav),
                            ctypes.byref (varistat))
        istat           = varistat.value
        return          istat

    def Close (self) -> None:
        """Fecha modelo estrutural aberto.
        """
        self.m_model.m_eagme.INTME_FECHARMODELOESP ()

#-----------------------------------------------------------------------------
#       Dados globais, usados como modelo para a criação de objetos novos
#
class CurGlobalData ():

    """Dados globais usados na criação de novos objetos.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais, que são usados na criação de objetos novos.

        Subdividido em objetos:
        globalAxisData       Dados de eixos automáticos
        globalCutData        Dados de cortes
        globalSoilpress      Carregamento de empuxo
        globalRefxData       Critérios de referências externas
        globalBeamData       Dados de vigas
        globalSlabData       Dados de lajes, rampas e escadas
        globalColumnData     Dados de pilares e fundações
        globalColumnOpening  Furo em pilar
        globalPrecast        Dados de pré-moldados
        globalBimData        Dados de BIM

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model          = model

        self.globalAxisData   = GlobalAxisData (model)
        self.globalCutData    = GlobalCutData (model)
        self.globalSoilpress  = GlobalSoilPressureData (model)
        self.globalRefxData   = GlobalRefxData (model)
        self.globalBeamData   = GlobalBeamData (model)
        self.globalSlabData   = GlobalSlabData (model)
        self.globalColumnData = GlobalColumnData (model)
        self.globalColumnOpening= GlobalColumnOpening (model)
        self.globalSlabFPile  = GlobalSlabFoundationPile (model)
        self.globalPrecast    = GlobalPrecastData (model)
        self.globalBimData    = GlobalBimData (model)
#
#       Dados globais de Eixos - CurGlobalData.globalAxisData
#
class GlobalAxisData ():

    """Dados globais de eixos automáticos.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais de eixos.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    @property
    def axis (self) -> "AutoAxis":
        """Operação ``axis``.

        Returns:
            :class:`AutoAxis` correspondente.
        """
        eixaut          = None
        vareixaut       = ctypes.c_void_p (eixaut)
        self.m_model.m_eagme.BASME_DADEDI_EIXAUT_LER (ctypes.byref (vareixaut))
        eixaut          = vareixaut.value
        autoaxis        = AutoAxis (self.m_model, eixaut)
        return          autoaxis

    @property
    def spaceAxis (self) -> int:
        """Eixos (0) somente planta atual (1) definidos para todas as plantas.

        Returns:
            Valor inteiro.
        """
        ieixosespac     = 0
        varieixosespac  = ctypes.c_int (ieixosespac)
        self.m_model.m_eagme.BASME_DADEDI_IEIXOSESPAC_LER (ctypes.byref (varieixosespac))
        ieixosespac     = varieixosespac.value
        return          ieixosespac

    @spaceAxis.setter
    def spaceAxis (self, ieixosespac: int) -> None:
        """Atribui Eixos (0) somente planta atual (1) definidos para todas as plantas."""
        varieixosespac  = ctypes.c_int (ieixosespac)
        self.m_model.m_eagme.BASME_DADEDI_IEIXOSESPAC_DEF (ctypes.byref (varieixosespac))
#
#      Cortes - CurGlobalData.globalCutData
#
class GlobalCutData ():

    """Dados globais de cortes.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais de cortes.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    @property
    def sectionType (self) -> int:
        """Corte (0)rebatido (1)profundidade (2)global.

        Returns:
            Valor inteiro.
        """
        iprofundcor     = 0
        variprofundcor  = ctypes.c_int (iprofundcor)
        self.m_model.m_eagme.BASME_DADEDI_IPROFUNDCOR_LER (ctypes.byref (variprofundcor))
        iprofundcor     = variprofundcor.value
        return          iprofundcor

    @sectionType.setter
    def sectionType (self, iprofundcor: int) -> None:
        """Atribui Corte (0)rebatido (1)profundidade (2)global."""
        variprofundcor  = ctypes.c_int (iprofundcor)
        self.m_model.m_eagme.BASME_DADEDI_IPROFUNDCOR_DEF (ctypes.byref (variprofundcor))

    @property
    def sectionElevationAngle (self) -> float:
        """Cortes: Ângulo de elevação, graus.

        Returns:
            Valor de ponto flutuante.
        """
        angelev         = 0.
        varangelev      = ctypes.c_double (angelev)
        self.m_model.m_eagme.BASME_DADEDI_ANGELEV_LER (ctypes.byref (varangelev))
        angelev         = varangelev.value
        return          angelev

    @sectionElevationAngle.setter
    def sectionElevationAngle (self, angelev: float) -> None:
        """Atribui Ângulo de elevação, graus."""
        varangelev      = ctypes.c_double (angelev)
        self.m_model.m_eagme.BASME_DADEDI_ANGELEV_DEF (ctypes.byref (varangelev))

    @property
    def sectionDeviationAngle (self) -> float:
        """Cortes: Ângulo de desvio, graus.

        Returns:
            Valor de ponto flutuante.
        """
        angdesv         = 0.
        varangdesv      = ctypes.c_double (angdesv)
        self.m_model.m_eagme.BASME_DADEDI_ANGDESV_LER (ctypes.byref (varangdesv))
        angdesv         = varangdesv.value
        return          angdesv

    @sectionDeviationAngle.setter
    def sectionDeviationAngle (self, angdesv: float) -> None:
        """Atribui Ângulo de desvio, graus."""
        varangdesv      = ctypes.c_double (angdesv)
        self.m_model.m_eagme.BASME_DADEDI_ANGDESV_DEF (ctypes.byref (varangdesv))

    @property
    def sectionHatch (self) -> int:
        """Cortes: Hachurar o resultado.

        Returns:
            Valor inteiro.
        """
        ihachurar       = 0
        varihachurar    = ctypes.c_int (ihachurar)
        self.m_model.m_eagme.BASME_DADEDI_IHACHURAR_LER (ctypes.byref (varihachurar))
        ihachurar       = varihachurar.value
        return          ihachurar

    @sectionHatch.setter
    def sectionHatch (self, ihachurar: int) -> None:
        """Atribui Hachurar o resultado."""
        varihachurar      = ctypes.c_int (ihachurar)
        self.m_model.m_eagme.BASME_DADEDI_IHACHURAR_DEF (ctypes.byref (varihachurar))

    @property
    def sectionLabel (self) -> int:
        """Cortes: (1) p/rotular cortes.

        Returns:
            Valor inteiro.
        """
        irotular        = 0
        varirotular     = ctypes.c_int (irotular)
        self.m_model.m_eagme.BASME_DADEDI_IROTULAR_LER (ctypes.byref (varirotular))
        irotular       = varirotular.value
        return          irotular

    @sectionLabel.setter
    def sectionLabel (self, irotular: int) -> None:
        """Atribui (1) p/rotular cortes."""
        varirotular      = ctypes.c_int (irotular)
        self.m_model.m_eagme.BASME_DADEDI_IROTULAR_DEF (ctypes.byref (varirotular))

    @property
    def section3DViewl (self) -> int:
        """Cortes: (1) Cortar na visualização 3D.

        Returns:
            Valor inteiro.
        """
        icortarv3d      = 0
        varicortarv3d   = ctypes.c_int (icortarv3d)
        self.m_model.m_eagme.BASME_DADEDI_ICORTARV3D_LER (ctypes.byref (varicortarv3d))
        icortarv3d       = varicortarv3d.value
        return          icortarv3d

    @section3DViewl.setter
    def section3DViewl (self, icortarv3d: int) -> None:
        """Atribui (1) Cortar na visualização 3D."""
        varicortarv3d      = ctypes.c_int (icortarv3d)
        self.m_model.m_eagme.BASME_DADEDI_ICORTARV3D_DEF (ctypes.byref (varicortarv3d))

    @property
    def sectionProject (self) -> int:
        """Cortes: (1) Projetar o corte.

        Returns:
            Valor inteiro.
        """
        iprojetar       = 0
        variprojetar    = ctypes.c_int (iprojetar)
        self.m_model.m_eagme.BASME_DADEDI_IPROJETAR_LER (ctypes.byref (variprojetar))
        iprojetar       = variprojetar.value
        return          iprojetar

    @sectionProject.setter
    def sectionProject (self, iprojetar: int) -> None:
        """Atribui (1) Projetar o corte."""
        variprojetar    = ctypes.c_int (iprojetar)
        self.m_model.m_eagme.BASME_DADEDI_IPROJETAR_DEF (ctypes.byref (variprojetar))
#
#      Carga de empuxo - CurGlobalData.globalSoilpress
#
class GlobalSoilPressureData ():

    """Dados globais de empuxo.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais de empuxo.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model      = model

    @property
    def soilPressureLoad (self) -> "SoilPressureLoad":
        """Carga de empuxo.

        Returns:
            :class:`SoilPressureLoad` correspondente.
        """
        caremp          = None
        varcaremp       = ctypes.c_void_p (caremp)
        self.m_model.m_eagme.BASME_DADEDI_CAREMP_LER (ctypes.byref (varcaremp))
        caremp          = varcaremp.value
        # Empuxo é sempre associado à primeira planta do edifício (fundação); abre-a se ainda não estiver no cache
        nomplafund      = self.m_model.floors.GetFloorName (1)
        floor           = self.m_model.floors.floors [nomplafund]
        if              (floor == None):
            floor       = Floor (self.m_model, nomplafund)
        soilpressure    = SoilPressureLoad (self.m_model, floor, caremp)
        return          soilpressure

#
#      Modos de visualização - model.visData
#
class VisData ():

    """Dados globais de visualização.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais de visualização.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    def GetVisModes (self, imode: int) -> "VisModes":
        """Objeto de modos de visualização.

        Args:
            imode: Aplicar modos em VISMODE_xxxx.

        Returns:
            Objeto VisModes() para controle de visualização.
        """
        varimode        = ctypes.c_int (imode)
        modvis          = None
        varmodvis       = ctypes.c_void_p (modvis)
        self.m_model.m_eagme.BASME_DADEDI_MODVIS_LER (ctypes.byref (varimode),
                          ctypes.byref (varmodvis))
        modvis          = varmodvis.value
        visModes        = VisModes (self.m_model, modvis)
        return          visModes
#
#      Critérios de referências externas - CurGlobalData.globalRefxData
#
class GlobalRefxData ():

    """Critérios de referências externas.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Critérios de referências externas.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    @property
    def externalReferenceColor (self) -> int:
        """(1) se referências devem usar cor original.

        Returns:
            Valor inteiro.
        """
        irefcorori      = 0
        varirefcorori   = ctypes.c_int (irefcorori)
        self.m_model.m_eagme.BASME_DADEDI_IREFCORORI_LER (ctypes.byref (varirefcorori))
        irefcorori      = varirefcorori.value
        return          irefcorori

    @externalReferenceColor.setter
    def externalReferenceColor (self, irefcorori: int) -> None:
        """Atribui (1) se referências devem usar cor original."""
        varirefcorori   = ctypes.c_int (irefcorori)
        self.m_model.m_eagme.BASME_DADEDI_IREFCORORI_DEF (ctypes.byref (varirefcorori))

#
#      Vigas - CurGlobalData.globalBeamData
#
class GlobalBeamData ():

    """Dados globais de vigas.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais de vigas.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    @property
    def beamRestraint (self) -> "BeamRestraint":
        """Objeto de Articulação de viga.

        Returns:
            :class:`BeamRestraint` correspondente.
        """
        artic           = None
        varartic        = ctypes.c_void_p (artic)
        self.m_model.m_eagme.BASME_DADEDI_ARTIC_LER (ctypes.byref (varartic))
        artic           = varartic.value
        beamRestraintx  = BeamRestraint (self.m_model, artic)
        return          beamRestraintx

    @property
    def firstSlopedBeamNumber (self) -> int:
        """Numero da primeira viga inclinada.

        Returns:
            Valor inteiro.
        """
        iprimvigainc    = 0
        variprimvigainc = ctypes.c_int (iprimvigainc)
        self.m_model.m_eagme.BASME_DADEDI_IPRIMVIGAINC_LER (ctypes.byref (variprimvigainc))
        iprimvigainc    = variprimvigainc.value
        return          iprimvigainc

    @firstSlopedBeamNumber.setter
    def firstSlopedBeamNumber (self, iprimvigainc: int) -> None:
        """Atribui Numero da primeira viga inclinada."""
        variprimvigainc   = ctypes.c_int (iprimvigainc)
        self.m_model.m_eagme.BASME_DADEDI_IPRIMVIGAINC_DEF (ctypes.byref (variprimvigainc))

    @property
    def slopedBeamIdent (self) -> "SMObjectIdent":
        """Identificação de viga inclinada.

        Returns:
            :class:`SMObjectIdent` correspondente.
        """
        identviginc     = None
        varidentviginc  = ctypes.c_void_p (identviginc)
        self.m_model.m_eagme.BASME_DADEDI_IDENTVIGINC_LER (ctypes.byref (varidentviginc))
        identviginc     = varidentviginc.value
        slopedbeamident = SMObjectIdent (self.m_model, identviginc)
        return          slopedbeamident
#
#	Lajes/escadas/rampas - CurGlobalData.globalSlabData
#
class GlobalSlabData ():

    """Dados globais de lajes/escadas/rampas.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais de Lajes/escadas/rampas.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    @property
    def stairCase (self) -> "StairCase":
        """Dados de escada.

        Returns:
            :class:`StairCase` correspondente.
        """
        escdad          = None
        varescdad       = ctypes.c_void_p (escdad)
        self.m_model.m_eagme.BASME_DADEDI_ESCADA_LER (ctypes.byref (varescdad))
        escdad          = varescdad.value
        staircasex      = StairCase (self.m_model, escdad)
        return          staircasex

    @property
    def firstRampNumber (self) -> int:
        """Número da primeira rampa.

        Returns:
            Valor inteiro.
        """
        iprimrampa      = 0
        variprimrampa   = ctypes.c_int (iprimrampa)
        self.m_model.m_eagme.BASME_DADEDI_IPRIMRAMPA_LER (ctypes.byref (variprimrampa))
        iprimrampa    = variprimrampa.value
        return          iprimrampa

    @firstRampNumber.setter
    def firstRampNumber (self, iprimrampa: int) -> None:
        """Atribui Número da primeira rampa."""
        variprimrampa   = ctypes.c_int (iprimrampa)
        self.m_model.m_eagme.BASME_DADEDI_IPRIMRAMPA_DEF (ctypes.byref (variprimrampa))

    @property
    def volumeOnlySlab (self) -> "VolumeOnlySlab":
        """Laje somente de volume.

        Returns:
            :class:`VolumeOnlySlab` correspondente.
        """
        lajsovol        = None
        varlajsovol     = ctypes.c_void_p (lajsovol)
        self.m_model.m_eagme.BASME_DADEDI_LAJSOVOL_LER (ctypes.byref (varlajsovol))
        lajsovol        = varlajsovol.value
        volumeonlyslab  = VolumeOnlySlab (self.m_model, lajsovol)
        return          volumeonlyslab

    @property
    def volumeOnlySlabIdent (self) -> "SMObjectIdent":
        """Identificador de laje somente de volume.

        Returns:
            :class:`SMObjectIdent` correspondente.
        """
        identrampa      = None
        varidentrampa   = ctypes.c_void_p (identrampa)
        self.m_model.m_eagme.BASME_DADEDI_IDENTRAMPA_LER (ctypes.byref (varidentrampa))
        identrampa      = varidentrampa.value
        volumeonlyslabident = SMObjectIdent (self.m_model, identrampa)
        return          volumeonlyslabident

#
#	Dados de pilares e fundações - CurGlobalData.globalColumnData
#
class GlobalColumnData ():

    """Dados globais de pilares e fundações.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais de eixos.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    def _GetColumnData (self, itipo: int) -> "ColumnData":
        """Dados para criação de pilares e fundações.

        Args:
            itipo: COLUMNDATA_xxxx.

        Returns:
            :class:`ColumnData` correspondente.
        """
        dadpil          = None
        varitipo        = ctypes.c_int (itipo)
        vardadpil       = ctypes.c_void_p (dadpil)
        self.m_model.m_eagme.BASME_DADEDI_DADPIL_LER (ctypes.byref (varitipo),
                            ctypes.byref (vardadpil))
        dadpil          = vardadpil.value
        columndata      = ColumnData (self.m_model, dadpil)
        return          columndata

    @property
    def columnData (self) -> Any:
        """Operação ``columnData``.

        Returns:
            Resultado da operação.
        """
        return          self._GetColumnData (COLUMNDATA_PILARS)

    @property
    def foundationColumnData (self) -> Any:
        """Operação ``foundationColumnData``.

        Returns:
            Resultado da operação.
        """
        return          self._GetColumnData (COLUMNDATA_FUNDAC)

    @property
    def shortColumnData (self) -> Any:
        """Operação ``shortColumnData``.

        Returns:
            Resultado da operação.
        """
        return          self._GetColumnData (COLUMNDATA_PILRTE)
#
#       Dados de fundação
#
    @property
    def foundationData (self) -> "FoundationData":
        """Dados de fundação.

        Returns:
            :class:`FoundationData` correspondente.
        """
        fundac          = None
        varfundac       = ctypes.c_void_p (fundac)
        self.m_model.m_eagme.BASME_DADEDI_FUNDAC_LER (ctypes.byref (varfundac))
        fundac          = varfundac.value
        foundationdata  = FoundationData (self.m_model, fundac)
        return          foundationdata

    @property
    def spreadFootingSideWalls (self) -> float:
        """Sapatas: Valor do colarinho cm.

        Returns:
            Valor de ponto flutuante.
        """
        sapcolar        = 0.
        varsapcolar     = ctypes.c_double (sapcolar)
        self.m_model.m_eagme.BASME_DADEDI_SAPCOLAR_LER (ctypes.byref (varsapcolar))
        sapcolar        = varsapcolar.value
        return          sapcolar

    @spreadFootingSideWalls.setter
    def spreadFootingSideWalls (self, sapcolar: float) -> None:
        """Atribui Valor do colarinho cm."""
        varsapcolar   = ctypes.c_double (sapcolar)
        self.m_model.m_eagme.BASME_DADEDI_SAPCOLAR_DEF (ctypes.byref (varsapcolar))

    @property
    def foundationsTopFaceRecess (self) -> float:
        """Fundações: Valor do rebaixo cm.

        Returns:
            Valor de ponto flutuante.
        """
        fixcotfunddfs   = 0.
        varfixcotfunddfs= ctypes.c_double (fixcotfunddfs)
        self.m_model.m_eagme.BASME_DADEDI_FIXCOTFUNDDFS_LER (ctypes.byref (varfixcotfunddfs))
        fixcotfunddfs   = varfixcotfunddfs.value
        return          fixcotfunddfs

    @foundationsTopFaceRecess.setter
    def foundationsTopFaceRecess (self, fixcotfunddfs: float) -> None:
        """Atribui Fundações: Valor do rebaixo cm."""
        varfixcotfunddfs= ctypes.c_double (fixcotfunddfs)
        self.m_model.m_eagme.BASME_DADEDI_FIXCOTFUNDDFS_DEF (ctypes.byref (varfixcotfunddfs))

    @property
    def firstPileNumber (self) -> int:
        """Fundações: Número de 1a estaca.

        Returns:
            Valor inteiro.
        """
        iprimestaca     = 0
        variprimestaca  = ctypes.c_int (iprimestaca)
        self.m_model.m_eagme.BASME_DADEDI_IPRIMESTACA_LER (ctypes.byref (variprimestaca))
        iprimestaca     = variprimestaca.value
        return          iprimestaca

    @firstPileNumber.setter
    def firstPileNumber (self, iprimestaca: int) -> None:
        """Atribui Fundações: Número de 1a estaca."""
        variprimestaca= ctypes.c_int (iprimestaca)
        self.m_model.m_eagme.BASME_DADEDI_IPRIMESTACA_DEF (ctypes.byref (variprimestaca))

    @property
    def lastPileNumber (self) -> int:
        """Fundações: Número da última estaca.

        Returns:
            Valor inteiro.
        """
        iultmestaca     = 0
        variultmestaca  = ctypes.c_int (iultmestaca)
        self.m_model.m_eagme.BASME_DADEDI_IULTMESTACA_LER (ctypes.byref (variultmestaca))
        iultmestaca     = variultmestaca.value
        return          iultmestaca

    @lastPileNumber.setter
    def lastPileNumber (self, iultmestaca: int) -> None:
        """Atribui Fundações: Número da última estaca."""
        variultmestaca= ctypes.c_int (iultmestaca)
        self.m_model.m_eagme.BASME_DADEDI_IULTMESTACA_DEF (ctypes.byref (variultmestaca))

#
#	Pré-Moldados - CurGlobalData.globalPrecast
#
class GlobalPrecastData ():

    """Dados globais de pré-moldados.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais de pré-moldados.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    @property
    def precastRegion (self) -> int:
        """Pré-moldados: Região construtiva.

        Returns:
            Valor inteiro.
        """
        iregiao         = 0
        variregiao      = ctypes.c_int (iregiao)
        self.m_model.m_eagme.BASME_DADEDI_IREGIAO_LER (ctypes.byref (variregiao))
        iregiao         = variregiao.value
        return          iregiao

    @precastRegion.setter
    def precastRegion (self, iregiao: int) -> None:
        """Atribui Pré-moldados: Região construtiva."""
        variregiao      = ctypes.c_int (iregiao)
        self.m_model.m_eagme.BASME_DADEDI_IREGIAO_DEF (ctypes.byref (variregiao))

    @property
    def corbelData (self) -> "CorbelData":
        """Pré-moldados: Dados de consolo.

        Returns:
            :class:`CorbelData` correspondente.
        """
        consolo         = None
        varconsolo      = ctypes.c_void_p (consolo)
        self.m_model.m_eagme.BASME_DADEDI_CONSOLO_LER (ctypes.byref (varconsolo))
        consolo         = varconsolo.value
        corbeldata      = CorbelData (self.m_model, consolo)
        return          corbeldata

    @property
    def initialCorbelIdent (self) -> str:
        """Pré-moldados: Identificação inicial de consolos (char *).

        Returns:
            Cadeia de caracteres.
        """
        varidentcons    = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_DADEDI_IDENTCONS_LER (varidentcons)
        identcons       = varidentcons.value.decode(TQSUtil.CHARSET)
        return          identcons

    @initialCorbelIdent.setter
    def initialCorbelIdent (self, identcons: str) -> None:
        """Atribui Pré-moldados: Identificação inicial de consolos (char *)."""
        varidentcons      = ctypes.c_char_p (identcons.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_DADEDI_IDENTCONS_DEF (varidentcons)

    @property
    def reinforcementConfig (self) -> str:
        """Pré-moldados: Prefixo padrão de alojamento de armaduras em elementos alveolares.

        Returns:
            Cadeia de caracteres.
        """
        varprefaljp     = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_DADEDI_PREFALJP_LER (varprefaljp)
        prefaljp        = varprefaljp.value.decode(TQSUtil.CHARSET)
        return          prefaljp

    @reinforcementConfig.setter
    def reinforcementConfig (self, prefaljp: str) -> None:
        """Atribui Pré-moldados: Prefixo padrão de alojamento de armaduras em elementos alveolares."""
        varprefaljp     = ctypes.c_char_p (prefaljp.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_DADEDI_PREFALJP_DEF (varprefaljp)

    @property
    def precastInsertWidth (self) -> float:
        """Pré-moldados: Largura do inserto simples cm.

        Returns:
            Valor de ponto flutuante.
        """
        alarginsr       = 0.
        varalarginsr    = ctypes.c_double (alarginsr)
        self.m_model.m_eagme.BASME_DADEDI_ALARGINSR_LER (ctypes.byref (varalarginsr))
        alarginsr       = varalarginsr.value
        return          alarginsr

    @precastInsertWidth.setter
    def precastInsertWidth (self, alarginsr: float) -> None:
        """Atribui Pré-moldados: Largura do inserto simples cm."""
        varalarginsr      = ctypes.c_double (alarginsr)
        self.m_model.m_eagme.BASME_DADEDI_ALARGINSR_DEF (ctypes.byref (varalarginsr))

    @property
    def precastInsertLenght (self) -> float:
        """Pré-moldados: Comprimento do inserto simples cm.

        ATENÇÃO: esta propriedade NÃO chega a ser usada. Mais abaixo na mesma
        classe um setter decorado com ``@precastInsertHeight.setter`` é nomeado
        ``precastInsertLenght`` e sobrepõe esta definição, de modo que
        ``precastInsertLenght`` lê e grava a ESPESSURA (``ALTURINSR``). O
        comprimento (``COMPRINSR``) fica inacessível pela API pública.

        Returns:
            Valor de ponto flutuante.
        """
        comprinsr       = 0.
        varcomprinsr    = ctypes.c_double (comprinsr)
        self.m_model.m_eagme.BASME_DADEDI_COMPRINSR_LER (ctypes.byref (varcomprinsr))
        comprinsr       = varcomprinsr.value
        return          comprinsr

    @precastInsertLenght.setter
    def precastInsertLenght (self, comprinsr: float) -> None:
        """Atribui Pré-moldados: Comprimento do inserto simples cm."""
        varcomprinsr      = ctypes.c_double (comprinsr)
        self.m_model.m_eagme.BASME_DADEDI_COMPRINSR_DEF (ctypes.byref (varcomprinsr))

    @property
    def precastInsertHeight (self) -> float:
        """Pré-moldados: Espessura do inserto simples cm.

        ATENÇÃO: o setter logo abaixo é decorado com
        ``@precastInsertHeight.setter`` mas nomeado ``precastInsertLenght``, o
        que produz dois efeitos na biblioteca TQS: ``precastInsertHeight`` fica
        SOMENTE LEITURA (atribuir levanta ``AttributeError``) e
        ``precastInsertLenght`` passa a ler e gravar a ESPESSURA
        (``ALTURINSR``), deixando o comprimento (``COMPRINSR``) inacessível.

        Returns:
            Valor de ponto flutuante.
        """
        alturinsr       = 0.
        varalturinsr    = ctypes.c_double (alturinsr)
        self.m_model.m_eagme.BASME_DADEDI_ALTURINSR_LER (ctypes.byref (varalturinsr))
        alturinsr       = varalturinsr.value
        return          alturinsr

    @precastInsertHeight.setter
    def precastInsertLenght (self, alturinsr: float) -> None:
        """Atribui Pré-moldados: Espessura do inserto simples cm."""
        varalturinsr      = ctypes.c_double (alturinsr)
        self.m_model.m_eagme.BASME_DADEDI_ALTURINSR_DEF (ctypes.byref (varalturinsr))

    @property
    def facadeData (self) -> "FacadeData":
        """Pré-moldados: Dados de fachada.

        Returns:
            :class:`FacadeData` correspondente.
        """
        fachada         = None
        varfachada      = ctypes.c_void_p (fachada)
        self.m_model.m_eagme.BASME_DADEDI_FACHADA_LER (ctypes.byref (varfachada))
        fachada         = varfachada.value
        facadedata      = FacadeData (self.m_model, fachada)
        return          facadedata
#
#       Atributos BIM - CurGlobalData.globalBimData
#
class GlobalBimData ():

    """Dados globais BIM.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados globais BIM.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    def GetUserAttrib (self, itypeattrib: int) -> "UserAttrib":
        """Atributos de usuário.

        Args:
            itypeattrib: BIM_USRATRTP_xxxx.

        Returns:
            :class:`UserAttrib` correspondente.
        """
        varitipoatrib   = ctypes.c_int (itypeattrib)
        usratrib        = None
        varusratrib     = ctypes.c_void_p (usratrib)
        self.m_model.m_eagme.BASME_DADEDI_USRATRIB_LER (ctypes.byref (varitipoatrib),
                ctypes.byref (varusratrib))
        usratrib        = varusratrib.value
        userattrib      = UserAttrib (self.m_model, usratrib)
        return          userattrib

    @property
    def globalAttrib (self) -> "GlobalAttrib":
        """Atributos BIM globais.

        Returns:
            :class:`GlobalAttrib` correspondente.
        """
        glbatrib        = None
        varglbatrib     = ctypes.c_void_p (glbatrib)
        self.m_model.m_eagme.BASME_DADEDI_GLBATRIB_LER (ctypes.byref (varglbatrib))
        glbatrib        = varglbatrib.value
        globalattrib    = GlobalAttrib (self.m_model, glbatrib)
        return          globalattrib

#-----------------------------------------------------------------------------
#       Furo em pilar
#
class GlobalColumnOpening ():

    """Furo em pilar (dados globais).

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Furo em pilar.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model

    @property
    def columnOpening (self) -> "ColumnOpening":
        """Furo em pilar.

        Returns:
            :class:`ColumnOpening` correspondente.
        """
        furopil         = None
        varfuropil      = ctypes.c_void_p (furopil)
        self.m_model.m_eagme.BASME_DADEDI_FUROPIL_LER (ctypes.byref (varfuropil))
        furopil         = varfuropil.value
        columnopening   = ColumnOpening (self.m_model, furopil)
        return          columnopening

#-----------------------------------------------------------------------------
#       Estaca de laje radier - CurGlobalData.globalSlabFPile
#
class GlobalSlabFoundationPile ():

    """Estaca de laje radier (dados globais).

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model") -> None:
        """Dados de uma estaca para laje radier.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model
#
#	Uma estaca de radier p/servir de modelo
#
    @property
    def slabFoundationPile (self) -> "SlabFoundationPile":
        """Dados de uma estaca para laje radier.

        Dados atuais definidos:
        model.current.column.slabFoundationPile

        Returns:
            :class:`SlabFoundationPile` correspondente.
        """
        estacrad        = None
        varestacrad     = ctypes.c_void_p (estacrad)
        self.m_model.m_eagme.BASME_DADEDI_ESTACRAD_LER (ctypes.byref (varestacrad))
        estacrad        = varestacrad.value
        slabfoundationpile = SlabFoundationPile (self.m_model, estacrad)
        return          slabfoundationpile


#-----------------------------------------------------------------------------
#      Rotinas que manipulam a lista de plantas
#
class FloorsList ():

    """Lista de plantas do edifício.

    Implementação:
        Mantém um dicionário ``floors`` indexado por nome da planta. Os métodos abrem
        sequencialmente cada planta no editor C++ via ``BASME_PLANTA_*`` para então
        instanciar :class:`Floor` correspondentes.
    """
    def __init__ (self, model: "Model") -> None:
        """Classe de manipulação de plantas e seu conteúdo.

        Args:
            model: Objeto Model() do modelo atual.
        """
        self.m_model    = model
        self.floors     = dict ()    # [nompla] = Floor ()

    def GetFloor (self, nompla: int) -> "Floor":
        """Define a planta atual e retorna um objeto Floor() de planta.

        Args:
            nompla: Nome da planta.

        Returns:
            Objeto Floor, com dados de uma planta.
        """
        floor           = Floor (self.m_model, nompla)
        return          floor

    def GetNumFloors (self) -> int:
        """Retorna num floors.

        Returns:
            Valor inteiro.
        """
        numplantas      = 0
        varnumplantas   = ctypes.c_int (numplantas)
        self.m_model.m_eagme.INTME_NUMPLANTAS (ctypes.byref (varnumplantas))
        numplantas      = varnumplantas.value
        return          numplantas

    def GetFloorName (self, indpla: int) -> str:
        """Nome de uma planta.

        Args:
            indpla: Índice da planta 1..GetNumFloors().

        Returns:
            Cadeia de caracteres.
        """
        varindpla       = ctypes.c_int (indpla)
        varnompla       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.INTME_LERPLANTA (ctypes.byref (varindpla),
                            varnompla)
        nompla          = varnompla.value.decode(TQSUtil.CHARSET)
        return          nompla

    def GetFloorIndex (self, nompla: str) -> int:
        """Índice da planta.

        Args:
            nompla: Nome da planta.

        Returns:
            indpla      <- Índice da planta 1..GetNumFloors() ou zero.
        """
        varnompla       = ctypes.c_char_p (nompla.encode (TQSUtil.CHARSET))
        indpla          = 0
        varindpla       = ctypes.c_int (indpla)
        self.m_model.m_eagme.INTME_LERINDPLA (varnompla, ctypes.byref (varindpla))
        indpla          = varindpla.value
        return          indpla


    def _EnterFloor (self, nompla: int, floor: "Floor") -> None:
        """Associa nome da planta nompla com objeto Floor.

        Args:
            nompla: Nome da planta.
            floor: Planta corrente (:class:`Floor`).
        """
        self.floors [nompla] = floor

#-----------------------------------------------------------------------------
#      Planta que contém objetos
#
class Floor ():

    """Planta que contém objetos estruturais.

    Implementação:
        Wrapper de ``CPlantaMe`` (planta corrente). Os metodos navegam para a planta no
        editor C++ (``BASME_PLANTA_ABRIR``) e expõem sub-objetos para criação,
        iteração e dados correntes. A maioria das propriedades é getter/setter direto.
    """
    def __init__ (self, model: "Model", nompla: Optional[str] = None, fabrica: Optional[int] = None) -> None:
        """Classe com dados de uma planta e seus objetos.

        NOTA:       ou fornecemos "nompla", ou "fabrica"

        Args:
            model: Objeto Model() do modelo atual.
            nompla: Nome da planta.
            fabrica: Estrutura C++ de planta do Modelador.
        """
        self.m_model    = model
        self.m_nompla   = nompla
        self.m_fabrica  = fabrica
        pvistav         = None
        if              (self.m_model.m_tqsjan != None):
            pvistav     = self.m_model.m_tqsjan.m_pvistav
        # Caso (1): só temos o nome -> abre a planta no editor e captura o handle 'fabrica'
        if              (fabrica == None):
            varpvistav  = ctypes.c_void_p (pvistav)
            varnompla   = ctypes.c_char_p (nompla.encode (TQSUtil.CHARSET))
            varfabrica  = ctypes.c_void_p (self.m_fabrica)
            istat       = 0
            varistat    = ctypes.c_int (istat)
            self.m_model.m_eagme.INTME_ABRIRMODELOPLANTA (ctypes.byref (varpvistav), varnompla,
                            ctypes.byref (varfabrica), ctypes.byref (varistat))
            istat       = varistat.value
            # Falha ao abrir a planta é fatal: não há como continuar sem o handle
            if          (istat != 0):
                TQSUtil.writef ("Erro abrindo a planta [%s]" % nompla)
                exit    ()
            self.m_fabrica  = varfabrica.value
        # Caso (2): já temos o handle -> só extrai o nome correspondente
        if              (fabrica != None):
            varfabrica  = ctypes.c_void_p (self.m_fabrica)
            varnompla   = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
            varagfan    = ctypes.c_int (0)
            self.m_model.m_eagme.BASME_PLANTA_NOMPLA_LER (ctypes.byref (varfabrica),
                                varnompla, varagfan)
            nompla      = varnompla.value.decode(TQSUtil.CHARSET)
            self.m_nompla= nompla

        # Registra a planta no dicionário global e instancia os sub-objetos auxiliares
        self.m_model.floors._EnterFloor (nompla, self)
        self.current    = CurrentFloorData (self.m_model, self)
        self.create     = SMOCreate (self.m_model, self.m_fabrica, self)
        self.iterator   = SMOIterator (self.m_model, self.m_fabrica, self)
        self.util       = FloorUtil (self.m_model, self.m_fabrica)

    @property
    def floorName (self) -> Any:
        """Operação ``floorName``.

        Returns:
            Resultado da operação.
        """
        return          self.m_nompla

    @property
    def height (self) -> float:
        """Pé-direito do piso (m), medido do nível atual ao nível do piso de baixo.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        pedireito       = 0.
        varpedireito    = ctypes.c_double (pedireito)
        self.m_model.m_eagme.BASME_PLANTA_PEDIREITO_LER (ctypes.byref (varfabrica), \
                                ctypes.byref (varpedireito))
        pedireito       = varpedireito.value
        return          pedireito

    @property
    def elevation (self) -> float:
        """Cota da planta atual (m).

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        cotaini         = 0.
        varcotaini      = ctypes.c_double (cotaini)
        self.m_model.m_eagme.BASME_PLANTA_COTAINI_LER (ctypes.byref (varfabrica), \
                                ctypes.byref (varcotaini))
        cotaini         = varcotaini.value
        return          cotaini

    @property
    def repetition (self) -> int:
        """Repetição da planta atual - número de pisos da planta.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        numrep          = 0
        varnumrep      = ctypes.c_int (numrep)
        self.m_model.m_eagme.BASME_PLANTA_NUMREP_LER (ctypes.byref (varfabrica), \
                                ctypes.byref (varnumrep))
        numrep         = varnumrep.value
        return          numrep

    def FloorElevation (self, irep: int) -> float:
        """Cota (m) de uma das repetições da planta atual 0..repetition-1.

        Args:
            irep: Número da repetição 0..repetition-1.

        Returns:
            Cota (m) da repetição.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varirep         = ctypes.c_int (irep)
        cota            = 0.
        varcota         = ctypes.c_double (cota)
        self.m_model.m_eagme.BASME_PLANTA_COTAREP_LER (ctypes.byref (varfabrica), \
                                ctypes.byref (varirep), ctypes.byref (varcota))
        cota            = varcota.value
        return          cota

    @property
    def auxiliaryFloors (self) -> int:
        """Número de pisos auxiliares nesta planta.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        numdfspiso      = 0
        varnumdfspiso   = ctypes.c_int (numdfspiso)
        self.m_model.m_eagme.BASME_PLANTA_NUMDFSPISO_LER (ctypes.byref (varfabrica), \
                                ctypes.byref (varnumdfspiso))
        numdfspiso      = varnumdfspiso.value
        return          numdfspiso

    def AuxiliaryFloorRecess (self, ipisoaux: int) -> float:
        """Rebaixo do piso auxiliar (m).

        Args:
            ipisoaux: 0..auxiliaryFloors-1.

        Returns:
            Rebaixo do piso auxiliar (m).
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varipisoaux     = ctypes.c_int (ipisoaux)
        dfspiso         = 0.
        vardfspiso      = ctypes.c_double (dfspiso)
        self.m_model.m_eagme.BASME_PLANTA_DFSPISO_LER (ctypes.byref (varfabrica), \
                                ctypes.byref (varipisoaux), ctypes.byref (vardfspiso))
        dfspiso         = vardfspiso.value
        return          dfspiso

#-----------------------------------------------------------------------------
#      Criação de objetos estruturais em uma planta
#
class SMOCreate ():

    """Criação de objetos estruturais em uma planta.

    Implementação:
        Cada método ``CreateXxx`` aplica a sequência: (1) garante a planta corrente,
        (2) preenche um buffer C++ com parâmetros do objeto, (3) chama a rotina
        ``BASME_*_INSERIR`` ou ``BASME_*_CRIAR`` da DLL e (4) devolve um wrapper Python
        apontando para o objeto recém-criado no ``CObjMe``. Falhas são sinalizadas
        como ponteiro nulo / ``istat != 0``.
    """
    def __init__ (self, model: "Model", fabrica: int, floor: "Floor") -> None:
        """Classe com dados de uma planta e seus objetos.

        Args:
            model: Objeto Model() do modelo atual.
            fabrica: Handle de acesso à planta no Modelador.
            floor: Planta corrente (:class:`Floor`).
        """
        self.m_model    = model
        self.m_fabrica  = fabrica
        self.m_floor    = floor

    def _CreateColumnType (self, itipo: int, xins: float, yins: float) -> "Column":
        """Criação de um pilar/fundação/pilarete.

        Args:
            itipo: Constante do tipo de objeto/elemento.
            xins: Coordenada ``xins`` em unidades de desenho.
            yins: Coordenada ``yins`` em unidades de desenho.

        Returns:
            :class:`Column` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varitipo        = ctypes.c_int (itipo)
        varxins         = ctypes.c_double (xins)
        varyins         = ctypes.c_double (yins)
        pilar           = None
        varpilar        = ctypes.c_void_p (pilar)
        self.m_model.m_eagme.BASME_PILARES_CRIAR (ctypes.byref (varfabrica),
                ctypes.byref (varitipo), ctypes.byref (varxins), ctypes.byref (varyins),
                ctypes.byref (varpilar))
        pilar           = varpilar.value
        return          Column (self.m_model, self, pilar)


    def CreateColumn (self, xins: float, yins: float) -> Any:
        """Criação de um pilar.

        Outras variáveis usadas na criação de um pilar:
        model       = TQSModel.Model ()
        model.current.globalBimData.userAttrib
        model.current.globalBimData.globalAttrib
        model.current.globalColumnData.foundationData
        model.current.globalColumnData.spreadFootingSideWalls
        model.current.globalColumnData.foundationsTopFaceRecess
        model.current.globalColumnData.firstPileNumber
        model.current.globalColumnData.lastPileNumber
        model.current.globalColumnData.columnData / foundationColumnData / shortColumnData
        columnData.columnDetailing
        columnData.columnGeometry
        columnData.columnInsertion
        columnData.columnPolygon
        columnData.columnCoil
        columnData.columnIdent
        columnData.columnPrecastData
        columnData.columnStarts
        columnData.columnModel
        columnData.columnWindSupport
        columnData.columnSectionMode
        columnData.columnInterference
        columnData.columnSloped
        columnData.columnIsAFoundation
        columnData.columnHinges
        columnData.columnExport
        columnData.columnNonLinearity
        columnData.columnBucklingX
        columnData.columnBucklingY
        columnData.columnDoubleStoryX
        columnData.columnDoubleStoryY
        columnData.columnConcreteFc
        columnData.columnExport
        floor = model.floors.GetFloor ("nome-da-planta")
        floor.current.column.columnFloorNames
        floor.current.column.columnBoundaryCond
        floor.current.column.columnCover
        floor.current.column.columnExposure
        floor.current.column.columnDynHorLoad

        Args:
            xins: Coordenada ``xins`` em unidades de desenho.
            yins: Coordenada ``yins`` em unidades de desenho.

        Returns:
            Objeto tipo Column().
        """
        itipo           = COLUMNDATA_PILARS
        return          self._CreateColumnType (itipo, xins, yins)

    def CreateShortColumn (self, xins: float, yins: float) -> Any:
        """Criação de um pilarete.

        Veja em CreateColumn as variáveis pré-definidas

        Args:
            xins: Coordenada ``xins`` em unidades de desenho.
            yins: Coordenada ``yins`` em unidades de desenho.

        Returns:
            Objeto tipo Column().
        """
        itipo           = COLUMNDATA_PILRTE
        return          self._CreateColumnType (itipo, xins, yins)

    def CreateFoundation (self, xins: float, yins: float) -> Any:
        """Criação de uma fundação.

        Veja em CreateColumn as variáveis pré-definidas

        Args:
            xins: Coordenada ``xins`` em unidades de desenho.
            yins: Coordenada ``yins`` em unidades de desenho.

        Returns:
            Objeto tipo Column().
        """
        itipo           = COLUMNDATA_FUNDAC
        return          self._CreateColumnType (itipo, xins, yins)

    def CreateBeam (self, xy: Any) -> "Beam":
        """Cria viga no plano.

        xy  ((x1,y1),(x2,y2)...)    coordenadas da viga
        Outras variáveis usadas na criação de um pilar:
        model       = TQSModel.Model ()
        model.current.globalBeamData.beamRestraint
        model.current.globalBeamData.firstSlopedBeamNumber
        model.current.globalBeamData.slopedBeamIdent
        model.current.globalBimData.userAttrib
        floor = model.floors.GetFloor ("nome-da-planta")
        floor.current.floorBeamData.beamGeometry
        floor.current.floorBeamData.beamInertia
        floor.current.floorBeamData.beamBond
        floor.current.floorBeamData.beamInsertion
        floor.current.floorBeamData.beamTemperShrink
        floor.current.floorBeamData.beamDetailing
        floor.current.floorBeamData.beamExport
        floor.current.floorLoadData.load

        Args:
            xy: Parâmetro ``xy``.

        Returns:
            Objeto tipo Beam().
        """
        # Limpa o buffer interno e empilha cada vértice da poligonal da viga via API ponto-a-ponto
        self.m_model.m_eagme.BASME_VIGAS_PONTOS_LIMPAR ()
        for             coords in xy:
            varxvig     = ctypes.c_double (coords [0])
            varyvig     = ctypes.c_double (coords [1])
            self.m_model.m_eagme.BASME_VIGAS_ENTRARPONTO (ctypes.byref (varxvig),
                            ctypes.byref (varyvig))

        # Cria a viga consumindo o buffer empilhado acima; viga não inclinada por padrão
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        inclinada       = 0
        varinclinada    = ctypes.c_int (inclinada)
        info3d          = None
        varinfo3d       = ctypes.c_void_p (info3d)
        viga            = None
        varviga         = ctypes.c_void_p (viga)
        self.m_model.m_eagme.BASME_VIGAS_CRIAR_PONTOS (ctypes.byref (varfabrica),
                            ctypes.byref (varinclinada), ctypes.byref (varinfo3d),
                            ctypes.byref (varviga))
        viga            = varviga.value
        return          Beam (self.m_model, viga)

    def CreateBeamOpening (self, beam: "Beam", xins: float, yins: float) -> "BeamOpening":
        """Cria um furo horizontal em viga.

        Outras variáveis usadas na criação de um furo em viga
        model       = TQSModel.Model ()
        floor       = model.floors.GetFloor ("nome-da-planta")
        floor.floorBeamData.beamOpening

        Args:
            beam: Objeto da viga.
            xins: Coordenada ``xins`` em unidades de desenho.
            yins: Coordenada ``yins`` em unidades de desenho.

        Returns:
            Objeto tipo BeamOpening().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varviga         = ctypes.c_void_p (beam.m_viga)
        varxins         = ctypes.c_double (xins)
        varyins         = ctypes.c_double (yins)
        furovig         = None
        varfurovig      = ctypes.c_void_p (furovig)
        self.m_model.m_eagme.BASME_FUROVIG_CRIAR (ctypes.byref (varfabrica),
                            ctypes.byref (varviga), ctypes.byref (varxins),
                            ctypes.byref (varyins), ctypes.byref (varfurovig))
        furovig         = varfurovig.value
        return          BeamOpening (self.m_model, furovig)

    def CreateSlabContour (self, x1: float, y1: float, x2: float, y2: float) -> "SlabContour":
        """Cria contorno auxiliar de laje - bordo livre.

        Args:
            x1: Coordenada ``x1`` em unidades de desenho.
            y1: Coordenada ``y1`` em unidades de desenho.
            x2: Coordenada ``x2`` em unidades de desenho.
            y2: Coordenada ``y2`` em unidades de desenho.

        Returns:
            Objeto tipo SlabContour().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varx1           = ctypes.c_double (x1)
        vary1           = ctypes.c_double (y1)
        varx2           = ctypes.c_double (x2)
        vary2           = ctypes.c_double (y2)
        info3d          = None
        varinfo3d       = ctypes.c_void_p (info3d)
        ctraux          = None
        varctraux       = ctypes.c_void_p (ctraux)
        self.m_model.m_eagme.BASME_CTRAUX_CRIAR (ctypes.byref (varfabrica),
                            ctypes.byref (varx1), ctypes.byref (vary1),
                            ctypes.byref (varx2), ctypes.byref (vary2),
                            ctypes.byref (varinfo3d), ctypes.byref (varctraux))
        ctraux          = varctraux.value
        return          SlabContour (self.m_model, ctraux)

    def CreateSlab (self, xins: float, yins: float, angpri: float) -> "Slab":
        """Cria laje dentro de contorno formado por vigas, pilares ou contorno auxiliar.

        Outras variáveis usadas na criação de uma laje:
        model       = TQSModel.Model ()
        floor       = model.floors.GetFloor ("nome-da-planta")
        model.current.globalSlabData.stairCase
        model.current.globalSlabData.firstRampNumber
        floor.current.floorSlabData.slabIdent
        floor.current.floorSlabData.slabFirstNumber
        floor.current.floorLoadData.GetLoad
        floor.current.floorSlabData.slabGeometry
        floor.current.floorSlabData.slabGrid
        floor.current.floorSlabData.stairTitle
        floor.current.floorSlabData.slabExport
        floor.current.floorSlabData.slabDetailing

        Args:
            xins: Coordenada ``xins`` em unidades de desenho.
            yins: Coordenada ``yins`` em unidades de desenho.
            angpri: Parâmetro ``angpri``.

        Returns:
            Objeto tipo Slab().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        irampa          = 0
        varirampa       = ctypes.c_int (irampa)
        iescada         = 0
        variescada      = ctypes.c_int (iescada)
        ipatamar        = 0
        varipatamar     = ctypes.c_int (ipatamar)
        varxins           = ctypes.c_double (xins)
        varyins           = ctypes.c_double (yins)
        varangpri         = ctypes.c_double (angpri)
        info3d          = None
        varinfo3d       = ctypes.c_void_p (info3d)
        lajeinc         = None
        varlajeinc      = ctypes.c_void_p (lajeinc)
        laje            = None
        varlaje         = ctypes.c_void_p (laje)
        self.m_model.m_eagme.BASME_LAJES_CRIAR (ctypes.byref (varfabrica),
                            ctypes.byref (varirampa), ctypes.byref (variescada),
                            ctypes.byref (varipatamar), ctypes.byref (varxins),
                            ctypes.byref (varyins), ctypes.byref (varangpri),
                            ctypes.byref (varinfo3d), ctypes.byref (varlajeinc),
                            ctypes.byref (varlaje))
        laje            = varlaje.value
        return          Slab (self.m_model, laje)

    def CreateDropPanel (self, polig: "Polygon") -> "DropPanel":
        """Cria capitel.

        Outras variáveis usadas na criação de um capitel:
        model       = TQSModel.Model ()
        floor       = model.floors.GetFloor ("nome-da-planta")
        floor.current.floorSlabData.dropPanelThickness
        floor.current.floorSlabData.dropPanelDiv

        Args:
            polig: Polígono (:class:`Polygon`).

        Returns:
            Objeto tipo DropPanel().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varpolig        = ctypes.c_void_p (polig.m_polig)
        capitel         = None
        varcapitel      = ctypes.c_void_p (capitel)
        self.m_model.m_eagme.BASME_CAPITEIS_CRIAR (ctypes.byref (varfabrica),
                            ctypes.byref (varpolig), ctypes.byref (varcapitel))
        capitel         = varcapitel.value
        return          DropPanel (self.m_model, capitel)

    def CreateSlabMould (self, slab: "Slab", xnerv: float, ynerv: float) -> "SlabMould":
        """Cria uma forma/cubeta de laje nevurada.

        Outras variáveis usadas na criação de uma forma de nervura:
        model       = TQSModel.Model ()
        floor       = model.floors.GetFloor ("nome-da-planta")
        floor.current.floorSlabData.slabMouldXSize
        floor.current.floorSlabData.slabMouldYSize
        floor.current.floorSlabData.slabMouldXSpace
        floor.current.floorSlabData.slabMouldYSpace
        floor.current.floorSlabData.slabMouldBasePoint

        Args:
            slab: Parâmetro ``slab``.
            xnerv: Parâmetro ``xnerv``.
            ynerv: Parâmetro ``ynerv``.

        Returns:
            Objeto tipo SlabMould().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varlaje         = ctypes.c_void_p (slab.m_laje)
        varxnerv        = ctypes.c_double (xnerv)
        varynerv        = ctypes.c_double (ynerv)
        forner          = None
        varforner       = ctypes.c_void_p (forner)
        self.m_model.m_eagme.BASME_FORNER_CRIAR (ctypes.byref (varfabrica),
                            ctypes.byref (varlaje), ctypes.byref (varxnerv),
                            ctypes.byref (varynerv), ctypes.byref (varforner))
        forner          = varforner.value
        return          SlabMould (self.m_model, forner)

    def CreateSlabOpening (self, polig: "Polygon", irecorte: int, isobrecapa: int) -> "SlabOpening":
        """Cria capitel.

        Args:
            polig: Polígono (:class:`Polygon`).
            irecorte: Parâmetro ``irecorte``.
            isobrecapa: Parâmetro ``isobrecapa``.

        Returns:
            Objeto tipo SlabOpening().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varpolig        = ctypes.c_void_p (polig.m_polig)
        varirecorte     = ctypes.c_int (irecorte)
        varisobrecapa   = ctypes.c_int (isobrecapa)
        furo            = None
        varfuro         = ctypes.c_void_p (furo)
        self.m_model.m_eagme.BASME_FUROS_CRIAR (ctypes.byref (varfabrica),
                            ctypes.byref (varpolig), ctypes.byref (varirecorte),
                            ctypes.byref (varisobrecapa), ctypes.byref (varfuro))
        furo            = varfuro.value
        return          SlabOpening (self.m_model, furo)


    def CreateSoilPressureLoad (self, xini: float, yini: float, xfin: float, yfin: float) -> "SoilPressureLoad":
        """Cria uma carga de empuxo.

        Os valores de cargas devem ser definidos primeiro em:
        model       = TQSModel.Model ()
        model.current.globalSoilpress.soilPressureLoad

        Args:
            xini: Ponto inicial X.
            yini: Ponto inicial Y.
            xfin: Ponto final   X.
            yfin: Ponto final   Y.

        Returns:
            Objeto tipo SoilPressureLoad().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varxini         = ctypes.c_double (xini)
        varyini         = ctypes.c_double (yini)
        varxfin         = ctypes.c_double (xfin)
        varyfin         = ctypes.c_double (yfin)
        caremp          = None
        varcaremp       = ctypes.c_void_p (caremp)
        self.m_model.m_eagme.BASME_CAREMP_CRIAR (ctypes.byref (varfabrica),
                        ctypes.byref (varxini), ctypes.byref (varyini),
                        ctypes.byref (varxfin), ctypes.byref (varyfin), ctypes.byref (varcaremp))
        caremp          = varcaremp.value
        soilPressureLoad = SoilPressureLoad (self.m_model, self.m_floor, caremp)
        return          soilPressureLoad

    def CreateAdditionalLoad (self, xins: float, yins: float) -> "AdditionalLoad":
        """Cria carga adicional em laje.

        O valor da carga deve ser definido primeiro em:
        model       = TQSModel.Model ()
        floor       = model.floors.GetFloor ("nome-da-planta")
        load        = floor.current.floorLoadData.GetLoad (TPLOAD_CARADI)

        Args:
            xins: Coordenada ``xins`` em unidades de desenho.
            yins: Coordenada ``yins`` em unidades de desenho.

        Returns:
            Objeto tipo AdditionalLoad().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varxins         = ctypes.c_double (xins)
        varyins         = ctypes.c_double (yins)
        caradi          = None
        varcaradi       = ctypes.c_void_p (caradi)
        self.m_model.m_eagme.BASME_CARADI_CRIAR (ctypes.byref (varfabrica),
                        ctypes.byref (varxins), ctypes.byref (varyins),
                        ctypes.byref (varcaradi))
        caradi          = varcaradi.value
        additionalLoad  = AdditionalLoad (self.m_model, self.m_floor, caradi)
        return          additionalLoad


    def CreateAreaDistributedLoad (self, polig: "Polygon") -> "AreaDistributedLoad":
        """Cria distribuída em laje dentro de uma poligonal fechada tf/m2.

        O valor da carga deve ser definido primeiro em:
        model       = TQSModel.Model ()
        floor       = model.floors.GetFloor ("nome-da-planta")
        load        = floor.current.floorLoadData.GetLoad (TPLOAD_CARARE)

        Args:
            polig: Polígono (:class:`Polygon`).

        Returns:
            Objeto tipo AreaDistributedLoad().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varpolig        = ctypes.c_void_p (polig.m_polig)
        carare          = None
        varcarare       = ctypes.c_void_p (carare)
        self.m_model.m_eagme.BASME_CARARE_CRIAR (ctypes.byref (varfabrica),
                        ctypes.byref (varpolig), ctypes.byref (varcarare))
        carare          = varcarare.value
        areaDistributedLoad = AreaDistributedLoad (self.m_model, self.m_floor, carare)
        return          areaDistributedLoad

    def CreateConcentratedLoad (self, xins: float, yins: float) -> "ConcentratedLoad":
        """Cria carga concentrada tf.

        O valor da carga deve ser definido primeiro em:
        model       = TQSModel.Model ()
        floor       = model.floors.GetFloor ("nome-da-planta")
        load        = floor.current.floorLoadData.GetLoad (
        TPLOAD_FORCFX/TPLOAD_FORCFY/TPLOAD_FORCFZ/TPLOAD_FORCMX/TPLOAD_FORCMY)

        Args:
            xins: Coordenada ``xins`` em unidades de desenho.
            yins: Coordenada ``yins`` em unidades de desenho.

        Returns:
            Objeto tipo ConcentratedLoad().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varxins         = ctypes.c_double (xins)
        varyins         = ctypes.c_double (yins)
        carcon          = None
        varcarcon       = ctypes.c_void_p (carcon)
        self.m_model.m_eagme.BASME_CARCON_CRIAR (ctypes.byref (varfabrica),
                        ctypes.byref (varxins), ctypes.byref (varyins),
                        ctypes.byref (varcarcon))
        carcon          = varcarcon.value
        concentratedLoad = ConcentratedLoad (self.m_model, self.m_floor, carcon)
        return          concentratedLoad

    def CreateLinearyDistributedLoad (self, xins1: float, yins1: float, xins2: float, yins2: float) -> "LinearyDistributedLoad":
        """Cria linear tf/m sobre viga ou laje.

        ATENÇÃO: o objeto devolvido é construído com ``self`` (a instância
        ``SMOCreate``) no lugar de ``self.m_floor``, diferente de todos os
        criadores de carga vizinhos. O ``m_floor`` do objeto devolvido aponta
        para ``SMOCreate``, então operações que dependem da planta a partir dessa
        carga usam o objeto errado. Obtenha a carga novamente pela planta se
        precisar dessas operações.

        O valor da carga deve ser definido primeiro em:
        model       = TQSModel.Model ()
        floor       = model.floors.GetFloor ("nome-da-planta")
        load        = floor.current.floorLoadData.GetLoad (TPLOAD_CARLIN)

        Args:
            xins1: Parâmetro ``xins1``.
            yins1: Parâmetro ``yins1``.
            xins2: Parâmetro ``xins2``.
            yins2: Parâmetro ``yins2``.

        Returns:
            Objeto tipo LinearyDistributedLoad().
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varxins1        = ctypes.c_double (xins1)
        varyins1        = ctypes.c_double (yins1)
        varxins2        = ctypes.c_double (xins2)
        varyins2        = ctypes.c_double (yins2)
        carlin          = None
        varcarlin       = ctypes.c_void_p (carlin)
        self.m_model.m_eagme.BASME_CARLIN_CRIAR (ctypes.byref (varfabrica),
                        ctypes.byref (varxins1), ctypes.byref (varyins1),
                        ctypes.byref (varxins2), ctypes.byref (varyins2),
                        ctypes.byref (varcarlin))
        carlin          = varcarlin.value
        linearyDistributedLoad = LinearyDistributedLoad (self.m_model, self, carlin)
        return          linearyDistributedLoad

#-----------------------------------------------------------------------------
#      Iteração pelos elementos de uma lista de objetos
#
class SMOIterator ():

    """Iteração pelos objetos de uma planta.

    Implementação:
        Itera elementos de uma planta percorrendo o ``CObjMe`` da DLL. ``GetNumObjects``
        retorna o total de uma classe ``TYPE_xxxx`` e ``GetObject`` / ``DerivedObject``
        constroem o wrapper Python apropriado (``Beam``, ``Slab``, ``Column``, ...) a
        partir do tipo lido em runtime. ``DerivedObject`` faz dispatch por ``TYPE_xxxx``.
    """
    def __init__ (self, model: "Model", fabrica: int, floor: "Floor") -> None:
        """Classe com dados de uma planta e seus objetos.

        Args:
            model: Objeto Model() do modelo atual.
            fabrica: Handle de acesso à planta no Modelador.
            floor: Planta corrente (:class:`Floor`).
        """
        self.m_model    = model
        self.m_fabrica  = fabrica
        self.m_floor    = floor


    def GetNumObjects (self, itype: int) -> int:
        """itype.

        Args:
            itype: TYPE_xxxx.

        Returns:
            itype       <- (int) TYPE_xxxx.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varitype        = ctypes.c_int (itype)
        numobjetos      = 0
        varnumobjetos   = ctypes.c_int (numobjetos)
        self.m_model.m_eagme.BASME_PLANTA_NUMOBJETOS (ctypes.byref (varfabrica),
                        ctypes.byref (varitype), ctypes.byref (varnumobjetos))
        numobjetos      = varnumobjetos.value
        return          numobjetos


    def DerivedObject (self, objme: int) -> "SMObject":
        """smobject.

        Args:
            objme: Parâmetro ``objme``.

        ATENÇÃO: o ramo ``TYPE_FUNDAC`` chama ``Column (self.m_model, objme)``
        com um argumento a menos do que o construtor exige — o ramo
        ``TYPE_PILARES`` logo acima passa ``(self.m_model, self, objme)``.
        Derivar um objeto de fundação levanta ``TypeError`` em vez de devolver o
        wrapper. Trate fundações pelo ``SMObject`` genérico até a correção.

        Returns:
            Objeto tipo SMObject que representa objeto do Modelador.
        """
        # Constrói wrapper genérico só para extrair o type tag, depois faz dispatch para a classe específica
        smobject        = SMObject (self.m_model, objme)
        itype           = smobject.type
        # Tipos não tratados caem no SMObject base (mantém o ponteiro mas sem API especializada)
        if              (itype == TYPE_VIGAS):
            smobject    = Beam (self.m_model, objme)

        if              (itype == TYPE_PILARES):
            smobject    = Column (self.m_model, self, objme)

        if              (itype == TYPE_LAJES):
            smobject    = Slab (self.m_model, objme)

        if              (itype == TYPE_FUNDAC):
            smobject    = Column (self.m_model, objme)

        if              (itype == TYPE_FUROS):
            smobject    = SlabOpening (self.m_model, objme)

        if              (itype == TYPE_CAPITEIS):
            smobject    = DropPanel (self.m_model, objme)

        if              (itype == TYPE_FORNER):
            smobject    = SlabMould (self.m_model, objme)

        if              (itype == TYPE_CTRAUX):
            smobject    = SlabContour (self.m_model, objme)

        if              (itype == TYPE_EIXOS):
            pass

        if              (itype == TYPE_COTAGENS):
            pass

        if              (itype == TYPE_CORTES):
            pass

        if              (itype == TYPE_DADPAV):
            pass

        if              (itype == TYPE_DADEDI):
            pass

        if              (itype == TYPE_SECPIL):
            smobject    = ColumnSection (None, self.m_model, self.m_floor, objme)

        if              (itype == TYPE_LISMAL):
            pass

        if              (itype == TYPE_CARCON):
            smobject    = ConcentratedLoad (self.m_model, self.m_floor, objme)

        if              (itype == TYPE_CARLIN):
            smobject    = LinearyDistributedLoad (self.m_model, self.m_floor, objme)

        if              (itype == TYPE_CARARE):
            smobject    = AreaDistributedLoad (self.m_model, self.m_floor, objme)

        if              (itype == TYPE_BARICEN):
            pass

        if              (itype == TYPE_CARADI):
            smobject    = AdditionalLoad (self.m_model, self.m_floor, objme)

        if              (itype == TYPE_RAMPAS):
            pass

        if              (itype == TYPE_ORIEIX):
            pass

        if              (itype == TYPE_TABNP):
            pass

        if              (itype == TYPE_IDCLI):
            pass

        if              (itype == TYPE_CONSBIB):
            pass

        if              (itype == TYPE_FUROVIG):
            smobject    = BeamOpening (self.m_model, objme)

        if              (itype == TYPE_ELMLJP):
            pass

        if              (itype == TYPE_TABELEM):
            pass

        if              (itype == TYPE_COTDIA):
            pass

        if              (itype == TYPE_COTANG):
            pass

        if              (itype == TYPE_COTNOT):
            pass

        if              (itype == TYPE_VENDST):
            pass

        if              (itype == TYPE_CENTOR):
            pass

        if              (itype == TYPE_CONSIND):
            pass

        if              (itype == TYPE_CAREMP):
            smobject    = SoilPressureLoad (self.m_model, self.m_floor, objme)

        if              (itype == TYPE_TABNIVPAV):
            pass

        if              (itype == TYPE_LEGDESNIV):
            pass

        if              (itype == TYPE_SIMDESNIV):
            pass

        if              (itype == TYPE_ELM3D):
            pass

        if              (itype == TYPE_INSRBLO):
            pass

        if              (itype == TYPE_INSRPOS):
            pass

        if              (itype == TYPE_FACHADA):
            pass

        if              (itype == TYPE_TUBOS):
            pass

        if              (itype == TYPE_FUROPIL):
            pass

        if              (itype == TYPE_LAJESSOVOL):
            pass

        if              (itype == TYPE_ESTACRAD):
            pass

        if              (itype == TYPE_VIGASINC):
            pass

        if              (itype == TYPE_PILARETES):
            pass

        if              (itype == TYPE_ESCADAS):
            pass

        if              (itype == TYPE_PATAMARES):
            pass

        if              (itype == TYPE_ORIBARI):
            pass

        if              (itype == TYPE_EDIEDI):
            pass

        if              (itype == TYPE_PTBAS):
            pass

        if              (itype == TYPE_PTLVT):
            pass

        if              (itype == TYPE_CERCATOR):
            pass

        return          smobject


    def GetObject (self, itype: int, iobject: int) -> Any:
        """itype.

        Args:
            itype: TYPE_xxxx.
            iobject: Parâmetro ``iobject``.

        Returns:
            itype       <- (int) TYPE_xxxx.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varitype        = ctypes.c_int (itype)
        variobject      = ctypes.c_int (iobject)
        objme           = None
        varobjme        = ctypes.c_void_p (objme)
        self.m_model.m_eagme.BASME_PLANTA_LEROBJETO (ctypes.byref (varfabrica),
                        ctypes.byref (varitype), ctypes.byref (variobject),
                        ctypes.byref (varobjme))
        objme           = varobjme.value
        smobject        = self.DerivedObject (objme)
        return          smobject

    def FindObject (self, identobj: int) -> Tuple[int, int, int, int]:
        """Acha um objeto dado seu identificador único.

        Args:
            identobj: Identificador único de um objeto.

        Returns:
            Objeto ou NULL se não achar.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        variuniqueid    = ctypes.c_int (identobj)
        objme           = None
        varobjme        = ctypes.c_void_p (objme)
        itype           = 0
        varitype        = ctypes.c_int (itype)
        index           = 0
        varindex        = ctypes.c_int (index)
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.BASME_PLANTA_ACHAROBJETO (ctypes.byref (varfabrica),
                        ctypes.byref (variuniqueid), ctypes.byref (varobjme), ctypes.byref (varitype),
                        ctypes.byref (varindex), ctypes.byref (varistat))
        objme           = varobjme.value
        itype           = varitype.value
        index           = varindex.value
        istat           = varistat.value
        return          objme, itype, index, istat

#------------------------------------------------------------------------------
#       Rotinas utilitárias do pavimento
#
class FloorUtil ():

    """Rotinas utilitárias de pavimento.

    Implementação:
        Utilitários de pavimento que delegam a chamadas C++ pontuais; ``DistributeSlabMould``
        aciona o algoritmo de distribuição de cubetas em lajes nervuradas.
    """
    def __init__ (self, model: "Model", fabrica: int) -> None:
        """Classe de rotinas utilitárias do pavimento.

        Args:
            model: Objeto Model() do modelo atual.
            fabrica: Handle de acesso à planta no Modelador.
        """
        self.m_model    = model
        self.m_fabrica  = fabrica

    def DoIntersections (self) -> None:
        """Refaz as intersecções de vigas, pilares e lajes em uma planta.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        self.m_model.m_eagme.BASME_PLANTA_REFAZERINTERSEC (ctypes.byref (varfabrica))


    def DistributeSlabMould (self, slab: "Slab", slabMould: "SlabMould") -> None:
        """Distribui formas de laje nervurada em uma laje, a partir de uma fornecida.

        Args:
            slab: Parâmetro ``slab``.
            slabMould: Parâmetro ``slabMould``.
        """
        varfabrica      = ctypes.c_void_p (self.m_fabrica)
        varlaje         = ctypes.c_void_p (slab.m_laje)
        varforner       = ctypes.c_void_p (slabMould.m_forner)
        self.m_model.m_eagme.BASME_FORNER_DISTRIBUIR (ctypes.byref (varfabrica),
                            ctypes.byref (varlaje), ctypes.byref (varforner))

#------------------------------------------------------------------------------
#       Objeto poligonal usado em vários tipos de objetos
#
class Polygon ():

    """Poligonal genérica usada em vários objetos.

    Implementação:
        Encapsula uma poligonal C++ (``CPolig``). Métodos ``GetPt`` / ``GetPts`` lêem
        vértices e ``Insert*`` mutam a poligonal; arcos são representados por raio
        associado a cada segmento.
    """
    def __init__ (self, model: "Model", polig: Optional["Polygon"] = None) -> None:
        """Cria objeto poligonal vazio. Se polig != None, usa polig, senão cria novo.

        Args:
            model: Modelo estrutural (:class:`Model`).
            polig: Polígono (:class:`Polygon`).
        """
        self.m_model    = model
        self.m_polig    = None
        # Sem ponteiro fornecido: aloca uma poligonal nova; com ponteiro: reusa o objeto C++ existente
        if              (polig is None):
            varpolig    = ctypes.c_void_p (self.m_polig)
            self.m_model.m_eagme.BASME_POLIG_LER (ctypes.byref (varpolig))
            self.m_polig= varpolig.value
        else:
            self.m_polig= polig

    def Clear (self) -> None:
        """Esvazia uma poligonal.
        """
        varpolig        = ctypes.c_void_p (self.m_polig)
        self.m_model.m_eagme.BASME_POLIG_LIMPAR (ctypes.byref (varpolig))

    def NumPts (self) -> int:
        """Operação ``NumPts``.

        Returns:
            Valor inteiro.
        """
        varpolig        = ctypes.c_void_p (self.m_polig)
        numpts          = 0
        varnumpts      = ctypes.c_int (numpts)
        self.m_model.m_eagme.BASME_POLIG_NUMPTS (ctypes.byref (varpolig),
                        ctypes.byref (varnumpts))
        numpts          = varnumpts.value
        return          numpts

    def GetPt (self, ipt: int) -> Tuple[float, float]:
        """Lê um ponto.

        Args:
            ipt: índice do ponto 0..NumPts()-1.

        Returns:
            x, y        <- (double, double) coordenadas do ponto.
        """
        varpolig        = ctypes.c_void_p (self.m_polig)
        vaript          = ctypes.c_int (ipt)
        x               = 0.
        varx            = ctypes.c_double (x)
        y               = 0.
        vary            = ctypes.c_double (y)
        self.m_model.m_eagme.BASME_POLIG_LERPT (ctypes.byref (varpolig),
                        ctypes.byref (vaript), ctypes.byref (varx), ctypes.byref (vary))
        x               = varx.value
        y               = vary.value
        return          x, y

    def GetPts (self) -> Tuple[Any, Any]:
        """Lê a poligonal inteira como uma matriz.

        Returns:
            x[], y[].
        """
        # Lê todos os vértices em paralelo: dois arrays Python alinhados por índice
        np              = self.NumPts ()
        x               = []
        y               = []
        for             ipt in range (0, np):
            x1, y1      = self.GetPt (ipt)
            x.append    (x1)
            y.append    (y1)
        return          x, y

    def Enter (self, x: float, y: float) -> None:
        """Entra um ponto no final da poligonal.

        Args:
            x: Coordenada ``x`` em unidades de desenho.
            y: Coordenada ``y`` em unidades de desenho.
        """
        varpolig        = ctypes.c_void_p (self.m_polig)
        varx            = ctypes.c_double (x)
        vary            = ctypes.c_double (y)
        self.m_model.m_eagme.BASME_POLIG_ENTRAR (ctypes.byref (varpolig),
                        ctypes.byref (varx), ctypes.byref (vary))

    def Set (self, ipt: int, x: float, y: float) -> None:
        """Define as coordenadas de um ponto na posição ipt.

        Args:
            ipt: Índice do ponto 0..NumPts()-1.
            x: Coordenada ``x`` em unidades de desenho.
            y: Coordenada ``y`` em unidades de desenho.
        """
        varpolig        = ctypes.c_void_p (self.m_polig)
        vaript          = ctypes.c_int (ipt)
        varx            = ctypes.c_double (x)
        vary            = ctypes.c_double (y)
        self.m_model.m_eagme.BASME_POLIG_ENTRAR_IPT (ctypes.byref (varpolig),
                        ctypes.byref (vaript), ctypes.byref (varx), ctypes.byref (vary))
    def Insert (self, ipt: int, x: float, y: float) -> None:
        """Entra as coordenadas de um ponto na posição ipt e empurra os demais para frente.

        Args:
            ipt: Índice do ponto 0..NumPts()-1.
            x: Coordenada ``x`` em unidades de desenho.
            y: Coordenada ``y`` em unidades de desenho.
        """
        varpolig        = ctypes.c_void_p (self.m_polig)
        vaript          = ctypes.c_int (ipt)
        varx            = ctypes.c_double (x)
        vary            = ctypes.c_double (y)
        self.m_model.m_eagme.BASME_POLIG_INSERIR_IPT (ctypes.byref (varpolig),
                        ctypes.byref (vaript), ctypes.byref (varx), ctypes.byref (vary))

#------------------------------------------------------------------------------
#       Objeto para a criação de pilares e fundações CDadPil
#
class ColumnData ():

    """Dados para criação de pilares/fundações (``CDadPil``).

    Implementação:
        Property bag para o objeto C++ ``CDadPil`` que serve de molde na criação de
        pilares e fundações. Quase todos os métodos seguem o padrão getter/setter
        direto sobre ``BASME_DADPIL_*``.
    """
    def __init__ (self, model: "Model", dadpil: int) -> None:
        """Dados de pilares e fundações.

        Args:
            model: Objeto Model() do modelo atual.
            dadpil: Apontador para objeto CDadPil.
        """
        self.m_model    = model
        self.m_dadpil   = dadpil

    @property
    def columnDetailing (self) -> "ColumnDetailing":
        """Dados de detalhamento de pilar.

        Returns:
            :class:`ColumnDetailing` correspondente.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        detpil          = None
        vardetpil       = ctypes.c_void_p (detpil)
        self.m_model.m_eagme.BASME_DADPIL_DETPIL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (vardetpil))
        detpil          = vardetpil.value
        columndetailing = ColumnDetailing (self.m_model, detpil)
        return          columndetailing

    @property
    def columnGeometry (self) -> "ColumnGeometry":
        """Dados de geometria de pilar.

        Returns:
            :class:`ColumnGeometry` correspondente.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        geopil          = None
        vargeopil       = ctypes.c_void_p (geopil)
        self.m_model.m_eagme.BASME_DADPIL_GEOPIL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (vargeopil))
        geopil          = vargeopil.value
        columngeometry  = ColumnGeometry (self.m_model, geopil)
        return          columngeometry

    @property
    def columnInsertion (self) -> "ColumnInsertion":
        """Dados de inserção de pilar.

        Returns:
            :class:`ColumnInsertion` correspondente.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        inspil          = None
        varinspil       = ctypes.c_void_p (inspil)
        self.m_model.m_eagme.BASME_DADPIL_INSPIL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varinspil))
        inspil          = varinspil.value
        columninsertion = ColumnInsertion (self.m_model, inspil)
        return          columninsertion

    @property
    def columnPolygon (self) -> "Polygon":
        """Contorno de pilar poligonal.

        Returns:
            :class:`Polygon` correspondente.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        poligp          = None
        varpoligp       = ctypes.c_void_p (poligp)
        self.m_model.m_eagme.BASME_DADPIL_POLIGPP_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varpoligp))
        poligp          = varpoligp.value
        columnpolygon   = Polygon (self.m_model, poligp)
        return          columnpolygon

    @property
    def columnCoil (self) -> "ColumnCoil":
        """Mola do pilar no pórtico espacial.

        Returns:
            :class:`ColumnCoil` correspondente.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        pormol          = None
        varpormol       = ctypes.c_void_p (pormol)
        self.m_model.m_eagme.BASME_DADPIL_PORMOL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varpormol))
        pormol          = varpormol.value
        columncoil      = ColumnCoil (self.m_model, pormol)
        return          columncoil

    @property
    def columnIdent (self) -> "SMObjectIdent":
        """Identificação do pilar.

        Returns:
            :class:`SMObjectIdent` correspondente.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        identpil        = None
        varidentpil     = ctypes.c_void_p (identpil)
        self.m_model.m_eagme.BASME_DADPIL_IDENTPIL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varidentpil))
        identpil        = varidentpil.value
        columnident     = SMObjectIdent (self.m_model, identpil)
        return          columnident

    @property
    def columnPrecastData (self) -> "ColumnPrecastData":
        """Dados de pilar pré-moldados CPreGPil.

        Returns:
            :class:`ColumnPrecastData` correspondente.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        pregpil         = None
        varpregpil     = ctypes.c_void_p (pregpil)
        self.m_model.m_eagme.BASME_DADPIL_PREGPIL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varpregpil))
        pregpil        = varpregpil.value
        columnprecastdata = ColumnPrecastData (self.m_model, pregpil)
        return          columnprecastdata

    @property
    def columnStarts (self) -> int:
        """Pilar nasce em COLUMNSTART_xxxx.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        icodnasce       = 0
        varicodnasce    = ctypes.c_int (icodnasce)
        self.m_model.m_eagme.BASME_DADPIL_ICODNASCE_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varicodnasce))
        icodnasce       = varicodnasce.value
        return          icodnasce

    @columnStarts.setter
    def columnStarts (self, icodnasce: int) -> None:
        """Atribui Pilar nasce em COLUMNSTART_xxxx."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varicodnasce    = ctypes.c_int (icodnasce)
        self.m_model.m_eagme.BASME_DADPIL_ICODNASCE_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varicodnasce))

    @property
    def columnModel (self) -> int:
        """Modelo de pilar: COLUMNUSE_xxxxxx.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        itirante        = 0
        varitirante     = ctypes.c_int (itirante)
        self.m_model.m_eagme.BASME_DADPIL_ITIRANTE_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varitirante))
        itirante       = varitirante.value
        return          itirante

    @columnModel.setter
    def columnModel (self, itirante: int) -> None:
        """Atribui COLUMNUSE_xxxxxx."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varitirante     = ctypes.c_int (itirante)
        self.m_model.m_eagme.BASME_DADPIL_ITIRANTE_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varitirante))

    @property
    def columnWindSupport (self) -> int:
        """Suporte a vento: (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        isupvento       = 0
        varisupvento    = ctypes.c_int (isupvento)
        self.m_model.m_eagme.BASME_DADPIL_ISUPVENTO_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varisupvento))
        isupvento       = varisupvento.value
        return          isupvento

    @columnWindSupport.setter
    def columnWindSupport (self, isupvento: int) -> None:
        """Atribui (0) não (1) sim."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varisupvento    = ctypes.c_int (isupvento)
        self.m_model.m_eagme.BASME_DADPIL_ISUPVENTO_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varisupvento))
    @property
    def columnSectionMode (self) -> int:
        """Dados de condições de contorno: (0) da seção (1) do pavimento.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        idefcontpil     = 0
        varidefcontpil  = ctypes.c_int (idefcontpil)
        self.m_model.m_eagme.BASME_DADPIL_IDEFCONTPIL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varidefcontpil))
        idefcontpil     = varidefcontpil.value
        return          idefcontpil

    @columnSectionMode.setter
    def columnSectionMode (self, idefcontpil: int) -> None:
        """Atribui Dados de condições de contorno: (0) da seção (1) do pavimento."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varidefcontpil  = ctypes.c_int (idefcontpil)
        self.m_model.m_eagme.BASME_DADPIL_IDEFCONTPIL_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varidefcontpil))
    @property
    def columnInterference (self) -> int:
        """Verificação de interferências (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        iverifinter     = 0
        variverifinter  = ctypes.c_int (iverifinter)
        self.m_model.m_eagme.BASME_DADPIL_IVERIFINTER_LER (ctypes.byref (vardadpil),
                            ctypes.byref (variverifinter))
        iverifinter     = variverifinter.value
        return          iverifinter

    @columnInterference.setter
    def columnInterference (self, iverifinter: int) -> None:
        """Atribui Verificação de interferências (0) não (1) sim."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        variverifinter  = ctypes.c_int (iverifinter)
        self.m_model.m_eagme.BASME_DADPIL_IVERIFINTER_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (variverifinter))
    @property
    def columnSloped (self) -> int:
        """Pilar inclinado (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        inclinado       = 0
        varinclinado    = ctypes.c_int (inclinado)
        self.m_model.m_eagme.BASME_DADPIL_INCLINADO_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varinclinado))
        inclinado       = varinclinado.value
        return          inclinado

    @columnSloped.setter
    def columnSloped (self, inclinado: int) -> None:
        """Atribui Pilar inclinado (0) não (1) sim."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varinclinado    = ctypes.c_int (inclinado)
        self.m_model.m_eagme.BASME_DADPIL_INCLINADO_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varinclinado))

    @property
    def columnIsAFoundation (self) -> int:
        """O objeto de pilar representa uma fundação (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        ifundacao       = 0
        varifundacao    = ctypes.c_int (ifundacao)
        self.m_model.m_eagme.BASME_DADPIL_IFUNDACAO_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varifundacao))
        ifundacao       = varifundacao.value
        return          ifundacao

    @columnIsAFoundation.setter
    def columnIsAFoundation (self, ifundacao: int) -> None:
        """Atribui O objeto de pilar representa uma fundação (0) não (1) sim."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varifundacao    = ctypes.c_int (ifundacao)
        self.m_model.m_eagme.BASME_DADPIL_IFUNDACAO_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varifundacao))

    @property
    def columnHinges (self) -> int:
        """Pilar articulado em (0)CONTPOR.DAT (1)base/topo (2)base (3)topo.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        iarticbt        = 0
        variarticbt     = ctypes.c_int (iarticbt)
        self.m_model.m_eagme.BASME_DADPIL_IARTICBT_LER (ctypes.byref (vardadpil),
                            ctypes.byref (variarticbt))
        iarticbt        = variarticbt.value
        return          iarticbt

    @columnHinges.setter
    def columnHinges (self, iarticbt: int) -> None:
        """Atribui Pilar articulado em (0)CONTPOR.DAT (1)base/topo (2)base (3)topo."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        variarticbt     = ctypes.c_int (iarticbt)
        self.m_model.m_eagme.BASME_DADPIL_IARTICBT_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (variarticbt))

    @property
    def columnExport (self) -> int:
        """Pilar exportável para o 3D (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        iexportavel     = 0
        variexportavel  = ctypes.c_int (iexportavel)
        self.m_model.m_eagme.BASME_DADPIL_IEXPORTAVEL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (variexportavel))
        iexportavel     = variexportavel.value
        return          iexportavel

    @columnExport.setter
    def columnExport (self, iexportavel: int) -> None:
        """Atribui Pilar exportável para o 3D (0) não (1) sim."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        variexportavel  = ctypes.c_int (iexportavel)
        self.m_model.m_eagme.BASME_DADPIL_IEXPORTAVEL_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (variexportavel))

    @property
    def columnNonLinearity (self) -> int:
        """Coeficientes de não linearidade (0)Pilar (1)Não fissurado (2)Fissurado.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        ipilparnlf      = 0
        varipilparnlf   = ctypes.c_int (ipilparnlf)
        self.m_model.m_eagme.BASME_DADPIL_IPILPARNLF_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varipilparnlf))
        ipilparnlf      = varipilparnlf.value
        return          ipilparnlf

    @columnNonLinearity.setter
    def columnNonLinearity (self, ipilparnlf: int) -> None:
        """Atribui Coeficientes de não linearidade (0)Pilar (1)Não fissurado (2)Fissurado."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varipilparnlf   = ctypes.c_int (ipilparnlf)
        self.m_model.m_eagme.BASME_DADPIL_IPILPARNLF_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varipilparnlf))

    @property
    def columnBucklingX (self) -> float:
        """Coeficiente de flambagem X.

        Returns:
            Valor de ponto flutuante.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        cflamx          = 0
        varcflamx       = ctypes.c_double (cflamx)
        self.m_model.m_eagme.BASME_DADPIL_CFLAMX_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varcflamx))
        cflamx          = varcflamx.value
        return          cflamx

    @columnBucklingX.setter
    def columnBucklingX (self, cflamx: float) -> None:
        """Atribui Coeficiente de flambagem X."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varcflamx       = ctypes.c_double (cflamx)
        self.m_model.m_eagme.BASME_DADPIL_CFLAMX_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varcflamx))

    @property
    def columnBucklingY (self) -> float:
        """Coeficiente de flambagem Y.

        Returns:
            Valor de ponto flutuante.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        cflamy          = 0
        varcflamy       = ctypes.c_double (cflamy)
        self.m_model.m_eagme.BASME_DADPIL_CFLAMY_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varcflamy))
        cflamy          = varcflamy.value
        return          cflamy

    @columnBucklingY.setter
    def columnBucklingY (self, cflamy: float) -> None:
        """Atribui Coeficiente de flambagem Y."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varcflamy       = ctypes.c_double (cflamy)
        self.m_model.m_eagme.BASME_DADPIL_CFLAMY_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varcflamy))

    @property
    def columnDoubleStoryX (self) -> int:
        """Pé-direito duplo X (0) Geometria (1) Não (2) Sim.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        itravadox       = 0
        varitravadox    = ctypes.c_int (itravadox)
        self.m_model.m_eagme.BASME_DADPIL_ITRAVADOX_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varitravadox))
        itravadox       = varitravadox.value
        return          itravadox

    @columnDoubleStoryX.setter
    def columnDoubleStoryX (self, itravadox: int) -> None:
        """Atribui Pé-direito duplo X (0) Geometria (1) Não (2) Sim."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varitravadox    = ctypes.c_int (itravadox)
        self.m_model.m_eagme.BASME_DADPIL_ITRAVADOX_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varitravadox))

    @property
    def columnDoubleStoryY (self) -> int:
        """Pé-direito duplo X (0) Geometria (1) Não (2) Sim.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        itravadoy       = 0
        varitravadoy    = ctypes.c_int (itravadoy)
        self.m_model.m_eagme.BASME_DADPIL_ITRAVADOY_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varitravadoy))
        itravadoy       = varitravadoy.value
        return          itravadoy

    @columnDoubleStoryY.setter
    def columnDoubleStoryY (self, itravadoy: int) -> None:
        """Atribui Pé-direito duplo X (0) Geometria (1) Não (2) Sim."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varitravadoy    = ctypes.c_int (itravadoy)
        self.m_model.m_eagme.BASME_DADPIL_ITRAVADOY_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varitravadoy))

    @property
    def columnConcreteFc (self) -> str:
        """Fck diferenciado de pilar (string).

        Returns:
            Cadeia de caracteres.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varfckpil       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_DADPIL_FCKPIL_LER (ctypes.byref (vardadpil),
                            varfckpil)
        fckpil          = varfckpil.value.decode(TQSUtil.CHARSET)
        return          fckpil

    @columnConcreteFc.setter
    def columnConcreteFc (self, fckpil: str) -> None:
        """Atribui Fck diferenciado de pilar (string)."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varfckpil       = ctypes.c_char_p (fckpil.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_DADPIL_FCKPIL_DEF (ctypes.byref (vardadpil),
                            varfckpil)

    @property
    def columnBoundaryCond (self) -> "ColumnBoundaryCond":
        """Condições de contorno de pilares.

        Returns:
            :class:`ColumnBoundaryCond` correspondente.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        contpil         = None
        varcontpil      = ctypes.c_void_p (contpil)
        self.m_model.m_eagme.BASME_DADPIL_CONTPIL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varcontpil))
        contpil         = varcontpil.value
        columnboundarycond = ColumnBoundaryCond (self.m_model, contpil)
        return          columnboundarycond

    @property
    def columnCover (self) -> float:
        """Cobrimento do pilar na planta, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        cobrpil         = 0.
        varcobrpil      = ctypes.c_double (cobrpil)
        self.m_model.m_eagme.BASME_DADPIL_COBRPIL_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varcobrpil))
        cobrpil        = varcobrpil.value
        return          cobrpil

    @columnCover.setter
    def columnCover (self, cobrpil: float) -> None:
        """Atribui Cobrimento do pilar na planta, cm."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varcobrpil      = ctypes.c_double (cobrpil)
        self.m_model.m_eagme.BASME_DADPIL_COBRPIL_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varcobrpil))

    @property
    def columnExposure (self) -> int:
        """Pilar em contato com o solo (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        icontsolo       = 0
        varicontsolo    = ctypes.c_int (icontsolo)
        self.m_model.m_eagme.BASME_DADPIL_ICONTSOLO_LER (ctypes.byref (vardadpil),
                            ctypes.byref (varicontsolo))
        icontsolo       = varicontsolo.value
        return          icontsolo

    @columnExposure.setter
    def columnExposure (self, icontsolo: int) -> None:
        """Atribui Pilar em contato com o solo (0) não (1) sim."""
        vardadpil       = ctypes.c_void_p (self.m_dadpil)
        varicontsolo = ctypes.c_int (icontsolo)
        self.m_model.m_eagme.BASME_DADPIL_ICONTSOLO_DEF (ctypes.byref (vardadpil),
                            ctypes.byref (varicontsolo))

#-----------------------------------------------------------------------------
#      Dados globais por planta - CDadPav
#      Lista de plantas (mudança de seção) para os pilares criados na planta atual
#
class CurrentFloorData ():

    """Dados globais correntes por planta.

    Implementação:
        Property bag sobre o registro global ``CDadEdi`` (dados do edifício); cada
        propriedade é um par ``BASME_DADEDI_*_LER`` / ``BASME_DADEDI_*_DEF`` em ctypes.
    """
    def __init__ (self, model: "Model", floor: "Floor") -> None:
        """Dados globais por planta, que são usados na criação de objetos novos.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
        """
        self.m_model    = model
        self.m_floor    = floor

        self.drawing         = CurFloorDrawingData (model, floor)
        self.floorLoadData   = CurFloorLoadData (model, floor)
        self.floorBeamData   = CurFloorBeamData (model, floor)
        self.floorSlabData   = CurFloorSlabData (model, floor)
        self.floorColumnData = CurFloorColumnData (model, floor)
        self.floorCutData    = CurFloorCutData (model, floor)
        self.floorAxisData   = CurFloorAxisData (model, floor)

#
#       Dados globais de desenho - CurrentFloorData.drawing
#
class CurFloorDrawingData ():

    """Dados de desenho por pavimento.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", floor: "Floor") -> None:
        """Dados de desenho por pavimento.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
        """
        self.m_model          = model
        self.m_floor          = floor

    @property
    def drawingScale (self) -> float:
        """Escala da planta de formas - cm plotados por cm na escala real.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        escala          = 0.
        varescala       = ctypes.c_double (escala)
        self.m_model.m_eagme.BASME_DADPAV_ESCALA_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varescala))
        escala       = varescala.value
        return          escala

    @drawingScale.setter
    def drawingScale (self, escala: float) -> None:
        """Atribui Escala da planta de formas - cm plotados por cm na escala real."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varescala       = ctypes.c_double (escala)
        self.m_model.m_eagme.BASME_DADPAV_ESCALA_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varescala))

    @property
    def drawingMultiplier (self) -> float:
        """Multiplicador de dimensões de formas.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        dimlfc          = 0.
        vardimlfc       = ctypes.c_double (dimlfc)
        self.m_model.m_eagme.BASME_DADPAV_DIMLFC_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vardimlfc))
        dimlfc          = vardimlfc.value
        return          dimlfc

    @drawingMultiplier.setter
    def drawingMultiplier (self, dimlfc: float) -> None:
        """Atribui Multiplicador de dimensões de formas."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        vardimlfc       = ctypes.c_double (dimlfc)
        self.m_model.m_eagme.BASME_DADPAV_DIMLFC_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (vardimlfc))
#
#       Dados de cargas - CurrentFloorData.load
#
class CurFloorLoadData ():

    """Dados de cargas correntes do pavimento.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", floor: "Floor") -> None:
        """Cargas por planta.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
        """
        self.m_model          = model
        self.m_floor          = floor

    def GetLoad (self, itipocarpav: int) -> "Load":
        """Carga atual de tipo TPLOAD_xxx.

        Args:
            itipocarpav: Constante do tipo de objeto/elemento.

        Returns:
            :class:`Load` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varitipocarpav  = ctypes.c_int (itipocarpav)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_DADPAV_CARGAS_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varitipocarpav), ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx
#
#      Vigas - CurrentFloorData.beam
#
class CurFloorBeamData ():

    """Dados de vigas correntes do pavimento.

    Implementação:
        Dados correntes de viga para criação no pavimento ativo. Sub-objetos são
        expostos via @property apontando para registros em ``CDadPlanta``.
    """
    def __init__ (self, model: "Model", floor: "Floor") -> None:
        """Dados globais de vigas por planta.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
        """
        self.m_model          = model
        self.m_floor          = floor

    @property
    def beamGeometry (self) -> "BeamGeometry":
        """Geometria de viga.

        Returns:
            :class:`BeamGeometry` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        geovig          = None
        vargeovig       = ctypes.c_void_p (geovig)
        self.m_model.m_eagme.BASME_DADPAV_GEOVIG_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vargeovig))
        geovig          = vargeovig.value
        beamgeometry    = BeamGeometry (self.m_model, geovig)
        return          beamgeometry

    @property
    def beamInertia (self) -> "BeamInertia":
        """Inércia de viga.

        Returns:
            :class:`BeamInertia` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        inervig         = None
        varinervig      = ctypes.c_void_p (inervig)
        self.m_model.m_eagme.BASME_DADPAV_INERVIG_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varinervig))
        inervig         = varinervig.value
        beaminertia     = BeamInertia (self.m_model, inervig)
        return          beaminertia

    @property
    def beamBond (self) -> "BeamBond":
        """Vinculações e outros dados de viga.

        Returns:
            :class:`BeamBond` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        vincvig         = None
        varvincvig      = ctypes.c_void_p (vincvig)
        self.m_model.m_eagme.BASME_DADPAV_VINCVIG_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varvincvig))
        vincvig         = varvincvig.value
        beambond        = BeamBond (self.m_model, vincvig)
        return          beambond

    @property
    def beamInsertion (self) -> "BeamInsertion":
        """Dados de inserção de vigas.

        Returns:
            :class:`BeamInsertion` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        insvig          = None
        varinsvig       = ctypes.c_void_p (insvig)
        self.m_model.m_eagme.BASME_DADPAV_INSVIG_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varinsvig))
        insvig          = varinsvig.value
        beaminsertion   = BeamInsertion (self.m_model, insvig)
        return          beaminsertion

    @property
    def beamTemperShrink (self) -> "TemperatureShrink":
        """Temperatura / retração de vigas.

        Returns:
            :class:`TemperatureShrink` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        tempretvig      = None
        vartempretvig   = ctypes.c_void_p (tempretvig)
        self.m_model.m_eagme.BASME_DADPAV_TEMPRETVIG_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vartempretvig))
        tempretvig      = vartempretvig.value
        beamtempershrink= TemperatureShrink (self.m_model, tempretvig)
        return          beamtempershrink

    @property
    def beamDetailing (self) -> "BeamDetailing":
        """Detalhamento de vigas.

        Returns:
            :class:`BeamDetailing` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        detvig          = None
        vardetvig       = ctypes.c_void_p (detvig)
        self.m_model.m_eagme.BASME_DADPAV_DETVIG_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vardetvig))
        detvig          = vardetvig.value
        beamdetailing   = BeamDetailing (self.m_model, detvig)
        return          beamdetailing

    @property
    def beamOpening (self) -> "BeamOpening":
        """Furo em viga.

        Returns:
            :class:`BeamOpening` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        furovig         = None
        varfurovig      = ctypes.c_void_p (furovig)
        self.m_model.m_eagme.BASME_DADPAV_FUROVIG_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varfurovig))
        furovig         = varfurovig.value
        beamopening     = BeamOpening (self.m_model, furovig)
        return          beamopening

    @property
    def beamIdent (self) -> "SMObjectIdent":
        """Identificação de viga.

        Returns:
            :class:`SMObjectIdent` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        identvig        = None
        varidentvig     = ctypes.c_void_p (identvig)
        self.m_model.m_eagme.BASME_DADPAV_IDENTVIG_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varidentvig))
        identvig        = varidentvig.value
        beamident       = SMObjectIdent (self.m_model, identvig)
        return          beamident

    @property
    def beamFirstNumber (self) -> int:
        """Numero da primeira viga.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        iprimviga       = 0
        variprimviga    = ctypes.c_int (iprimviga)
        self.m_model.m_eagme.BASME_DADPAV_IPRIMVIGA_LER (ctypes.byref (varfabrica),
                            ctypes.byref (variprimviga))
        iprimviga       = variprimviga.value
        return          iprimviga

    @beamFirstNumber.setter
    def beamFirstNumber (self, iprimviga: int) -> None:
        """Atribui Numero da primeira viga."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        variprimviga    = ctypes.c_int (iprimviga)
        self.m_model.m_eagme.BASME_DADPAV_IPRIMVIGA_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (variprimviga))

    @property
    def beamExport (self) -> int:
        """Viga exportável para o 3D (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        iexportavelv    = 0
        variexportavelv = ctypes.c_int (iexportavelv)
        self.m_model.m_eagme.BASME_DADPAV_IEXPORTAVELV_LER (ctypes.byref (varfabrica),
                            ctypes.byref (variexportavelv))
        iexportavelv    = variexportavelv.value
        return          iexportavelv

    @beamExport.setter
    def beamExport (self, iexportavelv: int) -> None:
        """Atribui Viga exportável para o 3D (0) não (1) sim."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        variexportavelv = ctypes.c_int (iexportavelv)
        self.m_model.m_eagme.BASME_DADPAV_IEXPORTAVELV_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (variexportavelv))
#
#      Lajes - CurrentFloorData.slab
#
class CurFloorSlabData ():

    """Dados de lajes correntes do pavimento.

    Implementação:
        Dados correntes de laje no pavimento ativo. Property bag com sub-objetos para
        geometria, malha, temperatura/retração e detalhamento.
    """
    def __init__ (self, model: "Model", floor: "Floor") -> None:
        """Dados globais de lajes por planta.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
        """
        self.m_model          = model
        self.m_floor          = floor

    @property
    def slabPlastification (self) -> int:
        """Engaste em viga (0) livre (1) apoio (2) engast laje.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        iengast         = 0
        variengast      = ctypes.c_int (iengast)
        self.m_model.m_eagme.BASME_DADPAV_IENGAST_LER (ctypes.byref (varfabrica),
                            ctypes.byref (variengast))
        iengast         = variengast.value
        return          iengast

    @slabPlastification.setter
    def slabPlastification (self, iengast: int) -> None:
        """Atribui Engaste em viga (0) livre (1) apoio (2) engast laje."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        variengast      = ctypes.c_int (iengast)
        self.m_model.m_eagme.BASME_DADPAV_IENGAST_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (variengast))

    @property
    def slabReleaseFx (self) -> int:
        """Liberar Fx no apoio da laje (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        ilivrfx         = 0
        varilivrfx      = ctypes.c_int (ilivrfx)
        self.m_model.m_eagme.BASME_DADPAV_ILIVRFX_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varilivrfx))
        ilivrfx         = varilivrfx.value
        return          ilivrfx

    @slabReleaseFx.setter
    def slabReleaseFx (self, ilivrfx: int) -> None:
        """Atribui Liberar Fx no apoio da laje (0) não (1) sim."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varilivrfx      = ctypes.c_int (ilivrfx)
        self.m_model.m_eagme.BASME_DADPAV_ILIVRFX_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varilivrfx))

    @property
    def slabFixedSupport (self) -> float:
        """Valor de engaste de bordo (0..1).

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        valengast       = 0
        varvalengast    = ctypes.c_double (valengast)
        self.m_model.m_eagme.BASME_DADPAV_VALENGAST_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varvalengast))
        valengast       = varvalengast.value
        return          valengast

    @slabFixedSupport.setter
    def slabFixedSupport (self, valengast: float) -> None:
        """Atribui Valor de engaste de bordo (0..1)."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varvalengast    = ctypes.c_double (valengast)
        self.m_model.m_eagme.BASME_DADPAV_VALENGAST_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varvalengast))

    @property
    def dropPanelThickness (self) -> float:
        """Altura de capitel cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        caph            = 0
        varcaph         = ctypes.c_double (caph)
        self.m_model.m_eagme.BASME_DADPAV_CAPH_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varcaph))
        caph            = varcaph.value
        return          caph

    @dropPanelThickness.setter
    def dropPanelThickness (self, caph: float) -> None:
        """Atribui Altura de capitel cm."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varcaph         = ctypes.c_double (caph)
        self.m_model.m_eagme.BASME_DADPAV_CAPH_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varcaph))

    @property
    def dropPanelDiv (self) -> float:
        """Divisor de flexão de capitel.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        capdivflx       = 0
        varcapdivflx    = ctypes.c_double (capdivflx)
        self.m_model.m_eagme.BASME_DADPAV_CAPDIVFLX_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varcapdivflx))
        capdivflx       = varcapdivflx.value
        return          capdivflx

    @dropPanelDiv.setter
    def dropPanelDiv (self, capdivflx: float) -> None:
        """Atribui Divisor de flexão de capitel."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varcapdivflx    = ctypes.c_double (capdivflx)
        self.m_model.m_eagme.BASME_DADPAV_CAPDIVFLX_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varcapdivflx))

    @property
    def slabMouldBasePoint (self) -> int:
        """Ponto base de inserção de nervura (0..5).

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        ibasenerv       = 0
        varibasenerv    = ctypes.c_int (ibasenerv)
        self.m_model.m_eagme.BASME_DADPAV_IBASENERV_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varibasenerv))
        ibasenerv       = varibasenerv.value
        return          ibasenerv

    @slabMouldBasePoint.setter
    def slabMouldBasePoint (self, ibasenerv: int) -> None:
        """Atribui Ponto base de inserção de nervura (0..5)."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varibasenerv    = ctypes.c_int (ibasenerv)
        self.m_model.m_eagme.BASME_DADPAV_IBASENERV_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varibasenerv))

    @property
    def slabMouldXSize (self) -> float:
        """Tamanho X da forma de nervura cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        tamxnerv        = 0
        vartamxnerv     = ctypes.c_double (tamxnerv)
        self.m_model.m_eagme.BASME_DADPAV_TAMXNERV_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vartamxnerv))
        tamxnerv        = vartamxnerv.value
        return          tamxnerv

    @slabMouldXSize.setter
    def slabMouldXSize (self, tamxnerv: float) -> None:
        """Atribui Tamanho X da forma de nervura cm."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        vartamxnerv     = ctypes.c_double (tamxnerv)
        self.m_model.m_eagme.BASME_DADPAV_TAMXNERV_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (vartamxnerv))

    @property
    def slabMouldYSize (self) -> float:
        """Tamanho Y da forma de nervura cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        tamynerv        = 0
        vartamynerv     = ctypes.c_double (tamynerv)
        self.m_model.m_eagme.BASME_DADPAV_TAMYNERV_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vartamynerv))
        tamynerv        = vartamynerv.value
        return          tamynerv

    @slabMouldYSize.setter
    def slabMouldYSize (self, tamynerv: float) -> None:
        """Atribui Tamanho Y da forma de nervura cm."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        vartamynerv     = ctypes.c_double (tamynerv)
        self.m_model.m_eagme.BASME_DADPAV_TAMYNERV_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (vartamynerv))

    @property
    def slabMouldXSpace (self) -> float:
        """Espaçamento X de forma de nervura cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        expxnerv        = 0
        varexpxnerv     = ctypes.c_double (expxnerv)
        self.m_model.m_eagme.BASME_DADPAV_ESPXNERV_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varexpxnerv))
        expxnerv        = varexpxnerv.value
        return          expxnerv

    @slabMouldXSpace.setter
    def slabMouldXSpace (self, expxnerv: float) -> None:
        """Atribui Espaçamento X de forma de nervura cm."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varexpxnerv     = ctypes.c_double (expxnerv)
        self.m_model.m_eagme.BASME_DADPAV_ESPXNERV_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varexpxnerv))

    @property
    def slabMouldYSpace (self) -> float:
        """Espaçamento Y de forma de nervura cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        expynerv        = 0.
        varexpynerv     = ctypes.c_double (expynerv)
        self.m_model.m_eagme.BASME_DADPAV_ESPYNERV_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varexpynerv))
        expynerv        = varexpynerv.value
        return          expynerv

    @slabMouldYSpace.setter
    def slabMouldYSpace (self, expynerv: float) -> None:
        """Atribui Espaçamento Y de forma de nervura cm."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varexpynerv     = ctypes.c_double (expynerv)
        self.m_model.m_eagme.BASME_DADPAV_ESPYNERV_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varexpynerv))

    @property
    def slabFirstNumber (self) -> int:
        """Número da primeira laje.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        iprimlaje       = 0
        variprimlaje    = ctypes.c_int (iprimlaje)
        self.m_model.m_eagme.BASME_DADPAV_IPRIMLAJE_LER (ctypes.byref (varfabrica),
                            ctypes.byref (variprimlaje))
        iprimlaje       = variprimlaje.value
        return          iprimlaje

    @slabFirstNumber.setter
    def slabFirstNumber (self, iprimlaje: int) -> None:
        """Atribui Número da primeira laje."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        variprimlaje    = ctypes.c_int (iprimlaje)
        self.m_model.m_eagme.BASME_DADPAV_IPRIMLAJE_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (variprimlaje))

    @property
    def slabExport (self) -> int:
        """Exportar a laje para visualização 3D (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        iexportavell    = 0
        variexportavell = ctypes.c_int (iexportavell)
        self.m_model.m_eagme.BASME_DADPAV_IEXPORTAVELL_LER (ctypes.byref (varfabrica),
                            ctypes.byref (variexportavell))
        iexportavell    = variexportavell.value
        return          iexportavell

    @slabExport.setter
    def slabExport (self, iexportavell: int) -> None:
        """Atribui Exportar a laje para visualização 3D (0) não (1) sim."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        variexportavell = ctypes.c_int (iexportavell)
        self.m_model.m_eagme.BASME_DADPAV_IEXPORTAVELL_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (variexportavell))

    @property
    def stairTitle (self) -> str:
        """Título de escada.

        Returns:
            Cadeia de caracteres.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varidentesc     = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_DADPAV_IDENTESC_LER (ctypes.byref (varfabrica),
                            varidentesc)
        identesc        = varidentesc.value.decode(TQSUtil.CHARSET)
        return         identesc

    @stairTitle.setter
    def stairTitle (self, identesc: str) -> None:
        """Atribui Título de escada."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varidentesc     = ctypes.c_char_p (identesc.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_DADPAV_IDENTESC_DEF (ctypes.byref (varfabrica),
                            varidentesc)
    @property
    def slabGeometry (self) -> "SlabGeometry":
        """Dados de geometria de laje.

        Returns:
            :class:`SlabGeometry` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        geolaj          = None
        vargeolaj       = ctypes.c_void_p (geolaj)
        self.m_model.m_eagme.BASME_DADPAV_GEOLAJ_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vargeolaj))
        geolaj          = vargeolaj.value
        slabGeometry    = SlabGeometry (self.m_model, geolaj)
        return          slabGeometry

    @property
    def slabGrid (self) -> "SlabGrid":
        """Dados para discretização de laje por grelha.

        Returns:
            :class:`SlabGrid` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        grelaj          = None
        vargrelaj       = ctypes.c_void_p (grelaj)
        self.m_model.m_eagme.BASME_DADPAV_GRELAJ_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vargrelaj))
        grelaj         = vargrelaj.value
        slabgrid        = SlabGrid (self.m_model, grelaj)
        return          slabgrid

    @property
    def slabTemperShrink (self) -> "TemperatureShrink":
        """Temperatura / retração de lajes.

        Returns:
            :class:`TemperatureShrink` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        tempretlaj      = None
        vartempretlaj   = ctypes.c_void_p (tempretlaj)
        self.m_model.m_eagme.BASME_DADPAV_TEMPRETLAJ_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vartempretlaj))
        tempretlaj      = vartempretlaj.value
        slabtempershrink= TemperatureShrink (self.m_model, tempretlaj)
        return          slabtempershrink

    @property
    def slabDetailing (self) -> "SlabDetailing":
        """Detalhamento de lajes.

        Returns:
            :class:`SlabDetailing` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        detlaj          = None
        vardetlaj       = ctypes.c_void_p (detlaj)
        self.m_model.m_eagme.BASME_DADPAV_DETLAJ_LER (ctypes.byref (varfabrica),
                            ctypes.byref (vardetlaj))
        detlaj          = vardetlaj.value
        slabdetailing   = SlabDetailing (self.m_model, detlaj)
        return          slabdetailing

    @property
    def slabIdent (self) -> "SMObjectIdent":
        """Identificação de lajes.

        Returns:
            :class:`SMObjectIdent` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        identlaj        = None
        varidentlaj     = ctypes.c_void_p (identlaj)
        self.m_model.m_eagme.BASME_DADPAV_IDENTLAJ_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varidentlaj))
        identlaj        = varidentlaj.value
        slabident       = SMObjectIdent (self.m_model, identlaj)
        return          slabident
#
#      Pilares - CurrentFloorData.column
#
class CurFloorColumnData ():

    """Dados de pilares correntes do pavimento.

    Implementação:
        Dados correntes de pilar no pavimento ativo. ``columnFloorNames`` instancia o
        iterador de nomes de pavimento associados.
    """
    def __init__ (self, model: "Model", floor: "Floor") -> None:
        """Dados globais de pilares por planta.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
        """
        self.m_model          = model
        self.m_floor          = floor

    @property
    def columnFloorNames (self) -> "ColumnFloorNames":
        """Lista de plantas de pilares.

        Returns:
            :class:`ColumnFloorNames` correspondente.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        plapil          = None
        varplapil       = ctypes.c_void_p (plapil)
        self.m_model.m_eagme.BASME_DADPAV_PLAPIL_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varplapil))
        plapil          = varplapil.value
        columnfloornames= ColumnFloorNames (self.m_model, plapil)
        return          columnfloornames

    @property
    def columnDynHorLoad (self) -> int:
        """Carga dinâmica de veiculo em pilar (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        icargadinvuc    = 0
        varicargadinvuc = ctypes.c_int (icargadinvuc)
        self.m_model.m_eagme.BASME_DADPAV_ICARGADINVUC_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varicargadinvuc))
        icargadinvuc    = varicargadinvuc.value
        return          icargadinvuc

    @columnDynHorLoad.setter
    def columnDynHorLoad (self, icargadinvuc: int) -> None:
        """Atribui Carga dinâmica de veiculo em pilar (0) não (1) sim."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varicargadinvuc = ctypes.c_int (icargadinvuc)
        self.m_model.m_eagme.BASME_DADPAV_ICARGADINVUC_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varicargadinvuc))

#
#      Cortes - CurrentFloorData.cut
#
class CurFloorCutData ():

    """Dados de cortes correntes do pavimento.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", floor: "Floor") -> None:
        """Dados globais de cortes por planta.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
        """
        self.m_model          = model
        self.m_floor          = floor

    @property
    def cutTitle (self) -> str:
        """Último título de corte.

        Returns:
            Cadeia de caracteres.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        vartitcor       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_DADPAV_TITCOR_LER (ctypes.byref (varfabrica),
                            vartitcor)
        titcor          = vartitcor.value.decode(TQSUtil.CHARSET)
        return          titcor

    @cutTitle.setter
    def cutTitle (self, titcor: str) -> None:
        """Atribui Último título de corte."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        vartitcor      = ctypes.c_char_p (titcor.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_DADPAV_TITCOR_DEF (ctypes.byref (varfabrica),
                            vartitcor)
#
#      Eixos - CurrentFloorData.axis
#
class CurFloorAxisData ():

    """Dados de eixos correntes do pavimento.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", floor: "Floor") -> None:
        """Dados globais de eixos por planta.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
        """
        self.m_model          = model
        self.m_floor          = floor

    @property
    def axisHorLabel (self) -> str:
        """Último rotulo de eixo horizontal.

        Returns:
            Cadeia de caracteres.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varrotuloh      = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_DADPAV_ROTULOH_LER (ctypes.byref (varfabrica),
                            varrotuloh)
        rotuloh         = varrotuloh.value.decode(TQSUtil.CHARSET)
        return          rotuloh

    @axisHorLabel.setter
    def axisHorLabel (self, rotuloh: str) -> None:
        """Atribui Último rotulo de eixo horizontal."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varrotuloh      = ctypes.c_char_p (rotuloh.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_DADPAV_ROTULOH_DEF (ctypes.byref (varfabrica),
                            varrotuloh)
    @property
    def axisVerLabel (self) -> str:
        """Último rótulo de eixo vertical.

        Returns:
            Cadeia de caracteres.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varrotulov      = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_DADPAV_ROTULOV_LER (ctypes.byref (varfabrica),
                            varrotulov)
        rotulov         = varrotulov.value.decode(TQSUtil.CHARSET)
        return          rotulov

    @axisVerLabel.setter
    def axisVerLabel (self, rotulov: str) -> None:
        """Atribui Último rótulo de eixo vertical."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varrotulov      = ctypes.c_char_p (rotulov.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_DADPAV_ROTULOV_DEF (ctypes.byref (varfabrica),
                            varrotulov)

    @property
    def axisSlopedLabel (self) -> str:
        """Último rótulo de eixo inclinado.

        Returns:
            Cadeia de caracteres.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varrotuloi      = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_DADPAV_ROTULOI_LER (ctypes.byref (varfabrica),
                            varrotuloi)
        rotuloi         = varrotuloi.value.decode(TQSUtil.CHARSET)
        return          rotuloi

    @axisSlopedLabel.setter
    def axisSlopedLabel (self, rotuloi: str) -> None:
        """Atribui Último rótulo de eixo inclinado."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varrotuloi      = ctypes.c_char_p (rotuloi.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_DADPAV_ROTULOI_DEF (ctypes.byref (varfabrica),
                            varrotuloi)

    @property
    def axisAngle (self) -> float:
        """Último angulo de eixo graus.

        Returns:
            Valor de ponto flutuante.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        angeixo         = 0.
        varangeixo      = ctypes.c_double (angeixo)
        self.m_model.m_eagme.BASME_DADPAV_ANGEIXO_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varangeixo))
        angeixo        = varangeixo.value
        return          angeixo

    @axisAngle.setter
    def axisAngle (self, angeixo: float) -> None:
        """Atribui Último angulo de eixo graus."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varangeixo      = ctypes.c_double (angeixo)
        self.m_model.m_eagme.BASME_DADPAV_ANGEIXO_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varangeixo))

    @property
    def unlockAxisAngle (self) -> int:
        """(0) Eixos em X e Y globais (1) ângulo qualquer.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        iangeixo        = 0
        variangeixo     = ctypes.c_int (iangeixo)
        self.m_model.m_eagme.BASME_DADPAV_IANGEIXO_LER (ctypes.byref (varfabrica),
                            ctypes.byref (variangeixo))
        iangeixo        = variangeixo.value
        return          iangeixo

    @unlockAxisAngle.setter
    def unlockAxisAngle (self, iangeixo: int) -> None:
        """Atribui (0) Eixos em X e Y globais (1) ângulo qualquer."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        variangeixo     = ctypes.c_int (iangeixo)
        self.m_model.m_eagme.BASME_DADPAV_IANGEIXO_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (variangeixo))

    @property
    def axisDirection (self) -> int:
        """Eixo na direção (0) X (1) Y.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        idirecaoeixo    = 0
        varidirecaoeixo = ctypes.c_int (idirecaoeixo)
        self.m_model.m_eagme.BASME_DADPAV_IDIRECAOEIXO_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varidirecaoeixo))
        idirecaoeixo    = varidirecaoeixo.value
        return          idirecaoeixo

    @axisDirection.setter
    def axisDirection (self, idirecaoeixo: int) -> None:
        """Atribui Eixo na direção (0) X (1) Y."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varidirecaoeixo = ctypes.c_int (idirecaoeixo)
        self.m_model.m_eagme.BASME_DADPAV_IDIRECAOEIXO_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varidirecaoeixo))

    @property
    def axisDimOrigin (self) -> int:
        """Cotar distância à origem (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        icotardisteixo  = 0
        varicotardisteixo= ctypes.c_int (icotardisteixo)
        self.m_model.m_eagme.BASME_DADPAV_ICOTARDISTEIXO_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varicotardisteixo))
        icotardisteixo  = varicotardisteixo.value
        return          icotardisteixo

    @axisDimOrigin.setter
    def axisDimOrigin (self, icotardisteixo: int) -> None:
        """Atribui Cotar distância à origem (0) não (1) sim."""
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varicotardisteixo= ctypes.c_int (icotardisteixo)
        self.m_model.m_eagme.BASME_DADPAV_ICOTARDISTEIXO_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varicotardisteixo))
#------------------------------------------------------------------------------
#       Objeto base do Modelador Estrutural - vigas, pilares, lajes, etc
#
class SMObject ():

    """Objeto base do Modelador (``CObjMe``).

    Implementação:
        Base comum dos objetos do Modelador (``CObjMe``). Concentra operações
        geométricas (``Move``, ``Rotate``), identificadores e leitura/escrita de GUID;
        classes filhas adicionam atributos específicos do tipo de elemento estrutural.
    """
    def __init__ (self, model: "Model", objme: int) -> None:
        """Inicialização de um objeto do Modelador.

        Args:
            model: Modelo estrutural (:class:`Model`).
            objme: Parâmetro ``objme``.
        """
        self.m_model  = model
        self.m_objme  = objme

    @property
    def type (self) -> int:
        """Tipo do objeto (TQSModel.TYPE_xxxx).

        Returns:
            Valor inteiro.
        """
        varobjme    = ctypes.c_void_p (self.m_objme)
        ilista      = 0
        varilista   = ctypes.c_int (ilista)
        self.m_model.m_eagme.BASME_OBJ_LISTA_LER (ctypes.byref (varobjme),
                        ctypes.byref (varilista))
        ilista      = varilista.value
        return      ilista

    @type.setter
    def type (self, ilista: int) -> None:
        """Atribui Tipo do objeto (TQSModel.TYPE_xxxx)."""
        varobjme        = ctypes.c_void_p (self.m_objme)
        varilista       = ctypes.c_int (ilista)
        self.m_model.m_eagme.BASME_OBJ_LISTA_DEF (ctypes.byref (varobjme),
                        ctypes.byref (varilista))

    @property
    def identobj (self) -> int:
        """Identificador único do objeto.

        Returns:
            Valor inteiro.
        """
        varobjme        = ctypes.c_void_p (self.m_objme)
        identobj        = 0
        varidentobj     = ctypes.c_int (identobj)
        self.m_model.m_eagme.BASME_OBJ_IDENTOBJ_LER (ctypes.byref (varobjme),
                        ctypes.byref(varidentobj))
        identobj        = varidentobj.value
        return          identobj

    @identobj.setter
    def identobj (self, identobj: int) -> None:
        """Atribui Identificador único do objeto."""
        varobjme        = ctypes.c_void_p (self.m_objme)
        varidentobj     = ctypes.c_int (identobj)
        self.m_model.m_eagme.BASME_OBJ_IDENTOBJ_DEF (ctypes.byref (varobjme),
                        ctypes.byref(varidentobj))
        identobj        = varidentobj.value
        return          identobj

    @property
    def number (self) -> int:
        """Número do objeto.

        Returns:
            Valor inteiro.
        """
        varobjme        = ctypes.c_void_p (self.m_objme)
        inum            = 0
        varinum         = ctypes.c_int (inum)
        self.m_model.m_eagme.BASME_OBJ_INUM_LER (ctypes.byref (varobjme),
                        ctypes.byref (varinum))
        inum            = varinum.value
        return          inum

    @number.setter
    def number (self, inum: int) -> None:
        """Atribui Número do objeto."""
        varobjme        = ctypes.c_void_p (self.m_objme)
        varinum         = ctypes.c_int (inum)
        self.m_model.m_eagme.BASME_OBJ_INUM_DEF (ctypes.byref (varobjme),
                        ctypes.byref (varinum))

    @property
    def title (self) -> str:
        """Título opcional do objeto.

        Returns:
            Cadeia de caracteres.
        """
        varobjme        = ctypes.c_void_p (self.m_objme)
        vartitulo       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_OBJ_TITULO_LER (ctypes.byref (varobjme), vartitulo)
        title           = vartitulo.value.decode(TQSUtil.CHARSET)
        return         title

    @title.setter
    def title (self, titulo: str) -> None:
        """Atribui Título opcional do objeto."""
        varobjme        = ctypes.c_void_p (self.m_objme)
        vartitulo       = ctypes.c_char_p (titulo.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_OBJ_TITULO_DEF (ctypes.byref (varobjme), vartitulo)

    @property
    def formattedTitle (self) -> str:
        """Título considerando número e título opcional.

        Returns:
            Cadeia de caracteres.
        """
        varobjme        = ctypes.c_void_p (self.m_objme)
        vartitulo       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_OBJ_TITULO_FORMATADO (ctypes.byref (varobjme), vartitulo)
        formattedTitle  = vartitulo.value.decode(TQSUtil.CHARSET)
        return         formattedTitle

    def GetGuid (self, iadic: int, ipiso: int, itrecho: int) -> str:
        """iadic.

        Args:
            iadic: Número adicional para diferenciar pisos e trechos.
            ipiso: int Piso.
            itrecho: int Trecho opcional.

        Returns:
            Identificador GUID.
        """
        varobjme        = ctypes.c_void_p (self.m_objme)
        variadic        = ctypes.c_int (iadic)
        varipiso        = ctypes.c_int (ipiso)
        varitrecho      = ctypes.c_int (itrecho)
        varguid         = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_OBJ_LERGUID (ctypes.byref (varobjme),
                        ctypes.byref (variadic), ctypes.byref (varipiso),
                        ctypes.byref (varitrecho), varguid)
        guid            = varguid.value.decode(TQSUtil.CHARSET)
        return          guid
#
#       Operações de edição virtuais com objetos
#
    def Move (self, floor: "Floor", dx: float, dy: float) -> None:
        """Mover um objeto.

        Args:
            floor: Planta corrente (:class:`Floor`).
            dx: Parâmetro ``dx``.
            dy: Parâmetro ``dy``.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_objme)
        vardx           = ctypes.c_double (dx)
        vardy           = ctypes.c_double (dy)
        self.m_model.m_eagme.BASME_EDIT_MOVER (                                 \
                        ctypes.byref (varfabrica), ctypes.byref (varobjme),     \
                        ctypes.byref (vardx), ctypes.byref (vardy))

    def Rotate (self, floor: "Floor", cx: float, cy: float, ang: float) -> None:
        """Rodar um objeto.

        Args:
            floor: Planta corrente (:class:`Floor`).
            cx: Parâmetro ``cx``.
            cy: Parâmetro ``cy``.
            ang: Parâmetro ``ang``.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_objme)
        varcx           = ctypes.c_double (cx)
        varcy           = ctypes.c_double (cy)
        varang          = ctypes.c_double (ang)
        self.m_model.m_eagme.BASME_EDIT_RODAR (                                 \
                        ctypes.byref (varfabrica), ctypes.byref (varobjme),     \
                        ctypes.byref (varcx), ctypes.byref (varcy), ctypes.byref (varang))

    def Scale (self, floor: "Floor", cx: float, cy: float, escala: float) -> None:
        """Escalar um objeto.

        Args:
            floor: Planta corrente (:class:`Floor`).
            cx: Parâmetro ``cx``.
            cy: Parâmetro ``cy``.
            escala: Parâmetro ``escala``.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_objme)
        varcx           = ctypes.c_double (cx)
        varcy           = ctypes.c_double (cy)
        varescala       = ctypes.c_double (escala)
        self.m_model.m_eagme.BASME_EDIT_ESCALAR (                               \
                        ctypes.byref (varfabrica), ctypes.byref (varobjme),     \
                        ctypes.byref (varcx), ctypes.byref (varcy), ctypes.byref (varescala))

    def Mirror (self, floor: "Floor", x1: float, y1: float, x2: float, y2: float) -> None:
        """Espelhar um objeto.

        Args:
            floor: Planta corrente (:class:`Floor`).
            x1: Coordenada ``x1`` em unidades de desenho.
            y1: Coordenada ``y1`` em unidades de desenho.
            x2: Coordenada ``x2`` em unidades de desenho.
            y2: Coordenada ``y2`` em unidades de desenho.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_objme)
        varx1           = ctypes.c_double (x1)
        vary1           = ctypes.c_double (y1)
        varx2           = ctypes.c_double (x2)
        vary2           = ctypes.c_double (y2)
        self.m_model.m_eagme.BASME_EDIT_ESPELHAR (                                      \
                        ctypes.byref (varfabrica), ctypes.byref (varobjme),             \
                        ctypes.byref (varx1), ctypes.byref (vary1),                     \
                        ctypes.byref (varx2), ctypes.byref (vary2))

    def Copy (self, floor: "Floor") -> Any:
        """Cria um novo objeto SMObject, cópia do objeto original.

        Args:
            floor: Planta corrente (:class:`Floor`).

        Returns:
            smobject        Objeto duplicado.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_objme)
        varobjmenov     = ctypes.c_void_p (None)
        self.m_model.m_eagme.BASME_EDIT_COPIAR (                                        \
                        ctypes.byref (varfabrica), ctypes.byref (varobjme),             \
                        ctypes.byref (varobjmenov))
        objme           = varobjmenov.value
        smobject        = floor.iterator.DerivedObject (objme)
        return         smobject

    def Erase (self, floor: "Floor") -> None:
        """Apaga um objeto SMObject.

        Args:
            floor: Planta corrente (:class:`Floor`).
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varobjme        = ctypes.c_void_p (self.m_objme)
        self.m_model.m_eagme.BASME_EDIT_APAGAR (                                        \
                        ctypes.byref (varfabrica), ctypes.byref (varobjme))

#------------------------------------------------------------------------------
#       Um Pilar
#
class Column (SMObject):

    """Pilar do modelo estrutural.

    Implementação:
        Wrapper de pilar (``CPilar``). Compõe sub-objetos ``columnGeometry``,
        ``columnInsertion``, ``columnCoil``, etc. cada um exposto via @property que
        chama ``BASME_PILAR_*_LER`` e devolve a instância Python apropriada.
    """
    def __init__ (self, model: "Model", floor: "Floor", pilar: int) -> None:
        """Criação de um pilar.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor() da planta atual.
            pilar: Objeto CPilares do Modelador.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_pilar    = pilar
        super().__init__(model, self.m_pilar)


    @property
    def columnDetailing (self) -> "ColumnDetailing":
        """Dados de detalhamento de pilar.

        Returns:
            :class:`ColumnDetailing` correspondente.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        detpil          = None
        vardetpil       = ctypes.c_void_p (detpil)
        self.m_model.m_eagme.BASME_PILARES_DETPIL_LER (ctypes.byref (varpilar),
                            ctypes.byref (vardetpil))
        detpil          = vardetpil.value
        columndetailing = ColumnDetailing (self.m_model, detpil)
        return          columndetailing

    @property
    def columnIdent (self) -> "SMObjectIdent":
        """Identificação do pilar.

        Returns:
            :class:`SMObjectIdent` correspondente.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        identpil        = None
        varidentpil     = ctypes.c_void_p (identpil)
        self.m_model.m_eagme.BASME_PILARES_IDENTPIL_LER (ctypes.byref (varpilar),
                            ctypes.byref (varidentpil))
        identpil        = varidentpil.value
        columnident     = SMObjectIdent (self.m_model, identpil)
        return          columnident

    @property
    def columnStarts (self) -> int:
        """Pilar nasce em COLUMNSTART_xxxx.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        icodnasce       = 0
        varicodnasce    = ctypes.c_int (icodnasce)
        self.m_model.m_eagme.BASME_PILARES_ICODNASCE_LER (ctypes.byref (varpilar),
                            ctypes.byref (varicodnasce))
        icodnasce       = varicodnasce.value
        return          icodnasce

    @columnStarts.setter
    def columnStarts (self, icodnasce: int) -> None:
        """Atribui Pilar nasce em COLUMNSTART_xxxx."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varicodnasce    = ctypes.c_int (icodnasce)
        self.m_model.m_eagme.BASME_PILARES_ICODNASCE_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varicodnasce))

    @property
    def columnModel (self) -> int:
        """Modelo de pilar: COLUMNUSE_xxxxxx.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        itirante        = 0
        varitirante     = ctypes.c_int (itirante)
        self.m_model.m_eagme.BASME_PILARES_ITIRANTE_LER (ctypes.byref (varpilar),
                            ctypes.byref (varitirante))
        itirante       = varitirante.value
        return          itirante

    @columnModel.setter
    def columnModel (self, itirante: int) -> None:
        """Atribui COLUMNUSE_xxxxxx."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varitirante     = ctypes.c_int (itirante)
        self.m_model.m_eagme.BASME_PILARES_ITIRANTE_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varitirante))

    @property
    def hasFixedPoint (self) -> int:
        """(1) Se o pilar tem um ponto fixo.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        ifixedpoint     = 0
        varifixedpoint  = ctypes.c_int (ifixedpoint)
        self.m_model.m_eagme.BASME_PILARES_IPTFIXO_LER (ctypes.byref (varpilar),
                            ctypes.byref (varifixedpoint))
        ifixedpoint     = varifixedpoint.value
        return          ifixedpoint

    @hasFixedPoint.setter
    def hasFixedPoint (self, ifixedpoint: int) -> None:
        """Atribui (1) Se o pilar tem um ponto fixo."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varifixedpoint  = ctypes.c_int (ifixedpoint)
        self.m_model.m_eagme.BASME_PILARES_IPTFIXO_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varifixedpoint))

    @property
    def fixedPointX (self) -> float:
        """X do ponto fixo do pilar.

        Returns:
            Valor de ponto flutuante.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        fixedpointx     = 0.
        varfixedpointx  = ctypes.c_double (fixedpointx)
        self.m_model.m_eagme.BASME_PILARES_PTFIXOX_LER (ctypes.byref (varpilar),
                            ctypes.byref (varfixedpointx))
        fixedpointx     = varfixedpointx.value
        return          fixedpointx

    @fixedPointX.setter
    def fixedPointX (self, fixedpointx: float) -> None:
        """Atribui X do ponto fixo do pilar."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varfixedpointx  = ctypes.c_double (fixedpointx)
        self.m_model.m_eagme.BASME_PILARES_PTFIXOX_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varfixedpointx))

    @property
    def fixedPointY (self) -> float:
        """Y do ponto fixo do pilar.

        Returns:
            Valor de ponto flutuante.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        fixedpointy     = 0.
        varfixedpointy  = ctypes.c_double (fixedpointy)
        self.m_model.m_eagme.BASME_PILARES_PTFIXOY_LER (ctypes.byref (varpilar),
                            ctypes.byref (varfixedpointy))
        fixedpointy     = varfixedpointy.value
        return          fixedpointy

    @fixedPointY.setter
    def fixedPointY (self, fixedpointy: float) -> None:
        """Atribui Y do ponto fixo do pilar."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varfixedpointy  = ctypes.c_double (fixedpointy)
        self.m_model.m_eagme.BASME_PILARES_PTFIXOY_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varfixedpointy))

    @property
    def columnWindSupport (self) -> int:
        """Suporte a vento: (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        isupvento       = 0
        varisupvento    = ctypes.c_int (isupvento)
        self.m_model.m_eagme.BASME_PILARES_ISUPVENTO_LER (ctypes.byref (varpilar),
                            ctypes.byref (varisupvento))
        isupvento       = varisupvento.value
        return          isupvento

    @columnWindSupport.setter
    def columnWindSupport (self, isupvento: int) -> None:
        """Atribui (0) não (1) sim."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varisupvento    = ctypes.c_int (isupvento)
        self.m_model.m_eagme.BASME_PILARES_ISUPVENTO_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varisupvento))
    @property
    def columnInterference (self) -> int:
        """Verificação de interferências (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        iverifinter     = 0
        variverifinter  = ctypes.c_int (iverifinter)
        self.m_model.m_eagme.BASME_PILARES_IVERIFINTER_LER (ctypes.byref (varpilar),
                            ctypes.byref (variverifinter))
        iverifinter     = variverifinter.value
        return          iverifinter

    @columnInterference.setter
    def columnInterference (self, iverifinter: int) -> None:
        """Atribui Verificação de interferências (0) não (1) sim."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        variverifinter  = ctypes.c_int (iverifinter)
        self.m_model.m_eagme.BASME_PILARES_IVERIFINTER_DEF (ctypes.byref (varpilar),
                            ctypes.byref (variverifinter))
    @property
    def columnSloped (self) -> int:
        """Inclinação do pilar (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        inclinado       = 0
        varinclinado    = ctypes.c_int (inclinado)
        self.m_model.m_eagme.BASME_PILARES_INCLINADO_LER (ctypes.byref (varpilar),
                            ctypes.byref (varinclinado))
        inclinado       = varinclinado.value
        return          inclinado

    @columnSloped.setter
    def columnSloped (self, inclinado: int) -> None:
        """Atribui Inclinação do pilar (0) não (1) sim."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varinclinado    = ctypes.c_int (inclinado)
        self.m_model.m_eagme.BASME_PILARES_INCLINADO_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varinclinado))
    @property
    def columnCoil (self) -> "ColumnCoil":
        """Mola do pilar no pórtico espacial.

        Returns:
            :class:`ColumnCoil` correspondente.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        pormol          = None
        varpormol       = ctypes.c_void_p (pormol)
        self.m_model.m_eagme.BASME_PILARES_PORMOL_LER (ctypes.byref (varpilar),
                            ctypes.byref (varpormol))
        pormol          = varpormol.value
        columncoil      = ColumnCoil (self.m_model, pormol)
        return          columncoil

    @property
    def columnIsAFoundation (self) -> int:
        """O objeto de pilar representa uma fundação (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        ifundacao       = 0
        varifundacao    = ctypes.c_int (ifundacao)
        self.m_model.m_eagme.BASME_PILARES_IFUNDACAO_LER (ctypes.byref (varpilar),
                            ctypes.byref (varifundacao))
        ifundacao       = varifundacao.value
        return          ifundacao

    @columnIsAFoundation.setter
    def columnIsAFoundation (self, ifundacao: int) -> None:
        """Atribui O objeto de pilar representa uma fundação (0) não (1) sim."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varifundacao    = ctypes.c_int (ifundacao)
        self.m_model.m_eagme.BASME_PILARES_IFUNDACAO_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varifundacao))
#
#       Dados de fundação
#
    @property
    def foundationData (self) -> "FoundationData":
        """Dados de fundação.

        Returns:
            :class:`FoundationData` correspondente.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        fundac          = None
        varfundac       = ctypes.c_void_p (fundac)
        self.m_model.m_eagme.BASME_PILARES_FUNDAC_LER (ctypes.byref (varpilar),
                            ctypes.byref (varfundac))
        fundac          = varfundac.value
        foundationdata  = FoundationData (self.m_model, fundac)
        return          foundationdata

    @property
    def foundationDefined (self) -> int:
        """Fundação definida (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        ideffund       = 0
        varideffund    = ctypes.c_int (ideffund)
        self.m_model.m_eagme.BASME_PILARES_IDEFFUND_LER (ctypes.byref (varpilar),
                            ctypes.byref (varideffund))
        ideffund       = varideffund.value
        return          ideffund

    @foundationDefined.setter
    def foundationDefined (self, ideffund: int) -> None:
        """Atribui Fundação definida (0) não (1) sim."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varideffund    = ctypes.c_int (ideffund)
        self.m_model.m_eagme.BASME_PILARES_IDEFFUND_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varideffund))
    @property
    def isShortColumn (self) -> int:
        """O pilar é (0) normal (1) pilarete.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        ipilarete       = 0
        varipilarete    = ctypes.c_int (ipilarete)
        self.m_model.m_eagme.BASME_PILARES_IPILARETE_LER (ctypes.byref (varpilar),
                            ctypes.byref (varipilarete))
        ipilarete       = varipilarete.value
        return          ipilarete

    @isShortColumn.setter
    def isShortColumn (self, ipilarete: int) -> None:
        """Atribui O pilar é (0) normal (1) pilarete."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varipilarete    = ctypes.c_int (ipilarete)
        self.m_model.m_eagme.BASME_PILARES_IPILARETE_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varipilarete))

    @property
    def shortColumnAuxiliaryFloor (self) -> int:
        """Piso auxiliar de base do pilarete.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        ipisoauxpilarete= 0
        varipisoauxpilarete = ctypes.c_int (ipisoauxpilarete)
        self.m_model.m_eagme.BASME_PILARES_IPISOAUXPILARETE_LER (ctypes.byref (varpilar),
                            ctypes.byref (varipisoauxpilarete))
        ipisoauxpilarete    = varipisoauxpilarete.value
        return          ipisoauxpilarete

    @shortColumnAuxiliaryFloor.setter
    def shortColumnAuxiliaryFloor (self, ipisoauxpilarete: int) -> None:
        """Atribui Piso auxiliar de base do pilarete."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varipisoauxpilarete = ctypes.c_int (ipisoauxpilarete)
        self.m_model.m_eagme.BASME_PILARES_IPISOAUXPILARETE_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varipisoauxpilarete))

    @property
    def columnPrecastData (self) -> "ColumnPrecastData":
        """Dados de pilar pré-moldados.

        Returns:
            :class:`ColumnPrecastData` correspondente.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        pregpil         = None
        varpregpil     = ctypes.c_void_p (pregpil)
        self.m_model.m_eagme.BASME_PILARES_PREGPIL_LER (ctypes.byref (varpilar),
                            ctypes.byref (varpregpil))
        pregpil        = varpregpil.value
        columnprecastdata = ColumnPrecastData (self.m_model, pregpil)
        return          columnprecastdata

    @property
    def columnExport (self) -> int:
        """Pilar exportável para o 3D (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        iexportavel     = 0
        variexportavel  = ctypes.c_int (iexportavel)
        self.m_model.m_eagme.BASME_PILARES_IEXPORTAVEL_LER (ctypes.byref (varpilar),
                            ctypes.byref (variexportavel))
        iexportavel     = variexportavel.value
        return          iexportavel

    @columnExport.setter
    def columnExport (self, iexportavel: int) -> None:
        """Atribui Pilar exportável para o 3D (0) não (1) sim."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        variexportavel  = ctypes.c_int (iexportavel)
        self.m_model.m_eagme.BASME_PILARES_IEXPORTAVEL_DEF (ctypes.byref (varpilar),
                            ctypes.byref (variexportavel))
    @property
    def columnNonLinearity (self) -> int:
        """Coeficientes de não linearidade (0)Pilar (1)Não fissurado (2)Fissurado.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        ipilparnlf      = 0
        varipilparnlf   = ctypes.c_int (ipilparnlf)
        self.m_model.m_eagme.BASME_PILARES_IPILPARNLF_LER (ctypes.byref (varpilar),
                            ctypes.byref (varipilparnlf))
        ipilparnlf      = varipilparnlf.value
        return          ipilparnlf

    @columnNonLinearity.setter
    def columnNonLinearity (self, ipilparnlf: int) -> None:
        """Atribui Coeficientes de não linearidade (0)Pilar (1)Não fissurado (2)Fissurado."""
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varipilparnlf   = ctypes.c_int (ipilparnlf)
        self.m_model.m_eagme.BASME_PILARES_IPILPARNLF_DEF (ctypes.byref (varpilar),
                            ctypes.byref (varipilparnlf))

    def GetFoudation (self) -> Any:
        """Retorna foudation.

        Returns:
            Resultado da operação.
        """
        pvistav         = None
        if              (self.m_model.m_tqsjan != None):
            pvistav     = self.m_model.m_tqsjan.m_pvistav
        varpvistav      = ctypes.c_void_p (pvistav)
        varpilar        = ctypes.c_void_p (self.m_pilar)
        pilarapo        = None
        varpilarapo     = ctypes.c_void_p (pilarapo)
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.BASME_PILARES_PILARAPO_LER (
                        ctypes.byref (varpvistav), ctypes.byref (varpilar),
                        ctypes.byref (varpilarapo),ctypes.byref (varistat))
        istat           = varistat.value
        if              istat != 0:
            return      None
        pilarapo        = varpilarapo.value
        return          Column (self.m_model, self.m_floor, pilarapo)

#
#      Atributos BIM do usuário
#
    @property
    def userAttrib (self) -> "UserAttrib":
        """Atributos de usuário.

        Returns:
            :class:`UserAttrib` correspondente.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        usratrib        = None
        varusratrib     = ctypes.c_void_p (usratrib)
        self.m_model.m_eagme.BASME_PILARES_USRATRIB_LER (ctypes.byref (varpilar),
                ctypes.byref (varusratrib))
        usratrib        = varusratrib.value
        userattrib      = UserAttrib (self.m_model, usratrib)
        return          userattrib

#
#      Lista de seções de pilares
#
    def ColumnNumSections (self) -> int:
        """Operação ``ColumnNumSections``.

        Returns:
            Valor inteiro.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        numsecp         = 0
        varnumsecp      = ctypes.c_int (numsecp)
        self.m_model.m_eagme.BASME_PILARES_NUMSECPIL (ctypes.byref (varpilar),
                ctypes.byref (varnumsecp))
        numsecp         = varnumsecp.value
        return          numsecp

    def ColumnGetSection (self, isec: int) -> "ColumnSection":
        """int isec.

        Args:
            isec: Parâmetro ``isec``.

        Returns:
            int isec    <- isec=0..ColumnNumSections()-1.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varisec         = ctypes.c_int (isec)
        secpil          = None
        varsecpil       = ctypes.c_void_p (secpil)
        self.m_model.m_eagme.BASME_PILARES_SECPIL_LER (ctypes.byref (varpilar),
                            ctypes.byref (varisec), ctypes.byref (varsecpil))
        secpil          = varsecpil.value
        columnSection   = ColumnSection (self, self.m_model, self.m_floor, secpil)
        return          columnSection

    def ColumnGetCurrentSection (self) -> "ColumnSection":
        """objeto ColumnSection.

        Returns:
            Retorna:.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        secpil          = None
        varsecpil       = ctypes.c_void_p (secpil)
        self.m_model.m_eagme.BASME_PILARES_SECPIL_LERATUAL (ctypes.byref (varpilar),
                            ctypes.byref (varsecpil))
        secpil          = varsecpil.value
        columnSection   = None
        if              (secpil != None):
            columnSection = ColumnSection (self, self.m_model, self.m_floor, secpil)
        return          columnSection

    def ColumnCreateSection (self, isec: int, lastfloor: str) -> "ColumnSection":
        """Insere nova seção de pilar. Empurra demais seções.

        A primeira seção é criada junto com o pilar
        Cria a princípio com a geometria da seção anterior

        Args:
            isec: Parâmetro ``isec``.
            lastfloor: Parâmetro ``lastfloor``.

        Returns:
            objeto ColumnSection.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varisec         = ctypes.c_int (isec)
        varplamorre     = ctypes.c_char_p (lastfloor.encode (TQSUtil.CHARSET))
        secpil          = None
        varsecpil       = ctypes.c_void_p (secpil)
        self.m_model.m_eagme.BASME_PILARES_SECPIL_CRIAR (ctypes.byref (varfabrica),
                        ctypes.byref (varpilar), ctypes.byref (varisec),
                        varplamorre, ctypes.byref (varsecpil))
        secpil          = varsecpil.value
        columnSection   = ColumnSection (self, self.m_model, self.m_floor, secpil)
        return          columnSection

    def ColumnSectionUpdateGeometry (self, columnSection: int) -> None:
        """Atualiza uma seção de pilar após alteração de geometria.

        Args:
            columnSection: Objeto ColumnSection.
        """
        varpilar        = ctypes.c_void_p (self.m_pilar)
        varsecpil       = ctypes.c_void_p (columnSection.m_secpil)
        self.m_model.m_eagme.BASME_PILARES_SECPIL_ATUGEO (ctypes.byref (varpilar),
                            ctypes.byref (varsecpil))

#------------------------------------------------------------------------------
#       Dados de detalhamento de pilar CDetPil
#
class ColumnDetailing ():

    """Detalhamento de pilar.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", detpil: int) -> None:
        """Dados de detalhamento de pilar.

        Args:
            model: Objeto Model() do modelo atual.
            detpil: Apontador para objeto CDetPil.
        """
        self.m_model    = model
        self.m_detpil   = detpil

    @property
    def foundationHeight (self) -> float:
        """Altura da fundação, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        hfun            = 0.
        varhfun         = ctypes.c_double (hfun)
        self.m_model.m_eagme.BASME_DETPIL_HFUN_LER (ctypes.byref (vardetpil),
                            ctypes.byref (varhfun))
        hfun            = varhfun.value
        return          hfun

    @foundationHeight.setter
    def foundationHeight (self, hfun: float) -> None:
        """Atribui Altura da fundação, cm."""
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        varhfun         = ctypes.c_double (hfun)
        self.m_model.m_eagme.BASME_DETPIL_HFUN_DEF (ctypes.byref (vardetpil),
                            ctypes.byref (varhfun))

    @property
    def baseRecess (self) -> float:
        """Rebaixo da base, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        dfspil          = 0.
        vardfspil       = ctypes.c_double (dfspil)
        self.m_model.m_eagme.BASME_DETPIL_DFSPIL_LER (ctypes.byref (vardetpil),
                            ctypes.byref (vardfspil))
        dfspil          = vardfspil.value
        return          dfspil

    @baseRecess.setter
    def baseRecess (self, dfspil: float) -> None:
        """Atribui Rebaixo da base, cm."""
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        vardfspil       = ctypes.c_double (dfspil)
        self.m_model.m_eagme.BASME_DETPIL_DFSPIL_DEF (ctypes.byref (vardetpil),
                            ctypes.byref (vardfspil))

    @property
    def topRecess (self) -> float:
        """Rebaixo no topo, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        dfstopo         = 0.
        vardfstopo      = ctypes.c_double (dfstopo)
        self.m_model.m_eagme.BASME_DETPIL_DFSTOPO_LER (ctypes.byref (vardetpil),
                            ctypes.byref (vardfstopo))
        dfstopo         = vardfstopo.value
        return          dfstopo

    @topRecess.setter
    def topRecess (self, dfstopo: float) -> None:
        """Atribui Rebaixo no topo, cm."""
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        vardfstopo      = ctypes.c_double (dfstopo)
        self.m_model.m_eagme.BASME_DETPIL_DFSTOPO_DEF (ctypes.byref (vardetpil),
                            ctypes.byref (vardfstopo))
    @property
    def isDetailable (self) -> int:
        """Pilar detalhável (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        idetalhavel     = 0
        varidetalhavel  = ctypes.c_int (idetalhavel)
        self.m_model.m_eagme.BASME_DETPIL_IDETALHAVEL_LER (ctypes.byref (vardetpil),
                            ctypes.byref (varidetalhavel))
        idetalhavel     = varidetalhavel.value
        return          idetalhavel

    @isDetailable.setter
    def isDetailable (self, idetalhavel: int) -> None:
        """Atribui Pilar detalhável (0) não (1) sim."""
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        varidetalhavel  = ctypes.c_int (idetalhavel)
        self.m_model.m_eagme.BASME_DETPIL_IDETALHAVEL_DEF (ctypes.byref (vardetpil),
                            ctypes.byref (varidetalhavel))
    @property
    def isCurtain (self) -> int:
        """Pilar simula cortina (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        icortina     = 0
        varicortina  = ctypes.c_int (icortina)
        self.m_model.m_eagme.BASME_DETPIL_ICORTINA_LER (ctypes.byref (vardetpil),
                            ctypes.byref (varicortina))
        icortina     = varicortina.value
        return          icortina

    @isCurtain.setter
    def isCurtain (self, icortina: int) -> None:
        """Atribui Pilar simula cortina (0) não (1) sim."""
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        varicortina  = ctypes.c_int (icortina)
        self.m_model.m_eagme.BASME_DETPIL_ICORTINA_DEF (ctypes.byref (vardetpil),
                            ctypes.byref (varicortina))
    @property
    def canStartOutOfFoundation (self) -> int:
        """Pode nascer fora do piso fundação (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        inasceforafund  = 0
        varinasceforafund= ctypes.c_int (inasceforafund)
        self.m_model.m_eagme.BASME_DETPIL_INASCEFORAFUND_LER (ctypes.byref (vardetpil),
                            ctypes.byref (varinasceforafund))
        inasceforafund  = varinasceforafund.value
        return          inasceforafund

    @canStartOutOfFoundation.setter
    def canStartOutOfFoundation (self, inasceforafund: int) -> None:
        """Atribui Pode nascer fora do piso fundação (0) não (1) sim."""
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        varinasceforafund= ctypes.c_int (inasceforafund)
        self.m_model.m_eagme.BASME_DETPIL_INASCEFORAFUND_DEF (ctypes.byref (vardetpil),
                            ctypes.byref (varinasceforafund))

    @property
    def isFictitious (self) -> int:
        """Pilar fictício (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        ificticio       = 0
        varificticio    = ctypes.c_int (ificticio)
        self.m_model.m_eagme.BASME_DETPIL_IFICTICIO_LER (ctypes.byref (vardetpil),
                            ctypes.byref (varificticio))
        ificticio       = varificticio.value
        return          ificticio

    @isFictitious.setter
    def isFictitious (self, ificticio: int) -> None:
        """Atribui Pilar fictício (0) não (1) sim."""
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        varificticio    = ctypes.c_int (ificticio)
        self.m_model.m_eagme.BASME_DETPIL_IFICTICIO_DEF (ctypes.byref (vardetpil),
                            ctypes.byref (varificticio))

    @property
    def isShearWall (self) -> int:
        """Pilar parede para o BIM.

        Returns:
            Valor inteiro.
        """
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        ipilarpar       = 0
        varipilarpar    = ctypes.c_int (ipilarpar)
        self.m_model.m_eagme.BASME_DETPIL_IPILARPAR_LER (ctypes.byref (vardetpil),
                            ctypes.byref (varipilarpar))
        ipilarpar       = varipilarpar.value
        return          ipilarpar

    @isShearWall.setter
    def isShearWall (self, ipilarpar: int) -> None:
        """Atribui Pilar parede para o BIM."""
        vardetpil       = ctypes.c_void_p (self.m_detpil)
        varipilarpar    = ctypes.c_int (ipilarpar)
        self.m_model.m_eagme.BASME_DETPIL_IPILARPAR_DEF (ctypes.byref (vardetpil),
                            ctypes.byref (varipilarpar))

#------------------------------------------------------------------------------
#       Dados de mola de pilar no pórtico CPorMol
#
class ColumnCoil ():

    """Mola de pilar no pórtico espacial.

    Implementação:
        Mola de pilar no pórtico espacial (``CMolapil``). Cada eixo de restrição
        (``COLUMNCOIL_IRES_*``) tem tipo de apoio e valor associados; gaps definem
        folga unilateral.
    """
    def __init__ (self, model: "Model", pormol: int) -> None:
        """Dados de mola de pilar no pórtico.

        Args:
            model: Objeto Model() do modelo atual.
            pormol: Apontador para objeto CPorMol.
        """
        self.m_model    = model
        self.m_pormol   = pormol

    def GetSupportType (self, ires: int) -> int:
        """Tipo de apoio de pilar.

        Args:
            ires: Restrição a considerar COLUMNCOIL_IRES_xxxx.

        Returns:
            Tipo de apoio COLUMNCOIL_IAPOPOR_xxxx.
        """
        varpormol       = ctypes.c_void_p (self.m_pormol)
        varires         = ctypes.c_int (ires)
        iapopor         = 0
        variapopor      = ctypes.c_int (iapopor)
        self.m_model.m_eagme.BASME_PORMOL_IAPOPOR_LER (ctypes.byref (varpormol),
                           ctypes.byref (varires), ctypes.byref (variapopor))
        iapopor         = variapopor.value
        return          iapopor

    def SetSupportType (self, ires: int, iapopor: int) -> None:
        """Tipo de apoio de pilar.

        Args:
            ires: Restrição a considerar COLUMNCOIL_IRES_xxxx.
            iapopor: Tipo de apoio COLUMNCOIL_IAPOPOR_xxxx.
        """
        varpormol       = ctypes.c_void_p (self.m_pormol)
        varires         = ctypes.c_int (ires)
        variapopor      = ctypes.c_int (iapopor)
        self.m_model.m_eagme.BASME_PORMOL_IAPOPOR_DEF (ctypes.byref (varpormol),
                          ctypes.byref (varires), ctypes.byref (variapopor))

    def GetCoil (self, ires: int) -> float:
        """Coeficiente de mola.

        Args:
            ires: Restrição a considerar COLUMNCOIL_IRES_xxxx.

        Returns:
            Coeficiente de mola à Rotação tfm/rad Translação tf/m.
        """
        varpormol       = ctypes.c_void_p (self.m_pormol)
        varires         = ctypes.c_int (ires)
        pormola         = 0.
        varpormola      = ctypes.c_double (pormola)
        self.m_model.m_eagme.BASME_PORMOL_PORMOLA_LER (ctypes.byref (varpormol),
                            ctypes.byref (varires), ctypes.byref (varpormola))
        pormola         = varpormola.value
        return          pormola

    def SetCoil (self, ires: int, pormola: float) -> None:
        """Coeficiente de mola.

        Args:
            ires: Restrição a considerar COLUMNCOIL_IRES_xxxx.
            pormola: Coeficiente de mola à Rotação tfm/rad Translação tf/m.
        """
        varpormol       = ctypes.c_void_p (self.m_pormol)
        varires         = ctypes.c_int (ires)
        varpormola      = ctypes.c_double (pormola)
        self.m_model.m_eagme.BASME_PORMOL_PORMOLA_DEF (ctypes.byref (varpormol),
                            ctypes.byref (varires), ctypes.byref (varpormola))

    def GetGap (self, igap: int) -> float:
        """Valor do gap (m) de restrição de apoio.

        Args:
            igap: Gap TIPO COLUMNCOIL_IGAP_xxxx.

        Returns:
            Valor do gap (m).
        """
        varpormol       = ctypes.c_void_p (self.m_pormol)
        varigap         = ctypes.c_int (igap)
        gap             = 0.
        vargap          = ctypes.c_double (gap)
        self.m_model.m_eagme.BASME_PORMOL_GAP_LER (ctypes.byref (varpormol),
                            ctypes.byref (varigap), ctypes.byref (vargap))
        gap             = vargap.value
        return          gap

    def SetGap (self, igap: int, gap: float) -> None:
        """Valor do gap (m) de restrição de apoio.

        Args:
            igap: Gap TIPO COLUMNCOIL_IGAP_xxxx.
            gap: Valor do gap (m).
        """
        varpormol       = ctypes.c_void_p (self.m_pormol)
        varigap         = ctypes.c_int (igap)
        vargap          = ctypes.c_double (gap)
        self.m_model.m_eagme.BASME_PORMOL_GAP_DEF (ctypes.byref (varpormol),
                            ctypes.byref (varigap), ctypes.byref (vargap))

#------------------------------------------------------------------------------
#       Dados de fundações CFundac
#
class FoundationData ():

    """Dados de fundação.

    Implementação:
        Property bag muito grande para ``CDadFun`` (sapatas, blocos, tubulões, cálice).
        Métodos quase exclusivamente getter/setter sobre ``BASME_DADFUN_*``; cada
        subgrupo (geometria, armaduras, materiais, cálice) ocupa uma faixa do C++.
    """
    def __init__ (self, model: "Model", fundac: int) -> None:
        """Dados de fundações.

        Args:
            model: Objeto Model() do modelo atual.
            fundac: Apontador para objeto CFundac.
        """
        self.m_model    = model
        self.m_fundac  = fundac

    @property
    def type (self) -> int:
        """Tipo de fundação FOUNDATION_ITIPOFUNDAC_xxxx.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        itipofundac     = 0
        varitipofundac  = ctypes.c_int (itipofundac)
        self.m_model.m_eagme.BASME_FUNDAC_ITIPOFUNDAC_LER (ctypes.byref (varfundac),
                            ctypes.byref (varitipofundac))
        itipofundac     = varitipofundac.value
        return          itipofundac

    @type.setter
    def type (self, itipofundac: int) -> None:
        """Atribui Tipo de fundação FOUNDATION_ITIPOFUNDAC_xxxx."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varitipofundac  = ctypes.c_int (itipofundac)
        self.m_model.m_eagme.BASME_FUNDAC_ITIPOFUNDAC_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varitipofundac))

    @property
    def ficticiousColumn (self) -> int:
        """Pilar fictício definido (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        idimpildef      = 0
        varidimpildef   = ctypes.c_int (idimpildef)
        self.m_model.m_eagme.BASME_FUNDAC_PILFIC_IDIMPILDEF_LER (ctypes.byref (varfundac),
                            ctypes.byref (varidimpildef))
        idimpildef      = varidimpildef.value
        return          idimpildef

    @ficticiousColumn.setter
    def ficticiousColumn (self, idimpildef: int) -> None:
        """Atribui Pilar fictício definido (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varidimpildef   = ctypes.c_int (idimpildef)
        self.m_model.m_eagme.BASME_FUNDAC_PILFIC_IDIMPILDEF_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varidimpildef))

    @property
    def ficticiousColumnXDim (self) -> float:
        """Dimensão X de pilar fictício cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        dimxpildef      = 0
        vardimxpildef   = ctypes.c_double (dimxpildef)
        self.m_model.m_eagme.BASME_FUNDAC_PILFIC_DIMXPILDEF_LER (ctypes.byref (varfundac),
                            ctypes.byref (vardimxpildef))
        dimxpildef      = vardimxpildef.value
        return          dimxpildef

    @ficticiousColumnXDim.setter
    def ficticiousColumnXDim (self, dimxpildef: float) -> None:
        """Atribui Dimensão X de pilar fictício cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vardimxpildef   = ctypes.c_double (dimxpildef)
        self.m_model.m_eagme.BASME_FUNDAC_PILFIC_DIMXPILDEF_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vardimxpildef))

    @property
    def ficticiousColumnYDim (self) -> float:
        """Dimensão Y de pilar fictício cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        dimypildef      = 0
        vardimypildef   = ctypes.c_double (dimypildef)
        self.m_model.m_eagme.BASME_FUNDAC_PILFIC_DIMYPILDEF_LER (ctypes.byref (varfundac),
                            ctypes.byref (vardimypildef))
        dimypildef      = vardimypildef.value
        return          dimypildef

    @ficticiousColumnYDim.setter
    def ficticiousColumnYDim (self, dimypildef: float) -> None:
        """Atribui Dimensão Y de pilar fictício cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vardimypildef   = ctypes.c_double (dimypildef)
        self.m_model.m_eagme.BASME_FUNDAC_PILFIC_DIMYPILDEF_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vardimypildef))

    @property
    def beamSupport (self) -> int:
        """Vigas apoiam na fundação (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        ivigapofun      = 0
        varivigapofun   = ctypes.c_int (ivigapofun)
        self.m_model.m_eagme.BASME_FUNDAC_IVIGAPOFUN_LER (ctypes.byref (varfundac),
                            ctypes.byref (varivigapofun))
        ivigapofun      = varivigapofun.value
        return          ivigapofun

    @beamSupport.setter
    def beamSupport (self, ivigapofun: int) -> None:
        """Atribui Vigas apoiam na fundação (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varivigapofun   = ctypes.c_int (ivigapofun)
        self.m_model.m_eagme.BASME_FUNDAC_IVIGAPOFUN_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varivigapofun))

    @property
    def footingXDim (self) -> float:
        """Sapatas, dimensão X da base cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        sapdimx         = 0
        varsapdimx      = ctypes.c_double (sapdimx)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPDIMX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsapdimx))
        sapdimx         = varsapdimx.value
        return          sapdimx

    @footingXDim.setter
    def footingXDim (self, sapdimx: float) -> None:
        """Atribui Sapatas, dimensão X da base cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsapdimx      = ctypes.c_double (sapdimx)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPDIMX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsapdimx))

    @property
    def footingYDim (self) -> float:
        """Sapatas, dimensão Y da base cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        sapdimy         = 0
        varsapdimy      = ctypes.c_double (sapdimy)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPDIMY_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsapdimy))
        sapdimy         = varsapdimy.value
        return          sapdimy

    @footingYDim.setter
    def footingYDim (self, sapdimy: float) -> None:
        """Atribui Sapatas, dimensão Y da base cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsapdimy      = ctypes.c_double (sapdimy)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPDIMY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsapdimy))

    @property
    def footingTopXDim (self) -> float:
        """Sapatas, dimensão X do topo cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        saptx           = 0
        varsaptx        = ctypes.c_double (saptx)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPTX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsaptx))
        saptx           = varsaptx.value
        return          saptx

    @footingTopXDim.setter
    def footingTopXDim (self, saptx: float) -> None:
        """Atribui Sapatas, dimensão X do topo cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsaptx        = ctypes.c_double (saptx)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPTX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsaptx))

    @property
    def footingTopYDim (self) -> float:
        """Sapatas, dimensão Y do topo cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        sapty           = 0
        varsapty        = ctypes.c_double (sapty)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPTY_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsapty))
        sapty           = varsapty.value
        return          sapty

    @footingTopYDim.setter
    def footingTopYDim (self, sapty: float) -> None:
        """Atribui Sapatas, dimensão Y do topo cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsapty        = ctypes.c_double (sapty)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPTY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsapty))

    @property
    def footingTopXExc (self) -> float:
        """Sapatas, excentricidade X do topo cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        sapexcx         = 0
        varsapexcx      = ctypes.c_double (sapexcx)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPEXCX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsapexcx))
        sapexcx         = varsapexcx.value
        return          sapexcx

    @footingTopXExc.setter
    def footingTopXExc (self, sapexcx: float) -> None:
        """Atribui Sapatas, excentricidade X do topo cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsapexcx      = ctypes.c_double (sapexcx)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPEXCX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsapexcx))

    @property
    def footingTopYExc (self) -> float:
        """Sapatas, eycentricidade Y do topo cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        sapexcy         = 0
        varsapexcy      = ctypes.c_double (sapexcy)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPEXCY_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsapexcy))
        sapexcy         = varsapexcy.value
        return          sapexcy

    @footingTopYExc.setter
    def footingTopYExc (self, sapexcy: float) -> None:
        """Atribui Sapatas, eycentricidade Y do topo cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsapexcy      = ctypes.c_double (sapexcy)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPEXCY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsapexcy))

    @property
    def footingTopExcLeft (self) -> int:
        """Sapata de divisa à esquerda (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        isapdive        = 0
        varisapdive     = ctypes.c_int (isapdive)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_ISAPDIVE_LER (ctypes.byref (varfundac),
                            ctypes.byref (varisapdive))
        isapdive        = varisapdive.value
        return          isapdive

    @footingTopExcLeft.setter
    def footingTopExcLeft (self, isapdive: int) -> None:
        """Atribui Sapata de divisa à esquerda (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varisapdive     = ctypes.c_int (isapdive)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_ISAPDIVE_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varisapdive))

    @property
    def footingTopExcAbove (self) -> int:
        """Sapata de divisa acima (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        isapdivc        = 0
        varisapdivc     = ctypes.c_int (isapdivc)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_ISAPDIVC_LER (ctypes.byref (varfundac),
                            ctypes.byref (varisapdivc))
        isapdivc        = varisapdivc.value
        return          isapdivc

    @footingTopExcAbove.setter
    def footingTopExcAbove (self, isapdivc: int) -> None:
        """Atribui Sapata de divisa acima (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varisapdivc     = ctypes.c_int (isapdivc)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_ISAPDIVC_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varisapdivc))

    @property
    def footingTopExcRight (self) -> int:
        """Sapata de divisa à direita (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        isapdivd        = 0
        varisapdivd     = ctypes.c_int (isapdivd)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_ISAPDIVD_LER (ctypes.byref (varfundac),
                            ctypes.byref (varisapdivd))
        isapdivd        = varisapdivd.value
        return          isapdivd

    @footingTopExcRight.setter
    def footingTopExcRight (self, isapdivd: int) -> None:
        """Atribui Sapata de divisa à direita (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varisapdivd     = ctypes.c_int (isapdivd)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_ISAPDIVD_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varisapdivd))

    @property
    def footingTopExcUnder (self) -> int:
        """Sapata de divisa abaixo (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        isapdivb        = 0
        varisapdivb     = ctypes.c_int (isapdivb)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_ISAPDIVB_LER (ctypes.byref (varfundac),
                            ctypes.byref (varisapdivb))
        isapdivb        = varisapdivb.value
        return          isapdivb

    @footingTopExcUnder.setter
    def footingTopExcUnder (self, isapdivb: int) -> None:
        """Atribui Sapata de divisa abaixo (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varisapdivb     = ctypes.c_int (isapdivb)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_ISAPDIVB_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varisapdivb))

    @property
    def footingHeight (self) -> float:
        """Altura total cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        saphs           = 0
        varsaphs        = ctypes.c_double (saphs)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPHS_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsaphs))
        saphs           = varsaphs.value
        return          saphs

    @footingHeight.setter
    def footingHeight (self, saphs: float) -> None:
        """Atribui Altura total cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsaphs        = ctypes.c_double (saphs)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPHS_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsaphs))
    @property
    def footingXBaseBoard (self) -> float:
        """Altura X do rodapé cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        saph0x          = 0
        varsaph0x       = ctypes.c_double (saph0x)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPH0X_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsaph0x))
        saph0x          = varsaph0x.value
        return          saph0x

    @footingXBaseBoard.setter
    def footingXBaseBoard (self, saph0x: float) -> None:
        """Atribui Altura X do rodapé cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsaph0x       = ctypes.c_double (saph0x)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPH0X_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsaph0x))

    @property
    def footingYBaseBoard (self) -> float:
        """Altura Y do rodapé cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        saph0y          = 0
        varsaph0y       = ctypes.c_double (saph0y)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPH0Y_LER (ctypes.byref (varfundac),
                            ctypes.byref (varsaph0y))
        saph0y          = varsaph0y.value
        return          saph0y

    @footingYBaseBoard.setter
    def footingYBaseBoard (self, saph0y: float) -> None:
        """Atribui Altura Y do rodapé cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varsaph0y       = ctypes.c_double (saph0y)
        self.m_model.m_eagme.BASME_FUNDAC_SAPATAS_SAPH0Y_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varsaph0y))

    @property
    def pileCapX (self) -> float:
        """Base X do bloco, cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        blodimx         = 0
        varblodimx      = ctypes.c_double (blodimx)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODIMX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varblodimx))
        blodimx         = varblodimx.value
        return          blodimx

    @pileCapX.setter
    def pileCapX (self, blodimx: float) -> None:
        """Atribui Base X do bloco, cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varblodimx      = ctypes.c_double (blodimx)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODIMX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varblodimx))

    @property
    def pileCapY (self) -> float:
        """Base Y do bloco, cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        blodimy         = 0
        varblodimy      = ctypes.c_double (blodimy)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODIMY_LER (ctypes.byref (varfundac),
                            ctypes.byref (varblodimy))
        blodimy         = varblodimy.value
        return          blodimy

    @pileCapY.setter
    def pileCapY (self, blodimy: float) -> None:
        """Atribui Base Y do bloco, cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varblodimy      = ctypes.c_double (blodimy)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODIMY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varblodimy))

    @property
    def pileCapHeight (self) -> float:
        """Altura do bloco, cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        bloalt          = 0
        varbloalt       = ctypes.c_double (bloalt)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLOALT_LER (ctypes.byref (varfundac),
                            ctypes.byref (varbloalt))
        bloalt          = varbloalt.value
        return          bloalt

    @pileCapHeight.setter
    def pileCapHeight (self, bloalt: float) -> None:
        """Atribui Altura do bloco, cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varbloalt       = ctypes.c_double (bloalt)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLOALT_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varbloalt))

    @property
    def pileCapPiles (self) -> int:
        """Número de estacas do bloco.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        numest          = 0
        varnumest       = ctypes.c_int (numest)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_NUMEST_LER (ctypes.byref (varfundac),
                            ctypes.byref (varnumest))
        numest          = varnumest.value
        return          numest

    @pileCapPiles.setter
    def pileCapPiles (self, numest: int) -> None:
        """Atribui Número de estacas do bloco."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varnumest       = ctypes.c_int (numest)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_NUMEST_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varnumest))

    @property
    def pileCapFormat (self) -> int:
        """Formato (0..) Varia com o número de estacas.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        iblofor         = 0
        variblofor      = ctypes.c_int (iblofor)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_IBLOFOR_LER (ctypes.byref (varfundac),
                            ctypes.byref (variblofor))
        iblofor         = variblofor.value
        return          iblofor

    @pileCapFormat.setter
    def pileCapFormat (self, iblofor: int) -> None:
        """Atribui Formato (0..) Varia com o número de estacas."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        variblofor      = ctypes.c_int (iblofor)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_IBLOFOR_DEF (ctypes.byref (varfundac),
                            ctypes.byref (variblofor))

    @property
    def pileCapDiameter (self) -> float:
        """Diâmetro da estaca cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        blodiam         = 0
        varblodiam      = ctypes.c_double (blodiam)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODIAM_LER (ctypes.byref (varfundac),
                            ctypes.byref (varblodiam))
        blodiam         = varblodiam.value
        return          blodiam

    @pileCapDiameter.setter
    def pileCapDiameter (self, blodiam: float) -> None:
        """Atribui Diâmetro da estaca cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varblodiam      = ctypes.c_double (blodiam)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODIAM_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varblodiam))

    @property
    def pileCapHeightW (self) -> float:
        """Altura da estaca dentro do bloco cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        bloaltb         = 0
        varbloaltb      = ctypes.c_double (bloaltb)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLOALTB_LER (ctypes.byref (varfundac),
                            ctypes.byref (varbloaltb))
        bloaltb         = varbloaltb.value
        return          bloaltb

    @pileCapHeightW.setter
    def pileCapHeightW (self, bloaltb: float) -> None:
        """Atribui Altura da estaca dentro do bloco cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varbloaltb      = ctypes.c_double (bloaltb)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLOALTB_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varbloaltb))

    @property
    def pileCapPileXDist (self) -> float:
        """Distância X entre eixos de estacas cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        blodistx        = 0
        varblodistx     = ctypes.c_double (blodistx)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODISTX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varblodistx))
        blodistx        = varblodistx.value
        return          blodistx

    @pileCapPileXDist.setter
    def pileCapPileXDist (self, blodistx: float) -> None:
        """Atribui Distância X entre eixos de estacas cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varblodistx     = ctypes.c_double (blodistx)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODISTX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varblodistx))

    @property
    def pileCapPileYDist (self) -> float:
        """Distância Y entre eiyos de estacas cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        blodisty        = 0
        varblodisty     = ctypes.c_double (blodisty)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODISTY_LER (ctypes.byref (varfundac),
                            ctypes.byref (varblodisty))
        blodisty        = varblodisty.value
        return          blodisty

    @pileCapPileYDist.setter
    def pileCapPileYDist (self, blodisty: float) -> None:
        """Atribui Distância Y entre eiyos de estacas cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varblodisty     = ctypes.c_double (blodisty)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLODISTY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varblodisty))

    @property
    def pileCapPileFaceDist (self) -> float:
        """Distância do eixo da estaca à face do bloco cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        distface        = 0
        vardistface     = ctypes.c_double (distface)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_DISTFACE_LER (ctypes.byref (varfundac),
                            ctypes.byref (vardistface))
        distface        = vardistface.value
        return          distface

    @pileCapPileFaceDist.setter
    def pileCapPileFaceDist (self, distface: float) -> None:
        """Atribui Distância do eixo da estaca à face do bloco cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vardistface     = ctypes.c_double (distface)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_DISTFACE_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vardistface))

    @property
    def pileCapDistMode (self) -> int:
        """Cálculo da dimensão do bloco (0) dimensões fornecidas (1) distância entre estacas.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        icalceix        = 0
        varicalceix     = ctypes.c_int (icalceix)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_ICALCEIX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varicalceix))
        icalceix        = varicalceix.value
        return          icalceix

    @pileCapDistMode.setter
    def pileCapDistMode (self, icalceix: int) -> None:
        """Atribui Cálculo da dimensão do bloco (0) dimensões fornecidas (1) distância entre estacas."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varicalceix     = ctypes.c_int (icalceix)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_ICALCEIX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varicalceix))

    @property
    def pileCapPileHeight (self) -> float:
        """Altura das estacas cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        bloaltesc       = 0
        varbloaltesc    = ctypes.c_double (bloaltesc)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLOALTESC_LER (ctypes.byref (varfundac),
                            ctypes.byref (varbloaltesc))
        bloaltesc       = varbloaltesc.value
        return          bloaltesc

    @pileCapPileHeight.setter
    def pileCapPileHeight (self, bloaltesc: float) -> None:
        """Atribui Altura das estacas cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varbloaltesc    = ctypes.c_double (bloaltesc)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_BLOALTESC_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varbloaltesc))
    @property
    def pileCapOverPiers (self) -> int:
        """Bloco sobre tubulões (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        iblocotub       = 0
        variblocotub    = ctypes.c_int (iblocotub)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_IBLOCOTUB_LER (ctypes.byref (varfundac),
                            ctypes.byref (variblocotub))
        iblocotub       = variblocotub.value
        return          iblocotub

    @pileCapOverPiers.setter
    def pileCapOverPiers (self, iblocotub: int) -> None:
        """Atribui Bloco sobre tubulões (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        variblocotub    = ctypes.c_int (iblocotub)
        self.m_model.m_eagme.BASME_FUNDAC_BLOCOS_IBLOCOTUB_DEF (ctypes.byref (varfundac),
                            ctypes.byref (variblocotub))

    @property
    def pierShaftDiameter (self) -> float:
        """Tubulão - diâmetro do fuste cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        tubdia          = 0
        vartubdia       = ctypes.c_double (tubdia)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBDIA_LER (ctypes.byref (varfundac),
                            ctypes.byref (vartubdia))
        tubdia          = vartubdia.value
        return          tubdia

    @pierShaftDiameter.setter
    def pierShaftDiameter (self, tubdia: float) -> None:
        """Atribui Tubulão - diâmetro do fuste cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vartubdia       = ctypes.c_double (tubdia)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBDIA_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vartubdia))

    @property
    def pierShaftHeight (self) -> float:
        """Tubulão - altura do fuste cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        tubalt          = 0
        vartubalt       = ctypes.c_double (tubalt)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBALT_LER (ctypes.byref (varfundac),
                            ctypes.byref (vartubalt))
        tubalt          = vartubalt.value
        return          tubalt

    @pierShaftHeight.setter
    def pierShaftHeight (self, tubalt: float) -> None:
        """Atribui Tubulão - altura do fuste cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vartubalt       = ctypes.c_double (tubalt)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBALT_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vartubalt))

    @property
    def pierBaseboardDiameter (self) -> float:
        """Tubulão - diâmetro do rodapé cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        tubdiarod       = 0
        vartubdiarod    = ctypes.c_double (tubdiarod)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBDIAROD_LER (ctypes.byref (varfundac),
                            ctypes.byref (vartubdiarod))
        tubdiarod       = vartubdiarod.value
        return          tubdiarod

    @pierBaseboardDiameter.setter
    def pierBaseboardDiameter (self, tubdiarod: float) -> None:
        """Atribui Tubulão - diâmetro do rodapé cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vartubdiarod    = ctypes.c_double (tubdiarod)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBDIAROD_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vartubdiarod))

    @property
    def pierBaseboardHeight (self) -> float:
        """Tubulão - altura do rodapé cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        tubaltrod       = 0
        vartubaltrod    = ctypes.c_double (tubaltrod)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBALTROD_LER (ctypes.byref (varfundac),
                            ctypes.byref (vartubaltrod))
        tubaltrod       = vartubaltrod.value
        return          tubaltrod

    @pierBaseboardHeight.setter
    def pierBaseboardHeight (self, tubaltrod: float) -> None:
        """Atribui Tubulão - altura do rodapé cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vartubaltrod    = ctypes.c_double (tubaltrod)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBALTROD_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vartubaltrod))

    @property
    def pierBaseboardCone (self) -> float:
        """Tubulão - altura do cone cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        tubaltcon       = 0
        vartubaltcon    = ctypes.c_double (tubaltcon)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBALTCON_LER (ctypes.byref (varfundac),
                            ctypes.byref (vartubaltcon))
        tubaltcon       = vartubaltcon.value
        return          tubaltcon

    @pierBaseboardCone.setter
    def pierBaseboardCone (self, tubaltcon: float) -> None:
        """Atribui Tubulão - altura do cone cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vartubaltcon    = ctypes.c_double (tubaltcon)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBALTCON_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vartubaltcon))

    @property
    def pierFalseEllipse (self) -> int:
        """Tubulão com base alargada (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        itubalarg       = 0
        varitubalarg    = ctypes.c_int (itubalarg)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_ITUBALARG_LER (ctypes.byref (varfundac),
                            ctypes.byref (varitubalarg))
        itubalarg       = varitubalarg.value
        return          itubalarg

    @pierFalseEllipse.setter
    def pierFalseEllipse (self, itubalarg: int) -> None:
        """Atribui Tubulão com base alargada (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varitubalarg    = ctypes.c_int (itubalarg)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_ITUBALARG_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varitubalarg))

    @property
    def pierFalseEllipseWidth (self) -> float:
        """Tubulão - alargamento da base cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        tubbasalarg     = 0
        vartubbasalarg  = ctypes.c_double (tubbasalarg)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBBASALARG_LER (ctypes.byref (varfundac),
                            ctypes.byref (vartubbasalarg))
        tubbasalarg     = vartubbasalarg.value
        return          tubbasalarg

    @pierFalseEllipseWidth.setter
    def pierFalseEllipseWidth (self, tubbasalarg: float) -> None:
        """Atribui Tubulão - alargamento da base cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vartubbasalarg  = ctypes.c_double (tubbasalarg)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBBASALARG_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vartubbasalarg))

    @property
    def pierFalseEllipseAngle (self) -> float:
        """Tubulão - Rotação da base, sistema global, graus.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        tubangrot       = 0
        vartubangrot    = ctypes.c_double (tubangrot)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBANGROT_LER (ctypes.byref (varfundac),
                            ctypes.byref (vartubangrot))
        tubangrot       = vartubangrot.value
        return          tubangrot

    @pierFalseEllipseAngle.setter
    def pierFalseEllipseAngle (self, tubangrot: float) -> None:
        """Atribui Tubulão - Rotação da base, sistema global, graus."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vartubangrot    = ctypes.c_double (tubangrot)
        self.m_model.m_eagme.BASME_FUNDAC_TUBULAO_TUBANGROT_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vartubangrot))

    @property
    def pocketFoundation (self) -> int:
        """Fundação em cálice (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        icalice         = 0
        varicalice      = ctypes.c_int (icalice)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_ICALICE_LER (ctypes.byref (varfundac),
                            ctypes.byref (varicalice))
        icalice         = varicalice.value
        return          icalice

    @pocketFoundation.setter
    def pocketFoundation (self, icalice: int) -> None:
        """Atribui Fundação em cálice (0) não (1) sim."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varicalice      = ctypes.c_int (icalice)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_ICALICE_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varicalice))

    @property
    def pocketFoundationFormat (self) -> int:
        """Cálice: Formato FOUNDATION_FORM_xxxxx.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        iformato        = 0
        variformato     = ctypes.c_int (iformato)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_IFORMATO_LER (ctypes.byref (varfundac),
                            ctypes.byref (variformato))
        iformato         = variformato.value
        return          iformato

    @pocketFoundationFormat.setter
    def pocketFoundationFormat (self, iformato: int) -> None:
        """Atribui Cálice: Formato FOUNDATION_FORM_xxxxx."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        variformato     = ctypes.c_int (iformato)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_IFORMATO_DEF (ctypes.byref (varfundac),
                            ctypes.byref (variformato))

    @property
    def pocketFoundationRoughness (self) -> int:
        """Cálice: Rugosidade FOUNDATION_RUGO_xxxx.

        Returns:
            Valor inteiro.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        icalrugos       = 0
        varicalrugos    = ctypes.c_int (icalrugos)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_ICALRUGOS_LER (ctypes.byref (varfundac),
                            ctypes.byref (varicalrugos))
        icalrugos       = varicalrugos.value
        return          icalrugos

    @pocketFoundationRoughness.setter
    def pocketFoundationRoughness (self, icalrugos: int) -> None:
        """Atribui Cálice: Rugosidade FOUNDATION_RUGO_xxxx."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varicalrugos    = ctypes.c_int (icalrugos)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_ICALRUGOS_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varicalrugos))

    @property
    def pocketFoundationXDim (self) -> float:
        """Cálice: dimensão X em planta cm (D circular).

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        dimx            = 0
        vardimx         = ctypes.c_double (dimx)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_DIMX_LER (ctypes.byref (varfundac),
                            ctypes.byref (vardimx))
        dimx            = vardimx.value
        return          dimx

    @pocketFoundationXDim.setter
    def pocketFoundationXDim (self, dimx: float) -> None:
        """Atribui Cálice: dimensão X em planta cm (D circular)."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vardimx         = ctypes.c_double (dimx)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_DIMX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vardimx))

    @property
    def pocketFoundationYDim (self) -> float:
        """Cálice: dimensão Y em planta cm (D circular).

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        dimy            = 0
        vardimy         = ctypes.c_double (dimy)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_DIMY_LER (ctypes.byref (varfundac),
                            ctypes.byref (vardimy))
        dimy            = vardimy.value
        return          dimy

    @pocketFoundationYDim.setter
    def pocketFoundationYDim (self, dimy: float) -> None:
        """Atribui Cálice: dimensão Y em planta cm (D circular)."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vardimy         = ctypes.c_double (dimy)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_DIMY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vardimy))

    @property
    def pocketFoundationXWall (self) -> float:
        """Cálice: dimensão parede X cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        parx            = 0
        varparx         = ctypes.c_double (parx)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_PARX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varparx))
        parx            = varparx.value
        return          parx

    @pocketFoundationXWall.setter
    def pocketFoundationXWall (self, parx: float) -> None:
        """Atribui Cálice: dimensão parede X cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varparx         = ctypes.c_double (parx)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_PARX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varparx))

    @property
    def pocketFoundationYWall (self) -> float:
        """Cálice: dimensão parede Y cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        pary            = 0
        varpary         = ctypes.c_double (pary)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_PARY_LER (ctypes.byref (varfundac),
                            ctypes.byref (varpary))
        pary            = varpary.value
        return          pary

    @pocketFoundationYWall.setter
    def pocketFoundationYWall (self, pary: float) -> None:
        """Atribui Cálice: dimensão parede Y cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varpary         = ctypes.c_double (pary)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_PARY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varpary))

    @property
    def pocketFoundationXExc (self) -> float:
        """Cálice: Excentricidade X em relação ao centro da fundação cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        excx            = 0
        varexcx         = ctypes.c_double (excx)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_EXCX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varexcx))
        excx            = varexcx.value
        return          excx

    @pocketFoundationXExc.setter
    def pocketFoundationXExc (self, excx: float) -> None:
        """Atribui Cálice: Excentricidade X em relação ao centro da fundação cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varexcx         = ctypes.c_double (excx)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_EXCX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varexcx))

    @property
    def pocketFoundationYExc (self) -> float:
        """Cálice: Excentricidade Y em relação ao centro da fundação cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        excy            = 0
        varexcy         = ctypes.c_double (excy)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_EXCY_LER (ctypes.byref (varfundac),
                            ctypes.byref (varexcy))
        excy            = varexcy.value
        return          excy

    @pocketFoundationYExc.setter
    def pocketFoundationYExc (self, excy: float) -> None:
        """Atribui Cálice: Excentricidade Y em relação ao centro da fundação cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varexcy         = ctypes.c_double (excy)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_EXCY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varexcy))

    @property
    def pocketFoundationXInc (self) -> float:
        """Cálice: Caimento X planta parede interna cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        caix            = 0
        varcaix         = ctypes.c_double (caix)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_CAIX_LER (ctypes.byref (varfundac),
                            ctypes.byref (varcaix))
        caix            = varcaix.value
        return          caix

    @pocketFoundationXInc.setter
    def pocketFoundationXInc (self, caix: float) -> None:
        """Atribui Cálice: Caimento X planta parede interna cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varcaix         = ctypes.c_double (caix)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_CAIX_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varcaix))

    @property
    def pocketFoundationYInc (self) -> float:
        """Cálice: Caimento Y planta parede interna cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        caiy            = 0
        varcaiy         = ctypes.c_double (caiy)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_CAIY_LER (ctypes.byref (varfundac),
                            ctypes.byref (varcaiy))
        caiy            = varcaiy.value
        return          caiy

    @pocketFoundationYInc.setter
    def pocketFoundationYInc (self, caiy: float) -> None:
        """Atribui Cálice: Caimento Y planta parede interna cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varcaiy         = ctypes.c_double (caiy)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_CAIY_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varcaiy))

    @property
    def pocketFoundationHeight (self) -> float:
        """Cálice: Altura cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        hcalice         = 0
        varhcalice      = ctypes.c_double (hcalice)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_HCALICE_LER (ctypes.byref (varfundac),
                            ctypes.byref (varhcalice))
        hcalice            = varhcalice.value
        return          hcalice

    @pocketFoundationHeight.setter
    def pocketFoundationHeight (self, hcalice: float) -> None:
        """Atribui Cálice: Altura cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        varhcalice      = ctypes.c_double (hcalice)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_HCALICE_DEF (ctypes.byref (varfundac),
                            ctypes.byref (varhcalice))

    @property
    def pocketFoundationRecess (self) -> float:
        """Cálice: Rebaixo em relação ao nível da fundação cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfundac       = ctypes.c_void_p (self.m_fundac)
        dfs             = 0
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_DFS_LER (ctypes.byref (varfundac),
                            ctypes.byref (vardfs))
        dfs             = vardfs.value
        return          dfs

    @pocketFoundationRecess.setter
    def pocketFoundationRecess (self, dfs: float) -> None:
        """Atribui Cálice: Rebaixo em relação ao nível da fundação cm."""
        varfundac       = ctypes.c_void_p (self.m_fundac)
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_FUNDAC_CALICE_DFS_DEF (ctypes.byref (varfundac),
                            ctypes.byref (vardfs))

#------------------------------------------------------------------------------
#       Dados de pilares pré-moldados CPreGPil
#
class ColumnPrecastData ():

    """Dados de pilar pré-moldado.

    Implementação:
        Dados de pilar pré-moldado (``CPrePil``). Compõe sub-objetos para tubos de
        água pluvial, alças de içamento e aberturas de içamento.
    """
    def __init__ (self, model: "Model", pregpil: int) -> None:
        """Dados de usuário para o BIM.

        Args:
            model: Objeto Model() do modelo atual.
            pregpil: Apontador para objeto CPreGPil.
        """
        self.m_model    = model
        self.m_pregpil  = pregpil

    @property
    def precastRegion (self) -> int:
        """Pilar pré-moldado: região construtiva.

        Returns:
            Valor inteiro.
        """
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        iregiao         = 0
        variregiao      = ctypes.c_int (iregiao)
        self.m_model.m_eagme.BASME_PREGPIL_IREGIAO_LER (ctypes.byref (varpregpil),
                            ctypes.byref (variregiao))
        iregiao         = variregiao.value
        return          iregiao

    @precastRegion.setter
    def precastRegion (self, iregiao: int) -> None:
        """Atribui Pilar pré-moldado: região construtiva."""
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        variregiao      = ctypes.c_int (iregiao)
        self.m_model.m_eagme.BASME_PREGPIL_IREGIAO_DEF (ctypes.byref (varpregpil),
                            ctypes.byref (variregiao))

    @property
    def isPrecast (self) -> int:
        """Pilar pré-moldado: (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        ipremoldado     = 0
        varipremoldado  = ctypes.c_int (ipremoldado)
        self.m_model.m_eagme.BASME_PREGPIL_IPREMOLDADO_LER (ctypes.byref (varpregpil),
                            ctypes.byref (varipremoldado))
        ipremoldado     = varipremoldado.value
        return          ipremoldado

    @isPrecast.setter
    def isPrecast (self, ipremoldado: int) -> None:
        """Atribui Pilar pré-moldado: (0) Não (1) Sim."""
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        varipremoldado  = ctypes.c_int (ipremoldado)
        self.m_model.m_eagme.BASME_PREGPIL_IPREMOLDADO_DEF (ctypes.byref (varpregpil),
                            ctypes.byref (varipremoldado))

    @property
    def rebarBundling (self) -> int:
        """Pilar pré-moldado: Alojamento de armadura (0)Critérios (1)TQS Pilar (2)Feixe.

        Returns:
            Valor inteiro.
        """
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        iarmfeixepil    = 0
        variarmfeixepil = ctypes.c_int (iarmfeixepil)
        self.m_model.m_eagme.BASME_PREGPIL_IARMFEIXEPIL_LER (ctypes.byref (varpregpil),
                            ctypes.byref (variarmfeixepil))
        iarmfeixepil    = variarmfeixepil.value
        return          iarmfeixepil

    @rebarBundling.setter
    def rebarBundling (self, iarmfeixepil: int) -> None:
        """Atribui Pilar pré-moldado: Alojamento de armadura (0)Critérios (1)TQS Pilar (2)Feixe."""
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        variarmfeixepil = ctypes.c_int (iarmfeixepil)
        self.m_model.m_eagme.BASME_PREGPIL_IARMFEIXEPIL_DEF (ctypes.byref (varpregpil),
                            ctypes.byref (variarmfeixepil))

    @property
    def rainWaterPipe (self) -> "RainWaterPipe":
        """Tubo de água pluvial.

        Returns:
            :class:`RainWaterPipe` correspondente.
        """
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        preagua         = None
        varpreagua      = ctypes.c_void_p (preagua)
        self.m_model.m_eagme.BASME_PREGPIL_PREAGUA_LER (ctypes.byref (varpregpil),
                            ctypes.byref (varpreagua))
        preagua         = varpreagua.value
        rainwaterpipe   = RainWaterPipe (self.m_model, preagua)
        return          rainwaterpipe

    @property
    def liftingAnchors (self) -> "LiftingAnchors":
        """Alça de içamento de pilares pré-moldados.

        Returns:
            :class:`LiftingAnchors` correspondente.
        """
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        prealca         = None
        varprealca      = ctypes.c_void_p (prealca)
        self.m_model.m_eagme.BASME_PREGPIL_PREALCA_LER (ctypes.byref (varpregpil),
                            ctypes.byref (varprealca))
        prealca         = varprealca.value
        liftinganchors  = LiftingAnchors (self.m_model, prealca)
        return          liftinganchors

    @property
    def liftOpenning (self) -> "LiftOpenning":
        """Furos de levantamento de pilares pré-moldados.

        Returns:
            :class:`LiftOpenning` correspondente.
        """
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        prefur          = None
        varprefur       = ctypes.c_void_p (prefur)
        self.m_model.m_eagme.BASME_PREGPIL_PREFUR_LER (ctypes.byref (varpregpil),
                            ctypes.byref (varprefur))
        prefur          = varprefur.value
        liftinghole     = LiftOpenning (self.m_model, prefur)
        return          liftinghole

    @property
    def preCastGroup (self) -> "PreCastGroup":
        """Grupo de pré-moldados.

        Returns:
            :class:`PreCastGroup` correspondente.
        """
        varpregpil      = ctypes.c_void_p (self.m_pregpil)
        grupopre        = None
        vargrupopre     = ctypes.c_void_p (grupopre)
        self.m_model.m_eagme.BASME_PREGPIL_GRUPOPRE_LER (ctypes.byref (varpregpil),
                            ctypes.byref (vargrupopre))
        grupopre        = vargrupopre.value
        preCastGroup    = PreCastGroup (self.m_model, grupopre)
        return          preCastGroup

#------------------------------------------------------------------------------
#       Seção de pilar - um pilar pode ter várias seções ao longo do edifício - CSecPil
#
class ColumnSection (SMObject):

    """Seção de pilar (``CSecPil``).

    Implementação:
        Representa uma seção de pilar ao longo da altura. Cada seção tem geometria,
        detalhamento e dados por pavimento; métodos navegam pelo array C++ de seções
        de um pilar.
    """
    def __init__ (self, column: "Column", model: "Model", floor: "Floor", secpil: int) -> None:
        """Seção de pilar - um pilar pode ter várias seções ao longo do edifício.

        Args:
            column: Objeto Column que abriga esta seção ou None.
            model: Objeto Model() do modelo atual.
            floor: Planta corrente (:class:`Floor`).
            secpil: Apontador para objeto CSecPil.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_secpil   = secpil
        # Quando criado a partir de iteração (sem objeto Column conhecido), recupera o pilar pai do C++
        if              (column == None):
            varsecpil   = ctypes.c_void_p (self.m_secpil)
            pilar       = None
            varpilar    = ctypes.c_void_p (pilar)
            self.m_model.m_eagme.BASME_SECPIL_PILAR_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varpilar))
            pilar       = varpilar.value
            column      = Column (self.m_model, self.m_floor, pilar)

        self.m_column   = column
        super().__init__(model, self.m_secpil)

    @property
    def column (self) -> "Column":
        """Operação ``column``.

        Returns:
            :class:`Column` correspondente.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        pilar           = None
        varpilar        = ctypes.c_void_p (pilar)
        self.m_model.m_eagme.BASME_SECPIL_PILAR_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varpilar))
        pilar           = varpilar.value
        return          Column (self.m_model, self.m_floor, pilar)

    @property
    def insertionX (self) -> float:
        """Ponto de inserção X.

        Returns:
            Valor de ponto flutuante.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        xins            = 0.
        varxins         = ctypes.c_double (xins)
        self.m_model.m_eagme.BASME_SECPIL_PTINSX_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varxins))
        xins            = varxins.value
        return          xins

    @insertionX.setter
    def insertionX (self, xins: float) -> None:
        """Atribui Ponto de inserção X."""
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        varxins         = ctypes.c_double (xins)
        self.m_model.m_eagme.BASME_SECPIL_PTINSX_DEF (ctypes.byref (varsecpil),
                            ctypes.byref (varxins))

    @property
    def insertionY (self) -> float:
        """Ponto de inserção Y.

        Returns:
            Valor de ponto flutuante.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        yins            = 0.
        varyins         = ctypes.c_double (yins)
        self.m_model.m_eagme.BASME_SECPIL_PTINSY_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varyins))
        yins            = varyins.value
        return          yins

    @insertionY.setter
    def insertionY (self, yins: float) -> None:
        """Atribui Ponto de inserção Y."""
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        varyins         = ctypes.c_double (yins)
        self.m_model.m_eagme.BASME_SECPIL_PTINSY_DEF (ctypes.byref (varsecpil),
                            ctypes.byref (varyins))

    def GetColumnFloorData (self, floor: "Floor") -> "ColumnFloorData":
        """floor.

        Args:
            floor: Pavimento Floor().

        Returns:
            floor       <- Pavimento Floor().
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        infopla         = None
        varinfopla      = ctypes.c_void_p (infopla)
        self.m_model.m_eagme.BASME_SECPIL_INFOPLA_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varsecpil), ctypes.byref (varinfopla))
        infopla         = varinfopla.value
        columnFloordata = ColumnFloorData (self.m_model, infopla)
        return          columnFloordata

    def GetColumnBoundaryCond (self, floor: "Floor") -> "ColumnBoundaryCond":
        """floor.

        Args:
            floor: Pavimento Floor().

        Returns:
            floor           <- Pavimento Floor().
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        contpil         = None
        varcontpil      = ctypes.c_void_p (contpil)
        self.m_model.m_eagme.BASME_SECPIL_CONTPIL_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varsecpil), ctypes.byref (varcontpil))
        contpil         = varcontpil.value
        columnBoundaryCond = ColumnBoundaryCond (self.m_model, contpil)
        return          columnBoundaryCond

    def SetColumnBoundaryMode (self, floor: "Floor", idefcontpil: int) -> None:
        """Define se as condições de contorno são por seção de pilar ou planta.

        Args:
            floor: Pavimento Floor().
            idefcontpil: Condições de contorno por (0) seção (1) planta.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        varidefcontpil  = ctypes.c_int (idefcontpil)
        self.m_model.m_eagme.BASME_SECPIL_IDEFCONTPIL_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varsecpil), ctypes.byref (varidefcontpil))

    def GetShearWallStripNum (self) -> int:
        """Retorna shear wall strip num.

        Returns:
            Valor inteiro.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        numlam          = 0
        varnumlam       = ctypes.c_int (numlam)
        self.m_model.m_eagme.BASME_SECPIL_LAMINAS_NUMERO_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varnumlam))
        numlam          = varnumlam.value
        return          numlam

    def GetShearWallStripNumPts (self, ilam: int) -> int:
        """ilam.

        Args:
            ilam: índice da lâmina 0..GetShearWallStripNum()-1.

        Returns:
            ilam                <- índice da lâmina 0..GetShearWallStripNum()-1.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        varilam         = ctypes.c_int (ilam)
        numpts          = 0
        varnumpts       = ctypes.c_int (numpts)
        self.m_model.m_eagme.BASME_SECPIL_LAMINAS_NUMPTS_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varilam), ctypes.byref (varnumpts))
        numpts          = varnumpts.value
        return          numpts

    def GetShearWallStripPoint (self, ilam: int, ipt: int) -> Tuple[float, float]:
        """ilam.

        Args:
            ilam: Índice da lâmina 0..GetShearWallStripNum()-1.
            ipt: Índice do ponto 0..GetShearWallStripNumPts()-1.

        Returns:
            ilam                <- Índice da lâmina 0..GetShearWallStripNum()-1.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        varilam         = ctypes.c_int (ilam)
        vaript          = ctypes.c_int (ipt)
        x               = 0.
        varx            = ctypes.c_double (x)
        y               = 0.
        vary            = ctypes.c_double (y)
        self.m_model.m_eagme.BASME_SECPIL_LAMINAS_PONTO_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varilam), ctypes.byref (vaript),
                            ctypes.byref (varx), ctypes.byref (vary))
        x               = varx.value
        y               = vary.value
        return          x, y

    @property
    def columnGeometry (self) -> "ColumnGeometry":
        """Dados de geometria de pilar.

        Returns:
            :class:`ColumnGeometry` correspondente.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        geopil          = None
        vargeopil       = ctypes.c_void_p (geopil)
        self.m_model.m_eagme.BASME_SECPIL_GEOPIL_LER (ctypes.byref (varsecpil),
                            ctypes.byref (vargeopil))
        geopil          = vargeopil.value
        columngeometry  = ColumnGeometry (self.m_model, geopil)
        return          columngeometry

    @property
    def sectionPolig (self) -> "Polygon":
        """Seção transversal.

        Returns:
            :class:`Polygon` correspondente.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        polig           = None
        varpolig        = ctypes.c_void_p (polig)
        self.m_model.m_eagme.BASME_SECPIL_POLIG_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varpolig))
        polig           = varpolig.value
        sectionPoligx   = Polygon (self.m_model, polig)
        return          sectionPoligx

    @property
    def sectionLastFloor (self) -> str:
        """Última planta da seção (string).

        Returns:
            Cadeia de caracteres.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        varplamorre     = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_SECPIL_PLAMORRE_LER (ctypes.byref (varsecpil),
                                varplamorre)
        plamorre        = varplamorre.value.decode(TQSUtil.CHARSET)
        return          plamorre

    @sectionLastFloor.setter
    def sectionLastFloor (self, plamorre: str) -> None:
        """Atribui Última planta da seção (string)."""
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        varplamorre     = ctypes.c_char_p (plamorre.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_SECPIL_PLAMORRE_DEF (ctypes.byref (varsecpil),
                                varplamorre)

    @property
    def columnInsertion (self) -> "ColumnInsertion":
        """Dados de inserção de pilar.

        Returns:
            :class:`ColumnInsertion` correspondente.
        """
        varsecpil       = ctypes.c_void_p (self.m_secpil)
        inspil          = None
        varinspil       = ctypes.c_void_p (inspil)
        self.m_model.m_eagme.BASME_SECPIL_INSPIL_LER (ctypes.byref (varsecpil),
                            ctypes.byref (varinspil))
        inspil          = varinspil.value
        columninsertion = ColumnInsertion (self.m_model, inspil)
        return          columninsertion

#------------------------------------------------------------------------------
#       Dados de usuário para o BIM - CUsrAtrib
#
class UserAttrib ():

    """Atributo BIM do usuário.

    Implementação:
        Itera atributos BIM do usuário associados a um objeto. ``usratribReadNext``
        percorre o conjunto e ``usratribInsert`` / ``usratribErase`` mutam-no.
    """
    def __init__ (self, model: "Model", usratrib: int) -> None:
        """Dados de usuário para o BIM.

        Args:
            model: Objeto Model() do modelo atual.
            usratrib: Apontador para objeto CUsrAtrib.
        """
        self.m_model    = model
        self.m_usratrib = usratrib

    def usratribClear (self) -> None:
        """Limpa atributos do usuário.
        """
        varusratrib     = ctypes.c_void_p (self.m_usratrib)
        self.m_model.m_eagme.BASME_USRATRIB_LIMPAR (ctypes.byref (varusratrib))

    def usratribNum (self) -> int:
        """Operação ``usratribNum``.

        Returns:
            Valor inteiro.
        """
        varusratrib     = ctypes.c_void_p (self.m_usratrib)
        numatrib        = 0
        varnumatrib     = ctypes.c_int (numatrib)
        self.m_model.m_eagme.BASME_USRATRIB_NUMATRIB_LER (ctypes.byref (varusratrib),
                            ctypes.byref (varnumatrib))
        numatrib        = varnumatrib.value
        return          numatrib

    def usratribInsert (self, chave: str, sval: str) -> None:
        """Insere novo atributo.

        Args:
            chave: Parâmetro ``chave``.
            sval: Parâmetro ``sval``.
        """
        varusratrib     = ctypes.c_void_p (self.m_usratrib)
        varchave        = ctypes.c_char_p (chave.encode (TQSUtil.CHARSET))
        varsval         = ctypes.c_char_p (sval.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_USRATRIB_INSERIR (ctypes.byref (varusratrib),
                            varchave, varsval)
    def usratribErase (self, chave: str) -> None:
        """Apaga atributo existente.

        ATENÇÃO: a chave é passada como ``ctypes.byref(varchave)``, ou seja
        ``char **``, enquanto ``varchave`` já é um ``char *``. Os métodos
        equivalentes de inserção e busca passam o ``c_char_p`` direto. A DLL
        recebe uma indireção extra, então a remoção não localiza a chave
        informada.

        Args:
            chave: Parâmetro ``chave``.
        """
        varusratrib     = ctypes.c_void_p (self.m_usratrib)
        varchave        = ctypes.c_char_p (chave.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_USRATRIB_APAGAR (ctypes.byref (varusratrib),
                            ctypes.byref (varchave))

    def usratribBegin (self) -> None:
        """Prepara para ler todos os atributos.
        """
        varusratrib     = ctypes.c_void_p (self.m_usratrib)
        self.m_model.m_eagme.BASME_USRATRIB_PREPLER (ctypes.byref (varusratrib))

    def usratribReadNext (self) -> Tuple[Any, Any, int]:
        """Lê próximo atributo.

        Returns:
            char *chave,        -> Chave.
        """
        varusratrib     = ctypes.c_void_p (self.m_usratrib)
        varchave        = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        varsval         = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.BASME_USRATRIB_LERPROX (ctypes.byref (varusratrib),
                            varchave, varsval, ctypes.byref (varistat))
        istat           = varistat.value
        # Só decodifica strings quando houve leitura válida; istat != 0 marca fim de iteração
        if              (istat == 0):
            chave       = varchave.value.decode(TQSUtil.CHARSET)
            sval        = varsval.value.decode(TQSUtil.CHARSET)
        else:
            chave       = ""
            sval        = ""
        return          chave, sval, istat

    def usratribFind (self, chave: str) -> Tuple[Any, int]:
        """Lê próximo atributo.

        Args:
            chave: Parâmetro ``chave``.

        Returns:
            char *sval,         -> Valor.
        """
        varusratrib     = ctypes.c_void_p (self.m_usratrib)
        varchave        = ctypes.c_char_p (chave.encode (TQSUtil.CHARSET))
        varsval         = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.BASME_USRATRIB_ACHAR (ctypes.byref (varusratrib),
                            varchave, varsval, ctypes.byref (varistat))
        istat           = varistat.value
        if              (istat == 0):
            sval        = varsval.value.decode(TQSUtil.CHARSET)
        else:
            sval        = ""
        return          sval, istat
#------------------------------------------------------------------------------
#        Informações por planta, associadas a seções de pilares - CInfoPla
#
class ColumnFloorData ():

    """Dados de pilar por pavimento.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", infopla: int) -> None:
        """Informações por planta, associadas à seção de pilar.

        Args:
            model: Objeto Model() do modelo atual.
            infopla: Apontador para objeto CInfoPla.
        """
        self.m_model    = model
        self.m_infopla  = infopla

    @property
    def infoByFloor (self) -> int:
        """Informações de pilares por (0) Seção de pilar (1) Planta.

        Returns:
            Valor inteiro.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        idefcontpil     = 0
        varidefcontpil  = ctypes.c_int (idefcontpil)
        self.m_model.m_eagme.BASME_INFOPLA_IDEFCONTPIL_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varidefcontpil))
        idefcontpil     = varidefcontpil.value
        return          idefcontpil

    @infoByFloor.setter
    def infoByFloor (self, idefcontpil: int) -> None:
        """Atribui Informações de pilares por (0) Seção de pilar (1) Planta."""
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        varidefcontpil  = ctypes.c_int (idefcontpil)
        self.m_model.m_eagme.BASME_INFOPLA_IDEFCONTPIL_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (varidefcontpil))

    @property
    def columnBoundaryCond (self) -> "ColumnBoundaryCond":
        """Condições de contorno de pilares.

        Returns:
            :class:`ColumnBoundaryCond` correspondente.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        contpil         = None
        varcontpil      = ctypes.c_void_p (contpil)
        self.m_model.m_eagme.BASME_INFOPLA_CONTPIL_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varcontpil))
        contpil         = varcontpil.value
        columnboundarycond = ColumnBoundaryCond (self.m_model, contpil)
        return          columnboundarycond

    @property
    def columnBucklingX (self) -> float:
        """Coeficiente de flambagem X.

        Returns:
            Valor de ponto flutuante.
        """
        varinfopla       = ctypes.c_void_p (self.m_infopla)
        cflamx          = 0
        varcflamx       = ctypes.c_double (cflamx)
        self.m_model.m_eagme.BASME_INFOPLA_CFLAMX_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varcflamx))
        cflamx          = varcflamx.value
        return          cflamx

    @columnBucklingX.setter
    def columnBucklingX (self, cflamx: float) -> None:
        """Atribui Coeficiente de flambagem X."""
        varinfopla       = ctypes.c_void_p (self.m_infopla)
        varcflamx       = ctypes.c_double (cflamx)
        self.m_model.m_eagme.BASME_INFOPLA_CFLAMX_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (varcflamx))

    @property
    def columnBucklingY (self) -> float:
        """Coeficiente de flambagem Y.

        Returns:
            Valor de ponto flutuante.
        """
        varinfopla       = ctypes.c_void_p (self.m_infopla)
        cflamy          = 0
        varcflamy       = ctypes.c_double (cflamy)
        self.m_model.m_eagme.BASME_INFOPLA_CFLAMY_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varcflamy))
        cflamy          = varcflamy.value
        return          cflamy

    @columnBucklingY.setter
    def columnBucklingY (self, cflamy: float) -> None:
        """Atribui Coeficiente de flambagem Y."""
        varinfopla       = ctypes.c_void_p (self.m_infopla)
        varcflamy       = ctypes.c_double (cflamy)
        self.m_model.m_eagme.BASME_INFOPLA_CFLAMY_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (varcflamy))

    @property
    def columnDoubleStoryX (self) -> int:
        """Pé-direito duplo X (0) Geometria (1) Não (2) Sim.

        Returns:
            Valor inteiro.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        itravadox       = 0
        varitravadox    = ctypes.c_int (itravadox)
        self.m_model.m_eagme.BASME_INFOPLA_ITRAVADOX_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varitravadox))
        itravadox       = varitravadox.value
        return          itravadox

    @columnDoubleStoryX.setter
    def columnDoubleStoryX (self, itravadox: int) -> None:
        """Atribui Pé-direito duplo X (0) Geometria (1) Não (2) Sim."""
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        varitravadox    = ctypes.c_int (itravadox)
        self.m_model.m_eagme.BASME_INFOPLA_ITRAVADOX_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (varitravadox))

    @property
    def columnDoubleStoryY (self) -> int:
        """Pé-direito duplo X (0) Geometria (1) Não (2) Sim.

        Returns:
            Valor inteiro.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        itravadoy       = 0
        varitravadoy    = ctypes.c_int (itravadoy)
        self.m_model.m_eagme.BASME_INFOPLA_ITRAVADOY_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varitravadoy))
        itravadoy       = varitravadoy.value
        return          itravadoy

    @columnDoubleStoryY.setter
    def columnDoubleStoryY (self, itravadoy: int) -> None:
        """Atribui Pé-direito duplo X (0) Geometria (1) Não (2) Sim."""
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        varitravadoy    = ctypes.c_int (itravadoy)
        self.m_model.m_eagme.BASME_INFOPLA_ITRAVADOY_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (varitravadoy))
    @property
    def columnConcreteFc (self) -> str:
        """Fck diferenciado de pilar (string).

        Returns:
            Cadeia de caracteres.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        varfckpil       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_INFOPLA_FCKPIL_LER (ctypes.byref (varinfopla),
                            varfckpil)
        fckpil          = varfckpil.value.decode(TQSUtil.CHARSET)
        return          fckpil

    @columnConcreteFc.setter
    def columnConcreteFc (self, fckpil: str) -> None:
        """Atribui Fck diferenciado de pilar (string)."""
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        varfckpil       = ctypes.c_char_p (fckpil.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_INFOPLA_FCKPIL_DEF (ctypes.byref (varinfopla),
                            varfckpil)
    @property
    def columnCover (self) -> float:
        """Cobrimento do pilar na planta, cm.

        Returns:
            Valor de ponto flutuante.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        cobrpil         = 0.
        varcobrpil      = ctypes.c_double (cobrpil)
        self.m_model.m_eagme.BASME_INFOPLA_COBRPIL_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varcobrpil))
        cobrpil        = varcobrpil.value
        return          cobrpil

    @columnCover.setter
    def columnCover (self, cobrpil: float) -> None:
        """Atribui Cobrimento do pilar na planta, cm."""
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        varcobrpil      = ctypes.c_double (cobrpil)
        self.m_model.m_eagme.BASME_INFOPLA_COBRPIL_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (varcobrpil))

    @property
    def columnExposure (self) -> int:
        """Pilar em contato com o solo (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        icontsolo       = 0
        varicontsolo    = ctypes.c_int (icontsolo)
        self.m_model.m_eagme.BASME_INFOPLA_ICONTSOLO_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varicontsolo))
        icontsolo       = varicontsolo.value
        return          icontsolo

    @columnExposure.setter
    def columnExposure (self, icontsolo: int) -> None:
        """Atribui Pilar em contato com o solo (0) não (1) sim."""
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        varicontsolo = ctypes.c_int (icontsolo)
        self.m_model.m_eagme.BASME_INFOPLA_ICONTSOLO_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (varicontsolo))


    @property
    def columnHinges (self) -> int:
        """Pilar articulado em (0)CONTPOR.DAT (1)base/topo (2)base (3)topo.

        Returns:
            Valor inteiro.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        iarticbt        = 0
        variarticbt     = ctypes.c_int (iarticbt)
        self.m_model.m_eagme.BASME_INFOPLA_IARTICBT_LER (ctypes.byref (varinfopla),
                            ctypes.byref (variarticbt))
        iarticbt        = variarticbt.value
        return          iarticbt

    @columnHinges.setter
    def columnHinges (self, iarticbt: int) -> None:
        """Atribui Pilar articulado em (0)CONTPOR.DAT (1)base/topo (2)base (3)topo."""
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        variarticbt     = ctypes.c_int (iarticbt)
        self.m_model.m_eagme.BASME_INFOPLA_IARTICBT_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (variarticbt))

    @property
    def columnDynHorLoad (self) -> int:
        """Carga dinâmica de veiculo em pilar (0) não (1) sim.

        Returns:
            Valor inteiro.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        icargadinvuc    = 0
        varicargadinvuc = ctypes.c_int (icargadinvuc)
        self.m_model.m_eagme.BASME_INFOPLA_ICARGADINVUC_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varicargadinvuc))
        icargadinvuc    = varicargadinvuc.value
        return          icargadinvuc

    @columnDynHorLoad.setter
    def columnDynHorLoad (self, icargadinvuc: int) -> None:
        """Atribui Carga dinâmica de veiculo em pilar (0) não (1) sim."""
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        varicargadinvuc = ctypes.c_int (icargadinvuc)
        self.m_model.m_eagme.BASME_INFOPLA_ICARGADINVUC_DEF (ctypes.byref (varinfopla),
                            ctypes.byref (varicargadinvuc))

    @property
    def columnTransferBlock (self) -> "ColumnTransferBlock":
        """Dados de Bloco de transição.

        Returns:
            :class:`ColumnTransferBlock` correspondente.
        """
        varinfopla      = ctypes.c_void_p (self.m_infopla)
        blocotrans      = None
        varblocotrans   = ctypes.c_void_p (blocotrans)
        self.m_model.m_eagme.BASME_INFOPLA_BLOCOTRANS_LER (ctypes.byref (varinfopla),
                            ctypes.byref (varblocotrans))
        blocotrans          = varblocotrans.value
        columntransferblock = ColumnTransferBlock (self.m_model, blocotrans)
        return          columntransferblock

#------------------------------------------------------------------------------
#       Dados de geometria de pilar - CGeoPil
#
class ColumnGeometry ():

    """Geometria de pilar.

    Implementação:
        Geometria de pilar (``CGeoPil``). Property bag de dimensões, materiais e nome
        da seção; tipos sobrecarregados (setter aceita string ou enum) tratam dispatch
        com ``isinstance``.
    """
    def __init__ (self, model: "Model", geopil: int) -> None:
        """Dados de geometria de pilar.

        Args:
            model: Objeto Model() do modelo atual.
            geopil: Apontador para objeto CGeoPil.
        """
        self.m_model    = model
        self.m_geopil   = geopil

    @property
    def sectionType (self) -> int:
        """Tipo de seção COLUMNTYPE_xxx.

        Returns:
            Valor inteiro.
        """
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        itpsec          = 0
        varitpsec       = ctypes.c_int (itpsec)
        self.m_model.m_eagme.BASME_GEOPIL_ITPSEC_LER (ctypes.byref (vargeopil),
                            ctypes.byref (varitpsec))
        itpsec          = varitpsec.value
        return          itpsec

    @sectionType.setter
    def sectionType (self, itpsec: int) -> None:
        """Atribui Tipo de seção COLUMNTYPE_xxx."""
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varitpsec       = ctypes.c_int (itpsec)
        self.m_model.m_eagme.BASME_GEOPIL_ITPSEC_DEF (ctypes.byref (vargeopil),
                            ctypes.byref (varitpsec))
    @property
    def sectionB1 (self) -> float:
        """Dimensão B1 de seções R/L/U/C.

        Returns:
            Valor de ponto flutuante.
        """
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        b1              = 0
        varb1           = ctypes.c_double (b1)
        self.m_model.m_eagme.BASME_GEOPIL_B1_LER (ctypes.byref (vargeopil),
                            ctypes.byref (varb1))
        b1              = varb1.value
        return          b1

    @sectionB1.setter
    def sectionB1 (self, b1: float) -> None:
        """Atribui Dimensão B1 de seções R/L/U/C."""
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varb1           = ctypes.c_double (b1)
        self.m_model.m_eagme.BASME_GEOPIL_B1_DEF (ctypes.byref (vargeopil),
                            ctypes.byref (varb1))
    @property
    def sectionH1 (self) -> float:
        """Dimensão H1 de seções R/L/U.

        Returns:
            Valor de ponto flutuante.
        """
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        h1              = 0
        varh1           = ctypes.c_double (h1)
        self.m_model.m_eagme.BASME_GEOPIL_H1_LER (ctypes.byref (vargeopil),
                            ctypes.byref (varh1))
        h1              = varh1.value
        return          h1

    @sectionH1.setter
    def sectionH1 (self, h1: float) -> None:
        """Atribui Dimensão H1 de seções R/L/U."""
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varh1           = ctypes.c_double (h1)
        self.m_model.m_eagme.BASME_GEOPIL_H1_DEF (ctypes.byref (vargeopil),
                            ctypes.byref (varh1))
    @property
    def sectionB2 (self) -> float:
        """Dimensão B2 de seções L/U.

        Returns:
            Valor de ponto flutuante.
        """
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        b2              = 0
        varb2           = ctypes.c_double (b2)
        self.m_model.m_eagme.BASME_GEOPIL_B2_LER (ctypes.byref (vargeopil),
                            ctypes.byref (varb2))
        b2              = varb2.value
        return          b2

    @sectionB2.setter
    def sectionB2 (self, b2: float) -> None:
        """Atribui Dimensão B2 de seções L/U."""
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varb2           = ctypes.c_double (b2)
        self.m_model.m_eagme.BASME_GEOPIL_B2_DEF (ctypes.byref (vargeopil),
                            ctypes.byref (varb2))

    @property
    def sectionH2 (self) -> float:
        """Dimensão H2 de seções L/U.

        Returns:
            Valor de ponto flutuante.
        """
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        h2              = 0
        varh2           = ctypes.c_double (h2)
        self.m_model.m_eagme.BASME_GEOPIL_H2_LER (ctypes.byref (vargeopil),
                            ctypes.byref (varh2))
        h2              = varh2.value
        return          h2

    @sectionH2.setter
    def sectionH2 (self, h2: float) -> None:
        """Atribui Dimensão H2 de seções L/U."""
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varh2           = ctypes.c_double (h2)
        self.m_model.m_eagme.BASME_GEOPIL_H2_DEF (ctypes.byref (vargeopil),
                            ctypes.byref (varh2))

    @property
    def sectionAngle (self) -> float:
        """Ângulo de inserção da seção em graus.

        Returns:
            Valor de ponto flutuante.
        """
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        ang             = 0
        varang          = ctypes.c_double (ang)
        self.m_model.m_eagme.BASME_GEOPIL_ANG_LER (ctypes.byref (vargeopil),
                            ctypes.byref (varang))
        ang             = varang.value
        return          ang

    @sectionAngle.setter
    def sectionAngle (self, ang: float) -> None:
        """Atribui Ângulo de inserção da seção em graus."""
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varang          = ctypes.c_double (ang)
        self.m_model.m_eagme.BASME_GEOPIL_ANG_DEF (ctypes.byref (vargeopil),
                            ctypes.byref (varang))

    @property
    def sectionMaterial (self) -> str:
        """Título do material diferente do concreto (não padrão).

        Returns:
            Cadeia de caracteres.
        """
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varmaternp      = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GEOPIL_MATERNP_LER (ctypes.byref (vargeopil),
                            ctypes.byref (varmaternp))
        maternp         = varmaternp.value.decode(TQSUtil.CHARSET)
        return          maternp

    @sectionMaterial.setter
    def sectionMaterial (self, maternp: str) -> None:
        """Atribui Título do material diferente do concreto (não padrão)."""
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varmaternp      = ctypes.c_char_p (maternp.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GEOPIL_MATERNP_DEF (ctypes.byref (vargeopil),
                            ctypes.byref (varmaternp))

    @property
    def sectionName (self) -> str:
        """Nome de seção não padrão - catalogada.

        Returns:
            Cadeia de caracteres.
        """
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varsecaonp      = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GEOPIL_SECAONP_LER (ctypes.byref (vargeopil),
                            ctypes.byref (varsecaonp))
        secaonp         = varsecaonp.value.decode(TQSUtil.CHARSET)
        return          secaonp

    @sectionName.setter
    def sectionName (self, secaonp: str) -> None:
        """Atribui Nome de seção não padrão - catalogada."""
        vargeopil       = ctypes.c_void_p (self.m_geopil)
        varsecaonp      = ctypes.c_char_p (secaonp.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GEOPIL_SECAONP_DEF (ctypes.byref (vargeopil),
                            ctypes.byref (varsecaonp))

#------------------------------------------------------------------------------
#       Dados de inserção de pilar CInsPil
#
class ColumnInsertion ():

    """Inserção de pilar.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", inspil: int) -> None:
        """Dados de inserção de pilar.

        Args:
            model: Objeto Model() do modelo atual.
            inspil: Apontador para objeto CInsPil.
        """
        self.m_model    = model
        self.m_inspil   = inspil

    @property
    def insertionType (self) -> int:
        """Inserção de pilar por (0) Centro (1) Canto.

        Returns:
            Valor inteiro.
        """
        varinspil       = ctypes.c_void_p (self.m_inspil)
        ipilins         = 0
        varipilins      = ctypes.c_int (ipilins)
        self.m_model.m_eagme.BASME_INSPIL_IPILINS_LER (ctypes.byref (varinspil),
                            ctypes.byref (varipilins))
        ipilins          = varipilins.value
        return          ipilins

    @insertionType.setter
    def insertionType (self, ipilins: int) -> None:
        """Atribui Inserção de pilar por (0) Centro (1) Canto."""
        varinspil       = ctypes.c_void_p (self.m_inspil)
        varipilins      = ctypes.c_int (ipilins)
        self.m_model.m_eagme.BASME_INSPIL_IPILINS_DEF (ctypes.byref (varinspil),
                            ctypes.byref (varipilins))

    @property
    def insertionCorner (self) -> int:
        """Numero do canto (0..) para insertionType == 1.

        Returns:
            Valor inteiro.
        """
        varinspil       = ctypes.c_void_p (self.m_inspil)
        ipilcan         = 0
        varipilcan      = ctypes.c_int (ipilcan)
        self.m_model.m_eagme.BASME_INSPIL_IPILCAN_LER (ctypes.byref (varinspil),
                            ctypes.byref (varipilcan))
        ipilcan          = varipilcan.value
        return          ipilcan

    @insertionCorner.setter
    def insertionCorner (self, ipilcan: int) -> None:
        """Atribui Numero do canto (0..) para insertionType == 1."""
        varinspil       = ctypes.c_void_p (self.m_inspil)
        varipilcan      = ctypes.c_int (ipilcan)
        self.m_model.m_eagme.BASME_INSPIL_IPILCAN_DEF (ctypes.byref (varinspil),
                            ctypes.byref (varipilcan))

    @property
    def sectionCover (self) -> float:
        """Revestimento cm.

        Returns:
            Valor de ponto flutuante.
        """
        varinspil       = ctypes.c_void_p (self.m_inspil)
        revpil          = 0
        varrevpil       = ctypes.c_double (revpil)
        self.m_model.m_eagme.BASME_INSPIL_REVPIL_LER (ctypes.byref (varinspil),
                            ctypes.byref (varrevpil))
        revpil          = varrevpil.value
        return          revpil

    @sectionCover.setter
    def sectionCover (self, revpil: float) -> None:
        """Atribui Revestimento cm."""
        varinspil       = ctypes.c_void_p (self.m_inspil)
        varrevpil       = ctypes.c_double (revpil)
        self.m_model.m_eagme.BASME_INSPIL_REVPIL_DEF (ctypes.byref (varinspil),
                            ctypes.byref (varrevpil))

    @property
    def mediumPointInsertion (self) -> int:
        """Inserção por ponto intermediário (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varinspil       = ctypes.c_void_p (self.m_inspil)
        intermed        = 0
        varintermed     = ctypes.c_int (intermed)
        self.m_model.m_eagme.BASME_INSPIL_INTERMED_LER (ctypes.byref (varinspil),
                            ctypes.byref (varintermed))
        intermed        = varintermed.value
        return          intermed

    @mediumPointInsertion.setter
    def mediumPointInsertion (self, intermed: int) -> None:
        """Atribui Inserção por ponto intermediário (0) Não (1) Sim."""
        varinspil       = ctypes.c_void_p (self.m_inspil)
        varintermed     = ctypes.c_int (intermed)
        self.m_model.m_eagme.BASME_INSPIL_INTERMED_DEF (ctypes.byref (varinspil),
                            ctypes.byref (varintermed))


#------------------------------------------------------------------------------
#       Modos de visualização CModVis
#
class VisModes ():

    """Modos de visualização.

    Implementação:
        Container dos modos de visualização por categoria (pilares, vigas, lajes, etc.).
        Cada sub-objeto é instanciado no ``__init__`` apontando para o mesmo ``CModVis``
        do C++; alterar uma flag em qualquer sub-objeto reflete imediatamente no editor.
    """
    def __init__ (self, model: "Model", modvis: int) -> None:
        """Classe que define modos de visualização do Modelador.

        Args:
            model: Objeto Model() do modelo atual.
            modvis: Apontador para objeto CModVis.
        """
        self.m_model     = model
        self.m_modvis    = modvis

        self.columns     = VisModeColumns (model, self)
        self.beams       = VisModeBeams (model, self)
        self.slabs       = VisModeSlabs (model, self)
        self.details     = VisModeDetails (model, self)
        self.bim         = VisModeBim (model, self)
        self.loads       = VisModeLoads (model, self)
        self.foundations = VisModeFoundations (model, self)
        self.precast     = VisModePrecast (model, self)
#
#       Modos de visualização de pilares
#
class VisModeColumns ():

    """Modos de visualização de pilares.

    Implementação:
        Property bag de flags de visualização; cada propriedade lê/escreve um inteiro
        booleano via ``BASME_MODVIS_*`` no ``CModVis`` correspondente ao modo selecionado.
    """
    def __init__ (self, model: "Model", vismodes: int) -> None:
        """Modos de visualização de pilares.

        Args:
            model: Objeto Model() do modelo atual.
            vismodes: Apontador para objeto VisModes.
        """
        self.m_model    = model
        self.m_vismodes = vismodes

    @property
    def columns (self) -> int:
        """Pilares (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pilares         = 0
        varpilares      = ctypes.c_int (pilares)
        self.m_model.m_eagme.BASME_MODVIS_PILARES_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpilares))
        pilares          = varpilares.value
        return          pilares

    @columns.setter
    def columns (self, pilares: int) -> None:
        """Atribui Pilares (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpilares       = ctypes.c_int (pilares)
        self.m_model.m_eagme.BASME_MODVIS_PILARES_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpilares))

    @property
    def name (self) -> int:
        """Título de pilar (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        piltit          = 0
        varpiltit       = ctypes.c_int (piltit)
        self.m_model.m_eagme.BASME_MODVIS_PILTIT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpiltit))
        piltit          = varpiltit.value
        return          piltit

    @name.setter
    def name (self, piltit: int) -> None:
        """Atribui Título de pilar (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpiltit       = ctypes.c_int (piltit)
        self.m_model.m_eagme.BASME_MODVIS_PILTIT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpiltit))

    @property
    def dimensions (self) -> int:
        """Dimensões de pilares (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pildim          = 0
        varpildim       = ctypes.c_int (pildim)
        self.m_model.m_eagme.BASME_MODVIS_PILDIM_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpildim))
        pildim          = varpildim.value
        return          pildim

    @dimensions.setter
    def dimensions (self, pildim: int) -> None:
        """Atribui Dimensões de pilares (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpildim       = ctypes.c_int (pildim)
        self.m_model.m_eagme.BASME_MODVIS_PILDIM_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpildim))
    @property
    def overlapUpper (self) -> int:
        """Sobreposição de pilar atual e superior (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pilsobre        = 0
        varpilsobre     = ctypes.c_int (pilsobre)
        self.m_model.m_eagme.BASME_MODVIS_PILSOBRE_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpilsobre))
        pilsobre        = varpilsobre.value
        return          pilsobre

    @overlapUpper.setter
    def overlapUpper (self, pilsobre: int) -> None:
        """Atribui Sobreposição de pilar atual e superior (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpilsobre     = ctypes.c_int (pilsobre)
        self.m_model.m_eagme.BASME_MODVIS_PILSOBRE_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpilsobre))
    @property
    def overlapBottom (self) -> int:
        """Sobreposição de pilar atual e inferior(0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pilsobreinf     = 0
        varpilsobreinf  = ctypes.c_int (pilsobreinf)
        self.m_model.m_eagme.BASME_MODVIS_PILSOBREINF_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpilsobreinf))
        pilsobreinf     = varpilsobreinf.value
        return          pilsobreinf

    @overlapBottom.setter
    def overlapBottom (self, pilsobreinf: int) -> None:
        """Atribui Sobreposição de pilar atual e inferior(0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpilsobreinf  = ctypes.c_int (pilsobreinf)
        self.m_model.m_eagme.BASME_MODVIS_PILSOBREINF_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpilsobreinf))

    @property
    def gridSupport (self) -> int:
        """Condições de apoio em grelha (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pilgre          = 0
        varpilgre       = ctypes.c_int (pilgre)
        self.m_model.m_eagme.BASME_MODVIS_PILGRE_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpilgre))
        pilgre          = varpilgre.value
        return          pilgre

    @gridSupport.setter
    def gridSupport (self, pilgre: int) -> None:
        """Atribui Condições de apoio em grelha (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpilgre       = ctypes.c_int (pilgre)
        self.m_model.m_eagme.BASME_MODVIS_PILGRE_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpilgre))

    @property
    def axes (self) -> int:
        """Eixos de pilares (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pileix          = 0
        varpileix       = ctypes.c_int (pileix)
        self.m_model.m_eagme.BASME_MODVIS_PILEIX_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpileix))
        pileix          = varpileix.value
        return          pileix

    @axes.setter
    def axes (self, pileix: int) -> None:
        """Atribui Eixos de pilares (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpileix       = ctypes.c_int (pileix)
        self.m_model.m_eagme.BASME_MODVIS_PILEIX_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpileix))

    @property
    def details (self) -> int:
        """Outros dados de detalhamento de pilares (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pildad          = 0
        varpildad       = ctypes.c_int (pildad)
        self.m_model.m_eagme.BASME_MODVIS_PILDAD_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpildad))
        pildad          = varpildad.value
        return          pildad

    @details.setter
    def details (self, pildad: int) -> None:
        """Atribui Outros dados de detalhamento de pilares (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpildad       = ctypes.c_int (pildad)
        self.m_model.m_eagme.BASME_MODVIS_PILDAD_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpildad))

    @property
    def circle (self) -> int:
        """Pilares circulares como círculos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        idiscretcirc    = 0
        varidiscretcirc = ctypes.c_int (idiscretcirc)
        self.m_model.m_eagme.BASME_MODVIS_IDISCRETCIRC_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varidiscretcirc))
        idiscretcirc    = varidiscretcirc.value
        return          idiscretcirc

    @circle.setter
    def circle (self, idiscretcirc: int) -> None:
        """Atribui Pilares circulares como círculos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varidiscretcirc = ctypes.c_int (idiscretcirc)
        self.m_model.m_eagme.BASME_MODVIS_IDISCRETCIRC_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varidiscretcirc))

    @property
    def shearStrip (self) -> int:
        """Mostra lâmina de pilares parede (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pillamina       = 0
        varpillamina    = ctypes.c_int (pillamina)
        self.m_model.m_eagme.BASME_MODVIS_PILLAMINA_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpillamina))
        pillamina       = varpillamina.value
        return          pillamina

    @shearStrip.setter
    def shearStrip (self, pillamina: int) -> None:
        """Atribui Mostra lâmina de pilares parede (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpillamina    = ctypes.c_int (pillamina)
        self.m_model.m_eagme.BASME_MODVIS_PILLAMINA_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpillamina))

    @property
    def shearWallDiscret (self) -> int:
        """Discretização de pilar parede (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pildiscret      = 0
        varpildiscret   = ctypes.c_int (pildiscret)
        self.m_model.m_eagme.BASME_MODVIS_PILDISCRET_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpildiscret))
        pildiscret      = varpildiscret.value
        return          pildiscret

    @shearWallDiscret.setter
    def shearWallDiscret (self, pildiscret: int) -> None:
        """Atribui Discretização de pilar parede (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpildiscret   = ctypes.c_int (pildiscret)
        self.m_model.m_eagme.BASME_MODVIS_PILDISCRET_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpildiscret))

    @property
    def fixedPoint (self) -> int:
        """Ponto fixo do pilar (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pilptfixo       = 0
        varpilptfixo    = ctypes.c_int (pilptfixo)
        self.m_model.m_eagme.BASME_MODVIS_PILPTFIXO_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpilptfixo))
        pilptfixo       = varpilptfixo.value
        return          pilptfixo

    @fixedPoint.setter
    def fixedPoint (self, pilptfixo: int) -> None:
        """Atribui Ponto fixo do pilar (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpilptfixo    = ctypes.c_int (pilptfixo)
        self.m_model.m_eagme.BASME_MODVIS_PILPTFIXO_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpilptfixo))

    @property
    def imposedRestraint (self) -> int:
        """Travamento imposto (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        piltrav         = 0
        varpiltrav      = ctypes.c_int (piltrav)
        self.m_model.m_eagme.BASME_MODVIS_PILTRAV_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpiltrav))
        piltrav         = varpiltrav.value
        return          piltrav

    @imposedRestraint.setter
    def imposedRestraint (self, piltrav: int) -> None:
        """Atribui Travamento imposto (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpiltrav      = ctypes.c_int (piltrav)
        self.m_model.m_eagme.BASME_MODVIS_PILTRAV_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpiltrav))

    @property
    def ficticiousSupport (self) -> int:
        """Apoios fictícios (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pilificticio     = 0
        varpilificticio  = ctypes.c_int (pilificticio)
        self.m_model.m_eagme.BASME_MODVIS_PILIFICTICIO_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpilificticio))
        pilificticio     = varpilificticio.value
        return          pilificticio

    @ficticiousSupport.setter
    def ficticiousSupport (self, pilificticio: int) -> None:
        """Atribui Apoios fictícios (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpilificticio  = ctypes.c_int (pilificticio)
        self.m_model.m_eagme.BASME_MODVIS_PILIFICTICIO_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpilificticio))

    @property
    def horizontalOpenings (self) -> int:
        """Furos em pilares (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pilfur          = 0
        varpilfur       = ctypes.c_int (pilfur)
        self.m_model.m_eagme.BASME_MODVIS_PILFUR_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpilfur))
        pilfur          = varpilfur.value
        return          pilfur

    @horizontalOpenings.setter
    def horizontalOpenings (self, pilfur: int) -> None:
        """Atribui Furos em pilares (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpilfur       = ctypes.c_int (pilfur)
        self.m_model.m_eagme.BASME_MODVIS_PILFUR_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpilfur))

    @property
    def metalCheck (self) -> int:
        """Resultados de pilares no MetalCheck (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        pilmetalcheck   = 0
        varpilmetalcheck= ctypes.c_int (pilmetalcheck)
        self.m_model.m_eagme.BASME_MODVIS_PILMETALCHECK_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varpilmetalcheck))
        pilmetalcheck   = varpilmetalcheck.value
        return          pilmetalcheck

    @metalCheck.setter
    def metalCheck (self, pilmetalcheck: int) -> None:
        """Atribui Resultados de pilares no MetalCheck (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varpilmetalcheck= ctypes.c_int (pilmetalcheck)
        self.m_model.m_eagme.BASME_MODVIS_PILMETALCHECK_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varpilmetalcheck))

#
#       Modos de visualização de vigas
#
class VisModeBeams ():

    """Modos de visualização de vigas.

    Implementação:
        Property bag de flags de visualização; cada propriedade lê/escreve um inteiro
        booleano via ``BASME_MODVIS_*`` no ``CModVis`` correspondente ao modo selecionado.
    """
    def __init__ (self, model: "Model", vismodes: int) -> None:
        """Modos de visualização de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            vismodes: Apontador para objeto VisModes.
        """
        self.m_model    = model
        self.m_vismodes = vismodes

    @property
    def beams (self) -> int:
        """Vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigas           = 0
        varvigas        = ctypes.c_int (vigas)
        self.m_model.m_eagme.BASME_MODVIS_VIGAS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigas))
        vigas           = varvigas.value
        return          vigas

    @beams.setter
    def beams (self, vigas: int) -> None:
        """Atribui Vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigas        = ctypes.c_int (vigas)
        self.m_model.m_eagme.BASME_MODVIS_VIGAS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigas))

    @property
    def name (self) -> int:
        """Título de vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigtit          = 0
        varvigtit       = ctypes.c_int (vigtit)
        self.m_model.m_eagme.BASME_MODVIS_VIGTIT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigtit))
        vigtit          = varvigtit.value
        return          vigtit

    @name.setter
    def name (self, vigtit: int) -> None:
        """Atribui Título de vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigtit       = ctypes.c_int (vigtit)
        self.m_model.m_eagme.BASME_MODVIS_VIGTIT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigtit))

    @property
    def dimensions (self) -> int:
        """Título de vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigdim          = 0
        varvigdim       = ctypes.c_int (vigdim)
        self.m_model.m_eagme.BASME_MODVIS_VIGDIM_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigdim))
        vigdim          = varvigdim.value
        return          vigdim

    @dimensions.setter
    def dimensions (self, vigdim: int) -> None:
        """Atribui Título de vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigdim       = ctypes.c_int (vigdim)
        self.m_model.m_eagme.BASME_MODVIS_VIGDIM_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigdim))


    @property
    def axes (self) -> int:
        """Eixos de vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigeix          = 0
        varvigeix       = ctypes.c_int (vigeix)
        self.m_model.m_eagme.BASME_MODVIS_VIGEIX_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigeix))
        vigeix          = varvigeix.value
        return          vigeix

    @axes.setter
    def axes (self, vigeix: int) -> None:
        """Atribui Eixos de vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigeix       = ctypes.c_int (vigeix)
        self.m_model.m_eagme.BASME_MODVIS_VIGEIX_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigeix))

    @property
    def connections (self) -> int:
        """Vinculações de vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigvinc         = 0
        varvigvinc      = ctypes.c_int (vigvinc)
        self.m_model.m_eagme.BASME_MODVIS_VIGVINC_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigvinc))
        vigvinc         = varvigvinc.value
        return          vigvinc

    @connections.setter
    def connections (self, vigvinc: int) -> None:
        """Atribui Vinculações de vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigvinc      = ctypes.c_int (vigvinc)
        self.m_model.m_eagme.BASME_MODVIS_VIGVINC_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigvinc))

    @property
    def nodes (self) -> int:
        """Nós de vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vignos          = 0
        varvignos       = ctypes.c_int (vignos)
        self.m_model.m_eagme.BASME_MODVIS_VIGNOS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvignos))
        vignos          = varvignos.value
        return          vignos

    @nodes.setter
    def nodes (self, vignos: int) -> None:
        """Atribui Nós de vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvignos       = ctypes.c_int (vignos)
        self.m_model.m_eagme.BASME_MODVIS_VIGNOS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvignos))

    @property
    def details (self) -> int:
        """Outros dados de detalhamento de vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigdad          = 0
        varvigdad       = ctypes.c_int (vigdad)
        self.m_model.m_eagme.BASME_MODVIS_VIGDAD_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigdad))
        vigdad          = varvigdad.value
        return          vigdad

    @details.setter
    def details (self, vigdad: int) -> None:
        """Atribui Outros dados de detalhamento de vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigdad       = ctypes.c_int (vigdad)
        self.m_model.m_eagme.BASME_MODVIS_VIGDAD_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigdad))

    @property
    def sectionT (self) -> int:
        """Seção T e B colaborante (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigsect         = 0
        varvigsect      = ctypes.c_int (vigsect)
        self.m_model.m_eagme.BASME_MODVIS_VIGSECT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigsect))
        vigsect         = varvigsect.value
        return          vigsect

    @sectionT.setter
    def sectionT (self, vigsect: int) -> None:
        """Atribui Seção T e B colaborante (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigsect      = ctypes.c_int (vigsect)
        self.m_model.m_eagme.BASME_MODVIS_VIGSECT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigsect))

    @property
    def cantilever (self) -> int:
        """Pintar vigas em balanço (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigbal          = 0
        varvigbal       = ctypes.c_int (vigbal)
        self.m_model.m_eagme.BASME_MODVIS_VIGBAL_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigbal))
        vigbal          = varvigbal.value
        return          vigbal

    @cantilever.setter
    def cantilever (self, vigbal: int) -> None:
        """Atribui Pintar vigas em balanço (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigbal       = ctypes.c_int (vigbal)
        self.m_model.m_eagme.BASME_MODVIS_VIGBAL_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigbal))

    @property
    def openings (self) -> int:
        """Furos horizontais (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigfur          = 0
        varvigfur       = ctypes.c_int (vigfur)
        self.m_model.m_eagme.BASME_MODVIS_VIGFUR_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigfur))
        vigfur          = varvigfur.value
        return          vigfur

    @openings.setter
    def openings (self, vigfur: int) -> None:
        """Atribui Furos horizontais (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigfur       = ctypes.c_int (vigfur)
        self.m_model.m_eagme.BASME_MODVIS_VIGFUR_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigfur))

    @property
    def transferBeam (self) -> int:
        """Viga de transição (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigtrans        = 0
        varvigtrans     = ctypes.c_int (vigtrans)
        self.m_model.m_eagme.BASME_MODVIS_VIGTRANS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigtrans))
        vigtrans        = varvigtrans.value
        return          vigtrans

    @transferBeam.setter
    def transferBeam (self, vigtrans: int) -> None:
        """Atribui Viga de transição (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigtrans     = ctypes.c_int (vigtrans)
        self.m_model.m_eagme.BASME_MODVIS_VIGTRANS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigtrans))

    @property
    def metalCheck (self) -> int:
        """Vigas no MetalCheck (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigmetalcheck   = 0
        varvigmetalcheck= ctypes.c_int (vigmetalcheck)
        self.m_model.m_eagme.BASME_MODVIS_VIGMETALCHECK_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigmetalcheck))
        vigmetalcheck   = varvigmetalcheck.value
        return          vigmetalcheck

    @metalCheck.setter
    def metalCheck (self, vigmetalcheck: int) -> None:
        """Atribui Vigas no MetalCheck (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigmetalcheck= ctypes.c_int (vigmetalcheck)
        self.m_model.m_eagme.BASME_MODVIS_VIGMETALCHECK_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigmetalcheck))

    @property
    def precast (self) -> int:
        """Pintar vigas protendidas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vigprotend        = 0
        varvigprotend     = ctypes.c_int (vigprotend)
        self.m_model.m_eagme.BASME_MODVIS_VIGPROTEND_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varvigprotend))
        vigprotend        = varvigprotend.value
        return          vigprotend

    @precast.setter
    def precast (self, vigprotend: int) -> None:
        """Atribui Pintar vigas protendidas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varvigprotend     = ctypes.c_int (vigprotend)
        self.m_model.m_eagme.BASME_MODVIS_VIGPROTEND_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varvigprotend))

#
#       Modos de visualização de lajes
#
class VisModeSlabs ():

    """Modos de visualização de lajes.

    Implementação:
        Property bag de flags de visualização; cada propriedade lê/escreve um inteiro
        booleano via ``BASME_MODVIS_*`` no ``CModVis`` correspondente ao modo selecionado.
    """
    def __init__ (self, model: "Model", vismodes: int) -> None:
        """Modos de visualização de lajes.

        Args:
            model: Objeto Model() do modelo atual.
            vismodes: Apontador para objeto VisModes.
        """
        self.m_model    = model
        self.m_vismodes = vismodes

    @property
    def slabs (self) -> int:
        """Lajes (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajes           = 0
        varlajes        = ctypes.c_int (lajes)
        self.m_model.m_eagme.BASME_MODVIS_LAJES_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajes))
        lajes           = varlajes.value
        return          lajes

    @slabs.setter
    def slabs (self, lajes: int) -> None:
        """Atribui Lajes (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajes        = ctypes.c_int (lajes)
        self.m_model.m_eagme.BASME_MODVIS_LAJES_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajes))

    @property
    def name (self) -> int:
        """Título de lajes (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajtit          = 0
        varlajtit       = ctypes.c_int (lajtit)
        self.m_model.m_eagme.BASME_MODVIS_LAJTIT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajtit))
        lajtit          = varlajtit.value
        return          lajtit

    @name.setter
    def name (self, lajtit: int) -> None:
        """Atribui Título de lajes (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajtit       = ctypes.c_int (lajtit)
        self.m_model.m_eagme.BASME_MODVIS_LAJTIT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajtit))

    @property
    def dimensions (self) -> int:
        """Dimensões de lajes (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajdim          = 0
        varlajdim       = ctypes.c_int (lajdim)
        self.m_model.m_eagme.BASME_MODVIS_LAJDIM_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajdim))
        lajdim          = varlajdim.value
        return          lajdim

    @dimensions.setter
    def dimensions (self, lajdim: int) -> None:
        """Atribui Dimensões de lajes (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajdim       = ctypes.c_int (lajdim)
        self.m_model.m_eagme.BASME_MODVIS_LAJDIM_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajdim))

    @property
    def mainDirection (self) -> int:
        """Símbolo de ângulo principal da laje (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajang          = 0
        varlajang       = ctypes.c_int (lajang)
        self.m_model.m_eagme.BASME_MODVIS_LAJANG_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajang))
        lajang          = varlajang.value
        return          lajang

    @mainDirection.setter
    def mainDirection (self, lajang: int) -> None:
        """Atribui Símbolo de ângulo principal da laje (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajang       = ctypes.c_int (lajang)
        self.m_model.m_eagme.BASME_MODVIS_LAJANG_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajang))

    @property
    def contour (self) -> int:
        """Contorno da laje (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajcont         = 0
        varlajcont      = ctypes.c_int (lajcont)
        self.m_model.m_eagme.BASME_MODVIS_LAJCONT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajcont))
        lajcont         = varlajcont.value
        return          lajcont

    @contour.setter
    def contour (self, lajcont: int) -> None:
        """Atribui Contorno da laje (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajcont      = ctypes.c_int (lajcont)
        self.m_model.m_eagme.BASME_MODVIS_LAJCONT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajcont))

    @property
    def details (self) -> int:
        """Outros dados de detalhamento de lajes (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajdad          = 0
        varlajdad       = ctypes.c_int (lajdad)
        self.m_model.m_eagme.BASME_MODVIS_LAJDAD_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajdad))
        lajdad          = varlajdad.value
        return          lajdad

    @details.setter
    def details (self, lajdad: int) -> None:
        """Atribui Outros dados de detalhamento de lajes (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajdad       = ctypes.c_int (lajdad)
        self.m_model.m_eagme.BASME_MODVIS_LAJDAD_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajdad))

    @property
    def ribs (self) -> int:
        """Nervuras em lajes (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajner          = 0
        varlajner       = ctypes.c_int (lajner)
        self.m_model.m_eagme.BASME_MODVIS_LAJNER_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajner))
        lajner          = varlajner.value
        return          lajner

    @ribs.setter
    def ribs (self, lajner: int) -> None:
        """Atribui Nervuras em lajes (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajner       = ctypes.c_int (lajner)
        self.m_model.m_eagme.BASME_MODVIS_LAJNER_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajner))

    @property
    def openings (self) -> int:
        """Furos em lajes (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajfuros        = 0
        varlajfuros     = ctypes.c_int (lajfuros)
        self.m_model.m_eagme.BASME_MODVIS_LAJFUROS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajfuros))
        lajfuros        = varlajfuros.value
        return          lajfuros

    @openings.setter
    def openings (self, lajfuros: int) -> None:
        """Atribui Furos em lajes (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajfuros     = ctypes.c_int (lajfuros)
        self.m_model.m_eagme.BASME_MODVIS_LAJFUROS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajfuros))

    @property
    def caps (self) -> int:
        """Capitéis (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajcapit        = 0
        varlajcapit     = ctypes.c_int (lajcapit)
        self.m_model.m_eagme.BASME_MODVIS_LAJCAPIT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajcapit))
        lajcapit        = varlajcapit.value
        return          lajcapit

    @caps.setter
    def caps (self, lajcapit: int) -> None:
        """Atribui Capitéis (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajcapit     = ctypes.c_int (lajcapit)
        self.m_model.m_eagme.BASME_MODVIS_LAJCAPIT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajcapit))

    @property
    def trapezoidalRibs (self) -> int:
        """Bordas de nervuras trapezoidais (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajborner       = 0
        varlajborner    = ctypes.c_int (lajborner)
        self.m_model.m_eagme.BASME_MODVIS_LAJBORNER_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajborner))
        lajborner       = varlajborner.value
        return          lajborner

    @trapezoidalRibs.setter
    def trapezoidalRibs (self, lajborner: int) -> None:
        """Atribui Bordas de nervuras trapezoidais (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajborner    = ctypes.c_int (lajborner)
        self.m_model.m_eagme.BASME_MODVIS_LAJBORNER_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajborner))

    @property
    def ficticiusRibs (self) -> int:
        """Nervuras em maciços (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajnermac       = 0
        varlajnermac    = ctypes.c_int (lajnermac)
        self.m_model.m_eagme.BASME_MODVIS_LAJNERMAC_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajnermac))
        lajnermac       = varlajnermac.value
        return          lajnermac

    @ficticiusRibs.setter
    def ficticiusRibs (self, lajnermac: int) -> None:
        """Atribui Nervuras em maciços (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajnermac    = ctypes.c_int (lajnermac)
        self.m_model.m_eagme.BASME_MODVIS_LAJNERMAC_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajnermac))

    @property
    def prefabDir (self) -> int:
        """Direção de nervuras (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajdirner       = 0
        varlajdirner    = ctypes.c_int (lajdirner)
        self.m_model.m_eagme.BASME_MODVIS_LAJDIRNER_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajdirner))
        lajdirner       = varlajdirner.value
        return          lajdirner

    @prefabDir.setter
    def prefabDir (self, lajdirner: int) -> None:
        """Atribui Direção de nervuras (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajdirner    = ctypes.c_int (lajdirner)
        self.m_model.m_eagme.BASME_MODVIS_LAJDIRNER_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajdirner))

    @property
    def cantilever (self) -> int:
        """Laje em balanço (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        lajbalan       = 0
        varlajbalan    = ctypes.c_int (lajbalan)
        self.m_model.m_eagme.BASME_MODVIS_LAJBALAN_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlajbalan))
        lajbalan       = varlajbalan.value
        return          lajbalan

    @cantilever.setter
    def cantilever (self, lajbalan: int) -> None:
        """Atribui Laje em balanço (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlajbalan    = ctypes.c_int (lajbalan)
        self.m_model.m_eagme.BASME_MODVIS_LAJBALAN_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlajbalan))

#
#       Modos de visualização de detalhamento (outros dados)
#
class VisModeDetails ():

    """Modos de visualização de detalhes.

    Implementação:
        Property bag de flags de visualização; cada propriedade lê/escreve um inteiro
        booleano via ``BASME_MODVIS_*`` no ``CModVis`` correspondente ao modo selecionado.
    """
    def __init__ (self, model: "Model", vismodes: int) -> None:
        """Modos de visualização de detalhamento.

        Args:
            model: Objeto Model() do modelo atual.
            vismodes: Apontador para objeto VisModes.
        """
        self.m_model    = model
        self.m_vismodes = vismodes

    @property
    def crossSections (self) -> int:
        """Cortes da planta de formas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        cortes          = 0
        varcortes       = ctypes.c_int (cortes)
        self.m_model.m_eagme.BASME_MODVIS_CORTES_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcortes))
        cortes          = varcortes.value
        return          cortes

    @crossSections.setter
    def crossSections (self, cortes: int) -> None:
        """Atribui Cortes da planta de formas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcortes       = ctypes.c_int (cortes)
        self.m_model.m_eagme.BASME_MODVIS_CORTES_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcortes))

    @property
    def dimensions (self) -> int:
        """Cotas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        cotas          = 0
        varcotas       = ctypes.c_int (cotas)
        self.m_model.m_eagme.BASME_MODVIS_COTAS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcotas))
        cotas          = varcotas.value
        return          cotas

    @dimensions.setter
    def dimensions (self, cotas: int) -> None:
        """Atribui Cotas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcotas       = ctypes.c_int (cotas)
        self.m_model.m_eagme.BASME_MODVIS_COTAS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcotas))

    @property
    def controlPoints (self) -> int:
        """Pontos de controle de cotagem (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        cotascontrole   = 0
        varcotascontrole= ctypes.c_int (cotascontrole)
        self.m_model.m_eagme.BASME_MODVIS_COTASCONTROLE_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcotascontrole))
        cotascontrole   = varcotascontrole.value
        return          cotascontrole

    @controlPoints.setter
    def controlPoints (self, cotascontrole: int) -> None:
        """Atribui Pontos de controle de cotagem (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcotascontrole= ctypes.c_int (cotascontrole)
        self.m_model.m_eagme.BASME_MODVIS_COTASCONTROLE_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcotascontrole))
    @property
    def formworkArea (self) -> int:
        """Áreas de vigas, pilares, lajes (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        iareas          = 0
        variareas       = ctypes.c_int (iareas)
        self.m_model.m_eagme.BASME_MODVIS_IAREAS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (variareas))
        iareas          = variareas.value
        return          iareas

    @formworkArea.setter
    def formworkArea (self, iareas: int) -> None:
        """Atribui Áreas de vigas, pilares, lajes (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        variareas       = ctypes.c_int (iareas)
        self.m_model.m_eagme.BASME_MODVIS_IAREAS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (variareas))

    @property
    def axes (self) -> int:
        """Eixos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        eixos           = 0
        vareixos        = ctypes.c_int (eixos)
        self.m_model.m_eagme.BASME_MODVIS_EIXOS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (vareixos))
        eixos           = vareixos.value
        return          eixos

    @axes.setter
    def axes (self, eixos: int) -> None:
        """Atribui Eixos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vareixos        = ctypes.c_int (eixos)
        self.m_model.m_eagme.BASME_MODVIS_EIXOS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (vareixos))

    @property
    def centroidsTable (self) -> int:
        """Tabela de baricentros (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        baricentros     = 0
        varbaricentros  = ctypes.c_int (baricentros)
        self.m_model.m_eagme.BASME_MODVIS_BARICENTROS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varbaricentros))
        baricentros     = varbaricentros.value
        return          baricentros

    @centroidsTable.setter
    def centroidsTable (self, baricentros: int) -> None:
        """Atribui Tabela de baricentros (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varbaricentros  = ctypes.c_int (baricentros)
        self.m_model.m_eagme.BASME_MODVIS_BARICENTROS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varbaricentros))

    @property
    def overlapAuxFloors (self) -> int:
        """Sobrepõe pisos auxiliares (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        mixpisosaux     = 0
        varmixpisosaux  = ctypes.c_int (mixpisosaux)
        self.m_model.m_eagme.BASME_MODVIS_MIXPISOSAUX_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varmixpisosaux))
        mixpisosaux     = varmixpisosaux.value
        return          mixpisosaux

    @overlapAuxFloors.setter
    def overlapAuxFloors (self, mixpisosaux: int) -> None:
        """Atribui Sobrepõe pisos auxiliares (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varmixpisosaux  = ctypes.c_int (mixpisosaux)
        self.m_model.m_eagme.BASME_MODVIS_MIXPISOSAUX_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varmixpisosaux))

    @property
    def elementsTable (self) -> int:
        """Tabela de elementos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        tabelem         = 0
        vartabelem      = ctypes.c_int (tabelem)
        self.m_model.m_eagme.BASME_MODVIS_TABELEM_LER (ctypes.byref (varmodvis),
                            ctypes.byref (vartabelem))
        tabelem         = vartabelem.value
        return          tabelem

    @elementsTable.setter
    def elementsTable (self, tabelem: int) -> None:
        """Atribui Tabela de elementos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        vartabelem      = ctypes.c_int (tabelem)
        self.m_model.m_eagme.BASME_MODVIS_TABELEM_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (vartabelem))

    @property
    def tunnelReference (self) -> int:
        """Centro de torção - referência de túnel de vento (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        icentor         = 0
        varicentor      = ctypes.c_int (icentor)
        self.m_model.m_eagme.BASME_MODVIS_ICENTOR_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varicentor))
        icentor         = varicentor.value
        return          icentor

    @tunnelReference.setter
    def tunnelReference (self, icentor: int) -> None:
        """Atribui Centro de torção - referência de túnel de vento (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varicentor      = ctypes.c_int (icentor)
        self.m_model.m_eagme.BASME_MODVIS_ICENTOR_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varicentor))

    @property
    def linesOutOfXY (self) -> int:
        """Linhas fora da direção X/Y global (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        linhasincl      = 0
        varlinhasincl   = ctypes.c_int (linhasincl)
        self.m_model.m_eagme.BASME_MODVIS_LINHASINCL_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varlinhasincl))
        linhasincl      = varlinhasincl.value
        return          linhasincl

    @linesOutOfXY.setter
    def linesOutOfXY (self, linhasincl: int) -> None:
        """Atribui Linhas fora da direção X/Y global (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varlinhasincl   = ctypes.c_int (linhasincl)
        self.m_model.m_eagme.BASME_MODVIS_LINHASINCL_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varlinhasincl))

    @property
    def disablePlotingHatches (self) -> int:
        """Inibe display de hachuras plotadas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        inibdisplayhachur= 0
        varinibdisplayhachur = ctypes.c_int (inibdisplayhachur)
        self.m_model.m_eagme.BASME_MODVIS_INIBDISPLAYHACHUR_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varinibdisplayhachur))
        inibdisplayhachur= varinibdisplayhachur.value
        return          inibdisplayhachur

    @disablePlotingHatches.setter
    def disablePlotingHatches (self, inibdisplayhachur: int) -> None:
        """Atribui Inibe display de hachuras plotadas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varinibdisplayhachur = ctypes.c_int (inibdisplayhachur)
        self.m_model.m_eagme.BASME_MODVIS_INIBDISPLAYHACHUR_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varinibdisplayhachur))

    @property
    def hatchedUnevenness (self) -> int:
        """Legenda e hachura de desníveis (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ilegdesniv      = 0
        varilegdesniv   = ctypes.c_int (ilegdesniv)
        self.m_model.m_eagme.BASME_MODVIS_ILEGDESNIV_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varilegdesniv))
        ilegdesniv      = varilegdesniv.value
        return          ilegdesniv

    @hatchedUnevenness.setter
    def hatchedUnevenness (self, ilegdesniv: int) -> None:
        """Atribui Legenda e hachura de desníveis (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varilegdesniv   = ctypes.c_int (ilegdesniv)
        self.m_model.m_eagme.BASME_MODVIS_ILEGDESNIV_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varilegdesniv))

    @property
    def floorLevels (self) -> int:
        """Cota pavimentos em desnível (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        isimdesniv      = 0
        varisimdesniv   = ctypes.c_int (isimdesniv)
        self.m_model.m_eagme.BASME_MODVIS_ISIMDESNIV_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varisimdesniv))
        isimdesniv      = varisimdesniv.value
        return          isimdesniv

    @floorLevels.setter
    def floorLevels (self, isimdesniv: int) -> None:
        """Atribui Cota pavimentos em desnível (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varisimdesniv   = ctypes.c_int (isimdesniv)
        self.m_model.m_eagme.BASME_MODVIS_ISIMDESNIV_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varisimdesniv))

    @property
    def floorLevelsTable (self) -> int:
        """Tabela de nível dos pavimentos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        itabnivpav      = 0
        varitabnivpav   = ctypes.c_int (itabnivpav)
        self.m_model.m_eagme.BASME_MODVIS_ITABNIVPAV_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varitabnivpav))
        itabnivpav      = varitabnivpav.value
        return          itabnivpav

    @floorLevelsTable.setter
    def floorLevelsTable (self, itabnivpav: int) -> None:
        """Atribui Tabela de nível dos pavimentos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varitabnivpav   = ctypes.c_int (itabnivpav)
        self.m_model.m_eagme.BASME_MODVIS_ITABNIVPAV_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varitabnivpav))

    @property
    def towerFence (self) -> int:
        """Cerca da torre (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        icercator       = 0
        varicercator    = ctypes.c_int (icercator)
        self.m_model.m_eagme.BASME_MODVIS_ICERCATOR_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varicercator))
        icercator       = varicercator.value
        return          icercator

    @towerFence.setter
    def towerFence (self, icercator: int) -> None:
        """Atribui Cerca da torre (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varicercator    = ctypes.c_int (icercator)
        self.m_model.m_eagme.BASME_MODVIS_ICERCATOR_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varicercator))

#
#       Modos de visualização de BIM
#
class VisModeBim ():

    """Modos de visualização BIM.

    Implementação:
        Property bag de flags de visualização; cada propriedade lê/escreve um inteiro
        booleano via ``BASME_MODVIS_*`` no ``CModVis`` correspondente ao modo selecionado.
    """
    def __init__ (self, model: "Model", vismodes: int) -> None:
        """Modos de visualização de BIM.

        Args:
            model: Objeto Model() do modelo atual.
            vismodes: Apontador para objeto VisModes.
        """
        self.m_model    = model
        self.m_vismodes = vismodes

    @property
    def importStatus (self) -> int:
        """Status de importação do BIM (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        importstatus    = 0
        varimportstatus = ctypes.c_int (importstatus)
        self.m_model.m_eagme.BASME_MODVIS_IMPORTSTATUS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varimportstatus))
        importstatus    = varimportstatus.value
        return          importstatus

    @importStatus.setter
    def importStatus (self, importstatus: int) -> None:
        """Atribui Status de importação do BIM (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varimportstatus = ctypes.c_int (importstatus)
        self.m_model.m_eagme.BASME_MODVIS_IMPORTSTATUS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varimportstatus))

    @property
    def notExported (self) -> int:
        """Elementos não exportados para o BIM (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        inaoexport      = 0
        varinaoexport   = ctypes.c_int (inaoexport)
        self.m_model.m_eagme.BASME_MODVIS_INAOEXPORT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varinaoexport))
        inaoexport      = varinaoexport.value
        return          inaoexport

    @notExported.setter
    def notExported (self, inaoexport: int) -> None:
        """Atribui Elementos não exportados para o BIM (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varinaoexport   = ctypes.c_int (inaoexport)
        self.m_model.m_eagme.BASME_MODVIS_INAOEXPORT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varinaoexport))

    @property
    def importedPipes (self) -> int:
        """Tubos importados (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        itubos          = 0
        varitubos       = ctypes.c_int (itubos)
        self.m_model.m_eagme.BASME_MODVIS_ITUBOS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varitubos))
        itubos          = varitubos.value
        return          itubos

    @importedPipes.setter
    def importedPipes (self, itubos: int) -> None:
        """Atribui Tubos importados (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varitubos       = ctypes.c_int (itubos)
        self.m_model.m_eagme.BASME_MODVIS_ITUBOS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varitubos))

    @property
    def pipeView (self) -> int:
        """Visualizar tubos (0) Só na vista 3D (1) Na vista 3D e 2D.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        itubosvis       = 0
        varitubosvis    = ctypes.c_int (itubosvis)
        self.m_model.m_eagme.BASME_MODVIS_ITUBOSVIS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varitubosvis))
        itubosvis       = varitubosvis.value
        return          itubosvis

    @pipeView.setter
    def pipeView (self, itubosvis: int) -> None:
        """Atribui Visualizar tubos (0) Só na vista 3D (1) Na vista 3D e 2D."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varitubosvis    = ctypes.c_int (itubosvis)
        self.m_model.m_eagme.BASME_MODVIS_ITUBOSVIS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varitubosvis))

    @property
    def importedWalls (self) -> int:
        """Paredes importadas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ipared3d        = 0
        varipared3d     = ctypes.c_int (ipared3d)
        self.m_model.m_eagme.BASME_MODVIS_IPARED3D_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varipared3d))
        ipared3d        = varipared3d.value
        return          ipared3d

    @importedWalls.setter
    def importedWalls (self, ipared3d: int) -> None:
        """Atribui Paredes importadas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varipared3d     = ctypes.c_int (ipared3d)
        self.m_model.m_eagme.BASME_MODVIS_IPARED3D_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varipared3d))

    @property
    def objects3D (self) -> int:
        """Objetos 3D (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ielm3d          = 0
        varielm3d       = ctypes.c_int (ielm3d)
        self.m_model.m_eagme.BASME_MODVIS_IELM3D_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varielm3d))
        ielm3d          = varielm3d.value
        return          ielm3d

    @objects3D.setter
    def objects3D (self, ielm3d: int) -> None:
        """Atribui Objetos 3D (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varielm3d       = ctypes.c_int (ielm3d)
        self.m_model.m_eagme.BASME_MODVIS_IELM3D_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varielm3d))

    @property
    def plan2D (self) -> int:
        """Planta 2D como referência para o 3D (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ipla2d3d        = 0
        varipla2d3d     = ctypes.c_int (ipla2d3d)
        self.m_model.m_eagme.BASME_MODVIS_IPLA2D3D_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varipla2d3d))
        ipla2d3d        = varipla2d3d.value
        return          ipla2d3d

    @plan2D.setter
    def plan2D (self, ipla2d3d: int) -> None:
        """Atribui Planta 2D como referência para o 3D (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varipla2d3d     = ctypes.c_int (ipla2d3d)
        self.m_model.m_eagme.BASME_MODVIS_IPLA2D3D_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varipla2d3d))

    @property
    def reference3D (self) -> int:
        """Referência externa 3D (0) Abaixo (1) Acima (2) Ambos.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ivisrefext3d    = 0
        varivisrefext3d = ctypes.c_int (ivisrefext3d)
        self.m_model.m_eagme.BASME_MODVIS_IVISREFEXT3D_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varivisrefext3d))
        ivisrefext3d    = varivisrefext3d.value
        return          ivisrefext3d

    @reference3D.setter
    def reference3D (self, ivisrefext3d: int) -> None:
        """Atribui Referência externa 3D (0) Abaixo (1) Acima (2) Ambos."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varivisrefext3d = ctypes.c_int (ivisrefext3d)
        self.m_model.m_eagme.BASME_MODVIS_IVISREFEXT3D_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varivisrefext3d))

    @property
    def basePoint (self) -> int:
        """Ponto base de projeto (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        iptbas          = 0
        variptbas       = ctypes.c_int (iptbas)
        self.m_model.m_eagme.BASME_MODVIS_IPTBAS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (variptbas))
        iptbas          = variptbas.value
        return          iptbas

    @basePoint.setter
    def basePoint (self, iptbas: int) -> None:
        """Atribui Ponto base de projeto (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        variptbas       = ctypes.c_int (iptbas)
        self.m_model.m_eagme.BASME_MODVIS_IPTBAS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (variptbas))

    @property
    def surveyPoint (self) -> int:
        """Ponto de levantamento topográfico (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        iptlvt          = 0
        variptlvt       = ctypes.c_int (iptlvt)
        self.m_model.m_eagme.BASME_MODVIS_IPTLVT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (variptlvt))
        iptlvt          = variptlvt.value
        return          iptlvt

    @surveyPoint.setter
    def surveyPoint (self, iptlvt: int) -> None:
        """Atribui Ponto de levantamento topográfico (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        variptlvt       = ctypes.c_int (iptlvt)
        self.m_model.m_eagme.BASME_MODVIS_IPTLVT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (variptlvt))

#
#       Modos de visualização de cargas
#
class VisModeLoads ():

    """Modos de visualização de cargas.

    Implementação:
        Property bag de flags de visualização; cada propriedade lê/escreve um inteiro
        booleano via ``BASME_MODVIS_*`` no ``CModVis`` correspondente ao modo selecionado.
    """
    def __init__ (self, model: "Model", vismodes: int) -> None:
        """Modos de visualização de cargas.

        Args:
            model: Objeto Model() do modelo atual.
            vismodes: Apontador para objeto VisModes.
        """
        self.m_model    = model
        self.m_vismodes = vismodes

    @property
    def beamDistributedLoad (self) -> int:
        """Cargas distribuídas nas vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        cardis          = 0
        varcardis       = ctypes.c_int (cardis)
        self.m_model.m_eagme.BASME_MODVIS_CARDIS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcardis))
        cardis          = varcardis.value
        return          cardis

    @beamDistributedLoad.setter
    def beamDistributedLoad (self, cardis: int) -> None:
        """Atribui Cargas distribuídas nas vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcardis       = ctypes.c_int (cardis)
        self.m_model.m_eagme.BASME_MODVIS_CARDIS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcardis))
    @property
    def slabDistributedLoad (self) -> int:
        """Cargas distribuídas nas lajes (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        cardislaj       = 0
        varcardislaj    = ctypes.c_int (cardislaj)
        self.m_model.m_eagme.BASME_MODVIS_CARDISLAJ_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcardislaj))
        cardislaj       = varcardislaj.value
        return          cardislaj

    @slabDistributedLoad.setter
    def slabDistributedLoad (self, cardislaj: int) -> None:
        """Atribui Cargas distribuídas nas lajes (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcardislaj    = ctypes.c_int (cardislaj)
        self.m_model.m_eagme.BASME_MODVIS_CARDISLAJ_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcardislaj))
    @property
    def concentratedLoad (self) -> int:
        """Cargas concentradas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        carcon          = 0
        varcarcon       = ctypes.c_int (carcon)
        self.m_model.m_eagme.BASME_MODVIS_CARCON_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcarcon))
        carcon          = varcarcon.value
        return          carcon

    @concentratedLoad.setter
    def concentratedLoad (self, carcon: int) -> None:
        """Atribui Cargas concentradas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcarcon       = ctypes.c_int (carcon)
        self.m_model.m_eagme.BASME_MODVIS_CARCON_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcarcon))

    @property
    def linearLoad (self) -> int:
        """Cargas concentradas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        carlin          = 0
        varcarlin       = ctypes.c_int (carlin)
        self.m_model.m_eagme.BASME_MODVIS_CARLIN_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcarlin))
        carlin          = varcarlin.value
        return          carlin

    @linearLoad.setter
    def linearLoad (self, carlin: int) -> None:
        """Atribui Cargas concentradas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcarlin       = ctypes.c_int (carlin)
        self.m_model.m_eagme.BASME_MODVIS_CARLIN_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcarlin))

    @property
    def areaDistributedLoad (self) -> int:
        """Carga distribuída por área (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        carare          = 0
        varcarare       = ctypes.c_int (carare)
        self.m_model.m_eagme.BASME_MODVIS_CARARE_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcarare))
        carare          = varcarare.value
        return          carare

    @areaDistributedLoad.setter
    def areaDistributedLoad (self, carare: int) -> None:
        """Atribui Carga distribuída por área (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcarare       = ctypes.c_int (carare)
        self.m_model.m_eagme.BASME_MODVIS_CARARE_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcarare))

    @property
    def soilPressureLoad (self) -> int:
        """Cargas de empuxo (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        icaremp         = 0
        varicaremp      = ctypes.c_int (icaremp)
        self.m_model.m_eagme.BASME_MODVIS_ICAREMP_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varicaremp))
        icaremp         = varicaremp.value
        return          icaremp

    @soilPressureLoad.setter
    def soilPressureLoad (self, icaremp: int) -> None:
        """Atribui Cargas de empuxo (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varicaremp      = ctypes.c_int (icaremp)
        self.m_model.m_eagme.BASME_MODVIS_ICAREMP_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varicaremp))

    @property
    def showCaseOnlyLoad (self) -> int:
        """Restringir ao caso (0)=todos.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        caricaso        = 0
        varcaricaso     = ctypes.c_int (caricaso)
        self.m_model.m_eagme.BASME_MODVIS_CARICASO_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcaricaso))
        caricaso        = varcaricaso.value
        return          caricaso

    @showCaseOnlyLoad.setter
    def showCaseOnlyLoad (self, caricaso: int) -> None:
        """Atribui Restringir ao caso (0)=todos."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcaricaso     = ctypes.c_int (caricaso)
        self.m_model.m_eagme.BASME_MODVIS_CARICASO_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcaricaso))

    @property
    def manualWindDistribution (self) -> int:
        """Distribuição manual de vento (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        carvendst       = 0
        varcarvendst    = ctypes.c_int (carvendst)
        self.m_model.m_eagme.BASME_MODVIS_CARVENDST_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varcarvendst))
        carvendst       = varcarvendst.value
        return          carvendst

    @manualWindDistribution.setter
    def manualWindDistribution (self, carvendst: int) -> None:
        """Atribui Distribuição manual de vento (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcarvendst    = ctypes.c_int (carvendst)
        self.m_model.m_eagme.BASME_MODVIS_CARVENDST_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varcarvendst))

    @property
    def manualWindPrefix (self) -> str:
        """Prefixo do caso de vento para distribuição manual (""=Todos).

        Returns:
            Cadeia de caracteres.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcarvenpref   = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_MODVIS_CARVENPREF_LER (ctypes.byref (varmodvis),
                            varcarvenpref)
        carvenpref      = varcarvenpref.value.decode(TQSUtil.CHARSET)
        return          carvenpref

    @manualWindPrefix.setter
    def manualWindPrefix (self, carvenpref: str) -> None:
        """Atribui Prefixo do caso de vento para distribuição manual (""=Todos)."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varcarvenpref   = ctypes.c_char_p (carvenpref.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_MODVIS_CARVENPREF_DEF (ctypes.byref (varmodvis),
                            varcarvenpref)

    @property
    def loadViewMode (self) -> int:
        """Mostrar cargas em (0) 2D (1) 3D (2) 2D e 3D.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        icargas3d       = 0
        varicargas3d    = ctypes.c_int (icargas3d)
        self.m_model.m_eagme.BASME_MODVIS_ICARGAS3D_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varicargas3d))
        icargas3d       = varicargas3d.value
        return          icargas3d

    @loadViewMode.setter
    def loadViewMode (self, icargas3d: int) -> None:
        """Atribui Mostrar cargas em (0) 2D (1) 3D (2) 2D e 3D."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varicargas3d    = ctypes.c_int (icargas3d)
        self.m_model.m_eagme.BASME_MODVIS_ICARGAS3D_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varicargas3d))

#
#       Modos de visualização de fundações
#
class VisModeFoundations ():

    """Modos de visualização de fundações.

    Implementação:
        Property bag de flags de visualização; cada propriedade lê/escreve um inteiro
        booleano via ``BASME_MODVIS_*`` no ``CModVis`` correspondente ao modo selecionado.
    """
    def __init__ (self, model: "Model", vismodes: int) -> None:
        """Modos de visualização de fundações.

        Args:
            model: Objeto Model() do modelo atual.
            vismodes: Apontador para objeto VisModes.
        """
        self.m_model    = model
        self.m_vismodes = vismodes

    @property
    def foundations (self) -> int:
        """Fundações (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        fundac          = 0
        varfundac       = ctypes.c_int (fundac)
        self.m_model.m_eagme.BASME_MODVIS_FUNDAC_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfundac))
        fundac          = varfundac.value
        return          fundac

    @foundations.setter
    def foundations (self, fundac: int) -> None:
        """Atribui Fundações (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfundac       = ctypes.c_int (fundac)
        self.m_model.m_eagme.BASME_MODVIS_FUNDAC_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfundac))

    @property
    def name (self) -> int:
        """Títulos de fundações (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        funtit          = 0
        varfuntit       = ctypes.c_int (funtit)
        self.m_model.m_eagme.BASME_MODVIS_FUNTIT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfuntit))
        funtit          = varfuntit.value
        return          funtit

    @name.setter
    def name (self, funtit: int) -> None:
        """Atribui Títulos de fundações (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfuntit       = ctypes.c_int (funtit)
        self.m_model.m_eagme.BASME_MODVIS_FUNTIT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfuntit))

    @property
    def dimensions (self) -> int:
        """Dimensões de fundações (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        fundim          = 0
        varfundim       = ctypes.c_int (fundim)
        self.m_model.m_eagme.BASME_MODVIS_FUNDIM_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfundim))
        fundim          = varfundim.value
        return          fundim

    @dimensions.setter
    def dimensions (self, fundim: int) -> None:
        """Atribui Dimensões de fundações (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfundim       = ctypes.c_int (fundim)
        self.m_model.m_eagme.BASME_MODVIS_FUNDIM_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfundim))

    @property
    def details (self) -> int:
        """Outros dados de detalhamento de fundações (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        fundad          = 0
        varfundad       = ctypes.c_int (fundad)
        self.m_model.m_eagme.BASME_MODVIS_FUNDAD_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfundad))
        fundad          = varfundad.value
        return          fundad

    @details.setter
    def details (self, fundad: int) -> None:
        """Atribui Outros dados de detalhamento de fundações (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfundad       = ctypes.c_int (fundad)
        self.m_model.m_eagme.BASME_MODVIS_FUNDAD_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfundad))

    @property
    def piles (self) -> int:
        """Estacas de blocos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        funestac        = 0
        varfunestac     = ctypes.c_int (funestac)
        self.m_model.m_eagme.BASME_MODVIS_FUNESTAC_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfunestac))
        funestac        = varfunestac.value
        return          funestac

    @piles.setter
    def piles (self, funestac: int) -> None:
        """Atribui Estacas de blocos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfunestac     = ctypes.c_int (funestac)
        self.m_model.m_eagme.BASME_MODVIS_FUNESTAC_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfunestac))

    @property
    def cutOffLevel (self) -> int:
        """Cotas de arrasamento (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        funcotarras     = 0
        varfuncotarras  = ctypes.c_int (funcotarras)
        self.m_model.m_eagme.BASME_MODVIS_FUNCOTARRAS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfuncotarras))
        funcotarras     = varfuncotarras.value
        return          funcotarras

    @cutOffLevel.setter
    def cutOffLevel (self, funcotarras: int) -> None:
        """Atribui Cotas de arrasamento (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfuncotarras  = ctypes.c_int (funcotarras)
        self.m_model.m_eagme.BASME_MODVIS_FUNCOTARRAS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfuncotarras))

    @property
    def pierDimension (self) -> int:
        """Dimensão da base do tubulão (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        funtitbasetub   = 0
        varfuntitbasetub= ctypes.c_int (funtitbasetub)
        self.m_model.m_eagme.BASME_MODVIS_FUNTITBASETUB_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfuntitbasetub))
        funtitbasetub   = varfuntitbasetub.value
        return          funtitbasetub

    @pierDimension.setter
    def pierDimension (self, funtitbasetub: int) -> None:
        """Atribui Dimensão da base do tubulão (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfuntitbasetub= ctypes.c_int (funtitbasetub)
        self.m_model.m_eagme.BASME_MODVIS_FUNTITBASETUB_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfuntitbasetub))

    @property
    def pileQuantity (self) -> int:
        """Quantidade e bitola de estacas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        funquantbit     = 0
        varfunquantbit  = ctypes.c_int (funquantbit)
        self.m_model.m_eagme.BASME_MODVIS_FUNQUANTBIT_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfunquantbit))
        funquantbit     = varfunquantbit.value
        return          funquantbit

    @pileQuantity.setter
    def pileQuantity (self, funquantbit: int) -> None:
        """Atribui Quantidade e bitola de estacas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfunquantbit  = ctypes.c_int (funquantbit)
        self.m_model.m_eagme.BASME_MODVIS_FUNQUANTBIT_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfunquantbit))

    @property
    def pileIdent (self) -> int:
        """Número da estaca (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        funestnum       = 0
        varfunestnum    = ctypes.c_int (funestnum)
        self.m_model.m_eagme.BASME_MODVIS_FUNESTNUM_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfunestnum))
        funestnum       = varfunestnum.value
        return          funestnum

    @pileIdent.setter
    def pileIdent (self, funestnum: int) -> None:
        """Atribui Número da estaca (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfunestnum    = ctypes.c_int (funestnum)
        self.m_model.m_eagme.BASME_MODVIS_FUNESTNUM_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfunestnum))

    @property
    def pileDimensions (self) -> int:
        """Diâmetro da estaca (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        funestdia       = 0
        varfunestdia    = ctypes.c_int (funestdia)
        self.m_model.m_eagme.BASME_MODVIS_FUNESTDIA_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varfunestdia))
        funestdia       = varfunestdia.value
        return          funestdia

    @pileDimensions.setter
    def pileDimensions (self, funestdia: int) -> None:
        """Atribui Diâmetro da estaca (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varfunestdia    = ctypes.c_int (funestdia)
        self.m_model.m_eagme.BASME_MODVIS_FUNESTDIA_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varfunestdia))

#
#       Modos de visualização de pré-moldados
#
class VisModePrecast ():

    """Modos de visualização de pré-moldados.

    Implementação:
        Property bag de flags de visualização; cada propriedade lê/escreve um inteiro
        booleano via ``BASME_MODVIS_*`` no ``CModVis`` correspondente ao modo selecionado.
    """
    def __init__ (self, model: "Model", vismodes: int) -> None:
        """Modos de visualização de pré-modados.

        Args:
            model: Objeto Model() do modelo atual.
            vismodes: Apontador para objeto VisModes.
        """
        self.m_model    = model
        self.m_vismodes = vismodes

    @property
    def constructionRegions (self) -> int:
        """Regiões pré-moldadas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        iregioes        = 0
        variregioes     = ctypes.c_int (iregioes)
        self.m_model.m_eagme.BASME_MODVIS_IREGIOES_LER (ctypes.byref (varmodvis),
                            ctypes.byref (variregioes))
        iregioes         = variregioes.value
        return          iregioes

    @constructionRegions.setter
    def constructionRegions (self, iregioes: int) -> None:
        """Atribui Regiões pré-moldadas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        variregioes     = ctypes.c_int (iregioes)
        self.m_model.m_eagme.BASME_MODVIS_IREGIOES_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (variregioes))

    @property
    def floorPlanGroups (self) -> int:
        """Título dos grupos de formas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        igrupopre       = 0
        varigrupopre    = ctypes.c_int (igrupopre)
        self.m_model.m_eagme.BASME_MODVIS_IGRUPOPRE_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varigrupopre))
        igrupopre       = varigrupopre.value
        return          igrupopre

    @floorPlanGroups.setter
    def floorPlanGroups (self, igrupopre: int) -> None:
        """Atribui Título dos grupos de formas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varigrupopre    = ctypes.c_int (igrupopre)
        self.m_model.m_eagme.BASME_MODVIS_IGRUPOPRE_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varigrupopre))

    @property
    def reinforcementGroups (self) -> int:
        """Título dos grupos de armação (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        igrupoarm       = 0
        varigrupoarm    = ctypes.c_int (igrupoarm)
        self.m_model.m_eagme.BASME_MODVIS_IGRUPOARM_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varigrupoarm))
        igrupoarm       = varigrupoarm.value
        return          igrupoarm

    @reinforcementGroups.setter
    def reinforcementGroups (self, igrupoarm: int) -> None:
        """Atribui Título dos grupos de armação (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varigrupoarm    = ctypes.c_int (igrupoarm)
        self.m_model.m_eagme.BASME_MODVIS_IGRUPOARM_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varigrupoarm))

    @property
    def corbelsName (self) -> int:
        """Título de consolos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ititcons        = 0
        varititcons     = ctypes.c_int (ititcons)
        self.m_model.m_eagme.BASME_MODVIS_ITITCONS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varititcons))
        ititcons        = varititcons.value
        return          ititcons

    @corbelsName.setter
    def corbelsName (self, ititcons: int) -> None:
        """Atribui Título de consolos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varititcons     = ctypes.c_int (ititcons)
        self.m_model.m_eagme.BASME_MODVIS_ITITCONS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varititcons))

    @property
    def corbels (self) -> int:
        """Consolos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        iconsolos       = 0
        variconsolos    = ctypes.c_int (iconsolos)
        self.m_model.m_eagme.BASME_MODVIS_ICONSOLOS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (variconsolos))
        iconsolos       = variconsolos.value
        return          iconsolos

    @corbels.setter
    def corbels (self, iconsolos: int) -> None:
        """Atribui Consolos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        variconsolos    = ctypes.c_int (iconsolos)
        self.m_model.m_eagme.BASME_MODVIS_ICONSOLOS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (variconsolos))

    @property
    def corbelsData (self) -> int:
        """Dados de consolos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        idadcons        = 0
        varidadcons     = ctypes.c_int (idadcons)
        self.m_model.m_eagme.BASME_MODVIS_IDADCONS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varidadcons))
        idadcons        = varidadcons.value
        return          idadcons

    @corbelsData.setter
    def corbelsData (self, idadcons: int) -> None:
        """Atribui Dados de consolos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varidadcons     = ctypes.c_int (idadcons)
        self.m_model.m_eagme.BASME_MODVIS_IDADCONS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varidadcons))

    @property
    def accessories (self) -> int:
        """Acessórios (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        iacessorios     = 0
        variacessorios  = ctypes.c_int (iacessorios)
        self.m_model.m_eagme.BASME_MODVIS_IACESSORIOS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (variacessorios))
        iacessorios     = variacessorios.value
        return          iacessorios

    @accessories.setter
    def accessories (self, iacessorios: int) -> None:
        """Atribui Acessórios (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        variacessorios  = ctypes.c_int (iacessorios)
        self.m_model.m_eagme.BASME_MODVIS_IACESSORIOS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (variacessorios))

    @property
    def slabsReport (self) -> int:
        """Resultados do cálculo de lajes pré-moldadas, se disponível (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ipreljpcalc     = 0
        varipreljpcalc  = ctypes.c_int (ipreljpcalc)
        self.m_model.m_eagme.BASME_MODVIS_IPRELJPCALC_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varipreljpcalc))
        ipreljpcalc     = varipreljpcalc.value
        return          ipreljpcalc

    @slabsReport.setter
    def slabsReport (self, ipreljpcalc: int) -> None:
        """Atribui Resultados do cálculo de lajes pré-moldadas, se disponível (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varipreljpcalc  = ctypes.c_int (ipreljpcalc)
        self.m_model.m_eagme.BASME_MODVIS_IPRELJPCALC_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varipreljpcalc))

    @property
    def showSlabsReport (self) -> int:
        """Mostrar o relatório após o cálculo de lajes pré-moldadas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ipreljprcalc    = 0
        varipreljprcalc = ctypes.c_int (ipreljprcalc)
        self.m_model.m_eagme.BASME_MODVIS_IPRELJPRCALC_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varipreljprcalc))
        ipreljprcalc    = varipreljprcalc.value
        return          ipreljprcalc

    @showSlabsReport.setter
    def showSlabsReport (self, ipreljprcalc: int) -> None:
        """Atribui Mostrar o relatório após o cálculo de lajes pré-moldadas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varipreljprcalc = ctypes.c_int (ipreljprcalc)
        self.m_model.m_eagme.BASME_MODVIS_IPRELJPRCALC_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varipreljprcalc))

    @property
    def beamsSectionTitle (self) -> int:
        """Título de seções catalogadas vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ipretitsecvig   = 0
        varipretitsecvig= ctypes.c_int (ipretitsecvig)
        self.m_model.m_eagme.BASME_MODVIS_IPRETITSECVIG_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varipretitsecvig))
        ipretitsecvig   = varipretitsecvig.value
        return          ipretitsecvig

    @beamsSectionTitle.setter
    def beamsSectionTitle (self, ipretitsecvig: int) -> None:
        """Atribui Título de seções catalogadas vigas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varipretitsecvig= ctypes.c_int (ipretitsecvig)
        self.m_model.m_eagme.BASME_MODVIS_IPRETITSECVIG_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varipretitsecvig))

    @property
    def sectionsLines (self) -> int:
        """Linhas de contorno das seções não padrão (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        iprelinsecnp    = 0
        variprelinsecnp = ctypes.c_int (iprelinsecnp)
        self.m_model.m_eagme.BASME_MODVIS_IPRELINSECNP_LER (ctypes.byref (varmodvis),
                            ctypes.byref (variprelinsecnp))
        iprelinsecnp    = variprelinsecnp.value
        return          iprelinsecnp

    @sectionsLines.setter
    def sectionsLines (self, iprelinsecnp: int) -> None:
        """Atribui Linhas de contorno das seções não padrão (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        variprelinsecnp = ctypes.c_int (iprelinsecnp)
        self.m_model.m_eagme.BASME_MODVIS_IPRELINSECNP_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (variprelinsecnp))

    @property
    def inserts (self) -> int:
        """Insertos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        insertos        = 0
        varinsertos     = ctypes.c_int (insertos)
        self.m_model.m_eagme.BASME_MODVIS_INSERTOS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varinsertos))
        insertos        = varinsertos.value
        return          insertos

    @inserts.setter
    def inserts (self, insertos: int) -> None:
        """Atribui Insertos (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varinsertos     = ctypes.c_int (insertos)
        self.m_model.m_eagme.BASME_MODVIS_INSERTOS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varinsertos))

    @property
    def facades (self) -> int:
        """Fachadas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        ifachadas       = 0
        varifachadas    = ctypes.c_int (ifachadas)
        self.m_model.m_eagme.BASME_MODVIS_IFACHADAS_LER (ctypes.byref (varmodvis),
                            ctypes.byref (varifachadas))
        ifachadas       = varifachadas.value
        return          ifachadas

    @facades.setter
    def facades (self, ifachadas: int) -> None:
        """Atribui Fachadas (0) Não (1) Sim."""
        varmodvis       = ctypes.c_void_p (self.m_vismodes.m_modvis)
        varifachadas    = ctypes.c_int (ifachadas)
        self.m_model.m_eagme.BASME_MODVIS_IFACHADAS_DEF (ctypes.byref (varmodvis),
                            ctypes.byref (varifachadas))

#------------------------------------------------------------------------------
#       Objeto de dados de escadas
#
class StairCase ():

    """Dados de escada.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", escdad: int) -> None:
        """Dados de escadas.

        Args:
            model: Objeto Model() do modelo atual.
            escdad: Apontador para objeto CEscDad.
        """
        self.m_model    = model
        self.m_escdad   = escdad

    @property
    def tread (self) -> float:
        """Passo cm.

        Returns:
            Valor de ponto flutuante.
        """
        varescdad       = ctypes.c_void_p (self.m_escdad)
        passo           = 0.
        varpasso        = ctypes.c_double (passo)
        self.m_model.m_eagme.BASME_ESCDAD_PASSO_LER (ctypes.byref (varescdad),
                            ctypes.byref (varpasso))
        passo           = varpasso.value
        return          passo

    @tread.setter
    def tread (self, passo: float) -> None:
        """Atribui Passo cm."""
        varescdad       = ctypes.c_void_p (self.m_escdad)
        varpasso        = ctypes.c_double (passo)
        self.m_model.m_eagme.BASME_ESCDAD_PASSO_DEF (ctypes.byref (varescdad),
                            ctypes.byref (varpasso))

    @property
    def riser (self) -> float:
        """Espelho cm.

        Returns:
            Valor de ponto flutuante.
        """
        varescdad       = ctypes.c_void_p (self.m_escdad)
        espelho         = 0.
        varespelho      = ctypes.c_double (espelho)
        self.m_model.m_eagme.BASME_ESCDAD_ESPELHO_LER (ctypes.byref (varescdad),
                            ctypes.byref (varespelho))
        espelho         = varespelho.value
        return          espelho

    @riser.setter
    def riser (self, espelho: float) -> None:
        """Atribui Espelho cm."""
        varescdad       = ctypes.c_void_p (self.m_escdad)
        varespelho      = ctypes.c_double (espelho)
        self.m_model.m_eagme.BASME_ESCDAD_ESPELHO_DEF (ctypes.byref (varescdad),
                            ctypes.byref (varespelho))

    @property
    def adjustment (self) -> float:
        """Ajuste inicial ou final cm conforme adjustmentMode.

        Returns:
            Valor de ponto flutuante.
        """
        varescdad       = ctypes.c_void_p (self.m_escdad)
        ajuste          = 0.
        varajuste       = ctypes.c_double (ajuste)
        self.m_model.m_eagme.BASME_ESCDAD_AJUSTE_LER (ctypes.byref (varescdad),
                            ctypes.byref (varajuste))
        ajuste          = varajuste.value
        return          ajuste

    @adjustment.setter
    def adjustment (self, ajuste: float) -> None:
        """Atribui Ajuste inicial ou final cm conforme adjustmentMode."""
        varescdad       = ctypes.c_void_p (self.m_escdad)
        varajuste       = ctypes.c_double (ajuste)
        self.m_model.m_eagme.BASME_ESCDAD_AJUSTE_DEF (ctypes.byref (varescdad),
                            ctypes.byref (varajuste))

    @property
    def adjustmentMode (self) -> int:
        """Ajuste (0) Inicial (1) Final.

        Returns:
            Valor inteiro.
        """
        varescdad       = ctypes.c_void_p (self.m_escdad)
        iajustefin      = 0
        variajustefin   = ctypes.c_int (iajustefin)
        self.m_model.m_eagme.BASME_ESCDAD_IAJUSTEFIN_LER (ctypes.byref (varescdad),
                            ctypes.byref (variajustefin))
        iajustefin      = variajustefin.value
        return          iajustefin

    @adjustmentMode.setter
    def adjustmentMode (self, iajustefin: int) -> None:
        """Atribui Ajuste (0) Inicial (1) Final."""
        varescdad       = ctypes.c_void_p (self.m_escdad)
        variajustefin   = ctypes.c_int (iajustefin)
        self.m_model.m_eagme.BASME_ESCDAD_IAJUSTEFIN_DEF (ctypes.byref (varescdad),
                            ctypes.byref (variajustefin))

    @property
    def fixedSteps (self) -> int:
        """Número de degraus fixos.

        Returns:
            Valor inteiro.
        """
        varescdad       = ctypes.c_void_p (self.m_escdad)
        ndegrausfixo    = 0
        varndegrausfixo = ctypes.c_int (ndegrausfixo)
        self.m_model.m_eagme.BASME_ESCDAD_NDEGRAUSFIXO_LER (ctypes.byref (varescdad),
                            ctypes.byref (varndegrausfixo))
        ndegrausfixo    = varndegrausfixo.value
        return          ndegrausfixo

    @fixedSteps.setter
    def fixedSteps (self, ndegrausfixo: int) -> None:
        """Atribui Número de degraus fixos."""
        varescdad       = ctypes.c_void_p (self.m_escdad)
        varndegrausfixo = ctypes.c_int (ndegrausfixo)
        self.m_model.m_eagme.BASME_ESCDAD_NDEGRAUSFIXO_DEF (ctypes.byref (varescdad),
                            ctypes.byref (varndegrausfixo))

    @property
    def winderStair (self) -> int:
        """Representar como escada plissada (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varescdad       = ctypes.c_void_p (self.m_escdad)
        iplissada       = 0
        variplissada    = ctypes.c_int (iplissada)
        self.m_model.m_eagme.BASME_ESCDAD_IPLISSADA_LER (ctypes.byref (varescdad),
                            ctypes.byref (variplissada))
        iplissada       = variplissada.value
        return          iplissada

    @winderStair.setter
    def winderStair (self, iplissada: int) -> None:
        """Atribui Representar como escada plissada (0) Não (1) Sim."""
        varescdad       = ctypes.c_void_p (self.m_escdad)
        variplissada    = ctypes.c_int (iplissada)
        self.m_model.m_eagme.BASME_ESCDAD_IPLISSADA_DEF (ctypes.byref (varescdad),
                            ctypes.byref (variplissada))
#------------------------------------------------------------------------------
#       Objeto de lajes somente de volume
#
class VolumeOnlySlab ():

    """Laje somente de volume.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", lajsovol: int) -> None:
        """Dados de laje somente de volume.

        Args:
            model: Objeto Model() do modelo atual.
            lajsovol: Apontador para objeto CLajSoVol.
        """
        self.m_model    = model
        self.m_lajsovol = lajsovol

    @property
    def insertionX (self) -> float:
        """Ponto de inserção X de laje retangular.

        Returns:
            Valor de ponto flutuante.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        xins            = 0.
        varxins         = ctypes.c_double (xins)
        self.m_model.m_eagme.BASME_LAJSOVOL_PTINSX_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varxins))
        xins            = varxins.value
        return          xins

    @insertionX.setter
    def insertionX (self, xins: float) -> None:
        """Atribui Ponto de inserção X de laje retangular."""
        varlajsovol       = ctypes.c_void_p (self.m_lajsovol)
        varxins                 = ctypes.c_double (xins)
        self.m_model.m_eagme.BASME_LAJSOVOL_PTINSX_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varxins))

    @property
    def insertionY (self) -> float:
        """Ponto de inserção Y de laje retangular.

        Returns:
            Valor de ponto flutuante.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        yins            = 0.
        varyins         = ctypes.c_double (yins)
        self.m_model.m_eagme.BASME_LAJSOVOL_PTINSY_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varyins))
        yins            = varyins.value
        return          yins

    @insertionY.setter
    def insertionY (self, yins: float) -> None:
        """Atribui Ponto de inserção Y de laje retangular."""
        varlajsovol       = ctypes.c_void_p (self.m_lajsovol)
        varyins                 = ctypes.c_double (yins)
        self.m_model.m_eagme.BASME_LAJSOVOL_PTINSY_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varyins))

    @property
    def fixedSpace (self) -> int:
        """Fixar comprimento da laje (0) Não  (1) Sim.

        Returns:
            Valor inteiro.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        ifixcompr       = 0
        varifixcompr    = ctypes.c_int (ifixcompr)
        self.m_model.m_eagme.BASME_LAJSOVOL_IFIXCOMPR_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varifixcompr))
        ifixcompr            = varifixcompr.value
        return          ifixcompr

    @fixedSpace.setter
    def fixedSpace (self, ifixcompr: int) -> None:
        """Atribui Fixar comprimento da laje (0) Não  (1) Sim."""
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        varifixcompr    = ctypes.c_int (ifixcompr)
        self.m_model.m_eagme.BASME_LAJSOVOL_IFIXCOMPR_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varifixcompr))

    @property
    def space (self) -> float:
        """Comprimento de laje retangular cm.

        Returns:
            Valor de ponto flutuante.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        compr           = 0.
        varcompr        = ctypes.c_double (compr)
        self.m_model.m_eagme.BASME_LAJSOVOL_COMPR_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varcompr))
        compr           = varcompr.value
        return          compr

    @space.setter
    def space (self, compr: float) -> None:
        """Atribui Comprimento de laje retangular cm."""
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        varcompr        = ctypes.c_double (compr)
        self.m_model.m_eagme.BASME_LAJSOVOL_COMPR_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varcompr))
    @property
    def fixedWidth (self) -> int:
        """Fixar largura da laje (0) Não  (1) Sim.

        Returns:
            Valor inteiro.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        ifixalarg       = 0
        varifixalarg    = ctypes.c_int (ifixalarg)
        self.m_model.m_eagme.BASME_LAJSOVOL_IFIXALARG_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varifixalarg))
        ifixalarg            = varifixalarg.value
        return          ifixalarg

    @fixedWidth.setter
    def fixedWidth (self, ifixalarg: int) -> None:
        """Atribui Fixar largura da laje (0) Não  (1) Sim."""
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        varifixalarg    = ctypes.c_int (ifixalarg)
        self.m_model.m_eagme.BASME_LAJSOVOL_IFIXALARG_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varifixalarg))

    @property
    def width (self) -> float:
        """Largura de laje retangular cm.

        Returns:
            Valor de ponto flutuante.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        alarg           = 0.
        varalarg        = ctypes.c_double (alarg)
        self.m_model.m_eagme.BASME_LAJSOVOL_ALARG_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varalarg))
        alarg           = varalarg.value
        return          alarg

    @width.setter
    def width (self, alarg: float) -> None:
        """Atribui Largura de laje retangular cm."""
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        varalarg        = ctypes.c_double (alarg)
        self.m_model.m_eagme.BASME_LAJSOVOL_ALARG_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varalarg))

    @property
    def fixedAngle (self) -> int:
        """Fixar ângulo da laje (0) Não  (1) Sim.

        Returns:
            Valor inteiro.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        ifixang         = 0
        varifixang      = ctypes.c_int (ifixang)
        self.m_model.m_eagme.BASME_LAJSOVOL_IFIXANG_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varifixang))
        ifixang            = varifixang.value
        return          ifixang

    @fixedAngle.setter
    def fixedAngle (self, ifixang: int) -> None:
        """Atribui Fixar ângulo da laje (0) Não  (1) Sim."""
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        varifixang      = ctypes.c_int (ifixang)
        self.m_model.m_eagme.BASME_LAJSOVOL_IFIXANG_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varifixang))
    @property
    def angle (self) -> float:
        """Direção da laje retangular em graus.

        Returns:
            Valor de ponto flutuante.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        ang             = 0.
        varang          = ctypes.c_double (ang)
        self.m_model.m_eagme.BASME_LAJSOVOL_ANG_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varang))
        ang             = varang.value
        return          ang

    @angle.setter
    def angle (self, ang: float) -> None:
        """Atribui Direção da laje retangular em graus."""
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        varang          = ctypes.c_double (ang)
        self.m_model.m_eagme.BASME_LAJSOVOL_ANG_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varang))

    @property
    def recess (self) -> float:
        """Rebaixo inicial em cm.

        Returns:
            Valor de ponto flutuante.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        dfs             = 0.
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_LAJSOVOL_DFS_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (vardfs))
        dfs             = vardfs.value
        return          dfs

    @recess.setter
    def recess (self, dfs: float) -> None:
        """Atribui Rebaixo inicial em cm."""
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_LAJSOVOL_DFS_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (vardfs))

    @property
    def zHeight (self) -> float:
        """Altura Z total em cm.

        Returns:
            Valor de ponto flutuante.
        """
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        alturaz         = 0.
        varalturaz      = ctypes.c_double (alturaz)
        self.m_model.m_eagme.BASME_LAJSOVOL_ALTURAZ_LER (ctypes.byref (varlajsovol),
                            ctypes.byref (varalturaz))
        alturaz         = varalturaz.value
        return          alturaz

    @zHeight.setter
    def zHeight (self, alturaz: float) -> None:
        """Atribui Altura Z total em cm."""
        varlajsovol     = ctypes.c_void_p (self.m_lajsovol)
        varalturaz      = ctypes.c_double (alturaz)
        self.m_model.m_eagme.BASME_LAJSOVOL_ALTURAZ_DEF (ctypes.byref (varlajsovol),
                            ctypes.byref (varalturaz))

#------------------------------------------------------------------------------
#       Objeto de estaca para laje radier CEstacRad
#
class SlabFoundationPile (SMObject):

    """Estaca de laje radier.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", estacrad: int) -> None:
        """Dados de estaca para laje radier.

        Args:
            model: Objeto Model() do modelo atual.
            estacrad: Apontador para objeto CEstacRad.
        """
        self.m_model    = model
        self.m_estacrad = estacrad
        super().__init__(model, self.m_estacrad)

#------------------------------------------------------------------------------
#       Objeto de furo em pilar CFuroPil
#
class ColumnOpening (SMObject):

    """Furo em pilar.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", furopil: int) -> None:
        """Dados de furo em pilar.

        Args:
            model: Objeto Model() do modelo atual.
            furopil: Apontador para objeto CFuroPil.
        """
        self.m_model    = model
        self.m_furopil  = furopil
        super().__init__(model, self.m_furopil)

#------------------------------------------------------------------------------
#       Dados de consolos CConsolo
#
class CorbelData ():

    """Dados de consolo.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", consolo: int) -> None:
        """Pré-moldados: Dados de consolos.

        Args:
            model: Objeto Model() do modelo atual.
            consolo: Apontador para objeto CConsolo.
        """
        self.m_model    = model
        self.m_consolo  = consolo
#------------------------------------------------------------------------------
#       Dados de fachada CFachada
#
class FacadeData (SMObject):

    """Dados de fachada de painel pré-moldado.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", fachada: int) -> None:
        """Pré-moldados: Dados de fachadas.

        Args:
            model: Objeto Model() do modelo atual.
            fachada: Apontador para objeto CFachada.
        """
        self.m_model    = model
        self.m_fachada  = fachada
        super().__init__(model, self.m_fachada)

#------------------------------------------------------------------------------
#       Dados globais para o BIM CGlbAtrib
#
class GlobalAttrib ():

    """Atributos BIM globais.

    Implementação:
        Itera atributos BIM globais por escopo (edifício, planta, piso). Os métodos
        ``ReadNext`` / ``ReadGroup`` percorrem o conjunto C++ enquanto ``SetGroup`` fixa
        o filtro de escopo antes da iteração.
    """
    def __init__ (self, model: "Model", glbatrib: int) -> None:
        """Dados globais para o BIM.

        Args:
            model: Objeto Model() do modelo atual.
            glbatrib: Apontador para objeto CGlbAtrib.
        """
        self.m_model    = model
        self.m_glbatrib = glbatrib

    def Clear (self) -> None:
        """Limpa atributos globais.
        """
        varglbatrib     = ctypes.c_void_p (self.m_glbatrib)
        self.m_model.m_eagme.BASME_GLBATRIB_LIMPAR (ctypes.byref (varglbatrib))

    def SetGroup (self, nomgrupo: str, iabrang: int, ielementos: int, ipiso: int, nompla: str) -> "UserAttrib":
        """Define novo grupo. Se já existir, acessa grupo existente.

        nomgrupo        Nome do grupo
        iabrang         Abrangência: BIM_GLBA_xxxx
        ielementos      Elementos definidos TYPE_xxxx (TYPE_INDEF=todos)
        ipiso           Piso para iabrang==BIM_GLBA_UMPISO
        nompla          Pavimento para  iabrang==BIM_GLBA_PLANTA

        ATENÇÃO: a biblioteca TQS codifica ``nompla`` mas não o repassa à
        chamada nativa. Grupos com ``iabrang == BIM_GLBA_PLANTA`` não ficam
        restritos à planta informada. Não escreva código que dependa desse
        filtro.

        Args:
            nomgrupo: Parâmetro ``nomgrupo``.
            iabrang: Parâmetro ``iabrang``.
            ielementos: Parâmetro ``ielementos``.
            ipiso: Parâmetro ``ipiso``.
            nompla: Aceito e codificado, mas ignorado pela biblioteca.

        Returns:
            objeto UserAttrib() de atributos do grupo.
        """
        varglbatrib     = ctypes.c_void_p (self.m_glbatrib)
        varnomgrupo     = ctypes.c_char_p (nomgrupo.encode (TQSUtil.CHARSET))
        variabrang      = ctypes.c_int (iabrang)
        varielementos   = ctypes.c_int (ielementos)
        varipiso        = ctypes.c_int (ipiso)
        varnompla       = ctypes.c_char_p (nompla.encode (TQSUtil.CHARSET))
        usratrib        = None
        varusratrib     = ctypes.c_void_p (usratrib)
        self.m_model.m_eagme.BASME_GLBATRIB_GRUPO_DEF (ctypes.byref (varglbatrib), \
                    varnomgrupo, ctypes.byref (variabrang), ctypes.byref (varielementos), \
                    ctypes.byref (varipiso), ctypes.byref (varusratrib))
        usratrib        = varusratrib.value
        userattrib      = UserAttrib (self.m_model, usratrib)
        return          userattrib

    def NumGroups (self) -> int:
        """Operação ``NumGroups``.

        Returns:
            Valor inteiro.
        """
        varglbatrib     = ctypes.c_void_p (self.m_glbatrib)
        numgrupos       = 0
        varnumgrupos    = ctypes.c_int (numgrupos)
        self.m_model.m_eagme.BASME_GLBATRIB_NUMGRUPOS_LER (ctypes.byref (varglbatrib), \
                        ctypes.byref (varnumgrupos))
        numgrupos       = varnumgrupos.value
        return          numgrupos

    def EraseGroup (self, nomgrupo: str) -> None:
        """Apaga atributo existente.

        Args:
            nomgrupo: Parâmetro ``nomgrupo``.
        """
        varglbatrib     = ctypes.c_void_p (self.m_glbatrib)
        varnomgrupo     = ctypes.c_char_p (nomgrupo.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GLBATRIB_GRUPO_APAGAR (ctypes.byref (varglbatrib), varnomgrupo)

    def ReadBegin (self) -> None:
        """Prepara para ler todos os atributos.
        """
        varglbatrib     = ctypes.c_void_p (self.m_glbatrib)
        self.m_model.m_eagme.BASME_GLBATRIB_PREPLER (ctypes.byref (varglbatrib))

    def ReadNext (self) -> Tuple[Any, int, int, int, Any, int]:
        """Lê próximo atributo.

        Returns:
            nomgrupo        Nome do grupo.
        """
        # Avança o iterador interno (precedido por ReadBegin) e devolve o atributo corrente; istat != 0 sinaliza fim
        varglbatrib     = ctypes.c_void_p (self.m_glbatrib)
        varnomgrupo     = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        iabrang         = BIM_GLBA_GLOBAL
        variabrang      = ctypes.c_int (iabrang)
        ielementos      = TYPE_INDEF
        varielementos   = ctypes.c_int (ielementos)
        ipiso           = 0
        varipiso        = ctypes.c_int (ipiso)
        varnompla       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        usratrib        = None
        varusratrib     = ctypes.c_void_p (usratrib)
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.BASME_GLBATRIB_LERPROX (ctypes.byref (varglbatrib),
                    varnomgrupo, ctypes.byref (variabrang), ctypes.byref (varielementos), \
                    ctypes.byref (varipiso), ctypes.byref (varusratrib), \
                    ctypes.byref (varistat))
        nomgrupo        = varnomgrupo.value.decode(TQSUtil.CHARSET)
        iabrang         = variabrang.value
        ielementos      = varielementos.value
        ipiso           = varipiso.value
        usratrib        = varusratrib.value
        userattrib      = UserAttrib (self.m_model, usratrib)
        istat           = varistat.value
        return          nomgrupo, iabrang, ielementos, ipiso, userattrib, istat

    def ReadGroup (self, nomgrupo: str) -> Tuple[int, int, int, Any, int]:
        """Lê atributos dado nome do grupo.

        nomgrupo        Nome do grupo

        Args:
            nomgrupo: Parâmetro ``nomgrupo``.

        Returns:
            iabrang         Abrangência: BIM_GLBA_xxxx.
        """
        varglbatrib     = ctypes.c_void_p (self.m_glbatrib)
        varnomgrupo     = ctypes.c_char_p (nomgrupo.encode (TQSUtil.CHARSET))
        iabrang         = BIM_GLBA_GLOBAL
        variabrang      = ctypes.c_int (iabrang)
        ielementos      = TYPE_INDEF
        varielementos   = ctypes.c_int (ielementos)
        ipiso           = 0
        varipiso        = ctypes.c_int (ipiso)
        varnompla       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        usratrib        = None
        varusratrib     = ctypes.c_void_p (usratrib)
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.BASME_GLBATRIB_GRUPO_LER (ctypes.byref (varglbatrib),
                    varnomgrupo, ctypes.byref (variabrang), ctypes.byref (varielementos), \
                    ctypes.byref (varipiso), ctypes.byref (varusratrib), \
                    ctypes.byref (varistat))
        iabrang         = variabrang.value
        ielementos      = varielementos.value
        ipiso           = varipiso.value
        usratrib        = varusratrib.value
        userattrib      = UserAttrib (self.m_model, usratrib)
        istat           = varistat.value
        return          iabrang, ielementos, ipiso, userattrib, istat

    def Sort (self) -> None:
        """Classifica grupos por nome.
        """
        varglbatrib     = ctypes.c_void_p (self.m_glbatrib)
        self.m_model.m_eagme.BASME_GLBATRIB_SORT (ctypes.byref (varglbatrib))

#------------------------------------------------------------------------------
#       Lista de plantas de pilares - CPlaPil
#
class ColumnFloorNames ():

    """Nomes de pavimentos nos pilares.

    Implementação:
        Itera nomes de pavimentos associados a um pilar. ``EnterFloor`` inicia a
        iteração e ``GetFloor`` lê o nome do pavimento corrente; usado quando o pilar
        atravessa múltiplos andares.
    """
    def __init__ (self, model: "Model", plapil: int) -> None:
        """Dados de usuário para o BIM.

        Args:
            model: Objeto Model() do modelo atual.
            plapil: Apontador para objeto CPlaPil.
        """
        self.m_model    = model
        self.m_plapil   = plapil

    @property
    def floorNumber (self) -> int:
        """Número de plantas.

        Returns:
            Valor inteiro.
        """
        varplapil       = ctypes.c_void_p (self.m_plapil)
        numplantas      = 0
        varnumplantas   = ctypes.c_int (numplantas)
        self.m_model.m_eagme.BASME_PLAPIL_NUMPLANTAS_LER (ctypes.byref (varplapil),
                            ctypes.byref (varnumplantas))
        numplantas      = varnumplantas.value
        return          numplantas

    def Clear (self) -> None:
        """Limpa a lista de plantas e cria duas vazias: a primeira e a última do edifício.
        """
        varplapil       = ctypes.c_void_p (self.m_plapil)
        self.m_model.m_eagme.BASME_PLAPIL_LIMPAR (ctypes.byref (varplapil))

    def EnterFloor (self, iplanta: int, nompla: str) -> None:
        """Entra uma planta em posição fixa e empurra as demais plantas.

        Args:
            iplanta: Parâmetro ``iplanta``.
            nompla: Nome da planta.
        """
        varplapil       = ctypes.c_void_p (self.m_plapil)
        variplanta      = ctypes.c_int (iplanta)
        varnompla       = ctypes.c_char_p (nompla.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_PLAPIL_ENTRAR_IPLANTA (ctypes.byref (varplapil),
                            ctypes.byref (variplanta), varnompla)

    def GetFloor (self, iplanta: int) -> str:
        """Lê uma planta do pilar.

        Args:
            iplanta: Parâmetro ``iplanta``.

        Returns:
            char *nompla        -> Nome da planta.
        """
        varplapil       = ctypes.c_void_p (self.m_plapil)
        variplanta      = ctypes.c_int (iplanta)
        varnompla       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_PLAPIL_PLANTA_LER (ctypes.byref (varplapil),
                            ctypes.byref (variplanta), varnompla)
        nompla          = varnompla.value.decode(TQSUtil.CHARSET)
        return         nompla
#------------------------------------------------------------------------------
#       Geometria de vigas - CGeoVig
#
class BeamGeometry ():

    """Geometria de viga.

    Implementação:
        Geometria de viga (``CGeoVig``). Property bag de dimensões e recessos; alguns
        setters aceitam multiplos tipos (string vs. enum) e fazem dispatch local.
    """
    def __init__ (self, model: "Model", geovig: int) -> None:
        """Geometria de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            geovig: Apontador para objeto CGeoVig.
        """
        self.m_model    = model
        self.m_geovig   = geovig

    @property
    def width (self) -> float:
        """Largura de viga retangular cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        bvig            = 0.
        varbvig         = ctypes.c_double (bvig)
        self.m_model.m_eagme.BASME_GEOVIG_B_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varbvig))
        bvig            = varbvig.value
        return          bvig

    @width.setter
    def width (self, bvig: float) -> None:
        """Atribui Largura de viga retangular cm."""
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        varbvig         = ctypes.c_double (bvig)
        self.m_model.m_eagme.BASME_GEOVIG_B_DEF (ctypes.byref (vargeovig),
                            ctypes.byref (varbvig))

    @property
    def depth (self) -> float:
        """Altura de viga retangular cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        hvig            = 0.
        varhvig         = ctypes.c_double (hvig)
        self.m_model.m_eagme.BASME_GEOVIG_H_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varhvig))
        hvig            = varhvig.value
        return          hvig

    @depth.setter
    def depth (self, hvig: float) -> None:
        """Atribui Altura de viga retangular cm."""
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        varhvig         = ctypes.c_double (hvig)
        self.m_model.m_eagme.BASME_GEOVIG_H_DEF (ctypes.byref (vargeovig),
                            ctypes.byref (varhvig))

    @property
    def eccentricity (self) -> float:
        """Excentricidade lateral cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        exc             = 0.
        varexc          = ctypes.c_double (exc)
        self.m_model.m_eagme.BASME_GEOVIG_EXC_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varexc))
        exc             = varexc.value
        return          exc

    @eccentricity.setter
    def eccentricity (self, exc: float) -> None:
        """Atribui Excentricidade lateral cm."""
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        varexc          = ctypes.c_double (exc)
        self.m_model.m_eagme.BASME_GEOVIG_EXC_DEF (ctypes.byref (vargeovig),
                            ctypes.byref (varexc))

    @property
    def recess (self) -> float:
        """Rebaixo em cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        dfs             = 0.
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_GEOVIG_DFS_LER (ctypes.byref (vargeovig),
                            ctypes.byref (vardfs))
        dfs             = vardfs.value
        return          dfs

    @recess.setter
    def recess (self, dfs: float) -> None:
        """Atribui Rebaixo em cm."""
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_GEOVIG_DFS_DEF (ctypes.byref (vargeovig),
                            ctypes.byref (vardfs))

    def GetFloorRecess (self, floor: "Floor", beam: "Beam") -> float:
        """Rebaixo em cm, considerando piso auxiliar.

        Args:
            floor: Objeto Floor, com dados de uma planta.
            beam: Objeto Beam que contém esta geometria.

        Returns:
            double dfspiso -> Rebaixo da viga, cm, considerando piso auxiliar.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varviga         = ctypes.c_void_p (beam.m_viga)
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        dfspiso         = 0.
        vardfspiso      = ctypes.c_double (dfspiso)
        self.m_model.m_eagme.BASME_GEOVIG_DFSPISO_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varviga), ctypes.byref (vargeovig),
                            ctypes.byref (vardfspiso))
        dfspiso         = vardfspiso.value
        return          dfspiso

    @property
    def sectionName (self) -> str:
        """Nome de seção não padrão - catalogada.

        Returns:
            Cadeia de caracteres.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        varsecaonp      = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GEOVIG_SECAONP_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varsecaonp))
        secaonp         = varsecaonp.value.decode(TQSUtil.CHARSET)
        return          secaonp

    @sectionName.setter
    def sectionName (self, secaonp: str) -> None:
        """Atribui Nome de seção não padrão - catalogada."""
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        varsecaonp      = ctypes.c_char_p (secaonp.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GEOVIG_SECAONP_DEF (ctypes.byref (vargeovig),
                            ctypes.byref (varsecaonp))
    @property
    def sectionRotation (self) -> float:
        """Ângulo de rotação da seção, graus.

        Returns:
            Valor de ponto flutuante.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        angsec             = 0.
        varangsec          = ctypes.c_double (angsec)
        self.m_model.m_eagme.BASME_GEOVIG_ANGSEC_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varangsec))
        angsec             = varangsec.value
        return          angsec

    @sectionRotation.setter
    def sectionRotation (self, angsec: float) -> None:
        """Atribui Ângulo de rotação da seção, graus."""
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        varangsec          = ctypes.c_double (angsec)
        self.m_model.m_eagme.BASME_GEOVIG_ANGSEC_DEF (ctypes.byref (vargeovig),
                            ctypes.byref (varangsec))

    @property
    def sectionMaterial (self) -> str:
        """Título do material diferente do concreto (não padrão).

        Returns:
            Cadeia de caracteres.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        varmaternp      = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GEOVIG_MATERNP_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varmaternp))
        maternp         = varmaternp.value.decode(TQSUtil.CHARSET)
        return          maternp

    @sectionMaterial.setter
    def sectionMaterial (self, maternp: str) -> None:
        """Atribui Título do material diferente do concreto (não padrão)."""
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        varmaternp      = ctypes.c_char_p (maternp.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GEOVIG_MATERNP_DEF (ctypes.byref (vargeovig),
                            ctypes.byref (varmaternp))

    @property
    def variableSection (self) -> "VariableSection":
        """Operação ``variableSection``.

        Returns:
            :class:`VariableSection` correspondente.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        misvig          = None
        varmisvig       = ctypes.c_void_p (misvig)
        self.m_model.m_eagme.BASME_GEOVIG_MISVIG_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varmisvig))
        misvig          = varmisvig.value
        variablesection = VariableSection (self.m_model, misvig)
        return          variablesection

    @property
    def precastRegion (self) -> int:
        """Pré-moldados: Região construtiva.

        Returns:
            Valor inteiro.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        iregiao         = 0
        variregiao      = ctypes.c_int (iregiao)
        self.m_model.m_eagme.BASME_GEOVIG_IREGIAO_LER (ctypes.byref (vargeovig),
                            ctypes.byref (variregiao))
        iregiao         = variregiao.value
        return          iregiao

    @precastRegion.setter
    def precastRegion (self, iregiao: int) -> None:
        """Atribui Pré-moldados: Região construtiva."""
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        variregiao      = ctypes.c_int (iregiao)
        self.m_model.m_eagme.BASME_GEOVIG_IREGIAO_DEF (ctypes.byref (vargeovig),
                            ctypes.byref (variregiao))

    @property
    def beamPrecastData (self) -> "BeamPrecastData":
        """Operação ``beamPrecastData``.

        Returns:
            :class:`BeamPrecastData` correspondente.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        previg          = None
        varprevig       = ctypes.c_void_p (previg)
        self.m_model.m_eagme.BASME_GEOVIG_PREVIG_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varprevig))
        previg          = varprevig.value
        beamprecastData = BeamPrecastData (self.m_model, previg)
        return          beamprecastData

    @property
    def beamMetalSection (self) -> "BeamMetalSection":
        """Operação ``beamMetalSection``.

        Returns:
            :class:`BeamMetalSection` correspondente.
        """
        vargeovig       = ctypes.c_void_p (self.m_geovig)
        metvig          = None
        varmetvig       = ctypes.c_void_p (metvig)
        self.m_model.m_eagme.BASME_GEOVIG_METVIG_LER (ctypes.byref (vargeovig),
                            ctypes.byref (varmetvig))
        metvig          = varmetvig.value
        beammetalsection= BeamMetalSection (self.m_model, metvig)
        return          beammetalsection

#------------------------------------------------------------------------------
#       Inércia de viga - CInerVig
#
class BeamInertia ():

    """Inércia de viga.

    Implementação:
        Inércia de viga (``CIneVig``). Property bag de coeficientes; ``_GetIndepDeLaje``
        / ``_SetIndepDeLaje`` controlam a flag de independência da rigidez da laje.
    """
    def __init__ (self, model: "Model", inervig: int) -> None:
        """Geometria de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            inervig: Apontador para objeto CInerVig.
        """
        self.m_model    = model
        self.m_inervig  = inervig


    @property
    def effectiveFlange (self) -> int:
        """Mesa colaborante (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        ibcolab         = 0
        varibcolab      = ctypes.c_int (ibcolab)
        self.m_model.m_eagme.BASME_INERVIG_IBCOLAB_LER (ctypes.byref (varinervig),
                            ctypes.byref (varibcolab))
        ibcolab         = varibcolab.value
        return          ibcolab

    @effectiveFlange.setter
    def effectiveFlange (self, ibcolab: int) -> None:
        """Atribui Mesa colaborante (0) Não (1) Sim."""
        varinervig      = ctypes.c_void_p (self.m_inervig)
        varibcolab      = ctypes.c_int (ibcolab)
        self.m_model.m_eagme.BASME_INERVIG_IBCOLAB_DEF (ctypes.byref (varinervig),
                            ctypes.byref (varibcolab))

    @property
    def maxEffectiveFlange (self) -> float:
        """Mesa colaborante máxima cm.

        Returns:
            Valor de ponto flutuante.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        bcolabmax       = 0.
        varbcolabmax    = ctypes.c_double (bcolabmax)
        self.m_model.m_eagme.BASME_INERVIG_BCOLABMAX_LER (ctypes.byref (varinervig),
                            ctypes.byref (varbcolabmax))
        bcolabmax       = varbcolabmax.value
        return          bcolabmax

    @maxEffectiveFlange.setter
    def maxEffectiveFlange (self, bcolabmax: float) -> None:
        """Atribui Mesa colaborante máxima cm."""
        varinervig      = ctypes.c_void_p (self.m_inervig)
        varbcolabmax    = ctypes.c_double (bcolabmax)
        self.m_model.m_eagme.BASME_INERVIG_BCOLABMAX_DEF (ctypes.byref (varinervig),
                            ctypes.byref (varbcolabmax))

    @property
    def fixedEffectiveFlange (self) -> float:
        """Mesa colaborante fixa cm.

        Returns:
            Valor de ponto flutuante.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        bcolabfix       = 0.
        varbcolabfix    = ctypes.c_double (bcolabfix)
        self.m_model.m_eagme.BASME_INERVIG_BCOLABFIX_LER (ctypes.byref (varinervig),
                            ctypes.byref (varbcolabfix))
        bcolabfix       = varbcolabfix.value
        return          bcolabfix

    @fixedEffectiveFlange.setter
    def fixedEffectiveFlange (self, bcolabfix: float) -> None:
        """Atribui Mesa colaborante fixa cm."""
        varinervig      = ctypes.c_void_p (self.m_inervig)
        varbcolabfix    = ctypes.c_double (bcolabfix)
        self.m_model.m_eagme.BASME_INERVIG_BCOLABFIX_DEF (ctypes.byref (varinervig),
                            ctypes.byref (varbcolabfix))

    @property
    def torsionalMomentMode (self) -> int:
        """Divisor de inércia à torção definido em (0) Critérios (1) torsionalMomentDivider ().

        Returns:
            Valor inteiro.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        itorcao         = 0
        varitorcao      = ctypes.c_int (itorcao)
        self.m_model.m_eagme.BASME_INERVIG_ITORCAO_LER (ctypes.byref (varinervig),
                            ctypes.byref (varitorcao))
        itorcao         = varitorcao.value
        return          itorcao

    @torsionalMomentMode.setter
    def torsionalMomentMode (self, itorcao: int) -> None:
        """Atribui Divisor de inércia à torção definido em (0) Critérios (1) torsionalMomentDivider ()."""
        varinervig      = ctypes.c_void_p (self.m_inervig)
        varitorcao      = ctypes.c_int (itorcao)
        self.m_model.m_eagme.BASME_INERVIG_ITORCAO_DEF (ctypes.byref (varinervig),
                            ctypes.byref (varitorcao))

    @property
    def torsionalMomentDivider (self) -> float:
        """Divisor de inércia à flexão, conforme torsionalMomentMode.

        Returns:
            Valor de ponto flutuante.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        divtor          = 0.
        vardivtor       = ctypes.c_double (divtor)
        self.m_model.m_eagme.BASME_INERVIG_DIVTOR_LER (ctypes.byref (varinervig),
                            ctypes.byref (vardivtor))
        divtor          = vardivtor.value
        return          divtor

    @torsionalMomentDivider.setter
    def torsionalMomentDivider (self, divtor: float) -> None:
        """Atribui Divisor de inércia à flexão, conforme torsionalMomentMode."""
        varinervig      = ctypes.c_void_p (self.m_inervig)
        vardivtor       = ctypes.c_double (divtor)
        self.m_model.m_eagme.BASME_INERVIG_DIVTOR_DEF (ctypes.byref (varinervig),
                            ctypes.byref (vardivtor))

    @property
    def inertiaMomentDivider (self) -> float:
        """Divisor de inércia à flexão, se (!=0).

        Returns:
            Valor de ponto flutuante.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        divflex         = 0.
        vardivflex      = ctypes.c_double (divflex)
        self.m_model.m_eagme.BASME_INERVIG_DIVFLEX_LER (ctypes.byref (varinervig),
                            ctypes.byref (vardivflex))
        divflex         = vardivflex.value
        return          divflex

    @inertiaMomentDivider.setter
    def inertiaMomentDivider (self, divflex: float) -> None:
        """Atribui Divisor de inércia à flexão, se (!=0)."""
        varinervig      = ctypes.c_void_p (self.m_inervig)
        vardivflex       = ctypes.c_double (divflex)
        self.m_model.m_eagme.BASME_INERVIG_DIVFLEX_DEF (ctypes.byref (varinervig),
                            ctypes.byref (vardivflex))

    def _GetIndepDeLaje (self, idir: int) -> int:
        """Retorna indep de laje.

        Args:
            idir: Parâmetro ``idir``.

        Returns:
            Valor inteiro.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        varidir         = ctypes.c_int (idir)
        inaoquebrlaj    = 0
        varinaoquebrlaj = ctypes.c_int (inaoquebrlaj)
        self.m_model.m_eagme.BASME_INERVIG_INTERLAJE_LER (ctypes.byref (varinervig),
                            ctypes.byref (varidir), ctypes.byref (varinaoquebrlaj))
        inaoquebrlaj    = varinaoquebrlaj.value
        return          inaoquebrlaj

    def _SetIndepDeLaje (self, idir: int, inaoquebrlaj: int) -> None:
        """Define indep de laje.

        Args:
            idir: Parâmetro ``idir``.
            inaoquebrlaj: Parâmetro ``inaoquebrlaj``.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        varidir         = ctypes.c_int (idir)
        varinaoquebrlaj = ctypes.c_int (inaoquebrlaj)
        self.m_model.m_eagme.BASME_INERVIG_INTERLAJE_DEF (ctypes.byref (varinervig),
                            ctypes.byref (varidir), ctypes.byref (varinaoquebrlaj))

    @property
    def notIntercectLeftSlab (self) -> Any:
        """Viga em relação à laje à esquerda (0) intercepta (1) não intercepta.

        Returns:
            Resultado da operação.
        """
        inaoquebrlaj    = self._GetIndepDeLaje (0)
        return          inaoquebrlaj

    @notIntercectLeftSlab.setter
    def notIntercectLeftSlab (self, inaoquebrlaj: int) -> None:
        """Atribui Viga em relação à laje à esquerda (0) intercepta (1) não intercepta."""
        self._SetIndepDeLaje (0, inaoquebrlaj)

    @property
    def notIntercectRightSlab (self) -> Any:
        """Viga em relação à laje à direita (0) intercepta (1) não intercepta.

        Returns:
            Resultado da operação.
        """
        inaoquebrlaj    = self._GetIndepDeLaje (1)
        return          inaoquebrlaj

    @notIntercectRightSlab.setter
    def notIntercectRightSlab (self, inaoquebrlaj: int) -> None:
        """Atribui Viga em relação à laje à direita (0) intercepta (1) não intercepta."""
        self._SetIndepDeLaje (1, inaoquebrlaj)

    @property
    def plasticAdaptability (self) -> int:
        """Capacidade de adaptação plástica à torção (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varinervig      = ctypes.c_void_p (self.m_inervig)
        icapplastor     = 0
        varicapplastor  = ctypes.c_int (icapplastor)
        self.m_model.m_eagme.BASME_INERVIG_ICAPLPASTTOR_LER (ctypes.byref (varinervig),
                            ctypes.byref (varicapplastor))
        icapplastor     = varicapplastor.value
        return          icapplastor

    @plasticAdaptability.setter
    def plasticAdaptability (self, icapplastor: int) -> None:
        """Atribui Capacidade de adaptação plástica à torção (0) Não (1) Sim."""
        varinervig      = ctypes.c_void_p (self.m_inervig)
        varicapplastor  = ctypes.c_int (icapplastor)
        self.m_model.m_eagme.BASME_INERVIG_ICAPLPASTTOR_DEF (ctypes.byref (varinervig),
                            ctypes.byref (varicapplastor))

#------------------------------------------------------------------------------
#       Vinculações e outros dados de viga - CVincVig
#
class BeamBond ():

    """Vinculação/articulação de viga.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", vincvig: int) -> None:
        """Geometria de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            vincvig: Apontador para objeto CVincVig.
        """
        self.m_model    = model
        self.m_vincvig  = vincvig

    @property
    def wideBeam (self) -> int:
        """Viga faixa (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        ivigafaixa      = 0
        varivigafaixa   = ctypes.c_int (ivigafaixa)
        self.m_model.m_eagme.BASME_VINCVIG_IVIGAFAIXA_LER (ctypes.byref (varvincvig),
                            ctypes.byref (varivigafaixa))
        ivigafaixa     = varivigafaixa.value
        return          ivigafaixa

    @wideBeam.setter
    def wideBeam (self, ivigafaixa: int) -> None:
        """Atribui Viga faixa (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        varivigafaixa   = ctypes.c_int (ivigafaixa)
        self.m_model.m_eagme.BASME_VINCVIG_IVIGAFAIXA_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (varivigafaixa))

    @property
    def fixAtTheBegin (self) -> int:
        """Engaste inicial (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        iengastini      = 0
        variengastini   = ctypes.c_int (iengastini)
        self.m_model.m_eagme.BASME_VINCVIG_IENGASTINI_LER (ctypes.byref (varvincvig),
                            ctypes.byref (variengastini))
        iengastini      = variengastini.value
        return          iengastini

    @fixAtTheBegin.setter
    def fixAtTheBegin (self, iengastini: int) -> None:
        """Atribui Engaste inicial (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        variengastini   = ctypes.c_int (iengastini)
        self.m_model.m_eagme.BASME_VINCVIG_IENGASTINI_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (variengastini))

    @property
    def fixAtTheEnd (self) -> int:
        """Engaste final (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        iengastfin      = 0
        variengastfin   = ctypes.c_int (iengastfin)
        self.m_model.m_eagme.BASME_VINCVIG_IENGASTFIN_LER (ctypes.byref (varvincvig),
                            ctypes.byref (variengastfin))
        iengastfin      = variengastfin.value
        return          iengastfin

    @fixAtTheEnd.setter
    def fixAtTheEnd (self, iengastfin: int) -> None:
        """Atribui Engaste final (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        variengastfin   = ctypes.c_int (iengastfin)
        self.m_model.m_eagme.BASME_VINCVIG_IENGASTFIN_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (variengastfin))

    @property
    def disableSelfWeight (self) -> int:
        """Desabilitar peso próprio (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        npp             = 0
        varnpp          = ctypes.c_int (npp)
        self.m_model.m_eagme.BASME_VINCVIG_NPP_LER (ctypes.byref (varvincvig),
                            ctypes.byref (varnpp))
        npp             = varnpp.value
        return          npp

    @disableSelfWeight.setter
    def disableSelfWeight (self, npp: int) -> None:
        """Atribui Desabilitar peso próprio (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        varnpp          = ctypes.c_int (npp)
        self.m_model.m_eagme.BASME_VINCVIG_NPP_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (varnpp))

    @property
    def bearColumnByTheFaces (self) -> int:
        """Intersececção de pilar com faces (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        iveriffaces     = 0
        variveriffaces  = ctypes.c_int (iveriffaces)
        self.m_model.m_eagme.BASME_VINCVIG_IVERIFFACES_LER (ctypes.byref (varvincvig),
                            ctypes.byref (variveriffaces))
        iveriffaces     = variveriffaces.value
        return          iveriffaces

    @bearColumnByTheFaces.setter
    def bearColumnByTheFaces (self, iveriffaces: int) -> None:
        """Atribui Intersececção de pilar com faces (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        variveriffaces  = ctypes.c_int (iveriffaces)
        self.m_model.m_eagme.BASME_VINCVIG_IVERIFFACES_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (variveriffaces))

    @property
    def adjustEdges (self) -> int:
        """Ajuste automático das pontas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        iajusteaut      = 0
        variajusteaut   = ctypes.c_int (iajusteaut)
        self.m_model.m_eagme.BASME_VINCVIG_IAJUSTEAUT_LER (ctypes.byref (varvincvig),
                            ctypes.byref (variajusteaut))
        iajusteaut      = variajusteaut.value
        return          iajusteaut

    @adjustEdges.setter
    def adjustEdges (self, iajusteaut: int) -> None:
        """Atribui Ajuste automático das pontas (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        variajusteaut   = ctypes.c_int (iajusteaut)
        self.m_model.m_eagme.BASME_VINCVIG_IAJUSTEAUT_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (variajusteaut))

    @property
    def interceptOthersBeams (self) -> int:
        """Intersececção com outras vigas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        intervigas      = 0
        varintervigas   = ctypes.c_int (intervigas)
        self.m_model.m_eagme.BASME_VINCVIG_INTERVIGAS_LER (ctypes.byref (varvincvig),
                            ctypes.byref (varintervigas))
        intervigas      = varintervigas.value
        return          intervigas

    @interceptOthersBeams.setter
    def interceptOthersBeams (self, intervigas: int) -> None:
        """Atribui Intersececção com outras vigas (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        varintervigas   = ctypes.c_int (intervigas)
        self.m_model.m_eagme.BASME_VINCVIG_INTERVIGAS_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (varintervigas))

    @property
    def startStrapBeam (self) -> int:
        """Alavanca inicial (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        ialavancaini    = 0
        varialavancaini = ctypes.c_int (ialavancaini)
        self.m_model.m_eagme.BASME_VINCVIG_IALAVANCAINI_LER (ctypes.byref (varvincvig),
                            ctypes.byref (varialavancaini))
        ialavancaini    = varialavancaini.value
        return          ialavancaini

    @startStrapBeam.setter
    def startStrapBeam (self, ialavancaini: int) -> None:
        """Atribui Alavanca inicial (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        varialavancaini = ctypes.c_int (ialavancaini)
        self.m_model.m_eagme.BASME_VINCVIG_IALAVANCAINI_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (varialavancaini))

    @property
    def endStrapBeam (self) -> int:
        """Alavanca final (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        ialavancafin    = 0
        varialavancafin = ctypes.c_int (ialavancafin)
        self.m_model.m_eagme.BASME_VINCVIG_IALAVANCAFIN_LER (ctypes.byref (varvincvig),
                            ctypes.byref (varialavancafin))
        ialavancafin    = varialavancafin.value
        return          ialavancafin

    @endStrapBeam.setter
    def endStrapBeam (self, ialavancafin: int) -> None:
        """Atribui Alavanca final (0) Não (1) Sim."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        varialavancafin = ctypes.c_int (ialavancafin)
        self.m_model.m_eagme.BASME_VINCVIG_IALAVANCAFIN_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (varialavancafin))

    @property
    def transferGirder (self) -> int:
        """Transição (0) pela geometria (1) Sim (2) Não.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        itransic        = 0
        varitransic     = ctypes.c_int (itransic)
        self.m_model.m_eagme.BASME_VINCVIG_ITRANSIC_LER (ctypes.byref (varvincvig),
                            ctypes.byref (varitransic))
        itransic        = varitransic.value
        return          itransic

    @transferGirder.setter
    def transferGirder (self, itransic: int) -> None:
        """Atribui Transição (0) pela geometria (1) Sim (2) Não."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        varitransic     = ctypes.c_int (itransic)
        self.m_model.m_eagme.BASME_VINCVIG_ITRANSIC_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (varitransic))

    @property
    def workAs (self) -> int:
        """Trabalha como (0) Viga (1) Tirante (2) Escora.

        Returns:
            Valor inteiro.
        """
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        itirante        = 0
        varitirante     = ctypes.c_int (itirante)
        self.m_model.m_eagme.BASME_VINCVIG_ITIRANTE_LER (ctypes.byref (varvincvig),
                            ctypes.byref (varitirante))
        itirante        = varitirante.value
        return          itirante

    @workAs.setter
    def workAs (self, itirante: int) -> None:
        """Atribui Trabalha como (0) Viga (1) Tirante (2) Escora."""
        varvincvig      = ctypes.c_void_p (self.m_vincvig)
        varitirante     = ctypes.c_int (itirante)
        self.m_model.m_eagme.BASME_VINCVIG_ITIRANTE_DEF (ctypes.byref (varvincvig),
                            ctypes.byref (varitirante))

#------------------------------------------------------------------------------
#       Dados de inserção de vigas - CInsVig
#
class BeamInsertion ():

    """Inserção de viga.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", insvig: int) -> None:
        """Geometria de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            insvig: Apontador para objeto CInsVig.
        """
        self.m_model    = model
        self.m_insvig  = insvig

    @property
    def insertBy (self) -> int:
        """Alinhamento (0) Esquerda (1) Direita (2) Eixo.

        Returns:
            Valor inteiro.
        """
        varinsvig       = ctypes.c_void_p (self.m_insvig)
        ialinvig        = 0
        varialinvig     = ctypes.c_int (ialinvig)
        self.m_model.m_eagme.BASME_INSVIG_IALINVIG_LER (ctypes.byref (varinsvig),
                            ctypes.byref (varialinvig))
        ialinvig        = varialinvig.value
        return          ialinvig

    @insertBy.setter
    def insertBy (self, ialinvig: int) -> None:
        """Atribui Alinhamento (0) Esquerda (1) Direita (2) Eixo."""
        varinsvig       = ctypes.c_void_p (self.m_insvig)
        varialinvig     = ctypes.c_int (ialinvig)
        self.m_model.m_eagme.BASME_INSVIG_IALINVIG_DEF (ctypes.byref (varinsvig),
                            ctypes.byref (varialinvig))

    @property
    def covering (self) -> float:
        """Revestimento das faces, cm.

        Returns:
            Valor de ponto flutuante.
        """
        varinsvig       = ctypes.c_void_p (self.m_insvig)
        revvig          = 0.
        varrevvig       = ctypes.c_double (revvig)
        self.m_model.m_eagme.BASME_INSVIG_REVVIG_LER (ctypes.byref (varinsvig),
                            ctypes.byref (varrevvig))
        revvig          = varrevvig.value
        return          revvig

    @covering.setter
    def covering (self, revvig: float) -> None:
        """Atribui Revestimento das faces, cm."""
        varinsvig       = ctypes.c_void_p (self.m_insvig)
        varrevvig       = ctypes.c_double (revvig)
        self.m_model.m_eagme.BASME_INSVIG_REVVIG_DEF (ctypes.byref (varinsvig),
                            ctypes.byref (varrevvig))

#------------------------------------------------------------------------------
#       Dados de Temperatura / retração - CTempRet
#
class TemperatureShrink ():

    """Carga de temperatura/retração.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", tempretvig: int) -> None:
        """Dados de Temperatura / retração de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            tempretvig: Apontador para objeto CTempRet.
        """
        self.m_model    = model
        self.m_tempretvig= tempretvig

    @property
    def temperatureDefined (self) -> int:
        """Definição de variação de temperatura ao longo da viga (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        itemperatura     = 0
        varitemperatura  = ctypes.c_int (itemperatura)
        self.m_model.m_eagme.BASME_TEMPRET_ITEMPERATURA_LER (ctypes.byref (vartempret),
                            ctypes.byref (varitemperatura))
        itemperatura     = varitemperatura.value
        return          itemperatura

    @temperatureDefined.setter
    def temperatureDefined (self, itemperatura: int) -> None:
        """Atribui Definição de variação de temperatura ao longo da viga (0) Não (1) Sim."""
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        varitemperatura  = ctypes.c_int (itemperatura)
        self.m_model.m_eagme.BASME_TEMPRET_ITEMPERATURA_DEF (ctypes.byref (vartempret),
                            ctypes.byref (varitemperatura))

    @property
    def uniformVariation (self) -> float:
        """Variação longitudinal de temperatura em graus Celcius.

        Returns:
            Valor de ponto flutuante.
        """
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        temvarlon       = 0.
        vartemvarlon    = ctypes.c_double (temvarlon)
        self.m_model.m_eagme.BASME_TEMPRET_TEMVARLON_LER (ctypes.byref (vartempret),
                            ctypes.byref (vartemvarlon))
        temvarlon       = vartemvarlon.value
        return          temvarlon

    @uniformVariation.setter
    def uniformVariation (self, temvarlon: float) -> None:
        """Atribui Variação longitudinal de temperatura em graus Celcius."""
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        vartemvarlon  = ctypes.c_double (temvarlon)
        self.m_model.m_eagme.BASME_TEMPRET_TEMVARLON_DEF (ctypes.byref (vartempret),
                            ctypes.byref (vartemvarlon))

    @property
    def uniformVariation2 (self) -> float:
        """Variação longitudinal de temperatura em graus Celcius - caso 2.

        Returns:
            Valor de ponto flutuante.
        """
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        temvarlon2      = 0.
        vartemvarlon2   = ctypes.c_double (temvarlon2)
        self.m_model.m_eagme.BASME_TEMPRET_TEMVARLON2_LER (ctypes.byref (vartempret),
                            ctypes.byref (vartemvarlon2))
        temvarlon2      = vartemvarlon2.value
        return          temvarlon2

    @uniformVariation2.setter
    def uniformVariation2 (self, temvarlon2: float) -> None:
        """Atribui Variação longitudinal de temperatura em graus Celcius - caso 2."""
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        vartemvarlon2   = ctypes.c_double (temvarlon2)
        self.m_model.m_eagme.BASME_TEMPRET_TEMVARLON2_DEF (ctypes.byref (vartempret),
                            ctypes.byref (vartemvarlon2))
    @property
    def transverseVariation (self) -> float:
        """Variação transversal de temperatura em graus Celcius.

        Returns:
            Valor de ponto flutuante.
        """
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        temvartra       = 0.
        vartemvartra    = ctypes.c_double (temvartra)
        self.m_model.m_eagme.BASME_TEMPRET_TEMVARTRA_LER (ctypes.byref (vartempret),
                            ctypes.byref (vartemvartra))
        temvartra       = vartemvartra.value
        return          temvartra

    @transverseVariation.setter
    def transverseVariation (self, temvartra: float) -> None:
        """Atribui Variação transversal de temperatura em graus Celcius."""
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        vartemvartra    = ctypes.c_double (temvartra)
        self.m_model.m_eagme.BASME_TEMPRET_TEMVARTRA_DEF (ctypes.byref (vartempret),
                            ctypes.byref (vartemvartra))

    @property
    def transverseVariation2 (self) -> float:
        """Variação transversal de temperatura em graus Celcius - caso 2.

        Returns:
            Valor de ponto flutuante.
        """
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        temvartra2      = 0.
        vartemvartra2   = ctypes.c_double (temvartra2)
        self.m_model.m_eagme.BASME_TEMPRET_TEMVARTRA2_LER (ctypes.byref (vartempret),
                            ctypes.byref (vartemvartra2))
        temvartra2      = vartemvartra2.value
        return          temvartra2

    @transverseVariation2.setter
    def transverseVariation2 (self, temvartra2: float) -> None:
        """Atribui Variação transversal de temperatura em graus Celcius - caso 2."""
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        vartemvartra2   = ctypes.c_double (temvartra2)
        self.m_model.m_eagme.BASME_TEMPRET_TEMVARTRA2_DEF (ctypes.byref (vartempret),
                            ctypes.byref (vartemvartra2))

    @property
    def shrinkageDefined (self) -> int:
        """Definição de retração ao longo da viga (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        iretracao       = 0
        variretracao    = ctypes.c_int (iretracao)
        self.m_model.m_eagme.BASME_TEMPRET_IRETRACAO_LER (ctypes.byref (vartempret),
                            ctypes.byref (variretracao))
        iretracao       = variretracao.value
        return          iretracao

    @shrinkageDefined.setter
    def shrinkageDefined (self, iretracao: int) -> None:
        """Atribui Definição de retração ao longo da viga (0) Não (1) Sim."""
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        variretracao    = ctypes.c_int (iretracao)
        self.m_model.m_eagme.BASME_TEMPRET_IRETRACAO_DEF (ctypes.byref (vartempret),
                            ctypes.byref (variretracao))

    @property
    def uniformShrinkage (self) -> float:
        """Variação longitudinal de temperatura equivalente à retração em graus Celcius.

        Returns:
            Valor de ponto flutuante.
        """
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        retvartemp      = 0.
        varretvartemp   = ctypes.c_double (retvartemp)
        self.m_model.m_eagme.BASME_TEMPRET_RETVARTEMP_LER (ctypes.byref (vartempret),
                            ctypes.byref (varretvartemp))
        retvartemp      = varretvartemp.value
        return          retvartemp

    @uniformShrinkage.setter
    def uniformShrinkage (self, retvartemp: float) -> None:
        """Atribui Variação longitudinal de temperatura equivalente à retração em graus Celcius."""
        vartempret      = ctypes.c_void_p (self.m_tempretvig)
        varretvartemp   = ctypes.c_double (retvartemp)
        self.m_model.m_eagme.BASME_TEMPRET_RETVARTEMP_DEF (ctypes.byref (vartempret),
                            ctypes.byref (varretvartemp))

#------------------------------------------------------------------------------
#       Detalhamento de vigas - CDetVig
#
class BeamDetailing ():

    """Detalhamento de viga.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", detvig: int) -> None:
        """Detalhamento de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            detvig: Apontador para objeto CDetVig.
        """
        self.m_model    = model
        self.m_detvig   = detvig

    @property
    def detailable (self) -> int:
        """Detalhamento da viga (0) Normal (1) Não (2) De compatibilização.

        Returns:
            Valor inteiro.
        """
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        idetvigas       = 0
        varidetvigas    = ctypes.c_int (idetvigas)
        self.m_model.m_eagme.BASME_DETVIG_IDETVIGAS_LER (ctypes.byref (vardetvig),
                            ctypes.byref (varidetvigas))
        idetvigas       = varidetvigas.value
        return          idetvigas

    @detailable.setter
    def detailable (self, idetvigas: int) -> None:
        """Atribui Detalhamento da viga (0) Normal (1) Não (2) De compatibilização."""
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        varidetvigas    = ctypes.c_int (idetvigas)
        self.m_model.m_eagme.BASME_DETVIG_IDETVIGAS_DEF (ctypes.byref (vardetvig),
                            ctypes.byref (varidetvigas))
    @property
    def cover (self) -> float:
        """Cobrimento em cm.

        Returns:
            Valor de ponto flutuante.
        """
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        cobrimento      = 0.
        varcobrimento   = ctypes.c_double (cobrimento)
        self.m_model.m_eagme.BASME_DETVIG_COBRIMENTO_LER (ctypes.byref (vardetvig),
                            ctypes.byref (varcobrimento))
        cobrimento      = varcobrimento.value
        return          cobrimento

    @cover.setter
    def cover (self, cobrimento: float) -> None:
        """Atribui Cobrimento em cm."""
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        varcobrimento   = ctypes.c_double (cobrimento)
        self.m_model.m_eagme.BASME_DETVIG_COBRIMENTO_DEF (ctypes.byref (vardetvig),
                            ctypes.byref (varcobrimento))

    @property
    def exposure (self) -> int:
        """Em contato com o solo (0) Não (1) Sim (2) Exposta ao ambiente.

        Returns:
            Valor inteiro.
        """
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        icontsolo       = 0
        varicontsolo    = ctypes.c_int (icontsolo)
        self.m_model.m_eagme.BASME_DETVIG_ICONTSOLO_LER (ctypes.byref (vardetvig),
                            ctypes.byref (varicontsolo))
        icontsolo       = varicontsolo.value
        return          icontsolo

    @exposure.setter
    def exposure (self, icontsolo: int) -> None:
        """Atribui Em contato com o solo (0) Não (1) Sim (2) Exposta ao ambiente."""
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        varicontsolo    = ctypes.c_int (icontsolo)
        self.m_model.m_eagme.BASME_DETVIG_ICONTSOLO_DEF (ctypes.byref (vardetvig),
                            ctypes.byref (varicontsolo))

    @property
    def restrainColumns (self) -> int:
        """A viga trava pilares (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        itravapil       = 0
        varitravapil    = ctypes.c_int (itravapil)
        self.m_model.m_eagme.BASME_DETVIG_ITRAVAPIL_LER (ctypes.byref (vardetvig),
                            ctypes.byref (varitravapil))
        itravapil       = varitravapil.value
        return          itravapil

    @restrainColumns.setter
    def restrainColumns (self, itravapil: int) -> None:
        """Atribui A viga trava pilares (0) Não (1) Sim."""
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        varitravapil    = ctypes.c_int (itravapil)
        self.m_model.m_eagme.BASME_DETVIG_ITRAVAPIL_DEF (ctypes.byref (vardetvig),
                            ctypes.byref (varitravapil))
    @property
    def simulatesCurtain (self) -> int:
        """Simula uma cortina (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        icortina        = 0
        varicortina     = ctypes.c_int (icortina)
        self.m_model.m_eagme.BASME_DETVIG_ICORTINA_LER (ctypes.byref (vardetvig),
                            ctypes.byref (varicortina))
        icortina        = varicortina.value
        return          icortina

    @simulatesCurtain.setter
    def simulatesCurtain (self, icortina: int) -> None:
        """Atribui Simula uma cortina (0) Não (1) Sim."""
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        varicortina     = ctypes.c_int (icortina)
        self.m_model.m_eagme.BASME_DETVIG_ICORTINA_DEF (ctypes.byref (vardetvig),
                            ctypes.byref (varicortina))
    @property
    def prestressed (self) -> int:
        """Protendida (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        iprotendida     = 0
        variprotendida  = ctypes.c_int (iprotendida)
        self.m_model.m_eagme.BASME_DETVIG_IPROTENDIDA_LER (ctypes.byref (vardetvig),
                            ctypes.byref (variprotendida))
        iprotendida     = variprotendida.value
        return          iprotendida

    @prestressed.setter
    def prestressed (self, iprotendida: int) -> None:
        """Atribui Protendida (0) Não (1) Sim."""
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        variprotendida  = ctypes.c_int (iprotendida)
        self.m_model.m_eagme.BASME_DETVIG_IPROTENDIDA_DEF (ctypes.byref (vardetvig),
                            ctypes.byref (variprotendida))
    @property
    def vproInterface (self) -> int:
        """Interface com o VPRO (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        intervpro       = 0
        varintervpro    = ctypes.c_int (intervpro)
        self.m_model.m_eagme.BASME_DETVIG_INTERVPRO_LER (ctypes.byref (vardetvig),
                            ctypes.byref (varintervpro))
        intervpro       = varintervpro.value
        return          intervpro

    @vproInterface.setter
    def vproInterface (self, intervpro: int) -> None:
        """Atribui Interface com o VPRO (0) Não (1) Sim."""
        vardetvig       = ctypes.c_void_p (self.m_detvig)
        varintervpro    = ctypes.c_int (intervpro)
        self.m_model.m_eagme.BASME_DETVIG_INTERVPRO_DEF (ctypes.byref (vardetvig),
                            ctypes.byref (varintervpro))

#------------------------------------------------------------------------------
#       Furo em viga - CFuroVig
#
class BeamOpening ():

    """Furo em viga.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", furovig: int) -> None:
        """Furo em viga.

        Args:
            model: Objeto Model() do modelo atual.
            furovig: Apontador para objeto CFuroVig.
        """
        self.m_model    = model
        self.m_furovig  = furovig

    @property
    def insertionX (self) -> float:
        """Ponto de inserção X cm (centro do furo, eixo da viga).

        Returns:
            Valor de ponto flutuante.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        xins            = 0.
        varxins         = ctypes.c_double (xins)
        self.m_model.m_eagme.BASME_FUROVIG_PTINSX_LER (ctypes.byref (varfurovig),
                            ctypes.byref (varxins))
        xins            = varxins.value
        return          xins

    @insertionX.setter
    def insertionX (self, xins: float) -> None:
        """Atribui Ponto de inserção X cm (centro do furo, eixo da viga)."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varxins         = ctypes.c_double (xins)
        self.m_model.m_eagme.BASME_FUROVIG_PTINSX_DEF (ctypes.byref (varfurovig),
                            ctypes.byref (varxins))
    @property
    def insertionY (self) -> float:
        """Ponto de inserção Y cm (centro do furo, eixo da viga).

        Returns:
            Valor de ponto flutuante.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        yins            = 0.
        varyins         = ctypes.c_double (yins)
        self.m_model.m_eagme.BASME_FUROVIG_PTINSY_LER (ctypes.byref (varfurovig),
                            ctypes.byref (varyins))
        yins            = varyins.value
        return          yins

    @insertionY.setter
    def insertionY (self, yins: float) -> None:
        """Atribui Ponto de inserção Y cm (centro do furo, eixo da viga)."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varyins         = ctypes.c_double (yins)
        self.m_model.m_eagme.BASME_FUROVIG_PTINSY_DEF (ctypes.byref (varfurovig),
                            ctypes.byref (varyins))

    @property
    def width (self) -> float:
        """Largura ou diâmetro em cm, visto em elevação.

        Returns:
            Valor de ponto flutuante.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        bfuro           = 0.
        varbfuro        = ctypes.c_double (bfuro)
        self.m_model.m_eagme.BASME_FUROVIG_B_LER (ctypes.byref (varfurovig),
                            ctypes.byref (varbfuro))
        bfuro           = varbfuro.value
        return          bfuro

    @width.setter
    def width (self, bfuro: float) -> None:
        """Atribui Largura ou diâmetro em cm, visto em elevação."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varbfuro        = ctypes.c_double (bfuro)
        self.m_model.m_eagme.BASME_FUROVIG_B_DEF (ctypes.byref (varfurovig),
                            ctypes.byref (varbfuro))

    @property
    def height (self) -> float:
        """Altura em cm, visto em elevação.

        Returns:
            Valor de ponto flutuante.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        hfuro           = 0.
        varhfuro        = ctypes.c_double (hfuro)
        self.m_model.m_eagme.BASME_FUROVIG_H_LER (ctypes.byref (varfurovig),
                            ctypes.byref (varhfuro))
        hfuro           = varhfuro.value
        return          hfuro

    @height.setter
    def height (self, hfuro: float) -> None:
        """Atribui Altura em cm, visto em elevação."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varhfuro        = ctypes.c_double (hfuro)
        self.m_model.m_eagme.BASME_FUROVIG_H_DEF (ctypes.byref (varfurovig),
                            ctypes.byref (varhfuro))

    @property
    def recess (self) -> float:
        """Rebaixo em relação à face da viga cm.

        Returns:
            Valor de ponto flutuante.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        dfs             = 0.
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_FUROVIG_DFS_LER (ctypes.byref (varfurovig),
                            ctypes.byref (vardfs))
        dfs             = vardfs.value
        return          dfs

    @recess.setter
    def recess (self, dfs: float) -> None:
        """Atribui Rebaixo em relação à face da viga cm."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_FUROVIG_DFS_DEF (ctypes.byref (varfurovig),
                            ctypes.byref (vardfs))

    @property
    def format (self) -> int:
        """Formato do furo (0) Retangular (1) Circular.

        Returns:
            Valor inteiro.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        ifurocirc       = 0
        varifurocirc    = ctypes.c_int (ifurocirc)
        self.m_model.m_eagme.BASME_FUROVIG_IFUROCIRC_LER (ctypes.byref (varfurovig),
                            ctypes.byref (varifurocirc))
        ifurocirc       = varifurocirc.value
        return          ifurocirc

    @format.setter
    def format (self, ifurocirc: int) -> None:
        """Atribui Formato do furo (0) Retangular (1) Circular."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varifurocirc    = ctypes.c_int (ifurocirc)
        self.m_model.m_eagme.BASME_FUROVIG_IFUROCIRC_DEF (ctypes.byref (varfurovig),
                            ctypes.byref (varifurocirc))

    @property
    def reference (self) -> int:
        """Referência do rebaixo BEAMOPENINGREFERENCE_xxxx.

        Returns:
            Valor inteiro.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        ireferencia     = 0
        varireferencia  = ctypes.c_int (ireferencia)
        self.m_model.m_eagme.BASME_FUROVIG_IREFERENCIA_LER (ctypes.byref (varfurovig),
                            ctypes.byref (varireferencia))
        ireferencia     = varireferencia.value
        return          ireferencia

    @reference.setter
    def reference (self, ireferencia: int) -> None:
        """Atribui Referência do rebaixo BEAMOPENINGREFERENCE_xxxx."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varireferencia  = ctypes.c_int (ireferencia)
        self.m_model.m_eagme.BASME_FUROVIG_IREFERENCIA_DEF (ctypes.byref (varfurovig),
                            ctypes.byref (varireferencia))

    @property
    def identification (self) -> str:
        """Identificação opcional.

        Returns:
            Cadeia de caracteres.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varident        = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_FUROVIG_IDENT_LER (ctypes.byref (varfurovig),
                            varident)
        ident           = varident.value.decode(TQSUtil.CHARSET)
        return          ident

    @identification.setter
    def identification (self, ident: str) -> None:
        """Atribui Identificação opcional."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varident        = ctypes.c_char_p (ident.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_FUROVIG_IDENT_DEF (ctypes.byref (varfurovig),
                            varident)

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_FUROVIG_IPISOAUX_LER (ctypes.byref (varfurovig),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varfurovig      = ctypes.c_void_p (self.m_furovig)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_FUROVIG_IPISOAUX_DEF (ctypes.byref (varfurovig),
                            ctypes.byref (varipisoaux))
#------------------------------------------------------------------------------
#        Dados de geometria de laje - CGeoLaj
#
class SlabGeometry ():

    """Geometria de laje.

    Implementação:
        Wrapper grande para a geometria de laje (``CGeoLaje``). Exposições incluem
        espessura, recessos por pavimento, peso próprio e tamanho médio; alguns
        métodos calculam derivados (``_GetAverageSize``).
    """
    def __init__ (self, model: "Model", geolaj: int) -> None:
        """Dados de geometria de laje.

        Args:
            model: Objeto Model() do modelo atual.
            geolaj: Apontador para objeto CGeoLaj.
        """
        self.m_model    = model
        self.m_geolaj   = geolaj

    @property
    def type (self) -> int:
        """Tipo de laje SLABTYPE_xxxxx.

        Returns:
            Valor inteiro.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        itipo           = 0
        varitipo        = ctypes.c_int (itipo)
        self.m_model.m_eagme.BASME_GEOLAJ_ITIPO_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varitipo))
        itipo         = varitipo.value
        return          itipo

    @type.setter
    def type (self, itipo: int) -> None:
        """Atribui Tipo de laje SLABTYPE_xxxxx."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varitipo        = ctypes.c_int (itipo)
        self.m_model.m_eagme.BASME_GEOLAJ_ITIPO_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varitipo))

    @property
    def noSelfWeight (self) -> int:
        """Desconsiderar peso proprio (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        npp             = 0
        varnpp          = ctypes.c_int (npp)
        self.m_model.m_eagme.BASME_GEOLAJ_NPP_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varnpp))
        npp             = varnpp.value
        return          npp

    @noSelfWeight.setter
    def noSelfWeight (self, npp: int) -> None:
        """Atribui Desconsiderar peso proprio (0) Não (1) Sim."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varnpp          = ctypes.c_int (npp)
        self.m_model.m_eagme.BASME_GEOLAJ_NPP_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varnpp))

    def GetSelfWeightLoad (self, floor: "Floor") -> "Load":
        """floor.

        Args:
            floor: Objeto Floor, com dados de uma planta.

        Returns:
            floor       <- Objeto Floor, com dados de uma planta.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        cargapp         = None
        varcargapp      = ctypes.c_void_p (cargapp)
        self.m_model.m_eagme.BASME_GEOLAJ_CARGAPP_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varcargapp))
        cargapp         = varcargapp.value
        load            = Load (self.m_model, floor, cargapp)
        return          load

    @property
    def thickness (self) -> float:
        """Altura da laje maciça em cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        hlaj            = 0.
        varhlaj         = ctypes.c_double (hlaj)
        self.m_model.m_eagme.BASME_GEOLAJ_H_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varhlaj))
        hlaj            = varhlaj.value
        return          hlaj

    @thickness.setter
    def thickness (self, hlaj: float) -> None:
        """Atribui Altura da laje maciça em cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varhlaj         = ctypes.c_double (hlaj)
        self.m_model.m_eagme.BASME_GEOLAJ_H_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varhlaj))

    @property
    def recess (self) -> float:
        """Rebaixo em cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        dfslaj          = 0.
        vardfslaj       = ctypes.c_double (dfslaj)
        self.m_model.m_eagme.BASME_GEOLAJ_DFS_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (vardfslaj))
        dfslaj          = vardfslaj.value
        return          dfslaj

    @recess.setter
    def recess (self, dfslaj: float) -> None:
        """Atribui Rebaixo em cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        vardfslaj       = ctypes.c_double (dfslaj)
        self.m_model.m_eagme.BASME_GEOLAJ_DFS_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (vardfslaj))

    def GetFloorRecess (self, floor: "Floor", slab: "Slab") -> float:
        """Rebaixo em cm, considerando piso auxiliar.

        Args:
            floor: Objeto Floor, com dados de uma planta.
            slab: Objeto Slab que contém esta geometria.

        Returns:
            double dfspiso -> Rebaixo da laje, cm, considerando piso auxiliar.
        """
        varfabrica      = ctypes.c_void_p (floor.m_fabrica)
        varlaje         = ctypes.c_void_p (slab.m_laje)
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        dfspiso         = 0.
        vardfspiso      = ctypes.c_double (dfspiso)
        self.m_model.m_eagme.BASME_GEOLAJ_DFSPISO_LER (ctypes.byref (varfabrica),
                            ctypes.byref (varlaje), ctypes.byref (vargeolaj),
                            ctypes.byref (vardfspiso))
        dfspiso         = vardfspiso.value
        return          dfspiso

    @property
    def additionalTopRecess (self) -> float:
        """Rebaixo adicional superior em cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        dfssupadi       = 0.
        vardfssupadi    = ctypes.c_double (dfssupadi)
        self.m_model.m_eagme.BASME_GEOLAJ_DFSSUPADI_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (vardfssupadi))
        dfssupadi       = vardfssupadi.value
        return          dfssupadi

    @additionalTopRecess.setter
    def additionalTopRecess (self, dfssupadi: float) -> None:
        """Atribui Rebaixo adicional superior em cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        vardfssupadi    = ctypes.c_double (dfssupadi)
        self.m_model.m_eagme.BASME_GEOLAJ_DFSSUPADI_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (vardfssupadi))

    @property
    def additionalBottomRecess (self) -> float:
        """Rebaixo adicional inferior em cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        dfsinfadi       = 0.
        vardfsinfadi    = ctypes.c_double (dfsinfadi)
        self.m_model.m_eagme.BASME_GEOLAJ_DFSINFADI_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (vardfsinfadi))
        dfsinfadi       = vardfsinfadi.value
        return          dfsinfadi

    @additionalBottomRecess.setter
    def additionalBottomRecess (self, dfsinfadi: float) -> None:
        """Atribui Rebaixo adicional inferior em cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        vardfsinfadi    = ctypes.c_double (dfsinfadi)
        self.m_model.m_eagme.BASME_GEOLAJ_DFSINFADI_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (vardfsinfadi))

    @property
    def ribbedTopping (self) -> float:
        """Laje nervurada: capa, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        capa            = 0.
        varcapa         = ctypes.c_double (capa)
        self.m_model.m_eagme.BASME_GEOLAJ_CAPA_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varcapa))
        capa            = varcapa.value
        return          capa

    @ribbedTopping.setter
    def ribbedTopping (self, capa: float) -> None:
        """Atribui capa, cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varcapa         = ctypes.c_double (capa)
        self.m_model.m_eagme.BASME_GEOLAJ_CAPA_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varcapa))

    @property
    def ribbedBottomTopping (self) -> float:
        """Laje nervurada: capa inferior, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        capainf         = 0.
        varcapainf      = ctypes.c_double (capainf)
        self.m_model.m_eagme.BASME_GEOLAJ_CAPAINF_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varcapainf))
        capainf         = varcapainf.value
        return          capainf

    @ribbedBottomTopping.setter
    def ribbedBottomTopping (self, capainf: float) -> None:
        """Atribui capa inferior, cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varcapainf      = ctypes.c_double (capainf)
        self.m_model.m_eagme.BASME_GEOLAJ_CAPAINF_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varcapainf))

    @property
    def ribHeight (self) -> float:
        """Laje nervurada: altura de nervura cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        hner            = 0.
        varhner         = ctypes.c_double (hner)
        self.m_model.m_eagme.BASME_GEOLAJ_HNER_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varhner))
        hner            = varhner.value
        return          hner

    @ribHeight.setter
    def ribHeight (self, hner: float) -> None:
        """Atribui altura de nervura cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varhner         = ctypes.c_double (hner)
        self.m_model.m_eagme.BASME_GEOLAJ_HNER_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varhner))

    @property
    def ribbedFill (self) -> float:
        """Laje nervurada: peso de enchimento tf/m3.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        ench            = 0.
        varench         = ctypes.c_double (ench)
        self.m_model.m_eagme.BASME_GEOLAJ_ENCH_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varench))
        ench            = varench.value
        return          ench

    @ribbedFill.setter
    def ribbedFill (self, ench: float) -> None:
        """Atribui peso de enchimento tf/m3."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varench         = ctypes.c_double (ench)
        self.m_model.m_eagme.BASME_GEOLAJ_ENCH_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varench))

    def _GetAverageSize (self, idir: int) -> float:
        """Retorna average size.

        Args:
            idir: Parâmetro ``idir``.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidir         = ctypes.c_int (idir)
        dnerv           = 0.
        vardnerv        = ctypes.c_double (dnerv)
        self.m_model.m_eagme.BASME_GEOLAJ_NERV_DNERV_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varidir), ctypes.byref (vardnerv))
        dnerv           = vardnerv.value
        return          dnerv

    def _SetAverageSize (self, idir: int, dnerv: float) -> None:
        """Define average size.

        Args:
            idir: Parâmetro ``idir``.
            dnerv: Parâmetro ``dnerv``.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidir         = ctypes.c_int (idir)
        vardnerv        = ctypes.c_double (dnerv)
        self.m_model.m_eagme.BASME_GEOLAJ_NERV_DNERV_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varidir), ctypes.byref (vardnerv))

    @property
    def averageSizeX (self) -> Any:
        """Laje nervurada: distância média horizontal entre nervuras cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetAverageSize (0)

    @averageSizeX.setter
    def averageSizeX (self, dnerv: Any) -> None:
        """Atribui distância média horizontal entre nervuras cm."""
        self._SetAverageSize (0, dnerv)

    @property
    def averageSizeY (self) -> Any:
        """Laje nervurada: distância média vertical entre nervuras cm.

        ATENÇÃO: na biblioteca TQS o setter abaixo é decorado com
        ``@averageSizeX.setter``, o que substitui esta propriedade por uma
        combinação do getter de ``averageSizeX`` com o setter de Y. Na prática:
        LER ``averageSizeY`` devolve a distância X (valor errado); ESCREVER
        ``averageSizeY`` grava corretamente em Y. Para ler a distância Y use o
        acesso direto do wrapper em vez desta propriedade.

        Returns:
            Resultado da operação (na prática, a distância X — ver ATENÇÃO).
        """
        return          self._GetAverageSize (1)

    @averageSizeX.setter
    def averageSizeY (self, dnerv: Any) -> None:
        """Atribui distância média vertical (Y) entre nervuras cm.

        ATENÇÃO: ver a nota no getter — este setter grava em Y corretamente,
        mas o decorador ``@averageSizeX.setter`` faz a leitura de
        ``averageSizeY`` devolver X.
        """
        self._SetAverageSize (1, dnerv)


    def _GetTopSpacing (self, idir: int) -> float:
        """Retorna top spacing.

        Args:
            idir: Parâmetro ``idir``.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidir         = ctypes.c_int (idir)
        bnervsup           = 0.
        varbnervsup        = ctypes.c_double (bnervsup)
        self.m_model.m_eagme.BASME_GEOLAJ_NERV_BNERVSUP_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varidir), ctypes.byref (varbnervsup))
        bnervsup           = varbnervsup.value
        return          bnervsup

    def _SetTopSpacing (self, idir: int, bnervsup: float) -> None:
        """Define top spacing.

        Args:
            idir: Parâmetro ``idir``.
            bnervsup: Parâmetro ``bnervsup``.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidir         = ctypes.c_int (idir)
        varbnervsup        = ctypes.c_double (bnervsup)
        self.m_model.m_eagme.BASME_GEOLAJ_NERV_BNERVSUP_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varidir), ctypes.byref (varbnervsup))

    @property
    def topSpacingX (self) -> Any:
        """Laje nervurada: largura superior de nervura horizontal cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetTopSpacing (0)

    @topSpacingX.setter
    def topSpacingX (self, bnervsup: Any) -> None:
        """Atribui largura superior de nervura horizontal cm."""
        self._SetTopSpacing (0, bnervsup)

    @property
    def topSpacingY (self) -> Any:
        """Laje nervurada: largura superior de nervura vertical cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetTopSpacing (1)

    @topSpacingY.setter
    def topSpacingY (self, bnervsup: Any) -> None:
        """Atribui largura superior de nervura vertical cm."""
        self._SetTopSpacing (1, bnervsup)

    def _GetBottomSpacing (self, idir: int) -> float:
        """Retorna bottom spacing.

        Args:
            idir: Parâmetro ``idir``.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidir         = ctypes.c_int (idir)
        bnervinf           = 0.
        varbnervinf        = ctypes.c_double (bnervinf)
        self.m_model.m_eagme.BASME_GEOLAJ_NERV_BNERVINF_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varidir), ctypes.byref (varbnervinf))
        bnervinf           = varbnervinf.value
        return          bnervinf

    def _SetBottomSpacing (self, idir: int, bnervinf: float) -> None:
        """Define bottom spacing.

        Args:
            idir: Parâmetro ``idir``.
            bnervinf: Parâmetro ``bnervinf``.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidir         = ctypes.c_int (idir)
        varbnervinf        = ctypes.c_double (bnervinf)
        self.m_model.m_eagme.BASME_GEOLAJ_NERV_BNERVINF_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varidir), ctypes.byref (varbnervinf))

    @property
    def bottomSpacingX (self) -> Any:
        """Laje nervurada: largura inferior de nervura horizontal cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetBottomSpacing (0)

    @bottomSpacingX.setter
    def bottomSpacingX (self, bnervinf: Any) -> None:
        """Atribui largura inferior de nervura horizontal cm."""
        self._SetBottomSpacing (0, bnervinf)

    @property
    def bottomSpacingY (self) -> Any:
        """Laje nervurada: largura inferior de nervura vertical cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetBottomSpacing (1)

    @bottomSpacingY.setter
    def bottomSpacingY (self, bnervinf: Any) -> None:
        """Atribui largura inferior de nervura vertical cm."""
        self._SetBottomSpacing (1, bnervinf)

    def _GetInertia (self, idir: int) -> float:
        """Retorna inertia.

        Args:
            idir: Parâmetro ``idir``.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidir         = ctypes.c_int (idir)
        ailaje          = 0.
        varailaje       = ctypes.c_double (ailaje)
        self.m_model.m_eagme.BASME_GEOLAJ_NERV_AILAJE_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varidir), ctypes.byref (varailaje))
        ailaje          = varailaje.value
        return          ailaje

    def _SetInertia (self, idir: int, ailaje: float) -> None:
        """Define inertia.

        Args:
            idir: Parâmetro ``idir``.
            ailaje: Parâmetro ``ailaje``.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidir         = ctypes.c_int (idir)
        varailaje       = ctypes.c_double (ailaje)
        self.m_model.m_eagme.BASME_GEOLAJ_NERV_AILAJE_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varidir), ctypes.byref (varailaje))

    @property
    def inertiaX (self) -> Any:
        """Laje nervurada: inércia opcional horizontal cm4.

        Returns:
            Resultado da operação.
        """
        return          self._GetInertia (0)

    @inertiaX.setter
    def inertiaX (self, ailaje: Any) -> None:
        """Atribui inércia opcional horizontal cm4."""
        self._SetInertia (0, ailaje)

    @property
    def inertiaY (self) -> Any:
        """Laje nervurada: inércia opcional vertical cm4.

        Returns:
            Resultado da operação.
        """
        return          self._GetInertia (1)

    @inertiaY.setter
    def inertiaY (self, ailaje: Any) -> None:
        """Atribui inércia opcional vertical cm4."""
        self._SetInertia (1, ailaje)

    @property
    def formworkVolume (self) -> float:
        """Laje nervurada: volume cubeta trapezoidal cm3.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        volforner       = 0.
        varvolforner    = ctypes.c_double (volforner)
        self.m_model.m_eagme.BASME_GEOLAJ_VOLFORNER_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varvolforner))
        volforner       = varvolforner.value
        return          volforner

    @formworkVolume.setter
    def formworkVolume (self, volforner: float) -> None:
        """Atribui volume cubeta trapezoidal cm3."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varvolforner    = ctypes.c_double (volforner)
        self.m_model.m_eagme.BASME_GEOLAJ_VOLFORNER_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varvolforner))

    @property
    def mouldManufacturer (self) -> str:
        """Laje nervurada: nome do fabricante de enchimentos.

        Returns:
            Cadeia de caracteres.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varnomfab       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GEOLAJ_NOMFAB_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varnomfab))
        nomfab          = varnomfab.value.decode(TQSUtil.CHARSET)
        return          nomfab

    @mouldManufacturer.setter
    def mouldManufacturer (self, nomfab: str) -> None:
        """Atribui nome do fabricante de enchimentos."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varnomfab       = ctypes.c_char_p (nomfab.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GEOLAJ_NOMFAB_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varnomfab))

    @property
    def mouldID (self) -> str:
        """Laje nervurada: nome do enchimento.

        Returns:
            Cadeia de caracteres.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varnomenc       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GEOLAJ_NOMENC_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varnomenc))
        nomenc          = varnomenc.value.decode(TQSUtil.CHARSET)
        return          nomenc

    @mouldID.setter
    def mouldID (self, nomenc: str) -> None:
        """Atribui nome do enchimento."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varnomenc       = ctypes.c_char_p (nomenc.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GEOLAJ_NOMENC_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varnomenc))

    @property
    def latticeTraverseRibEvery (self) -> int:
        """Laje treliçada: nervura transversal a cada N blocos.

        Returns:
            Valor inteiro.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        nervtcada       = 0
        varnervtcada    = ctypes.c_int (nervtcada)
        self.m_model.m_eagme.BASME_GEOLAJ_NERVTCADA_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varnervtcada))
        nervtcada       = varnervtcada.value
        return          nervtcada

    @latticeTraverseRibEvery.setter
    def latticeTraverseRibEvery (self, nervtcada: int) -> None:
        """Atribui Laje treliçada: nervura transversal a cada N blocos."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varnervtcada    = ctypes.c_int (nervtcada)
        self.m_model.m_eagme.BASME_GEOLAJ_NERVTCADA_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varnervtcada))
    @property
    def latticeTraverseWidth (self) -> float:
        """Laje treliçada: largura da nervura secundária cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        espsec          = 0.
        varespsec       = ctypes.c_double (espsec)
        self.m_model.m_eagme.BASME_GEOLAJ_ESPSEC_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varespsec))
        espsec          = varespsec.value
        return          espsec

    @latticeTraverseWidth.setter
    def latticeTraverseWidth (self, espsec: float) -> None:
        """Atribui Laje treliçada: largura da nervura secundária cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varespsec       = ctypes.c_double (espsec)
        self.m_model.m_eagme.BASME_GEOLAJ_ESPSEC_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varespsec))
    @property
    def latticeJoistWidth (self) -> float:
        """Laje treliçada: largura da vigota cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        bvigota         = 0.
        varbvigota      = ctypes.c_double (bvigota)
        self.m_model.m_eagme.BASME_GEOLAJ_BVIGOTA_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varbvigota))
        bvigota         = varbvigota.value
        return          bvigota

    @latticeJoistWidth.setter
    def latticeJoistWidth (self, bvigota: float) -> None:
        """Atribui Laje treliçada: largura da vigota cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varbvigota      = ctypes.c_double (bvigota)
        self.m_model.m_eagme.BASME_GEOLAJ_BVIGOTA_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varbvigota))
    @property
    def latticeJoistHeight (self) -> float:
        """Laje treliçada: altura da vigota cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        hvigota         = 0.
        varhvigota      = ctypes.c_double (hvigota)
        self.m_model.m_eagme.BASME_GEOLAJ_HVIGOTA_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varhvigota))
        hvigota         = varhvigota.value
        return          hvigota

    @latticeJoistHeight.setter
    def latticeJoistHeight (self, hvigota: float) -> None:
        """Atribui Laje treliçada: altura da vigota cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varhvigota      = ctypes.c_double (hvigota)
        self.m_model.m_eagme.BASME_GEOLAJ_HVIGOTA_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varhvigota))
    @property
    def latticeMiniPanel (self) -> int:
        """Laje treliçada: minipainél (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        minipainel      = 0
        varminipainel   = ctypes.c_int (minipainel)
        self.m_model.m_eagme.BASME_GEOLAJ_MINIPAINEL_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varminipainel))
        minipainel      = varminipainel.value
        return          minipainel

    @latticeMiniPanel.setter
    def latticeMiniPanel (self, minipainel: int) -> None:
        """Atribui Laje treliçada: minipainél (0) Não (1) Sim."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varminipainel   = ctypes.c_int (minipainel)
        self.m_model.m_eagme.BASME_GEOLAJ_MINIPAINEL_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varminipainel))

    @property
    def compositeHeight (self) -> float:
        """Laje mista: altura do perfil, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        altperf         = 0.
        varaltperf      = ctypes.c_double (altperf)
        self.m_model.m_eagme.BASME_GEOLAJ_ALTPERF_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varaltperf))
        altperf         = varaltperf.value
        return          altperf

    @compositeHeight.setter
    def compositeHeight (self, altperf: float) -> None:
        """Atribui altura do perfil, cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varaltperf      = ctypes.c_double (altperf)
        self.m_model.m_eagme.BASME_GEOLAJ_ALTPERF_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varaltperf))

    @property
    def compositeWidth (self) -> float:
        """Laje mista: largura do perfil, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        basperf         = 0.
        varbasperf      = ctypes.c_double (basperf)
        self.m_model.m_eagme.BASME_GEOLAJ_BASPERF_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varbasperf))
        basperf         = varbasperf.value
        return          basperf

    @compositeWidth.setter
    def compositeWidth (self, basperf: float) -> None:
        """Atribui largura do perfil, cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varbasperf      = ctypes.c_double (basperf)
        self.m_model.m_eagme.BASME_GEOLAJ_BASPERF_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varbasperf))

    @property
    def compositeFlange (self) -> float:
        """Laje mista: largura da aba, cm.

        Returns:
            Valor de ponto flutuante.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        abaperf         = 0.
        varabaperf      = ctypes.c_double (abaperf)
        self.m_model.m_eagme.BASME_GEOLAJ_ABAPERF_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varabaperf))
        abaperf         = varabaperf.value
        return          abaperf

    @compositeFlange.setter
    def compositeFlange (self, abaperf: float) -> None:
        """Atribui largura da aba, cm."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varabaperf      = ctypes.c_double (abaperf)
        self.m_model.m_eagme.BASME_GEOLAJ_ABAPERF_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varabaperf))

    @property
    def precastRegion (self) -> int:
        """Pré-moldados: Região construtiva.

        Returns:
            Valor inteiro.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        iregiao         = 0
        variregiao      = ctypes.c_int (iregiao)
        self.m_model.m_eagme.BASME_GEOLAJ_IREGIAO_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (variregiao))
        iregiao         = variregiao.value
        return          iregiao

    @precastRegion.setter
    def precastRegion (self, iregiao: int) -> None:
        """Atribui Pré-moldados: Região construtiva."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        variregiao      = ctypes.c_int (iregiao)
        self.m_model.m_eagme.BASME_GEOLAJ_IREGIAO_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (variregiao))
    @property
    def sectionName (self) -> str:
        """Nome de seção não padrão - catalogada.

        Returns:
            Cadeia de caracteres.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varsecaonp      = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GEOLAJ_SECAONP_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varsecaonp))
        secaonp         = varsecaonp.value.decode(TQSUtil.CHARSET)
        return          secaonp

    @sectionName.setter
    def sectionName (self, secaonp: str) -> None:
        """Atribui Nome de seção não padrão - catalogada."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varsecaonp      = ctypes.c_char_p (secaonp.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GEOLAJ_SECAONP_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varsecaonp))
    @property
    def prestressedReinforcement (self) -> str:
        """Nome da configuração de armaduras protendidas.

        Returns:
            Cadeia de caracteres.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidconf       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GEOLAJ_IDCONF_LER (ctypes.byref (vargeolaj),
                            ctypes.byref (varidconf))
        idconf          = varidconf.value.decode(TQSUtil.CHARSET)
        return          idconf

    @prestressedReinforcement.setter
    def prestressedReinforcement (self, idconf: str) -> None:
        """Atribui Nome da configuração de armaduras protendidas."""
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varidconf       = ctypes.c_char_p (idconf.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GEOLAJ_IDCONF_DEF (ctypes.byref (vargeolaj),
                            ctypes.byref (varidconf))

    def LoadManufacturer (self, nomfab: str, nomenc: str) -> int:
        """Carrega os dados de moldes de lajes nervuradas. Retorna (0) Se carregou.

        Args:
            nomfab: Parâmetro ``nomfab``.
            nomenc: Parâmetro ``nomenc``.

        Returns:
            Valor inteiro.
        """
        vargeolaj       = ctypes.c_void_p (self.m_geolaj)
        varnomfab       = ctypes.c_char_p (nomfab.encode (TQSUtil.CHARSET))
        varnomenc       = ctypes.c_char_p (nomenc.encode (TQSUtil.CHARSET))
        istat           = 0
        varistat        = ctypes.c_int (istat)
        self.m_model.m_eagme.BASME_GEOLAJ_ACHARFAB (ctypes.byref (vargeolaj),
                            varnomfab, varnomenc, ctypes.byref (varistat))
        istat           = varistat.value
        return          istat

#------------------------------------------------------------------------------
#        Dados para discretização de laje por grelha
#
class SlabGrid ():

    """Malha de laje.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", grelaj: int) -> None:
        """Dados para discretização de laje por grelha.

        Args:
            model: Objeto Model() do modelo atual.
            grelaj: Apontador para objeto CGreLaj.
        """
        self.m_model    = model
        self.m_grelaj   = grelaj

    @property
    def asGrid (self) -> int:
        """Discretizar esta laje em grelha (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        idiscret        = 0
        varidiscret     = ctypes.c_int (idiscret)
        self.m_model.m_eagme.BASME_GRELAJ_IDISCRET_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (varidiscret))
        idiscret        = varidiscret.value
        return          idiscret

    @asGrid.setter
    def asGrid (self, idiscret: int) -> None:
        """Atribui Discretizar esta laje em grelha (0) Não (1) Sim."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        varidiscret     = ctypes.c_int (idiscret)
        self.m_model.m_eagme.BASME_GRELAJ_IDISCRET_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (varidiscret))

    @property
    def forceAsGrid (self) -> int:
        """Forçar a discretização em laje de escadas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        idiscresc       = 0
        varidiscresc    = ctypes.c_int (idiscresc)
        self.m_model.m_eagme.BASME_GRELAJ_IDISCRESC_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (varidiscresc))
        idiscresc       = varidiscresc.value
        return          idiscresc

    @forceAsGrid.setter
    def forceAsGrid (self, idiscresc: int) -> None:
        """Atribui Forçar a discretização em laje de escadas (0) Não (1) Sim."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        varidiscresc    = ctypes.c_int (idiscresc)
        self.m_model.m_eagme.BASME_GRELAJ_IDISCRESC_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (varidiscresc))

    @property
    def plastSupports (self) -> int:
        """Plastificação (0) conforme critérios (1) Sim (2) Não.

        Returns:
            Valor inteiro.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        iplastif        = 0
        variplastif     = ctypes.c_int (iplastif)
        self.m_model.m_eagme.BASME_GRELAJ_IPLASTIF_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (variplastif))
        iplastif        = variplastif.value
        return          iplastif

    @plastSupports.setter
    def plastSupports (self, iplastif: int) -> None:
        """Atribui Plastificação (0) conforme critérios (1) Sim (2) Não."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        variplastif     = ctypes.c_int (iplastif)
        self.m_model.m_eagme.BASME_GRELAJ_IPLASTIF_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (variplastif))

    @property
    def elstBase (self) -> int:
        """Laje sobre base elástica (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        ibaseelast      = 0
        varibaseelast   = ctypes.c_int (ibaseelast)
        self.m_model.m_eagme.BASME_GRELAJ_IBASEELAST_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (varibaseelast))
        ibaseelast      = varibaseelast.value
        return          ibaseelast

    @elstBase.setter
    def elstBase (self, ibaseelast: int) -> None:
        """Atribui Laje sobre base elástica (0) Não (1) Sim."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        varibaseelast   = ctypes.c_int (ibaseelast)
        self.m_model.m_eagme.BASME_GRELAJ_IBASEELAST_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (varibaseelast))

    @property
    def elstBaseTxSpring (self) -> float:
        """Mola de translação Tx por nó tf/m.

        Returns:
            Valor de ponto flutuante.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        cmolbaseelatx   = 0.
        varcmolbaseelatx= ctypes.c_double (cmolbaseelatx)
        self.m_model.m_eagme.BASME_GRELAJ_CMOLBASEELATX_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (varcmolbaseelatx))
        cmolbaseelatx   = varcmolbaseelatx.value
        return          cmolbaseelatx

    @elstBaseTxSpring.setter
    def elstBaseTxSpring (self, cmolbaseelatx: float) -> None:
        """Atribui Mola de translação Tx por nó tf/m."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        varcmolbaseelatx= ctypes.c_double (cmolbaseelatx)
        self.m_model.m_eagme.BASME_GRELAJ_CMOLBASEELATX_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (varcmolbaseelatx))
    @property
    def elstBaseTySpring (self) -> float:
        """Mola de translação Ty por nó tf/m.

        Returns:
            Valor de ponto flutuante.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        cmolbaseelaty   = 0.
        varcmolbaseelaty= ctypes.c_double (cmolbaseelaty)
        self.m_model.m_eagme.BASME_GRELAJ_CMOLBASEELATY_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (varcmolbaseelaty))
        cmolbaseelaty   = varcmolbaseelaty.value
        return          cmolbaseelaty

    @elstBaseTySpring.setter
    def elstBaseTySpring (self, cmolbaseelaty: float) -> None:
        """Atribui Mola de translação Ty por nó tf/m."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        varcmolbaseelaty= ctypes.c_double (cmolbaseelaty)
        self.m_model.m_eagme.BASME_GRELAJ_CMOLBASEELATY_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (varcmolbaseelaty))
    @property
    def elstBaseTzSpring (self) -> float:
        """Mola de translação Tz por nó tf/m.

        Returns:
            Valor de ponto flutuante.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        cmolbaseelatz   = 0.
        varcmolbaseelatz= ctypes.c_double (cmolbaseelatz)
        self.m_model.m_eagme.BASME_GRELAJ_CMOLBASEELATZ_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (varcmolbaseelatz))
        cmolbaseelatz   = varcmolbaseelatz.value
        return          cmolbaseelatz

    @elstBaseTzSpring.setter
    def elstBaseTzSpring (self, cmolbaseelatz: float) -> None:
        """Atribui Mola de translação Tz por nó tf/m."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        varcmolbaseelatz= ctypes.c_double (cmolbaseelatz)
        self.m_model.m_eagme.BASME_GRELAJ_CMOLBASEELATZ_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (varcmolbaseelatz))
    @property
    def elstBaseGapZPlus (self) -> float:
        """Gap de translação Z+ (m).

        Returns:
            Valor de ponto flutuante.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        gapzp           = 0.
        vargapzp        = ctypes.c_double (gapzp)
        self.m_model.m_eagme.BASME_GRELAJ_GAPZP_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (vargapzp))
        gapzp           = vargapzp.value
        return          gapzp

    @elstBaseGapZPlus.setter
    def elstBaseGapZPlus (self, gapzp: float) -> None:
        """Atribui Gap de translação Z+ (m)."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        vargapzp        = ctypes.c_double (gapzp)
        self.m_model.m_eagme.BASME_GRELAJ_GAPZP_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (vargapzp))
    @property
    def elstBaseGapZMinus (self) -> float:
        """Gap de translação Z- (m).

        Returns:
            Valor de ponto flutuante.
        """
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        gapzn           = 0.
        vargapzn        = ctypes.c_double (gapzn)
        self.m_model.m_eagme.BASME_GRELAJ_GAPZN_LER (ctypes.byref (vargrelaj),
                            ctypes.byref (vargapzn))
        gapzn           = vargapzn.value
        return          gapzn

    @elstBaseGapZMinus.setter
    def elstBaseGapZMinus (self, gapzn: float) -> None:
        """Atribui Gap de translação Z- (m)."""
        vargrelaj       = ctypes.c_void_p (self.m_grelaj)
        vargapzn        = ctypes.c_double (gapzn)
        self.m_model.m_eagme.BASME_GRELAJ_GAPZN_DEF (ctypes.byref (vargrelaj),
                            ctypes.byref (vargapzn))
#------------------------------------------------------------------------------
#        Detalhamento de lajes - CDetLaj
#
class SlabDetailing ():

    """Detalhamento de laje.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", detlaj: int) -> None:
        """Detalhamento de lajes - CDetLaj.

        Args:
            model: Objeto Model() do modelo atual.
            detlaj: Apontador para objeto CDetLaj.
        """
        self.m_model    = model
        self.m_detlaj   = detlaj

    @property
    def detailable (self) -> int:
        """Detalhamento da laje (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        idetlajes       = 0
        varidetlajes    = ctypes.c_int (idetlajes)
        self.m_model.m_eagme.BASME_DETLAJ_IDETALHAVEL_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (varidetlajes))
        idetlajes       = varidetlajes.value
        return          idetlajes

    @detailable.setter
    def detailable (self, idetlajes: int) -> None:
        """Atribui Detalhamento da laje (0) Não (1) Sim."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        varidetlajes    = ctypes.c_int (idetlajes)
        self.m_model.m_eagme.BASME_DETLAJ_IDETALHAVEL_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (varidetlajes))

    @property
    def rigidDiafragm (self) -> int:
        """Diafragma rígido (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        idiafrg         = 0
        varidiafrg      = ctypes.c_int (idiafrg)
        self.m_model.m_eagme.BASME_DETLAJ_IDIAFRG_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (varidiafrg))
        idiafrg         = varidiafrg.value
        return          idiafrg

    @rigidDiafragm.setter
    def rigidDiafragm (self, idiafrg: int) -> None:
        """Atribui Diafragma rígido (0) Não (1) Sim."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        varidiafrg      = ctypes.c_int (idiafrg)
        self.m_model.m_eagme.BASME_DETLAJ_IDIAFRG_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (varidiafrg))

    @property
    def prestressed (self) -> int:
        """Protendida (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        iprotendida     = 0
        variprotendida  = ctypes.c_int (iprotendida)
        self.m_model.m_eagme.BASME_DETLAJ_IPROTENDIDA_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (variprotendida))
        iprotendida     = variprotendida.value
        return          iprotendida

    @prestressed.setter
    def prestressed (self, iprotendida: int) -> None:
        """Atribui Protendida (0) Não (1) Sim."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        variprotendida  = ctypes.c_int (iprotendida)
        self.m_model.m_eagme.BASME_DETLAJ_IPROTENDIDA_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (variprotendida))

    @property
    def cover (self) -> float:
        """Cobrimento diferenciado em cm.

        Returns:
            Valor de ponto flutuante.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        cobrimento      = 0.
        varcobrimento   = ctypes.c_double (cobrimento)
        self.m_model.m_eagme.BASME_DETLAJ_COBRIMENTO_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (varcobrimento))
        cobrimento       = varcobrimento.value
        return          cobrimento

    @cover.setter
    def cover (self, cobrimento: float) -> None:
        """Atribui Cobrimento diferenciado em cm."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        varcobrimento   = ctypes.c_double (cobrimento)
        self.m_model.m_eagme.BASME_DETLAJ_COBRIMENTO_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (varcobrimento))
    @property
    def exposure (self) -> int:
        """Em contato com o solo (0) Não (1) Sim (2) Exposta ao ambiente.

        Returns:
            Valor inteiro.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        icontsolo       = 0
        varicontsolo    = ctypes.c_int (icontsolo)
        self.m_model.m_eagme.BASME_DETLAJ_ICONTSOLO_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (varicontsolo))
        icontsolo       = varicontsolo.value
        return          icontsolo

    @exposure.setter
    def exposure (self, icontsolo: int) -> None:
        """Atribui Em contato com o solo (0) Não (1) Sim (2) Exposta ao ambiente."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        varicontsolo    = ctypes.c_int (icontsolo)
        self.m_model.m_eagme.BASME_DETLAJ_ICONTSOLO_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (varicontsolo))
    @property
    def cantileverFactor (self) -> float:
        """Majorador para laje em balanço ou (0.).

        Returns:
            Valor de ponto flutuante.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        gaman           = 0.
        vargaman        = ctypes.c_double (gaman)
        self.m_model.m_eagme.BASME_DETLAJ_GAMAN_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (vargaman))
        gaman           = vargaman.value
        return          gaman

    @cantileverFactor.setter
    def cantileverFactor (self, gaman: float) -> None:
        """Atribui Majorador para laje em balanço ou (0.)."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        vargaman        = ctypes.c_double (gaman)
        self.m_model.m_eagme.BASME_DETLAJ_GAMAN_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (vargaman))
    @property
    def cantilever (self) -> int:
        """Verificação de dimensões: Balanço (0) Estimado, geometria (1) Não (2) Sim.

        Returns:
            Valor inteiro.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        ibalanco        = 0
        varibalanco     = ctypes.c_int (ibalanco)
        self.m_model.m_eagme.BASME_DETLAJ_IBALANCO_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (varibalanco))
        ibalanco        = varibalanco.value
        return          ibalanco

    @cantilever.setter
    def cantilever (self, ibalanco: int) -> None:
        """Atribui Verificação de dimensões: Balanço (0) Estimado, geometria (1) Não (2) Sim."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        varibalanco     = ctypes.c_int (ibalanco)
        self.m_model.m_eagme.BASME_DETLAJ_IBALANCO_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (varibalanco))
    @property
    def estimatedSpan (self) -> float:
        """Vão estimado ou (0.) cm.

        Returns:
            Valor de ponto flutuante.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        vaoest          = 0.
        varvaoest       = ctypes.c_double (vaoest)
        self.m_model.m_eagme.BASME_DETLAJ_VAOEST_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (varvaoest))
        vaoest          = varvaoest.value
        return          vaoest

    @estimatedSpan.setter
    def estimatedSpan (self, vaoest: float) -> None:
        """Atribui Vão estimado ou (0.) cm."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        varvaoest       = ctypes.c_double (vaoest)
        self.m_model.m_eagme.BASME_DETLAJ_VAOEST_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (varvaoest))
    @property
    def roofSlab (self) -> int:
        """Verificação de dimensões: Laje de cobertura (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        icobertura      = 0
        varicobertura   = ctypes.c_int (icobertura)
        self.m_model.m_eagme.BASME_DETLAJ_ICOBERTURA_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (varicobertura))
        icobertura      = varicobertura.value
        return          icobertura

    @roofSlab.setter
    def roofSlab (self, icobertura: int) -> None:
        """Atribui Verificação de dimensões: Laje de cobertura (0) Não (1) Sim."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        varicobertura   = ctypes.c_int (icobertura)
        self.m_model.m_eagme.BASME_DETLAJ_ICOBERTURA_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (varicobertura))
    @property
    def flatSlab (self) -> int:
        """Verificação de dimensões: Laje plana (0) Geometria (1) Não (2) Sim (3) C/capitéis.

        Returns:
            Valor inteiro.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        iplana          = 0
        variplana       = ctypes.c_int (iplana)
        self.m_model.m_eagme.BASME_DETLAJ_IPLANA_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (variplana))
        iplana          = variplana.value
        return          iplana

    @flatSlab.setter
    def flatSlab (self, iplana: int) -> None:
        """Atribui Verificação de dimensões: Laje plana (0) Geometria (1) Não (2) Sim (3) C/capitéis."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        variplana       = ctypes.c_int (iplana)
        self.m_model.m_eagme.BASME_DETLAJ_IPLANA_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (variplana))
    @property
    def bottomReinforcement (self) -> int:
        """Direção de armação: (0) Padrão (1) uma direção (2) duas direções.

        Returns:
            Valor inteiro.
        """
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        idirarma        = 0
        varidirarma     = ctypes.c_int (idirarma)
        self.m_model.m_eagme.BASME_DETLAJ_IDIRARMA_LER (ctypes.byref (vardetlaj),
                            ctypes.byref (varidirarma))
        idirarma        = varidirarma.value
        return          idirarma

    @bottomReinforcement.setter
    def bottomReinforcement (self, idirarma: int) -> None:
        """Atribui Direção de armação: (0) Padrão (1) uma direção (2) duas direções."""
        vardetlaj       = ctypes.c_void_p (self.m_detlaj)
        varidirarma     = ctypes.c_int (idirarma)
        self.m_model.m_eagme.BASME_DETLAJ_IDIRARMA_DEF (ctypes.byref (vardetlaj),
                            ctypes.byref (varidirarma))

#-----------------------------------------------------------------------------
#      Grupo de pré-moldados - Agrupa/define nome para pré-moldado - CGrupoPre
#
class PreCastGroup ():

    """Grupo de pré-moldados.

    Implementação:
        Grupo de pré-moldados (``CGrupoPm``). Sub-objetos são expostos via @property que
        lêem ponteiros do agrupamento e instanciam wrappers Python.
    """
    def __init__ (self, model: "Model", grupopre: int) -> None:
        """Detalhamento de lajes - CDetLaj.

        Args:
            model: Objeto Model() do modelo atual.
            grupopre: Apontador para objeto CGrupoPre.
        """
        self.m_model    = model
        self.m_grupopre = grupopre

    @property
    def floorPlanGroup (self) -> str:
        """Nome do grupo de formas.

        Returns:
            Cadeia de caracteres.
        """
        vargrupopre     = ctypes.c_void_p (self.m_grupopre)
        vargrupofor     = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GRUPOPRE_GRUPOFOR_LER (ctypes.byref (vargrupopre),
                            ctypes.byref (vargrupofor))
        grupofor        = vargrupofor.value.decode(TQSUtil.CHARSET)
        return          grupofor

    @floorPlanGroup.setter
    def floorPlanGroup (self, grupofor: str) -> None:
        """Atribui Nome do grupo de formas."""
        vargrupopre       = ctypes.c_void_p (self.m_grupopre)
        vargrupofor       = ctypes.c_char_p (grupofor.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GRUPOPRE_GRUPOFOR_DEF (ctypes.byref (vargrupopre),
                            ctypes.byref (vargrupofor))

    @property
    def floorPlanNumber (self) -> int:
        """Número único de elemento do grupo.

        Returns:
            Valor inteiro.
        """
        vargrupopre     = ctypes.c_void_p (self.m_grupopre)
        igrupofor       = 0
        varigrupofor    = ctypes.c_int (igrupofor)
        self.m_model.m_eagme.BASME_GRUPOPRE_IGRUPOFOR_LER (ctypes.byref (vargrupopre),
                            ctypes.byref (varigrupofor))
        igrupofor       = varigrupofor.value
        return          igrupofor

    @floorPlanNumber.setter
    def floorPlanNumber (self, igrupofor: int) -> None:
        """Atribui Número único de elemento do grupo."""
        vargrupopre     = ctypes.c_void_p (self.m_grupopre)
        varigrupofor    = ctypes.c_int (igrupofor)
        self.m_model.m_eagme.BASME_GRUPOPRE_IGRUPOFOR_DEF (ctypes.byref (vargrupopre),
                            ctypes.byref (varigrupofor))
    @property
    def reinforcementGroup (self) -> str:
        """Nome do grupo de armação.

        Returns:
            Cadeia de caracteres.
        """
        vargrupopre     = ctypes.c_void_p (self.m_grupopre)
        vargrupoarm     = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_GRUPOPRE_GRUPOARM_LER (ctypes.byref (vargrupopre),
                            ctypes.byref (vargrupoarm))
        grupoarm        = vargrupoarm.value.decode(TQSUtil.CHARSET)
        return          grupoarm

    @reinforcementGroup.setter
    def reinforcementGroup (self, grupoarm: str) -> None:
        """Atribui Nome do grupo de armação."""
        vargrupopre       = ctypes.c_void_p (self.m_grupopre)
        vargrupoarm       = ctypes.c_char_p (grupoarm.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_GRUPOPRE_GRUPOARM_DEF (ctypes.byref (vargrupopre),
                            ctypes.byref (vargrupoarm))
    @property
    def beamLoad (self) -> float:
        """Carga distribuída para vigas com grupo de armação renumerado tf/m.

        Returns:
            Valor de ponto flutuante.
        """
        vargrupopre     = ctypes.c_void_p (self.m_grupopre)
        cdistv          = 0.
        varcdistv       = ctypes.c_double (cdistv)
        self.m_model.m_eagme.BASME_GRUPOPRE_CDISTV_LER (ctypes.byref (vargrupopre),
                            ctypes.byref (varcdistv))
        cdistv          = varcdistv.value
        return          cdistv

    @beamLoad.setter
    def beamLoad (self, cdistv: float) -> None:
        """Atribui Carga distribuída para vigas com grupo de armação renumerado tf/m."""
        vargrupopre     = ctypes.c_void_p (self.m_grupopre)
        varcdistv       = ctypes.c_double (cdistv)
        self.m_model.m_eagme.BASME_GRUPOPRE_CDISTV_DEF (ctypes.byref (vargrupopre),
                            ctypes.byref (varcdistv))
#-----------------------------------------------------------------------------
#      Variáveis de um tubo de água pluvial de pilar pré-moldado CPreAgua
#
class RainWaterPipe  ():

    """Tubo de água pluvial em pré-moldado.

    Implementação:
        Tubo de água pluvial em pilar pré-moldado (``CTuboPM``). Property bag com
        coordenadas, dimensões e identificador textual.
    """
    def __init__ (self, model: "Model", preagua: int) -> None:
        """Tubo de água pluvial.

        Args:
            model: Objeto Model() do modelo atual.
            preagua: Apontador para objeto CPreAgua.
        """
        self.m_model    = model
        self.m_preagua  = preagua

    @property
    def pipeDiameter (self) -> float:
        """Diâmetro do tubo cm.

        Returns:
            Valor de ponto flutuante.
        """
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        diamtub         = 0.
        vardiamtub      = ctypes.c_double (diamtub)
        self.m_model.m_eagme.BASME_PREAGUA_DIAMTUB_LER (ctypes.byref (varpreagua),
                            ctypes.byref (vardiamtub))
        diamtub         = vardiamtub.value
        return          diamtub

    @pipeDiameter.setter
    def pipeDiameter (self, diamtub: float) -> None:
        """Atribui Diâmetro do tubo cm."""
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        vardiamtub      = ctypes.c_double (diamtub)
        self.m_model.m_eagme.BASME_PREAGUA_DIAMTUB_DEF (ctypes.byref (varpreagua),
                            ctypes.byref (vardiamtub))

    @property
    def minFunnelWidth (self) -> float:
        """Diâmetro do funil menor cm.

        Returns:
            Valor de ponto flutuante.
        """
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        diamfunmin      = 0.
        vardiamfunmin   = ctypes.c_double (diamfunmin)
        self.m_model.m_eagme.BASME_PREAGUA_DIAMFUNMIN_LER (ctypes.byref (varpreagua),
                            ctypes.byref (vardiamfunmin))
        diamfunmin      = vardiamfunmin.value
        return          diamfunmin

    @minFunnelWidth.setter
    def minFunnelWidth (self, diamfunmin: float) -> None:
        """Atribui Diâmetro do funil menor cm."""
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        vardiamfunmin   = ctypes.c_double (diamfunmin)
        self.m_model.m_eagme.BASME_PREAGUA_DIAMFUNMIN_DEF (ctypes.byref (varpreagua),
                            ctypes.byref (vardiamfunmin))

    @property
    def maxFunnelWidth (self) -> float:
        """Diâmetro do funil maior cm.

        Returns:
            Valor de ponto flutuante.
        """
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        diamfunmax      = 0.
        vardiamfunmax   = ctypes.c_double (diamfunmax)
        self.m_model.m_eagme.BASME_PREAGUA_DIAMFUNMAX_LER (ctypes.byref (varpreagua),
                            ctypes.byref (vardiamfunmax))
        diamfunmax      = vardiamfunmax.value
        return          diamfunmax

    @maxFunnelWidth.setter
    def maxFunnelWidth (self, diamfunmax: float) -> None:
        """Atribui Diâmetro do funil maior cm."""
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        vardiamfunmax   = ctypes.c_double (diamfunmax)
        self.m_model.m_eagme.BASME_PREAGUA_DIAMFUNMAX_DEF (ctypes.byref (varpreagua),
                            ctypes.byref (vardiamfunmax))

    @property
    def rotation (self) -> float:
        """Ângulo adicional em relação ao pilar em graus.

        Returns:
            Valor de ponto flutuante.
        """
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        angadi          = 0.
        varangadi       = ctypes.c_double (angadi)
        self.m_model.m_eagme.BASME_PREAGUA_ANGADI_LER (ctypes.byref (varpreagua),
                            ctypes.byref (varangadi))
        angadi          = varangadi.value
        return          angadi

    @rotation.setter
    def rotation (self, angadi: float) -> None:
        """Atribui Ângulo adicional em relação ao pilar em graus."""
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        varangadi       = ctypes.c_double (angadi)
        self.m_model.m_eagme.BASME_PREAGUA_ANGADI_DEF (ctypes.byref (varpreagua),
                            ctypes.byref (varangadi))

    @property
    def baseDistance (self) -> float:
        """Distância de saída da base cm (0.) Adota default.

        Returns:
            Valor de ponto flutuante.
        """
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        distagusai      = 0.
        vardistagusai   = ctypes.c_double (distagusai)
        self.m_model.m_eagme.BASME_PREAGUA_DISTAGUSAI_LER (ctypes.byref (varpreagua),
                            ctypes.byref (vardistagusai))
        distagusai      = vardistagusai.value
        return          distagusai

    @baseDistance.setter
    def baseDistance (self, distagusai: float) -> None:
        """Atribui Distância de saída da base cm (0.) Adota default."""
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        vardistagusai   = ctypes.c_double (distagusai)
        self.m_model.m_eagme.BASME_PREAGUA_DISTAGUSAI_DEF (ctypes.byref (varpreagua),
                            ctypes.byref (vardistagusai))

    @property
    def tubeIdentification (self) -> str:
        """Identificador do tubo.

        Returns:
            Cadeia de caracteres.
        """
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        varidenttube    = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_PREAGUA_IDENT_LER (ctypes.byref (varpreagua),
                            ctypes.byref (varidenttube))
        identtube       = varidenttube.value.decode(TQSUtil.CHARSET)
        return          identtube

    @tubeIdentification.setter
    def tubeIdentification (self, identtube: str) -> None:
        """Atribui Identificador do tubo."""
        varpreagua      = ctypes.c_void_p (self.m_preagua)
        varidenttube    = ctypes.c_char_p (identtube.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_PREAGUA_IDENT_DEF (ctypes.byref (varpreagua),
                            ctypes.byref (varidenttube))
#-----------------------------------------------------------------------------
#      Alça de içamento de pilares pré-moldados- CPreAlca
#
class LiftingAnchors  ():

    """Içamento (alças de transporte) em pré-moldado.

    Implementação:
        Alças de içamento em pilar pré-moldado (``CIcamPM``). Property bag de coordenadas
        e rebaixos; ``GetLiftingRecess`` / ``SetLiftingRecess`` indexam por face.
    """
    def __init__ (self, model: "Model", prealca: int) -> None:
        """Alça de içamento de pilares pré-moldados.

        Args:
            model: Objeto Model() do modelo atual.
            prealca: Apontador para objeto CPreAlca.
        """
        self.m_model    = model
        self.m_prealca  = prealca

    def GetNumLiftingAnchors (self) -> int:
        """Retorna num lifting anchors.

        Returns:
            Valor inteiro.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        numalcas        = 0
        varnumalcas     = ctypes.c_int (numalcas)
        self.m_model.m_eagme.BASME_PREALCA_NUMALCAS_LER (ctypes.byref (varprealca),
                            ctypes.byref (varnumalcas))
        numalcas        = varnumalcas.value
        return          numalcas

    def GetLiftingRecess (self, ialca: int) -> float:
        """int ialca.

        Args:
            ialca: Parâmetro ``ialca``.

        Returns:
            int ialca   <- 0..GetNumLifting()-1.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        varialca        = ctypes.c_int (ialca)
        dfs             = 0.
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_PREALCA_DFS_LER (ctypes.byref (varprealca),
                            ctypes.byref (varialca), ctypes.byref (vardfs))
        dfs             = vardfs.value
        return          dfs

    def SetLiftingRecess (self, ialca: int, dfs: float) -> None:
        """Define um rebaixo de alça.

        Args:
            ialca: Parâmetro ``ialca``.
            dfs: Parâmetro ``dfs``.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        varialca        = ctypes.c_int (ialca)
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_PREALCA_DFS_DEF (ctypes.byref (varprealca),
                            ctypes.byref (varialca), ctypes.byref (vardfs))

    def EnterLiftingRecess (self, dfs: float) -> None:
        """Entra um rebaixo de alça no final da lista.

        Args:
            dfs: Parâmetro ``dfs``.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_PREALCA_DFS_ENTRAR (ctypes.byref (varprealca),
                            ctypes.byref (vardfs))

    def EraseLiftingAnchor (self, ialca: int) -> None:
        """Apaga um rebaixo de alça.

        Args:
            ialca: Parâmetro ``ialca``.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        varialca        = ctypes.c_int (ialca)
        self.m_model.m_eagme.BASME_PREALCA_DFS_APAGAR (ctypes.byref (varprealca),
                            ctypes.byref (varialca))

    def SortLiftingAnchors (self) -> None:
        """Classifica as alças por ordem de rebaixo.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        self.m_model.m_eagme.BASME_PREALCA_CLASSIFICAR (ctypes.byref (varprealca))


    @property
    def liftingAnchorId (self) -> str:
        """Identificador de alças.

        Returns:
            Cadeia de caracteres.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        varidentalca    = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_PREALCA_IDENT_LER (ctypes.byref (varprealca),
                            ctypes.byref (varidentalca))
        identalca       = varidentalca.value.decode(TQSUtil.CHARSET)
        return          identalca

    @liftingAnchorId.setter
    def liftingAnchorId (self, identalca: str) -> None:
        """Atribui Identificador de alças."""
        varprealca      = ctypes.c_void_p (self.m_prealca)
        varidentalca    = ctypes.c_char_p (identalca.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_PREALCA_IDENT_DEF (ctypes.byref (varprealca),
                            ctypes.byref (varidentalca))

    @property
    def liftingPosition (self) -> int:
        """Alças em posição padrão (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        ialcauto        = 0
        varialcauto     = ctypes.c_int (ialcauto)
        self.m_model.m_eagme.BASME_PREALCA_IALCAUTO_LER (ctypes.byref (varprealca),
                            ctypes.byref (varialcauto))
        ialcauto        = varialcauto.value
        return          ialcauto

    @liftingPosition.setter
    def liftingPosition (self, ialcauto: int) -> None:
        """Atribui Alças em posição padrão (0) Não (1) Sim."""
        varprealca      = ctypes.c_void_p (self.m_prealca)
        varialcauto     = ctypes.c_int (ialcauto)
        self.m_model.m_eagme.BASME_PREALCA_IALCAUTO_DEF (ctypes.byref (varprealca),
                            ctypes.byref (varialcauto))
    @property
    def liftingAnchorsDefined (self) -> int:
        """Alças definidas (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        ialcadef        = 0
        varialcadef     = ctypes.c_int (ialcadef)
        self.m_model.m_eagme.BASME_PREALCA_IALCADEF_LER (ctypes.byref (varprealca),
                            ctypes.byref (varialcadef))
        ialcadef        = varialcadef.value
        return          ialcadef

    @liftingAnchorsDefined.setter
    def liftingAnchorsDefined (self, ialcadef: int) -> None:
        """Atribui Alças definidas (0) Não (1) Sim."""
        varprealca      = ctypes.c_void_p (self.m_prealca)
        varialcadef     = ctypes.c_int (ialcadef)
        self.m_model.m_eagme.BASME_PREALCA_IALCADEF_DEF (ctypes.byref (varprealca),
                            ctypes.byref (varialcadef))

    @property
    def topLiftingAngle (self) -> float:
        """Ângulo da alça de topo em graus.

        Returns:
            Valor de ponto flutuante.
        """
        varprealca      = ctypes.c_void_p (self.m_prealca)
        angtopo         = 0.
        varangtopo      = ctypes.c_double (angtopo)
        self.m_model.m_eagme.BASME_PREALCA_ANGTOPO_LER (ctypes.byref (varprealca),
                            ctypes.byref (varangtopo))
        angtopo         = varangtopo.value
        return          angtopo

    @topLiftingAngle.setter
    def topLiftingAngle (self, angtopo: float) -> None:
        """Atribui Ângulo da alça de topo em graus."""
        varprealca      = ctypes.c_void_p (self.m_prealca)
        varangtopo      = ctypes.c_double (angtopo)
        self.m_model.m_eagme.BASME_PREALCA_ANGTOPO_DEF (ctypes.byref (varprealca),
                            ctypes.byref (varangtopo))
#-----------------------------------------------------------------------------
#      Furos de içamento de pilares pré-moldados - CPreFur
#
class LiftOpenning  ():

    """Abertura de içamento em pré-moldado.

    Implementação:
        Abertura para alça de içamento (``CFurIca``). Property bag análogo a
        :class:`LiftingAnchors` mas para os furos correspondentes.
    """
    def __init__ (self, model: "Model", prefur: int) -> None:
        """Furos de levantamento de pilares pré-moldados.

        Args:
            model: Objeto Model() do modelo atual.
            prefur: Apontador para objeto CPreFur.
        """
        self.m_model    = model
        self.m_prefur   = prefur

    def GetNumLiftingOpennings (self) -> int:
        """Retorna num lifting opennings.

        Returns:
            Valor inteiro.
        """
        varprefur       = ctypes.c_void_p (self.m_prefur)
        numfur          = 0
        varnumfur       = ctypes.c_int (numfur)
        self.m_model.m_eagme.BASME_PREFUR_NUMFUR_LER (ctypes.byref (varprefur),
                            ctypes.byref (varnumfur))
        numfur          = varnumfur.value
        return          numfur

    def GetLiftingRecess (self, ifur: int) -> float:
        """int ifur.

        Args:
            ifur: Parâmetro ``ifur``.

        Returns:
            int ifur    <- 0..GetNumLiftingOpennings()-1.
        """
        varprefur       = ctypes.c_void_p (self.m_prefur)
        varifur         = ctypes.c_int (ifur)
        dfs             = 0.
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_PREFUR_DFS_LER (ctypes.byref (varprefur),
                            ctypes.byref (varifur), ctypes.byref (vardfs))
        dfs             = vardfs.value
        return          dfs

    def SetLiftingRecess (self, ifur: int, dfs: float) -> None:
        """Define um rebaixo de furo.

        Args:
            ifur: Parâmetro ``ifur``.
            dfs: Parâmetro ``dfs``.
        """
        varprefur       = ctypes.c_void_p (self.m_prefur)
        varifur         = ctypes.c_int (ifur)
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_PREFUR_DFS_DEF (ctypes.byref (varprefur),
                            ctypes.byref (varifur), ctypes.byref (vardfs))

    def EnterLiftingRecess (self, dfs: float) -> None:
        """Entra um rebaixo de furo no final da lista.

        Args:
            dfs: Parâmetro ``dfs``.
        """
        varprefur      = ctypes.c_void_p (self.m_prefur)
        vardfs          = ctypes.c_double (dfs)
        self.m_model.m_eagme.BASME_PREFUR_DFS_ENTRAR (ctypes.byref (varprefur),
                            ctypes.byref (vardfs))

    def EraseLiftingOpenning (self, ifur: int) -> None:
        """Apaga um rebaixo de furo.

        Args:
            ifur: Parâmetro ``ifur``.
        """
        varprefur      = ctypes.c_void_p (self.m_prefur)
        varifur        = ctypes.c_int (ifur)
        self.m_model.m_eagme.BASME_PREFUR_DFS_APAGAR (ctypes.byref (varprefur),
                            ctypes.byref (varifur))

    def SortLiftingOpennings (self) -> None:
        """Classifica as furos por ordem de rebaixo.
        """
        varprefur      = ctypes.c_void_p (self.m_prefur)
        self.m_model.m_eagme.BASME_PREFUR_DFS_CLASSIFICAR (ctypes.byref (varprefur))


    @property
    def liftingDiameter (self) -> float:
        """Diâmetro do furo, cm.

        Returns:
            Valor de ponto flutuante.
        """
        varprefur       = ctypes.c_void_p (self.m_prefur)
        diamfuro        = 0.
        vardiamfuro     = ctypes.c_double (diamfuro)
        self.m_model.m_eagme.BASME_PREFUR_DIAM_LER (ctypes.byref (varprefur),
                            ctypes.byref (vardiamfuro))
        diamfuro        = vardiamfuro.value
        return          diamfuro

    @liftingDiameter.setter
    def liftingDiameter (self, diamfuro: float) -> None:
        """Atribui Diâmetro do furo, cm."""
        varprefur       = ctypes.c_void_p (self.m_prefur)
        vardiamfuro     = ctypes.c_double (diamfuro)
        self.m_model.m_eagme.BASME_PREFUR_DIAM_DEF (ctypes.byref (varprefur),
                            ctypes.byref (vardiamfuro))

    @property
    def liftingEccentricity (self) -> float:
        """Excentricidade do furo (cm) em relação ao CG do pilar.

        Returns:
            Valor de ponto flutuante.
        """
        varprefur       = ctypes.c_void_p (self.m_prefur)
        excenfuro       = 0.
        varexcenfuro    = ctypes.c_double (excenfuro)
        self.m_model.m_eagme.BASME_PREFUR_EXCENFURO_LER (ctypes.byref (varprefur),
                            ctypes.byref (varexcenfuro))
        excenfuro       = varexcenfuro.value
        return          excenfuro

    @liftingEccentricity.setter
    def liftingEccentricity (self, excenfuro: float) -> None:
        """Atribui Excentricidade do furo (cm) em relação ao CG do pilar."""
        varprefur       = ctypes.c_void_p (self.m_prefur)
        varexcenfuro     = ctypes.c_double (excenfuro)
        self.m_model.m_eagme.BASME_PREFUR_EXCENFURO_DEF (ctypes.byref (varprefur),
                            ctypes.byref (varexcenfuro))

    @property
    def liftingPosition (self) -> int:
        """Furos em posição padrão (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varprefur       = ctypes.c_void_p (self.m_prefur)
        ifuroauto       = 0
        varifuroauto    = ctypes.c_int (ifuroauto)
        self.m_model.m_eagme.BASME_PREFUR_IFUROAUTO_LER (ctypes.byref (varprefur),
                            ctypes.byref (varifuroauto))
        ifuroauto       = varifuroauto.value
        return          ifuroauto

    @liftingPosition.setter
    def liftingPosition (self, ifuroauto: int) -> None:
        """Atribui Furos em posição padrão (0) Não (1) Sim."""
        varprefur       = ctypes.c_void_p (self.m_prefur)
        varifuroauto    = ctypes.c_int (ifuroauto)
        self.m_model.m_eagme.BASME_PREFUR_IFUROAUTO_DEF (ctypes.byref (varprefur),
                            ctypes.byref (varifuroauto))

    @property
    def liftOpenningDefined (self) -> int:
        """Furos de içamento definidos (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varprefur       = ctypes.c_void_p (self.m_prefur)
        ifurodef        = 0
        varifurodef     = ctypes.c_int (ifurodef)
        self.m_model.m_eagme.BASME_PREFUR_IFURODEF_LER (ctypes.byref (varprefur),
                            ctypes.byref (varifurodef))
        ifurodef        = varifurodef.value
        return          ifurodef

    @liftOpenningDefined.setter
    def liftOpenningDefined (self, ifurodef: int) -> None:
        """Atribui Furos de içamento definidos (0) Não (1) Sim."""
        varprefur       = ctypes.c_void_p (self.m_prefur)
        varifurodef     = ctypes.c_int (ifurodef)
        self.m_model.m_eagme.BASME_PREFUR_IFURODEF_DEF (ctypes.byref (varprefur),
                            ctypes.byref (varifurodef))

#------------------------------------------------------------------------------
#        Condições de contorno de pilares - CContPil
#
class ColumnBoundaryCond ():

    """Condições de contorno de pilar.

    Implementação:
        Condições de contorno de pilar na grelha (``CContPil``). Métodos indexados
        por ``COLUMNSPRING_*`` lêem/escrevem coeficiente de mola e gap por direção.
    """
    def __init__ (self, model: "Model", contpil: int) -> None:
        """Condições de contorno de pilares.

        Args:
            model: Objeto Model() do modelo atual.
            contpil: Apontador para objeto CContPil.
        """
        self.m_model    = model
        self.m_contpil  = contpil

    @property
    def bearingModel (self) -> int:
        """Tipo de apoio em grelha COLUMNBEARING_xxxxx.

        Returns:
            Valor inteiro.
        """
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        iapogre         = 0
        variapogre      = ctypes.c_int (iapogre)
        self.m_model.m_eagme.BASME_CONTPIL_IAPOGRE_LER (ctypes.byref (varcontpil),
                            ctypes.byref (variapogre))
        iapogre         = variapogre.value
        return          iapogre

    @bearingModel.setter
    def bearingModel (self, iapogre: int) -> None:
        """Atribui Tipo de apoio em grelha COLUMNBEARING_xxxxx."""
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        variapogre      = ctypes.c_int (iapogre)
        self.m_model.m_eagme.BASME_CONTPIL_IAPOGRE_DEF (ctypes.byref (varcontpil),
                            ctypes.byref (variapogre))

    def GetSpringValue (self, icoef: int) -> float:
        """int icoef.

        Args:
            icoef: Parâmetro ``icoef``.

        Returns:
            int icoef           <- Coeficiente COLUMNSPRING_xxxx.
        """
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        varicoef        = ctypes.c_int (icoef)
        coefmola        = 0.
        varcoefmola     = ctypes.c_double (coefmola)
        self.m_model.m_eagme.BASME_CONTPIL_COEFMOLA_LER (ctypes.byref (varcontpil),
                            ctypes.byref (varicoef), ctypes.byref (varcoefmola))
        coefmola        = varcoefmola.value
        return          coefmola

    def SetSpringValue (self, icoef: int, coefmola: float) -> None:
        """Define o valor da mola de rotação ou translação do apoio em pilar nas grelhas.

        Args:
            icoef: Parâmetro ``icoef``.
            coefmola: Parâmetro ``coefmola``.
        """
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        varicoef        = ctypes.c_int (icoef)
        varcoefmola     = ctypes.c_double (coefmola)
        self.m_model.m_eagme.BASME_CONTPIL_COEFMOLA_DEF (ctypes.byref (varcontpil),
                            ctypes.byref (varicoef), ctypes.byref (varcoefmola))

    @property
    def madatoryPunchingShear (self) -> int:
        """Armadura de punção obrigatória (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        ipuncaoobrig    = 0
        varipuncaoobrig = ctypes.c_int (ipuncaoobrig)
        self.m_model.m_eagme.BASME_CONTPIL_IPUNCAOOBRIG_LER (ctypes.byref (varcontpil),
                            ctypes.byref (varipuncaoobrig))
        ipuncaoobrig    = varipuncaoobrig.value
        return          ipuncaoobrig

    @madatoryPunchingShear.setter
    def madatoryPunchingShear (self, ipuncaoobrig: int) -> None:
        """Atribui Armadura de punção obrigatória (0) Não (1) Sim."""
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        varipuncaoobrig = ctypes.c_int (ipuncaoobrig)
        self.m_model.m_eagme.BASME_CONTPIL_IPUNCAOOBRIG_DEF (ctypes.byref (varcontpil),
                            ctypes.byref (varipuncaoobrig))
    @property
    def shearWallDiscretization (self) -> int:
        """Pilar parede discretizado (0) Não (1) Sim, estimado ou discretizado.

        Returns:
            Valor inteiro.
        """
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        idiscretmodel   = 0
        varidiscretmodel= ctypes.c_int (idiscretmodel)
        self.m_model.m_eagme.BASME_CONTPIL_IDISCRETMODEL_LER (ctypes.byref (varcontpil),
                            ctypes.byref (varidiscretmodel))
        idiscretmodel   = varidiscretmodel.value
        return          idiscretmodel

    @shearWallDiscretization.setter
    def shearWallDiscretization (self, idiscretmodel: int) -> None:
        """Atribui Pilar parede discretizado (0) Não (1) Sim, estimado ou discretizado."""
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        varidiscretmodel= ctypes.c_int (idiscretmodel)
        self.m_model.m_eagme.BASME_CONTPIL_IDISCRETMODEL_DEF (ctypes.byref (varcontpil),
                            ctypes.byref (varidiscretmodel))
    def GetGap (self, igap: int) -> float:
        """Valor do gap (m) de restrição de apoio.

        Args:
            igap: Gap TIPO COLUMNCOIL_IGAP_xxxx.

        Returns:
            Valor do gap (m).
        """
        varcontpil      = ctypes.c_void_p (self.m_contpil)
        varigap         = ctypes.c_int (igap)
        gap             = 0.
        vargap          = ctypes.c_double (gap)
        self.m_model.m_eagme.BASME_CONTPIL_GAP_LER (ctypes.byref (varcontpil),
                            ctypes.byref (varigap), ctypes.byref (vargap))
        gap             = vargap.value
        return          gap

    def SetGap (self, igap: int, gap: float) -> None:
        """Valor do gap (m) de restrição de apoio.

        Args:
            igap: Gap TIPO COLUMNCOIL_IGAP_xxxx.
            gap: Valor do gap (m).
        """
        varcontpil       = ctypes.c_void_p (self.m_contpil)
        varigap         = ctypes.c_int (igap)
        vargap          = ctypes.c_double (gap)
        self.m_model.m_eagme.BASME_CONTPIL_GAP_DEF (ctypes.byref (varcontpil),
                            ctypes.byref (varigap), ctypes.byref (vargap))

#------------------------------------------------------------------------------
#        Dados de Bloco de transição - CBlocoTrans
#
class ColumnTransferBlock ():

    """Bloco de transferência de pilar.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", blocotrans: int) -> None:
        """Blocos de transição de pilares.

        Args:
            model: Objeto Model() do modelo atual.
            blocotrans: Apontador para objeto CBlocoTrans.
        """
        self.m_model      = model
        self.m_blocotrans = blocotrans
#------------------------------------------------------------------------------
#       Objeto de identificação de objetos CIdentElem
#
class SMObjectIdent ():

    """Identificação textual de objeto do Modelador.

    Implementação:
        Identificação textual (numérica + sufixos) de um objeto do Modelador,
        armazenada em ``CIdentNum``. ``textPosition`` devolve o objeto de coordenadas
        da rotulação associada.
    """
    def __init__ (self, model: "Model", ident: int) -> None:
        """Classe de identificação de objeto.

        Args:
            model: Objeto Model() do modelo atual.
            ident: Apontador para objeto CIdent.
        """
        self.m_model    = model
        self.m_ident    = ident

    @property
    def objectNumber (self) -> int:
        """Número do elemento.

        Returns:
            Valor inteiro.
        """
        varident        = ctypes.c_void_p (self.m_ident)
        numelem         = 0
        varnumelem      = ctypes.c_int (numelem)
        self.m_model.m_eagme.BASME_IDENT_NUMELEM_LER (ctypes.byref (varident),
                            ctypes.byref (varnumelem))
        numelem         = varnumelem.value
        return          numelem

    @objectNumber.setter
    def objectNumber (self, numelem: int) -> None:
        """Atribui Número do elemento."""
        varident        = ctypes.c_void_p (self.m_ident)
        varnumelem      = ctypes.c_int (numelem)
        self.m_model.m_eagme.BASME_IDENT_NUMELEM_DEF (ctypes.byref (varident),
                            ctypes.byref (varnumelem))

    @property
    def objectTitle (self) -> str:
        """Título alfanumérico ou "" se não definido.

        Returns:
            Cadeia de caracteres.
        """
        varident        = ctypes.c_void_p (self.m_ident)
        vartitulo       = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_IDENT_TITULO_LER (ctypes.byref (varident),
                            vartitulo)
        titulo          = vartitulo.value.decode(TQSUtil.CHARSET)
        return         titulo

    @objectTitle.setter
    def objectTitle (self, titulo: str) -> None:
        """Atribui Título alfanumérico ou "" se não definido."""
        varident        = ctypes.c_void_p (self.m_ident)
        vartitulo       = ctypes.c_char_p (titulo.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_IDENT_TITULO_DEF (ctypes.byref (varident),
                            vartitulo)
    @property
    def textPosition (self) -> "TextPosition":
        """Operação ``textPosition``.

        Returns:
            :class:`TextPosition` correspondente.
        """
        varident        = ctypes.c_void_p (self.m_ident)
        postex          = None
        varpostex       = ctypes.c_void_p (postex)
        self.m_model.m_eagme.BASME_IDENT_POSTEX_LER (ctypes.byref (varident),
                            ctypes.byref (varpostex))
        postex          = varpostex.value
        textposition    = TextPosition (self.m_model, postex)
        return          textposition


    @property
    def renumerable (self) -> int:
        """Elemento renumeravel (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varident        = ctypes.c_void_p (self.m_ident)
        irenumeravel    = 0
        varirenumeravel = ctypes.c_int (irenumeravel)
        self.m_model.m_eagme.BASME_IDENT_IRENUMERAVEL_LER (ctypes.byref (varident),
                            ctypes.byref (varirenumeravel))
        irenumeravel    = varirenumeravel.value
        return          irenumeravel

    @renumerable.setter
    def renumerable (self, irenumeravel: int) -> None:
        """Atribui Elemento renumeravel (0) Não (1) Sim."""
        varident        = ctypes.c_void_p (self.m_ident)
        varirenumeravel = ctypes.c_int (irenumeravel)
        self.m_model.m_eagme.BASME_IDENT_IRENUMERAVEL_DEF (ctypes.byref (varident),
                            ctypes.byref (varirenumeravel))

#-----------------------------------------------------------------------------
#      Objeto de eixos automáticos - CEixAut
#
class AutoAxis ():

    """Geração automática de eixos rotulados.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", eixaut: int) -> None:
        """Classe p/geração automática de eixos.

        Args:
            model: Objeto Model() do modelo atual.
            eixaut: Apontador para objeto CEixAut.
        """
        self.m_model    = model
        self.m_eixaut   = eixaut

#-----------------------------------------------------------------------------
#       Mísula em viga - somente visual -  CMisVig
#
class VariableSection ():

    """Seção variável de pilar.

    Implementação:
        Seção variável de pilar (``CSecVar``). Property bag de geometria, materiais e
        interpolação entre seções; cada propriedade é um par LER/DEF em ``BASME_SECVAR_*``.
    """
    def __init__ (self, model: "Model", misvig: int) -> None:
        """Classe com dados de mísula/seção variável de viga.

        Args:
            model: Objeto Model() do modelo atual.
            misvig: Apontador para objeto CMisVig.
        """
        self.m_model    = model
        self.m_misvig   = misvig

    @property
    def corbelDefined (self) -> int:
        """Mísula definida (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        idefin          = 0
        varidefin       = ctypes.c_int (idefin)
        self.m_model.m_eagme.BASME_MISVIG_IDEFIN_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varidefin))
        idefin          = varidefin.value
        return          idefin

    @corbelDefined.setter
    def corbelDefined (self, idefin: int) -> None:
        """Atribui Mísula definida (0) Não (1) Sim."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varidefin       = ctypes.c_int (idefin)
        self.m_model.m_eagme.BASME_MISVIG_IDEFIN_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varidefin))

    @property
    def startBottomHeight (self) -> float:
        """Mísula: Altura inferior inicial cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        hinici          = 0.
        varhinici       = ctypes.c_double (hinici)
        self.m_model.m_eagme.BASME_MISVIG_HINICI_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varhinici))
        hinici          = varhinici.value
        return          hinici

    @startBottomHeight.setter
    def startBottomHeight (self, hinici: float) -> None:
        """Atribui Mísula: Altura inferior inicial cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varhinici       = ctypes.c_double (hinici)
        self.m_model.m_eagme.BASME_MISVIG_HINICI_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varhinici))

    @property
    def endBottomHeight (self) -> float:
        """Mísula: Altura inferior final cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        hfinal          = 0.
        varhfinal       = ctypes.c_double (hfinal)
        self.m_model.m_eagme.BASME_MISVIG_HFINAL_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varhfinal))
        hfinal          = varhfinal.value
        return          hfinal

    @endBottomHeight.setter
    def endBottomHeight (self, hfinal: float) -> None:
        """Atribui Mísula: Altura inferior final cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varhfinal       = ctypes.c_double (hfinal)
        self.m_model.m_eagme.BASME_MISVIG_HFINAL_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varhfinal))

    @property
    def startTopHeight (self) -> float:
        """Mísula: Altura superior inicial cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        hinicis         = 0.
        varhinicis      = ctypes.c_double (hinicis)
        self.m_model.m_eagme.BASME_MISVIG_HINICIS_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varhinicis))
        hinicis         = varhinicis.value
        return          hinicis

    @startTopHeight.setter
    def startTopHeight (self, hinicis: float) -> None:
        """Atribui Mísula: Altura superior inicial cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varhinicis      = ctypes.c_double (hinicis)
        self.m_model.m_eagme.BASME_MISVIG_HINICIS_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varhinicis))

    @property
    def endTopHeight (self) -> float:
        """Mísula: Altura superior final cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        hfinals         = 0.
        varhfinals      = ctypes.c_double (hfinals)
        self.m_model.m_eagme.BASME_MISVIG_HFINALS_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varhfinals))
        hfinals         = varhfinals.value
        return          hfinals

    @endTopHeight.setter
    def endTopHeight (self, hfinals: float) -> None:
        """Atribui Mísula: Altura superior final cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varhfinals      = ctypes.c_double (hfinals)
        self.m_model.m_eagme.BASME_MISVIG_HFINALS_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varhfinals))

    @property
    def startLeftWidth (self) -> float:
        """Mísula: Largura esquerda inicial cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        hinicie         = 0.
        varhinicie      = ctypes.c_double (hinicie)
        self.m_model.m_eagme.BASME_MISVIG_HINICIE_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varhinicie))
        hinicie         = varhinicie.value
        return          hinicie

    @startLeftWidth.setter
    def startLeftWidth (self, hinicie: float) -> None:
        """Atribui Mísula: Largura esquerda inicial cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varhinicie      = ctypes.c_double (hinicie)
        self.m_model.m_eagme.BASME_MISVIG_HINICIE_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varhinicie))

    @property
    def endLeftWidth (self) -> float:
        """Mísula: Largura esquerda final cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        hfinale         = 0.
        varhfinale      = ctypes.c_double (hfinale)
        self.m_model.m_eagme.BASME_MISVIG_HFINALE_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varhfinale))
        hfinale         = varhfinale.value
        return          hfinale

    @endLeftWidth.setter
    def endLeftWidth (self, hfinale: float) -> None:
        """Atribui Mísula: Largura esquerda final cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varhfinale      = ctypes.c_double (hfinale)
        self.m_model.m_eagme.BASME_MISVIG_HFINALE_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varhfinale))

    @property
    def startRightWidth (self) -> float:
        """Mísula: Largura direita inicial cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        hinicid         = 0.
        varhinicid      = ctypes.c_double (hinicid)
        self.m_model.m_eagme.BASME_MISVIG_HINICID_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varhinicid))
        hinicid         = varhinicid.value
        return          hinicid

    @startRightWidth.setter
    def startRightWidth (self, hinicid: float) -> None:
        """Atribui Mísula: Largura direita inicial cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varhinicid      = ctypes.c_double (hinicid)
        self.m_model.m_eagme.BASME_MISVIG_HINICID_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varhinicid))

    @property
    def endRightWidth (self) -> float:
        """Mísula: Largura direita final cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        hfinald         = 0.
        varhfinald      = ctypes.c_double (hfinald)
        self.m_model.m_eagme.BASME_MISVIG_HFINALD_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varhfinald))
        hfinald         = varhfinald.value
        return          hfinald

    @endRightWidth.setter
    def endRightWidth (self, hfinald: float) -> None:
        """Atribui Mísula: Largura direita final cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varhfinald      = ctypes.c_double (hfinald)
        self.m_model.m_eagme.BASME_MISVIG_HFINALD_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varhfinald))

    @property
    def variableSectionDefined (self) -> int:
        """Seção variável definida (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        isecvr          = 0
        varisecvr       = ctypes.c_int (isecvr)
        self.m_model.m_eagme.BASME_MISVIG_ISECVR_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varisecvr))
        isecvr          = varisecvr.value
        return          isecvr

    @variableSectionDefined.setter
    def variableSectionDefined (self, isecvr: int) -> None:
        """Atribui Seção variável definida (0) Não (1) Sim."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varisecvr       = ctypes.c_int (isecvr)
        self.m_model.m_eagme.BASME_MISVIG_ISECVR_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varisecvr))

    @property
    def startWidth (self) -> float:
        """Seção variável: Largura inicial cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        basini          = 0.
        varbasini       = ctypes.c_double (basini)
        self.m_model.m_eagme.BASME_MISVIG_BASINI_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varbasini))
        basini          = varbasini.value
        return          basini

    @startWidth.setter
    def startWidth (self, basini: float) -> None:
        """Atribui Seção variável: Largura inicial cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varbasini       = ctypes.c_double (basini)
        self.m_model.m_eagme.BASME_MISVIG_BASINI_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varbasini))

    @property
    def startHeight (self) -> float:
        """Seção variável: Altura inicial cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        altini          = 0.
        varaltini       = ctypes.c_double (altini)
        self.m_model.m_eagme.BASME_MISVIG_ALTINI_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varaltini))
        altini          = varaltini.value
        return          altini

    @startHeight.setter
    def startHeight (self, altini: float) -> None:
        """Atribui Seção variável: Altura inicial cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varaltini       = ctypes.c_double (altini)
        self.m_model.m_eagme.BASME_MISVIG_ALTINI_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varaltini))

    @property
    def startRecess (self) -> float:
        """Seção variável: Rebaixo inicial cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        dfsini          = 0.
        vardfsini       = ctypes.c_double (dfsini)
        self.m_model.m_eagme.BASME_MISVIG_DFSINI_LER (ctypes.byref (varmisvig),
                            ctypes.byref (vardfsini))
        dfsini          = vardfsini.value
        return          dfsini

    @startRecess.setter
    def startRecess (self, dfsini: float) -> None:
        """Atribui Seção variável: Rebaixo inicial cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        vardfsini       = ctypes.c_double (dfsini)
        self.m_model.m_eagme.BASME_MISVIG_DFSINI_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (vardfsini))

    @property
    def endWidth (self) -> float:
        """Seção variável: Largura final cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        basfin          = 0.
        varbasfin       = ctypes.c_double (basfin)
        self.m_model.m_eagme.BASME_MISVIG_BASFIN_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varbasfin))
        basfin          = varbasfin.value
        return          basfin

    @endWidth.setter
    def endWidth (self, basfin: float) -> None:
        """Atribui Seção variável: Largura final cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varbasfin       = ctypes.c_double (basfin)
        self.m_model.m_eagme.BASME_MISVIG_BASFIN_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varbasfin))

    @property
    def endHeight (self) -> float:
        """Seção variável: Altura final cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        altfin          = 0.
        varaltfin       = ctypes.c_double (altfin)
        self.m_model.m_eagme.BASME_MISVIG_ALTFIN_LER (ctypes.byref (varmisvig),
                            ctypes.byref (varaltfin))
        altfin          = varaltfin.value
        return          altfin

    @endHeight.setter
    def endHeight (self, altfin: float) -> None:
        """Atribui Seção variável: Altura final cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        varaltfin       = ctypes.c_double (altfin)
        self.m_model.m_eagme.BASME_MISVIG_ALTFIN_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (varaltfin))

    @property
    def endRecess (self) -> float:
        """Seção variável: Rebaixo final cm.

        Returns:
            Valor de ponto flutuante.
        """
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        dfsfin          = 0.
        vardfsfin       = ctypes.c_double (dfsfin)
        self.m_model.m_eagme.BASME_MISVIG_DFSFIN_LER (ctypes.byref (varmisvig),
                            ctypes.byref (vardfsfin))
        dfsfin          = vardfsfin.value
        return          dfsfin

    @endRecess.setter
    def endRecess (self, dfsfin: float) -> None:
        """Atribui Seção variável: Rebaixo final cm."""
        varmisvig       = ctypes.c_void_p (self.m_misvig)
        vardfsfin       = ctypes.c_double (dfsfin)
        self.m_model.m_eagme.BASME_MISVIG_DFSFIN_DEF (ctypes.byref (varmisvig),
                            ctypes.byref (vardfsfin))

#-----------------------------------------------------------------------------
#       Dados de vigas pré-moldadas - CPreVig
#
class BeamPrecastData ():

    """Dados de viga pré-moldada.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", previg: int) -> None:
        """Classe com dados de mísula/seção variável de viga.

        Args:
            model: Objeto Model() do modelo atual.
            previg: Apontador para objeto CPreVig.
        """
        self.m_model    = model
        self.m_previg   = previg

#-----------------------------------------------------------------------------
#       Dados de vigas - seção metálica - CMetVig
#
class BeamMetalSection ():

    """Seção metálica de viga.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", metvig: int) -> None:
        """Classe com dados de mísula/seção variável de viga.

        Args:
            model: Objeto Model() do modelo atual.
            metvig: Apontador para objeto CMetVig.
        """
        self.m_model    = model
        self.m_metvig   = metvig

#-----------------------------------------------------------------------------
#       Posição de texto editável - CPosTex
#
class TextPosition ():

    """Posicionamento de texto/rotulação.

    Implementação:
        Posicionamento textual de rotulações. ``_LerXy`` / ``_DefXy`` empacotam pares
        ``(x, y)`` em ``ctypes.c_double`` para cada índice de etiqueta.
    """
    def __init__ (self, model: "Model", postex: int) -> None:
        """Classe com dados de.

        Args:
            model: Objeto Model() do modelo atual.
            postex: Apontador para objeto CPosTex.
        """
        self.m_model    = model
        self.m_postex   = postex


    def _LerXy (self) -> Tuple[Any, Any]:
        """Operação ``_LerXy``.

        Returns:
            Tupla com os valores lidos.
        """
        varpostex       = ctypes.c_void_p(self.m_postex)
        varx            = ctypes.c_double(0.0)
        vary            = ctypes.c_double(0.0)
        self.m_model.m_eagme.BASME_POSTEX_COORD_LER (ctypes.byref(varpostex), \
                        ctypes.byref(varx), ctypes.byref(vary))
        x               = varx.value
        y               = vary.value
        return          x, y

    def _DefXy (self, x: float, y: float) -> None:
        """Operação ``_DefXy``.

        Args:
            x: Coordenada ``x`` em unidades de desenho.
            y: Coordenada ``y`` em unidades de desenho.
        """
        varpostex       = ctypes.c_void_p(self.m_postex)
        varx            = ctypes.c_double(x)
        vary            = ctypes.c_double(y)
        self.m_model.m_eagme.BASME_POSTEX_COORD_DEF (ctypes.byref(varpostex), \
                        ctypes.byref(varx), ctypes.byref(vary))

    @property
    def x (self) -> Any:
        """Ponto X de inserção do texto.

        Returns:
            Resultado da operação.
        """
        x, y            = self._LerXy ()
        return          x

    @x.setter
    def x (self, xr: Any) -> None:
        """Atribui Ponto X de inserção do texto."""
        x1, y1          = self._LerXy ()
        self._DefXy     (xr, y1)

    @property
    def y (self) -> Any:
        """Ponto Y de inserção do texto.

        Returns:
            Resultado da operação.
        """
        x, y            = self._LerXy ()
        return          y

    @y.setter
    def y (self, yr: Any) -> None:
        """Atribui Ponto Y de inserção do texto."""
        x1, y1          = self._LerXy ()
        self._DefXy     (x1, yr)

    @property
    def angle (self) -> Any:
        """Ângulo de rotação do texto.

        Returns:
            Resultado da operação.
        """
        varpostex       = ctypes.c_void_p (self.m_postex)
        varangle        = ctypes.c_double (0.0)
        self.m_model.m_eagme.BASME_POSTEX_ANG_LER (ctypes.byref(varpostex), ctypes.byref(varangle))
        ang             = varangle.value
        return          ang

    @angle.setter
    def angle (self, ang: float) -> None:
        """Atribui Ângulo de rotação do texto."""
        varpostex       = ctypes.c_void_p (self.m_postex)
        varangle        = ctypes.c_double (ang)
        self.m_model.m_eagme.BASME_POSTEX_ANG_DEF (ctypes.byref(varpostex),ctypes.byref(varangle))

    @property
    def height (self) -> Any:
        """Altura do texto.

        Returns:
            Resultado da operação.
        """
        varpostex       = ctypes.c_void_p (self.m_postex)
        varheight       = ctypes.c_double (0.0)
        self.m_model.m_eagme.BASME_POSTEX_HTEX_LER (ctypes.byref(varpostex), ctypes.byref(varheight))
        htex            = varheight.value
        return          htex

    @height.setter
    def height (self, htex: float) -> None:
        """Atribui Altura do texto."""
        varpostex       = ctypes.c_void_p (self.m_postex)
        varheight       = ctypes.c_double (htex)
        self.m_model.m_eagme.BASME_POSTEX_HTEX_DEF (ctypes.byref(varpostex),ctypes.byref(varheight))

    @property
    def modified (self) -> Any:
        """Status de texto modificado.

        Returns:
            Resultado da operação.
        """
        varpostex       = ctypes.c_void_p (self.m_postex)
        varimodif       = ctypes.c_int (0)
        self.m_model.m_eagme.BASME_POSTEX_IMODIF_LER (ctypes.byref(varpostex),ctypes.byref(varimodif))
        imodif          = varimodif.value
        return          imodif

    @modified.setter
    def modified (self, imodif: int) -> None:
        """Atribui Status de texto modificado."""
        varpostex       = ctypes.c_void_p (self.m_postex)
        varimodif       = ctypes.c_int (imodif)
        self.m_model.m_eagme.BASME_POSTEX_IMODIF_DEF (ctypes.byref(varpostex),ctypes.byref(varimodif))

#-----------------------------------------------------------------------------
#       Objeto de viga
#
class Beam (SMObject):

    """Viga do modelo estrutural.

    Implementação:
        Wrapper de viga (``CViga``). Expõe geometria, inserção, articulações e nós em
        sub-objetos via ``@property``; iteração de nós usa ``GetBeamNode`` percorrendo
        o array de nós ``CNoVig``.
    """
    def __init__ (self, model: "Model", viga: int) -> None:
        """Criação de uma viga.

        Args:
            model: Objeto Model() do modelo atual.
            viga: Objeto CVigas do Modelador.
        """
        self.m_model    = model
        self.m_viga     = viga
        super().__init__(model, self.m_viga)

    @property
    def beamIdent (self) -> "SMObjectIdent":
        """Identificação da viga.

        Returns:
            :class:`SMObjectIdent` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        identvig        = None
        varidentvig     = ctypes.c_void_p (identvig)
        self.m_model.m_eagme.BASME_VIGAS_IDENTVIG_LER (ctypes.byref (varviga),
                            ctypes.byref (varidentvig))
        identvig        = varidentvig.value
        beamident       = SMObjectIdent (self.m_model, identvig)
        return          beamident

    def NumNodes (self) -> int:
        """Número de nós de uma viga (objetos BeamNode).

        Returns:
            Valor inteiro.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        numnos          = 0
        varnumnos       = ctypes.c_int (numnos)
        self.m_model.m_eagme.BASME_VIGAS_NOVIG_NUMNOS (ctypes.byref (varviga),
                            ctypes.byref (varnumnos))
        numnos          = varnumnos.value
        return          numnos


    def GetBeamNode (self, ino: int) -> "BeamNode":
        """Retorna beam node.

        Args:
            ino: Parâmetro ``ino``.

        Returns:
            :class:`BeamNode` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        varino          = ctypes.c_int (ino)
        novig           = None
        varnovig        = ctypes.c_void_p (novig)
        self.m_model.m_eagme.BASME_VIGAS_NOVIG_LER (ctypes.byref (varviga),
                            ctypes.byref (varino), ctypes.byref (varnovig))
        novig           = varnovig.value
        return          BeamNode (self.m_model, novig)

    def GetUserNodes (self) -> "Polygon":
        """Retorna user nodes.

        Returns:
            :class:`Polygon` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        polig           = None
        varpolig        = ctypes.c_void_p (polig)
        self.m_model.m_eagme.BASME_VIGAS_NOSORIG_LER (ctypes.byref (varviga), ctypes.byref (varpolig))
        polig           = varpolig.value
        polygon         = Polygon (self.m_model, polig)
        return          polygon

    def GetBeamGeometry (self) -> "BeamGeometry":
        """Geometria de viga - válida nos trechos sem definição específica (SetSegmentBeamGeometryDefined).

        Returns:
            :class:`BeamGeometry` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        geovig          = None
        vargeovig       = ctypes.c_void_p (geovig)
        self.m_model.m_eagme.BASME_VIGAS_GEOVIG_GERAL_LER (ctypes.byref (varviga),
                            ctypes.byref (vargeovig))
        geovig          = vargeovig.value
        beamgeometry    = BeamGeometry (self.m_model, geovig)
        return          beamgeometry

    def GetSegmentBeamGeometry (self, ino: int) -> "BeamGeometry":
        """Geometria de viga - do trecho ou geral (conforme SetSegmentBeamGeometryDefined).

        Args:
            ino: Parâmetro ``ino``.

        Returns:
            :class:`BeamGeometry` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        varino          = ctypes.c_int (ino)
        geovig          = None
        vargeovig       = ctypes.c_void_p (geovig)
        self.m_model.m_eagme.BASME_VIGAS_GEOVIG_TRECHO_LER (ctypes.byref (varviga),
                            ctypes.byref (varino), ctypes.byref (vargeovig))
        geovig          = vargeovig.value
        beamgeometry    = BeamGeometry (self.m_model, geovig)
        return          beamgeometry

    def GetSegmentBeamGeometryDefined (self, ino: int) -> int:
        """Retorna segment beam geometry defined.

        Args:
            ino: Parâmetro ``ino``.

        Returns:
            Valor inteiro.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        varino          = ctypes.c_int (ino)
        idefgeovig      = 0
        varidefgeovig   = ctypes.c_int (idefgeovig)
        self.m_model.m_eagme.BASME_VIGAS_IDEFGEOVIG_LER (ctypes.byref (varviga),
                            ctypes.byref (varino), ctypes.byref (varidefgeovig))
        idefgeovig       = varidefgeovig.value
        return          idefgeovig

    def SetSegmentBeamGeometryDefined (self, ino: int, idefgeovig: int) -> None:
        """Define (1) se a geometria do trecho ino é específica ou (0) se é geral.

        Args:
            ino: Parâmetro ``ino``.
            idefgeovig: Parâmetro ``idefgeovig``.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        varino          = ctypes.c_int (ino)
        varidefgeovig   = ctypes.c_int (idefgeovig)
        self.m_model.m_eagme.BASME_VIGAS_IDEFGEOVIG_DEF (ctypes.byref (varviga),
                            ctypes.byref (varino), ctypes.byref (varidefgeovig))

    def GetBeamInertia (self) -> "BeamInertia":
        """Inércia de viga - válida nos trechos sem definição específica (SetSegmentBeamInertiaDefined).

        Returns:
            :class:`BeamInertia` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        inervig         = None
        varinervig      = ctypes.c_void_p (inervig)
        self.m_model.m_eagme.BASME_VIGAS_INERVIG_GERAL_LER (ctypes.byref (varviga),
                            ctypes.byref (varinervig))
        inervig         = varinervig.value
        beaminertia     = BeamInertia (self.m_model, inervig)
        return          beaminertia

    def GetSegmentBeamInertia (self, ino: int) -> "BeamInertia":
        """Inércia de viga - Do trecho ou geral, conforme SetSegmentBeamInertiaDefined.

        Args:
            ino: Parâmetro ``ino``.

        Returns:
            :class:`BeamInertia` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        varino          = ctypes.c_int (ino)
        inervig         = None
        varinervig      = ctypes.c_void_p (inervig)
        self.m_model.m_eagme.BASME_VIGAS_INERVIG_TRECHO_LER (ctypes.byref (varviga),
                            ctypes.byref (varino), ctypes.byref (varinervig))
        inervig         = varinervig.value
        beaminertia     = BeamInertia (self.m_model, inervig)
        return          beaminertia

    def GetSegmentBeamInertiaDefined (self, ino: int) -> Any:
        """Retorna segment beam inertia defined.

        Args:
            ino: Parâmetro ``ino``.

        Returns:
            Resultado da operação.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        varino          = ctypes.c_int (ino)
        idefinervig     = 0
        varidefinervig  = ctypes.c_int (idefinervig)
        self.m_model.m_eagme.BASME_VIGAS_IDEFINERVIG_LER (ctypes.byref (varviga),
                            ctypes.byref (varino), ctypes.byref (varidefinervig))
        varidefinervig  = varidefinervig.value
        return          varidefinervig

    def SetSegmentBeamInertiaDefined (self, ino: int, idefinervig: int) -> None:
        """Define (1) se a inércia do trecho ino é específica ou (0) se é geral.

        Args:
            ino: Parâmetro ``ino``.
            idefinervig: Parâmetro ``idefinervig``.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        varino          = ctypes.c_int (ino)
        varidefinervig  = ctypes.c_int (idefinervig)
        self.m_model.m_eagme.BASME_VIGAS_IDEFINERVIG_DEF (ctypes.byref (varviga),
                            ctypes.byref (varino), ctypes.byref (varidefinervig))

    @property
    def beamBond (self) -> "BeamBond":
        """Vinculações e outros dados de viga.

        Returns:
            :class:`BeamBond` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        vincvig         = None
        varvincvig      = ctypes.c_void_p (vincvig)
        self.m_model.m_eagme.BASME_VIGAS_VINCVIG_LER (ctypes.byref (varviga),
                            ctypes.byref (varvincvig))
        vincvig         = varvincvig.value
        beambond        = BeamBond (self.m_model, vincvig)
        return          beambond

    @property
    def beamInsertion (self) -> "BeamInsertion":
        """Dados de inserção de vigas.

        ATENÇÃO: esta leitura chama ``BASME_VIGAS_VINCVIG_LER``, a entrada nativa
        de vínculo usada pela propriedade ``beamBond``, em vez da entrada de
        inserção. O ponteiro devolvido é um ``CVincVig`` embrulhado como
        :class:`BeamInsertion`, portanto os acessos seguintes operam sobre o tipo
        errado. Para dados de inserção confiáveis use a propriedade equivalente
        em :class:`FloorBeamData` (que chama ``BASME_DADPAV_INSVIG_LER``).

        Returns:
            :class:`BeamInsertion` — ver ATENÇÃO.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        insvig          = None
        varinsvig       = ctypes.c_void_p (insvig)
        self.m_model.m_eagme.BASME_VIGAS_VINCVIG_LER (ctypes.byref (varviga),
                            ctypes.byref (varinsvig))
        insvig          = varinsvig.value
        beaminsertion   = BeamInsertion (self.m_model, insvig)
        return          beaminsertion

    def GetLoad (self, floor: "Floor") -> "Load":
        """floor.

        Args:
            floor: Objeto Floor, com dados da planta atual.

        Returns:
            floor       <- Objeto Floor, com dados da planta atual.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_VIGAS_CARGAVIG_LER (ctypes.byref (varviga),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, floor, carga)
        return          loadx

    @property
    def temperShrink (self) -> "TemperatureShrink":
        """Temperatura / retração de vigas.

        Returns:
            :class:`TemperatureShrink` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        tempretvig      = None
        vartempretvig   = ctypes.c_void_p (tempretvig)
        self.m_model.m_eagme.BASME_VIGAS_TEMPRET_LER (ctypes.byref (varviga),
                            ctypes.byref (vartempretvig))
        tempretvig      = vartempretvig.value
        tempershrink    = TemperatureShrink (self.m_model, tempretvig)
        return          tempershrink

    @property
    def beamDetailing (self) -> "BeamDetailing":
        """Detalhamento de vigas.

        ATENÇÃO: esta leitura chama ``BASME_VIGAS_TEMPRET_LER``, a entrada nativa
        de temperatura/retração, em vez da entrada de detalhamento. O ponteiro
        devolvido é embrulhado como :class:`BeamDetailing`, portanto os acessos
        seguintes operam sobre o tipo errado. Para detalhamento confiável use a
        propriedade equivalente em :class:`FloorBeamData` (que chama
        ``BASME_DADPAV_DETVIG_LER``).

        Returns:
            :class:`BeamDetailing` — ver ATENÇÃO.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        detvig          = None
        vardetvig       = ctypes.c_void_p (detvig)
        self.m_model.m_eagme.BASME_VIGAS_TEMPRET_LER (ctypes.byref (varviga),
                            ctypes.byref (vardetvig))
        detvig          = vardetvig.value
        beamdetailing   = BeamDetailing (self.m_model, detvig)
        return          beamdetailing


    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_VIGAS_IPISOAUX_LER (ctypes.byref (varviga),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varviga         = ctypes.c_void_p (self.m_viga)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_VIGAS_IPISOAUX_DEF (ctypes.byref (varviga),
                            ctypes.byref (varipisoaux))

    @property
    def userAttrib (self) -> "UserAttrib":
        """Atributos de usuário.

        Returns:
            :class:`UserAttrib` correspondente.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        usratrib        = None
        varusratrib     = ctypes.c_void_p (usratrib)
        self.m_model.m_eagme.BASME_VIGAS_USRATRIB_LER (ctypes.byref (varviga),
                            ctypes.byref (varusratrib))
        usratrib        = varusratrib.value
        userattrib      = UserAttrib (self.m_model, usratrib)
        return          userattrib

    @property
    def beamExport (self) -> int:
        """(1) Se viga exportável para o 3D/BIM.

        Returns:
            Valor inteiro.
        """
        varviga         = ctypes.c_void_p (self.m_viga)
        iexportavel     = 0
        variexportavel  = ctypes.c_int (iexportavel)
        self.m_model.m_eagme.BASME_VIGAS_IEXPORTAVEL_LER (ctypes.byref (varviga),
                            ctypes.byref (variexportavel))
        iexportavel     = variexportavel.value
        return          iexportavel

    @beamExport.setter
    def beamExport (self, iexportavel: int) -> None:
        """Atribui (1) Se viga exportável para o 3D/BIM."""
        varviga         = ctypes.c_void_p (self.m_viga)
        variexportavel  = ctypes.c_int (iexportavel)
        self.m_model.m_eagme.BASME_VIGAS_IEXPORTAVEL_DEF (ctypes.byref (varviga),
                            ctypes.byref (variexportavel))

#-----------------------------------------------------------------------------
#       Nó de viga - Objeto CNoVig com dados de um nó/trecho de viga
#
class BeamNode ():

    """Nó de viga.

    Implementação:
        Representa um nó de viga (``CNoVig``). Métodos lêem/escrevem articulações,
        vinculação com laje e restrições no nó via ``BASME_NOVIG_*``.
    """
    def __init__ (self, model: "Model", novig: int) -> None:
        """Classe com dados de mísula/seção variável de viga.

        Args:
            model: Objeto Model() do modelo atual.
            novig: Apontador para objeto CNoVig.
        """
        self.m_model    = model
        self.m_novig    = novig

    @property
    def nodeX (self) -> float:
        """X do nó da viga.

        Returns:
            Valor de ponto flutuante.
        """
        varnovig        = ctypes.c_void_p (self.m_novig)
        xno             = 0.
        varxno          = ctypes.c_double (xno)
        self.m_model.m_eagme.BASME_NOVIG_XYNO_LERX (ctypes.byref (varnovig),
                            ctypes.byref (varxno))
        xno             = varxno.value
        return          xno

    @nodeX.setter
    def nodeX (self, xno: float) -> None:
        """Atribui X do nó da viga."""
        varnovig        = ctypes.c_void_p (self.m_novig)
        varxno          = ctypes.c_double (xno)
        self.m_model.m_eagme.BASME_NOVIG_XYNO_DEFX (ctypes.byref (varnovig),
                            ctypes.byref (varxno))

    @property
    def nodeY (self) -> float:
        """Y do nó da viga.

        Returns:
            Valor de ponto flutuante.
        """
        varnovig        = ctypes.c_void_p (self.m_novig)
        yno             = 0.
        varyno          = ctypes.c_double (yno)
        self.m_model.m_eagme.BASME_NOVIG_XYNO_LERY (ctypes.byref (varnovig),
                            ctypes.byref (varyno))
        yno             = varyno.value
        return          yno

    @nodeY.setter
    def nodeY (self, yno: float) -> None:
        """Atribui Y do nó da viga."""
        varnovig        = ctypes.c_void_p (self.m_novig)
        varyno          = ctypes.c_double (yno)
        self.m_model.m_eagme.BASME_NOVIG_XYNO_DEFY (ctypes.byref (varnovig),
                            ctypes.byref (varyno))

    @property
    def crossingType (self) -> int:
        """Tipo de vinculação do nó da viga BEAMCROSSING_xxxx.

        Returns:
            Valor inteiro.
        """
        varnovig        = ctypes.c_void_p (self.m_novig)
        ivinc           = 0
        varivinc        = ctypes.c_int (ivinc)
        self.m_model.m_eagme.BASME_NOVIG_IVINC_LER (ctypes.byref (varnovig),
                            ctypes.byref (varivinc))
        ivinc           = varivinc.value
        return          ivinc

    @crossingType.setter
    def crossingType (self, ivinc: int) -> None:
        """Atribui Tipo de vinculação do nó da viga BEAMCROSSING_xxxx."""
        varnovig        = ctypes.c_void_p (self.m_novig)
        varivinc        = ctypes.c_int (ivinc)
        self.m_model.m_eagme.BASME_NOVIG_IVINC_DEF (ctypes.byref (varnovig),
                            ctypes.byref (varivinc))

    def GetSlabConnection (self, idireito: int) -> Tuple[int, float]:
        """int    idireito.

        Args:
            idireito: Parâmetro ``idireito``.

        Returns:
            int    idireito     <- (0) Esquerdo (1) Direito.
        """
        varnovig        = ctypes.c_void_p (self.m_novig)
        varidireito     = ctypes.c_int (idireito)
        iengast         = 0
        variengast      = ctypes.c_int (iengast)
        fatengast	= 0.
        varfatengast    = ctypes.c_double (fatengast)
        self.m_model.m_eagme.BASME_NOVIG_IENGAST_LER (ctypes.byref (varnovig),
                            ctypes.byref (varidireito), ctypes.byref (variengast),
                            ctypes.byref (varfatengast))
        iengast         = variengast.value
        fatengast       = varfatengast.value
        return          iengast, fatengast

    def SetSlabConnection (self, idireito: int, iengast: int, fatengast: float) -> None:
        """Define engastamento de um lado da viga com a laje.

        Args:
            idireito: Parâmetro ``idireito``.
            iengast: Parâmetro ``iengast``.
            fatengast: Parâmetro ``fatengast``.
        """
        varnovig        = ctypes.c_void_p (self.m_novig)
        varidireito     = ctypes.c_int (idireito)
        variengast      = ctypes.c_int (iengast)
        varfatengast    = ctypes.c_double (fatengast)
        self.m_model.m_eagme.BASME_NOVIG_IENGAST_DEF (ctypes.byref (varnovig),
                            ctypes.byref (varidireito), ctypes.byref (variengast),
                            ctypes.byref (varfatengast))

    def GetRestraint (self, ifinal: int) -> "BeamRestraint":
        """int ifinal.

        Args:
            ifinal: Parâmetro ``ifinal``.

        Returns:
            int ifinal          <- (0) Inicial (1) Final.
        """
        varnovig        = ctypes.c_void_p (self.m_novig)
        varifinal       = ctypes.c_int (ifinal)
        artic           = None
        varartic        = ctypes.c_void_p (artic)
        self.m_model.m_eagme.BASME_NOVIG_ARTIC_LER (ctypes.byref (varnovig),
                            ctypes.byref (varifinal), ctypes.byref (varartic))
        artic           = varartic.value
        beamRestraint   = BeamRestraint (self.m_model, artic)
        return          beamRestraint

    @property
    def arcSegment (self) -> "ArcSegment":
        """Operação ``arcSegment``.

        Returns:
            :class:`ArcSegment` correspondente.
        """
        varnovig        = ctypes.c_void_p (self.m_novig)
        novigarco       = None
        varnovigarco    = ctypes.c_void_p (novigarco)
        self.m_model.m_eagme.BASME_NOVIG_ARCO_LER (ctypes.byref (varnovig),
                            ctypes.byref (varnovigarco))
        novigarco       = varnovigarco.value
        arcsegment      = ArcSegment (self.m_model, novigarco)
        return          arcsegment

#------------------------------------------------------------------------------
#       Articulação de vigas CArtic
#
class BeamRestraint ():

    """Articulação/vinculação de viga.

    Implementação:
        Wrapper de articulação de viga (``CArtic``). Métodos por par de eixo manipulam
        coeficientes elásticos e momentos plásticos (``GetRestraintCoef``, ``GetPlasticMoments``).
    """
    def __init__ (self, model: "Model", artic: int) -> None:
        """Classe que define articulação de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            artic: Apontador para objeto CArtic.
        """
        self.m_model    = model
        self.m_artic    = artic

    def GetRestraintCoef (self, irdir: int) -> Tuple[int, float]:
        """Coeficientes de articulação na extremidade da viga.

        ATENÇÃO: na biblioteca TQS o primeiro valor retornado é lido de
        ``varartic`` (o ponteiro nativo ``CArtic``) em vez de ``variartic``, onde
        a DLL grava o indicador. O primeiro elemento da tupla é portanto um
        endereço grande (ou ``None``), nunca o ``0``/``1`` documentado. Use
        apenas o segundo elemento (``coef``); o indicador de articulação não é
        legível por este método.

        Args:
            irdir: Parâmetro ``irdir``.

        Returns:
            int iartic  -> Na prática o ponteiro nativo — ver ATENÇÃO.
        """
        varartic        = ctypes.c_void_p (self.m_artic)
        varirdir        = ctypes.c_int (irdir)
        iartic          = 0
        variartic       = ctypes.c_int (iartic)
        coef            = 0.
        varcoef         = ctypes.c_double (coef)
        self.m_model.m_eagme.BASME_ARTIC_COEFART_LER (ctypes.byref (varartic),
                        ctypes.byref (varirdir), ctypes.byref (variartic),
                        ctypes.byref (varcoef))
        iartic          = varartic.value
        coef            = varcoef.value
        return          iartic, coef

    def SetRestraint (self, irdir: int, iartic: int, coef: float) -> None:
        """Coeficientes de articulação na extremidade da viga.

        Args:
            irdir: Parâmetro ``irdir``.
            iartic: Parâmetro ``iartic``.
            coef: Parâmetro ``coef``.
        """
        varartic        = ctypes.c_void_p (self.m_artic)
        varirdir        = ctypes.c_int (irdir)
        variartic       = ctypes.c_int (iartic)
        varcoef         = ctypes.c_double (coef)
        self.m_model.m_eagme.BASME_ARTIC_COEFART_DEF (ctypes.byref (varartic),
                        ctypes.byref (varirdir), ctypes.byref (variartic),
                        ctypes.byref (varcoef))

    def GetPlasticMoments (self, itipopl: int, imompos: int) -> Tuple[int, float]:
        """Coeficientes de plastificação impostos.

        Valor máximo de momento fletor em uma ligação

        Args:
            itipopl: Constante do tipo de objeto/elemento.
            imompos: Parâmetro ``imompos``.

        Returns:
            int isfmax    -> (0) Conforme critérios (1) Não definido (2) em esfmax.
        """
        varartic        = ctypes.c_void_p (self.m_artic)
        varitipopl      = ctypes.c_int (itipopl)
        varimompos      = ctypes.c_int (imompos)
        isfmax          = 0
        varisfmax       = ctypes.c_int (isfmax)
        esfmax          = 0.
        varesfmax       = ctypes.c_double (esfmax)
        self.m_model.m_eagme.BASME_ARTIC_MOMPLAST_LER (ctypes.byref (varartic),
                        ctypes.byref (varitipopl), ctypes.byref (varimompos),
                        ctypes.byref (varisfmax), ctypes.byref (varesfmax))
        isfmax          = varisfmax.value
        esfmax          = varesfmax.value
        return          isfmax, esfmax

    def SetPlasticMoments (self, itipopl: int, imompos: int, isfmax: int, esfmax: float) -> None:
        """Coeficientes de plastificação impostos.

        Valor máximo de momento fletor em uma ligação

        Args:
            itipopl: Constante do tipo de objeto/elemento.
            imompos: Parâmetro ``imompos``.
            isfmax: Parâmetro ``isfmax``.
            esfmax: Parâmetro ``esfmax``.
        """
        varartic        = ctypes.c_void_p (self.m_artic)
        varitipopl      = ctypes.c_int (itipopl)
        varimompos      = ctypes.c_int (imompos)
        varisfmax       = ctypes.c_int (isfmax)
        varesfmax       = ctypes.c_double (esfmax)
        self.m_model.m_eagme.BASME_ARTIC_MOMPLAST_DEF (ctypes.byref (varartic),
                        ctypes.byref (varitipopl), ctypes.byref (varimompos),
                        ctypes.byref (varisfmax), ctypes.byref (varesfmax))

#------------------------------------------------------------------------------
#       Dados de um trecho de viga em arco CNoVigArco
#
class ArcSegment ():

    """Segmento de arco em poligonal.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", novigarco: int) -> None:
        """Classe que define articulação de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            novigarco: Apontador para objeto CNoVigArco.
        """
        self.m_model    = model
        self.m_novigarco= novigarco

    @property
    def startNode (self) -> int:
        """Nó inicial da viga 0..NumNodes()-1.

        Returns:
            Valor inteiro.
        """
        varnovigarco    = ctypes.c_void_p (self.m_novigarco)
        inoini          = 0
        varinoini       = ctypes.c_int (inoini)
        self.m_model.m_eagme.BASME_NOVIGARCO_INOINI_LER (ctypes.byref (varnovigarco),
                            ctypes.byref (varinoini))
        inoini          = varinoini.value
        return          inoini

    @startNode.setter
    def startNode (self, inoini: int) -> None:
        """Atribui Nó inicial da viga 0..NumNodes()-1."""
        varnovigarco        = ctypes.c_void_p (self.m_novigarco)
        varinoini        = ctypes.c_int (inoini)
        self.m_model.m_eagme.BASME_NOVIGARCO_INOINI_DEF (ctypes.byref (varnovigarco),
                            ctypes.byref (varinoini))

    @property
    def endNode (self) -> int:
        """Nó final da viga 0..NumNodes()-1.

        Returns:
            Valor inteiro.
        """
        varnovigarco    = ctypes.c_void_p (self.m_novigarco)
        inofin          = 0
        varinofin       = ctypes.c_int (inofin)
        self.m_model.m_eagme.BASME_NOVIGARCO_INOFIN_LER (ctypes.byref (varnovigarco),
                            ctypes.byref (varinofin))
        inofin          = varinofin.value
        return          inofin

    @endNode.setter
    def endNode (self, inofin: int) -> None:
        """Atribui Nó final da viga 0..NumNodes()-1."""
        varnovigarco        = ctypes.c_void_p (self.m_novigarco)
        varinofin        = ctypes.c_int (inofin)
        self.m_model.m_eagme.BASME_NOVIGARCO_INOFIN_DEF (ctypes.byref (varnovigarco),
                            ctypes.byref (varinofin))

    @property
    def signal (self) -> int:
        """Sinal do arco (1) anti-horário (-1) horário.

        Returns:
            Valor inteiro.
        """
        varnovigarco    = ctypes.c_void_p (self.m_novigarco)
        isinal          = 0
        varisinal       = ctypes.c_int (isinal)
        self.m_model.m_eagme.BASME_NOVIGARCO_ISINAL_LER (ctypes.byref (varnovigarco),
                            ctypes.byref (varisinal))
        isinal          = varisinal.value
        return          isinal

    @signal.setter
    def signal (self, isinal: int) -> None:
        """Atribui Sinal do arco (1) anti-horário (-1) horário."""
        varnovigarco        = ctypes.c_void_p (self.m_novigarco)
        varisinal        = ctypes.c_int (isinal)
        self.m_model.m_eagme.BASME_NOVIGARCO_ISINAL_DEF (ctypes.byref (varnovigarco),
                            ctypes.byref (varisinal))

    @property
    def centerX (self) -> float:
        """X do centro do arco cm.

        Returns:
            Valor de ponto flutuante.
        """
        varnovigarco    = ctypes.c_void_p (self.m_novigarco)
        xc              = 0
        varxc           = ctypes.c_double (xc)
        self.m_model.m_eagme.BASME_NOVIGARCO_XC_LER (ctypes.byref (varnovigarco),
                            ctypes.byref (varxc))
        xc              = varxc.value
        return          xc

    @centerX.setter
    def centerX (self, xc: float) -> None:
        """Atribui X do centro do arco cm."""
        varnovigarco    = ctypes.c_void_p (self.m_novigarco)
        varxc           = ctypes.c_double (xc)
        self.m_model.m_eagme.BASME_NOVIGARCO_XC_DEF (ctypes.byref (varnovigarco),
                            ctypes.byref (varxc))

    @property
    def centerY (self) -> float:
        """Y do centro do arco cm.

        Returns:
            Valor de ponto flutuante.
        """
        varnovigarco    = ctypes.c_void_p (self.m_novigarco)
        yc              = 0
        varyc           = ctypes.c_double (yc)
        self.m_model.m_eagme.BASME_NOVIGARCO_YC_LER (ctypes.byref (varnovigarco),
                            ctypes.byref (varyc))
        yc              = varyc.value
        return          yc

    @centerY.setter
    def centerY (self, yc: float) -> None:
        """Atribui Y do centro do arco cm."""
        varnovigarco    = ctypes.c_void_p (self.m_novigarco)
        varyc           = ctypes.c_double (yc)
        self.m_model.m_eagme.BASME_NOVIGARCO_YC_DEF (ctypes.byref (varnovigarco),
                            ctypes.byref (varyc))

#------------------------------------------------------------------------------
#       Objeto de contorno auxiliar de laje - bordo livre - CCtrAux
#
class SlabContour (SMObject):

    """Contorno auxiliar de laje (bordo livre).

    Implementação:
        Contorno auxiliar de laje (bordo livre). Metodos ``_GetX`` / ``_GetY`` indexam
        coordenadas dos vértices, e ``_SetX`` / ``_SetY`` mutam o ``CCtrAux`` subjacente.
    """
    def __init__ (self, model: "Model", ctraux: int) -> None:
        """Classe que define articulação de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            ctraux: Apontador para objeto CCtrAux.
        """
        self.m_model    = model
        self.m_ctraux   = ctraux
        super().__init__(model, self.m_ctraux)

    def _GetX (self, ifinal: int) -> float:
        """Retorna x.

        Args:
            ifinal: Parâmetro ``ifinal``.

        Returns:
            Valor de ponto flutuante.
        """
        varctraux       = ctypes.c_void_p (self.m_ctraux)
        varifinal       = ctypes.c_int (ifinal)
        xctr            = 0
        varxctr         = ctypes.c_double (xctr)
        self.m_model.m_eagme.BASME_CTRAUX_PT_LERX (ctypes.byref (varctraux),
                            ctypes.byref (varifinal), ctypes.byref (varxctr))
        xctr            = varxctr.value
        return          xctr

    def _SetX (self, ifinal: int, xctr: float) -> None:
        """Define x.

        Args:
            ifinal: Parâmetro ``ifinal``.
            xctr: Parâmetro ``xctr``.
        """
        varctraux       = ctypes.c_void_p (self.m_ctraux)
        varifinal       = ctypes.c_int (ifinal)
        varxctr         = ctypes.c_double (xctr)
        self.m_model.m_eagme.BASME_CTRAUX_PT_DEFX (ctypes.byref (varctraux),
                            ctypes.byref (varifinal), ctypes.byref (varxctr))

    def _GetY (self, ifinal: int) -> float:
        """Retorna y.

        Args:
            ifinal: Parâmetro ``ifinal``.

        Returns:
            Valor de ponto flutuante.
        """
        varctraux       = ctypes.c_void_p (self.m_ctraux)
        varifinal       = ctypes.c_int (ifinal)
        yctr            = 0
        varyctr         = ctypes.c_double (yctr)
        self.m_model.m_eagme.BASME_CTRAUX_PT_LERY (ctypes.byref (varctraux),
                            ctypes.byref (varifinal), ctypes.byref (varyctr))
        yctr            = varyctr.value
        return          yctr

    def _SetY (self, ifinal: int, yctr: float) -> None:
        """Define y.

        Args:
            ifinal: Parâmetro ``ifinal``.
            yctr: Parâmetro ``yctr``.
        """
        varctraux       = ctypes.c_void_p (self.m_ctraux)
        varifinal       = ctypes.c_int (ifinal)
        varyctr         = ctypes.c_double (yctr)
        self.m_model.m_eagme.BASME_CTRAUX_PT_DEFY (ctypes.byref (varctraux),
                            ctypes.byref (varifinal), ctypes.byref (varyctr))

    @property
    def startX (self) -> Any:
        """X inicial cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetX (0)

    @startX.setter
    def startX (self, xctr: Any) -> None:
        """Atribui X inicial cm."""
        self._SetX (0, xctr)

    @property
    def startY (self) -> Any:
        """Y inicial cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetY (0)

    @startY.setter
    def startY (self, xctr: Any) -> None:
        """Atribui Y inicial cm."""
        self._SetY (0, xctr)

    @property
    def endX (self) -> Any:
        """X final cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetX (1)

    @endX.setter
    def endX (self, xctr: Any) -> None:
        """Atribui X final cm."""
        self._SetX (1, xctr)

    @property
    def endY (self) -> Any:
        """Y final cm.

        Returns:
            Resultado da operação.
        """
        return          self._GetY (1)

    @endY.setter
    def endY (self, xctr: Any) -> None:
        """Atribui Y final cm."""
        self._SetY (1, xctr)

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varctraux       = ctypes.c_void_p (self.m_ctraux)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CTRAUX_IPISOAUX_LER (ctypes.byref (varctraux),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varctraux       = ctypes.c_void_p (self.m_ctraux)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CTRAUX_IPISOAUX_DEF (ctypes.byref (varctraux),
                            ctypes.byref (varipisoaux))

#------------------------------------------------------------------------------
#       Objeto de laje - CLajes
#
class Slab (SMObject):

    """Laje do modelo estrutural.

    Implementação:
        Wrapper de laje (``CLaje``). Compõe sub-objetos de geometria, malha e
        detalhamento; carga distribuída é exposta como objeto separado em ``GetLoad``.
    """
    def __init__ (self, model: "Model", laje: int) -> None:
        """Classe que define articulação de vigas.

        Args:
            model: Objeto Model() do modelo atual.
            laje: Apontador para objeto CLajes.
        """
        self.m_model    = model
        self.m_laje     = laje
        super().__init__(model, self.m_laje)

    @property
    def slabIdent (self) -> "SMObjectIdent":
        """Identificação da laje.

        Returns:
            :class:`SMObjectIdent` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        identlaj        = None
        varidentlaj     = ctypes.c_void_p (identlaj)
        self.m_model.m_eagme.BASME_LAJES_IDENTLAJ_LER (ctypes.byref (varlaje),
                            ctypes.byref (varidentlaj))
        identlaj        = varidentlaj.value
        slabident       = SMObjectIdent (self.m_model, identlaj)
        return          slabident

    def GetLoad (self, floor: "Floor") -> "Load":
        """Carga distribuída em toda a laje tf/m2.

        Args:
            floor: Planta corrente (:class:`Floor`).

        Returns:
            :class:`Load` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        cargalaj        = None
        varcargalaj     = ctypes.c_void_p (cargalaj)
        self.m_model.m_eagme.BASME_LAJES_CARGALAJ_LER (ctypes.byref (varlaje),
                            ctypes.byref (varcargalaj))
        cargalaj       = varcargalaj.value
        slabload        = Load (self.m_model, floor, cargalaj)
        return          slabload

    @property
    def slabGeometry (self) -> "SlabGeometry":
        """Dados de geometria de laje.

        Returns:
            :class:`SlabGeometry` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        geolaj          = None
        vargeolaj       = ctypes.c_void_p (geolaj)
        self.m_model.m_eagme.BASME_LAJES_GEOLAJ_LER (ctypes.byref (varlaje),
                            ctypes.byref (vargeolaj))
        geolaj          = vargeolaj.value
        slabGeometry    = SlabGeometry (self.m_model, geolaj)
        return          slabGeometry

    @property
    def slabGrid (self) -> "SlabGrid":
        """Dados para discretização de laje por grelha.

        Returns:
            :class:`SlabGrid` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        grelaj          = None
        vargrelaj       = ctypes.c_void_p (grelaj)
        self.m_model.m_eagme.BASME_LAJES_GRELAJ_LER (ctypes.byref (varlaje),
                            ctypes.byref (vargrelaj))
        grelaj          = vargrelaj.value
        slabGrid        = SlabGrid (self.m_model, grelaj)
        return          slabGrid

    @property
    def mainAngle (self) -> float:
        """Ângulo principal em graus.

        Returns:
            Valor de ponto flutuante.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        angpri          = 0.
        varangpri       = ctypes.c_double (angpri)
        self.m_model.m_eagme.BASME_LAJES_ANGPRI_LER (ctypes.byref (varlaje),
                            ctypes.byref (varangpri))
        angpri          = varangpri.value
        return          angpri

    @mainAngle.setter
    def mainAngle (self, angpri: float) -> None:
        """Atribui Ângulo principal em graus."""
        varlaje         = ctypes.c_void_p (self.m_laje)
        varangpri       = ctypes.c_double (angpri)
        self.m_model.m_eagme.BASME_LAJES_ANGPRI_DEF (ctypes.byref (varlaje),
                            ctypes.byref (varangpri))

    @property
    def slabTemperShrink (self) -> "TemperatureShrink":
        """Temperatura / retração de lajes.

        Returns:
            :class:`TemperatureShrink` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        tempretlaj      = None
        vartempretlaj   = ctypes.c_void_p (tempretlaj)
        self.m_model.m_eagme.BASME_LAJES_TEMPRET_LER (ctypes.byref (varlaje),
                            ctypes.byref (vartempretlaj))
        tempretlaj      = vartempretlaj.value
        slabTemperShrink= TemperatureShrink (self.m_model, tempretlaj)
        return          slabTemperShrink

    @property
    def slabDetailing (self) -> "SlabDetailing":
        """Detalhamento de lajes.

        Returns:
            :class:`SlabDetailing` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        detlaj          = None
        vardetlaj       = ctypes.c_void_p (detlaj)
        self.m_model.m_eagme.BASME_LAJES_DETLAJ_LER (ctypes.byref (varlaje),
                            ctypes.byref (vardetlaj))
        detlaj          = vardetlaj.value
        slabDetailing   = SlabDetailing (self.m_model, detlaj)
        return          slabDetailing

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_LAJES_IPISOAUX_LER (ctypes.byref (varlaje),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varlaje         = ctypes.c_void_p (self.m_laje)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_LAJES_IPISOAUX_DEF (ctypes.byref (varlaje),
                            ctypes.byref (varipisoaux))
    @property
    def isAStair (self) -> int:
        """Lance de escada (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        iescada         = 0
        variescada      = ctypes.c_int (iescada)
        self.m_model.m_eagme.BASME_LAJES_IESCADA_LER (ctypes.byref (varlaje),
                            ctypes.byref (variescada))
        iescada         = variescada.value
        return          iescada

    @isAStair.setter
    def isAStair (self, iescada: int) -> None:
        """Atribui Lance de escada (0) Não (1) Sim."""
        varlaje         = ctypes.c_void_p (self.m_laje)
        variescada      = ctypes.c_int (iescada)
        self.m_model.m_eagme.BASME_LAJES_IESCADA_DEF (ctypes.byref (varlaje),
                            ctypes.byref (variescada))

    @property
    def stairCase (self) -> "StairCase":
        """Dados de escada - Objeto StairCase().

        Returns:
            :class:`StairCase` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        escdad          = None
        varescdad       = ctypes.c_void_p (escdad)
        self.m_model.m_eagme.BASME_LAJES_ESCADA_LER (ctypes.byref (varlaje),
                            ctypes.byref (varescdad))
        escdad          = varescdad.value
        stairCase       = StairCase (self.m_model, escdad)
        return          stairCase

    @property
    def isALanding (self) -> int:
        """Patamar de escada (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        ipatamar        = 0
        varipatamar     = ctypes.c_int (ipatamar)
        self.m_model.m_eagme.BASME_LAJES_IPATAMAR_LER (ctypes.byref (varlaje),
                            ctypes.byref (varipatamar))
        ipatamar        = varipatamar.value
        return          ipatamar

    @isALanding.setter
    def isALanding (self, ipatamar: int) -> None:
        """Atribui Patamar de escada (0) Não (1) Sim."""
        varlaje         = ctypes.c_void_p (self.m_laje)
        varipatamar     = ctypes.c_int (ipatamar)
        self.m_model.m_eagme.BASME_LAJES_IPATAMAR_DEF (ctypes.byref (varlaje),
                            ctypes.byref (varipatamar))

    @property
    def stairIdent (self) -> str:
        """Título de escadas.

        Returns:
            Cadeia de caracteres.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        varidentesc     = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_LAJES_IDENTESC_LER (ctypes.byref (varlaje), varidentesc)
        identesc        = varidentesc.value.decode(TQSUtil.CHARSET)
        return          identesc

    @stairIdent.setter
    def stairIdent (self, identesc: str) -> None:
        """Atribui Título de escadas."""
        varlaje         = ctypes.c_void_p (self.m_laje)
        varidentesc     = ctypes.c_char_p (identesc.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_LAJES_IDENTESC_DEF (ctypes.byref (varlaje), varidentesc)

    @property
    def isVolumeOnly (self) -> int:
        """Laje somente de volume (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        ilajsovol       = 0
        varilajsovol    = ctypes.c_int (ilajsovol)
        self.m_model.m_eagme.BASME_LAJES_ILAJSOVOL_LER (ctypes.byref (varlaje),
                            ctypes.byref (varilajsovol))
        ilajsovol       = varilajsovol.value
        return          ilajsovol

    @isVolumeOnly.setter
    def isVolumeOnly (self, ilajsovol: int) -> None:
        """Atribui Laje somente de volume (0) Não (1) Sim."""
        varlaje         = ctypes.c_void_p (self.m_laje)
        varilajsovol    = ctypes.c_int (ilajsovol)
        self.m_model.m_eagme.BASME_LAJES_ILAJSOVOL_DEF (ctypes.byref (varlaje),
                            ctypes.byref (varilajsovol))

    @property
    def volumeOnlySlab (self) -> "VolumeOnlySlab":
        """Operação ``volumeOnlySlab``.

        Returns:
            :class:`VolumeOnlySlab` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        lajsovol        = None
        varlajsovol     = ctypes.c_void_p (lajsovol)
        self.m_model.m_eagme.BASME_LAJES_LAJSOVOL_LER (ctypes.byref (varlaje),
                            ctypes.byref (varlajsovol))
        lajsovol        = varlajsovol.value
        volumeOnlySlab  = VolumeOnlySlab (self.m_model, lajsovol)
        return          volumeOnlySlab

    @property
    def userAttrib (self) -> "UserAttrib":
        """Operação ``userAttrib``.

        Returns:
            :class:`UserAttrib` correspondente.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        usratrib        = None
        varusratrib     = ctypes.c_void_p (usratrib)
        self.m_model.m_eagme.BASME_LAJES_USRATRIB_LER (ctypes.byref (varlaje),
                            ctypes.byref (varusratrib))
        usratrib        = varusratrib.value
        userAttrib      = UserAttrib (self.m_model, usratrib)
        return          userAttrib


    @property
    def slabExport (self) -> int:
        """Laje exportável para 3D/BIM (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varlaje         = ctypes.c_void_p (self.m_laje)
        iexportavel     = 0
        variexportavel  = ctypes.c_int (iexportavel)
        self.m_model.m_eagme.BASME_LAJES_IEXPORTAVEL_LER (ctypes.byref (varlaje),
                            ctypes.byref (variexportavel))
        iexportavel     = variexportavel.value
        return          iexportavel

    @slabExport.setter
    def slabExport (self, iexportavel: int) -> None:
        """Atribui Laje exportável para 3D/BIM (0) Não (1) Sim."""
        varlaje         = ctypes.c_void_p (self.m_laje)
        variexportavel  = ctypes.c_int (iexportavel)
        self.m_model.m_eagme.BASME_LAJES_IEXPORTAVEL_DEF (ctypes.byref (varlaje),
                            ctypes.byref (variexportavel))

#------------------------------------------------------------------------------
#       Objeto de capitel - CCapiteis
#
class DropPanel (SMObject):

    """Capitel de laje.

    Implementação:
        Capitel de laje (``CCapitel``). Compõe poligonal de contorno via
        ``dropPanelPolygon``.
    """
    def __init__ (self, model: "Model", capitel: int) -> None:
        """Classe que define capitel.

        Args:
            model: Objeto Model() do modelo atual.
            capitel: Apontador para objeto CCapiteis.
        """
        self.m_model    = model
        self.m_capitel  = capitel
        super().__init__(model, self.m_capitel)

    @property
    def dropPanelPolygon (self) -> "Polygon":
        """Poligonal do capitel - Poygon().

        Returns:
            :class:`Polygon` correspondente.
        """
        varcapitel      = ctypes.c_void_p (self.m_capitel)
        poligp          = None
        varpoligp       = ctypes.c_void_p (poligp)
        self.m_model.m_eagme.BASME_CAPITEIS_POLIGONAL_LER (ctypes.byref (varcapitel),
                            ctypes.byref (varpoligp))
        poligp          = varpoligp.value
        columnpolygon   = Polygon (self.m_model, poligp)
        return          columnpolygon


    @property
    def dropPanelThickness (self) -> float:
        """Altura do capitel, cm.

        Returns:
            Valor de ponto flutuante.
        """
        varcapitel      = ctypes.c_void_p (self.m_capitel)
        hcap            = 0.
        varhcap         = ctypes.c_double (hcap)
        self.m_model.m_eagme.BASME_CAPITEIS_H_LER (ctypes.byref (varcapitel),
                            ctypes.byref (varhcap))
        hcap            = varhcap.value
        return          hcap

    @dropPanelThickness.setter
    def dropPanelThickness (self, hcap: float) -> None:
        """Atribui Altura do capitel, cm."""
        varcapitel      = ctypes.c_void_p (self.m_capitel)
        varhcap         = ctypes.c_double (hcap)
        self.m_model.m_eagme.BASME_CAPITEIS_H_DEF (ctypes.byref (varcapitel),
                            ctypes.byref (varhcap))

    @property
    def dropPanelDiv (self) -> float:
        """Divisor de inércia à flexão do capitel.

        Returns:
            Valor de ponto flutuante.
        """
        varcapitel      = ctypes.c_void_p (self.m_capitel)
        divflx          = 0.
        vardivflx       = ctypes.c_double (divflx)
        self.m_model.m_eagme.BASME_CAPITEIS_DIVFLX_LER (ctypes.byref (varcapitel),
                            ctypes.byref (vardivflx))
        divflx          = vardivflx.value
        return          divflx

    @dropPanelDiv.setter
    def dropPanelDiv (self, divflx: float) -> None:
        """Atribui Divisor de inércia à flexão do capitel."""
        varcapitel      = ctypes.c_void_p (self.m_capitel)
        vardivflx       = ctypes.c_double (divflx)
        self.m_model.m_eagme.BASME_CAPITEIS_DIVFLX_DEF (ctypes.byref (varcapitel),
                            ctypes.byref (vardivflx))
    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varcapitel      = ctypes.c_void_p (self.m_capitel)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CAPITEIS_IPISOAUX_LER (ctypes.byref (varcapitel),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varcapitel      = ctypes.c_void_p (self.m_capitel)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CAPITEIS_IPISOAUX_DEF (ctypes.byref (varcapitel),
                            ctypes.byref (varipisoaux))

#------------------------------------------------------------------------------
#       Objeto de forma de nervura
#
class SlabMould (SMObject):

    """Forma/cubeta de laje nervurada.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", forner: int) -> None:
        """Classe que define uma forma de nervura.

        Args:
            model: Objeto Model() do modelo atual.
            forner: Apontador para objeto CForNer.
        """
        self.m_model    = model
        self.m_forner   = forner
        super().__init__(model, self.m_forner)

    @property
    def insX (self) -> float:
        """X de inserção do molde.

        Returns:
            Valor de ponto flutuante.
        """
        varforner       = ctypes.c_void_p (self.m_forner)
        xins            = 0.
        varxins         = ctypes.c_double (xins)
        self.m_model.m_eagme.BASME_FORNER_PT_LERX (ctypes.byref (varforner),
                            ctypes.byref (varxins))
        xins            = varxins.value
        return          xins

    @insX.setter
    def insX (self, xins: float) -> None:
        """Atribui X de inserção do molde."""
        varforner       = ctypes.c_void_p (self.m_forner)
        varxins         = ctypes.c_double (xins)
        self.m_model.m_eagme.BASME_FORNER_PT_DEFX (ctypes.byref (varforner),
                            ctypes.byref (varxins))

    @property
    def insY (self) -> float:
        """Y de inserção do molde.

        Returns:
            Valor de ponto flutuante.
        """
        varforner       = ctypes.c_void_p (self.m_forner)
        yins            = 0.
        varyins         = ctypes.c_double (yins)
        self.m_model.m_eagme.BASME_FORNER_PT_LERY (ctypes.byref (varforner),
                            ctypes.byref (varyins))
        yins            = varyins.value
        return          yins

    @insY.setter
    def insY (self, yins: float) -> None:
        """Atribui Y de inserção do molde."""
        varforner       = ctypes.c_void_p (self.m_forner)
        varyins         = ctypes.c_double (yins)
        self.m_model.m_eagme.BASME_FORNER_PT_DEFY (ctypes.byref (varforner),
                            ctypes.byref (varyins))

    @property
    def averageSizeX (self) -> float:
        """Tamanho X médio cm.

        Returns:
            Valor de ponto flutuante.
        """
        varforner       = ctypes.c_void_p (self.m_forner)
        tamx            = 0.
        vartamx         = ctypes.c_double (tamx)
        self.m_model.m_eagme.BASME_FORNER_GEO_TAMX_LER (ctypes.byref (varforner),
                            ctypes.byref (vartamx))
        tamx            = vartamx.value
        return          tamx

    @averageSizeX.setter
    def averageSizeX (self, tamx: float) -> None:
        """Atribui Tamanho X médio cm."""
        varforner       = ctypes.c_void_p (self.m_forner)
        vartamx         = ctypes.c_double (tamx)
        self.m_model.m_eagme.BASME_FORNER_GEO_TAMX_DEF (ctypes.byref (varforner),
                            ctypes.byref (vartamx))

    @property
    def averageSizeY (self) -> float:
        """Tamanho Y médio cm.

        Returns:
            Valor de ponto flutuante.
        """
        varforner       = ctypes.c_void_p (self.m_forner)
        tamy            = 0.
        vartamy         = ctypes.c_double (tamy)
        self.m_model.m_eagme.BASME_FORNER_GEO_TAMY_LER (ctypes.byref (varforner),
                            ctypes.byref (vartamy))
        tamy            = vartamy.value
        return          tamy

    @averageSizeY.setter
    def averageSizeY (self, tamy: float) -> None:
        """Atribui Tamanho Y médio cm."""
        varforner       = ctypes.c_void_p (self.m_forner)
        vartamy         = ctypes.c_double (tamy)
        self.m_model.m_eagme.BASME_FORNER_GEO_TAMY_DEF (ctypes.byref (varforner),
                            ctypes.byref (vartamy))

    @property
    def rotationAngle (self) -> float:
        """Ângulo de rotação em graus.

        Returns:
            Valor de ponto flutuante.
        """
        varforner       = ctypes.c_void_p (self.m_forner)
        ang             = 0.
        varang          = ctypes.c_double (ang)
        self.m_model.m_eagme.BASME_FORNER_GEO_ANG_LER (ctypes.byref (varforner),
                            ctypes.byref (varang))
        ang             = varang.value
        return          ang

    @rotationAngle.setter
    def rotationAngle (self, ang: float) -> None:
        """Atribui Ângulo de rotação em graus."""
        varforner       = ctypes.c_void_p (self.m_forner)
        varang          = ctypes.c_double (ang)
        self.m_model.m_eagme.BASME_FORNER_GEO_ANG_DEF (ctypes.byref (varforner),
                            ctypes.byref (varang))

    @property
    def sizeXDelta (self) -> float:
        """Variação de espessura trapezoidal X cm.

        Returns:
            Valor de ponto flutuante.
        """
        varforner       = ctypes.c_void_p (self.m_forner)
        vartx           = 0.
        varvartx        = ctypes.c_double (vartx)
        self.m_model.m_eagme.BASME_FORNER_GEO_VARTX_LER (ctypes.byref (varforner),
                            ctypes.byref (varvartx))
        vartx           = varvartx.value
        return          vartx

    @sizeXDelta.setter
    def sizeXDelta (self, vartx: float) -> None:
        """Atribui Variação de espessura trapezoidal X cm."""
        varforner       = ctypes.c_void_p (self.m_forner)
        varvartx        = ctypes.c_double (vartx)
        self.m_model.m_eagme.BASME_FORNER_GEO_VARTX_DEF (ctypes.byref (varforner),
                            ctypes.byref (varvartx))

    @property
    def sizeYDelta (self) -> float:
        """Variação de espessura trapezoidal Y cm.

        Returns:
            Valor de ponto flutuante.
        """
        varforner       = ctypes.c_void_p (self.m_forner)
        varty           = 0.
        varvarty        = ctypes.c_double (varty)
        self.m_model.m_eagme.BASME_FORNER_GEO_VARTY_LER (ctypes.byref (varforner),
                            ctypes.byref (varvarty))
        varty           = varvarty.value
        return          varty

    @sizeYDelta.setter
    def sizeYDelta (self, varty: float) -> None:
        """Atribui Variação de espessura trapezoidal Y cm."""
        varforner       = ctypes.c_void_p (self.m_forner)
        varvarty        = ctypes.c_double (varty)
        self.m_model.m_eagme.BASME_FORNER_GEO_VARTY_DEF (ctypes.byref (varforner),
                            ctypes.byref (varvarty))

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varforner       = ctypes.c_void_p (self.m_forner)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_FORNER_IPISOAUX_LER (ctypes.byref (varforner),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varforner       = ctypes.c_void_p (self.m_forner)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_FORNER_IPISOAUX_DEF (ctypes.byref (varforner),
                            ctypes.byref (varipisoaux))
#------------------------------------------------------------------------------
#       Objeto de furo em lajes - CFuros
#
class SlabOpening (SMObject):

    """Furo em laje.

    Implementação:
        Furo em laje (``CFurLaj``). Compõe poligonal de contorno via ``slabOpeningPolygon``.
    """
    def __init__ (self, model: "Model", furo: int) -> None:
        """Classe que define um furo em laje.

        Args:
            model: Objeto Model() do modelo atual.
            furo: Apontador para objeto CFuros.
        """
        self.m_model    = model
        self.m_furo     = furo
        super().__init__(model, self.m_furo)

    @property
    def slabOpeningPolygon (self) -> "Polygon":
        """Poligonal do furo em laje - Polygon().

        Returns:
            :class:`Polygon` correspondente.
        """
        varfuro         = ctypes.c_void_p (self.m_furo)
        polig           = None
        varpolig        = ctypes.c_void_p (polig)
        self.m_model.m_eagme.BASME_FUROS_POLIGONAL_LER (ctypes.byref (varfuro),
                            ctypes.byref (varpolig))
        polig           = varpolig.value
        openingpolygon   = Polygon (self.m_model, polig)
        return          openingpolygon

    @property
    def isCut (self) -> int:
        """Tipo de furo (0) Shaft (respeita nervuras) (1) Corte.

        Returns:
            Valor inteiro.
        """
        varfuro         = ctypes.c_void_p (self.m_furo)
        irecorte        = 0
        varirecorte     = ctypes.c_int (irecorte)
        self.m_model.m_eagme.BASME_FUROS_IRECORTE_LER (ctypes.byref (varfuro),
                            ctypes.byref (varirecorte))
        irecorte        = varirecorte.value
        return          irecorte

    @isCut.setter
    def isCut (self, irecorte: int) -> None:
        """Atribui Tipo de furo (0) Shaft (respeita nervuras) (1) Corte."""
        varfuro         = ctypes.c_void_p (self.m_furo)
        varirecorte     = ctypes.c_int (irecorte)
        self.m_model.m_eagme.BASME_FUROS_IRECORTE_DEF (ctypes.byref (varfuro),
                            ctypes.byref (varirecorte))
    @property
    def inConcretTopping (self) -> int:
        """Somente na capa da laje nervurada (0) Não (1) Sim.

        Returns:
            Valor inteiro.
        """
        varfuro         = ctypes.c_void_p (self.m_furo)
        isobrecapa      = 0
        varisobrecapa   = ctypes.c_int (isobrecapa)
        self.m_model.m_eagme.BASME_FUROS_ISOBRECAPA_LER (ctypes.byref (varfuro),
                            ctypes.byref (varisobrecapa))
        isobrecapa      = varisobrecapa.value
        return          isobrecapa

    @inConcretTopping.setter
    def inConcretTopping (self, isobrecapa: int) -> None:
        """Atribui Somente na capa da laje nervurada (0) Não (1) Sim."""
        varfuro         = ctypes.c_void_p (self.m_furo)
        varisobrecapa   = ctypes.c_int (isobrecapa)
        self.m_model.m_eagme.BASME_FUROS_ISOBRECAPA_DEF (ctypes.byref (varfuro),
                            ctypes.byref (varisobrecapa))

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varfuro         = ctypes.c_void_p (self.m_furo)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_FUROS_IPISOAUX_LER (ctypes.byref (varfuro),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varfuro         = ctypes.c_void_p (self.m_furo)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_FUROS_IPISOAUX_DEF (ctypes.byref (varfuro),
                            ctypes.byref (varipisoaux))
#------------------------------------------------------------------------------
#       Valores de cargas - CCargas
#
class Load ():

    """Valor genérico de carga.

    Implementação:
        Valor genérico de carga (``CCarga``). Métodos ``Set*`` empacotam valor,
        coeficiente alfa e nome em strings/doubles e os gravam no objeto C++.
    """
    def __init__ (self, model: "Model", floor: "Floor", carga: int) -> None:
        """Classe de valor de carga - usada pelas cargas aplicadas (concentrada, linear, etc).

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor, com dados de uma planta.
            carga: Apontador para objeto CCargas.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_carga    = carga

    def SetLoad (self, itype: int) -> None:
        """Define o tipo de carga.

        Args:
            itype: Constante do tipo de objeto/elemento.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varcarga        = ctypes.c_void_p (self.m_carga)
        varitype        = ctypes.c_int (itype)
        self.m_model.m_eagme.BASME_CARGAS_TIPO_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varcarga), ctypes.byref (varitype))

    def SetAlpha (self, icase: int, ialpha: int) -> None:
        """Define modo de carga numérico ou alfanumérico.

        Args:
            icase: Parâmetro ``icase``.
            ialpha: Parâmetro ``ialpha``.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varcarga        = ctypes.c_void_p (self.m_carga)
        varicase        = ctypes.c_int (icase)
        varialpha       = ctypes.c_int (ialpha)
        self.m_model.m_eagme.BASME_CARGAS_IALFA_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varcarga), ctypes.byref (varicase),
                            ctypes.byref (varialpha))

    def SetLoadName (self, icase: int, loadname: str) -> None:
        """Para cargas alfanuméricas, define o nome da carga na tabela de cargas.

        Args:
            icase: Parâmetro ``icase``.
            loadname: Nome da carga.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varcarga        = ctypes.c_void_p (self.m_carga)
        varicase        = ctypes.c_int (icase)
        varnomcar       = ctypes.c_char_p (loadname.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_CARGAS_NOMCAR_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varcarga), ctypes.byref (varicase),
                            varnomcar)

    def SetMainLoad (self, icase: int, loadval: float) -> None:
        """Valor da carga permanente.

        Args:
            icase: Parâmetro ``icase``.
            loadval: Valor da carga em unidades coerentes.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varcarga        = ctypes.c_void_p (self.m_carga)
        varicase        = ctypes.c_int (icase)
        varloadval      = ctypes.c_double (loadval)
        self.m_model.m_eagme.BASME_CARGAS_CPERM_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varcarga), ctypes.byref (varicase),
                            ctypes.byref (varloadval))

    def SetLiveLoad (self, icase: int, loadval: float) -> None:
        """Valor da carga variável.

        Args:
            icase: Parâmetro ``icase``.
            loadval: Valor da carga em unidades coerentes.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varcarga        = ctypes.c_void_p (self.m_carga)
        varicase        = ctypes.c_int (icase)
        varloadval      = ctypes.c_double (loadval)
        self.m_model.m_eagme.BASME_CARGAS_CACID_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varcarga), ctypes.byref (varicase),
                            ctypes.byref (varloadval))

    def SetWallHeight (self, icase: int, iwall: int, wallheight: float) -> None:
        """Define o uso da altura da parede.

        Args:
            icase: Parâmetro ``icase``.
            iwall: Parâmetro ``iwall``.
            wallheight: Parâmetro ``wallheight``.
        """
        varfabrica      = ctypes.c_void_p (self.m_floor.m_fabrica)
        varcarga        = ctypes.c_void_p (self.m_carga)
        varicase        = ctypes.c_int (icase)
        variwall        = ctypes.c_int (iwall)
        varwallheight   = ctypes.c_double (wallheight)
        self.m_model.m_eagme.BASME_CARGAS_PAREDES_DEF (ctypes.byref (varfabrica),
                            ctypes.byref (varcarga), ctypes.byref (varicase),
                            ctypes.byref (variwall), ctypes.byref (varwallheight))

#------------------------------------------------------------------------------
#       Carga de empuxo lateral aplicada em pilares - CCarEmp
#
class SoilPressureLoad (SMObject):

    """Carga de empuxo.

    Implementação:
        Carga de empuxo no fundo do edifício. Expõe duas cargas independentes
        (topo e base) cada uma como sub-objeto :class:`Load`.
    """
    def __init__ (self, model: "Model", floor: "Floor", caremp: int) -> None:
        """Classe que define empuxo lateral de solo.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor, com dados de uma planta.
            caremp: Apontador para objeto CCarEmp.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_caremp   = caremp
        super().__init__(model, self.m_caremp)

    @property
    def topLoad (self) -> "Load":
        """Carga de empuxo no topo - Objeto Load().

        Returns:
            :class:`Load` correspondente.
        """
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        cargatopo       = None
        varcargatopo    = ctypes.c_void_p (cargatopo)
        self.m_model.m_eagme.BASME_CAREMP_CARGATOPO_LER (ctypes.byref (varcaremp),
                            ctypes.byref (varcargatopo))
        cargatopo       = varcargatopo.value
        topload         = Load (self.m_model, self.m_floor, cargatopo)
        return          topload

    @property
    def baseLoad (self) -> "Load":
        """Carga de empuxo na base - Objeto Load().

        Returns:
            :class:`Load` correspondente.
        """
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        cargabase       = None
        varcargabase    = ctypes.c_void_p (cargabase)
        self.m_model.m_eagme.BASME_CAREMP_CARGABASE_LER (ctypes.byref (varcaremp),
                            ctypes.byref (varcargabase))
        cargabase       = varcargabase.value
        baseload        = Load (self.m_model, self.m_floor, cargabase)
        return          baseload

    @property
    def topFloorName (self) -> str:
        """Nome da planta do topo da carga de empuxo.

        Returns:
            Cadeia de caracteres.
        """
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        varplanttopo    = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_CAREMP_PLANTTOPO_LER (ctypes.byref (varcaremp),
                            varplanttopo)
        planttopo       = varplanttopo.value.decode(TQSUtil.CHARSET)
        return          planttopo

    @topFloorName.setter
    def topFloorName (self, planttopo: str) -> None:
        """Atribui Nome da planta do topo da carga de empuxo."""
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        varplanttopo    = ctypes.c_char_p (planttopo.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_CAREMP_PLANTTOPO_DEF (ctypes.byref (varcaremp),
                            varplanttopo)

    @property
    def baseFloorName (self) -> str:
        """Nome da planta da base da carga de empuxo.

        Returns:
            Cadeia de caracteres.
        """
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        varplantbase    = ctypes.create_string_buffer (TQSUtil.MAXNCSTR)
        self.m_model.m_eagme.BASME_CAREMP_PLANTBASE_LER (ctypes.byref (varcaremp),
                            varplantbase)
        plantbase       = varplantbase.value.decode(TQSUtil.CHARSET)
        return          plantbase

    @baseFloorName.setter
    def baseFloorName (self, plantbase: str) -> None:
        """Atribui Nome da planta da base da carga de empuxo."""
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        varplantbase    = ctypes.c_char_p (plantbase.encode (TQSUtil.CHARSET))
        self.m_model.m_eagme.BASME_CAREMP_PLANTBASE_DEF (ctypes.byref (varcaremp),
                            varplantbase)

    @property
    def startPointX (self) -> float:
        """Ponto inicial X.

        Returns:
            Valor de ponto flutuante.
        """
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        xini            = 0
        varxini         = ctypes.c_double (xini)
        self.m_model.m_eagme.BASME_CAREMP_PTINIX_LER (ctypes.byref (varcaremp),
                            ctypes.byref (varxini))
        xini            = varxini.value
        return          xini

    @startPointX.setter
    def startPointX (self, xini: float) -> None:
        """Atribui Ponto inicial X."""
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        varxini         = ctypes.c_double (xini)
        self.m_model.m_eagme.BASME_CAREMP_PTINIX_DEF (ctypes.byref (varcaremp),
                            ctypes.byref (varxini))

    @property
    def startPointY (self) -> float:
        """Ponto inicial Y.

        Returns:
            Valor de ponto flutuante.
        """
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        yini            = 0
        varyini         = ctypes.c_double (yini)
        self.m_model.m_eagme.BASME_CAREMP_PTINIY_LER (ctypes.byref (varcaremp),
                            ctypes.byref (varyini))
        yini            = varyini.value
        return          yini

    @startPointY.setter
    def startPointY (self, yini: float) -> None:
        """Atribui Ponto inicial Y."""
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        varyini         = ctypes.c_double (yini)
        self.m_model.m_eagme.BASME_CAREMP_PTINIY_DEF (ctypes.byref (varcaremp),
                            ctypes.byref (varyini))

    @property
    def endPointX (self) -> float:
        """Ponto final X.

        Returns:
            Valor de ponto flutuante.
        """
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        xfin            = 0
        varxfin         = ctypes.c_double (xfin)
        self.m_model.m_eagme.BASME_CAREMP_PTFINX_LER (ctypes.byref (varcaremp),
                            ctypes.byref (varxfin))
        xfin            = varxfin.value
        return          xfin

    @endPointX.setter
    def endPointX (self, xfin: float) -> None:
        """Atribui Ponto final X."""
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        varxfin         = ctypes.c_double (xfin)
        self.m_model.m_eagme.BASME_CAREMP_PTFINX_DEF (ctypes.byref (varcaremp),
                            ctypes.byref (varxfin))

    @property
    def endPointY (self) -> float:
        """Ponto final Y.

        Returns:
            Valor de ponto flutuante.
        """
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        yfin            = 0
        varyfin         = ctypes.c_double (yfin)
        self.m_model.m_eagme.BASME_CAREMP_PTFINY_LER (ctypes.byref (varcaremp),
                            ctypes.byref (varyfin))
        yfin            = varyfin.value
        return          yfin

    @endPointY.setter
    def endPointY (self, yfin: float) -> None:
        """Atribui Ponto final Y."""
        varcaremp       = ctypes.c_void_p (self.m_caremp)
        varyfin         = ctypes.c_double (yfin)
        self.m_model.m_eagme.BASME_CAREMP_PTFINY_DEF (ctypes.byref (varcaremp),
                            ctypes.byref (varyfin))

#------------------------------------------------------------------------------
#       Carga adicional em lajes CCarAdi
#
class AdditionalLoad (SMObject):

    """Carga adicional em laje.

    Implementação:
        Carga adicional em laje (``CCarAdic``). Carrega um sub-objeto :class:`Load`
        com o valor da carga adicional.
    """
    def __init__ (self, model: "Model", floor: "Floor", caradi: int) -> None:
        """Carga adicional em lajes tf/m2.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor, com dados de uma planta.
            caradi: Apontador para objeto CCarAdi.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_caradi   = caradi
        super().__init__(model, self.m_caradi)

    @property
    def load (self) -> "Load":
        """Valor da carga - Objeto Load ().

        Returns:
            :class:`Load` correspondente.
        """
        varcaradi       = ctypes.c_void_p (self.m_caradi)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_CARADI_CARGA_LER (ctypes.byref (varcaradi),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx

    @property
    def insertionX (self) -> float:
        """Ponto de inserção X.

        Returns:
            Valor de ponto flutuante.
        """
        varcaradi       = ctypes.c_void_p (self.m_caradi)
        xini            = 0
        varxini         = ctypes.c_double (xini)
        self.m_model.m_eagme.BASME_CARADI_PTINS_LERX (ctypes.byref (varcaradi),
                            ctypes.byref (varxini))
        xini            = varxini.value
        return          xini

    @insertionX.setter
    def insertionX (self, xini: float) -> None:
        """Atribui Ponto de inserção X."""
        varcaradi       = ctypes.c_void_p (self.m_caradi)
        varxini         = ctypes.c_double (xini)
        self.m_model.m_eagme.BASME_CARADI_PTINS_DEFX (ctypes.byref (varcaradi),
                            ctypes.byref (varxini))

    @property
    def insertionY (self) -> float:
        """Ponto de inserção Y.

        Returns:
            Valor de ponto flutuante.
        """
        varcaradi       = ctypes.c_void_p (self.m_caradi)
        yini            = 0
        varyini         = ctypes.c_double (yini)
        self.m_model.m_eagme.BASME_CARADI_PTINS_LERY (ctypes.byref (varcaradi),
                            ctypes.byref (varyini))
        yini            = varyini.value
        return          yini

    @insertionY.setter
    def insertionY (self, yini: float) -> None:
        """Atribui Ponto de inserção Y."""
        varcaradi       = ctypes.c_void_p (self.m_caradi)
        varyini         = ctypes.c_double (yini)
        self.m_model.m_eagme.BASME_CARADI_PTINS_DEFY (ctypes.byref (varcaradi),
                            ctypes.byref (varyini))

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varcaradi       = ctypes.c_void_p (self.m_caradi)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CARADI_IPISOAUX_LER (ctypes.byref (varcaradi),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varcaradi       = ctypes.c_void_p (self.m_caradi)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CARADI_IPISOAUX_DEF (ctypes.byref (varcaradi),
                            ctypes.byref (varipisoaux))
#------------------------------------------------------------------------------
#       Carga distribuída por área em lajes CCarAre
#
class AreaDistributedLoad (SMObject):

    """Carga distribuída por área.

    Implementação:
        Carga distribuída por área (``CCarArea``). Composta por valor (:class:`Load`)
        e poligonal (:class:`Polygon`) que delimita a região.
    """
    def __init__ (self, model: "Model", floor: "Floor", carare: int) -> None:
        """Carga distribuída por área em lajes tf/m2.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor, com dados de uma planta.
            carare: Apontador para objeto CCarAre.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_carare   = carare
        super().__init__(model, self.m_carare)

    @property
    def load (self) -> "Load":
        """Valor da carga - Objeto Load().

        Returns:
            :class:`Load` correspondente.
        """
        varcarare       = ctypes.c_void_p (self.m_carare)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_CARARE_CARGA_LER (ctypes.byref (varcarare),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx

    @property
    def polygon (self) -> "Polygon":
        """Poligonal fechada onde a polig é distribuída - Polygon().

        Returns:
            :class:`Polygon` correspondente.
        """
        varcarare       = ctypes.c_void_p (self.m_carare)
        polig           = None
        varpolig        = ctypes.c_void_p (polig)
        self.m_model.m_eagme.BASME_CARARE_POLIG_LER (ctypes.byref (varcarare),
                            ctypes.byref (varpolig))
        polig           = varpolig.value
        polygonx        = Polygon (self.m_model, polig)
        return          polygonx

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varcarare       = ctypes.c_void_p (self.m_carare)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CARARE_IPISOAUX_LER (ctypes.byref (varcarare),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varcarare       = ctypes.c_void_p (self.m_carare)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CARARE_IPISOAUX_DEF (ctypes.byref (varcarare),
                            ctypes.byref (varipisoaux))

#------------------------------------------------------------------------------
#       Carga concentrada em laje, viga ou pilar CCarCon
#
class ConcentratedLoad (SMObject):

    """Carga concentrada.

    Implementação:
        Carga concentrada (``CCarCon``) com componentes ``Fx``, ``Fy``, ``Fz`` e
        momentos ``Mx``, ``My``, ``Mz``; cada componente é um sub-objeto :class:`Load`.
    """
    def __init__ (self, model: "Model", floor: "Floor", carcon: int) -> None:
        """Carga concentrada em laje, viga ou pilar.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor, com dados de uma planta.
            carcon: Apontador para objeto CCarCon.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_carcon   = carcon
        super().__init__(model, self.m_carcon)

    @property
    def loadFx (self) -> "Load":
        """Força Fx - tf - Somente pilar - Objeto Load ().

        Returns:
            :class:`Load` correspondente.
        """
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_CARCON_FX_LER (ctypes.byref (varcarcon),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx

    @property
    def loadFy (self) -> "Load":
        """Força Fy - tf - Somente pilar - Objeto Load ().

        Returns:
            :class:`Load` correspondente.
        """
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_CARCON_FY_LER (ctypes.byref (varcarcon),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx

    @property
    def loadFz (self) -> "Load":
        """Força Fz - tf - Pilar, viga ou laje - Objeto Load ().

        Returns:
            :class:`Load` correspondente.
        """
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_CARCON_FZ_LER (ctypes.byref (varcarcon),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx

    @property
    def loadMx (self) -> "Load":
        """Força Mx - tfm - Somente pilar - Objeto Load ().

        Returns:
            :class:`Load` correspondente.
        """
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_CARCON_MX_LER (ctypes.byref (varcarcon),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx

    @property
    def loadMy (self) -> "Load":
        """Força My - tfm - Somente pilar - Objeto Load ().

        Returns:
            :class:`Load` correspondente.
        """
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_CARCON_MY_LER (ctypes.byref (varcarcon),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx

    @property
    def insertionX (self) -> float:
        """Ponto de inserção X.

        Returns:
            Valor de ponto flutuante.
        """
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        xini            = 0
        varxini         = ctypes.c_double (xini)
        self.m_model.m_eagme.BASME_CARCON_PTINS_LERX (ctypes.byref (varcarcon),
                            ctypes.byref (varxini))
        xini            = varxini.value
        return          xini

    @insertionX.setter
    def insertionX (self, xini: float) -> None:
        """Atribui Ponto de inserção X."""
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        varxini         = ctypes.c_double (xini)
        self.m_model.m_eagme.BASME_CARCON_PTINS_DEFX (ctypes.byref (varcarcon),
                            ctypes.byref (varxini))

    @property
    def insertionY (self) -> float:
        """Ponto de inserção Y.

        Returns:
            Valor de ponto flutuante.
        """
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        yini            = 0
        varyini         = ctypes.c_double (yini)
        self.m_model.m_eagme.BASME_CARCON_PTINS_LERY (ctypes.byref (varcarcon),
                            ctypes.byref (varyini))
        yini            = varyini.value
        return          yini

    @insertionY.setter
    def insertionY (self, yini: float) -> None:
        """Atribui Ponto de inserção Y."""
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        varyini         = ctypes.c_double (yini)
        self.m_model.m_eagme.BASME_CARCON_PTINS_DEFY (ctypes.byref (varcarcon),
                            ctypes.byref (varyini))

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CARCON_IPISOAUX_LER (ctypes.byref (varcarcon),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varcarcon       = ctypes.c_void_p (self.m_carcon)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CARCON_IPISOAUX_DEF (ctypes.byref (varcarcon),
                            ctypes.byref (varipisoaux))
#------------------------------------------------------------------------------
#       Carga linear distribuída por metro sobre laje ou viga CCarLin
#
class LinearyDistributedLoad (SMObject):

    """Carga distribuída linear.

    Implementação:
        Carga distribuída linear (``CCarLin``). Sub-objeto ``load`` carrega o valor e
        ``wall`` referencia a parede onde a carga é aplicada.
    """
    def __init__ (self, model: "Model", floor: "Floor", carlin: int) -> None:
        """Carga linear distribuída tf/m.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor, com dados de uma planta.
            carlin: Apontador para objeto CCarLin.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_carlin   = carlin
        super().__init__(model, self.m_carlin)

    @property
    def load (self) -> "Load":
        """Valor da carga - Objeto Load().

        Returns:
            :class:`Load` correspondente.
        """
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        carga           = None
        varcarga        = ctypes.c_void_p (carga)
        self.m_model.m_eagme.BASME_CARLIN_CARGA_LER (ctypes.byref (varcarlin),
                            ctypes.byref (varcarga))
        carga           = varcarga.value
        loadx           = Load (self.m_model, self.m_floor, carga)
        return          loadx

    @property
    def startPointX (self) -> float:
        """Ponto inicial X.

        Returns:
            Valor de ponto flutuante.
        """
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        xini            = 0
        varxini         = ctypes.c_double (xini)
        self.m_model.m_eagme.BASME_CARLIN_PTINI_LERX (ctypes.byref (varcarlin),
                            ctypes.byref (varxini))
        xini            = varxini.value
        return          xini

    @startPointX.setter
    def startPointX (self, xini: float) -> None:
        """Atribui Ponto inicial X."""
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        varxini         = ctypes.c_double (xini)
        self.m_model.m_eagme.BASME_CARLIN_PTINI_DEFX (ctypes.byref (varcarlin),
                            ctypes.byref (varxini))

    @property
    def startPointY (self) -> float:
        """Ponto inicial Y.

        Returns:
            Valor de ponto flutuante.
        """
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        yini            = 0
        varyini         = ctypes.c_double (yini)
        self.m_model.m_eagme.BASME_CARLIN_PTINI_LERY (ctypes.byref (varcarlin),
                            ctypes.byref (varyini))
        yini            = varyini.value
        return          yini

    @startPointY.setter
    def startPointY (self, yini: float) -> None:
        """Atribui Ponto inicial Y."""
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        varyini         = ctypes.c_double (yini)
        self.m_model.m_eagme.BASME_CARLIN_PTINI_DEFY (ctypes.byref (varcarlin),
                            ctypes.byref (varyini))

    @property
    def endPointX (self) -> float:
        """Ponto final X.

        Returns:
            Valor de ponto flutuante.
        """
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        xfin            = 0
        varxfin         = ctypes.c_double (xfin)
        self.m_model.m_eagme.BASME_CARLIN_PTFIN_LERX (ctypes.byref (varcarlin),
                            ctypes.byref (varxfin))
        xfin            = varxfin.value
        return          xfin

    @endPointX.setter
    def endPointX (self, xfin: float) -> None:
        """Atribui Ponto final X."""
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        varxfin         = ctypes.c_double (xfin)
        self.m_model.m_eagme.BASME_CARLIN_PTFIN_DEFX (ctypes.byref (varcarlin),
                            ctypes.byref (varxfin))

    @property
    def endPointY (self) -> float:
        """Ponto final Y.

        Returns:
            Valor de ponto flutuante.
        """
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        yfin            = 0
        varyfin         = ctypes.c_double (yfin)
        self.m_model.m_eagme.BASME_CARLIN_PTFIN_LERY (ctypes.byref (varcarlin),
                            ctypes.byref (varyfin))
        yfin            = varyfin.value
        return          yfin

    @endPointY.setter
    def endPointY (self, yfin: float) -> None:
        """Atribui Ponto final Y."""
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        varyfin         = ctypes.c_double (yfin)
        self.m_model.m_eagme.BASME_CARLIN_PTFIN_DEFY (ctypes.byref (varcarlin),
                            ctypes.byref (varyfin))

    @property
    def auxiliaryFloor (self) -> int:
        """Piso auxiliar.

        Returns:
            Valor inteiro.
        """
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        ipisoaux        = 0
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CARLIN_IPISOAUX_LER (ctypes.byref (varcarlin),
                            ctypes.byref (varipisoaux))
        ipisoaux        = varipisoaux.value
        return          ipisoaux

    @auxiliaryFloor.setter
    def auxiliaryFloor (self, ipisoaux: int) -> None:
        """Atribui Piso auxiliar."""
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        varipisoaux     = ctypes.c_int (ipisoaux)
        self.m_model.m_eagme.BASME_CARLIN_IPISOAUX_DEF (ctypes.byref (varcarlin),
                            ctypes.byref (varipisoaux))

    @property
    def wall (self) -> "Wall":
        """Parede 3D importada do BIM - Objeto Wall() ou None.

        Returns:
            :class:`Wall` correspondente.
        """
        varcarlin       = ctypes.c_void_p (self.m_carlin)
        paresp          = None
        varparesp       = ctypes.c_void_p (paresp)
        self.m_model.m_eagme.BASME_CARLIN_PARESP_LER (ctypes.byref (varcarlin),
                            ctypes.byref (varparesp))
        paresp          = varparesp.value
        wallx           = Wall (self.m_model, self.m_floor, paresp)
        return          wallx
#------------------------------------------------------------------------------
#       Parede 3D importada do BIM - CParEsp
#
class Wall ():

    """Parede estrutural.

    Implementação:
        Property bag de getters/setters sobre o objeto C++ correspondente; cada propriedade
        é uma chamada ``BASME_*_LER`` / ``BASME_*_DEF`` empacotando o argumento em ``ctypes``.
    """
    def __init__ (self, model: "Model", floor: "Floor", paresp: int) -> None:
        """Parede importada do BIM.

        Args:
            model: Objeto Model() do modelo atual.
            floor: Objeto Floor, com dados de uma planta.
            paresp: Apontador para objeto CParEsp.
        """
        self.m_model    = model
        self.m_floor    = floor
        self.m_paresp   = paresp
