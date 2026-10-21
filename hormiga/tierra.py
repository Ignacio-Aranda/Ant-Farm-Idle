"""La tierra y el plan de obras del hormiguero.

El nido inicial (las salas de salas/*.toml, cada una en su planta) ya existe
el día 0: se colocan en la columna pedida o en un hueco al azar, y los túneles
y las rampas entre plantas se trazan solos. A partir de ahí, a lo largo del año
se excavan salas nuevas, galerías y una segunda salida. Todo se calcula a
partir de la semilla y la fecha de fundación, así que el hormiguero de un
día concreto es siempre el mismo aunque la Pi se apague.

Las hormigas miden 3 filas, así que las galerías tienen 4 de alto y se baja
de un nivel a otro por rampas (como en una granja de hormigas de verdad).
"""

import datetime
import random
from collections import deque

from .tiempo import estacion

ANCHO = 160
PROF = 42

HUMUS, ARENA, ARCILLA, ROCA = 1, 2, 3, 4

ALTO_GALERIA = 4
ALTO_SALA = 7
PISOS = {0: 0, 1: 8, 2: 18, 3: 28, 4: 38}   # fila del suelo de cada planta (0 = la superficie)
ENTRADA = 20                     # columna preferida para la entrada principal
BORDE = 3                        # columnas que se dejan libres a cada lado
GAP = 4                          # separación mínima entre salas

# Salas que las hormigas excavan a lo largo del año (se pueden cambiar en config.toml)
OBRAS = [
    {"clave": "despensa", "nombre": "Despensa", "ancho": 24},
    {"clave": "museo", "nombre": "Museo de hallazgos", "ancho": 28},
    {"clave": "hongos", "nombre": "Vivero de hongos", "ancho": 22},
    {"clave": "almacen", "nombre": "Almacén", "ancho": 16},
    {"clave": "biblioteca", "nombre": "Biblioteca", "ancho": 20},
]

OBJETOS = [
    ("una peseta de 1982", "(P)", "dorado"),
    ("una chapa de cerveza", "(*)", "plata"),
    ("una pieza de Lego", "[::]", "rojo_brillante"),
    ("un hueso de aceituna", "0", "marron"),
    ("un fósil de amonites", "@", "arena"),
    ("una Raspberry Pi 1", "[Pi]", "verde_brillante"),
    ("un dado", "[:]", "blanco_brillante"),
    ("una canica", "o", "azul_brillante"),
    ("una llave antigua", "o-m", "dorado"),
    ("un pendrive perdido", "[=}", "cian"),
    ("una moneda romana", "(R)", "naranja"),
    ("el IRPF fosilizado", "<IRPF<", "gris"),
]


class Sala:
    __slots__ = ("clave", "nombre", "x0", "piso", "ancho", "alto", "color", "principal", "tipo", "funcion",
                 "nivel")

    def __init__(self, clave, nombre, x0, piso, ancho, alto=ALTO_SALA, principal=False):
        self.clave, self.nombre, self.x0, self.piso = clave, nombre, x0, piso
        self.ancho, self.alto, self.principal = ancho, alto, principal
        self.color = None
        self.tipo = self.funcion = clave
        self.nivel = 0

    @property
    def y0(self):
        return self.piso - self.alto + 1

    def punto(self, rng):
        """Un sitio del suelo de la sala donde puede pararse una hormiga."""
        return (rng.randint(self.x0 + 5, self.x0 + self.ancho - 6), self.piso)


class Obra:
    __slots__ = ("tipo", "nombre", "celdas", "ini", "fin", "sala", "objeto", "roca", "trabajo")

    def __init__(self, tipo, nombre, celdas, sala=None):
        self.tipo, self.nombre, self.celdas, self.sala = tipo, nombre, celdas, sala
        self.ini = self.fin = 0.0
        self.objeto = None
        self.roca = False
        self.trabajo = 0.0


def _columna(x, piso, alto):
    return [(x, y) for y in range(piso, piso - alto, -1) if y >= 0]


def galeria(x1, x2, piso, alto=ALTO_GALERIA):
    paso = 1 if x2 >= x1 else -1
    celdas = []
    for x in range(x1, x2 + paso, paso):
        celdas += _columna(x, piso, alto)
    return celdas


def rampa(x1, piso1, x2, piso2):
    """Rampa de x1 a x2 bajando (o subiendo) una fila cada dos columnas."""
    paso = 1 if x2 >= x1 else -1
    n = abs(x2 - x1)
    celdas = []
    for i in range(n + 1):
        piso = round(piso1 + (piso2 - piso1) * i / max(1, n))
        celdas += _columna(x1 + i * paso, piso, ALTO_GALERIA)
    return celdas


def _unir(tramo, otro):
    if tramo is None:
        return otro
    return (min(tramo[0], otro[0]), max(tramo[1], otro[1]))


def _alargar(tramo, x):
    """Cuántas columnas habría que alargar la galería para llegar a x."""
    if tramo is None:
        return 0
    return max(0, tramo[0] - x, x - tramo[1])


def sala_celdas(sala):
    celdas = []
    for x in range(sala.x0, sala.x0 + sala.ancho):
        borde = x in (sala.x0, sala.x0 + sala.ancho - 1)
        alto = sala.alto - (2 if borde else 0)  # esquinas redondeadas
        celdas += _columna(x, sala.piso, alto)
    return celdas


class Plan:
    def __init__(self, semilla, fundacion, principales, dias_obras=330, obras=None, entrada=ENTRADA):
        """principales: lista de dicts (clave, nombre, color, planta, ancho, x, tipo, funcion).
        obras: las salas que se excavan durante el año (por defecto OBRAS)."""
        self.semilla = semilla
        self.fundacion = fundacion
        self.rng = random.Random("plan-%s" % semilla)
        self.suelo = self._generar_suelo()
        self.entrada_preferida = entrada
        self.salas_obras = OBRAS if obras is None else obras
        self.obras = []
        self.objetos = []
        self.salas_todas = []
        self.avisos = []
        self._montar_nido(principales)
        self._montar_obras(dias_obras)
        self._poner_objetos()
        self._cavado = bytearray(ANCHO * PROF)
        self._dia_calc = None
        self._idx = 0
        self._parcial = 0
        self.version = 0

    # ---------------------------------------------------------------- suelo

    def _generar_suelo(self):
        rng = random.Random("suelo-%s" % self.semilla)
        s = bytearray(ANCHO * PROF)
        lim1 = [5 + int(rng.uniform(-1, 1.5)) for _ in range(ANCHO)]
        lim2 = [16 + int(rng.uniform(-1.5, 1.5)) for _ in range(ANCHO)]
        for lim in (lim1, lim2):
            for i in range(1, ANCHO - 1):
                lim[i] = round((lim[i - 1] + lim[i] + lim[i + 1]) / 3)
        for y in range(PROF):
            for x in range(ANCHO):
                s[y * ANCHO + x] = HUMUS if y < lim1[x] else ARENA if y < lim2[x] else ARCILLA
        for _ in range(30):
            cx, cy = rng.randrange(ANCHO), rng.randrange(8, PROF)
            rx, ry = rng.randint(2, 6), rng.randint(1, 2)
            for y in range(cy - ry, cy + ry + 1):
                for x in range(cx - rx, cx + rx + 1):
                    if 0 <= x < ANCHO and 0 <= y < PROF:
                        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.1:
                            s[y * ANCHO + x] = ROCA
        for y in range(PROF - 3, PROF):
            for x in range(ANCHO):
                if rng.random() < 0.5 + (y - PROF + 3) * 0.25:
                    s[y * ANCHO + x] = ROCA
        return s

    def tipo(self, x, y):
        if 0 <= x < ANCHO and 0 <= y < PROF:
            return self.suelo[y * ANCHO + x]
        return ARCILLA

    # ----------------------------------------------------------- el nido

    def _libre(self, nivel, a, b, margen=GAP):
        """¿Están libres las columnas a..b del nivel (sin salas ni rampas cerca)?"""
        if a < BORDE or b > ANCHO - 1 - BORDE:
            return False
        return all(b + margen < x0 or a - margen > x1 for x0, x1 in self.ocupado[nivel])

    def _ocupar(self, nivel, a, b):
        self.ocupado[nivel].append((min(a, b), max(a, b)))

    def _colocar(self, s, nivel, x_fijo=None):
        """Pone la sala en su planta: en la columna pedida o en un hueco al azar."""
        if x_fijo is not None:
            x0 = max(BORDE, min(ANCHO - BORDE - s.ancho, int(x_fijo)))
            if self._libre(nivel, x0, x0 + s.ancho - 1):
                candidatos = [x0]
            else:
                self.avisos.append("%s: la columna %s choca con otra sala" % (s.nombre, x_fijo))
                candidatos = []
        else:
            candidatos = []
        if not candidatos:
            candidatos = [x for x in range(BORDE, ANCHO - BORDE - s.ancho + 1)
                          if self._libre(nivel, x, x + s.ancho - 1)]
        if not candidatos:
            self.avisos.append("%s no cabe en la planta %d" % (s.nombre, nivel))
            return False
        rng = random.Random("sala-%s-%s" % (self.semilla, s.clave))
        x0 = candidatos[0] if len(candidatos) == 1 else rng.choice(candidatos)
        s.x0, s.piso = x0, PISOS[nivel]
        s.nivel = nivel
        self._ocupar(nivel, x0, x0 + s.ancho - 1)
        self.tramo[nivel] = _unir(self.tramo[nivel], (x0, x0 + s.ancho - 1))
        return True

    def _rampa_libre(self, nivel_a, nivel_b, a, b):
        return self._libre(nivel_a, a, b, 1) and (nivel_b == 0 or self._libre(nivel_b, a, b, 1))

    def _elegir_rampa(self, arriba, abajo, cerca, sentido_previo):
        """Busca dónde poner la rampa de la planta `arriba` a la de `abajo` (0 = superficie):
        que no atraviese salas y que alargue lo menos posible las galerías."""
        largo = 2 * (PISOS[abajo] - PISOS[arriba])
        mejor = None
        for x in range(BORDE, ANCHO - BORDE):
            for sentido in (1, -1):
                x2 = x + sentido * largo
                a, b = min(x, x2), max(x, x2)
                if a < BORDE or b > ANCHO - 1 - BORDE:
                    continue
                libre = self._rampa_libre(abajo, arriba, a, b) if arriba else self._libre(abajo, a, b, 1)
                coste = _alargar(self.tramo[arriba], x) + _alargar(self.tramo[abajo], x2)
                if arriba == 0:
                    coste = abs(x - cerca) * 0.5 + _alargar(self.tramo[abajo], x2)
                coste += 0 if sentido != sentido_previo else 6   # mejor en zigzag
                coste += 0 if libre else 1000                     # atravesar una sala, sólo si no hay otra
                if mejor is None or coste < mejor[0]:
                    mejor = (coste, x, x2, sentido, libre)
        _, x, x2, sentido, libre = mejor
        if not libre:
            self.avisos.append("no hay sitio para una rampa sin atravesar una sala (planta %d)" % abajo)
        return x, x2, sentido

    def _montar_nido(self, principales):
        self.ocupado = {n: [] for n in PISOS}
        self.tramo = {n: None for n in PISOS}     # (x_ini, x_fin) de la galería de cada planta
        colocadas = []
        salas = []
        for d in principales:
            nivel = max(1, min(len(PISOS) - 1, int(d.get("planta", 2))))
            s = Sala(d["clave"], d["nombre"], 0, 0, int(d.get("ancho", 32)), principal=True)
            s.color = d.get("color")
            s.tipo, s.funcion = d.get("tipo", "trabajo"), d.get("funcion", "trabajo")
            salas.append((s, nivel, d.get("x")))
        # primero las que tienen columna fija, luego las demás (en orden de nombre de fichero)
        for s, nivel, x in sorted(salas, key=lambda e: (e[2] is None, e[0].clave)):
            if self._colocar(s, nivel, x):
                colocadas.append(s)
        hondo = max([s.nivel for s in colocadas], default=1)
        # túneles: rampa desde la superficie y de cada planta a la siguiente
        celdas = []
        x, x2, sentido = self._elegir_rampa(0, 1, self.entrada_preferida, 0)
        self.entrada = x
        self.rampas = [(0, 1, x, x2)]
        celdas += rampa(x, 0, x2, PISOS[1])
        self._ocupar(1, x, x2)
        self.tramo[1] = _unir(self.tramo[1], (x2, x2))
        for n in range(1, hondo):
            x, x2, sentido = self._elegir_rampa(n, n + 1, 0, sentido)
            self.rampas.append((n, n + 1, x, x2))
            celdas += rampa(x, PISOS[n], x2, PISOS[n + 1])
            self.tramo[n] = _unir(self.tramo[n], (x, x))
            self.tramo[n + 1] = _unir(self.tramo[n + 1], (x2, x2))
            self._ocupar(n, x, x2)
            self._ocupar(n + 1, x, x2)
        for n in range(1, hondo + 1):
            a, b = self.tramo[n]
            celdas += galeria(a, b, PISOS[n])
        for s in colocadas:
            celdas += sala_celdas(s)
        ini = Obra("inicial", "el nido", celdas)
        ini.ini, ini.fin = -2.0, -1.0
        self.obras.append(ini)
        self.salas_todas = colocadas
        self._obra_sala = {s.clave: ini for s in colocadas}
        self.hondo = hondo

    # ------------------------------------------------------- las obras del año

    def _montar_obras(self, dias):
        rng = self.rng
        obras = []
        # salas nuevas, al lado de las galerías que ya hay (mejor en las plantas de abajo)
        lado = -1
        for d in self.salas_obras:
            ancho = int(d.get("ancho", 22))
            hecho = False
            for n in sorted(range(1, self.hondo + 1), key=lambda n: -n):
                for intento in (lado, -lado):
                    a, b = self.tramo[n]
                    # el primer hueco libre a ese lado de la galería
                    xs = range(b + 1, ANCHO) if intento == 1 else range(a - ancho, -1, -1)
                    x0 = next((x for x in xs if self._libre(n, x, x + ancho - 1)), None)
                    if x0 is not None:
                        gal = galeria(b + 1, x0 + ancho - 1, PISOS[n]) if intento == 1 else \
                            galeria(a - 1, x0, PISOS[n])
                        self.tramo[n] = _unir(self.tramo[n], (x0, x0 + ancho - 1))
                        hecho = True
                        break
                if hecho:
                    break
            if not hecho:
                continue
            sala = Sala(d["clave"], d["nombre"], x0, PISOS[n], ancho)
            sala.tipo, sala.funcion, sala.nivel = d.get("tipo", d["clave"]), d.get("funcion", d["clave"]), n
            self._ocupar(n, x0, x0 + ancho - 1)
            obras.append(Obra("galeria", "la galería de la planta %d" % n, gal))
            obras.append(Obra("sala", d["nombre"], sala_celdas(sala), sala))
            self.salas_todas.append(sala)
            lado = -lado
        # segunda salida: desde la galería de la planta 1 hacia arriba, lejos de la entrada
        a, b = self.tramo[1]
        largo = 2 * PISOS[1]
        mejor = None
        for x in range(a, b + 1):
            for sentido in (1, -1):
                x2 = x + sentido * largo
                lo, hi = min(x, x2), max(x, x2)
                if lo < BORDE or hi > ANCHO - 1 - BORDE:
                    continue
                # sube por encima de las rampas que bajan, pero no puede atravesar salas
                if any(s.nivel == 1 and not (hi + 1 < s.x0 or lo - 1 > s.x0 + s.ancho - 1)
                       for s in self.salas_todas):
                    continue
                lejos = abs(x2 - self.entrada)
                if lejos > 24 and (mejor is None or lejos > mejor[0]):
                    mejor = (lejos, x, x2)
        if mejor:
            _, x, x2 = mejor
            obras.insert(min(3, len(obras)), Obra("salida", "una segunda salida", rampa(x, PISOS[1], x2, 0)))
        # exploración: alargan las galerías hacia los bordes
        for n in range(1, self.hondo + 1):
            a, b = self.tramo[n]
            if a - 14 >= BORDE and self._libre(n, a - 14, a - 1, 0):
                obras.append(Obra("galeria", "una galería hacia el oeste", galeria(a, a - 14, PISOS[n])))
            elif b + 14 <= ANCHO - 1 - BORDE and self._libre(n, b + 1, b + 14, 0):
                obras.append(Obra("galeria", "una galería hacia el este", galeria(b, b + 14, PISOS[n])))

        # Trabajo de cada obra (la roca y la arcilla cuestan más)
        coste = {HUMUS: 0.8, ARENA: 1.0, ARCILLA: 1.4, ROCA: 3.0}
        for o in obras:
            o.trabajo = sum(coste[self.suelo[y * ANCHO + x]] for x, y in o.celdas)
            o.roca = any(self.suelo[y * ANCHO + x] == ROCA for x, y in o.celdas)
        # Repartir el trabajo para que dure el año: cavan más en primavera y menos en invierno
        ritmo = {"invierno": 0.5, "primavera": 1.3, "verano": 1.0, "otoño": 0.9}
        descansos = [rng.uniform(2, 6) for _ in obras]
        dias_trabajo = dias - sum(descansos)
        capacidad = []
        for d in range(int(dias_trabajo * 2) + 400):
            f = self.fundacion + datetime.timedelta(days=d)
            capacidad.append(ritmo[estacion(f)])
        total = sum(o.trabajo for o in obras)
        cap_total = sum(capacidad[:int(dias)])
        escala = total / max(1e-6, cap_total * (dias_trabajo / dias))
        dia = 1.0
        for o, desc in zip(obras, descansos):
            o.ini = dia
            restante = o.trabajo
            while restante > 0:
                c = capacidad[min(len(capacidad) - 1, int(dia))] * escala * 0.25
                restante -= c
                dia += 0.25
            o.fin = dia
            dia += desc
            self.obras.append(o)
            if o.sala:
                self._obra_sala[o.sala.clave] = o

    def _poner_objetos(self):
        rng = random.Random("objetos-%s" % self.semilla)
        candidatas = [o for o in self.obras if o.ini >= 0]
        objetos = list(OBJETOS)
        rng.shuffle(objetos)
        ocupado = set()
        for o in self.obras:
            ocupado.update(o.celdas)
        for obra, (nombre, icono, color) in zip(candidatas, objetos):
            borde = [(x, y) for x, y in obra.celdas[-40:]]
            rng.shuffle(borde)
            for cx, cy in borde:
                x, y = cx, cy - ALTO_GALERIA if (cx, cy - 1) in ocupado else cy + 1
                for dy in (-1, 1, -2, 2):
                    yy = cy + dy
                    celdas = [(x + i, yy) for i in range(len(icono))]
                    if all(0 < cx2 < ANCHO - 1 and 0 <= cy2 < PROF - 3 and (cx2, cy2) not in ocupado
                           and self.suelo[cy2 * ANCHO + cx2] != ROCA for cx2, cy2 in celdas):
                        obra.objeto = (x, yy, nombre, icono, color)
                        self.objetos.append((x, yy, nombre, icono, color, obra.fin))
                        ocupado.update(celdas)
                        break
                if obra.objeto:
                    break

    # ----------------------------------------------------------- estado

    def actualizar(self, dia):
        if self._dia_calc is not None and dia < self._dia_calc:
            self._cavado = bytearray(ANCHO * PROF)
            self._idx, self._parcial = 0, 0
        cambio = False
        obras = self.obras
        while self._idx < len(obras):
            o = obras[self._idx]
            if dia >= o.fin:
                n = len(o.celdas)
            elif dia > o.ini:
                n = int(len(o.celdas) * (dia - o.ini) / max(1e-6, o.fin - o.ini))
            else:
                n = 0
            for x, y in o.celdas[self._parcial:n]:
                self._cavado[y * ANCHO + x] = 1
                cambio = True
            if n >= len(o.celdas):
                self._idx += 1
                self._parcial = 0
            else:
                self._parcial = max(self._parcial, n)
                break
        self._dia_calc = dia
        if cambio:
            self.version += 1
        return cambio

    def cavado(self, x, y):
        if y < 0:
            return 0 <= x < ANCHO
        if 0 <= x < ANCHO and y < PROF:
            return self._cavado[y * ANCHO + x] == 1
        return False

    def suelo_en(self, x, y):
        """¿Puede pisar aquí una hormiga? (hueco con tierra debajo, o la superficie)"""
        if y == -1:
            return 0 <= x < ANCHO
        return self.cavado(x, y) and not self.cavado(x, y + 1)

    def obra_actual(self, dia):
        for o in self.obras:
            if o.ini <= dia < o.fin:
                return o
        return None

    def frente(self, dia):
        o = self.obra_actual(dia)
        if not o:
            return None
        n = int(len(o.celdas) * (dia - o.ini) / max(1e-6, o.fin - o.ini))
        for i in range(min(n, len(o.celdas)) - 1, -1, -1):
            x, y = o.celdas[i]
            # buscar el suelo de esa columna
            for yy in range(y, PROF):
                if self.suelo_en(x, yy):
                    return (x, yy)
        return None

    def salas(self, dia):
        return [s for s in self.salas_todas if self._obra_sala[s.clave].fin <= dia]

    def salidas(self, dia):
        s = [self.entrada]
        for o in self.obras:
            if o.tipo == "salida" and o.fin <= dia:
                s.append(o.celdas[-1][0])
        return s

    def total_cavado(self):
        return sum(self._cavado)

    def _abierto(self, x, y1, y2):
        """¿Está hueca la columna x entre las filas y1 e y2? (para trepar escalones)"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if y >= 0 and not self.cavado(x, y):
                return False
        return True

    def camino(self, origen, destino):
        """BFS por el suelo de túneles, rampas y salas (y por la superficie, fila -1).
        Trepan por las paredes: pueden subir o bajar hasta 8 filas si el hueco lo permite."""
        if origen == destino:
            return []
        if not self.suelo_en(*destino):
            return None
        previo = {origen: None}
        cola = deque([origen])
        while cola:
            x, y = cola.popleft()
            for dx in (1, -1):
                nx = x + dx
                for dy in (0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -7, 7, -8, 8):
                    ny = y + dy
                    n = (nx, ny)
                    if n in previo or not self.suelo_en(nx, ny):
                        continue
                    if ny == -1 and y > 0:
                        continue  # a la superficie sólo desde lo alto de una rampa
                    if y == -1 and ny > 0:
                        continue
                    if abs(dy) > 1 and not (self._abierto(nx, y, ny) or self._abierto(x, y, ny)):
                        continue
                    previo[n] = (x, y)
                    if n == destino:
                        ruta = []
                        p = n
                        while p != origen:
                            ruta.append(p)
                            p = previo[p]
                        ruta.reverse()
                        return ruta
                    cola.append(n)
        return None
