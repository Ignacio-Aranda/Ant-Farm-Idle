"""La vida del hormiguero: comida que recoger, bichos que cazar, enemigos de
los que defenderse y visitantes bajo tierra. Aquí se decide qué pasa; las
hormigas (hormigas.py) sólo obedecen.
"""

import math
import random

from motor.colores import color

# ------------------------------------------------------------------ catálogo
# nombre, arte (fotogramas, mirando a la derecha), color, peso (hormigas
# necesarias para llevarlo), vida (aguante al cazarlo), huye (0-1), velocidad
COMIDAS = {
    "miga": ("una miga de pan", ["•"], "arena", 1),
    "semilla": ("una semilla", ["ø"], "marron", 1),
    "azucar": ("un azucarillo", ["▪▪"], "blanco_brillante", 2),
    "higo": ("un higo chumbo", ["(◍)"], "morado", 3),
    "almendra": ("una almendra", ["◖◗"], "marron", 2),
    "galleta": ("una galleta", ["▐▓▓▌"], "naranja", 4),
    "bocadillo": ("medio bocadillo", ["▐▀▀▀▀▌"], "amarillo", 5),
}
PRESAS = {
    "grillo": ("un grillo", ["_╱╲_o", "‾╱╲‾o"], "verde_brillante", 2, 4.0, 0.5, 2.5),
    "oruga": ("una oruga", ["oooO", "oOoO"], "lima", 3, 5.0, 0.0, 0.6),
    "mosca": ("una mosca", ["»o«", ">o<"], "gris", 1, 1.5, 0.8, 4.0),
    "lombriz": ("una lombriz", ["~~~o", "∿∿∿o"], "rosa", 3, 3.0, 0.1, 0.5),
    "escarabajo": ("un escarabajo", ["◖▓▓◗", "◖▓▓◗"], "morado", 4, 8.0, 0.1, 1.0),
}
MUERTO = {"grillo": "_╱╲_x", "oruga": "oooX", "mosca": "-x-", "lombriz": "~~~x",
          "escarabajo": "◖▓▓◗", "roja": "x8x"}

ARANA = ["╱╲(ºº)╱╲", "╲╱(ºº)╲╱"]
PAJARO = ["  ▄▄", "<(•)▀▀▄"]
ROJA = {1: "◖█◗•◖●◗›", -1: "‹◖●◗•◖█◗"}


class Cosa:
    """Algo de la superficie: comida, presa o enemigo."""

    def __init__(self, tipo, clave, nombre, x, arte, col, peso=1, vida=1.0, huye=0.0, vel=0.0):
        self.tipo, self.clave, self.nombre = tipo, clave, nombre
        self.x, self.y = float(x), -1
        self.arte, self.color = arte, color(col)
        self.peso, self.vida, self.huye, self.vel = peso, vida, huye, vel
        self.asignadas = []
        self.estado = "libre"   # libre | llevada | fin
        self.t = 0.0
        self.dir = random.choice([1, -1])
        self.lider = None
        self.golpes = 0.0

    @property
    def ancho(self):
        return len(self.arte[0])

    def cerca(self, h, margen=6):
        return h.y == -1 and abs(h.x - self.x) <= margen and not h.ruta

    def presentes(self):
        return [h for h in self.asignadas if self.cerca(h)]


class Vida:
    def __init__(self, m):
        self.m = m
        self.rng = random.Random()
        self.cosas = []
        self.enemigos = []
        self.debajo = []         # lombrices y cochinillas bajo tierra
        self.chispas = []        # [x, y, t] destellos de pelea
        self.alarma = 0.0
        self.espera_comida = 20.0
        self.espera_presa = 40.0
        self.espera_enemigo = self.rng.uniform(300, 900)
        self.espera_reclutar = 2.0

    # ------------------------------------------------------------- consultas

    def pendientes(self, tipo):
        out = []
        for c in self.cosas:
            if c.tipo != tipo or c.estado != "libre":
                continue
            cupo = c.peso + (1 if tipo == "presa" else 0)
            if len(c.asignadas) < cupo:
                out.append(c)
        return out

    def apuntar(self, h, c):
        c.asignadas.append(h)
        n = len(c.asignadas)
        lado = 1 if n % 2 else -1
        return int(c.x + lado * (5 + 9 * ((n - 1) // 2)))

    def soltar(self, h):
        for c in self.cosas + self.enemigos:
            if h in c.asignadas:
                c.asignadas.remove(h)

    # ------------------------------------------------------------- aparecer

    def _aparecer(self, dt):
        m, rng = self.m, self.rng
        W = m.plan_ancho
        bueno = not m.de_noche and m.lluvia == 0
        mes = m.mes_natural   # las estaciones de la ciudad (en el hemisferio sur, al revés)
        # comida
        self.espera_comida -= dt
        libres = sum(1 for c in self.cosas if c.tipo == "comida" and c.estado == "libre")
        if bueno and self.espera_comida <= 0 and libres < 3:
            self.espera_comida = rng.uniform(25, 70)
            opciones = [("miga", 4), ("semilla", 3 if mes in (9, 10, 11, 12, 1) else 1),
                        ("azucar", 1.5), ("galleta", 0.6), ("bocadillo", 0.3)]
            if 7 <= mes <= 9 and m.superficie.chumbera_x is not None:
                opciones.append(("higo", 3))
            if 8 <= mes <= 9 and m.superficie.arbol_x is not None:
                opciones.append(("almendra", 3))
            clave = rng.choices([o for o, _ in opciones], [w for _, w in opciones])[0]
            nombre, arte, col, peso = COMIDAS[clave]
            x = rng.uniform(6, W - 8)
            if clave == "higo":
                x = max(1, m.superficie.chumbera_x + rng.uniform(-4, 6))
            elif clave == "almendra":
                x = m.superficie.arbol_x - m.ox + rng.uniform(-7, 7)
            c = Cosa("comida", clave, nombre, x, arte, col, peso)
            self.cosas.append(c)
            if peso >= 4:
                m.noticia("¡Alguien ha tirado %s! Hacen falta %d hormigas para moverlo." % (nombre, peso))
        # presas
        self.espera_presa -= dt
        presas = sum(1 for c in self.cosas if c.tipo == "presa")
        if (not m.de_noche) and self.espera_presa <= 0 and presas < 2:
            self.espera_presa = rng.uniform(50, 140)
            frio = m.temperatura < 12
            opciones = [("mosca", 2 if 5 <= mes <= 9 else 0.5)]
            if m.llovio:
                opciones.append(("lombriz", 6))
            if not frio:
                opciones += [("grillo", 3 if 4 <= mes <= 10 else 0.5),
                             ("oruga", 3 if 3 <= mes <= 6 else 0.4),
                             ("escarabajo", 1.5 if 5 <= mes <= 9 else 0.3)]
            if m.lluvia > 0:
                opciones = [("lombriz", 1)]
            clave = rng.choices([o for o, _ in opciones], [w for _, w in opciones])[0]
            nombre, arte, col, peso, vida, huye, vel = PRESAS[clave]
            c = Cosa("presa", clave, nombre, rng.uniform(10, W - 10), arte, col, peso, vida, huye, vel)
            self.cosas.append(c)
        # enemigos
        self.espera_enemigo -= dt
        if not m.de_noche and m.lluvia == 0 and self.espera_enemigo <= 0 and not self.enemigos:
            self.espera_enemigo = rng.uniform(600, 1500)
            opciones = [("arana", 3), ("pajaro", 3)]
            if 4 <= mes <= 10:
                opciones.append(("invasion", 1))
            clave = rng.choices([o for o, _ in opciones], [w for _, w in opciones])[0]
            getattr(self, "_" + clave)()
        # bajo tierra: siempre hay alguna lombriz, y de vez en cuando una cochinilla
        if len([d for d in self.debajo if d["tipo"] == "lombriz"]) < 2 and rng.random() < dt / 30:
            self.debajo.append({"tipo": "lombriz", "x": rng.choice([-6.0, W + 2.0]),
                                "y": rng.randint(2, 30), "vx": 0.0, "t": 0.0})
            d = self.debajo[-1]
            d["vx"] = 0.4 if d["x"] < 0 else -0.4
        if not any(d["tipo"] == "cochinilla" for d in self.debajo) and rng.random() < dt / 600:
            self._cochinilla()

    def _arana(self):
        m = self.m
        x = self.rng.choice([-8, m.plan_ancho + 1])
        a = Cosa("enemigo", "arana", "una araña", x, ARANA, "gris", vida=10, vel=3)
        a.dir = 1 if x < 0 else -1
        self.enemigos.append(a)
        m.noticia("¡Una araña ronda el hormiguero!")
        self._llamar_defensa(a, 4)

    def _pajaro(self):
        m = self.m
        x = self.rng.uniform(20, m.plan_ancho - 20)
        p = Cosa("enemigo", "pajaro", "un pájaro", x, PAJARO, "marron", vida=999)
        p.y = -12
        p.dir = 1
        self.enemigos.append(p)
        self.alarma = 14.0
        m.noticia("¡Un pájaro! Todas para dentro.")

    def _invasion(self):
        m = self.m
        lado = self.rng.choice([1, -1])
        x0 = m.plan_ancho + 2 if lado == 1 else -10
        grupo = []
        for i in range(self.rng.randint(3, 5)):
            r = Cosa("enemigo", "roja", "una hormiga roja", x0 + lado * i * 11, [ROJA[-lado]],
                     "rojo", vida=3, vel=3)
            r.dir = -lado
            grupo.append(r)
        self.enemigos += grupo
        m.noticia("¡Invasión de hormigas rojas! Salen las defensoras.")
        self._llamar_defensa(grupo[0], 6)

    def _llamar_defensa(self, enemigo, n):
        m = self.m
        # las que llevan algo (o ayudan a llevarlo) primero lo guardan
        despiertas = [h for h in m.hormigas.values() if not h.durmiendo and h.tarea is None
                      and h.y >= -1 and not h.escoltando and h.carga_cosa is None]
        self.rng.shuffle(despiertas)
        for h in despiertas[:n]:
            h.defender(m, enemigo)

    def _cochinilla(self):
        m = self.m
        salas = [s for s in m.salas]
        if len(salas) < 2:
            return
        a, b = self.rng.sample(salas, 2)
        ruta = m.plan.camino(a.punto(self.rng), b.punto(self.rng))
        if ruta:
            self.debajo.append({"tipo": "cochinilla", "ruta": ruta, "x": ruta[0][0], "y": ruta[0][1],
                                "avance": 0.0, "t": 0.0, "dir": 1, "sala": b.nombre})
            m.noticia("Una cochinilla se ha colado y va hacia %s." % b.nombre)

    # ------------------------------------------------------------- actualizar

    def _reclutar(self):
        """Feromonas: si a algo le faltan hormigas, avisa a la libre más cercana."""
        m = self.m
        if self.alarma > 0 or m.de_noche:
            return
        for c in self.pendientes("comida") + self.pendientes("presa"):
            libres = [h for h in m.hormigas.values() if h.libre()]
            if not libres:
                return
            # más cerca = más arriba y más cerca en horizontal
            h = min(libres, key=lambda h: abs(h.x - c.x) + (0 if h.y < 0 else 20 + h.y * 2))
            h.reclutar(m, c)

    def actualizar(self, dt):
        m, rng = self.m, self.rng
        self._aparecer(dt)
        self.espera_reclutar -= dt
        if self.espera_reclutar <= 0:
            self.espera_reclutar = rng.uniform(3, 6)
            self._reclutar()
        self.alarma = max(0.0, self.alarma - dt)
        W = m.plan_ancho

        for c in self.cosas:
            c.t += dt
            if c.estado == "llevada":
                if c.lider is None or c.lider.carga_cosa is not c:
                    c.estado = "fin"
                continue
            presentes = c.presentes()
            if c.tipo == "presa":
                if presentes:
                    c.vida -= len(presentes) * dt * 0.9
                    if rng.random() < dt * 3:
                        self.chispas.append([c.x + rng.uniform(-1, c.ancho), -1 - rng.random(), 0.3])
                    # puede escaparse si son pocas
                    if c.huye and rng.random() < dt * c.huye * 0.4 / len(presentes):
                        c.x += rng.choice([-1, 1]) * rng.uniform(6, 14)
                    if c.vida <= 0:
                        nombres = [h.nombre for h in presentes]
                        c.tipo = "comida"
                        c.arte = [MUERTO.get(c.clave, "x")]
                        # se la llevan las que caben; las demás quedan libres
                        quedan = list(dict.fromkeys(presentes + c.asignadas))
                        for h in quedan[c.peso:]:
                            h.liberar(m)
                        c.asignadas = quedan[:c.peso]
                        m.noticia("%s han cazado %s." % (_lista(nombres), c.nombre) if len(nombres) > 1
                                  else "%s ha cazado %s." % (nombres[0], c.nombre))
                else:
                    c.x += c.dir * c.vel * dt * (0.5 + 0.5 * math.sin(c.t))
                    if rng.random() < dt * 0.2:
                        c.dir = -c.dir
                    if c.t > 400:  # se aburre y se va
                        c.dir = 1 if c.x > W / 2 else -1
                        c.vel = max(c.vel, 2)
                c.x = max(-20.0, min(W + 20.0, c.x))
                if c.x < -12 or c.x > W + 8:
                    c.estado = "fin"
            if c.tipo == "comida" and c.estado == "libre":
                if len(presentes) >= c.peso:
                    lider, *ayudantes = presentes[:c.peso]
                    c.estado = "llevada"
                    c.lider = lider
                    lider.llevar(m, c)
                    for k, a in enumerate(ayudantes):
                        a.escoltar(lider, k + 1)
                    for h in list(c.asignadas):   # liberar() la quita de la lista
                        if h not in presentes[:c.peso]:
                            h.liberar(m)
                    c.asignadas = []
                elif c.t > 600:
                    c.estado = "fin"
        for c in self.cosas:
            if c.estado == "fin":
                for h in list(c.asignadas):
                    h.liberar(m)
                c.asignadas = []
        self.cosas = [c for c in self.cosas if c.estado != "fin"]

        self._enemigos(dt)
        for d in self.debajo:
            d["t"] += dt
            if d["tipo"] == "lombriz":
                d["x"] += d["vx"] * dt
                if rng.random() < dt * 0.05:
                    d["y"] = max(1, min(32, d["y"] + rng.choice([-1, 1])))
            else:
                d["avance"] += 2.0 * dt
                while d["avance"] >= 1 and d["ruta"]:
                    nx, ny = d["ruta"].pop(0)
                    d["dir"] = 1 if nx > d["x"] else -1 if nx < d["x"] else d["dir"]
                    d["x"], d["y"] = nx, ny
                    d["avance"] -= 1
                if not d["ruta"] and d["t"] > 60:
                    d["fin"] = True
        self.debajo = [d for d in self.debajo
                       if not d.get("fin") and -10 < d["x"] < W + 10]
        for ch in self.chispas:
            ch[2] -= dt
        self.chispas = [ch for ch in self.chispas if ch[2] > 0]

    def _enemigos(self, dt):
        m, rng = self.m, self.rng
        W = m.plan_ancho
        for e in self.enemigos:
            e.t += dt
            if e.clave == "pajaro":
                # baja en picado, da una pasada y se va
                if e.t < 4:
                    e.y = -12 + e.t * 2.5
                elif e.t < 9:
                    e.x += 8 * dt
                else:
                    e.y -= 4 * dt
                    e.x += 10 * dt
                if e.t > 16:
                    e.estado = "fin"
                continue
            presentes = e.presentes() if e.estado == "libre" else []
            if e.estado == "huye":
                e.x += e.dir * 7 * dt
                if e.x < -14 or e.x > W + 10:
                    e.estado = "fin"
                continue
            if presentes:
                e.vida -= len(presentes) * dt * (0.6 if e.clave == "arana" else 1.0)
                if rng.random() < dt * 4:
                    self.chispas.append([e.x + rng.uniform(0, e.ancho), -1 - rng.random(), 0.3])
                if e.vida <= 0:
                    nombres = [h.nombre for h in presentes]
                    if e.clave == "arana":
                        e.estado = "huye"
                        e.dir = 1 if e.x > W / 2 else -1
                        verbo = "han" if len(set(nombres)) > 1 else "ha"
                        m.noticia("%s %s echado a la araña." % (_lista(nombres), verbo))
                    else:
                        if rng.random() < 0.5:
                            e.estado = "huye"
                            e.dir = 1 if e.x > W / 2 else -1
                            e.arte = [ROJA[e.dir]]
                        else:
                            e.estado = "fin"
                            muerta = Cosa("comida", "roja", "una hormiga roja", e.x, [MUERTO["roja"]],
                                          "rojo", 1)
                            self.cosas.append(muerta)
                        if not any(o.estado == "libre" for o in self.enemigos
                                   if o.clave == "roja" and o is not e):
                            m.noticia("¡Las defensoras han echado a las hormigas rojas!")
                    for h in list(e.asignadas):
                        h.liberar(m)
                    e.asignadas = []
            else:
                # avanza hacia el hormiguero / la hormiga más cercana de fuera
                fuera = [h for h in m.hormigas.values() if h.y == -1]
                objetivo = min(fuera, key=lambda h: abs(h.x - e.x)).x if fuera else m.plan.entrada
                e.dir = 1 if objetivo > e.x else -1
                e.x += e.dir * e.vel * dt
                if e.clave == "roja":
                    e.arte = [ROJA[e.dir]]
                if e.clave == "arana" and fuera and min(abs(h.x - e.x) for h in fuera) < 14:
                    self.alarma = max(self.alarma, 1.5)
            if e.t > 240 and e.estado == "libre":
                e.estado = "huye"
                e.dir = 1 if e.x > W / 2 else -1
        for e in self.enemigos:
            if e.estado == "fin":
                for h in list(e.asignadas):
                    h.liberar(m)
        self.enemigos = [e for e in self.enemigos if e.estado != "fin"]

    # ------------------------------------------------------------- dibujar

_ESPEJO = str.maketrans("<>()[]{}╱╲«»◖◗", "><)(][}{╲╱»«◗◖")


def _lista(nombres):
    nombres = list(dict.fromkeys(nombres))
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]
