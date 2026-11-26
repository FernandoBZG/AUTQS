import os
import sys
import types
import winreg
from typing import Tuple

def _assegurar_pacote_tqs_disponivel():
    """
    Garante que 'import TQS' funcione em qualquer computador, mesmo que o usuário
    não tenha instalado o pacote TQS globalmente no site-packages do Python.
    Utiliza as bibliotecas oficiais do TQS fornecidas em src/reference.
    """
    try:
        import TQS
    except ImportError:
        caminho_ref = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reference"))
        if os.path.isdir(caminho_ref):
            tqs_pkg = types.ModuleType("TQS")
            tqs_pkg.__path__ = [caminho_ref]
            tqs_pkg.__file__ = os.path.join(caminho_ref, "__init__.py")
            sys.modules["TQS"] = tqs_pkg
            if caminho_ref not in sys.path:
                sys.path.insert(0, caminho_ref)

_assegurar_pacote_tqs_disponivel()

def configurar_ambiente_tqs_64() -> Tuple[str, str, str]:
    """
    Localiza e configura o carregamento das DLLs do TQS V25 em modo 64-bit (X64).
    Garante que os ponteiros e caminhos das pastas de Programas, Suporte e Usuário
    sejam inicializados corretamente no TQSUtil em qualquer computador.
    """
    pasta_programas = ""
    pasta_suporte = ""
    pasta_usuario = ""

    # 1. Tenta ler do Registro do Windows (HKLM e HKCU, 64 e 32 bits)
    chaves_registro = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\TQS"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\TQS"),
    ]
    flags_view = [winreg.KEY_READ | winreg.KEY_WOW64_64KEY, winreg.KEY_READ | winreg.KEY_WOW64_32KEY, winreg.KEY_READ]

    for hroot, subkey in chaves_registro:
        if pasta_programas:
            break
        for fv in flags_view:
            try:
                with winreg.OpenKey(hroot, subkey, 0, fv) as hkey:
                    pasta_programas, _ = winreg.QueryValueEx(hkey, "Programas")
                    pasta_suporte, _ = winreg.QueryValueEx(hkey, "Suporte")
                    pasta_usuario, _ = winreg.QueryValueEx(hkey, "Usuario")
                    if os.path.exists(pasta_programas):
                        break
            except Exception:
                pass

    # 2. Se não encontrou no registro, faz varredura nos discos padrão do Windows
    if not pasta_programas or not os.path.exists(pasta_programas):
        for drive in ["C", "D", "E", "F"]:
            candidato_exec = fr"{drive}:\TQSW\EXEC"
            if os.path.exists(candidato_exec):
                pasta_programas = candidato_exec
                pasta_suporte = fr"{drive}:\TQSW\SUPORTE"
                pasta_usuario = fr"{drive}:\TQSW\USUARIO"
                break

    # 3. Garante que utilizamos a pasta X64 para compatibilidade com Python 64 bits
    pasta_x64 = os.path.join(pasta_programas, "X64") if pasta_programas else ""
    if not os.path.exists(pasta_x64):
        for drive in ["C", "D", "E", "F"]:
            cand_x64 = fr"{drive}:\TQSW\EXEC\X64"
            if os.path.exists(cand_x64):
                pasta_x64 = cand_x64
                if not pasta_suporte:
                    pasta_suporte = fr"{drive}:\TQSW\SUPORTE"
                if not pasta_usuario:
                    pasta_usuario = fr"{drive}:\TQSW\USUARIO"
                break

    # 4. Adiciona ao DLL search path do Windows no Python 3.8+ e ao PATH de ambiente
    if pasta_x64 and os.path.exists(pasta_x64):
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(pasta_x64)
            except OSError:
                pass
        os.environ["PATH"] = pasta_x64 + os.pathsep + os.environ.get("PATH", "")

    # 5. Atualiza variáveis internas do TQSUtil
    try:
        from TQS import TQSUtil
        TQSUtil.__pastaProgram = pasta_x64
        TQSUtil.__pastaSuporte = pasta_suporte
        TQSUtil.__pastaUsuario = pasta_usuario
    except Exception:
        pass

    # 6. Corrige o setter de nível da classe TQSDwg.Draw para usar g_desniv em níveis numéricos.
    # No binding nativo do TQS, dwg.draw.level chama g_desnivalfa, o que falha silenciosamente
    # para níveis numéricos (ex: 3, 9, 12, 21, 100, 222, 250), desenhando tudo no nível 0.
    try:
        from TQS import TQSDwg
        import ctypes

        def _set_dwg_level(self, level):
            parpedmv = ctypes.c_void_p(self.m_dwg.m_pedmv)
            try:
                parnivel = ctypes.c_int(int(level))
                self.m_dwg.m_mdwg.g_desniv(parpedmv, ctypes.byref(parnivel))
            except (ValueError, TypeError):
                parlevel = ctypes.c_char_p(str(level).encode('latin1'))
                nivel = ctypes.c_int(0)
                self.m_dwg.m_mdwg.g_desnivalfa(parpedmv, parlevel, ctypes.byref(nivel))

        TQSDwg.Draw.level = property(TQSDwg.Draw.level.fget, _set_dwg_level)
    except Exception:
        pass

    return pasta_x64, pasta_suporte, pasta_usuario

# Inicializa o ambiente ao importar o módulo
PASTA_X64, PASTA_SUPORTE, PASTA_USUARIO = configurar_ambiente_tqs_64()
