"""
Moldura (formato de folha), margens, área do selo e marcas de dobra das pranchas geradas
pelo AUTQS. Antes este código estava copiado no tqs_dwg_builder (planta de cargas) e no
alvenaria_dwg_builder (1ª fiada), e as cópias já tinham divergido.

As diferenças que ainda existem entre as duas pranchas viraram parâmetros, para que o
desenho de cada uma continue exatamente igual ao de antes:
- folga de respiro: 4,0 cm (planta de cargas) x 2,0 cm (alvenaria);
- catálogo: a alvenaria aceita também 180-50, A0-45 e A0-40;
- linha vertical do selo: começa na borda do papel (planta de cargas, ``selo_desde_borda=True``)
  ou na margem inferior (alvenaria). Qual das duas é a correta ainda está em aberto.
"""
from typing import Iterable, Optional, Tuple

# Área do selo nas molduras oficiais do TQS (C:\TQSW\SUPORTE\NGE\MOLDURAS, A0-45, A1, 180-50...):
# largura de 17.5 cm encostada na margem direita; altura da margem inferior (y=1.0) até o topo
# da tabela de revisões (y=29.7, Nível 221), ou seja, carimbo + tabela de revisões = 28.7 cm.
SELO_LARGURA_CM = 17.5
SELO_ALTURA_CM = 28.7

# Catálogo oficial de formatos/molduras padronizados do TQS (D:\TQSW\SUPORTE\NGE\MOLDURAS)
# Todos os arquivos .DWG abaixo existem na instalação nativa do TQS. Largura máxima é rigorosamente 180.0 cm.
# (Nome, Largura_papel_cm, Altura_papel_cm)
CATALOGO_MOLDURAS_TQS = [
    # Formatos ISO Padronizados
    ("A3", 42.0, 29.7),
    ("A2", 59.4, 42.0),
    ("A1", 84.1, 59.4),
    ("A1L", 118.9, 59.4),
    ("A0", 118.9, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (95 cm)
    ("95-40", 95.0, 40.0),
    ("95-50", 95.0, 50.0),
    ("95-60", 95.0, 59.4),
    ("95-70", 95.0, 70.0),
    ("95-80", 95.0, 80.0),
    ("95-85", 95.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (105 cm)
    ("105-40", 105.0, 40.0),
    ("105-50", 105.0, 50.0),
    ("105-60", 105.0, 59.4),
    ("105-70", 105.0, 70.0),
    ("105-80", 105.0, 80.0),
    ("105-85", 105.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (130 cm)
    ("130-40", 130.0, 40.0),
    ("130-50", 130.0, 50.0),
    ("130-60", 130.0, 59.4),
    ("130-70", 130.0, 70.0),
    ("130-80", 130.0, 80.0),
    ("130-85", 130.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (140 cm)
    ("140-40", 140.0, 40.0),
    ("140-50", 140.0, 50.0),
    ("140-60", 140.0, 59.4),
    ("140-70", 140.0, 70.0),
    ("140-80", 140.0, 80.0),
    ("140-85", 140.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (150 cm)
    ("150-40", 150.0, 40.0),
    ("150-50", 150.0, 50.0),
    ("150-60", 150.0, 59.4),
    ("150-70", 150.0, 70.0),
    ("150-80", 150.0, 80.0),
    ("150-85", 150.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (160 cm)
    ("160-40", 160.0, 40.0),
    ("160-50", 160.0, 50.0),
    ("160-60", 160.0, 59.4),
    ("160-70", 160.0, 70.0),
    ("160-80", 160.0, 80.0),
    ("160-85", 160.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (170 cm)
    ("170-40", 170.0, 40.0),
    ("170-50", 170.0, 50.0),
    ("170-60", 170.0, 59.4),
    ("170-70", 170.0, 70.0),
    ("170-80", 170.0, 80.0),
    ("170-85", 170.0, 84.1),
    # Formatos Estendidos Oficiais TQS em Rolo (180 cm - Formato Máximo Oficial)
    ("180-50", 180.0, 50.0),
    ("180-55", 180.0, 55.0),
    ("180-60", 180.0, 59.4),
    ("180-65", 180.0, 65.0),
    ("180-70", 180.0, 70.0),
    ("180-75", 180.0, 75.0),
    ("180-80", 180.0, 80.0),
    ("180-85", 180.0, 84.1),
]

# Margens ABNT/TQS no papel (cm): 2,5 à esquerda (encadernação) e 1,0 nas demais
MARGEM_ESQ_CM = 2.5
MARGEM_CM = 1.0
MODULO_DOBRA_X_CM = 18.5
MODULO_DOBRA_Y_CM = 14.85


def selecionar_formato(
    bounds_conteudo: Tuple[float, float, float, float],
    escala: int,
    folga_cm: float,
    catalogo: Optional[Iterable[Tuple[str, float, float]]] = None,
) -> Optional[Tuple[str, float, float]]:
    """
    Menor formato do catálogo (por área de papel) que comporta o conteúdo com as margens
    e a folga de respiro. Devolve (nome, largura_cm, altura_cm) ou None se nenhum couber.
    """
    min_x, max_x, min_y, max_y = bounds_conteudo
    larg_min = ((max_x - min_x) + (MARGEM_ESQ_CM + MARGEM_CM + folga_cm) * escala) / escala
    alt_min = ((max_y - min_y) + (MARGEM_CM + MARGEM_CM + folga_cm) * escala) / escala
    candidatos = [
        (nome, wp, hp) for nome, wp, hp in (catalogo or CATALOGO_MOLDURAS_TQS)
        if wp >= larg_min and hp >= alt_min
    ]
    if not candidatos:
        return None
    return min(candidatos, key=lambda c: c[1] * c[2])


def posicao_centralizada(
    bounds_conteudo: Tuple[float, float, float, float], wp: float, hp: float, escala: int
) -> Tuple[float, float]:
    """Canto inferior esquerdo da folha que centraliza o conteúdo na área útil (margens 2,5/1,0)."""
    min_x, max_x, min_y, max_y = bounds_conteudo
    cx_papel_util = (wp + (MARGEM_ESQ_CM - MARGEM_CM)) / 2.0
    cy_papel_util = hp / 2.0
    x0 = (min_x + max_x) / 2.0 - cx_papel_util * escala
    y0 = (min_y + max_y) / 2.0 - cy_papel_util * escala
    return x0, y0


def desenhar_moldura(
    dwg,
    formato: str,
    wp: float,
    hp: float,
    escala: int,
    x0: float = 0.0,
    y0: float = 0.0,
    selo_desde_borda: bool = False,
) -> None:
    """
    Desenha borda do papel, margem útil, área do selo (canto inferior direito), marcas de
    dobra e o nome do formato, com origem da folha em (x0, y0). Usa o nível e a cor já
    definidos em ``dwg.draw`` (a cor deve ser -1, cor do nível).
    """
    w = wp * escala
    h = hp * escala
    mx0 = MARGEM_ESQ_CM * escala
    my0 = MARGEM_CM * escala
    mx1 = w - MARGEM_CM * escala
    my1 = h - MARGEM_CM * escala
    sx0 = mx1 - SELO_LARGURA_CM * escala
    sy1 = my0 + SELO_ALTURA_CM * escala
    d = dwg.draw

    # 1. Borda externa do papel
    d.Line(x0, y0, x0 + w, y0)
    d.Line(x0 + w, y0, x0 + w, y0 + h)
    d.Line(x0, y0, x0, y0 + h)
    d.Line(x0, y0 + h, x0 + w, y0 + h)

    # 2. Margem interna útil
    d.Line(x0 + mx0, y0 + my0, x0 + mx1, y0 + my0)
    d.Line(x0 + mx1, y0 + my0, x0 + mx1, y0 + my1)
    d.Line(x0 + mx0, y0 + my1, x0 + mx1, y0 + my1)
    d.Line(x0 + mx0, y0 + my1, x0 + mx0, y0 + my0)

    # 3. Área do selo (só a demarcação, sem carimbo)
    d.Line(x0 + sx0, y0 + (0.0 if selo_desde_borda else my0), x0 + sx0, y0 + sy1)
    d.Line(x0 + mx1, y0 + sy1, x0 + sx0, y0 + sy1)

    # 4. Marcas de dobra
    x_tick = sx0 - MODULO_DOBRA_X_CM * escala
    while x_tick > mx0:
        d.Line(x0 + x_tick, y0, x0 + x_tick, y0 + my0)
        d.Line(x0 + x_tick, y0 + my1, x0 + x_tick, y0 + h)
        x_tick -= MODULO_DOBRA_X_CM * escala

    y_tick = MODULO_DOBRA_Y_CM * escala
    while y_tick < my1:
        d.Line(x0, y0 + y_tick, x0 + mx0, y0 + y_tick)
        d.Line(x0 + mx1, y0 + y_tick, x0 + w, y0 + y_tick)
        y_tick += MODULO_DOBRA_Y_CM * escala

    # 5. Nome do formato na margem esquerda
    d.Text(x0 + mx0 - 0.4 * escala, y0 + my0 + 6.0 * escala, 1.8 * escala, 90.0, formato)
