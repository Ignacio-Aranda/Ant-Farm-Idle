"""Pixel art de bichos, comida y adornos. Todo mira a la derecha; la izquierda
se saca con espejo. Cada sprite: lista de filas y paleta {carácter: color}."""

import pygame

from .base import espejo, rejilla, superficie

# --------------------------------------------------------------- paletas comunes
NEGRO = (20, 18, 16)
BLANCO = (245, 245, 240)

CONEJO = {
    "pal": {"w": (196, 178, 156), "d": (150, 130, 110), "p": (230, 150, 160), "E": NEGRO,
            "n": (220, 120, 130), "T": BLANCO},
    "sentado": [
        "........ww...",
        ".......wpw...",
        ".......wpw...",
        "......wwwww..",
        ".....wwwwEwn.",
        ".wwwwwwwwwww.",
        "wwwwwwwwwdw..",
        "Twwwwwwwwdw..",
        ".dwwwwwwdd...",
        "..dd....dd...",
    ],
    "salto": [
        ".........ww..",
        "........wpw..",
        ".......wpw...",
        "......wwwwww.",
        "....wwwwwEwn.",
        ".wwwwwwwwwww.",
        "Twwwwwwwwdw..",
        ".wwwwwwwwd...",
        "dd.......dd..",
        "d.........d..",
    ],
    "come": [
        ".............",
        "......ww.....",
        "......wpw....",
        "......wpww...",
        ".wwwwwwwwww..",
        "wwwwwwwwwEw..",
        "Twwwwwwwwwwn.",
        ".wwwwwwwwd...",
        ".dwwwwwwdd...",
        "..dd....dd...",
    ],
}
PALOMA = {
    "pal": {"g": (150, 152, 165), "G": (95, 98, 120), "v": (90, 150, 120), "E": (230, 110, 40),
            "b": (220, 200, 180), "o": (210, 100, 100)},
    "quieta": [
        "......gg.",
        ".....gvEb",
        "....gvgg.",
        ".ggggggg.",
        "GGgggggg.",
        ".Gggggg..",
        "..o..o...",
    ],
    "come": [
        ".........",
        ".........",
        ".....gg..",
        ".gggggvg.",
        "GGggggvEb",
        ".Gggggg..",
        "..o..o...",
    ],
    "vuela": [
        "..gg.....",
        "...ggg.gg",
        ".gggggvEb",
        "GGgggggg.",
        "..ggg....",
        ".gg......",
        ".........",
    ],
}
GAVIOTA = {
    "pal": {"w": BLANCO, "g": (170, 175, 185), "y": (240, 200, 60), "k": NEGRO},
    "arriba": [
        "k.........k",
        "gw.......wg",
        ".gww...wwg.",
        "...wwwwwky.",
        ".....ww....",
    ],
    "abajo": [
        "...........",
        "....wwwwwky",
        "..gww.wwg..",
        ".gw.....wg.",
        "k.........k",
    ],
}
GATO = {
    "pal": {"c": (0, 0, 0), "d": (0, 0, 0), "E": (120, 220, 80), "n": (230, 140, 150)},
    "anda": [
        "..........c..c",
        "..........cccc",
        "c........cEcEc",
        ".c.......cccnc",
        "..cccccccccc..",
        "..ccccccccdc..",
        "..cdcccccccd..",
        "..c.d....c.d..",
        "..c.d....c.d..",
    ],
    "anda2": [
        "..........c..c",
        "..........cccc",
        ".c.......cEcEc",
        "c.c......cccnc",
        "..cccccccccc..",
        "..ccccccccdc..",
        "..cdcccccccd..",
        "...cd....dc...",
        "...cd....dc...",
    ],
    "sentado": [
        ".......c..c..",
        ".......cccc..",
        ".......cEcEc.",
        ".......cccnc.",
        "......cccccc.",
        ".....ccccccc.",
        "....cccccccc.",
        "c..ccccccccc.",
        ".ccccccccdcd.",
    ],
}
ABEJA = {
    "pal": {"y": (250, 210, 40), "k": NEGRO, "w": (220, 235, 255)},
    "a": [".ww..", "kykyk", ".kyk."],
    "b": ["..ww.", "kykyk", ".kyk."],
}
MARIPOSA = {
    "pal": {"a": (240, 160, 40), "b": (250, 230, 120), "k": NEGRO},
    "a": ["aa.aa", "abkba", ".aka.", "..k.."],
    "b": [".....", "aakaa", "bbkbb", "..k.."],
}
LAGARTIJA = {
    "pal": {"g": (110, 170, 70), "d": (70, 120, 50), "E": NEGRO},
    "a": [
        "............gg..",
        "dd.....gggggEgg.",
        "..ddggggggggg...",
        "......d...d.....",
    ],
}
CARACOL = {
    "pal": {"s": (170, 110, 60), "S": (120, 70, 40), "b": (200, 180, 140), "k": NEGRO},
    "a": [
        "..SSS...",
        ".SsssS.k",
        "SsSSsS.b",
        "SsSsSSbb",
        ".SSSSbbb",
        "bbbbbbb.",
    ],
}
ERIZO = {
    "pal": {"s": (110, 85, 60), "S": (70, 55, 40), "f": (190, 160, 120), "k": NEGRO},
    "a": [
        "..S.S.S.S..",
        ".SsSsSsSs..",
        "SsSsSsSsSff",
        "sSsSsSsSffk",
        ".sssssssff.",
        "..f.f..f.f.",
    ],
}
BUHO = {
    "pal": {"b": (140, 105, 70), "d": (95, 70, 45), "o": (250, 200, 40), "k": NEGRO, "y": (230, 170, 60)},
    "abierto": [
        "d.....d",
        "bbbbbbb",
        "bokbokb",
        "bbbybbb",
        "dbbbbbd",
        "dbdbdbd",
        ".bbbbb.",
        "..y.y..",
    ],
    "cerrado": [
        "d.....d",
        "bbbbbbb",
        "bdddddb",
        "bbbybbb",
        "dbbbbbd",
        "dbdbdbd",
        ".bbbbb.",
        "..y.y..",
    ],
}
MURCIELAGO = {
    "pal": {"k": (40, 30, 50), "r": (200, 40, 40)},
    "a": ["k..k.k..k", ".kkkkkkk.", "...krk...", "....k...."],
    "b": [".........", "..kkkkk..", "kkkkrkkkk", "k..kkk..k"],
}
GOLONDRINA = {
    "pal": {"k": (30, 35, 70), "w": BLANCO, "r": (190, 70, 50)},
    "a": ["k.......", ".kk..kkk", "..kkkkr.", "...ww..."],
    "b": ["........", ".kkkkkkk", "kk.kkkr.", "...ww..."],
}
AVION = {
    "pal": {"w": (230, 232, 240), "g": (150, 155, 170), "b": (60, 110, 200), "r": (220, 50, 50)},
    "a": [
        "w...............",
        "ww........gg....",
        "wwwwwwwwwwwwwwb.",
        ".gggggggggggggg.",
        "........gg......",
    ],
}
ARANA = {
    "pal": {"k": (35, 30, 30), "K": (70, 60, 60), "r": (220, 40, 40)},
    "a": [
        "..k.......k..",
        ".k..KKKKK..k.",
        "k..KKkkkKK..k",
        "kkkKkrkrkKkkk",
        "...kkKKKkk...",
        "..k.k...k.k..",
        ".k..k...k..k.",
    ],
    "b": [
        ".k.........k.",
        "k...KKKKK...k",
        ".k.KKkkkKK.k.",
        "..kKkrkrkKk..",
        "kkkkkKKKkkkkk",
        "...k.k.k.k...",
        "..k..k.k..k..",
    ],
}
GRILLO = {
    "pal": {"g": (90, 140, 50), "d": (55, 90, 30), "k": NEGRO},
    "a": [
        "......d....",
        "..dddd.d...",
        ".gggggggkg.",
        "ddgggggggg.",
        "..d..dd.d..",
        ".d..d..d...",
    ],
}
ORUGA = {
    "pal": {"g": (130, 190, 60), "d": (80, 130, 40), "k": NEGRO, "y": (240, 220, 80)},
    "a": ["...........", ".gdgdgdgdgk", "gdgdgdgdgdg", ".y.y.y.y.y."],
    "b": ["..gdg......", ".gd.gdgdgdk", "gd...dgdgdg", ".y...y.y.y."],
}
MOSCA = {
    "pal": {"k": (30, 30, 35), "w": (190, 210, 230), "r": (180, 40, 40)},
    "a": [".ww..", "kkkkr", ".k.k."],
    "b": ["ww...", "kkkkr", ".k.k."],
}
LOMBRIZ = {
    "pal": {"p": (220, 140, 150), "d": (180, 100, 110)},
    "a": ["..pp....pp..", ".pdpp..ppdp.", "pp..pppp..pp"],
    "b": [".pp......pp.", "pdpp....ppdp", "...pppppp..."],
}
ESCARABAJO = {
    "pal": {"b": (60, 40, 90), "B": (110, 80, 160), "k": NEGRO, "h": (180, 160, 230)},
    "a": [
        "...BBBB...",
        "..BbhbbBkk",
        ".BbbbbbBk.",
        ".bbbbbbbk.",
        "..k.k..k..",
        ".k..k...k.",
    ],
}
COCHINILLA = {
    "pal": {"g": (120, 120, 130), "G": (85, 85, 95), "k": NEGRO},
    "a": ["..GGGG..", ".GgGgGG.", "GgGgGgGk", ".k.k.k.."],
}
PAJARO = {
    "pal": {"b": (120, 85, 55), "d": (80, 55, 35), "w": (225, 215, 195), "y": (240, 180, 40), "k": NEGRO},
    "a": [
        "dd..........",
        ".dbb....bb..",
        "..dbbbbbbkby",
        "...bbbwwbbb.",
        "....bwwwbb..",
        ".....bbbd...",
        "......y.y...",
    ],
}

# --------------------------------------------------------------- comida
COMIDA = {
    "miga": ({"a": (230, 205, 150), "b": (200, 170, 110)}, ["ab", "ba"]),
    "semilla": ({"a": (150, 100, 50), "b": (110, 70, 35)}, [".a.", "aab", ".b."]),
    "azucar": ({"a": BLANCO, "b": (210, 210, 215)}, ["aab", "abb", "bbb"]),
    "higo": ({"a": (140, 60, 110), "b": (100, 40, 80), "g": (90, 140, 50)},
             ["..g..", ".aaa.", "aaaab", "aaabb", ".bbb."]),
    "almendra": ({"a": (190, 140, 90), "b": (150, 100, 60)}, [".aa.", "aaab", ".bb."]),
    "galleta": ({"a": (210, 160, 90), "b": (170, 120, 60), "c": (90, 55, 30)},
                [".aaaaaa.", "aacaacaa", "aaaaaaab", "acaacaab", ".abbbbb."]),
    "bocadillo": ({"a": (220, 170, 100), "b": (180, 130, 70), "r": (200, 60, 50), "g": (120, 180, 60),
                   "y": (240, 220, 120)},
                  [".aaaaaaaaaa.", "aaaaaaaaaaab", "rrgrrgyrrgrr", "bbbbbbbbbbbb", ".bbbbbbbbbb."]),
    "roja": ({"a": (150, 40, 30)}, ["aaaaaa"]),
}

# --------------------------------------------------------------- adornos
CALABAZA = ({"o": (240, 130, 30), "O": (200, 90, 20), "g": (90, 140, 50), "y": (255, 230, 90)},
            ["...g....", "..OoOo..", ".oOoOoO.", "oyoOoyoO", "oOyyyyOo", ".oOoOoO.", "..OoOo.."])
REGALO = ["..rr..", "bbrrbb", "bbrrbb", "rrrrrr", "bbrrbb", "bbrrbb"]
TARTA = ({"w": BLANCO, "p": (240, 160, 180), "r": (200, 60, 60), "c": (140, 80, 50), "y": (255, 220, 80)},
         ["..y..y..y...", "..w..w..w...", ".pppppppppp.", "pwpwpwpwpwpp", "pppppppppppp",
          "cccccccccccc", "crcrcrcrcrcc", "cccccccccccc"])
CORAZON = ({"r": (230, 40, 70), "w": (255, 150, 170)}, [".r.r.", "rwrrr", "rrrrr", ".rrr.", "..r.."])
TRONO = ({"y": (230, 190, 60), "Y": (180, 140, 40), "w": (255, 240, 180), "p": (120, 60, 140)},
         ["..w...w...w...w..", "..y...y...y...y..", "yyyyyyyyyyyyyyyyy", "YpppppppppppppppY",
          "YyyyyyyyyyyyyyyyY"])
CRUZ_MAYO = ({"r": (220, 40, 60), "p": (240, 150, 180), "y": (250, 220, 60), "g": (70, 140, 50)},
             ["...rpr...", "..rpypr..", "rprpypprp", "pypyyypyp", "rprpypprp", "..rpypr..",
              "...rpr...", "....g....", "....g...."])

# --------------------------------------------------------------- muebles y salas
# La Catedral de Málaga ("la Manquita"): una torre con su remate y la otra sin terminar.
CATEDRAL = [
    "....k..................",
    "...kkk.................",
    "...kkk.................",
    "..kkkkk................",
    "..kwkwk................",
    "..kkkkk................",
    ".kkkkkkk...............",
    ".kwkkkwk...............",
    ".kkkkkkk.......kkk.....",
    ".kkkkkkk......kkkkk....",
    ".kwkkkwk.kkk..kkkkk....",
    "kkkkkkkkkkkkkkkkkkkkk..",
    "kkkkkkkkkkkkkkkkkkkkkk.",
    "kkwkkkwkkkwwkkkwkkkwkk.",
    "kkwkkkwkkkwwkkkwkkkwkkk",
    "kkkkkkkkkkkkkkkkkkkkkkk",
]


def sprite(definicion, clave):
    return rejilla(definicion[clave], definicion["pal"])


def par(s):
    """(derecha, izquierda)"""
    return s, espejo(s)


def recolor(defi, cambios):
    pal = dict(defi["pal"])
    pal.update(cambios)
    d = dict(defi)
    d["pal"] = pal
    return d


def comida(clave):
    pal, filas = COMIDA[clave]
    return rejilla(filas, pal)


def regalo(color_caja, color_lazo):
    return rejilla(REGALO, {"b": color_caja, "r": color_lazo})


def simple(defi):
    pal, filas = defi
    return rejilla(filas, pal)


def globo(color):
    s = superficie(5, 9)
    pygame.draw.ellipse(s, color, (0, 0, 5, 6))
    s.set_at((1, 1), (255, 255, 255))
    pygame.draw.line(s, (200, 200, 200), (2, 6), (2, 8))
    return s
