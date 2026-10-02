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
#    TQSGeo.PY    27-10-2020 Rotinas de geometria analítica
#                 Versão anotada: docstrings Google-style + type hints
#-----------------------------------------------------------------------------
from __future__ import annotations

import math
import tkinter.messagebox
from typing import List, Optional, Tuple

import TQS.TQSUtil

#-----------------------------------------------------------------------------
#   Algumas constantes
#
glb_delprec:   float = 0.001            # precisão para igualar 2 pontos
glb_delang:    float = 0.001            # precisão para igualar ângulos
glb_delgeoint: float = 0.01             # tolerância de arctangente em geoint

#-----------------------------------------------------------------------------
def SetPrecision (delx: float) -> None:
    """Define a precisão usada para considerar dois pontos coincidentes.

    Args:
        delx: Tolerância em unidades de desenho.
    """
    global             glb_delprec
    glb_delprec        = delx

def SetAnglePrecision (delx: float) -> None:
    """Define a precisão usada para considerar dois ângulos iguais.

    Args:
        delx: Tolerância em graus.
    """
    global             glb_delang
    glb_delang         = delx


def Equals (x1: float, y1: float, x2: float, y2: float) -> int:
    """Verifica se dois pontos são iguais dentro da precisão configurada.

    Args:
        x1: X do primeiro ponto.
        y1: Y do primeiro ponto.
        x2: X do segundo ponto.
        y2: Y do segundo ponto.

    Returns:
        ``1`` se os pontos coincidem dentro de :data:`glb_delprec`, senão ``0``.
    """
    global             glb_delprec
    if                 math.fabs (x1 - x2) < glb_delprec and math.fabs (y1 - y2) < glb_delprec:
        return         1
    else:
        return         0

def Distance (x1: float, y1: float, x2: float, y2: float) -> float:
    """Retorna a distância euclidiana entre dois pontos.

    Args:
        x1: X do primeiro ponto.
        y1: Y do primeiro ponto.
        x2: X do segundo ponto.
        y2: Y do segundo ponto.

    Returns:
        Distância em unidades de desenho.
    """
    return             math.sqrt ((x2 - x1)*(x2 - x1) + (y2 - y1)*(y2 - y1))

def LineCoefficients (x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float, float]:
    """Calcula os coeficientes ``(a, b, c)`` da reta na forma ``ax + by + c = 0``.

    Args:
        x1: X do primeiro ponto da reta.
        y1: Y do primeiro ponto da reta.
        x2: X do segundo ponto da reta.
        y2: Y do segundo ponto da reta.

    Returns:
        Tupla ``(a, b, c)`` com os coeficientes da reta.
    """
    a                  = y2 - y1
    b                  = x1 - x2
    c                  = x2*y1 - x1*y2
    return             a, b, c

def DistancePointLine (x1line: float, y1line: float, x2line: float, y2line: float,
                       xpoint: float, ypoint: float) -> float:
    """Retorna a distância de um ponto à reta definida por dois pontos.

    Args:
        x1line: X do primeiro ponto da reta.
        y1line: Y do primeiro ponto da reta.
        x2line: X do segundo ponto da reta.
        y2line: Y do segundo ponto da reta.
        xpoint: X do ponto.
        ypoint: Y do ponto.

    Returns:
        Distância perpendicular do ponto à reta. Retorna ``0`` se a reta
        for degenerada (dois pontos coincidentes).
    """
    a, b, c            = LineCoefficients (x1line, y1line, x2line, y2line)
    div                = math.sqrt (a*a + b*b)
    global             glb_delprec
    if                 math.fabs (div) < glb_delprec:
        return         0.
    dpr                = math.fabs (a*xpoint + b*ypoint + c)/div
    return            dpr


def Angle2p (x1: float, y1: float, x2: float, y2: float) -> float:
    """Calcula o ângulo do vetor ``(x1,y1)→(x2,y2)`` em graus, ``0..360``.

    Args:
        x1: X da origem.
        y1: Y da origem.
        x2: X do destino.
        y2: Y do destino.

    Returns:
        Ângulo em graus no intervalo ``[0, 360]``. Retorna ``0`` para
        vetor nulo.
    """
    global             glb_delprec
    global             glb_delang
    # Vetor nulo: convenção retorna 0
    if                 math.fabs (x2 - x1) + math.fabs (y2 - y1) < glb_delprec:
        return         0.
    # Caso geral: arctan do quociente (-PI/2..PI/2). Eixo Y vertical é tratado à parte
    if                 math.fabs (x2 - x1)  > glb_delprec:
        ang            = math.atan ((y2-y1) / (x2-x1))
    else:
        if              y2 > y1:
            ang        = TQS.TQSUtil.PI / 2.
        else:
            ang        = -TQS.TQSUtil.PI / 2.

    # Resolve ambiguidade de quadrante somando PI quando o vetor cai no 2º/3º quadrante
    if                 ang < -glb_delang:
        if             y2 > y1:
            ang        = ang + TQS.TQSUtil.PI
    elif               ang > glb_delang:
        if             y2 < y1:
            ang        = ang + TQS.TQSUtil.PI
    else:
        if             x2 < x1:
            ang        = ang + TQS.TQSUtil.PI

    # Normaliza para [0, 2*PI)
    if                 ang < 0.:
        ang            = ang + 2.*TQS.TQSUtil.PI
    elif               ang > 2.*TQS.TQSUtil.PI:
        ang            = ang - 2.*TQS.TQSUtil.PI

    return             ang*180./TQS.TQSUtil.PI


def Angle2r (x1: float, y1: float, x2: float, y2: float,
             x3: float, y3: float, x4: float, y4: float) -> float:
    """Calcula o ângulo entre as retas ``1-2`` e ``3-4``, em graus ``0..180``.

    Args:
        x1: X do primeiro ponto da primeira reta.
        y1: Y do primeiro ponto da primeira reta.
        x2: X do segundo ponto da primeira reta.
        y2: Y do segundo ponto da primeira reta.
        x3: X do primeiro ponto da segunda reta.
        y3: Y do primeiro ponto da segunda reta.
        x4: X do segundo ponto da segunda reta.
        y4: Y do segundo ponto da segunda reta.

    Returns:
        Ângulo em graus no intervalo ``[0, 180]``.
    """
    global             glb_delprec
    # Default 180° para casos degenerados (retas coincidentes ou nulas)
    ang                = TQS.TQSUtil.PI
    # Vetor da reta 1 e seu módulo
    ux                 = x2 - x1
    uy                 = y2 - y1
    umod               = Distance (x1, y1, x2, y2)
    if                 math.fabs (umod) < glb_delprec:
        return         ang*180./TQS.TQSUtil.PI

    # Vetor da reta 2 e seu módulo
    vx                 = x4 - x3
    vy                 = y4 - y3
    vmod               = Distance (x3, y3, x4, y4)
    if                 math.fabs (vmod) < glb_delprec:
        return         ang*180./TQS.TQSUtil.PI

    # cos(theta) = (u . v) / (|u| |v|), saturado em [-1, 1] por segurança numérica
    arco               = (ux*vx + uy*vy) / (umod*vmod)
    if                 arco >  1.:
        arco           = 1.
    if                 arco < -1.:
        arco           = -1.
    ang                = math.acos (arco)

    return             ang*180./TQS.TQSUtil.PI

def NormalizeAngle (angle: float) -> float:
    """Normaliza um ângulo para o intervalo ``[0, 360)`` graus.

    Args:
        angle: Ângulo em graus, possivelmente fora do intervalo.

    Returns:
        Ângulo normalizado em graus.
    """
    global             glb_delang
    while              angle < 0.:
        angle          += 360.
    while              angle > 360.:
        angle          -= 360.
    if                 math.fabs (angle - 360.) < glb_delang:
        angle          = 0.
    return             angle

def _VerificarVetoresIguais (vecx: List[float], vecy: List[float]) -> int:
    """Valida que os vetores X e Y têm o mesmo tamanho não-nulo.

    Args:
        vecx: Vetor de coordenadas X.
        vecy: Vetor de coordenadas Y.

    Returns:
        ``0`` se os vetores são consistentes, ``1`` em caso de erro
        (também exibe um messagebox).
    """
    if                 len (vecx) != len (vecy) or len (vecx) == 0:
        tkinter.messagebox.showerror(title="Vetores vecx e vecy de dimensões diferentes",
                                         message="TQSGeo")
        return         1
    else:
        return         0

def Area (vecx: List[float], vecy: List[float]) -> Optional[float]:
    """Calcula a área (com sinal) da poligonal definida por ``vecx``/``vecy``.

    O sinal indica a orientação: positivo para sentido anti-horário,
    negativo para horário (no sistema de coordenadas TQS).

    Args:
        vecx: Vetor de coordenadas X dos vértices.
        vecy: Vetor de coordenadas Y dos vértices.

    Returns:
        Área com sinal, ``0.0`` se não houver pontos, ``None`` em caso
        de inconsistência entre os vetores.
    """

    if                 _VerificarVetoresIguais (vecx, vecy):
        return

    # Fórmula do "shoelace" / Gauss: soma sinalizada de trapézios
    # Para cada segmento i→j fecha um trapézio sob o eixo X
    area               = 0.
    npt                = len (vecx)
    if                npt == 0:
        return         0.
    x1                = vecx [0]
    y1                = vecy [0]
    npt               = len (vecx)
    for               i in range (0, npt):
        # Próximo vértice; volta ao 0 para fechar a poligonal
        j             = i + 1
        if            j >= npt:
            j         = 0
        x2            = vecx [j]
        y2            = vecy [j]
        deltax        = x2 - x1
        # Área do trapézio = (y_med * deltax) com y_med = (y1+y2)/2 (a divisão por 2 é feita ao final)
        area          = area + (y2 + y1)*deltax
        x1            = x2
        y1            = y2

    area              = area / 2.
    return            area

def Perimeter (vecx: List[float], vecy: List[float]) -> Optional[float]:
    """Calcula o perímetro da poligonal aberta definida por ``vecx``/``vecy``.

    Args:
        vecx: Vetor de coordenadas X dos vértices.
        vecy: Vetor de coordenadas Y dos vértices.

    Returns:
        Perímetro acumulado dos segmentos, ``0.0`` se não houver pontos,
        ``None`` em caso de inconsistência entre os vetores.
    """
    if                 _VerificarVetoresIguais (vecx, vecy):
        return
    perim              = 0.
    npt                = len (vecx)
    if                 npt == 0:
        return         0.
    npt                = len (vecx)
    x1                 = vecx [0]
    y1                 = vecy [0]
    for                i in range (0, npt-1):
        j              = i + 1
        x2             = vecx [j]
        y2             = vecy [j]
        perim          += Distance (x1, y1, x2, y2)
        x1             = x2
        y1             = y2

    return             perim

def GravityCenter (vecx: List[float], vecy: List[float]) -> Optional[Tuple[float, float, float]]:
    """Retorna o centro de gravidade e a área (com sinal) de uma poligonal.

    Args:
        vecx: Vetor de coordenadas X dos vértices.
        vecy: Vetor de coordenadas Y dos vértices.

    Returns:
        Tupla ``(xg, yg, area)`` ou ``None`` se a poligonal for degenerada
        ou os vetores forem inconsistentes.
    """
    if                 _VerificarVetoresIguais (vecx, vecy):
        return
    xgg                = 0.
    ygg                = 0.
    areac              = 0.
    xg                 = 0.
    yg                 = 0.
    area               = 0.
    npt                = len (vecx)
    if                 npt == 0:
        return         0., 0., 0.

    global             glb_delprec
    # Detecção de poligonal degenerada: variação total nula em X ou Y
    difx               = 0.
    dify               = 0.
    for                i in range (0, npt-1):
        difx           += math.fabs (vecx [i] - vecx [i+1])
        dify           += math.fabs (vecy [i] - vecy [i+1])

    if                 difx < glb_delprec or dify < glb_delprec:
        return         0., 0., 0.

    # Centróide ponderado pela área. Cada segmento gera um trapézio decomposto em
    # um retângulo (arear) e um triângulo (areat) com seus respectivos centros de gravidade.
    # A soma dá os momentos estáticos; a divisão final pela área total dá xg, yg.
    x1                 = vecx [0]
    y1                 = vecy [0]
    for                i in range (0, npt):
        j              = i + 1
        if             j >= npt:
            j          = 0
        x2             = vecx [j]
        y2             = vecy [j]
        deltax         = x2 - x1
        deltay         = y2 - y1
        arear          = y1    *deltax*0.5
        areat          = deltay*deltax*0.5
        area           = area   + (y2 + y1)*deltax
        xg             = xg     + (x1 + x2)*arear +  (x1 + 2./3.*deltax)*areat
        yg             = yg     +  y1      *arear +  (y1 + 1./3.*deltay)*areat
        x1             = x2
        y1             = y2

    # Fecha a fórmula de Gauss para a área (divisão por 2)
    area               = area / 2.
    if                 math.fabs (area) < glb_delprec:
        return
    # Normaliza os momentos pela área total
    xg                 = xg / area
    yg                 = yg / area
    areac              = area
    xgg                = xg
    ygg                = yg
    return             xgg, ygg, areac


def PointInSegment (x: float, y: float, x1: float, y1: float,
                    x2: float, y2: float) -> int:
    """Verifica se o ponto ``(x, y)`` cai dentro do segmento ``1-2``.

    O ponto é projetado sobre a reta ``1-2`` antes do teste.

    Args:
        x: X do ponto.
        y: Y do ponto.
        x1: X do início do segmento.
        y1: Y do início do segmento.
        x2: X do fim do segmento.
        y2: Y do fim do segmento.

    Returns:
        ``1`` se está no segmento, ``0`` caso contrário.
    """
    global             glb_delprec
    # Projeta o ponto na reta — a partir daqui o teste é unidimensional
    x, y               = Projection (x1, y1, x2, y2, x, y)
    insegment          = 1
    # Coincidência com um dos extremos é considerada dentro do segmento
    if                 math.fabs (x-x1) < glb_delprec and math.fabs (y-y1) < glb_delprec:
        return         insegment

    if                 math.fabs (x-x2) < glb_delprec and math.fabs (y-y2) < glb_delprec:
        return         insegment

    # Escolhe o eixo dominante para o teste de "entre extremos".
    # O sinal do produto (extr-pt)*(pt-orig) é positivo quando o ponto está entre os dois extremos.
    dis1               = math.fabs (x2 - x1)
    dis2               = math.fabs (y2 - y1)
    if                 dis1 > dis2:
        if             dis1 < glb_delprec:
            insegment  = 0
        if            (x2 - x)*(x - x1) < 0:
            insegment  = 0
    else:
        if             dis2  < glb_delprec:
            insegment  = 0
        if             (y2-y) * (y-y1) < 0:
            insegment  = 0

    return             insegment


def IntersectionByCoefs (a: float, b: float, c: float,
                         d: float, e: float, f: float) -> Tuple[float, float, int]:
    """Intersecção de duas retas dadas por coeficientes.

    Reta 1: ``a·x + b·y + c = 0``. Reta 2: ``d·x + e·y + f = 0``.

    Args:
        a: Coeficiente ``a`` da primeira reta.
        b: Coeficiente ``b`` da primeira reta.
        c: Coeficiente ``c`` da primeira reta.
        d: Coeficiente ``a`` da segunda reta.
        e: Coeficiente ``b`` da segunda reta.
        f: Coeficiente ``c`` da segunda reta.

    Returns:
        Tupla ``(x, y, istat)`` com o ponto de intersecção. ``istat != 0``
        quando as retas são paralelas, anti-paralelas ou degeneradas.
    """
    global             glb_delgeoint
    x                  = 0.
    y                  = 0.
    istat              = 1
    # Normas dos vetores normais às retas; usadas para detectar paralelismo
    d1                 = math.sqrt (a*a + b*b)
    d2                 = math.sqrt (d*d + e*e)
    if                 d1 == 0. or d2 == 0.:
        return         x, y, istat
    # Versores normais (a, b)/|n| de cada reta
    vx1                = b / d1
    vy1                = a / d1
    vx2                = e / d2
    vy2                = d / d2
    # Retas paralelas (versores iguais) ou anti-paralelas (versores opostos) → sem intersecção
    if                 math.fabs (vx1-vx2) < glb_delgeoint and math.fabs (vy1-vy2) < glb_delgeoint:
        return         x, y, istat
    if                 math.fabs (vx1+vx2) < glb_delgeoint and math.fabs (vy1+vy2) < glb_delgeoint:
        return         x, y, istat
    # Resolve sistema 2x2 pela regra de Cramer
    div                = e*a - d*b
    if                 div == 0.:
        return         x, y, istat
    x                  = (f*b -  c*e) / div
    y                  = (d*c  - f*a) / div
    istat              = 0
    return             x, y, istat

def Intersection2r (x1: float, y1: float, x2: float, y2: float,
                    x3: float, y3: float, x4: float, y4: float) -> Tuple[float, float, int]:
    """Calcula a intersecção das retas ``1-2`` e ``3-4`` (retas infinitas).

    Args:
        x1: X do primeiro ponto da reta 1.
        y1: Y do primeiro ponto da reta 1.
        x2: X do segundo ponto da reta 1.
        y2: Y do segundo ponto da reta 1.
        x3: X do primeiro ponto da reta 2.
        y3: Y do primeiro ponto da reta 2.
        x4: X do segundo ponto da reta 2.
        y4: Y do segundo ponto da reta 2.

    Returns:
        Tupla ``(x, y, istat)`` com o ponto de intersecção.
        ``istat != 0`` se não há intersecção.
    """
    a, b, c            = LineCoefficients (x1, y1, x2, y2)
    d, e, f            = LineCoefficients (x3, y3, x4, y4)
    x, y, istat        = IntersectionByCoefs (a, b, c, d, e, f)
    return             x, y, istat


def IntersectionSegment (x1: float, y1: float, x2: float, y2: float,
                         x3: float, y3: float, x4: float, y4: float) -> Tuple[float, float, int]:
    """Intersecção de dois segmentos (não retas infinitas).

    A intersecção precisa cair dentro de ambos os segmentos ``1-2`` e ``3-4``.

    Args:
        x1: X do início do segmento 1.
        y1: Y do início do segmento 1.
        x2: X do fim do segmento 1.
        y2: Y do fim do segmento 1.
        x3: X do início do segmento 2.
        y3: Y do início do segmento 2.
        x4: X do fim do segmento 2.
        y4: Y do fim do segmento 2.

    Returns:
        Tupla ``(x, y, istat)`` com o ponto de intersecção.
        ``istat != 0`` se as retas não se cruzam ou se a intersecção
        cai fora de algum dos segmentos.
    """
    x, y, istat        = Intersection2r (x1, y1, x2, y2, x3, y3, x4, y4)
    if                 istat != 0:
        return         x, y, istat
    if                 not PointInSegment (x, y, x1, y1, x2, y2):
        return         x, y, 1
    if                 not PointInSegment (x, y, x3, y3, x4, y4):
        return         x, y, 1
    istat              = 0
    return             x, y, istat


def Projection (x1: float, y1: float, x2: float, y2: float,
                xp: float, yp: float) -> Tuple[float, float]:
    """Projeta um ponto sobre uma reta.

    Args:
        x1: X do primeiro ponto da reta.
        y1: Y do primeiro ponto da reta.
        x2: X do segundo ponto da reta.
        y2: Y do segundo ponto da reta.
        xp: X do ponto a projetar.
        yp: Y do ponto a projetar.

    Returns:
        Tupla ``(x, y)`` com o ponto projetado. Em caso de reta degenerada
        retorna ``(xp, yp)``.
    """
    # Constrói uma reta perpendicular à 1-2 passando por (xp, yp).
    # Coeficientes da reta original: a*x + b*y + c = 0  (vetor normal (a, b))
    # A perpendicular tem normal rotacionada 90°: (d, e) = (-b, a)
    a, b, c            = LineCoefficients (x1, y1, x2, y2)
    d                  = -b
    e                  = a
    f                  = -d*xp -e*yp
    # A intersecção das duas retas é a projeção
    x, y, istat        = IntersectionByCoefs (a, b, c, d, e, f)
    # Reta degenerada: devolve o próprio ponto
    if                 istat != 0:
        x              = xp
        y              = yp

    return             x, y

def ParallelPoint (x1: float, y1: float, x2: float, y2: float,
                   dist: float) -> Tuple[float, float]:
    """Calcula um ponto sobre a normal a ``1-2`` passando por ``2``.

    A distância é positiva à direita do vetor ``1→2``.

    Args:
        x1: X do primeiro ponto.
        y1: Y do primeiro ponto.
        x2: X do segundo ponto.
        y2: Y do segundo ponto.
        dist: Distância (positiva à direita, negativa à esquerda).

    Returns:
        Tupla ``(px, py)`` do ponto resultante.
    """
    vetmod             = Distance (x1, y1, x2, y2)
    global             glb_delprec
    # Vetor degenerado: devolve o próprio ponto 1
    if                 vetmod < glb_delprec:
        px             = x1
        py             = y1
    else:
        # Versor ortogonal a 1-2 rotacionado 90° à direita: (dy, -dx)/|v|
        # Aplicado a partir do ponto 2 com magnitude `dist`.
        vx             = (y2 - y1)/vetmod
        vy             = (x1 - x2)/vetmod
        px             =  x2 + vx*dist
        py             =  y2 + vy*dist

    return             px, py

def ParallelLine (x1: float, y1: float, x2: float, y2: float,
                  dist: float) -> Tuple[float, float, float, float]:
    """Calcula a reta paralela a ``1-2`` a uma dada distância.

    A distância é positiva à direita do vetor ``1→2``.

    Args:
        x1: X do primeiro ponto.
        y1: Y do primeiro ponto.
        x2: X do segundo ponto.
        y2: Y do segundo ponto.
        dist: Distância (positiva à direita, negativa à esquerda).

    Returns:
        Tupla ``(xp1, yp1, xp2, yp2)`` da reta paralela.
    """
    xp2, yp2           = ParallelPoint (x1, y1, x2, y2, dist)
    xp1, yp1           = ParallelPoint (x2, y2, x1, y1, -dist)
    return             xp1, yp1, xp2, yp2


def ParallelPolyline (vecx: List[float], vecy: List[float], dist: float) -> Optional[int]:
    """Calcula a paralela à poligonal ``vecx``/``vecy`` à direita.

    Modifica os vetores ``vecx`` e ``vecy`` **in-place** com os pontos
    da poligonal paralela. Trata poligonais abertas e fechadas.

    Args:
        vecx: Vetor de coordenadas X (modificado in-place).
        vecy: Vetor de coordenadas Y (modificado in-place).
        dist: Distância de offset (positiva à direita, negativa à esquerda).

    Returns:
        ``None`` no fluxo normal; valor truthy se os vetores forem
        inconsistentes (encerra a função antecipadamente).
    """
    if                 _VerificarVetoresIguais (vecx, vecy):
        return

    global             glb_delprec
    # Detecta se a poligonal é fechada (último ponto coincide com o primeiro)
    ifecha             = 0
    npt                = len (vecx)
    if                 math.fabs (vecx[0] - vecx[npt-1]) < glb_delprec and math.fabs (vecy[0] - vecy[npt-1]) < glb_delprec:
        ifecha         = 1
    # Vetores de trabalho: o trecho i é representado pelos seus pontos inicial (1) e final (2)
    xtrab1             = []    # matriz de trabalho p/paralelas
    ytrab1             = []    # o trecho i e formado pelos pontos
    xtrab2             = []    # 1 inicial e 2 final
    ytrab2             = []
    for                i in range (0, npt-1):
        xtrab1.append  (vecx [i  ])
        ytrab1.append  (vecy [i  ])
        xtrab2.append  (vecx [i+1])
        ytrab2.append  (vecy [i+1])

    # Etapa 1: deslocamento individual de cada segmento — gera retas paralelas isoladas
    for                i in range (0, npt-1):
        x1, y1, x2, y2 = ParallelLine (xtrab1 [i], ytrab1 [i], xtrab2 [i], ytrab2 [i], dist)
        xtrab1 [i]     = x1
        ytrab1 [i]     = y1
        xtrab2 [i]     = x2
        ytrab2 [i]     = y2

    # Etapa 2: re-conexão dos segmentos paralelos. Em cada vértice interno (e em todos os
    # vértices se a poligonal for fechada) substitui as extremidades pelo ponto de
    # intersecção com o segmento vizinho — assim os "cantos" voltam a fechar.
    for                i in range (0, npt-1):
        j              = i - 1
        if             j < 0:
            j          = npt-2
        k              = i + 1
        if             k >= npt-1:
            k          = 0
        istat1         = 1
        istat2         = 1
        # Intersecta com o segmento anterior (à esquerda) — pula apenas no primeiro vértice de poligonal aberta
        if             ifecha != 0 or i > 0:
            x1, y1, istat1 = Intersection2r (xtrab1 [j], ytrab1 [j], xtrab2 [j], ytrab2 [j],
                                             xtrab1 [i], ytrab1 [i], xtrab2 [i], ytrab2 [i])
        # Intersecta com o segmento seguinte (à direita) — pula apenas no último vértice de poligonal aberta
        if             ifecha != 0 or  i < npt-2:
            x2, y2, istat2 =  Intersection2r (xtrab1 [i], ytrab1 [i], xtrab2 [i], ytrab2 [i],
                                              xtrab1 [k], ytrab1 [k], xtrab2 [k], ytrab2 [k])
        if             istat1 == 0:
            xtrab1 [i] = x1
            ytrab1 [i] = y1
        if             istat2 == 0:
            xtrab2 [i] = x2
            ytrab2 [i] = y2

    # Copia o resultado de volta para vecx/vecy (modificação in-place).
    # O último ponto vem do extremo final do último segmento.
    for                i in range (0, npt-1):
        vecx [i]       = xtrab1 [i]
        vecy [i]       = ytrab1 [i]

    vecx [npt-1]       = xtrab2 [npt-2]
    vecy [npt-1]       = ytrab2 [npt-2]


def Limits (vecx: List[float], vecy: List[float]) -> Optional[Tuple[float, float, float, float]]:
    """Retorna o retângulo envolvente dos vetores ``vecx``/``vecy``.

    Args:
        vecx: Vetor de coordenadas X.
        vecy: Vetor de coordenadas Y.

    Returns:
        Tupla ``(xmin, ymin, xmax, ymax)``, ou ``None`` se os vetores
        forem inconsistentes.
    """
    if                 _VerificarVetoresIguais (vecx, vecy):
        return
    ambda             = 1.e32
    xmax               = -ambda
    ymax               = -ambda
    xmin               =  ambda
    ymin               =  ambda
    np                 = len (vecx)
    for                i in range (0, np):
        if            vecx [i] < xmin:
            xmin       = vecx [i]
        if            vecy [i] < ymin:
            ymin       = vecy [i]
        if            vecx [i] > xmax:
            xmax       = vecx [i]
        if            vecy [i] > ymax:
            ymax       = vecy [i]
    return             xmin, ymin, xmax, ymax


def VectorProduct (x1: float, y1: float, x2: float, y2: float,
                   x3: float, y3: float, x4: float, y4: float) -> float:
    """Produto vetorial 2D dos vetores ``(1→2)`` e ``(3→4)``.

    Args:
        x1: X da origem do primeiro vetor.
        y1: Y da origem do primeiro vetor.
        x2: X da extremidade do primeiro vetor.
        y2: Y da extremidade do primeiro vetor.
        x3: X da origem do segundo vetor.
        y3: Y da origem do segundo vetor.
        x4: X da extremidade do segundo vetor.
        y4: Y da extremidade do segundo vetor.

    Returns:
        Componente Z do produto vetorial (escalar).
    """
    ux                 = x2 - x1
    uy                 = y2 - y1
    vx                 = x4 - x3
    vy                 = y4 - y3
    return             ux*vy - uy*vx

def PointProduct (x1: float, y1: float, x2: float, y2: float,
                  x3: float, y3: float, x4: float, y4: float) -> float:
    """Produto escalar dos vetores ``(1→2)`` e ``(3→4)``.

    Args:
        x1: X da origem do primeiro vetor.
        y1: Y da origem do primeiro vetor.
        x2: X da extremidade do primeiro vetor.
        y2: Y da extremidade do primeiro vetor.
        x3: X da origem do segundo vetor.
        y3: Y da origem do segundo vetor.
        x4: X da extremidade do segundo vetor.
        y4: Y da extremidade do segundo vetor.

    Returns:
        Produto escalar.
    """
    ux                 = x2 - x1
    uy                 = y2 - y1
    vx                 = x4 - x3
    vy                 = y4 - y3
    return             ux*vx + uy*vy

def Versor (x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    """Calcula o versor (vetor unitário) do vetor ``(1→2)``.

    Args:
        x1: X da origem.
        y1: Y da origem.
        x2: X da extremidade.
        y2: Y da extremidade.

    Returns:
        Tupla ``(vx, vy)`` do versor, ou ``(0, 0)`` para vetor nulo.
    """
    dis                = Distance (x1, y1, x2, y2)
    global             glb_delprec
    if                 dis < glb_delprec:
        return         0., 0.
    vx                = (x2 - x1)/dis
    vy                = (y2 - y1)/dis
    return            vx, vy

def PointInArea (x: float, y: float, vecx: List[float], vecy: List[float]) -> int:
    """Verifica se o ponto ``(x, y)`` está dentro de uma poligonal.

    Usa o método da soma de ângulos. Pontos sobre o contorno são
    considerados internos.

    Args:
        x: X do ponto.
        y: Y do ponto.
        vecx: Vetor de coordenadas X dos vértices da poligonal.
        vecy: Vetor de coordenadas Y dos vértices da poligonal.

    Returns:
        ``1`` se o ponto está dentro (ou no contorno), ``0`` caso contrário.
    """
    inarea             = 0
    if                 _VerificarVetoresIguais (vecx, vecy):
        return         inarea

    # Rejeição barata por bounding box antes do teste angular caro
    xmin, ymin, xmax, ymax = Limits (vecx, vecy)
    global             glb_delprec
    delx                = glb_delprec
    inarea             = 0
    if                 x < xmin - delx or x > xmax + delx or y < ymin - delx or y > ymax + delx:
        return         inarea
    # Fecha a poligonal automaticamente se ainda não estiver fechada
    npc                = len (vecx)
    numtre             = npc-1
    if                 math.fabs (vecx [0] - vecx [numtre]) > delx or math.fabs (vecy [0] - vecy [numtre]) > delx:
        numtre         += 1
    # Algoritmo da soma de ângulos: se o ponto é interno, a soma dos ângulos sob os
    # quais cada aresta é vista é ±360°; se externo, é 0°.
    angtot             = 0.
    for                i in range (0, numtre):
        x1             = vecx [i]
        y1             = vecy [i]
        if             i < npc-1:
            x2         = vecx [i+1]
            y2         = vecy [i+1]
        else:
            x2         = vecx [0]
            y2         = vecy [0]
        # Coincidência com vértice → considera dentro
        if             math.fabs(x-x1) < delx and math.fabs(y-y1) < delx:
            inarea     = 1
            return

        # Coincidência com ponto sobre uma aresta → considera dentro
        xp, yp         = Projection (x1, y1, x2, y2, x, y)
        if             Distance (x, y, xp, yp) < delx:
            if         PointInSegment (xp, yp, x1, y1, x2, y2):
                inarea = 1
                return inarea
        # Ângulo "complementar" sob o qual a aresta é vista, com sinal definido pelo produto vetorial
        ang            = 180. - Angle2r (x1, y1, x, y, x, y, x2, y2)
        if             VectorProduct (x1, y1, x, y, x, y, x2, y2) > 0.:
            ang        = -ang
        angtot         = angtot + ang

    # Soma ≈ ±360° → ponto interno; soma ≈ 0° → externo.
    if                 math.fabs (math.fabs (angtot) - 360.) < delx:
        inarea         = 1
    else:
        inarea         = 0

    return             inarea


glb_a: float = 0.        # Usados no espelhamento
glb_b: float = 0.        # Usados no espelhamento
glb_c: float = 0.        # Usados no espelhamento
glb_d: float = 0.        # Usados no espelhamento
glb_e: float = 0.        # Usados no espelhamento

def MirrorInit (x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    """Inicializa o espelhamento configurando a linha ``1-2`` como eixo.

    Esta função deve ser chamada antes de :func:`Mirror`. Os coeficientes
    da reta ficam armazenados em variáveis globais do módulo.

    Args:
        x1: X do primeiro ponto da reta de espelhamento.
        y1: Y do primeiro ponto da reta de espelhamento.
        x2: X do segundo ponto da reta de espelhamento.
        y2: Y do segundo ponto da reta de espelhamento.

    Returns:
        Tupla ``(angOriginal, angEspelhado)`` em graus — o ângulo da reta
        original e o ângulo após o espelhamento.
    """
    global             glb_a, glb_b, glb_c, glb_d, glb_e
    # Armazena coeficientes da reta de espelhamento (a, b, c) e da perpendicular (d, e)
    # nas globais do módulo. Mirror() re-utiliza esses valores em cada chamada.
    glb_a, glb_b, glb_c = LineCoefficients (x1, y1, x2, y2)
    glb_d              = -glb_b
    glb_e              = glb_a
    # Calcula o ângulo da reta original e o ângulo após o espelhamento.
    # Espelhamento dobra o ângulo de incidência, daí o termo 2*angog.
    angog              = Angle2p (x1, y1, x2, y2)
    angg               = 180. + 2.*angog
    angg               = NormalizeAngle (angg)
    return             angog, angg

def Mirror (xe: float, ye: float) -> Tuple[float, float]:
    """Espelha um ponto pela reta definida em :func:`MirrorInit`.

    Args:
        xe: X do ponto a espelhar.
        ye: Y do ponto a espelhar.

    Returns:
        Tupla ``(xe, ye)`` com o ponto espelhado, ou ``(0, 0)`` em caso
        de erro de intersecção.
    """
    global             glb_a, glb_b, glb_c, glb_d, glb_e
    x3                 = xe
    y3                 = ye;
    # Reta perpendicular (d, e, f) à reta de espelhamento, passando pelo ponto.
    f		       = -glb_d*x3 -glb_e*y3
    # O pé da perpendicular é a projeção do ponto na reta espelhante
    x, y, istat        = IntersectionByCoefs (glb_a, glb_b, glb_c, glb_d, glb_e, f)
    if                 istat != 0:
        return         0., 0.
    # Espelha refletindo o ponto através do pé da perpendicular: P' = P + 2*(F - P)
    xe                 = x3 + 2.*(x - x3)
    ye                 = y3 + 2.*(y - y3)
    return             xe, ye

def Rotate (x: float, y: float, ang: float, orgx: float, orgy: float) -> Tuple[float, float]:
    """Roda um ponto em torno de uma origem.

    Args:
        x: X do ponto a rodar.
        y: Y do ponto a rodar.
        ang: Ângulo em graus (positivo no sentido anti-horário).
        orgx: X da origem da rotação.
        orgy: Y da origem da rotação.

    Returns:
        Tupla ``(x, y)`` com o ponto rotacionado.
    """
    angr               = ang * TQS.TQSUtil.PI/180.
    # Translada para a origem da rotação, aplica matriz de rotação 2D, translada de volta:
    #   [x']   [cos -sin] [x]
    #   [y'] = [sin  cos] [y]
    xx                 = x - orgx
    yy                 = y - orgy
    cosang             = math.cos (angr)
    sinang             = math.sin (angr)
    x                  = orgx + xx*cosang - yy*sinang
    y                  = orgy + xx*sinang + yy*cosang
    return             x, y
