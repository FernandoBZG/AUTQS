from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any


class TipoSecao(Enum):
    RETANGULAR = "RETANGULAR"
    POLIGONAL = "POLIGONAL"
    CIRCULAR = "CIRCULAR"
    SECAO_L = "SECAO_L"
    SECAO_T = "SECAO_T"

@dataclass
class Baricentro:
    """Coordenadas globais (X, Y) do Centro de Gravidade (Baricentro) da seção."""
    x: float
    y: float

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

@dataclass
class GeometriaPilar:
    """Geometria da seção transversal do pilar na base."""
    tipo: TipoSecao
    b: float                             # Largura da seção (cm)
    h: float                             # Altura da seção (cm)
    angulo_rotacao_graus: float          # Rotação da seção em graus
    ponto_fixo_coord: Tuple[float, float]# Coordenada global (X, Y) do Ponto Fixo de inserção
    ponto_fixo_indice: int = 1           # Vértice de inserção (1=inf-esq, 3=sup-dir, 5=centro, etc.)
    espessura_alma: Optional[float] = None
    espessura_mesa: Optional[float] = None
    vertices_poligono: Optional[List[Tuple[float, float]]] = None

@dataclass
class EsforcosFundacao:
    """Esforços característicos e de cálculo atuantes na cota de fundação."""
    nk_max: float        # Esforço axial característico máximo de compressão (tf)
    nk_min: Optional[float] = None  # Fz mínimo real (caso FZ MIN do PORLID); None se o TQS não o forneceu (tf)
    mxk: float = 0.0     # Momento fletor característico em torno do eixo X (tf.m)
    myk: float = 0.0     # Momento fletor característico em torno do eixo Y (tf.m)
    mz: float = 0.0      # Momento fletor / torçor característico em torno do eixo Z (tf.m)
    hx: float = 0.0      # Força horizontal em X (tf)
    hy: float = 0.0      # Força horizontal em Y (tf)
    caso_critico: str = "Envoltória ELU"

@dataclass
class PilarFundacao:
    """Entidade de pilar com nascimento em nível de fundação."""
    nome: str                            # Ex: P1, P2
    pavimento_origem: str                # Pavimento onde o pilar nasce
    geometria: GeometriaPilar
    baricentro: Optional[Baricentro] = None
    esforcos: Optional[EsforcosFundacao] = None

@dataclass
class PavimentoModel:
    """Representação de um pavimento do edifício."""
    indice: int
    nome: str
    classe: int                          # ICLFUN=1, ICLTER=3, etc.
    cota_nivel: float                    # Cota do piso (m)
    pe_direito: float                    # Altura livre / pé direito (m)
    caminho_formas: str = ""
    pilares: List[PilarFundacao] = field(default_factory=list)

@dataclass
class EdificioModel:
    """Representação unificada de um projeto de edifício TQS."""
    nome: str
    caminho: str
    norma: str = "NBR 6118:2014"
    pavimentos: List[PavimentoModel] = field(default_factory=list)

@dataclass
class PlantaDeCargasModel:
    """Modelo consolidado para a emissão da Planta de Cargas (Case 1)."""
    edificio_nome: str
    caminho_edificio: str
    pavimento_fundacao: str
    pilares: List[PilarFundacao] = field(default_factory=list)
    escala_locacao: int = 50             # 1:50
    notas_projeto: List[str] = field(default_factory=list)
    dados_porlid: Optional[Dict[str, Any]] = None

