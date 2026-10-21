"""Colores: nombres, códigos de máscara y paleta xterm-256."""

from collections import namedtuple

# c256: color en terminales de 256 colores
# c8:   color base (0-7) para terminales de 8/16 colores
# vivo: usar la variante brillante/negrita en 8/16 colores
# (en pantalla se pinta en RGB: rgb_de_256(c256), o el "#RRGGBB" tal cual)
Color = namedtuple("Color", "c256 c8 vivo")

_BASE = {
    # nombre: (c256, c8, vivo)
    "negro": (16, 0, False), "black": (16, 0, False),
    "rojo": (160, 1, False), "red": (160, 1, False),
    "verde": (34, 2, False), "green": (34, 2, False),
    "amarillo": (178, 3, False), "yellow": (178, 3, False),
    "azul": (27, 4, False), "blue": (27, 4, False),
    "magenta": (163, 5, False),
    "cian": (37, 6, False), "cyan": (37, 6, False),
    "blanco": (252, 7, False), "white": (252, 7, False),
    "gris": (244, 0, True), "gray": (244, 0, True), "grey": (244, 0, True),
    "gris_oscuro": (239, 0, True),
    "naranja": (208, 3, False), "orange": (208, 3, False),
    "rosa": (211, 5, True), "pink": (211, 5, True),
    "morado": (98, 5, False), "purple": (98, 5, False),
    "marron": (130, 3, False), "marrón": (130, 3, False), "brown": (130, 3, False),
    "dorado": (220, 3, True), "gold": (220, 3, True),
    "arena": (180, 3, False),
    "turquesa": (44, 6, True),
    "lima": (154, 2, True),
    "coral": (209, 1, True),
    "salmon": (216, 1, True), "salmón": (216, 1, True),
    "plata": (250, 7, False),
}
for _n in list(_BASE):
    c256, c8, _v = _BASE[_n]
    if _n in ("gris", "gray", "grey", "gris_oscuro", "rosa", "pink", "dorado",
              "gold", "turquesa", "lima", "coral", "salmon", "salmón"):
        continue
    _BRILLANTES = {16: 242, 160: 196, 34: 82, 178: 226, 27: 39, 163: 201,
                   37: 51, 252: 231, 208: 214, 98: 141, 130: 172, 180: 223,
                   250: 255}
    _BASE[_n + "_brillante"] = (_BRILLANTES.get(c256, c256), c8, True)
    _BASE["bright_" + _n] = _BASE[_n + "_brillante"]

# Códigos de una letra usados en las máscaras (compatibles con asciiquarium).
CODIGOS = {
    "r": "rojo", "g": "verde", "y": "amarillo", "b": "azul", "m": "magenta",
    "c": "cian", "w": "blanco", "k": "negro", "o": "naranja", "p": "rosa",
    "n": "marron", "s": "plata",
}

# ---------------------------------------------------------------- xterm-256

_NIVELES = (0, 95, 135, 175, 215, 255)


def rgb_de_256(n):
    if n < 16:
        basicos = [(0, 0, 0), (205, 0, 0), (0, 205, 0), (205, 205, 0),
                   (0, 0, 238), (205, 0, 205), (0, 205, 205), (229, 229, 229),
                   (127, 127, 127), (255, 0, 0), (0, 255, 0), (255, 255, 0),
                   (92, 92, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)]
        return basicos[n]
    if n < 232:
        n -= 16
        return (_NIVELES[n // 36], _NIVELES[(n // 6) % 6], _NIVELES[n % 6])
    g = 8 + (n - 232) * 10
    return (g, g, g)


def _cercano(v):
    return min(range(6), key=lambda i: abs(_NIVELES[i] - v))


def a_256(rgb):
    r, g, b = rgb
    cubo = 16 + 36 * _cercano(r) + 6 * _cercano(g) + _cercano(b)
    gris_i = max(0, min(23, round((sum(rgb) / 3 - 8) / 10)))
    gris = 232 + gris_i

    def d(n):
        rr, gg, bb = rgb_de_256(n)
        return (rr - r) ** 2 + (gg - g) ** 2 + (bb - b) ** 2
    return cubo if d(cubo) <= d(gris) else gris


def a_8(rgb):
    """Color básico más parecido (0-7) y si debería ir brillante."""
    r, g, b = rgb
    c = (1 if r > 110 else 0) | (2 if g > 110 else 0) | (4 if b > 110 else 0)
    return c, max(rgb) > 200


_HEX = set("0123456789abcdefABCDEF")


def _hex_bueno(s):
    s = str(s).strip().lstrip("#")
    return len(s) in (3, 6) and all(ch in _HEX for ch in s)


def hex_a_rgb(s):
    """"#RRGGBB" o "#RGB" -> (r, g, b). Mal escrito ("#GG8800"), el blanco de por defecto."""
    if not _hex_bueno(s):
        return rgb_de_256(_BASE["blanco"][0])
    s = str(s).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def es_color(valor):
    """¿Se entiende este color de la configuración? (un nombre de la lista, un número
    de 0 a 255, "#RGB" o "#RRGGBB")"""
    if isinstance(valor, bool):
        return False
    if isinstance(valor, int):
        return 0 <= valor <= 255
    if not isinstance(valor, str):
        return False
    s = valor.strip()
    if s.startswith("#"):
        return _hex_bueno(s)
    if s.isdecimal():
        return int(s) <= 255
    if len(s) == 1 and s.lower() in CODIGOS:
        return True
    return s.lower().replace(" ", "_").replace("-", "_") in _BASE


_CACHE = {}


def color(valor, defecto="blanco"):
    """Convierte un valor de configuración (nombre, número, #hex, código) a Color."""
    if isinstance(valor, Color):
        return valor
    try:
        return _CACHE[(valor, defecto)]
    except (KeyError, TypeError):
        pass
    c = _color(valor, defecto)
    try:
        _CACHE[(valor, defecto)] = c
    except TypeError:
        pass
    return c


def _color(valor, defecto):
    if valor is None:
        valor = defecto
    if isinstance(valor, int) and not isinstance(valor, bool) and 0 <= valor <= 255:
        c8, vivo = a_8(rgb_de_256(valor))
        return Color(valor, c8, vivo)
    s = str(valor).strip()
    if s.startswith("#") and _hex_bueno(s):
        rgb = hex_a_rgb(s)
        c8, vivo = a_8(rgb)
        return Color(a_256(rgb), c8, vivo)
    if s.isdecimal() and int(s) <= 255:
        return color(int(s))
    if len(s) == 1 and s.lower() in CODIGOS:
        base = CODIGOS[s.lower()]
        return Color(*_BASE.get(base + "_brillante", _BASE[base]) if s.isupper() else _BASE[base])
    clave = s.lower().replace(" ", "_").replace("-", "_")
    if clave in _BASE:
        return Color(*_BASE[clave])
    return color(defecto) if valor != defecto else Color(252, 7, False)


def rgb(valor):
    """RGB de un valor de configuración (nombre, número, "#hex" o (r, g, b))."""
    if isinstance(valor, (list, tuple)) and len(valor) == 3:
        return tuple(int(v) for v in valor)
    if isinstance(valor, str) and valor.startswith("#"):
        return hex_a_rgb(valor)
    return rgb_de_256(color(valor).c256)


def mezclar(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

