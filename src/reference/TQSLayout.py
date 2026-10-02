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
#    TQSLayout         Módulo para leitura e gravação de plantas para plotagem
#                      Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes
import os
from typing import List

import TQS.TQSUtil, TQS.TQSDwg, TQS.TQSBuild

#-----------------------------------------------------------------------------
class Layout ():
    """Leitura e gravação de plantas (arquivos CPL) para plotagem.

    Um layout é um conjunto de :class:`Drawing` (desenhos DWG) posicionados
    sobre uma folha de papel de dimensões ``sizex`` × ``sizey`` cm.

    Implementação:
        Os métodos desta classe são wrappers finos sobre as funções ``IOCPL_*``
        exportadas por ``MDWG.DLL`` (com apoio de ``ACESSOL.DLL``) para ler e
        gravar arquivos CPL. O padrão recorrente é: (1) embrulhar strings em
        ``c_char_p`` (codificadas em :data:`TQS.TQSUtil.CHARSET`), ints/doubles
        em ``c_int``/``c_double``, e buffers em ``create_string_buffer``;
        (2) chamar a rotina C++ via handle de DLL passando ponteiros por
        referência; (3) ler de volta as saídas via ``.value`` ou decodificando
        o buffer. Comentários inline destacam apenas as fronteiras lógicas
        (cabeçalho, iteração de desenhos, finalização) onde a sequência não
        é puramente plumbing de ctypes.

    Attributes:
        m_cplname: Nome do arquivo CPL associado.
        m_drawings: Lista de :class:`Drawing` que compõem a planta.
        m_sizex: Largura do papel em cm.
        m_sizey: Altura do papel em cm.
        m_mdwg: Handle de ``MDWG.DLL``.
        m_acessol: Handle de ``ACESSOL.DLL``.
        m_layer: Vetor de layers ativos (tamanho ``TQSDwg.MAXIELY``).
    """

    def __init__ (self) -> None:
        """Inicializa um layout vazio carregando as DLLs necessárias."""
        self.m_cplname  = ""
        self.m_drawings = []
        self.m_sizex    = 0.
        self.m_sizey    = 0.
        self.m_mdwg     = TQS.TQSUtil.LoadDll ("MDWG.DLL")
        self.m_acessol  = TQS.TQSUtil.LoadDll ("ACESSOL.DLL")
        self.m_layer    = [1] * TQS.TQSDwg.MAXIELY

    def __str__(self) -> str:
        """Retorna representação textual do layout (debug).

        ATENÇÃO: o laço final faz ``str += ...``, incrementando o nome embutido
        ``str`` em vez da mensagem, e chama ``str(drawing)`` na mesma expressão.
        Converter esta classe para texto levanta ``TypeError``/``UnboundLocalError``
        e os desenhos nunca aparecem no resultado. Percorra ``m_drawings`` por
        conta própria para inspecioná-los.
        """
        msg             = "Class Layout"
        msg             += "\n   m_mdwg " + str (self.m_mdwg)
        msg             += "\n   m_acessol " + str (self.m_acessol)
        msg             += "\n   [%s]" % self.m_cplname
        msg             += "\n   Size X %7.2f" % self.m_sizex
        msg             += "\n   Size Y %7.2f" % self.m_sizey
        for             drawing in self.m_drawings:
            str         += "\n" + str (drawing)
        return          msg

    def CreateName (self, prefix1: str, prefix2: str, iplanta: int,
                    irevisao: int, tipo: str) -> str:
        """Cria nome de arquivo CPL segundo a Nomenclatura de Arquivos atual.

        ATENÇÃO: após a chamada nativa o corpo testa ``istat``, um nome que nunca
        é atribuído (o status fica em ``paristat``). Toda chamada a
        ``CreateName()`` levanta ``NameError`` antes de retornar. Monte o nome do
        arquivo por conta própria enquanto a biblioteca não for corrigida.

        Args:
            prefix1: Prefixo primário do nome de arquivo.
            prefix2: Prefixo secundário do nome de arquivo.
            iplanta: Número da planta.
            irevisao: Número da revisão.
            tipo: Tipo do arquivo (ex.: ``"CPL"``).

        Returns:
            Nome completo do arquivo CPL conforme nomenclatura, ou string
            vazia em caso de erro.
        """
        # Prepara entradas (prefixos, índices, tipo) e o buffer de saída para o nome composto
        parprefix1      = ctypes.c_char_p (prefix1.encode(TQS.TQSUtil.CHARSET))
        parprefix2      = ctypes.c_char_p (prefix2.encode(TQS.TQSUtil.CHARSET))
        pariplanta      = ctypes.c_int (iplanta)
        parirevisao     = ctypes.c_int (irevisao)
        partipo         = ctypes.c_char_p (tipo.encode(TQS.TQSUtil.CHARSET))
        ifan            = ctypes.c_int (0)
        parcplname      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        paristat        = ctypes.c_int (0)
        # Monta o nome conforme a Nomenclatura de Arquivos TQS (DLL devolve o nome no buffer)
        self.m_mdwg.IOCPL_MONCAR (parprefix1, ifan, parprefix2, ifan, ctypes.byref (pariplanta), \
                         ctypes.byref (parirevisao), partipo, ifan, parcplname, ifan, \
                         ctypes.byref (paristat))
        # Decodifica o resultado; em caso de erro devolve string vazia
        cplname         = parcplname.value.decode(TQS.TQSUtil.CHARSET)
        if              istat != 0:
            cplname     = ""
        return          cplname

    def New (self, cplname: str, sizex: float, sizey: float) -> None:
        """Cria uma planta nova (em memória), descartando o conteúdo atual.

        ATENÇÃO: o corpo atribui ``self.drawings = []``, mas a coleção usada pelo
        construtor, pelo ``Open`` e pelo ``SaveAs`` é ``self.m_drawings``. O
        conteúdo anterior NÃO é descartado: reutilizar uma instância e chamar
        ``New`` preserva os desenhos antigos, que serão gravados na planta nova.
        Crie uma instância de :class:`Layout` nova, ou limpe ``m_drawings``
        explicitamente.

        Args:
            cplname: Nome do arquivo CPL associado.
            sizex: Largura do papel em cm.
            sizey: Altura do papel em cm.
        """
        self.m_cplname  = cplname
        self.drawings   = []
        self.m_sizex    = sizex
        self.m_sizey    = sizey

    def Save (self) -> int:
        """Salva o arquivo CPL em disco usando o nome corrente.

        Returns:
            ``0`` em sucesso, ``!= 0`` em caso de erro.
        """
        return          self.SaveAs (self.m_cplname)

    def SaveAs (self, cplname: str) -> int:
        """Salva o arquivo CPL em disco com o nome fornecido.

        Args:
            cplname: Nome do arquivo CPL de saída.

        Returns:
            ``0`` em sucesso, ``!= 0`` em caso de erro.
        """
        # Abre o CPL para escrita na unidade lógica 31 (handle interno do MDWG)
        pararqcpl       = ctypes.c_char_p (cplname.encode(TQS.TQSUtil.CHARSET))
        ifan            = ctypes.c_int (0)
        iunit           = 31
        pariunit        = ctypes.c_int (iunit)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_mdwg.IOCPL_OPENWX (pararqcpl, ifan, ctypes.byref (pariunit), ctypes.byref (paristat))
        istat           = paristat.value
        if              istat != 0:
            TQS.TQSUtil.writef ("Não consegui salvar [%s]" % self.m_cplname)
            return      istat
        # Cabeçalho da planta: tipo de folha A0, índice e dimensões do papel em cm
        ielm            = 0
        parielm         = ctypes.c_int (ielm)
        iedcar          = 0
        pariedcar       = ctypes.c_int (iedcar)
        iedmol          = 0
        pariedmol       = ctypes.c_int (iedmol)
        iedcor          = 0
        pariedcor       = ctypes.c_int (iedcor)
        itptab          = 0
        paritptab       = ctypes.c_int (itptab)
        itipla          = "A0      "
        paritipla       = ctypes.c_char_p (itipla.encode(TQS.TQSUtil.CHARSET))
        indpla          = 1
        parindpla       = ctypes.c_int (indpla)
        comform         = self.m_sizex
        parcomform      = ctypes.c_double (comform)
        altform         = self.m_sizey
        paraltform      = ctypes.c_double (altform)
        paristat        = ctypes.c_int (istat)
        # Grava o registro de cabeçalho do CPL (uma única vez antes dos desenhos)
        self.m_mdwg.IOCPL_GRVHED (ctypes.byref (parielm), ctypes.byref (pariedcar), \
                            ctypes.byref (pariedmol), ctypes.byref (pariedcor), \
                            ctypes.byref (paritptab), paritipla, ifan, ctypes.byref (parindpla), \
                            ctypes.byref (parcomform), ctypes.byref (paraltform));
#
#       Itera pelos desenhos
#
        # Cada desenho da planta vira um registro IOCPL_GRVARQ no CPL
        for             drawing in self.m_drawings:
            # Empacota nome do DWG, descrição, pavimento e demais atributos do desenho
            arqdwg      = drawing.m_nomarq
            pararqdwg   = ctypes.c_char_p (arqdwg.encode(TQS.TQSUtil.CHARSET))
            parnomfan   = ctypes.c_char_p (drawing.m_nomfan.encode(TQS.TQSUtil.CHARSET))
            parnompav   = ctypes.c_char_p (drawing.m_nompav.encode(TQS.TQSUtil.CHARSET))
            pariaplic   = ctypes.c_int (drawing.m_iaplic)
            itipdes     = 0
            paritipdes  = ctypes.c_int (itipdes)
            size        = TQS.TQSDwg.MAXIELY
            c_array     = (ctypes.c_int * size)(*self.m_layer)
            parescala   = ctypes.c_double (drawing.m_escala)
            parangulo   = ctypes.c_double (drawing.m_angulo)
            pardesorx   = ctypes.c_double (drawing.m_desorx)
            pardesory   = ctypes.c_double (drawing.m_desory)
            parposx     = ctypes.c_double (drawing.m_posx)
            parposy     = ctypes.c_double (drawing.m_posy)
            pardestax   = ctypes.c_double (drawing.m_destax)
            pardestay   = ctypes.c_double (drawing.m_destay)
            parxjmin    = ctypes.c_double (0.)
            paryjmin    = ctypes.c_double (0.)
            parxjmax    = ctypes.c_double (0.)
            paryjmax    = ctypes.c_double (0.)
            paristat    = ctypes.c_int (0)
            # Grava um registro de desenho com layers, escala, ângulo, origem e posição na planta
            self.m_mdwg.IOCPL_GRVARQ (pararqdwg, ifan, parnomfan, ifan, parnompav, ifan, \
                            ctypes.byref (pariaplic), ctypes.byref (paritipdes), \
                            c_array, ctypes.byref (parescala), ctypes.byref (parangulo), \
                            ctypes.byref (pardesorx), ctypes.byref (pardesory),
			    ctypes.byref (parposx), ctypes.byref (parposy), \
                            ctypes.byref (pardestax), ctypes.byref (pardestay), \
			    ctypes.byref (parxjmin), ctypes.byref (paryjmin), \
                            ctypes.byref (parxjmax), ctypes.byref (paryjmax), \
                            ctypes.byref (paristat))
            istat          = paristat.value
            if          istat != 0:
                TQS.TQSUtil.writef ("Não consegui gravar [%s]" % arqdwg)

        # Fecha o CPL liberando a unidade lógica
        self.m_mdwg.IOCPL_CLOSEW ()
        return          istat;

    def Open (self, cplname: str) -> int:
        """Abre e carrega um arquivo de layout CPL. Não precisa ser fechado.

        Lê o cabeçalho (dimensões da folha) e itera por todos os
        desenhos do CPL, populando :attr:`m_drawings`.

        ATENÇÃO: após ler o cabeçalho o código testa a variável Python anterior à
        chamada (``istat == 0``) em vez de ``paristat.value``. Uma falha de
        leitura do cabeçalho é tratada como sucesso e a rotina segue
        interpretando um CPL ilegível. Valide o retorno e o conteúdo de
        ``m_drawings`` antes de confiar no resultado.

        Args:
            cplname: Nome do arquivo CPL a abrir.

        Returns:
            ``0`` em sucesso, ``!= 0`` em caso de erro de abertura ou leitura.
        """
        # Abre o CPL para leitura na unidade lógica 32 (handle interno do MDWG)
        self.m_cplname  = cplname
        pararqcpl       = ctypes.c_char_p (cplname.encode(TQS.TQSUtil.CHARSET))
        ifan            = ctypes.c_int (0)
        iunit           = 32
        pariunit        = ctypes.c_int (iunit)
        paristat        = ctypes.c_int (0)
        self.m_mdwg.IOCPL_OPENRX (pararqcpl, ifan, ctypes.byref (pariunit), ctypes.byref (paristat))
        istat           = paristat.value
        if              istat != 0:
            TQS.TQSUtil.writef ("Não consegui ler [%s]" % cplname)
            return      istat

        # Aloca buffers para o cabeçalho (tipo de folha, dimensões, configurações de pena)
        ielm            = 0
        parielm         = ctypes.c_int (ielm)
        iedcar          = 0
        pariedcar       = ctypes.c_int (iedcar)
        iedmol          = 0
        pariedmol       = ctypes.c_int (iedmol)
        iedcor          = 0
        pariedcor       = ctypes.c_int (iedcor)
        itptab          = 0
        paritptab       = ctypes.c_int (itptab)
        paritipla       = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        indpla          = 0
        parindpla       = ctypes.c_int (indpla)
        comform         = 0.
        parcomform      = ctypes.c_double (comform)
        altform         = 0.
        paraltform      = ctypes.c_double (altform)
        iprpen          = 0
        pariprpen       = ctypes.c_int (iprpen)
        istat           = 0
        paristat        = ctypes.c_int (istat)
        # Lê o registro de cabeçalho do CPL (chamado uma única vez antes do loop de desenhos)
        self.m_mdwg.IOCPL_LERHED (ctypes.byref (parielm), ctypes.byref (pariedcar), \
                            ctypes.byref (pariedmol), ctypes.byref (pariedcor), \
                            ctypes.byref (paritptab), paritipla, ifan, ctypes.byref (parindpla), \
                            ctypes.byref (parcomform), ctypes.byref (paraltform), \
                            ctypes.byref (pariprpen), ctypes.byref (paristat))
        if              istat != 0:
            TQS.TQSUtil.writef ("Erro lendo header do [%s]" % cplname)
            return      istat
        # Extrai dimensões do papel (cm) do cabeçalho
        self.m_sizex    = parcomform.value
        self.m_sizey    = paraltform.value

        # Itera lendo um registro de desenho por vez até IOCPL_LERARQ sinalizar EOF (istat != 0)
        while           True:
            parnomarq   = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
            parnomfan   = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
            parnompav   = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
            size        = TQS.TQSDwg.MAXIELY
            c_array     = (ctypes.c_int * size)(*self.m_layer)
            iaplic      = 0
            pariaplic   = ctypes.c_int (iaplic)
            itipdes     = 0
            paritipdes  = ctypes.c_int (itipdes)
            escala      = 0.
            parescala   = ctypes.c_double (escala)
            angulo      = 0.
            parangulo   = ctypes.c_double (angulo)
            desorx      = 0.
            pardesorx   = ctypes.c_double (desorx)
            desory      = 0.
            pardesory   = ctypes.c_double (desory)
            posx        = 0.
            parposx     = ctypes.c_double (posx)
            posy        = 0.
            parposy     = ctypes.c_double (posy)
            destax      = 0.
            pardestax   = ctypes.c_double (destax)
            destay      = 0.
            pardestay   = ctypes.c_double (destay)
            xjmin       = 0.
            parxjmin    = ctypes.c_double (xjmin)
            yjmin       = 0.
            paryjmin    = ctypes.c_double (yjmin)
            xjmax       = 0.
            parxjmax    = ctypes.c_double (xjmax)
            yjmax       = 0.
            paryjmax    = ctypes.c_double (yjmax)
            ipen        = 0
            paripen     = ctypes.c_int (ipen)
            istat       = 0
            paristat    = ctypes.c_int (istat)
            # Lê o próximo registro de desenho do CPL
            self.m_mdwg.IOCPL_LERARQ (parnomarq, ifan, parnomfan, ifan, parnompav, ifan, \
                        ctypes.byref (pariaplic), ctypes.byref (paritipdes), c_array, \
                        ctypes.byref (parescala), ctypes.byref (parangulo), ctypes.byref (pardesorx), \
                        ctypes.byref (pardesory), ctypes.byref (parposx), ctypes.byref (parposy), \
                        ctypes.byref (pardestax), ctypes.byref (pardestay), ctypes.byref (parxjmin), \
                        ctypes.byref (paryjmin), ctypes.byref (parxjmax), ctypes.byref (paryjmax), \
                        ctypes.byref (paripen), ctypes.byref (paristat));
            # Decodifica strings e desempacota valores numéricos do registro lido
            nomarq      = parnomarq.value.decode(TQS.TQSUtil.CHARSET)
            nomfan      = parnomfan.value.decode(TQS.TQSUtil.CHARSET)
            nompav      = parnompav.value.decode(TQS.TQSUtil.CHARSET)
            iaplic      = pariaplic.value
            itipdes     = paritipdes.value
            escala      = parescala.value
            angulo      = parangulo.value
            desorx      = pardesorx.value
            desory      = pardesory.value
            posx        = parposx.value
            posy        = parposy.value
            destax      = pardestax.value
            destay      = pardestay.value
            istat       = paristat.value
            if          istat != 0:
                break
            # Reconstitui o Drawing com os dados do CPL (sobrescreve os valores
            # extraídos automaticamente da abertura do DWG dentro de Drawing.__init__)
            drawing     = Drawing (nomarq)
            drawing.fileDescription = nomfan
            drawing.floorPlan       = nompav
            drawing.scale           = escala
            drawing.xOrigin         = desorx
            drawing.yOrigin         = desory
            drawing.xDimension      = destax
            drawing.yDimension      = destay
            drawing.systemId        = iaplic
            drawing.xInsertion      = posx
            drawing.yInsertion      = posy
            drawing.insertionAngle  = angulo
            self.EnterDrawing (drawing)
        # Fecha o CPL liberando a unidade lógica de leitura
        self.m_mdwg.IOCPL_CLOSER ()
        return          0

    def NumDrawings (self) -> int:
        """Retorna o número de desenhos da planta.

        Returns:
            Quantidade de :class:`Drawing` no layout.
        """
        return          len (self.m_drawings)


    def ReadDrawing (self, idrawing: int) -> "Drawing":
        """Lê os dados de um desenho da planta pelo seu índice.

        Args:
            idrawing: Índice do desenho (``0..NumDrawings()-1``).

        Returns:
            Objeto :class:`Drawing` correspondente.
        """
        return          self.m_drawings [idrawing]

    def EnterDrawing (self, drawing: "Drawing") -> None:
        """Adiciona um desenho à planta atual.

        Args:
            drawing: Desenho a inserir.
        """
        self.m_drawings.append (drawing)

#-----------------------------------------------------------------------------
class Drawing ():
    """Um desenho posicionado em uma planta CPL.

    Algumas propriedades (origem, tamanho, escala, sistema TQS) são
    determinadas automaticamente da leitura do DWG; outras (posição na
    planta, ângulo, descrição) são fornecidas pelo usuário.

    Attributes:
        m_nomarq: Nome do arquivo DWG.
        m_nompav: Pavimento ou pasta associada.
        m_escala: Escala de desenho (un. desenho / escala = cm plotados).
        m_desorx: X do canto inferior esquerdo do desenho, em un. de desenho.
        m_desory: Y do canto inferior esquerdo do desenho, em un. de desenho.
        m_destax: Largura do desenho em un. de desenho.
        m_destay: Altura do desenho em un. de desenho.
        m_iaplic: Número da aplicação TQS (sistema, 1..).
        m_nomfan: Descrição livre do desenho.
        m_angulo: Ângulo de inserção em graus.
        m_posx: X de inserção na planta, em cm.
        m_posy: Y de inserção na planta, em cm.
    """

    def __init__ (self, filename: str) -> None:
        """Cria um desenho a partir do nome de um arquivo DWG.

        Determina automaticamente pavimento, escala, aplicação e origem no
        canto inferior esquerdo. Os dados de inserção e a descrição
        do desenho devem ser definidos depois via setters.

        Args:
            filename: Caminho do arquivo DWG. Será aberto temporariamente
                para extrair limites e configurações.
        """
        self.m_nomarq   = ""                    # Nome do arquivo
        self.m_nompav   = ""                    # Planta associado
        self.m_escala   = 50.                   # Escala de desenho
        self.m_desorx   = 0.                    # Origem  X do desenho em unidades do desenho
        self.m_desory   = 0.                    #         Y
        self.m_destax   = 0.                    # Tamanho X do desenho em unidades do desenho
        self.m_destay   = 0.                    #         Y
        self.m_iaplic   = 1                     # Aplicação TQS
        self.m_nomfan   = ""                    # Descrição
        self.m_angulo   = 0.                    # Ângulo de inserção em graus
        self.m_posx     = 0.                    # Posição X no sistema da planta cm
        self.m_posy     = 0.                    #         Y

        # Etapa 1: abre temporariamente o DWG para extrair escala, limites e sistema TQS
        dwg             = TQS.TQSDwg.Dwg ()
        if              dwg.file.Open (filename) != 0:
            TQS.TQSUtil.writef ("Não abri o arquivo [%s] para leitura" % filename)
        self.m_nomarq   = filename
        self.m_escala   = dwg.settings.scale
        # Limites do desenho definem origem (canto inferior esquerdo) e tamanho
        xmin, ymin, xmax, ymax = dwg.limits.DwgLimits ()
        self.m_desorx   = xmin
        self.m_desory   = ymin
        self.m_destax   = xmax - xmin
        self.m_destay   = ymax - ymin
        self.m_iaplic   = dwg.settings.systemId
        dwg.file.Close  ()

        # Etapa 2: descobre o pavimento entrando momentaneamente no diretório do DWG
        # (BuildingContext lê o contexto do edifício a partir do cwd)
        diratu          = os.getcwd()
        dir, name       = os.path.split (filename)
        os.chdir        (dir)
        nprjpv, nprjed, nombde, nomedi, nompav, istat = TQS.TQSBuild.BuildingContext ()
        # Restaura o cwd original para não afetar o restante da aplicação
        os.chdir        (diratu)
        self.m_nompav   = nompav

    def __str__(self) -> str:
        """Retorna representação textual do desenho (debug)."""
        msg             =  "   Class Drawing\n"
        msg             += "       m_nomarq         [%s]\n"  % self.m_nomarq
        msg             += "       m_nompav         [%s]\n"  % self.m_nompav
        msg             += "       m_iaplic         %7d\n"   % self.m_iaplic
        msg             += "       m_escala         %7.2f\n" % self.m_escala
        msg             += "       m_desorx         %7.2f\n" % self.m_desorx
        msg             += "       m_desory         %7.2f\n" % self.m_desory
        msg             += "       m_destax         %7.2f\n" % self.m_destax
        msg             += "       m_destay         %7.2f\n" % self.m_destay
        msg             += "       ---- Outros fornecidos:\n"
        msg             += "       m_nomfan         [%s]\n"  % self.m_nomfan
        msg             += "       m_angulo         %7.2f\n" % self.m_angulo
        msg             += "       m_posx           %7.2f\n" % self.m_posx
        msg             += "       m_posy           %7.2f\n" % self.m_posy
        return          msg

    @property
    def fileName (self) -> str:
        """str: Nome (caminho) do arquivo DWG."""
        return          self.m_nomarq

    @fileName.setter
    def fileName (self, filename: str) -> None:
        """Atribui Nome (caminho) do arquivo DWG."""
        self.m_nomarq   = filename

    @property
    def fileDescription (self) -> str:
        """str: Descrição livre do desenho."""
        return          self.m_nomfan

    @fileDescription.setter
    def fileDescription (self, description: str) -> None:
        """Atribui Descrição livre do desenho."""
        self.m_nomfan   = description

    @property
    def floorPlan (self) -> str:
        """str: Pavimento associado (ou nome da pasta)."""
        return          self.m_nompav

    @floorPlan.setter
    def floorPlan (self, floorplan: str) -> None:
        """Atribui Pavimento associado (ou nome da pasta)."""
        self.m_nompav   = floorplan

    @property
    def scale (self) -> float:
        """float: Escala (unidade de desenho / escala = cm plotados).

        ATENÇÃO: na biblioteca TQS esta propriedade usa ``m_scale``, enquanto a
        construção, a serialização e o ``SaveAs`` usam ``m_escala``. Duas
        consequências: LER ``drawing.scale`` em uma instância nova levanta
        ``AttributeError`` (``m_scale`` nunca é inicializado) e ATRIBUIR
        ``drawing.scale`` não altera a escala gravada — o desenho sai na escala
        de ``m_escala``. Para mudar a escala efetiva, atribua ``m_escala``.
        """
        return          self.m_scale

    @scale.setter
    def scale (self, scale: float) -> None:
        """Atribui Escala (unidade de desenho / escala = cm plotados).

        ATENÇÃO: ver a nota no getter — grava ``m_scale``, que o ``SaveAs``
        ignora; a escala efetiva vem de ``m_escala``.
        """
        self.m_scale    = scale

    @property
    def xOrigin (self) -> float:
        """float: Origem X em unidades de desenho (= ponto de inserção na planta)."""
        return          self.m_desorx

    @xOrigin.setter
    def xOrigin (self, xOrigin: float) -> None:
        """Atribui Origem X em unidades de desenho (= ponto de inserção na planta)."""
        self.m_desorx   = xOrigin

    @property
    def yOrigin (self) -> float:
        """float: Origem Y em unidades de desenho (= ponto de inserção na planta)."""
        return          self.m_desory

    @yOrigin.setter
    def yOrigin (self, yOrigin: float) -> None:
        """Atribui Origem Y em unidades de desenho (= ponto de inserção na planta)."""
        self.m_desory   = yOrigin

    @property
    def xDimension (self) -> float:
        """float: Tamanho X em unidades de desenho."""
        return          self.m_destax

    @xDimension.setter
    def xDimension (self, xDimension: float) -> None:
        """Atribui Tamanho X em unidades de desenho."""
        self.m_destax   = xDimension

    @property
    def yDimension (self) -> float:
        """float: Tamanho Y em unidades de desenho."""
        return          self.m_destay

    @yDimension.setter
    def yDimension (self, yDimension: float) -> None:
        """Atribui Tamanho Y em unidades de desenho."""
        self.m_destay   = yDimension

    @property
    def systemId (self) -> int:
        """int: Número do sistema TQS (1..) na caixa de propriedades do EAG."""
        return          self.m_iaplic

    @systemId.setter
    def systemId (self, systemid: int) -> None:
        """Atribui Número do sistema TQS (1..) na caixa de propriedades do EAG."""
        self.m_iaplic     = systemid
#
#       Os atributos abaixo não podem ser determinados automaticamente
#       Devem ser fornecidos pelo usuário para posicionar o desenho na planta
#
    @property
    def xInsertion (self) -> float:
        """float: Ponto de inserção X na planta, em cm."""
        return          self.m_posx

    @xInsertion.setter
    def xInsertion (self, xInsertion: float) -> None:
        """Atribui Ponto de inserção X na planta, em cm."""
        self.m_posx     = xInsertion

    @property
    def yInsertion (self) -> float:
        """float: Ponto de inserção Y na planta, em cm."""
        return          self.m_posy

    @yInsertion.setter
    def yInsertion (self, yInsertion: float) -> None:
        """Atribui Ponto de inserção Y na planta, em cm."""
        self.m_posy     = yInsertion

    @property
    def insertionAngle (self) -> float:
        """float: Ângulo de inserção do desenho na planta, em graus."""
        return          self.m_angulo

    @insertionAngle.setter
    def insertionAngle (self, insertionAngle: float) -> None:
        """Atribui Ângulo de inserção do desenho na planta, em graus."""
        self.m_angulo   = insertionAngle
