"""Muebles y decoración de las salas.

Cada mueble: (nombre, arte, máscara de color, color por defecto, dx, sitio, día)
  dx    : columna dentro de la sala (negativo = desde la derecha)
  sitio : "suelo" (apoyado abajo) o "pared" (colgado arriba)
  día   : día del hormiguero en que aparece (0 = desde el principio)
Los ficheros de cada sala pueden añadir más con [[mueble]].
"""

ESCRITORIO = ("""
 ┌───┐
 └─┬─┘
╒══╧═══╕
│      │
""", """
 sssss
 ssCss
nnnnnnnn
n      n
""")
PLANTA_PEQUENA = (r"""
 ,
(_)
""", """
 g
nnn
""")
PLANTA = (r"""
\|/
(_)
""", """
GgG
nnn
""")
PLANTA_GRANDE = (r"""
\\|//
 \|/
 (_)
""", """
GgGgG
 GgG
 nnn
""")
CACTUS = (r"""
 _
(|)
|||
""", """
 G
GGG
nnn
""")
SOFA = ("""
▄▄▄▄▄▄▄▄
█▀▀▀▀▀▀█
""", """
rrrrrrrr
rrrrrrrr
""")
PIZARRA = ("""
┌────────────┐
│ ∑x² + ∫f dx│
│  P≠NP  ?   │
└────────────┘
""", """
wwwwwwwwwwwwww
wGGGGGGGGGGGGw
wGGGGGGGGGGGGw
wwwwwwwwwwwwww
""")
ESTANTERIA = ("""
┌─────┐
│▌▐▍▌▐│
│▍▌▐▌▍│
└─────┘
""", """
nnnnnnn
nRBYGMn
nGYRBCn
nnnnnnn
""")
RELOJ = ("◷", "W")
MESA_LARGA = ("""
════════════════
 ║            ║
""", """
nnnnnnnnnnnnnnnn
 n            n
""")
NEVERA = ("""
┌──┐
│ ▫│
├──┤
│ ▫│
│  │
└──┘
""", """
WWWW
WWsW
WWWW
WWsW
WWWW
WWWW
""")
MICROONDAS = ("""
┌────┐
│▤▤ ▫│
└────┘
▀▀▀▀▀▀
""", """
ssssss
sccsYs
ssssss
nnnnnn
""")
CAFETERA = ("""
┌┐
││▫
└┴c
""", """
kk
kkR
kkw
""")
FUENTE = ("""
 ╭─╮
 │░│
 ┌┴┐
 │▪│
 └─┘
""", """
 CCC
 CBC
 www
 wBw
 www
""")
CARTEL_PLANTA2 = ("""
┌──────────┐
│ PLANTA 2 │
└──────────┘
""", """
wwwwwwwwwwww
wwYYYYYYYYww
wwwwwwwwwwww
""")
VENTANA = ("""
┌─┬─┐
│ │ │
├─┼─┤
└─┴─┘
""", """
wwwww
wCwCw
wwwww
wwwww
""")
CAJAS = ("""
 ▐▀▌
▐▀▌▐▀▌
▐▄▌▐▄▌
""", """
 nnn
nnnnnn
nnnnnn
""")
SETAS = ("""
 ▄█▄  ▄▄  ▄█▄
  │   ││   │
""", """
 RWR  nn  RWR
  w   ww   w
""")
SACO = ("""
 ▄▄
(°°)
""", """
 yy
nyyn
""")

MESA_REUNIONES = ("""
╔════════════════╗
╚╤══════════════╤╝
 │              │
""", """
nnnnnnnnnnnnnnnnnn
nnnnnnnnnnnnnnnnnn
 n              n
""")
PANTALLA = ("""
┌──────────┐
│  ▁▃▅▇ %  │
└────┬─────┘
""", """
ssssssssssss
sCCCCCCCCCCs
ssssssssssss
""")
SILLON = ("""
 ▄▄▄
▐███▌
 ╨ ╨
""", """
 kkk
kkkkk
 sss
""")
ESCRITORIO_GRANDE = ("""
  ┌────┐
  └─┬──┘
╒═══╧══════╕
│          │
""", """
  ssssss
  ssCsss
nnnnnnnnnnnn
n          n
""")

# Muebles de las salas de trabajo (todas iguales)
TRABAJO = [
    ("un escritorio", *ESCRITORIO, "plata", 3, "suelo", 0),
    ("otro escritorio", *ESCRITORIO, "plata", 13, "suelo", 0),
    ("una plantita", *PLANTA_PEQUENA, "verde", -4, "suelo", 0),
    ("la plantita ha crecido", *PLANTA, "verde", -4, "suelo", 90),
    ("la planta ya es enorme", *PLANTA_GRANDE, "verde", -5, "suelo", 240),
]

# Muebles por defecto de cada sala (los ficheros de salas/ pueden añadir más)
POR_DEFECTO = {
    "reuniones": [
        ("la mesa de reuniones", *MESA_REUNIONES, "marron", 5, "suelo", 0),
        ("la pantalla", *PANTALLA, "plata", 8, "pared", 0),
    ],
    "despacho": [
        ("el escritorio", *ESCRITORIO_GRANDE, "plata", 3, "suelo", 0),
        ("el sillón", *SILLON, "negro", -7, "suelo", 0),
        ("una planta", *PLANTA, "verde", -3, "suelo", 60),
    ],
    "comedor": [
        ("la mesa", *MESA_LARGA, "marron", 9, "suelo", 0),
        ("la nevera", *NEVERA, "blanco", 2, "suelo", 0),
        ("el microondas", *MICROONDAS, "plata", -9, "suelo", 0),
        ("la cafetera", *CAFETERA, "negro", -3, "suelo", 0),
    ],
    "planta2": [
        ("la fuente de agua", *FUENTE, "cian", 4, "suelo", 0),
        ("el cartel", *CARTEL_PLANTA2, "blanco", 12, "pared", 0),
        ("una planta", *PLANTA, "verde", -5, "suelo", 0),
    ],
    "despensa": [("sacos", *SACO, "amarillo", 3, "suelo", 0), ("más sacos", *SACO, "amarillo", 8, "suelo", 60)],
    "hongos": [("setas", *SETAS, "rojo", 4, "suelo", 0)],
    "almacen": [("cajas", *CAJAS, "marron", 3, "suelo", 0)],
    "biblioteca": [("estantería", *ESTANTERIA, "marron", 2, "suelo", 0),
                   ("estantería", *ESTANTERIA, "marron", 11, "suelo", 0)],
}


def de_sala(sala):
    if sala.clave in POR_DEFECTO:
        return POR_DEFECTO[sala.clave]
    return TRABAJO if sala.principal else []
