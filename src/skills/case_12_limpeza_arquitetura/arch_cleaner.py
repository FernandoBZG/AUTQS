import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Set

try:
    import ezdxf
    from ezdxf.math import Matrix44
except ImportError:
    ezdxf = None
    Matrix44 = None

try:
    from TQS import TQSDwg
except ImportError:
    TQSDwg = None


@dataclass
class LimpezaArquiteturaResultado:
    """Resultado da padronização e higienização de DWG/DXF de arquitetura para o TQS."""
    arquivo_origem: str
    arquivo_destino: str
    entidades_originais: int = 0
    entidades_mantidas: int = 0
    hachuras_removidas: int = 0
    cotas_removidas: int = 0
    blocos_parasitas_removidos: int = 0
    camadas_purgadas: List[str] = field(default_factory=list)
    camadas_preservadas: List[str] = field(default_factory=list)
    fator_escala_aplicado: float = 1.0
    bounds_originais: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    bounds_finais: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    def para_dict(self) -> Dict[str, Any]:
        return {
            "arquivo_origem": self.arquivo_origem,
            "arquivo_destino": self.arquivo_destino,
            "metricas": {
                "entidades_originais": self.entidades_originais,
                "entidades_mantidas": self.entidades_mantidas,
                "hachuras_removidas": self.hachuras_removidas,
                "cotas_removidas": self.cotas_removidas,
                "blocos_parasitas_removidos": self.blocos_parasitas_removidos,
                "total_camadas_purgadas": len(self.camadas_purgadas),
            },
            "camadas_purgadas": self.camadas_purgadas,
            "camadas_preservadas": self.camadas_preservadas,
            "fator_escala": self.fator_escala_aplicado,
            "bounds_finais_cm": {
                "min_x": round(self.bounds_finais[0], 2),
                "min_y": round(self.bounds_finais[1], 2),
                "max_x": round(self.bounds_finais[2], 2),
                "max_y": round(self.bounds_finais[3], 2),
                "largura": round(self.bounds_finais[2] - self.bounds_finais[0], 2),
                "comprimento": round(self.bounds_finais[3] - self.bounds_finais[1], 2),
            }
        }

    def para_resumo_executivo(self) -> str:
        """Gera resumo em Markdown da limpeza e padronização realizada."""
        dx = self.bounds_finais[2] - self.bounds_finais[0]
        dy = self.bounds_finais[3] - self.bounds_finais[1]
        linhas = [
            f"# LIMPEZA E PADRONIZAÇÃO DE ARQUITETURA PARA TQS (Geo_*.DXF)",
            f"- **Arquivo de Entrada:** `{os.path.basename(self.arquivo_origem)}`",
            f"- **Arquivo Gerado:** `{os.path.basename(self.arquivo_destino)}`",
            f"- **Fator de Escala Aplicado:** `{self.fator_escala_aplicado}x` ({'Metros para Centímetros' if self.fator_escala_aplicado == 100.0 else 'Mantido original'})\n",
            "### 1. Higienização de Entidades Gráficas",
            f"- **Entidades Analisadas:** `{self.entidades_originais}`",
            f"- **Entidades Preservadas no Modelo:** `{self.entidades_mantidas}`",
            f"- **Hachuras Pesadas Eliminadas:** `{self.hachuras_removidas}`",
            f"- **Cotas e Dimensões Purgadas:** `{self.cotas_removidas}`",
            f"- **Blocos / Entidades Parasitas Removidos:** `{self.blocos_parasitas_removidos}`",
            f"- **Camadas Filtradas:** `{len(self.camadas_purgadas)}` excluídas | `{len(self.camadas_preservadas)}` mantidas\n",
            "### 2. Dimensões Geométricas Finais (em cm)",
            f"- **Extensão em X:** `{dx:.1f} cm` (`{dx/100.0:.2f} m`)",
            f"- **Extensão em Y:** `{dy:.1f} cm` (`{dy/100.0:.2f} m`)",
            f"- **Bounding Box:** `({self.bounds_finais[0]:.1f}, {self.bounds_finais[1]:.1f})` a `({self.bounds_finais[2]:.1f}, {self.bounds_finais[3]:.1f})`\n",
            "> [!TIP]\n> O arquivo gerado está pronto para ser inserido como desenho de referência externa (`Geo_*.DWG/DXF`) no Modelador Estrutural do TQS sem causar lentidão ou interferência visual."
        ]
        return "\n".join(linhas)


class TQSArchCleaner:
    """
    Higienizador e padronizador de arquivos CAD de arquitetura (DXF/DWG)
    para conversão em bases limpas de referência Geo_*.DWG no TQS V25.
    """

    # Padrões de camadas parasitárias de arquitetura que poluem o modelador
    PADROES_PARASITAS = [
        r"mob[ií]l", r"layout", r"m[oó]ve[ií]s", r"arm[aá]r", r"cama", r"sof[aá]",
        r"veget", r"[aá]rvor", r"paisag", r"plant[ií]o", r"jard[ií]m",
        r"ve[ií]c", r"carro", r"auto", r"moto",
        r"humano", r"pessoa", r"figura",
        r"hach", r"hatch", r"pat", r"s[oó]lido",
        r"cota", r"dim", r"dimens",
        r"acab", r"revest", r"piso.*hach",
        r"esquadr.*text", r"tabela", r"quadro"
    ]

    def __init__(self):
        if ezdxf is None:
            raise ImportError("ezdxf é obrigatório para a manipulação e limpeza de arquivos CAD.")

    def limpar_e_padronizar(
        self,
        caminho_entrada: str,
        caminho_saida: Optional[str] = None,
        fator_escala: str = "auto",
        centralizar_origem: bool = False,
    ) -> LimpezaArquiteturaResultado:
        """
        Executa a limpeza das camadas parasitas, purga de hachuras/cotas e padronização.
        :param caminho_entrada: Arquivo DXF (ou DWG) de arquitetura original.
        :param caminho_saida: Destino do DXF limpo (ex: Geo_PAV.dxf).
        :param fator_escala: 'auto' (detecta metros vs cm), ou valor numérico (ex: 100.0 ou 1.0).
        :param centralizar_origem: Se True, translada o canto inferior esquerdo para (0, 0).
        """
        p_in = Path(caminho_entrada)
        if not p_in.exists():
            raise FileNotFoundError(f"Arquivo de arquitetura não encontrado: {caminho_entrada}")

        # Se caminho_saida não for fornecido, cria Geo_<nome>.dxf na mesma pasta
        if not caminho_saida:
            nome_base = p_in.stem
            if not nome_base.lower().startswith("geo_"):
                nome_base = f"Geo_{nome_base}"
            caminho_saida = str(p_in.parent / f"{nome_base}.dxf")

        doc_origem = ezdxf.readfile(str(p_in))
        msp_origem = doc_origem.modelspace()

        doc_novo = ezdxf.new(doc_origem.dxfversion, setup=True)
        msp_novo = doc_novo.modelspace()

        # Compila regex de camadas parasitas
        regex_parasita = re.compile("|".join(self.PADROES_PARASITAS), re.IGNORECASE)

        # Contadores
        tot_originais = 0
        tot_mantidas = 0
        hachuras_removidas = 0
        cotas_removidas = 0
        parasitas_removidos = 0
        camadas_purgadas: Set[str] = set()
        camadas_preservadas: Set[str] = set()

        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")

        for entity in msp_origem:
            tot_originais += 1
            dxftype = entity.dxftype()
            layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"

            # 1. Filtro por tipo de entidade
            if dxftype in ["HATCH"]:
                hachuras_removidas += 1
                continue
            if dxftype in ["DIMENSION", "LEADER", "MULTILEADER"]:
                cotas_removidas += 1
                continue

            # 2. Filtro por camada parasita
            if regex_parasita.search(layer):
                parasitas_removidos += 1
                camadas_purgadas.add(layer)
                continue

            camadas_preservadas.add(layer)

            # Garante que a camada exista no novo documento
            if layer not in doc_novo.layers:
                doc_novo.layers.add(layer)

            # Adiciona ao novo documento mantendo layer e atributos
            try:
                msp_novo.add_foreign_entity(entity)
                tot_mantidas += 1

                # Calcula bounding box aproximado
                if hasattr(entity, "dxf"):
                    if hasattr(entity.dxf, "start") and hasattr(entity.dxf, "end"):
                        min_x = min(min_x, entity.dxf.start[0], entity.dxf.end[0])
                        max_x = max(max_x, entity.dxf.start[0], entity.dxf.end[0])
                        min_y = min(min_y, entity.dxf.start[1], entity.dxf.end[1])
                        max_y = max(max_y, entity.dxf.start[1], entity.dxf.end[1])
                    elif hasattr(entity.dxf, "insert"):
                        min_x = min(min_x, entity.dxf.insert[0])
                        max_x = max(max_x, entity.dxf.insert[0])
                        min_y = min(min_y, entity.dxf.insert[1])
                        max_y = max(max_y, entity.dxf.insert[1])
            except Exception:
                continue

        if min_x == float("inf"):
            min_x, min_y, max_x, max_y = 0.0, 0.0, 0.0, 0.0

        bounds_orig = (min_x, min_y, max_x, max_y)

        # 3. Determinação e aplicação do fator de escala
        extensao_max = max(max_x - min_x, max_y - min_y)
        fator = 1.0
        if fator_escala == "auto":
            # Se a extensão máxima da planta está entre 3 e 150 unidades, o desenho está em metros!
            # Converte para centímetros (padrão TQS) multiplicando por 100.
            if 3.0 <= extensao_max <= 200.0:
                fator = 100.0
            else:
                fator = 1.0
        else:
            try:
                fator = float(fator_escala)
            except ValueError:
                fator = 1.0

        # Aplica fator de escala e/ou translação
        if fator != 1.0 or centralizar_origem:
            dx_trans = -min_x * fator if centralizar_origem else 0.0
            dy_trans = -min_y * fator if centralizar_origem else 0.0

            mat = Matrix44.scale(fator, fator, 1.0)
            if centralizar_origem:
                mat = mat @ Matrix44.translate(dx_trans, dy_trans, 0.0)

            for ent in msp_novo:
                try:
                    ent.transform(mat)
                except Exception:
                    pass

            bounds_fin = (
                (min_x * fator) + dx_trans,
                (min_y * fator) + dy_trans,
                (max_x * fator) + dx_trans,
                (max_y * fator) + dy_trans,
            )
        else:
            bounds_fin = bounds_orig

        os.makedirs(os.path.dirname(os.path.abspath(caminho_saida)), exist_ok=True)
        doc_novo.saveas(caminho_saida)

        return LimpezaArquiteturaResultado(
            arquivo_origem=str(p_in),
            arquivo_destino=str(Path(caminho_saida).resolve()),
            entidades_originais=tot_originais,
            entidades_mantidas=tot_mantidas,
            hachuras_removidas=hachuras_removidas,
            cotas_removidas=cotas_removidas,
            blocos_parasitas_removidos=parasitas_removidos,
            camadas_purgadas=sorted(list(camadas_purgadas)),
            camadas_preservadas=sorted(list(camadas_preservadas)),
            fator_escala_aplicado=fator,
            bounds_originais=bounds_orig,
            bounds_finais=bounds_fin,
        )
