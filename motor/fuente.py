"""Fuente grande de 5 filas para letreros, peces con nombre y el reloj."""

import unicodedata

_GLIFOS = """
A .###. #...# ##### #...# #...#
B ####. #...# ####. #...# ####.
C .#### #.... #.... #.... .####
D ####. #...# #...# #...# ####.
E ##### #.... ####. #.... #####
F ##### #.... ####. #.... #....
G .#### #.... #..## #...# .###.
H #...# #...# ##### #...# #...#
I ### .#. .#. .#. ###
J ..### ...#. ...#. #..#. .##..
K #..#. #.#.. ##... #.#.. #..#.
L #.... #.... #.... #.... #####
M #...# ##.## #.#.# #...# #...#
N #...# ##..# #.#.# #..## #...#
O .###. #...# #...# #...# .###.
P ####. #...# ####. #.... #....
Q .###. #...# #.#.# #..#. .##.#
R ####. #...# ####. #.#.. #..##
S .#### #.... .###. ....# ####.
T ##### ..#.. ..#.. ..#.. ..#..
U #...# #...# #...# #...# .###.
V #...# #...# #...# .#.#. ..#..
W #...# #...# #.#.# ##.## #...#
X #...# .#.#. ..#.. .#.#. #...#
Y #...# .#.#. ..#.. ..#.. ..#..
Z ##### ...#. ..#.. .#... #####
Ñ .###. ..... ##..# #.#.# #..##
0 .###. #..## #.#.# ##..# .###.
1 .#. ##. .#. .#. ###
2 .###. #...# ..##. .#... #####
3 ####. ....# .###. ....# ####.
4 #..#. #..#. ##### ...#. ...#.
5 ##### #.... ####. ....# ####.
6 .###. #.... ####. #...# .###.
7 ##### ...#. ..#.. .#... .#...
8 .###. #...# .###. #...# .###.
9 .###. #...# .#### ....# .###.
: . # . # .
. . . . . #
, .. .. .. .# #.
! # # # . #
¡ # . # # #
? .###. #...# ..##. ..... ..#..
¿ ..#.. ..... .##.. #...# .###.
- .... .... #### .... ....
+ ..... ..#.. ##### ..#.. .....
' # # . . .
% #...# ...#. ..#.. .#... #...#
/ ....# ...#. ..#.. .#... #....
& .##.. #..#. .##.# #..#. .##.#
* ..... #.#.# .###. #.#.# .....
= .... #### .... #### ....
_ ..... ..... ..... ..... #####
( .# #. #. #. .#
) #. .# .# .# #.
<3 .#.#. ##### ##### .###. ..#..
"""

GLIFOS = {}
for _linea in _GLIFOS.strip().splitlines():
    _clave, *_filas = _linea.split()
    GLIFOS["♥" if _clave == "<3" else _clave] = _filas
GLIFOS[" "] = ["..."] * 5

ALTO = 5


def normalizar(texto):
    """Mayúsculas y sin tildes (excepto Ñ, ¡ y ¿, que tienen glifo)."""
    out = []
    for ch in texto.upper():
        if ch in GLIFOS:
            out.append(ch)
            continue
        base = unicodedata.normalize("NFD", ch)[0]
        out.append(base if base in GLIFOS else " ")
    return "".join(out)


def renderizar(texto, relleno="letra", espacio=1):
    """Devuelve una lista de 5 líneas con el texto en grande.

    relleno: "letra" (cada letra se dibuja con ella misma), "bloque" (█) o cualquier carácter.
    """
    filas = [""] * ALTO
    texto = normalizar(texto)
    for i, ch in enumerate(texto):
        glifo = GLIFOS.get(ch, GLIFOS[" "])
        tinta = ch if relleno == "letra" else "█" if relleno == "bloque" else relleno
        if ch == " " or not ch.strip():
            tinta = " "
        sep = " " * espacio if i < len(texto) - 1 else ""
        for f in range(ALTO):
            filas[f] += glifo[f].replace("#", tinta).replace(".", " ") + sep
    return filas


def ancho(texto, espacio=1):
    return len(renderizar(texto, "#", espacio)[0])
