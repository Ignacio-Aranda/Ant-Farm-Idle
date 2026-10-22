"""Catálogo del paisaje: lo que se pone en la superficie y al fondo, sobre los montes.

Se elige en config.toml ([[paisaje.suelo]] y [[paisaje.fondo]]), cada pieza con su
posición `x` en tanto por ciento del ancho (0 = borde izquierdo, 100 = derecho).
Cada pieza se pinta de día; por la noche toda la superficie se oscurece y luego se
encienden las luces de las piezas que tienen (ventanas, farolas, el faro...).
"""

import math
import random

import pygame

from . import arte as A
from .base import CLAVE, circulo_luz, oscuro


class Contexto:
    def __init__(self, dia, semilla, noche, indice=0):
        self.dia, self.semilla, self.noche, self.indice = dia, semilla, noche, indice


# ================================================================ suelo

def chumbera(s, cx, G, c):
    x = cx - 6
    verde, osc = (96, 150, 70), (64, 110, 50)
    palas = [(0, -10, 9, 12), (8, -18, 9, 11), (-6, -20, 8, 10), (3, -28, 8, 10), (12, -28, 7, 9)]
    pygame.draw.rect(s, (110, 120, 70), (x + 2, G - 6, 4, 6))
    for dx, dy, w, h in palas:
        pygame.draw.ellipse(s, osc, (x + dx, G + dy, w, h))
        pygame.draw.ellipse(s, verde, (x + dx + 1, G + dy + 1, w - 2, h - 3))
        for k in range(3):
            s.set_at((x + dx + 2 + k * 2, G + dy + 3 + (k % 2) * 3), (230, 230, 190))
    if 182 <= c.dia <= 273:   # higos chumbos en verano
        for dx, dy in ((4, -29), (11, -29), (15, -29), (12, -19)):
            pygame.draw.ellipse(s, (210, 70, 60), (x + dx, G + dy - 2, 3, 4))


def almendro(s, cx, G, c):
    r = random.Random("almendro-%s-%s" % (c.semilla, c.indice))
    tronco, tronco_o = (110, 74, 50), (80, 52, 34)
    pygame.draw.polygon(s, tronco_o, [(cx - 4, G), (cx + 4, G), (cx + 2, G - 22), (cx - 2, G - 22)])
    pygame.draw.polygon(s, tronco, [(cx - 3, G), (cx + 2, G), (cx + 1, G - 22), (cx - 1, G - 22)])
    ramas = [((cx, G - 20), (cx - 16, G - 38)), ((cx, G - 22), (cx + 18, G - 40)),
             ((cx, G - 24), (cx - 4, G - 48)), ((cx - 8, G - 30), (cx - 24, G - 34)),
             ((cx + 9, G - 31), (cx + 26, G - 33)), ((cx - 2, G - 36), (cx + 8, G - 50))]
    for a, b in ramas:
        pygame.draw.line(s, tronco_o, a, b, 3)
        pygame.draw.line(s, tronco, a, b, 1)
    dia = c.dia
    if dia < 20 or dia > 335:
        return  # invierno: ramas desnudas
    if dia <= 64:
        cols, dens = [(250, 190, 210), (255, 235, 240), (240, 160, 190), (255, 255, 255)], 1.0
    elif dia <= 273:
        cols, dens = [(70, 140, 60), (90, 165, 70), (55, 115, 50), (110, 180, 80)], 1.0
    else:
        dens = max(0.15, 1 - (dia - 273) / 60)
        cols = [(220, 140, 50), (200, 100, 40), (230, 190, 70), (150, 90, 50)]
    for _ in range(int(150 * dens)):
        ang = r.uniform(0, math.pi)
        rad = r.uniform(0, 1) ** 0.6
        x = cx + int(math.cos(ang) * rad * 32)
        y = G - 40 - int(math.sin(ang) * rad * 22) + r.randint(-4, 6)
        pygame.draw.circle(s, r.choice(cols), (x, y), r.choice((2, 2, 3)))
    if 65 <= dia <= 180:  # mariquitas
        for k in range(3):
            pygame.draw.circle(s, (220, 30, 30), (cx - 14 + k * 13, G - 42 + (k % 2) * 5), 1)


def palmera(s, cx, G, c):
    tronco = [(150, 110, 70), (120, 86, 54)]
    for k in range(14):
        y = G - k * 4
        x = cx + int(math.sin(k / 6) * 3)
        pygame.draw.rect(s, tronco[k % 2], (x - 3, y - 4, 6, 4))
    tx, ty = cx + int(math.sin(13 / 6) * 3), G - 56
    hojas = (60, 130, 60), (90, 160, 70)
    for ang in (-170, -140, -110, -70, -40, -10, 20, -90):
        a = math.radians(ang)
        pts = []
        for k in range(9):
            d = k * 4
            pts.append((tx + int(math.cos(a) * d), ty + int(math.sin(a) * d * 0.6 + (k * k) * 0.35)))
        pygame.draw.lines(s, hojas[0], False, pts, 3)
        pygame.draw.lines(s, hojas[1], False, pts, 1)
        for (x, y) in pts[2::2]:
            pygame.draw.line(s, hojas[0], (x, y), (x + 2, y + 3))
            pygame.draw.line(s, hojas[0], (x, y), (x - 2, y + 3))
    if 213 <= c.dia <= 300:   # dátiles
        for k in range(5):
            pygame.draw.circle(s, (220, 140, 40), (tx - 4 + k * 2, ty + 3 + (k % 2)), 1)


def olivo(s, cx, G, c):
    r = random.Random("olivo-%s-%s" % (c.semilla, c.indice))
    t1, t2 = (100, 86, 66), (70, 60, 46)
    pygame.draw.polygon(s, t2, [(cx - 6, G), (cx + 6, G), (cx + 2, G - 10), (cx + 4, G - 18), (cx - 1, G - 20),
                                (cx - 3, G - 12)])
    pygame.draw.line(s, t1, (cx - 2, G), (cx + 1, G - 16), 2)
    pygame.draw.line(s, t2, (cx, G - 16), (cx - 10, G - 24), 2)
    pygame.draw.line(s, t2, (cx + 2, G - 16), (cx + 11, G - 25), 2)
    cols = [(120, 140, 90), (100, 122, 76), (140, 158, 108), (88, 110, 70)]
    for _ in range(110):
        ang = r.uniform(0, math.pi)
        rad = r.uniform(0, 1) ** 0.6
        x = cx + int(math.cos(ang) * rad * 24)
        y = G - 28 - int(math.sin(ang) * rad * 12) + r.randint(-3, 5)
        pygame.draw.circle(s, r.choice(cols), (x, y), 2)
    if c.dia >= 274 or c.dia <= 31:   # aceitunas
        for _ in range(14):
            x, y = cx + r.randint(-18, 18), G - 28 + r.randint(-8, 5)
            s.set_at((x, y), (70, 30, 70))
            s.set_at((x + 1, y), (50, 20, 50))


def pino(s, cx, G, c):
    r = random.Random("pino-%s-%s" % (c.semilla, c.indice))
    pygame.draw.rect(s, (90, 60, 40), (cx - 2, G - 14, 4, 14))
    for k, (w, y) in enumerate(((30, 12), (24, 22), (18, 31), (11, 39))):
        col = (36, 96 + k * 6, 56)
        pygame.draw.polygon(s, col, [(cx - w // 2, G - y), (cx + w // 2, G - y), (cx, G - y - 14)])
    for _ in range(12):
        s.set_at((cx + r.randint(-10, 10), G - r.randint(14, 40)), (24, 70, 40))


def farola(s, cx, G, c):
    x = cx
    pygame.draw.rect(s, (40, 40, 46), (x, G - 34, 2, 34))
    pygame.draw.rect(s, (40, 40, 46), (x - 2, G - 2, 6, 2))
    pygame.draw.polygon(s, (40, 40, 46), [(x - 4, G - 36), (x + 5, G - 36), (x + 3, G - 42), (x - 2, G - 42)])
    pygame.draw.rect(s, (190, 190, 170), (x - 2, G - 41, 5, 4))


def farola_luz(s, cx, G, c):
    pygame.draw.rect(s, (255, 230, 150), (cx - 2, G - 41, 5, 4))


def banco(s, cx, G, c):
    x = cx - 12
    madera, hierro = (150, 100, 60), (50, 50, 56)
    for k in range(2):
        pygame.draw.rect(s, madera, (x, G - 9 + k * 3 - 6 * (k == 0), 24, 2))
    pygame.draw.rect(s, madera, (x, G - 7, 24, 2))
    for px in (x + 2, x + 20):
        pygame.draw.rect(s, hierro, (px, G - 7, 2, 7))
    pygame.draw.rect(s, hierro, (x + 1, G - 15, 2, 8))
    pygame.draw.rect(s, hierro, (x + 21, G - 15, 2, 8))


def casa(s, cx, G, c):
    r = random.Random("casa-%s-%s" % (c.semilla, c.indice))
    pared = r.choice([(236, 226, 200), (240, 236, 228), (220, 190, 150), (230, 210, 170)])
    x, w, h = cx - 20, 40, 30
    pygame.draw.rect(s, pared, (x, G - h, w, h))
    pygame.draw.rect(s, oscuro(pared, 0.8), (x, G - h, w, h), 1)
    teja = r.choice([(170, 70, 50), (150, 60, 45), (110, 60, 50)])
    pygame.draw.polygon(s, teja, [(x - 4, G - h), (x + w + 4, G - h), (x + w // 2, G - h - 16)])
    pygame.draw.rect(s, (110, 70, 40), (cx - 4, G - 14, 8, 14))           # puerta
    for vx in (x + 5, x + w - 13):
        pygame.draw.rect(s, (60, 80, 110), (vx, G - h + 8, 8, 8))          # ventanas
        pygame.draw.rect(s, (250, 250, 250), (vx, G - h + 8, 8, 8), 1)
    pygame.draw.rect(s, oscuro(teja, 0.8), (x + w - 10, G - h - 14, 5, 8))  # chimenea


def casa_luz(s, cx, G, c):
    r = random.Random("luces-%s-%s" % (c.semilla, c.indice))
    x, h = cx - 20, 30
    for vx in (x + 5, x + 40 - 13):
        if r.random() < 0.7:
            pygame.draw.rect(s, (255, 214, 120), (vx + 1, G - h + 9, 6, 6))


# ================================================================ fondo (sobre los montes)

def catedral(s, cx, base, c, cuerpo, luz):
    img = A.rejilla(A.CATEDRAL, {"k": cuerpo, "w": luz if c.noche else oscuro(cuerpo, 0.7)})
    img = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
    img.set_colorkey(CLAVE)
    s.blit(img, (cx - img.get_width() // 2, base - img.get_height() + 4))


def ciudad(s, cx, base, c, cuerpo, luz):
    r = random.Random("ciudad-%s-%s" % (c.semilla, c.indice))
    x = cx - 50
    while x < cx + 50:
        w, h = r.randint(8, 16), r.randint(12, 40)
        tono = oscuro(cuerpo, r.uniform(0.8, 1.1)) if c.noche else tuple(min(255, int(v * r.uniform(0.9, 1.1)))
                                                                        for v in cuerpo)
        pygame.draw.rect(s, tono, (x, base - h, w, h + 4))
        for vy in range(base - h + 3, base - 2, 5):
            for vx in range(x + 2, x + w - 2, 4):
                if c.noche and r.random() < 0.45:
                    s.fill(luz, (vx, vy, 2, 2))
                elif not c.noche and r.random() < 0.6:
                    s.fill(oscuro(tono, 0.8), (vx, vy, 2, 2))
        x += w + r.randint(0, 3)


def faro(s, cx, base, c, cuerpo, luz):
    for k in range(9):
        col = (230, 230, 230) if k % 2 == 0 else (200, 50, 50)
        if c.noche:
            col = oscuro(col, 0.35)
        w = 10 - k // 3
        pygame.draw.rect(s, col, (cx - w // 2, base - 4 - k * 4, w, 4))
    pygame.draw.rect(s, luz if c.noche else (200, 200, 180), (cx - 3, base - 46, 6, 6))
    pygame.draw.polygon(s, oscuro(cuerpo, 0.6), [(cx - 5, base - 46), (cx + 5, base - 46), (cx, base - 52)])


HAZ_LARGO, HAZ_ALTO = 134, 53   # el haz del faro visto de lado, entero (en píxeles)
_HAZ = {}                       # el haz y el resplandor de la lámpara, ya dibujados


def _haz_de_luz():
    """El haz del faro de lado, hacia la derecha, para sumarlo al cielo (BLEND_ADD: el negro no
    cambia nada): un triángulo de luz cálida que se abre desde la lámpara, más brillante cerca de
    ella y en el centro, y que se desvanece hacia la punta y hacia los bordes."""
    s = pygame.Surface((HAZ_LARGO, HAZ_ALTO), 0, 32)
    s.fill((0, 0, 0))
    medio = HAZ_ALTO // 2
    for x in range(HAZ_LARGO):
        d = x / (HAZ_LARGO - 1)                     # 0 en la lámpara, 1 en la punta
        abierto = 1.5 + d * (medio - 1.5)           # medio alto del haz en esta columna
        fuerza = (1 - d) * (0.55 + 0.45 * min(1.0, x / 6))
        for y in range(HAZ_ALTO):
            borde = abs(y - medio) / abierto
            if borde < 1:
                f = fuerza * (1 - borde) ** 0.7
                s.set_at((x, y), (int(215 * f), int(180 * f), int(85 * f)))
    return s


def faro_vivo(dst, cx, base, c, t):
    """El haz del faro barriendo el cielo (sólo de noche). Gira: de lado se ve entero, y al
    apuntar hacia aquí (o hacia el otro lado) se acorta; cuando apunta hacia aquí, la lámpara
    deslumbra un momento."""
    if not c.noche:
        return
    if "haz" not in _HAZ:
        _HAZ["haz"] = _haz_de_luz()
        _HAZ["brillos"] = [circulo_luz(12, (255, 225, 160), 60 + 30 * k) for k in range(6)]
    ang = t * 0.9
    lado = math.cos(ang)            # > 0, hacia la derecha; < 0, hacia la izquierda
    ly = base - 43                  # la lámpara
    largo = int(abs(lado) * HAZ_LARGO) // 2 * 2
    if largo >= 4:
        clave = (largo, lado < 0)
        haz = _HAZ.get(clave)
        if haz is None:
            haz = pygame.transform.smoothscale(_HAZ["haz"], (largo, HAZ_ALTO))
            k = min(1.0, 3 * largo / HAZ_LARGO)   # muy corto (casi de frente o de espaldas), más tenue
            if k < 1:
                haz.fill((int(255 * k),) * 3, special_flags=pygame.BLEND_MULT)
            if lado < 0:
                haz = pygame.transform.flip(haz, True, False)
            _HAZ[clave] = haz
        dst.blit(haz, (cx if lado > 0 else cx - largo, ly - HAZ_ALTO // 2), special_flags=pygame.BLEND_ADD)
    hacia_aqui = max(0.0, math.sin(ang)) ** 4
    brillo = _HAZ["brillos"][min(5, int(hacia_aqui * 6))]
    dst.blit(brillo, (cx - 12, ly - 12), special_flags=pygame.BLEND_ADD)


def molino(s, cx, base, c, cuerpo, luz):
    pygame.draw.polygon(s, oscuro((235, 230, 220), 0.4) if c.noche else (235, 230, 220),
                        [(cx - 8, base), (cx + 8, base), (cx + 5, base - 26), (cx - 5, base - 26)])
    pygame.draw.polygon(s, oscuro(cuerpo, 0.7), [(cx - 7, base - 26), (cx + 7, base - 26), (cx, base - 34)])
    pygame.draw.rect(s, luz if c.noche else (60, 50, 40), (cx - 2, base - 16, 3, 4))


def molino_vivo(dst, cx, base, c, t):
    """Las aspas del molino girando despacio."""
    col = (60, 56, 50) if c.noche else (120, 100, 80)
    for k in range(4):
        a = t * 0.6 + k * math.pi / 2
        x2, y2 = cx + int(math.cos(a) * 18), base - 26 + int(math.sin(a) * 18)
        pygame.draw.line(dst, col, (cx, base - 26), (x2, y2), 2)


def torre(s, cx, base, c, cuerpo, luz):
    pygame.draw.rect(s, cuerpo, (cx - 6, base - 40, 12, 44))
    pygame.draw.polygon(s, oscuro(cuerpo, 0.75), [(cx - 8, base - 40), (cx + 8, base - 40), (cx, base - 56)])
    pygame.draw.rect(s, luz if c.noche else oscuro(cuerpo, 0.6), (cx - 2, base - 34, 4, 6))
    pygame.draw.circle(s, (240, 236, 220) if not c.noche else luz, (cx, base - 22), 3)


def castillo(s, cx, base, c, cuerpo, luz):
    for dx, h in ((-22, 26), (14, 26)):
        pygame.draw.rect(s, cuerpo, (cx + dx, base - h, 9, h + 4))
        for k in range(3):
            pygame.draw.rect(s, cuerpo, (cx + dx + k * 3, base - h - 3, 2, 3))
    pygame.draw.rect(s, cuerpo, (cx - 14, base - 18, 28, 22))
    for k in range(7):
        pygame.draw.rect(s, cuerpo, (cx - 14 + k * 4, base - 21, 2, 3))
    pygame.draw.rect(s, luz if c.noche else oscuro(cuerpo, 0.6), (cx - 3, base - 10, 6, 10))


# ================================================================ catálogo

# suelo: nombre -> (pintar, luces de noche, ¿es un árbol?)
SUELO = {
    "chumbera": (chumbera, None, False),
    "almendro": (almendro, None, True),
    "palmera": (palmera, None, True),
    "olivo": (olivo, None, True),
    "pino": (pino, None, True),
    "farola": (farola, farola_luz, False),
    "banco": (banco, None, False),
    "casa": (casa, casa_luz, False),
}

# lo que ocupa cada pieza de la superficie a cada lado de su x, en píxeles (con la copa de los
# árboles y el tejado de la casa): el cementerio busca un sitio donde no tape ninguna
ANCHO_SUELO = {
    "chumbera": (12, 12),
    "almendro": (34, 33),
    "palmera": (31, 35),
    "olivo": (25, 24),
    "pino": (15, 15),
    "farola": (4, 5),
    "banco": (12, 11),
    "casa": (24, 24),
}

# fondo: nombre -> (pintar, animar o None)
FONDO = {
    "catedral": (catedral, None),
    "ciudad": (ciudad, None),
    "faro": (faro, faro_vivo),
    "molino": (molino, molino_vivo),
    "torre": (torre, None),
    "castillo": (castillo, None),
}
