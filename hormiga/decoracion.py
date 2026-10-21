"""Detalles de decoración: lo que hay dentro de la tierra, el adorno de las
salas y lo que se pone en cada fiesta. Todo es determinista (misma semilla,
mismo dibujo) salvo los parpadeos."""

import random

from motor.colores import color

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


def dibujar_sala(m, s, persona_cumple=None):
    """Lámparas, cuadros, suelo de madera y adornos de fiesta de una sala."""
    rng = random.Random("sala-%s-%s" % (m.semilla, s.clave))
    sx, sy = m.a_pantalla(s.x0, s.y0)
    piso = m.a_pantalla(0, s.piso)[1]
    W = s.ancho
    uni = m.unicode
    # suelo de madera
    if s.clave != "planta2":
        m.texto(piso + 1, sx + 1, ("▀" if uni else "=") * (W - 2), color(130))
    else:
        m.texto(piso + 1, sx + 1, ("▔" if uni else "-") * (W - 2), color("cian"))
    # lámparas colgando del techo (se encienden más de noche)
    lamparas = [sx + W // 4, sx + 3 * W // 4] if W > 24 else [sx + W // 2]
    for lx in lamparas:
        m.texto(sy, lx, "┬" if uni else "|", color("gris"))
        luz = "●" if uni else "o"
        m.texto(sy + 1, lx, luz, color("amarillo_brillante" if m.de_noche else "amarillo"))
    # un cuadro en la pared (las salas de trabajo)
    if s.principal and W >= 24 and s.clave != "reuniones":
        i = rng.randrange(len(CUADROS))
        marco, dentro = COLORES_CUADRO[i]
        cx = sx + W // 2 - 2
        for k, fila in enumerate(CUADROS[i]):
            m.texto(sy + 2 + k, cx, fila if uni else "+--+"[:len(fila)], color(marco))
        m.texto(sy + 3, cx + 1, CUADROS[i][1][1:-1] if uni else "##", color(dentro))
    deco = m.decoraciones
    t = m.t
    # ---- fiestas dentro de las salas
    if "navidad" in deco:
        for k in range(2, W - 2, 2):
            if (int(t * 2) + k) % 3:
                m.texto(sy + 1, sx + k, "•" if uni else "*", color("RYGBM"[k % 5]))
        if s.principal or s.clave == "comedor":
            arbol = ["  *  ", " ╱o╲ ", "╱*o*╲", " ▐█▌ "] if uni else ["  *  ", " /o\\ ", "/*o*\\", " |#| "]
            ax = sx + W - 8
            for k, fila in enumerate(arbol):
                m.texto(piso - 3 + k, ax, fila, color("Y" if k == 0 else "verde" if k < 3 else "marron"))
            m.texto(piso, ax - 2, "▣" if uni else "#", color("R"))
            m.texto(piso, ax + 6, "▣" if uni else "#", color("B"))
        if s.clave == "comedor":  # el belén
            m.texto(piso - 1, sx + 3, "★" if uni else "*", color("Y"))
            m.texto(piso, sx + 2, "⌂ ° ⌂" if uni else "^ o ^", color("arena"))
    if "nochevieja" in deco and s.clave == "comedor":
        m.texto(piso - 2, sx + W // 2 - 6, "12 uvas: " + ("●" * 12 if uni else "o" * 12), color("verde_brillante"))
    if "halloween" in deco:
        tela = ["╲│╱", "─┼─", "╱│╲"] if uni else ["\\|/", "-+-", "/|\\"]
        for k, fila in enumerate(tela):
            m.texto(sy + 1 + k, sx + 1, fila, color("gris"))
        if s.principal or s.clave == "comedor":
            vela = "▲" if int(t * 5) % 2 else "▴"
            m.texto(piso - 1, sx + W - 6, "(" + (vela if uni else "^") + ")", color("naranja"))
            m.texto(piso, sx + W - 7, "(▀▄▀)" if uni else "(^v^)", color("naranja"))
    if "feria" in deco:
        for k in range(2, W - 2, 3):
            m.texto(sy + 1, sx + k, "o", color("RWGY"[(k // 3) % 4]))
    if "andalucia" in deco and s.principal:
        for k, col in enumerate(["verde_brillante", "blanco_brillante", "verde_brillante"]):
            m.texto(sy + 2 + k, sx + 2, "▬▬" if uni else "==", color(col))
    if "espana" in deco and s.principal:
        for k, col in enumerate(["rojo_brillante", "amarillo_brillante", "rojo_brillante"]):
            m.texto(sy + 2 + k, sx + 2, "▬▬" if uni else "==", color(col))
    if "semana_santa" in deco and s.principal:
        m.texto(sy + 2, sx + 2, "▐▀▀▌" if uni else "|##|", color("morado"))
        m.texto(sy + 3, sx + 2, " ✝ " if uni else " + ", color("dorado"))
    if "carnaval" in deco:
        for k in range(3):
            x = sx + 2 + (int(t * 3) * 7 + k * 11) % max(1, W - 4)
            m.texto(sy + 2 + k, x, "*", color("RYGBMC"[(k + int(t)) % 6]))
    # globos en la sala de quien cumple años
    if persona_cumple:
        globos = [("R", 3), ("Y", 7), ("B", 11), ("M", W - 12), ("G", W - 8)]
        for col, dx in globos:
            if 1 < dx < W - 2:
                sube = int(t * 1.5 + dx) % 2
                m.texto(sy + 2 - sube, sx + dx, "◯" if uni else "O", color(col))
                m.texto(sy + 3 - sube, sx + dx, "│" if uni else "|", color("s"))
        texto = "¡Feliz cumple, %s!" % persona_cumple
        m.texto(sy + 1, sx + (W - len(texto)) // 2, texto[:W - 2], color("Y"))


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
