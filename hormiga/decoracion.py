"""Detalles de decoración: lo que hay dentro de la tierra, el adorno de las
salas y lo que se pone en cada fiesta. Todo es determinista (misma semilla,
mismo dibujo) salvo los parpadeos."""

import random

from .tierra import ANCHO, ARCILLA, ARENA, HUMUS, PROF, ROCA

# ------------------------------------------------------------ dentro de la tierra

FOSILES = [
    ("<°)))><", "arena"),        # un pez fósil: homenaje a la pecera
    ("═╦══╦═", "blanco"),         # un hueso
    ("@", "arena"),               # amonites
    ("▐▀▌", "verde"),             # una botella vieja
    ("═══╗", "gris"),             # una tubería abandonada
    ("ᴥ", "blanco"),              # una huella
]


def detalles_suelo(plan, semilla):
    """{(x, y): (carácter, color)} con raíces, piedras, gemas y fósiles."""
    rng = random.Random("detalles-%s" % semilla)
    d = {}
    # raíces que bajan desde la hierba
    for _ in range(ANCHO // 7):
        x = rng.randrange(2, ANCHO - 2)
        largo = rng.randint(2, 6)
        for y in range(largo):
            ch = rng.choice("│╽╿┃") if rng.random() < 0.6 else ("╲" if rng.random() < 0.5 else "╱")
            d[(x, y)] = (ch, "marron")
            if ch == "╲":
                x += 1
            elif ch == "╱":
                x -= 1
        if rng.random() < 0.6:
            d[(x + rng.choice([-1, 1]), largo)] = ("┘" if rng.random() < 0.5 else "└", "marron")
    # piedrecitas
    for _ in range(ANCHO * PROF // 40):
        x, y = rng.randrange(ANCHO), rng.randrange(PROF - 3)
        d[(x, y)] = (rng.choice("°∙◦o•"), rng.choice(["gris", "plata", "gris_oscuro"]))
    # gemas en la arcilla y la roca
    for _ in range(14):
        x, y = rng.randrange(ANCHO), rng.randrange(20, PROF - 2)
        if plan.tipo(x, y) in (ARCILLA, ROCA):
            d[(x, y)] = ("◆", rng.choice(["rojo_brillante", "verde_brillante", "azul_brillante",
                                          "magenta_brillante", "cian"]))
    # fósiles y cosas enterradas (sólo decoran)
    for texto, col in FOSILES:
        for _ in range(20):
            x, y = rng.randrange(3, ANCHO - 10), rng.randrange(10, PROF - 4)
            if all((x + i, y) not in d for i in range(len(texto))):
                for i, ch in enumerate(texto):
                    d[(x + i, y)] = (ch, col)
                break
    # gotas de humedad cerca del fondo
    for _ in range(25):
        x, y = rng.randrange(ANCHO), rng.randrange(PROF - 10, PROF - 3)
        d[(x, y)] = ("¸", "azul_brillante")
    return d


BORDE = {HUMUS: 94, ARENA: 137, ARCILLA: 130, ROCA: 240}

# ------------------------------------------------------------ las salas

CUADROS = [
    ["╔═══╗", "║▓▒║", "╚═══╝"],
    ["┌──┐", "│◠◡│", "└──┘"],
    ["╭─╮", "│✦│", "╰─╯"],
]
COLORES_CUADRO = [("marron", "cian"), ("dorado", "verde_brillante"), ("plata", "magenta")]


# ------------------------------------------------------------ el horizonte

def horizonte(W, rng):
    """Los Montes de Málaga al fondo (alturas por columna)."""
    alturas = []
    h = 2.0
    for x in range(W):
        h += rng.uniform(-0.45, 0.45)
        h = max(0.5, min(5.0, h))
        alturas.append(h)
    for _ in range(3):
        alturas = [(alturas[max(0, i - 1)] + alturas[i] + alturas[min(W - 1, i + 1)]) / 3
                   for i in range(W)]
    return alturas


CATEDRAL = [
    "   ▲      ",
    "  ▐█▌     ",
    "  ▐█▌ ▄   ",
    " ▄███▄█▄▄ ",
    "▐████████▌",
]
CATEDRAL_ASCII = [
    "   A      ",
    "  |#|     ",
    "  |#| _   ",
    " _###_#__ ",
    "|########|",
]
