"""La hormiga en pixel art, dibujada por partes (28x14 píxeles, mirando a la derecha).

El ancla es la cintura (columna ANCLA_X) y la última fila (las patas tocan el suelo).
Las patas se mueven en trípode, como las de verdad.
"""

import math

import pygame

from .base import claro, espejo, oscuro, superficie

ANCHO, ALTO = 28, 14
ANCLA_X = 12
CADERAS = (14, 16, 18)


def _cuerpo(s, color, dormida=False):
    d = oscuro(color, 0.42)
    l = claro(color, 0.45)
    # abdomen (gáster)
    pygame.draw.ellipse(s, d, (0, 3, 12, 8))
    pygame.draw.ellipse(s, color, (1, 4, 10, 6))
    pygame.draw.ellipse(s, l, (3, 4, 4, 2))
    s.set_at((2, 7), oscuro(color, 0.75))
    s.set_at((5, 8), oscuro(color, 0.75))
    # cintura (pecíolo)
    pygame.draw.rect(s, d, (11, 6, 3, 2))
    # tórax
    pygame.draw.ellipse(s, d, (13, 4, 6, 5))
    pygame.draw.ellipse(s, color, (14, 5, 4, 3))
    s.set_at((15, 5), l)
    # cabeza
    hy = 5 if dormida else 3
    pygame.draw.ellipse(s, d, (18, hy, 8, 7))
    pygame.draw.ellipse(s, color, (19, hy + 1, 6, 5))
    s.set_at((20, hy + 1), l)
    if dormida:
        pygame.draw.line(s, (20, 20, 20), (22, hy + 3), (23, hy + 3))
    else:
        s.set_at((23, hy + 2), (250, 250, 240))
        s.set_at((23, hy + 3), (20, 20, 20))
    # mandíbulas
    pygame.draw.line(s, d, (25, hy + 4), (27, hy + 5))
    pygame.draw.line(s, d, (25, hy + 5), (26, hy + 6))
    # antenas acodadas
    if not dormida:
        pygame.draw.line(s, d, (21, 3), (21, 1))
        pygame.draw.line(s, d, (21, 1), (25, 0))
        pygame.draw.line(s, d, (22, 3), (23, 2))
        pygame.draw.line(s, d, (23, 2), (26, 2))
    else:
        pygame.draw.line(s, d, (22, hy), (25, hy + 1))


HUESO = (226, 222, 204)
NEGRO = (30, 28, 34)


def _huesos(s, dormida=False):
    """Encima de un cuerpo negro: costillas, columna y una calavera con las cuencas vacías."""
    for x in (3, 5, 7, 9):
        pygame.draw.line(s, HUESO, (x, 5), (x, 8))
    pygame.draw.line(s, HUESO, (2, 6), (10, 6))
    pygame.draw.line(s, HUESO, (11, 6), (18, 6))
    hy = 5 if dormida else 3
    pygame.draw.ellipse(s, HUESO, (19, hy + 1, 6, 5))
    s.set_at((22, hy + 2), (10, 10, 10))
    s.set_at((23, hy + 2), (10, 10, 10))
    for x in (21, 23):
        s.set_at((x, hy + 5), (10, 10, 10))


def _patas(s, color, fase, c=None):
    c = c or oscuro(color, 0.55)
    for i, hx in enumerate(CADERAS):
        ph = fase + (0 if i % 2 == 0 else math.pi)  # trípode: 1ª y 3ª juntas
        dx = round(2.5 * math.sin(ph)) + (-1 if i == 0 else 1 if i == 2 else 0)
        alza = 1 if math.cos(ph) > 0.5 else 0
        rod = (hx + (-1 if i == 0 else 1 if i == 2 else 0) + dx // 2, 10 - alza)
        pie = (hx + dx, 13 - alza)
        pygame.draw.line(s, c, (hx, 8), rod)
        pygame.draw.line(s, c, rod, pie)


def fotogramas(color, esqueleto=False):
    """{(dirección, clave): Surface}; claves 0-3 (andar), 'quieta' y 'dormida'.
    esqueleto: una hormiga negra con los huesos a la vista (para Halloween)."""
    if esqueleto:
        color = NEGRO
    patas = HUESO if esqueleto else None
    out = {}
    for i in range(4):
        s = superficie(ANCHO, ALTO)
        _patas(s, color, i * math.pi / 2, patas)
        _cuerpo(s, color)
        if esqueleto:
            _huesos(s)
        out[(1, i)] = s
        out[(-1, i)] = espejo(s)
    q = superficie(ANCHO, ALTO)
    _patas(q, color, math.pi / 2, patas)
    _cuerpo(q, color)
    if esqueleto:
        _huesos(q)
    out[(1, "quieta")] = q
    out[(-1, "quieta")] = espejo(q)
    d = superficie(ANCHO, ALTO)
    c = patas or oscuro(color, 0.55)
    pygame.draw.line(d, c, (12, 12), (20, 12))
    _cuerpo(d, color, dormida=True)
    if esqueleto:
        _huesos(d, dormida=True)
    out[(1, "dormida")] = d
    out[(-1, "dormida")] = espejo(d)
    return out
