"""La parte de arriba: cielo, tiempo, plantas, bichos, cementerio y fiestas."""

import math
import random

from motor.colores import color
from motor.sprites import construir, lineas, mascara_lineas, pintor_fijo

from . import decoracion as DE

# Lo que hay en la superficie si config.toml no dice nada (x en % del ancho)
SUELO_DEFECTO = [{"pieza": "chumbera", "x": 2}, {"pieza": "palmera", "x": 30}, {"pieza": "farola", "x": 42},
                 {"pieza": "olivo", "x": 49}, {"pieza": "almendro", "x": 89}]
FONDO_DEFECTO = [{"pieza": "catedral", "x": 58}]


def _sprite(arte, mascara=None, defecto="blanco", solido=False, extra=None):
    al = lineas(arte)
    return construir(al, mascara_lineas(mascara, len(al)), pintor_fijo(defecto, extra), solido)


# ------------------------------------------------------------------ dibujos

SOL = [r"""
 \ | /
-- O --
 / | \
""", r"""
  \ /
-  O  -
  / \
"""]
LUNAS = {
    "llena": " .--.\n(    )\n `--'",
    "creciente": " .-.\n(  _)\n `-'",
    "menguante": " .-.\n(_  )\n `-'",
    "nueva": "  .\n (  \n  '",
}
NUBES = [r"""
   .--.
.-(    ).
(___.__)__)
""", r"""
  .-~~-.
 (______)
""", r"""
      _
    _( )_
 .-(_    )-.
(___________)
"""]
CONEJO = [r"""
(\_/)
(o.o)
(")(")
""", r"""
(\_/)
(o.o)
/")(")
""", r"""
(\_/)
(-.-)
(")(")
"""]
CONEJO_MASC = """
wwwww
wwRww
wwwww
"""
CHUMBERA = r"""
   _   _
  ( ) ( )
 _( )_( )
( ) | |
 \_ |_|
    | |
"""
CHUMBERA_FRUTOS = [(0, 3), (0, 7), (1, 1), (2, 1)]
TRONCO = r"""
    )|(
    )|(
   /_|_\
"""
RAMAS = r"""
 \ \| |/ /
  \_\|/_/
    \|/
"""
# Copa del almendro: celdas que pueden tener flor u hoja
COPA = [
    "    .-~~~-.    ",
    "  (~ ~ ~ ~ ~)  ",
    " (~ ~ ~ ~ ~ ~) ",
    "  (~ ~ ~ ~ ~)  ",
    "    `~-.-~'    ",
]
COPA_ALMENDRO = [
    "      ######      ",
    "   ############   ",
    " ################ ",
    "##################",
    " ################ ",
    "  ######\\/######  ",
    "     ###\\/###     ",
]
TRONCO_ALMENDRO = [
    "        \\|/",
    "        )|(",
    "        )|(",
    "       /)|(\\",
    "      /_/ \\_\\",
]
RAMAS_ALMENDRO = [
    "  \\   \\  |  /   /",
    "   \\ \\  \\ | /  / /",
    "    \\_\\__\\|/__/_/",
    "         \\|/",
]
PALMERA = [
    " '._  \\ |  / _.' ",
    " _.-'\\ \\|/ /'-._ ",
    "'   _.-'|'-._   '",
    "   '   )|(    '  ",
    "       (|)       ",
    "       )|(       ",
    "       (|)       ",
    "       )|(       ",
    "       (|)       ",
    "      /)|(\\      ",
]
PALMERA_MASC = [
    " GGG  G G  G GGG ",
    " ggggG GgG Ggggg ",
    "g   gggggggg   g ",
    "   g   nNn    g  ",
    "       nNn       ",
    "       nNn       ",
    "       nNn       ",
    "       nNn       ",
    "       nNn       ",
    "      nnNnn      ",
]
COPA_OLIVO = [
    "   ########   ",
    " ############ ",
    "##############",
    " ############ ",
    "   ###\\/###   ",
]
TRONCO_OLIVO = [
    "     \\||",
    "      ||/",
    "      ||",
    "     /||\\",
    "    /_/\\_\\",
]
PINO_NAVIDAD = r"""
    *
   /o\
  /*o*\
 /o*o*o\
/*o*o*o*\
   |_|
"""
PINO_MASC = """
    Y
   gRg
  gYgBg
 gRgYgRg
gBgRgYgBg
   nnn
"""
CALABAZA = r"""
  ,
(^v^)
"""
CALABAZA_MASC = """
  g
OOOOO
"""
REGALO = r"""
 _\/_
[_##_]
"""
TARTA = r"""
 i i i
[~~~~~]
[_____]
"""
TARTA_MASC = """
 Y Y Y
pwwwwwp
nnnnnnn
"""
CRUZ_MAYO = r"""
  *@*
 *@+@*
  *@*
   |
"""
CRUZ_MASC = """
  RPR
 RPYPR
  RPR
   g
"""
HOGUERA = [r"""
  ) (
 ( ) )
(_)\_)
""", r"""
 ( )
( ( )
(_)\_)
"""]
HOGUERA_MASC = """
  Y R
 R O Y
nnnnnn
"""
TRONO = r"""
  i  i  i  i
 /==========\
 |  *    *  |
"""
TRONO_MASC = """
  Y  Y  Y  Y
 YYYYYYYYYYYY
 YY  O    O YY
"""
BANDERAS = {
    "andalucia": ["verde_brillante", "blanco_brillante", "verde_brillante"],
    "espana": ["rojo_brillante", "amarillo_brillante", "rojo_brillante"],
}


class Bicho:
    """Animal o cosa que cruza la superficie o el cielo."""

    def __init__(self, cuadros, x, y, vx, vy=0.0, fps=2.0, vida=None, saltos=False):
        self.cuadros, self.x, self.y, self.vx, self.vy = cuadros, x, y, vx, vy
        self.fps, self.vida, self.saltos = fps, vida, saltos
        self.t = 0.0
        self.vivo = True
        self.pausa = 0.0
        self.y0 = y

    def actualizar(self, m, dt):
        self.t += dt
        if self.pausa > 0:
            self.pausa -= dt
        else:
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.saltos:
                self.y = self.y0 - (1 if int(self.t * 3) % 2 else 0)
        if self.vida is not None and self.t > self.vida:
            self.vivo = False
        ancho = self.cuadros[0].ancho
        if self.x > m.ancho + 2 or self.x + ancho < -2 or self.y < -6:
            self.vivo = False

    def cuadro(self):
        if self.pausa > 0 and len(self.cuadros) > 2:
            return self.cuadros[2]
        return self.cuadros[int(self.t * self.fps) % min(2, len(self.cuadros))]

class Superficie:
    def __init__(self, m):
        self.m = m
        rng = random.Random("superficie-%s" % m.semilla)
        W = m.ancho
        self._leer_paisaje(m.cfg.get("paisaje", {}), W)
        self.hierba = "".join(rng.choice(",;'\".`,,") for _ in range(W))
        self.flores = []
        for _ in range(W // 5):
            x = rng.randrange(1, W - 1)
            self.flores.append((x, rng.random(), rng.random()))
        self.charcos = [rng.randrange(4, W - 6) for _ in range(5)]
        self.estrellas = [(rng.random(), rng.randrange(W), rng.uniform(0, 6.3), rng.uniform(0.5, 2))
                          for _ in range(W * 2)]
        self.nubes = []
        self.bichos = []
        self.particulas = []  # gotas, confeti, hojas: [x, y, vx, vy, char, color, vida]
        self.rng = random.Random()
        self.relampago = 0.0
        self.cuadros_conejo = [_sprite(a, CONEJO_MASC) for a in CONEJO]
        self.montes = DE.horizonte(W, rng)
        y0 = m.suelo_y - 1
        self.cima = [y0 - int(h) + 1 for h in self.montes]   # primera fila de montaña llena
        self.cima_min = min(self.cima)
        self.fondo_monte = None
        self.piedras = [(rng.randrange(2, W - 3), rng.choice(["◖◗", "◖▬◗", "°", "◦"]))
                        for _ in range(W // 16)]
        self.copa_rng = [[rng.random() for _ in range(20)] for _ in range(10)]
        self.copa_rng2 = [[rng.random() for _ in range(20)] for _ in range(10)]

    def _leer_paisaje(self, p, W):
        """[paisaje] de config.toml. Las x vienen en % del ancho y aquí pasan a columnas."""
        def piezas(lista):
            out = []
            for d in lista:
                try:
                    out.append((str(d["pieza"]).lower(), int(max(0.0, min(100.0, float(d.get("x", 50)))) / 100 * (W - 1))))
                except (KeyError, TypeError, ValueError):
                    self.m.avisos.append("paisaje: pieza mal escrita (%s)" % d)
            return out
        self.piezas_suelo = piezas(p.get("suelo", SUELO_DEFECTO))
        self.piezas_fondo = piezas(p.get("fondo", FONDO_DEFECTO))
        self.montes_lejos = bool(p.get("montes", True))
        self.costa = bool(p.get("costa", True))
        self.cementerio_x = int(max(0.0, min(100.0, float(p.get("cementerio", 74)))) / 100 * (W - 1))
        def primera(*nombres):
            return next((x for n in nombres for pieza, x in self.piezas_suelo if pieza == n), None)
        self.arbol_x = primera("almendro")                       # flores, hojas y almendras
        self.chumbera_x = primera("chumbera")                    # higos chumbos
        self.buho_x = primera("olivo", "pino", "almendro", "palmera")
        self.farolas = [x for pieza, x in self.piezas_suelo if pieza == "farola"]

    # -------------------------------------------------------------- lógica

    def actualizar(self, dt):
        m = self.m
        rng = self.rng
        W = m.ancho
        tiempo = m.tiempo_hoy
        # nubes según la nubosidad del día
        objetivo = int(tiempo.nubes * W / 30)
        if len(self.nubes) < objetivo and rng.random() < dt * 0.5:
            arte = rng.choice(NUBES)
            col = "s" if tiempo.llueve else "W"
            if m.de_noche:
                col = "gris_oscuro"
            c = _sprite(arte, None, col, solido=True)
            y = rng.randint(0, max(0, m.cielo_alto - 8))
            x = rng.uniform(0, W) if not self.nubes and m.t < 1 else W + 1
            self.nubes.append(Bicho([c], x, y, -rng.uniform(0.4, 1.2)))
        for n in self.nubes:
            n.actualizar(m, dt)
        self.nubes = [n for n in self.nubes if n.vivo]

        # lluvia
        lluvia = m.lluvia
        if lluvia > 0:
            n = int(lluvia * W / 4 * dt * 12)
            viento = -6 if tiempo.tormenta else -2
            for _ in range(n):
                self.particulas.append([rng.uniform(0, W + 10), rng.uniform(-1, 2), viento,
                                        rng.uniform(18, 26), "/" if tiempo.tormenta else "|",
                                        color("c" if not m.de_noche else "b"), 3.0])
            if tiempo.tormenta and rng.random() < dt * 0.05:
                self.relampago = 0.25
        self.relampago = max(0.0, self.relampago - dt)

        # bichos
        self._bichos(dt)
        for b in self.bichos:
            b.actualizar(m, dt)
        self.bichos = [b for b in self.bichos if b.vivo]

        # hojas de otoño cayendo del almendro
        dia_año = m.ahora.timetuple().tm_yday
        if self.arbol_x is not None and 274 <= dia_año <= 335 and rng.random() < dt * 0.4:
            self.particulas.append([self.arbol_x + rng.uniform(-8, 8), m.suelo_y - 7, rng.uniform(-1, 1),
                                    1.5, rng.choice("',`"), color(rng.choice(["o", "y", "n"])), 8])
        # pétalos del almendro en flor
        if self.arbol_x is not None and 20 <= dia_año <= 64 and rng.random() < dt * 0.3:
            self.particulas.append([self.arbol_x + rng.uniform(-8, 8), m.suelo_y - 7, rng.uniform(-1.5, 0.5),
                                    1.2, ".", color(rng.choice(["P", "W"])), 10])
        # confeti, corazones, chispas de fiestas
        deco = m.decoraciones
        if "carnaval" in deco and rng.random() < dt * 4:
            self.particulas.append([rng.uniform(0, W), 0, rng.uniform(-1, 1), rng.uniform(2, 4),
                                    rng.choice("*.,'~"), color(rng.choice("RYGBMCO")), 12])
        if "corazones" in deco and rng.random() < dt * 0.8:
            self.particulas.append([rng.uniform(0, W), m.suelo_y - 1, rng.uniform(-0.5, 0.5), -1.5,
                                    "♥" if m.unicode else "<3", color("R"), 8])
        if "nochevieja" in deco and m.de_noche and rng.random() < dt * 0.7:
            self._fuego_artificial()
        for p in self.particulas:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[6] -= dt
        suelo = m.suelo_y
        self.particulas = [p for p in self.particulas if p[6] > 0 and p[1] < suelo and p[1] > -3]

    def _fuego_artificial(self):
        m, rng = self.m, self.rng
        cx, cy = rng.uniform(10, m.ancho - 10), rng.uniform(2, max(3, m.cielo_alto - 8))
        col = color(rng.choice("RYGBMCW"))
        for k in range(14):
            a = k / 14 * 2 * math.pi
            v = rng.uniform(4, 7)
            self.particulas.append([cx, cy, math.cos(a) * v * 2, math.sin(a) * v, "*", col, 1.2])

    def _bichos(self, dt):
        m, rng = self.m, self.rng
        W = m.ancho
        hay = {getattr(b, "tipo", "") for b in self.bichos}
        mes = m.ahora.month
        hora = m.ahora.hour + m.ahora.minute / 60
        a, p = m.sol_hoy
        crepusculo = abs(hora * 60 - a) < 90 or abs(hora * 60 - p) < 90
        # conejo: más al amanecer y al atardecer, nunca con lluvia fuerte
        if "conejo" not in hay and m.lluvia < 0.3:
            prob = (1 / 120) if crepusculo else (1 / 600 if not m.de_noche else 1 / 900)
            if rng.random() < dt * prob:
                der = rng.random() < 0.5
                b = Bicho(self.cuadros_conejo, -6 if der else W + 1, m.suelo_y - 3,
                          (1 if der else -1) * rng.uniform(4, 6), fps=3, saltos=True)
                b.tipo = "conejo"
                self.bichos.append(b)
        for b in self.bichos:
            if getattr(b, "tipo", "") == "conejo" and b.pausa <= 0 and rng.random() < dt * 0.08:
                b.pausa = rng.uniform(2, 6)  # se para a comer
        # golondrinas de marzo a septiembre, de día
        if 3 <= mes <= 9 and not m.de_noche and m.lluvia == 0 and rng.random() < dt / 40:
            der = rng.random() < 0.5
            for k in range(rng.randint(1, 3)):
                c = [_sprite("\\v/", None, "k"), _sprite("-v-", None, "k")]
                b = Bicho(c, (-4 - k * 5) if der else (W + k * 5), rng.uniform(1, m.cielo_alto - 6),
                          (1 if der else -1) * rng.uniform(12, 16), rng.uniform(-0.5, 0.5), fps=5)
                b.tipo = "pajaro"
                self.bichos.append(b)
        # mariposas en primavera
        if 3 <= mes <= 6 and not m.de_noche and m.lluvia == 0 and "mariposa" not in hay \
                and rng.random() < dt / 60:
            col = rng.choice(["Y", "P", "C", "W"])
            c = [_sprite("}{", None, col), _sprite(")(", None, col)]
            der = rng.random() < 0.5
            b = Bicho(c, -3 if der else W + 1, m.suelo_y - rng.uniform(3, 8),
                      (1 if der else -1) * rng.uniform(2, 4), rng.uniform(-0.3, 0.3), fps=4)
            b.tipo = "mariposa"
            self.bichos.append(b)
        # lagartija en días de calor y sol
        if m.temperatura > 20 and not m.de_noche and "lagartija" not in hay and rng.random() < dt / 150:
            der = rng.random() < 0.5
            c = [_sprite("~-=:>" if der else "<:=-~", None, "verde_brillante")]
            b = Bicho(c, -6 if der else W + 1, m.suelo_y, (1 if der else -1) * rng.uniform(5, 9))
            b.tipo = "lagartija"
            self.bichos.append(b)
        # caracol después de llover
        if m.llovio and m.lluvia < 0.2 and "caracol" not in hay and rng.random() < dt / 100:
            der = rng.random() < 0.5
            c = [_sprite("_@)" if der else "(@_", None, "marron")]
            b = Bicho(c, rng.uniform(5, W - 5), m.suelo_y, (1 if der else -1) * 0.25, vida=240)
            b.tipo = "caracol"
            self.bichos.append(b)
        # murciélagos en noches de verano
        if 5 <= mes <= 9 and m.de_noche and m.lluvia == 0 and rng.random() < dt / 50:
            c = [_sprite("/^v^\\", None, "s"), _sprite("\\^v^/", None, "s")]
            der = rng.random() < 0.5
            b = Bicho(c, -6 if der else W + 1, rng.uniform(1, m.cielo_alto - 4),
                      (1 if der else -1) * rng.uniform(8, 12), rng.uniform(-1, 1), fps=6)
            b.tipo = "murcielago"
            self.bichos.append(b)
        uni = m.unicode
        dia_claro = not m.de_noche and m.lluvia == 0
        # gaviotas (si hay costa cerca)
        if self.costa and dia_claro and rng.random() < dt / 45:
            der = rng.random() < 0.5
            for k in range(rng.randint(1, 3)):
                c = [_sprite("‿v‿" if uni else "~v~", None, "W"), _sprite("⌒v⌒" if uni else "^v^", None, "W")]
                b = Bicho(c, (-5 - k * 7) if der else (W + k * 7), rng.uniform(4, m.cielo_alto - 8),
                          (1 if der else -1) * rng.uniform(7, 10), rng.uniform(-0.4, 0.4), fps=2.5)
                b.tipo = "gaviota"
                self.bichos.append(b)
        # un avión que va o viene del aeropuerto (de noche, con luces)
        if "avion" not in hay and rng.random() < dt / 150:
            der = rng.random() < 0.5
            arte = ("━━╸✈" if der else "✈╺━━") if uni else ("--=>" if der else "<=--")
            b = Bicho([_sprite(arte, None, "plata")], -8 if der else W + 2, rng.uniform(5, 8),
                      (1 if der else -1) * 14)
            b.tipo = "avion"
            self.bichos.append(b)
        # palomas picoteando en grupo
        if dia_claro and "paloma" not in hay and rng.random() < dt / 90:
            x = rng.uniform(30, W - 30)
            for k in range(rng.randint(3, 5)):
                der = rng.random() < 0.5
                c = [_sprite("(o>" if der else "<o)", None, "plata"),
                     _sprite("(o." if der else ".o)", None, "plata")]
                b = Bicho(c, x + k * 4 + rng.uniform(-1, 1), m.suelo_y - 1, 0, fps=rng.uniform(1, 3),
                          vida=rng.uniform(60, 150))
                b.tipo = "paloma"
                self.bichos.append(b)
        # el gato del barrio: pasea, se sienta y espanta a las palomas
        if dia_claro and "gato" not in hay and rng.random() < dt / 300:
            der = rng.random() < 0.5
            col = rng.choice(["naranja", "negro_brillante", "plata", "blanco_brillante"])
            arte = ["  /\\_/\\ ", "~(=^.^=)"] if der else [" /\\_/\\  ", "(=^.^=)~"]
            c = [_sprite("\n".join(arte), None, col)]
            b = Bicho(c, -9 if der else W + 1, m.suelo_y - 2, (1 if der else -1) * 3, fps=1)
            b.tipo = "gato"
            self.bichos.append(b)
        for g in self.bichos:
            if getattr(g, "tipo", "") == "gato":
                if g.pausa <= 0 and rng.random() < dt * 0.05:
                    g.pausa = rng.uniform(4, 12)  # se sienta a mirar
                for p in self.bichos:
                    if getattr(p, "tipo", "") == "paloma" and abs(p.x - g.x) < 14 and p.vy == 0:
                        p.vy = -rng.uniform(4, 7)  # ¡salen volando!
                        p.vx = rng.choice([-1, 1]) * rng.uniform(5, 9)
                        p.cuadros = [_sprite("\\v/", None, "plata"), _sprite("-v-", None, "plata")]
                        p.fps = 6
        # abejas en las flores (primavera y verano)
        if dia_claro and 3 <= mes <= 8 and len([b for b in self.bichos if getattr(b, "tipo", "") == "abeja"]) < 3 \
                and rng.random() < dt / 20:
            x, _, _ = rng.choice(self.flores)
            b = Bicho([_sprite("ʚ●ɞ" if uni else "o", None, "amarillo_brillante")], x, m.suelo_y - 2, 0,
                      vida=rng.uniform(20, 50))
            b.tipo = "abeja"
            b.x0 = x
            self.bichos.append(b)
        for b in self.bichos:
            if getattr(b, "tipo", "") == "abeja":
                b.x = b.x0 + math.sin(b.t * 2.3) * 4 + math.sin(b.t * 0.7) * 3
                b.y = m.suelo_y - 2 - abs(math.sin(b.t * 1.7)) * 2
        # erizo de noche
        if m.de_noche and m.lluvia == 0 and "erizo" not in hay and rng.random() < dt / 400:
            der = rng.random() < 0.5
            arte = "⌒⌒⌒°>" if der else "<°⌒⌒⌒"
            if not uni:
                arte = "^^^o>" if der else "<o^^^"
            b = Bicho([_sprite(arte, None, "marron")], -6 if der else W + 1, m.suelo_y,
                      (1 if der else -1) * 1.5)
            b.tipo = "erizo"
            self.bichos.append(b)
        if "halloween" in m.decoraciones and m.de_noche and rng.random() < dt / 8:
            c = [_sprite("/^v^\\", None, "M"), _sprite("\\^v^/", None, "M")]
            b = Bicho(c, rng.choice([-6, W + 1]), rng.uniform(1, m.cielo_alto - 4), 0, fps=6)
            b.vx = 10 if b.x < 0 else -10
            b.vy = rng.uniform(-1, 1)
            self.bichos.append(b)

    # ------------------------------------------------------------- dibujo

    def _alto_monticulo(self):
        return min(3, 1 + self.m.plan.total_cavado() // 600)
