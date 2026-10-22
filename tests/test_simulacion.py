"""Pruebas de la simulación: hormiga/mundo.py, hormigas.py, vida.py y superficie.py.

Se simulan días y semanas con un reloj simulado (como pixel/app.sin_pantalla), con
fechas fijas y con los ficheros de cada prueba en una carpeta temporal. Nada se escribe
en local/ del repositorio: la raíz del hormiguero de prueba es siempre la carpeta temporal.

    SDL_VIDEODRIVER=dummy python3 -m unittest tests.test_simulacion -v
"""

import datetime
import json
import os
import re
import shutil
import sys
import tempfile
import tomllib
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hormiga import app as A  # noqa: E402
from hormiga import tiempo as T  # noqa: E402
from hormiga.mundo import Mundo  # noqa: E402
from hormiga.tierra import ANCHO, PROF  # noqa: E402
from hormiga.vida import Cosa  # noqa: E402
from motor.colores import color  # noqa: E402
from pixel import app as APP  # noqa: E402

TIPOS = os.path.join(RAIZ, "tipos")   # sólo se leen
FUNDACION = datetime.date(2026, 1, 1)
CALAVERA = " ☠"


# ------------------------------------------------------------- ficheros de prueba

class Crudo(str):
    """Un valor que va tal cual en el TOML (sin comillas), p. ej. una fecha de TOML."""


def _toml(v):
    if isinstance(v, Crudo):
        return str(v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_toml(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)


def _tabla(nombre, campos):
    return "\n[[%s]]\n" % nombre + "".join("%s = %s\n" % (k, _toml(v)) for k, v in campos.items())


def zona(nombre):
    """La zona horaria, si este ordenador la conoce (si no, el sol va con la hora del ordenador)."""
    return {"zona_horaria": nombre} if T.zona_horaria(nombre) else {}


def config(semilla=2026, fundacion=FUNDACION, nombre=None, cavar="fecha", obras=None,
           esqueletos=False, ciudad=None):
    """config.toml de prueba. La ciudad va en hora de Madrid (si se puede), para que el día y la
    noche no dependan de la zona horaria del ordenador que pasa las pruebas."""
    texto = '[general]\nfundacion = "%s"\nsemilla = %d\n' % (fundacion.isoformat(), semilla)
    if nombre:
        texto += "nombre = %s\n" % _toml(nombre)
    c = dict(zona("Europe/Madrid"), **(ciudad or {}))
    if c:
        texto += "\n[ciudad]\n" + "".join("%s = %s\n" % (k, _toml(v)) for k, v in c.items())
    texto += '\n[tiempo]\nfuente = "estadistico"\n'
    texto += "\n[nido]\ncavar = %s\n" % _toml(cavar)
    if obras is not None:
        texto += "obras = %s\n" % _toml(obras)
    texto += "\n[halloween]\nesqueletos = %s\n" % _toml(esqueletos)
    return texto


def sala(nombre, planta, ancho=30, tipo="trabajo", miembros=(), jefe=False, reuniones=()):
    texto = "nombre = %s\nplanta = %d\nancho = %d\ntipo = %s\n" % (_toml(nombre), planta, ancho, _toml(tipo))
    if jefe:
        texto += "jefe = true\n"
    for m in miembros:
        texto += _tabla("miembro", m if isinstance(m, dict) else {"nombre": m})
    for r in reuniones:
        texto += _tabla("reunion", r)
    return texto


def idos(*gente):
    return "".join(_tabla("ido", d if isinstance(d, dict) else {"nombre": d}) for d in gente)


def calendario(*fiestas):
    return "".join(_tabla("fiesta", f) for f in fiestas)


def oficina(miembros_trabajo=("Ana", "Luis", "Marta"), miembros_diseno=("Diego", "Lucía")):
    """Un hormiguero como el de ejemplo: comedor, fuente, dos salas de trabajo, despacho
    con jefa y sala de reuniones."""
    return {
        "comedor": sala("Comedor", 1, 34, "comedor"),
        "desarrollo": sala("Desarrollo", 2, 40, miembros=miembros_trabajo),
        "despacho": sala("Despacho", 1, 22, "despacho", miembros=["Elena"], jefe=True),
        "diseno": sala("Diseño", 2, 34, miembros=miembros_diseno),
        "fuente": sala("Fuente", 4, 28, "fuente"),
        "reuniones": sala("Reuniones", 1, 30, "reuniones", reuniones=[
            {"nombre": "Reunión de equipo", "dia": "lunes", "hora": "10:00", "minutos": 60,
             "quien": "todos"}]),
    }


class Reloj:
    """La hora la pone la prueba. Con real=True, Mundo lo trata como el reloj de verdad
    (guarda el estado en <raíz>/local/estado.json, que aquí es la carpeta temporal)."""

    def __init__(self, ahora, real=False):
        self.ahora = ahora
        self.real = real

    def __call__(self):
        return self.ahora


class Hormiguero:
    """Un hormiguero de prueba en una carpeta temporal, con su reloj simulado."""

    def __init__(self, prueba, cfg_texto, salas=None, idos_texto="", calendario_texto="",
                 fecha=datetime.datetime(2026, 6, 1, 12, 0), real=False, tiempo=None, rutas=None):
        self.dir = tempfile.mkdtemp(prefix="hormiguero-prueba-")
        prueba.addCleanup(shutil.rmtree, self.dir, True)
        os.makedirs(self.ruta("salas"))
        self.escribir("config.toml", cfg_texto)
        for clave, texto in (salas or {}).items():
            self.escribir(os.path.join("salas", clave + ".toml"), texto)
        self.escribir("idos.toml", idos_texto)
        self.escribir("calendario.toml", calendario_texto)
        r = dict(config=self.ruta("config.toml"), salas=self.ruta("salas"), idos=self.ruta("idos.toml"),
                 calendario=self.ruta("calendario.toml"))
        r.update(rutas or {})
        self.args = APP.argumentos(["-c", r["config"], "--salas", r["salas"], "--tipos", TIPOS,
                                    "--idos", r["idos"], "--calendario", r["calendario"],
                                    "--fecha", fecha.date().isoformat()])
        self.args.sin_estado = True   # nunca escribe en local/ del repositorio
        self.tiempo = tiempo
        self.reloj = Reloj(fecha, real)
        self.m = self.arrancar()

    def ruta(self, nombre):
        return os.path.join(self.dir, nombre)

    def escribir(self, nombre, texto):
        with open(self.ruta(nombre), "w", encoding="utf-8") as f:
            f.write(texto)

    def cargar(self, avisos):
        cfg, salas, idos_, fiestas = APP.cargar(A, self.args, avisos)
        cfg["raiz"] = self.dir   # el estado y el tiempo real, en la carpeta temporal
        if self.tiempo:
            cfg["tiempo_forzado"] = self.tiempo
        return cfg, salas, idos_, fiestas

    def arrancar(self):
        """Un Mundo nuevo con los ficheros de la carpeta (como al reiniciar el hormiguero)."""
        self.avisos = []
        cfg, salas, idos_, fiestas = self.cargar(self.avisos)
        return Mundo(cfg, salas, idos_, fiestas, APP.PantallaNula(), self.reloj, self.avisos)

    def recargar(self):
        """Como pixel/app.py al guardar un fichero con el hormiguero en marcha."""
        nuevos = []
        _cfg, salas, idos_, fiestas = self.cargar(nuevos)
        m = self.m
        m.avisos_carga = nuevos
        m.fiestas = fiestas
        m.cargar_gente(salas, idos_)
        m.actualizar_contexto(forzar=True)

    # ---- el paso del tiempo

    def fino(self, pasos, dt=0.05, cada_paso=None):
        """Fotograma a fotograma: el reloj avanza lo mismo que la simulación."""
        for _ in range(pasos):
            self.reloj.ahora += datetime.timedelta(seconds=dt)
            self.m.paso(dt)
            if cada_paso:
                cada_paso()

    def avanzar(self, minutos, cada=10, cada_paso=None):
        """A saltos: el reloj avanza `cada` minutos en cada paso (para simular días y semanas)."""
        for _ in range(int(minutos // cada)):
            self.reloj.ahora += datetime.timedelta(minutes=cada)
            self.m.paso(1.0)
            if cada_paso:
                cada_paso()

    def ir_a(self, fecha):
        self.reloj.ahora = fecha
        self.m.paso(1.0)


def k(fecha, fundacion=FUNDACION):
    """El día del hormiguero de una fecha (el que lleva cada línea del diario)."""
    return (fecha - fundacion).days


def mediodia(fecha):
    return datetime.datetime.combine(fecha, datetime.time(12, 0))


class Comprobaciones(unittest.TestCase):

    def comprobar_hormigas(self, m):
        for h in m.hormigas.values():
            self.assertTrue(0 <= h.x < ANCHO and -1 <= h.y < PROF,
                            "%s está fuera del hormiguero: (%s, %s)" % (h.nombre, h.x, h.y))

    def comprobar_diario(self, m):
        m.actualizar_diario()
        dias = [e[0] for e in m.diario]
        self.assertEqual(dias, sorted(dias), "el diario no va en orden")
        self.assertTrue(all(0 <= d <= int(m.dia) for d in dias),
                        "hay líneas del diario de días que no han llegado: %s (hoy %d)" % (dias[-3:], int(m.dia)))
        self.assertTrue(m.diario[0][1].startswith("Se funda el hormiguero"))
        return m.diario

    def textos(self, m, dia=None):
        return [t for d, t in m.diario if dia is None or d == dia]


# ------------------------------------------------------------------ días y semanas

class DiasYSemanas(Comprobaciones):

    def test_dos_semanas_seguidas(self):
        """Dos semanas a saltos de 10 minutos, con un rato fotograma a fotograma cada día:
        cada día están las que tienen que estar (Irene se va el 30 de septiembre)."""
        h = Hormiguero(self, config(nombre="la Oficina", esqueletos=True),
                       oficina(miembros_diseno=("Diego", "Lucía", "Irene")),
                       idos(dict(nombre="Irene", fecha="2026-09-30", epitafio="se fue a otra colonia")),
                       fecha=datetime.datetime(2026, 9, 21, 8, 0))
        todas = {"Ana", "Luis", "Marta", "Elena", "Diego", "Lucía", "Irene"}
        for _ in range(14):
            h.avanzar(5 * 60)    # hasta las 13:00
            h.fino(200)
            h.avanzar(19 * 60)   # hasta las 8:00 del día siguiente
            hoy = h.reloj.ahora.date()
            esperadas = todas - ({"Irene"} if hoy >= datetime.date(2026, 9, 30) else set())
            self.assertEqual(set(h.m.hormigas), esperadas, hoy)
            self.comprobar_hormigas(h.m)
        self.assertEqual(h.m.todos_los_avisos(), [])
        diario = self.comprobar_diario(h.m)
        self.assertEqual(diario[0], (0, "Se funda el hormiguero de la Oficina: Ana, Luis, Marta, Elena, "
                                        "Diego, Lucía, Irene."))
        self.assertIn((k(datetime.date(2026, 9, 30)), "Irene se va del hormiguero. Se fue a otra colonia."),
                      diario)

    def test_ficheros_de_ejemplo_del_repositorio(self):
        """Las salas, idos.toml y calendario.toml del repositorio (sólo se leen) pasan una
        semana sin avisos. config.toml se copia con fundación y semilla fijas."""
        with open(os.path.join(RAIZ, "config.toml"), encoding="utf-8") as f:
            texto = f.read()
        general = tomllib.loads(texto).get("general", {})
        fijas = "".join('%s = %s\n' % (c, v) for c, v in (("fundacion", '"2026-01-01"'), ("semilla", "2026"))
                        if c not in general)
        texto, n = re.subn(r"(?m)^\[general\][ \t]*(#.*)?$", "[general]\n" + fijas, texto, count=1)
        self.assertTrue(n == 1 or not fijas, "no encuentro [general] en config.toml")
        texto = texto.replace('fuente = "openweather"', 'fuente = "estadistico"')
        h = Hormiguero(self, texto, rutas=dict(salas=os.path.join(RAIZ, "salas"),
                                                idos=os.path.join(RAIZ, "idos.toml"),
                                                calendario=os.path.join(RAIZ, "calendario.toml")),
                       fecha=datetime.datetime(2026, 12, 20, 9, 0))
        self.assertTrue(h.m.hormigas)
        h.fino(300)
        h.avanzar(7 * 24 * 60, cada=15)
        h.fino(300)
        self.comprobar_hormigas(h.m)
        self.comprobar_diario(h.m)
        self.assertEqual(h.m.todos_los_avisos(), [])
        self.assertFalse(os.path.exists(h.ruta("local")))

    def test_fechas_y_configuraciones_variadas(self):
        with open(os.path.join(RAIZ, "calendario.toml"), encoding="utf-8") as f:
            fiestas = f.read()
        sur = dict(lat=-33.87, lon=151.21, **zona("Australia/Sydney"))
        polar = dict(lat=69.65, lon=18.96, **zona("Europe/Oslo"))
        casos = [
            ("Nochebuena de noche", datetime.datetime(2026, 12, 24, 23, 30), None, None),
            ("Nochevieja con fuegos", datetime.datetime(2026, 12, 31, 23, 50), None, None),
            ("San Valentín", datetime.datetime(2026, 2, 14, 12, 0), None, None),
            ("hemisferio sur", datetime.datetime(2026, 7, 15, 12, 0), sur, None),
            ("noche polar", datetime.datetime(2026, 12, 21, 12, 0), polar, None),
            ("sol de medianoche", datetime.datetime(2026, 6, 21, 0, 30), polar, None),
            ("nieve", datetime.datetime(2026, 1, 20, 9, 0), None, "nieve"),
            ("tormenta", datetime.datetime(2026, 10, 10, 15, 0), None, "tormenta"),
            ("calima", datetime.datetime(2026, 7, 3, 13, 0), None, "calima"),
            ("cambio de hora de marzo", datetime.datetime(2026, 3, 29, 1, 30), None, None),
            ("cambio de hora de octubre", datetime.datetime(2026, 10, 25, 1, 30), None, None),
            ("antes de la fundación", datetime.datetime(2025, 12, 31, 12, 0), None, None),
            ("años después", datetime.datetime(2030, 6, 1, 12, 0), None, None),
        ]
        for nombre, fecha, ciudad, tiempo in casos:
            with self.subTest(nombre):
                h = Hormiguero(self, config(semilla=len(nombre), ciudad=ciudad), oficina(), "", fiestas,
                               fecha=fecha, tiempo=tiempo)
                h.fino(300)
                h.avanzar(2 * 24 * 60)
                h.fino(300)
                self.assertEqual(set(h.m.hormigas), {"Ana", "Luis", "Marta", "Elena", "Diego", "Lucía"})
                self.comprobar_hormigas(h.m)
                self.comprobar_diario(h.m)
                self.assertEqual(h.m.todos_los_avisos(), [])

    def test_reunion_del_lunes(self):
        h = Hormiguero(self, config(), oficina(), fecha=datetime.datetime(2026, 6, 1, 9, 59, 50))
        self.assertEqual(h.reloj.ahora.weekday(), 0)   # lunes
        h.fino(600)   # pasan las 10:00
        noticias = [n[1] for n in h.m.noticias]
        self.assertIn("Reunión de equipo en la sala Reuniones.", noticias)
        convocadas = [x for x in h.m.hormigas.values() if x.cita]
        self.assertTrue(convocadas)
        self.assertTrue(all(x.cita[0].nombre == "Reuniones" for x in convocadas))
        h.avanzar(24 * 60)
        self.comprobar_hormigas(h.m)

    def test_la_jefa_llama_al_despacho(self):
        """En horario de oficina y un día laborable, la jefa llama a alguien que no esté en
        una reunión (aquí, sin esperar los 10 minutos del principio)."""
        h = Hormiguero(self, config(), oficina(), fecha=datetime.datetime(2026, 6, 2, 11, 0))
        h.m._espera_jefe = 0
        h.fino(40)
        llamadas = [n[1] for n in h.m.noticias if re.fullmatch(r"Elena llama a .+ al despacho\.", n[1])]
        self.assertEqual(len(llamadas), 1, [n[1] for n in h.m.noticias])
        llamada = h.m.hormigas[llamadas[0][len("Elena llama a "):-len(" al despacho.")]]
        self.assertEqual(llamada.cita[0].nombre, "Despacho")
        # el sábado no llama nadie
        h = Hormiguero(self, config(), oficina(), fecha=datetime.datetime(2026, 6, 6, 11, 0))
        h.m._espera_jefe = 0
        h.fino(40)
        self.assertFalse(any("despacho" in n[1] for n in h.m.noticias))


# ------------------------------------------------------------------ sin salas

class SinSalas(Comprobaciones):

    def test_sin_ninguna_sala_pasan_los_dias(self):
        """Sin salas no hay hormigas, pero las obras del año siguen y no casca nada."""
        h = Hormiguero(self, config(), {}, fecha=datetime.datetime(2026, 3, 1, 12, 0))
        self.assertEqual(h.m.hormigas, {})
        self.assertTrue(all(not s.principal for s in h.m.salas))
        h.avanzar(7 * 24 * 60)
        h.fino(500)
        self.assertEqual(h.m.hormigas, {})
        self.assertEqual(h.m.refugio(), h.m.salas[0] if h.m.salas else None)
        self.comprobar_diario(h.m)
        self.assertEqual(h.m.diario[0], (0, "Se funda el hormiguero."))

    def test_sin_salas_ni_obras_los_esqueletos_esperan_en_la_entrada(self):
        """Sin ninguna sala ni obra y lloviendo, el esqueleto de Halloween no tiene adónde
        ir: espera junto a la entrada, y lo que lleva lo guarda en la entrada del nido."""
        dia = datetime.date(2026, 10, 27)
        h = Hormiguero(self, config(fundacion=dia, obras=[], esqueletos=True), {}, idos("Pepe"),
                       fecha=mediodia(dia), tiempo="lluvia")
        m = h.m
        self.assertEqual(m.salas, [])
        self.assertIsNone(m.refugio())
        self.assertIsNone(m.almacen_comida())
        self.assertIsNone(m.frente)
        self.assertFalse(m.de_noche)
        pepe = m.hormigas["Pepe" + CALAVERA]
        self.assertTrue(pepe.esqueleto)
        self.assertIsNone(pepe.sala)
        self.assertEqual((pepe.x, pepe.y), (m.plan.entrada, -1))
        pepe.decidir(m)
        self.assertEqual(pepe.actividad, "entrada")
        destino = pepe.ruta[-1] if pepe.ruta else (pepe.x, pepe.y)
        self.assertEqual(destino[1], -1)
        self.assertLessEqual(abs(destino[0] - m.plan.entrada), 6)
        # lo que lleva a cuestas, a la entrada del nido
        pepe.ruta, pepe.x, pepe.y = [], min(ANCHO - 1, m.plan.entrada + 30), -1
        azucar = Cosa("comida", "azucar", "un azucarillo", pepe.x, ["▪▪"], "blanco_brillante", 2)
        pepe.llevar(m, azucar)
        self.assertEqual(pepe.actividad, "guardar")
        self.assertEqual(pepe.ruta[-1], (m.plan.entrada, -1))
        for _ in range(4000):
            if pepe.carga_cosa is None:
                break
            h.fino(1)
        self.assertIsNone(pepe.carga_cosa)
        self.assertIn("Pepe ☠ ha guardado un azucarillo en el nido.", [n[1] for n in m.noticias])
        # un pájaro: sin refugio, a la entrada
        m.vida._pajaro()
        h.fino(1500)
        h.avanzar(24 * 60)
        self.comprobar_hormigas(m)
        self.comprobar_diario(m)

    def test_sin_comedor_ni_fuente(self):
        """Sólo una sala de trabajo: es el refugio y donde guardan la comida hasta que hay despensa."""
        cfg = config(obras=["despensa"])
        salas = {"trabajo": sala("Trabajo", 2, 34, miembros=["Ana", "Luis", "Marta"])}
        h = Hormiguero(self, cfg, salas, fecha=datetime.datetime(2026, 1, 2, 13, 0))
        m = h.m
        trabajo = m.sala_por_clave["trabajo"]
        self.assertIsNone(m.sala_funcion("comedor"))
        self.assertIsNone(m.sala_funcion("agua"))
        self.assertIs(m.refugio(), trabajo)
        self.assertIs(m.almacen_comida(), trabajo)
        # la hora de comer sin comedor, una araña y una invasión de hormigas rojas
        h.fino(600)
        m.vida._arana()
        m.vida._invasion()
        h.fino(2000)
        # alarma: la que está fuera corre al refugio
        ana = m.hormigas["Ana"]
        ana.escoltando = ana.tarea = ana.carga_cosa = ana.cita = None
        ana.ruta, ana.x, ana.y, ana.actividad = [], 80, -1, "forrajear"
        m.vida.alarma = 10.0
        ana.actualizar(m, 0.05)
        self.assertEqual(ana.actividad, "refugio")
        self.assertEqual(ana.ruta[-1][1], trabajo.piso)
        self.assertIn(ana.ruta[-1][0], trabajo.sitios())
        # cuando se termina la despensa, la comida va allí
        despensa = next(o for o in m.plan.obras if o.tipo == "sala")
        h.ir_a(mediodia(FUNDACION + datetime.timedelta(days=int(despensa.fin) + 1)))
        self.assertEqual(m.almacen_comida().nombre, "Despensa")
        self.assertIs(m.refugio(), trabajo)
        h.avanzar(3 * 24 * 60)
        h.fino(1000)
        self.comprobar_hormigas(m)
        self.comprobar_diario(m)
        self.assertIn("Inauguran: Despensa.", self.textos(m))


# ------------------------------------------------------------------ Halloween

class Halloween(Comprobaciones):

    def _hormiguero(self, esqueletos=True, gente_ida=True):
        salas = {"comedor": sala("Comedor", 1, 30, "comedor"),
                 "trabajo": sala("Trabajo", 2, 34, miembros=["Ana", "Futuro"])}
        ida = idos("Pepe", dict(nombre="Lola", fecha="2026-10-01"),
                   dict(nombre="Futuro", fecha="2026-12-01")) if gente_ida else ""
        return Hormiguero(self, config(esqueletos=esqueletos), salas, ida,
                          fecha=datetime.datetime(2026, 10, 25, 23, 0))

    def test_los_que_se_fueron_vuelven_del_26_al_31_de_octubre(self):
        h = self._hormiguero()
        m = h.m
        self.assertEqual(set(m.hormigas), {"Ana", "Futuro"})
        h.ir_a(datetime.datetime(2026, 10, 26, 2, 0))
        self.assertEqual(set(m.hormigas), {"Ana", "Futuro", "Pepe" + CALAVERA, "Lola" + CALAVERA})
        principales = {s.clave for s in m.plan.salas_todas if s.principal}
        for nombre in ("Pepe" + CALAVERA, "Lola" + CALAVERA):
            esq = m.hormigas[nombre]
            self.assertTrue(esq.esqueleto)
            self.assertIn(esq.sala, principales)
            self.assertNotIn(nombre, m.cumples)
        self.assertFalse(m.hormigas["Futuro"].esqueleto)   # se va en diciembre: aún está

        # de noche los esqueletos no duermen
        def despiertos():
            self.assertFalse(any(x.durmiendo for x in m.hormigas.values() if x.esqueleto))
        self.assertTrue(m.de_noche)
        h.fino(3000, cada_paso=despiertos)
        h.avanzar(3 * 24 * 60, cada_paso=despiertos)
        h.ir_a(datetime.datetime(2026, 10, 31, 23, 0))
        self.assertIn("Lola" + CALAVERA, m.hormigas)
        h.ir_a(datetime.datetime(2026, 11, 1, 2, 0))
        self.assertEqual(set(m.hormigas), {"Ana", "Futuro"})
        h.fino(500)
        self.comprobar_hormigas(m)
        self.comprobar_diario(m)
        aviso = "¡Los que se fueron salen del cementerio! Pasearán por aquí hasta Halloween."
        self.assertEqual([d for d, t in m.diario if t == aviso], [k(datetime.date(2026, 10, 26))])

    def test_sin_esqueletos_en_la_configuracion(self):
        h = self._hormiguero(esqueletos=False)
        h.ir_a(datetime.datetime(2026, 10, 28, 2, 0))
        self.assertEqual(set(h.m.hormigas), {"Ana", "Futuro"})
        self.comprobar_diario(h.m)
        self.assertFalse(any("cementerio" in t for t in self.textos(h.m)))

    def test_sin_nadie_que_se_haya_ido_no_sale_nadie_del_cementerio(self):
        h = self._hormiguero(gente_ida=False)
        h.ir_a(datetime.datetime(2026, 10, 28, 2, 0))
        self.assertEqual(set(h.m.hormigas), {"Ana", "Futuro"})
        self.comprobar_diario(h.m)
        self.assertFalse(any("cementerio" in t for t in self.textos(h.m)))


# ------------------------------------------------------------- cumpleaños y diario

class CumpleanosYDiario(Comprobaciones):

    def test_un_anio_de_cumpleanos_solo_de_quien_esta(self):
        """Día a día durante más de un año: los cumpleaños del hormiguero y los del diario son
        los mismos, y sólo de quien ese día está (ya ha llegado y aún no se ha ido)."""
        miembros = [dict(nombre="Ana", cumple="14-03"),
                    dict(nombre="Sara", cumple="30-01", alta="2026-03-01"),
                    dict(nombre="Irene", cumple="15-10"),
                    dict(nombre="Febe", cumple="29-02"),
                    dict(nombre="Pepe", cumple="01-02")]
        salas = {"comedor": sala("Comedor", 1, 30, "comedor"), "trabajo": sala("Trabajo", 2, 40, miembros=miembros)}
        gente_ida = idos(dict(nombre="Irene", fecha="2026-09-30", epitafio="se fue a otra colonia"), "Pepe")
        h = Hormiguero(self, config(), salas, gente_ida, fecha=mediodia(FUNDACION))
        m = h.m
        self.assertTrue(any("Pepe" in a and "idos.toml" in a for a in m.todos_los_avisos()))
        cumples = {datetime.date(2026, 2, 28): {"Febe"},   # 2026 no es bisiesto: el 28
                   datetime.date(2026, 3, 14): {"Ana"},
                   datetime.date(2027, 1, 30): {"Sara"},   # en 2026 aún no había llegado
                   datetime.date(2027, 2, 28): {"Febe"},
                   datetime.date(2027, 3, 14): {"Ana"}}    # Irene, el 15-10, ya se ha ido
        vistos = {}
        dia = FUNDACION
        while dia <= datetime.date(2027, 3, 15):
            h.ir_a(mediodia(dia))
            esperadas = {"Ana", "Febe"}
            if dia >= datetime.date(2026, 3, 1):
                esperadas.add("Sara")
            if dia < datetime.date(2026, 9, 30):
                esperadas.add("Irene")
            self.assertEqual(set(m.hormigas), esperadas, dia)
            self.assertEqual(set(m.cumples), cumples.get(dia, set()), dia)
            self.assertEqual(int(m.dia), k(dia))
            vistos[k(dia)] = set(m.cumples)
            dia += datetime.timedelta(days=1)
        diario = self.comprobar_diario(m)
        del_diario = {}
        for d, t in diario:
            r = re.fullmatch(r"¡Cumpleaños de (.+)! Hay tarta arriba\.", t)
            if r:
                del_diario.setdefault(d, set()).add(r.group(1))
        self.assertEqual(del_diario, {d: c for d, c in vistos.items() if c})
        self.assertEqual(diario[0], (0, "Se funda el hormiguero: Ana, Irene, Febe."))
        self.assertEqual([(d, t) for d, t in diario if t.startswith("Llega")],
                         [(k(datetime.date(2026, 3, 1)), "Llega Sara al hormiguero. ¡Bienvenida/o!")])
        self.assertEqual([(d, t) for d, t in diario if "se va del hormiguero" in t],
                         [(k(datetime.date(2026, 9, 30)), "Irene se va del hormiguero. Se fue a otra colonia.")])
        self.assertFalse(any("Pepe" in t for _, t in diario))

    def test_cumple_del_29_de_febrero_en_anio_bisiesto(self):
        salas = {"trabajo": sala("Trabajo", 2, miembros=[dict(nombre="Febe", cumple="29-02")])}
        h = Hormiguero(self, config(), salas, fecha=datetime.datetime(2028, 2, 28, 12, 0))
        self.assertEqual(h.m.cumples, [])
        h.ir_a(datetime.datetime(2028, 2, 29, 12, 0))
        self.assertEqual(h.m.cumples, ["Febe"])
        self.comprobar_diario(h.m)
        self.assertIn((k(datetime.date(2028, 2, 29)), "¡Cumpleaños de Febe! Hay tarta arriba."), h.m.diario)
        self.assertNotIn((k(datetime.date(2028, 2, 28)), "¡Cumpleaños de Febe! Hay tarta arriba."), h.m.diario)

    def test_en_su_cumple_sube_a_la_tarta_y_las_demas_la_felicitan(self):
        salas = oficina(miembros_trabajo=(dict(nombre="Ana", cumple="14-03"), "Luis", "Marta"))
        h = Hormiguero(self, config(), salas, fecha=datetime.datetime(2026, 3, 14, 12, 0))
        m = h.m
        self.assertEqual(m.cumples, ["Ana"])
        self.assertFalse(m.de_noche)

        def decisiones(x, veces=60):
            out = []
            for _ in range(veces):
                x.siguiente = x.cita = x.tarea = None
                x.decidir(m)
                out.append((x.actividad, x.ruta[-1] if x.ruta else (x.x, x.y)))
            return out
        ana = decisiones(m.hormigas["Ana"])
        self.assertIn("cumple", [a for a, _ in ana])
        for a, (x, y) in ana:
            if a == "cumple":
                self.assertEqual(y, -1)
                self.assertTrue(m.x_cumple - 2 <= x <= m.x_cumple + 16)
        self.assertIn("felicitar", [a for a, _ in decisiones(m.hormigas["Luis"])])
        h.fino(1500)
        self.comprobar_hormigas(m)

    def test_altas_y_bajas_con_fecha(self):
        miembros = ["Ana", dict(nombre="Bea", alta="2026-02-10"), dict(nombre="Carla", alta="2025-06-01"),
                    dict(nombre="Dani", alta="2026-01-01"), "Eva"]
        salas = {"comedor": sala("Comedor", 1, 30, "comedor"), "trabajo": sala("Trabajo", 2, 40, miembros=miembros)}
        gente_ida = idos(dict(nombre="Eva", fecha="2026-02-20", epitafio="¡hasta pronto!"),
                         dict(nombre="Futuro", fecha="2026-12-01"))
        h = Hormiguero(self, config(), salas, gente_ida, fecha=datetime.datetime(2026, 2, 9, 12, 0))
        m = h.m
        aviso = ("idos.toml: Futuro se va el 2026-12-01, pero ya no está en ninguna sala; "
                 "déjalo en la suya hasta ese día")
        self.assertIn(aviso, m.todos_los_avisos())
        self.assertEqual(set(m.hormigas), {"Ana", "Carla", "Dani", "Eva"})
        h.fino(300)
        h.avanzar(12 * 60 - 10)
        self.assertNotIn("Bea", m.hormigas)
        h.ir_a(datetime.datetime(2026, 2, 10, 0, 0, 30))   # llega a medianoche, a su sala
        self.assertEqual(set(m.hormigas), {"Ana", "Bea", "Carla", "Dani", "Eva"})
        bea = m.hormigas["Bea"]
        trabajo = m.sala_por_clave["trabajo"]
        self.assertEqual((bea.y, bea.sala), (trabajo.piso, "trabajo"))
        self.assertTrue(m.plan.suelo_en(bea.x, bea.y))
        h.fino(300)
        h.ir_a(datetime.datetime(2026, 2, 19, 23, 0))
        self.assertIn("Eva", m.hormigas)
        h.ir_a(datetime.datetime(2026, 2, 20, 1, 0))
        self.assertEqual(set(m.hormigas), {"Ana", "Bea", "Carla", "Dani"})
        h.fino(300)
        diario = self.comprobar_diario(m)
        self.assertEqual(diario[0], (0, "Se funda el hormiguero: Ana, Carla, Dani, Eva."))
        self.assertEqual([(d, t) for d, t in diario if t.startswith("Llega")],
                         [(k(datetime.date(2026, 2, 10)), "Llega Bea al hormiguero. ¡Bienvenida/o!")])
        self.assertIn((k(datetime.date(2026, 2, 20)), "Eva se va del hormiguero. ¡Hasta pronto!"), diario)
        self.assertIn(aviso, m.todos_los_avisos())
        h.ir_a(datetime.datetime(2026, 12, 2, 12, 0))   # ya pasó su fecha: el aviso se va solo
        self.assertNotIn(aviso, m.todos_los_avisos())
        self.assertIn((k(datetime.date(2026, 12, 1)), "Futuro se va del hormiguero. Se fue, pero no lo olvidamos."),
                      self.comprobar_diario(m))

    def test_epitafios(self):
        gente_ida = idos(dict(nombre="Lola", fecha="2026-02-10", epitafio="¡hasta pronto!"),
                         dict(nombre="Max", fecha="2026-02-11"),
                         dict(nombre="Leo", fecha="2026-02-12", epitafio="«adiós»"),
                         dict(nombre="Eva", fecha="2026-02-13", epitafio="   "),
                         dict(nombre="Bea", fecha="2026-02-14", epitafio="se fue a otra colonia"),
                         dict(nombre="Teo", fecha="2026-02-15", epitafio="¿volverá?"))
        salas = {"trabajo": sala("Trabajo", 2, miembros=["Lola", "Max", "Leo", "Eva", "Bea", "Teo"])}
        h = Hormiguero(self, config(), salas, gente_ida, fecha=datetime.datetime(2026, 3, 1, 12, 0))
        self.assertEqual(h.m.hormigas, {})
        diario = self.comprobar_diario(h.m)
        esperadas = [(40, "Lola se va del hormiguero. ¡Hasta pronto!"),
                     (41, "Max se va del hormiguero. Se fue, pero no lo olvidamos."),
                     (42, "Leo se va del hormiguero. «Adiós»"),
                     (43, "Eva se va del hormiguero. Se fue, pero no lo olvidamos."),
                     (44, "Bea se va del hormiguero. Se fue a otra colonia."),
                     (45, "Teo se va del hormiguero. ¿Volverá?")]
        self.assertEqual([e for e in diario if "se va del hormiguero" in e[1]], esperadas)

    def test_dias_relativos(self):
        """Cada línea del diario lleva el día del hormiguero en que pasó (contado desde la
        fundación); la pantalla dice cuándo fue restándolo de hoy (Hoy, Ayer, Hace N días)."""
        fundacion = datetime.date(2025, 12, 20)
        salas = {"trabajo": sala("Trabajo", 2, miembros=[dict(nombre="Ana", cumple="14-03")])}
        h = Hormiguero(self, config(fundacion=fundacion), salas, fecha=datetime.datetime(2026, 3, 14, 0, 30))
        m = h.m
        cumple = "¡Cumpleaños de Ana! Hay tarta arriba."
        dia_cumple = k(datetime.date(2026, 3, 14), fundacion)
        self.assertEqual(dia_cumple, 84)
        for fecha, hace in ((datetime.datetime(2026, 3, 14, 0, 30), 0), (datetime.datetime(2026, 3, 14, 23, 59), 0),
                            (datetime.datetime(2026, 3, 15, 0, 1), 1), (datetime.datetime(2026, 3, 24, 12, 0), 10)):
            h.ir_a(fecha)
            diario = self.comprobar_diario(m)
            self.assertEqual([d for d, t in diario if t == cumple], [dia_cumple])
            self.assertEqual(int(m.dia) - dia_cumple, hace, fecha)
        m.noticia("Algo acaba de pasar.")
        self.assertEqual(m.noticias[-1][:2], (int(m.dia), "Algo acaba de pasar."))


# ------------------------------------------------------------- recarga en caliente

class Recarga(Comprobaciones):

    SALAS = {"comedor": sala("Comedor", 1, 30, "comedor"),
             "trabajo": sala("Trabajo", 2, 34, miembros=[dict(nombre="Ana", color="naranja"), "Luis", "Marta"]),
             "diseno": sala("Diseño", 3, 30, miembros=["Diego"])}

    def _hormiguero(self, real=False):
        h = Hormiguero(self, config(semilla=11), self.SALAS, fecha=datetime.datetime(2026, 3, 10, 11, 0), real=real)
        h.fino(3000)
        return h

    @staticmethod
    def _foto(m):
        return {n: (x, x.x, x.y, x.actividad, list(x.ruta), x.espera, x.tarea, x.carga_cosa, x.escoltando, x.sala)
                for n, x in m.hormigas.items()}

    def test_recarga_conserva_las_hormigas(self):
        h = self._hormiguero()
        m = h.m
        antes = self._foto(m)
        marta = m.hormigas["Marta"]
        # Ana cambia de color, Luis se pasa a Diseño, llega Nuevo, Marta se va hoy y empieza una fiesta
        h.escribir("salas/trabajo.toml", sala("Trabajo", 2, 34, miembros=[
            dict(nombre="Ana", color="cian"), dict(nombre="Nuevo", alta="2026-03-10")]))
        h.escribir("salas/diseno.toml", sala("Diseño", 3, 30, miembros=["Diego", "Luis"]))
        h.escribir("idos.toml", idos(dict(nombre="Marta", fecha="2026-03-10", epitafio="hasta luego")))
        h.escribir("calendario.toml", calendario(dict(nombre="Fiesta", desde="10-03", hasta="11-03",
                                                       decoracion="banderines", mensaje="¡Fiesta de prueba!")))
        h.recargar()
        self.assertEqual(set(m.hormigas), {"Ana", "Luis", "Diego", "Nuevo"})
        for n in ("Ana", "Luis", "Diego"):
            x = m.hormigas[n]
            self.assertIs(x, antes[n][0], n)
            self.assertEqual((x.x, x.y, x.actividad, list(x.ruta), x.espera, x.tarea, x.carga_cosa),
                             antes[n][1:8], "%s se ha movido al recargar" % n)
        self.assertEqual(m.hormigas["Luis"].sala, "diseno")
        self.assertEqual(m.hormigas["Ana"].color, color("cian"))
        self.assertEqual(m.hormigas["Diego"].sala, "diseno")
        nuevo = m.hormigas["Nuevo"]
        self.assertEqual((nuevo.sala, nuevo.y), ("trabajo", m.sala_por_clave["trabajo"].piso))
        self.assertTrue(m.plan.suelo_en(nuevo.x, nuevo.y))
        # Marta ha soltado lo que hacía: nadie la espera y, en cuanto se mueven, nadie la sigue
        for c in m.vida.cosas + m.vida.enemigos:
            self.assertNotIn(marta, c.asignadas)
        self.assertIsNone(marta.carga_cosa)
        self.assertEqual(m.fiesta_mensaje, "¡Fiesta de prueba!")
        h.fino(1)
        self.assertFalse(any(x.escoltando and x.escoltando[0] is marta for x in m.hormigas.values()))
        hoy = int(m.dia)
        diario = self.comprobar_diario(m)
        self.assertIn((hoy, "Llega Nuevo al hormiguero. ¡Bienvenida/o!"), diario)
        self.assertIn((hoy, "Marta se va del hormiguero. Hasta luego."), diario)
        self.assertIn((hoy, "¡Fiesta de prueba!"), diario)
        self.assertEqual(m.todos_los_avisos(), [])
        h.fino(3000)
        h.avanzar(7 * 24 * 60)
        self.assertEqual(set(m.hormigas), {"Ana", "Luis", "Diego", "Nuevo"})
        self.comprobar_hormigas(m)

    def test_recarga_sin_cambios_no_toca_nada(self):
        h = self._hormiguero()
        m = h.m
        antes = self._foto(m)
        diario = list(self.comprobar_diario(m))
        h.recargar()
        despues = self._foto(m)
        self.assertEqual(despues.keys(), antes.keys())
        for n in antes:
            self.assertIs(despues[n][0], antes[n][0])
            self.assertEqual(despues[n][1:], antes[n][1:], n)
        self.assertEqual(self.comprobar_diario(m), diario)

    def test_recarga_con_una_sala_nueva(self):
        """Una sala nueva no se excava hasta reiniciar, pero su gente sale ya (en el refugio)."""
        h = self._hormiguero()
        m = h.m
        h.escribir("salas/nueva.toml", sala("Nueva", 3, 20, miembros=["Nora"]))
        h.recargar()
        nora = m.hormigas["Nora"]
        self.assertEqual(nora.sala, "nueva")
        self.assertNotIn("nueva", m.sala_por_clave)
        self.assertIs(nora.sala_propia(m), m.refugio())
        self.assertTrue(m.plan.suelo_en(nora.x, nora.y))
        h.fino(2000)
        h.avanzar(2 * 24 * 60)
        self.comprobar_hormigas(m)
        self.assertIn("Nora", m.hormigas)

    def test_recarga_con_un_alta_mal_escrita_avisa(self):
        h = self._hormiguero()
        h.escribir("salas/diseno.toml", sala("Diseño", 3, 30, miembros=["Diego", dict(nombre="Rosa", alta="2026-13-45")]))
        h.recargar()
        self.assertIn("salas/diseno.toml: Rosa: fecha de alta mal escrita (2026-13-45), usa AAAA-MM-DD",
                      h.m.todos_los_avisos())
        self.assertIn("Rosa", h.m.hormigas)   # sin fecha válida, está desde siempre
        h.fino(500)
        h.escribir("salas/diseno.toml", sala("Diseño", 3, 30, miembros=["Diego", "Rosa"]))
        h.recargar()
        self.assertEqual(h.m.todos_los_avisos(), [])

    def test_recarga_con_el_estado_quitar_el_color_fijo(self):
        """Con el reloj de verdad (estado en la carpeta temporal), quien pierde su color fijo
        pasa a tener uno de la paleta, sin moverse."""
        h = self._hormiguero(real=True)
        m = h.m
        ana = m.hormigas["Ana"]
        sitio = (ana.x, ana.y)
        self.assertEqual(ana.color, color("naranja"))
        h.escribir("salas/trabajo.toml", sala("Trabajo", 2, 34, miembros=["Ana", "Luis", "Marta"]))
        h.recargar()
        self.assertIs(m.hormigas["Ana"], ana)
        self.assertEqual((ana.x, ana.y), sitio)
        self.assertNotEqual(ana.color, color("naranja"))
        self.assertEqual(ana.color, color(m.estado.colores["Ana"]))


# ------------------------------------------------------------- obras: dia_obras

class Obras(Comprobaciones):

    SALAS = {"comedor": sala("Comedor", 1, 30, "comedor"),
             "trabajo": sala("Trabajo", 2, 34, miembros=["Ana", "Luis"])}

    def test_cavar_fecha_va_con_los_dias(self):
        h = Hormiguero(self, config(semilla=11, cavar="fecha"), self.SALAS, real=True)
        m = h.m
        self.assertIsNotNone(m.estado)
        self.assertFalse(m.cava_encendido())
        self.assertEqual(m.dia_obras, m.dia)
        h.avanzar(2 * 24 * 60)
        self.assertEqual(m.dia_obras, m.dia)
        hechas = {o.sala.nombre for o in m.plan.obras if o.tipo == "sala" and o.fin <= m.dia}
        self.assertTrue(hechas)   # el 1 de junio ya hay alguna sala de las obras
        self.assertEqual({s.nombre for s in m.salas if not s.principal}, hechas)
        self.assertEqual(os.path.dirname(m.estado.ruta), h.ruta("local"))

    def test_cavar_encendido_con_reloj_simulado_va_con_los_dias(self):
        """En la demo o con --fecha no hay estado: las obras van con los días."""
        h = Hormiguero(self, config(semilla=11, cavar="encendido"), self.SALAS)
        self.assertIsNone(h.m.estado)
        self.assertFalse(h.m.cava_encendido())
        self.assertEqual(h.m.dia_obras, h.m.dia)
        h.avanzar(24 * 60)
        self.assertEqual(h.m.dia_obras, h.m.dia)
        self.assertFalse(os.path.exists(h.ruta("local")))   # nada que guardar

    def test_cavar_encendido_solo_cuenta_lo_que_esta_en_marcha(self):
        h = Hormiguero(self, config(semilla=11, cavar="ENCENDIDO"), self.SALAS, real=True)
        m = h.m
        self.assertTrue(m.cava_encendido())
        self.assertGreater(m.dia, 150)
        self.assertEqual(m.dia_obras, 0.0)
        self.assertTrue(all(s.principal for s in m.salas))
        h.avanzar(3 * 60, cada=1)   # tres horas en marcha
        self.assertAlmostEqual(m.dia_obras, 3 / 24, places=9)
        h.ir_a(h.reloj.ahora + datetime.timedelta(hours=6))   # un salto (apagado, suspensión...)
        self.assertAlmostEqual(m.dia_obras, 3 / 24, places=9)
        h.ir_a(h.reloj.ahora - datetime.timedelta(minutes=2))   # el reloj vuelve atrás
        self.assertAlmostEqual(m.dia_obras, 3 / 24, places=9)
        m.estado.guardar(m.hormigas.values())
        with open(h.ruta(os.path.join("local", "estado.json")), encoding="utf-8") as f:
            guardado = json.load(f)["hormigueros"]["2026-01-01-11"]
        self.assertAlmostEqual(guardado["obras"]["dias"], 3 / 24, places=9)
        # al reiniciar días después sigue por donde iba, no por la fecha
        h.reloj.ahora = datetime.datetime(2026, 6, 20, 12, 0)
        h.m = m2 = h.arrancar()
        self.assertAlmostEqual(m2.dia_obras, 3 / 24, places=9)
        h.avanzar(60, cada=1)
        self.assertAlmostEqual(m2.dia_obras, 3 / 24 + 1 / 24, places=9)

    def _sembrar_estado(self, h, dias, posiciones=None, acabadas=None):
        datos = {"inicio": {}, "colores": {},
                 "hormigueros": {"2026-01-01-11": {"fundacion": "2026-01-01", "semilla": 11,
                                                   "obras": {"dias": dias, "acabadas": acabadas or {}},
                                                   "posiciones": posiciones or {}}}}
        os.makedirs(h.ruta("local"), exist_ok=True)
        with open(h.ruta(os.path.join("local", "estado.json")), "w", encoding="utf-8") as f:
            json.dump(datos, f)

    def _primera_sala(self, h):
        return next((i, o) for i, o in enumerate(h.m.plan.obras) if o.tipo == "sala")

    def test_cavar_encendido_el_diario_dice_el_dia_en_que_se_termino(self):
        cfg = config(semilla=11, cavar="encendido")
        h = Hormiguero(self, cfg, self.SALAS)   # sin estado: sólo para ver el plan de obras
        i, sala_obra = self._primera_sala(h)
        self._sembrar_estado(h, sala_obra.fin + 0.01)
        h.reloj.real = True
        h.m = m = h.arrancar()
        self.assertIn(sala_obra.sala.nombre, [s.nombre for s in m.salas])
        hoy = int(m.dia)
        self.assertNotEqual(hoy, int(sala_obra.fin))
        self.assertEqual(m.estado.acabadas["%d %s" % (i, sala_obra.nombre)], hoy)
        inaugura = "Inauguran: %s." % sala_obra.sala.nombre
        self.assertEqual([d for d, t in self.comprobar_diario(m) if t == inaugura], [hoy])
        # al reiniciar otro día, el diario sigue diciendo el día en que se terminó
        h.reloj.ahora = datetime.datetime(2026, 6, 5, 12, 0)
        h.m = m2 = h.arrancar()
        self.assertEqual([d for d, t in self.comprobar_diario(m2) if t == inaugura], [hoy])

    def test_al_reiniciar_conservan_color_y_sitio(self):
        h = Hormiguero(self, config(semilla=11, cavar="encendido"), self.SALAS, real=True)
        h.fino(600)
        m = h.m
        colores = {n: x.color for n, x in m.hormigas.items()}
        self.assertEqual(len(set(colores.values())), len(colores))
        m.estado.guardar(m.hormigas.values())   # como al parar el hormiguero
        sitios = {n: (x.x, x.y) for n, x in m.hormigas.items()}
        h.reloj.ahora += datetime.timedelta(minutes=1)
        h.m = m2 = h.arrancar()
        self.assertEqual({n: x.color for n, x in m2.hormigas.items()}, colores)
        for n, (x, y) in sitios.items():
            if m2.plan.suelo_en(x, y):
                self.assertEqual((m2.hormigas[n].x, m2.hormigas[n].y), (x, y), n)

    # si al arrancar se da por terminada alguna obra (p. ej. tras cambiar [nido] obras en
    # config.toml, o con un estado.json sin "acabadas"), se guarda el estado cuando aún no hay
    # hormigas: antes se guardaban unas posiciones vacías y no volvían al sitio donde estaban
    def test_obra_terminada_al_arrancar_no_borra_donde_estaban(self):
        h = Hormiguero(self, config(semilla=11, cavar="encendido"), self.SALAS)
        _i, sala_obra = self._primera_sala(h)
        sitios = {"Ana": [100, -1], "Luis": [60, -1]}   # en la superficie: siempre se puede pisar
        self._sembrar_estado(h, sala_obra.fin + 0.01, posiciones=sitios)
        h.reloj.real = True
        h.m = m = h.arrancar()
        self.assertEqual({n: [x.x, x.y] for n, x in m.hormigas.items()}, sitios)

    def test_config_ilegible_sigue_cavando_como_la_ultima_vez(self):
        # con cavar = "fecha", una errata que deja config.toml sin leer no lo vuelve a cavar
        # "encendido" (antes se veía de golpe recién fundado: lo cavado encendido era 0)
        h = Hormiguero(self, config(semilla=11, cavar="fecha"), self.SALAS, real=True)
        h.m.estado.guardar(h.m.hormigas.values())
        h.escribir("config.toml", "[general]\n[general]\n")
        with mock.patch.object(A, "RAIZ", h.dir):   # el estado de verdad, el de la carpeta de la prueba
            h.m = m = h.arrancar()
        self.assertTrue(m.cfg["config_ilegible"])
        self.assertEqual((m.fundacion.isoformat(), m.semilla), ("2026-01-01", 11))
        self.assertFalse(m.cava_encendido())
        self.assertEqual(m.dia_obras, m.dia)

    def test_el_reloj_simulado_no_escribe_nada(self):
        h = Hormiguero(self, config(cavar="encendido", esqueletos=True), oficina(), idos("Pepe"),
                       fecha=datetime.datetime(2026, 10, 27, 12, 0))
        self.assertIsNone(h.m.estado)
        h.fino(500)
        h.avanzar(24 * 60)
        self.assertFalse(os.path.exists(h.ruta("local")))


# ------------------------------------------------------------ fallos que hubo

class FallosArreglados(Comprobaciones):

    # un alta escrita como fecha y hora de TOML (alta = 2026-03-01T09:00:00, sin comillas, que es
    # TOML válido) vale por el día; antes mundo._fecha la dejaba con la hora y al compararla con
    # la fecha de hoy el hormiguero no arrancaba (TypeError)
    def test_alta_con_fecha_y_hora_de_toml_no_casca(self):
        salas = {"trabajo": sala("Trabajo", 2, miembros=[dict(nombre="Ana", alta=Crudo("2026-03-01T09:00:00"))])}
        h = Hormiguero(self, config(), salas, fecha=datetime.datetime(2026, 6, 1, 12, 0))
        h.fino(200)
        self.assertIn("Ana", h.m.hormigas)
        self.comprobar_diario(h.m)

    # lo mismo con la fecha de idos.toml (fecha = 2026-09-30 18:00:00): antes el hormiguero no
    # arrancaba y, si se escribía así con el hormiguero en marcha, se paraba tras recargar
    def test_baja_con_fecha_y_hora_de_toml_no_casca(self):
        salas = {"trabajo": sala("Trabajo", 2, miembros=["Ana", "Irene"])}
        h = Hormiguero(self, config(), salas, idos(dict(nombre="Irene", fecha=Crudo("2026-09-30 18:00:00"))),
                       fecha=datetime.datetime(2026, 6, 1, 12, 0))
        h.fino(200)
        h.ir_a(datetime.datetime(2026, 10, 5, 12, 0))
        self.assertIn("Ana", h.m.hormigas)
        self.comprobar_diario(h.m)

    # el color de quien llega más tarde (alta con fecha, o alguien nuevo al recargar) es el menos
    # usado contando los de todas las que están; antes sólo contaba los de las que van antes que
    # ella en las salas y repetía el de otra aunque quedaran libres (Sara, el de Diego)
    def test_quien_llega_tarde_no_repite_color_si_quedan_libres(self):
        salas = {"a": sala("A", 2, miembros=["Ana", dict(nombre="Sara", alta="2026-03-01")]),
                 "b": sala("B", 3, miembros=["Diego", "Lucía"])}
        h = Hormiguero(self, config(), salas, fecha=datetime.datetime(2026, 2, 27, 12, 0), real=True)
        self.assertEqual(len({x.color for x in h.m.hormigas.values()}), 3)
        h.ir_a(datetime.datetime(2026, 3, 1, 12, 0))
        colores = {n: x.color for n, x in h.m.hormigas.items()}
        self.assertEqual(len(colores), 4)
        self.assertEqual(len(set(colores.values())), 4, colores)

    # en Halloween, los esqueletos se pasean: ni van a las reuniones ni los llama el jefe (antes
    # iban a las de «todos» y el jefe podía llamarlos, o llamar él si era uno)
    def test_los_esqueletos_ni_van_a_reuniones_ni_al_despacho(self):
        salas = oficina()
        salas["reuniones"] = sala("Reuniones", 1, 30, "reuniones", reuniones=[
            {"nombre": "Café", "dia": "todos", "hora": "10:00", "minutos": 60, "quien": "todos"}])
        h = Hormiguero(self, config(esqueletos=True), salas, idos("Pepe", "Juan"),
                       fecha=datetime.datetime(2026, 10, 27, 9, 59))
        m = h.m
        esqueletos = [x for x in m.hormigas.values() if x.esqueleto]
        self.assertEqual(len(esqueletos), 2)
        h.fino(90, dt=1.0)   # pasan las 10:00: la reunión es de todos (salvo quien lleva algo a cuestas)
        self.assertTrue(any(x.cita for x in m.hormigas.values() if not x.esqueleto))
        self.assertTrue(all(x.cita is None for x in esqueletos))
        for x in m.hormigas.values():   # sin citas, cualquiera podría ir al despacho
            x.cita = None
        for _ in range(20):   # más llamadas que hormigas: al final sólo quedarían los esqueletos
            m._espera_jefe = 0
            m._citas()
        self.assertTrue(all(x.cita is None for x in esqueletos))

    def test_nombre_que_empieza_por_el(self):
        h = Hormiguero(self, config(nombre="el Taller"), {"trabajo": sala("Trabajo", 2, miembros=["Ana"])})
        self.comprobar_diario(h.m)
        self.assertEqual(h.m.diario[0], (0, "Se funda el hormiguero del Taller: Ana."))

    def test_tiempo_forzado_manda_en_charcos_y_diario(self):
        # con --tiempo lluvia hay charcos (antes salían del modelo de respaldo, no del tiempo elegido)
        for tiempo, llovio in (("lluvia", True), ("tormenta", True), ("despejado", False)):
            with self.subTest(tiempo=tiempo):
                h = Hormiguero(self, config(), {"trabajo": sala("Trabajo", 2, miembros=["Ana"])}, tiempo=tiempo)
                self.assertIs(h.m.llovio, llovio)
                self.assertIs(h.m.llovio_semana, llovio)
                hoy = [t for d, t in self.comprobar_diario(h.m) if d == int(h.m.dia)]
                self.assertEqual("Tormenta. Todas dentro." in hoy, tiempo == "tormenta", hoy)

    def test_mueble_nuevo_en_el_diario(self):
        texto = sala("Trabajo", 2, miembros=["Ana"]) + '\n[[mueble]]\npieza = "sofa"\naparece = 10\n' \
                                                      '\n[[mueble]]\npieza = "planta"\naparece = 20\nnombre = "un ficus"\n'
        h = Hormiguero(self, config(), {"trabajo": texto})
        diario = self.comprobar_diario(h.m)
        self.assertIn((10, "Novedad en Trabajo: un sofá."), diario)
        self.assertIn((20, "Novedad en Trabajo: un ficus."), diario)


if __name__ == "__main__":
    unittest.main()
