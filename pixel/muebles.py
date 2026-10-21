"""Catálogo de muebles de las salas (las piezas de tipos/*.toml).

Cada pieza sabe su ancho, si va en el suelo o en la pared, cómo se pinta en la
capa fija de la tierra (`pintar`) y, si tiene algo que se mueve, cómo se anima
en cada fotograma (`animar`). Se colocan en huecos fijos de la sala para que sea
fácil montar habitaciones sin pensar en píxeles.
"""

import math
import random

import pygame

from .base import rgb

MADERA = (126, 82, 46)
MADERA_OSC = (92, 58, 32)
COLORES_LIBROS = [(230, 50, 50), (250, 220, 60), (60, 200, 90), (70, 140, 240), (240, 240, 240),
                  (230, 90, 200)]

# Huecos: posición del centro de la pieza, en fracción del ancho de la sala
HUECOS_SUELO = {"izquierda": 0.17, "centro_izquierda": 0.38, "centro": 0.5,
                "centro_derecha": 0.65, "derecha": 0.88}
HUECOS_PARED = {"pared_izquierda": 0.2, "pared": 0.5, "pared_centro": 0.5, "pared_derecha": 0.8}
ALTO_PARED = 16   # píxeles desde el techo de la sala hasta lo alto de un cuadro


class Contexto:
    """Lo que necesitan las piezas para pintarse: el día, el render y cuántas van de su clase."""

    def __init__(self, render, dia, aparece=0, indice=0):
        self.render, self.dia, self.aparece, self.indice = render, dia, aparece, indice

    @property
    def edad(self):
        """Días desde que apareció la pieza (para lo que crece)."""
        return self.dia - self.aparece


# ---------------------------------------------------------------- suelo

def escritorio(s, x, suelo, r, c, grande=False):
    w = 34 if grande else 26
    pygame.draw.rect(s, MADERA, (x, suelo - 11, w, 3))
    pygame.draw.rect(s, MADERA_OSC, (x + 1, suelo - 8, 2, 8))
    pygame.draw.rect(s, MADERA_OSC, (x + w - 3, suelo - 8, 2, 8))
    pygame.draw.rect(s, (30, 30, 36), (x + 6, suelo - 23, 14, 10))
    pygame.draw.rect(s, (60, 110, 170), (x + 7, suelo - 22, 12, 8))
    pygame.draw.rect(s, (30, 30, 36), (x + 12, suelo - 13, 2, 2))
    pygame.draw.rect(s, (200, 200, 205), (x + 5, suelo - 12, 10, 1))
    # silla
    pygame.draw.rect(s, (50, 50, 60), (x + w + 2, suelo - 14, 3, 8))
    pygame.draw.rect(s, (50, 50, 60), (x + w - 3, suelo - 7, 8, 2))
    pygame.draw.line(s, (40, 40, 48), (x + w + 1, suelo - 5), (x + w + 1, suelo - 1))


def escritorio_vivo(dst, x, suelo, r, c, t):
    if int(t * 3 + x) % 7 == 0:   # la pantalla parpadea de vez en cuando
        dst.fill((90, 150, 210), (x + 7, suelo - 22, 12, 8))


def sillon(s, x, suelo, r, c):
    pygame.draw.rect(s, (40, 36, 40), (x, suelo - 14, 12, 14))
    pygame.draw.rect(s, (60, 54, 60), (x, suelo - 14, 12, 4))


def sofa(s, x, suelo, r, c):
    base, osc = (150, 60, 60), (110, 40, 40)
    pygame.draw.rect(s, osc, (x, suelo - 14, 36, 8))
    pygame.draw.rect(s, base, (x + 2, suelo - 9, 32, 5))
    pygame.draw.rect(s, osc, (x - 2, suelo - 11, 5, 8))
    pygame.draw.rect(s, osc, (x + 33, suelo - 11, 5, 8))
    for k in (0, 34):
        pygame.draw.rect(s, MADERA_OSC, (x + k, suelo - 3, 2, 3))


def planta(s, x, suelo, r, c):
    edad = c.edad
    etapa = 0 if edad < 90 else 1 if edad < 240 else 2
    cx = x + 8
    pygame.draw.polygon(s, (180, 90, 50), [(cx - 4, suelo - 7), (cx + 4, suelo - 7), (cx + 3, suelo),
                                           (cx - 3, suelo)])
    hojas = [(6, 3), (12, 5), (18, 7)][etapa]
    rng = random.Random(cx)
    for _ in range(hojas[0] * 2):
        ang = rng.uniform(math.pi * 1.05, math.pi * 1.95)
        d = rng.uniform(2, hojas[0])
        pygame.draw.circle(s, rng.choice([(60, 150, 60), (90, 180, 70), (40, 120, 50)]),
                           (cx + int(math.cos(ang) * d * 0.8), suelo - 7 + int(math.sin(ang) * d)), 2)


def mesa_reuniones(s, x, suelo, r, c):
    mesa = pygame.Rect(r.x + 16, suelo - 12, r.width - 32, 4)
    pygame.draw.rect(s, MADERA, mesa)
    pygame.draw.rect(s, MADERA_OSC, (mesa.x + 4, mesa.bottom, 3, 8))
    pygame.draw.rect(s, MADERA_OSC, (mesa.right - 7, mesa.bottom, 3, 8))


def mesa_comedor(s, x, suelo, r, c):
    mesa = pygame.Rect(x, suelo - 12, 60, 3)
    pygame.draw.rect(s, MADERA, mesa)
    for px in (mesa.x + 3, mesa.right - 6):
        pygame.draw.rect(s, MADERA_OSC, (px, mesa.bottom, 3, 9))
    for k in range(4):
        pygame.draw.ellipse(s, (240, 240, 240), (mesa.x + 6 + k * 14, mesa.y - 2, 7, 2))


def nevera(s, x, suelo, r, c):
    pygame.draw.rect(s, (230, 232, 236), (x, suelo - 34, 16, 34))
    pygame.draw.line(s, (170, 170, 176), (x, suelo - 22), (x + 15, suelo - 22))
    pygame.draw.rect(s, (150, 150, 156), (x + 12, suelo - 30, 2, 5))
    pygame.draw.rect(s, (150, 150, 156), (x + 12, suelo - 18, 2, 6))


def encimera(s, x, suelo, r, c):
    enc = pygame.Rect(x, suelo - 14, 40, 14)
    pygame.draw.rect(s, MADERA_OSC, enc)
    pygame.draw.rect(s, (150, 150, 158), (enc.x + 3, enc.y - 11, 18, 11))
    pygame.draw.rect(s, (40, 50, 60), (enc.x + 5, enc.y - 9, 10, 7))
    s.set_at((enc.x + 18, enc.y - 6), (90, 230, 120))
    pygame.draw.rect(s, (40, 36, 36), (enc.x + 27, enc.y - 13, 8, 13))
    pygame.draw.rect(s, (240, 240, 240), (enc.x + 29, enc.y - 4, 3, 3))


def encimera_viva(dst, x, suelo, r, c, t):
    cx = x + 31   # vapor de la cafetera
    for k in range(3):
        fase = (t * 0.8 + k / 3) % 1
        dst.fill((200, 200, 200), (cx + int(math.sin(fase * 6 + k) * 2), suelo - 18 - int(fase * 14), 1, 2))


def fuente(s, x, suelo, r, c):
    pygame.draw.rect(s, (225, 228, 232), (x, suelo - 18, 12, 18))
    pygame.draw.rect(s, (60, 120, 200), (x + 4, suelo - 12, 4, 3))
    pygame.draw.rect(s, (150, 200, 240), (x + 1, suelo - 32, 10, 14))
    pygame.draw.rect(s, (110, 170, 230), (x + 1, suelo - 26, 10, 8))
    pygame.draw.rect(s, (190, 225, 250), (x + 3, suelo - 31, 2, 10))


def fuente_viva(dst, x, suelo, r, c, t):
    if int(t * 2) % 3 == 0:   # una burbuja que sube por la garrafa
        dst.fill((210, 235, 255), (x + 4, suelo - 28 + int(t * 6) % 8, 2, 2))


def estanteria(s, x, suelo, r, c, libros=True):
    pygame.draw.rect(s, MADERA_OSC, (x, suelo - 30, 22, 30), 2)
    for fila in range(3):
        yy = suelo - 28 + fila * 9
        pygame.draw.line(s, MADERA_OSC, (x, yy + 8), (x + 21, yy + 8))
        if libros:
            for libro in range(5):
                pygame.draw.rect(s, COLORES_LIBROS[(libro + fila + c.indice) % 6], (x + 3 + libro * 3, yy + 2, 2, 6))


def vitrina(s, x, suelo, r, c):
    estanteria(s, x, suelo, r, c, libros=False)
    m = c.render.m
    hallados = [o for o in m.plan.objetos if o[5] <= m.dia_obras]
    for i, (_x, _y, nombre, _icono, col, _d) in enumerate(hallados[c.indice * 6:c.indice * 6 + 6]):
        ex = x + 3 + (i % 2) * 9
        yy = suelo - 27 + (i // 2) * 9
        c.render._objeto(s, ex, yy, nombre, rgb(col))


def sacos(s, x, suelo, r, c):
    for k in range(2):
        px = x + k * 14
        pygame.draw.ellipse(s, (200, 170, 100), (px, suelo - 12, 12, 12))
        pygame.draw.rect(s, (160, 130, 70), (px + 3, suelo - 15, 6, 4))


def cajas(s, x, suelo, r, c):
    for px, py, w, h in ((0, 12, 14, 12), (15, 12, 12, 12), (4, 24, 12, 12)):
        caja = pygame.Rect(x + px, suelo - py, w, h)
        pygame.draw.rect(s, (170, 130, 80), caja)
        pygame.draw.rect(s, (120, 90, 54), caja, 1)
        pygame.draw.line(s, (120, 90, 54), (caja.x, caja.y + 3), (caja.right - 1, caja.y + 3))


def setas(s, x, suelo, r, c):
    for k in range(5):
        px = x + k * 16
        pygame.draw.rect(s, (235, 225, 200), (px + 3, suelo - 7, 3, 7))
        pygame.draw.ellipse(s, (200, 50, 50) if k % 2 == 0 else (190, 140, 90), (px, suelo - 11, 9, 6))
        s.set_at((px + 3, suelo - 10), (255, 255, 255))


# ---------------------------------------------------------------- pared

def cuadro(s, x, y, r, c):
    marcos = [(150, 110, 60), (200, 170, 60), (170, 170, 175)]
    h = r.x // 4 + c.indice
    pygame.draw.rect(s, marcos[h % 3], (x, y, 14, 11))
    dentro = pygame.Rect(x + 2, y + 2, 10, 7)
    pygame.draw.rect(s, (120, 180, 220), dentro)
    pygame.draw.polygon(s, (70, 130, 70), [(dentro.x, dentro.bottom), (dentro.x + 4, dentro.y + 3),
                                           (dentro.right, dentro.bottom)])
    s.set_at((dentro.right - 2, dentro.y + 1), (255, 230, 90))


def pantalla(s, x, y, r, c):
    pant = pygame.Rect(x, y - 2, 44, 22)
    pygame.draw.rect(s, (40, 40, 48), pant)
    pygame.draw.rect(s, (30, 60, 110), pant.inflate(-4, -4))
    for k, h in enumerate((5, 9, 7, 13, 11)):
        pygame.draw.rect(s, (90, 200, 120), (pant.x + 6 + k * 7, pant.bottom - 4 - h, 4, h))


def pizarra(s, x, y, r, c):
    p = pygame.Rect(x, y - 2, 36, 18)
    pygame.draw.rect(s, (150, 150, 158), p)
    pygame.draw.rect(s, (238, 240, 236), p.inflate(-2, -2))
    rng = random.Random(r.x + c.indice)
    for fila in range(3):
        xx = p.x + 4
        while xx < p.right - 6:
            largo = rng.randint(2, 7)
            col = rng.choice([(40, 60, 160), (40, 40, 40), (180, 40, 40)])
            pygame.draw.line(s, col, (xx, p.y + 4 + fila * 4), (min(p.right - 4, xx + largo), p.y + 4 + fila * 4))
            xx += largo + 2
    pygame.draw.rect(s, (120, 120, 128), (p.x + 4, p.bottom, p.width - 8, 2))


def reloj(s, x, y, r, c):
    pygame.draw.circle(s, (60, 50, 40), (x + 6, y + 6), 7)
    pygame.draw.circle(s, (240, 236, 220), (x + 6, y + 6), 6)


def reloj_vivo(dst, x, y, r, c, t):
    ahora = c.render.m.ahora
    cx, cy = x + 6, y + 6
    for valor, largo, col in ((ahora.hour % 12 + ahora.minute / 60, 3, (30, 30, 30)), (ahora.minute / 5, 5, (60, 60, 60))):
        ang = math.radians(valor * 30 - 90)
        pygame.draw.line(dst, col, (cx, cy), (cx + round(math.cos(ang) * largo), cy + round(math.sin(ang) * largo)))


# ---------------------------------------------------------------- catálogo

# nombre: (ancho en píxeles, "suelo" | "pared", hueco por defecto, pintar, animar)
PIEZAS = {
    "escritorio": (33, "suelo", "izquierda", escritorio, escritorio_vivo),
    "escritorio_grande": (41, "suelo", "izquierda", lambda *a: escritorio(*a, grande=True), escritorio_vivo),
    "sillon": (12, "suelo", "centro_derecha", sillon, None),
    "sofa": (38, "suelo", "centro", sofa, None),
    "planta": (16, "suelo", "derecha", planta, None),
    "mesa_reuniones": (0, "suelo", "centro", mesa_reuniones, None),
    "mesa_comedor": (60, "suelo", "centro", mesa_comedor, None),
    "nevera": (16, "suelo", "izquierda", nevera, None),
    "encimera": (40, "suelo", "derecha", encimera, encimera_viva),
    "fuente": (12, "suelo", "izquierda", fuente, fuente_viva),
    "estanteria": (22, "suelo", "izquierda", estanteria, None),
    "vitrina": (22, "suelo", "izquierda", vitrina, None),
    "sacos": (26, "suelo", "izquierda", sacos, None),
    "cajas": (27, "suelo", "izquierda", cajas, None),
    "setas": (73, "suelo", "centro", setas, None),
    "cuadro": (14, "pared", "pared", cuadro, None),
    "pantalla": (44, "pared", "pared", pantalla, None),
    "pizarra": (36, "pared", "pared", pizarra, None),
    "reloj": (13, "pared", "pared_derecha", reloj, reloj_vivo),
}


def colocar(pieza, sitio, r):
    """Esquina (x, y) donde va la pieza dentro del rectángulo r de la sala.
    En las piezas de suelo, y es la línea del suelo; en las de pared, lo alto de la pieza."""
    ancho, donde, defecto = PIEZAS[pieza][:3]
    sitio = defecto if sitio is None else sitio
    if isinstance(sitio, (int, float)):
        frac = max(0.0, min(100.0, float(sitio))) / 100
    else:
        frac = {**HUECOS_SUELO, **HUECOS_PARED}.get(str(sitio).lower(), None)
        if frac is None:
            frac = {**HUECOS_SUELO, **HUECOS_PARED}[defecto]
    x = int(r.x + frac * r.width - ancho / 2)
    x = max(r.x + 4, min(r.right - 4 - ancho, x))
    y = r.bottom if donde == "suelo" else r.y + ALTO_PARED
    return x, y
