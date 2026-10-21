"""Las hormigas: una por cada persona del equipo.

Dibujo (mirando a la derecha), anclado en la cintura '•' y apoyado en el suelo:

        ╲╱          <- antenas      (fila y-2)
   ◖██◗•◖●◗›        <- cuerpo       (fila y-1)
     ╱╲╱╲╱╲         <- patas        (fila y, el suelo)
"""

import random
from collections import deque

from motor.colores import color

COLORES = ["rojo_brillante", "amarillo_brillante", "cian", "magenta_brillante", "verde_brillante",
           "naranja", "azul_brillante", "rosa", "blanco_brillante", "turquesa", "lima", "coral",
           "dorado", "morado", "salmon"]

# (desplazamiento, texto) relativo a la cintura, para cada dirección
UNI = {
    1: {"cuerpo": (-4, "◖██◗•◖●◗›"), "dormida": (-4, "◖██◗•◖-◗"), "antenas": (3, "╲╱"),
        "patas": [(-2, "╱╲╱╲╱╲"), (-2, "╲╱╲╱╲╱")], "patas_quieta": (-2, "╱╲╱╲╱╲"),
        "patas_dormida": (-3, "‿‿‿‿‿‿"), "cabeza": 2, "carga": 5},
    -1: {"cuerpo": (-4, "‹◖●◗•◖██◗"), "dormida": (-3, "◖-◗•◖██◗"), "antenas": (-4, "╲╱"),
         "patas": [(-3, "╱╲╱╲╱╲"), (-3, "╲╱╲╱╲╱")], "patas_quieta": (-3, "╱╲╱╲╱╲"),
         "patas_dormida": (-2, "‿‿‿‿‿‿"), "cabeza": -2, "carga": -5},
}
ASCII = {
    1: {"cuerpo": (-4, "(##)o(o)>"), "dormida": (-4, "(##)o(-)"), "antenas": (3, "\\/"),
        "patas": [(-2, "/\\/\\/\\"), (-2, "\\/\\/\\/")], "patas_quieta": (-2, "/\\/\\/\\"),
        "patas_dormida": (-3, "______"), "cabeza": 2, "carga": 5},
    -1: {"cuerpo": (-4, "<(o)o(##)"), "dormida": (-3, "(-)o(##)"), "antenas": (-4, "\\/"),
         "patas": [(-3, "/\\/\\/\\"), (-3, "\\/\\/\\/")], "patas_quieta": (-3, "/\\/\\/\\"),
         "patas_dormida": (-2, "______"), "cabeza": -2, "carga": -5},
}

# Gorros: lista de (dy, dx relativo al centro de la cabeza, texto unicode, texto ascii, color)
GORROS = {
    "cumple": [(-3, 0, "*", "*", "Y"), (-2, -1, "╱▓╲", "/#\\", "M")],
    "fiesta": [(-3, 0, "*", "*", "Y"), (-2, -1, "╱▓╲", "/#\\", "C")],
    "papa_noel": [(-3, 1, "○", "o", "W"), (-2, -1, "╱█╲", "/#\\", "R")],
    "corona": [(-2, 0, "♛", "w", "Y")],
    "capirote": [(-3, 0, "▲", "A", "morado"), (-2, -1, "▐█▌", "|#|", "morado")],
    "bruja": [(-3, 0, "▲", "A", "morado"), (-2, -1, "▄█▄", "_#_", "morado")],
    "flor": [(-2, -1, "✿", "*", "R")],
    "antifaz": [(-1, -1, "▬", "=", "C")],
}


class Hormiga:
    def __init__(self, persona, indice, m):
        self.persona = persona
        self.nombre = persona["nombre"]
        self.esqueleto = bool(persona.get("esqueleto"))   # Halloween: vuelve uno que se fue
        self.sala = persona.get("sala")
        self.color = color(persona.get("color") or COLORES[indice % len(COLORES)])
        self.rng = random.Random("hormiga-%s-%s-%s" % (m.semilla, self.nombre, m.t))
        casa = self.sala_propia(m)
        self.x, self.y = casa.punto(self.rng) if casa else (m.plan.entrada, -1)
        self.ruta = []
        self.avance = 0.0
        self.espera = self.rng.uniform(0, 4)
        self.dir = self.rng.choice([1, -1])
        self.vel = self.rng.uniform(3.0, 4.5)
        self.actividad = "llegar"
        self.carga = None
        self.carga_color = None
        self.siguiente = None
        self.durmiendo = False
        self.t = self.rng.uniform(0, 10)
        self.pasos = 0
        self.tarea = None          # Cosa de vida.py (comida, presa o enemigo)
        self.carga_cosa = None     # lo que lleva a cuestas (si es la que guía)
        self.escoltando = None     # (líder, puesto) si ayuda a cargar algo grande
        self.historial = deque(maxlen=80)
        self.cita = None           # (sala, hasta_t) reunión o llamada del jefe
        self.repensar = 0.0

    # ---------------------------------------------- órdenes desde vida/mundo

    def liberar(self, m):
        m.vida.soltar(self)
        self.tarea = None
        self.escoltando = None
        if self.carga_cosa is not None:
            self.carga_cosa = None
            self.carga = None
        self.ruta = []
        self.espera = self.rng.uniform(0.5, 2)

    def defender(self, m, enemigo):
        m.vida.soltar(self)
        self.escoltando = None
        self.tarea = enemigo
        enemigo.asignadas.append(self)
        self.durmiendo = False
        self.ir(m, (max(0, min(m.plan_ancho - 1, int(enemigo.x))), -1), "defender")

    def llevar(self, m, cosa):
        self.tarea = None
        self.carga_cosa = cosa
        destino = m.almacen_comida()
        # sin despensa ni ninguna sala, lo dejan en la entrada del nido
        punto = m.punto_libre(destino, self.rng, self) if destino else (m.plan.entrada, -1)
        arte = cosa.arte[0]
        self.ir(m, punto, "guardar", carga=arte if len(arte) <= 6 else arte[:6])
        self.carga_color = cosa.color

    def libre(self):
        """¿Está disponible para que la recluten?"""
        return (not self.durmiendo and self.tarea is None and self.carga_cosa is None
                and not self.escoltando and not self.cita
                and self.actividad not in ("reunion", "despacho", "refugio", "guardar", "tierra"))

    def reclutar(self, m, cosa):
        """Otra hormiga le ha avisado (feromonas) de comida o de una presa."""
        self.tarea = cosa
        x = max(0, min(m.plan_ancho - 1, m.vida.apuntar(self, cosa)))
        self.siguiente = None
        self.ir(m, (x, -1), "cazar" if cosa.tipo == "presa" else "recolectar")

    def escoltar(self, lider, puesto):
        self.tarea = None
        self.escoltando = (lider, puesto)
        self.ruta = []
        self.actividad = "ayudar"

    def convocar(self, m, sala, hasta, motivo):
        m.vida.soltar(self)
        self.tarea = None
        self.escoltando = None
        if self.carga_cosa is not None:
            return  # primero termina de guardar lo que lleva
        self.durmiendo = False
        self.cita = (sala, hasta)
        self.ir(m, m.punto_libre(sala, self.rng, self), motivo)

    def sala_propia(self, m):
        return m.sala_por_clave.get(self.sala) or m.refugio()

    # ------------------------------------------------------------ destinos

    def decidir(self, m):
        rng = self.rng
        self.durmiendo = False
        if self.carga_cosa is not None:   # lo que lleva a cuestas, primero a guardarlo
            return self.llevar(m, self.carga_cosa)
        if self.cita:
            sala, hasta = self.cita
            if m.ahora < hasta:
                return self.ir(m, m.punto_libre(sala, rng, self), "reunion")
            self.cita = None
        if self.siguiente:
            act, destino, carga = self.siguiente
            self.siguiente = None
            return self.ir(m, destino, act, carga)
        casa = self.sala_propia(m)

        if m.de_noche and self.esqueleto:   # los esqueletos no duermen: rondan por todas partes
            if rng.random() < 0.5:
                return self.ir(m, (rng.randrange(4, m.plan_ancho - 4), -1), "rondar")
            s = rng.choice(m.salas) if m.salas else casa
            if s:
                return self.ir(m, m.punto_libre(s, rng, self), "rondar")
        if m.de_noche:
            if rng.random() < 0.9 and casa:
                self.durmiendo = True
                return self.ir(m, m.punto_libre(casa, rng, self), "dormir")
            refugio = m.refugio()
            if refugio:
                return self.ir(m, refugio.punto(rng), "trasnochar")

        if self.nombre in m.cumples and rng.random() < 0.7:
            return self.ir(m, (m.x_cumple + rng.randint(-2, 16), -1), "cumple")

        hora = m.ahora.hour + m.ahora.minute / 60
        opciones = []
        alarma = m.vida.alarma > 0
        comidas = [] if alarma else m.vida.pendientes("comida")
        presas = [] if alarma else m.vida.pendientes("presa")
        if comidas:
            opciones.append(("recolectar", 4.0 + 2 * min(3, len(comidas))))
        if presas:
            opciones.append(("cazar", 8.0))
        if casa:
            opciones.append(("casa", 5.0))
        for s in m.salas:
            if s is casa:
                continue
            if s.funcion == "comedor":
                opciones.append((s, m.ganas_de_comer(hora)))
            elif s.funcion == "agua":
                opciones.append((s, 1.8))
            elif s.principal:
                opciones.append((s, 1.0))
            else:
                opciones.append((s, 0.5))
        if m.frente:
            opciones.append(("obra", 1.5))
        afuera = 1.5
        if m.lluvia > 0:
            afuera = 0.0
        elif m.temperatura < 11 or m.estacion == "invierno":
            afuera = 0.4
        elif m.temperatura > 30:
            afuera = 0.3
        if afuera and not alarma:
            opciones.append(("forrajear", afuera))
        if m.cumples and self.nombre not in m.cumples:
            opciones.append(("felicitar", 2.0))
        if not opciones:   # sin ninguna sala ni obra, y sin poder salir: esperan junto a la entrada
            x = max(0, min(m.plan_ancho - 1, m.plan.entrada + rng.randint(-6, 6)))
            return self.ir(m, (x, -1), "entrada")
        destino = rng.choices([o for o, _ in opciones], [w for _, w in opciones])[0]

        if destino == "casa":
            return self.ir(m, m.punto_libre(casa, rng, self), "casa")
        if destino == "obra":
            fx, fy = m.frente
            salida = m.salidas_x_grid[0]
            self.siguiente = ("tierra", (salida + rng.choice([-6, -5, 5, 6]), -1), "·")
            return self.ir(m, (fx, fy), "excavar")
        if destino in ("recolectar", "cazar"):
            lista = comidas if destino == "recolectar" else presas
            c = min(lista, key=lambda c: abs(c.x - self.x) + (0 if self.y == -1 else 30))
            self.tarea = c
            x = m.vida.apuntar(self, c)
            x = max(0, min(m.plan_ancho - 1, x))
            return self.ir(m, (x, -1), destino)
        if destino == "forrajear":
            x = rng.randrange(4, m.plan_ancho - 4)
            despensa = m.almacen_comida()
            if despensa:
                self.siguiente = ("guardar", despensa.punto(rng), rng.choice("•°"))
            return self.ir(m, (x, -1), "forrajear")
        if destino == "felicitar":
            return self.ir(m, (m.x_cumple + rng.randint(0, 16), -1), "felicitar")
        s = destino
        return self.ir(m, m.punto_libre(s, rng, self), "agua" if s.funcion == "agua" else s.clave)

    def ir(self, m, destino, actividad, carga=None):
        ruta = m.plan.camino((self.x, self.y), destino)
        self.actividad = actividad
        if ruta is None:
            self.espera = self.rng.uniform(1, 3)
            self.siguiente = None
            return
        self.ruta = ruta
        self.avance = 0.0
        if carga is not None:
            self.carga = carga
        if not ruta:
            self._llegar(m)

    def _llegar(self, m):
        rng = self.rng
        act = self.actividad
        if act == "guardar" and self.carga_cosa is not None:
            cosa = self.carga_cosa
            self.carga_cosa = None
            self.carga = None
            m.vida_entregada(self, cosa)
            self.espera = rng.uniform(2, 5)
            return
        if act in ("recolectar", "cazar", "defender"):
            self.espera = 60  # espera a las demás / pelea; vida.py decide
            return
        if act == "refugio":
            self.espera = rng.uniform(10, 20)
            return
        if act in ("reunion", "despacho") and self.cita:
            self.espera = rng.uniform(15, 40)
            return
        if act == "dormir":
            self.espera = rng.uniform(120, 400)
        elif act in ("guardar", "tierra"):
            self.carga = None
            self.espera = rng.uniform(1, 3)
        elif act == "excavar":
            self.espera = rng.uniform(4, 10)
        elif act == "forrajear":
            self.espera = rng.uniform(1, 3)
        elif act == "agua":
            self.espera = rng.uniform(4, 10)
        elif act in ("cumple", "felicitar"):
            self.espera = rng.uniform(8, 25)
        elif act == "casa":
            self.espera = rng.uniform(25, 90)
        else:
            self.espera = rng.uniform(10, 40)

    # ---------------------------------------------------------- movimiento

    def actualizar(self, m, dt):
        self.t += dt
        # ayudando a cargar: va detrás de la que guía, siguiendo sus pasos
        if self.escoltando:
            lider, puesto = self.escoltando
            if lider.carga_cosa is None:
                self.escoltando = None
                self.espera = self.rng.uniform(1, 3)
                return
            h = lider.historial
            k = 10 * puesto
            if len(h) > k:
                self.x, self.y = h[-1 - k]
                self.dir = lider.dir
                self.pasos = lider.pasos
            return
        # alarma: si está fuera, corre adentro
        if m.vida.alarma > 0 and self.y == -1 and self.actividad not in ("refugio", "defender") \
                and self.carga_cosa is None:
            m.vida.soltar(self)
            self.tarea = None
            self.siguiente = None
            refugio = m.refugio()
            if refugio:
                return self.ir(m, m.punto_libre(refugio, self.rng, self), "refugio")
            return self.ir(m, (m.plan.entrada, -1), "refugio")
        # cazando o defendiendo: si el bicho se mueve, recalcula el camino
        if self.tarea is not None and self.actividad in ("cazar", "defender"):
            self.repensar -= dt
            objetivo = self.tarea
            if objetivo.estado != "libre":
                pass
            elif self.repensar <= 0 and abs(objetivo.x - self.x) > 6:
                self.repensar = 1.0
                x = max(0, min(m.plan_ancho - 1, int(objetivo.x + self.rng.randint(-4, 4))))
                ruta = m.plan.camino((self.x, self.y), (x, -1))
                if ruta is not None:
                    self.ruta = ruta
        if self.ruta:
            self.avance += self.vel * dt
            while self.avance >= 1 and self.ruta:
                nx, ny = self.ruta[0]
                if not m.plan.suelo_en(nx, ny):
                    self.ruta = []
                    break
                self.ruta.pop(0)
                if nx != self.x:
                    self.dir = 1 if nx > self.x else -1
                self.x, self.y = nx, ny
                self.historial.append((nx, ny))
                self.avance -= 1
                self.pasos += 1
            if not self.ruta:
                self._llegar(m)
            return
        self.espera -= dt
        if self.espera <= 0:
            if self.tarea is not None:
                m.vida.soltar(self)  # se cansó de esperar
                self.tarea = None
            self.decidir(m)
        elif not self.durmiendo and self.rng.random() < dt * 0.15:
            self.dir = -self.dir  # mira a su alrededor
