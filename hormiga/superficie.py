"""La parte de arriba: cielo, tiempo, plantas, bichos, cementerio y fiestas."""

import datetime
import math
import random

from motor import fuente
from motor.colores import Fondo, color
from motor.sprites import construir, lineas, mascara_lineas, pintor_fijo

from . import decoracion as DE
from . import tiempo as T


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

    def dibujar(self, m):
        m.blit(self.cuadro(), self.x, self.y)


class Superficie:
    def __init__(self, m):
        self.m = m
        rng = random.Random("superficie-%s" % m.semilla)
        W = m.ancho
        self.arbol_x = int(W * 0.84)
        self.palmera_x = int(W * 0.27)
        self.olivo_x = int(W * 0.45)
        self.chumbera_x = 2
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
        self.catedral_x = int(W * 0.56)
        self.farola_x = int(W * 0.42)
        self.piedras = [(rng.randrange(2, W - 3), rng.choice(["◖◗", "◖▬◗", "°", "◦"]))
                        for _ in range(W // 16)]
        self.copa_rng = [[rng.random() for _ in range(20)] for _ in range(10)]
        self.copa_rng2 = [[rng.random() for _ in range(20)] for _ in range(10)]

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
        if 274 <= dia_año <= 335 and rng.random() < dt * 0.4:
            self.particulas.append([self.arbol_x + rng.uniform(1, 17), m.suelo_y - 7, rng.uniform(-1, 1),
                                    1.5, rng.choice("',`"), color(rng.choice(["o", "y", "n"])), 8])
        # pétalos del almendro en flor
        if 20 <= dia_año <= 64 and rng.random() < dt * 0.3:
            self.particulas.append([self.arbol_x + rng.uniform(1, 17), m.suelo_y - 7, rng.uniform(-1.5, 0.5),
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
        # gaviotas (Málaga es costa)
        if dia_claro and rng.random() < dt / 45:
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

    def dibujar_cielo(self):
        m = self.m
        poner = m.pantalla.poner
        W = m.ancho
        f = m.fondo_cielo
        if self.relampago > 0:
            f = Fondo(250, 7)
        if f is not None:
            for y in range(m.suelo_y):
                poner(y, 0, " " * W, color("blanco"), f)
        # estrellas
        if m.de_noche and m.tiempo_hoy.nubes < 0.7:
            for prof, x, fase, vel in self.estrellas:
                y = int(prof * (m.cielo_alto - 4))
                b = math.sin(m.t * vel + fase)
                if b > -0.3 and (x + y) % 3 == 0:
                    ch = "*" if b > 0.85 else "+" if b > 0.55 else "."
                    m.texto(y, x, ch, color("W" if b > 0.55 else "s"), f)
        self._astro(f)
        for n in self.nubes:
            n.dibujar(m)
        self._montes(f)
        if m.decoraciones:
            self._deco_cielo()

    def _montes(self, f):
        """Los Montes de Málaga al fondo, con la Catedral (la Manquita).
        Con 256 colores la montaña es un fondo: lo que se dibuja delante la respeta."""
        m = self.m
        y0 = m.suelo_y - 1
        num = 23 if not m.de_noche else 235
        if m.tiempo_hoy.calima and not m.de_noche:
            num = 95
        self.fondo_monte = Fondo(num, -1) if f is not None else None
        col = color(num)
        bloques = " ▁▂▃▄▅▆▇" if m.unicode else "  ..::##"
        for x, h in enumerate(self.montes):
            top = self.cima[x]
            if self.fondo_monte is not None:
                for yy in range(top, y0 + 1):
                    m.pantalla.poner(yy, x, " ", col, self.fondo_monte)
            else:
                for yy in range(top, y0 + 1):
                    m.texto(yy, x, "█" if m.unicode else "#", col, f)
            idx = int((h - int(h)) * (len(bloques) - 1))
            if idx and top - 1 >= 0:
                m.pantalla.poner(top - 1, x, bloques[idx], col, f)
        dibujo = DE.CATEDRAL if m.unicode else DE.CATEDRAL_ASCII
        cx = self.catedral_x
        base = self.cima[min(cx, len(self.cima) - 1)] - 1
        ccol = color(101 if not m.de_noche else 238)
        for k, fila in enumerate(dibujo):
            yy = base - len(dibujo) + 1 + k
            for i, ch in enumerate(fila):
                if ch != " ":
                    m.texto(yy, cx + i, ch, ccol)
        if m.de_noche:  # ventanitas encendidas
            m.texto(base - 1, cx + 3, "▪" if m.unicode else ".", color("amarillo"))
            m.texto(base - 3, cx + 3, "▪" if m.unicode else ".", color("amarillo"))

    def _farola(self, y):
        m = self.m
        x = self.farola_x
        uni = m.unicode
        encendida = m.de_noche
        m.texto(y - 5, x - 1, "▄█▄" if uni else "_#_", color("amarillo_brillante" if encendida else "gris"))
        for k in range(1, 5):
            m.texto(y - 5 + k, x, "║" if uni else "|", color("gris_oscuro"))
        m.texto(y, x - 1, "▀▀▀" if uni else "===", color("gris_oscuro"))
        if encendida:
            for dx, dy in ((-2, -4), (2, -4), (-3, -3), (3, -3)):
                m.texto(y - 5 + dy + 4, x + dx, "·", color("amarillo"))

    def _astro(self, f):
        m = self.m
        a, p = m.sol_hoy
        mins = m.ahora.hour * 60 + m.ahora.minute
        alto = max(1, m.cielo_alto - 10)
        if not m.de_noche:
            fr = (mins - a) / max(1, p - a)
            arte = SOL[int(m.t * 1.5) % 2]
            col = "naranja" if m.tiempo_hoy.calima else "amarillo_brillante"
        else:
            noche = 24 * 60 - p + a
            fr = ((mins - p) % (24 * 60)) / max(1, noche)
            fase = T.fase_lunar(m.ahora.date())
            if fase < 0.04 or fase > 0.96:
                arte = LUNAS["nueva"]
            elif fase < 0.45:
                arte = LUNAS["creciente"]
            elif fase < 0.55:
                arte = LUNAS["llena"]
            else:
                arte = LUNAS["menguante"]
            col = "W"
        if m.tiempo_hoy.nubes > 0.85 or m.lluvia > 0:
            return  # cubierto
        fr = max(0.0, min(1.0, fr))
        cu = _sprite(arte, None, col)
        x = 2 + fr * (m.ancho - 12)
        y = round((1 - math.sin(math.pi * fr)) * alto)
        m.blit(cu, x, y)

    def _deco_cielo(self):
        m = self.m
        W = m.ancho
        deco = m.decoraciones
        if "feria" in deco or "banderines" in deco or "navidad" in deco or "andalucia" in deco:
            # guirnalda colgando de lado a lado (farolillos, banderines o luces)
            if "feria" in deco:
                chars, cols = "o", ["R", "W", "G", "Y", "R", "W"]
            elif "navidad" in deco:
                chars, cols = "*", ["R", "Y", "G", "B", "W"]
            elif "andalucia" in deco:
                chars, cols = "v", ["G", "W"]
            else:
                chars, cols = "v", ["R", "Y", "G", "B", "M", "C"]
            reloj = W - 30  # no tapar la hora grande de arriba a la derecha
            for x in range(0, reloj, 3):
                y = 3 + int(2 * math.sin(math.pi * (x % 40) / 40))
                k = x // 3
                if "navidad" in deco and int(m.t * 2 + k) % 3 == 0:
                    continue  # luces que parpadean
                m.texto(y, x, chars, color(cols[k % len(cols)]), m.fondo_cielo)
        if "pi" in deco:
            m.texto(7, W // 2 - 8, "π = 3,14159265...", color("Y"), m.fondo_cielo)

    def dibujar_suelo(self):
        """Hierba, plantas, decoración y bichos (lo que está a ras de suelo)."""
        m = self.m
        W = m.ancho
        y = m.suelo_y
        est = T.estacion(m.ahora.date())
        dia_año = m.ahora.timetuple().tm_yday
        # charcos tras la lluvia
        verde = {"invierno": "verde", "primavera": "verde_brillante",
                 "verano": "amarillo", "otoño": "verde"}[est]
        hierba_col = color(verde)
        seca = color("marron")
        linea = self.hierba
        for x0 in range(0, W, 40):
            trozo = linea[x0:x0 + 40]
            m.texto(y, x0, trozo, hierba_col if (est != "verano" or x0 % 80) else seca)
        if m.llovio:
            for cx in self.charcos:
                m.texto(y, cx, "~~~~", color("B"))
        # el viento mueve la hierba (una ola que recorre el suelo)
        ola = int(m.t * 6) % (W + 40) - 20
        for dx in range(-6, 7):
            x = ola + dx
            if 0 <= x < W and (x * 3) % 4 == 0:
                m.texto(y, x, "/" if dx < 0 else "\\", hierba_col)
        # hierba alta en primavera
        if est == "primavera" or (est == "invierno" and m.ahora.month in (2, 3)):
            for x, a, b in self.flores[::2]:
                m.texto(y - 1, x, "\\|/" if a > 0.5 else "|/", color("verde"))
        for px, piedra in self.piedras:
            m.texto(y, px, piedra if m.unicode else "o", color("gris"))
        self._farola(y)
        self._flores(y, dia_año, est)
        self._palmera(y, dia_año)
        self._olivo(y, dia_año)
        self._nocturnos(y)
        self._almendro(y, dia_año)
        self._chumbera(y, dia_año)
        self._montones(y)
        self._cementerio(y)
        self._deco_suelo(y)
        self._cumples(y)
        # terral: el aire caliente tiembla
        if m.tiempo_hoy.terral and not m.de_noche:
            for x in range(int(m.t * 3) % 6, W, 6):
                m.texto(y - 2, x, "~", color("amarillo"))

    def _flores(self, y, dia, est):
        m = self.m
        for x, a, b in self.flores:
            if 60 <= dia <= 151 and a < 0.35:          # amapolas: marzo-mayo
                m.texto(y - 1, x, "*", color("R"))
            elif 15 <= dia <= 90 and a > 0.75:         # jaramagos amarillos: invierno-primavera
                m.texto(y - 1, x, "*", color("Y"))
            elif 32 <= dia <= 120 and 0.55 < a < 0.65:  # margaritas
                m.texto(y - 1, x, "*", color("W"))
            elif 182 <= dia <= 243 and a < 0.12:       # biznagas (jazmín) en verano
                m.texto(y - 1, x, "✿" if m.unicode else "*", color("W"))
            elif 280 <= dia <= 350 and a < 0.2 and m.llovio_semana:  # setas en otoño
                m.texto(y - 1, x, "n" if b < 0.5 else "T", color("rojo" if b < 0.3 else "arena"))

    def _copa(self, mascara, x0, y0, rnd, hoja):
        """Rellena una copa: '#' son celdas de hoja; hoja(v) -> (carácter, color) o None."""
        m = self.m
        for r, fila in enumerate(mascara):
            for c, ch in enumerate(fila):
                if ch == " ":
                    continue
                if ch == "#":
                    res = hoja(rnd[r][c], rnd[(r + 3) % 10][(c + 7) % 20])
                    if res:
                        m.texto(y0 + r, x0 + c, res[0], color(res[1]))
                else:
                    m.texto(y0 + r, x0 + c, ch, color("marron"))

    def _almendro(self, y, dia):
        m = self.m
        x0 = self.arbol_x
        if x0 + 18 > m.ancho:
            return
        uni = m.unicode
        for k, fila in enumerate(TRONCO_ALMENDRO):
            m.texto(y - len(TRONCO_ALMENDRO) + 1 + k, x0, fila, color("marron"))
        top = y - len(TRONCO_ALMENDRO) - len(COPA_ALMENDRO) + 1
        if dia < 20 or dia > 335:  # invierno: ramas desnudas
            for k, fila in enumerate(RAMAS_ALMENDRO):
                m.texto(top + 3 + k, x0, fila, color("marron"))
            return
        if dia <= 64:
            def hoja(v, w):
                if v > 0.92:
                    return None
                return ("✿" if uni and w < 0.25 else "*" if w < 0.6 else "•",
                        "P" if v < 0.45 else "W" if v < 0.8 else "rosa")
        elif dia <= 273:
            def hoja(v, w):
                if v > 0.95:
                    return None
                ch = "♣" if uni and w < 0.15 else "@" if w < 0.5 else "&" if w < 0.8 else "%"
                return ch, "verde" if v < 0.4 else "G" if v < 0.7 else 28
        else:
            dens = max(0.15, 0.9 - (dia - 273) / 70)
            def hoja(v, w):
                if v > dens:
                    return None
                return ("&" if w < 0.6 else "*"), ("o" if v < 0.35 else "y" if v < 0.65 else "n")
        self._copa(COPA_ALMENDRO, x0, top, self.copa_rng, hoja)
        if 65 <= dia <= 180 and not m.de_noche:  # mariquitas
            for k, (fx, fy) in enumerate(((4, 2), (12, 3), (8, 4))):
                if int(m.t / 7 + k) % 3:
                    m.texto(top + fy, x0 + fx, "●" if uni else "o", color("rojo_brillante"))
        if "halloween" in m.decoraciones:
            m.texto(top + 2, x0 + 14, "/\\/\\" if not uni else "╱╲╱╲", color("s"))

    def _palmera(self, y, dia):
        m = self.m
        x0 = m.salidas_x[0] + 22  # a la derecha de la entrada (y del árbol de Navidad)
        alto = len(PALMERA)
        for k, (fila, masc) in enumerate(zip(PALMERA, PALMERA_MASC)):
            for c, ch in enumerate(fila):
                if ch != " ":
                    col = {"g": "verde", "G": "verde_brillante", "n": "marron", "N": 94}.get(masc[c], "verde")
                    m.texto(y - alto + 1 + k, x0 + c, ch, color(col))
        if 213 <= dia <= 300:  # dátiles a final de verano
            m.texto(y - alto + 4, x0 + 6, "•••" if m.unicode else "ooo", color("naranja"))

    def _olivo(self, y, dia):
        m = self.m
        x0 = self.olivo_x
        uni = m.unicode
        for k, fila in enumerate(TRONCO_OLIVO):
            m.texto(y - len(TRONCO_OLIVO) + 1 + k, x0, fila, color(94))
        top = y - len(TRONCO_OLIVO) - len(COPA_OLIVO) + 1
        aceitunas = dia >= 274 or dia <= 31

        def hoja(v, w):
            if v > 0.9:
                return None
            if aceitunas and w < 0.12:
                return ("●" if uni else "o"), ("morado" if v < 0.5 else "negro_brillante")
            return ("°" if w < 0.4 else "•" if w < 0.7 else "o"), (101 if v < 0.4 else 65 if v < 0.75 else "verde")
        self._copa(COPA_OLIVO, x0, top, self.copa_rng2, hoja)

    def _nocturnos(self, y):
        """Búho en el olivo y luciérnagas en las noches de verano."""
        m = self.m
        if not m.de_noche:
            return
        hoy = m.ahora.date()
        if random.Random("buho-%s" % hoy).random() < 0.6:
            ojos = "(◉v◉)" if m.unicode else "(OvO)"
            if int(m.t * 1.3) % 9 == 0:
                ojos = "(-v-)"
            m.texto(y - len(TRONCO_OLIVO) - len(COPA_OLIVO) + 2, self.olivo_x + 5, ojos, color("arena"))
        if 6 <= m.ahora.month <= 8 and m.lluvia == 0:
            r = random.Random("luciernagas-%s" % hoy)
            for k in range(10):
                bx = r.uniform(0, m.ancho) + math.sin(m.t * 0.3 + k) * 6
                by = y - 1 - r.uniform(0, 5) + math.sin(m.t * 0.5 + k * 2) * 1.5
                if math.sin(m.t * 2 + k * 1.7) > 0.2:
                    m.texto(by, bx, "·" if m.unicode else ".", color("lima"))

    def _chumbera(self, y, dia):
        m = self.m
        x0 = self.chumbera_x
        cu = _sprite(CHUMBERA, None, "verde")
        m.blit(cu, x0, y - cu.alto)
        if 182 <= dia <= 273:
            for r, c in CHUMBERA_FRUTOS:
                m.texto(y - cu.alto + r, x0 + c, "o", color("R"))

    def _alto_monticulo(self):
        return min(3, 1 + self.m.plan.total_cavado() // 600)

    def _montones(self, y):
        """Montículo de tierra en cada salida: una cúpula baja y granulada con
        el agujero de la entrada en el centro (crece con la tierra que sacan)."""
        m = self.m
        uni = m.unicode
        alto = self._alto_monticulo()
        grano = "·∙:" if uni else ".:'"
        for n, sx in enumerate(m.salidas_x):
            h = alto if n == 0 else max(1, alto - 1)
            base = 9 + 4 * h
            for k in range(h):
                fila = y - 1 - k
                ancho = base - 4 * k - (2 if k == h - 1 and h > 1 else 0)
                x0 = sx - ancho // 2
                for i in range(ancho):
                    x = x0 + i
                    if i == 0:
                        ch = "(" if k < h - 1 else "."
                    elif i == ancho - 1:
                        ch = ")" if k < h - 1 else "."
                    elif k == h - 1:
                        ch = "-" if (i % 3) else "~"
                    else:
                        ch = grano[(x * 7 + k * 3) % len(grano)]
                    col = "arena" if ch in grano and (x + k) % 3 == 0 else "marron"
                    m.texto(fila, x, ch, color(col))
            # el agujero de la entrada, a ras de suelo
            m.texto(y - 1, sx - 1, "◖ ◗" if uni else "( )", color(94))
            m.texto(y - 1, sx, " ", color("negro"))
        sx = m.salidas_x[0]
        bandera = None
        for clave in ("andalucia", "espana"):
            if clave in m.decoraciones:
                bandera = BANDERAS[clave]
        if bandera:
            top = y - 1 - alto
            for k, col in enumerate(bandera):
                m.texto(top - 3 + k, sx + 1, "▬▬▬▬" if uni else "####", color(col))
            for k in range(4):
                m.texto(top - 3 + k, sx, "|", color("plata"))

    def _cementerio(self, y):
        m = self.m
        idos = m.idos
        if not idos:
            return
        anchos = [max(5, len(n) + 2) for n in idos]
        total = sum(anchos) + len(anchos) + 3
        x = self.arbol_x - total - 3
        if x < m.salidas_x[0] + 6:
            x = m.salidas_x[0] + 6
        m.texto(y - 4, x, "R.I.P.".center(total), color("s"))
        m.texto(y - 1, x, "+" + "-+" * (total // 2), color("marron"))
        cx = x + 2
        for nombre, w in zip(idos, anchos):
            m.texto(y - 3, cx, "." + "-" * (w - 2) + ".", color("gris"))
            m.texto(y - 2, cx, "|" + nombre.center(w - 2) + "|", color("blanco"))
            m.texto(y - 1, cx, "|" + "_" * (w - 2) + "|", color("gris"))
            if "difuntos" in m.decoraciones:
                m.texto(y - 4, cx + w // 2, "i", color("Y" if int(m.t * 4 + cx) % 2 else "o"))
                m.texto(y, cx, "@", color("R"))
            if "halloween" in m.decoraciones and m.de_noche and int(m.t / 6) % len(idos) == idos.index(nombre):
                m.texto(y - 6 - int(m.t * 2) % 2, cx + 1, "(o o)", color("W"))
            cx += w + 1

    def _deco_suelo(self, y):
        m = self.m
        deco = m.decoraciones
        W = m.ancho
        sx = m.salidas_x[0]
        if "navidad" in deco or "reyes" in deco:
            pino = _sprite(PINO_NAVIDAD, PINO_MASC, "verde")
            m.blit(pino, sx + 11, y - pino.alto)
            if "reyes" in deco:
                regalo = _sprite(REGALO, None, "R", extra={})
                for k, col in enumerate(["R", "Y", "B"]):
                    m.blit(_sprite(REGALO, None, col), sx + 20 + k * 7, y - 2)
        if "halloween" in deco:
            for k in range(4):
                m.blit(_sprite(CALABAZA, CALABAZA_MASC, "O"), 8 + k * (W // 5), y - 2)
        if "cruces" in deco:
            m.blit(_sprite(CRUZ_MAYO, CRUZ_MASC, "R"), sx + 12, y - 4)
        if "san_juan" in deco and m.de_noche:
            h = _sprite(HOGUERA[int(m.t * 4) % 2], HOGUERA_MASC, "O")
            m.blit(h, sx + 14, y - 3)
            if self.rng.random() < 0.3:
                m.texto(y - 4 - self.rng.randint(0, 3), sx + 15 + self.rng.randint(0, 3), "*",
                        color("Y"))
        if "semana_santa" in deco:
            hora = m.ahora.hour
            if 18 <= hora <= 23:  # la procesión sale por la tarde
                ciclo = (m.t * 3) % (W + 40) - 20
                trono = _sprite(TRONO, TRONO_MASC, "Y")
                m.blit(trono, ciclo, y - 3)
                for k in range(1, 6):
                    m.texto(y - 1, ciclo - k * 4, "A", color("morado"))
                    m.texto(y, ciclo - k * 4, "o", color("negro_brillante"))
        if "libro" in deco:
            m.texto(y - 2, sx + 12, "[==]", color("R"))
            m.texto(y - 1, sx + 11, "[====]", color("B"))
        if "feria" in deco:
            # portada de feria sobre la entrada, con bombillas que parpadean
            uni = m.unicode
            ancho = 17
            base = 9 + 4 * self._alto_monticulo()
            x0 = sx + base // 2 + 3  # al lado del montículo, no encima
            top = y - 6
            if x0 + ancho >= m.ancho:  # si no cabe a la derecha, encima de la entrada
                x0 = sx - ancho // 2
                top = y - self._alto_monticulo() - 5
            m.texto(top, x0, ("╔═══╡ FERIA ╞═══╗" if uni else "+---[ FERIA ]---+"), color("Y"))
            for k in range(1, y - top):
                m.texto(top + k, x0, "║" if uni else "|", color("R"))
                m.texto(top + k, x0 + ancho - 1, "║" if uni else "|", color("R"))
            for i in range(2, ancho - 2, 2):
                if (int(m.t * 3) + i) % 3:
                    m.texto(top + 1, x0 + i, "o", color("RYGW"[(i // 2) % 4]))
        # partículas (lluvia, hojas, confeti...)
        for p in self.particulas:
            m.texto(p[1], p[0], p[4], p[5])
        for b in self.bichos:
            b.dibujar(m)

    def _cumples(self, y):
        m = self.m
        if not m.cumples:
            return
        x = m.ox + m.x_cumple
        m.blit(_sprite(TARTA, TARTA_MASC, "W"), x, y - 3)
        for k, col in enumerate(["R", "B", "Y", "M", "G"][:3 + len(m.cumples)]):
            m.blit(_sprite(REGALO, None, col), x + 9 + k * 7, y - 2)

    def dibujar_pancarta(self):
        """Felicitación grande en el cielo (cumpleaños) o mensaje de la fiesta."""
        m = self.m
        W = m.ancho
        if m.cumples:
            texto = "FELIZ CUMPLE " + " Y ".join(n.upper() for n in m.cumples)
            filas = fuente.renderizar(texto, "bloque" if m.unicode else "#", 1)
            if len(filas[0]) > W - 4:
                filas = fuente.renderizar("FELIZ CUMPLE", "bloque" if m.unicode else "#", 1)
                sub = " y ".join(m.cumples)
                m.texto(12, (W - len(sub)) // 2, sub[:W - 4], color("Y"), m.fondo_cielo)
            x = (W - len(filas[0])) // 2
            cols = ["R", "Y", "G", "C", "M"]
            for i, f in enumerate(filas):
                m.texto(6 + i, x, f, color(cols[int(m.t * 2 + i) % len(cols)]), m.fondo_cielo)
        elif m.fiesta_mensaje:
            t = "  %s  " % m.fiesta_mensaje
            m.texto(5, (W - len(t)) // 2, t, color("Y"), m.fondo_cielo)
