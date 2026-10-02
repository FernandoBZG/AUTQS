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
#    TQSDwg.PY         Módulo para leitura e gravação de desenhos DWG TQS
#                      Inclui geração de cotagens e ferros inteligentes
#                      Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes
from typing import List, Optional, Tuple, Union

import TQS.TQSUtil

#-----------------------------------------------------------------------------
#    Aplicações TQS
#
IEDOUT:    int = 1    # Outras
IEDFOR:    int = 2    # Formas
IEDLAJ:    int = 3    # Lajes
IEDFUS:    int = 4    # Fundações sapatas
IEDFUE:    int = 5    # Fundações blocos
IEDFUT:    int = 6    # Fundações tubuloes
IEDVIG:    int = 7    # Vigas
IEDPIL:    int = 8    # Pilares
IEDTAB:    int = 9    # Armação genérica AGC & DP
IEDARQ:    int = 10   # Arquitetura
IEDMAD:    int = 11   # Madeira
IEDMA2:    int = 12   # Madeira
IEDMA3:    int = 13   # Madeira
IEDMA4:    int = 14   # Madeira
IEDCORB:   int = 15   # Corbar
IEDCOM:    int = 16   # Cormad
IEDALV:    int = 17   # Alvest
IEDPOR:    int = 18   # Pórtico
IEDGRE:    int = 19   # Grelha
IEDVPP:    int = 20   # Vigota pré-moldada protend
IEDPLW:    int = 21   # Leitor de PLW
IEDESC:    int = 22   # Escadas
IEDISE:    int = 23   # Interação solo-estrutura
IEDPRE:    int = 24   # Pré-moldados/Pré-fabricados
IEDRER:    int = 25   # Reservatórios/especiais
IEDPAR:    int = 26   # Paredes de concreto
#-----------------------------------------------------------------------------
#    Constantes usadas em cotagem
#
IDHOR:     int = 0         # Cotagem horizontal
IDVER:     int = 1         # Cotagem vertical
IDANG:     int = 2         # Cotagem alinhada
IDINC:     int = 3         # Cotagem inclinada
#-----------------------------------------------------------------------------
#    Tipos de objeto de desenho
#
DWGTYPE_EOF:        int = 0    # Fim de arquivo
DWGTYPE_LINE:       int = 1    # Linha
DWGTYPE_TEXT:       int = 2    # Texto
DWGTYPE_POLYLINE:   int = 3    # Polyline
DWGTYPE_BLOCK:      int = 4    # Insercao de bloco
DWGTYPE_BLOCKEND:   int = 5    # Fim de bloco
DWGTYPE_BLOCKBEGIN: int = 4    # Inicio de bloco
DWGTYPE_CIRCLE:     int = 6    # Circulo
DWGTYPE_ARC:        int = 7    # Arco
DWGTYPE_CURVE:      int = 8    # Curva
DWGTYPE_OBJECT:     int = 9    # Objeto de desenho
DWGTYPE_OBJECTEND:  int = 10   # Fim de leitura, objeto de desenho

#-----------------------------------------------------------------------------
#       Outras constantes
#
MAXIELY:            int = 256  # Máximo de níveis numéricos
#-----------------------------------------------------------------------------
#    Constantes usadas em Ferros Inteligentes
#
ICPDEF:     int = -1        # Usar default do arquivo de critérios

ICPPOS:     int = 0         # Ferro Reto: armadura horizontal positiva
ICPNEG:     int = 1         # Ferro Reto: armadura horizontal negativa

ICPTPDOBGAN: int = 0        # Tipo de dobra: Gancho tração NBR6118:2003 9.4.2.3
ICPTPDOBNOP: int = 1        # Tipo de dobra: Nó de pórtico NBR6118:2003 18.2.2

ICPSRA:     int = 0         # Comprimento total: Faces externas sem desconto de raio
ICPCRA:     int = 1         # Comprimento total: Desenvolvido com desconto de raio
ICPSMS:     int = 2         # Comprimento total: Soma simples dos trechos

ICPDOBSRA:  int = 0         # Comprimento das dobras: Face externa sem desconto de raio
ICPDOBCRA:  int = 1         # Comprimento das dobras: Desenvolvido com raio de dobra
ICPDOBSMS:  int = 2         # Comprimento das dobras: Comprimento do trecho

ICPMAN:     int = 0         # Aplicar raio de dobra: manualmente
ICPAUT:     int = 1         # Aplicar raio de dobra: automaticamente

ICPSCR:     int = 0         # Círculo da posição: Não
ICPPCR:     int = 1         # Círculo da posição: Em volta da posição
ICPPCG:     int = 2         # Círculo da posição: Não: Só texto aumentado
ICPPCA:     int = 3         # Círculo da posição: Não: Texto antes do número de ferros

ICPNSU:     int = 0         # Dobra de sustentação: normal
ICPDSU:     int = 1         # Dobra de sustentação: definida
ICPDS2:     int = 2         # Dobra de sustentação: definida na mesma direção

ICPESP:     int = 0         # Número de ferros: Núm Espaçamentos = Núm de ferros
ICPE1P:     int = 1         # Número de ferros: Núm Espaçamentos = Núm de ferros + 1
ICPE1M:     int = 2         # Número de ferros: Núm Espaçamentos = Núm de ferros - 1

ICPCIR:     int = 0         # Ferro em corte: Círculo
ICPFCR:     int = 1         # Ferro em corte: Bloco 'FERCOR'

ICPNNV:     int = 0         # Espacamento de ferros: em maciço
ICPNRV:     int = 1         # Espacamento de ferros: em nervuras

ICPSAL:     int = 0         # Alternância de ferros: Não
ICPCAL:     int = 1         # Alternância de ferros: Sim

ICPSTP:     int = 0         # Tipo de aço como comentário: Não
ICPCTP:     int = 1         # Tipo de aço como comentário: Sim

ICPSGA:     int = 0         # Tipo de gancho: Sem gancho
ICP090:     int = 1         # Tipo de gancho: Gancho a 90  graus
ICP135:     int = 2         # Tipo de gancho: Gancho a 135 graus
ICP180:     int = 3         # Tipo de gancho: Gancho a 180 graus

ICPNR2:     int = 0         # Número de ramos de estribos: 2 ramos
ICPNR4:     int = 1         # Número de ramos de estribos: 4 ramos
ICPNR6:     int = 2         # Número de ramos de estribos: 6 ramos
ICPNR4B:    int = 3         # Número de ramos de estribos: 4 ramos configuração B

ICPENR:     int = 0         # Estribo de viga: Normal
ICPEFC:     int = 1         # Estribo de viga: Fechado
ICPEAB:     int = 2         # Estribo de viga: Aberto
ICPENC:     int = 3         # Estribo de viga: Normal com largura colaborante

ICPEGENFEC: int = 0         # Estribo genérico: Fechado
ICPEGENABR: int = 1         # Estribo genérico: Aberto
ICPEGENGRA: int = 2         # Estribo genérico: Grampo de pilar
ICPEGENCIR: int = 3         # Estribo genérico: Circular

ICPEGPONTOSLONG: int = 0    # Definição de estribos genéricos: Pontos longitudinais
ICPEGPONTOSSECA: int = 1    # Definição de estribos genéricos: Pontos da seção longitudinal
ICPEGPONTOSEXTR: int = 2    # Definição de estribos genéricos: Pontos externos

ICPTPPATA45: int = 0        # Patas de estribo: 45°
ICPTPPATA90: int = 1        # Patas de estribo: 90°

ICPCA1:     int = 0         # Cotagem de ferro negativo alternado: uma ponta
ICPCA2:     int = 1         # Cotagem de ferro negativo alternado: duas pontas

ICPFRT:     int = 0         # Tipo de ferro: Ferro reto
ICPFGN:     int = 1         # Tipo de ferro: Ferro genérico
ICPSTR:     int = 2         # Tipo de ferro: Estribo
ICPGRA:     int = 3         # Tipo de ferro: Grampo de vigas
ICPSTRGEN:  int = 4         # Tipo de ferro: Estribo genérico, pilar
ICPFAIMUL:  int = 5         # Tipo de ferro: Faixa múltipla (não é ferro)

ICPSRR:     int = 0         # Ferro repitido: Identificar
ICPCRR:     int = 1         # Ferro repitido: Identificar somente posição e quantidade

ICPQUEBR_SEMQUEBRA: int = 0 # Texto de ferro: Sem quebra
ICPQUEBR_SALTOCBCI: int = 1 # Texto de ferro: Salto C/ ou C=
ICPQUEBR_SALTOBITO: int = 2 # Texto de ferro: Salto {
ICPQUEBR_SALTODECD: int = 3 # Texto de ferro: Salto após C/
ICPQUEBR_SALTONPOS: int = 4 # Texto de ferro: Salto número de ferros

ICPCENTR_CENTRAD: int = 0   # Texto de ferros: Centrado
ICPCENTR_ESQUERD: int = 1   # Texto de ferros: Esquerda
ICPCENTR_DIREITA: int = 2   # Texto de ferros: Direita
#-----------------------------------------------------------------------------
#    Constantes usadas no DWG
#
IEXMAX:      int =  1024    # Máximo de pontos de uma poligonal

#-----------------------------------------------------------------------------
#    Classe de desenho
#
class Dwg ():
    """Encapsula um desenho TQS (DWG) e expõe sub-objetos para manipulação.

    Carrega as bibliotecas nativas necessárias para leitura, gravação e
    edição de desenhos TQS, mantendo o handle ``pedmv`` interno.

    Implementação:
        O construtor carrega via ``TQSUtil.LoadDll`` o conjunto de DLLs nativas
        (``MDWG.DLL`` é o motor central, complementado por ``ACESSOL``,
        ``CUSTOMDL``, ``EAGPAR``, ``F2DTRIAZ``, ``NLMPDWG``, ``IPOFER`` e
        ``NV3D``) e instancia os sub-objetos que agrupam comandos por tema.
        Toda manipulação posterior usa o handle ``m_pedmv`` retornado pela DLL,
        passado a cada chamada como ``ctypes.c_void_p``.

    Attributes:
        m_acessol: Handle de ``ACESSOL.DLL``.
        m_customdl: Handle de ``CUSTOMDL.DLL``.
        m_eagpar: Handle de ``EAGPAR.DLL``.
        m_f2dtriaz: Handle de ``F2DTRIAZ.DLL``.
        m_mdwg: Handle de ``MDWG.DLL``.
        m_nlmpdwg: Handle de ``NLMPDWG.DLL``.
        m_ipofer: Handle de ``IPOFER.DLL`` (ferros inteligentes).
        m_nv3d: Handle de ``NV3D.DLL``.
        m_nomedwg: Nome do desenho atual.
        m_icargaok: ``1`` se todas as DLLs foram carregadas, ``0`` caso contrário.
        m_pedmv: Handle interno do desenho (PEDIT/MV).
        file: Sub-objeto :class:`File` para operações de arquivo.
        draw: Sub-objeto :class:`Draw` para inserção de elementos gráficos.
        dim: Sub-objeto :class:`Dim` para cotagem.
        limits: Sub-objeto :class:`Limits` para limites do desenho.
        iterator: Sub-objeto :class:`Iterator` para iteração de elementos.
        settings: Sub-objeto :class:`Settings` com variáveis globais do DWG.
        levelstable: Sub-objeto :class:`LevelsTable` (tabela de níveis).
        blockstable: Sub-objeto :class:`BlocksTable` (tabela de blocos).
        xreference: Sub-objeto :class:`XReference` (referências externas).
        edit: Sub-objeto :class:`Edit` para edição de elementos.
        plotting: Sub-objeto :class:`Plotting` (tabela de plotagem).
        globalrebar: Sub-objeto :class:`GlobalRebar` (posições globais de ferros).
    """
#
#    Construtor: carrega as bibliotecas e inicializa um desenho vazio
#
    def __init__ (self, pedmv: Optional[int] = None) -> None:
        """Carrega as DLLs e inicializa um desenho novo ou a partir de um handle.

        Args:
            pedmv: Handle ``pedmv`` de um desenho já aberto. Se ``None``,
                cria um desenho vazio com ``File.New()``.
        """
        # Inicializa todos os handles como None antes de tentar carregar
        self.m_acessol  = None
        self.m_customdl = None
        self.m_eagpar   = None
        self.m_f2dtriaz = None
        self.m_mdwg     = None
        self.m_nlmpdwg  = None
        self.m_nomedwg  = ""
        self.m_icargaok = 0
        # Carrega cada DLL nativa; falhas deixam o handle em None
        self.m_acessol  = TQS.TQSUtil.LoadDll ("ACESSOL.DLL")
        self.m_customdl = TQS.TQSUtil.LoadDll ("CUSTOMDL.DLL")
        self.m_eagpar   = TQS.TQSUtil.LoadDll ("EAGPAR.DLL")
        self.m_f2dtriaz = TQS.TQSUtil.LoadDll ("F2DTRIAZ.DLL")
        self.m_mdwg     = TQS.TQSUtil.LoadDll ("MDWG.DLL")
        self.m_nlmpdwg  = TQS.TQSUtil.LoadDll ("NLMPDWG.DLL")
        self.m_ipofer   = TQS.TQSUtil.LoadDll ("IPOFER.DLL")
        self.m_nv3d     = TQS.TQSUtil.LoadDll ("NV3D.DLL")
        # Sem todas as DLLs essenciais, o objeto fica inutilizável (m_icargaok = 0)
        if self.m_acessol != None and self.m_customdl != None and self.m_eagpar != None and self.m_f2dtriaz != None and self.m_mdwg != None and self.m_nlmpdwg != None and self.m_ipofer != None:
            self.m_icargaok = 1
        else:
            return

        # Cria o sub-objeto File primeiro: ele aloca/herda o handle pedmv usado pelos demais
        self.m_pedmv    = 0
        self.file       = File (self)
        if              pedmv is None:
            self.file.New ()
        else:
            self.m_pedmv= pedmv

        # Demais sub-objetos compartilham o mesmo pedmv via self.m_dwg
        self.draw       = Draw (self)
        self.dim        = Dim (self)
        self.limits     = Limits (self)
        self.iterator   = Iterator (self)
        self.settings   = Settings (self)
        self.levelstable= LevelsTable (self)
        self.blockstable= BlocksTable (self)
        self.xreference = XReference (self)
        self.edit       = Edit (self)
        self.plotting   = Plotting (self)
        self.globalrebar= GlobalRebar (self)
        self.m_acessol.ACL_INIACESSO ()
#
#    Representação deste objeto
#
    def __str__(self) -> str:
        """Retorna a representação textual do desenho para depuração.

        Returns:
            String com handles e nome do desenho.
        """
        msg         = "Class TQSDwg"
        msg         += "\n   self.m_pedmv %s"  % str (self.m_pedmv)
        msg         += "\n   sef.m_nomedwg [" + self.m_nomedwg + "]"
        msg         += "\n   self.m_acessol " + str (self.m_acessol)
        msg         += "\n   self.m_customdl" + str (self.m_customdl)
        msg         += "\n   self.m_eagpar  " + str (self.m_eagpar)
        msg         += "\n   self.m_f2dtriaz" + str (self.m_f2dtriaz)
        msg         += "\n   self.m_mdwg    " + str (self.m_mdwg)
        msg         += "\n   self.m_nlmpdwg " + str (self.m_nlmpdwg)
        msg         += "\n   self.m_ipofer  " + str (self.m_ipofer)
        return         msg

#
#    Inicializa cores e tabela de plotagem
#
    def CarregarCores (self) -> None:
        """Inicializa cores e a tabela de plotagem associadas ao desenho."""
        istat          = 0
        paristat       = ctypes.c_int (istat)
        parpedmv       = ctypes.c_void_p (self.m_pedmv)
        # Carrega paleta -> inicializa tabela de plot -> lê o nome para validar
        self.m_mdwg.g_carregcores (parpedmv, ctypes.byref(paristat))
        self.m_mdwg.tabplt_ini (parpedmv, ctypes.byref(paristat))
        parnomtab      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_mdwg.tabplt_ler (parpedmv, parnomtab, ctypes.byref(paristat))

#-----------------------------------------------------------------------------
#    Comandos relacionados a arquivos
#
class File ():
    """Comandos relacionados a arquivos do desenho (abrir, salvar, fechar).

    Implementação:
        Os métodos delegam ao subconjunto ``g_des*``/``g_ext*``/``g_edm*`` de
        ``MDWG.DLL`` para abrir, fechar, salvar e migrar formatos. Caminhos
        e nomes são codificados em ``TQSUtil.CHARSET`` antes de virarem
        ``c_char_p``; ``istat`` retornado pelo motor sinaliza erros. O
        handle ``pedmv`` do :class:`Dwg` proprietário é atualizado em cada
        ciclo de criação/abertura.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de arquivo.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg  = dwg
#
#    Abre desenho novo SEM_NOME - fecha anterior se aberto
#
    def New (self) -> None:
        """Inicializa um novo desenho (``SEM_NOME``) para ser salvo com :meth:`SaveAs`.

        Fecha o desenho anterior se estiver aberto.
        """
        # Garante que não há desenho aberto antes de criar um novo
        self.Close ()

        # Obtém o seed (template default) configurado no ACESSOL
        parseed     = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_acessol.ACLSEED (parseed, 0)
        seed        = "%s" % parseed.value.decode(TQS.TQSUtil.CHARSET)
        self.m_dwg.m_nomedwg = "SEM_NOME"
        parnomedwg  = ctypes.c_char_p (self.m_dwg.m_nomedwg.encode(TQS.TQSUtil.CHARSET))
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        istat       = 0
        paristat    = ctypes.c_int (istat)
        # g_desopn aloca um pedmv novo a partir do seed
        self.m_dwg.m_mdwg.g_desopn (parnomedwg, parseed, None,
                              ctypes.byref(parpedmv), ctypes.byref(paristat))
        self.m_dwg.m_pedmv = parpedmv.value
        istat       = paristat.value
        if istat != 0:
            TQS.TQSUtil.writef ("Nao abri o desenho " + self.m_dwg.m_nomedwg)
            return

        # Inicializa cotagem, sincroniza variáveis, ativa leitura de blocos e carrega cores
        self.m_dwg.m_mdwg.COTINI ()
        self.m_dwg.m_mdwg.COTIFOR (parpedmv)
        self.m_dwg.m_mdwg.g_extpbl (parpedmv)
        self.m_dwg.CarregarCores ()
#
#    Abre desenho existente
#
    def Open (self, dwgname: str) -> int:
        """Abre e carrega um desenho existente.

        Args:
            dwgname: Nome do desenho.

        Returns:
            ``0`` se abriu Ok, ``!= 0`` se não abriu.
        """
        # Fecha qualquer desenho aberto e re-inicializa o módulo de acesso
        self.Close ()
        self.m_dwg.m_acessol.ACL_INIACESSO ()
        self.m_dwg.m_nomedwg = dwgname
        parnomedwg  = ctypes.c_char_p (self.m_dwg.m_nomedwg.encode(TQS.TQSUtil.CHARSET))
        istat       = 0
        paristat    = ctypes.c_int (istat)
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        # g_extopn carrega o arquivo do disco e devolve um novo pedmv
        self.m_dwg.m_mdwg.g_extopn (parnomedwg, ctypes.byref(paristat),
                              None, ctypes.byref(parpedmv))
        self.m_dwg.m_pedmv = parpedmv.value
        istat       = paristat.value
        if         istat != 0:
            TQS.TQSUtil.writef ("Nao abri o desenho [%s]"% self.m_dwg.m_nomedwg)
        else:
            # Sucesso: sincroniza variáveis de cotagem, ativa leitura de blocos e cores
            self.m_dwg.m_mdwg.COTIFOR (parpedmv)
            self.m_dwg.m_mdwg.g_extpbl (parpedmv)
            self.m_dwg.CarregarCores ()
        return        istat


    def Close (self) -> None:
        """Fecha o desenho atual sem salvar."""
        # Só chama g_extclo se houver pedmv válido; depois zera o handle
        if self.m_dwg.m_pedmv != 0:
            par = ctypes.c_void_p (self.m_dwg.m_pedmv)
            self.m_dwg.m_mdwg.g_extclo (par)
        self.m_dwg.m_pedmv = 0


    def Save (self) -> None:
        """Salva o desenho com o nome atual sem fechar o arquivo."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_rectam (parpedmv)
        self.m_dwg.m_mdwg.g_desslvcon (parpedmv)


    def SaveAs (self, dwgname: str) -> None:
        """Salva o desenho com o nome fornecido.

        Detecta extensões ``.DXF`` e ``.PDF`` e salva em formato apropriado;
        do contrário, salva no formato nativo TQS.

        Args:
            dwgname: Nome do desenho a salvar.
        """
        self.m_dwg.m_nomedwg = dwgname
        parpedmv    = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pardwgname  = ctypes.c_char_p (dwgname.encode(TQS.TQSUtil.CHARSET))
        istat       = 0
        paristat    = ctypes.c_int (istat)
        # Despacha pelo formato detectado pela extensão
        if         dwgname.upper ().find (".DXF") >= 0:
            self.m_dwg.m_mdwg.g_salvarcomodxf (parpedmv, pardwgname, ctypes.byref (paristat))
            istat   = paristat.value
            if        istat != 0:
                TQS.TQSUtil.writef ("Erro salvando DXF: [%s]" % dwgname)
                return
        elif    dwgname.upper ().find (".PDF") >= 0:
            # PDF requer escala atual do desenho para dimensionamento da página
            dimsca  = self.m_dwg.settings.scale
            pardimsca = ctypes.c_double (dimsca)
            self.m_dwg.m_mdwg.g_salvarcomopdf (parpedmv, pardwgname, pardimsca, ctypes.byref (paristat))
            istat   = paristat.value
            if        istat != 0:
                TQS.TQSUtil.writef ("Erro salvando PDF: [%s]" % dwgname)
                return
        else:
            # Formato nativo TQS: renomeia, recalcula limites, marca e grava
            self.m_dwg.m_mdwg.g_edmrdn (parpedmv, pardwgname)
            self.m_dwg.m_mdwg.g_rectam (parpedmv)
            self.m_dwg.m_mdwg.g_edmdsn (parpedmv)
            self.m_dwg.m_mdwg.g_desslvcon (parpedmv)


    def Name (self) -> str:
        """Retorna o nome do desenho atual.

        Returns:
            Nome do desenho.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pardwgname  = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.g_edmdwgfil (parpedmv, pardwgname)
        return      pardwgname.value.decode(TQS.TQSUtil.CHARSET)


    def PurgeBlocks (self) -> None:
        """Elimina blocos não utilizados do desenho."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_purgeblk (parpedmv)


    def PurgeLevels (self) -> None:
        """Elimina níveis não utilizados do desenho."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_purgelay (parpedmv)


    def LoadColors (self) -> None:
        """Carrega a tabela padrão de cores associada ao sistema/subsistema.

        O sistema e subsistema devem ser definidos antes desta chamada.
        """
        self.m_dwg.CarregarCores ()


    def IsModified (self) -> int:
        """Retorna se o desenho foi modificado depois de aberto.

        Returns:
            ``1`` se modificado, ``0`` caso contrário.
        """
        parpedmv    = ctypes.c_void_p (self.m_dwg.m_pedmv)
        istat       = 0
        paristat    = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_modver (parpedmv,  ctypes.byref (paristat))
        istat       = paristat.value
        return      istat


    def IsModifiedAfterCreation (self) -> int:
        """Retorna se o desenho foi modificado por edição gráfica após sua criação.

        Returns:
            ``1`` se modificado por edição gráfica, ``0`` caso contrário.
        """
        parpedmv    = ctypes.c_void_p (self.m_dwg.m_pedmv)
        imodificado = 0
        parimodificado = ctypes.c_int (imodificado)
        self.m_dwg.m_mdwg.g_edmexlerimodificado (parpedmv, ctypes.byref (parimodificado))
        imodificado = parimodificado.value
        return      imodificado


    def IsOutOfProject (self) -> int:
        """Retorna se o desenho foi retirado do projeto.

        Returns:
            ``1`` se foi retirado do projeto, ``0`` caso contrário.
        """
        parpedmv        = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iforadoproj     = 0
        pariforadoproj  = ctypes.c_int (iforadoproj)
        self.m_dwg.m_mdwg.g_edmexleriforadoproj (parpedmv, ctypes.byref (pariforadoproj))
        iforadoproj     = pariforadoproj.value
        return          iforadoproj


    def IsVerified (self) -> int:
        """Retorna se o desenho foi verificado pelo engenheiro.

        Returns:
            ``1`` se verificado, ``0`` caso contrário.
        """
        parpedmv        = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iverificado     = 0
        pariverificado  = ctypes.c_int (iverificado)
        self.m_dwg.m_mdwg.g_edmexleriverificado (parpedmv, ctypes.byref (pariverificado))
        iverificado     = pariverificado.value
        return          iverificado

#-----------------------------------------------------------------------------
#    Comandos inserção de elementos gráficos no desenho
#
class Draw ():
    """Inserção de elementos gráficos no desenho. Unidades: cm e graus.

    Implementação:
        Cada primitiva (linha, arco, círculo, texto, polyline, bloco)
        é um wrapper fino sobre uma função ``g_des*`` de ``MDWG.DLL``.
        Coordenadas são embrulhadas em ``ctypes.c_double``; cores, níveis,
        estilos em ``ctypes.c_int``; nomes de bloco e textos em
        ``ctypes.c_char_p`` codificados em ``TQSUtil.CHARSET``. As
        propriedades de nível/cor/estilo lêem ou definem variáveis de
        estado do desenho através de ``g_deslerXXX``/``g_desXXX``.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de desenho.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg  = dwg

    def Line  (self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Desenha uma linha entre dois pontos.

        Args:
            x1: X do ponto 1 (cm).
            y1: Y do ponto 1 (cm).
            x2: X do ponto 2 (cm).
            y2: Y do ponto 2 (cm).
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parx1        = ctypes.c_double (x1)
        pary1        = ctypes.c_double (y1)
        parx2        = ctypes.c_double (x2)
        pary2        = ctypes.c_double (y2)
        self.m_dwg.m_mdwg.g_deslin (parpedmv,
            ctypes.byref (parx1), ctypes.byref (pary1),
            ctypes.byref (parx2), ctypes.byref (pary2))

    def Rectangle (self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Desenha um retângulo entre dois pontos.

        Args:
            x1: X do canto esquerdo inferior (cm).
            y1: Y do canto esquerdo inferior (cm).
            x2: X do canto direito superior (cm).
            y2: Y do canto direito superior (cm).
        """
        # Retângulo é uma polyline fechada de 5 pontos (último igual ao primeiro)
        self.PolyStart ()
        self.PolyEnterPoint (x1, y1)
        self.PolyEnterPoint (x2, y1)
        self.PolyEnterPoint (x2, y2)
        self.PolyEnterPoint (x1, y2)
        self.PolyEnterPoint (x1, y1)
        self.Polyline ()

    def PolyStart (self) -> None:
        """Inicia a acumulação de pontos por :meth:`PolyEnterPoint`.

        Os pontos acumulados podem ser usados em :meth:`Polyline`,
        :meth:`PolylineFilled` e :meth:`PolylineCurve`.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_despolyiniciar (parpedmv)

    def PolyEnterPoint  (self, x: float, y: float) -> None:
        """Acumula um ponto de uma polyline.

        Os pontos acumulados podem ser usados em :meth:`Polyline`,
        :meth:`PolylineFilled` e :meth:`PolylineCurve`.

        Args:
            x: Coordenada X do ponto (cm).
            y: Coordenada Y do ponto (cm).
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parx        = ctypes.c_double (x)
        pary        = ctypes.c_double (y)
        self.m_dwg.m_mdwg.g_despolyentrar (parpedmv, ctypes.byref (parx), ctypes.byref (pary))

    def PolyEnterXY  (self, xy: List[List[float]]) -> None:
        """Acumula um vetor de pontos para uma polyline.

        Os pontos acumulados podem ser usados em :meth:`Polyline`,
        :meth:`PolylineFilled` e :meth:`PolylineCurve`.

        Args:
            xy: Lista de pontos no formato ``[[x1,y1], [x2,y2], ...]``.
        """
        # Inicia acumulação e empilha cada ponto via PolyEnterPoint
        self.PolyStart ()
        for pt in xy:
            self.PolyEnterPoint (pt [0], pt [1])

    def Polyline  (self) -> None:
        """Desenha uma polyline com os pontos acumulados por :meth:`PolyEnterPoint`."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_despolypln (parpedmv)

    def PolylineFilled (self) -> None:
        """Desenha uma polyline preenchida com os pontos acumulados."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_despolyplnp (parpedmv)

    def PolylineCurve (self) -> None:
        """Desenha uma polyline curva com os pontos acumulados."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_despolycur (parpedmv)

    def Arc (self, xc: float, yc: float, r: float, angi: float, angf: float) -> None:
        """Desenha um arco por centro, raio e ângulos inicial e final.

        Args:
            xc: Abscissa do centro (cm).
            yc: Ordenada do centro (cm).
            r: Raio (cm).
            angi: Ângulo inicial (graus), sentido anti-horário.
            angf: Ângulo final (graus), sentido anti-horário.
        """
        parpedmv    = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parxc      = ctypes.c_double (xc)
        paryc      = ctypes.c_double (yc)
        parr       = ctypes.c_double (r)
        parangi    = ctypes.c_double (angi)
        parangf    = ctypes.c_double (angf)
        self.m_dwg.m_mdwg.g_desarc (parpedmv,
            ctypes.byref (parxc), ctypes.byref (paryc), ctypes.byref (parr),
            ctypes.byref (parangi), ctypes.byref (parangf))

    def Circle (self, xc: float, yc: float, r: float) -> None:
        """Desenha um círculo por centro e raio.

        Args:
            xc: Abscissa do centro (cm).
            yc: Ordenada do centro (cm).
            r: Raio (cm).
        """
        parpedmv    = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parxc      = ctypes.c_double (xc)
        paryc      = ctypes.c_double (yc)
        parr       = ctypes.c_double (r)
        self.m_dwg.m_mdwg.g_descrc (parpedmv,
            ctypes.byref (parxc), ctypes.byref (paryc), ctypes.byref (parr))

    def Text (self, x: float, y: float, h: float, ang: float, text: str) -> None:
        """Insere um texto em coordenadas, altura e ângulo fornecidos.

        Args:
            x: Coordenada X do ponto de inserção (cm).
            y: Coordenada Y do ponto de inserção (cm).
            h: Altura (cm).
            ang: Ângulo (graus), sentido anti-horário.
            text: Texto a desenhar.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parx        = ctypes.c_double (x)
        pary        = ctypes.c_double (y)
        parh        = ctypes.c_double (h)
        parang      = ctypes.c_double (ang)
        partext     = ctypes.c_char_p (text.encode(TQS.TQSUtil.CHARSET))
        self.m_dwg.m_mdwg.g_desatx (parpedmv, ctypes.byref (parh))
        self.m_dwg.m_mdwg.g_desang (parpedmv, ctypes.byref (parang))
        self.m_dwg.m_mdwg.g_destex (parpedmv, ctypes.byref (parx),
                                    ctypes.byref (pary), partext)

    def BlockOpen (self, blockname: str, xbase: float, ybase: float) -> None:
        """Inicia a criação de um novo bloco interno.

        Elementos gráficos criados a seguir (ex.: :meth:`Line`) entrarão
        dentro do bloco.

        Args:
            blockname: Nome do bloco.
            xbase: X da base do bloco; coincidirá com o ponto de inserção.
            ybase: Y da base do bloco.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parblockname= ctypes.c_char_p (blockname.encode(TQS.TQSUtil.CHARSET))
        parxbase    = ctypes.c_double (xbase)
        parybase    = ctypes.c_double (ybase)
        icond       = 1        # Overlap
        paricond    = ctypes.c_int (icond)
        self.m_dwg.m_mdwg.g_opnblx (parpedmv, parblockname,
                ctypes.byref (parxbase), ctypes.byref (parybase), ctypes.byref (paricond))

    def BlockClose (self) -> None:
        """Encerra a criação de um bloco interno."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_desfbl (parpedmv)

    def BlockInsert (self, blockname: str, x: float, y: float, escx: float,
                     escy: float, ang: float) -> None:
        """Insere um bloco interno pré-definido.

        Args:
            blockname: Nome do bloco.
            x: X do ponto de inserção (cm).
            y: Y do ponto de inserção (cm).
            escx: Escala X.
            escy: Escala Y.
            ang: Ângulo de inserção (graus), sentido anti-horário.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parblockname= ctypes.c_char_p (blockname.encode(TQS.TQSUtil.CHARSET))
        parx        = ctypes.c_double (x)
        pary        = ctypes.c_double (y)
        parescx     = ctypes.c_double (escx)
        parescy     = ctypes.c_double (escy)
        parang      = ctypes.c_double (ang)
        self.m_dwg.m_mdwg.g_desins (parpedmv, parblockname,
                  ctypes.byref (parx), ctypes.byref (pary),
                  ctypes.byref (parescx), ctypes.byref (parescy),
                  ctypes.byref (parang))

    def BlockLoadFromDwg  (self, dwgname: str) -> int:
        """Carrega um arquivo externo e o transforma em bloco interno.

        Args:
            dwgname: Nome do arquivo de desenho com o bloco.

        Returns:
            ``0`` se carregou, ``1`` em caso de erro.
        """
        parpedmv    = ctypes.c_void_p (self.m_dwg.m_pedmv)
        dir        = ""
        pardir     = ctypes.c_char_p (dir.encode(TQS.TQSUtil.CHARSET))
        pardwgname = ctypes.c_char_p (dwgname.encode(TQS.TQSUtil.CHARSET))
        istat      = 0
        paristat   = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_inilbk (parpedmv, pardir, pardwgname, ctypes.byref (paristat))
        istat      = paristat.value
        return     istat

    @property
    def level (self) -> int:
        """Nível atual de desenho, sempre na forma numérica."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        nivel       = 0
        parnivel    = ctypes.c_int (nivel)
        self.m_dwg.m_mdwg.g_desvnv (parpedmv, ctypes.byref (parnivel))
        nivel       = parnivel.value
        return      nivel

    @level.setter
    def level (self, level: Union[int, str]) -> None:
        """Atribui Nível atual de desenho, sempre na forma numérica."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        slevel      = level
        if        level is not str:
            slevel  = str (level)
        parlevel    = ctypes.c_char_p (slevel.encode(TQS.TQSUtil.CHARSET))
        nivel       = 0
        parnivel    = ctypes.c_int (nivel)
        self.m_dwg.m_mdwg.g_desnivalfa (parpedmv, parlevel, ctypes.byref (parnivel))
        nivel       = parnivel.value

    @property
    def style (self) -> int:
        """Estilo atual de desenho ou ``-1`` para usar o estilo associado ao nível."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iestilo     = 0
        pariestilo  = ctypes.c_int (iestilo)
        self.m_dwg.m_mdwg.g_deslerstl (parpedmv, ctypes.byref (pariestilo))
        iestilo     = pariestilo.value
        return      iestilo

    @style.setter
    def style (self, istyle: int) -> None:
        """Atribui Estilo atual de desenho ou ``-1`` para usar o estilo associado ao nível."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariestilo  = ctypes.c_int (istyle)
        self.m_dwg.m_mdwg.g_desstl (parpedmv, ctypes.byref (pariestilo))

    @property
    def color (self) -> int:
        """Cor atual de desenho (``1..255``) ou ``-1`` para usar a cor do nível."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        icor           = 0
        paricor        = ctypes.c_int (icor)
        self.m_dwg.m_mdwg.g_deslercor (parpedmv, ctypes.byref (paricor))
        icor           = paricor.value
        return         icor

    @color.setter
    def color (self, icolor: int) -> None:
        """Atribui Cor atual de desenho (``1..255``) ou ``-1`` para usar a cor do nível."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        paricor        = ctypes.c_int (icolor)
        self.m_dwg.m_mdwg.g_descor (parpedmv, ctypes.byref (paricor))


    @property
    def textAlignment (self) -> int:
        """Alinhamento de texto não proporcional: ``0`` esquerda, ``1`` centro, ``2`` direita."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        ialintxt       = 0
        parialintxt    = ctypes.c_int (ialintxt)
        self.m_dwg.m_mdwg.g_deslerialintxt (parpedmv, ctypes.byref (parialintxt))
        ialintxt       = parialintxt.value
        return         ialintxt

    @textAlignment.setter
    def textAlignment (self, ialintxt: int) -> None:
        """Atribui Alinhamento de texto não proporcional: ``0`` esquerda, ``1`` centro, ``2`` direita."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parialintxt    = ctypes.c_int (ialintxt)
        self.m_dwg.m_mdwg.g_desialintxt (parpedmv, ctypes.byref (parialintxt))


    def DwgMix  (self, dwgname: str, deltax: float, deltay: float) -> int:
        """Mistura um desenho externo com o desenho atual.

        Args:
            dwgname: Nome do desenho a misturar.
            deltax: Deslocamento aplicado ao desenho misturado em X (cm).
            deltay: Deslocamento aplicado ao desenho misturado em Y (cm).

        Returns:
            ``0`` se a mistura foi feita Ok, ``1`` em caso de erro.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pardwgname  = ctypes.c_char_p (dwgname.encode(TQS.TQSUtil.CHARSET))
        pardeltax   = ctypes.c_double (deltax)
        pardeltay   = ctypes.c_double (deltay)
        istat       = 0
        paristat    = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_inimix (parpedmv, pardwgname,
                         ctypes.byref (pardeltax), ctypes.byref (pardeltay),
                         ctypes.byref (paristat))
        istat       = paristat.value
        return      istat

    def XrefInsert  (self, dwgname: str, deltax: float, deltay: float, ang: float) -> int:
        """Insere um desenho de referência externa.

        Args:
            dwgname: Nome do desenho.
            deltax: Deslocamento adicional X.
            deltay: Deslocamento adicional Y.
            ang: Ângulo de rotação (graus).

        Returns:
            ``0`` se inseriu, ``1`` em caso de erro.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pardwgname  = ctypes.c_char_p (dwgname.encode(TQS.TQSUtil.CHARSET))
        parblockname= ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        istat       = 0
        paristat    = ctypes.c_int (istat)
        index       = 0
        parindex    = ctypes.c_int (index)
        # Procura se a XRef já existe registrada no desenho
        self.m_dwg.m_mdwg.refx_acharef (parpedmv, pardwgname, ctypes.byref (parindex))
        index       = parindex.value
        if        index >= 0:
            # Já registrada: apenas lê dados; rejeita se for XRef interna
            interna    = 0
            parinterna = ctypes.c_int (interna)
            pardwgname = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
            pedmref    = 0
            parpedmref = ctypes.c_void_p (pedmref)
            ligada     = 0
            parligada  = ctypes.c_int (ligada)
            self.m_dwg.m_mdwg.refx_ler (parpedmv, parindex, ctypes.byref (parinterna),
                                 pardwgname, ctypes.byref (parpedmref),
                                 ctypes.byref (parligada), parblockname)
            interna    = parinterna.value
            if        interna != 0:
                return    1
            istat     = 0
        else:
            # Não registrada: cria nova XRef externa apontando para o arquivo
            self.m_dwg.m_mdwg.refx_criaexterno (parpedmv, pardwgname, parblockname,
                                            ctypes.byref (paristat))
            istat     = paristat.value

        if        istat != 0:
            return  istat
        # Insere o bloco da XRef no ponto/ângulo solicitado
        blockname   = parblockname.value.decode(TQS.TQSUtil.CHARSET)
        escx        = 1.
        escy        = 1.
        self.BlockInsert (blockname, deltax, deltay, escx, escy, ang)
        return        istat

#-----------------------------------------------------------------------------
#    Leitura de limites do DWG
#
class Limits ():
    """Leitura e definição dos limites geométricos do desenho.

    Implementação:
        Métodos chamam ``g_loaext``/``g_ledext``/``g_letam``/``g_defdwv`` de
        ``MDWG.DLL`` passando quatro doubles por referência (``xmin, ymin,
        xmax, ymax``) que são lidos via ``.value`` após a chamada.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de limites.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg     = dwg

    def FileLimits (self, dwgname: str) -> Tuple[float, float, float, float, int]:
        """Retorna os limites de um desenho sem carregá-lo na memória.

        Args:
            dwgname: Nome do arquivo de desenho.

        Returns:
            Tupla ``(xmin, ymin, xmax, ymax, istat)`` com ``istat == 0`` se
            leu o arquivo, ``1`` se não leu.
        """
        pardwgname     = ctypes.c_char_p (dwgname.encode(TQS.TQSUtil.CHARSET))
        xmin           = 0.
        ymin           = 0.
        xmax           = 0.
        ymax           = 0.
        parxmin        = ctypes.c_double (xmin)
        parymin        = ctypes.c_double (ymin)
        parxmax        = ctypes.c_double (xmax)
        parymax        = ctypes.c_double (ymax)
        xmin2          = 0.
        ymin2          = 0.
        xmax2          = 0.
        ymax2          = 0.
        parxmin2       = ctypes.c_double (xmin2)
        parymin2       = ctypes.c_double (ymin2)
        parxmax2       = ctypes.c_double (xmax2)
        parymax2       = ctypes.c_double (ymax2)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_loaext (pardwgname,
            ctypes.byref (parxmin) , ctypes.byref (parymin),
            ctypes.byref (parxmax) , ctypes.byref (parymax),
            ctypes.byref (parxmin2), ctypes.byref (parymin2),
            ctypes.byref (parxmax2), ctypes.byref (parymax2),
            ctypes.byref (paristat))
        xmin           = parxmin.value
        ymin           = parymin.value
        xmax           = parxmax.value
        ymax           = parymax.value
        istat          = paristat.value
        return         xmin, ymin, xmax, ymax, istat

    def DwgLimits (self) -> Tuple[float, float, float, float]:
        """Lê os limites do desenho atual.

        Returns:
            Tupla ``(xmin, ymin, xmax, ymax)``.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        xmin           = 0.
        ymin           = 0.
        xmax           = 0.
        ymax           = 0.
        parxmin        = ctypes.c_double (xmin)
        parymin        = ctypes.c_double (ymin)
        parxmax        = ctypes.c_double (xmax)
        parymax        = ctypes.c_double (ymax)
        self.m_dwg.m_mdwg.g_ledext (parpedmv,
            ctypes.byref (parxmin) , ctypes.byref (parymin),
            ctypes.byref (parxmax) , ctypes.byref (parymax))
        xmin           = parxmin.value
        ymin           = parymin.value
        xmax           = parxmax.value
        ymax           = parymax.value
        return         xmin, ymin, xmax, ymax

    def UpdateLimits (self) -> None:
        """Recalcula os limites do desenho atual."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_rectam (parpedmv)

    def WindowLimits (self) -> Tuple[float, float, float, float]:
        """Lê a janela inicial do desenho no EAG.

        Returns:
            Tupla ``(xmin, ymin, xmax, ymax)``.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        xmin           = 0.
        ymin           = 0.
        xmax           = 0.
        ymax           = 0.
        parxmin        = ctypes.c_double (xmin)
        parymin        = ctypes.c_double (ymin)
        parxmax        = ctypes.c_double (xmax)
        parymax        = ctypes.c_double (ymax)
        self.m_dwg.m_mdwg.g_letam (parpedmv,
            ctypes.byref (parxmin) , ctypes.byref (parymin),
            ctypes.byref (parxmax) , ctypes.byref (parymax))
        xmin           = parxmin.value
        ymin           = parymin.value
        xmax           = parxmax.value
        ymax           = parymax.value
        return         xmin, ymin, xmax, ymax

    def DefineWindowLimits (self, xmin: float, ymin: float, xmax: float, ymax: float) -> None:
        """Define a janela inicial do desenho no EAG.

        ATENÇÃO: a biblioteca TQS descarta os quatro argumentos — eles são
        zerados antes da chamada nativa, que sempre recebe ``(0, 0, 0, 0)``.
        Chamar este método não define a janela pedida. Não há alternativa
        pública neste wrapper; documentado aqui para evitar código que
        dependa de um enquadramento inicial que não ocorre.

        Args:
            xmin: Aceito e ignorado pela biblioteca.
            ymin: Aceito e ignorado pela biblioteca.
            xmax: Aceito e ignorado pela biblioteca.
            ymax: Aceito e ignorado pela biblioteca.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        xmin           = 0.
        ymin           = 0.
        xmax           = 0.
        ymax           = 0.
        parxmin        = ctypes.c_double (xmin)
        parymin        = ctypes.c_double (ymin)
        parxmax        = ctypes.c_double (xmax)
        parymax        = ctypes.c_double (ymax)
        self.m_dwg.m_mdwg.g_defdwv (parpedmv,
            ctypes.byref (parxmin) , ctypes.byref (parymin),
            ctypes.byref (parxmax) , ctypes.byref (parymax))

#-----------------------------------------------------------------------------
#    Iteração de elementos no DWG
#
class Iterator ():
    """Iteração de elementos do desenho com leitura de atributos individuais.

    Após posicionar com :meth:`Begin` e avançar com :meth:`Next`, as
    propriedades expõem dados do elemento corrente (linha, texto, polyline,
    bloco etc.).

    Implementação:
        ``Begin``/``Next``/``SetPosition`` movimentam o cursor interno do
        desenho via ``g_extrew``/``g_extpeg``/``g_extpnt``. Cada propriedade
        (``itype``, ``text``, ``radius``, ``blockName`` etc.) lê uma variável
        nomeada do elemento corrente através de ``g_extgra_ler_int``,
        ``g_extgra_ler_double``, ``g_extgra_ler_string`` ou
        ``g_extgra_ler_xy``, conforme o tipo. O dicionário ``tipoobj`` mapeia
        ``DWGTYPE_*`` para descrições legíveis usadas em diagnóstico.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de iteração.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg  = dwg
        self.tipoobj = dict ((
            [DWGTYPE_LINE     , "Linha"],
            [DWGTYPE_TEXT     , "Texto"],
            [DWGTYPE_POLYLINE , "Polyline"],
            [DWGTYPE_BLOCK    , "Bloco"],
            [DWGTYPE_BLOCKEND , "Fim de bloco"],
            [DWGTYPE_CIRCLE   , "Circulo"],
            [DWGTYPE_ARC      , "Arco"],
            [DWGTYPE_CURVE    , "Curva"],
            [DWGTYPE_OBJECT   , "Objeto"],
            [DWGTYPE_OBJECTEND, "Fim de objeto"],
            ))

    def Begin (self) -> None:
        """Posiciona o desenho para leitura no início."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_extrew (parpedmv)

    def Next (self) -> int:
        """Lê o próximo elemento do desenho.

        Returns:
            Tipo ``iterator.DWGTYPE_xxxx`` (``DWGTYPE_EOF`` ao final).
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        # Avança o cursor; istat != 0 indica EOF e itype permanece DWGTYPE_EOF
        self.m_dwg.m_mdwg.g_extpeg (parpedmv, ctypes.byref (paristat))
        istat          = paristat.value
        itype          = DWGTYPE_EOF
        if             istat == 0:
            itype      = self.itype
        return         itype


    @property
    def itype (self) -> int:
        """Tipo ``DWGTYPE_xxxx`` do elemento gráfico lido."""
        itipo          = DWGTYPE_EOF
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iextip".encode(TQS.TQSUtil.CHARSET))
        paritipo       = ctypes.c_int (itipo)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (paritipo))
        itipo          = paritipo.value
        return         itipo

    @property
    def elementName (self) -> str:
        """Nome textual do tipo do elemento gráfico lido."""
        nome           = "Indefinido"
        itipo          = self.itype
        if             itipo in self.tipoobj:
            nome       = self.tipoobj [itipo]
        return         nome

    def SetPosition (self, addr: int) -> None:
        """Posiciona para leitura na posição ``addr``.

        Args:
            addr: Endereço do elemento.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr        = ctypes.c_void_p (addr)
        self.m_dwg.m_mdwg.g_extpnt (parpedmv, ctypes.byref (pariadr))

    def GetElementReadPosition (self) -> int:
        """Retorna a posição do último elemento lido.

        Returns:
            Endereço do último elemento lido.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        addr           = 0
        pariadr        = ctypes.c_void_p (addr)
        itype          = DWGTYPE_EOF
        paritype       = ctypes.c_int (itype)
        self.m_dwg.m_mdwg.g_extpnr (parpedmv, ctypes.byref (pariadr),
            ctypes.byref (paritype))
        addr           = pariadr.value
        return         addr

    def GetElementWritePosition (self) -> int:
        """Retorna a posição do último elemento gravado.

        Returns:
            Endereço do último elemento gravado.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        addr           = 0
        pariadr        = ctypes.c_void_p (addr)
        self.m_dwg.m_mdwg.g_extpng (parpedmv, ctypes.byref (pariadr))
        addr           = pariadr.value
        return         addr

    def GetReadPosition (self) -> int:
        """Retorna a posição do próximo elemento a ser lido.

        Returns:
            Endereço do próximo elemento a ler.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        addr           = 0
        pariadr        = ctypes.c_void_p (addr)
        self.m_dwg.m_mdwg.g_extprr (parpedmv, ctypes.byref (pariadr))
        addr           = pariadr.value
        return         addr

    def GetWritePosition (self) -> int:
        """Retorna a posição do próximo elemento a ser gravado.

        Returns:
            Endereço do próximo elemento a gravar.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        addr           = 0
        pariadr        = ctypes.c_void_p (addr)
        self.m_dwg.m_mdwg.g_extpnw (parpedmv, ctypes.byref (pariadr))
        addr           = pariadr.value
        return         addr

    def SetBlockPosition (self, blockname: str) -> int:
        """Posiciona para leitura dos elementos internos a um bloco.

        Args:
            blockname: Nome do bloco.

        Returns:
            ``0`` se Ok, ``1`` se o bloco não existe.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parblockname   = ctypes.c_char_p (blockname.encode(TQS.TQSUtil.CHARSET))
        addr           = 0
        pariadr        = ctypes.c_void_p (addr)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_extpbr (parpedmv, parblockname, ctypes.byref (pariadr),
                                    ctypes.byref (paristat))
        istat          = paristat.value
        return         istat

    def CopyReadAtribbutes (self) -> None:
        """Copia os atributos do último elemento lido para o próximo a gravar."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_descopyatr (parpedmv)

    def GetPolylinePt (self, ipt: int) -> Tuple[float, float]:
        """Retorna as coordenadas ``x, y`` do ponto ``ipt`` da poligonal.

        Args:
            ipt: Índice do ponto, ``0..xySize-1``.

        Returns:
            Tupla ``(x, y)`` do ponto.
        """
        # Valida o índice contra xySize antes de chamar a DLL
        if             ipt < 0 or ipt >= self.xySize:
            TQS.TQSUtil.writef ("Indice invalido de ponto %d/%d" % (ipt, self.xySize))
            return     0., 0.
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extxy".encode(TQS.TQSUtil.CHARSET))
        paript         = ctypes.c_int (ipt)
        x              = 0.
        parx           = ctypes.c_double (x)
        y              = 0.
        pary           = ctypes.c_double (y)
        self.m_dwg.m_mdwg.g_extgra_ler_xy (parpedmv, parnomvar, ctypes.byref (paript),
                                           ctypes.byref (parx), ctypes.byref (pary))
        x              = parx.value
        y              = pary.value
        return         x, y

    @property
    def x1 (self) -> float:
        """X1 de linha/texto/inserção de bloco."""
        x, y           = self.GetPolylinePt (0)
        return         x

    @property
    def y1 (self) -> float:
        """Y1 de linha/texto/inserção de bloco."""
        x, y           = self.GetPolylinePt (0)
        return         y

    @property
    def x2 (self) -> float:
        """X2 de linha."""
        x, y           = self.GetPolylinePt (1)
        return         x

    @property
    def y2 (self) -> float:
        """Y2 de linha."""
        x, y           = self.GetPolylinePt (1)
        return         y

    @property
    def xySize (self) -> int:
        """Número de pontos da poligonal."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iexnp".encode(TQS.TQSUtil.CHARSET))
        np             = 0
        parnp          = ctypes.c_int (np)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (parnp))
        np             = parnp.value
        return         np

    @property
    def xy (self) -> List[List[float]]:
        """Matriz inteira de pontos da poligonal no formato ``[[x,y], ...]``."""
        # Itera pelos np pontos da poligonal corrente acumulando em lista Python
        np             = self.xySize
        xy             = []
        for            ipt in range (0, np):
            x, y       = self.GetPolylinePt (ipt)
            xy.append  ([x, y])
        return         xy

    @property
    def isFilled (self) -> int:
        """``1`` se a poligonal atual é preenchida, ``0`` caso contrário."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        ipreenche      = 0
        paripreenche   = ctypes.c_int (ipreenche)
        self.m_dwg.m_mdwg.g_verpolypre (parpedmv, ctypes.byref (paripreenche))
        ipreenche      = paripreenche.value
        return         ipreenche

    @property
    def xc (self) -> float:
        """X do centro de arco/círculo."""
        x, y           = self.GetPolylinePt (0)
        return         x

    @property
    def yc (self) -> float:
        """Y do centro de arco/círculo."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        x, y           = self.GetPolylinePt (0)
        return         y

    @property
    def radius (self) -> float:
        """Raio de um arco/círculo."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extlrg".encode(TQS.TQSUtil.CHARSET))
        radiusx        = 0.
        parradius      = ctypes.c_double (radiusx)
        self.m_dwg.m_mdwg.g_extgra_ler_double (parpedmv, parnomvar, ctypes.byref (parradius))
        radiusx        = parradius.value
        return         radiusx

    @property
    def startAngle (self) -> float:
        """Ângulo inicial de um arco (graus)."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extalt".encode(TQS.TQSUtil.CHARSET))
        angi           = 0.
        parangi        = ctypes.c_double (angi)
        self.m_dwg.m_mdwg.g_extgra_ler_double (parpedmv, parnomvar, ctypes.byref (parangi))
        angi           = parangi.value
        return         angi

    @property
    def endAngle (self) -> float:
        """Ângulo final de um arco (graus)."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extang".encode(TQS.TQSUtil.CHARSET))
        angf           = 0.
        parangf        = ctypes.c_double (angf)
        self.m_dwg.m_mdwg.g_extgra_ler_double (parpedmv, parnomvar, ctypes.byref (parangf))
        angf           = parangf.value
        return         angf

    @property
    def textHeight (self) -> float:
        """Altura do último texto lido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extalt".encode(TQS.TQSUtil.CHARSET))
        alttxt         = 0.
        paralttxt      = ctypes.c_double (alttxt)
        self.m_dwg.m_mdwg.g_extgra_ler_double (parpedmv, parnomvar, ctypes.byref (paralttxt))
        alttxt         = paralttxt.value
        return         alttxt

    @property
    def textAngle (self) -> float:
        """Ângulo do último texto lido (graus)."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extang".encode(TQS.TQSUtil.CHARSET))
        angf           = 0.
        parangf        = ctypes.c_double (angf)
        self.m_dwg.m_mdwg.g_extgra_ler_double (parpedmv, parnomvar, ctypes.byref (parangf))
        angf           = parangf.value
        return         angf

    @property
    def textLength (self) -> int:
        """Número de caracteres do texto lido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iexnc".encode(TQS.TQSUtil.CHARSET))
        nc             = 0
        parnc          = ctypes.c_int (nc)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (parnc))
        nc             = parnc.value
        return         nc

    @property
    def text (self) -> str:
        """Texto lido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iextxt".encode(TQS.TQSUtil.CHARSET))
        partxt         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.g_extgra_ler_string (parpedmv, parnomvar, partxt)
        return         partxt.value.decode(TQS.TQSUtil.CHARSET)

    @property
    def blockName (self) -> str:
        """Nome do bloco inserido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extnomblo".encode(TQS.TQSUtil.CHARSET))
        parnomblo      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.g_extgra_ler_string (parpedmv, parnomvar, parnomblo)
        return         parnomblo.value.decode(TQS.TQSUtil.CHARSET)

    @property
    def xScale (self) -> float:
        """Escala X de um bloco inserido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extesx".encode(TQS.TQSUtil.CHARSET))
        escx           = 0.
        parescx        = ctypes.c_double (escx)
        self.m_dwg.m_mdwg.g_extgra_ler_double (parpedmv, parnomvar, ctypes.byref (parescx))
        escx           = parescx.value
        return         escx

    @property
    def yScale (self) -> float:
        """Escala Y de um bloco inserido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extesy".encode(TQS.TQSUtil.CHARSET))
        escy           = 0.
        parescy        = ctypes.c_double (escy)
        self.m_dwg.m_mdwg.g_extgra_ler_double (parpedmv, parnomvar, ctypes.byref (parescy))
        escy           = parescy.value
        return         escy

    @property
    def insertAngle (self) -> float:
        """Ângulo de um bloco inserido (graus)."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extanb".encode(TQS.TQSUtil.CHARSET))
        angrad         = 0.
        parangrad      = ctypes.c_double (angrad)
        self.m_dwg.m_mdwg.g_extgra_ler_double (parpedmv, parnomvar, ctypes.byref (parangrad))
        angrad         = parangrad.value
        return         angrad * TQS.TQSUtil.RADGRAUS

    @property
    def level (self) -> int:
        """Nível de um elemento lido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iexil".encode(TQS.TQSUtil.CHARSET))
        nivel          = 0
        parnivel       = ctypes.c_int (nivel)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (parnivel))
        nivel          = parnivel.value
        return         nivel

    @property
    def color (self) -> int:
        """Cor (``0..255``) de um elemento lido (considerando o nível)."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iexcor".encode(TQS.TQSUtil.CHARSET))
        icor           = 0
        paricor        = ctypes.c_int (icor)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (paricor))
        icor           = paricor.value
        return         icor

    @property
    def colorRGB (self) -> int:
        """Cor RGB opcional de um elemento lido (considerando o nível)."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iexcorrgb".encode(TQS.TQSUtil.CHARSET))
        icor           = 0
        paricor        = ctypes.c_int (icor)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (paricor))
        icor           = paricor.value
        return         icor

    @property
    def style (self) -> int:
        """Estilo de um elemento lido (considerando o nível)."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iexstl".encode(TQS.TQSUtil.CHARSET))
        iestil         = 0
        pariestil      = ctypes.c_int (iestil)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (pariestil))
        iestil         = pariestil.value
        return         iestil

    @property
    def levelLock (self) -> int:
        """``1`` se o nível do elemento lido está travado."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("itravado".encode(TQS.TQSUtil.CHARSET))
        itrava         = 0
        paritrava      = ctypes.c_int (itrava)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (paritrava))
        itrava         = paritrava.value
        return         itrava

    @property
    def captureable (self) -> int:
        """``1`` se o elemento é capturável."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("icaptura".encode(TQS.TQSUtil.CHARSET))
        icaptura       = 0
        paricaptura    = ctypes.c_int (icaptura)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (paricaptura))
        icaptura       = paricaptura.value
        return         icaptura

    @property
    def textAlignment (self) -> int:
        """Alinhamento de texto não proporcional: ``0`` esquerda, ``1`` centro, ``2`` direita."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("ialintxt".encode(TQS.TQSUtil.CHARSET))#!NTR
        ialintxt       = 0
        parialintxt    = ctypes.c_int (ialintxt)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (parialintxt))
        ialintxt       = parialintxt.value
        return         ialintxt


    @property
    def hasPlotData (self) -> int:
        """``1`` se há informações de plotagem independentes para este elemento."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("ivalid".encode(TQS.TQSUtil.CHARSET))
        itabinfo       = 0
        paritabinfo    = ctypes.c_int (itabinfo)
        self.m_dwg.m_mdwg.g_extgra_ler_tabinfo (parpedmv, parnomvar, ctypes.byref (paritabinfo))
        itabinfo       = paritabinfo.value
        return         itabinfo

    @property
    def plotPen (self) -> int:
        """Pena de plotagem somente se disponível."""
        ipena          = 0
        if             self.hasPlotData != 0:
            parpedmv   = ctypes.c_void_p (self.m_dwg.m_pedmv)
            parnomvar  = ctypes.c_char_p ("ipena".encode(TQS.TQSUtil.CHARSET))
            paripena   = ctypes.c_int (ipena)
            self.m_dwg.m_mdwg.g_extgra_ler_tabinfo (parpedmv, parnomvar, ctypes.byref (paripena))
            ipena      = paripena.value
        return         ipena

    @property
    def plotWeight (self) -> int:
        """Peso de plotagem somente se disponível."""
        ipeso          = 0
        if             self.hasPlotData != 0:
            parpedmv   = ctypes.c_void_p (self.m_dwg.m_pedmv)
            parnomvar  = ctypes.c_char_p ("ipeso".encode(TQS.TQSUtil.CHARSET))
            paripeso   = ctypes.c_int (ipeso)
            self.m_dwg.m_mdwg.g_extgra_ler_tabinfo (parpedmv, parnomvar, ctypes.byref (paripeso))
            ipeso      = paripeso.value
        return         ipeso

    @property
    def plotStyle (self) -> int:
        """Estilo de plotagem se disponível."""
        iestil         = 0
        if             self.hasPlotData != 0:
            parpedmv   = ctypes.c_void_p (self.m_dwg.m_pedmv)
            parnomvar  = ctypes.c_char_p ("iestilo".encode(TQS.TQSUtil.CHARSET))
            pariestil  = ctypes.c_int (iestil)
            self.m_dwg.m_mdwg.g_extgra_ler_tabinfo (parpedmv, parnomvar, ctypes.byref (pariestil))
            iestil     = pariestil.value
        return         iestil

    @property
    def plotFont (self) -> int:
        """Fonte de plotagem se disponível."""
        ifont          = 0
        if             self.hasPlotData != 0:
            parpedmv   = ctypes.c_void_p (self.m_dwg.m_pedmv)
            parnomvar  = ctypes.c_char_p ("ifonte".encode(TQS.TQSUtil.CHARSET))
            parifont   = ctypes.c_int (ifont)
            self.m_dwg.m_mdwg.g_extgra_ler_tabinfo (parpedmv, parnomvar, ctypes.byref (parifont))
            ifont      = parifont.value
        return         ifont

    @property
    def plotHatch (self) -> int:
        """Hachura de plotagem se disponível."""
        ihachura       = 0
        if             self.hasPlotData != 0:
            parpedmv   = ctypes.c_void_p (self.m_dwg.m_pedmv)
            parnomvar  = ctypes.c_char_p ("ihachura".encode(TQS.TQSUtil.CHARSET))
            parihachura= ctypes.c_int (ihachura)
            self.m_dwg.m_mdwg.g_extgra_ler_tabinfo (parpedmv, parnomvar, ctypes.byref (parihachura))
            ihachura   = parihachura.value
        return         ihachura

    @property
    def objectName (self) -> str:
        """Nome do objeto de desenho lido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("nomobj".encode(TQS.TQSUtil.CHARSET))
        parnomeobj     = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.g_extgra_ler_string (parpedmv, parnomvar, parnomeobj)
        return         parnomeobj.value.decode(TQS.TQSUtil.CHARSET)

    @property
    def objectPointer (self) -> int:
        """Apontador do objeto de desenho lido."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("pntobj".encode(TQS.TQSUtil.CHARSET))
        pntobj         = 0
        parpntobj      = ctypes.c_void_p (pntobj)
        self.m_dwg.m_mdwg.g_extgra_ler_pnt (parpedmv, parnomvar, ctypes.byref (parpntobj))
        return         (parpntobj.value)

    @property
    def smartRebar (self) -> Optional["SmartRebar"]:
        """Objeto :class:`SmartRebar` se o objeto extraído é um ferro inteligente, senão ``None``."""
        # Só constrói SmartRebar se o elemento for um objeto inteligente do tipo IPOFER
        rebar          = None
        itype          = self.itype
        if             itype == DWGTYPE_OBJECT:
            if         self.objectName == "IPOFER":
                ferobjv = self.objectPointer
                rebar   = SmartRebar (self.m_dwg, ferobjv)
        return        rebar

    @property
    def inBlock (self) -> int:
        """``1`` se o elemento gráfico lido está dentro de um bloco."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("extblc".encode(TQS.TQSUtil.CHARSET))
        inblock        = 0
        parinblock     = ctypes.c_int (inblock)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (parinblock))
        inblock        = parinblock.value
        return         inblock

    @property
    def inXref (self) -> int:
        """``1`` se o elemento gráfico lido está dentro de uma referência externa."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iexrefext".encode(TQS.TQSUtil.CHARSET))
        inxref         = 0
        parinxref      = ctypes.c_int (inxref)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (parinxref))
        inxref         = parinxref.value
        return         inxref

    @property
    def isOpenObject (self) -> int:
        """``1`` se o elemento gráfico lido está dentro de um objeto inteligente."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnomvar      = ctypes.c_char_p ("iobjaberto".encode(TQS.TQSUtil.CHARSET))
        inobject       = 0
        parinobject    = ctypes.c_int (inobject)
        self.m_dwg.m_mdwg.g_extgra_ler_int (parpedmv, parnomvar, ctypes.byref (parinobject))
        inobject       = parinobject.value
        return         inobject


#-----------------------------------------------------------------------------
#    Acesso a algumas variáveis globais do DWG
#
class Settings ():
    """Acesso a variáveis globais do DWG (sistema, escala, base, modos, grade).

    Implementação:
        Cada propriedade lê/grava um conjunto correlato de variáveis através
        de funções pareadas ``g_edmexlerXXX``/``g_edmexgrvXXX`` ou ``g_extXXX``
        de ``MDWG.DLL``. Métodos privados ``__LerXXX``/``__DefXXX``/``__AlterarXXX``
        encapsulam grupos de variáveis que precisam ser lidas/escritas em
        bloco (sistema/subsistema, escala/multiplicador, base, grade).
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de configurações.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg     = dwg

    def __LerId (self) -> Tuple[int, int]:
        """Lê o sistema/subsistema atual da caixa de propriedades do EAG."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iaplic         = 0
        pariaplic      = ctypes.c_int (iaplic)
        isubsis        = 0
        parisubsis     = ctypes.c_int (isubsis)
        itabela        = 0
        paritabela     = ctypes.c_int (itabela)
        self.m_dwg.m_mdwg.g_edmexlerapli (parpedmv, ctypes.byref (pariaplic),
                          ctypes.byref (parisubsis), ctypes.byref (paritabela))
        iaplic         = pariaplic.value
        isubsis        = parisubsis.value
        return        iaplic, isubsis

    def __AlterarId (self, iaplic: int, isubsis: int) -> None:
        """Altera o sistema/subsistema da caixa de propriedades do EAG."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariaplic      = ctypes.c_int (iaplic)
        parisubsis     = ctypes.c_int (isubsis)
        itabela        = 0
        paritabela     = ctypes.c_int (itabela)
        # Após mudar sistema/subsistema, recarrega cores: a paleta depende do contexto
        self.m_dwg.m_mdwg.g_edmexgrvapli (parpedmv, ctypes.byref (pariaplic),
                          ctypes.byref (parisubsis), ctypes.byref (paritabela))
        self.m_dwg.CarregarCores ()

    @property
    def systemId (self) -> int:
        """Número do sistema (``1..``) na caixa de propriedades do EAG."""
        iaplic, isubsis= self.__LerId ()
        return         iaplic

    @systemId.setter
    def systemId (self, isystemid: int) -> None:
        """Atribui Número do sistema (``1..``) na caixa de propriedades do EAG."""
        iaplic, isubsis= self.__LerId ()
        self.__AlterarId (isystemid, isubsis)

    @property
    def subSystemId (self) -> int:
        """Subsistema (``1..``) na caixa de propriedades do EAG."""
        iaplic, isubsis= self.__LerId ()
        return        isubsis

    @subSystemId.setter
    def subSystemId (self, isubsystem: int) -> None:
        """Atribui Subsistema (``1..``) na caixa de propriedades do EAG."""
        iaplic, isubsis= self.__LerId ()
        self.__AlterarId (iaplic, isubsystem)

    @property
    def rebarDrawing (self) -> int:
        """Retorna ``!= 0`` se este é um desenho de armação."""
        parpedmv        = ctypes.c_void_p (self.m_dwg.m_pedmv)
        itabfer         = 0
        paritabfer      = ctypes.c_int (itabfer)
        self.m_dwg.m_mdwg.g_edmexleritabfer (parpedmv, ctypes.byref (paritabfer))
        itabfer         = paritabfer.value
        return          itabfer

    def __LerEscala (self) -> Tuple[float, float]:
        """Lê a escala (``dimsca``) e o multiplicador (``dimlfc``) atuais."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        dimsca         = 0.
        pardimsca      = ctypes.c_double (dimsca)
        dimlfc         = 0.
        pardimlfc      = ctypes.c_double (dimlfc)
        self.m_dwg.m_mdwg.g_edmexleresc (parpedmv, ctypes.byref (pardimsca),
                                         ctypes.byref (pardimlfc))
        dimsca         = pardimsca.value
        dimlfc         = pardimlfc.value
        return         dimsca, dimlfc

    @property
    def scale (self) -> float:
        """Valor que divide uma unidade e resulta em centímetros de plotagem."""
        dimsca, dimlfc = self.__LerEscala ()
        return         dimsca

    @scale.setter
    def scale (self, scaleval: float) -> None:
        """Atribui Valor que divide uma unidade e resulta em centímetros de plotagem."""
        dimsca, dimlfc = self.__LerEscala ()
        dimsca         = scaleval
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pardimsca      = ctypes.c_double (dimsca)
        pardimlfc      = ctypes.c_double (dimlfc)
        self.m_dwg.m_mdwg.g_edmexgrvesc (parpedmv, ctypes.byref (pardimsca),
                                         ctypes.byref (pardimlfc))

    def __LerBase (self) -> Tuple[float, float]:
        """Lê o ponto-base (``xbas, ybas``) atual."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        xbas           = 0.
        parxbas        = ctypes.c_double (xbas)
        ybas           = 0.
        parybas        = ctypes.c_double (ybas)
        self.m_dwg.m_mdwg.g_extbas (parpedmv, ctypes.byref (parxbas), ctypes.byref (parybas))
        xbas           = parxbas.value
        ybas           = parybas.value
        return         xbas, ybas

    def __DefBase    (self, xbas: float, ybas: float) -> None:
        """Define o ponto-base (``xbas, ybas``)."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parxbas        = ctypes.c_double (xbas)
        parybas        = ctypes.c_double (ybas)
        self.m_dwg.m_mdwg.g_defbsd (parpedmv, ctypes.byref (parxbas), ctypes.byref (parybas))

    @property
    def xBase (self) -> float:
        """X do ponto que coincidirá com o cursor ao inserir este desenho em outro."""
        xbas, ybas     = self.__LerBase ()
        return         xbas

    @xBase.setter
    def xBase (self, val: float) -> None:
        """Atribui X do ponto que coincidirá com o cursor ao inserir este desenho em outro."""
        xbas, ybas     = self.__LerBase ()
        self.__DefBase (val, ybas)

    @property
    def yBase (self) -> float:
        """Y do ponto que coincidirá com o cursor ao inserir este desenho em outro."""
        xbas, ybas     = self.__LerBase ()
        return         ybas

    @yBase.setter
    def yBase (self, val: float) -> None:
        """Atribui Y do ponto que coincidirá com o cursor ao inserir este desenho em outro."""
        xbas, ybas     = self.__LerBase ()
        self.__DefBase (xbas, val)

    @property
    def blockReadDelimiterMode (self) -> int:
        """``1`` se delimitadores ``DWGTYPE_BLOCK``/``DWGTYPE_BLOCKEND`` devem ser lidos."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iedcpl         = 0
        pariedcpl      = ctypes.c_int (iedcpl)
        self.m_dwg.m_mdwg.g_extpbller (parpedmv, ctypes.byref (pariedcpl))
        iedcpl         = pariedcpl.value
        return         iedcpl

    @blockReadDelimiterMode.setter
    def blockReadDelimiterMode (self, ival: int) -> None:
        """Atribui ``1`` se delimitadores ``DWGTYPE_BLOCK``/``DWGTYPE_BLOCKEND`` devem ser lidos."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        # 0/1 mapeia para funções distintas de inibir/permitir leitura de delimitadores
        if             ival == 0:
            self.m_dwg.m_mdwg.g_extibl (parpedmv)
        else:
            self.m_dwg.m_mdwg.g_extpbl (parpedmv)

    @property
    def blockReadElementsMode (self) -> int:
        """``1`` para ler elementos dentro do bloco inserido, ``0`` apenas delimitadores."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iedexb         = 0
        pariedexb      = ctypes.c_int (iedexb)
        self.m_dwg.m_mdwg.g_extpbxler (parpedmv, ctypes.byref (pariedexb))
        iedexb         = pariedexb.value
        return         iedexb

    @blockReadElementsMode.setter
    def blockReadElementsMode (self, ival: int) -> None:
        """Atribui ``1`` para ler elementos dentro do bloco inserido, ``0`` apenas delimitadores."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        if             ival == 0:
            self.m_dwg.m_mdwg.g_extibx (parpedmv)
        else:
            self.m_dwg.m_mdwg.g_extpbx (parpedmv)

    @property
    def levelsReadMode (self) -> int:
        """``1`` para ler apenas elementos em níveis ligados, ``0`` para todos."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iedily         = 0
        pariedily      = ctypes.c_int (iedily)
        self.m_dwg.m_mdwg.g_extplaler (parpedmv, ctypes.byref (pariedily))
        iedily         = pariedily.value
        return         iedily

    @levelsReadMode.setter
    def levelsReadMode (self, ival: int) -> None:
        """Atribui ``1`` para ler apenas elementos em níveis ligados, ``0`` para todos."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        if             ival == 0:
            self.m_dwg.m_mdwg.g_extila (parpedmv)
        else:
            self.m_dwg.m_mdwg.g_extpla (parpedmv)


    @property
    def captureMode (self) -> int:
        """Modo de captura: ``0`` no gerenciador, ``1`` desligado, ``2`` ligado, ``3`` por nível.

        ATENÇÃO: o setter logo abaixo é decorado com ``@levelsReadMode.setter``
        mas nomeado ``captureMode``. Na biblioteca TQS isso substitui
        ``captureMode`` por uma combinação do getter de ``levelsReadMode`` com o
        setter de captura: LER ``settings.captureMode`` devolve o modo de
        leitura de níveis (valor errado) e este getter, que chama
        ``g_exlercaptura``, fica inalcançável. A atribuição grava a captura
        corretamente.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        icaptura       = 0
        paricaptura    = ctypes.c_int (icaptura)
        istcaptura     = 0
        paristcaptura  = ctypes.c_int (istcaptura)
        self.m_dwg.m_mdwg.g_exlercaptura (parpedmv, ctypes.byref (paricaptura),
                                          ctypes.byref (paristcaptura))
        icaptura       = paricaptura.value
        istcaptura     = paristcaptura.value
        # Estado de captura desligado pela DLL sobrescreve o modo retornado
        if        istcaptura != 0:
            icaptura   = 1
        return         icaptura

    @levelsReadMode.setter
    def captureMode (self, icaptura: int) -> None:
        """Atribui ``1`` para ler apenas elementos em níveis ligados, ``0`` para todos."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        paricaptura    = ctypes.c_int (icaptura)
        istcaptura     = 0
        paristcaptura  = ctypes.c_int (istcaptura)
        self.m_dwg.m_mdwg.g_exgrvcaptura (parpedmv, paricaptura, paristcaptura)

    def __LerGrade (self) -> Tuple[int, float, float, float, float, float, int, int]:
        """Lê os parâmetros da grade do desenho."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        igrade         = 0
        parigrade      = ctypes.c_int (igrade)
        grdorx         = 0.
        pargrdorx      = ctypes.c_double (grdorx)
        grdory         = 0.
        pargrdory      = ctypes.c_double (grdory)
        grdesx         = 0.
        pargrdesx      = ctypes.c_double (grdesx)
        grdesy         = 0.
        pargrdesy      = ctypes.c_double (grdesy)
        grdang         = 0.
        pargrdang      = ctypes.c_double (grdang)
        iespacponto    = 0
        pariespacponto = ctypes.c_int (iespacponto)
        igraderubber   = 0
        parigraderubber= ctypes.c_int (igraderubber)
        self.m_dwg.m_mdwg.g_exlerigrade    (parpedmv, ctypes.byref (parigrade),
            ctypes.byref (pargrdorx), ctypes.byref (pargrdory),
            ctypes.byref (pargrdesx), ctypes.byref (pargrdesy),
            ctypes.byref (pargrdang), ctypes.byref (pariespacponto),
            ctypes.byref (parigraderubber))
        igrade         = parigrade.value
        grdorx         = pargrdorx.value
        grdory         = pargrdory.value
        grdesx         = pargrdesx.value
        grdesy         = pargrdesy.value
        grdang         = pargrdang.value
        iespacponto    = pariespacponto.value
        igraderubber   = parigraderubber.value
        return         igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber

    def __DefGrade (self, igrade: int, grdorx: float, grdory: float, grdesx: float,
                    grdesy: float, grdang: float, iespacponto: int, igraderubber: int) -> None:
        """Define os parâmetros da grade do desenho."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parigrade      = ctypes.c_int (igrade)
        pargrdorx      = ctypes.c_double (grdorx)
        pargrdory      = ctypes.c_double (grdory)
        pargrdesx      = ctypes.c_double (grdesx)
        pargrdesy      = ctypes.c_double (grdesy)
        pargrdang      = ctypes.c_double (grdang)
        pariespacponto = ctypes.c_int (iespacponto)
        parigraderubber= ctypes.c_int (igraderubber)
        self.m_dwg.m_mdwg.g_exgrvigrade    (parpedmv, parigrade,
            pargrdorx, pargrdory, pargrdesx, pargrdesy, pargrdang, pariespacponto,
            parigraderubber)


    @property
    def gridMode (self) -> int:
        """Modo de grade: ``0`` vale captura, ``1`` vale grade, ``2`` nem captura nem grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        return         igrade

    @gridMode.setter
    def gridMode (self, ival: int) -> None:
        """Atribui ``0`` vale captura, ``1`` vale grade, ``2`` nem captura nem grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        igrade         = ival
        self.__DefGrade (igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber)

    @property
    def gridOriginX (self) -> float:
        """Origem X da grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        return         grdorx

    @gridOriginX.setter
    def gridOriginX (self, val: float) -> None:
        """Atribui Origem X da grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        grdorx         = val
        self.__DefGrade (igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber)

    @property
    def gridOriginY (self) -> float:
        """Origem Y da grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        return         grdory

    @gridOriginY.setter
    def gridOriginY (self, val: float) -> None:
        """Atribui Origem Y da grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        grdory         = val
        self.__DefGrade (igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber)

    @property
    def gridSpacingX (self) -> float:
        """Espaçamento X da grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        return         grdesx

    @gridSpacingX.setter
    def gridSpacingX (self, val: float) -> None:
        """Atribui Espaçamento X da grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        grdesx         = val
        self.__DefGrade (igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber)

    @property
    def gridSpacingY (self) -> float:
        """Espaçamento Y da grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        return         grdesy

    @gridSpacingY.setter
    def gridSpacingY (self, val: float) -> None:
        """Atribui Espaçamento Y da grade."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        grdesy         = val
        self.__DefGrade (igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber)

    @property
    def gridAngle (self) -> float:
        """Ângulo da grade em graus."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        return         grdang

    @gridAngle.setter
    def gridAngle (self, val: float) -> None:
        """Atribui Ângulo da grade em graus."""
        igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber = self.__LerGrade ()
        grdang         = val
        self.__DefGrade (igrade, grdorx, grdory, grdesx, grdesy, grdang, iespacponto, igraderubber)


    @property
    def handle_pedmv (self) -> int:
        """Handle de desenho ``pedmv`` para uso em outras bibliotecas."""
        return         self.m_dwg.m_pedmv

    @property
    def originalColorsMode (self) -> int:
        """``1`` se o desenho deve ser plotado com cores originais e não da tabela."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iplotcorori    = 0
        pariplotcorori = ctypes.c_int (iplotcorori)
        self.m_dwg.m_mdwg.g_edmexleriplotcorori (parpedmv, ctypes.byref (pariplotcorori))
        iplotcorori    = pariplotcorori.value
        return         iplotcorori

    @originalColorsMode.setter
    def originalColorsMode (self, ival: int) -> None:
        """Atribui ``1`` se o desenho deve ser plotado com cores originais e não da tabela."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        iplotcorori    = ival
        pariplotcorori = ctypes.c_int (iplotcorori)
        self.m_dwg.m_mdwg.g_edmexgrviplotcorori (parpedmv, pariplotcorori)

    @property
    def comment (self) -> str:
        """Comentário associado ao desenho."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parcomment     = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.g_edmexlercoment (parpedmv, parcomment)
        return         parcomment.value.decode(TQS.TQSUtil.CHARSET)

    @comment.setter
    def comment (self, commentx: str) -> None:
        """Atribui Comentário associado ao desenho."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parcomment     = ctypes.c_char_p (commentx.encode(TQS.TQSUtil.CHARSET))
        self.m_dwg.m_mdwg.g_edmexgrvcoment (parpedmv, parcomment)

    @property
    def revComment (self) -> str:
        """Comentários da revisão do desenho."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parcomment     = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.g_edmexlerrevisao (parpedmv, parcomment)
        return         parcomment.value.decode(TQS.TQSUtil.CHARSET)

    @revComment.setter
    def revComment (self, commentx: str) -> None:
        """Atribui Comentários da revisão do desenho."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parcomment     = ctypes.c_char_p (commentx.encode(TQS.TQSUtil.CHARSET))
        self.m_dwg.m_mdwg.g_edmexgrvrevisao (parpedmv, parcomment)

    @property
    def blueprintMode (self) -> int:
        """``1`` se está em modo de visualização de plantas."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        ixref          = 0
        parixref       = ctypes.c_int (ixref)
        self.m_dwg.m_mdwg.g_edmexlerxref (parpedmv, ctypes.byref (parixref))
        ixref          = parixref.value
        return         ixref

    @blueprintMode.setter
    def blueprintMode (self, ival: int) -> None:
        """Atribui ``1`` se está em modo de visualização de plantas."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        ixref          = ival
        parixref       = ctypes.c_int (ixref)
        self.m_dwg.m_mdwg.g_edmexgrvxref (parpedmv, parixref)

#-----------------------------------------------------------------------------
#    Acesso à tabela de níveis do DWG
#
class LevelsTable ():
    """Acesso à tabela de níveis do DWG (cores, estilos, travamentos, captura).

    Implementação:
        Os níveis no TQS aceitam tanto a forma numérica (``0..MAXCARLAY-1``)
        quanto alfanumérica. :meth:`ConvNivel` faz o despacho conforme o tipo
        do argumento e devolve o par ``(snivel, inivel)`` consumido pelos
        demais métodos. Cada operação (cor, estilo, lock, captura) é um
        wrapper sobre uma função ``g_*lay``/``g_*nivel`` de ``MDWG.DLL``.

    Attributes:
        MAXCARLAY: Limite de caracteres para níveis alfanuméricos.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de tabela de níveis.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg     = dwg
        self.MAXCARLAY = 256

    def ConvNivel (self, level: Union[int, str]) -> Tuple[bytes, int]:
        """Converte um nível alfanumérico ou numérico para a forma numérica.

        Args:
            level: Nível numérico (``int``) ou alfanumérico (``str``).

        Returns:
            Tupla ``(snivel, inivel)``: nome alfanumérico (bytes) e número.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel         = str (level)
        parsnivel      = ctypes.c_char_p (snivel.encode(TQS.TQSUtil.CHARSET))
        inivel         = 0
        parnivel       = ctypes.c_int (inivel)
        ialfa          = 0
        # Despacho conforme tipo: numérico ou alfanumérico
        if             isinstance (level, (int, float)):
            inivel     = level
            parnivel   = ctypes.c_int (inivel)
            # Numérico fora de MAXCARLAY: cai no caminho alfanumérico se já existir nome correspondente
            if         inivel < 0 or inivel >= self.MAXCARLAY:
                ialfa  = 1
                parnomlay = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
                idesligado = 0
                paridesligado = ctypes.c_int (idesligado)
                inaoexiste = 0
                parinaoexiste = ctypes.c_int (inaoexiste)
                self.m_dwg.m_mdwg.g_onflayx (parpedmv, ctypes.byref (parnivel), parnomlay,
                              ctypes.byref (paridesligado), ctypes.byref (parinaoexiste))
                iexiste= 1 - parinaoexiste.value
                if     iexiste != 0:
                    parsnivel = parnomlay
        else:
            # String pura entra direto na via alfanumérica
            parsnivel  = ctypes.c_char_p (level.encode(TQS.TQSUtil.CHARSET))
            ialfa      = 1
        # Aplica o nível usando a função adequada e devolve o par (snivel, inivel) coerente
        if        ialfa== 0:
            self.m_dwg.m_mdwg.g_desniv (parpedmv, ctypes.byref (parnivel))
        else:
            self.m_dwg.m_mdwg.g_desnivalfa (parpedmv, parsnivel, ctypes.byref (parnivel))
        snivel         = parsnivel.value
        inivel         = parnivel.value
        return         snivel, inivel

    @property
    def count (self) -> int:
        """Número total de níveis numerados de ``0`` a ``N-1``."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        numniveis      = 0
        parnumniveis   = ctypes.c_int (numniveis)
        self.m_dwg.m_mdwg.g_numlay (parpedmv, ctypes.byref (parnumniveis))
        numniveis      = parnumniveis.value
        return         numniveis

    def IsDefined (self, level: Union[int, str]) -> int:
        """Verifica se o nível está definido.

        ATENÇÃO: a biblioteca TQS zera ``level`` antes da chamada nativa, que
        consulta sempre o nível ``0``. O retorno não corresponde ao nível
        pedido. Não use para testar um nível específico.

        Args:
            level: Aceito e ignorado pela biblioteca (consulta o nível ``0``).

        Returns:
            ``1`` se o nível ``0`` está definido, ``0`` caso contrário.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        level          = 0
        parlevel       = ctypes.c_int (level)
        parnomlay      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        idesligado     = 0
        paridesligado  = ctypes.c_int (idesligado)
        inaoexiste     = 0
        parinaoexiste  = ctypes.c_int (inaoexiste)
        self.m_dwg.m_mdwg.g_onflayx (parpedmv, ctypes.byref (parlevel), parnomlay,
               ctypes.byref (paridesligado), ctypes.byref (parinaoexiste))
        iexiste        = 1 - parinaoexiste.value
        return         iexiste

    def GetStyle (self, level: Union[int, str]) -> int:
        """Retorna o estilo associado ao nível.

        Args:
            level: Nível.

        Returns:
            Estilo associado, ``-1`` se for o estilo default.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        iestilo        = 0
        pariestilo     = ctypes.c_int (iestilo)
        self.m_dwg.m_mdwg.g_extstl (parpedmv, ctypes.byref (parnivel),
                                    ctypes.byref (pariestilo))
        iestilo        = pariestilo.value
        return         iestilo

    def SetStyle (self, level: Union[int, str], ival: int) -> None:
        """Define o estilo associado ao nível.

        Args:
            level: Nível.
            ival: Estilo a aplicar; ``-1`` para o default.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        # Convenção interna: estilo é codificado como negativo (offset +1 para reservar -1 como default)
        iestilo        = ival + 1
        if             iestilo > 0:
            iestilo    = - iestilo
        pariestilo     = ctypes.c_int (iestilo)
        self.m_dwg.m_mdwg.g_atribestilniv (parpedmv, parnivel, pariestilo)

    def IsOn (self, level: Union[int, str]) -> int:
        """Retorna o estado ligado/desligado de um nível.

        Args:
            level: Nível.

        Returns:
            ``1`` ligado, ``0`` desligado.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        parnomlay      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        idesligado     = 0
        paridesligado  = ctypes.c_int (idesligado)
        inaoexiste     = 0
        parinaoexiste  = ctypes.c_int (inaoexiste)
        self.m_dwg.m_mdwg.g_onflayx (parpedmv, ctypes.byref (parnivel), parnomlay,
                         ctypes.byref (paridesligado), ctypes.byref (parinaoexiste))
        # Inverte: a DLL devolve idesligado, mas a API expõe ligado/desligado
        idesligado     = 1 - paridesligado.value
        return         idesligado

    def TurnOn (self, level: Union[int, str], ival: int) -> None:
        """Liga ou desliga um nível.

        Args:
            level: Nível.
            ival: ``1`` liga, ``0`` desliga.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        # Despacha entre função de ligar e desligar nível
        iligado        = ival
        if             iligado != 0:
            self.m_dwg.m_mdwg.g_liglay (parpedmv, ctypes.byref (parnivel))
        else:
            self.m_dwg.m_mdwg.g_deslay (parpedmv, ctypes.byref (parnivel))

    def GetColor (self, level: Union[int, str]) -> int:
        """Retorna a cor de um nível.

        Args:
            level: Nível.

        Returns:
            Cor (``0..255``) do nível.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        icor           = 0
        paricor        = ctypes.c_int (icor)
        self.m_dwg.m_mdwg.g_icorly (parpedmv, ctypes.byref (parnivel),
                          ctypes.byref (paricor))
        icor           = paricor.value
        return         icor

    def SetColor (self, level: Union[int, str], ival: int) -> None:
        """Define a cor de um nível.

        Args:
            level: Nível.
            ival: Cor ``0..255``.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        icor           = ival
        paricor        = ctypes.c_int (icor)
        self.m_dwg.m_mdwg.g_corlay (parpedmv, ctypes.byref (parnivel),
                          ctypes.byref (paricor))

    def GetLock (self, level: Union[int, str]) -> int:
        """Retorna o estado de trava de um nível.

        Args:
            level: Nível.

        Returns:
            ``1`` travado, ``0`` não travado.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        itravado       = 0
        paritravado    = ctypes.c_int (itravado)
        self.m_dwg.m_mdwg.g_lertravanivel (parpedmv, parnivel, ctypes.byref (paritravado))
        itravado       = paritravado.value
        return         itravado

    def SetLock (self, level: Union[int, str], ival: int) -> None:
        """Define o estado de trava de um nível.

        Args:
            level: Nível.
            ival: ``1`` para travar, ``0`` para destravar.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        itravado       = ival
        paritravado    = ctypes.c_int (itravado)
        self.m_dwg.m_mdwg.g_deftravanivel (parpedmv, parnivel, paritravado)

    def GetCapture (self, level: Union[int, str]) -> int:
        """Retorna o estado de captura de um nível.

        Args:
            level: Nível.

        Returns:
            ``1`` se captura ligada, ``0`` caso contrário.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        icaptura       = 0
        paricaptura    = ctypes.c_int (icaptura)
        self.m_dwg.m_mdwg.g_lercapturanivel (parpedmv, parnivel, ctypes.byref (paricaptura))
        icaptura       = paricaptura.value
        return         icaptura

    def SetCapture (self, level: Union[int, str], ival: int) -> None:
        """Define o estado de captura de um nível.

        Args:
            level: Nível.
            ival: ``1`` para ligar captura, ``0`` para desligar.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        parnivel       = ctypes.c_int (nivel)
        icaptura       = ival
        paricaptura    = ctypes.c_int (icaptura)
        self.m_dwg.m_mdwg.g_defcapturanivel (parpedmv, parnivel, paricaptura)

    def Create (self, level: Union[int, str]) -> int:
        """Cria um nível numérico/alfanumérico e retorna o número correspondente.

        Args:
            level: Nível numérico ou alfanumérico a criar.

        Returns:
            Número do nível para uso em outros métodos.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        snivel, nivel  = self.ConvNivel (level)
        return         nivel

    def Name (self, level: Union[int, str]) -> str:
        """Retorna o nível em formato alfanumérico.

        Args:
            level: Nível.

        Returns:
            Nome alfanumérico do nível.
        """
        snivel, nivel  = self.ConvNivel (level)
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnivel       = ctypes.c_int (nivel)
        parnomlay      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        idesligado     = 0
        paridesligado  = ctypes.c_int (idesligado)
        inaoexiste     = 0
        parinaoexiste  = ctypes.c_int (inaoexiste)
        self.m_dwg.m_mdwg.g_onflayx (parpedmv, ctypes.byref (parnivel), parnomlay,
                         ctypes.byref (paridesligado), ctypes.byref (parinaoexiste))
        snivel         = parnomlay.value
        return         snivel.decode(TQS.TQSUtil.CHARSET)

#-----------------------------------------------------------------------------
#    Acesso à tabela de blocos do DWG
#
class BlocksTable ():
    """Acesso à tabela de blocos do DWG.

    Implementação:
        ``count`` chama ``g_iexnbl`` para obter o número de blocos definidos
        e ``Name``/``IsDefined`` recuperam metadados via ``g_extnbl``/
        ``g_tstblk``. A enumeração usa índices baseados em 1 internamente
        (``index + 1``) mas expõe ``0..count-1`` na API Python.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de tabela de blocos.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg  = dwg

    @property
    def count (self) -> int:
        """Número total de blocos definidos."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        numblo         = 0
        parnumblo      = ctypes.c_int (numblo)
        self.m_dwg.m_mdwg.g_iexnbl (parpedmv, ctypes.byref (parnumblo))
        numblo         = parnumblo.value
        return         numblo

    def IsDefined (self, name: str) -> int:
        """Retorna se o bloco existe.

        Args:
            name: Nome do bloco.

        Returns:
            ``1`` se existe, ``0`` caso contrário.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parname        = ctypes.c_char_p (name.encode(TQS.TQSUtil.CHARSET))
        istat          = 0
        paristat       = ctypes.c_int (istat)
        # g_tstblk devolve 0 se existe, 1 caso contrário; inverte para retornar boolean de existência
        self.m_dwg.m_mdwg.g_tstblk (parpedmv, parname, ctypes.byref (paristat))
        istat          = paristat.value
        iexiste        = 1 - istat
        return         iexiste

    def Name (self, index: int) -> Optional[str]:
        """Retorna o nome do bloco de índice ``index``.

        Args:
            index: Índice do bloco em ``0..count-1``.

        Returns:
            Nome do bloco ou ``None`` se o índice for inválido.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        # API Python usa índice 0-based, mas g_extnbl espera 1-based
        numblo         = self.count
        indblo         = index + 1
        if             index < 0 or index >= numblo:
            TQS.TQSUtil.writef ("BlocksTable.name: indice invalido: %d/%d" %
                              (index, numblo))
            return
        parindblo      = ctypes.c_int (indblo)
        parnomblk      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.g_extnbl (parpedmv, ctypes.byref (parindblo), parnomblk)
        return         parnomblk.value.decode(TQS.TQSUtil.CHARSET)

#-----------------------------------------------------------------------------
#    Acesso às referências externas
#
class XReference ():
    """Acesso às referências externas (XRef) do desenho.

    Implementação:
        Os métodos delegam ao subconjunto ``refx_*`` de ``MDWG.DLL``
        (``refx_numelem``, ``refx_inibe``, ``refx_ler``, ``refx_ligada``).
        Strings de nome de DWG e de bloco trafegam por ``ctypes.create_string_buffer``
        e o índice de XRef é validado contra :attr:`count` antes de cada
        operação.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de referências externas.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg     = dwg

    @property
    def count (self) -> int:
        """Número de referências externas definidas e inseridas."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        numelem        = 0
        parnumelem     = ctypes.c_int (numelem)
        self.m_dwg.m_mdwg.refx_numelem (parpedmv, ctypes.byref (parnumelem))
        numelem        = parnumelem.value
        return         numelem

    def Disable (self, ival: int) -> None:
        """Inibe ou habilita a interpretação de referências externas.

        Args:
            ival: ``1`` para inibir.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        inibepref      = ival
        parinibepref   = ctypes.c_int (inibepref)
        self.m_dwg.m_mdwg.refx_inibe (parpedmv, parinibepref)

    def Read (self, index: int) -> Tuple[str, int, str]:
        """Lê os dados de uma referência externa inserida no desenho.

        Args:
            index: Índice em ``0..count-1``.

        Returns:
            Tupla ``(dwgname, ion, blockname)``:

            * ``dwgname``: Nome do desenho associado.
            * ``ion``: ``1`` se ligada.
            * ``blockname``: Nome do bloco interno do DWG.
        """
        # Valida o índice contra o número de XRefs definidas
        if        index < 0 or index >= self.count:
            TQS.TQSUtil.writef ("XReference::Read índice invalido %d/%d" %
                              (index, self.count))
            return    "", 0, ""

        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parindex    = ctypes.c_int (index)
        interna        = 0
        parinterna    = ctypes.c_int (interna)
        pardwgname    = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        pedmref        = 0
        parpedmref    = ctypes.c_void_p (pedmref)
        ligada        = 0
        parligada    = ctypes.c_int (ligada)
        parblockname     = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.refx_ler (parpedmv, parindex, ctypes.byref (parinterna),
                                 pardwgname, ctypes.byref (parpedmref),
                                 ctypes.byref (parligada), parblockname)
        dwgname        = pardwgname.value.decode(TQS.TQSUtil.CHARSET)
        ion        = parligada.value
        blockname    = parblockname.value.decode(TQS.TQSUtil.CHARSET)
        return        dwgname, ion, blockname

    def TurnOn (self, index: int, ival: int) -> None:
        """Liga ou desliga a visualização de uma referência externa.

        Args:
            index: Índice em ``0..count-1``.
            ival: ``1`` para ligar.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        if        index < 0 or index >= self.count:
            TQS.TQSUtil.writef ("XReference::TurnOn índice invalido %d/%d" %
                              (index, self.count))
            return
        parindex    = ctypes.c_int (index)
        ligada        = ival
        parligada    = ctypes.c_int (ligada)
        self.m_dwg.m_mdwg.refx_ligada (parpedmv, parindex, parligada)

#-----------------------------------------------------------------------------
#    Modificação de elementos
#
class Edit ():
    """Modificação de elementos individuais do desenho.

    Implementação:
        Os elementos são identificados pelo endereço (``addr``) devolvido
        pelo iterador. Cada modificação chama uma função ``g_alt*`` ou
        ``g_del*`` de ``MDWG.DLL`` passando esse endereço como ``c_void_p``.
        Atributos compostos (cor, RGB, estilo, espessura) são lidos em bloco
        por ``__LerAtribElem`` e regravados por ``__DefAtribElem`` para
        preservar campos não alterados pelo método público.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de edição.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg      = dwg

    def ModifyLevel (self, addr: int, level: Union[int, str]) -> None:
        """Modifica o nível de um elemento.

        Args:
            addr: Endereço do elemento.
            level: Novo nível.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        snivel, nivel= self.m_dwg.levelstable.ConvNivel (level)
        parnivel    = ctypes.c_int (nivel)
        self.m_dwg.m_mdwg.g_altely (parpedmv, ctypes.byref (pariadr), ctypes.byref (parnivel))

    def __LerAtribElem (self, addr: int) -> Tuple[int, int, int, int]:
        """Lê atributos de um elemento (cor, RGB, estilo, espessura)."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        icor        = 0
        paricor     = ctypes.c_int (icor)
        icorrgb        = 0
        paricorrgb     = ctypes.c_void_p (icorrgb)
        iestilo        = 0
        pariestilo     = ctypes.c_int (iestilo)
        iespes        = 0
        pariespes     = ctypes.c_int (iespes)
        self.m_dwg.m_mdwg.g_leratribelem (parpedmv, ctypes.byref (pariadr),
                          ctypes.byref (paricor), ctypes.byref (paricorrgb),
                          ctypes.byref (pariestilo), ctypes.byref (pariespes))
        icor        = paricor.value
        icorrgb        = paricorrgb.value
        iestilo        = pariestilo.value
        iespes        = pariespes.value
        return        icor, icorrgb, iestilo, iespes

    def __DefAtribElem (self, addr: int, icor: int, icorrgb: int, iestilo: int, iespes: int) -> None:
        """Define atributos de um elemento (cor, RGB, estilo, espessura)."""
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        paricor     = ctypes.c_int (icor)
        paricorrgb     = ctypes.c_void_p (icorrgb)
        pariestilo     = ctypes.c_int (iestilo)
        pariespes     = ctypes.c_int (iespes)
        self.m_dwg.m_mdwg.g_altatrib (parpedmv, ctypes.byref (pariadr), paricor, paricorrgb,
                          pariestilo, pariespes)

    def ModifyColor (self, addr: int, icolor: int) -> None:
        """Modifica a cor de um elemento.

        Args:
            addr: Endereço do elemento.
            icolor: Cor ``0..255``.
        """
        # Lê tudo, sobrescreve só a cor, regrava: preserva os demais atributos
        icor, icorrgb, iestilo, iespes = self.__LerAtribElem (addr)
        self.__DefAtribElem (addr, icolor, icorrgb, iestilo, iespes)


    def ModifyStyle (self, addr: int, istyle: int) -> None:
        """Modifica o estilo de um elemento.

        Args:
            addr: Endereço do elemento.
            istyle: Novo estilo.
        """
        # Lê tudo, sobrescreve só o estilo, regrava: preserva os demais atributos
        icor, icorrgb, iestilo, iespes = self.__LerAtribElem (addr)
        self.__DefAtribElem (addr, icor, icorrgb, istyle, iespes)

    def Erase (self, addr: int) -> int:
        """Apaga um elemento.

        Args:
            addr: Endereço do elemento.

        Returns:
            ``0`` se Ok, ``!= 0`` se erro.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        istat        = 0
        paristat     = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_delelm (parpedmv, ctypes.byref (pariadr), ctypes.byref (paristat))
        istat        = paristat.value
        return        istat

    def Recover (self, addr: int) -> int:
        """Recupera um elemento apagado.

        Args:
            addr: Endereço do elemento.

        Returns:
            ``0`` se Ok, ``!= 0`` se erro.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        istat        = 0
        paristat     = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_recelm (parpedmv, ctypes.byref (pariadr), ctypes.byref (paristat))
        istat        = paristat.value
        return        istat

    def ModifyPoint (self, addr: int, index: int, x: float, y: float) -> int:
        """Modifica as coordenadas de um ponto de um elemento.

        Args:
            addr: Endereço do elemento.
            index: Índice do ponto em ``0..np-1``.
            x: Nova coordenada X.
            y: Nova coordenada Y.

        Returns:
            ``0`` se Ok, ``!= 0`` se erro.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        istat        = 0
        paristat     = ctypes.c_int (istat)
        # API Python usa índice 0-based; g_altelm espera 1-based
        index        = index+1
        parindex     = ctypes.c_int (index)
        parx         = ctypes.c_double (x)
        pary         = ctypes.c_double (y)
        self.m_dwg.m_mdwg.g_altelm (parpedmv, ctypes.byref (pariadr), ctypes.byref (parindex),
                         ctypes.byref (parx), ctypes.byref (pary), ctypes.byref (paristat))
        istat        = paristat.value
        return        istat

    def ModifyText (self, addr: int, h: float, ang: float) -> None:
        """Modifica altura e ângulo de um texto.

        Para alterar o conteúdo do texto é necessário apagar e criar outro.

        Args:
            addr: Endereço do elemento.
            h: Nova altura.
            ang: Novo ângulo (graus).
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        parh         = ctypes.c_double (h)
        parang         = ctypes.c_double (ang)
        self.m_dwg.m_mdwg.g_altatx (parpedmv, ctypes.byref (pariadr), ctypes.byref (parh),
                          ctypes.byref (parang))

    def ModifyArc (self, addr: int, r: float, angi: float, angf: float) -> None:
        """Modifica os dados de um arco.

        Args:
            addr: Endereço do elemento.
            r: Raio.
            angi: Ângulo inicial (graus).
            angf: Ângulo final (graus).
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        parr         = ctypes.c_double (r)
        parangi         = ctypes.c_double (angi)
        parangf         = ctypes.c_double (angf)
        # Arco no TQS é círculo+ângulos: atualiza raio e ângulos em chamadas separadas
        self.m_dwg.m_mdwg.g_altcir (parpedmv, ctypes.byref (pariadr), ctypes.byref (parr))
        self.m_dwg.m_mdwg.g_altarc (parpedmv, ctypes.byref (pariadr),
                          ctypes.byref (parangi), ctypes.byref (parangf))

    def ModifyCircle (self, addr: int, r: float) -> None:
        """Modifica os dados de um círculo.

        Args:
            addr: Endereço do elemento.
            r: Novo raio.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        parr         = ctypes.c_double (r)
        self.m_dwg.m_mdwg.g_altcir (parpedmv, ctypes.byref (pariadr), ctypes.byref (parr))

    def ModifyBlock (self, addr: int, escx: float, escy: float, ang: float) -> int:
        """Modifica os dados de um bloco inserido.

        Args:
            addr: Endereço do elemento.
            escx: Escala X.
            escy: Escala Y.
            ang: Ângulo de inserção (graus).

        Returns:
            ``0`` se Ok, ``!= 0`` se erro.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        parescx         = ctypes.c_double (escx)
        parescy         = ctypes.c_double (escy)
        # g_altblk recebe o ângulo em radianos, mas a API Python usa graus
        angrad        = ang * TQS.TQSUtil.GRAUSRAD
        parangrad     = ctypes.c_double (angrad)
        istat        = 0
        paristat     = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_altblk (parpedmv, ctypes.byref (pariadr), ctypes.byref (parangrad),
                          ctypes.byref (parescx), ctypes.byref (parescy), ctypes.byref (paristat))
        istat        = paristat.value
        return        istat

    def Move (self, addr: int, dx: float, dy: float) -> int:
        """Movimenta um elemento qualquer.

        Args:
            addr: Endereço do elemento.
            dx: Deslocamento em X.
            dy: Deslocamento em Y.

        Returns:
            ``0`` se Ok, ``!= 0`` se erro.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pariadr     = ctypes.c_void_p (addr)
        pardx         = ctypes.c_double (dx)
        pardy         = ctypes.c_double (dy)
        istat        = 0
        paristat     = ctypes.c_int (istat)
        self.m_dwg.m_mdwg.g_movelm (parpedmv, ctypes.byref (pariadr), ctypes.byref (pardx),
                          ctypes.byref (pardy), ctypes.byref (paristat))
        istat        = paristat.value
        return        istat

#-----------------------------------------------------------------------------
#    Acesso à tabela de plotagem
#
class Plotting ():
    """Acesso à tabela de plotagem associada ao desenho.

    Implementação:
        :meth:`LoadPlottingTable` orquestra ``g_carregcores`` + ``tabplt_ini``
        + ``tabplt_ler`` para preparar a tabela; :meth:`AttributeRead` lê os
        cinco índices (``invpen``, ``invpes``, ``invstl``, ``invhac``,
        ``invtbf``) e o título do nível através de chamadas ``tabplt_*``
        sucessivas em ``MDWG.DLL``.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de plotagem.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg      = dwg

    def LoadPlottingTable (self) -> Tuple[str, int]:
        """Torna disponíveis os dados de tabela de plotagem associados ao desenho.

        Returns:
            Tupla ``(tabname, istat)`` com o nome da tabela e o status
            (``0`` Ok, ``!= 0`` erro).
        """
        istat          = 0
        paristat       = ctypes.c_int (istat)
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        # Sequência: carrega cores -> inicializa tabela de plot -> lê o nome
        self.m_dwg.m_mdwg.g_carregcores (parpedmv, ctypes.byref(paristat))
        self.m_dwg.m_mdwg.tabplt_ini (parpedmv, ctypes.byref(paristat))
        parnomtab      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.tabplt_ler (parpedmv, parnomtab, ctypes.byref(paristat))
        istat          = paristat.value
        tabname        = parnomtab.value.decode(TQS.TQSUtil.CHARSET)
        return         tabname, istat

    def AttributeRead (self, nivel: int) -> Tuple[int, int, int, int, int, str]:
        """Lê os atributos de um nível da tabela de plotagem.

        Args:
            nivel: Nível.

        Returns:
            Tupla ``(invpen, invpes, invstl, invhac, invtbf, titulomsg)``:

            * ``invpen``: Índice da pena.
            * ``invpes``: Índice do peso.
            * ``invstl``: Índice do estilo.
            * ``invhac``: Índice da hachura.
            * ``invtbf``: Índice da fonte.
            * ``titulomsg``: Título do nível.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parnivel       = ctypes.c_int (nivel)
        invpen         = 0
        parinvpen      = ctypes.c_int (invpen)
        invpes         = 0
        parinvpes      = ctypes.c_int (invpes)
        invstl         = 0
        parinvstl      = ctypes.c_int (invstl)
        invhac         = 0
        parinvhac      = ctypes.c_int (invhac)
        invtbf         = 0
        parinvtbf      = ctypes.c_int (invtbf)
        # Cinco chamadas tabplt_inv* + uma para o título: cada atributo tem sua função própria
        self.m_dwg.m_mdwg.tabplt_invpen (parpedmv, parnivel, ctypes.byref (parinvpen))
        self.m_dwg.m_mdwg.tabplt_invpes (parpedmv, parnivel, ctypes.byref (parinvpes))
        self.m_dwg.m_mdwg.tabplt_invstl (parpedmv, parnivel, ctypes.byref (parinvstl))
        self.m_dwg.m_mdwg.tabplt_invhac (parpedmv, parnivel, ctypes.byref (parinvhac))
        self.m_dwg.m_mdwg.tabplt_invtbf (parpedmv, parnivel, ctypes.byref (parinvtbf))
        partitulomsg   = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.tabplt_titulomsg2 (parpedmv, parnivel, partitulomsg)
        invpen         = parinvpen.value
        invpes         = parinvpes.value
        invstl         = parinvstl.value
        invhac         = parinvhac.value
        invtbf         = parinvtbf.value
        titulomsg      = partitulomsg.value.decode(TQS.TQSUtil.CHARSET)
        return         invpen, invpes, invstl, invhac, invtbf, titulomsg


#-----------------------------------------------------------------------------
#    Comandos de cotagem
#
class Dim ():
    """Comandos de cotagem (dimension) com configuração de variáveis estilo AutoCAD.

    Implementação:
        As propriedades (``dimtxt``, ``dimexe``, ``dimdle``, ``idmniv`` etc.)
        delegam a pares ``COTXXX_LER``/``COTXXX`` de ``MDWG.DLL``, espelhando
        as variáveis ``DIMxxx`` do AutoCAD. Os comandos de cotagem
        (``Dim3P``, ``DimHorizontal``, ``DimAngular`` etc.) chamam
        ``COTIFOR`` para sincronizar variáveis com o desenho corrente,
        executam o comando (``COT3P``, ``DIMANG`` etc.) e finalizam com
        ``COTDTX`` para gravar o texto de cotagem.
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de cotagem.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg     = dwg

    @property
    def dimtxt (self) -> float:
        """Altura do texto de cotagem."""
        dimtxt         = 0.
        pardimtxt      = ctypes.c_double (dimtxt)
        self.m_dwg.m_mdwg.COTTXT_LER (ctypes.byref (pardimtxt))
        dimtxt         = pardimtxt.value
        return         dimtxt

    @dimtxt.setter
    def dimtxt (self, val: float) -> None:
        """Atribui Altura do texto de cotagem."""
        pardimtxt      = ctypes.c_double (val)
        self.m_dwg.m_mdwg.COTTXT (ctypes.byref (pardimtxt))

    @property
    def dimexe (self) -> float:
        """Extensão da linha de chamada."""
        dimexe         = 0.
        pardimexe      = ctypes.c_double (dimexe)
        self.m_dwg.m_mdwg.COTEXE_LER (ctypes.byref (pardimexe))
        dimexe         = pardimexe.value
        return         dimexe

    @dimexe.setter
    def dimexe (self, val: float) -> None:
        """Atribui Extensão da linha de chamada."""
        pardimexe      = ctypes.c_double (val)
        self.m_dwg.m_mdwg.COTEXE (ctypes.byref (pardimexe))

    @property
    def dimdle (self) -> float:
        """Extensão da linha de cotagem."""
        dimdle         = 0.
        pardimdle      = ctypes.c_double (dimdle)
        self.m_dwg.m_mdwg.COTDLE_LER (ctypes.byref (pardimdle))
        dimdle         = pardimdle.value
        return         dimdle

    @dimdle.setter
    def dimdle (self, val: float) -> None:
        """Atribui Extensão da linha de cotagem."""
        pardimdle      = ctypes.c_double (val)
        self.m_dwg.m_mdwg.COTDLE (ctypes.byref (pardimdle))

    @property
    def dimexo (self) -> float:
        """Folga na linha de chamada."""
        dimexo        = 0.
        pardimexo    = ctypes.c_double (dimexo)
        self.m_dwg.m_mdwg.COTEXO_LER (ctypes.byref (pardimexo))
        dimexo        = pardimexo.value
        return        dimexo

    @dimexo.setter
    def dimexo (self, val: float) -> None:
        """Atribui Folga na linha de chamada."""
        pardimexo    = ctypes.c_double (val)
        self.m_dwg.m_mdwg.COTEXO (ctypes.byref (pardimexo))

    @property
    def dimtsz (self) -> float:
        """Tamanho do símbolo de cotagem."""
        dimtsz        = 0.
        pardimtsz    = ctypes.c_double (dimtsz)
        self.m_dwg.m_mdwg.COTTSZ_LER (ctypes.byref (pardimtsz))
        dimtsz        = pardimtsz.value
        return        dimtsz

    @dimtsz.setter
    def dimtsz (self, val: float) -> None:
        """Atribui Tamanho do símbolo de cotagem."""
        pardimtsz    = ctypes.c_double (val)
        self.m_dwg.m_mdwg.COTTSZ (ctypes.byref (pardimtsz))

    @property
    def dimlfc (self) -> float:
        """Multiplicador de comprimentos."""
        dimlfc        = 0.
        pardimlfc    = ctypes.c_double (dimlfc)
        self.m_dwg.m_mdwg.COTLFC_LER (ctypes.byref (pardimlfc))
        dimlfc        = pardimlfc.value
        return        dimlfc

    @dimlfc.setter
    def dimlfc (self, val: float) -> None:
        """Atribui Multiplicador de comprimentos."""
        pardimlfc     = ctypes.c_double (val)
        self.m_dwg.m_mdwg.COTLFC (ctypes.byref (pardimlfc))

    @property
    def idmniv (self) -> int:
        """Nível geral de cotagem."""
        idmniv        = 0
        paridmniv     = ctypes.c_int (idmniv)
        self.m_dwg.m_mdwg.COTNIVLER (ctypes.byref (paridmniv))
        idmniv        = paridmniv.value
        return        idmniv

    @idmniv.setter
    def idmniv (self, val: int) -> None:
        """Atribui Nível geral de cotagem."""
        paridmniv    = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTNIV (ctypes.byref (paridmniv))

    @property
    def idmnic (self) -> int:
        """Nível da linha de cotagem."""
        idmnic        = 0
        paridmnic     = ctypes.c_int (idmnic)
        self.m_dwg.m_mdwg.COTNICLER (ctypes.byref (paridmnic))
        idmnic        = paridmnic.value
        return        idmnic

    @idmnic.setter
    def idmnic (self, val: int) -> None:
        """Atribui Nível da linha de cotagem."""
        paridmnic      = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTNIC (ctypes.byref (paridmnic))

    @property
    def idmnil (self) -> int:
        """Nível da linha de chamada."""
        idmnil         = 0
        paridmnil      = ctypes.c_int (idmnil)
        self.m_dwg.m_mdwg.COTNILLER (ctypes.byref (paridmnil))
        idmnil         = paridmnil.value
        return         idmnil

    @idmnil.setter
    def idmnil (self, val: int) -> None:
        """Atribui Nível da linha de chamada."""
        paridmnil      = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTNIL (ctypes.byref (paridmnil))

    @property
    def idmnib (self) -> int:
        """Nível do símbolo de cotagem."""
        idmnib         = 0
        paridmnib      = ctypes.c_int (idmnib)
        self.m_dwg.m_mdwg.COTNIBLER (ctypes.byref (paridmnib))
        idmnib         = paridmnib.value
        return         idmnib

    @idmnib.setter
    def idmnib (self, val: int) -> None:
        """Atribui Nível do símbolo de cotagem."""
        paridmnib      = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTNIB (ctypes.byref (paridmnib))

    @property
    def idmcim (self) -> int:
        """``1`` se o texto fica abaixo da linha de cotagem."""
        idmcim         = 0
        paridmcim      = ctypes.c_int (idmcim)
        self.m_dwg.m_mdwg.COTCIM_LER (ctypes.byref (paridmcim))
        idmcim         = paridmcim.value
        return         idmcim

    @idmcim.setter
    def idmcim (self, val: int) -> None:
        """Atribui ``1`` se o texto fica abaixo da linha de cotagem."""
        paridmcim      = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTCIM (ctypes.byref (paridmcim))

    @property
    def idmar5 (self) -> int:
        """``1`` se as medidas são arredondadas de 5 em 5."""
        idmar5         = 0
        paridmar5      = ctypes.c_int (idmar5)
        self.m_dwg.m_mdwg.COTAR5_LER (ctypes.byref (paridmar5))
        idmar5         = paridmar5.value
        return         idmar5

    @idmar5.setter
    def idmar5 (self, val: int) -> None:
        """Atribui ``1`` se as medidas são arredondadas de 5 em 5."""
        paridmar5      = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTAR5 (ctypes.byref (paridmar5))

    @property
    def dimblk (self) -> str:
        """Nome do bloco de cotagem (``TICK``/``DOT``/``ARROW`` são pré-definidos)."""
        pardimblk      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.COTBLK_LER (ctypes.byref (pardimblk), 0)
        return         pardimblk.value.decode(TQS.TQSUtil.CHARSET)

    @dimblk.setter
    def dimblk (self, val: str) -> None:
        """Atribui Nome do bloco de cotagem (``TICK``/``DOT``/``ARROW`` são pré-definidos)."""
        pardimblk      = ctypes.c_char_p (val.encode(TQS.TQSUtil.CHARSET))
        self.m_dwg.m_mdwg.COTBLK (pardimblk, 0)

    @property
    def dimse1 (self) -> int:
        """``1`` se a linha de chamada é suprimida."""
        dimse1         = 0
        pardimse1      = ctypes.c_int (dimse1)
        self.m_dwg.m_mdwg.COTLCM_LER (ctypes.byref (pardimse1))
        dimse1         = pardimse1.value
        return         dimse1

    @dimse1.setter
    def dimse1 (self, val: int) -> None:
        """Atribui ``1`` se a linha de chamada é suprimida."""
        pardimse1      = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTLCM (ctypes.byref (pardimse1))

    @property
    def idmaut (self) -> int:
        """Modo automático: ``0`` não, ``1`` auto 2P, ``2`` auto ELM."""
        idmaut         = 0
        paridmaut      = ctypes.c_int (idmaut)
        self.m_dwg.m_mdwg.COTAUT_LER (ctypes.byref (paridmaut))
        idmaut         = paridmaut.value
        return         idmaut

    @idmaut.setter
    def idmaut (self, val: int) -> None:
        """Atribui Modo automático: ``0`` não, ``1`` auto 2P, ``2`` auto ELM."""
        paridmaut      = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTAUT (ctypes.byref (paridmaut))

    @property
    def idmcot (self) -> int:
        """``1`` se a linha de cotagem é suprimida."""
        idmcot         = 0
        paridmcot      = ctypes.c_int (idmcot)
        self.m_dwg.m_mdwg.COTIDMCOT_LER (ctypes.byref (paridmcot))
        idmcot         = paridmcot.value
        return         idmcot

    @idmcot.setter
    def idmcot (self, val: int) -> None:
        """Atribui ``1`` se a linha de cotagem é suprimida."""
        paridmcot      = ctypes.c_int (val)
        self.m_dwg.m_mdwg.COTIDMCOT (ctypes.byref (paridmcot))

    @property
    def dimtxu (self) -> str:
        """Texto manual de cotagem."""
        pardimtxu      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_dwg.m_mdwg.COTTXU_LER (pardimtxu, 0)
        return         pardimtxu.value.decode(TQS.TQSUtil.CHARSET)

    @dimtxu.setter
    def dimtxu (self, val: str) -> None:
        """Atribui Texto manual de cotagem."""
        pardimtxu      = ctypes.c_char_p (val.encode(TQS.TQSUtil.CHARSET))
        # COTTXU define o texto e COTETX o efetiva no modelo de cotagem
        self.m_dwg.m_mdwg.COTTXU (pardimtxu, 0)
        self.m_dwg.m_mdwg.COTETX ()

    def Dim3P (self, itipo: int, x1: float, y1: float, x2: float, y2: float,
               x3: float, y3: float) -> None:
        """Cotagem por 3 pontos.

        Args:
            itipo: Direção de cotagem ``IDHOR``/``IDVER``/``IDANG``/``IDINC``.
            x1: X do primeiro ponto de cotagem.
            y1: Y do primeiro ponto de cotagem.
            x2: X do segundo ponto de cotagem.
            y2: Y do segundo ponto de cotagem.
            x3: X do ponto da linha de cotagem.
            y3: Y do ponto da linha de cotagem.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        paritipo       = ctypes.c_int (itipo)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        parx3          = ctypes.c_double (x3)
        pary3          = ctypes.c_double (y3)
        # Pipeline padrão de cotagem: sincroniza variáveis -> executa cotagem -> grava texto
        self.m_dwg.m_mdwg.COTIFOR (parpedmv)
        self.m_dwg.m_mdwg.COT3P    (ctypes.byref(paritipo),
            ctypes.byref(parx1), ctypes.byref(pary1),
            ctypes.byref(parx2), ctypes.byref(pary2),
            ctypes.byref(parx3), ctypes.byref(pary3))
        self.m_dwg.m_mdwg.COTDTX ()

    def DimHorizontal (self, x1: float, y1: float, x2: float, y2: float,
                       x3: float, y3: float) -> None:
        """Faz cotagem horizontal entre dois pontos passando pelo terceiro.

        Args:
            x1: X do primeiro ponto de cotagem.
            y1: Y do primeiro ponto de cotagem.
            x2: X do segundo ponto de cotagem.
            y2: Y do segundo ponto de cotagem.
            x3: X do ponto da linha de cotagem.
            y3: Y do ponto da linha de cotagem.
        """
        self.Dim3P     (IDHOR, x1, y1, x2, y2, x3, y3)

    def DimVertical(self, x1: float, y1: float, x2: float, y2: float,
                    x3: float, y3: float) -> None:
        """Faz cotagem vertical entre dois pontos passando pelo terceiro.

        Args:
            x1: X do primeiro ponto de cotagem.
            y1: Y do primeiro ponto de cotagem.
            x2: X do segundo ponto de cotagem.
            y2: Y do segundo ponto de cotagem.
            x3: X do ponto da linha de cotagem.
            y3: Y do ponto da linha de cotagem.
        """
        self.Dim3P     (IDVER, x1, y1, x2, y2, x3, y3)

    def DimAligned (self, x1: float, y1: float, x2: float, y2: float,
                    x3: float, y3: float) -> None:
        """Cotagem alinhada entre dois pontos, na direção destes pontos.

        Args:
            x1: X do primeiro ponto de cotagem.
            y1: Y do primeiro ponto de cotagem.
            x2: X do segundo ponto de cotagem.
            y2: Y do segundo ponto de cotagem.
            x3: X do ponto da linha de cotagem.
            y3: Y do ponto da linha de cotagem.
        """
        self.Dim3P     (IDANG, x1, y1, x2, y2, x3, y3)

    def DimInclined (self, x1: float, y1: float, x2: float, y2: float,
                     x3: float, y3: float, ang: float) -> None:
        """Faz cotagem inclinada com ângulo fornecido entre dois pontos.

        Args:
            x1: X do primeiro ponto de cotagem.
            y1: Y do primeiro ponto de cotagem.
            x2: X do segundo ponto de cotagem.
            y2: Y do segundo ponto de cotagem.
            x3: X do ponto da linha de cotagem.
            y3: Y do ponto da linha de cotagem.
            ang: Ângulo de inclinação em graus.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        parx3          = ctypes.c_double (x3)
        pary3          = ctypes.c_double (y3)
        parang         = ctypes.c_double (ang)
        self.m_dwg.m_mdwg.COTIFOR (parpedmv)
        self.m_dwg.m_mdwg.COTINC (ctypes.byref(parang),
            ctypes.byref(parx1), ctypes.byref(pary1),
            ctypes.byref(parx2), ctypes.byref(pary2),
            ctypes.byref(parx3), ctypes.byref(pary3))
        self.m_dwg.m_mdwg.COTDTX ()

    def DimContinue (self, x: float, y: float) -> None:
        """Continua a última cotagem com ponto adicional.

        Args:
            x: X do ponto de continuação.
            y: Y do ponto de continuação.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parx           = ctypes.c_double (x)
        pary           = ctypes.c_double (y)
        self.m_dwg.m_mdwg.COTIFOR (parpedmv)
        self.m_dwg.m_mdwg.COTCON (ctypes.byref(parx), ctypes.byref(pary))
        self.m_dwg.m_mdwg.COTDTX ()


    def DimRadiusDiameter (self, itip: int, x1: float, y1: float,
                            x2: float, y2: float) -> None:
        """Cotagem de raio ou diâmetro de arco/círculo.

        Args:
            itip: ``0`` diâmetro, ``1`` raio.
            x1: X do primeiro ponto de cotagem.
            y1: Y do primeiro ponto de cotagem.
            x2: X do segundo ponto de cotagem.
            y2: Y do segundo ponto de cotagem.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        paritip        = ctypes.c_int (itip)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        self.m_dwg.m_mdwg.COTIFOR (parpedmv)
        self.m_dwg.m_mdwg.DIMAR2 (ctypes.byref(parx1), ctypes.byref(pary1),
            ctypes.byref(parx2), ctypes.byref(pary2), ctypes.byref(paritip))


    def DimRadius (self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Cotagem de raio de arco/círculo.

        Args:
            x1: X do primeiro ponto de cotagem.
            y1: Y do primeiro ponto de cotagem.
            x2: X do segundo ponto de cotagem.
            y2: Y do segundo ponto de cotagem.
        """
        itip        = 1
        self.DimRadiusDiameter (itip, x1, y1, x2, y2)

    def DimDiameter (self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Cotagem de diâmetro de arco/círculo.

        Args:
            x1: X do primeiro ponto de cotagem.
            y1: Y do primeiro ponto de cotagem.
            x2: X do segundo ponto de cotagem.
            y2: Y do segundo ponto de cotagem.
        """
        itip        = 0
        self.DimRadiusDiameter (itip, x1, y1, x2, y2)

    def DimAngular (self, x1: float, y1: float, x2: float, y2: float,
                     x3: float, y3: float, x4: float, y4: float,
                     xcota: float, ycota: float) -> None:
        """Cotagem angular entre as retas 1-2 e 3-4 passando pelo ponto de cota.

        Args:
            x1: X do primeiro ponto da reta 1.
            y1: Y do primeiro ponto da reta 1.
            x2: X do segundo ponto da reta 1.
            y2: Y do segundo ponto da reta 1.
            x3: X do primeiro ponto da reta 2.
            y3: Y do primeiro ponto da reta 2.
            x4: X do segundo ponto da reta 2.
            y4: Y do segundo ponto da reta 2.
            xcota: X do ponto da linha de cota.
            ycota: Y do ponto da linha de cota.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parx1          = ctypes.c_double (x1)
        pary1          = ctypes.c_double (y1)
        parx2          = ctypes.c_double (x2)
        pary2          = ctypes.c_double (y2)
        parx3          = ctypes.c_double (x3)
        pary3          = ctypes.c_double (y3)
        parx4          = ctypes.c_double (x4)
        pary4          = ctypes.c_double (y4)
        parxcota       = ctypes.c_double (xcota)
        parycota       = ctypes.c_double (ycota)
        self.m_dwg.m_mdwg.COTIFOR (parpedmv)
        self.m_dwg.m_mdwg.DIMANG (ctypes.byref(parx1), ctypes.byref(pary1),
            ctypes.byref(parx2), ctypes.byref(pary2),
            ctypes.byref(parx3), ctypes.byref(pary3),
            ctypes.byref(parx4), ctypes.byref(pary4),
            ctypes.byref(parxcota), ctypes.byref(parycota))

    def DimNote (self) -> None:
        """Desenha a linha com flecha de nota.

        Use :meth:`Draw.PolyStart` e :meth:`Draw.PolyEnterPoint` para a
        definição dos pontos. Será desenhada a polyline com uma flecha
        na ponta.
        """
        parpedmv     = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_mdwg.g_dsppfl (parpedmv)

#-----------------------------------------------------------------------------
#    Funções globais de posições de ferros - Dentro do Dwg ()
#
class GlobalRebar ():
    """Funções globais de posições de ferros associadas ao desenho.

    Implementação:
        Wrappers sobre ``IPOFER_POS_*`` de ``IPOFER.DLL`` para consultar e
        renumerar posições no escopo do desenho inteiro (não no escopo de
        um ferro individual).
    """

    def __init__ (self, dwg: "Dwg") -> None:
        """Inicializa o sub-objeto de posições globais de ferros.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
        """
        self.m_dwg      = dwg

    @property
    def firstMark (self) -> int:
        """Primeira posição para renumeração."""
        ifirstMark     = 0
        parifirstMark  = ctypes.c_int (ifirstMark)
        self.m_dwg.m_ipofer.IPOFER_POS_LERPRIMEIRA (ctypes.byref (parifirstMark))
        ifirstMark     = parifirstMark.value
        return      ifirstMark

    @firstMark.setter
    def firstMark (self, ifirstMark: int) -> None:
        """Atribui Primeira posição para renumeração."""
        parifirstMark  = ctypes.c_int (ifirstMark)
        self.m_dwg.m_ipofer.IPOFER_POS_PRIMEIRA (ctypes.byref (parifirstMark))

    def RenumerateMarks (self) -> None:
        """Renumeração de posições, a partir da primeira posição em :attr:`firstMark`."""
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        self.m_dwg.m_ipofer.IPOFER_POS_RENUMERAR (ctypes.byref (parpedmv))

    def FreeMark (self) -> int:
        """Retorna o próximo número de posição livre para uso.

        Returns:
            Próximo número de posição disponível.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        ifreeMark      = 0
        parifreeMark   = ctypes.c_int (ifreeMark)
        self.m_dwg.m_ipofer.IPOFER_POS_PROXLIVRE (ctypes.byref (parpedmv),
                                                  ctypes.byref (parifreeMark))
        ifreeMark      = parifreeMark.value
        return         ifreeMark

#-----------------------------------------------------------------------------
#    Ferros Inteligentes
#    Um objeto para cada ferro criado, associado a um Dwg
#
class SmartRebar ():
    """Ferro inteligente do TQS associado a um :class:`Dwg`.

    Cada instância representa um ferro específico no desenho, com bitola,
    posição, ganchos, dobras e múltiplas linhas de inserção. As propriedades
    expõem todos os parâmetros aceitos pela DLL ``IPOFER``.

    Implementação:
        Cada ferro é representado por um handle ``ferobjv`` (``c_void_p``)
        criado por ``IPOFER_CRIARFERRO`` ou recebido externamente (extração
        do desenho). As propriedades simples mapeiam diretamente para pares
        ``IPOFER_LER_XXX``/``IPOFER_XXX``. Grupos de campos correlatos
        (ganchos, raios de curvatura, dados de estribo, luvas, grampo,
        chamada automática) são lidos/escritos em bloco por métodos
        privados ``_LerXXX``/``_DefXXX`` para preservar valores não
        alterados pela API pública. As linhas de inserção e as faixas de
        distribuição são coleções acessadas por índice
        (``GetInsertionNumber`` / ``GetRebarDistrNum``). As operações
        geométricas (Move/Rotate/Scale/Mirror) usam o subconjunto
        ``OBJDWG_*`` da mesma DLL.
    """

    def __init__ (self, dwg: "Dwg", ferobjv: Optional[int] = None) -> None:
        """Cria um novo ferro ou encapsula um ferro existente.

        Args:
            dwg: Instância de :class:`Dwg` proprietária.
            ferobjv: Handle C++ para um ferro existente. Se ``None``,
                cria um novo ferro. Útil ao montar um :class:`SmartRebar`
                durante a extração de desenhos.
        """
        self.m_dwg      = dwg
        # Sem ferobjv pré-existente, aloca um novo ferro via IPOFER_CRIARFERRO
        if              ferobjv == None:
            parpedmv        = ctypes.c_void_p (self.m_dwg.m_pedmv)
            self.m_ferobjv  = 0
            parferobjv      = ctypes.c_void_p (self.m_ferobjv)
            istat           = 0
            paristat        = ctypes.c_int (istat)
            self.m_dwg.m_ipofer.IPOFER_CRIARFERRO (ctypes.byref (parpedmv),
                             ctypes.byref (parferobjv), ctypes.byref (paristat))
            self.m_ferobjv  = parferobjv.value
            istat           = paristat.value
            if              istat != 0:
                self.m_ferobjv = None
        else:
            # Caso contrário, encapsula o handle existente (ex.: extração de DWG)
            self.m_ferobjv  = ferobjv

    @property
    def handle_rebar (self) -> Optional[int]:
        """Referência a este ferro, que pode ser usada em outro comando."""
        return          self.m_ferobjv

    @property
    def uniqueid (self) -> int:
        """Identificador único do ferro dentro do desenho."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        iuniqueid      = 0
        pariuniqueid   = ctypes.c_int (iuniqueid)
        self.m_dwg.m_ipofer.IPOFER_IUNIQUEID (ctypes.byref (parferobjv),
                                              ctypes.byref (pariuniqueid))
        iuniqueid      = pariuniqueid.value
        return         iuniqueid

    @property
    def type (self) -> int:
        """Tipo de ferro.

        Valores:

        * :data:`ICPFRT`    Ferro reto.
        * :data:`ICPFGN`    Ferro genérico.
        * :data:`ICPSTR`    Estribo de viga.
        * :data:`ICPSTRGEN` Estribo genérico.
        * :data:`ICPGRA`    Grampo.
        * :data:`ICPFAIMUL` Faixa múltipla (não é ferro).
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icftpf         = ICPFRT
        paricftpf      = ctypes.c_int (icftpf)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFTPF (ctypes.byref (parferobjv),
                                               ctypes.byref (paricftpf))
        icftpf         = paricftpf.value
        return         icftpf

    @type.setter
    def type (self, icftpf: int) -> None:
        """Atribui Tipo de ferro."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricftpf      = ctypes.c_int (icftpf)
        self.m_dwg.m_ipofer.IPOFER_ICFTPF (ctypes.byref (parferobjv),
                                           ctypes.byref (paricftpf))

    @property
    def mark (self) -> int:
        """Número da posição do ferro."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfpos         = 0
        paricfpos      = ctypes.c_int (icfpos)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFPOS (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfpos))
        icfpos         = paricfpos.value
        return         icfpos

    @mark.setter
    def mark (self, icfpos: int) -> None:
        """Atribui Número da posição do ferro."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfpos      = ctypes.c_int (icfpos)
        self.m_dwg.m_ipofer.IPOFER_ICFPOS (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfpos))

    @property
    def quantity (self) -> int:
        """Número de ferros."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfnfr         = 0
        paricfnfr      = ctypes.c_int (icfnfr)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFNFR (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfnfr))
        icfnfr         = paricfnfr.value
        return         icfnfr

    @quantity.setter
    def quantity (self, icfnfr: int) -> None:
        """Atribui Número de ferros."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfnfr      = ctypes.c_int (icfnfr)
        self.m_dwg.m_ipofer.IPOFER_ICFNFR (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfnfr))

    @property
    def multiplier (self) -> int:
        """Multiplicador de ferros."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfmul         = 0
        paricfmul      = ctypes.c_int (icfmul)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFMUL (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfmul))
        icfmul         = paricfmul.value
        return         icfmul

    @multiplier.setter
    def multiplier (self, icfmul: int) -> None:
        """Atribui Multiplicador de ferros."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfmul      = ctypes.c_int (icfmul)
        self.m_dwg.m_ipofer.IPOFER_ICFMUL (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfmul))

    @property
    def diameter (self) -> float:
        """Bitola do ferro em mm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        cfrbit         = 0.
        parcfrbit      = ctypes.c_double (cfrbit)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRBIT (ctypes.byref (parferobjv),
                                               ctypes.byref (parcfrbit))
        cfrbit         = parcfrbit.value
        return         cfrbit

    @diameter.setter
    def diameter (self, cfrbit: float) -> None:
        """Atribui Bitola do ferro em mm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrbit      = ctypes.c_double (cfrbit)
        self.m_dwg.m_ipofer.IPOFER_CFRBIT (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrbit))

    @property
    def spacing (self) -> float:
        """Espaçamento entre ferros em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        cfresp         = 0.
        parcfresp      = ctypes.c_double (cfresp)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRESP (ctypes.byref (parferobjv),
                                               ctypes.byref (parcfresp))
        cfresp         = parcfresp.value
        return         cfresp

    @spacing.setter
    def spacing (self, cfresp: float) -> None:
        """Atribui Espaçamento entre ferros em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfresp      = ctypes.c_double (cfresp)
        self.m_dwg.m_ipofer.IPOFER_CFRESP (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfresp))

    @property
    def ribbed (self) -> int:
        """``0`` ferros em lajes maciças, ``1`` ferros em lajes nervuradas."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfnrv         = 0
        paricfnrv      = ctypes.c_int (icfnrv)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFNRV (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfnrv))
        icfnrv         = paricfnrv.value
        return         icfnrv

    @ribbed.setter
    def ribbed (self, icfnrv: int) -> None:
        """Atribui ``0`` ferros em lajes maciças, ``1`` ferros em lajes nervuradas."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfnrv      = ctypes.c_int (icfnrv)
        self.m_dwg.m_ipofer.IPOFER_ICFNRV (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfnrv))

    @property
    def showRibbed (self) -> int:
        """``0`` não mostrar, ``1`` mostrar status de laje nervurada (``C/NERV``)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfnes         = 0
        paricfnes      = ctypes.c_int (icfnes)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFNES (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfnes))
        icfnes         = paricfnes.value
        return         icfnes

    @showRibbed.setter
    def showRibbed (self, icfnes: int) -> None:
        """Atribui ``0`` não mostrar, ``1`` mostrar status de laje nervurada (``C/NERV``)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfnes      = ctypes.c_int (icfnes)
        self.m_dwg.m_ipofer.IPOFER_ICFNES (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfnes))

    @property
    def comment (self) -> str:
        """Comentário do ferro."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrobs      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        argfan         = ctypes.c_int (0)
        self.m_dwg.m_ipofer.IPOFER_LER_CFROBS (ctypes.byref (parferobjv), parcfrobs, argfan)
        cfrobs         = parcfrobs.value.decode(TQS.TQSUtil.CHARSET)
        return         cfrobs

    @comment.setter
    def comment (self, cfrobs: str) -> None:
        """Atribui Comentário do ferro."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrobs      = ctypes.c_char_p (cfrobs.encode(TQS.TQSUtil.CHARSET))
        argfan         = ctypes.c_int (0)
        self.m_dwg.m_ipofer.IPOFER_CFROBS (ctypes.byref (parferobjv), parcfrobs, argfan)


    def _LerIcgtge (self) -> Tuple[int, int]:
        """Lê dados do gancho à esquerda."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icgtge         = 0
        paricgtge      = ctypes.c_int (icgtge)
        icgtgeneg      = 0
        paricgtgeneg   = ctypes.c_int (icgtgeneg)
        self.m_dwg.m_ipofer.IPOFER_LER_ICGTGE (ctypes.byref (parferobjv),
                         ctypes.byref (paricgtge), ctypes.byref (paricgtgeneg))
        return         paricgtge.value, paricgtgeneg.value

    def _DefIcgtge (self, icgtge: int, icgtgeneg: int) -> None:
        """Define dados do gancho à esquerda."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricgtge      = ctypes.c_int (icgtge)
        paricgtgeneg   = ctypes.c_int (icgtgeneg)
        self.m_dwg.m_ipofer.IPOFER_ICGTGE (ctypes.byref (parferobjv),
                         ctypes.byref (paricgtge), ctypes.byref (paricgtgeneg))

    @property
    def leftHook (self) -> int:
        """Tipo de gancho à esquerda: :data:`ICPSGA`, :data:`ICP090`, :data:`ICP135`, :data:`ICP180`."""
        icgtge, icgtgeneg = self._LerIcgtge ()
        return            icgtge


    @leftHook.setter
    def leftHook (self, icgtge: int) -> None:
        """Atribui Tipo de gancho à esquerda: :data:`ICPSGA`, :data:`ICP090`, :data:`ICP135`, :data:`ICP180`."""
        icgtge2, icgtgeneg = self._LerIcgtge ()
        self._DefIcgtge (icgtge, icgtgeneg)

    @property
    def leftHookInvert (self) -> int:
        """``0`` não, ``1`` gancho à esquerda invertido.

        ATENÇÃO: o setter logo abaixo é decorado com ``@leftHook.setter`` mas
        nomeado ``leftHookInvert``. Na biblioteca TQS isso substitui esta
        propriedade por uma combinação do getter de ``leftHook`` com o setter de
        inversão: LER ``leftHookInvert`` devolve o TIPO do gancho
        (:data:`ICP090` etc.), não o indicador de inversão. ESCREVER grava a
        inversão corretamente.
        """
        icgtge, icgtgeneg = self._LerIcgtge ()
        return            icgtgeneg


    @leftHook.setter
    def leftHookInvert (self, icgtgeneg: int) -> None:
        """Atribui Tipo de gancho à esquerda: :data:`ICPSGA`, :data:`ICP090`, :data:`ICP135`, :data:`ICP180`."""
        icgtge, icgtgeneg2 = self._LerIcgtge ()
        self._DefIcgtge (icgtge, icgtgeneg)


    def _LerIcgtgd (self) -> Tuple[int, int]:
        """Lê dados do gancho à direita."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icgtgd         = 0
        paricgtgd      = ctypes.c_int (icgtgd)
        icgtgdneg      = 0
        paricgtgdneg   = ctypes.c_int (icgtgdneg)
        self.m_dwg.m_ipofer.IPOFER_LER_ICGTGD (ctypes.byref (parferobjv),
                         ctypes.byref (paricgtgd), ctypes.byref (paricgtgdneg))
        return         paricgtgd.value, paricgtgdneg.value

    def _DefIcgtgd (self, icgtgd: int, icgtgdneg: int) -> None:
        """Define dados do gancho à direita."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricgtgd      = ctypes.c_int (icgtgd)
        paricgtgdneg   = ctypes.c_int (icgtgdneg)
        self.m_dwg.m_ipofer.IPOFER_ICGTGD (ctypes.byref (parferobjv),
                         ctypes.byref (paricgtgd), ctypes.byref (paricgtgdneg))

    @property
    def rightHook (self) -> int:
        """Tipo de gancho à direita: :data:`ICPSGA`, :data:`ICP090`, :data:`ICP135`, :data:`ICP180`."""
        icgtgd, icgtgdneg = self._LerIcgtgd ()
        return            icgtgd


    @rightHook.setter
    def rightHook (self, icgtgd: int) -> None:
        """Atribui Tipo de gancho à direita: :data:`ICPSGA`, :data:`ICP090`, :data:`ICP135`, :data:`ICP180`."""
        icgtgd2, icgtgdneg = self._LerIcgtgd ()
        self._DefIcgtgd (icgtgd, icgtgdneg)

    @property
    def rightHookInvert (self) -> int:
        """``0`` não, ``1`` gancho à direita invertido.

        ATENÇÃO: o setter logo abaixo é decorado com ``@rightHook.setter`` mas
        nomeado ``rightHookInvert``. Na biblioteca TQS isso substitui esta
        propriedade por uma combinação do getter de ``rightHook`` com o setter de
        inversão: LER ``rightHookInvert`` devolve o TIPO do gancho
        (:data:`ICP090` etc.), não o indicador de inversão. ESCREVER grava a
        inversão corretamente.
        """
        icgtgd, icgtgdneg = self._LerIcgtgd ()
        return            icgtgdneg


    @rightHook.setter
    def rightHookInvert (self, icgtgdneg: int) -> None:
        """Atribui Tipo de gancho à direita: :data:`ICPSGA`, :data:`ICP090`, :data:`ICP135`, :data:`ICP180`."""
        icgtgd, icgtgdneg2 = self._LerIcgtgd ()
        self._DefIcgtgd (icgtgd, icgtgdneg)

    @property
    def columnLevel (self) -> int:
        """Lance de pilar."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        ilance         = 0
        parilance      = ctypes.c_int (ilance)
        self.m_dwg.m_ipofer.IPOFER_LER_LANCE (ctypes.byref (parferobjv),
                                              ctypes.byref (parilance))
        ilance         = parilance.value
        return         ilance

    @columnLevel.setter
    def columnLevel (self, ilance: int) -> None:
        """Atribui Lance de pilar."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parilance      = ctypes.c_int (ilance)
        self.m_dwg.m_ipofer.IPOFER_DEFLANCE (ctypes.byref (parferobjv),
                                             ctypes.byref (parilance))


    @property
    def cover (self) -> float:
        """Cobrimento em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        cfrreb         = 0.
        parcfrreb      = ctypes.c_double (cfrreb)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRREB (ctypes.byref (parferobjv),
                                               ctypes.byref (parcfrreb))
        cfrreb         = parcfrreb.value
        return         cfrreb

    @cover.setter
    def cover (self, cfrreb: float) -> None:
        """Atribui Cobrimento em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrreb      = ctypes.c_double (cfrreb)
        self.m_dwg.m_ipofer.IPOFER_CFRREB (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrreb))

    def RebarLine (self, xins: float, yins: float, angle: float, scale: float,
                   identify: int, identifyBends: int, ipatas: int,
                   iexplode: int, ilevel: int, iestilo: int, icolor: int) -> None:
        """Insere uma linha de ferro com os dados atuais.

        Um mesmo ferro pode ser representado por mais de uma linha no desenho.

        Args:
            xins: X do ponto de inserção.
            yins: Y do ponto de inserção.
            angle: Ângulo de inserção em graus.
            scale: Escala de inserção.
            identify: ``1`` para identificar o ferro.
            identifyBends: ``1`` para identificar dobras.
            ipatas: ``0`` não, ``1`` sim, ``2`` 45°, ``3`` 225°, ``4`` invertido.
                ``0/1`` valem para ``ICPFRT``, ``ICPSTR``, ``ICPSTRGEN`` e ``ICPGRA``.
                ``2/3/4`` valem para ``ICPFRT``.
            iexplode: ``1`` para explodir se for estribo.
            ilevel: Nível ``0..255`` EAG, ``-1`` default.
            iestilo: Estilo ``0..5`` EAG, ``-1`` default.
            icolor: Cor ``0..255`` EAG, ``-1`` default.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parxins        = ctypes.c_double (xins)
        paryins        = ctypes.c_double (yins)
        parangle       = ctypes.c_double (angle)
        parscale       = ctypes.c_double (scale)
        paridentify    = ctypes.c_int (identify)
        paridentifyBend= ctypes.c_int (identifyBends)
        paripatas      = ctypes.c_int (ipatas)
        pariexplode    = ctypes.c_int (iexplode)
        parilevel      = ctypes.c_int (ilevel)
        pariestilo     = ctypes.c_int (iestilo)
        paricolor      = ctypes.c_int (icolor)
        self.m_dwg.m_ipofer.IPOFER_LINHAFER (ctypes.byref (parferobjv),
            ctypes.byref (parxins), ctypes.byref (paryins), ctypes.byref (parangle),
            ctypes.byref (parscale), ctypes.byref (paridentify), ctypes.byref (paridentifyBend),
            ctypes.byref (paripatas), ctypes.byref (pariexplode), ctypes.byref (parilevel),
            ctypes.byref (pariestilo), ctypes.byref (paricolor))

    def GetInsertionNumber (self) -> int:
        """Retorna o número de linhas inseridas associadas a este ferro.

        Returns:
            Número de linhas inseridas.
        """
        parferobjv  = ctypes.c_void_p (self.m_ferobjv)
        numins      = 0
        parnumins   = ctypes.c_int (numins)
        self.m_dwg.m_ipofer.IPOFER_LER_NUMINSER (ctypes.byref (parferobjv),
                      ctypes.byref (parnumins))
        numins      = parnumins.value
        return      numins

    def GetInsertionData (self, indexins: int) -> Tuple[float, float, float, float,
                                                          int, int, int, int, int, int, int]:
        """Retorna os dados de uma linha inserida.

        Args:
            indexins: Índice da linha inserida em ``0..GetInsertionNumber()-1``.

        Returns:
            Tupla ``(xins, yins, angins, escxy, identfer, identdobr, ipatas,
            iexplodir, inivel, iestilo, icor)`` com ponto de inserção,
            ângulo, escala, flags de identificação, patas, explode e
            atributos gráficos.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parindexins     = ctypes.c_int (indexins)
        xins            = 0.
        parxins         = ctypes.c_double (xins)
        yins            = 0.
        paryins         = ctypes.c_double (yins)
        angins          = 0.
        parangins       = ctypes.c_double (angins)
        escxy           = 0.
        parescxy        = ctypes.c_double (escxy)
        identfer        = 0
        paridentfer     = ctypes.c_int (identfer)
        identdobr       = 0
        paridentdobr    = ctypes.c_int (identdobr)
        ipatas          = 0
        paripatas       = ctypes.c_int (ipatas)
        iexplodir       = 0
        pariexplodir    = ctypes.c_int (iexplodir)
        inivel          = 0
        parinivel       = ctypes.c_int (inivel)
        iestilo         = 0
        pariestilo      = ctypes.c_int (iestilo)
        icor            = 0
        paricor         = ctypes.c_int (icor)
        self.m_dwg.m_ipofer.IPOFER_LER_INSERCAO (ctypes.byref (parferobjv), ctypes.byref (parindexins),
                          ctypes.byref (parxins), ctypes.byref (paryins), ctypes.byref (parangins),
                          ctypes.byref (parescxy), ctypes.byref (paridentfer),
                          ctypes.byref (paridentdobr), ctypes.byref (paripatas),
                          ctypes.byref (pariexplodir), ctypes.byref (parinivel),
                          ctypes.byref (pariestilo), ctypes.byref (paricor))
        xins            = parxins.value
        yins            = paryins.value
        angins          = parangins.value
        escxy           = parescxy.value
        identfer        = paridentfer.value
        identdobr       = paridentdobr.value
        ipatas          = paripatas.value
        iexplodir       = pariexplodir.value
        inivel          = parinivel.value
        iestilo         = pariestilo.value
        icor            = paricor.value
        return          xins, yins, angins, escxy, identfer, identdobr, ipatas, iexplodir, inivel, iestilo, icor

    def GetInsertionPoints (self, indexins: int) -> Tuple[int, int]:
        """Retorna o número de pontos de uma inserção.

        Args:
            indexins: Índice da linha inserida em ``0..GetInsertionNumber()-1``.

        Returns:
            Tupla ``(np, istat)`` com o número de pontos e ``istat == 0`` Ok,
            ``!= 0`` se não leu.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parindexins     = ctypes.c_int (indexins)
        np              = 0
        parnp           = ctypes.c_int (np)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_dwg.m_ipofer.IPOFER_LER_INSERCAOPOLIGNP (ctypes.byref (parferobjv),
                        ctypes.byref (parindexins), ctypes.byref (parnp),
                        ctypes.byref (paristat))
        np              = parnp.value
        istat           = paristat.value
        return          np, istat

    def GetInsertionPoint (self, indexins: int, ipt: int) -> Tuple[float, float, int]:
        """Retorna as coordenadas de um ponto de um ferro inserido.

        Args:
            indexins: Índice da linha inserida em ``0..GetInsertionNumber()-1``.
            ipt: Ponto a ler em ``0..np-1``.

        Returns:
            Tupla ``(x, y, istat)`` com coordenadas e status (``0`` Ok,
            ``!= 0`` se não leu).
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parindexins     = ctypes.c_int (indexins)
        paript          = ctypes.c_int (ipt)
        x               = 0.
        parx            = ctypes.c_double (x)
        y               = 0.
        pary            = ctypes.c_double (y)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_dwg.m_ipofer.IPOFER_LER_INSERCAOPOLIGXY (ctypes.byref (parferobjv),
                        ctypes.byref (parindexins), ctypes.byref (paript),
                        ctypes.byref (parx), ctypes.byref (pary), ctypes.byref (paristat))
        x               = parx.value
        y               = pary.value
        istat           = paristat.value
        return          x, y, istat

    def SetInsertionData (self, indexins: int, xins: float, yins: float, angins: float,
                          escxy: float, identfer: int, identdobr: int, ipatas: int,
                          iexplodir: int, inivel: int, iestilo: int, icor: int) -> None:
        """Redefine os dados de uma linha inserida.

        Args:
            indexins: Índice da linha em ``0..GetInsertionNumber()-1``.
            xins: X do ponto de inserção.
            yins: Y do ponto de inserção.
            angins: Ângulo de inserção em graus.
            escxy: Escala de inserção.
            identfer: ``1`` identifica o ferro.
            identdobr: ``1`` identifica dobras.
            ipatas: ``0`` não, ``1`` sim, ``2`` 45°.
            iexplodir: ``1`` se representação explodida.
            inivel: Nível EAG, ``-1`` default.
            iestilo: Estilo EAG, ``-1`` default.
            icor: Cor EAG, ``-1`` default.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parindexins     = ctypes.c_int (indexins)
        parxins         = ctypes.c_double (xins)
        paryins         = ctypes.c_double (yins)
        parangins       = ctypes.c_double (angins)
        parescxy        = ctypes.c_double (escxy)
        paridentfer     = ctypes.c_int (identfer)
        paridentdobr    = ctypes.c_int (identdobr)
        paripatas       = ctypes.c_int (ipatas)
        pariexplodir    = ctypes.c_int (iexplodir)
        parinivel       = ctypes.c_int (inivel)
        pariestilo      = ctypes.c_int (iestilo)
        paricor         = ctypes.c_int (icor)
        self.m_dwg.m_ipofer.IPOFER_MOD_INSERCAO (ctypes.byref (parferobjv), ctypes.byref (parindexins),
                          ctypes.byref (parxins), ctypes.byref (paryins), ctypes.byref (parangins),
                          ctypes.byref (parescxy), ctypes.byref (paridentfer),
                          ctypes.byref (paridentdobr), ctypes.byref (paripatas),
                          ctypes.byref (pariexplodir), ctypes.byref (parinivel),
                          ctypes.byref (pariestilo), ctypes.byref (paricor))

    def SetInsertionPoint (self, indexins: int, ipt: int, x: float, y: float) -> int:
        """Redefine as coordenadas de um ponto de um ferro inserido.

        Args:
            indexins: Índice da linha em ``0..GetInsertionNumber()-1``.
            ipt: Ponto a redefinir em ``0..np-1``.
            x: Nova abscissa X.
            y: Nova ordenada Y.

        Returns:
            ``0`` Ok, ``!= 0`` se não leu.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parindexins     = ctypes.c_int (indexins)
        paript          = ctypes.c_int (ipt)
        parx            = ctypes.c_double (x)
        pary            = ctypes.c_double (y)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_dwg.m_ipofer.IPOFER_DEF_INSERCAOPOLIGXY (ctypes.byref (parferobjv),
                        ctypes.byref (parindexins), ctypes.byref (paript),
                        ctypes.byref (parx), ctypes.byref (pary), ctypes.byref (paristat))
        istat           = paristat.value
        return          istat

    @property
    def repeated (self) -> int:
        """``0`` não, ``1`` ferro repetido."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        irepeated      = 0
        parirepeated   = ctypes.c_int (irepeated)
        self.m_dwg.m_ipofer.IPOFER_LER_REPETIR (ctypes.byref (parferobjv),
                                                ctypes.byref (parirepeated))
        irepeated      = parirepeated.value
        return         irepeated

    @repeated.setter
    def repeated (self, irepeated: int) -> None:
        """Atribui ``0`` não, ``1`` ferro repetido."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parirepeated   = ctypes.c_int (irepeated)
        self.m_dwg.m_ipofer.IPOFER_REPETIR (ctypes.byref (parferobjv),
                                            ctypes.byref (parirepeated))

    def _LerRaiosCurv (self) -> Tuple[int, float, int, int, int, int, int, int, float]:
        """Lê os parâmetros de raios de curvatura/dobra do ferro."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        icftpdob        = 0
        cfrrai          = 0.
        icfrai          = 0
        icfraa          = 0
        icfrad          = 0
        icfrcurcotrai   = 0
        icfrcurcotdes   = 0
        icfrcurdestic   = 0
        cfrrcurtamtic   = 0.
        paricftpdob     = ctypes.c_int    (icftpdob)
        parcfrrai       = ctypes.c_double (cfrrai)
        paricfrai       = ctypes.c_int    (icfrai)
        paricfraa       = ctypes.c_int    (icfraa)
        paricfrad       = ctypes.c_int    (icfrad)
        paricfrcurcotrai= ctypes.c_int    (icfrcurcotrai)
        paricfrcurcotdes= ctypes.c_int    (icfrcurcotdes)
        paricfrcurdestic= ctypes.c_int    (icfrcurdestic)
        parcfrrcurtamtic= ctypes.c_double (cfrrcurtamtic)
        self.m_dwg.m_ipofer.IPOFER_LER_RAIOSDECURV (ctypes.byref (parferobjv),
            ctypes.byref (paricftpdob), ctypes.byref (parcfrrai), ctypes.byref (paricfrai),
            ctypes.byref (paricfraa), ctypes.byref (paricfrad), ctypes.byref (paricfrcurcotrai),
            ctypes.byref (paricfrcurcotdes), ctypes.byref (paricfrcurdestic),
            ctypes.byref (parcfrrcurtamtic))
        icftpdob        = paricftpdob.value
        cfrrai          = parcfrrai.value
        icfrai          = paricfrai.value
        icfraa          = paricfraa.value
        icfrad          = paricfrad.value
        icfrcurcotrai   = paricfrcurcotrai.value
        icfrcurcotdes   = paricfrcurcotdes.value
        icfrcurdestic   = paricfrcurdestic.value
        cfrrcurtamtic   = parcfrrcurtamtic.value
        return           icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic

    def _DefRaiosCurv (self, icftpdob: int, cfrrai: float, icfrai: int, icfraa: int,
                        icfrad: int, icfrcurcotrai: int, icfrcurcotdes: int,
                        icfrcurdestic: int, cfrrcurtamtic: float) -> None:
        """Define os parâmetros de raios de curvatura/dobra do ferro."""
        parferobjv      = ctypes.c_void_p   (self.m_ferobjv)
        paricftpdob     = ctypes.c_int    (icftpdob)
        parcfrrai       = ctypes.c_double (cfrrai)
        paricfrai       = ctypes.c_int    (icfrai)
        paricfraa       = ctypes.c_int    (icfraa)
        paricfrad       = ctypes.c_int    (icfrad)
        paricfrcurcotrai= ctypes.c_int    (icfrcurcotrai)
        paricfrcurcotdes= ctypes.c_int    (icfrcurcotdes)
        paricfrcurdestic= ctypes.c_int    (icfrcurdestic)
        parcfrrcurtamtic= ctypes.c_double (cfrrcurtamtic)
        self.m_dwg.m_ipofer.IPOFER_RAIOSDECURV (ctypes.byref (parferobjv),
            ctypes.byref (paricftpdob), ctypes.byref (parcfrrai), ctypes.byref (paricfrai),
            ctypes.byref (paricfraa), ctypes.byref (paricfrad), ctypes.byref (paricfrcurcotrai),
            ctypes.byref (paricfrcurcotdes), ctypes.byref (paricfrcurdestic),
            ctypes.byref (parcfrrcurtamtic))

    @property
    def bendType (self) -> int:
        """Tipo de dobra: :data:`ICPTPDOBGAN` ou :data:`ICPTPDOBNOP`."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           icftpdob


    @bendType.setter
    def bendType (self, icftpdob: int) -> None:
        """Atribui :data:`ICPTPDOBGAN` ou :data:`ICPTPDOBNOP`."""
        icftpdob2, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)

    @property
    def bendRadius (self) -> float:
        """Raio de dobra atual em cm; ``0`` para usar em função da bitola."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           cfrrai


    @bendRadius.setter
    def bendRadius (self, cfrrai: float) -> None:
        """Atribui Raio de dobra atual em cm; ``0`` para usar em função da bitola."""
        icftpdob, cfrrai2, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)


    @property
    def bendTotalLengthMode (self) -> int:
        """Modo de desconto de raios de dobra do comprimento total.

        Valores: :data:`ICPDEF`, :data:`ICPSRA`, :data:`ICPCRA`, :data:`ICPSMS`.
        """
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           icfrai


    @bendTotalLengthMode.setter
    def bendTotalLengthMode (self, icfrai: int) -> None:
        """Atribui Modo de desconto de raios de dobra do comprimento total."""
        icftpdob, cfrrai, icfrai2, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)


    @property
    def bendRadiusDisplay (self) -> int:
        """Modo de apresentação dos raios de dobra: :data:`ICPDEF`, :data:`ICPMAN`, :data:`ICPAUT`."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           icfraa


    @bendRadiusDisplay.setter
    def bendRadiusDisplay (self, icfraa: int) -> None:
        """Atribui Modo de apresentação dos raios de dobra: :data:`ICPDEF`, :data:`ICPMAN`, :data:`ICPAUT`."""
        icftpdob, cfrrai, icfrai, icfraa2, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)


    @property
    def bendBendLengthMode (self) -> int:
        """Modo de representação de desconto das dobras: :data:`ICPDEF`, :data:`ICPDOBSRA`, :data:`ICPDOBCRA`, :data:`ICPDOBSMS`."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           icfrad


    @bendBendLengthMode.setter
    def bendBendLengthMode (self, icfrad: int) -> None:
        """Atribui Modo de representação de desconto das dobras: :data:`ICPDEF`, :data:`ICPDOBSRA`, :data:`ICPDOBCRA`, :data:`ICPDOBSMS`."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad2, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)


    @property
    def bendDimRadius (self) -> int:
        """Cotagem de raio de curvatura: ``-1`` critério, ``0`` não, ``1`` sim."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           icfrcurcotrai


    @bendDimRadius.setter
    def bendDimRadius (self, icfrcurcotrai: int) -> None:
        """Atribui ``-1`` critério, ``0`` não, ``1`` sim."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai2, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)


    @property
    def bendDimPerimeter (self) -> int:
        """Cotagem de perímetro da curvatura: ``-1`` critério, ``0`` não, ``1`` sim."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           icfrcurcotdes


    @bendDimPerimeter.setter
    def bendDimPerimeter (self, icfrcurcotdes: int) -> None:
        """Atribui Cotagem de perímetro da curvatura: ``-1`` critério, ``0`` não, ``1`` sim."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes2, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)


    @property
    def bendTickDisplay (self) -> int:
        """Desenho de tick da cotagem de curvatura: ``-1`` critério, ``0`` não, ``1`` sim."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           icfrcurdestic


    @bendTickDisplay.setter
    def bendTickDisplay (self, icfrcurdestic: int) -> None:
        """Atribui ``-1`` critério, ``0`` não, ``1`` sim."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic2, cfrrcurtamtic = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)


    @property
    def bendTickSize (self) -> float:
        """Tamanho do tick da cotagem da curvatura em cm de plotagem."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic = self._LerRaiosCurv ()
        return           cfrrcurtamtic


    @bendTickSize.setter
    def bendTickSize (self, cfrrcurtamtic: float) -> None:
        """Atribui Tamanho do tick da cotagem da curvatura em cm de plotagem."""
        icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai, icfrcurcotdes, icfrcurdestic, cfrrcurtamtic2 = self._LerRaiosCurv ()
        self._DefRaiosCurv (icftpdob, cfrrai, icfrai, icfraa, icfrad, icfrcurcotrai,
                       icfrcurcotdes, icfrcurdestic, cfrrcurtamtic)


    @property
    def textHeigth (self) -> float:
        """Altura do texto de ferros em cm de plotagem."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        cfrtfr         = 0.
        parcfrtfr      = ctypes.c_double (cfrtfr)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRTFR (ctypes.byref (parferobjv),
                                               ctypes.byref (parcfrtfr))
        cfrtfr         = parcfrtfr.value
        return         cfrtfr

    @textHeigth.setter
    def textHeigth (self, cfrtfr: float) -> None:
        """Atribui Altura do texto de ferros em cm de plotagem."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrtfr      = ctypes.c_double (cfrtfr)
        self.m_dwg.m_ipofer.IPOFER_CFRTFR (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrtfr))

    @property
    def distributionTextHeigth (self) -> float:
        """Altura do texto de descrição das faixas de distribuição em cm de plotagem."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        cfrtfai        = 0.
        parcfrtfai     = ctypes.c_double (cfrtfai)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRTFAI (ctypes.byref (parferobjv),
                                                ctypes.byref (parcfrtfai))
        cfrtfai         = parcfrtfai.value
        return         cfrtfai

    @distributionTextHeigth.setter
    def distributionTextHeigth (self, cfrtfai: float) -> None:
        """Atribui Altura do texto de descrição das faixas de distribuição em cm de plotagem."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrtfai      = ctypes.c_double (cfrtfai)
        self.m_dwg.m_ipofer.IPOFER_CFRTFAI (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrtfai))


    @property
    def straightBarMainLength (self) -> float:
        """Comprimento principal de ferro reto em cm."""
        parferobjv    = ctypes.c_void_p (self.m_ferobjv)
        cfrcho        = 0.
        parcfrcho     = ctypes.c_double (cfrcho)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRCHO (ctypes.byref (parferobjv),
                                                ctypes.byref (parcfrcho))
        cfrcho         = parcfrcho.value
        return         cfrcho

    @straightBarMainLength.setter
    def straightBarMainLength (self, cfrcho: float) -> None:
        """Atribui Comprimento principal de ferro reto em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrcho      = ctypes.c_double (cfrcho)
        self.m_dwg.m_ipofer.IPOFER_CFRCHO (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrcho))

    @property
    def straightBarLeftLength (self) -> float:
        """Comprimento da dobra esquerda de ferro reto em cm."""
        parferobjv    = ctypes.c_void_p (self.m_ferobjv)
        cfrdes        = 0.
        parcfrdes     = ctypes.c_double (cfrdes)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRDES (ctypes.byref (parferobjv),
                                                ctypes.byref (parcfrdes))
        cfrdes         = parcfrdes.value
        return         cfrdes

    @straightBarLeftLength.setter
    def straightBarLeftLength (self, cfrdes: float) -> None:
        """Atribui Comprimento da dobra esquerda de ferro reto em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrdes      = ctypes.c_double (cfrdes)
        self.m_dwg.m_ipofer.IPOFER_CFRDES (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrdes))

    @property
    def straightBarRightLength (self) -> float:
        """Comprimento da dobra direita de ferro reto em cm."""
        parferobjv    = ctypes.c_void_p (self.m_ferobjv)
        cfrded        = 0.
        parcfrded     = ctypes.c_double (cfrded)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRDED (ctypes.byref (parferobjv),
                                                ctypes.byref (parcfrded))
        cfrded         = parcfrded.value
        return         cfrded

    @straightBarRightLength.setter
    def straightBarRightLength (self, cfrded: float) -> None:
        """Atribui Comprimento da dobra direita de ferro reto em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrded      = ctypes.c_double (cfrded)
        self.m_dwg.m_ipofer.IPOFER_CFRDED (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrded))

    @property
    def straightBarLeftLength2 (self) -> float:
        """Comprimento da 2ª dobra esquerda de ferro reto em cm."""
        parferobjv    = ctypes.c_void_p (self.m_ferobjv)
        cfrde2        = 0.
        parcfrde2     = ctypes.c_double (cfrde2)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRDE2 (ctypes.byref (parferobjv),
                                                ctypes.byref (parcfrde2))
        cfrde2         = parcfrde2.value
        return         cfrde2

    @straightBarLeftLength2.setter
    def straightBarLeftLength2 (self, cfrde2: float) -> None:
        """Atribui Comprimento da 2ª dobra esquerda de ferro reto em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrde2      = ctypes.c_double (cfrde2)
        self.m_dwg.m_ipofer.IPOFER_CFRDE2 (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrde2))

    @property
    def straightBarRightLength2 (self) -> float:
        """Comprimento da 2ª dobra direita de ferro reto em cm."""
        parferobjv    = ctypes.c_void_p (self.m_ferobjv)
        cfrdd2        = 0.
        parcfrdd2     = ctypes.c_double (cfrdd2)
        self.m_dwg.m_ipofer.IPOFER_LER_CFRDD2 (ctypes.byref (parferobjv),
                                                ctypes.byref (parcfrdd2))
        cfrdd2         = parcfrdd2.value
        return         cfrdd2

    @straightBarRightLength2.setter
    def straightBarRightLength2 (self, cfrdd2: float) -> None:
        """Atribui Comprimento da 2ª dobra direita de ferro reto em cm."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfrdd2      = ctypes.c_double (cfrdd2)
        self.m_dwg.m_ipofer.IPOFER_CFRDD2 (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfrdd2))


    @property
    def straightBarZone (self) -> int:
        """Posição de ferro reto: :data:`ICPPOS` (positiva) ou :data:`ICPNEG` (negativa)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfipn         = 0
        paricfipn      = ctypes.c_int (icfipn)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFIPN (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfipn))
        icfipn         = paricfipn.value
        return         icfipn

    @straightBarZone.setter
    def straightBarZone (self, icfipn: int) -> None:
        """Atribui Posição de ferro reto: :data:`ICPPOS` (positiva) ou :data:`ICPNEG` (negativa)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfipn      = ctypes.c_int (icfipn)
        self.m_dwg.m_ipofer.IPOFER_ICFIPN (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfipn))

    @property
    def straightBarBendType (self) -> int:
        """Tipo de dobra de ferro reto: :data:`ICPNSU`, :data:`ICPDSU` ou :data:`ICPDS2`."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfdsu         = 0
        paricfdsu      = ctypes.c_int (icfdsu)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFDSU (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfdsu))
        icfdsu         = paricfdsu.value
        return         icfdsu

    @straightBarBendType.setter
    def straightBarBendType (self, icfdsu: int) -> None:
        """Atribui :data:`ICPNSU`, :data:`ICPDSU` ou :data:`ICPDS2`."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfdsu      = ctypes.c_int (icfdsu)
        self.m_dwg.m_ipofer.IPOFER_ICFDSU (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfdsu))

    @property
    def straightBarTextDirection (self) -> int:
        """Direção dos textos de dobras: ``0`` direção do trecho, ``1`` direção do ferro."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        idirdobr       = 0
        paridirdobr    = ctypes.c_int (idirdobr)
        self.m_dwg.m_ipofer.IPOFER_LER_IDIRDOBR (ctypes.byref (parferobjv),
                                                 ctypes.byref (paridirdobr))
        idirdobr         = paridirdobr.value
        return         idirdobr

    @straightBarTextDirection.setter
    def straightBarTextDirection (self, idirdobr: int) -> None:
        """Atribui Direção dos textos de dobras: ``0`` direção do trecho, ``1`` direção do ferro."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paridirdobr    = ctypes.c_int (idirdobr)
        self.m_dwg.m_ipofer.IPOFER_IDIRDOBR (ctypes.byref (parferobjv),
                                             ctypes.byref (paridirdobr))

    @property
    def straightBarTextPosition (self) -> int:
        """Texto principal de ferros: ``0`` não colocar, ``1`` acima, ``2`` abaixo."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        ipostrepri     = 0
        paripostrepri  = ctypes.c_int (ipostrepri)
        self.m_dwg.m_ipofer.IPOFER_LER_IPOSTREPRI (ctypes.byref (parferobjv),
                                                   ctypes.byref (paripostrepri))
        ipostrepri     = paripostrepri.value
        return         ipostrepri

    @straightBarTextPosition.setter
    def straightBarTextPosition (self, ipostrepri: int) -> None:
        """Atribui ``0`` não colocar, ``1`` acima, ``2`` abaixo."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paripostrepri  = ctypes.c_int (ipostrepri)
        self.m_dwg.m_ipofer.IPOFER_IPOSTREPRI (ctypes.byref (parferobjv),
                                               ctypes.byref (paripostrepri))

    @property
    def straightBarContinuous (self) -> int:
        """Ferro corrido: ``0`` não, ``1`` sim."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icorrido     = 0
        paricorrido  = ctypes.c_int (icorrido)
        self.m_dwg.m_ipofer.IPOFER_LER_ICORRIDO (ctypes.byref (parferobjv),
                                                 ctypes.byref (paricorrido))
        icorrido     = paricorrido.value
        return         icorrido

    @straightBarContinuous.setter
    def straightBarContinuous (self, icorrido: int) -> None:
        """Atribui ``0`` não, ``1`` sim."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricorrido    = ctypes.c_int (icorrido)
        self.m_dwg.m_ipofer.IPOFER_ICORRIDO (ctypes.byref (parferobjv),
                                             ctypes.byref (paricorrido))

    def _LerLuvas (self) -> Tuple[int, int]:
        """Lê configuração de luvas (início/fim)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        iluvai         = 0
        pariluvai  = ctypes.c_int (iluvai)
        iluvaf         = 0
        pariluvaf  = ctypes.c_int (iluvaf)
        self.m_dwg.m_ipofer.IPOFER_LER_ILUVAS (ctypes.byref (parferobjv),
                            ctypes.byref (pariluvai), ctypes.byref (pariluvaf))
        iluvai         = pariluvai.value
        iluvaf         = pariluvaf.value
        return         iluvai, iluvaf

    def _DefLuvas (self, iluvai: int, iluvaf: int) -> None:
        """Define configuração de luvas (início/fim)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        pariluvai  = ctypes.c_int (iluvai)
        pariluvaf  = ctypes.c_int (iluvaf)
        self.m_dwg.m_ipofer.IPOFER_ILUVAS (ctypes.byref (parferobjv),
                            ctypes.byref (pariluvai), ctypes.byref (pariluvaf))

    @property
    def startCoupler (self) -> int:
        """Luva no início da barra: ``0`` não, ``1`` sim."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        iluvai, iluvaf = self._LerLuvas ()
        return         iluvai

    @startCoupler.setter
    def startCoupler (self, iluvai: int) -> None:
        """Atribui Luva no início da barra: ``0`` não, ``1`` sim."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        iluvai2, iluvaf = self._LerLuvas ()
        self._DefLuvas (iluvai, iluvaf)

    @property
    def endCoupler (self) -> int:
        """Luva no fim da barra: ``0`` não, ``1`` sim.

        ATENÇÃO: na biblioteca TQS este getter devolve ``iluvai``, o indicador
        da luva INICIAL, e não ``iluvaf``. Ler ``endCoupler`` espelha sempre
        ``startCoupler``; o estado da luva final não é legível. A atribuição
        grava a luva final corretamente.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        iluvai, iluvaf = self._LerLuvas ()
        return         iluvai

    @endCoupler.setter
    def endCoupler (self, iluvaf: int) -> None:
        """Atribui ``0`` não, ``1`` sim."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        iluvai, iluvaf2 = self._LerLuvas ()
        self._DefLuvas (iluvai, iluvaf)

    @property
    def mirrorMode (self) -> int:
        """Espelhamento: ``0`` restrito, ``1`` completo."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        idbresp        = 0
        paridbresp     = ctypes.c_int (idbresp)
        self.m_dwg.m_ipofer.IPOFER_LER_IDBRESP (ctypes.byref (parferobjv),
                                                ctypes.byref (paridbresp))
        idbresp        = paridbresp.value
        return         idbresp

    @mirrorMode.setter
    def mirrorMode (self, idbresp: int) -> None:
        """Atribui ``0`` restrito, ``1`` completo."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paridbresp     = ctypes.c_int (idbresp)
        self.m_dwg.m_ipofer.IPOFER_IDBRESP (ctypes.byref (parferobjv),
                                            ctypes.byref (paridbresp))


    @property
    def alternatingMode (self) -> int:
        """Alternância de ferros retos: :data:`ICPSAL` (não) ou :data:`ICPCAL` (sim)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfalt         = 0
        paricfalt      = ctypes.c_int (icfalt)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFALT (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfalt))
        icfalt        = paricfalt.value
        return         icfalt

    @alternatingMode.setter
    def alternatingMode (self, icfalt: int) -> None:
        """Atribui Alternância de ferros retos: :data:`ICPSAL` (não) ou :data:`ICPCAL` (sim)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfalt      = ctypes.c_int (icfalt)
        self.m_dwg.m_ipofer.IPOFER_ICFALT (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfalt))


    @property
    def alternatingFactor (self) -> float:
        """Fator de alternância de ferro reto."""
        parferobjv    = ctypes.c_void_p (self.m_ferobjv)
        cfaltf        = 0.
        parcfaltf     = ctypes.c_double (cfaltf)
        self.m_dwg.m_ipofer.IPOFER_LER_CFALTF (ctypes.byref (parferobjv),
                                               ctypes.byref (parcfaltf))
        cfaltf         = parcfaltf.value
        return         cfaltf

    @alternatingFactor.setter
    def alternatingFactor (self, cfaltf: float) -> None:
        """Atribui Fator de alternância de ferro reto."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcfaltf      = ctypes.c_double (cfaltf)
        self.m_dwg.m_ipofer.IPOFER_CFALTF (ctypes.byref (parferobjv),
                                           ctypes.byref (parcfaltf))

    def GenRebarPoint (self, xpt: float, ypt: float, zpt: float, iarc: int,
                        identbend: int, indfrt: int) -> None:
        """Insere um ponto da poligonal de ferro genérico.

        A poligonal será transformada na inserção em ``IPOFER_LINHAFER``.

        Args:
            xpt: Coordenada X.
            ypt: Coordenada Y.
            zpt: Coordenada Z.
            iarc: ``0`` trecho reto, ``1`` centro de arco.
            identbend: ``0`` não, ``1`` identificar a dobra.
            indfrt: Índice de trecho principal, ``-1`` se não aplicável.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parxpt         = ctypes.c_double (xpt)
        parypt         = ctypes.c_double (ypt)
        parzpt         = ctypes.c_double (zpt)
        pariarc        = ctypes.c_int    (iarc)
        paridentbend   = ctypes.c_int    (identbend)
        parindfrt      = ctypes.c_int    (indfrt)
        self.m_dwg.m_ipofer.IPOFER_PTFERGEN (ctypes.byref (parferobjv),
            ctypes.byref (parxpt), ctypes.byref (parypt), ctypes.byref (parzpt),
            ctypes.byref (pariarc), ctypes.byref (paridentbend), ctypes.byref (parindfrt))

    def GetGenRebarPoints (self) -> int:
        """Retorna o número de pontos da poligonal de ferro genérico.

        Returns:
            Número de pontos.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        numpts          = 0
        parnumpts       = ctypes.c_int (numpts)
        self.m_dwg.m_ipofer.IPOFER_LER_NUMPTFERGEN (ctypes.byref (parferobjv),
                         ctypes.byref (parnumpts))
        numpts          = parnumpts.value
        return          numpts


    def GetGenRebarPoint (self, indexpoint: int) -> Tuple[float, float, float, int, int, int]:
        """Retorna um ponto de ferro genérico (em relação ao ponto de inserção).

        Args:
            indexpoint: Índice do ponto em ``0..GetGenRebarPoints()-1``.

        Returns:
            Tupla ``(xpt, ypt, zpt, iarco, identdobr, indfrt)`` com
            coordenadas, flag de centro de arco, identificador de dobra
            e índice de trecho equivalente (``-1`` se ausente).
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parindexpoint   = ctypes.c_int (indexpoint)
        xpt             = 0.
        parxpt          = ctypes.c_double (xpt)
        ypt             = 0.
        parypt          = ctypes.c_double (ypt)
        zpt             = 0.
        parzpt          = ctypes.c_double (zpt)
        iarco           = 0
        pariarco        = ctypes.c_int (iarco)
        identdobr       = 0
        paridentdobr    = ctypes.c_int (identdobr)
        indfrt          = 0
        parindfrt       = ctypes.c_int (indfrt)
        self.m_dwg.m_ipofer.IPOFER_LER_PTFERGEN (ctypes.byref (parferobjv),
                        ctypes.byref (parindexpoint), ctypes.byref (parxpt),
                        ctypes.byref (parypt), ctypes.byref (parzpt),
                        ctypes.byref (pariarco), ctypes.byref (paridentdobr),
                        ctypes.byref (parindfrt))
        xpt             = parxpt.value
        ypt             = parypt.value
        zpt             = parzpt.value
        iarco           = pariarco.value
        identdobr       = paridentdobr.value
        indfrt          = parindfrt.value
        return          xpt, ypt, zpt, iarco, identdobr, indfrt

    def SetGenRebarPoint (self, indexpoint: int, xpt: float, ypt: float, zpt: float,
                          iarco: int, identdobr: int, indfrt: int) -> None:
        """Redefine um ponto de ferro genérico.

        Args:
            indexpoint: Índice do ponto em ``0..GetGenRebarPoints()-1``.
            xpt: Coordenada X.
            ypt: Coordenada Y.
            zpt: Coordenada Z.
            iarco: ``1`` se centro de arco.
            identdobr: ``1`` para identificar a dobra.
            indfrt: Índice de trecho equivalente ou ``-1``.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parindexpoint   = ctypes.c_int (indexpoint)
        parxpt          = ctypes.c_double (xpt)
        parypt          = ctypes.c_double (ypt)
        parzpt          = ctypes.c_double (zpt)
        pariarco        = ctypes.c_int (iarco)
        paridentdobr    = ctypes.c_int (identdobr)
        parindfrt       = ctypes.c_int (indfrt)
        self.m_dwg.m_ipofer.IPOFER_MOD_PTFERGEN (ctypes.byref (parferobjv),
                        ctypes.byref (parindexpoint), ctypes.byref (parxpt),
                        ctypes.byref (parypt), ctypes.byref (parzpt),
                        ctypes.byref (pariarco), ctypes.byref (paridentdobr),
                        ctypes.byref (parindfrt))

    @property
    def stirrupType (self) -> int:
        """Tipo de estribo de viga: :data:`ICPENR`, :data:`ICPEFC`, :data:`ICPEAB` ou :data:`ICPENC`."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icftpe         = 0
        paricftpe      = ctypes.c_int (icftpe)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFTPE (ctypes.byref (parferobjv),
                                               ctypes.byref (paricftpe))
        icftpe     = paricftpe.value
        return         icftpe

    @stirrupType.setter
    def stirrupType (self, icftpe: int) -> None:
        """Atribui :data:`ICPENR`, :data:`ICPEFC`, :data:`ICPEAB` ou :data:`ICPENC`."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricftpe      = ctypes.c_int (icftpe)
        self.m_dwg.m_ipofer.IPOFER_ICFTPE (ctypes.byref (parferobjv),
                                           ctypes.byref (paricftpe))


    @property
    def stirrupLegs (self) -> int:
        """Número de ramos de estribos: :data:`ICPNR2`, :data:`ICPNR4`, :data:`ICPNR6` ou :data:`ICPNR4B`."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icfnre         = 0
        paricfnre      = ctypes.c_int (icfnre)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFNRE (ctypes.byref (parferobjv),
                                               ctypes.byref (paricfnre))
        icfnre     = paricfnre.value
        return         icfnre

    @stirrupLegs.setter
    def stirrupLegs (self, icfnre: int) -> None:
        """Atribui :data:`ICPNR2`, :data:`ICPNR4`, :data:`ICPNR6` ou :data:`ICPNR4B`."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfnre      = ctypes.c_int (icfnre)
        self.m_dwg.m_ipofer.IPOFER_ICFNRE (ctypes.byref (parferobjv),
                                           ctypes.byref (paricfnre))

    def _LerDadEstrib (self) -> Tuple[float, float, float, float, float, float, float]:
        """Lê dados geométricos do estribo (largura, altura, colaborantes, dobra)."""
        parferobjv     = ctypes.c_void_p   (self.m_ferobjv)
        cfeb           = 0.
        cfeh           = 0.
        cfeb2          = 0.
        cfeh2          = 0.
        cfelce         = 0.
        cfelcd         = 0.
        cfedbr         = 0.
        parcfeb        = ctypes.c_double (cfeb)
        parcfeh        = ctypes.c_double (cfeh)
        parcfeb2       = ctypes.c_double (cfeb2)
        parcfeh2       = ctypes.c_double (cfeh2)
        parcfelce      = ctypes.c_double (cfelce)
        parcfelcd      = ctypes.c_double (cfelcd)
        parcfedbr      = ctypes.c_double (cfedbr)
        self.m_dwg.m_ipofer.IPOFER_LER_DADESTRIB (ctypes.byref (parferobjv),
            ctypes.byref (parcfeb), ctypes.byref (parcfeh), ctypes.byref (parcfeb2),
            ctypes.byref (parcfeh2), ctypes.byref (parcfelce), ctypes.byref (parcfelcd),
            ctypes.byref (parcfedbr))
        cfeb           = parcfeb.value
        cfeh           = parcfeh.value
        cfeb2          = parcfeb2.value
        cfeh2          = parcfeh2.value
        cfelce         = parcfelce.value
        cfelcd         = parcfelcd.value
        cfedbr         = parcfedbr.value
        return         cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr

    def _DefDadEstrib (self, cfeb: float, cfeh: float, cfeb2: float, cfeh2: float,
                        cfelce: float, cfelcd: float, cfedbr: float) -> None:
        """Define dados geométricos do estribo."""
        parferobjv     = ctypes.c_void_p   (self.m_ferobjv)
        parcfeb        = ctypes.c_double (cfeb)
        parcfeh        = ctypes.c_double (cfeh)
        parcfeb2       = ctypes.c_double (cfeb2)
        parcfeh2       = ctypes.c_double (cfeh2)
        parcfelce      = ctypes.c_double (cfelce)
        parcfelcd      = ctypes.c_double (cfelcd)
        parcfedbr      = ctypes.c_double (cfedbr)
        self.m_dwg.m_ipofer.IPOFER_DADESTRIB (ctypes.byref (parferobjv),
            ctypes.byref (parcfeb), ctypes.byref (parcfeh), ctypes.byref (parcfeb2),
            ctypes.byref (parcfeh2), ctypes.byref (parcfelce), ctypes.byref (parcfelcd),
            ctypes.byref (parcfedbr))

    @property
    def stirrupSectionWidth (self) -> float:
        """Largura da seção transversal que contém o estribo, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        return         cfeb

    @stirrupSectionWidth.setter
    def stirrupSectionWidth (self, cfeb: float) -> None:
        """Atribui Largura da seção transversal que contém o estribo, cm."""
        cfebx, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        self._DefDadEstrib (cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr)

    @property
    def stirrupSectionHeight (self) -> float:
        """Altura da seção transversal que contém o estribo, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        return         cfeh

    @stirrupSectionHeight.setter
    def stirrupSectionHeight (self, cfeh: float) -> None:
        """Atribui Altura da seção transversal que contém o estribo, cm."""
        cfeb, cfehx, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        self._DefDadEstrib (cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr)

    @property
    def stirrupSectionWidth2 (self) -> float:
        """Largura final da seção transversal variável, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        return         cfeb2

    @stirrupSectionWidth2.setter
    def stirrupSectionWidth2 (self, cfeb2: float) -> None:
        """Atribui Largura final da seção transversal variável, cm."""
        cfeb, cfeh, cfeb2x, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        self._DefDadEstrib (cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr)

    @property
    def stirrupSectionHeight2 (self) -> float:
        """Altura final da seção transversal variável, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        return         cfeh2

    @stirrupSectionHeight2.setter
    def stirrupSectionHeight2 (self, cfeh2: float) -> None:
        """Atribui Altura final da seção transversal variável, cm."""
        cfeb, cfeh, cfeb2, cfeh2x, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        self._DefDadEstrib (cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr)

    @property
    def stirrupEffectiveLeftWidth (self) -> float:
        """Largura esquerda colaborante da seção transversal, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        return         cfelce

    @stirrupEffectiveLeftWidth.setter
    def stirrupEffectiveLeftWidth (self, cfelce: float) -> None:
        """Atribui Largura esquerda colaborante da seção transversal, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelcex, cfelcd, cfedbr = self._LerDadEstrib ()
        self._DefDadEstrib (cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr)

    @property
    def stirrupEffectiveRightWidth (self) -> float:
        """Largura direita colaborante da seção transversal, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        return         cfelcd

    @stirrupEffectiveRightWidth.setter
    def stirrupEffectiveRightWidth (self, cfelcd: float) -> None:
        """Atribui Largura direita colaborante da seção transversal, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcdx, cfedbr = self._LerDadEstrib ()
        self._DefDadEstrib (cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr)

    @property
    def stirrupSlabBendLength (self) -> float:
        """Comprimento de dobra de estribo em laje, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr = self._LerDadEstrib ()
        return         cfedbr

    @stirrupSlabBendLength.setter
    def stirrupSlabBendLength (self, cfedbr: float) -> None:
        """Atribui Comprimento de dobra de estribo em laje, cm."""
        cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbrx = self._LerDadEstrib ()
        self._DefDadEstrib (cfeb, cfeh, cfeb2, cfeh2, cfelce, cfelcd, cfedbr)


    @property
    def stirrupHookLength (self) -> int:
        """Comprimento da pata de estribos em número de bitolas."""
        parferobjv    = ctypes.c_void_p (self.m_ferobjv)
        nfiane        = 0
        parnfiane     = ctypes.c_int (nfiane)
        self.m_dwg.m_ipofer.IPOFER_LER_NFIANE (ctypes.byref (parferobjv),
                                               ctypes.byref (parnfiane))
        nfiane         = parnfiane.value
        return         nfiane

    @stirrupHookLength.setter
    def stirrupHookLength (self, nfiane: int) -> None:
        """Atribui Comprimento da pata de estribos em número de bitolas."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parnfiane      = ctypes.c_int (nfiane)
        self.m_dwg.m_ipofer.IPOFER_NFIANE (ctypes.byref (parferobjv),
                                           ctypes.byref (parnfiane))

    @property
    def stirrupHookType (self) -> int:
        """Tipo de pata de estribo: :data:`ICPTPPATA45` ou :data:`ICPTPPATA90`."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icftppata      = 0
        paricftppata   = ctypes.c_int (icftppata)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFTPPATA (ctypes.byref (parferobjv),
                                                  ctypes.byref (paricftppata))
        icftppata      = paricftppata.value
        return         icftppata

    @stirrupHookType.setter
    def stirrupHookType (self, icftppata: int) -> None:
        """Atribui :data:`ICPTPPATA45` ou :data:`ICPTPPATA90`."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        paricftppata    = ctypes.c_int (icftppata)
        self.m_dwg.m_ipofer.IPOFER_ICFTPPATA (ctypes.byref (parferobjv),
                                              ctypes.byref (paricftppata))

    @property
    def stirrupInternalLegDiameter (self) -> float:
        """Bitola em mm diferente para estribo interno de 4 ou 6 ramos."""
        parferobjv    = ctypes.c_void_p (self.m_ferobjv)
        cfaltf        = 0.
        bitstrin     = ctypes.c_double (cfaltf)
        self.m_dwg.m_ipofer.IPOFER_LER_BITSTRIN (ctypes.byref (parferobjv),
                                               ctypes.byref (bitstrin))
        cfaltf         = bitstrin.value
        return         cfaltf

    @stirrupInternalLegDiameter.setter
    def stirrupInternalLegDiameter (self, cfaltf: float) -> None:
        """Atribui Bitola em mm diferente para estribo interno de 4 ou 6 ramos."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        bitstrin      = ctypes.c_double (cfaltf)
        self.m_dwg.m_ipofer.IPOFER_BITSTRIN (ctypes.byref (parferobjv),
                                           ctypes.byref (bitstrin))

    @property
    def genericStirrupType (self) -> int:
        """Tipo de estribo genérico: :data:`ICPEGENFEC`, :data:`ICPEGENABR`, :data:`ICPEGENGRA` ou :data:`ICPEGENCIR`."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        icftpeg        = 0
        paricftpeg     = ctypes.c_int (icftpeg)
        self.m_dwg.m_ipofer.IPOFER_LER_ICFTPEG (ctypes.byref (parferobjv),
                                                ctypes.byref (paricftpeg))
        icftpeg        = paricftpeg.value
        return         icftpeg

    @genericStirrupType.setter
    def genericStirrupType (self, icftpeg: int) -> None:
        """Atribui Tipo de estribo genérico: :data:`ICPEGENFEC`, :data:`ICPEGENABR`, :data:`ICPEGENGRA` ou :data:`ICPEGENCIR`."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        paricftpeg      = ctypes.c_int (icftpeg)
        self.m_dwg.m_ipofer.IPOFER_ICFTPEG (ctypes.byref (parferobjv),
                                            ctypes.byref (paricftpeg))


    @property
    def genericStirrupEntryMode (self) -> int:
        """Modo de definição de estribo genérico: :data:`ICPEGPONTOSLONG`, :data:`ICPEGPONTOSSECA` ou :data:`ICPEGPONTOSEXTR`."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        iestrgenstat    = 0
        pariestrgenstat = ctypes.c_int (iestrgenstat)
        self.m_dwg.m_ipofer.IPOFER_LER_IESTRGENSTAT (ctypes.byref (parferobjv),
                                                     ctypes.byref (pariestrgenstat))
        iestrgenstat        = pariestrgenstat.value
        return         iestrgenstat

    @genericStirrupEntryMode.setter
    def genericStirrupEntryMode (self, iestrgenstat: int) -> None:
        """Atribui Modo de definição de estribo genérico: :data:`ICPEGPONTOSLONG`, :data:`ICPEGPONTOSSECA` ou :data:`ICPEGPONTOSEXTR`."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        pariestrgenstat = ctypes.c_int (iestrgenstat)
        self.m_dwg.m_ipofer.IPOFER_IESTRGENSTAT (ctypes.byref (parferobjv),
                                                 ctypes.byref (pariestrgenstat))

    @property
    def genericStirrupLongDiameter (self) -> float:
        """Bitola longitudinal em mm de referência para a definição dos pontos."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        bitlnest        = 0.
        parbitlnest     = ctypes.c_double (bitlnest)
        self.m_dwg.m_ipofer.IPOFER_LER_BITLESTRGEN (ctypes.byref (parferobjv),
                                                    ctypes.byref (parbitlnest))
        bitlnest        = parbitlnest.value
        return          bitlnest

    @genericStirrupLongDiameter.setter
    def genericStirrupLongDiameter (self, bitlnest: float) -> None:
        """Atribui Bitola longitudinal em mm de referência para a definição dos pontos."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parbitlnest     = ctypes.c_double (bitlnest)
        self.m_dwg.m_ipofer.IPOFER_BITLESTRGEN (ctypes.byref (parferobjv),
                                                ctypes.byref (parbitlnest))

    def GenericStirrupPoint (self, xlong: float, ylong: float) -> None:
        """Insere um ponto de estribo genérico.

        Os pontos são fornecidos no centro da armadura longitudinal. A
        bitola é definida por :attr:`genericStirrupLongDiameter`. No
        estribo fechado, não fornecer o último ponto.

        Args:
            xlong: Coordenada X.
            ylong: Coordenada Y.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parxlong       = ctypes.c_double (xlong)
        parylong       = ctypes.c_double (ylong)
        self.m_dwg.m_ipofer.IPOFER_PTESTRGEN (ctypes.byref (parferobjv),
                         ctypes.byref (parxlong), ctypes.byref (parylong))

    @property
    def circularStirrupRadius (self) -> float:
        """Raio de estribo circular em cm."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        raioestr        = 0.
        parraioestr     = ctypes.c_double (raioestr)
        self.m_dwg.m_ipofer.IPOFER_LER_RAIOESTR (ctypes.byref (parferobjv),
                                                 ctypes.byref (parraioestr))
        raioestr        = parraioestr.value
        return          raioestr

    @circularStirrupRadius.setter
    def circularStirrupRadius (self, raioestr: float) -> None:
        """Atribui Raio de estribo circular em cm."""
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parraioestr     = ctypes.c_double (raioestr)
        self.m_dwg.m_ipofer.IPOFER_RAIOESTR (ctypes.byref (parferobjv),
                                             ctypes.byref (parraioestr))

    def StirrupAdditionalCriteria (self, compradgra: float, igrasck83: int, igrak77: int) -> None:
        """Configura critérios adicionais que modificam o grampo de pilar.

        Args:
            compradgra: Valor em cm a somar ao comprimento do grampo.
            igrasck83: Desenho de grampo: ``0`` em S, ``1`` em C.
            igrak77: ``1`` para somar duas bitolas ao comprimento do grampo.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parcompradgra  = ctypes.c_double (compradgra)
        parigrasck83   = ctypes.c_int (igrasck83)
        parigrak77     = ctypes.c_int (igrak77)
        self.m_dwg.m_ipofer.IPOFER_COMPRADGRA (ctypes.byref (parferobjv),
                       ctypes.byref (parcompradgra), ctypes.byref (parigrasck83),
                       ctypes.byref (parigrak77))


    def _LerDadGrampo (self) -> Tuple[int, float, float]:
        """Lê dados do grampo (direção, comprimentos longitudinal/transversal)."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        igrdir         = 0
        grclong        = 0.
        grctran        = 0.
        parigrdir      = ctypes.c_int (igrdir)
        pargrclong     = ctypes.c_double (grclong)
        pargrctran     = ctypes.c_double (grctran)
        self.m_dwg.m_ipofer.IPOFER_LER_DADGRAMPO (ctypes.byref (parferobjv),
                         ctypes.byref (parigrdir), ctypes.byref (pargrclong),
                         ctypes.byref (pargrctran))
        igrdir         = parigrdir.value
        grclong        = pargrclong.value
        grctran        = pargrctran.value
        return         igrdir, grclong, grctran

    def _DefDadGrampo (self, igrdir: int, grclong: float, grctran: float) -> None:
        """Define dados do grampo."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parigrdir      = ctypes.c_int (igrdir)
        pargrclong     = ctypes.c_double (grclong)
        pargrctran     = ctypes.c_double (grctran)
        self.m_dwg.m_ipofer.IPOFER_DADGRAMPO (ctypes.byref (parferobjv),
                         ctypes.byref (parigrdir), ctypes.byref (pargrclong),
                         ctypes.byref (pargrctran))

    @property
    def crosstiesDirection (self) -> int:
        """Direção do grampo de vigas: ``1`` esquerda, ``-1`` direita."""
        igrdir, grclong, grctran = self._LerDadGrampo ()
        return          igrdir

    @crosstiesDirection.setter
    def crosstiesDirection (self, igrdir: int) -> None:
        """Atribui Direção do grampo de vigas: ``1`` esquerda, ``-1`` direita."""
        igrdir2, grclong, grctran = self._LerDadGrampo ()
        self._DefDadGrampo (igrdir, grclong, grctran)

    @property
    def crosstiesLongLength (self) -> float:
        """Comprimento longitudinal do grampo de vigas em cm."""
        igrdir, grclong, grctran = self._LerDadGrampo ()
        return          grclong

    @crosstiesLongLength.setter
    def crosstiesLongLength (self, grclong: float) -> None:
        """Atribui Comprimento longitudinal do grampo de vigas em cm."""
        igrdir, grclong2, grctran = self._LerDadGrampo ()
        self._DefDadGrampo (igrdir, grclong, grctran)

    @property
    def crosstiesTransvLength (self) -> float:
        """Comprimento transversal do grampo de vigas em cm."""
        igrdir, grclong, grctran = self._LerDadGrampo ()
        return          grctran

    @crosstiesTransvLength.setter
    def crosstiesTransvLength (self, grctran: float) -> None:
        """Atribui Comprimento transversal do grampo de vigas em cm."""
        igrdir, grclong, grctran2 = self._LerDadGrampo ()
        self._DefDadGrampo (igrdir, grclong, grctran)

    def RebarTextDisplaySelection (self, iflnfr: int, iflpos: int, iflbit: int,
                                    iflesp: int, iflcmp: int, ialign: int, ibreak: int) -> None:
        """Seleciona os textos de identificação a serem mostrados.

        Args:
            iflnfr: ``1`` para mostrar número de ferros.
            iflpos: ``1`` para mostrar número da posição.
            iflbit: ``1`` para mostrar bitola.
            iflesp: ``1`` para mostrar espaçamento.
            iflcmp: ``1`` para mostrar comprimento.
            ialign: Alinhamento ``ICPCENTR_xxxxxxx``.
            ibreak: Salto de linha ``ICPQUEBR_xxxxxxxxx``.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        pariflnfr      = ctypes.c_int (iflnfr)
        pariflpos      = ctypes.c_int (iflpos)
        pariflbit      = ctypes.c_int (iflbit)
        pariflesp      = ctypes.c_int (iflesp)
        pariflcmp      = ctypes.c_int (iflcmp)
        paricentr      = ctypes.c_int (ialign)
        pariquebr      = ctypes.c_int (ibreak)
        self.m_dwg.m_ipofer.IPOFER_ARM_LAJMNTX (ctypes.byref (parferobjv),
            ctypes.byref (pariflnfr), ctypes.byref (pariflpos), ctypes.byref (pariflbit),
            ctypes.byref (pariflesp), ctypes.byref (pariflcmp), ctypes.byref (paricentr),
            ctypes.byref (pariquebr))

    def RebarTextDisplayPosition (self, xtex: float, ytex: float, htex: float, angle: float,
                                   imod: int, ialign: int, ibreak: int) -> None:
        """Fornece a posição e formatação do texto de identificação.

        Args:
            xtex: Coordenada X do texto.
            ytex: Coordenada Y do texto.
            htex: Altura do texto em cm de plotagem.
            angle: Ângulo do texto em graus.
            imod: Modo (``0`` normal, ``1`` bit/espac p/tabela var,
                ``2`` posição, ``3`` posição centrada com círculo).
            ialign: Alinhamento ``ICPCENTR_xxxxxxx``.
            ibreak: Salto de linha ``ICPQUEBR_xxxxxxxxx``.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parxtex        = ctypes.c_double (xtex)
        parytex        = ctypes.c_double (ytex)
        parhtex        = ctypes.c_double (htex)
        parangle       = ctypes.c_double (angle)
        parimod        = ctypes.c_int (imod)
        paricentr      = ctypes.c_int (ialign)
        pariquebr      = ctypes.c_int (ibreak)
        self.m_dwg.m_ipofer.IPOFER_ARM_TEXTOFER (ctypes.byref (parferobjv),
            ctypes.byref (parxtex), ctypes.byref (parytex), ctypes.byref (parhtex),
            ctypes.byref (parangle), ctypes.byref (parimod), ctypes.byref (paricentr),
            ctypes.byref (pariquebr))


    def __LerChamAuto (self) -> Tuple[int, float]:
        """Lê parâmetros de linha de chamada automática."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parilinchamauto= ctypes.c_int (0)
        pardistchamauto= ctypes.c_double (0.)
        self.m_dwg.m_ipofer.IPOFER_LER_CHAMAUTO (ctypes.byref (parferobjv),     \
                ctypes.byref (parilinchamauto), ctypes.byref (pardistchamauto))
        ilinchamauto   = parilinchamauto.value
        distchamauto   = pardistchamauto.value
        return          ilinchamauto, distchamauto

    def __DefChamAuto (self, ilinchamauto: int, distchamauto: float) -> None:
        """Define parâmetros de linha de chamada automática."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parilinchamauto= ctypes.c_int (ilinchamauto)
        pardistchamauto= ctypes.c_double (distchamauto)
        self.m_dwg.m_ipofer.IPOFER_CHAMAUTO (ctypes.byref (parferobjv),     \
                        parilinchamauto, pardistchamauto)

    @property
    def leaderLine (self) -> int:
        """Geração automática de linha de chamada para textos afastados.

        ``0`` não coloca linha de chamada; ``1`` será gerada acima da
        distância definida em :attr:`leaderLineDistance`.
        """
        ilinchamauto, distchamauto = self.__LerChamAuto ()
        return          ilinchamauto

    @leaderLine.setter
    def leaderLine (self, leaderline: int) -> None:
        """Atribui Geração automática de linha de chamada para textos afastados."""
        ilinchamauto, distchamauto = self.__LerChamAuto ()
        self.__DefChamAuto (leaderline, distchamauto)

    @property
    def leaderLineDistance (self) -> float:
        """Distância mínima em cm de plotagem para gerar linha de chamada."""
        ilinchamauto, distchamauto = self.__LerChamAuto ()
        return          distchamauto

    @leaderLineDistance.setter
    def leaderLineDistance (self, leaderlinedistance: float) -> None:
        """Atribui Distância mínima em cm de plotagem para gerar linha de chamada."""
        ilinchamauto, distchamauto = self.__LerChamAuto ()
        self.__DefChamAuto (ilinchamauto, leaderlinedistance)

    def VariableRebarContoursInit (self) -> None:
        """Inicializa os contornos para a definição de ferros variáveis."""
        self.m_dwg.m_ipofer.IPOFER_ARM_INITRNSFP ()

    def VariableRebarOneContourInit (self) -> None:
        """Inicializa o contorno atual para a definição de ferros variáveis."""
        self.m_dwg.m_ipofer.IPOFER_ARM_TRNSFP_INI ()

    def VariableRebarOneContourPoint (self, x: float, y: float) -> None:
        """Insere um ponto no contorno atual para ferros variáveis.

        Args:
            x: Coordenada X.
            y: Coordenada Y.
        """
        parx           = ctypes.c_double (x)
        pary           = ctypes.c_double (y)
        self.m_dwg.m_ipofer.IPOFER_ARM_TRNSFP_ENTRARCOORD (ctypes.byref (parx),
                                                           ctypes.byref (pary))

    def VariableRebarOneContourEnd (self) -> None:
        """Finaliza a entrada de pontos no contorno atual para ferros variáveis."""
        self.m_dwg.m_ipofer.IPOFER_ARM_TRNSFP_FIM ()

    def VariableRebarMainSegIndex (self, idobravar: int) -> None:
        """Define o índice da dobra variável (numerada a partir de zero).

        Args:
            idobravar: Índice da dobra variável.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paridobravar   = ctypes.c_int (idobravar)
        self.m_dwg.m_ipofer.IPOFER_FERVAR_IDOBRAVAR (ctypes.byref (parferobjv),
                         ctypes.byref (paridobravar))

    def VariableRebarGenerate (self, icfes1: int, angdist: float,
                                scale: float) -> Tuple[float, float, float, float, int]:
        """Geração automática de ferros variáveis.

        Args:
            icfes1: Número de ferros distribuídos: :data:`ICPE1P`,
                :data:`ICPE1M` ou :data:`ICPESP`.
            angdist: Ângulo em graus da faixa de distribuição
                ortogonal ao ferro.
            scale: Escala de inserção.

        Returns:
            Tupla ``(xins, yins, meanLength, angle, istat)``:

            * ``xins``, ``yins``: posição média de inserção do ferro.
            * ``meanLength``: comprimento do ferro médio em cm.
            * ``angle``: ângulo do ferro em graus.
            * ``istat``: ``0`` Ok, ``1`` contorno inválido,
              ``2`` o número gerado não bate com o número de
              espaçamentos, ``3`` espaçamento zero.
        """
        parferobjv     = ctypes.c_void_p   (self.m_ferobjv)
        paricfes1      = ctypes.c_int    (icfes1)
        parangdist     = ctypes.c_double (angdist)
        parscale       = ctypes.c_double (scale)
        xins           = 0.
        yins           = 0.
        meanLength     = 0.
        angle          = 0.
        istat          = 0
        parxins        = ctypes.c_double (xins)
        paryins        = ctypes.c_double (yins)
        parmeanLength  = ctypes.c_double (meanLength)
        parangle       = ctypes.c_double (angle)
        paristat       = ctypes.c_int    (istat)
        self.m_dwg.m_ipofer.IPOFER_ARM_FERVAR (ctypes.byref (parferobjv),
            ctypes.byref (paricfes1), ctypes.byref (parangdist),
            ctypes.byref (parscale), ctypes.byref (parxins), ctypes.byref (paryins),
            ctypes.byref (parmeanLength), ctypes.byref (parangle), ctypes.byref (paristat))
        xins           = parxins.value
        yins           = paryins.value
        meanLength     = parmeanLength.value
        angle          = parangle.value
        istat          = paristat.value
        return         xins, yins, meanLength, angle, istat


    def VariableRebarQuantity (self) -> int:
        """Retorna o número de ferros variáveis gerados.

        Returns:
            Número de ferros variáveis.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        numfer         = 0
        parnumfer      = ctypes.c_int (numfer)
        self.m_dwg.m_ipofer.IPOFER_ARM_FERVARNUM (ctypes.byref (parferobjv),
                        ctypes.byref (parnumfer))
        numfer         = parnumfer.value
        return         numfer

    def VariableRebarScheduleInsert (self, xins: float, yins: float) -> None:
        """Insere uma tabela de ferros variável no desenho.

        Args:
            xins: X do ponto de inserção.
            yins: Y do ponto de inserção.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parxins        = ctypes.c_double (xins)
        paryins        = ctypes.c_double (yins)
        self.m_dwg.m_ipofer.IPOFER_ARM_TABVAR (ctypes.byref (parferobjv),
                        ctypes.byref (parxins), ctypes.byref (paryins))

    def VariableStirrupGenerate (self) -> None:
        """Gera a lista de comprimentos variáveis de estribos.

        Funciona apenas para estribos retangulares, com variação na
        largura ou na altura, entre ``cfeb`` e ``cfeb2`` ou ``cfeh`` e
        ``cfeh2``. Se ambos zerados, elimina a variação. A quantidade
        é calculada pela faixa ou por número fixo. Sem faixa,
        ``icfes1 == ICPE1P``.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        self.m_dwg.m_ipofer.IPOFER_FERVAR_GERARESTR (
                       ctypes.byref (parpedmv), ctypes.byref (parferobjv))


    def RebarDistrQuant (self, icfes1: int, distrLength: float, spacing: float) -> Tuple[int, int]:
        """Calcula o número de ferros dado o comprimento da faixa e o espaçamento.

        Args:
            icfes1: Número de ferros em função dos espaçamentos:
                :data:`ICPE1P`, :data:`ICPE1M` ou :data:`ICPESP`.
            distrLength: Comprimento da faixa de distribuição em cm.
            spacing: Espaçamento da faixa em cm.

        Returns:
            Tupla ``(iquant, istat)`` com o número de ferros calculado
            e ``istat != 0`` se ``spacing == 0.``.
        """
        paricfes1      = ctypes.c_int (icfes1)
        pardistrLength = ctypes.c_double (distrLength)
        parspacing     = ctypes.c_double (spacing)
        iquant         = 0
        pariquant      = ctypes.c_int (iquant)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_dwg.m_ipofer.IPOFER_ARM_CALNFR (ctypes.byref (paricfes1),
            ctypes.byref (pardistrLength), ctypes.byref (parspacing),
            ctypes.byref (pariquant), ctypes.byref (paristat))
        iquant          = pariquant.value
        istat           = paristat.value
        return          iquant, istat


    def RebarDistrAdd (self, icfes1: int, angdist: float, xpt1: float, ypt1: float,
                        xpt2: float, ypt2: float, xcot: float, ycot: float,
                        ifdcotc: int, iflnfr: int, iflpos: int, iflbit: int, iflesp: int,
                        ialign: int, ibreak: int, ordem: str, k32vigas: int,
                        k41vigas: int, ilinexten: int, ilinchama: int, itpponta: int,
                        spacing: float, scale: float) -> None:
        """Adiciona uma faixa de distribuição ao ferro.

        Há dois tipos de faixas de distribuição:

        a) Embutida em um ferro. Um ferro pode ter várias faixas. Não
           é usada em pilares; cada faixa pertence a um ferro.
        b) Independente do ferro. Uma faixa pode ter vários ferros, é
           usada em pilares onde estribos e grampos partilham uma
           faixa única. Definida primeiro como ferro do tipo
           :data:`ICPFAIMUL`, depois associada via
           :meth:`RebarDistrLink`.

        Quando um ferro tem uma ou mais faixas, o número de ferros
        passa a ser calculado pela soma dos ferros das faixas.

        Args:
            icfes1: Número de ferros em função dos espaçamentos:
                :data:`ICPE1P`, :data:`ICPE1M` ou :data:`ICPESP`.
            angdist: Ângulo em graus da faixa ortogonal ao ferro.
            xpt1: X do primeiro ponto.
            ypt1: Y do primeiro ponto.
            xpt2: X do segundo ponto.
            ypt2: Y do segundo ponto.
            xcot: X do ponto da linha de cotagem.
            ycot: Y do ponto da linha de cotagem.
            ifdcotc: ``1`` para cotar comprimento da faixa.
            iflnfr: ``1`` para descrever número de ferros.
            iflpos: ``1`` para descrever número da posição.
            iflbit: ``1`` para descrever bitola.
            iflesp: ``1`` para descrever espaçamento.
            ialign: Alinhamento ``ICPCENTR_xxxxxxx``.
            ibreak: Salto de linha ``ICPQUEBR_xxxxxxxxx``.
            ordem: Ordem dos textos (``""`` padrão); letras: ``N``
                número de ferros, ``n`` só o número, ``M`` só o
                multiplicador, ``P`` posição, ``B`` bitola, ``E``
                espaçamento, ``C`` comprimento, ``F`` comprimento de
                faixa.
            k32vigas: Critério K32 CAD/Vigas para ``ordem == ""``.
            k41vigas: Critério K41 CAD/Vigas para ``ordem == ""``.
                ``0`` não cota faixa, ``1`` cota, ``2`` cota e altera Pn.
            ilinexten: ``1`` para linha de extensão automática.
            ilinchama: ``1`` para linha de chamada.
            itpponta: ``0`` flecha, ``1`` círculo, ``2`` traço.
            spacing: Espaçamento em cm se diferente do ferro.
            scale: Escala de inserção (multiplica todas as dimensões).
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paricfes1      = ctypes.c_int    (icfes1)
        parangdist     = ctypes.c_double (angdist)
        parxpt1        = ctypes.c_double (xpt1)
        parypt1        = ctypes.c_double (ypt1)
        parxpt2        = ctypes.c_double (xpt2)
        parypt2        = ctypes.c_double (ypt2)
        parxcot        = ctypes.c_double (xcot)
        parycot        = ctypes.c_double (ycot)
        parifdcotc     = ctypes.c_int    (ifdcotc)
        pariflnfr      = ctypes.c_int    (iflnfr)
        pariflpos      = ctypes.c_int    (iflpos)
        pariflbit      = ctypes.c_int    (iflbit)
        pariflesp      = ctypes.c_int    (iflesp)
        parialign      = ctypes.c_int    (ialign)
        paribreak      = ctypes.c_int    (ibreak)
        parordem       = ctypes.c_char_p (ordem.encode(TQS.TQSUtil.CHARSET))
        parargfan      = ctypes.c_int    (0)
        park32vigas    = ctypes.c_int    (k32vigas)
        park41vigas    = ctypes.c_int    (k41vigas)
        parilinexten   = ctypes.c_int    (ilinexten)
        parilinchama   = ctypes.c_int    (ilinchama)
        paritpponta    = ctypes.c_int    (itpponta)
        parspacing     = ctypes.c_double (spacing)
        parscale       = ctypes.c_double (scale)
        self.m_dwg.m_ipofer.IPOFER_FAIXADIST (ctypes.byref (parferobjv), ctypes.byref (paricfes1),
            ctypes.byref (parangdist), ctypes.byref (parxpt1), ctypes.byref (parypt1),
            ctypes.byref (parxpt2), ctypes.byref (parypt2), ctypes.byref (parxcot),
            ctypes.byref (parycot), ctypes.byref (parifdcotc), ctypes.byref (pariflnfr),
            ctypes.byref (pariflpos), ctypes.byref (pariflbit), ctypes.byref (pariflesp),
            ctypes.byref (parialign), ctypes.byref (paribreak), parordem, parargfan,
            ctypes.byref (park32vigas), ctypes.byref (park41vigas), ctypes.byref (parilinexten),
            ctypes.byref (parilinchama), ctypes.byref (paritpponta), ctypes.byref (parspacing),
            ctypes.byref (parscale))

    def RebarDistrAutoSum (self, icalcnfauto: int, irecalsemod: int, icfnfr: int) -> None:
        """Define parâmetros extras na última faixa adicionada para cálculo de quantidades.

        Args:
            icalcnfauto: ``1`` se soma o número de ferros desta faixa
                à quantidade total.
            irecalsemod: ``1`` se recalcula a quantidade quando a
                faixa for modificada.
            icfnfr: Número de ferros se ``irecalsemod == 0``.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        paricalcnfauto  = ctypes.c_int (icalcnfauto)
        parirecalsemod  = ctypes.c_int (irecalsemod)
        paricfnfr       = ctypes.c_int (icfnfr)
        self.m_dwg.m_ipofer.IPOFER_FAIXDISTCALCNFAUTO (ctypes.byref (parferobjv), \
                        ctypes.byref (paricalcnfauto), ctypes.byref (parirecalsemod), \
                        ctypes.byref (paricfnfr))

    def RebarDistrLink (self, rebar: "SmartRebar") -> None:
        """Associa um ferro à faixa múltipla atual.

        Args:
            rebar: Ferro :class:`SmartRebar` a associar.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        handleRebar    = rebar.handle_rebar;
        parhandleRebar = ctypes.c_void_p (handleRebar)
        self.m_dwg.m_ipofer.IPOFER_ASSOCFAIXAMULT  (ctypes.byref (parferobjv),
            ctypes.byref (parhandleRebar))


    def GetRebarDistrNum (self) -> int:
        """Retorna o número de faixas de distribuição.

        Returns:
            Número de faixas de distribuição.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        numfaixas       = 0
        parnumfaixas    = ctypes.c_int (numfaixas)
        self.m_dwg.m_ipofer.IPOFER_LER_NUMFAIXAS (ctypes.byref (parferobjv),
                            ctypes.byref (parnumfaixas))
        numfaixas       = parnumfaixas.value
        return          (numfaixas)


    def GetRebarDistrInfo (self, ifaixa: int) -> Tuple[int, float, float, float, float, float,
                                                         float, float, int, int, int, int, int,
                                                         int, int, str, int, int, int, int, int,
                                                         float, float]:
        """Retorna os dados de uma faixa de distribuição.

        Args:
            ifaixa: Índice em ``0..GetRebarDistrNum()-1``.

        Returns:
            Tupla com ``(icfes1, angfai, xpt1, ypt1, xpt2, ypt2, xcot,
            ycot, ifdcotc, iflnfr, iflpos, iflbit, iflesp, icentr,
            iquebr, ordem, k32vigas, k41vigas, ilinexten, ilinchama,
            itpponta, espac, escxy)`` — ver :meth:`RebarDistrAdd` para
            o significado dos campos.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parifaixa       = ctypes.c_int (ifaixa)
        icfes1          = 0
        paricfes1       = ctypes.c_int (icfes1)
        angfai          = 0.
        parangfai       = ctypes.c_double (angfai)
        xpt1            = 0.
        parxpt1         = ctypes.c_double (xpt1)
        ypt1            = 0.
        parypt1         = ctypes.c_double (ypt1)
        xpt2            = 0.
        parxpt2         = ctypes.c_double (xpt2)
        ypt2            = 0.
        parypt2         = ctypes.c_double (ypt2)
        xcot            = 0.
        parxcot         = ctypes.c_double (xcot)
        ycot            = 0.
        parycot         = ctypes.c_double (ycot)
        ifdcotc         = 0
        parifdcotc      = ctypes.c_int (ifdcotc)
        iflnfr          = 0
        pariflnfr       = ctypes.c_int (iflnfr)
        iflpos          = 0
        pariflpos       = ctypes.c_int (iflpos)
        iflbit          = 0
        pariflbit       = ctypes.c_int (iflbit)
        iflesp          = 0
        pariflesp       = ctypes.c_int (iflesp)
        icentr          = 0
        paricentr       = ctypes.c_int (icentr)
        iquebr          = 0
        pariquebr       = ctypes.c_int (iquebr)
        parordem        = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        argfan         = ctypes.c_int (0)
        k32vigas        = 0
        park32vigas     = ctypes.c_int (k32vigas)
        k41vigas        = 0
        park41vigas     = ctypes.c_int (k41vigas)
        ilinexten       = 0
        parilinexten    = ctypes.c_int (ilinexten)
        ilinchama       = 0
        parilinchama    = ctypes.c_int (ilinchama)
        itpponta        = 0
        paritpponta     = ctypes.c_int (itpponta)
        espac           = 0.
        parespac        = ctypes.c_double (espac)
        escxy           = 0.
        parescxy        = ctypes.c_double (escxy)
        self.m_dwg.m_ipofer.IPOFER_LER_FAIXADIST (ctypes.byref (parferobjv),
                            ctypes.byref (parifaixa), ctypes.byref (paricfes1),
                            ctypes.byref (parangfai), ctypes.byref (parxpt1), ctypes.byref (parypt1),
                            ctypes.byref (parxpt2), ctypes.byref (parypt2), ctypes.byref (parxcot),
                            ctypes.byref (parycot), ctypes.byref (parifdcotc), ctypes.byref (pariflnfr),
                            ctypes.byref (pariflpos), ctypes.byref (pariflbit), ctypes.byref (pariflesp),
                            ctypes.byref (paricentr), ctypes.byref (pariquebr), parordem, argfan,
                            ctypes.byref (park32vigas), ctypes.byref (park41vigas),
                            ctypes.byref (parilinexten), ctypes.byref (parilinchama),
                            ctypes.byref (paritpponta), ctypes.byref (parespac),
                            ctypes.byref (parescxy))
        icfes1          = paricfes1.value
        angfai          = parangfai.value
        xpt1            = parxpt1.value
        ypt1            = parypt1.value
        xpt2            = parxpt2.value
        ypt2            = parypt2.value
        xcot            = parxcot.value
        ycot            = parycot.value
        ifdcotc         = parifdcotc.value
        iflnfr          = pariflnfr.value
        iflpos          = pariflpos.value
        iflbit          = pariflbit.value
        iflesp          = pariflesp.value
        icentr          = paricentr.value
        iquebr          = pariquebr.value
        ordem           = parordem.value.decode(TQS.TQSUtil.CHARSET)
        k32vigas        = park32vigas.value
        k41vigas        = park41vigas.value
        ilinexten       = parilinexten.value
        ilinchama       = parilinchama.value
        itpponta        = paritpponta.value
        espac           = parespac.value
        escxy           = parescxy.value
        return          icfes1, angfai, xpt1, ypt1, xpt2, ypt2, xcot, ycot, ifdcotc, iflnfr, \
                        iflpos, iflbit, iflesp, icentr, iquebr, ordem, k32vigas, k41vigas, \
                        ilinexten, ilinchama, itpponta, espac, escxy

    def SetRebarDistrParam (self, ifaixa: int, idmniv: int = 0, idmnic: int = 0,
                             idmnil: int = 0, idmnib: int = 0, dimexe: float = 0.,
                             dimexo: float = 0., dimtsz: float = 0., dimdle: float = 0.) -> None:
        """Define os critérios de cotagem da faixa de distribuição de um ferro.

        Args:
            ifaixa: Índice em ``0..GetRebarDistrNum()-1``.
            idmniv: Nível geral de cotagem (se ``!= -1``).
            idmnic: Nível da linha de cotagem (se ``!= -1``).
            idmnil: Nível das linhas de chamada (se ``!= -1``).
            idmnib: Nível do símbolo de cotagem (se ``!= -1``).
            dimexe: Extensão da linha de chamada (se ``!= 0.``).
            dimexo: Folga da linha de chamada (se ``!= 0.``).
            dimtsz: Tamanho da marca sem linha de cotagem (se ``!= 0.``).
            dimdle: Extensão da linha de cotagem (se ``!= 0.``).
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parifaixa       = ctypes.c_int    (ifaixa)
        paridmniv       = ctypes.c_int    (idmniv)
        paridmnic       = ctypes.c_int    (idmnic)
        paridmnil       = ctypes.c_int    (idmnil)
        paridmnib       = ctypes.c_int    (idmnib)
        pardimexe       = ctypes.c_double (dimexe)
        pardimexo       = ctypes.c_double (dimexo)
        pardimtsz       = ctypes.c_double (dimtsz)
        pardimdle       = ctypes.c_double (dimdle)
        self.m_dwg.m_ipofer.IPOFER_FAIXADISTPARCOT2 (ctypes.byref (parferobjv),  \
                        ctypes.byref (parifaixa), ctypes.byref (paridmniv), ctypes.byref (paridmnic), \
                        ctypes.byref (paridmnil), ctypes.byref (paridmnib), ctypes.byref (pardimexe), \
                        ctypes.byref (pardimexo), ctypes.byref (pardimtsz), ctypes.byref (pardimdle))

    def GetRebarDistrParam (self, ifaixa: int) -> Tuple[int, int, int, int, float, float, float, float]:
        """Lê os critérios de cotagem da faixa de distribuição de um ferro.

        Args:
            ifaixa: Índice em ``0..GetRebarDistrNum()-1``.

        Returns:
            Tupla ``(idmniv, idmnic, idmnil, idmnib, dimexe, dimexo,
            dimtsz, dimdle)`` — ver :meth:`SetRebarDistrParam`.
        """
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parifaixa       = ctypes.c_int    (ifaixa)
        paridmniv       = ctypes.c_int    (0)
        paridmnic       = ctypes.c_int    (0)
        paridmnil       = ctypes.c_int    (0)
        paridmnib       = ctypes.c_int    (0)
        pardimexe       = ctypes.c_double (0.)
        pardimexo       = ctypes.c_double (0.)
        pardimtsz       = ctypes.c_double (0.)
        pardimdle       = ctypes.c_double (0.)
        self.m_dwg.m_ipofer.IPOFER_LER_FAIXADISTPARCOT (ctypes.byref (parferobjv),  \
                        ctypes.byref (parifaixa), ctypes.byref (paridmniv), ctypes.byref (paridmnic), \
                        ctypes.byref (paridmnil), ctypes.byref (paridmnib), ctypes.byref (pardimexe), \
                        ctypes.byref (pardimexo), ctypes.byref (pardimtsz), ctypes.byref (pardimdle))
        idmniv          = paridmniv.value
        idmnic          = paridmnic.value
        idmnil          = paridmnil.value
        idmnib          = paridmnib.value
        dimexe          = pardimexe.value
        dimexo          = pardimexo.value
        dimtsz          = pardimtsz.value
        dimdle          = pardimdle.value
        return          idmniv, idmnic, idmnil, idmnib, dimexe, dimexo, dimtsz, dimdle


    def DimRebarEndPoint (self, insindex: int, idimpoint: int, xpt: float, ypt: float) -> None:
        """Cotagem de uma ponta de ferro.

        Um ferro pode ter mais de uma linha definida.

        Args:
            insindex: Índice da linha a cotar (``0..``).
            idimpoint: ``0`` não, ``1`` cotar 1º ponto,
                ``2`` cotar pontos 1 e 2.
            xpt: Coordenada X.
            ypt: Coordenada Y.
        """
        parferobjv     = ctypes.c_void_p   (self.m_ferobjv)
        parinsindex    = ctypes.c_int    (insindex)
        paridimpoint   = ctypes.c_int    (idimpoint)
        parxpt         = ctypes.c_double (xpt)
        parypt         = ctypes.c_double (ypt)
        self.m_dwg.m_ipofer.IPOFER_ENTRARPTCOT (ctypes.byref (parferobjv),
            ctypes.byref (parinsindex), ctypes.byref (paridimpoint),
            ctypes.byref (parxpt), ctypes.byref (parypt))

    def RebarMarkIdentify (self, imultiple: int, xtex: float, ytex: float,
                            iflnfr: int, iflpos: int, iflbit: int, iflesp: int) -> None:
        """Identificação de uma posição de ferro.

        Cria uma nova identificação consistindo em uma ou mais linhas
        de chamada com um texto de descrição. As chamadas a
        :meth:`RebarMarkIdentifyPoint` em seguida se referem à última
        identificação criada.

        Args:
            imultiple: ``0`` poligonal+flecha, ``1`` múltiplas linhas.
            xtex: X da posição do texto de identificação.
            ytex: Y da posição do texto de identificação.
            iflnfr: ``1`` para descrever número de ferros.
            iflpos: ``1`` para descrever número da posição.
            iflbit: ``1`` para descrever bitola.
            iflesp: ``1`` para descrever espaçamento.
        """
        parferobjv     = ctypes.c_void_p   (self.m_ferobjv)
        parimultiple   = ctypes.c_int    (imultiple)
        parxtex        = ctypes.c_double (xtex)
        parytex        = ctypes.c_double (ytex)
        pariflnfr      = ctypes.c_int    (iflnfr)
        pariflpos      = ctypes.c_int    (iflpos)
        pariflbit      = ctypes.c_int    (iflbit)
        pariflesp      = ctypes.c_int    (iflesp)
        self.m_dwg.m_ipofer.IPOFER_IDENTPOS (ctypes.byref (parferobjv),
            ctypes.byref (parimultiple), ctypes.byref (parxtex), ctypes.byref (parytex),
            ctypes.byref (pariflnfr), ctypes.byref (pariflpos), ctypes.byref (pariflbit),
            ctypes.byref (pariflesp))

    def RebarMarkIdentifyPoint (self, xid: float, yid: float) -> None:
        """Insere um novo ponto da linha de cotagem.

        O primeiro ponto está na posição do texto.

        Args:
            xid: Coordenada X.
            yid: Coordenada Y.
        """
        parferobjv     = ctypes.c_void_p   (self.m_ferobjv)
        parxid         = ctypes.c_double (xid)
        paryid         = ctypes.c_double (yid)
        self.m_dwg.m_ipofer.IPOFER_IDENTPOS_ENTRARPT (ctypes.byref (parferobjv),
            ctypes.byref (parxid), ctypes.byref (paryid))

    def AdditionalLineInit (self, inivel: int, iestilo: int, icor: int) -> None:
        """Abre uma linha adicional de ferro.

        Os pontos serão definidos por :meth:`AdditionalLineInitPoint`.
        Para abrir nova linha, chame novamente esta rotina.

        Args:
            inivel: Nível EAG, ``-1`` default.
            iestilo: Estilo EAG, ``-1`` default.
            icor: Cor EAG, ``-1`` default.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        parinivel      = ctypes.c_int  (inivel)
        pariestilo     = ctypes.c_int  (iestilo)
        paricor        = ctypes.c_int  (icor)
        self.m_dwg.m_ipofer.IPOFER_LINADICINICIAR (ctypes.byref (parferobjv),
            ctypes.byref (parinivel), ctypes.byref (pariestilo), ctypes.byref (paricor))

    def AdditionalLineInitPoint (self, xpt: float, ypt: float, zpt: float, iarco: int) -> None:
        """Insere um ponto na linha adicional aberta.

        Args:
            xpt: Coordenada X.
            ypt: Coordenada Y.
            zpt: Coordenada Z.
            iarco: ``1`` se for centro de arco.
        """
        parferobjv     = ctypes.c_void_p   (self.m_ferobjv)
        parxpt         = ctypes.c_double (xpt)
        parypt         = ctypes.c_double (ypt)
        parzpt         = ctypes.c_double (zpt)
        pariarco       = ctypes.c_int    (iarco)
        self.m_dwg.m_ipofer.IPOFER_LINADICENTRARPT (ctypes.byref (parferobjv),
            ctypes.byref (parxpt), ctypes.byref (parypt), ctypes.byref (parzpt),
            ctypes.byref (pariarco))


    def DeepCopy (self) -> "SmartRebar":
        """Retorna uma cópia :class:`SmartRebar` do objeto atual.

        Returns:
            Novo :class:`SmartRebar` com os dados copiados.
        """
        rebardest       = SmartRebar (self.m_dwg)
        parferobjv      = ctypes.c_void_p (self.m_ferobjv)
        parferobjvdest  = ctypes.c_void_p (rebardest.m_ferobjv)
        self.m_dwg.m_ipofer.IPOFER_COPIARDADOSFERRO (ctypes.byref (parferobjv),
            ctypes.byref (parferobjvdest))
        return            rebardest

    def InUse (self) -> int:
        """Retorna se a posição do ferro está em uso por outro ferro.

        Returns:
            ``!= 0`` se em uso, ``0`` caso contrário.
        """
        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        inUse          = 0
        parinuse       = ctypes.c_int (inUse)
        self.m_dwg.m_ipofer.IPOFER_POS_EMUSO (ctypes.byref (parpedmv),
            ctypes.byref (parferobjv), ctypes.byref (parinuse))
        inUse          = parinuse.value
        return         inUse

    def RebarScheduleNumDescr (self) -> int:
        """Retorna o número de descrições de um ferro.

        Estribos podem gerar duas descrições.

        Returns:
            Número de descrições.
        """
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        numdescr       = 0
        parnumdescr    = ctypes.c_int (numdescr)
        self.m_dwg.m_ipofer.IPOFER_EXTTAB_NUMDESCR (ctypes.byref (parferobjv),
            ctypes.byref (parnumdescr))
        numdescr       = parnumdescr.value
        return         numdescr

    def RebarScheduleInfo (self, idescr: int) -> Tuple[int, float, int, int, int, int, float,
                                                          float, float, int, int, str, int, int,
                                                          int, int, int, int]:
        """Retorna informações de extração de tabela para uma descrição.

        Args:
            idescr: Número da descrição em ``0..RebarScheduleNumDescr()-1``.

        Returns:
            Tupla ``(ipos, bitola, nfer, mult, itpcorbar, ivar, rdval,
            rddsc, compr, igane, igand, observ, ilance, itipo99,
            icftppata, icorrido, iluvai, iluvaf)`` com posição,
            bitola, número de ferros, multiplicador, tipo CORBAR,
            flag de variável, raio de dobra e desconto, comprimento,
            ganchos, observações, lance, tipo 99, pata, corrido e
            luvas inicial/final.
        """
        ipos           = 0
        bitola         = 0.
        nfer           = 0
        mult           = 0
        itpcorbar      = 0
        ivar           = 0
        rdval          = 0.
        rddsc          = 0.
        compr          = 0.
        igane          = 0
        igand          = 0
        observ         = ""
        ilance         = 0
        itipo99        = 0
        icftppata      = 0
        icorrido       = 0
        iluvai         = 0
        iluvaf         = 0

        parpedmv       = ctypes.c_void_p (self.m_dwg.m_pedmv)
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        paridescr      = ctypes.c_int    (idescr)
        paripos        = ctypes.c_int    (ipos)
        parbitola      = ctypes.c_double (bitola)
        parnfer        = ctypes.c_int    (nfer)
        parmult        = ctypes.c_int    (mult)
        paritpcorbar   = ctypes.c_int    (itpcorbar)
        parivar        = ctypes.c_int    (ivar)
        parrdval       = ctypes.c_double (rdval)
        parrddsc       = ctypes.c_double (rddsc)
        parcompr       = ctypes.c_double (compr)
        parigane       = ctypes.c_int    (igane)
        parigand       = ctypes.c_int    (igand)
        parobserv      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        argfan         = ctypes.c_int    (0)
        parilance      = ctypes.c_int    (ilance)
        paritipo99     = ctypes.c_int    (itipo99)
        paricftppata   = ctypes.c_int    (icftppata)
        paricorrido    = ctypes.c_int    (icorrido)
        pariluvai      = ctypes.c_int    (iluvai)
        pariluvaf      = ctypes.c_int    (iluvaf)
        self.m_dwg.m_ipofer.IPOFER_EXTTAB_LERFER (ctypes.byref (parpedmv),
            ctypes.byref (parferobjv), ctypes.byref (paridescr), ctypes.byref (paripos),
            ctypes.byref (parbitola), ctypes.byref (parnfer), ctypes.byref (parmult),
            ctypes.byref (paritpcorbar), ctypes.byref (parivar), ctypes.byref (parrdval),
            ctypes.byref (parrddsc), ctypes.byref (parcompr), ctypes.byref (parigane),
            ctypes.byref (parigand), parobserv, argfan, ctypes.byref (parilance),
            ctypes.byref (paritipo99), ctypes.byref (paricftppata), ctypes.byref (paricorrido),
            ctypes.byref (pariluvai), ctypes.byref (pariluvaf))
        ipos           = paripos.value
        bitola         = parbitola.value
        nfer           = parnfer.value
        mult           = parmult.value
        itpcorbar      = paritpcorbar.value
        ivar           = parivar.value
        rdval          = parrdval.value
        rddsc          = parrddsc.value
        compr          = parcompr.value
        igane          = parigane.value
        igand          = parigand.value
        observ         = parobserv.value.decode(TQS.TQSUtil.CHARSET)
        ilance         = parilance.value
        itipo99        = paritipo99.value
        icftppata      = paricftppata.value
        icorrido       = paricorrido.value
        iluvai         = pariluvai.value
        iluvaf         = pariluvaf.value
        return         ipos, bitola, nfer, mult, itpcorbar, ivar, rdval, rddsc, compr, igane, igand, observ, ilance, itipo99, icftppata, icorrido, iluvai, iluvaf

    def ResetTextPosition (self) -> None:
        """Reposiciona os textos identificadores do ferro em posição padrão."""
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        self.m_dwg.m_ipofer.IPOFER_POSICOESPADRAO (ctypes.byref (parferobjv))
#
#       Operações geométricas com ferros
#
    def Move (self, dx: float, dy: float) -> None:
        """Movimenta um ferro.

        Args:
            dx: Deslocamento X em cm.
            dy: Deslocamento Y em cm.
        """
        parpedmv        = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pvistav         = None
        parpvistav      = ctypes.c_void_p (pvistav)
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        vardx           = ctypes.c_double (dx)
        vardy           = ctypes.c_double (dy)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_dwg.m_ipofer.OBJDWG_MOVER (parpedmv, parpvistav, parferobjv, vardx, vardy, \
                            ctypes.byref (paristat))
        istat           = paristat.value


    def Rotate (self, cx: float, cy: float, ang: float) -> None:
        """Roda um ferro em torno de um centro de rotação.

        Args:
            cx: Centro de rotação X em cm.
            cy: Centro de rotação Y em cm.
            ang: Ângulo de rotação em graus, sentido anti-horário.
        """
        parpedmv        = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pvistav         = None
        parpvistav      = ctypes.c_void_p (pvistav)
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        varcx           = ctypes.c_double (cx)
        varcy           = ctypes.c_double (cy)
        varang          = ctypes.c_double (ang)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_dwg.m_ipofer.OBJDWG_RODAR (parpedmv, parpvistav, parferobjv,
                            varcx, varcy, varang, ctypes.byref (paristat))


    def Scale (self, cx: float, cy: float, escala: float) -> None:
        """Escala um ferro a partir de um centro.

        Args:
            cx: Centro de escala X em cm.
            cy: Centro de escala Y em cm.
            escala: Valor da escala.
        """
        parpedmv        = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pvistav         = None
        parpvistav      = ctypes.c_void_p (pvistav)
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        varcx           = ctypes.c_double (cx)
        varcy           = ctypes.c_double (cy)
        varescala       = ctypes.c_double (escala)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_dwg.m_ipofer.OBJDWG_ESCALAR (parpedmv, parpvistav, parferobjv,
                            varcx, varcy, varescala, ctypes.byref (paristat))


    def Mirror (self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Espelha um ferro em torno de uma linha.

        Args:
            x1: X do primeiro ponto da linha de espelho em cm.
            y1: Y do primeiro ponto da linha de espelho em cm.
            x2: X do segundo ponto da linha de espelho em cm.
            y2: Y do segundo ponto da linha de espelho em cm.
        """
        parpedmv        = ctypes.c_void_p (self.m_dwg.m_pedmv)
        pvistav         = None
        parpvistav      = ctypes.c_void_p (pvistav)
        parferobjv     = ctypes.c_void_p (self.m_ferobjv)
        varx1           = ctypes.c_double (x1)
        vary1           = ctypes.c_double (y1)
        varx2           = ctypes.c_double (x2)
        vary2           = ctypes.c_double (y2)
        istat          = 0
        paristat       = ctypes.c_int (istat)
        self.m_dwg.m_ipofer.OBJDWG_ESPELHAR (parpedmv, parpvistav, parferobjv,
                            varx1, vary1, varx2, vary2, ctypes.byref (paristat))
