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
#    TQSUTIL.PY        Utilidades TQS
#                      Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
import inspect
import tkinter.messagebox
import ctypes
import winreg
import sys
import os
from typing import NoReturn

#-----------------------------------------------------------------------------
#    Constantes auxiliares
#
PI:       float = 3.1415926535897932              # Constante PI
RADGRAUS: float = 180./PI                         # Conversão graus radianos
GRAUSRAD: float = PI/180.                         # Conversão radianos graus
CHARSET:  str   = "latin-1"                       #!NTR Caracteres usados nos fontes
MAXNCSTR: int   = 256                             # Número máximo de caracteres de strings
                                                  # Limite dos strings recebidos das DLLs C++
#-----------------------------------------------------------------------------
#    Variáveis globais
#
__jmsgdll:      ctypes.WinDLL | None = None       # JMSGDLL.DLL
__pastaProgram: str                  = ""         # Pasta EXEC
__pastaSuporte: str                  = ""         # Pasta SUPORTE
__pastaUsuario: str                  = ""         # Pasta USUARIO
#-----------------------------------------------------------------------------
#   Verifica DLLs carregadas
#
def __VerifyDlls () -> None:
    """Carrega ``JMSGDLL.DLL`` se ainda não foi carregada nesta sessão.

    Função interna idempotente — chamadas subsequentes são no-op.
    """
    global             __jmsgdll
    if                 __jmsgdll != None:
        return
    __jmsgdll           = LoadDll ("JMSGDLL.DLL")

#-----------------------------------------------------------------------------
#   Verifica strings das pastas TQS Carregados
#
def __VerifyFolfers () -> None:
    """Carrega os caminhos das pastas TQS a partir do Registro do Windows.

    Lê de ``HKEY_LOCAL_MACHINE\\SOFTWARE\\TQS`` os valores ``Programas``,
    ``Suporte`` e ``Usuario`` e armazena em variáveis de módulo.

    Chamada necessária antes de :func:`LoadDll` se nenhuma impressão foi
    feita com :func:`writef`. Idempotente após a primeira execução bem
    sucedida.
    """
    global             __pastaProgram, __pastaSuporte, __pastaUsuario
    if                 len (__pastaProgram) > 0 and len (__pastaSuporte) > 0 and len (__pastaUsuario) > 0:
        return
    sKey               = "SOFTWARE\\TQS"#!NTR
    hReg               = winreg.ConnectRegistry (None, winreg.HKEY_LOCAL_MACHINE)
    hKey               = winreg.OpenKey (hReg, sKey)
    __pastaProgram, itype = winreg.QueryValueEx (hKey, "Programas")#!NTR
    __pastaProgram      += "\\X64"
    __pastaSuporte, itype = winreg.QueryValueEx (hKey, "Suporte")#!NTR
    __pastaUsuario, itype = winreg.QueryValueEx (hKey, "Usuario")#!NTR
    winreg.CloseKey    (hKey)
    winreg.CloseKey    (hReg)

#-----------------------------------------------------------------------------
#   Carrega e retorna handle para uma DLL
#
def LoadDll (libname: str) -> ctypes.WinDLL:
    """Carrega uma DLL/EXE da pasta de programas TQS e retorna seu handle.

    Resolve o caminho completo concatenando :func:`ProgramsFolder` com
    ``libname``. Em caso de falha exibe ``messagebox`` de erro.

    ATENÇÃO: a função troca o diretório corrente do processo para a pasta de
    programas e só o restaura depois de ``LoadLibrary`` retornar. Se
    ``LoadLibrary`` levantar exceção (arquivo ausente, bitness incompatível), o
    ``os.chdir`` de volta não é executado e o processo permanece com o diretório
    corrente alterado, quebrando caminhos relativos usados depois. Ao tratar
    falhas de carga, restaure o diretório por conta própria.

    Args:
        libname: Nome do arquivo (``.DLL`` ou ``.EXE``) a carregar, sem caminho.

    Returns:
        Handle ``ctypes.WinDLL`` da biblioteca carregada.
    """
    __VerifyFolfers    ()
    global             __pastaProgram
    # Monta o caminho absoluto da DLL: <pastaPrograms>\<libname>
    nomearqdll         = __pastaProgram
    # Salva o cwd e move para a pasta de programas — algumas DLLs do TQS dependem
    # de carregar bibliotecas auxiliares relativas ao cwd, daí esse "passeio".
    dirsalvo            = os.getcwd()
    os.chdir            (__pastaProgram)
    if                 __pastaProgram [len (__pastaProgram)-1] != '\\':
        nomearqdll     += "\\"
    nomearqdll         += libname
    hlib               = ctypes.windll.LoadLibrary (nomearqdll)
    if                 hlib == None:
        tkinter.messagebox.showerror(title="Biblioteca não encontrada", message=nomearqdll)
    # Sempre restaura o cwd original, mesmo em caso de erro reportado por messagebox
    os.chdir            (dirsalvo)
    return             hlib

#-----------------------------------------------------------------------------
#    Rotina de impressão de mensagens via JMSG.EXE
#
def writef (*args: object) -> None:
    """Imprime mensagens em janela TQS com número variável de argumentos.

    Concatena ``str(arg)`` de todos os argumentos e despacha para a janela
    de mensagens do TQS via ``JMSGDLL.writej``.

    Args:
        *args: Objetos a serem convertidos em string e concatenados na mensagem.
    """
    __VerifyDlls       ()
    if                 __jmsgdll == None:
        return
    txt                 = ""
    for                 msg in args:
        txt             += str (msg)
    par                 = ctypes.c_char_p (txt.encode(CHARSET))
    __jmsgdll.writej     (par)
#-----------------------------------------------------------------------------
#    Rotina de debug igual a ASMLIB::DEBW
#
def DEBW () -> int:
    """Imprime nome do arquivo e número da linha do chamador (debug).

    Equivalente a ``ASMLIB::DEBW`` do TQS C++.

    Returns:
        Sempre ``0``.
    """
    __VerifyDlls       ()
    caller             = inspect.getframeinfo (inspect.stack()[1][0])
    writef             ("[%s] [%d]" % (caller.filename, caller.lineno))
    return             0
#-----------------------------------------------------------------------------
#    Retorna pastas padrão TQS lidas do Registry
#
def ProgramsFolder () -> str:
    """Retorna a pasta de programas TQS lida do Registro.

    Returns:
        Caminho absoluto da pasta de programas TQS (subpasta ``\\X64``).
    """
    __VerifyFolfers    ()
    return             (__pastaProgram)

def SupportFolder () -> str:
    """Retorna a pasta de arquivos de suporte TQS lida do Registro.

    Returns:
        Caminho absoluto da pasta de arquivos de suporte TQS.
    """
    __VerifyFolfers    ()
    return             (__pastaSuporte)

def UserFolder () -> str:
    """Retorna a pasta de arquivos de usuário TQS lida do Registro.

    Returns:
        Caminho absoluto da pasta de arquivos de usuário TQS.
    """
    __VerifyFolfers    ()
    return             (__pastaUsuario)
#-----------------------------------------------------------------------------
#    Mostra o resultado de uma exceção genérica
#
def ShowException (e: BaseException) -> NoReturn:
    """Mostra detalhes de uma exceção (classe, mensagem, traceback) e re-lança.

    Imprime a classe da exceção, a mensagem ``str(e)`` e, para cada frame
    do traceback, o arquivo, função e linha em que ocorreu o erro. Ao final
    re-lança a exceção corrente com ``raise``.

    Args:
        e: Exceção capturada (deve ser chamada dentro de um bloco ``except``).

    Raises:
        BaseException: Re-lança a exceção corrente.
    """
    __VerifyDlls       ()
    iprimeira          = 0
    # Captura o traceback da exceção corrente e inverte para imprimir do mais
    # recente para o mais antigo (chamador mais próximo do erro primeiro).
    frames             = inspect.trace()
    frames.reverse     ()
    iprim               = 1
    for                fr in frames:
        # No primeiro frame imprime cabeçalho com a classe e mensagem da exceção
        if             (iprim != 0):
            writef     ("Classe      ", str (sys.exc_info()[0]))
            writef     ("Erro        ", str (e))
            iprim       = 0
        # Para cada frame, imprime arquivo/função/linha + contexto de código
        caller         = inspect.getframeinfo (fr [0])
        writef         ("TQS Erro em [%s] [%s] [%d]" %
                        (caller.filename, caller.function, caller.lineno))
        writef         (caller.code_context)
        writef         ("")
    # Re-lança a exceção corrente para que o chamador também a veja
    raise

#-----------------------------------------------------------------------------
#    Executa programa na pasta TQS
#
def ExecTqs (command: str) -> None:
    """Executa um programa e seus parâmetros na pasta ``TQSW\\EXEC``.

    Args:
        command: Linha de comando — nome do executável seguido dos argumentos.
    """
    linhacmd    = ProgramsFolder () + "\\" + command
    os.system   (linhacmd)
