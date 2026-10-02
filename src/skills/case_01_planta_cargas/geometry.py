import math
from typing import Tuple, List, Optional
from src.core.models import GeometriaPilar, Baricentro, TipoSecao

try:
    from TQS import TQSGeo
    TQS_GEO_DISPONIVEL = True
except ImportError:
    TQS_GEO_DISPONIVEL = False

def calcular_offset_ponto_fixo_retangulo(
    b: float, h: float, indice_pf: int
) -> Tuple[float, float]:
    """
    Calcula o deslocamento do Baricentro (CG) em relação ao Ponto Fixo (PF)
    no sistema de coordenadas local do pilar (antes da rotação).
    
    Convenção padrão de pontos fixos TQS (1 a 9):
    7  8  9   (Superior)
    4  5  6   (Médio)
    1  2  3   (Inferior)
    """
    mapa_offsets = {
        1: (b / 2.0, h / 2.0),     # Canto inferior esquerdo
        2: (0.0, h / 2.0),         # Face inferior meio
        3: (-b / 2.0, h / 2.0),    # Canto inferior direito
        4: (b / 2.0, 0.0),         # Face esquerda meio
        5: (0.0, 0.0),             # Centro de gravidade
        6: (-b / 2.0, 0.0),        # Face direita meio
        7: (b / 2.0, -h / 2.0),    # Canto superior esquerdo
        8: (0.0, -h / 2.0),        # Face superior meio
        9: (-b / 2.0, -h / 2.0),   # Canto superior direito
    }
    return mapa_offsets.get(indice_pf, (b / 2.0, h / 2.0))

def calcular_baricentro_poligono(vertices: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calcula o baricentro (Cx, Cy) de um polígono qualquer fechado
    utilizando a fórmula do Baricentro / Shoelace.
    """
    n = len(vertices)
    if n < 3:
        raise ValueError("Um polígono precisa de pelo menos 3 vértices.")

    area = 0.0
    cx = 0.0
    cy = 0.0

    for i in range(n):
        x0, y0 = vertices[i]
        x1, y1 = vertices[(i + 1) % n]
        cross = (x0 * y1 - x1 * y0)
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    area = area * 0.5
    if abs(area) < 1e-9:
        # Polígono degenerado; retorna média simples dos vértices
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    fator = 1.0 / (6.0 * area)
    return (cx * fator, cy * fator)

def calcular_baricentro_pilar(geom: GeometriaPilar) -> Baricentro:
    """
    Calcula as coordenadas globais absolutas (X_cg, Y_cg) do Baricentro de um pilar.
    Leva em conta:
    - Dimensões da seção transversal (b x h)
    - Posição do Ponto Fixo de inserção
    - Ângulo de rotação da seção (em graus)
    """
    x_pf, y_pf = geom.ponto_fixo_coord
    theta_rad = math.radians(geom.angulo_rotacao_graus)

    if geom.tipo == TipoSecao.RETANGULAR:
        dx_loc, dy_loc = calcular_offset_ponto_fixo_retangulo(
            geom.b, geom.h, geom.ponto_fixo_indice
        )
    elif geom.tipo == TipoSecao.CIRCULAR:
        dx_loc, dy_loc = (0.0, 0.0)
    elif geom.tipo == TipoSecao.POLIGONAL and geom.vertices_poligono:
        # Se temos os vértices do polígono no sistema local
        cx_pol, cy_pol = calcular_baricentro_poligono(geom.vertices_poligono)
        dx_loc, dy_loc = cx_pol, cy_pol
    else:
        # Padrão retangular
        dx_loc, dy_loc = calcular_offset_ponto_fixo_retangulo(
            geom.b, geom.h, geom.ponto_fixo_indice
        )

    # Rotação bidimensional no plano global
    dx_glob = dx_loc * math.cos(theta_rad) - dy_loc * math.sin(theta_rad)
    dy_glob = dx_loc * math.sin(theta_rad) + dy_loc * math.cos(theta_rad)

    x_cg = round(x_pf + dx_glob, 4)
    y_cg = round(y_pf + dy_glob, 4)

    return Baricentro(x=x_cg, y=y_cg)
