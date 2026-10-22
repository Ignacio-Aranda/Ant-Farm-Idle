"""Colores: nombres, códigos de máscara y paleta xterm-256."""

from collections import namedtuple

# Un color de la configuración, como número de la paleta de 256 colores (la de xterm).
# En pantalla se pinta en RGB: rgb_de_256(c256) (los "#RRGGBB" de las salas, tal cual).
Color = namedtuple("Color", "c256")

_BASE = {
    # nombre: número de la paleta
    "negro": 16, "black": 16,
    "rojo": 160, "red": 160,
    "verde": 34, "green": 34,
    "amarillo": 178, "yellow": 178,
    "azul": 27, "blue": 27,
    "magenta": 163,
    "cian": 37, "cyan": 37,
    "blanco": 252, "white": 252,
    "gris": 244, "gray": 244, "grey": 244,
    "gris_oscuro": 239,
    "naranja": 208, "orange": 208,
    "rosa": 211, "pink": 211,
    "morado": 98, "purple": 98,
    "marron": 130, "marrón": 130, "brown": 130,
    "dorado": 220, "gold": 220,
    "arena": 180,
    "turquesa": 44,
    "lima": 154,
    "coral": 209,
    "salmon": 216, "salmón": 216,
    "plata": 250,
}
# las variantes brillantes ("rojo_brillante" o "bright_red"), menos las de los que ya son claros
_BRILLANTES = {16: 242, 160: 196, 34: 82, 178: 226, 27: 39, 163: 201,
               37: 51, 252: 231, 208: 214, 98: 141, 130: 172, 180: 223,
               250: 255}
for _n in list(_BASE):
    if _n in ("gris", "gray", "grey", "gris_oscuro", "rosa", "pink", "dorado",
              "gold", "turquesa", "lima", "coral", "salmon", "salmón"):
        continue
    _BASE[_n + "_brillante"] = _BASE["bright_" + _n] = _BRILLANTES.get(_BASE[_n], _BASE[_n])

# Códigos de una letra de las máscaras de los dibujos (en mayúscula, la variante brillante).
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


_HEX = set("0123456789abcdefABCDEF")


def _hex_bueno(s):
    s = str(s).strip().lstrip("#")
    return len(s) in (3, 6) and all(ch in _HEX for ch in s)


def hex_a_rgb(s):
    """"#RRGGBB" o "#RGB" -> (r, g, b). Mal escrito ("#GG8800"), el blanco de por defecto."""
    if not _hex_bueno(s):
        return rgb_de_256(_BASE["blanco"])
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
        return Color(valor)
    s = str(valor).strip()
    if s.startswith("#") and _hex_bueno(s):
        return Color(a_256(hex_a_rgb(s)))
    if s.isdecimal() and int(s) <= 255:
        return color(int(s))
    if len(s) == 1 and s.lower() in CODIGOS:
        base = CODIGOS[s.lower()]
        return Color(_BASE.get(base + "_brillante", _BASE[base]) if s.isupper() else _BASE[base])
    clave = s.lower().replace(" ", "_").replace("-", "_")
    if clave in _BASE:
        return Color(_BASE[clave])
    return color(defecto) if valor != defecto else Color(_BASE["blanco"])

