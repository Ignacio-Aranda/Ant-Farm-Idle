"""Utilidades de pixel art: colores, sprites a partir de texto y letras."""

import os

import pygame

from motor import colores as C
from motor import fuente

CLAVE = (255, 0, 255)  # color transparente de los sprites (más rápido que el canal alfa)

# Medidas: la simulación trabaja en "celdas" (una rejilla de 160 columnas);
# cada celda son 4x8 píxeles de la imagen interna de 640x512.
CW, CH = 4, 8
ANCHO_PX, ALTO_PX = 640, 512


def rgb(valor):
    """Color de la configuración (nombre, número, #hex) -> (r, g, b)."""
    if isinstance(valor, tuple):
        return valor
    if isinstance(valor, str) and valor.strip().startswith("#"):
        return C.hex_a_rgb(valor)
    return C.rgb_de_256(C.color(valor).c256)


def mezclar(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def oscuro(c, f=0.6):
    return tuple(int(v * f) for v in c)


def claro(c, f=0.35):
    return tuple(int(v + (255 - v) * f) for v in c)


def superficie(w, h):
    s = pygame.Surface((max(1, w), max(1, h))).convert()
    s.fill(CLAVE)
    s.set_colorkey(CLAVE)
    return s


def rejilla(filas, paleta):
    """Sprite a partir de líneas de texto: cada carácter es un píxel.
    '.' y ' ' son transparentes; el resto se busca en 'paleta' {car: (r,g,b)}."""
    filas = [f for f in filas]
    w = max(len(f) for f in filas)
    s = superficie(w, len(filas))
    for y, f in enumerate(filas):
        for x, ch in enumerate(f):
            if ch in ". ":
                continue
            c = paleta.get(ch)
            if c is not None:
                s.set_at((x, y), c)
    return s


def espejo(s):
    t = pygame.transform.flip(s, True, False)
    t.set_colorkey(CLAVE)
    return t


def tenir(s, color_destino, fuerza):
    """Copia de un sprite mezclado hacia un color (para la noche, los muertos...)."""
    t = s.copy()
    t.set_colorkey(None)
    capa = pygame.Surface(t.get_size()).convert()
    capa.fill(color_destino)
    capa.set_alpha(int(255 * fuerza))
    t.blit(capa, (0, 0))
    return _reclavar(s, t)


def multiplicar(s, color):
    t = s.copy()
    t.set_colorkey(None)
    t.fill(color, special_flags=pygame.BLEND_RGB_MULT)
    if s.get_flags() & pygame.SRCALPHA:   # con canal alfa (los textos) no hay color clave
        return t
    return _reclavar(s, t)


def _reclavar(original, t):
    m = pygame.mask.from_surface(original)
    m.invert()
    m.to_surface(t, setcolor=CLAVE, unsetcolor=None)
    t.set_colorkey(CLAVE)
    return t


def circulo_luz(radio, color, intensidad=120):
    """Halo de luz para sumar (BLEND_ADD): negro en los bordes y el color en el centro."""
    s = pygame.Surface((radio * 2, radio * 2)).convert()
    s.fill((0, 0, 0))
    for r in range(radio, 0, -1):
        k = intensidad / 255.0 * (1 - r / radio) ** 1.8
        pygame.draw.circle(s, tuple(int(c * k) for c in color), (radio, radio), r)
    return s


# ----------------------------------------------------------------- letras

def _ruta_fuente():
    for r in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(r):
            return r
    # en Windows o macOS, si está instalada (la letra de pygame no tiene la calavera ☠)
    try:
        return pygame.font.match_font("dejavusans", bold=True) or None
    except Exception:
        return None


# Ajustes de los textos (config.toml, [general]): texto_aumento suma puntos a todos los
# tamaños; texto_suavizado = false da letras de bordes duros, más legibles en monitores VGA.
TEXTO_AUMENTO = 0
TEXTO_SUAVIZADO = True


def ajustar_textos(cfg):
    global TEXTO_AUMENTO, TEXTO_SUAVIZADO
    TEXTO_AUMENTO = int(cfg["general"].get("texto_aumento", 0))
    TEXTO_SUAVIZADO = bool(cfg["general"].get("texto_suavizado", True))


class Letras:
    """Textos con sombra, cacheados (renderizar texto es caro en la Pi)."""

    def __init__(self):
        ruta = _ruta_fuente()
        self.fuentes = {}
        self.ruta = ruta
        self.cache = {}
        self.recortes = {}

    def fuente(self, tam):
        f = self.fuentes.get(tam)
        if f is None:
            f = self.fuentes[tam] = pygame.font.Font(self.ruta, tam + TEXTO_AUMENTO)
        return f

    def texto(self, texto, color, tam=9, sombra=True, fondo=None):
        clave = (texto, color, tam, sombra, fondo)
        s = self.cache.get(clave)
        if s is not None:
            return s
        f = self.fuente(tam)
        img = f.render(texto, TEXTO_SUAVIZADO, color)
        w, h = img.get_size()
        if fondo is not None:
            s = pygame.Surface((w + 4, h + 1)).convert()
            s.fill(fondo)
            s.blit(img, (2, 0))
        elif sombra:
            s = pygame.Surface((w + 1, h + 1), pygame.SRCALPHA)
            som = f.render(texto, TEXTO_SUAVIZADO, (10, 8, 6))
            s.blit(som, (1, 1))
            s.blit(img, (0, 0))
        else:
            s = img
        if len(self.cache) > 600:
            self.cache.clear()
        self.cache[clave] = s
        return s

    def recortar(self, texto, ancho, tam=9):
        """El texto tal cual si cabe en 'ancho' píxeles; si no, hasta la última palabra que
        cabe y con «…» (letra a letra sólo si no cabe ni la primera palabra)."""
        clave = (texto, ancho, tam)
        r = self.recortes.get(clave)
        if r is None:
            f = self.fuente(tam)

            def cabe(t):
                return f.size(t)[0] <= ancho
            r = texto
            if not cabe(texto):
                palabras = texto.split(" ")
                cortes = (" ".join(palabras[:n]).rstrip(" ,;:·-") for n in range(len(palabras) - 1, 0, -1))
                r = next((c + "…" for c in cortes if c and cabe(c + "…")), None)
                if r is None:
                    r = next((texto[:n] + "…" for n in range(len(texto) - 1, 0, -1) if cabe(texto[:n] + "…")),
                             "…")
            if len(self.recortes) > 200:
                self.recortes.clear()
            self.recortes[clave] = r
        return r


def reloj_grande(texto, color, bloque=3):
    """Hora en grande con la fuente de bloques (motor/fuente.py)."""
    filas = fuente.renderizar(texto, "#", 1)
    w = len(filas[0]) * bloque
    s = pygame.Surface((w + 2, len(filas) * bloque + 2), pygame.SRCALPHA)
    sombra = (10, 10, 30, 160)
    for y, f in enumerate(filas):
        for x, ch in enumerate(f):
            if ch == "#":
                pygame.draw.rect(s, sombra, (x * bloque + 2, y * bloque + 2, bloque, bloque))
    for y, f in enumerate(filas):
        for x, ch in enumerate(f):
            if ch == "#":
                pygame.draw.rect(s, color, (x * bloque, y * bloque, bloque - 0, bloque - 0))
    return s
