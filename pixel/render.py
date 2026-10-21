"""Dibuja el hormiguero en pixel art a partir del estado de la simulación.

La simulación (hormiga/mundo.py) trabaja en celdas de la versión de terminal;
aquí cada celda son 4x8 píxeles de una imagen interna de 640x512, que luego
se escala x2 a los 1280x1024 del monitor.

Para que la Raspberry Pi 3 vaya holgada, todo lo que no cambia en cada
fotograma se guarda en capas: el cielo (cada minuto), los montes, la
superficie (árboles, cementerio... cada día) y la tierra (sólo se repinta lo
que se excava).
"""

import math
import random

import pygame

from hormiga import tiempo as T
from hormiga.tierra import ANCHO, ARCILLA, ARENA, HUMUS, PROF, ROCA

from . import arte as A
from . import hormiga_arte as HA
from . import muebles as MU
from . import paisaje as PA
from .base import (CH, CW, CLAVE, Letras, circulo_luz, claro, espejo, mezclar, multiplicar, oscuro,
                   reloj_grande, rgb, superficie, tenir)

TIERRA = {
    HUMUS: [(92, 62, 38), (84, 56, 34), (100, 70, 44), (76, 50, 30)],
    ARENA: [(176, 140, 92), (166, 130, 84), (186, 150, 100), (156, 122, 78)],
    ARCILLA: [(150, 92, 58), (140, 84, 52), (160, 100, 64), (128, 76, 46)],
    ROCA: [(118, 112, 108), (104, 98, 95), (132, 126, 120), (92, 88, 85)],
}
TUNEL = (34, 23, 17)
PARED_SALA = (66, 47, 34)
MADERA = (126, 82, 46)
MADERA_OSC = (92, 58, 32)
PAREDES = {"madera": PARED_SALA, "azulejo": (52, 70, 82), "piedra": (74, 70, 68)}

COLORES_FIESTA = [(230, 50, 50), (250, 220, 60), (60, 200, 90), (70, 140, 240), (240, 240, 240),
                  (230, 90, 200)]


def _hash(*v):
    h = 0
    for x in v:
        h = (h * 1000003 + int(x)) & 0xFFFFFFFF
    return h


class Render:
    def __init__(self, m, destino):
        self.m = m
        self.dst = destino
        self.W, self.H = destino.get_size()
        self.letras = Letras()
        self.rng = random.Random()
        self.G = m.oy * CH                      # línea del suelo en píxeles
        self.capa_cielo = None
        self.clave_cielo = None
        self.capa_montes = None
        self.clave_montes = None
        self.capa_sup = None
        self.clave_sup = None
        self.capa_tierra = pygame.Surface((self.W, PROF * CH)).convert()
        self.cavado_pintado = bytearray(ANCHO * PROF)
        self.clave_salas = None
        self.tierra_lista = False
        self.cache_hormigas = {}
        self.cache_reloj = (None, None)
        self.estrellas = [(random.Random(i).randrange(self.W), random.Random(i * 7).randrange(self.G - 30),
                           random.Random(i * 3).uniform(0, 6.3)) for i in range(140)]
        self.halo_lampara = circulo_luz(26, (255, 200, 120), 70)
        self.halo_farola = circulo_luz(40, (255, 210, 130), 90)
        self.halo_sol = circulo_luz(22, (255, 240, 170), 110)
        self.halo_pantalla = circulo_luz(10, (120, 190, 255), 60)
        self.halo_luna = circulo_luz(26, (170, 180, 220), 70)
        self.arcoiris = self._hacer_arcoiris()
        self.nubes = self._hacer_nubes()
        self._sprites()
        self.detalles = self._detalles_tierra()
        self.tiles = self._tiles()
        self.hierba = {}
        self.cementerio_px = None
        self.carteles = {}
        self.fuegos = []      # [x, y, vx, vy, color, vida]
        self.t_prev = 0.0

    # ================================================================ sprites

    def _sprites(self):
        S = {}
        for nombre, defi, claves in (("conejo", A.CONEJO, ("sentado", "salto", "come")),
                                     ("paloma", A.PALOMA, ("quieta", "come", "vuela")),
                                     ("gaviota", A.GAVIOTA, ("arriba", "abajo")),
                                     ("abeja", A.ABEJA, ("a", "b")),
                                     ("mariposa", A.MARIPOSA, ("a", "b")),
                                     ("lagartija", A.LAGARTIJA, ("a",)),
                                     ("caracol", A.CARACOL, ("a",)),
                                     ("erizo", A.ERIZO, ("a",)),
                                     ("buho", A.BUHO, ("abierto", "cerrado")),
                                     ("murcielago", A.MURCIELAGO, ("a", "b")),
                                     ("golondrina", A.GOLONDRINA, ("a", "b")),
                                     ("avion", A.AVION, ("a",)),
                                     ("arana", A.ARANA, ("a", "b")),
                                     ("grillo", A.GRILLO, ("a",)),
                                     ("oruga", A.ORUGA, ("a", "b")),
                                     ("mosca", A.MOSCA, ("a", "b")),
                                     ("lombriz", A.LOMBRIZ, ("a", "b")),
                                     ("escarabajo", A.ESCARABAJO, ("a",)),
                                     ("cochinilla", A.COCHINILLA, ("a",)),
                                     ("pajaro", A.PAJARO, ("a",))):
            for c in claves:
                s = _doble(A.sprite(defi, c)) if nombre in DOBLES else A.sprite(defi, c)
                S[(nombre, c, 1)] = s
                S[(nombre, c, -1)] = espejo(s)
        for color_gato in ("naranja", "negro_brillante", "plata", "blanco_brillante"):
            base = {"naranja": (220, 130, 50), "negro_brillante": (60, 58, 62),
                    "plata": (150, 150, 160), "blanco_brillante": (230, 228, 220)}[color_gato]
            defi = A.recolor(A.GATO, {"c": base, "d": oscuro(base, 0.7)})
            for c in ("anda", "anda2", "sentado"):
                s = _doble(A.sprite(defi, c))
                S[("gato_" + color_gato, c, 1)] = s
                S[("gato_" + color_gato, c, -1)] = espejo(s)
        for k in A.COMIDA:
            s = A.comida(k)
            if k in ("galleta", "bocadillo", "higo", "almendra", "azucar", "roja"):
                s = _doble(s)
            S[("comida", k)] = s
            S[("muerta", k)] = tenir(s, (90, 90, 90), 0.5)
        for k in ("grillo", "oruga", "mosca", "lombriz", "escarabajo"):
            s = S[(k, "a", 1)]
            S[("muerta", k)] = pygame.transform.flip(tenir(s, (80, 80, 80), 0.4), False, True)
            S[("muerta", k)].set_colorkey(CLAVE)
        S["calabaza"] = _doble(A.simple(A.CALABAZA))
        S["tarta"] = _doble(A.simple(A.TARTA))
        S["corazon"] = A.simple(A.CORAZON)
        S["trono"] = _doble(A.simple(A.TRONO))
        S["cruz"] = _doble(A.simple(A.CRUZ_MAYO))
        S["regalos"] = [_doble(A.regalo(c, l)) for c, l in (((200, 40, 50), (250, 220, 70)),
                                                     ((50, 110, 210), (240, 240, 240)),
                                                     ((70, 170, 80), (230, 60, 60)),
                                                     ((200, 80, 200), (250, 230, 120)))]
        S["globos"] = [A.globo(c) for c in COLORES_FIESTA]
        self.S = S
        self.hormigas_rojas = HA.fotogramas((190, 40, 30))

    def _hacer_nubes(self):
        out = []
        for k in range(4):
            r = random.Random(k)
            w, h = r.randint(36, 60), r.randint(12, 18)
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            for _ in range(9):
                cx, cy = r.randint(6, w - 6), r.randint(h // 2, h - 4)
                rad = r.randint(4, 8)
                pygame.draw.circle(s, (225, 230, 240, 255), (cx, cy), rad)
            for _ in range(5):
                cx, cy = r.randint(8, w - 8), r.randint(h // 2 - 2, h - 6)
                pygame.draw.circle(s, (255, 255, 255, 255), (cx, cy - 2), r.randint(3, 6))
            out.append(s)
        return out

    def hormiga(self, color):
        f = self.cache_hormigas.get(color)
        if f is None:
            f = self.cache_hormigas[color] = HA.fotogramas(color)
        return f

    # ================================================================ coordenadas

    def px(self, cx):
        return int(cx * CW)

    def py_suelo(self, gy):
        """Píxel del suelo bajo una celda de la rejilla (las patas apoyan aquí)."""
        return (self.m.oy + gy + 1) * CH

    # ================================================================ cielo

    def _colores_cielo(self):
        m = self.m
        a, p = m.sol_hoy
        mins = m.ahora.hour * 60 + m.ahora.minute
        noche = ((10, 12, 38), (28, 38, 84))
        dia = ((46, 124, 214), (150, 206, 242))
        alba = ((80, 86, 160), (246, 168, 112))
        tarde = ((70, 60, 130), (248, 132, 82))
        # amanecer y atardecer, de 40 minutos como mucho: menos si el día o la noche son más cortos,
        # y ninguno en la noche polar (a == p) ni con el sol de medianoche (0, 1440)
        T_ = min(40.0, (p - a) / 2, (1440 - p + a) / 2)
        if abs(mins - a) < T_:
            t = (mins - a + T_) / (2 * T_)
            arriba = mezclar(noche[0], alba[0], min(1, t * 2)) if t < 0.5 else mezclar(alba[0], dia[0], (t - 0.5) * 2)
            abajo = mezclar(noche[1], alba[1], min(1, t * 2)) if t < 0.5 else mezclar(alba[1], dia[1], (t - 0.5) * 2)
        elif abs(mins - p) < T_:
            t = (mins - p + T_) / (2 * T_)
            arriba = mezclar(dia[0], tarde[0], min(1, t * 2)) if t < 0.5 else mezclar(tarde[0], noche[0], (t - 0.5) * 2)
            abajo = mezclar(dia[1], tarde[1], min(1, t * 2)) if t < 0.5 else mezclar(tarde[1], noche[1], (t - 0.5) * 2)
        elif m.de_noche:
            arriba, abajo = noche
        else:
            arriba, abajo = dia
        td = m.tiempo_hoy
        if m.lluvia > 0 or td.nubes > 0.75:
            gris = ((80, 88, 104), (140, 146, 158)) if not m.de_noche else ((22, 24, 32), (44, 48, 60))
            f = 0.75 if m.lluvia > 0 else (td.nubes - 0.75) * 2
            arriba, abajo = mezclar(arriba, gris[0], f), mezclar(abajo, gris[1], f)
        if td.calima and not m.de_noche:
            arriba, abajo = mezclar(arriba, (196, 150, 96), 0.6), mezclar(abajo, (232, 196, 140), 0.7)
        return arriba, abajo

    def _cielo(self):
        arriba, abajo = self._colores_cielo()
        clave = (arriba, abajo)
        if clave != self.clave_cielo:
            self.clave_cielo = clave
            s = pygame.Surface((self.W, self.G)).convert()
            for y in range(self.G):
                pygame.draw.line(s, mezclar(arriba, abajo, y / max(1, self.G - 1)), (0, y), (self.W, y))
            self.capa_cielo = s
        self.dst.blit(self.capa_cielo, (0, 0))
        return arriba

    def _estrellas(self, t):
        m = self.m
        if not m.de_noche or m.tiempo_hoy.nubes > 0.8 or m.lluvia > 0:
            return
        for x, y, f in self.estrellas:
            b = math.sin(t * 1.3 + f)
            if b > -0.4:
                c = 255 if b > 0.6 else 190 if b > 0 else 130
                self.dst.fill((c, c, min(255, c + 20)), (x, y, 1, 1))
                if b > 0.9:
                    self.dst.fill((c, c, c), (x - 1, y, 3, 1))
                    self.dst.fill((c, c, c), (x, y - 1, 1, 3))

    def _hacer_arcoiris(self):
        r = 150
        s = pygame.Surface((r * 2 + 4, r + 4)).convert()
        s.fill((0, 0, 0))
        cols = [(105, 28, 28), (105, 62, 14), (105, 98, 20), (28, 90, 28), (20, 56, 105), (50, 28, 92)]
        for k, c in enumerate(cols):
            pygame.draw.circle(s, c, (r + 2, r + 2), r - k * 4, 4)
        return s

    def _arcoiris(self):
        """Tras la lluvia, si sale el sol (no todos los días)."""
        m = self.m
        if m.de_noche or m.lluvia > 0 or not m.llovio or m.tiempo_hoy.nubes > 0.85:
            return
        if random.Random("arcoiris-%s" % m.ahora.date()).random() > 0.6:
            return
        self.dst.blit(self.arcoiris, (self.W // 2 - 30, self.G - 150), special_flags=pygame.BLEND_ADD)

    def _fugaz(self, t):
        """De vez en cuando, una estrella fugaz."""
        m = self.m
        if not m.de_noche or m.lluvia > 0 or m.tiempo_hoy.nubes > 0.7:
            self._estrella_fugaz = None
            return
        f = getattr(self, "_estrella_fugaz", None)
        if f is None and self.rng.random() < 0.004:
            f = self._estrella_fugaz = [self.rng.uniform(150, self.W - 120), self.rng.uniform(10, 60), t]
        if f:
            k = (t - f[2]) * 120
            x, y = f[0] - k, f[1] + k * 0.45
            for i in range(10):
                c = 255 - i * 22
                self.dst.fill((c, c, max(0, c - 20)), (int(x + i * 2), int(y - i * 0.9), 2, 1))
            if k > 140:
                self._estrella_fugaz = None

    def _astro(self):
        m = self.m
        if m.lluvia > 0 or m.tiempo_hoy.nubes > 0.9:
            return
        a, p = m.sol_hoy
        mins = m.ahora.hour * 60 + m.ahora.minute
        if not m.de_noche:
            fr = (mins - a) / max(1, p - a)
        else:
            fr = ((mins - p) % 1440) / max(1, 1440 - p + a)
        fr = max(0.0, min(1.0, fr))
        x = int(30 + fr * (self.W - 60))
        y = int(24 + (1 - math.sin(math.pi * fr)) * (self.G - 70))
        if not m.de_noche:
            col = (255, 200, 90) if m.tiempo_hoy.calima else (255, 236, 120)
            self.dst.blit(self.halo_sol, (x - 22, y - 22), special_flags=pygame.BLEND_ADD)
            pygame.draw.circle(self.dst, col, (x, y), 8)
            pygame.draw.circle(self.dst, (255, 250, 200), (x - 2, y - 2), 3)
        else:
            fase = T.fase_lunar(m.ahora.date())
            ilum = 1 - abs(fase - 0.5) * 2          # 0 nueva, 1 llena
            if ilum < 0.08:
                return                               # luna nueva: no se ve
            cielo_aqui = mezclar(self.clave_cielo[0], self.clave_cielo[1], y / max(1, self.G))
            pygame.draw.circle(self.dst, (235, 235, 215), (x, y), 7)
            if ilum < 0.97:
                desp = int((1 - ilum) * 12) * (1 if fase < 0.5 else -1)
                pygame.draw.circle(self.dst, cielo_aqui, (x - desp, y), 7)
            else:
                self.dst.fill((200, 200, 185), (x + 1, y + 2, 2, 2))
                self.dst.fill((210, 210, 195), (x - 3, y - 2, 2, 2))
            # el halo, al final: suma la misma luz a la luna, a su sombra y al cielo
            if ilum > 0.35:
                self.dst.blit(self.halo_luna, (x - 26, y - 26), special_flags=pygame.BLEND_ADD)

    def _nubes(self):
        m = self.m
        lluvia = m.lluvia > 0
        for i, n in enumerate(m.superficie.nubes):
            s = self.nubes[i % len(self.nubes)]
            x = self.px(n.x)
            y = int(n.y * CH)
            if lluvia or m.de_noche:
                if not hasattr(self, "_nube_gris"):
                    self._nube_gris = [_oscurecer_alpha(c, 0.55) for c in self.nubes]
                    self._nube_noche = [_oscurecer_alpha(c, 0.35) for c in self.nubes]
                s = (self._nube_gris if lluvia and not m.de_noche else self._nube_noche)[i % len(self.nubes)]
            self.dst.blit(s, (x, y))

    # ================================================================ montes

    def _montes(self):
        m = self.m
        clave = (m.de_noche, m.tiempo_hoy.calima, m.nevado)
        if clave != self.clave_montes:
            self.clave_montes = clave
            s = superficie(self.W, self.G)
            alturas = m.superficie.montes
            if m.de_noche:
                lejos, cerca, cat = (34, 40, 66), (24, 30, 46), (40, 44, 62)
            else:
                lejos, cerca, cat = (116, 150, 176), (88, 126, 104), (150, 128, 100)
            if m.tiempo_hoy.calima and not m.de_noche:
                lejos, cerca = (190, 150, 110), (160, 125, 90)
            # montes del fondo (más altos y azulados)
            pts = [(0, self.G)]
            for x in range(0, self.W + 4, 4):
                h = alturas[min(len(alturas) - 1, x // CW)]
                pts.append((x, self.G - 10 - int(h * 9)))
            pts.append((self.W, self.G))
            if m.superficie.montes_lejos:
                pygame.draw.polygon(s, lejos, pts)
                if m.nevado:   # nieve sólo en las cumbres (la parte más alta de los montes)
                    nieve = (150, 160, 190) if m.de_noche else (240, 244, 250)
                    cima = min(y for _, y in pts[1:-1])
                    corte = cima + (self.G - cima) * 0.35
                    for x, y in pts[1:-1]:
                        if y < corte:
                            pygame.draw.line(s, nieve, (x, y), (x, int(min(corte, y + 10))), 4)
            # colinas más cerca
            r = random.Random(m.semilla)
            pts = [(0, self.G)]
            fase = r.uniform(0, 6)
            for x in range(0, self.W + 4, 4):
                h = 10 + 6 * math.sin(x / 70 + fase) + 4 * math.sin(x / 23 + fase * 2)
                pts.append((x, self.G - int(h)))
            pts.append((self.W, self.G))
            pygame.draw.polygon(s, cerca, pts)
            # construcciones al fondo, en la ladera
            for k, (pieza, x) in enumerate(m.superficie.piezas_fondo):
                if pieza not in PA.FONDO:
                    self._aviso("paisaje: no existe la pieza de fondo «%s»" % pieza)
                    continue
                ctx = PA.Contexto(0, m.semilla, m.de_noche, k)
                PA.FONDO[pieza][0](s, self.px(x), self._base_fondo(x), ctx, cat, (250, 210, 110))
            self.capa_montes = s
        self.dst.blit(self.capa_montes, (0, 0))

    def _base_fondo(self, x):
        """Altura (en píxeles) de la ladera de los montes en la columna x."""
        alturas = self.m.superficie.montes
        if not self.m.superficie.montes_lejos:
            return self.G - 8
        return self.G - 10 - int(alturas[min(len(alturas) - 1, max(0, x))] * 9) + 6

    def _aviso(self, texto):
        if texto not in self.m.avisos:
            self.m.avisos.append(texto)

    # ================================================================ superficie

    def _clave_superficie(self):
        m = self.m
        return (m.ahora.date(), m.de_noche, frozenset(m.decoraciones), tuple(m.cumples), tuple(m.idos),
                tuple(m.salidas_x), m.plan.total_cavado() // 600, m.llovio, m.llovio_semana, m.nevado)

    def _superficie(self):
        clave = self._clave_superficie()
        if clave != self.clave_sup:
            self.clave_sup = clave
            s = superficie(self.W, self.G + 4)
            self._pintar_superficie(s)
            m = self.m
            if m.nevado:
                _nevar(s, self.G)
            # los letreros van aparte y se pegan encima de la capa (y de la nieve) en cada fotograma:
            # sus bordes suavizados, mezclados con el color clave, saldrían con un halo magenta
            self.letreros_sup = self._textos_superficie
            if m.de_noche:
                s = multiplicar(s, (110, 120, 170))
                self.letreros_sup = [(multiplicar(img, (110, 120, 170)), pos) for img, pos in self.letreros_sup]
                # de noche se encienden las ventanas y las farolas
                dia = m.dia_natural
                for k, (pieza, x) in enumerate(m.superficie.piezas_suelo):
                    luces = PA.SUELO.get(pieza, (None, None))[1]
                    if luces:
                        luces(s, self.px(x), self.G, PA.Contexto(dia, m.semilla, True, k))
            self.capa_sup = s
        self.dst.blit(self.capa_sup, (0, 0))
        for img, pos in self.letreros_sup:
            self.dst.blit(img, pos)

    def _pintar_superficie(self, s):
        m = self.m
        self._textos_superficie = []
        sup = m.superficie
        G = self.G
        dia = m.dia_natural   # flores, hojas y frutos (en el hemisferio sur, medio año desplazado)
        # charcos
        if m.llovio:
            for cx in sup.charcos:
                pygame.draw.ellipse(s, (90, 130, 190), (self.px(cx), G - 2, 18, 4))
        for k, (pieza, x) in enumerate(sup.piezas_suelo):
            if pieza not in PA.SUELO:
                self._aviso("paisaje: no existe la pieza «%s»" % pieza)
                continue
            PA.SUELO[pieza][0](s, self.px(x), G, PA.Contexto(dia, m.semilla, m.de_noche, k))
        self._flores(s, G, dia)
        self._piedras(s, G)
        self._cementerio(s, G)
        for n, sx in enumerate(m.salidas_x):
            self._monticulo(s, self.px(sx) + 2, G, grande=n == 0)
        deco = m.decoraciones
        sx0 = self.px(m.salidas_x[0])
        if "navidad" in deco or "reyes" in deco:
            self._pino(s, sx0 + 50, G)
            if "reyes" in deco:
                for k in range(3):
                    s.blit(self.S["regalos"][k], (sx0 + 66 + k * 14, G - 12))
        if "halloween" in deco:
            for x in self._calabazas():
                s.blit(self.S["calabaza"], (x, G - 14))
        if "cruces" in deco:
            s.blit(self.S["cruz"], (sx0 + 52, G - 18))
        if "libro" in deco:
            for k, col in enumerate(((180, 50, 50), (50, 90, 170), (60, 140, 70))):
                pygame.draw.rect(s, col, (sx0 + 52 + k, G - 3 - k * 3, 12, 3))
        if m.cumples:
            x = self.px(m.ox + m.x_cumple)
            s.blit(self.S["tarta"], (x, G - 16))
            for k in range(min(4, 1 + len(m.cumples))):
                s.blit(self.S["regalos"][k], (x + 28 + k * 14, G - 12))

    def _monticulo(self, s, cx, G, grande=True):
        alto = self.m.superficie._alto_monticulo() if grande else 1
        w = 22 + alto * 10
        h = 5 + alto * 4
        r = random.Random(cx)
        pygame.draw.ellipse(s, (120, 84, 52), (cx - w // 2, G - h, w, h * 2))
        pygame.draw.ellipse(s, (146, 104, 66), (cx - w // 2 + 3, G - h + 1, w - 10, h))
        for _ in range(w * 2):
            x = r.randint(cx - w // 2 + 2, cx + w // 2 - 2)
            y = r.randint(G - h + 2, G - 1)
            if ((x - cx) / (w / 2)) ** 2 + ((y - G) / h) ** 2 < 0.9:
                s.set_at((x, y), r.choice([(176, 136, 90), (96, 66, 40), (160, 120, 80)]))
        pygame.draw.ellipse(s, (20, 12, 8), (cx - 4, G - 4, 9, 6))

    def _piedras(self, s, G):
        for px_, _ in self.m.superficie.piedras:
            x = self.px(px_)
            pygame.draw.ellipse(s, (120, 116, 110), (x, G - 3, 6, 4))
            s.set_at((x + 1, G - 3), (170, 166, 160))

    def _flores(self, s, G, dia):
        m = self.m
        for x, a, b in m.superficie.flores:
            px_ = self.px(x)
            h = 3 + int(b * 4)
            col = None
            if 60 <= dia <= 151 and a < 0.35:
                col = (220, 40, 40)          # amapolas
            elif 15 <= dia <= 90 and a > 0.75:
                col = (240, 210, 40)         # jaramagos
            elif 32 <= dia <= 120 and 0.55 < a < 0.65:
                col = (250, 250, 250)        # margaritas
            elif 182 <= dia <= 243 and a < 0.12:
                col = (255, 255, 240)        # biznagas
            elif 280 <= dia <= 350 and a < 0.2 and m.llovio_semana:
                pygame.draw.rect(s, (230, 220, 200), (px_ + 1, G - 4, 1, 4))
                pygame.draw.ellipse(s, (200, 60, 50) if b < 0.4 else (170, 120, 70), (px_ - 1, G - 6, 5, 3))
                continue
            if col:
                pygame.draw.line(s, (70, 130, 50), (px_, G), (px_, G - h))
                pygame.draw.circle(s, col, (px_, G - h), 1)
                if col == (250, 250, 250):
                    s.set_at((px_, G - h), (240, 200, 40))

    def _calabazas(self):
        """Dónde van las calabazas de Halloween: repartidas, sin tapar las lápidas."""
        out = []
        for k in range(4):
            x = 30 + k * self.W // 5
            if self.cementerio_px and x + 16 > self.cementerio_px[0] and x < self.cementerio_px[1]:
                x = self.cementerio_px[0] - 18 if self.cementerio_px[0] >= 18 else self.cementerio_px[1] + 2
            out.append(x)
        return out

    def _cementerio(self, s, G):
        m = self.m
        self.cementerio_px = None   # de dónde a dónde va (en píxeles), para no taparlo
        if not m.idos:
            return
        sup = m.superficie
        # que no quede encima de una salida (los montículos de tierra la taparían)
        def choca(x0, total):
            return any(x0 - 8 <= s <= x0 + total + 8 for s in m.salidas_x_grid)
        # cada lápida, tan ancha como su nombre (con margen); si no hay sitio, con letra más pequeña
        for tam in (7, 6, 5):
            textos = [self.letras.texto(n, (40, 40, 48), tam, sombra=False) for n in m.idos]
            anchos = [max(5, math.ceil((t.get_width() + 8) / CW)) for t in textos]
            total = sum(anchos) + len(anchos) + 3
            x = min(sup.cementerio_x, m.plan_ancho - total - 2)
            if choca(x, total):
                libres = [x0 for x0 in range(2, m.plan_ancho - total - 2) if not choca(x0, total)]
                if libres:
                    x = min(libres, key=lambda x0: abs(x0 - x))
            if not choca(x, total):
                break
        x0 = self.px(x)
        # valla
        ancho_px = self.px(total)
        self.cementerio_px = (x0, x0 + ancho_px)
        pygame.draw.line(s, (120, 90, 60), (x0, G - 5), (x0 + ancho_px, G - 5))
        for k in range(0, ancho_px + 1, 6):
            pygame.draw.line(s, (120, 90, 60), (x0 + k, G - 8), (x0 + k, G))
        rip = self.letras.texto("R.I.P.", (200, 200, 205), 8)
        self._textos_superficie.append((rip, (x0 + ancho_px // 2 - rip.get_width() // 2, G - 34)))
        cx = x0 + 8
        for t, w in zip(textos, anchos):
            ancho = self.px(w) - 2
            lap = pygame.Rect(cx, G - 22, ancho, 22)
            pygame.draw.rect(s, (110, 110, 118), lap, border_top_left_radius=6, border_top_right_radius=6)
            pygame.draw.rect(s, (150, 150, 158), lap.inflate(-4, -4), border_top_left_radius=4,
                             border_top_right_radius=4)
            s.blit(t, (cx + ancho // 2 - t.get_width() // 2, G - 15 + (7 - tam) // 2))
            pygame.draw.line(s, (90, 90, 96), (cx + ancho // 2, G - 20), (cx + ancho // 2, G - 17))
            pygame.draw.line(s, (90, 90, 96), (cx + ancho // 2 - 2, G - 19), (cx + ancho // 2 + 2, G - 19))
            if "difuntos" in m.decoraciones:
                pygame.draw.circle(s, (220, 40, 40), (cx + 3, G - 2), 2)
                pygame.draw.circle(s, (250, 200, 60), (cx + ancho - 4, G - 2), 2)
            cx += self.px(w + 1)

    def _pino(self, s, x, G):
        pygame.draw.rect(s, (100, 66, 40), (x + 9, G - 6, 4, 6))
        for k, (w, y) in enumerate(((22, 6), (18, 13), (13, 20), (8, 26))):
            pygame.draw.polygon(s, (30, 110, 50), [(x + 11 - w // 2, G - y), (x + 11 + w // 2, G - y),
                                                    (x + 11, G - y - 9)])
        pygame.draw.circle(s, (255, 220, 60), (x + 11, G - 35), 2)

    # ---------------------------------------------------------------- hierba

    def _hierba(self, t):
        m = self.m
        est = m.estacion
        fase = int(t * 2) % 3
        clave = (est, fase, m.de_noche, m.nevado)
        s = self.hierba.get(clave)
        if s is None:
            s = superficie(self.W, 10)
            r = random.Random("hierba")
            base = {"invierno": (60, 130, 60), "primavera": (80, 170, 60), "verano": (170, 160, 80),
                    "otoño": (110, 140, 60)}[est]
            for x in range(0, self.W, 2):
                h = r.randint(2, 7)
                dx = (fase - 1) * (1 if r.random() < 0.7 else 0)
                c = mezclar(base, (40, 70, 30), r.random() * 0.5)
                if est == "verano" and r.random() < 0.4:
                    c = (190, 170, 90)
                pygame.draw.line(s, c, (x, 9), (x + dx, 9 - h))
            pygame.draw.line(s, (70, 50, 32), (0, 9), (self.W, 9))
            if m.nevado:   # una capa de nieve con algún bulto
                for x in range(0, self.W, 3):
                    h = 3 + (r.random() < 0.3)
                    s.fill((236, 240, 248), (x, 9 - h, 3, h + 1))
            if m.de_noche:
                s = multiplicar(s, (110, 120, 170))
            self.hierba[clave] = s
        self.dst.blit(s, (0, self.G - 9))

    # ================================================================ tierra

    def _tiles(self):
        out = {}
        for tipo, cols in TIERRA.items():
            vs = []
            for v in range(6):
                r = random.Random(tipo * 10 + v)
                t = pygame.Surface((CW, CH)).convert()
                t.fill(cols[0])
                for _ in range(10):
                    t.set_at((r.randrange(CW), r.randrange(CH)), r.choice(cols[1:]))
                if tipo == ARENA and v == 0:
                    t.set_at((1, 3), (220, 200, 160))
                vs.append(t)
            out[tipo] = vs
        tun = pygame.Surface((CW, CH)).convert()
        tun.fill(TUNEL)
        out["tunel"] = tun
        return out

    def _detalles_tierra(self):
        """Raíces, piedras, gemas y fósiles (en celdas de la rejilla)."""
        m = self.m
        r = random.Random("pix-detalles-%s" % m.semilla)
        piedras = [(r.randrange(ANCHO), r.randrange(PROF - 3), r.randint(1, 3)) for _ in range(ANCHO * PROF // 30)]
        gemas = [(r.randrange(ANCHO), r.randrange(20, PROF - 2),
                  r.choice([(230, 50, 60), (60, 210, 120), (70, 140, 250), (220, 90, 230), (60, 220, 220)]))
                 for _ in range(16)]
        raices = []
        for _ in range(ANCHO // 6):
            x = r.randrange(2, ANCHO - 2) * CW + r.randrange(CW)
            largo = r.randint(10, 40)
            raices.append((x, largo, r.uniform(-0.5, 0.5)))
        fosiles = [(r.randrange(5, ANCHO - 10), r.randrange(12, PROF - 4), k) for k in range(5)]
        return {"piedras": piedras, "gemas": gemas, "raices": raices, "fosiles": fosiles}

    def _actualizar_tierra(self):
        """Repinta sólo lo necesario: todo al empezar o si cambian las salas, las salas
        al cambiar de día (muebles nuevos, hallazgos) y la zona excavada si avanza una obra."""
        m = self.m
        cav = m.plan._cavado
        salas = tuple(s.clave for s in m.salas)
        if not self.tierra_lista or salas != self.clave_salas:
            self.clave_salas = salas
            self.tierra_lista = True
            self.dia_pintado = int(m.dia)
            self.cavado_pintado = bytearray(cav)
            self._pintar_tierra_entera()
            return
        if cav != self.cavado_pintado:
            viejo = self.cavado_pintado
            cambios = [i for i, (a, b) in enumerate(zip(cav, viejo)) if a != b]
            self.cavado_pintado = bytearray(cav)
            xs, ys = [], []
            for i in cambios:
                gy, gx = divmod(i, ANCHO)
                xs.append(gx)
                ys.append(gy)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        self._pintar_celda(gx + dx, gy + dy)
            if cambios:
                zona = pygame.Rect(self.px(m.ox + min(xs) - 2), (min(ys) - 2) * CH,
                                   (max(xs) - min(xs) + 5) * CW, (max(ys) - min(ys) + 5) * CH)
                self._pintar_detalles(zona)
                self._pintar_salas([sl for sl in m.salas if self._rect_sala(sl).inflate(8, 16).colliderect(zona)])
        if int(m.dia) != self.dia_pintado:
            self.dia_pintado = int(m.dia)
            self._pintar_salas()

    def _pintar_tierra_entera(self):
        s = self.capa_tierra
        for gy in range(PROF):
            for gx in range(ANCHO):
                self._pintar_celda(gx, gy)
        self._pintar_detalles()
        self._pintar_salas()

    def _pintar_celda(self, gx, gy):
        if not (0 <= gx < ANCHO and 0 <= gy < PROF):
            return
        plan = self.m.plan
        s = self.capa_tierra
        x, y = self.px(self.m.ox + gx), gy * CH
        if plan.cavado(gx, gy):
            s.blit(self.tiles["tunel"], (x, y))
            return
        tipo = plan.tipo(gx, gy)
        s.blit(self.tiles[tipo][_hash(gx, gy) % 6], (x, y))
        # borde oscuro hacia los túneles (da relieve)
        borde = oscuro(TIERRA[tipo][0], 0.55)
        luz = claro(TIERRA[tipo][0], 0.15)
        if gy + 1 < PROF and plan.cavado(gx, gy + 1):
            s.fill(borde, (x, y + CH - 2, CW, 2))
        if gy > 0 and plan.cavado(gx, gy - 1):
            s.fill(luz, (x, y, CW, 1))
        if plan.cavado(gx - 1, gy) and gx > 0:
            s.fill(borde, (x, y, 1, CH))
        if plan.cavado(gx + 1, gy) and gx + 1 < ANCHO:
            s.fill(borde, (x + CW - 1, y, 1, CH))

    def _pintar_detalles(self, zona=None):
        s = self.capa_tierra
        plan = self.m.plan
        ox = self.px(self.m.ox)
        d = self.detalles
        def dentro(px_, py_):
            return zona is None or zona.collidepoint(px_, py_)
        for x, largo, inc in d["raices"]:
            if not dentro(ox + x, 5):
                continue
            for k in range(largo):
                yy = k
                xx = ox + x + int(inc * k + math.sin(k / 3) * 1.5)
                if not plan.cavado((xx - ox) // CW, yy // CH):
                    s.set_at((xx, yy), (70, 46, 28) if k % 5 else (90, 62, 40))
        for gx, gy, tam in d["piedras"]:
            if dentro(ox + gx * CW, gy * CH) and not plan.cavado(gx, gy):
                x, y = ox + gx * CW, gy * CH + 3
                pygame.draw.ellipse(s, (120, 114, 108), (x, y, tam + 1, tam))
                s.set_at((x, y), (170, 165, 160))
        for gx, gy, col in d["gemas"]:
            if dentro(ox + gx * CW, gy * CH) and not plan.cavado(gx, gy) and plan.tipo(gx, gy) in (ARCILLA, ROCA):
                x, y = ox + gx * CW + 1, gy * CH + 3
                pygame.draw.polygon(s, col, [(x + 1, y), (x + 3, y + 2), (x + 1, y + 4), (x - 1, y + 2)])
                s.set_at((x + 1, y + 1), (255, 255, 255))
        for gx, gy, k in d["fosiles"]:
            if not dentro(ox + gx * CW, gy * CH) or any(plan.cavado(gx + i, gy) for i in range(5)):
                continue
            x, y = ox + gx * CW, gy * CH + 2
            hueso = (225, 215, 190)
            if k == 0:  # pez fósil (homenaje a la pecera)
                pygame.draw.line(s, hueso, (x, y + 2), (x + 14, y + 2))
                for i in range(2, 12, 3):
                    pygame.draw.line(s, hueso, (x + i, y), (x + i, y + 4))
                pygame.draw.polygon(s, hueso, [(x + 14, y), (x + 18, y + 2), (x + 14, y + 4)], 1)
                pygame.draw.line(s, hueso, (x, y + 2), (x - 3, y))
                pygame.draw.line(s, hueso, (x, y + 2), (x - 3, y + 4))
            elif k == 1:  # amonites
                for i in range(4, 0, -1):
                    pygame.draw.circle(s, hueso if i % 2 else (160, 140, 110), (x + 4, y + 3), i)
            elif k == 2:  # hueso
                pygame.draw.line(s, hueso, (x, y + 2), (x + 12, y + 2), 2)
                for e in (x, x + 12):
                    pygame.draw.circle(s, hueso, (e, y + 1), 1)
                    pygame.draw.circle(s, hueso, (e, y + 3), 1)
            elif k == 3:  # botella
                pygame.draw.rect(s, (70, 140, 90), (x, y, 8, 4))
                pygame.draw.rect(s, (70, 140, 90), (x + 8, y + 1, 3, 2))
                s.set_at((x + 1, y + 1), (150, 220, 170))
            else:  # tubería vieja
                pygame.draw.rect(s, (110, 110, 120), (x, y + 1, 16, 3))
                pygame.draw.rect(s, (110, 110, 120), (x + 14, y + 1, 3, 8))

    # ---------------------------------------------------------------- salas

    def _rect_sala(self, sala):
        x = self.px(self.m.ox + sala.x0)
        y = sala.y0 * CH
        return pygame.Rect(x, y, sala.ancho * CW, sala.alto * CH)

    def _pintar_salas(self, salas=None):
        s = self.capa_tierra
        m = self.m
        for sala in (m.salas if salas is None else salas):
            r = self._rect_sala(sala)
            # pared interior (más clara que los túneles) sólo donde está excavado
            estilo = self.m.tipos.get(sala.tipo, {})
            pared = estilo.get("paredes", "madera")
            pared = PAREDES.get(pared) or (rgb(pared) if str(pared).startswith("#") else PARED_SALA)
            for gy in range(sala.y0, sala.piso + 1):
                for gx in range(sala.x0, sala.x0 + sala.ancho):
                    if m.plan.cavado(gx, gy):
                        s.fill(pared, (self.px(m.ox + gx), gy * CH, CW, CH))
            # papel pintado: rayas suaves
            for x in range(r.x + 2, r.right - 2, 6):
                pygame.draw.line(s, oscuro(pared, 0.88), (x, r.y + 6), (x, r.bottom - 4))
            # suelo de madera
            suelo_y = (sala.piso + 1) * CH
            if estilo.get("suelo") == "baldosa":
                for x in range(r.x, r.right, 6):
                    pygame.draw.rect(s, (200, 210, 215), (x, suelo_y, 5, 3))
            elif estilo.get("suelo") == "tierra":
                pygame.draw.rect(s, (110, 78, 50), (r.x + 2, suelo_y, r.width - 4, 3))
            else:
                pygame.draw.rect(s, MADERA, (r.x + 2, suelo_y, r.width - 4, 3))
                for x in range(r.x + 4, r.right - 4, 9):
                    pygame.draw.line(s, MADERA_OSC, (x, suelo_y), (x, suelo_y + 2))
            # zócalo
            pygame.draw.line(s, oscuro(pared, 0.7), (r.x + 2, suelo_y - 1), (r.right - 3, suelo_y - 1))
            # muebles (estáticos)
            self._muebles(s, sala, r, suelo_y)
            # cartel con el nombre
            t, cartel = self._cartel(sala, r)
            pygame.draw.rect(s, (60, 38, 22), cartel)
            pygame.draw.rect(s, (120, 80, 48), cartel, 1)
            s.blit(t, (cartel.x + 4, cartel.y + (cartel.height - t.get_height()) // 2))
        # hallazgos
        for x, y, nombre, icono, col, dia in m.plan.objetos:
            if dia <= m.dia_obras:
                self._objeto(s, self.px(m.ox + x), y * CH + 2, nombre, rgb(col))

    def _cartel(self, sala, r):
        """El cartel con el nombre, centrado arriba en la sala r: (texto, rectángulo). En las salas
        estrechas, con letra más pequeña o recortado, para que no se salga de la sala."""
        clave = (sala.nombre, sala.color, sala.principal, r.width)
        t = self.carteles.get(clave)   # se pide en cada fotograma (para las lámparas y los nombres)
        if t is None:
            col = rgb(sala.color) if sala.color else (230, 230, 230)
            col = col if sala.principal else (230, 225, 215)
            cabe = r.width - 12   # el texto, con 4 píxeles a cada lado dentro del cartel y 2 fuera
            for tam in (8, 7, 6):
                t = self.letras.texto(sala.nombre, col, tam, sombra=False)
                if t.get_width() <= cabe:
                    break
            else:   # ni con la letra más pequeña: recortado, con la de 7
                t = self.letras.texto(self.letras.recortar(sala.nombre, cabe, 7), col, 7, sombra=False)
            self.carteles[clave] = t
        w = t.get_width() + 8
        return t, pygame.Rect(r.centerx - w // 2, r.y + 1, w, 11)

    def _objeto(self, s, x, y, nombre, col):
        if "peseta" in nombre or "moneda" in nombre:
            pygame.draw.circle(s, col, (x + 3, y + 3), 3)
            pygame.draw.circle(s, oscuro(col, 0.7), (x + 3, y + 3), 3, 1)
        elif "Lego" in nombre:
            pygame.draw.rect(s, (220, 40, 40), (x, y + 2, 8, 4))
            for i in (1, 5):
                pygame.draw.rect(s, (240, 80, 80), (x + i, y, 2, 2))
        elif "Raspberry" in nombre:
            pygame.draw.rect(s, (40, 150, 60), (x, y, 10, 6))
            pygame.draw.rect(s, (200, 200, 200), (x + 2, y + 1, 3, 2))
            pygame.draw.rect(s, (30, 30, 30), (x + 6, y + 2, 2, 2))
        elif "dado" in nombre:
            pygame.draw.rect(s, (245, 245, 240), (x, y, 6, 6))
            for p in ((1, 1), (4, 4), (2, 3)):
                s.set_at((x + p[0], y + p[1]), (20, 20, 20))
        elif "llave" in nombre:
            pygame.draw.circle(s, col, (x + 2, y + 3), 2, 1)
            pygame.draw.line(s, col, (x + 4, y + 3), (x + 10, y + 3))
            pygame.draw.line(s, col, (x + 8, y + 3), (x + 8, y + 5))
        elif "pendrive" in nombre:
            pygame.draw.rect(s, (40, 180, 200), (x, y + 1, 8, 4))
            pygame.draw.rect(s, (190, 190, 190), (x + 8, y + 2, 3, 2))
        elif "IRPF" in nombre:
            t = self.letras.texto("IRPF", (150, 150, 150), 6, sombra=False)
            pygame.draw.ellipse(s, (110, 110, 110), (x, y - 1, t.get_width() + 6, 8), 1)
            s.blit(t, (x + 3, y - 1))
        elif "amonites" in nombre:
            pygame.draw.circle(s, col, (x + 3, y + 3), 3, 1)
            pygame.draw.circle(s, col, (x + 3, y + 3), 1)
        else:
            pygame.draw.ellipse(s, col, (x, y + 1, 6, 4))
            s.set_at((x + 1, y + 2), claro(col, 0.5))

    def _piezas(self, sala):
        """Los muebles de la sala que ya han aparecido: (pieza, sitio, contexto)."""
        m = self.m
        dia = int(m.dia)
        out, cuenta = [], {}
        for mu in m.muebles_de(sala):
            pieza = str(mu.get("pieza", "")).lower()
            if pieza not in MU.PIEZAS:   # el aviso sale al cargar (muebles.revisar)
                continue
            try:
                aparece = int(mu.get("aparece", 0))
            except (TypeError, ValueError):
                aparece = 0
            if aparece > dia:
                continue
            if sala.ancho < MU.ancho_minimo(pieza):   # no se pinta: se saldría de la sala
                self._aviso("%s: «%s» no cabe en la sala (tiene %d columnas y hacen falta %d)"
                            % (sala.nombre, pieza, sala.ancho, MU.ancho_minimo(pieza)))
                continue
            k = cuenta[pieza] = cuenta.get(pieza, -1) + 1
            out.append((pieza, mu.get("sitio"), MU.Contexto(self, dia, aparece, k)))
        return out

    def _muebles(self, s, sala, r, suelo_y):
        for pieza, sitio, ctx in self._piezas(sala):
            x, y = MU.colocar(pieza, sitio, r)
            MU.PIEZAS[pieza][3](s, x, y, r, ctx)

    # ================================================================ fotograma

    def dibujar(self):
        m = self.m
        t = m.t
        dst = self.dst
        self._cielo()
        self._estrellas(t)
        self._fugaz(t)
        self._arcoiris()
        self._astro()
        self._nubes()
        self._fuegos_y_cielo_fiesta(t)
        self._montes()
        self._superficie()
        self._hierba(t)
        self._superficie_viva(t)
        self._actualizar_tierra()
        dst.blit(self.capa_tierra, (0, self.G))
        self._salas_vivas(t)
        self._debajo(t)
        etiquetas = self._hormigas(t)
        self._lluvia(t)
        self._pancarta(t)
        self._nombres(etiquetas, self.textos_salas)
        self._hud()
        self._diario()

    # ---------------------------------------------------------------- vivos de superficie

    def _superficie_viva(self, t):
        m = self.m
        dst = self.dst
        G = self.G
        deco = m.decoraciones
        sup = m.superficie
        noche = m.de_noche
        # farola encendida
        if noche:
            for x in sup.farolas:
                fx = self.px(x)
                dst.blit(self.halo_farola, (fx - 40, G - 80), special_flags=pygame.BLEND_ADD)
        # lo que se mueve al fondo (el faro, las aspas del molino)
        for k, (pieza, x) in enumerate(sup.piezas_fondo):
            animar = PA.FONDO.get(pieza, (None, None))[1]
            if animar:
                animar(dst, self.px(x), self._base_fondo(x), PA.Contexto(0, m.semilla, noche, k), t)
        # búho
        if sup.buho_x is not None and noche and m.lluvia == 0 and \
                random.Random("buho-%s" % m.ahora.date()).random() < 0.6:
            ojos = "cerrado" if int(t * 1.3) % 9 == 0 else "abierto"
            dst.blit(self.S[("buho", ojos, 1)], (self.px(sup.buho_x) - 7, G - 52))
        # luciérnagas
        if noche and 6 <= m.mes_natural <= 8 and m.lluvia == 0:
            r = random.Random("luc-%s" % m.ahora.date())
            for k in range(14):
                bx = r.uniform(0, self.W) + math.sin(t * 0.3 + k) * 20
                by = G - 4 - r.uniform(0, 30) + math.sin(t * 0.5 + k * 2) * 5
                if math.sin(t * 2 + k * 1.7) > 0.2:
                    dst.fill((200, 255, 90), (int(bx), int(by), 1, 1))
                    dst.fill((120, 160, 50), (int(bx) - 1, int(by), 3, 1))
        # bandera en el montículo
        for clave, cols in (("andalucia", ((40, 150, 70), (245, 245, 245), (40, 150, 70))),
                            ("espana", ((200, 30, 40), (250, 200, 30), (200, 30, 40)))):
            if clave in deco:
                x = self.px(m.salidas_x[0]) + 2
                top = G - 46
                pygame.draw.line(dst, (190, 190, 195), (x, top), (x, G - 8), 2)
                for i in range(18):
                    ola = int(math.sin(t * 4 + i / 3) * 1.5)
                    for k, c in enumerate(cols):
                        dst.fill(c, (x + 2 + i, top + 1 + k * 4 + ola, 1, 4))
        # portada de feria con bombillas
        if "feria" in deco:
            self._portada(t)
        if "feria" in deco or "banderines" in deco or "andalucia" in deco or "carnaval" in deco:
            pass
        if "san_juan" in deco and noche:
            hx = self.px(m.salidas_x[0]) + 60
            for k in range(14):
                fx = hx + self.rng.randint(-6, 6)
                fy = G - self.rng.randint(0, 16)
                dst.fill(self.rng.choice([(255, 200, 60), (250, 120, 30), (255, 240, 150)]), (fx, fy, 2, 2))
            pygame.draw.line(dst, (90, 60, 40), (hx - 8, G - 1), (hx + 8, G - 3), 2)
            pygame.draw.line(dst, (90, 60, 40), (hx - 8, G - 3), (hx + 8, G - 1), 2)
            dst.blit(self.halo_farola, (hx - 40, G - 50), special_flags=pygame.BLEND_ADD)
        if "halloween" in deco and noche:
            for k, x in enumerate(self._calabazas()):
                if int(t * 4 + k) % 3:
                    dst.fill((255, 220, 90), (x + 6, G - 8, 4, 2))
        if "semana_santa" in deco and 18 <= m.ahora.hour <= 23:
            ciclo = (t * 12) % (self.W + 160) - 80
            dst.blit(self.S["trono"], (int(ciclo), G - 12))
            dst.blit(self.halo_lampara, (int(ciclo) + 8, G - 40), special_flags=pygame.BLEND_ADD)
            for k in range(1, 6):
                cx = int(ciclo) - k * 14
                pygame.draw.polygon(dst, (110, 50, 140), [(cx, G - 1), (cx + 6, G - 1), (cx + 3, G - 16)])
                dst.fill((30, 20, 30), (cx + 2, G - 9, 3, 1))
        if m.cumples:
            x = self.px(m.ox + m.x_cumple)
            for k in range(3):
                if int(t * 6 + k) % 4:
                    dst.fill((255, 230, 120), (x + 4 + k * 6, G - 20, 2, 3))
        # bichos de la superficie
        for b in sup.bichos:
            self._bicho(b, t)
        # comida, presas y enemigos
        for c in m.vida.cosas:
            if c.estado != "libre":
                continue
            x, yb = self.px(m.ox + c.x), G
            if c.tipo == "comida":
                spr = self.S.get(("muerta", c.clave)) if c.clave in A.PRESAS_CLAVES else None
                spr = spr or self.S.get(("comida", c.clave)) or self.S[("comida", "miga")]
            else:
                fr = "b" if int(t * 4) % 2 and (c.clave, "b", 1) in self.S else "a"
                spr = self.S[(c.clave, fr, 1 if c.dir > 0 else -1)]
            dst.blit(spr, (x, yb - spr.get_height()))
        for e in m.vida.enemigos:
            x = self.px(m.ox + e.x)
            if e.clave == "pajaro":
                spr = self.S[("pajaro", "a", 1)]
                dst.blit(spr, (x, (m.oy + e.y) * CH))
            elif e.clave == "arana":
                spr = self.S[("arana", "a" if int(t * 5) % 2 else "b", 1)]
                dst.blit(spr, (x, G - spr.get_height()))
            elif e.clave == "roja":
                f = self.hormigas_rojas[(e.dir, int(t * 8) % 4)]
                dst.blit(f, (x, G - HA.ALTO))
        for x, y, _ in m.vida.chispas:
            sx, sy = self.px(m.ox + x), int((m.oy + y) * CH)
            dst.fill((255, 240, 120), (sx, sy, 2, 2))
            dst.fill((255, 160, 40), (sx - 2, sy + 1, 6, 1))

    def _portada(self, t):
        m = self.m
        dst = self.dst
        G = self.G
        sx = self.px(m.salidas_x[0])
        base = 9 + 4 * m.superficie._alto_monticulo()
        x0 = sx + self.px(base // 2 + 3)
        w = 64
        if x0 + w > self.W:
            x0 = sx - w // 2
        top = G - 44
        pygame.draw.rect(dst, (200, 40, 40), (x0, top, 3, 44))
        pygame.draw.rect(dst, (200, 40, 40), (x0 + w - 3, top, 3, 44))
        pygame.draw.rect(dst, (240, 230, 220), (x0, top, w, 12))
        pygame.draw.rect(dst, (200, 40, 40), (x0, top, w, 12), 2)
        txt = self.letras.texto("FERIA", (200, 40, 40), 9, sombra=False)
        dst.blit(txt, (x0 + w // 2 - txt.get_width() // 2, top + 1))
        for i in range(4, w - 3, 5):
            if (int(t * 4) + i) % 3:
                dst.fill(COLORES_FIESTA[(i // 5) % 6], (x0 + i, top + 13, 2, 2))

    def _bicho(self, b, t):
        m = self.m
        tipo = getattr(b, "tipo", "murcielago")
        der = 1 if (b.vx > 0 or (b.vx == 0 and getattr(b, "x0", 0) <= b.x)) else -1
        x = self.px(b.x)
        G = self.G
        fr2 = int(t * 4) % 2
        if tipo == "conejo":
            clave = "come" if b.pausa > 0 else ("salto" if fr2 else "sentado")
            spr = self.S[("conejo", clave, der)]
            y = G - spr.get_height() - (3 if clave == "salto" else 0)
        elif tipo == "paloma":
            if b.vy != 0:
                spr = self.S[("paloma", "vuela", der)]
                y = int(b.y * CH)
            else:
                spr = self.S[("paloma", "come" if int(t * 2 + b.x) % 3 == 0 else "quieta", der)]
                y = G - spr.get_height()
        elif tipo == "gato":
            col = _color_gato(b)
            clave = "sentado" if b.pausa > 0 else ("anda" if fr2 else "anda2")
            spr = self.S[("gato_" + col, clave, der)]
            y = G - spr.get_height()
        elif tipo in ("lagartija", "caracol", "erizo"):
            spr = self.S[(tipo, "a", der)]
            y = G - spr.get_height()
        elif tipo == "abeja":
            spr = self.S[("abeja", "a" if int(t * 12) % 2 else "b", der)]
            y = int(b.y * CH) + 4
        elif tipo == "mariposa":
            spr = self.S[("mariposa", "a" if int(t * 6) % 2 else "b", 1)]
            y = int(b.y * CH)
        elif tipo == "gaviota":
            spr = self.S[("gaviota", "arriba" if int(t * 3 + b.x) % 2 else "abajo", der)]
            y = int(b.y * CH)
        elif tipo == "pajaro":
            spr = self.S[("golondrina", "a" if int(t * 6) % 2 else "b", der)]
            y = int(b.y * CH)
        elif tipo == "avion":
            spr = self.S[("avion", "a", der)]
            y = int(b.y * CH)
            if m.de_noche:
                luz = (255, 60, 60) if int(t * 2) % 2 else (60, 255, 80)
                self.dst.fill(luz, (x + (4 if der < 0 else 28), y + 4, 2, 2))
            # estela
            for k in range(1, 6):
                self.dst.fill((235, 235, 240), (x - der * k * 8 + (0 if der > 0 else 30), y + 5, 5, 1))
        else:  # murciélagos
            spr = self.S[("murcielago", "a" if int(t * 8) % 2 else "b", 1)]
            y = int(b.y * CH)
        self.dst.blit(spr, (x, y))

    def _fuegos(self, t):
        """Fuegos artificiales: Nochevieja (sobre todo a medianoche), noches de feria y San Juan."""
        m = self.m
        dt = max(0.0, min(0.2, t - self.t_prev))
        self.t_prev = t
        deco = m.decoraciones
        ritmo = 0.0
        if m.de_noche and m.lluvia == 0:
            h = m.ahora.hour + m.ahora.minute / 60
            if "nochevieja" in deco:
                ritmo = 3.0 if (h >= 23.9 or h <= 0.4) else 0.6
            elif "feria" in deco and h >= 22.5:
                ritmo = 0.4
            elif "san_juan" in deco:
                ritmo = 0.25
        r = self.rng
        if ritmo and r.random() < dt * ritmo:
            cx, cy = r.uniform(60, self.W - 140), r.uniform(40, self.G - 70)
            col = r.choice(COLORES_FIESTA + [(255, 180, 60), (180, 120, 255)])
            n = r.randint(24, 40)
            for k in range(n):
                a = k / n * 2 * math.pi
                v = r.uniform(30, 55)
                self.fuegos.append([cx, cy, math.cos(a) * v, math.sin(a) * v, col, r.uniform(1.0, 1.6)])
        vivos = []
        for p in self.fuegos:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 30 * dt
            p[2] *= 0.985
            p[5] -= dt
            if p[5] > 0:
                vivos.append(p)
                tam = 2 if p[5] > 0.5 else 1
                c = p[4] if p[5] > 0.4 else oscuro(p[4], 0.6)
                self.dst.fill(c, (int(p[0]), int(p[1]), tam, tam))
        self.fuegos = vivos

    def _fuegos_y_cielo_fiesta(self, t):
        m = self.m
        dst = self.dst
        self._fuegos(t)
        deco = m.decoraciones
        reloj_x = self.W - 110
        if "feria" in deco or "navidad" in deco or "banderines" in deco or "andalucia" in deco:
            # guirnalda de farolillos / luces / banderines, de los textos de arriba al reloj (sin taparlos)
            x0 = 10 + max(x + img.get_width() for img, (x, _y) in self._textos_hud())
            for x in range(x0, reloj_x, 8):
                y = 22 + int(8 * math.sin(math.pi * ((x - x0) % 120) / 120))
                k = (x - x0) // 8
                if "feria" in deco:
                    c = COLORES_FIESTA[k % 4]
                    pygame.draw.ellipse(dst, c, (x - 2, y, 5, 6))
                    dst.fill(claro(c, 0.5), (x - 1, y + 1, 1, 2))
                elif "navidad" in deco:
                    if (int(t * 2) + k) % 3:
                        dst.fill(COLORES_FIESTA[k % 6], (x, y + 1, 2, 2))
                elif "andalucia" in deco:
                    c = (40, 150, 70) if k % 2 else (245, 245, 245)
                    pygame.draw.polygon(dst, c, [(x - 3, y), (x + 3, y), (x, y + 6)])
                else:
                    pygame.draw.polygon(dst, COLORES_FIESTA[k % 6], [(x - 3, y), (x + 3, y), (x, y + 6)])
                if x + 8 < reloj_x:
                    y2 = 22 + int(8 * math.sin(math.pi * ((x + 8 - x0) % 120) / 120))
                    pygame.draw.line(dst, (90, 80, 70), (x, y), (x + 8, y2))
        if "pi" in deco:
            t2 = self.letras.texto("π = 3,14159265...", (255, 230, 120), 11)
            dst.blit(t2, (self.W // 2 - t2.get_width() // 2, 88 if m.cumples else 60))

    # ---------------------------------------------------------------- lluvia y partículas

    def _lluvia(self, t):
        m = self.m
        dst = self.dst
        for p in m.superficie.particulas:
            x, y = int(p[0] * CW), int(p[1] * CH)
            ch = p[4]
            if ch in "|/":
                dx = -3 if ch == "/" else 0
                dst.fill((170, 190, 230), (x, y, 1, 5)) if dx == 0 else \
                    pygame.draw.line(dst, (170, 190, 230), (x, y), (x + dx, y + 6))
                if y > self.G - 10 and self.rng.random() < 0.3:
                    dst.fill((200, 215, 240), (x - 1, self.G - 2, 3, 1))
            elif ch == "❄":
                dst.fill((240, 244, 255), (x + int(math.sin(p[1] + p[0]) * 2), y, 2, 2))
            elif ch in ("♥", "<3"):
                dst.blit(self.S["corazon"], (x, y))
            elif ch == "*" and p[6] < 1.3:  # fuegos artificiales
                c = rgb(_color_de(p[5]))
                dst.fill(c, (x, y, 2, 2))
            else:  # hojas, pétalos, confeti
                c = rgb(_color_de(p[5]))
                dst.fill(c, (x, y, 2, 1))
        if m.superficie.relampago > 0:
            capa = pygame.Surface((self.W, self.G)).convert()
            capa.fill((240, 240, 255))
            capa.set_alpha(110)
            dst.blit(capa, (0, 0))
            r = random.Random(int(t))
            x = r.randint(60, self.W - 60)
            pts = [(x, 0)]
            for y in range(12, self.G - 10, 14):
                x += r.randint(-10, 10)
                pts.append((x, y))
            pygame.draw.lines(dst, (255, 255, 230), False, pts, 2)

    # ---------------------------------------------------------------- salas (lo que se mueve)

    def _piezas_vivas(self, sala):
        """Las piezas animadas de la sala (se recalcula una vez al día)."""
        clave = (sala.clave, int(self.m.dia))
        cache = self.__dict__.setdefault("_cache_vivas", {})
        if clave not in cache:
            if len(cache) > 200:
                cache.clear()
            cache[clave] = [p for p in self._piezas(sala) if MU.PIEZAS[p[0]][4]]
        return cache[clave]

    def _salas_vivas(self, t):
        m = self.m
        dst = self.dst
        G = self.G
        deco = m.decoraciones
        cumple_en = {}
        for h in m.hormigas.values():
            if h.nombre in m.cumples:
                cumple_en.setdefault(h.sala, []).append(h.nombre)
        self.textos_salas = []   # carteles y frases de cumpleaños: los nombres de las hormigas no los tapan
        for sala in m.salas:
            r = self._rect_sala(sala).move(0, G)
            suelo = r.bottom
            cartel = self._cartel(sala, r)[1]
            self.textos_salas.append(cartel)
            # lámparas con luz cálida, sin tapar el cartel: a un lado o, si no caben, colgadas de él
            xs = [r.x + r.width // 4, r.x + 3 * r.width // 4] if r.width > 96 else [r.centerx]
            lamparas = []
            for lx in xs:
                techo = r.y
                if cartel.left - 6 < lx < cartel.right + 6:
                    lado = cartel.left - 7 if lx < cartel.centerx else cartel.right + 7
                    if r.x + 6 <= lado <= r.right - 7:
                        lx = lado
                    else:
                        techo = cartel.bottom
                y = r.y if techo == r.y else techo - 6   # colgada del cartel, con el cable más corto
                pygame.draw.line(dst, (60, 60, 60), (lx, techo), (lx, y + 8))
                pygame.draw.polygon(dst, (170, 150, 90), [(lx - 4, y + 12), (lx + 4, y + 12), (lx + 2, y + 8),
                                                          (lx - 2, y + 8)])
                dst.fill((255, 240, 170), (lx - 1, y + 12, 3, 2))
                dst.blit(self.halo_lampara, (lx - 26, y - 10), special_flags=pygame.BLEND_ADD)
                lamparas.append(pygame.Rect(lx - 4, techo, 9, y + 14 - techo))
            # lo que se mueve en los muebles (pantallas, vapor, burbujas, relojes)
            for pieza, sitio, ctx in self._piezas_vivas(sala):
                x, y = MU.colocar(pieza, sitio, r)
                MU.PIEZAS[pieza][4](dst, x, y, r, ctx, t)
            # el cumpleaños: la frase, debajo del cartel (y de las lámparas que cuelguen de él)
            frase = None
            nombres = cumple_en.get(sala.clave)
            if nombres:
                for texto, tam in (("¡Feliz cumple, %s!" % " y ".join(nombres), 8), ("¡Feliz cumple!", 8),
                                   ("¡Feliz cumple!", 7), ("¡Feliz cumple!", 6)):
                    txt = self.letras.texto(texto, (255, 230, 90), tam)
                    if txt.get_width() <= r.width - 8:
                        frase = pygame.Rect(r.centerx - txt.get_width() // 2, r.y + 14, *txt.get_size())
                        break
                if frase:
                    frase.top = max([frase.top] + [lp.bottom for lp in lamparas
                                                   if lp.left < frase.right and frase.left < lp.right])
                    self.textos_salas.append(frase)

            def libre(rect):   # sólo se mira si hay frase: (not frase or libre(...))
                return not frase.colliderect(rect)
            festiva = sala.funcion in ("trabajo", "comedor", "reuniones", "despacho")
            # fiestas dentro de las salas (sin pisar la frase del cumpleaños ni salirse de la sala)
            if "navidad" in deco:
                for k, x in enumerate(range(r.x + 6, r.right - 6, 6)):
                    if (int(t * 2) + k) % 3 and (not frase or libre((x, r.y + 14 + (k % 2), 2, 2))):
                        dst.fill(COLORES_FIESTA[k % 6], (x, r.y + 14 + (k % 2), 2, 2))
                if festiva:
                    self._pino(dst, r.right - 34, suelo)
            if "feria" in deco:
                for k, x in enumerate(range(r.x + 8, r.right - 8, 10)):
                    c = COLORES_FIESTA[k % 4]
                    farolillo = (x, r.y + 13 + (k % 2) * 2, 5, 6)
                    if not frase or libre(farolillo):
                        pygame.draw.ellipse(dst, c, farolillo)
            if "halloween" in deco:
                # la telaraña, en la esquina y sin llegar al cartel (más pequeña si no cabe)
                f = min(1.0, (cartel.left - r.x - 4) / 15)
                if f > 0.3:
                    for i in range(6):
                        pygame.draw.line(dst, (200, 200, 200), (r.x + 2, r.y + 2),
                                         (r.x + 2 + int(i * 3 * f), r.y + 18 - i * 2))
                if festiva:
                    dst.blit(self.S["calabaza"], (r.right - 24, suelo - 14))
            if ("andalucia" in deco or "espana" in deco) and festiva and \
                    (not frase or libre((r.x + 6, r.y + 16, 12, 9))):
                cols = ((40, 150, 70), (245, 245, 245), (40, 150, 70)) if "andalucia" in deco else \
                    ((200, 30, 40), (250, 200, 30), (200, 30, 40))
                for k, c in enumerate(cols):
                    dst.fill(c, (r.x + 6, r.y + 16 + k * 3, 12, 3))
            if "nochevieja" in deco and sala.funcion == "comedor":
                for k in range(12):
                    if r.x + 46 + k * 4 <= r.right - 4:
                        pygame.draw.circle(dst, (130, 190, 70), (r.x + 44 + k * 4, suelo - 14), 2)
            if "carnaval" in deco:
                for k in range(8):
                    x = r.x + (int(t * 20) * 7 + k * 37) % max(1, r.width - 1)
                    y = r.y + 14 + (k * 7) % (r.height - 20)
                    if not frase or libre((x, y, 2, 2)):
                        dst.fill(COLORES_FIESTA[k % 6], (x, y, 2, 2))
            if nombres:
                # los globos: a los dos lados de la frase o, si no cabe, repartidos por la sala
                for k, g in enumerate(self.S["globos"]):
                    if frase:
                        gx = frase.left - 9 - k // 2 * 8 if k % 2 == 0 else frase.right + 4 + k // 2 * 8
                    else:
                        gx = r.x + 10 + k * (r.width - 20) // 6
                    globo = g.get_rect(topleft=(gx, r.y + 14 + int(math.sin(t * 2 + k) * 2)))
                    if r.x + 3 <= globo.left and globo.right <= r.right - 3 and globo.collidelist(lamparas) == -1:
                        dst.blit(g, globo)
                if frase:
                    dst.blit(txt, frase)

    def _debajo(self, t):
        m = self.m
        for d in m.vida.debajo:
            x = self.px(m.ox + d["x"])
            if d["tipo"] == "lombriz":
                spr = self.S[("lombriz", "a" if int(t * 2) % 2 else "b", 1 if d["vx"] > 0 else -1)]
                self.dst.blit(spr, (x, (m.oy + d["y"]) * CH + 2))
            else:
                spr = self.S[("cochinilla", "a", d["dir"])]
                self.dst.blit(spr, (x - 4, self.py_suelo(d["y"]) - spr.get_height()))

    # ---------------------------------------------------------------- hormigas

    def _hormigas(self, t):
        m = self.m
        dst = self.dst
        etiquetas = []
        gorro_fiesta = m.gorro_fiesta
        for h in m.hormigas.values():
            if getattr(h, "esqueleto", False):
                col = HA.HUESO
                fr = self.cache_hormigas.get("esqueleto") or self.cache_hormigas.setdefault(
                    "esqueleto", HA.fotogramas(None, esqueleto=True))
            else:
                col = rgb_desde(h.color)
                fr = self.hormiga(col)
            gx, gy = h.x, h.y
            if h.ruta and not h.escoltando:  # entre celda y celda, movimiento suave
                nx, ny = h.ruta[0]
                f = min(1.0, h.avance)
                gx, gy = h.x + (nx - h.x) * f, h.y + (ny - h.y) * f
            x = self.px(m.ox + gx) + 2 - HA.ANCLA_X
            y = int(self.py_suelo(gy)) - HA.ALTO
            andando = bool(h.ruta) or (h.escoltando and h.escoltando[0].ruta)
            if h.durmiendo and not h.ruta:
                spr = fr[(h.dir, "dormida")]
            elif andando:
                spr = fr[(h.dir, h.pasos % 4)]
            else:
                spr = fr[(h.dir, "quieta")]
            dst.blit(spr, (x, y))
            cabeza_x = x + (22 if h.dir > 0 else HA.ANCHO - 22)
            # lo que lleva
            if h.carga_cosa is not None:
                c = h.carga_cosa
                s = self.S.get(("muerta", c.clave)) or self.S.get(("comida", c.clave)) or self.S[("comida", "miga")]
                dst.blit(s, (cabeza_x - s.get_width() // 2 + 4 * h.dir, y + 2 - s.get_height()))
            elif h.carga:
                c = (150, 110, 70) if h.carga == "·" else (230, 205, 150)
                dst.fill(c, (cabeza_x + 5 * h.dir, y + 8, 3, 3))
            # gorro
            gorro = "cumple" if h.nombre in m.cumples else gorro_fiesta
            if gorro and not (h.durmiendo and not h.ruta):
                self._gorro(gorro, cabeza_x, y + 3, h.dir)
            if h.durmiendo and not h.ruta:
                for k in range(2):
                    fase = (t * 0.7 + k * 0.5) % 1
                    zz = self.letras.texto("z", (200, 200, 220), 7 + k, sombra=False)
                    dst.blit(zz, (x + 22 + int(fase * 6), y - 2 - int(fase * 10) - k * 3))
            dormida = h.durmiendo and not h.ruta
            etiquetas.append((x + HA.ANCHO // 2, y - (12 if gorro and not dormida else 4), h.nombre, col,
                              dormida))
        return etiquetas

    def _gorro(self, gorro, cx, y, d):
        dst = self.dst
        if gorro in ("cumple", "fiesta"):
            pygame.draw.polygon(dst, (230, 60, 200), [(cx - 4, y), (cx + 4, y), (cx, y - 10)])
            for k in range(3):
                dst.fill((250, 230, 80), (cx - 3 + k * 2, y - 2 - k * 3, 2, 1))
            dst.fill((255, 255, 255), (cx - 1, y - 12, 3, 3))
        elif gorro == "papa_noel":
            pygame.draw.polygon(dst, (210, 30, 30), [(cx - 5, y), (cx + 4, y), (cx + 6 * -d, y - 8)])
            dst.fill((250, 250, 250), (cx - 5, y - 1, 10, 2))
            dst.fill((250, 250, 250), (cx + 6 * -d - 1, y - 10, 3, 3))
        elif gorro == "corona":
            pygame.draw.polygon(dst, (250, 200, 40), [(cx - 4, y), (cx + 4, y), (cx + 4, y - 5), (cx + 2, y - 3),
                                                      (cx, y - 6), (cx - 2, y - 3), (cx - 4, y - 5)])
            dst.fill((220, 40, 60), (cx, y - 2, 1, 1))
        elif gorro == "capirote":
            pygame.draw.polygon(dst, (110, 50, 140), [(cx - 4, y), (cx + 4, y), (cx, y - 14)])
        elif gorro == "bruja":
            dst.fill((40, 20, 50), (cx - 6, y - 1, 12, 2))
            pygame.draw.polygon(dst, (60, 30, 80), [(cx - 3, y - 1), (cx + 3, y - 1), (cx - 2 * d, y - 12)])
        elif gorro == "flor":
            for ang in range(0, 360, 72):
                a = math.radians(ang)
                dst.fill((230, 40, 60), (cx - 3 + int(math.cos(a) * 2), y - 5 + int(math.sin(a) * 2), 2, 2))
            dst.fill((250, 220, 60), (cx - 3, y - 5, 1, 1))
        elif gorro == "antifaz":
            dst.fill((40, 160, 200), (cx - 2, y + 3, 6, 2))

    def _nombres(self, etiquetas, textos=()):
        """Nombres siempre encima; si chocan, uno sube. Los textos de las salas (carteles y frases
        de cumpleaños) no se tapan: si no queda otro sitio, antes se monta sobre otro nombre."""
        ocupado = list(textos)
        # primero las despiertas (siempre se ven); las dormidas sólo si caben
        for cx, y, nombre, col, dormida in sorted(etiquetas, key=lambda e: (e[4], e[1], e[0])):
            s = self.letras.texto(nombre, claro(col, 0.25) if not dormida else oscuro(claro(col, 0.25), 0.7), 8)
            w, h = s.get_size()
            x = cx - w // 2

            def sitios():
                for fila in range(5):
                    for dx in (0, -w // 2 - 2, w // 2 + 2):
                        yield pygame.Rect(x + dx, y - h - fila * (h - 1), w, h)
            r = next((c for c in sitios() if c.collidelist(ocupado) == -1), None)
            if r is None:
                if dormida:
                    continue
                r = next((c for c in sitios() if c.collidelist(textos) == -1), pygame.Rect(x, y - h, w, h))
            ocupado.append(r)
            self.dst.blit(s, r.topleft)

    # ---------------------------------------------------------------- textos

    def _pancarta(self, t):
        m = self.m
        dst = self.dst
        if m.cumples:
            clave = ("cumple",)
            if getattr(self, "_pancarta_clave", None) != clave:
                self._pancarta_clave = clave
                self._pancarta_img = [reloj_grande("FELIZ CUMPLE", c, 3) for c in COLORES_FIESTA[:4]]
            img = self._pancarta_img[int(t * 2) % 4]
            dst.blit(img, (self.W // 2 - img.get_width() // 2, 48))
            nombres = ", ".join(m.cumples)
            txt = self.letras.texto(nombres if len(nombres) < 90 else nombres[:87] + "...", (255, 240, 150), 10)
            dst.blit(txt, (self.W // 2 - txt.get_width() // 2, 70))
        elif m.fiesta_mensaje:
            txt = self.letras.texto(m.fiesta_mensaje, (255, 236, 120), 11)
            dst.blit(txt, (self.W // 2 - txt.get_width() // 2, 44))

    def _textos_hud(self):
        """Los textos de arriba a la izquierda: [(imagen, posición)]."""
        m = self.m
        a = m.ahora
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                 "octubre", "noviembre", "diciembre"]
        fecha = "%s, %d de %s de %d" % (dias[a.weekday()], a.day, meses[a.month - 1], a.year)
        out = [(self.letras.texto(fecha, (255, 255, 255), 11), (6, 4))]
        # redondeada antes: con "%.0f", de -0,5 a 0 grados saldría «-0 °C»
        info = "Día %d del hormiguero · %s · %d °C%s" % (int(m.dia), m.estacion, round(m.temperatura),
                                                         (" · nieve" if m.nieve else " · lluvia") if m.lluvia else "")
        out.append((self.letras.texto(info, (225, 230, 240), 9), (6, 18)))
        if m.pausa_texto:
            out.append((self.letras.texto(" ★ " + m.pausa_texto + " ", (30, 30, 30), 10, fondo=(255, 225, 90)),
                        (6, 31)))
        elif m.demo_texto:
            out.append((self.letras.texto(m.demo_texto, (200, 205, 220), 8), (6, 31)))
        return out

    def _hud(self):
        dst = self.dst
        for img, pos in self._textos_hud():
            dst.blit(img, pos)
        hora = self.m.ahora.strftime("%H:%M")
        if self.cache_reloj[0] != hora:
            self.cache_reloj = (hora, reloj_grande(hora, (255, 255, 255), 3))
        img = self.cache_reloj[1]
        dst.blit(img, (self.W - img.get_width() - 8, 6))

    def _diario(self):
        m = self.m
        dst = self.dst
        m.actualizar_diario()
        y = self.H - 9
        dst.fill((16, 12, 10), (0, y, self.W, 9))
        if m.noticias and m.t - m.noticias[-1][2] < 25:
            texto, col = "¡Ahora! · " + m.noticias[-1][1], (255, 225, 90)
        elif m.diario:
            recientes = m.diario[-4:] + [(n[0], n[1]) for n in m.noticias[-4:]]
            e = recientes[-1 - int(m.t / 8) % len(recientes)]
            # cuándo pasó, contado desde hoy (arriba ya pone en qué día del hormiguero estamos)
            hace = int(m.dia) - int(e[0])
            cuando = "Hoy" if hace <= 0 else "Ayer" if hace == 1 else "Hace %d días" % hace
            texto, col = "%s · %s" % (cuando, e[1]), (220, 200, 160)
        else:
            return
        texto = self.letras.recortar(texto, self.W - 8, 8)   # lo que no cabe, con «…»
        dst.blit(self.letras.texto(texto, col, 8, sombra=False), (4, y - 1))


# ---------------------------------------------------------------- utilidades

# bichos que se dibujan a tamaño doble (los pequeños, como abejas o mariposas, no)
DOBLES = {"conejo", "paloma", "gaviota", "lagartija", "caracol", "erizo", "buho", "golondrina", "avion",
          "arana", "grillo", "oruga", "escarabajo", "cochinilla", "pajaro", "lombriz"}


def _doble(s):
    t = pygame.transform.scale(s, (s.get_width() * 2, s.get_height() * 2))
    t.set_colorkey(CLAVE)
    return t


def rgb_desde(c):
    """motor.colores.Color -> (r,g,b), un poco aclarado para que luzca sobre la tierra."""
    from motor.colores import rgb_de_256
    r = rgb_de_256(c.c256)
    return r


def _color_de(c):
    return c.c256 if hasattr(c, "c256") else c


def _nevar(s, suelo):
    """Pone nieve encima de todo lo que hay pintado en la capa (árboles, tejados, lápidas...):
    en cada columna, unos píxeles blancos sobre el primer píxel opaco que se encuentra."""
    mascara = pygame.mask.from_surface(s)
    w, h = s.get_size()
    blanco, sombra = (240, 244, 250), (200, 210, 228)
    for x in range(w):
        for y in range(0, min(h, suelo)):
            if mascara.get_at((x, y)):
                grosor = 2 + (x * 7 % 5 == 0)
                for k in range(grosor):
                    if y + k < h and mascara.get_at((x, y + k)):
                        s.set_at((x, y + k), blanco if k < grosor - 1 else sombra)
                break


def _color_gato(b):
    if not hasattr(b, "_color_pix"):
        b._color_pix = random.Random(id(b)).choice(["naranja", "negro_brillante", "plata", "blanco_brillante"])
    return b._color_pix


def _oscurecer_alpha(s, f):
    t = s.copy()
    t.fill((int(255 * f), int(255 * f), int(255 * (f + 0.1))), special_flags=pygame.BLEND_RGB_MULT)
    return t


A.PRESAS_CLAVES = ("grillo", "oruga", "mosca", "lombriz", "escarabajo", "roja")
