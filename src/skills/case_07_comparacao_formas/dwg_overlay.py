import os
import shutil
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64

# Mapa oficial de cores TQS (0..15) herdado de 'Comparar geometrias'
TQS_COLOR_MAP: Dict[int, str] = {
    0: "Preto",
    1: "Vermelho",
    2: "Amarelo",
    3: "Verde",
    4: "Ciano",
    5: "Azul",
    6: "Rosa",
    7: "Branco",
    8: "Cinza",
    9: "Laranja",
    10: "Marrom",
    11: "Verde Escuro",
    12: "Azul Brim",
    13: "Azul Escuro",
    14: "Roxo",
    15: "Cinza Claro",
}

TQS_COLOR_NAME_TO_CODE: Dict[str, int] = {
    "preto": 0, "black": 0,
    "vermelho": 1, "red": 1,
    "amarelo": 2, "yellow": 2,
    "verde": 3, "green": 3,
    "ciano": 4, "cyan": 4,
    "azul": 5, "blue": 5,
    "rosa": 6, "magenta": 6,
    "branco": 7, "white": 7,
    "cinza": 8, "gray": 8, "grey": 8,
    "laranja": 9, "orange": 9,
    "marrom": 10, "brown": 10,
    "verde escuro": 11,
    "azul brim": 12,
    "azul escuro": 13,
    "roxo": 14, "purple": 14,
    "cinza claro": 15,
}

# Cores padrão quando não especificadas explicitamente para N arquivos
DEFAULT_OVERLAY_COLORS: List[int] = [8, 3, 1, 4, 2, 6, 5, 9]


def resolver_cor_tqs(cor: Union[int, str]) -> int:
    """Converte nome de cor ou inteiro para código de cor TQS válido (0..15)."""
    if isinstance(cor, int):
        if 0 <= cor <= 15:
            return cor
        raise ValueError(f"Código de cor TQS fora da faixa (0..15): {cor}")
    if isinstance(cor, str):
        chave = cor.strip().lower()
        if chave.isdigit():
            return resolver_cor_tqs(int(chave))
        if chave in TQS_COLOR_NAME_TO_CODE:
            return TQS_COLOR_NAME_TO_CODE[chave]
    raise ValueError(f"Cor TQS desconhecida: {cor!r}")


def _remover_extensao_dwg(caminho: str) -> str:
    """Remove a extensão .DWG/.dwg para uso nas APIs do TQSDwg (que adicionam .DWG automaticamente)."""
    if caminho.lower().endswith(".dwg"):
        return caminho[:-4]
    return caminho


def sobrepor_dwgs_coloridos(
    arquivos_com_cores: List[Tuple[str, Union[int, str]]],
    caminho_saida: Optional[str] = None,
) -> Dict[str, object]:
    """
    Sobrepõe dois ou mais arquivos .DWG nativos do TQS em um único DWG comparativo,
    alterando a cor de todas as entidades de cada arquivo antes da mesclagem (DwgMix).

    Baseado no fluxo de 'Comparar geometrias' (ModifyColor + DwgMix na origem 0,0),
    isolado em diretório temporário para não poluir o workspace.

    :param arquivos_com_cores: Lista de tuplas (caminho_dwg, cor_tqs). Mínimo 2 arquivos.
    :param caminho_saida: Caminho do DWG final. Se omitido, salva COMPARACAO_<timestamp>.DWG
                          na pasta do primeiro arquivo.
    :return: Dicionário com status, caminho_saida_dwg e legenda das cores aplicadas.
    """
    if not arquivos_com_cores or len(arquivos_com_cores) < 2:
        raise ValueError("São necessários pelo menos 2 arquivos DWG para sobreposição.")

    arquivos_validados: List[Tuple[str, int]] = []
    for caminho, cor in arquivos_com_cores:
        caminho_abs = os.path.abspath(caminho)
        if not os.path.isfile(caminho_abs) or not caminho_abs.lower().endswith(".dwg"):
            raise FileNotFoundError(f"Arquivo DWG inválido ou não encontrado: {caminho}")
        arquivos_validados.append((caminho_abs, resolver_cor_tqs(cor)))

    if not caminho_saida:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta_base = os.path.dirname(arquivos_validados[0][0])
        caminho_saida = os.path.join(pasta_base, f"COMPARACAO_{timestamp}.DWG")
    else:
        caminho_saida = os.path.abspath(caminho_saida)
        if not caminho_saida.lower().endswith(".dwg"):
            caminho_saida += ".DWG"

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)

    configurar_ambiente_tqs_64()
    from TQS import TQSDwg

    temp_dir = tempfile.mkdtemp(prefix="autqs_cmp_")
    dwg = TQSDwg.Dwg()
    legenda = []

    try:
        temp_base = os.path.join(temp_dir, "TEMP_BASE")

        for idx, (filepath, color_code) in enumerate(arquivos_validados):
            dwg.file.Open(_remover_extensao_dwg(filepath))
            dwg.iterator.Begin()
            modificados = 0
            while True:
                itipo = dwg.iterator.Next()
                if itipo == TQSDwg.DWGTYPE_EOF:
                    break
                addr = dwg.iterator.GetElementReadPosition()
                dwg.edit.ModifyColor(addr, color_code)
                modificados += 1

            if idx == 0:
                dwg.file.SaveAs(temp_base)
                dwg.file.Close()
            else:
                temp_i = os.path.join(temp_dir, f"TEMP_{idx}")
                dwg.file.SaveAs(temp_i)
                dwg.file.Close()

                dwg.file.Open(temp_base)
                dwg.draw.DwgMix(temp_i, 0, 0)
                dwg.file.Save()
                dwg.file.Close()

            legenda.append({
                "arquivo": os.path.basename(filepath),
                "caminho": filepath,
                "cor_codigo": color_code,
                "cor_nome": TQS_COLOR_MAP.get(color_code, str(color_code)),
                "entidades_coloridas": modificados,
            })

        dwg.file.Open(temp_base)
        dwg.file.SaveAs(_remover_extensao_dwg(caminho_saida))
        dwg.file.Close()

        return {
            "sucesso": True,
            "caminho_saida_dwg": caminho_saida,
            "legenda_cores": legenda,
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
