"""
Backups de segurança do AUTQS.

Todo arquivo que o AUTQS vai sobrescrever é copiado antes para a subpasta
BACKUP_PASTA ("backup_claude") ao lado do original, com o nome
<nome>_BKP_<aaaammdd_hhmmss><ext>. Assim os backups não se misturam com os
arquivos do TQS (o Editor de Plantas, por exemplo, não os lista como plantas).
"""
import os
import shutil
from datetime import datetime
from typing import Optional

BACKUP_PASTA = "backup_claude"


def timestamp_backup() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def caminho_backup(caminho_arquivo: str, ts: Optional[str] = None) -> str:
    """Caminho do backup de um arquivo, em <pasta do arquivo>\\backup_claude."""
    pasta, nome = os.path.split(os.path.abspath(caminho_arquivo))
    base, ext = os.path.splitext(nome)
    return os.path.join(pasta, BACKUP_PASTA, f"{base}_BKP_{ts or timestamp_backup()}{ext}")


def criar_backup(caminho_arquivo: str, ts: Optional[str] = None) -> Optional[str]:
    """Copia o arquivo para backup_claude; devolve o caminho do backup (None se o arquivo não existe)."""
    if not os.path.isfile(caminho_arquivo):
        return None
    destino = caminho_backup(caminho_arquivo, ts)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy2(caminho_arquivo, destino)
    return destino
