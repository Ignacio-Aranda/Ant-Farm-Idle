"""La tierra y el plan de obras del hormiguero.

El nido inicial (las tres salas principales, el comedor y la Planta 2) ya
existe el día 0. A partir de ahí, a lo largo del año se excava un tercer
nivel con salas nuevas, galerías y una segunda salida. Todo se calcula a
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
N1, N2, N3, N4 = 8, 18, 28, 38   # filas del suelo de cada nivel (la Planta 2 va en el 4)
ENTRADA = 20                     # columna de la entrada principal

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
    __slots__ = ("clave", "nombre", "x0", "piso", "ancho", "alto", "color", "principal")

    def __init__(self, clave, nombre, x0, piso, ancho, alto=ALTO_SALA, principal=False):
        self.clave, self.nombre, self.x0, self.piso = clave, nombre, x0, piso
        self.ancho, self.alto, self.principal = ancho, alto, principal
        self.color = None

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


def sala_celdas(sala):
    celdas = []
    for x in range(sala.x0, sala.x0 + sala.ancho):
        borde = x in (sala.x0, sala.x0 + sala.ancho - 1)
        alto = sala.alto - (2 if borde else 0)  # esquinas redondeadas
        celdas += _columna(x, sala.piso, alto)
    return celdas


class Plan:
    def __init__(self, semilla, fundacion, principales, dias_obras=330):
        """principales: lista de dicts (clave, nombre, color, nivel, ancho), en orden."""
        self.semilla = semilla
        self.fundacion = fundacion
        self.rng = random.Random("plan-%s" % semilla)
        self.suelo = self._generar_suelo()
        self.entrada = ENTRADA
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

    def _fila_de_salas(self, salas, x, piso, limite):
        """Coloca salas seguidas en un nivel. Devuelve (salas colocadas, x final)."""
        colocadas = []
        for s in salas:
            hueco = 4
            if x + hueco + s.ancho > limite:
                hueco = 2
            if x + hueco + s.ancho > limite:
                self.avisos.append("%s no cabe en su nivel" % s.nombre)
                continue
            x += hueco
            s.x0, s.piso = x, piso
            colocadas.append(s)
            x += s.ancho
        return colocadas, x

    def _montar_nido(self, principales):
        celdas = []
        def sala(d, nivel):
            s = Sala(d["clave"], d["nombre"], 0, 0, int(d.get("ancho", 32)), principal=True)
            s.color = d.get("color")
            return s
        nivel1 = [Sala("comedor", "Comedor", 0, 0, 34)] + \
            [sala(d, 1) for d in principales if int(d.get("nivel", 2)) == 1]
        nivel2 = [sala(d, 2) for d in principales if int(d.get("nivel", 2)) != 1]
        # entrada y rampa al nivel 1
        x1 = ENTRADA + 2 * N1                       # 36
        celdas += rampa(ENTRADA, 0, x1, N1)
        s1, fin1 = self._fila_de_salas(nivel1, x1, N1, ANCHO - 6)
        fin1 += 2
        celdas += galeria(x1, fin1, N1)
        # rampa al nivel 2 (hacia la izquierda) y las salas de trabajo
        x2 = x1 - 2 * (N2 - N1)                     # 16
        celdas += rampa(x1, N1, x2, N2)
        s2, fin2 = self._fila_de_salas(nivel2, x1 + 2, N2, ANCHO - 4)
        fin2 = min(ANCHO - 3, fin2 + 2)
        celdas += galeria(x2, fin2, N2)
        # bajada al nivel 3 (desde el final del nivel 2) y luego a la Planta 2
        xr = fin2 - 1
        x3 = xr - 2 * (N3 - N2)
        celdas += rampa(xr, N2, x3, N3)
        xa = x3 - 24
        celdas += galeria(x3, xa, N3)
        x4 = xa - 2 * (N4 - N3)
        celdas += rampa(xa, N3, x4, N4)
        planta2 = Sala("planta2", "Planta 2", max(3, x4 - 32), N4, 28)
        celdas += galeria(x4, planta2.x0 + planta2.ancho - 1, N4)
        for s in s1 + s2 + [planta2]:
            celdas += sala_celdas(s)
        ini = Obra("inicial", "el nido", celdas)
        ini.ini, ini.fin = -2.0, -1.0
        self.obras.append(ini)
        self.salas_todas = s1 + s2 + [planta2]
        self._obra_sala = {s.clave: ini for s in self.salas_todas}
        self.x1, self.x2, self.fin1, self.fin2 = x1, x2, fin1, fin2
        self.x3, self.xa, self.xr = x3, xa, xr
        self.principales = [s for s in s1 + s2 if s.principal]

    # ------------------------------------------------------- las obras del año

    def _montar_obras(self, dias):
        rng = self.rng
        obras = []
        # salas nuevas en el nivel 3, a ambos lados de la galería inicial
        nuevas = [("despensa", "Despensa", 24), ("museo", "Museo de hallazgos", 28),
                  ("hongos", "Vivero de hongos", 22), ("almacen", "Almacén", 16),
                  ("biblioteca", "Biblioteca", 20)]
        izq, der = self.xa, self.x3
        lado = -1
        for clave, nombre, ancho in nuevas:
            for intento in (lado, -lado):
                # a la derecha sólo si queda fuera de la rampa del nivel 2 al 3
                if intento == 1 and der + 4 > self.xr + 2 and der + 4 + ancho + 2 < ANCHO - 2:
                    x0 = der + 4
                    gal = galeria(der + 1, x0 + ancho + 1, N3)
                    der = x0 + ancho + 1
                    break
                if intento == -1 and izq - 4 - ancho > 3:
                    x0 = izq - 4 - ancho
                    gal = galeria(izq - 1, x0 - 1, N3)
                    izq = x0 - 1
                    break
            else:
                continue
            sala = Sala(clave, nombre, x0, N3, ancho)
            obras.append(Obra("galeria", "la galería del nivel 3", gal))
            obras.append(Obra("sala", nombre, sala_celdas(sala), sala))
            self.salas_todas.append(sala)
            lado = -lado
        # segunda salida, desde el final del nivel 1 hacia arriba
        xs = min(ANCHO - 4, self.fin1 + 2 * N1)
        obras.insert(3, Obra("salida", "una segunda salida", rampa(self.fin1, N1, xs, 0)))
        # exploración: alargan las galerías hacia los bordes
        obras.append(Obra("galeria", "una galería hacia el oeste", galeria(self.x2, 3, N2)))
        obras.append(Obra("galeria", "una galería en el nivel 3", galeria(izq, max(3, izq - 14), N3)))
        if der > self.x3:
            obras.append(Obra("galeria", "una galería en el nivel 3",
                              galeria(der, min(ANCHO - 4, der + 14), N3)))

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
        s = [ENTRADA]
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
