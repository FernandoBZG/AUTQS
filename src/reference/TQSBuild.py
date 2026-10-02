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
#       TQSBuild.py     Leitura e gravação de dados de edifício TQS
#                       Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import ctypes, os
from typing import Tuple

import TQS.TQSUtil
from pathlib import Path

#-----------------------------------------------------------------------------
#
#    Tipos de pórtico
#
PORTICO_INDEF:          int = 0             # (I)   Modelo indefinido
PORTICO_NAO:            int = 1             # (II)  Não calcula
PORTICO_HOR:            int = 2             # (III) Somente para esforços horizontais
PORTICO_HORVER:         int = 3             # (IV)  Esforços horizontais e verticais + flexibilização
PORTICO_CONJUN:         int = 4             # (V)   Modelo articulado/engastado
PORTICO_LAJES:          int = 5             # (VI)  Com subestruturas de lajes e flexibilização
#
#       Tipos de grelha
#
GRELHA_INDEF:           int = 0             # Indefinido
GRELHA_VIGAS:           int = 1             # Vigas contínuas
GRELHA_LAJNER:          int = 2             # Grelha de lajes nervuradas
GRELHA_LAJPLA:          int = 3             # Grelha de laje plana
GRELHA_GREVIG:          int = 4             # Grelha só de vigas
GRELHA_PLACAS:          int = 5             # Grelha de laje plana de placa
GRELHA_AUTOMA:          int = 6             # Automático: Nervurada ou Plana
#
#       Classe de planta
#
ICLFUN:                 int = 1             # Fundação
ICLSUB:                 int = 2             # Subsolo
ICLTER:                 int = 3             # Térreo
ICLMEZ:                 int = 4             # Mezzanino
ICLTRN:                 int = 5             # Transição
ICLPRI:                 int = 6             # Primeiro
ICLTIP:                 int = 7             # Tipo
ICLCOB:                 int = 8             # Cobertura
ICLATI:                 int = 9             # Ático
ICLDUP:                 int = 10            # Duplex
ICLTRI:                 int = 11            # Triplex
#
#       Etapas construtivas
#
PISOINDEF:              int = -1            # Sem definição de piso
#
#        Normas de alvenaria estrutural
#
NORMALVS_10837:         str = "NBR 10837 : 1989 - Blocos vazados de Concreto"#!NTR
NORMALVI_10837:         int = 0
NORMALVS_15961:         str = "NBR 15961-1 : 2011 - Blocos de Concreto"#!NTR
NORMALVI_15961:         int = 1
NORMALVS_15812:         str = "NBR 15812-1 : 2010 - Blocos Cerâmicos"#!NTR
NORMALVI_15812:         int = 2
NORMALVS_16868:         str = "NBR 16868-1 : 2020 - Blocos de Concreto e Cerâmicos"#!NTR
NORMALVI_16868:         int = 3
#
#       Materiais de alvenaria estrutural
#
MATRALVS_CONVAZ:        str = "Blocos vazados de CONCRETO"
MATRALVI_CONVAZ:        int = 0
MATRALVS_CONMAC:        str = "Blocos maciços de CONCRETO"
MATRALVI_CONMAC:        int = 1
MATRALVS_CERVAZ:        str = "Blocos CERÂMICOS vazados"
MATRALVI_CERVAZ:        int = 2
MATRALVS_CERMAC:        str = "Blocos CERÂMICOS maciços"
MATRALVI_CERMAC:        int = 3
MATRALVS_SILVAZ:        str = "Blocos SILICO-CALCÁREOS vazados"
MATRALVI_SILVAZ:        int = 4
MATRALVS_SILMAC:        str = "Blocos SILICO-CALCÁREOS maciços"
MATRALVI_SILMAC:        int = 5
MATRALVS_OUTROS:        str = "Outro (Bloco/Tijolo)"
MATRALVI_OUTROS:        int = 6
#
#        Normas de paredes de concreto
#
NORMAPAREDS_NBR16055:   str = "NBR 16055:2012 - Paredes de Concreto"
NORMAPAREDI_NBR16055:   int = 0
#
#        Normas de concreto armador
#
NORMA_INDEF:            int = 0
SNORMA_INDEF:           str = "Norma indefinida"

NORMA_NB1_78:           int = 1
SNORMA_NB1_78:          str = "NB1-78"                      #!NTR
ANORMA_NB1_78:          str = "NB1-78"                      #!NTR

NORMA_NBR_6118_2003:    int = 2
SNORMA_NBR_6118_2003:   str = "NBR-6118:2003"               #!NTR
ANORMA_NBR_6118_2003:   str = "NBR-6118-2003"               #!NTR

NORMA_NBR_6118_2014:    int = 3
SNORMA_NBR_6118_2014:   str = "NBR-6118:2014"               #!NTR
ANORMA_NBR_6118_2014:   str = "NBR-6118-2014"               #!NTR

NORMA_CIRSOC:           int = 4
SNORMA_CIRSOC:          str = "CIRSOC-2005"                #!NTR
ANORMA_CIRSOC:          str = "CIRSOC-2005"                #!NTR

NORMA_ACI_318_05:       int = 5
SNORMA_ACI_318_05:      str = "ACI-318-05"                 #!NTR
ANORMA_ACI_318_05:      str = "ACI-318-05"                 #!NTR

NORMA_ACI_318_14:       int = 6
SNORMA_ACI_318_14:      str = "ACI-318-14"                 #!NTR
ANORMA_ACI_318_14:      str = "ACI-318-14"                 #!NTR
#
#        Países para escolha de isopletas e mapa de sismo
#
PAIS_INDEF:             int = 0
PAIS_BRASIL:            int = 1
PAIS_ARGENTINA:         int = 2
PAIS_COLOMBIA:          int = 3
PAIS_BOLIVIA:           int = 4
PAIS_EUA:               int = 5
PAIS_PARAGUAI:          int = 6
#
#        Classes de agressividade ambiental CIRSOC
#
CLAGCIRSOC_A1:          int = 0             # Não agressiva
CLAGCIRSOC_A2:          int = 1             # Moderada
CLAGCIRSOC_A3:          int = 2             # Quente úmido
CLAGCIRSOC_CL:          int = 3             # Submerso
CLAGCIRSOC_M1:          int = 4             # Marinho 1
CLAGCIRSOC_M2:          int = 5             # Marinho 2
CLAGCIRSOC_M3:          int = 6             # Marinho 3
CLAGCIRSOC_C1:          int = 7             # Gelo e degelo 1
CLAGCIRSOC_C2:          int = 8             # Gelo e degelo 2
CLAGCIRSOC_Q1:          int = 9             # Agressividade química 1
CLAGCIRSOC_Q2:          int = 10            # Agressividade química 2
CLAGCIRSOC_Q3:          int = 11            # Agressividade química 3
#
#        Classes de protensão CIRSOC
#
CLPRCIRSOC_FTU:         int = 0             # Ft <= 0.7xSQRT (F'c)
CLPRCIRSOC_FTT:         int = 1             # 0.7xSQRT (F'c) < Ft <= SQRT (F'c)
CLPRCIRSOC_FTC:         int = 2             # Ft > SQRT (F'c)
#
#        Prefixos de cargas
#
PREFIXOTODAS:           str = "TODAS"      #!NTR Todas verticais
PREFIXOPP:              str = "PP"         #!NTR Peso Próprio
PREFIXOPERM:            str = "PERM"       #!NTR Cargas permanentes
PREFIXOACID:            str = "ACID"       #!NTR Cargas acidentais
PREFIXOEMPU:            str = "EMPU"       #!NTR Empuxo
PREFIXORETR:            str = "RETR"       #!NTR Retração
PREFIXOSISM:            str = "SISM"       #!NTR Sismo
PREFIXOTEMP:            str = "TEMP"       #!NTR Temperatura
PREFIXOVENT:            str = "VENT"       #!NTR Vento
PREFIXODESA:            str = "DESA"       #!NTR Desaprumo
PREFIXOHIPER:           str = "HIPER"      #!NTR Hiperestático de protensão
PREFIXOFORALI:          str = "FORALI"     #!NTR Forças de alívio de protenção
PREFIXOADIC:            str = "ADI"        #!NTR Cargas adicionais do usuário
PREFIXOGELO:            str = "GELO"       #!NTR Gelo
PREFIXOFLUI:            str = "FLUI"       #!NTR Pressão de fluídos
PREFIXOENCH:            str = "ENCH"       #!NTR Cargas de enchente
PREFIXOTELH:            str = "TELH"       #!NTR Cargas acidentais em telhado
PREFIXOCHUV:            str = "CHUV"       #!NTR Chuva
PREFIXONEVE:            str = "NEVE"       #!NTR Neve
PREFIXOVEGE:            str = "VEGE"       #!NTR Vento sobre gelo
#
#      Variáveis de EDILIB
#
#      Variáveis DOUBLE da estrutura EDIFICIO
#
EDL_V_COTIED:               str = "cotied"                #!NTR Cota inicial
EDL_V_FCKVED:               str = "fckved"                #!NTR FCK das vigas, quando definida
EDL_V_FCKFED:               str = "fckfed"                #!NTR FCK das fundações
EDL_V_FCKPDF:               str = "fckpdf"                #!NTR Fck default de pilar
EDL_V_PONDACID:             str = "pondacid"              #!NTR Ponderação de carga acidental secundária
EDL_V_ESACED:               str = "esaced"                #!NTR Estimativa carga acidental/total
EDL_V_VMULETR:              str = "vmuletr"               #!NTR Multiplicador de inércia de vigas de transição
EDL_V_REDTORVTRN:           str = "redtorvtrn"            #!NTR Redutor torção viga transição enrijecida
EDL_V_PONDMASPP:            str = "pondmaspp"             #!NTR Ponderador de massa p/PP
EDL_V_PONDMASPERM:          str = "pondmasperm"           #!NTR Ponderador de massa p/Permanentes
EDL_V_PONDMASSOBR:          str = "pondmassobr"           #!NTR Ponderador de massa p/sobrecargas
EDL_V_TAXAMORANADIM:        str = "taxamoranadim"         #!NTR Taxa amortecimento p/anális dinâmica
EDL_V_BITARMMAXVIGPIL:      str = "bitarmmaxvigpil"       #!NTR bitola máxima vigas/pilares mm
EDL_V_BITARMMAXLAJ:         str = "bitarmmaxlaj"          #!NTR bitola máxima lajes mm
EDL_V_ALTBAINHAMAX:         str = "altbainhamax"          #!NTR Altura máxima bainha protensão mm
EDL_V_COBRVIG:              str = "cobrvig"               #!NTR Cobrimento cm vigas
EDL_V_COBRPIL:              str = "cobrpil"               #!NTR Cobrimento cm pilares
EDL_V_COBRFUND:             str = "cobrfund"              #!NTR Cobrimento cm fundações
EDL_V_COBRFUNDSEC:          str = "cobrfundsec"           #!NTR Cobrimento cm fundações adic secund (<0)sec princ
EDL_V_COBRLAJINF:           str = "cobrlajinf"            #!NTR Cobrimento cm laje inferior
EDL_V_COBRLAJSUP:           str = "cobrlajsup"            #!NTR Cobrimento cm laje superior
EDL_V_COBRLAJSECINF:        str = "cobrlajsecinf"         #!NTR Cobrimento cm laje secundário inf
EDL_V_COBRLAJSECSUP:        str = "cobrlajsecsup"         #!NTR Cobrimento cm laje secundário sup
EDL_V_COBRPROINF:           str = "cobrproinf"            #!NTR Cobrimento cm protend inferior
EDL_V_COBRPROSUP:           str = "cobrprosup"            #!NTR Cobrimento cm protend superior
EDL_V_COBRPROSEC:           str = "cobrprosec"            #!NTR Cobrimento cm protend secundário
EDL_V_COBRVLJSOL:           str = "cobrvljsol"            #!NTR Cobrimento cm vigas/lajes contato c/solo
EDL_V_COBRPILSOL:           str = "cobrpilsol"            #!NTR Cobrimento cm pilares contato c/solo
EDL_V_PRECOBRVIG:           str = "precobrvig"            #!NTR Cobrimento cm vigas pré-mold
EDL_V_PRECOBRPIL:           str = "precobrpil"            #!NTR Cobrimento cm pilares pré-mold
EDL_V_PRECOBRFUND:          str = "precobrfund"           #!NTR Cobrimento cm fundações pré-mold
EDL_V_PRECOBRFUNDSEC:       str = "precobrfundsec"        #!NTR Cobrimento cm adic secund (<0) princip
EDL_V_PRECOBRLAJINF:        str = "precobrlajinf"         #!NTR Cobrimento cm laje inferior
EDL_V_PRECOBRLAJSUP:        str = "precobrlajsup"         #!NTR Cobrimento cm laje superior
EDL_V_PRECOBRLAJSECINF:     str = "precobrlajsecinf"      #!NTR Cobrimento cm adic secund inf
EDL_V_GAMAFREF:             str = "gamafref"              #!NTR GamaF de referência
EDL_V_GAMAF3:               str = "gamaf3"                #!NTR GamaF3 (parte do GamaF)
EDL_V_GAMAFCONSTR:          str = "gamafconstr"           #!NTR GamaF construtivo pré-moldados
EDL_V_ANGTUNVEN:            str = "angtunven"             #!NTR Ângulo de incidência graus
EDL_V_ALARGFRONT:           str = "alargfront"            #!NTR Largura frontal estimada (m) p/vento
EDL_V_COMPRLATER:           str = "comprlater"            #!NTR Comprimento lateral estimado (m) p/vento
EDL_V_ALTURVENTO:           str = "alturvento"            #!NTR Altura estimada sujeita a vento, (m)
EDL_V_TRRF:                 str = "trrf"                  #!NTR TRRF Incêndio 30/60/90/120 padrão 120
EDL_V_CIRSOC_V0:            str = "cirsoc_v0"             #!NTR CIRSOC Velocidade básica de vento (m/s)
EDL_V_CIRSOC_FREQNAT:       str = "cirsoc_freqnat"        #!NTR CIRSOC Frequência natural Hz (iflex != 0)
EDL_V_CIRSOC_TXAMORT:       str = "cirsoc_txamort"        #!NTR CIRSOC Taxa amortecimento % valor crítico (iflex != 0)
EDL_V_CIRSOC_AKZT:          str = "cirsoc_akzt"           #!NTR CIRSOC Fator topográfico Kzt
EDL_V_CIRSOC_PMINTFM2:      str = "cirsoc_pmintfm2"       #!NTR CIRSOC Pressão mínima de vento, tf/m2
EDL_V_CIRSOC_COBRNPREXPL:   str = "cirsoc_cobrnprexpl"    #!NTR CIRSOC Cobrimento cm lajes ñ prot exposto
EDL_V_CIRSOC_COBRVLJSOLPRO: str = "cirsoc_cobrvljsolpro"  #!NTR CIRSOC Cobrimento cm lajes prot contato c/solo
EDL_V_CIRSOC_COBRPROEXPLAJE: str = "cirsoc_cobrproexplaje" #!NTR CIRSOC Cobrimento cm lajes prot exposto
EDL_V_CIRSOC_COBRNPRLJSOLV: str = "cirsoc_cobrnprljsolv"  #!NTR CIRSOC Cobrimento cm vigas contato c/solo
EDL_V_CIRSOC_COBRNPREXPV:   str = "cirsoc_cobrnprexpv"    #!NTR CIRSOC Cobrimento cm vigas ñ prot exposto
EDL_V_CIRSOC_COBRPREEXPV:   str = "cirsoc_cobrpreexpv"    #!NTR CIRSOC Cobrimento cm vigas pré-mold exposto
EDL_V_CIRSOC_COBRNPREXPP:   str = "cirsoc_cobrnprexpp"    #!NTR CIRSOC Cobrimento cm pilar ñ prot exposto
EDL_V_CIRSOC_COBRPREEXPP:   str = "cirsoc_cobrpreexpp"    #!NTR CIRSOC Cobrimento cm pilar pré-mold exposto
EDL_V_ACI_PONDCARACI:       str = "aci_pondcaraci"        #!NTR CIRSOC Ponderador de carga acidental
EDL_V_ACI_PONDNEVE:         str = "aci_pondneve"          #!NTR CIRSOC Ponderador de neve
EDL_V_EXCVENPERC:           str = "excvenperc"            #!NTR Valor da excentricidade %
EDL_V_ALTITMAR:             str = "altitmar"              #!NTR Classe CLAGACI19_xxxxx
#
#      Variáveis INT da estrutura EDIFICIO
#
EDL_V_NPRJED:           str = "nprjed"                   #!NTR Número do projeto
EDL_V_IPISED:           str = "ipised"                   #!NTR Piso inicial do edifúcio
EDL_V_IATIED:           str = "iatied"                   #!NTR Piso ativo inicial (-1) todos
EDL_V_IATFED:           str = "iatfed"                   #!NTR Piso ativo final   (-1) todos
EDL_V_NUPLED:           str = "nupled"                   #!NTR Número total de plantas
EDL_V_ICRMED:           str = "icrmed"                   #!NTR (1) Projeto com formas de madeira
EDL_V_IALVENED:         str = "ialvened"                 #!NTR (0)Concreto (1)Alvenaria (2)Parede de concreto
EDL_V_IMODELED:         str = "imodeled"                 #!NTR (0) EG Formas (1) Modelador
EDL_V_IENVTED:          str = "ienvted"                  #!NTR (1) Se envoltória viga transição
EDL_V_IPORED:           str = "ipored"                   #!NTR Modelo PORTICO_xxxx (ACESSOL.H)
EDL_V_NFCVED:           str = "nfcved"                   #!NTR Numero de variações de FCK de pilar
EDL_V_IGRVFCKV:         str = "igrvfckv"                 #!NTR (0) Grava fck vigas (1) não
EDL_V_IGRVFCKF:         str = "igrvfckf"                 #!NTR (0) Grava fck fundac(1) não
EDL_V_IGRVFCKP:         str = "igrvfckp"                 #!NTR (0) Grava fck pilar (1) não
EDL_V_IACIED:           str = "iacied"                   #!NTR (0) Não (1) separa acident
EDL_V_IREDACID:         str = "iredacid"                 #!NTR (1) Se redução de sobrecargas
EDL_V_ICLAGRESS:        str = "iclagress"                #!NTR Classe de agressividade I..IV
EDL_V_ICLIMASECO:       str = "iclimaseco"               #!NTR (1) Se clima seco
EDL_V_ICONTROLQUAL:     str = "icontrolqual"             #!NTR (1) Se controle de qualidade
EDL_V_ICONCRPROT:       str = "iconcrprot"               #!NTR (1) Se concreto para protensão
EDL_V_NUMMODOSLAJES:    str = "nummodoslajes"            #!NTR Número de modos de vibração de lajes
EDL_V_NUMMODOSMODVI:    str = "nummodosmodvi"            #!NTR Número de modos de vibração Modelo VI
EDL_V_ITIPOMATMAS:      str = "itipomatmas"              #!NTR Tipo da matriz de massa
EDL_V_IHIPERPOR:        str = "ihiperpor"                #!NTR Hiperestático no pórtico (0) sim (1) não
EDL_V_IFCKTAB:          str = "ifcktab"                  #!NTR (1) Se fck tabelado c/título
EDL_V_NFCVED_TIT:       str = "nfcved_tit"               #!NTR Número de variações de FCK tabelado de pilar
EDL_V_IPDELTA:          str = "ipdelta"                  #!NTR (0)padrão (1)não (2)p-delta
EDL_V_ICALCPDELTA:      str = "icalcpdelta"              #!NTR (1) se p-delta escolhido
EDL_V_ICLACARACID:      str = "iclacaracid"              #!NTR Classe de carga acidental (0)não (1)leve (2)média (3)pesada
EDL_V_IDESATIVARVERFCK: str = "idesativarverfck"         #!NTR (1) p/desativar verificação do fck mínimo
EDL_V_IDESATIVARVERCOBR: str = "idesativarvercobr"        #!NTR (1) p/desativar verificação do cobrimento mínimo
EDL_V_IDINAMICAPOR:     str = "idinamicapor"             #!NTR (1) p/análise dinâmica pórtico
EDL_V_ICASOVENTOFOR:    str = "icasoventofor"            #!NTR (1) p/vento na planta de formas
EDL_V_IDUASTOUJUNTA:    str = "iduastoujunta"            #!NTR (1) Se duas torres ou junta
EDL_V_ISISGLOB:         str = "isisglob"                 #!NTR (1) Túnel de vento: Se sistema global
EDL_V_INVERTSN:         str = "invertsn"                 #!NTR (1) Túnel de vento: Se inverter sinal
EDL_V_IDESPCOL:         str = "idespcol"                 #!NTR Túnel de vento: Número de colunas a desprezar
EDL_V_IDESPLIN:         str = "idesplin"                 #!NTR Túnel de vento: Número de linhas a desprezar
EDL_V_IORDPISO:         str = "iordpiso"                 #!NTR Túnel de vento: (1) Se de cima para baixo
EDL_V_IPRIMPIS:         str = "iprimpis"                 #!NTR Túnel de vento: Prim piso da lista ou (-1)
EDL_V_IUNIDKNM:         str = "iunidknm"                 #!NTR Túnel de vento: (1) se KN e KNM
EDL_V_ISISGLOBEXC:      str = "isisglobexc"              #!NTR Túnel de vento: (1) Excen armaz no sist glob
EDL_V_INVERTSNEXC:      str = "invertsnexc"              #!NTR Túnel de vento: (1) Excen armaz c/sinal invr
EDL_V_INTSISES:         str = "intsises"                 #!NTR (1) se interface com SISEs
EDL_V_INTSISESPOR:      str = "intsisespor"              #!NTR (1) somar fund SISEs no TQS
EDL_V_IPREFABVIG:       str = "iprefabvig"               #!NTR (1) viga  pré-fabricada
EDL_V_IPREFABPIL:       str = "iprefabpil"               #!NTR (1) pilar pré-fabricado
EDL_V_IPREFABLAJ:       str = "iprefablaj"               #!NTR (1) laje  pré-fabricada
EDL_V_ITURBULENCIA:     str = "iturbulencia"             #!NTR Vento (0) baixa turbolência (1) alta
EDL_V_INORMALVEN:       str = "inormalven"               #!NTR Norma alvenaria NORMALVI_xxx
EDL_V_IMATRALVEN:       str = "imatralven"               #!NTR Mater alvenaria MATRALVI_xxx
EDL_V_INORMAPAREDE:     str = "inormaparede"             #!NTR Norma de parede NORMAPAREDI_xxxx
EDL_V_IEFEITOINCREM:    str = "iefeitoincrem"            #!NTR (1) Se efeito incremental ativo
EDL_V_IPAIS:            str = "ipais"                    #!NTR PAIS_xxxx
EDL_V_CIRSOC_IFLEX:     str = "cirsoc_iflex"             #!NTR (0) Edifício rígido (1) flexível
EDL_V_CIRSOC_INATUROCUP: str = "cirsoc_inaturocup"        #!NTR Natur de ocup (0)I (1)II (2)III (3)IV
EDL_V_CIRSOC_ICATEXPOSI: str = "cirsoc_icatexposi"        #!NTR Cat exposição (0)A (1)B (2)C (3)D
EDL_V_CIRSOC_ICLAGRESS: str = "cirsoc_iclagress"         #!NTR Classe CLAGCIRSOC_xxxx
EDL_V_CIRSOC_ICLAPROTN: str = "cirsoc_iclaprotn"         #!NTR Classe CLPRCIRSOC_xxxx
EDL_V_ACI_IPONDCARACI:  str = "aci_ipondcaraci"          #!NTR (0)Acima (1)grgem 1.0 (2)Outros 0.5
EDL_V_ACI_IZONAALAGA:   str = "aci_izonaalaga"           #!NTR (0) Costeira (1) Não costeira
EDL_V_ACI_IPONDNEVE:    str = "aci_ipondneve"            #!NTR (0)Acima (1)Não escoa 0.7 (2) Escoa 0.2
EDL_V_IFORCARNORMA:     str = "iforcarnorma"             #!NTR (1) p/forçar cópia de critérios
EDL_V_ITIPOESTPRE:      str = "itipoestpre"              #!NTR (0) Galpão (1) Térreo c/laje
EDL_V_IEXCVEN:          str = "iexcven"                  #!NTR (1) Aplicar excentricidade
EDL_V_ICONSTRHABTER:    str = "iconstrhabter"            #!NTR (0) Não (1) Constr hab tér(2) Um pav+mez (3) Até 4 pav(4) Mais de 4pav
EDL_V_ACI31819_ICLAGRESS: str = "aci31819_iclagress"       #!NTR Classe CLAGACI19_xxxxx

EDL_V_TITEED:           str = "titeed"                   #!NTR Titulo do edificio c/delim
EDL_V_TITGED:           str = "titged"                   #!NTR Titulo geral
EDL_V_CLIGED:           str = "cliged"                   #!NTR Cliente geral
EDL_V_ENDEROBRA:        str = "enderobra"                #!NTR Endereço da obta
EDL_V_PREFEDIPLA:       str = "prefedipla"               #!NTR Prefixo do edif p/plantas
EDL_V_DRPLED:           str = "drpled"                   #!NTR Diretório de pilares
EDL_V_DRGRED:           str = "drgred"                   #!NTR Diretório gerais
EDL_V_DRFUED:           str = "drfued"                   #!NTR Diretório de fundacoes
EDL_V_DRPOED:           str = "drpoed"                   #!NTR Diretório de portico
EDL_V_DRA1ED:           str = "dra1ed"                   #!NTR Diretório adicional 1
EDL_V_DRA2ED:           str = "dra2ed"                   #!NTR Diretório adicional 2
EDL_V_DRA3ED:           str = "dra3ed"                   #!NTR Diretório adicional 3
EDL_V_DRA4ED:           str = "dra4ed"                   #!NTR Diretório adicional 4
EDL_V_DRA5ED:           str = "dra5ed"                   #!NTR Sayeg
EDL_V_DRA6ED:           str = "dra6ed"                   #!NTR Sayeg
EDL_V_DRA7ED:           str = "dra7ed"                   #!NTR Sayeg
EDL_V_DRA8ED:           str = "dra8ed"                   #!NTR Sayeg
EDL_V_DRSISE:           str = "dirsize"                  #!NTR Diretório do SISEs
EDL_V_DRPLOT:           str = "drdirplo"                 #!NTR Diretório de plotagem de plantas
EDL_V_ALVEST:           str = "diralvest"                #!NTR Diretório geral do Alvest
EDL_V_FCKVED_TIT:       str = "fckved_tit"               #!NTR FCK das vigas
EDL_V_FCKFED_TIT:       str = "fckfed_tit"               #!NTR FCK das fundacoes
EDL_V_FCKPDF_TIT:       str = "fckpdf_tit"               #!NTR Fck default de pilar
EDL_V_ARQNORMA:         str = "arqnorma"                 #!NTR Arq de norma, sem path/tipo
EDL_V_NOMARQFX:         str = "nomarqfx"                 #!NTR Arquivo de forças   FX
EDL_V_NOMARQFY:         str = "nomarqfy"                 #!NTR Arquivo de forças   FY
EDL_V_NOMARQMZ:         str = "nomarqmz"                 #!NTR Arquivo de momentos MZ
EDL_V_NOMARQFTV:        str = "nomarqftv"                #!NTR Arquivo FTV
EDL_V_DRPREPIL:         str = "drprepil"                 #!NTR Diretório de pilares pré
EDL_V_DRPREVIG:         str = "drprevig"                 #!NTR Diretório de vigas   pré
EDL_V_DRPRELAJ:         str = "drprelaj"                 #!NTR Diretório de lajes   pré
EDL_V_DRPREPILA:        str = "drprepila"                #!NTR Diretório de pilares pré - Armaduras
EDL_V_DRPREVIGA:        str = "drpreviga"                #!NTR Diretório de vigas   pré - Armaduras
EDL_V_DRPRELAJA:        str = "drprelaja"                #!NTR Diretório de lajes   pré - Armaduras
EDL_V_DRPRECONS:        str = "drprecons"                #!NTR Diretório de consolos pré-moldados
EDL_V_DRPREFUND:        str = "drprefund"                #!NTR Diretório de fundações pré-moldadas
EDL_V_DRPREFACHADA:     str = "drprefachada"             #!NTR Diretório de fachadas pré-moldadas
EDL_V_FCKVIGPRESAQ:     str = "fckvigpresaq"             #!NTR Fck tabelado viga  pré saque
EDL_V_FCKPILPRESAQ:     str = "fckpilpresaq"             #!NTR Fck tabelado pilar pré saque
EDL_V_FCKLAJPRESAQ:     str = "fcklajpresaq"             #!NTR Fck tabelado laje  pré saque
EDL_V_FCKVIGPRELEV:     str = "fckvigprelev"             #!NTR Fck tabelado viga  pré levant
EDL_V_FCKPILPRELEV:     str = "fckpilprelev"             #!NTR Fck tabelado pilar pré levant
EDL_V_FCKLAJPRELEV:     str = "fcklajprelev"             #!NTR Fck tabelado laje  pré levant
EDL_V_FCKFUNPREFIN:     str = "fckfunprefin"             #!NTR Fck tabelado fun pré final
EDL_V_FCKFUNPRESAQ:     str = "fckfunpresaq"             #!NTR Fck tabelado fun pré saque
EDL_V_FCKFUNPRELEV:     str = "fckfunprelev"             #!NTR Fck tabelado fun pré levant
EDL_V_DESCRICAO:        str = "descricao"                #!NTR Descrição do edifício


#------------------------------------------------------------------------------
#       Funções globais, sem edifício aberto
#
def BuildingContext () -> Tuple[int, int, str, str, str, int]:
        """Retorna dados do contexto do edifício na pasta atual.

        Returns:
            Tupla ``(nprjpv, nprjed, nombde, nomedi, nompav, istat)``:

            * ``nprjpv``: número do projeto do pavimento.
            * ``nprjed``: número do projeto do edifício.
            * ``nombde``: nome completo do ``EDIFICIO.BDE``.
            * ``nomedi``: nome do edifício.
            * ``nompav``: nome do pavimento.
            * ``istat``: ``!= 0`` se fora do contexto do edifício.
        """
        # ACLPAV consulta o contexto a partir do diretório corrente (cwd)
        acessol         = TQS.TQSUtil.LoadDll ("ACESSOL.DLL")
        parnprjpv       = ctypes.c_int (0)
        parnprjed       = ctypes.c_int (0)
        parnombde       = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        argfan1         = ctypes.c_int (0)
        parnomedi       = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        argfan2         = ctypes.c_int (0)
        parnompav       = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        argfan3         = ctypes.c_int (0)
        paristat        = ctypes.c_int (0)
        acessol.ACLPAV  (ctypes.byref (parnprjpv), ctypes.byref (parnprjed),
                         parnombde, argfan1, parnomedi, argfan2, parnompav, argfan3,
                         ctypes.byref (paristat))
        nprjpv          = parnprjpv.value
        nprjed          = parnprjed.value
        nombde          = parnombde.value.decode(TQS.TQSUtil.CHARSET)
        nomedi          = parnomedi.value.decode(TQS.TQSUtil.CHARSET)
        nompav          = parnompav.value.decode(TQS.TQSUtil.CHARSET)
        istat           = paristat.value
        return          nprjpv, nprjed, nombde, nomedi, nompav, istat

def BuildingRoot () -> str:
        """Retorna a raiz geral da árvore de edifícios.

        Returns:
            Caminho da pasta raiz geral.
        """
        parraiz         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        argfan          = ctypes.c_int (0)
        acessol         = TQS.TQSUtil.LoadDll ("ACESSOL.DLL")
        acessol.ACLRAIZGERAL (parraiz, argfan);
        raiz            = parraiz.value.decode(TQS.TQSUtil.CHARSET)
        return          raiz

#------------------------------------------------------------------------------
#       Objeto que controla todo o edifício
#
class Building ():
    """Objeto que controla todo o edifício TQS.

    Agrega os sub-objetos de arquivos, projeto, modelo, pavimentos,
    materiais, cobrimentos, cargas e gerenciamento.

    Implementação:
        Esta classe e suas agregadas são wrappers finos sobre as funções C++ exportadas
        por ``NEDILIB.DLL`` (com chamadas eventuais a ``ACESSOL.DLL`` para contexto de
        edifício). O padrão recorrente é: (1) embrulhar parâmetros em ``ctypes.c_int``,
        ``ctypes.c_double`` ou ``ctypes.c_char_p`` (com ``encode`` em :data:`TQSUtil.CHARSET`);
        (2) chamar a função ``EDILIB_*`` apropriada; (3) ler de volta saídas via ``.value``
        e decodificar buffers de string. Os campos da estrutura ``EDIFICIO`` são acessados
        de modo genérico pelos métodos ``_GetVar*`` / ``_SetVar*``, que recebem o nome
        interno da variável (constantes ``EDL_V_*``). Comentários inline são adicionados
        somente onde a lógica foge desse padrão (branches, loops, sequências multi-DLL).

    Attributes:
        m_edilib: Handle de ``NEDILIB.DLL``.
        file: Sub-objeto :class:`File` para leitura/gravação.
        project: Sub-objeto :class:`Project` (aba gerais).
        model: Sub-objeto :class:`Model` (modelo de cálculo).
        floorsplan: Sub-objeto :class:`FloorsPlan` (pavimentos).
        materials: Sub-objeto :class:`Materials` (materiais).
        covers: Sub-objeto :class:`Covers` (cobrimentos).
        loads: Sub-objeto :class:`Loads` (cargas).
        management: Sub-objeto :class:`Management` (gerenciamento).
        m_nomodelo: Nome do modelo "template" cadastrado.
        m_inovo: ``1`` se o edifício é novo, ``0`` se carregado.
        m_imodelo: ``1`` se inicializado a partir de um template, ``0`` caso contrário.
    """

    def __init__ (self, nomodelo: str = "") -> None:
        """Inicializa um edifício, opcionalmente a partir de um modelo cadastrado.

        Args:
            nomodelo: Nome opcional de um modelo "template" cadastrado.
        """
        # Carrega a DLL de edifícios e instancia todos os sub-objetos que compartilham este Building
        self.m_edilib   = TQS.TQSUtil.LoadDll ("NEDILIB.DLL")
        self.file       = File (self)
        self.project    = Project (self)
        self.model      = Model (self)
        self.floorsplan = FloorsPlan (self)
        self.materials  = Materials (self)
        self.covers     = Covers (self)
        self.loads      = Loads (self)
        self.management = Management (self)
        self.m_nomodelo = nomodelo
        self.m_inovo    = 1
        # Sem modelo template: inicializa com defaults; com template: copia valores do modelo cadastrado
        if              (len (nomodelo) == 0):
            self.m_edilib.EDILIB_INICIAR ()
            self.m_imodelo = 0
        else:
            parmodelo   = ctypes.c_char_p (nomodelo.encode(TQS.TQSUtil.CHARSET))
            self.m_edilib.EDILIB_INICIAR_MODELO (parmodelo)
            self.m_imodelo = 1

    def __str__(self) -> str:
        """Retorna uma representação textual do edifício e seus sub-objetos."""
        msg             = "Classe TQSBuild"
        msg             += "\n   self.m_edilib  " + str (self.m_edilib)
        msg             += "\n   self.file      " + str (self.file    )
        msg             += "\n   self.project   " + str (self.project )
        msg             += "\n   self.model     " + str (self.model   )
        msg             += "\n   self.floors    " + str (self.floorsplan)
        msg             += "\n   self.materials " + str (self.materials)
        msg             += "\n   self.covers    " + str (self.covers)
        msg             += "\n   self.loads     " + str (self.loads)
        msg             += "\n   self.management" + str (self.management)
        return          (msg)

    def _GetVarDouble (self, nomvar: str) -> float:
        """Retorna o valor ``double`` de uma variável da estrutura ``EDIFICIO``.

        Args:
            nomvar: Nome interno da variável (constantes ``EDL_V_*``).

        Returns:
            Valor da variável.
        """
        varnomvar       = ctypes.c_char_p (nomvar.encode(TQS.TQSUtil.CHARSET))
        varval          = ctypes.c_double (0.)
        self.m_edilib.EDILIB_GET_EDIF_DOUBLE (varnomvar, ctypes.byref (varval))
        return          varval.value

    def _SetVarDouble (self, nomvar: str, val: float) -> None:
        """Define o valor ``double`` de uma variável da estrutura ``EDIFICIO``.

        Args:
            nomvar: Nome interno da variável (constantes ``EDL_V_*``).
            val: Valor a atribuir.
        """
        varnomvar       = ctypes.c_char_p (nomvar.encode(TQS.TQSUtil.CHARSET))
        varval          = ctypes.c_double (val)
        self.m_edilib.EDILIB_SET_EDIF_DOUBLE (varnomvar, varval)

    def _GetVarInt (self, nomvar: str) -> int:
        """Retorna o valor ``int`` de uma variável da estrutura ``EDIFICIO``.

        Args:
            nomvar: Nome interno da variável (constantes ``EDL_V_*``).

        Returns:
            Valor da variável.
        """
        varnomvar       = ctypes.c_char_p (nomvar.encode(TQS.TQSUtil.CHARSET))
        varival         = ctypes.c_int (0)
        self.m_edilib.EDILIB_GET_EDIF_INT (varnomvar, ctypes.byref (varival))
        return          varival.value

    def _SetVarInt (self, nomvar: str, ival: int) -> None:
        """Define o valor ``int`` de uma variável da estrutura ``EDIFICIO``.

        Args:
            nomvar: Nome interno da variável (constantes ``EDL_V_*``).
            ival: Valor a atribuir.
        """
        varnomvar       = ctypes.c_char_p (nomvar.encode(TQS.TQSUtil.CHARSET))
        varival         = ctypes.c_int (ival)
        self.m_edilib.EDILIB_SET_EDIF_INT (varnomvar, varival)

    def _GetVarStr (self, nomvar: str) -> str:
        """Retorna o valor ``string`` de uma variável da estrutura ``EDIFICIO``.

        Args:
            nomvar: Nome interno da variável (constantes ``EDL_V_*``).

        Returns:
            Valor da variável.
        """
        varnomvar       = ctypes.c_char_p (nomvar.encode(TQS.TQSUtil.CHARSET))
        varstr          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_edilib.EDILIB_GET_EDIF_STR (varnomvar, varstr)
        str             = varstr.value.decode(TQS.TQSUtil.CHARSET)
        return          str

    def _SetVarStr (self, nomvar: str, str: str) -> None:
        """Define o valor ``string`` de uma variável da estrutura ``EDIFICIO``.

        Args:
            nomvar: Nome interno da variável (constantes ``EDL_V_*``).
            str: Valor a atribuir.
        """
        varnomvar       = ctypes.c_char_p (nomvar.encode(TQS.TQSUtil.CHARSET))
        varstr          = ctypes.c_char_p (str.encode(TQS.TQSUtil.CHARSET))
        self.m_edilib.EDILIB_SET_EDIF_STR (varnomvar, varstr)

    def RootFolder (self, filename: str) -> int:
        """Entra na pasta raiz de um edifício, criando-a se necessário.

        Args:
            filename: Nome do edifício.

        Returns:
            ``!= 0`` se o edifício não existe.
        """
        # Permite à DLL normalizar/sanear o nome (ex: remover caracteres inválidos)
        parfilename     = ctypes.c_char_p (filename.encode(TQS.TQSUtil.CHARSET))
        self.m_edilib.EDILIB_EDIFICIO_PASTA_RAIZ (parfilename)
        filename        = parfilename.value.decode(TQS.TQSUtil.CHARSET)
        # Monta a pasta sob a raiz geral, cria-a se não existir e entra nela
        raiz            = BuildingRoot ()
        folder          = raiz + "\\" + filename
        myfolder        = Path (folder)
        myfolder.mkdir  (parents=True, exist_ok=True)
        os.chdir        (folder)
        # Confere se o contexto agora aponta para o edifício esperado (case-insensitive)
        nprjpv, nprjed, nombde, nomedi, nompav, istat = BuildingContext ()
        if              (istat == 0):
            if          (filename.lower () != nomedi.lower ()):
                istat   = 1
        return          istat

#------------------------------------------------------------------------------
#       Arquivos - ler e gravar edifícios
#
class File ():
    """Operações de arquivo (leitura, gravação) para o edifício TQS.

    Implementação:
        Wrapper sobre as funções ``EDILIB_EDIFICIO_*`` do ``NEDILIB.DLL`` que leem e
        gravam o ``EDIFICIO.BDE``. Mantém o nome do arquivo corrente em ``m_filename``
        para que :meth:`Save` possa reusá-lo. As funções de gravação consideram o flag
        ``m_inovo`` do :class:`Building` proprietário para decidir entre criar do zero
        ou duplicar um edifício existente.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        m_filename: Nome do arquivo de edifício atual.
    """

    def __init__ (self, building: "Building") -> None:
        """Inicializa o sub-objeto de arquivos.

        Args:
            building: Instância de :class:`Building` proprietária.
        """
        self.m_building     = building
        self.m_filename     = ""

    def Open (self, filename: str) -> int:
        """Carrega um edifício existente.

        Args:
            filename: Nome do edifício.

        Returns:
            ``!= 0`` se não conseguiu ler o edifício.
        """
        self.m_filename = filename
        parfilename     = ctypes.c_char_p (filename.encode(TQS.TQSUtil.CHARSET))
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_building.m_edilib.EDILIB_EDIFICIO_LER (parfilename, ctypes.byref (paristat))
        istat           = paristat.value
        # Leitura bem-sucedida: marca como edifício existente (não-novo) p/ futura gravação
        if              (istat == 0):
            self.m_building.m_inovo = 0
        return          (istat)

    def Save (self) -> int:
        """Salva o edifício atual aberto com :meth:`Open`.

        Returns:
            ``!= 0`` se não conseguiu gravar.
        """
        # Sem nome de arquivo definido, não há onde salvar: aborta com erro
        if              self.m_filename == "":
            TQS.TQSUtil.writef ("Não posso salvar: nome do edifício indefinido")
            return      1
        return          self.SaveAs (self.m_filename)

    def SaveAs (self, filename: str) -> int:
        """Salva o edifício com um nome arbitrário.

        Args:
            filename: Nome do edifício.

        Returns:
            ``!= 0`` se não conseguiu gravar.
        """
        self.m_filename = filename
        parfilename     = ctypes.c_char_p (filename.encode(TQS.TQSUtil.CHARSET))
        parimodelo      = ctypes.c_int (self.m_building.m_imodelo)
        # Edifício já existente é gravado como duplicação para preservar arquivos auxiliares
        iduplicar       = 0
        if              (self.m_building.m_inovo == 0):
            iduplicar   = 1
        pariduplicar    = ctypes.c_int (iduplicar)
        parnomodelo     = ctypes.c_char_p (self.m_building.m_nomodelo.encode(TQS.TQSUtil.CHARSET))
        istat           = 0
        paristat        = ctypes.c_int (istat)
        self.m_building.m_edilib.EDILIB_EDIFICIO_GRAVARMOD (parfilename,
                            pariduplicar, parimodelo, parnomodelo, ctypes.byref (paristat))
        istat           = paristat.value
        return          (istat)

    def SuppressMessages (self, isuprimir: int) -> None:
        """Suprime mensagens durante a gravação do edifício.

        Args:
            isuprimir: ``0`` Não, ``1`` Sim.
        """
        parisuprimir    = ctypes.c_int (isuprimir)
        self.m_building.m_edilib.EDILIB_EDIFICIO_SUPRIMIRMSG (parisuprimir)


#------------------------------------------------------------------------------
#       Aba gerais - identificação, títulos, tipo de estrutura
#
class Project ():
    """Aba "Gerais" do edifício: identificação, títulos e tipo de estrutura.

    Implementação:
        Wrapper sobre os campos da estrutura ``EDIFICIO`` em ``NEDILIB.DLL``. A maioria
        das propriedades é um par ``@property`` / ``@<prop>.setter`` que delega aos
        métodos genéricos ``_GetVar*`` / ``_SetVar*`` do :class:`Building`, passando
        o nome interno (constantes ``EDL_V_*``). Algumas propriedades (e.g.
        :attr:`structureType`, :attr:`concreteCode`) chamam funções ``EDILIB_*`` próprias
        por envolverem mais de um campo. Os métodos ``Get*Path`` apenas decodificam o
        buffer devolvido por ``EDILIB_GET_DIR*``. Comentários inline aparecem somente
        nos pontos com lógica condicional.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
    """

    def __init__ (self, building: "Building") -> None:
        """Inicializa o sub-objeto de projeto.

        Args:
            building: Instância de :class:`Building` proprietária.
        """
        self.m_building     = building

    @property
    def projectTitle (self) -> str:
        """Título do edifício."""
        return          self.m_building._GetVarStr (EDL_V_TITGED)#!NTR

    @projectTitle.setter
    def projectTitle (self, stitle: str) -> None:
        """Atribui Título do edifício."""
        self.m_building._SetVarStr (EDL_V_TITGED, stitle)#!NTR

    @property
    def clientTitle (self) -> str:
        """Título do cliente."""
        return          self.m_building._GetVarStr (EDL_V_CLIGED)#!NTR

    @clientTitle.setter
    def clientTitle (self, stitle: str) -> None:
        """Atribui Título do cliente."""
        self.m_building._SetVarStr (EDL_V_CLIGED, stitle)#!NTR

    @property
    def projectAddress (self) -> str:
        """Endereço da obra."""
        return          self.m_building._GetVarStr (EDL_V_ENDEROBRA)#!NTR

    @projectAddress.setter
    def projectAddress (self, saddress: str) -> None:
        """Atribui Endereço da obra."""
        self.m_building._SetVarStr (EDL_V_ENDEROBRA, saddress)#!NTR

    @property
    def projectNumber (self) -> int:
        """Número arbitrário de projeto ``1..9999``."""
        return          self.m_building._GetVarInt (EDL_V_NPRJED)#!NTR

    @projectNumber.setter
    def projectNumber (self, nprj: int) -> None:
        """Atribui Número arbitrário de projeto ``1..9999``."""
        self.m_building._SetVarInt (EDL_V_NPRJED, nprj)#!NTR

    @property
    def blueprintPrefix (self) -> str:
        """Prefixo arbitrário para plantas plotadas."""
        return          self.m_building._GetVarStr (EDL_V_PREFEDIPLA)#!NTR

    @blueprintPrefix.setter
    def blueprintPrefix (self, sprefix: str) -> None:
        """Atribui Prefixo arbitrário para plantas plotadas."""
        self.m_building._SetVarStr (EDL_V_PREFEDIPLA, sprefix)#!NTR

    @property
    def projectDescription (self) -> str:
        """Descrição do projeto."""
        return          self.m_building._GetVarStr (EDL_V_DESCRICAO)#!NTR

    @projectDescription.setter
    def projectDescription (self, sdescription: str) -> None:
        """Atribui Descrição do projeto."""
        self.m_building._SetVarStr (EDL_V_DESCRICAO, sdescription)#!NTR

    @property
    def structureType (self) -> int:
        """Tipo da estrutura.

        Returns:
            * ``0``: Concreto armado/protendido.
            * ``1``: Concreto pré-moldado.
            * ``2``: Alvenaria estrutural.
            * ``3``: Paredes de concreto.
        """
        # ialvened mapeia o macro-tipo (concreto/alvenaria/parede); concreto se subdivide via ipremold
        itype           = -1
        ialvened        = self.m_building._GetVarInt (EDL_V_IALVENED)#!NTR
        if              ialvened == 0:
            # Concreto: distingue armado (0) de pré-moldado (1) por flag adicional
            varipremold = ctypes.c_int (0)
            self.m_building.m_edilib.EDILIB_ECP_GET_IPREMOLD (ctypes.byref (varipremold))
            ipremold    = varipremold.value
            if          ipremold == 0:
                itype   = 0
            else:
                itype   = 1
        elif            ialvened == 1:
            itype       = 2
        elif            ialvened == 2:
            itype       = 3
        return          itype


    @structureType.setter
    def structureType (self, itype: int) -> None:
        """Atribui Tipo da estrutura."""
        # Inverso do getter: cada itype mapeia em um par (ialvened, ipremold) específico
        if              itype == 0:
            self.m_building._SetVarInt (EDL_V_IALVENED, 0)#!NTR
            varipremold = ctypes.c_int (0)
            self.m_building.m_edilib.EDILIB_ECP_SET_IPREMOLD (varipremold)

        elif            itype == 1:
            self.m_building._SetVarInt (EDL_V_IALVENED, 0)#!NTR
            varipremold = ctypes.c_int (1)
            self.m_building.m_edilib.EDILIB_ECP_SET_IPREMOLD (varipremold)

        elif            itype == 2:
            self.m_building._SetVarInt (EDL_V_IALVENED, 1)#!NTR
            varipremold = ctypes.c_int (0)
            self.m_building.m_edilib.EDILIB_ECP_SET_IPREMOLD (varipremold)

        elif            itype == 3:
            self.m_building._SetVarInt (EDL_V_IALVENED, 2)#!NTR
            varipremold = ctypes.c_int (0)
            self.m_building.m_edilib.EDILIB_ECP_SET_IPREMOLD (varipremold)

    @property
    def formworkActive (self) -> int:
        """``1`` se com projeto de formas de madeira."""
        return          self.m_building._GetVarInt (EDL_V_ICRMED)#!NTR

    @formworkActive.setter
    def formworkActive (self, iactive: int) -> None:
        """Atribui ``1`` se com projeto de formas de madeira."""
        self.m_building._SetVarInt (EDL_V_ICRMED, iactive)#!NTR

    @property
    def concreteCode (self) -> int:
        """Norma de concreto ``TQSBuild.NORMA_xxxx``."""
        varinorma       = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_NORMACONCR (ctypes.byref (varinorma))
        return          varinorma.value

    @concreteCode.setter
    def concreteCode (self, icode: int) -> None:
        """Atribui Norma de concreto ``TQSBuild.NORMA_xxxx``."""
        varinorma       = ctypes.c_int (icode)
        self.m_building.m_edilib.EDILIB_SET_NORMACONCR (varinorma)

    @property
    def masonryCode (self) -> int:
        """Norma de alvenaria estrutural ``TQSBuild.NORMALVI_xxxx``."""
        return          self.m_building._GetVarInt (EDL_V_INORMALVEN)#!NTR

    @masonryCode.setter
    def masonryCode (self, icode: int) -> None:
        """Atribui Norma de alvenaria estrutural ``TQSBuild.NORMALVI_xxxx``."""
        self.m_building._SetVarInt (EDL_V_INORMALVEN, icode)#!NTR

    @property
    def concreteWallsCode (self) -> int:
        """Norma de paredes de concreto ``TQSBuild.NORMAPAREDI_xxxx``."""
        return          self.m_building._GetVarInt (EDL_V_INORMAPAREDE)#!NTR

    @concreteWallsCode.setter
    def concreteWallsCode (self, icode: int) -> None:
        """Atribui Norma de paredes de concreto ``TQSBuild.NORMAPAREDI_xxxx``."""
        self.m_building._SetVarInt (EDL_V_INORMAPAREDE, icode)#!NTR

    @property
    def codeStrictUse (self) -> int:
        """``1`` se forçar o uso de critérios de norma."""
        return          self.m_building._GetVarInt (EDL_V_IFORCARNORMA)#!NTR

    @codeStrictUse.setter
    def codeStrictUse (self, iforcecode: int) -> None:
        """Atribui ``1`` se forçar o uso de critérios de norma."""
        self.m_building._SetVarInt (EDL_V_IFORCARNORMA, iforcecode)#!NTR

    @property
    def floorHeight (self) -> float:
        """Cota inicial da planta (m)."""
        return          self.m_building._GetVarDouble (EDL_V_COTIED)

    @floorHeight.setter
    def floorHeight (self, height: float) -> None:
        """Atribui Cota inicial da planta (m)."""
        self.m_building._SetVarDouble (EDL_V_COTIED, height)#!NTR

    @property
    def country (self) -> int:
        """País ``TQSBuild.PAIS_xxx``."""
        icountry        = self.m_building._GetVarInt (EDL_V_IPAIS)#!NTR
        return          icountry

    @country.setter
    def country (self, icountry: int) -> None:
        """Atribui País ``TQSBuild.PAIS_xxx``."""
        self.m_building._SetVarInt (EDL_V_IPAIS, icountry)#!NTR

    def GetSpacePath (self) -> str:
        """Retorna o caminho da pasta espacial.

        Returns:
            Pasta/diretório espacial.
        """
        pardirespac     = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRESPACIAL (pardirespac)
        direspac        = pardirespac.value.decode(TQS.TQSUtil.CHARSET)
        return          (direspac)

    def GetColumnsPath (self) -> str:
        """Retorna o caminho da pasta de pilares.

        Returns:
            Pasta/diretório de pilares.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPILAR (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetGeneralPath (self) -> str:
        """Retorna o caminho da pasta Gerais.

        Returns:
            Pasta/diretório Gerais.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRGERAIS (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetLayoutPath (self) -> str:
        """Retorna o caminho da pasta de plantas.

        Returns:
            Pasta/diretório de plantas.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPLANTAS (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetFoundationsPath (self) -> str:
        """Retorna o caminho da pasta de Fundações.

        Returns:
            Pasta/diretório de fundações.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRFUNDAC (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetAdditionalPath (self, index: int) -> str:
        """Retorna o caminho de uma pasta adicional.

        Args:
            index: Índice da pasta adicional ``1..8``.

        Returns:
            Pasta/diretório adicional.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        parindex        = ctypes.c_int (index)
        self.m_building.m_edilib.EDILIB_GET_DIRADIC (parindex, pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetSisesPath (self) -> str:
        """Retorna o caminho da pasta SISEs.

        Returns:
            Pasta/diretório SISEs.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRSISES (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetMasonryPath (self) -> str:
        """Retorna o caminho da pasta de alvenaria estrutural.

        Returns:
            Pasta/diretório de alvenaria estrutural.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRALVEST (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetPrecastColumnsPath (self) -> str:
        """Retorna o caminho da pasta de formas de pilares pré-moldados.

        Returns:
            Pasta/diretório de pilares pré-moldados.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPREPIL (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetPrecastBeamsPath (self) -> str:
        """Retorna o caminho da pasta de formas de vigas pré-moldadas.

        Returns:
            Pasta/diretório de vigas pré-moldadas.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPREVIG (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetPrecastSlabsPath (self) -> str:
        """Retorna o caminho da pasta de formas de lajes pré-moldadas.

        Returns:
            Pasta/diretório de lajes pré-moldadas.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPRELAJ (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetPrecastColumnsDesignPath (self) -> str:
        """Retorna o caminho da pasta de armaduras de pilares pré-moldados.

        Returns:
            Pasta/diretório de armaduras de pilares pré-moldados.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPREPILA (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetPrecastBeamsDesignPath (self) -> str:
        """Retorna o caminho da pasta de armaduras de vigas pré-moldadas.

        Returns:
            Pasta/diretório de armaduras de vigas pré-moldadas.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPREVIGA (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetPrecastCorbelsPath (self) -> str:
        """Retorna o caminho da pasta de consolos.

        Returns:
            Pasta/diretório de consolos.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPRECONS (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetPrecastFoundationsPath (self) -> str:
        """Retorna o caminho da pasta de fundações pré-moldadas.

        Returns:
            Pasta/diretório de fundações pré-moldadas.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPREFUND (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

    def GetPrecastFacadesPath (self) -> str:
        """Retorna o caminho da pasta de fachadas pré-moldadas.

        Returns:
            Pasta/diretório de fachadas pré-moldadas.
        """
        pardir          = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_DIRPREFACHADA (pardir)
        dir             = pardir.value.decode(TQS.TQSUtil.CHARSET)
        return          (dir)

#------------------------------------------------------------------------------
#       Aba Modelo - Modelo de cálculo, vigas de transição, etc
#
class Model ():
    """Aba "Modelo": modelo de cálculo, vigas de transição, dinâmica.

    Implementação:
        Wrapper sobre flags e parâmetros da estrutura ``EDIFICIO`` ligados ao modelo
        de cálculo (modelo de pórtico, junta de dilatação, vigas de transição,
        dinâmica, SISEs, análise incremental). Cada propriedade é um par get/set
        que delega aos métodos ``_GetVar*`` / ``_SetVar*`` do :class:`Building`,
        passando as constantes ``EDL_V_*``. Sem lógica condicional: os comentários
        inline são desnecessários no corpo dos métodos.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        precastmodel: Sub-objeto :class:`PrecastModel` (modelo de pré-moldados).
    """

    def __init__ (self, building: "Building") -> None:
        """Inicializa o sub-objeto de modelo.

        Args:
            building: Instância de :class:`Building` proprietária.
        """
        self.m_building   = building
        self.precastmodel = PrecastModel (building, self)

    @property
    def structuralModel (self) -> int:
        """Modelo IV (:data:`PORTICO_HORVER`) ou Modelo VI (:data:`PORTICO_LAJES`)."""
        return          self.m_building._GetVarInt (EDL_V_IPORED)#!NTR

    @structuralModel.setter
    def structuralModel (self, imodel: int) -> None:
        """Atribui Modelo IV (:data:`PORTICO_HORVER`) ou Modelo VI (:data:`PORTICO_LAJES`)."""
        self.m_building._SetVarInt (EDL_V_IPORED, imodel)#!NTR

    @property
    def expansionJoints (self) -> int:
        """``0`` estrutura única; ``1`` duas ou mais separadas por junta de dilatação."""
        return          self.m_building._GetVarInt (EDL_V_IDUASTOUJUNTA)#!NTR

    @expansionJoints.setter
    def expansionJoints (self, ijoints: int) -> None:
        """Atribui ``0`` estrutura única; ``1`` duas ou mais separadas por junta de dilatação."""
        self.m_building._SetVarInt (EDL_V_IDUASTOUJUNTA, ijoints)#!NTR

    @property
    def transferBeamModel (self) -> int:
        """``1`` para dois modelos de viga de transição (inércia enrijecida/real)."""
        return          self.m_building._GetVarInt (EDL_V_IENVTED)#!NTR

    @transferBeamModel.setter
    def transferBeamModel (self, ienvted: int) -> None:
        """Atribui ``1`` para dois modelos de viga de transição (inércia enrijecida/real)."""
        self.m_building._SetVarInt (EDL_V_IENVTED, ienvted)#!NTR

    @property
    def transferBeamModelInertiaMultiplier (self) -> float:
        """Multiplicador de inércia à flexão para viga de transição enrijecida."""
        return          self.m_building._GetVarDouble (EDL_V_VMULETR)

    @transferBeamModelInertiaMultiplier.setter
    def transferBeamModelInertiaMultiplier (self, muletr: float) -> None:
        """Atribui Multiplicador de inércia à flexão para viga de transição enrijecida."""
        self.m_building._SetVarDouble (EDL_V_VMULETR, muletr)#!NTR

    @property
    def transferBemModelPolarInertiaDivider (self) -> float:
        """Divisor da inércia à torção para viga de transição enrijecida."""
        return          self.m_building._GetVarDouble (EDL_V_REDTORVTRN)

    @transferBemModelPolarInertiaDivider.setter
    def transferBemModelPolarInertiaDivider (self, redtor: float) -> None:
        """Atribui Divisor da inércia à torção para viga de transição enrijecida."""
        self.m_building._SetVarDouble (EDL_V_REDTORVTRN, redtor)#!NTR

    @property
    def secondOrderEfect (self) -> int:
        """Efeitos globais de segunda ordem: ``0`` GamaZ, ``1`` P-Delta."""
        return          self.m_building._GetVarInt (EDL_V_ICALCPDELTA)#!NTR

    @secondOrderEfect.setter
    def secondOrderEfect (self, ipdelta: int) -> None:
        """Atribui ``0`` GamaZ, ``1`` P-Delta."""
        self.m_building._SetVarInt (EDL_V_ICALCPDELTA, ipdelta)#!NTR

    @property
    def structuralDynamicsAnalysis (self) -> int:
        """``0`` análise estática, ``1`` dinâmica da estrutura."""
        return          self.m_building._GetVarInt (EDL_V_IDINAMICAPOR)#!NTR

    @structuralDynamicsAnalysis.setter
    def structuralDynamicsAnalysis (self, idynamic: int) -> None:
        """Atribui ``0`` análise estática, ``1`` dinâmica da estrutura."""
        self.m_building._SetVarInt (EDL_V_IDINAMICAPOR, idynamic)#!NTR

    @property
    def soilStructureInteraction (self) -> int:
        """``1`` se integrado ao sistema de interação solo-estrutura SISEs."""
        return          self.m_building._GetVarInt (EDL_V_INTSISES)#!NTR

    @soilStructureInteraction.setter
    def soilStructureInteraction (self, isises: int) -> None:
        """Atribui ``1`` se integrado ao sistema de interação solo-estrutura SISEs."""
        self.m_building._SetVarInt (EDL_V_INTSISES, isises)#!NTR

    @property
    def soilStructureIntegrateFoundations (self) -> int:
        """``1`` para agregar a fundação discretizada do SISEs no pórtico espacial."""
        return          self.m_building._GetVarInt (EDL_V_INTSISESPOR)#!NTR

    @soilStructureIntegrateFoundations.setter
    def soilStructureIntegrateFoundations (self, isisespor: int) -> None:
        """Atribui ``1`` para agregar a fundação discretizada do SISEs no pórtico espacial."""
        self.m_building._SetVarInt (EDL_V_INTSISESPOR, isisespor)#!NTR

    @property
    def incrementalAnalysis (self) -> int:
        """``1`` para analisar a estrutura considerando efeito incremental."""
        return          self.m_building._GetVarInt (EDL_V_IEFEITOINCREM)#!NTR

    @incrementalAnalysis.setter
    def incrementalAnalysis (self, incremental: int) -> None:
        """Atribui ``1`` para analisar a estrutura considerando efeito incremental."""
        self.m_building._SetVarInt (EDL_V_IEFEITOINCREM, incremental)#!NTR

#------------------------------------------------------------------------------
#       Modelo de Pré-Moldados
#
class PrecastModel ():
    """Modelo construtivo para estruturas pré-moldadas.

    Implementação:
        Wrapper sobre as funções ``EDILIB_ECP_*`` que controlam etapas e regiões
        construtivas de estruturas pré-moldadas. As tuplas ``(numetapas, numregioes)``
        e ``(istage, iregion)`` indexam uma matriz de etapas dentro do EDIFICIO.
        Os pares ``stagesNumber`` / ``regionsNumber`` reusam :meth:`_GetEtapas` /
        :meth:`_SetEtapas` para preservar a outra dimensão ao alterar uma delas.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        m_model: Modelo :class:`Model` proprietário.
    """

    def __init__ (self, building: "Building", model: "Model") -> None:
        """Inicializa o sub-objeto de modelo de pré-moldados.

        Args:
            building: Instância de :class:`Building` proprietária.
            model: Instância de :class:`Model` proprietária.
        """
        self.m_building      = building
        self.m_model         = model

    def _GetEtapas (self) -> Tuple[int, int]:
        """Retorna o número de etapas e regiões construtivas.

        Returns:
            Tupla ``(numetapas, numregioes)``.
        """
        varnumetapas    = ctypes.c_int (0)
        varnumregioes   = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_ECP_GET_ETAPAS (ctypes.byref (varnumetapas),
                        ctypes.byref (varnumregioes))
        numetapas       = varnumetapas.value
        numregioes      = varnumregioes.value
        return          numetapas, numregioes

    def _SetEtapas (self, numetapas: int, numregioes: int) -> None:
        """Define o número de etapas e regiões construtivas.

        Args:
            numetapas: Número de etapas construtivas.
            numregioes: Número de regiões construtivas.
        """
        varnumetapas    = ctypes.c_int (numetapas)
        varnumregioes   = ctypes.c_int (numregioes)
        self.m_building.m_edilib.EDILIB_ECP_SET_ETAPAS (varnumetapas, varnumregioes)

    def Clear (self) -> None:
        """Limpa a lista de etapas e regiões construtivas.

        ATENÇÃO: a chamada omite o handle de DLL — usa
        ``self.m_building.EDILIB_ECP_LIMPAR`` em vez de
        ``self.m_building.m_edilib.EDILIB_ECP_LIMPAR``, como fazem todas as
        outras rotinas ``EDILIB_ECP_*``. ``Clear()`` levanta ``AttributeError``
        antes de chegar à DLL.
        """
        self.m_building.EDILIB_ECP_LIMPAR ()

    @property
    def stagesNumber (self) -> int:
        """Número de etapas construtivas de estrutura pré-moldada."""
        numetapas, numregioes = self._GetEtapas ()
        return          numetapas

    @stagesNumber.setter
    def stagesNumber (self, numstages: int) -> None:
        """Atribui Número de etapas construtivas de estrutura pré-moldada."""
        numetapas, numregioes = self._GetEtapas ()
        self._SetEtapas (numstages, numregioes)

    @property
    def regionsNumber (self) -> int:
        """Número de regiões construtivas de estrutura pré-moldada."""
        numetapas, numregioes = self._GetEtapas ()
        return          numregioes

    @regionsNumber.setter
    def regionsNumber (self, numregions: int) -> None:
        """Atribui Número de regiões construtivas de estrutura pré-moldada."""
        numetapas, numregioes = self._GetEtapas ()
        self._SetEtapas (numetapas, numregions)

    def GetFloor(self, istage: int, iregion: int) -> Tuple[int, int]:
        """Retorna o piso construído e o piso solidarizado de uma etapa/região.

        Args:
            istage: Etapa construtiva ``0..stagesNumber-1``.
            iregion: Região construtiva ``0..regionsNumber-1``.

        Returns:
            Tupla ``(ifloor, ifloormonolithic)``:

            * ``ifloor``: piso até onde será construído.
            * ``ifloormonolithic``: piso até onde será solidarizado.
        """
        varistage       = ctypes.c_int (istage)
        variregion      = ctypes.c_int (iregion)
        varipisof       = ctypes.c_int (0)
        varipisosoli    = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_ECP_GET_ETAPA (varistage, variregion,
                       ctypes.byref (varipisof), ctypes.byref (varipisosoli))
        ipisof          = varipisof.value
        ipisosoli       = varipisosoli.value
        return          ipisof, ipisosoli

    def SetFloor(self, istage: int, iregion: int, ifloor: int, ifloormonolithic: int) -> None:
        """Define o piso construído e o piso solidarizado de uma etapa/região.

        Args:
            istage: Etapa construtiva ``0..stagesNumber-1``.
            iregion: Região construtiva ``0..regionsNumber-1``.
            ifloor: Piso até onde será construído.
            ifloormonolithic: Piso até onde será solidarizado.
        """
        varistage       = ctypes.c_int (istage)
        variregion      = ctypes.c_int (iregion)
        varipisof       = ctypes.c_int (ifloor)
        varipisosoli    = ctypes.c_int (ifloormonolithic)
        self.m_building.m_edilib.EDILIB_ECP_SET_ETAPA (varistage, variregion,
                       varipisof, varipisosoli)

#------------------------------------------------------------------------------
#       Aba Pavimentos - Definição de pavimentos e dados de pavimento
#
class FloorsPlan ():
    """Aba "Pavimentos": definição e dados de plantas/pavimentos.

    Implementação:
        Wrapper sobre as funções ``EDILIB_PLANTAS_*`` e ``EDILIB_GET_PLANTAS_*`` /
        ``EDILIB_SET_PLANTAS_*`` que manipulam o vetor de plantas do edifício. O
        índice ``ipla`` (base zero, ``0..floorsPlanNumber-1``) é o primeiro
        argumento de quase toda função; cada Get/Set corresponde a um campo da
        estrutura ``PLANTAS`` (nome, classe, cota, repetição, modelo de grelha,
        cargas térmicas, retração, pisos auxiliares, etc.). Os métodos ``Create``,
        ``CreateAbove``, ``Erase`` e ``Clear`` operam sobre o vetor inteiro.
        Comentários inline desnecessários — toda a lógica é pack/call/unpack.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
    """

    def __init__ (self, building: "Building") -> None:
        """Inicializa o sub-objeto de pavimentos.

        Args:
            building: Instância de :class:`Building` proprietária.
        """
        self.m_building = building

    def GetFloorsNumber (self) -> int:
        """Retorna o número de pisos do edifício.

        É diferente do número de plantas, pois uma planta pode ter repetições.

        Returns:
            Número de pisos.
        """
        varnumpisos     = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_NUMPISOS (ctypes.byref (varnumpisos))
        numpisos        = varnumpisos.value
        return          numpisos

    @property
    def floorsPlanNumber (self) -> int:
        """Número de plantas. Plantas com repetição contam como uma única."""
        varnumplantas   = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_PLANTAS_NUMPLANTAS (ctypes.byref (varnumplantas))
        numplantas      = varnumplantas.value
        return          numplantas

    def Clear (self) -> None:
        """Elimina todas as plantas do edifício."""
        self.m_building.m_edilib.EDILIB_PLANTAS_LIMPAR ()

    def Create (self, ipla: int) -> None:
        """Cria nova planta no índice fornecido.

        Args:
            ipla: Índice da planta com base zero.
        """
        varipla         = ctypes.c_int (ipla)
        self.m_building.m_edilib.EDILIB_PLANTAS_CRIAR (varipla);

    def CreateAbove (self, nompla: str, pd: float, iclass: int) -> None:
        """Cria uma planta acima de todas as outras.

        Args:
            nompla: Nome e título da planta.
            pd: Altura da planta (m).
            iclass: Classe do piso ``ICLxxx``.
        """
        varnompla       = ctypes.c_char_p (nompla.encode(TQS.TQSUtil.CHARSET))
        varpd           = ctypes.c_double (pd)
        variclass       = ctypes.c_int (iclass)
        self.m_building.m_edilib.EDILIB_PLANTAS_CRIAR_ACIMA (varnompla, varpd, variclass)

    def Erase (self, ipla: int) -> None:
        """Apaga a planta no índice fornecido.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
        """
        varipla         = ctypes.c_int (ipla)
        self.m_building.m_edilib.EDILIB_PLANTAS_APAGAR (varipla);

    def GetRepetition (self, ipla: int) -> int:
        """Retorna o número de repetições de uma planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Número de repetições da planta.
        """
        varipla         = ctypes.c_int (ipla)
        varirep         = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_NPISSC (varipla, ctypes.byref (varirep))
        irep            = varirep.value
        return          irep

    def SetRepetition (self, ipla: int, irep: int) -> None:
        """Define o número de repetições da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            irep: Número de repetições da planta.
        """
        varipla         = ctypes.c_int (ipla)
        varirep         = ctypes.c_int (irep)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_NPISSC (varipla, varirep)

    def GetFloorHeight (self, ipla: int) -> float:
        """Retorna a diferença de cota entre a planta atual e a de baixo (m).

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Altura da planta em metros.
        """
        varipla         = ctypes.c_int (ipla)
        varpedrsc       = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_PEDRSC (varipla, ctypes.byref (varpedrsc))
        pedrsc          = varpedrsc.value
        return          pedrsc

    def SetFloorHeight (self, ipla: int, pd: float) -> None:
        """Define a diferença de cota entre a planta atual e a de baixo (m).

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            pd: Altura da planta (m).
        """
        varipla         = ctypes.c_int (ipla)
        varpedrsc       = ctypes.c_double (pd)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_PEDRSC (varipla, varpedrsc)

    def GetClass (self, ipla: int) -> int:
        """Retorna a classe de uma planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Classe ``TQSBuild.ICLxxx``.
        """
        varipla         = ctypes.c_int (ipla)
        variclass       = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_ICLASC (varipla, ctypes.byref (variclass))
        iclass          = variclass.value
        return          iclass

    def SetClass (self, ipla: int, iclass: int) -> None:
        """Define a classe de uma planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            iclass: Classe ``TQSBuild.ICLxxx``.
        """
        varipla         = ctypes.c_int (ipla)
        variclass       = ctypes.c_int (iclass)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_ICLASC (varipla, variclass)

    def GetProjectNumber (self, ipla: int) -> int:
        """Retorna o número de projeto da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Número do projeto da planta.
        """
        varipla         = ctypes.c_int (ipla)
        varnprj         = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_NPRPLA (varipla, ctypes.byref (varnprj))
        nprj            = varnprj.value
        return          nprj

    def SetProjectNumber (self, ipla: int, nprj: int) -> None:
        """Define o número de projeto da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            nprj: Número arbitrário de projeto da planta.
                Usado em alguns nomes de arquivos.
        """
        varipla         = ctypes.c_int (ipla)
        varnprj         = ctypes.c_int (nprj)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_NPRPLA (varipla, varnprj)

    def GetName (self, ipla: int) -> str:
        """Retorna o nome da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Nome da planta. Usado também como nome da pasta dos arquivos.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_TNMPLA (varipla, varname)
        sname           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          sname

    def SetName (self, ipla: int, sname: str) -> None:
        """Define o nome da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            sname: Nome da planta. Usado também como nome da pasta dos arquivos.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (sname.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_TNMPLA (varipla, varname)

    def GetDescription (self, ipla: int) -> str:
        """Retorna a descrição da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Descrição da planta.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_TITPLA (varipla, varname)
        sname           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          sname

    def SetDescription (self, ipla: int, sdescription: str) -> None:
        """Define a descrição da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            sdescription: Descrição da planta.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (sdescription.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_TITPLA (varipla, varname)

    def GetFloorPath (self, ipla: int) -> str:
        """Retorna a pasta da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Pasta/diretório.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_DIRPLA (varipla, varname)
        spath           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          spath

    def SetFloorPath (self, ipla: int, path: str) -> None:
        """Define a pasta da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            path: Pasta/diretório.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (path.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_DIRPLA (varipla, varname)

    def GetBeamsPath (self, ipla: int) -> str:
        """Retorna a pasta de vigas se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Pasta/diretório de vigas.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_DIVPLA (varipla, varname)
        spath           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          spath

    def SetBeamsPath (self, ipla: int, path: str) -> None:
        """Define a pasta de vigas se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            path: Pasta/diretório.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (path.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_DIVPLA (varipla, varname)

    def GetFormworkPath (self, ipla: int) -> str:
        """Retorna a pasta de madeira se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Pasta/diretório de madeira.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_DIMPLA (varipla, varname)
        spath           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          spath

    def SetFormworkPath (self, ipla: int, path: str) -> None:
        """Define a pasta de madeira se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            path: Pasta/diretório.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (path.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_DIMPLA (varipla, varname)


    def GetMasonryPath (self, ipla: int) -> str:
        """Retorna a pasta de alvenaria estrutural se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Pasta/diretório de alvenaria.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_DIAPLA (varipla, varname)
        spath           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          spath

    def SetMasonryPath (self, ipla: int, path: str) -> None:
        """Define a pasta de alvenaria estrutural se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            path: Pasta/diretório.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (path.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_DIAPLA (varipla, varname)

    def GetStairsPath (self, ipla: int) -> str:
        """Retorna a pasta de escadas se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Pasta/diretório de escadas.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_DIRESC (varipla, varname)
        spath           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          spath

    def SetStairsPath (self, ipla: int, path: str) -> None:
        """Define a pasta de escadas se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            path: Pasta/diretório.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (path.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_DIRESC (varipla, varname)


    def GetOthersPath (self, ipla: int) -> str:
        """Retorna a pasta de elementos especiais se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Pasta/diretório de elementos especiais.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_DRESPECIAIS (varipla, varname)
        spath           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          spath

    def SetOthersPath (self, ipla: int, path: str) -> None:
        """Define a pasta de elementos especiais se diferente do padrão.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            path: Pasta/diretório.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (path.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_DRESPECIAIS (varipla, varname)

    def GetTitle (self, ipla: int) -> str:
        """Retorna o título da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Título da planta.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_TITPSC (varipla, varname)
        sname           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          sname

    def SetTitle (self, ipla: int, stitle: str) -> None:
        """Define o título da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            stitle: Título da planta.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (stitle.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_TITPSC (varipla, varname)

    def GetBlueprintPrefix (self, ipla: int) -> str:
        """Retorna o prefixo de plantas usado em layouts de plotagem.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Prefixo opcional para a planta nos layouts de plotagem.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_PREFPAVPLA (varipla, varname)
        sname           = varname.value.decode(TQS.TQSUtil.CHARSET)
        return          sname

    def SetBlueprintPrefix (self, ipla: int, sprefix: str) -> None:
        """Define o prefixo de plantas usado em layouts de plotagem.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            sprefix: Prefixo opcional para a planta nos layouts de plotagem.
        """
        varipla         = ctypes.c_int (ipla)
        varname         = ctypes.c_char_p (sprefix.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_PREFPAVPLA (varipla, varname)

    def GetPlaneFrameModel (self, ipla: int) -> int:
        """Retorna o modelo estrutural da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Modelo estrutural ``TQSBuild.GRELHA_xxxx``.
        """
        varipla         = ctypes.c_int (ipla)
        varigrpla       = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_IGRPLA (varipla, ctypes.byref (varigrpla))
        igrpla          = varigrpla.value
        return          igrpla

    def SetPlaneFrameModel (self, ipla: int, igrpla: int) -> None:
        """Define o modelo estrutural da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            igrpla: Modelo estrutural ``TQSBuild.GRELHA_xxxx``.
        """
        varipla         = ctypes.c_int (ipla)
        varigrpla       = ctypes.c_int (igrpla)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_IGRPLA (varipla, varigrpla)

    def GetPreStressed (self, ipla: int) -> int:
        """Retorna se o pavimento é protendido.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            ``1`` se o pavimento é protendido.
        """
        varipla         = ctypes.c_int (ipla)
        variprpla       = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_IPRPLA (varipla, ctypes.byref (variprpla))
        iprpla          = variprpla.value
        return          iprpla

    def SetPreStressed (self, ipla: int, iprpla: int) -> None:
        """Define se o pavimento é protendido.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            iprpla: ``1`` se o pavimento é protendido.
        """
        varipla         = ctypes.c_int (ipla)
        variprpla       = ctypes.c_int (iprpla)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_IPRPLA (varipla, variprpla)

    def GetTemperatureAnalysis (self, ipla: int) -> int:
        """Retorna se o pavimento é calculado com carregamento de temperatura.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            ``1`` definida por elemento no Modelador, ``2`` uniforme na planta.
        """
        varipla         = ctypes.c_int (ipla)
        varitemper       = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_ITEMPER (varipla, ctypes.byref (varitemper))
        itemper          = varitemper.value
        return          itemper

    def SetTemperatureAnalysis (self, ipla: int, itemper: int) -> None:
        """Define se o pavimento é calculado com carregamento de temperatura.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            itemper: ``1`` definida por elemento no Modelador, ``2`` uniforme na planta.
        """
        varipla         = ctypes.c_int (ipla)
        varitemper      = ctypes.c_int (itemper)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_ITEMPER (varipla, varitemper)

    def GetTemperatureTransVariation (self, ipla: int) -> float:
        """Retorna a variação transversal de temperatura uniforme na planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Variação transversal de temperatura uniforme em graus.
        """
        varipla         = ctypes.c_int (ipla)
        vartemvartra    = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_TEMVARTRA (varipla, ctypes.byref (vartemvartra))
        temvartra       = vartemvartra.value
        return          temvartra

    def SetTemperatureTransVariation (self, ipla: int, temvartra: float) -> None:
        """Define a variação transversal de temperatura uniforme na planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            temvartra: Variação transversal de temperatura uniforme em graus.
        """
        varipla         = ctypes.c_int (ipla)
        vartemvartra    = ctypes.c_double (temvartra)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_TEMVARTRA (varipla, vartemvartra)

    def GetTemperatureLongVariation (self, ipla: int) -> float:
        """Retorna a variação longitudinal de temperatura uniforme na planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Variação longitudinal de temperatura uniforme em graus.
        """
        varipla         = ctypes.c_int (ipla)
        vartemvarlon    = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_TEMVARLON (varipla, ctypes.byref (vartemvarlon))
        temvarlon       = vartemvarlon.value
        return          temvarlon

    def SetTemperatureLongVariation (self, ipla: int, temvarlon: float) -> None:
        """Define a variação longitudinal de temperatura uniforme na planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            temvarlon: Variação longitudinal de temperatura uniforme em graus.
        """
        varipla         = ctypes.c_int (ipla)
        vartemvarlon    = ctypes.c_double (temvarlon)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_TEMVARLON (varipla, vartemvarlon)

    def GetTemperatureAnalysis2 (self, ipla: int) -> int:
        """Retorna se a planta tem um segundo caso de temperatura definido.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            ``1`` se segundo caso de temperatura definido.
        """
        varipla         = ctypes.c_int (ipla)
        varitemper2     = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_ITEMPER2 (varipla, ctypes.byref (varitemper2))
        itemper2        = varitemper2.value
        return          itemper2

    def SetTemperatureAnalysis2 (self, ipla: int, itemper2: int) -> None:
        """Define se a planta tem um segundo caso de temperatura definido.

        ATENÇÃO: o corpo chama ``EDILIB_SET_PLANTAS_TEMVARTRA2``, a mesma entrada
        nativa usada por ``SetTemperatureTransVariation2``, em vez da entrada do
        indicador ``ITEMPER2`` que o getter correspondente lê. Esta rotina não
        atualiza o indicador que promete definir — e grava um inteiro na variável
        de variação transversal. Não use até a correção.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            itemper2: ``1`` se segundo caso de temperatura definido — ver ATENÇÃO.
        """
        varipla         = ctypes.c_int (ipla)
        varitemper2     = ctypes.c_int (itemper2)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_TEMVARTRA2 (varipla, varitemper2)

    def GetTemperatureTransVariation2 (self, ipla: int) -> float:
        """Retorna a variação transversal do segundo caso de temperatura.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Variação transversal de temperatura do segundo caso.
        """
        varipla         = ctypes.c_int (ipla)
        vartemvartra2   = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_TEMVARTRA2 (varipla, ctypes.byref (vartemvartra2))
        temvartra2      = vartemvartra2.value
        return          temvartra2

    def SetTemperatureTransVariation2 (self, ipla: int, temvartra2: float) -> None:
        """Define a variação transversal do segundo caso de temperatura.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            temvartra2: Variação transversal de temperatura do segundo caso.
        """
        varipla         = ctypes.c_int (ipla)
        vartemvartra2   = ctypes.c_double (temvartra2)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_TEMVARTRA2 (varipla, vartemvartra2)

    def GetTemperatureLongVariation2 (self, ipla: int) -> float:
        """Retorna a variação longitudinal do segundo caso de temperatura.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Variação longitudinal de temperatura do segundo caso.
        """
        varipla         = ctypes.c_int (ipla)
        vartemvarlon2   = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_TEMVARLON2 (varipla, ctypes.byref (vartemvarlon2))
        temvarlon2      = vartemvarlon2.value
        return          temvarlon2

    def SetTemperatureLongVariation2 (self, ipla: int, temvarlon2: float) -> None:
        """Define a variação longitudinal do segundo caso de temperatura.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            temvarlon2: Variação longitudinal de temperatura do segundo caso.
        """
        varipla         = ctypes.c_int (ipla)
        vartemvarlon2   = ctypes.c_double (temvarlon2)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_TEMVARLON2 (varipla, vartemvarlon2)

    def GetShrinkageAnalysis (self, ipla: int) -> int:
        """Retorna se o pavimento é calculado com carregamento de retração.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            ``1`` definida por elemento no Modelador, ``2`` uniforme na planta.
        """
        varipla         = ctypes.c_int (ipla)
        varishrink      = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_IRETRACAO (varipla, ctypes.byref (varishrink))
        ishrink         = varishrink.value
        return          ishrink

    def SetShrinkageAnalysis (self, ipla: int, ishrink: int) -> None:
        """Define se o pavimento é calculado com carregamento de retração.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            ishrink: ``1`` definida por elemento no Modelador, ``2`` uniforme na planta.
        """
        varipla         = ctypes.c_int (ipla)
        varishrink      = ctypes.c_int (ishrink)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_IRETRACAO (varipla, varishrink)

    def GetShrinkageVariation (self, ipla: int) -> float:
        """Retorna a variação equivalente de retração da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Variação transversal de temperatura equivalente em graus.
        """
        varipla         = ctypes.c_int (ipla)
        varshrinkage    = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_RETRVAR (varipla, ctypes.byref (varshrinkage))
        shrinkage       = varshrinkage.value
        return          shrinkage

    def SetShrinkageVariation (self, ipla: int, shrinkage: float) -> None:
        """Define a variação equivalente de retração da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            shrinkage: Variação transversal de temperatura equivalente em graus.
        """
        varipla         = ctypes.c_int (ipla)
        varshrinkage    = ctypes.c_double (shrinkage)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_RETRVAR (varipla, varshrinkage)

    def GetDegreesOfFreddom (self, ipla: int) -> int:
        """Retorna o tipo de modelo de grelha da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            ``0`` automático, ``1`` 3 graus de liberdade, ``2`` 6 graus de liberdade.
        """
        varipla         = ctypes.c_int (ipla)
        variporgre      = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_IPORGRE (varipla, ctypes.byref (variporgre))
        iporgre         = variporgre.value
        return          iporgre

    def SetDegreesOfFreddom (self, ipla: int, iporgre: int) -> None:
        """Define o tipo de modelo de grelha da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            iporgre: ``0`` automático, ``1`` 3 graus de liberdade, ``2`` 6 graus de liberdade.
        """
        varipla         = ctypes.c_int (ipla)
        variporgre      = ctypes.c_int (iporgre)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_IPORGRE (varipla, variporgre)

    def GetVehicleLoad (self, ipla: int) -> int:
        """Retorna a configuração de cargas de veículos da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Veículos: ``0`` não, ``1`` ``<= 30 kN``, ``2`` ``> 30 kN``.
        """
        varipla         = ctypes.c_int (ipla)
        varipavveic     = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_IPAVVEIC (varipla, ctypes.byref (varipavveic))
        ipavveic        = varipavveic.value
        return          ipavveic

    def SetVehicleLoad (self, ipla: int, ipavveic: int) -> None:
        """Define a configuração de cargas de veículos da planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            ipavveic: Veículos ``0`` não, ``1`` ``<= 30 kN``, ``2`` ``> 30 kN``.
        """
        varipla         = ctypes.c_int (ipla)
        varipavveic     = ctypes.c_int (ipavveic)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_IPAVVEIC (varipla, varipavveic)

    def GetSlopedElements (self, ipla: int) -> int:
        """Retorna se a planta contém elementos inclinados.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            ``1`` se a planta contém elementos inclinados.
        """
        varipla         = ctypes.c_int (ipla)
        varislopedelem  = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_IELEMINCLIN (varipla,
                            ctypes.byref (varislopedelem))
        islopedelem     = varislopedelem.value
        return          islopedelem

    def SetSlopedElements (self, ipla: int, islopedelem: int) -> None:
        """Define se a planta contém elementos inclinados.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            islopedelem: ``1`` se a planta contém elementos inclinados.
        """
        varipla         = ctypes.c_int (ipla)
        varislopedelem  = ctypes.c_int (islopedelem)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_IELEMINCLIN (varipla, varislopedelem)

    def GetAuxiliaryFloorsNumber (self, ipla: int) -> int:
        """Retorna o número de pisos auxiliares associados à planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Número de pisos auxiliares.
        """
        varipla         = ctypes.c_int (ipla)
        varnumfloors    = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_NUMDFSPISO (varipla, ctypes.byref (varnumfloors))
        numfloors          = varnumfloors.value
        return          numfloors

    def SetAuxiliaryFloorsNumber (self, ipla: int, numfloors: int) -> None:
        """Define o número de pisos auxiliares associados à planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            numfloors: Número de pisos auxiliares.
        """
        varipla         = ctypes.c_int (ipla)
        varnumfloors    = ctypes.c_int (numfloors)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_NUMDFSPISO (varipla, varnumfloors)

    def GetAuxiliaryFloorUnderneath (self, ipla: int, ifloor: int) -> float:
        """Retorna o rebaixo de um piso auxiliar.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            ifloor: Índice do piso auxiliar ``0..GetAuxiliaryFloorsNumber-1``.

        Returns:
            Rebaixo do piso em metros.
        """
        varipla         = ctypes.c_int (ipla)
        varifloor       = ctypes.c_int (ifloor)
        varundereneath  = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_DFSPISO (varipla, varifloor,
                            ctypes.byref (varundereneath))
        undereneath     = varundereneath.value
        return          undereneath

    def SetAuxiliaryFloorUnderneath (self, ipla: int, ifloor: int, undereneath: float) -> None:
        """Define o rebaixo de um piso auxiliar.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            ifloor: Índice do piso auxiliar ``0..GetAuxiliaryFloorsNumber-1``.
            undereneath: Rebaixo do piso em metros.
        """
        varipla         = ctypes.c_int (ipla)
        varifloor       = ctypes.c_int (ifloor)
        varundereneath  = ctypes.c_double (undereneath)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_DFSPISO (varipla, varifloor, varundereneath)

#------------------------------------------------------------------------------
#       Aba Materiais - principalmente concreto
#
class Materials ():
    """Aba "Materiais": principalmente concreto.

    Implementação:
        Wrapper sobre os campos da estrutura ``EDIFICIO`` relacionados a materiais
        (classe ambiental, controle de qualidade, fck de vigas/pilares/fundações,
        variações por piso, alvenaria, exposição ACI). Os títulos de fck (``FCK*_TIT``)
        são strings tabeladas; as variações por pilar são acessadas por
        :meth:`GetColumnConcreteVariantion` / :meth:`SetColumnConcreteVariantion`,
        que indexam um vetor interno por ``index``. Sem ramificação no corpo: o
        padrão pack/call/unpack cobre todos os métodos.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        precast: Sub-objeto :class:`PrecastMaterials` para materiais pré-moldados.
    """

    def __init__ (self, building: "Building") -> None:
        """Inicializa o sub-objeto de materiais.

        Args:
            building: Instância de :class:`Building` proprietária.
        """
        self.m_building      = building
        self.precast         = PrecastMaterials (building, self)

    @property
    def disableConcreteCheck (self) -> int:
        """``1`` para desativar verificação do fck mínimo."""
        return          self.m_building._GetVarInt (EDL_V_IDESATIVARVERFCK)#!NTR

    @disableConcreteCheck.setter
    def disableConcreteCheck (self, idisable: int) -> None:
        """Atribui ``1`` para desativar verificação do fck mínimo."""
        self.m_building._SetVarInt (EDL_V_IDESATIVARVERFCK, idisable)#!NTR

    @property
    def environmentalClass (self) -> int:
        """Classe de agressividade I..IV (valores ``0..3``)."""
        return          self.m_building._GetVarInt (EDL_V_ICLAGRESS)#!NTR

    @environmentalClass.setter
    def environmentalClass (self, ienvclass: int) -> None:
        """Atribui Classe de agressividade I..IV (valores ``0..3``)."""
        self.m_building._SetVarInt (EDL_V_ICLAGRESS, ienvclass)#!NTR

    @property
    def dryClimate (self) -> int:
        """``1`` se clima seco."""
        return          self.m_building._GetVarInt (EDL_V_ICLIMASECO)#!NTR

    @dryClimate.setter
    def dryClimate (self, idryclimate: int) -> None:
        """Atribui ``1`` se clima seco."""
        self.m_building._SetVarInt (EDL_V_ICLIMASECO, idryclimate)#!NTR

    @property
    def qualityControl (self) -> int:
        """``1`` se concreto realizado com controle de qualidade."""
        return          self.m_building._GetVarInt (EDL_V_ICONTROLQUAL)#!NTR

    @qualityControl.setter
    def qualityControl (self, iqualitycontrol: int) -> None:
        """Atribui ``1`` se concreto realizado com controle de qualidade."""
        self.m_building._SetVarInt (EDL_V_ICONTROLQUAL, iqualitycontrol)#!NTR


    @property
    def beamConcreteStrength (self) -> str:
        """Concreto de vigas e lajes."""
        return          self.m_building._GetVarStr (EDL_V_FCKVED_TIT)#!NTR

    @beamConcreteStrength.setter
    def beamConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto de vigas e lajes."""
        self.m_building._SetVarStr (EDL_V_FCKVED_TIT, sfck)#!NTR

    @property
    def columnConcreteStrength (self) -> str:
        """Concreto de pilares."""
        return          self.m_building._GetVarStr (EDL_V_FCKPDF_TIT)#!NTR

    @columnConcreteStrength.setter
    def columnConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto de pilares."""
        self.m_building._SetVarStr (EDL_V_FCKPDF_TIT, sfck)#!NTR

    @property
    def foundationConcreteStrength (self) -> str:
        """Concreto de fundações."""
        return          self.m_building._GetVarStr (EDL_V_FCKFED_TIT)#!NTR

    @foundationConcreteStrength.setter
    def foundationConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto de fundações."""
        self.m_building._SetVarStr (EDL_V_FCKFED_TIT, sfck)#!NTR

    @property
    def columnConcreteVariantions (self) -> int:
        """Número de variações de resistência de concreto em pilares."""
        return          self.m_building._GetVarInt (EDL_V_NFCVED_TIT)#!NTR

    @columnConcreteVariantions.setter
    def columnConcreteVariantions (self, nvar: int) -> None:
        """Atribui Número de variações de resistência de concreto em pilares."""
        self.m_building._SetVarInt (EDL_V_NFCVED_TIT, nvar)#!NTR

    def GetColumnConcreteVariantion (self, index: int) -> Tuple[str, int]:
        """Retorna um concreto e o último piso onde ele vale.

        Args:
            index: Índice da variação ``0..columnConcreteVariantions-1``.

        Returns:
            Tupla ``(sfck, iuntilfloor)``:

            * ``sfck``: título do fck até o piso abaixo.
            * ``iuntilfloor``: último piso no qual vale o Fck.
        """
        varindex        = ctypes.c_int (index)
        varsfck         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        variuntilfloor  = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_FCKPEDTIT (varindex, varsfck,
                            ctypes.byref (variuntilfloor))
        sfck            = varsfck.value.decode(TQS.TQSUtil.CHARSET)
        iuntilfloor     = variuntilfloor.value
        return          sfck, iuntilfloor


    def SetColumnConcreteVariantion (self, index: int, sfck: str, iuntilfloor: int) -> None:
        """Define um concreto e o último piso onde ele vale.

        Args:
            index: Índice da variação ``0..columnConcreteVariantions-1``.
            sfck: Título do fck até o piso abaixo.
            iuntilfloor: Último piso no qual vale o Fck.
        """
        varindex        = ctypes.c_int (index)
        varsfck         = ctypes.c_char_p (sfck.encode(TQS.TQSUtil.CHARSET))
        variuntilfloor  = ctypes.c_int (iuntilfloor)
        self.m_building.m_edilib.EDILIB_SET_FCKPEDTIT (varindex, varsfck, variuntilfloor)

    def GetFloorPlanConcreteStrength (self, ipla: int) -> str:
        """Retorna o concreto específico de uma planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Título do concreto.
        """
        varipla         = ctypes.c_int (ipla)
        varsfck         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_FCKPAVTIT (varipla, varsfck)
        sfck            = varsfck.value.decode(TQS.TQSUtil.CHARSET)
        return          sfck

    def SetFloorPlanConcreteStrength (self, ipla: int, sfck: str) -> None:
        """Define o concreto específico de uma planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            sfck: Título do concreto.
        """
        varipla         = ctypes.c_int (ipla)
        varsfck         = ctypes.c_char_p (sfck.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_FCKPAVTIT (varipla, varsfck)

    @property
    def masonryMaterial (self) -> int:
        """Material de alvenaria ``TQSBuild.MATRALVI_xxx``."""
        return          self.m_building._GetVarInt (EDL_V_IMATRALVEN)#!NTR

    @masonryMaterial.setter
    def masonryMaterial (self, imat: int) -> None:
        """Atribui Material de alvenaria ``TQSBuild.MATRALVI_xxx``."""
        self.m_building._SetVarInt (EDL_V_IMATRALVEN, imat)#!NTR

    @property
    def aciExposureClass (self) -> int:
        """Classe de exposição ambiental ``TQSBuild.CLAGCIRSOC_xxx``."""
        return          self.m_building._GetVarInt (EDL_V_CIRSOC_ICLAGRESS)#!NTR

    @aciExposureClass.setter
    def aciExposureClass (self, iclass: int) -> None:
        """Atribui Classe de exposição ambiental ``TQSBuild.CLAGCIRSOC_xxx``."""
        self.m_building._SetVarInt (EDL_V_CIRSOC_ICLAGRESS, iclass)#!NTR

#------------------------------------------------------------------------------
#       Materiais - Concreto pré-moldados
#
class PrecastMaterials ():
    """Materiais de concreto para estruturas pré-moldadas.

    Implementação:
        Wrapper sobre os fck tabelados de elementos pré-moldados, com três fases:
        final (em serviço), saque (desforma) e içamento (levantamento). Para os
        casos final, usa funções dedicadas ``EDILIB_GET_PREDAD_FCK*PRE`` /
        ``EDILIB_SET_PREDAD_FCK*PRE`` (string buffer); para saque/içamento delega
        a ``_GetVarStr`` / ``_SetVarStr`` com constantes ``EDL_V_FCK*PRESAQ`` /
        ``EDL_V_FCK*PRELEV``. Sem lógica condicional.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        m_materials: Materiais :class:`Materials` proprietários.
    """

    def __init__ (self, building: "Building", materials: "Materials") -> None:
        """Inicializa o sub-objeto de materiais pré-moldados.

        Args:
            building: Instância de :class:`Building` proprietária.
            materials: Instância de :class:`Materials` proprietária.
        """
        self.m_building      = building
        self.m_materials     = materials

    @property
    def pbeamConcreteStrength (self) -> str:
        """Concreto das vigas pré-moldadas."""
        varsfck         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_FCKVIGPRE (varsfck)
        sfck            = varsfck.value.decode(TQS.TQSUtil.CHARSET)
        return          sfck

    @pbeamConcreteStrength.setter
    def pbeamConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das vigas pré-moldadas."""
        varsfck         = ctypes.c_char_p (sfck.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PREDAD_FCKVIGPRE (varsfck)

    @property
    def pbeamDemouldingConcreteStrength (self) -> str:
        """Concreto das vigas pré-moldadas no saque."""
        return          self.m_building._GetVarStr (EDL_V_FCKVIGPRESAQ)#!NTR

    @pbeamDemouldingConcreteStrength.setter
    def pbeamDemouldingConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das vigas pré-moldadas no saque."""
        self.m_building._SetVarStr (EDL_V_FCKVIGPRESAQ, sfck)#!NTR

    @property
    def pbeamLiftingConcreteStrength (self) -> str:
        """Concreto das vigas pré-moldadas no içamento."""
        return          self.m_building._GetVarStr (EDL_V_FCKVIGPRELEV)#!NTR

    @pbeamLiftingConcreteStrength.setter
    def pbeamLiftingConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das vigas pré-moldadas no içamento."""
        self.m_building._SetVarStr (EDL_V_FCKVIGPRELEV, sfck)#!NTR

    @property
    def pcolumnConcreteStrength (self) -> str:
        """Concreto dos pilares pré-moldados."""
        varsfck         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_FCKPILPRE (varsfck)
        sfck            = varsfck.value.decode(TQS.TQSUtil.CHARSET)
        return          sfck

    @pcolumnConcreteStrength.setter
    def pcolumnConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto dos pilares pré-moldados."""
        varsfck         = ctypes.c_char_p (sfck.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PREDAD_FCKPILPRE (varsfck)

    @property
    def pcolumnDemouldingConcreteStrength (self) -> str:
        """Concreto dos pilares pré-moldados no saque."""
        return          self.m_building._GetVarStr (EDL_V_FCKPILPRESAQ)#!NTR

    @pcolumnDemouldingConcreteStrength.setter
    def pcolumnDemouldingConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto dos pilares pré-moldados no saque."""
        self.m_building._SetVarStr (EDL_V_FCKPILPRESAQ, sfck)#!NTR

    @property
    def pcolumnLiftingConcreteStrength (self) -> str:
        """Concreto dos pilares pré-moldados no içamento."""
        return          self.m_building._GetVarStr (EDL_V_FCKPILPRELEV)#!NTR

    @pcolumnLiftingConcreteStrength.setter
    def pcolumnLiftingConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto dos pilares pré-moldados no içamento."""
        self.m_building._SetVarStr (EDL_V_FCKPILPRELEV, sfck)#!NTR

    @property
    def pslabConcreteStrength (self) -> str:
        """Concreto das lajes pré-moldadas."""
        varsfck         = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_FCKLAJPRE (varsfck)
        sfck            = varsfck.value.decode(TQS.TQSUtil.CHARSET)
        return          sfck

    @pslabConcreteStrength.setter
    def pslabConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das lajes pré-moldadas."""
        varsfck         = ctypes.c_char_p (sfck.encode(TQS.TQSUtil.CHARSET))
        self.m_building.m_edilib.EDILIB_SET_PREDAD_FCKLAJPRE (varsfck)

    @property
    def pslabDemouldingConcreteStrength (self) -> str:
        """Concreto das lajes pré-moldadas no saque."""
        return          self.m_building._GetVarStr (EDL_V_FCKLAJPRESAQ)#!NTR

    @pslabDemouldingConcreteStrength.setter
    def pslabDemouldingConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das lajes pré-moldadas no saque."""
        self.m_building._SetVarStr (EDL_V_FCKLAJPRESAQ, sfck)#!NTR

    @property
    def pslabLiftingConcreteStrength (self) -> str:
        """Concreto das lajes pré-moldadas no içamento."""
        return          self.m_building._GetVarStr (EDL_V_FCKLAJPRELEV)#!NTR

    @pslabLiftingConcreteStrength.setter
    def pslabLiftingConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das lajes pré-moldadas no içamento."""
        self.m_building._SetVarStr (EDL_V_FCKLAJPRELEV, sfck)#!NTR

    @property
    def pfoundationConcreteStrength (self) -> str:
        """Concreto das fundações pré-moldadas."""
        return          self.m_building._GetVarStr (EDL_V_FCKFUNPREFIN)#!NTR

    @pfoundationConcreteStrength.setter
    def pfoundationConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das fundações pré-moldadas."""
        self.m_building._SetVarStr (EDL_V_FCKFUNPREFIN, sfck)#!NTR

    @property
    def pfoundationDemouldingConcreteStrength (self) -> str:
        """Concreto das fundações pré-moldadas no saque."""
        return          self.m_building._GetVarStr (EDL_V_FCKFUNPRESAQ)#!NTR

    @pfoundationDemouldingConcreteStrength.setter
    def pfoundationDemouldingConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das fundações pré-moldadas no saque."""
        self.m_building._SetVarStr (EDL_V_FCKFUNPRESAQ, sfck)#!NTR

    @property
    def pfoundationLiftingConcreteStrength (self) -> str:
        """Concreto das fundações pré-moldadas no içamento."""
        return          self.m_building._GetVarStr (EDL_V_FCKFUNPRELEV)#!NTR

    @pfoundationLiftingConcreteStrength.setter
    def pfoundationLiftingConcreteStrength (self, sfck: str) -> None:
        """Atribui Concreto das fundações pré-moldadas no içamento."""
        self.m_building._SetVarStr (EDL_V_FCKFUNPRELEV, sfck)#!NTR


#------------------------------------------------------------------------------
#       Aba Cobrimentos
#
class Covers ():
    """Aba "Cobrimentos" do edifício.

    Implementação:
        Wrapper sobre os campos ``COBR*`` da estrutura ``EDIFICIO`` (cobrimentos
        em cm de vigas, pilares, fundações, lajes inferior/superior, lajes
        secundárias, protendidas, contato com solo). Cada par de propriedades
        delega a :meth:`Building._GetVarDouble` / :meth:`Building._SetVarDouble`
        passando a constante ``EDL_V_COBR*``. Os sub-objetos :attr:`aci`,
        :attr:`precast` e :attr:`floorplan` cobrem variantes específicas.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        aci: Sub-objeto :class:`AciCovers` para cobrimentos ACI/CIRSOC.
        precast: Sub-objeto :class:`PrecastCovers` para cobrimentos pré-moldados.
        floorplan: Sub-objeto :class:`FloorPlanCovers` para cobrimentos por planta.
    """

    def __init__ (self, building: "Building") -> None:
        """Inicializa o sub-objeto de cobrimentos.

        Args:
            building: Instância de :class:`Building` proprietária.
        """
        self.m_building      = building
        self.aci             = AciCovers (building, self)
        self.precast         = PrecastCovers (building, self)
        self.floorplan       = FloorPlanCovers(building, self)

    @property
    def disableCoverCheck (self) -> int:
        """``1`` para desativar verificação do cobrimento mínimo."""
        return          self.m_building._GetVarInt (EDL_V_IDESATIVARVERCOBR)#!NTR

    @disableCoverCheck.setter
    def disableCoverCheck (self, idisable: int) -> None:
        """Atribui ``1`` para desativar verificação do cobrimento mínimo."""
        self.m_building._SetVarInt (EDL_V_IDESATIVARVERCOBR, idisable)#!NTR

    @property
    def beamCover (self) -> float:
        """Cobrimento (cm) de vigas."""
        return          self.m_building._GetVarDouble (EDL_V_COBRVIG)

    @beamCover.setter
    def beamCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de vigas."""
        self.m_building._SetVarDouble (EDL_V_COBRVIG, cover)#!NTR

    @property
    def columnCover (self) -> float:
        """Cobrimento (cm) de pilares."""
        return          self.m_building._GetVarDouble (EDL_V_COBRPIL)

    @columnCover.setter
    def columnCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de pilares."""
        self.m_building._SetVarDouble (EDL_V_COBRPIL, cover)#!NTR

    @property
    def foundationCover (self) -> float:
        """Cobrimento (cm) de fundações.

        ATENÇÃO: os dois acessadores usam ``EDL_V_COBRPIL`` — a mesma variável
        de ``columnCover`` — em vez de ``EDL_V_COBRFUND``. Ler devolve, e
        escrever altera, o valor de ``columnCover``. ``EDL_V_COBRFUND`` existe no
        módulo mas não é usada aqui, portanto o cobrimento de fundações não é
        acessível por esta propriedade.
        """
        return          self.m_building._GetVarDouble (EDL_V_COBRPIL)

    @foundationCover.setter
    def foundationCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de fundações.

        ATENÇÃO: ver a nota no getter — grava em ``EDL_V_COBRPIL``, alterando
        ``columnCover``.
        """
        self.m_building._SetVarDouble (EDL_V_COBRPIL, cover)#!NTR

    @property
    def foundationSecCover (self) -> float:
        """Cobrimento secundário (cm) de fundações."""
        return          self.m_building._GetVarDouble (EDL_V_COBRFUNDSEC)

    @foundationSecCover.setter
    def foundationSecCover (self, cover: float) -> None:
        """Atribui Cobrimento secundário (cm) de fundações."""
        self.m_building._SetVarDouble (EDL_V_COBRFUNDSEC, cover)#!NTR

    @property
    def slabLowerCover (self) -> float:
        """Cobrimento (cm) de laje inferior."""
        return          self.m_building._GetVarDouble (EDL_V_COBRLAJINF)

    @slabLowerCover.setter
    def slabLowerCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de laje inferior."""
        self.m_building._SetVarDouble (EDL_V_COBRLAJINF, cover)#!NTR

    @property
    def slabUpperCover (self) -> float:
        """Cobrimento (cm) de laje superior."""
        return          self.m_building._GetVarDouble (EDL_V_COBRLAJSUP)

    @slabUpperCover.setter
    def slabUpperCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de laje superior."""
        self.m_building._SetVarDouble (EDL_V_COBRLAJSUP, cover)#!NTR

    @property
    def slabSecLowerCover (self) -> float:
        """Cobrimento secundário (cm) de laje inferior."""
        return          self.m_building._GetVarDouble (EDL_V_COBRLAJSECINF)

    @slabSecLowerCover.setter
    def slabSecLowerCover (self, cover: float) -> None:
        """Atribui Cobrimento secundário (cm) de laje inferior."""
        self.m_building._SetVarDouble (EDL_V_COBRLAJSECINF, cover)#!NTR

    @property
    def slabSecUpperCover (self) -> float:
        """Cobrimento secundário (cm) de laje superior."""
        return          self.m_building._GetVarDouble (EDL_V_COBRLAJSECSUP)

    @slabSecUpperCover.setter
    def slabSecUpperCover (self, cover: float) -> None:
        """Atribui Cobrimento secundário (cm) de laje superior."""
        self.m_building._SetVarDouble (EDL_V_COBRLAJSECSUP, cover)#!NTR

    @property
    def prestressedSlabLowerCover (self) -> float:
        """Cobrimento (cm) de protendido inferior."""
        return          self.m_building._GetVarDouble (EDL_V_COBRPROINF)

    @prestressedSlabLowerCover.setter
    def prestressedSlabLowerCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de protendido inferior."""
        self.m_building._SetVarDouble (EDL_V_COBRPROINF, cover)#!NTR

    @property
    def prestressedSlabUpperCover (self) -> float:
        """Cobrimento (cm) de protendido superior."""
        return          self.m_building._GetVarDouble (EDL_V_COBRPROSUP)

    @prestressedSlabUpperCover.setter
    def prestressedSlabUpperCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de protendido superior."""
        self.m_building._SetVarDouble (EDL_V_COBRPROSUP, cover)#!NTR

    @property
    def prestressedSlabSecCover (self) -> float:
        """Cobrimento (cm) de protendido secundário."""
        return          self.m_building._GetVarDouble (EDL_V_COBRPROSEC)

    @prestressedSlabSecCover.setter
    def prestressedSlabSecCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de protendido secundário."""
        self.m_building._SetVarDouble (EDL_V_COBRPROSEC, cover)#!NTR

    @property
    def beamAndSlabSoilCover (self) -> float:
        """Cobrimento (cm) de vigas e lajes em contato com o solo."""
        return          self.m_building._GetVarDouble (EDL_V_COBRVLJSOL)

    @beamAndSlabSoilCover.setter
    def beamAndSlabSoilCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de vigas e lajes em contato com o solo."""
        self.m_building._SetVarDouble (EDL_V_COBRVLJSOL, cover)#!NTR

    @property
    def columnSoilCover (self) -> float:
        """Cobrimento (cm) de pilares em contato com o solo."""
        return          self.m_building._GetVarDouble (EDL_V_COBRPILSOL)

    @columnSoilCover.setter
    def columnSoilCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de pilares em contato com o solo."""
        self.m_building._SetVarDouble (EDL_V_COBRPILSOL, cover)#!NTR

#-----------------------------------------------------------------------------
#       Cobrimentos específicos ACI
#
class AciCovers ():
    """Cobrimentos específicos das normas ACI/CIRSOC.

    Implementação:
        Wrapper sobre os campos ``CIRSOC_COBR*`` do EDIFICIO, que correspondem aos
        cobrimentos definidos pelas normas ACI-318/CIRSOC para cada combinação de
        elemento (laje/viga/pilar) com situação (protendido ou não, exposto ao
        ambiente, em contato com solo, pré-moldado). Cada par de propriedades é
        um get/set delegado a :meth:`Building._GetVarDouble` / ``_SetVarDouble``.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        m_covers: :class:`Covers` proprietário.
    """

    def __init__ (self, building: "Building", covers: "Covers") -> None:
        """Inicializa o sub-objeto de cobrimentos ACI.

        Args:
            building: Instância de :class:`Building` proprietária.
            covers: Instância de :class:`Covers` proprietária.
        """
        self.m_building      = building
        self.m_covers        = covers

    @property
    def aciPrestressClass (self) -> int:
        """Classe de protensão ``TQSBuild.CLPRCIRSOC_xxx``."""
        return          self.m_building._GetVarInt (EDL_V_CIRSOC_ICLAPROTN)#!NTR

    @aciPrestressClass.setter
    def aciPrestressClass (self, iclass: int) -> None:
        """Atribui Classe de protensão ``TQSBuild.CLPRCIRSOC_xxx``."""
        self.m_building._SetVarInt (EDL_V_CIRSOC_ICLAPROTN, iclass)#!NTR

    @property
    def slabNotpresstressedExposedCover (self) -> float:
        """Cobrimento (cm) de lajes não protendidas expostas ao ambiente."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_COBRNPREXPL)

    @slabNotpresstressedExposedCover.setter
    def slabNotpresstressedExposedCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de lajes não protendidas expostas ao ambiente."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_COBRNPREXPL, cover)#!NTR

    @property
    def slabPrestressedSoilCover (self) -> float:
        """Cobrimento (cm) de lajes protendidas em contato com o solo."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_COBRVLJSOLPRO)

    @slabPrestressedSoilCover.setter
    def slabPrestressedSoilCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de lajes protendidas em contato com o solo."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_COBRVLJSOLPRO, cover)#!NTR

    @property
    def slabPrestressedExposedCover (self) -> float:
        """Cobrimento (cm) de lajes protendidas expostas ao ambiente."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_COBRPROEXPLAJE)

    @slabPrestressedExposedCover.setter
    def slabPrestressedExposedCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de lajes protendidas expostas ao ambiente."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_COBRPROEXPLAJE, cover)#!NTR

    @property
    def beamSoilCover (self) -> float:
        """Cobrimento (cm) de vigas em contato com o solo."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_COBRNPRLJSOLV)

    @beamSoilCover.setter
    def beamSoilCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de vigas em contato com o solo."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_COBRNPRLJSOLV, cover)#!NTR

    @property
    def beamExposedCover (self) -> float:
        """Cobrimento (cm) de vigas não protendidas expostas ao ambiente."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_COBRNPREXPV)

    @beamExposedCover.setter
    def beamExposedCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de vigas não protendidas expostas ao ambiente."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_COBRNPREXPV, cover)#!NTR

    @property
    def beamPrestressedExposedCover (self) -> float:
        """Cobrimento (cm) de vigas pré-moldadas expostas ao ambiente."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_COBRPREEXPV)

    @beamPrestressedExposedCover.setter
    def beamPrestressedExposedCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de vigas pré-moldadas expostas ao ambiente."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_COBRPREEXPV, cover)#!NTR

    @property
    def columnExposedCover (self) -> float:
        """Cobrimento (cm) de pilar não protendido exposto ao ambiente."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_COBRNPREXPP)

    @columnExposedCover.setter
    def columnExposedCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de pilar não protendido exposto ao ambiente."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_COBRNPREXPP, cover)#!NTR

    @property
    def columnPrecastExposedCover (self) -> float:
        """Cobrimento (cm) de pilar pré-moldado exposto ao ambiente."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_COBRPREEXPP)

    @columnPrecastExposedCover.setter
    def columnPrecastExposedCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de pilar pré-moldado exposto ao ambiente."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_COBRPREEXPP, cover)#!NTR


#-----------------------------------------------------------------------------
#       Cobrimentos específicos de pré-moldados
#
class PrecastCovers ():
    """Cobrimentos específicos de elementos pré-moldados.

    Implementação:
        Wrapper sobre os campos ``PRECOBR*`` do EDIFICIO (cobrimentos de vigas,
        pilares, fundações e lajes pré-moldadas, incluindo casos secundários).
        Cada par de propriedades delega a :meth:`Building._GetVarDouble` /
        ``_SetVarDouble`` com as constantes ``EDL_V_PRECOBR*``.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        m_covers: :class:`Covers` proprietário.
    """

    def __init__ (self, building: "Building", covers: "Covers") -> None:
        """Inicializa o sub-objeto de cobrimentos pré-moldados.

        Args:
            building: Instância de :class:`Building` proprietária.
            covers: Instância de :class:`Covers` proprietária.
        """
        self.m_building      = building
        self.m_covers        = covers

    @property
    def pbeamCover (self) -> float:
        """Cobrimento (cm) de viga pré-moldada."""
        return          self.m_building._GetVarDouble (EDL_V_PRECOBRVIG)

    @pbeamCover.setter
    def pbeamCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de viga pré-moldada."""
        self.m_building._SetVarDouble (EDL_V_PRECOBRVIG, cover)#!NTR

    @property
    def pcolumnCover (self) -> float:
        """Cobrimento (cm) de pilares pré-moldados."""
        return          self.m_building._GetVarDouble (EDL_V_PRECOBRPIL)

    @pcolumnCover.setter
    def pcolumnCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de pilares pré-moldados."""
        self.m_building._SetVarDouble (EDL_V_PRECOBRPIL, cover)#!NTR

    @property
    def pfoundationCover (self) -> float:
        """Cobrimento (cm) de fundações pré-moldadas."""
        return          self.m_building._GetVarDouble (EDL_V_PRECOBRFUND)

    @pfoundationCover.setter
    def pfoundationCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de fundações pré-moldadas."""
        self.m_building._SetVarDouble (EDL_V_PRECOBRFUND, cover)#!NTR

    @property
    def pfoundationSecCover (self) -> float:
        """Cobrimento (cm) de fundações pré-moldadas adicional secundário (``< 0`` primário)."""
        return          self.m_building._GetVarDouble (EDL_V_PRECOBRFUNDSEC)

    @pfoundationSecCover.setter
    def pfoundationSecCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de fundações pré-moldadas adicional secundário (``< 0`` primário)."""
        self.m_building._SetVarDouble (EDL_V_PRECOBRFUNDSEC, cover)#!NTR

    @property
    def pslabLowerCover (self) -> float:
        """Cobrimento (cm) de laje inferior pré-moldada."""
        return          self.m_building._GetVarDouble (EDL_V_PRECOBRLAJINF)

    @pslabLowerCover.setter
    def pslabLowerCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de laje inferior pré-moldada."""
        self.m_building._SetVarDouble (EDL_V_PRECOBRLAJINF, cover)#!NTR

    @property
    def pslabUpperCover (self) -> float:
        """Cobrimento (cm) de laje superior pré-moldada."""
        return          self.m_building._GetVarDouble (EDL_V_PRECOBRLAJSUP)

    @pslabUpperCover.setter
    def pslabUpperCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de laje superior pré-moldada."""
        self.m_building._SetVarDouble (EDL_V_PRECOBRLAJSUP, cover)#!NTR

    @property
    def pslabSecLowerCover (self) -> float:
        """Cobrimento (cm) de laje adicional secundário inferior."""
        return          self.m_building._GetVarDouble (EDL_V_PRECOBRLAJSECINF)

    @pslabSecLowerCover.setter
    def pslabSecLowerCover (self, cover: float) -> None:
        """Atribui Cobrimento (cm) de laje adicional secundário inferior."""
        self.m_building._SetVarDouble (EDL_V_PRECOBRLAJSECINF, cover)#!NTR


#-----------------------------------------------------------------------------
#       Cobrimentos por planta, se definidos
#
class FloorPlanCovers ():
    """Cobrimentos por planta, quando definidos.

    Implementação:
        Wrapper sobre as funções ``EDILIB_GET_PLANTAS_COBR*`` /
        ``EDILIB_SET_PLANTAS_COBR*``, que sobrescrevem os cobrimentos default por
        planta (indexada por ``ipla``). Um valor ``0`` significa "usar o default
        do edifício". Os métodos seguem o padrão pack ``(ipla, cover)`` /
        chamada DLL / unpack ``cover.value``.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        m_covers: :class:`Covers` proprietário.
    """

    def __init__ (self, building: "Building", covers: "Covers") -> None:
        """Inicializa o sub-objeto de cobrimentos por planta.

        Args:
            building: Instância de :class:`Building` proprietária.
            covers: Instância de :class:`Covers` proprietária.
        """
        self.m_building      = building
        self.m_covers        = covers

    def GetFloorPlanBeamsCover (self, ipla: int) -> float:
        """Retorna o cobrimento (cm) de vigas para a planta, se definido.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_COBRVIG (varipla, ctypes.byref (varcover))
        cover           = varcover.value
        return          cover

    def SetFloorPlanBeamsCover (self, ipla: int, cover: float) -> None:
        """Define o cobrimento (cm) de vigas para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            cover: Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (cover)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_COBRVIG (varipla, varcover)

    def GetFloorPlanSlabLowerCover (self, ipla: int) -> float:
        """Retorna o cobrimento inferior (cm) de lajes para a planta, se definido.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_COBRLAJINF (varipla, ctypes.byref (varcover))
        cover           = varcover.value
        return          cover

    def SetFloorPlanSlabLowerCover (self, ipla: int, cover: float) -> None:
        """Define o cobrimento inferior (cm) de lajes para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            cover: Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (cover)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_COBRLAJINF (varipla, varcover)

    def GetFloorPlanSlabUpperCover (self, ipla: int) -> float:
        """Retorna o cobrimento superior (cm) de lajes para a planta, se definido.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_COBRLAJSUP (varipla, ctypes.byref (varcover))
        cover           = varcover.value
        return          cover

    def SetFloorPlanSlabUpperCover (self, ipla: int, cover: float) -> None:
        """Define o cobrimento superior (cm) de lajes para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            cover: Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (cover)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_COBRLAJSUP (varipla, varcover)

    def GetFloorPlanSlabSecLowerCover (self, ipla: int) -> float:
        """Retorna o cobrimento secundário inferior (cm) de lajes para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_COBRLAJSECINF (varipla, ctypes.byref (varcover))
        cover           = varcover.value
        return          cover

    def SetFloorPlanSlabSecLowerCover (self, ipla: int, cover: float) -> None:
        """Define o cobrimento secundário inferior (cm) de lajes para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            cover: Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (cover)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_COBRLAJSECINF (varipla, varcover)

    def GetFloorPlanSlabSecUpperCover (self, ipla: int) -> float:
        """Retorna o cobrimento secundário superior (cm) de lajes para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_COBRLAJSECSUP (varipla, ctypes.byref (varcover))
        cover           = varcover.value
        return          cover

    def SetFloorPlanSlabSecUpperCover (self, ipla: int, cover: float) -> None:
        """Define o cobrimento secundário superior (cm) de lajes para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            cover: Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (cover)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_COBRLAJSECSUP (varipla, varcover)

    def GetFloorPlanPrestressedSlabLowerCover (self, ipla: int) -> float:
        """Retorna o cobrimento inferior (cm) de lajes protendidas para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Valor do cobrimento em cm ou ``0``.
        """
        varcover        = ctypes.c_double (0.)
        varipla         = ctypes.c_int (ipla)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_COBRPROINF (varipla, ctypes.byref (varcover))
        cover           = varcover.value
        return          cover

    def SetFloorPlanPrestressedSlabLowerCover (self, ipla: int, cover: float) -> None:
        """Define o cobrimento inferior (cm) de lajes protendidas para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            cover: Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (cover)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_COBRPROINF (varipla, varcover)

    def GetFloorPlanPrestressedSlabUpperCover (self, ipla: int) -> float:
        """Retorna o cobrimento superior (cm) de lajes protendidas para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_COBPROSUP (varipla, ctypes.byref (varcover))
        cover           = varcover.value
        return          cover

    def SetFloorPlanPrestressedSlabUpperCover (self, ipla: int, cover: float) -> None:
        """Define o cobrimento superior (cm) de lajes protendidas para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            cover: Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (cover)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_COBPROSUP (varipla, varcover)

    def GetFloorPlanPrestressedSlabSecCover (self, ipla: int) -> float:
        """Retorna o cobrimento secundário (cm) de lajes protendidas para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.

        Returns:
            Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PLANTAS_COBRPROSEC (varipla, ctypes.byref (varcover))
        cover           = varcover.value
        return          cover

    def SetFloorPlanPrestressedSlabSecCover (self, ipla: int, cover: float) -> None:
        """Define o cobrimento secundário (cm) de lajes protendidas para a planta.

        Args:
            ipla: Índice da planta ``0..floorsPlanNumber-1``.
            cover: Valor do cobrimento em cm ou ``0``.
        """
        varipla         = ctypes.c_int (ipla)
        varcover        = ctypes.c_double (cover)
        self.m_building.m_edilib.EDILIB_SET_PLANTAS_COBRPROSEC (varipla, varcover)


#------------------------------------------------------------------------------
#       Aba Cargas
#
class Loads ():
    """Aba "Cargas" do edifício.

    Implementação:
        Wrapper sobre as funções ``EDILIB_*CARREG`` (carregamentos pré-definidos
        por prefixo: PP, PERM, ACID, VENT, ...) e auxiliares de redução de
        sobrecarga e desaprumo. :meth:`GetLoad` e :meth:`SetLoad` empacotam ~14
        parâmetros em ``ctypes`` e validam o ``istat`` retornado pela DLL,
        emitindo mensagem de erro quando o prefixo é inválido. Os sub-objetos
        :attr:`windloads` e :attr:`precastloads` cobrem cargas de vento e cargas
        em etapas construtivas, respectivamente.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        precastloads: Sub-objeto :class:`PrecastLoads` para cargas pré-moldadas.
        windloads: Sub-objeto :class:`WindLoads` para cargas de vento.
    """

    def __init__ (self, building: "Building") -> None:
        """Inicializa o sub-objeto de cargas.

        Args:
            building: Instância de :class:`Building` proprietária.
        """
        self.m_building      = building
        self.precastloads    = PrecastLoads (building, self)
        self.windloads       = WindLoads (building, self)

    def GetLoad (self, prefixo: str) -> Tuple[str, int, int, int, int, float, int, float, float, float, float, int, int, int]:
        """Retorna os parâmetros comuns de um caso simples de carregamento pré-definido TQS.

        Args:
            prefixo: Prefixo ``TQSBuild.PREFIXOxxxx``.

        Returns:
            Tupla ``(titulo, ipermacid, ivigtrans, ireduzida, imulaxi, gamaf,
            igamafd, gamafd, psi0, psi1, psi2, ipavimento, numcasos, istat)``:

            * ``titulo``: título do carregamento.
            * ``ipermacid``: grupo ``0`` permanente / ``1`` acidental / ``2`` excepcional.
            * ``ivigtrans``: ``1`` se afetado pelo caso de viga de transição enrigecida.
            * ``ireduzida``: ``1`` se afetado pelo caso de carga acidental reduzida.
            * ``imulaxi``: ``1`` se aplicar multiplicador de área de pilares ``MULAXI``.
            * ``gamaf``: ponderador de cargas GamaF favorável.
            * ``igamafd``: ``1`` se aplicar ponderador GamaF desfavorável.
            * ``gamafd``: ponderador de cargas GamaF desfavorável.
            * ``psi0``: fator de redução das combinações ELU.
            * ``psi1``: fator de redução das combinações frequentes ELS.
            * ``psi2``: fator de redução das combinações quase permanentes ELS.
            * ``ipavimento``: ``1`` se aplicado nas grelhas do pavimento.
            * ``numcasos``: número de casos diferentes gerados por este carregamento.
            * ``istat``: ``!= 0`` se prefixo indefinido ou erro.
        """
        varprefixo      = ctypes.c_char_p (prefixo.encode(TQS.TQSUtil.CHARSET))
        vartitulo       = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        varmaxnc        = ctypes.c_int (TQS.TQSUtil.MAXNCSTR)
        varipermacid    = ctypes.c_int (0)
        varivigtrans    = ctypes.c_int (0)
        varireduzida    = ctypes.c_int (0)
        varimulaxi      = ctypes.c_int (0)
        vargamaf        = ctypes.c_double (0.)
        varigamafd      = ctypes.c_int (0)
        vargamafd       = ctypes.c_double (0.)
        varpsi0         = ctypes.c_double (0.)
        varpsi1         = ctypes.c_double (0.)
        varpsi2         = ctypes.c_double (0.)
        varipavimento   = ctypes.c_int (0)
        varnumcasos     = ctypes.c_int (0)
        varistat        = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_CARREG (varprefixo, vartitulo, varmaxnc,
                        ctypes.byref (varipermacid), ctypes.byref (varivigtrans),
                        ctypes.byref (varireduzida), ctypes.byref (varimulaxi),
                        ctypes.byref (vargamaf), ctypes.byref (varigamafd),
                        ctypes.byref (vargamafd), ctypes.byref (varpsi0),
                        ctypes.byref (varpsi1), ctypes.byref (varpsi2),
                        ctypes.byref (varipavimento), ctypes.byref (varnumcasos),
                        ctypes.byref (varistat))
        titulo          = vartitulo.value.decode(TQS.TQSUtil.CHARSET)
        ipermacid       = varipermacid.value
        ivigtrans       = varivigtrans.value
        ireduzida       = varireduzida.value
        imulaxi         = varimulaxi.value
        gamaf           = vargamaf.value
        igamafd         = varigamafd.value
        gamafd          = vargamafd.value
        psi0            = varpsi0.value
        psi1            = varpsi1.value
        psi2            = varpsi2.value
        ipavimento      = varipavimento.value
        numcasos        = varnumcasos.value
        istat           = varistat.value
        # Prefixo desconhecido pelo NEDILIB: log do erro mas devolve a tupla mesmo assim
        if              istat != 0:
            TQS.TQSUtil.writef ("TQSBuild: Leitura de cargas com prefixo de carregamento inválido: [%s]" %
                            prefixo)
        return          titulo, ipermacid, ivigtrans, ireduzida, imulaxi, gamaf, igamafd, gamafd, psi0, psi1, psi2, ipavimento, numcasos, istat

    def SetLoad (self, prefixo: str, titulo: str, ipermacid: int, ivigtrans: int, ireduzida: int, imulaxi: int,
                    gamaf: float, igamafd: int, gamafd: float, psi0: float, psi1: float, psi2: float, ipavimento: int, numcasos: int, icasadi: int) -> int:
        """Fixa os parâmetros comuns de um caso simples de carregamento pré-definido TQS.

        Args:
            prefixo: Prefixo ``TQSBuild.PREFIXOxxxx``.
            titulo: Título do carregamento.
            ipermacid: Grupo ``0`` permanente / ``1`` acidental / ``2`` excepcional.
            ivigtrans: ``1`` se afetado pelo caso de viga de transição enrigecida.
            ireduzida: ``1`` se afetado pelo caso de carga acidental reduzida.
            imulaxi: ``1`` se aplicar multiplicador de área de pilares ``MULAXI``.
            gamaf: Ponderador de cargas GamaF favorável.
            igamafd: ``1`` se aplicar ponderador GamaF desfavorável.
            gamafd: Ponderador de cargas GamaF desfavorável.
            psi0: Fator de redução das combinações ELU.
            psi1: Fator de redução das combinações frequentes ELS.
            psi2: Fator de redução das combinações quase permanentes ELS.
            ipavimento: ``1`` se aplicado nas grelhas do pavimento.
            numcasos: Número de casos diferentes gerados por este carregamento.
            icasadi: ``1`` se este é um caso adicional definido pelo usuário.

        Returns:
            ``!= 0`` se prefixo indefinido ou erro.
        """
        varprefixo      = ctypes.c_char_p (prefixo.encode(TQS.TQSUtil.CHARSET))
        vartitulo       = ctypes.c_char_p (titulo.encode(TQS.TQSUtil.CHARSET))
        varipermacid    = ctypes.c_int (ipermacid)
        varivigtrans    = ctypes.c_int (ivigtrans)
        varireduzida    = ctypes.c_int (ireduzida)
        varimulaxi      = ctypes.c_int (imulaxi)
        vargamaf        = ctypes.c_double (gamaf)
        varigamafd      = ctypes.c_int (igamafd)
        vargamafd       = ctypes.c_double (gamafd)
        varpsi0         = ctypes.c_double (psi0)
        varpsi1         = ctypes.c_double (psi1)
        varpsi2         = ctypes.c_double (psi2)
        varipavimento   = ctypes.c_int (ipavimento)
        varnumcasos     = ctypes.c_int (numcasos)
        varicasadi      = ctypes.c_int (icasadi)
        varistat        = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_SET_CARREG (varprefixo, vartitulo, varipermacid,
                        varivigtrans, varireduzida, varimulaxi, vargamaf, varigamafd,
                        vargamafd, varpsi0, varpsi1, varpsi2, varipavimento,
                        varnumcasos, varicasadi, ctypes.byref (varistat))
        istat           = varistat.value
        # Prefixo desconhecido: log do erro e retorno do código de status para o chamador
        if              istat != 0:
            TQS.TQSUtil.writef ("TQSBuild: Definição de cargas com prefixo de carregamento inválido: [%s]" %
                            prefixo)
        istat           = varistat.value
        return          istat


    def CreateLoad (self, prefixo: str) -> int:
        """Cria carregamento com novo prefixo.

        Args:
            prefixo: Prefixo do novo carregamento.

        Returns:
            ``!= 0`` em caso de erro.
        """
        varprefixo      = ctypes.c_char_p (prefixo.encode(TQS.TQSUtil.CHARSET))
        varistat        = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_CRIARCARREG (varprefixo, ctypes.byref (varistat))
        istat           = varistat.value
        return          istat

    def GetAdditionalCasesNumber (self) -> int:
        """Retorna o número de casos adicionais definidos.

        São casos com ``icasadi != 0`` definido.

        Returns:
            Número de casos adicionais.
        """
        varnumcasadi        = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_NUMCASADI (ctypes.byref (varnumcasadi))
        numcasadi       = varnumcasadi.value
        return          numcasadi

    def GetAadditionalCasePrefix (self, icasadi: int) -> str:
        """Retorna o prefixo de um caso adicional.

        Args:
            icasadi: Índice do caso adicional ``0..GetAdditionalCasesNumber()-1``.

        Returns:
            Prefixo do caso adicional.
        """
        varicasadi      = ctypes.c_int (icasadi)
        varprefixo      = ctypes.create_string_buffer (TQS.TQSUtil.MAXNCSTR)
        self.m_building.m_edilib.EDILIB_GET_PRECASADI (varicasadi, varprefixo)
        prefixo         = varprefixo.value.decode(TQS.TQSUtil.CHARSET)
        return          prefixo

    def GetLiveLoadReduction (self, ifloor: int) -> float:
        """Retorna o redutor de sobrecargas para um piso.

        Args:
            ifloor: Número do piso do edifício, começando em zero.

        Returns:
            Redutor de sobrecargas. ``0.`` Não reduz, ``1.`` reduz 100%.
        """
        varifloor       = ctypes.c_int (ifloor)
        varreductor     = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_REDSOBRE (varifloor, ctypes.byref (varreductor))
        reductor        = varreductor.value
        return          reductor

    def SetLiveLoadReduction (self, ifloor: int, reductor: float) -> None:
        """Define um redutor de sobrecargas para um piso.

        Args:
            ifloor: Número do piso do edifício, começando em zero.
            reductor: Redutor de sobrecargas. ``0.`` Não reduz, ``1.`` reduz 100%.
        """
        varifloor       = ctypes.c_int (ifloor)
        varreductor     = ctypes.c_double (reductor)
        self.m_building.m_edilib.EDILIB_SET_REDSOBRE (varifloor, varreductor)

    @property
    def outOfPlumbCases (self) -> int:
        """Número de casos de desaprumo."""
        varnoutofplumb  = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_DESAPRUMO_NUMCASOS (ctypes.byref (varnoutofplumb))
        noutofplumb     = varnoutofplumb.value
        return          noutofplumb

    @outOfPlumbCases.setter
    def outOfPlumbCases (self, noutofplumb: int) -> None:
        """Atribui Número de casos de desaprumo."""
        varnoutofplumb  = ctypes.c_int (noutofplumb)
        self.m_building.m_edilib.EDILIB_SET_DESAPRUMO_NUMCASOS (varnoutofplumb)

    def GetOutOfPlumbleAngle (self, ioopcase: int) -> float:
        """Retorna o ângulo do caso de desaprumo em graus.

        Args:
            ioopcase: Número do caso de desaprumo ``0..outOfPlumbCases-1``.

        Returns:
            Ângulo em planta do caso de desaprumo em graus.
        """
        varioopcase     = ctypes.c_int (ioopcase)
        varangle        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_DESAPRUMO_CASO (varioopcase, ctypes.byref (varangle))
        angle           = varangle.value
        return          angle

    def SetOutOfPlumbleAngle (self, ioopcase: int, angle: float) -> None:
        """Define o ângulo do caso de desaprumo em graus.

        Args:
            ioopcase: Número do caso de desaprumo ``0..outOfPlumbCases-1``.
            angle: Ângulo em planta do caso de desaprumo em graus.
        """
        varioopcase     = ctypes.c_int (ioopcase)
        varangle        = ctypes.c_double (angle)
        self.m_building.m_edilib.EDILIB_SET_DESAPRUMO_CASO (varioopcase, varangle)

#------------------------------------------------------------------------------
#       Cargas de vento
#
class WindLoads ():
    """Cargas de vento (NBR-6123 e ACI-318/CIRSOC).

    Implementação:
        Wrapper sobre três famílias de funções: (1) ``EDILIB_*CASVEN`` para os
        parâmetros gerais NBR-6123 e cada caso direcional; (2) ``EDILIB_*EXCVEN``
        para a lista variável de excentricidades por caso (com ``InitWindEccentricity``
        / ``AddWindEccentricity`` / ``GetWindEccentricity``); (3) campos do EDIFICIO
        de configuração de túnel de vento e parâmetros ACI/CIRSOC, expostos como
        propriedades simples. As tuplas longas de :meth:`GetWindEccentricity` e
        :meth:`AddWindEccentricity` empacotam piso inicial/final, pilar, percentual
        de excentricidade e parâmetros meteorológicos em chamadas únicas.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        m_loads: :class:`Loads` proprietário.
    """

    def __init__ (self, building: "Building", loads: "Loads") -> None:
        """Inicializa o sub-objeto de cargas de vento.

        Args:
            building: Instância de :class:`Building` proprietária.
            loads: Instância de :class:`Loads` proprietária.
        """
        self.m_building      = building
        self.m_loads         = loads

    def GetWindLoadParametersNBR (self) -> Tuple[float, float, int, float, int, int]:
        """Retorna os parâmetros de cálculo de caso de vento pela NBR-6123.

        Returns:
            Tupla ``(windv0, winds1, iwndrug, winds3, iwindclass, numcaswind)``:

            * ``windv0``: velocidade básica (m/s).
            * ``winds1``: fator topográfico.
            * ``iwndrug``: categoria de rugosidade ``I..IV``.
            * ``winds3``: fator estatístico.
            * ``iwindclass``: classe ``0`` A, ``1`` B, ``2`` C.
            * ``numcaswind``: número de casos em direções diferentes.
        """
        varwindv0       = ctypes.c_double (0)
        varwinds1       = ctypes.c_double (0)
        variwndrug      = ctypes.c_int (0)
        varwinds3       = ctypes.c_double (0)
        variwindclass   = ctypes.c_int (0)
        varnumcaswind   = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_CASVEN (ctypes.byref (varwindv0),
                    ctypes.byref (varwinds1), ctypes.byref (variwndrug),
                    ctypes.byref (varwinds3), ctypes.byref (variwindclass),
                    ctypes.byref (varnumcaswind))
        windv0          = varwindv0.value
        winds1          = varwinds1.value
        iwndrug         = variwndrug.value
        winds3          = varwinds3.value
        iwindclass      = variwindclass.value
        numcaswind      = varnumcaswind.value
        return          windv0, winds1, iwndrug, winds3, iwindclass, numcaswind

    def SetWindLoadParametersNBR (self, windv0: float, winds1: float, iwndrug: int, winds3: float, iwindclass: int, numcaswind: int) -> None:
        """Define os parâmetros de cálculo de caso de vento pela NBR-6123.

        Args:
            windv0: Velocidade básica (m/s).
            winds1: Fator topográfico.
            iwndrug: Categoria de rugosidade ``I..IV``.
            winds3: Fator estatístico.
            iwindclass: Classe ``0`` A, ``1`` B, ``2`` C.
            numcaswind: Número de casos em direções diferentes.
        """
        varwindv0       = ctypes.c_double (windv0)
        varwinds1       = ctypes.c_double (winds1)
        variwndrug      = ctypes.c_int (iwndrug)
        varwinds3       = ctypes.c_double (winds3)
        variwindclass   = ctypes.c_int (iwindclass)
        varnumcaswind   = ctypes.c_int (numcaswind)
        self.m_building.m_edilib.EDILIB_SET_CASVEN (varwindv0, varwinds1, variwndrug,
                        varwinds3, variwindclass, varnumcaswind)

    def GetWindLoadCase (self, iwindcase: int) -> Tuple[float, float, int, float]:
        """Retorna os dados de um caso de vento em uma direção.

        Args:
            iwindcase: Número do caso de vento ``0..numcaswind-1``.

        Returns:
            Tupla ``(ca, ang, icti, cti)``:

            * ``ca``: coeficiente de arrasto.
            * ``ang``: ângulo de vento em graus.
            * ``icti``: ``1`` se cota inicial definida.
            * ``cti``: cota inicial (m).
        """
        variwindcase    = ctypes.c_int (iwindcase)
        varca           = ctypes.c_double (0.)
        varang          = ctypes.c_double (0.)
        varicti         = ctypes.c_int (0)
        varcti          = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_CASVEN_ICASO (variwindcase, ctypes.byref (varca),
                        ctypes.byref (varang), ctypes.byref (varicti),
                        ctypes.byref (varcti))
        ca              = varca.value
        ang             = varang.value
        icti            = varicti.value
        cti             = varcti.value
        return          ca, ang, icti, cti

    def SetWindLoadCase (self, iwindcase: int, ca: float, ang: float, icti: int, cti: float) -> None:
        """Define os dados de um caso de vento em uma direção.

        Args:
            iwindcase: Número do caso de vento ``0..numcaswind-1``.
            ca: Coeficiente de arrasto.
            ang: Ângulo de vento em graus.
            icti: ``1`` se cota inicial definida.
            cti: Cota inicial (m).
        """
        variwindcase    = ctypes.c_int (iwindcase)
        varca           = ctypes.c_double (ca)
        varang          = ctypes.c_double (ang)
        varicti         = ctypes.c_int (icti)
        varcti          = ctypes.c_double (cti)
        self.m_building.m_edilib.EDILIB_SET_CASVEN_ICASO (variwindcase, varca,
                        varang, varicti, varcti)

    def InitWindEccentricity (self, iwindcase: int) -> None:
        """Inicializa excenctricidades de vento e outros dados para o caso fornecido.

        Args:
            iwindcase: Número do caso de vento ``0..numcaswind-1``.
        """
        variwindcase    = ctypes.c_int (iwindcase)
        self.m_building.m_edilib.EDILIB_EXCVEN_INICIARCASO (variwindcase)

    def GetWindEccentricityNumber (self, iwindcase: int) -> int:
        """Retorna o número de excentricidades de vento associadas a um caso.

        Args:
            iwindcase: Número do caso de vento ``0..numcaswind-1``.

        Returns:
            Número de excentricidades do caso ``iwindcase``.
        """
        variwindcase    = ctypes.c_int (iwindcase)
        varnumwindecc   = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_EXCVEN_NUMEXCVEN (variwindcase,
                            ctypes.byref (varnumwindecc))
        numwindecc      = varnumwindecc.value
        return          numwindecc

    def AddWindEccentricity (self, iwindcase: int, ipisoi: int, ipisof: int, ipil: int, excven: float, alrgpis: float,
                            forven: float, s2b: float, s2fr: float, s2p: float, forlat: float, amomz: float) -> None:
        """Adiciona excentricidade e outros dados no caso de vento fornecido.

        Args:
            iwindcase: Número do caso de vento ``0..numcaswind-1``.
            ipisoi: Piso inicial (``-1`` o primeiro).
            ipisof: Piso final (``-1`` o último).
            ipil: Número do pilar (``-1`` distribui em todos).
            excven: Excentricidade percentual %.
            alrgpis: Largura imposta do piso (m).
            forven: Força total de vento no piso (tf).
            s2b: Parâmetro meteorológico.
            s2fr: ``Fr`` — fator de rajada.
            s2p: ``p`` — expoente da lei potencial S2.
            forlat: Força lateral de vento (tf).
            amomz: Momento torsor de vento (tfm).
        """
        variwindcase    = ctypes.c_int (iwindcase)
        varipisoi       = ctypes.c_int (ipisoi)
        varipisof       = ctypes.c_int (ipisof)
        varipil         = ctypes.c_int (ipil)
        varexcven       = ctypes.c_double (excven)
        varalrgpis      = ctypes.c_double (alrgpis)
        varforven       = ctypes.c_double (forven)
        vars2b          = ctypes.c_double (s2b)
        vars2fr         = ctypes.c_double (s2fr)
        vars2p          = ctypes.c_double (s2p)
        varforlat       = ctypes.c_double (forlat)
        varamomz        = ctypes.c_double (amomz)
        self.m_building.m_edilib.EDILIB_ADD_EXCVEN (variwindcase, varipisoi, varipisof,
                        varipil, varexcven, varalrgpis, varforven, vars2b, vars2fr,
                        vars2p, varforlat, varamomz)

    def GetWindEccentricity (self, iwindcase: int, iwindexc: int) -> Tuple[int, int, int, float, float, float, float, float, float, float, float]:
        """Retorna a excentricidade e outros dados no caso de vento fornecido.

        Args:
            iwindcase: Número do caso de vento ``0..numcaswind-1``.
            iwindexc: Número da excentricidade ``0..GetWindEccentricityNumber()-1``.

        Returns:
            Tupla ``(ipisoi, ipisof, ipil, excven, alrgpis, forven, s2b, s2fr,
            s2p, forlat, amomz)``:

            * ``ipisoi``: piso inicial (``-1`` o primeiro).
            * ``ipisof``: piso final (``-1`` o último).
            * ``ipil``: número do pilar (``-1`` distribui em todos).
            * ``excven``: excentricidade percentual %.
            * ``alrgpis``: largura imposta do piso (m).
            * ``forven``: força total de vento no piso (tf).
            * ``s2b``: parâmetro meteorológico.
            * ``s2fr``: ``Fr`` — fator de rajada.
            * ``s2p``: ``p`` — expoente da lei potencial S2.
            * ``forlat``: força lateral de vento (tf).
            * ``amomz``: momento torsor de vento (tfm).
        """
        variwindcase    = ctypes.c_int (iwindcase)
        variwindexc     = ctypes.c_int (iwindexc)
        varipisoi       = ctypes.c_int (0)
        varipisof       = ctypes.c_int (0)
        varipil         = ctypes.c_int (0)
        varexcven       = ctypes.c_double (0.)
        varalrgpis      = ctypes.c_double (0.)
        varforven       = ctypes.c_double (0.)
        vars2b          = ctypes.c_double (0.)
        vars2fr         = ctypes.c_double (0.)
        vars2p          = ctypes.c_double (0.)
        varforlat       = ctypes.c_double (0.)
        varamomz        = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_EXCVEN (variwindcase, variwindexc,
                        ctypes.byref (varipisoi), ctypes.byref (varipisof),
                        ctypes.byref (varipil), ctypes.byref (varexcven),
                        ctypes.byref (varalrgpis), ctypes.byref (varforven),
                        ctypes.byref (vars2b), ctypes.byref (vars2fr),
                        ctypes.byref (vars2p), ctypes.byref (varforlat),
                        ctypes.byref (varamomz))
        ipisoi          = varipisoi.value
        ipisof          = varipisof.value
        ipil            = varipil.value
        excven          = varexcven.value
        alrgpis         = varalrgpis.value
        forven          = varforven.value
        s2b             = vars2b.value
        s2fr            = vars2fr.value
        s2p             = vars2p.value
        forlat          = varforlat.value
        amomz           = varamomz.value
        return          ipisoi, ipisof, ipil, excven, alrgpis, forven, s2b, s2fr, s2p, forlat, amomz

    @property
    def windInPlanFloor (self) -> int:
        """``1`` se caso de vento na planta de formas e grelha."""
        return          self.m_building._GetVarInt (EDL_V_ICASOVENTOFOR)#!NTR

    @windInPlanFloor.setter
    def windInPlanFloor (self, cover: int) -> None:
        """Atribui ``1`` se caso de vento na planta de formas e grelha."""
        self.m_building._SetVarInt (EDL_V_ICASOVENTOFOR, cover)#!NTR

    @property
    def windTunnelGlobalSystem (self) -> int:
        """Túnel de vento: ``0`` forças no sistema local, ``1`` sistema global.

        Somente aplicável no momento da leitura da tabela de forças.
        """
        return          self.m_building._GetVarInt (EDL_V_ISISGLOBEXC)#!NTR

    @windTunnelGlobalSystem.setter
    def windTunnelGlobalSystem (self, isisglobexc: int) -> None:
        """Atribui ``0`` forças no sistema local, ``1`` sistema global."""
        self.m_building._SetVarInt (EDL_V_ISISGLOBEXC, isisglobexc)#!NTR

    @property
    def windTunnelInvertSignal (self) -> int:
        """Túnel de vento: ``1`` se inverter sinal."""
        return          self.m_building._GetVarInt (EDL_V_INVERTSN)#!NTR

    @windTunnelInvertSignal.setter
    def windTunnelInvertSignal (self, invertsn: int) -> None:
        """Atribui ``1`` se inverter sinal."""
        self.m_building._SetVarInt (EDL_V_INVERTSN, invertsn)#!NTR

    @property
    def windTunnelIgnoreColumns (self) -> int:
        """Túnel de vento: número de colunas a desprezar."""
        return          self.m_building._GetVarInt (EDL_V_IDESPCOL)#!NTR

    @windTunnelIgnoreColumns.setter
    def windTunnelIgnoreColumns (self, idespcol: int) -> None:
        """Atribui número de colunas a desprezar."""
        self.m_building._SetVarInt (EDL_V_IDESPCOL, idespcol)#!NTR

    @property
    def windTunnelIgnoreLines (self) -> int:
        """Túnel de vento: número de linhas a desprezar."""
        return          self.m_building._GetVarInt (EDL_V_IDESPLIN)#!NTR

    @windTunnelIgnoreLines.setter
    def windTunnelIgnoreLines (self, idesplin: int) -> None:
        """Atribui número de linhas a desprezar."""
        self.m_building._SetVarInt (EDL_V_IDESPLIN, idesplin)#!NTR

    @property
    def windTunnelTopToBottom (self) -> int:
        """Túnel de vento: ``1`` se de cima para baixo."""
        return          self.m_building._GetVarInt (EDL_V_IORDPISO)#!NTR

    @windTunnelTopToBottom.setter
    def windTunnelTopToBottom (self, iordpiso: int) -> None:
        """Atribui ``1`` se de cima para baixo."""
        self.m_building._SetVarInt (EDL_V_IORDPISO, iordpiso)#!NTR

    @property
    def windTunnelFirstFloor (self) -> int:
        """Túnel de vento: primeiro piso da lista ou ``-1``."""
        return          self.m_building._GetVarInt (EDL_V_IPRIMPIS)#!NTR

    @windTunnelFirstFloor.setter
    def windTunnelFirstFloor (self, iprimpis: int) -> None:
        """Atribui primeiro piso da lista ou ``-1``."""
        self.m_building._SetVarInt (EDL_V_IPRIMPIS, iprimpis)#!NTR

    @property
    def windTunnelForcesUnits (self) -> int:
        """Túnel de vento: ``0`` tf e tfm, ``1`` kN e kNm."""
        return          self.m_building._GetVarInt (EDL_V_IUNIDKNM)#!NTR

    @windTunnelForcesUnits.setter
    def windTunnelForcesUnits (self, iunidknm: int) -> None:
        """Atribui ``0`` tf e tfm, ``1`` kN e kNm."""
        self.m_building._SetVarInt (EDL_V_IUNIDKNM, iunidknm)#!NTR

    @property
    def windTunnelInvertExcc (self) -> int:
        """Túnel de vento: ``1`` excentricidades armazenadas com sinal invertido."""
        return          self.m_building._GetVarInt (EDL_V_INVERTSNEXC)#!NTR

    @windTunnelInvertExcc.setter
    def windTunnelInvertExcc (self, invertsnexc: int) -> None:
        """Atribui ``1`` excentricidades armazenadas com sinal invertido."""
        self.m_building._SetVarInt (EDL_V_INVERTSNEXC, invertsnexc)#!NTR

    @property
    def aciBasicWindSpeed (self) -> float:
        """ACI-318: velocidade básica de vento (m/s)."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_V0)

    @aciBasicWindSpeed.setter
    def aciBasicWindSpeed (self, v0: float) -> None:
        """Atribui ACI-318: velocidade básica de vento (m/s)."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_V0, v0)#!NTR

    @property
    def aciNaturalFrequency (self) -> float:
        """ACI-318: frequência natural Hz (``aciStructureStiffness != 0``)."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_FREQNAT)

    @aciNaturalFrequency.setter
    def aciNaturalFrequency (self, fr: float) -> None:
        """Atribui ACI-318: frequência natural Hz (``aciStructureStiffness != 0``)."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_FREQNAT, fr)#!NTR

    @property
    def aciDampingRate (self) -> float:
        """ACI-318: taxa de amortecimento % do valor crítico (``aciStructureStiffness != 0``)."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_TXAMORT)

    @aciDampingRate.setter
    def aciDampingRate (self, dr: float) -> None:
        """Atribui ACI-318: taxa de amortecimento % do valor crítico (``aciStructureStiffness != 0``)."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_TXAMORT, dr)#!NTR

    @property
    def aciStructureStiffness (self) -> int:
        """ACI-318: ``0`` edifício rígido, ``1`` flexível."""
        return          self.m_building._GetVarInt (EDL_V_CIRSOC_IFLEX)#!NTR

    @aciStructureStiffness.setter
    def aciStructureStiffness (self, istiff: int) -> None:
        """Atribui ACI-318: ``0`` edifício rígido, ``1`` flexível."""
        self.m_building._SetVarInt (EDL_V_CIRSOC_IFLEX, istiff)#!NTR

    @property
    def aciTopographicFactor (self) -> float:
        """ACI-318: fator topográfico ``Kzt``."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_AKZT)

    @aciTopographicFactor.setter
    def aciTopographicFactor (self, fact: float) -> None:
        """Atribui ACI-318: fator topográfico ``Kzt``."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_AKZT, fact)#!NTR

    @property
    def aciMinimumWindPressure (self) -> float:
        """ACI-318: pressão mínima de vento (tf/m2)."""
        return          self.m_building._GetVarDouble (EDL_V_CIRSOC_PMINTFM2)

    @aciMinimumWindPressure.setter
    def aciMinimumWindPressure (self, press: float) -> None:
        """Atribui ACI-318: pressão mínima de vento (tf/m2)."""
        self.m_building._SetVarDouble (EDL_V_CIRSOC_PMINTFM2, press)#!NTR

    @property
    def aciOccupancyCategory (self) -> int:
        """ACI-318: natureza de ocupação ``0`` I, ``1`` II, ``2`` III, ``3`` IV."""
        return          self.m_building._GetVarInt (EDL_V_CIRSOC_INATUROCUP)#!NTR

    @aciOccupancyCategory.setter
    def aciOccupancyCategory (self, iocc: int) -> None:
        """Atribui ACI-318: natureza de ocupação ``0`` I, ``1`` II, ``2`` III, ``3`` IV."""
        self.m_building._SetVarInt (EDL_V_CIRSOC_INATUROCUP, iocc)#!NTR

    @property
    def aciExposureCategory (self) -> int:
        """ACI-318: categoria de exposição ``0`` A, ``1`` B, ``2`` C, ``3`` D."""
        return          self.m_building._GetVarInt (EDL_V_CIRSOC_ICATEXPOSI)#!NTR

    @aciExposureCategory.setter
    def aciExposureCategory (self, icat: int) -> None:
        """Atribui ACI-318: categoria de exposição ``0`` A, ``1`` B, ``2`` C, ``3`` D."""
        self.m_building._SetVarInt (EDL_V_CIRSOC_ICATEXPOSI, icat)#!NTR

    @property
    def aciAltitude (self) -> float:
        """ACI-318: altitude da edificação em relação ao nível do mar (m)."""
        return          self.m_building._GetVarDouble (EDL_V_ALTITMAR)#!NTR

    @aciAltitude.setter
    def aciAltitude (self, icat: float) -> None:
        """Atribui ACI-318: altitude da edificação em relação ao nível do mar (m)."""
        self.m_building._SetVarDouble (EDL_V_ALTITMAR, icat)#!NTR

#------------------------------------------------------------------------------
#       Cargas em estruturas pré-moldadas
#
class PrecastLoads ():
    """Cargas em estruturas pré-moldadas (frações nas etapas construtivas).

    Implementação:
        Wrapper sobre as funções ``EDILIB_GET_PREDAD_PERCAR*`` /
        ``EDILIB_SET_PREDAD_PERCAR*``, que devolvem/definem o percentual (em %)
        de cada tipo de carga (peso próprio, permanente, sobrecarga, vento,
        empuxo, temperatura, retração) aplicado durante as etapas construtivas.
        Os campos extras de desaprumo são expostos via ``EDILIB_*_PREDAD_NUMCASODES``
        e ``EDILIB_*_PREDAD_DESAPRUMO``. Cada propriedade é um par get/set simples.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
        m_loads: :class:`Loads` proprietário.
    """

    def __init__ (self, building: "Building", loads: "Loads") -> None:
        """Inicializa o sub-objeto de cargas pré-moldadas.

        Args:
            building: Instância de :class:`Building` proprietária.
            loads: Instância de :class:`Loads` proprietária.
        """
        self.m_building      = building
        self.m_loads         = loads

    @property
    def fracSelfLoadConsStage (self) -> float:
        """Fração % da carga de peso próprio engastado nas etapas construtivas."""
        varfrac         = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_PERCARPPEN (ctypes.byref (varfrac))
        frac            = varfrac.value
        return          frac

    @fracSelfLoadConsStage.setter
    def fracSelfLoadConsStage (self, frac: float) -> None:
        """Atribui Fração % da carga de peso próprio engastado nas etapas construtivas."""
        varfrac         = ctypes.c_double (frac)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_PERCARPPEN (varfrac)

    @property
    def fracDeadLoadConsStage (self) -> float:
        """Fração % da carga permanente nas etapas construtivas."""
        varfrac         = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_PERCARPERM (ctypes.byref (varfrac))
        frac            = varfrac.value
        return          frac

    @fracDeadLoadConsStage.setter
    def fracDeadLoadConsStage (self, frac: float) -> None:
        """Atribui Fração % da carga permanente nas etapas construtivas."""
        varfrac         = ctypes.c_double (frac)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_PERCARPERM (varfrac)

    @property
    def fracLiveLoadConsStage (self) -> float:
        """Fração % de sobrecargas nas etapas construtivas."""
        varfrac         = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_PERCARSOBR (ctypes.byref (varfrac))
        frac            = varfrac.value
        return          frac

    @fracLiveLoadConsStage.setter
    def fracLiveLoadConsStage (self, frac: float) -> None:
        """Atribui Fração % de sobrecargas nas etapas construtivas."""
        varfrac         = ctypes.c_double (frac)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_PERCARSOBR (varfrac)

    @property
    def fracWindConsStage (self) -> float:
        """Fração % de carga de vento nas etapas construtivas."""
        varfrac         = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_PERCARVENT (ctypes.byref (varfrac))
        frac            = varfrac.value
        return          frac

    @fracWindConsStage.setter
    def fracWindConsStage (self, frac: float) -> None:
        """Atribui Fração % de carga de vento nas etapas construtivas."""
        varfrac         = ctypes.c_double (frac)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_PERCARVENT (varfrac)

    @property
    def fracEarthPressureStage (self) -> float:
        """Fração % de carga de empuxo de terra nas etapas construtivas."""
        varfrac         = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_PERCAREMPU (ctypes.byref (varfrac))
        frac            = varfrac.value
        return          frac

    @fracEarthPressureStage.setter
    def fracEarthPressureStage (self, frac: float) -> None:
        """Atribui Fração % de carga de empuxo de terra nas etapas construtivas."""
        varfrac         = ctypes.c_double (frac)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_PERCAREMPU (varfrac)

    @property
    def fracTemperatureStage (self) -> float:
        """Fração % de carga de temperatura nas etapas construtivas."""
        varfrac         = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_PERCARTEMP (ctypes.byref (varfrac))
        frac            = varfrac.value
        return          frac

    @fracTemperatureStage.setter
    def fracTemperatureStage (self, frac: float) -> None:
        """Atribui Fração % de carga de temperatura nas etapas construtivas."""
        varfrac         = ctypes.c_double (frac)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_PERCARTEMP (varfrac)

    @property
    def fracShrinkageStage (self) -> float:
        """Fração % de carga de retração nas etapas construtivas."""
        varfrac         = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_PERCARRETR (ctypes.byref (varfrac))
        frac            = varfrac.value
        return          frac

    @fracShrinkageStage.setter
    def fracShrinkageStage (self, frac: float) -> None:
        """Atribui Fração % de carga de retração nas etapas construtivas."""
        varfrac         = ctypes.c_double (frac)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_PERCARRETR (varfrac)

    @property
    def outOfPlumbNumber (self) -> float:
        """Número de casos de desaprumo."""
        varfrac         = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_NUMCASODES (ctypes.byref (varfrac))
        frac            = varfrac.value
        return          frac

    @outOfPlumbNumber.setter
    def outOfPlumbNumber (self, frac: float) -> None:
        """Atribui Número de casos de desaprumo."""
        varfrac         = ctypes.c_double (frac)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_NUMCASODES (varfrac)

    @property
    def outOfPlumbInverseAngle (self) -> float:
        """Inverso do ângulo de desaprumo."""
        varinvangle     = ctypes.c_double (0.)
        self.m_building.m_edilib.EDILIB_GET_PREDAD_DESAPRUMO (ctypes.byref (varinvangle))
        invangle        = varinvangle.value
        return          invangle

    @outOfPlumbInverseAngle.setter
    def outOfPlumbInverseAngle (self, invangle: float) -> None:
        """Atribui Inverso do ângulo de desaprumo."""
        varinvangle     = ctypes.c_double (invangle)
        self.m_building.m_edilib.EDILIB_SET_PREDAD_DESAPRUMO (varinvangle)

#------------------------------------------------------------------------------
#       Aba Gerenciamento
#
class Management ():
    """Aba "Gerenciamento": GerPrE, ferros corridos, formatos exigidos.

    Implementação:
        Wrapper sobre as funções ``EDILIB_GET_GERPRE`` / ``EDILIB_SET_GERPRE``, que
        leem/escrevem em bloco a tupla ``(icgerpre, iconsfer, iapdfpla, iadwfpla,
        iadxfpla)``. Cada propriedade individual obtém o vetor inteiro via
        :meth:`_GetGerPre`, substitui o campo desejado e regrava com :meth:`_SetGerPre`,
        para preservar os demais campos.

    Attributes:
        m_building: Edifício :class:`Building` proprietário.
    """

    def __init__ (self, building: "Building") -> None:
        """Inicializa o sub-objeto de gerenciamento.

        Args:
            building: Instância de :class:`Building` proprietária.
        """
        self.m_building      = building

    def _GetGerPre (self) -> Tuple[int, int, int, int, int]:
        """Retorna a tupla de configurações do GerPrE.

        Returns:
            Tupla ``(icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla)``.
        """
        varicgerpre     = ctypes.c_int (0)
        variconsfer     = ctypes.c_int (0)
        variapdfpla     = ctypes.c_int (0)
        variadwfpla     = ctypes.c_int (0)
        variadxfpla     = ctypes.c_int (0)
        self.m_building.m_edilib.EDILIB_GET_GERPRE (ctypes.byref (varicgerpre),
                        ctypes.byref (variconsfer), ctypes.byref (variapdfpla),
                        ctypes.byref (variadwfpla), ctypes.byref (variadxfpla))
        icgerpre        = varicgerpre.value
        iconsfer        = variconsfer.value
        iapdfpla        = variapdfpla.value
        iadwfpla        = variadwfpla.value
        iadxfpla        = variadxfpla.value
        return          icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla

    def _SetGerPre (self, icgerpre: int, iconsfer: int, iapdfpla: int, iadwfpla: int, iadxfpla: int) -> None:
        """Define a tupla de configurações do GerPrE.

        Args:
            icgerpre: ``1`` se controle/transferência para o GerPrE ativada.
            iconsfer: ``1`` para verificar a existência de ferros corridos/variáveis.
            iapdfpla: ``1`` se PDF de plantas requerido.
            iadwfpla: ``1`` se DWF de plantas requerido.
            iadxfpla: ``1`` se DXF de plantas requerido.
        """
        varicgerpre     = ctypes.c_int (icgerpre)
        variconsfer     = ctypes.c_int (iconsfer)
        variapdfpla     = ctypes.c_int (iapdfpla)
        variadwfpla     = ctypes.c_int (iadwfpla)
        variadxfpla     = ctypes.c_int (iadxfpla)
        self.m_building.m_edilib.EDILIB_SET_GERPRE (varicgerpre, variconsfer,
                        variapdfpla, variadwfpla, variadxfpla)

    @property
    def gerpreActive (self) -> int:
        """``1`` se controle e transferência para o GerPrE ativada."""
        icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla = self._GetGerPre ()
        return          icgerpre

    @gerpreActive.setter
    def gerpreActive (self, icgerpre: int) -> None:
        """Atribui ``1`` se controle e transferência para o GerPrE ativada."""
        icgerpre2, iconsfer, iapdfpla, iadwfpla, iadxfpla = self._GetGerPre ()
        self._SetGerPre (icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla)

    @property
    def checkVariableRebar (self) -> int:
        """``1`` para verificar a existência de ferros corridos e variáveis."""
        icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla = self._GetGerPre ()
        return          iconsfer

    @checkVariableRebar.setter
    def checkVariableRebar (self, iconsfer: int) -> None:
        """Atribui ``1`` para verificar a existência de ferros corridos e variáveis."""
        icgerpre, iconsfer2, iapdfpla, iadwfpla, iadxfpla = self._GetGerPre ()
        self._SetGerPre (icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla)

    @property
    def pdfRequired (self) -> int:
        """``1`` se PDF de plantas requerido."""
        icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla = self._GetGerPre ()
        return          iapdfpla

    @pdfRequired.setter
    def pdfRequired (self, iapdfpla: int) -> None:
        """Atribui ``1`` se PDF de plantas requerido."""
        icgerpre, iconsfer, iapdfpla2, iadwfpla, iadxfpla = self._GetGerPre ()
        self._SetGerPre (icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla)

    @property
    def dwfRequired (self) -> int:
        """``1`` se DWF de plantas requerido."""
        icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla = self._GetGerPre ()
        return          iadwfpla

    @dwfRequired.setter
    def dwfRequired (self, iadwfpla: int) -> None:
        """Atribui ``1`` se DWF de plantas requerido."""
        icgerpre, iconsfer, iapdfpla, iadwfpla2, iadxfpla = self._GetGerPre ()
        self._SetGerPre (icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla)

    @property
    def dxfRequired (self) -> int:
        """``1`` se DXF de plantas requerido."""
        icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla = self._GetGerPre ()
        return          iadxfpla

    @dxfRequired.setter
    def dxfRequired (self, iadxfpla: int) -> None:
        """Atribui ``1`` se DXF de plantas requerido."""
        icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla2 = self._GetGerPre ()
        self._SetGerPre (icgerpre, iconsfer, iapdfpla, iadwfpla, iadxfpla)
