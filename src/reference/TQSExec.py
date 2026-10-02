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
#   TQSExec.py          Execução do TQS em batch
#                       Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes
from typing import List

from TQS import TQSUtil
#-----------------------------------------------------------------------------
#       Classe Task: uma tarefa a ser executada
#
class Task ():
    """Classe-mãe das tarefas executadas pelo gerenciador TQS em batch.

    Cada subclasse representa uma tarefa específica e define :meth:`Script`
    para retornar a string de comando correspondente.

    Implementação:
        O padrão deste módulo difere dos wrappers ctypes — não há chamada a DLL.
        Cada subclasse de :class:`Task` modela uma tarefa do gerenciador TQS e
        sobrescreve :meth:`Script` para devolver uma única linha na DSL do
        ``TQS.EXE`` (por exemplo ``EDIFICIO ...``, ``PROC ...``, ``DESLAJ ...``).
        A classe :class:`Job` acumula instâncias de :class:`Task` e, em
        :meth:`Job.Execute`, serializa cada script para o arquivo
        ``GERENCIADOR.DAT`` antes de invocar ``TQS.EXE -CMD:GERENCIADOR.DAT``,
        que então interpreta o lote de comandos.

    Attributes:
        TASK_NONE: Tarefa não definida.
        TASK_FOLDER: Selecionar pasta atual do edifício.
        TASK_ROOTFOLDER: Selecionar pasta raiz de edifícios.
        TASK_GLOBALPROC: Processamento global.
        TASK_LOADSREPORT: Planta de cargas (PORLID).
        TASK_SLABDRAWINGS: Desenhos de lajes.
        TASK_LATTICESLABS: Desenhos de lajes treliçadas.
        TASK_COMPOSITESLABS: Desenhos de lajes mistas nervuradas.
        TASK_REBARSCHEDULE: Tabela de ferros consolidada.
        TASK_STAIRS: Processamento de escadas.
        TASK_FLOORPLANDRAWINGS: Desenho de formas.
        TASK_PRECASTDRAWINGS: Desenhos de pré-moldados.
        TASK_PRECASTBEAMS: Transferência de esforços para vigas pré-moldadas.
        TASK_PRECASTFOUNDATIONS: Transferência de esforços para fundações pré-moldadas.
        TASK_PRECASTCOLUMNS: Pilares pré-moldados.
        TASK_PRECASTCORBELS: Consolos pré-moldados.
        TASK_PRECASTMATERIALS: Quantitativos de pré-moldados.
        TASK_STRUCTURALREPORT: Resumo estrutural.
    """

    TASK_NONE:               int =  0
    TASK_FOLDER:             int =  1
    TASK_ROOTFOLDER:         int =  2
    TASK_GLOBALPROC:         int =  3
    TASK_LOADSREPORT:        int =  4
    TASK_SLABDRAWINGS:       int =  5
    TASK_LATTICESLABS:       int =  6
    TASK_COMPOSITESLABS:     int =  7
    TASK_REBARSCHEDULE:      int =  8
    TASK_STAIRS:             int =  9
    TASK_FLOORPLANDRAWINGS:  int = 10
    TASK_PRECASTDRAWINGS:    int = 11
    TASK_PRECASTBEAMS:       int = 12
    TASK_PRECASTFOUNDATIONS: int = 13
    TASK_PRECASTCOLUMNS:     int = 14
    TASK_PRECASTCORBELS:     int = 15
    TASK_PRECASTMATERIALS:   int = 16
    TASK_STRUCTURALREPORT:   int = 17

    def __init__ (self) -> None:
        """Inicializa a tarefa-mãe (subclasses sobrescrevem :attr:`m_itask`)."""
        self.m_itask         = self.TASK_NONE
#-----------------------------------------------------------------------------
#       Pasta atual do edifício
#
class TaskFolder (Task):
    """Tarefa que define a pasta atual de trabalho dentro do edifício.

    Attributes:
        FOLDER_FRAMES: Pasta Espacial.
        FOLDER_COLUMNS: Pasta Pilares.
        FOLDER_FOUNDATIONS: Pasta Fundações.
        FOLDER_FLOORS: Pasta de pavimento (requer ``folderName``).
        FOLDER_GENERAL: Pasta Gerais.
        FOLDER_INFRASTRUCTURE: Pasta Infraestrutura.
        SUBFOLDER_NONE: Sem subpasta — usar pasta de pavimento direta.
        SUBFOLDER_BEAMS: Subpasta vigas.
        SUBFOLDER_STAIRS: Subpasta escadas.
    """
#
#       Tipo da pasta escolhida
#
    FOLDER_FRAMES:         int = 0           # Pasta Espacial
    FOLDER_COLUMNS:        int = 1           # Pasta Pilares
    FOLDER_FOUNDATIONS:    int = 2           # Pasta Fundacoes
    FOLDER_FLOORS:         int = 3           # Pasta do pavimento
    FOLDER_GENERAL:        int = 4           # Pasta Gerais
    FOLDER_INFRASTRUCTURE: int = 5           # Pasta Infraestrutura
#
#       Subpasta de plantas
#
    SUBFOLDER_NONE:        int = 0           # Pasta do pavimento
    SUBFOLDER_BEAMS:       int = 1           # Subpasta vigas
    SUBFOLDER_STAIRS:      int = 2           # Subpasta escadas

    def __init__ (self,
            buildingName: str,
            folderType: int = FOLDER_FRAMES,
            folderName: str = "",
            subFolder:  int = SUBFOLDER_NONE) -> None:
        """Define a pasta atual do edifício.

        Args:
            buildingName: Nome do edifício alvo.
            folderType: Tipo da pasta. Use uma constante ``FOLDER_*``.
            folderName: Nome da pasta — obrigatório quando ``folderType``
                é :data:`FOLDER_FLOORS`.
            subFolder: Subpasta. Use uma constante ``SUBFOLDER_*``.
        """
        super().__init__()
        self.m_itask         = self.TASK_FOLDER
        self.m_buildingName  = buildingName
        self.m_folderType    = folderType
        self.m_folderName    = folderName
        self.m_subFolder     = subFolder

    def Script (self) -> str:
        """Retorna o script para execução no gerenciador.

        Returns:
            Linha de comando ``EDIFICIO ...`` correspondente à pasta.
        """
        # Mapeia constantes FOLDER_* / SUBFOLDER_* para os tokens da DSL do gerenciador.
        tipos           = ["ESPACIAL", "PILAR", "FUNDAC", "", "GERAIS", "SISE"] #!NTR
        subtipos        = ["", "VIGAS", "ESCADAS"]                              #!NTR
        # Comando base: identifica o edifício e o tipo de pasta.
        script          = "EDIFICIO '" + self.m_buildingName + "' " + tipos [self.m_folderType]#!NTR
        # Pasta de pavimento exige o nome da pasta como argumento adicional.
        if              (self.m_folderType == self.FOLDER_FLOORS):
            script      += " '" + self.m_folderName + "'"
        # Subpasta opcional (vigas/escadas) — anexa apenas se diferente de NONE.
        if              (self.m_subFolder != self.SUBFOLDER_NONE):
            script      += " " + subtipos [self.m_subFolder-1]
        return          (script)

#-----------------------------------------------------------------------------
#       Raiz do edifício
#
class TaskRootFolder (Task):
    """Tarefa que define a pasta raiz da árvore de edifícios."""

    def __init__ (self, rootfolder: str) -> None:
        """Define a pasta raiz de edifícios.

        Args:
            rootfolder: Caminho da pasta raiz.
        """
        super().__init__()
        self.m_itask         = self.TASK_ROOTFOLDER
        self.m_rootfolder    = rootfolder

    def Script (self) -> str:
        """Retorna o script ``ARVORE ...`` para o gerenciador."""
        return          "ARVORE '" + self.m_rootfolder + "'"   #!NTR

#-----------------------------------------------------------------------------
#       Processamento Global
#
class TaskGlobalProc (Task):
    """Tarefa de Processamento Global — equivalente ao comando ``PROC``."""

    def __init__ (self,
            floorPlan:         int = 2,
            floorDraw:         int = 0,
            slabs:             int = 0,
            beams:             int = 1,
            columnsData:       int = 1,
            columns:           int = 0,
            columnsReport:     int = 1,
            gridModel:         int = 1,
            gridDraw:          int = 1,
            gridExtr:          int = 1,
            gridAnalysis:      int = 1,
            gridBeamsTrnsf:    int = 0,
            gridSlabsTrnsf:    int = 1,
            gridNonLinear:     int = 0,
            frameModel:        int = 1,
            frameAnalysis:     int = 1,
            frameBeamsTrnsf:   int = 1,
            frameColumnsTrnsf: int = 1,
            foundations:       int = 0,
            stairs:            int = 0,
            fire:              int = 0,
            precastPhases:     int = 0,
            ) -> None:
        """Configura o processamento global conforme parâmetros escolhidos.

        Cada flag aceita valores ``0`` (não executar), ``1`` ou ``2`` conforme
        a etapa. ``2`` em geral significa "etapa anterior + desenho".

        Args:
            floorPlan: ``0`` Não / ``1`` Extrair plantas / ``2`` Extrair e processar.
            floorDraw: ``0`` Não / ``1`` Desenhar formas.
            slabs: ``0`` Não / ``1`` Esforços / ``2`` Esforços + desenho.
            beams: ``0`` Não / ``1`` Esforços / ``2`` Dimensionamento + detalhamento / ``3`` + desenho.
            columnsData: ``0`` Não / ``1`` Gravação de dados de pilares.
            columns: ``0`` Não / ``1`` Dimensionamento + detalhamento / ``2`` + desenho.
            columnsReport: ``0`` Não / ``1`` Relatório geral de pilares.
            gridModel: ``0`` Não / ``1`` Geração do modelo de grelha.
            gridDraw: ``0`` Não / ``1`` Desenho de dados de grelha.
            gridExtr: ``0`` Não / ``1`` Extração do desenho de grelha.
            gridAnalysis: ``0`` Não / ``1`` Análise de esforços de grelha.
            gridBeamsTrnsf: ``0`` Não / ``1`` Transferência de esforços para vigas.
            gridSlabsTrnsf: ``0`` Não / ``1`` Transferência de esforços para lajes.
            gridNonLinear: ``0`` Não / ``1`` Análise não linear.
            frameModel: ``0`` Não / ``1`` Geração do modelo de pórtico.
            frameAnalysis: ``0`` Não / ``1`` Análise de esforços do pórtico.
            frameBeamsTrnsf: ``0`` Não / ``1`` Transferência para vigas.
            frameColumnsTrnsf: ``0`` Não / ``1`` Transferência para pilares.
            foundations: ``0`` Não / ``1`` Dimensionamento + detalhamento / ``2`` + desenho.
            stairs: ``0`` Não / ``1`` Dimensionamento, detalhamento e desenho.
            fire: ``0`` Não / ``1`` Verificação a incêndio.
            precastPhases: ``0`` Não / ``1`` Pré-moldados — todas as etapas construtivas.
        """
        super().__init__()
        self.m_itask         = self.TASK_GLOBALPROC
        self.m_floorPlan       = floorPlan
        self.m_floorDraw       = floorDraw
        self.m_slabs           = slabs
        self.m_beams           = beams
        self.m_columnsData     = columnsData
        self.m_columns         = columns
        self.m_columnsReport   = columnsReport
        self.m_gridModel       = gridModel
        self.m_gridDraw        = gridDraw
        self.m_gridExtr        = gridExtr
        self.m_gridAnalysis    = gridAnalysis
        self.m_gridBeamsTrnsf  = gridBeamsTrnsf
        self.m_gridSlabsTrnsf  = gridSlabsTrnsf
        self.m_gridNonLinear   = gridNonLinear
        self.m_frameModel      = frameModel
        self.m_frameAnalysis   = frameAnalysis
        self.m_frameBeamsTrnsf = frameBeamsTrnsf
        self.m_frameColumnsTrnsf=frameColumnsTrnsf
        self.m_foundations     = foundations
        self.m_stairs          = stairs
        self.m_fire            = fire
        self.m_precastPhases   = precastPhases

    def Script (self) -> str:
        """Retorna o script ``PROC ...`` consolidado para o gerenciador."""
        # Comando-raiz do processamento global; sub-comandos são acrescentados em sequência.
        script          =  "PROC"                                               #!NTR
        # Blocos sempre presentes — formas, lajes, vigas, pilares, grelhas, pórtico e fundações.
        script          += " FORMAS %d %d" % (self.m_floorPlan, self.m_floorDraw)#!NTR
        script          += " LAJES %d" % (self.m_slabs)                         #!NTR
        script          += " VIGAS %d" % (self.m_beams)                         #!NTR
        script          += " PILARES %d %d %d" % (self.m_columnsData, self.m_columns, #!NTR
                             self.m_columnsReport)
        script          += " GRELHAS %d %d %d %d %d %d %d" % (                  #!NTR
                            self.m_gridModel, self.m_gridDraw,
                            self.m_gridExtr, self.m_gridAnalysis, self.m_gridBeamsTrnsf,
                            self.m_gridSlabsTrnsf, self.m_gridNonLinear)
        script          += " PORTICO %d %d %d %d" % (self.m_frameModel, self.m_frameAnalysis, #!NTR
                            self.m_frameBeamsTrnsf, self.m_frameColumnsTrnsf)
        script          += " FUNDAC %d" % (self.m_foundations)                  #!NTR
        # Sub-comandos opcionais — só aparecem na linha quando a flag correspondente for não-zero.
        if              (self.m_stairs != 0):
            script      += " ESCADAS"                                           #!NTR
        if              (self.m_fire != 0):
            script      += " INCENDIO"                                          #!NTR
        if              (self.m_precastPhases != 0):
            script      += " ETAPAS"                                            #!NTR
        return          script


#-----------------------------------------------------------------------------
#       Planta de cargas
#
class TaskLoadsReport (Task):
    """Tarefa que gera a planta de cargas ``PORLID.DWG``."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de planta de cargas."""
        super().__init__()
        self.m_itask         = self.TASK_LOADSREPORT

    def Script (self) -> str:
        """Retorna o script ``PORLID`` para o gerenciador."""
        script          = "PORLID"                                        #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Desenho de lajes
#
class TaskSlabDrawings (Task):
    """Tarefa de desenhos de lajes (ferros e faixas)."""

    def __init__ (self,
        rebartop:    int = 1,
        rebarbot:    int = 1,
        rebarpunch:  int = 1,
        rebarshear:  int = 1,
        forcestop:   int = 1,
        forcesbot:   int = 1,
        forcespunch: int = 1,
        forcesshear: int = 1
            ) -> None:
        """Configura quais desenhos de lajes serão gerados.

        Args:
            rebartop: ``0`` Não / ``1`` Ferros positivos.
            rebarbot: ``0`` Não / ``1`` Ferros negativos.
            rebarpunch: ``0`` Não / ``1`` Ferros de punção.
            rebarshear: ``0`` Não / ``1`` Ferros de cisalhamento.
            forcestop: ``0`` Não / ``1`` Faixas positivas.
            forcesbot: ``0`` Não / ``1`` Faixas negativas.
            forcespunch: ``0`` Não / ``1`` Faixas de punção.
            forcesshear: ``0`` Não / ``1`` Faixas de cisalhamento.
        """
        super().__init__()
        self.m_itask            = self.TASK_SLABDRAWINGS
        self.m_rebartop         = rebartop
        self.m_rebarbot         = rebarbot
        self.m_rebarpunch       = rebarpunch
        self.m_rebarshear       = rebarshear
        self.m_forcestop        = forcestop
        self.m_forcesbot        = forcesbot
        self.m_forcespunch      = forcespunch
        self.m_forcesshear      = forcesshear

    def Script (self) -> str:
        """Retorna o script ``DESLAJ ...`` para o gerenciador."""
        # Compõe DESLAJ com os 8 flags de desenho na ordem ferros (top/bot/punch/shear)
        # seguidos das faixas de esforços (top/bot/punch/shear).
        script          = "DESLAJ %d %d %d %d %d %d %d %d" % (           #!NTR
                         self.m_rebartop, self.m_rebarbot, self.m_rebarpunch,
                         self.m_rebarshear, self.m_forcestop,
                         self.m_forcesbot, self.m_forcespunch, self.m_forcesshear)
        return          script

#-----------------------------------------------------------------------------
#       Desenho de lajes treliçadas
#
class TaskLatticeSlabs (Task):
    """Tarefa de desenhos de lajes treliçadas."""

    def __init__ (self,
        latticeList:  int = 1,
        latticeBeams: int = 1,
        rebarList:    int = 1,
        fillingList:  int = 1
            ) -> None:
        """Configura desenhos de lajes treliçadas.

        Args:
            latticeList: ``0`` Não / ``1`` Tabela de vigotas treliçadas.
            latticeBeams: ``0`` Não / ``1`` Planta de fabricação de vigotas.
            rebarList: ``0`` Não / ``1`` Tabela de ferros complementares.
            fillingList: ``0`` Não / ``1`` Tabela de enchimentos.
        """
        super().__init__()
        self.m_itask            = self.TASK_LATTICESLABS
        self.m_latticeList      = latticeList
        self.m_latticeBeams     = latticeBeams
        self.m_rebarList        = rebarList
        self.m_fillingList      = fillingList

    def Script (self) -> str:
        """Retorna o script ``DESLAJTRE ...`` para o gerenciador."""
        script          = "DESLAJTRE %d %d %d %d" % (                    #!NTR
                         self.m_latticeList, self.m_latticeBeams,
                         self.m_rebarList, self.m_fillingList)
        return          script

#-----------------------------------------------------------------------------
#       Desenho de lajes mistas nervuradas
#
class TaskCompositeSlabs (Task):
    """Tarefa de desenhos de lajes mistas nervuradas."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de lajes mistas nervuradas."""
        super().__init__()
        self.m_itask         = self.TASK_COMPOSITESLABS


    def Script (self) -> str:
        """Retorna o script ``DESLAJMISNER`` para o gerenciador."""
        script          = "DESLAJMISNER"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Tabela de ferros com todos os desenhos
#
class TaskRebarSchedule (Task):
    """Tarefa que gera a tabela consolidada de ferros do edifício."""

    def __init__ (self) -> None:
        """Inicializa a tabela de ferros (todos os desenhos de armadura)."""
        super().__init__()
        self.m_itask         = self.TASK_REBARSCHEDULE

    def Script (self) -> str:
        """Retorna o script ``TABFERTODOSDWG`` para o gerenciador."""
        script          = "TABFERTODOSDWG"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Processamento de escadas
#
class TaskStairs (Task):
    """Tarefa de dimensionamento, detalhamento e desenho de escadas."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de escadas."""
        super().__init__()
        self.m_itask         = self.TASK_STAIRS

    def Script (self) -> str:
        """Retorna o script ``ESCADAS`` para o gerenciador."""
        script          = "ESCADAS"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Desenho de formas
#
class TaskFloorPlanDrawings (Task):
    """Tarefa de desenho de formas."""

    def __init__ (self,
            floor:     int = 1,
            columns:   int = 1,
            slabs:     int = 1,
            slabsDims: int = 1,
            beams:     int = 1,
            loads:     int = 1,
            sections:  int = 1
            ) -> None:
        """Configura desenhos de formas.

        Args:
            floor: ``0`` Não / ``1`` Planta de formas.
            columns: ``0`` Não / ``1`` Planta de pilares.
            slabs: ``0`` Não / ``1`` Verificação de nós de lajes.
            slabsDims: ``0`` Não / ``1`` Verificação de medidas de lajes.
            beams: ``0`` Não / ``1`` Nós e cargas em vigas.
            loads: ``0`` Não / ``1`` Cargas em lajes.
            sections: ``0`` Não / ``1`` Cortes do edifício.
        """
        super().__init__()
        self.m_itask            = self.TASK_FLOORPLANDRAWINGS
        self.m_floor            = floor
        self.m_columns          = columns
        self.m_slabs            = slabs
        self.m_slabsDims        = slabsDims
        self.m_beams            = beams
        self.m_loads            = loads
        self.m_sections         = sections

    def Script (self) -> str:
        """Retorna o script ``DESFOR ...`` para o gerenciador."""
        # Compõe DESFOR com os 7 flags de desenho na ordem: forma, pilares, lajes,
        # medidas de lajes, vigas, cargas e cortes.
        script          = "DESFOR %d %d %d %d %d %d %d" % (                              #!NTR
                         self.m_floor, self.m_columns, self.m_slabs, self.m_slabsDims,
                         self.m_beams, self.m_loads, self.m_sections)
        return          script

#-----------------------------------------------------------------------------
#       Desenhos de pré-moldados
#
class TaskPreCastDrawings (Task):
    """Tarefa de desenho de pré-moldados."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de desenhos de pré-moldados."""
        super().__init__()
        self.m_itask         = self.TASK_PRECASTDRAWINGS

    def Script (self) -> str:
        """Retorna o script ``DESPRE`` para o gerenciador."""
        script          = "DESPRE"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Transferência de esforços para cálculo de vigas pré-moldadas
#
class TaskPreCastBeams (Task):
    """Tarefa de transferência de esforços para vigas pré-moldadas."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de transferência para vigas pré-moldadas."""
        super().__init__()
        self.m_itask         = self.TASK_PRECASTBEAMS

    def Script (self) -> str:
        """Retorna o script ``TRNPREVIG`` para o gerenciador."""
        script          = "TRNPREVIG"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Transferência de esforços para cálculo de fundações pré-moldadas
#
class TaskPreCastFoundations (Task):
    """Tarefa de transferência de esforços para fundações pré-moldadas."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de transferência para fundações pré-moldadas."""
        super().__init__()
        self.m_itask         = self.TASK_PRECASTFOUNDATIONS

    def Script (self) -> str:
        """Retorna o script ``TRNPREFUN`` para o gerenciador."""
        script          = "TRNPREFUN"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Dimensionamento, detalhamento e desenho de pilares pré-moldados
#
class TaskPreCastColumns (Task):
    """Tarefa de pilares pré-moldados (dimensionamento + detalhamento + desenho)."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de pilares pré-moldados."""
        super().__init__()
        self.m_itask         = self.TASK_PRECASTCOLUMNS

    def Script (self) -> str:
        """Retorna o script ``DIMPILPRE`` para o gerenciador."""
        script          = "DIMPILPRE"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Processamento de consolos pré-moldaddos
#
class TaskPreCastCorbels (Task):
    """Tarefa de consolos pré-moldados (dimensionamento + detalhamento + desenho)."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de consolos pré-moldados."""
        super().__init__()
        self.m_itask         = self.TASK_PRECASTCORBELS

    def Script (self) -> str:
        """Retorna o script ``DIMCONPRE`` para o gerenciador."""
        script          = "DIMCONPRE"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Quantitativos de pré-moldados
#
class TaskPreCastMaterials (Task):
    """Tarefa de quantitativos de pré-moldados."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de quantitativos de pré-moldados."""
        super().__init__()
        self.m_itask         = self.TASK_PRECASTMATERIALS

    def Script (self) -> str:
        """Retorna o script ``QUANTPRE`` para o gerenciador."""
        script          = "QUANTPRE"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Resumo Estutural
#
class TaskStructuralReport (Task):
    """Tarefa que gera o Resumo Estrutural."""

    def __init__ (self) -> None:
        """Inicializa a tarefa de Resumo Estrutural."""
        super().__init__()
        self.m_itask         = self.TASK_STRUCTURALREPORT

    def Script (self) -> str:
        """Retorna o script ``RESEST`` para o gerenciador."""
        script          = "RESEST"                                #!NTR
        return          script

#-----------------------------------------------------------------------------
#       Classe que controla a excecução do TQS com o script fornecido
#
class Job ():
    """Controla a execução do TQS em batch a partir de um script de tarefas.

    Acumula objetos :class:`Task` em :attr:`listaexec`, gera o arquivo
    ``GERENCIADOR.DAT`` com os scripts e dispara ``TQS.EXE``.

    Attributes:
        listaexec: Lista de tarefas acumuladas.
    """

    def __init__ (self) -> None:
        """Inicializa um job vazio."""
        self.listaexec = []

    def EnterTask (self, task: "Task") -> None:
        """Acumula uma tarefa para execução.

        Args:
            task: Instância de :class:`Task` (ou subclasse).
        """
        self.listaexec.append (task)

    def Execute (self) -> None:
        """Executa as tarefas acumuladas: grava ``GERENCIADOR.DAT`` e chama TQS.

        Cada tarefa contribui com o resultado de :meth:`Task.Script` para o
        arquivo de comandos. O programa ``TQS.EXE -RLST -CMD:GERENCIADOR.DAT``
        é então acionado via :func:`TQSUtil.ExecTqs`.
        """
        # Nome fixo do arquivo de comandos esperado pelo TQS.EXE.
        nomarq          = "GERENCIADOR.DAT"
        # Serializa cada Task como uma linha de comando da DSL do gerenciador.
        file            = open(nomarq, 'w')
        for              task in self.listaexec:
            file.write  ("%s\n" % task.Script ())
        file.close      ()
        # Dispara o TQS em modo batch lendo o lote recém-gravado (-RLST registra log).
        command         = "TQS.EXE -RLST -CMD:" + nomarq
        TQSUtil.ExecTqs (command)
