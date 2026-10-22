"""Pruebas del dibujo en pixel art (pixel/): que Render.dibujar no falle nunca.

Se dibuja el hormiguero con fechas y horas de todo tipo, con el tiempo forzado (nieve, lluvia,
tormenta, calima...), en latitudes extremas (sol de medianoche y noche polar), con todas las
decoraciones de fiesta y todos los gorros, en salas estrechas con todos los muebles y con todas
las piezas del paisaje. También se prueban las capturas (--captura), el volcado al framebuffer
(hormiguero_fb.py, con un fichero en lugar de /dev/fb0), la galería de herramientas/ y lo que
tarda un fotograma.

Sin pantalla (SDL_VIDEODRIVER=dummy), sin red y sin la hora de verdad: todo usa fechas fijas y
lo que se escribe va a directorios temporales (nunca a local/ ni a docs/).

    SDL_VIDEODRIVER=dummy python3 -m unittest tests.test_dibujo -v
"""

import contextlib
import copy
import datetime
import importlib
import importlib.util
import io
import itertools
import math
import os
import re
import shutil
import signal
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

from hormiga import clima_real as CR  # noqa: E402
from hormiga import estado as E  # noqa: E402
from hormiga import fiestas as F  # noqa: E402
from hormiga import tiempo as T  # noqa: E402
from hormiga.mundo import Mundo  # noqa: E402
from hormiga.tierra import ANCHO, ANCHO_MIN, OBJETOS  # noqa: E402
from pixel import app as APP  # noqa: E402
from pixel import muebles as MU  # noqa: E402
from pixel import paisaje as PA  # noqa: E402
from pixel.base import CH, CLAVE, CW, Letras, superficie  # noqa: E402
from pixel.render import Render  # noqa: E402

W, H = 640, 512                 # la imagen interna del hormiguero
FECHA_BASE = "2026-06-15 12:00"
SIN_COLOR = (1, 2, 3)           # fondo para ver qué pinta cada pieza
# las salas de las obras, si no caben, se estrechan hasta 14 columnas como mucho (hormiga/tierra.py)
ANCHO_OBRA_MIN = ANCHO_MIN
LATITUDES = (90, 89.99, 78.2, 66.56, 45, 0, -33.9, -66.56, -78.2, -89.99, -90)
# un framebuffer de 16 bits (RGB565) y uno de 32 (XRGB): (desplazamiento, longitud) de cada canal
CANALES = {16: ((11, 5), (5, 6), (0, 5)), 32: ((16, 8), (8, 8), (0, 8))}

_parches = []
_tmp = None
_sys_path = []
CONFIG = None


def repo(nombre):
    return os.path.join(RAIZ, nombre)


def _config_de_prueba():
    """Un config.toml con fundación y semilla fijas (así no se lee local/estado.json), el tiempo
    estadístico (sin internet) y todas las piezas del paisaje repartidas por la superficie."""
    lineas = [
        "[general]", 'nombre = "las pruebas"', 'fundacion = "2026-01-01"', "semilla = 2026", "fps_pixel = 20", "",
        "[ciudad]", 'nombre = "Málaga"', "lat = 36.72", "lon = -4.42", 'zona_horaria = "Europe/Madrid"', "",
        "[tiempo]", 'fuente = "estadistico"', "",
        "[horario]", 'desayuno = "10:30-11:00"', 'comida = "13:30-15:30"', 'jornada = "09:00-18:00"', "",
        "[nido]", "entrada = 20", 'cavar = "fecha"',
        'obras = ["despensa", "museo", "hongos", "almacen", "biblioteca"]', "",
        "[halloween]", "esqueletos = true", "",
        "[paisaje]", "montes = true", "costa = true", "cementerio = 74",
    ]
    for tabla, piezas in (("suelo", list(PA.SUELO)), ("fondo", list(PA.FONDO))):
        for i, pieza in enumerate(piezas):
            lineas += ["", "[[paisaje.%s]]" % tabla, 'pieza = "%s"' % pieza,
                       "x = %d" % round(5 + i * 90 / max(1, len(piezas) - 1))]
    return "\n".join(lineas) + "\n"


def setUpModule():
    global _tmp, CONFIG
    _sys_path[:] = sys.path   # pixel.app.preparar añade la raíz a sys.path en cada llamada
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((W, H))
    _tmp = tempfile.TemporaryDirectory(prefix="ant-farm-dibujo-")
    CONFIG = os.path.join(_tmp.name, "config.toml")
    with open(CONFIG, "w", encoding="utf-8") as f:
        f.write(_config_de_prueba())
    # nunca a internet (OpenWeather) ni a local/estado.json, aunque una fecha coincida con la de hoy
    for p in (mock.patch.object(CR, "desde_config", return_value=None),
              mock.patch.object(E, "_escribir", side_effect=AssertionError("no se debe escribir en local/"))):
        p.start()
        _parches.append(p)


def tearDownModule():
    while _parches:
        _parches.pop().stop()
    _tmp.cleanup()
    sys.path[:] = _sys_path


# ===================================================================== utilidades

def momento(texto):
    return datetime.datetime.strptime(texto, "%Y-%m-%d %H:%M")


_cargados = {}


def cargar(salas=None, tipos=None, idos=None, calendario=None, config=None, fresco=False):
    """Lee los ficheros como el hormiguero (pixel.app.preparar), sin estado guardado.
    Devuelve una copia de (cfg, salas, idos, fiestas, avisos)."""
    rutas = (config or CONFIG, salas or repo("salas"), tipos or repo("tipos"), idos or repo("idos.toml"),
             calendario or repo("calendario.toml"))
    if fresco or rutas not in _cargados:
        args = APP.argumentos(["--fecha", "2026-06-15", "--hora", "12:00", "-c", rutas[0], "--salas", rutas[1],
                               "--tipos", rutas[2], "--idos", rutas[3], "--calendario", rutas[4]])
        args.sin_estado = True
        _cargados[rutas] = APP.preparar(args)[1:]
    return copy.deepcopy(_cargados[rutas])


def fiestas(*lista, avisos=None):
    """Fiestas de un calendario (como [[fiesta]] de calendario.toml), por defecto el 15 de junio."""
    datos = []
    for d in lista:
        d = dict(d)
        d.setdefault("desde", "15-06")
        d.setdefault("nombre", "Fiesta de %s" % d.get("decoracion", "prueba"))
        datos.append(d)
    return F.cargar({"fiesta": datos}, avisos)


class Escena:
    """Un hormiguero listo para dibujar, con el reloj parado en una fecha fija (se mueve a mano)."""

    def __init__(self, cuando=FECHA_BASE, tiempo=None, ciudad=None, paisaje=None, nido=None, idos=None,
                 fiestas=None, **ficheros):
        self.ahora = momento(cuando)
        cfg, salas, idos_cfg, fiestas_cfg, avisos = cargar(**ficheros)
        if tiempo:
            cfg["tiempo_forzado"] = tiempo
        cfg["ciudad"].update(ciudad or {})
        cfg["nido"].update(nido or {})
        if paisaje is not None:
            cfg["paisaje"] = paisaje
        self.avisos_carga = list(avisos)
        self.m = Mundo(cfg, salas, idos_cfg if idos is None else idos, fiestas_cfg if fiestas is None else fiestas,
                       APP.PantallaNula(), lambda: self.ahora, avisos)
        self.m.superficie.rng.seed(1)
        self.m.vida.rng.seed(1)
        self.pantalla = pygame.Surface((W, H))
        self.r = Render(self.m, self.pantalla)
        self.r.rng.seed(1)

    def ir_a(self, cuando):
        self.ahora = momento(cuando) if isinstance(cuando, str) else cuando
        self.m.actualizar_contexto(forzar=True)

    def fotogramas(self, n=1, dt=0.05):
        for _ in range(n):
            self.ahora += datetime.timedelta(seconds=dt)
            self.m.paso(dt)
            self.r.dibujar()
        return self.pantalla

    def rect_sala(self, sala):
        return self.r._rect_sala(sala).move(0, self.r.G)


def colores(s, paso=16):
    """Cuántos colores distintos hay en una muestra de la imagen (una vacía tiene uno)."""
    w, h = s.get_size()
    return len({tuple(s.get_at((x, y)))[:3] for x in range(0, w, paso) for y in range(0, h, paso)})


def brillo(s, rect):
    r, g, b = pygame.transform.average_color(s, rect)[:3]
    return (r + g + b) / 3


def pintado(s, fondo=SIN_COLOR):
    """El rectángulo que abarca todo lo que no es del color de fondo (None si no hay nada)."""
    mascara = pygame.mask.from_threshold(s, fondo, (1, 1, 1, 255))
    mascara.invert()
    rects = mascara.get_bounding_rects()
    return rects[0].unionall(rects[1:]) if rects else None


def bytes_de(s):
    return (getattr(pygame.image, "tobytes", None) or pygame.image.tostring)(s, "RGB")


@contextlib.contextmanager
def textos_dibujados(render):
    """Apunta los textos que pide el render (Letras.texto): [(texto, color, tamaño, imagen)]."""
    vistos = []
    original = render.letras.texto

    def texto(t, color, tam=9, *a, **k):
        img = original(t, color, tam, *a, **k)
        vistos.append((t, color, tam, img))
        return img
    with mock.patch.object(render.letras, "texto", texto):
        yield vistos


def carpeta(base, nombre, ficheros, copiar_de=None):
    """base/nombre con los ficheros {nombre: texto} (y, si se da, una copia de otra carpeta)."""
    d = os.path.join(base, nombre)
    if copiar_de:
        shutil.copytree(copiar_de, d)
    else:
        os.makedirs(d)
    for n, texto in ficheros.items():
        with open(os.path.join(d, n), "w", encoding="utf-8") as f:
            f.write(texto)
    return d


def sala_toml(nombre, planta, ancho, tipo, miembros=(), cumple=None, extra=""):
    t = 'nombre = "%s"\nplanta = %d\nancho = %d\ntipo = "%s"\n' % (nombre, planta, ancho, tipo)
    for m in miembros:
        t += '\n[[miembro]]\nnombre = "%s"\n' % m + ('cumple = "%s"\n' % cumple if cumple else "")
    return t + extra


class ConTemporal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ant-farm-dibujo-")
        self.addCleanup(shutil.rmtree, self.tmp, True)


# ===================================================================== fechas y horas

FECHAS = ("2025-06-01 12:00",   # antes de la fundación
          "2026-01-01 00:00",   # el día de la fundación, a medianoche
          "2026-01-06 09:00", "2026-02-14 20:30", "2026-03-14 03:14", "2026-03-29 02:30",
          "2026-04-05 12:00", "2026-06-24 00:30", "2026-08-15 16:00", "2026-10-31 23:00",
          "2026-11-02 07:45", "2026-12-24 22:00", "2026-12-31 23:59", "2027-01-01 00:01",
          "2028-02-29 12:00",   # año bisiesto
          "2031-07-20 05:30", "2040-05-17 18:00")
CIELO = pygame.Rect(150, 60, 340, 40)   # un trozo de cielo sin textos, montes ni sol a mediodía


class TestFechasYHoras(unittest.TestCase):
    def test_fechas_variadas(self):
        for cuando in FECHAS:
            with self.subTest(cuando=cuando):
                e = Escena(cuando)
                img = e.fotogramas(8, dt=0.5)
                self.assertEqual(img.get_size(), (W, H))
                self.assertGreater(colores(img), 20)
                if cuando < "2026-01-01":
                    self.assertEqual(e.m.dia, 0)

    def test_todas_las_horas_del_dia(self):
        e = Escena("2026-06-15 00:00")
        for minuto in range(0, 24 * 60, 20):
            with self.subTest(hora="%02d:%02d" % divmod(minuto, 60)):
                e.ir_a(datetime.datetime(2026, 6, 15) + datetime.timedelta(minutes=minuto))
                e.fotogramas(2)
                self.assertGreater(colores(e.pantalla), 20)

    def test_el_cielo_de_noche_es_mas_oscuro(self):
        e = Escena("2026-06-15 13:00", tiempo="despejado")
        e.fotogramas(2)
        self.assertFalse(e.m.de_noche)
        dia = brillo(e.pantalla, CIELO)
        e.ir_a("2026-06-15 02:00")
        e.fotogramas(2)
        self.assertTrue(e.m.de_noche)
        noche = brillo(e.pantalla, CIELO)
        self.assertGreater(dia, 120)
        self.assertLess(noche, 80)

    def test_amanecer_y_anochecer(self):
        e = Escena("2026-06-15 12:00", tiempo="despejado")
        a, p = e.m.sol_hoy
        medianoche = datetime.datetime(2026, 6, 15)
        for centro in (a, p):
            for d in range(-60, 61, 5):
                with self.subTest(minuto=int(centro + d)):
                    e.ir_a(medianoche + datetime.timedelta(minutes=int(centro + d)))
                    e.fotogramas(1)
                    self.assertGreater(colores(e.pantalla), 20)
        # una hora antes de amanecer es de noche, y una hora después ya es de día
        e.ir_a(medianoche + datetime.timedelta(minutes=int(a - 60)))
        self.assertTrue(e.m.de_noche)
        e.ir_a(medianoche + datetime.timedelta(minutes=int(a + 60)))
        self.assertFalse(e.m.de_noche)

    def test_saltos_de_fecha_adelante_y_atras(self):
        """Volver atrás en el tiempo (otro --fecha al recargar, el reloj del sistema...) repinta bien."""
        e = Escena("2030-06-15 12:00")
        e.fotogramas(2)
        for cuando in ("2026-01-02 12:00", "2033-03-03 21:00", "2026-01-01 00:00", "2027-07-07 07:07"):
            with self.subTest(cuando=cuando):
                e.ir_a(cuando)
                e.fotogramas(3)
                self.assertGreater(colores(e.pantalla), 20)


# ===================================================================== el tiempo

class TestTiempo(unittest.TestCase):
    def test_tiempos_forzados_de_dia_y_de_noche(self):
        for tipo in T.TiempoForzado.TIPOS:
            for hora in ("12:00", "23:30"):
                with self.subTest(tiempo=tipo, hora=hora):
                    e = Escena("2026-11-20 " + hora, tiempo=tipo)
                    e.fotogramas(25, dt=0.2)
                    m = e.m
                    self.assertEqual(m.tiempo_hoy.tipo, tipo)
                    self.assertEqual(m.lluvia > 0, tipo in ("lluvia", "tormenta", "nieve"))
                    self.assertEqual(m.nevado, tipo == "nieve")
                    self.assertEqual(m.de_noche, hora == "23:30")
                    self.assertGreater(colores(e.pantalla), 15)
                    marcas = {p[4] for p in m.superficie.particulas}
                    gota = {"lluvia": "|", "tormenta": "/", "nieve": "❄"}.get(tipo)
                    if gota:
                        self.assertIn(gota, marcas)

    def test_la_nieve_cubre_el_paisaje(self):
        def blancos(tipo):
            e = Escena("2026-01-20 12:00", tiempo=tipo)
            e.fotogramas(2)
            return pygame.mask.from_threshold(e.r.capa_sup, (240, 244, 250), (1, 1, 1, 255)).count()
        self.assertGreater(blancos("nieve"), blancos("despejado") + 200)

    def test_la_calima_vuelve_naranja_el_cielo(self):
        def tono(tipo):
            e = Escena("2026-07-10 12:00", tiempo=tipo)
            e.fotogramas(2)
            r, _g, b = pygame.transform.average_color(e.pantalla, (0, 0, W, e.r.G))[:3]
            return r - b
        self.assertGreater(tono("calima"), tono("despejado") + 40)

    def test_relampago(self):
        e = Escena("2026-11-20 22:00", tiempo="tormenta")
        e.fotogramas(5)
        cielo = pygame.Rect(0, 0, W, e.r.G)
        e.m.superficie.relampago = 0
        e.r.dibujar()
        antes = brillo(e.pantalla, cielo)
        e.m.superficie.relampago = 0.25
        e.r.dibujar()
        self.assertGreater(brillo(e.pantalla, cielo), antes + 30)

    def test_el_rotulo_dice_si_llueve_o_nieva(self):
        for tipo, palabra in (("lluvia", "· lluvia"), ("tormenta", "· lluvia"), ("nieve", "· nieve"),
                              ("despejado", None), ("calima", None)):
            with self.subTest(tiempo=tipo):
                e = Escena("2026-11-20 12:00", tiempo=tipo)
                e.fotogramas(1)
                with textos_dibujados(e.r) as vistos:
                    e.r.dibujar()
                info = [t for t, *_ in vistos if "del hormiguero" in t]
                self.assertTrue(info)
                for t in info:
                    if palabra:
                        self.assertIn(palabra, t)
                    else:
                        self.assertNotIn("lluvia", t)
                        self.assertNotIn("nieve", t)


# ===================================================================== latitudes y zonas horarias

class TestLatitudes(unittest.TestCase):
    def test_latitudes_extremas(self):
        for lat in LATITUDES:
            e = Escena("2026-06-21 12:00", ciudad={"lat": lat})
            for dia in ("2026-03-20", "2026-06-21", "2026-09-23", "2026-12-21"):
                for hora in ("00:00", "06:00", "12:00", "18:00", "23:59"):
                    with self.subTest(lat=lat, cuando=dia + " " + hora):
                        e.ir_a(dia + " " + hora)
                        e.fotogramas(2)
                        a, p = e.m.sol_hoy
                        self.assertLessEqual(a, p)
                        self.assertGreater(colores(e.pantalla), 15)

    def test_sol_de_medianoche_y_noche_polar(self):
        for lat, verano, invierno in ((78.2, "2026-06-21", "2026-12-21"), (90, "2026-06-21", "2026-12-21"),
                                      (-78.2, "2026-12-21", "2026-06-21"), (-90, "2026-12-21", "2026-06-21")):
            e = Escena(verano + " 12:00", ciudad={"lat": lat}, tiempo="despejado")
            for hora in ("00:00", "12:00", "23:59"):
                with self.subTest(lat=lat, hora=hora):
                    e.ir_a(verano + " " + hora)
                    e.fotogramas(1)
                    self.assertFalse(e.m.de_noche)   # sol de medianoche
                    self.assertGreater(brillo(e.pantalla, CIELO), 120)
                    e.ir_a(invierno + " " + hora)
                    e.fotogramas(1)
                    self.assertTrue(e.m.de_noche)    # noche polar
                    self.assertLess(brillo(e.pantalla, CIELO), 80)

    def test_hemisferio_sur(self):
        e = Escena("2026-07-15 12:00", ciudad={"lat": -33.9, "lon": 18.4})
        e.fotogramas(5)
        self.assertEqual(e.m.estacion, "invierno")
        self.assertGreater(colores(e.pantalla), 20)

    def test_ciudades_y_zonas_horarias(self):
        for ciudad in ({"lat": -34.6, "lon": -58.4, "zona_horaria": "America/Argentina/Buenos_Aires"},
                       {"lat": -36.85, "lon": 174.76, "zona_horaria": "Pacific/Auckland"},
                       {"lat": 1.87, "lon": -157.4, "zona_horaria": "Pacific/Kiritimati"},
                       {"lat": 64.15, "lon": -21.94, "zona_horaria": "Atlantic/Reykjavik"},
                       {"lat": 36.72, "lon": 179.9, "zona_horaria": "Europe/Madrid"},
                       {"lat": 36.72, "lon": -4.42, "zona_horaria": "Marte/Olympus_Mons"}):
            e = Escena("2026-03-29 00:00", ciudad=ciudad)
            for hora in range(0, 24, 3):
                with self.subTest(zona=ciudad["zona_horaria"], hora=hora):
                    e.ir_a("2026-03-29 %02d:00" % hora)
                    e.fotogramas(2)
                    self.assertGreater(colores(e.pantalla), 15)


# ===================================================================== fiestas

class TestFiestas(ConTemporal):
    def test_cada_decoracion_de_dia_y_de_noche(self):
        e = Escena("2026-06-15 12:00", tiempo="despejado", fiestas=[])
        for deco in F.DECORACIONES:
            e.m.fiestas = fiestas({"decoracion": deco, "mensaje": "¡Feliz %s!" % deco})
            for hora in ("12:00", "19:30", "23:45", "00:05"):
                with self.subTest(decoracion=deco, hora=hora):
                    e.ir_a("2026-06-15 " + hora)
                    self.assertEqual(e.m.decoraciones, {deco})
                    self.assertEqual(e.m.fiesta_mensaje, "¡Feliz %s!" % deco)
                    e.fotogramas(12, dt=0.1)
                    self.assertGreater(colores(e.pantalla), 20)

    def test_cada_decoracion_se_ve(self):
        """Con la misma escena, cada decoración cambia el dibujo (de noche, cuando se ven todas)."""
        e = Escena("2026-06-15 23:30", tiempo="despejado", fiestas=[],
                   idos=[{"nombre": "CARLOS"}])   # el cementerio, para las flores de difuntos
        e.fotogramas(3)
        e.m.t = 30.0   # la procesión de Semana Santa entra por la izquierda: a los 30 s va por el centro
        for deco in F.DECORACIONES:
            if deco == "corazones":   # son partículas que suben del suelo: se prueban aparte
                continue
            with self.subTest(decoracion=deco):
                e.m.decoraciones = set()
                e.r.rng.seed(5)
                e.r.dibujar()
                sin = bytes_de(e.pantalla)
                e.m.decoraciones = {deco}
                e.r.rng.seed(5)
                e.r.dibujar()
                self.assertTrue(bytes_de(e.pantalla) != sin, "«%s» no cambia nada" % deco)

    def test_corazones_de_san_valentin(self):
        e = Escena("2026-02-14 12:00", fiestas=fiestas({"decoracion": "corazones", "desde": "14-02"}))
        e.fotogramas(40, dt=0.25)
        self.assertIn("♥", {p[4] for p in e.m.superficie.particulas})

    def test_fuegos_artificiales_en_nochevieja(self):
        e = Escena("2026-12-31 23:55", tiempo="despejado",
                   fiestas=fiestas({"decoracion": "nochevieja", "desde": "31-12", "hasta": "01-01"}))
        maximo = 0
        for _ in range(40):
            e.fotogramas(1, dt=0.1)
            maximo = max(maximo, len(e.r.fuegos))
        self.assertGreater(maximo, 0)

    def test_cada_gorro_se_dibuja(self):
        e = Escena(FECHA_BASE)
        e.fotogramas(1)
        for gorro in F.GORROS + ("cumple",):
            for d in (1, -1):
                with self.subTest(gorro=gorro, direccion=d):
                    e.pantalla.fill(SIN_COLOR)
                    e.r._gorro(gorro, 100, 100, d)
                    caja = pintado(e.pantalla)
                    self.assertIsNotNone(caja)
                    self.assertLess(max(caja.width, caja.height), 20)

    def test_cada_gorro_en_el_hormiguero(self):
        e = Escena(FECHA_BASE, fiestas=[])
        for gorro in F.GORROS:
            with self.subTest(gorro=gorro):
                e.m.fiestas = fiestas({"decoracion": "banderines", "gorro": gorro})
                e.ir_a(FECHA_BASE)
                self.assertEqual(e.m.gorro_fiesta, gorro)
                e.fotogramas(5)

    def test_decoracion_y_gorro_que_no_existen(self):
        avisos = []
        lista = fiestas({"decoracion": "inventada", "gorro": "chistera"}, avisos=avisos)
        self.assertTrue(any("«inventada»" in a for a in avisos))
        self.assertTrue(any("«chistera»" in a for a in avisos))
        e = Escena(FECHA_BASE, fiestas=lista)
        e.fotogramas(10)
        # el gorro que no existe se quita: si no, taparía el de otra fiesta del mismo día
        self.assertIsNone(e.m.gorro_fiesta)
        self.assertGreater(colores(e.pantalla), 20)

    def test_todas_las_fiestas_a_la_vez(self):
        lista = fiestas(*({"decoracion": d, "gorro": g, "desde": "02-07"}
                          for d, g in zip(F.DECORACIONES, itertools.cycle(F.GORROS))))
        salas = carpeta(self.tmp, "salas", {"fiesta.toml": sala_toml("Fiesta", 2, 30, "comedor", ["Ana", "Luis"],
                                                                      cumple="02-07")})
        e = Escena("2026-07-02 12:00", fiestas=lista, salas=salas)
        self.assertEqual(e.m.decoraciones, set(F.DECORACIONES))
        for tiempo in ("despejado", "tormenta", "nieve"):
            e.m.cfg["tiempo_forzado"] = tiempo
            for hora in ("12:00", "22:45", "00:10"):
                with self.subTest(tiempo=tiempo, hora=hora):
                    e.ir_a("2026-07-02 " + hora)
                    e.fotogramas(15, dt=0.2)
                    self.assertGreater(colores(e.pantalla), 20)

    def test_halloween_con_esqueletos(self):
        e = Escena("2026-10-28 22:00", idos=[{"nombre": "CARLOS"}, {"nombre": "IRENE", "fecha": "2026-09-30"}],
                   fiestas=fiestas({"decoracion": "halloween", "desde": "25-10", "hasta": "31-10", "gorro": "bruja"}))
        e.fotogramas(20, dt=0.25)
        esqueletos = sorted(h.nombre for h in e.m.hormigas.values() if h.esqueleto)
        self.assertEqual(esqueletos, ["CARLOS ☠", "IRENE ☠"])
        self.assertIsNotNone(e.r.cementerio_px)

    def test_cementerio(self):
        for n, largo in ((1, "ANA"), (6, "Persona"), (40, "Persona con un nombre muy largo")):
            with self.subTest(idos=n):
                idos = [{"nombre": "%s %d" % (largo, i)} for i in range(n)]
                e = Escena("2026-10-30 23:00", idos=idos,
                           fiestas=fiestas({"decoracion": "difuntos", "desde": "30-10", "hasta": "02-11"}))
                e.fotogramas(5, dt=0.25)
                no_caben = [a for a in e.m.todos_los_avisos() if "no caben todas las lápidas" in a]
                self.assertEqual(bool(no_caben), n == 40)
                self.assertIsNotNone(e.r.cementerio_px)
                a, b = e.r.cementerio_px
                self.assertGreaterEqual(a, 0)
                self.assertLessEqual(b, W)

    def test_la_tarta_no_tapa_el_cementerio(self):
        """Con el cementerio justo donde iría la tarta (30 columnas a la derecha de la entrada),
        la tarta y los regalos se apartan."""
        salas = carpeta(self.tmp, "salas", {"fiesta.toml": sala_toml("Fiesta", 2, 30, "trabajo", ["Ana"],
                                                                      cumple="15-06")})
        e = Escena("2026-06-15 12:00", salas=salas, fiestas=[], idos=[{"nombre": "PEPE"}, {"nombre": "JUAN"}])
        e.m.superficie.cementerio_x = e.m.ox + e.m.plan.entrada + 30
        e.r.recargado()
        e.fotogramas(1)   # pinta el cementerio y apunta dónde queda
        e.ir_a(e.ahora)   # y la tarta se aparta
        a, b = e.m.zona_cementerio
        x = e.m.x_cumple
        self.assertTrue(x + 20 < a or x > b, (x, a, b))
        self.assertTrue(3 <= x and x + 20 <= ANCHO - 3, x)
        e.fotogramas(3)

    def test_cumpleanos(self):
        salas = carpeta(self.tmp, "salas", {
            "fiesta.toml": sala_toml("Sala de fiestas", 1, 30, "trabajo", ["Ana", "Luis"], cumple="02-07"),
            "otra.toml": sala_toml("Otra", 2, 20, "trabajo", ["Eva"])})
        e = Escena("2026-07-02 12:00", salas=salas, fiestas=[])
        e.fotogramas(3)
        self.assertEqual(sorted(e.m.cumples), ["Ana", "Luis"])
        with textos_dibujados(e.r) as vistos:
            e.r.dibujar()
        textos = [t for t, *_ in vistos]
        self.assertIn("Ana, Luis", textos)   # bajo la pancarta de FELIZ CUMPLE
        self.assertTrue(any(t.startswith("¡Feliz cumple") for t in textos))

    def test_muchos_cumpleanos_en_sala_estrecha(self):
        nombres = ["Maximiliano %d" % i for i in range(7)]
        salas = carpeta(self.tmp, "salas", {
            "estrecha.toml": sala_toml("Estrecha", 1, ANCHO_MIN, "trabajo", nombres, cumple="02-07")})
        e = Escena("2026-07-02 12:00", salas=salas, fiestas=[])
        e.fotogramas(10, dt=0.25)
        salas_px = [e.rect_sala(s) for s in e.m.salas]
        for rect in e.r.textos_salas:   # los carteles y las frases no se salen de su sala
            self.assertTrue(any(s.contains(rect) for s in salas_px), rect)

    def test_entrada_en_los_bordes(self):
        """La portada de la feria, la bandera y la tarta con la entrada pegada a un lado."""
        salas = carpeta(self.tmp, "salas", {"fiesta.toml": sala_toml("Fiesta", 2, 30, "trabajo", ["Ana"],
                                                                      cumple="15-06")})
        lista = fiestas(*({"decoracion": d} for d in F.DECORACIONES))
        for entrada in (3, 156):
            with self.subTest(entrada=entrada):
                e = Escena("2026-06-15 23:00", salas=salas, fiestas=lista, nido={"entrada": entrada})
                e.fotogramas(10, dt=0.2)
                self.assertGreater(colores(e.pantalla), 20)


# ===================================================================== salas y muebles

class TestSalas(ConTemporal):
    def montar(self):
        """Tipos con todos los muebles (paredes y suelos distintos) y salas estrechas de esos tipos."""
        todos = "".join('\n[[mueble]]\npieza = "%s"\n' % p for p in MU.PIEZAS)
        tipos = carpeta(self.tmp, "tipos", {
            "todo.toml": 'funcion = "trabajo"\nparedes = "azulejo"\nsuelo = "baldosa"\n' + todos,
            "todo_piedra.toml": 'funcion = "comedor"\nparedes = "piedra"\nsuelo = "tierra"\n' + todos,
            "todo_color.toml": 'funcion = "reuniones"\nparedes = "#203040"\nsuelo = "madera"\n' + todos,
        }, copiar_de=repo("tipos"))
        raros = ('\n[[mueble]]\npieza = "reloj"\nsitio = 0\n'
                 '\n[[mueble]]\npieza = "cuadro"\nsitio = 100\n'
                 '\n[[mueble]]\npieza = "sillon"\nsitio = "35,5"\n'
                 '\n[[mueble]]\npieza = "nevera"\nsitio = "por ahí"\n'
                 '\n[[mueble]]\npieza = "sofa"\nsitio = 150\n'
                 '\n[[mueble]]\npieza = "planta"\naparece = 30\n'
                 '\n[[mueble]]\npieza = "inventada"\n')
        salas = carpeta(self.tmp, "salas", {
            "a.toml": sala_toml("Sala de reuniones del departamento de diseño gráfico y comunicación", 1, 14,
                                "todo", ["Ana", "Luis"], cumple="14-03", extra=raros),
            "b.toml": sala_toml("Supercalifragilisticoespialidoso", 2, 15, "todo_piedra", ["Eva"]),
            "c.toml": sala_toml("Ce", 3, 18, "todo_color", ["Pepe"], cumple="14-03"),
            "d.toml": sala_toml("De", 4, 21, "todo", ["Rosa"]),
            "e.toml": sala_toml("Mínima", 2, 5, "todo", ["Juan"]),
            "f.toml": sala_toml("Grande", 3, 60, "todo_piedra", ["Lola", "Paco"]),
        })
        return salas, tipos

    def test_salas_estrechas_con_todos_los_muebles(self):
        salas, tipos = self.montar()
        e = Escena("2031-03-14 12:00", salas=salas, tipos=tipos, fiestas=[])
        e.fotogramas(5)
        carga = e.avisos_carga
        self.assertTrue(any("el ancho mínimo es %d" % ANCHO_MIN in a for a in carga))
        self.assertTrue(any("no existe la pieza «inventada»" in a for a in carga))
        self.assertTrue(any("no existe el hueco «por ahí»" in a for a in carga))
        mias = {s.clave: s for s in e.m.salas if len(s.clave) == 1}
        self.assertEqual(sorted(mias), ["a", "b", "c", "d", "e", "f"])
        self.assertEqual(mias["e"].ancho, ANCHO_MIN)
        avisos = e.m.todos_los_avisos()
        for s in mias.values():
            rect = e.rect_sala(s)
            self.assertTrue(rect.contains(e.r._cartel(s, rect)[1]), s.nombre)
            for pieza in MU.PIEZAS:
                with self.subTest(sala=s.clave, ancho=s.ancho, pieza=pieza):
                    hay = any(a.startswith("%s: «%s» no cabe en la sala" % (s.nombre, pieza)) for a in avisos)
                    self.assertEqual(hay, s.ancho < MU.ancho_minimo(pieza))
        # y con todas las fiestas, de noche y nevando, en esas mismas salas
        e.m.fiestas = fiestas(*({"decoracion": d, "desde": "14-03"} for d in F.DECORACIONES))
        e.m.cfg["tiempo_forzado"] = "nieve"
        for hora in ("12:00", "23:30"):
            with self.subTest(fiestas=hora):
                e.ir_a("2031-03-14 " + hora)
                e.fotogramas(10, dt=0.25)
                salas_px = [e.rect_sala(s) for s in e.m.salas]
                for rect in e.r.textos_salas:
                    self.assertTrue(any(s.contains(rect) for s in salas_px), rect)

    def test_el_aviso_se_va_al_quitar_el_mueble(self):
        base = sala_toml("Estrecha", 1, ANCHO_MIN, "trabajo", ["Ana"])
        salas = carpeta(self.tmp, "salas", {"estrecha.toml": base + '\n[[mueble]]\npieza = "setas"\n'})
        e = Escena(FECHA_BASE, salas=salas)
        e.fotogramas(2)
        aviso = "Estrecha: «setas» no cabe en la sala"
        self.assertTrue(any(a.startswith(aviso) for a in e.m.todos_los_avisos()))
        # se quita del fichero y se recarga, como hace el hormiguero al guardar
        with open(os.path.join(salas, "estrecha.toml"), "w", encoding="utf-8") as f:
            f.write(base)
        _cfg, salas_cfg, idos, lista, avisos = cargar(salas=salas, fresco=True)
        e.m.avisos_carga = avisos
        e.m.fiestas = lista
        e.m.cargar_gente(salas_cfg, idos)
        e.m.actualizar_contexto(forzar=True)
        e.r.recargado()
        e.fotogramas(2)
        self.assertFalse(any(a.startswith(aviso) for a in e.m.todos_los_avisos()))


class TestPiezas(unittest.TestCase):
    SITIOS = list(MU.HUECOS_SUELO) + list(MU.HUECOS_PARED) + [None, 0, 37.5, 100, "no_existe", True]

    @classmethod
    def setUpClass(cls):
        cls.e = Escena("2031-06-15 12:00")
        cls.e.fotogramas(1)

    def contexto(self, dia=0, indice=0, objetos=()):
        """El Contexto de un mueble, con un render de verdad; la vitrina enseña 'objetos'."""
        r = self.e.r
        falso = types.SimpleNamespace(
            m=types.SimpleNamespace(plan=types.SimpleNamespace(objetos=list(objetos)), dia_obras=10 ** 6,
                                    ahora=datetime.datetime(2031, 6, 15, 10, 10)),
            _objeto=r._objeto)
        return MU.Contexto(falso, dia, 0, indice)

    def pintar(self, pieza, sitio, columnas, ctx, t=1.3):
        """Pinta la pieza (y lo que se mueve) en una sala de 'columnas' de ancho, con margen
        alrededor: (rectángulo de la sala, rectángulo de lo pintado)."""
        sala = pygame.Rect(40, 40, columnas * CW, 7 * CH)
        s = pygame.Surface((sala.width + 80, sala.height + 80))
        s.fill(SIN_COLOR)
        x, y = MU.colocar(pieza, sitio, sala)
        MU.PIEZAS[pieza][3](s, x, y, sala, ctx)
        if MU.PIEZAS[pieza][4]:
            MU.PIEZAS[pieza][4](s, x, y, sala, ctx, t)
        return sala, pintado(s)

    def assertDentro(self, sala, caja):
        """Lo pintado no se sale de la sala por los lados ni por el techo; por abajo puede
        pisar el suelo de la sala (3 píxeles), como la maceta de la planta."""
        self.assertIsNotNone(caja)
        self.assertGreaterEqual(caja.left, sala.left, caja)
        self.assertLessEqual(caja.right, sala.right, caja)
        self.assertGreaterEqual(caja.top, sala.top, caja)
        self.assertLessEqual(caja.bottom, sala.bottom + 3, caja)

    def test_cada_mueble_cabe_en_la_sala_mas_estrecha(self):
        for pieza in MU.PIEZAS:
            columnas = max(MU.ancho_minimo(pieza), ANCHO_OBRA_MIN)
            for sitio in self.SITIOS:
                for dia in (0, 100, 400):   # la planta crece
                    for indice in (0, 1):
                        with self.subTest(pieza=pieza, sitio=sitio, dia=dia, indice=indice):
                            sala, caja = self.pintar(pieza, sitio, columnas, self.contexto(dia, indice))
                            self.assertDentro(sala, caja)

    def test_cada_mueble_a_su_tiempo(self):
        """Lo que se mueve (pantallas, vapor, burbujas, relojes) a lo largo de un rato."""
        for pieza, (_ancho, _donde, _defecto, _pintar, animar) in MU.PIEZAS.items():
            if not animar:
                continue
            for t in (0.0, 0.33, 1.0, 2.5, 59.9, 3600.0):
                with self.subTest(pieza=pieza, t=t):
                    sala, caja = self.pintar(pieza, None, 30, self.contexto(), t)
                    self.assertDentro(sala, caja)

    def test_vitrina_con_los_hallazgos(self):
        objetos = [(0, 0) + o + (0,) for o in OBJETOS if "IRPF" not in o[0]]
        for desfase in (0, 1):   # así cada hallazgo pasa por las dos columnas de la vitrina
            for indice in (0, 1):
                for sitio in ("izquierda", "centro", "derecha", 0, 100):
                    with self.subTest(desfase=desfase, indice=indice, sitio=sitio):
                        ctx = self.contexto(indice=indice, objetos=objetos[desfase:])
                        sala, caja = self.pintar("vitrina", sitio, ANCHO_MIN, ctx)
                        self.assertDentro(sala, caja)

    def test_vitrina_con_el_irpf_a_la_derecha(self):
        # el hallazgo «el IRPF fosilizado» (un óvalo con el texto «IRPF», de unos 21 píxeles) no
        # cabe en un hueco de la vitrina (de 9): va encima. Antes, en la columna de la derecha,
        # sobresalía 11 píxeles y, con la vitrina a la derecha de la sala, se salía de ella
        irpf = next(o for o in OBJETOS if "IRPF" in o[0])
        objetos = [(0, 0) + OBJETOS[0] + (0,), (0, 0) + irpf + (0,)]
        sala, caja = self.pintar("vitrina", "derecha", ANCHO_MIN, self.contexto(objetos=objetos))
        self.assertDentro(sala, caja)

    def test_cada_pieza_del_paisaje(self):
        for nombre, (pintar, luces, _arbol) in PA.SUELO.items():
            for dia in range(1, 367, 15):   # flores, hojas y frutos según el día del año
                for noche in (False, True):
                    with self.subTest(suelo=nombre, dia=dia, noche=noche):
                        s = superficie(120, 90)
                        pintar(s, 60, 80, PA.Contexto(dia, 2026, noche, 0))
                        if noche and luces:
                            luces(s, 60, 80, PA.Contexto(dia, 2026, True, 0))
                        self.assertIsNotNone(pintado(s, CLAVE))
        for nombre, (pintar, animar) in PA.FONDO.items():
            for noche in (False, True):
                for t in (0.0, 0.7, 3.3, 61.0):
                    with self.subTest(fondo=nombre, noche=noche, t=t):
                        s = superficie(150, 80)
                        ctx = PA.Contexto(0, 2026, noche, 0)
                        pintar(s, 75, 62, ctx, (40, 44, 62) if noche else (150, 128, 100), (250, 210, 110))
                        if animar:
                            animar(s, 75, 62, ctx, t)
                        self.assertIsNotNone(pintado(s, CLAVE))

    def test_todo_el_paisaje_en_el_hormiguero(self):
        """Todas las piezas, también en los bordes (x = 0 y x = 100), sin montes ni costa."""
        paisaje = {"montes": False, "costa": False, "cementerio": 100,
                   "suelo": [{"pieza": p, "x": x} for p in PA.SUELO for x in (0, 100)],
                   "fondo": [{"pieza": p, "x": x} for p in PA.FONDO for x in (0, 100)]}
        for kw in ({}, {"paisaje": paisaje}):
            for cuando, tiempo in (("2026-03-01 12:00", None), ("2026-09-01 23:00", None),
                                   ("2026-01-10 12:00", "nieve"), ("2026-01-10 23:00", "nieve")):
                with self.subTest(paisaje="bordes" if kw else "config", cuando=cuando, tiempo=tiempo):
                    e = Escena(cuando, tiempo=tiempo, idos=[{"nombre": "CARLOS"}], **kw)
                    e.fotogramas(5, dt=0.5)
                    self.assertFalse([a for a in e.m.todos_los_avisos() if a.startswith("paisaje")])
                    self.assertGreater(colores(e.pantalla), 20)

    def test_pieza_de_paisaje_que_no_existe(self):
        paisaje = {"suelo": [{"pieza": "baobab", "x": 50}, {"pieza": "pino", "x": "mucho"}, {"x": 3}],
                   "fondo": [{"pieza": "piramide", "x": 50}]}
        e = Escena(FECHA_BASE, paisaje=paisaje)
        e.fotogramas(3)
        avisos = e.m.todos_los_avisos()
        self.assertIn("paisaje: no existe la pieza «baobab»", avisos)
        self.assertIn("paisaje: no existe la pieza de fondo «piramide»", avisos)
        self.assertTrue(any(a.startswith("paisaje: pieza mal escrita") for a in avisos))


# ===================================================================== textos

class TestTextos(unittest.TestCase):
    def test_fecha_y_dia_en_el_rotulo(self):
        e = Escena("2026-10-22 12:00", fiestas=[])
        e.fotogramas(1)
        with textos_dibujados(e.r) as vistos:
            e.r.dibujar()
        textos = [t for t, *_ in vistos]
        self.assertIn("Jueves, 22 de octubre de 2026", textos)
        self.assertTrue(any(t.startswith("Día 294 del hormiguero · otoño · ") for t in textos), textos)

    def test_sin_menos_cero_grados(self):
        e = Escena("2026-01-20 07:00", tiempo="despejado")
        e.fotogramas(1)
        for temperatura, esperado in ((-0.4, "· 0 °C"), (-0.6, "· -1 °C"), (0.4, "· 0 °C")):
            with self.subTest(temperatura=temperatura):
                e.m.temperatura = temperatura
                with textos_dibujados(e.r) as vistos:
                    e.r.dibujar()
                info = [t for t, *_ in vistos if "del hormiguero" in t]
                self.assertTrue(info)
                for t in info:
                    self.assertIn(esperado, t)
                    self.assertNotIn("-0 °C", t)

    def test_el_diario_cabe_en_la_pantalla(self):
        largo = "Una fiesta con un mensaje larguísimo " * 8
        e = Escena(FECHA_BASE, fiestas=fiestas({"decoracion": "banderines", "mensaje": largo.strip()}))
        vistos_diario = []
        for _ in range(6):
            with textos_dibujados(e.r) as vistos:
                e.fotogramas(1, dt=2.0)
            vistos_diario += [(t, img) for t, _c, tam, img in vistos
                              if tam == 8 and re.match(r"(Hoy|Ayer|Hace \d+ días|¡Ahora!) · ", t)]
        self.assertTrue(vistos_diario)
        for t, img in vistos_diario:
            self.assertLessEqual(img.get_width(), W - 8, t)

    def test_el_mensaje_de_la_fiesta_cabe_en_la_pantalla(self):
        # el mensaje de una fiesta (calendario.toml) cabe en el cielo: con letra más pequeña y, si
        # ni así, recortado con «…». Antes salía tal cual y se cortaba por los dos lados
        largo = ("¡Feliz Navidad y próspero Año Nuevo a todo el equipo de la Oficina! Que paséis unas "
                 "fiestas estupendas con los vuestros y nos vemos a la vuelta")
        e = Escena(FECHA_BASE, fiestas=fiestas({"decoracion": "navidad", "mensaje": largo}))
        e.fotogramas(1)
        with textos_dibujados(e.r) as vistos:
            e.r.dibujar()
        pancarta = [(t, img) for t, color, tam, img in vistos if color == (255, 236, 120) and tam in (9, 10, 11)]
        self.assertTrue(pancarta)
        for t, img in pancarta:
            self.assertLessEqual(img.get_width(), W - 8)
            self.assertTrue(t.endswith("…"), t)
        # uno corto, tal cual y con la letra de siempre
        e.m.fiesta_mensaje = "¡Feliz Navidad!"
        with textos_dibujados(e.r) as vistos:
            e.r.dibujar()
        self.assertIn(("¡Feliz Navidad!", 11), [(t, tam) for t, color, tam, _img in vistos if color == (255, 236, 120)])


# ===================================================================== capturas (--captura y --medir)

class TestCapturas(ConTemporal):
    def argumentos(self, *extra):
        return ["--fecha", "2026-06-15", "--hora", "12:00", "-c", CONFIG, "--salas", repo("salas"),
                "--tipos", repo("tipos"), "--idos", repo("idos.toml"), "--calendario", repo("calendario.toml"),
                "--segundos", "0.5"] + list(extra)

    def test_captura_en_un_directorio_temporal(self):
        for tiempo in (None, "nieve", "tormenta", "calima"):
            with self.subTest(tiempo=tiempo):
                ruta = os.path.join(self.tmp, "captura-%s.png" % (tiempo or "normal"))
                salida = io.StringIO()
                with contextlib.redirect_stdout(salida):
                    APP.main(self.argumentos("--captura", ruta, *(["--tiempo", tiempo] if tiempo else [])))
                self.assertIn("captura guardada en " + ruta, salida.getvalue())
                img = pygame.image.load(ruta)
                self.assertEqual(img.get_size(), (2 * W, 2 * H))
                self.assertGreater(colores(img, 32), 20)

    def test_captura_de_la_demo(self):
        ruta = os.path.join(self.tmp, "demo.png")
        with contextlib.redirect_stdout(io.StringIO()):
            APP.main(self.argumentos("--demo", "--semilla", "7", "--captura", ruta))
        self.assertGreater(colores(pygame.image.load(ruta), 32), 20)

    def test_medir(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            APP.main(self.argumentos("--medir"))
        texto = salida.getvalue()
        self.assertRegex(texto, r"simulación [\d.]+ ms · dibujo [\d.]+ ms por fotograma \(10 fotogramas\)")
        self.assertRegex(texto, r"memoria máxima: [\d.]+ MB")


# ===================================================================== framebuffer (hormiguero_fb.py)

def _cerrar(fb):
    fb.mapa.close()
    os.close(fb.fd)


def _pixel(datos, x, y, bits, linea):
    """El color (r, g, b) de un píxel del framebuffer, de 0 a 255."""
    b = bits // 8
    v = int.from_bytes(datos[y * linea + x * b:y * linea + x * b + b], sys.byteorder)
    if bits == 16:
        return ((v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31)
    return (v >> 16 & 255, v >> 8 & 255, v & 255)


class TestFramebuffer(ConTemporal):
    CASOS = ((16, 1280, 1024, 0), (32, 1280, 1024, 0), (16, 1280, 1024, 64), (32, 1920, 1080, 0),
             (16, 1366, 768, 0), (32, 800, 480, 32), (32, 320, 240, 0))

    @classmethod
    def setUpClass(cls):
        with mock.patch.dict(os.environ):   # pone SDL_VIDEODRIVER=dummy: que no quede puesto
            cls.FB = importlib.import_module("hormiguero_fb")
        e = Escena(FECHA_BASE, tiempo="despejado")
        cls.imagen = e.fotogramas(3).copy()

    def fichero(self, ancho, alto, bits, relleno=0):
        """Un fichero que hace de /dev/fb0, y la geometría que tendría el dispositivo."""
        linea = ancho * bits // 8 + relleno
        ruta = os.path.join(self.tmp, "fb%d-%dx%d-%d" % (bits, ancho, alto, relleno))
        with open(ruta, "wb") as f:
            f.truncate(linea * alto)
        return ruta, (ancho, alto, bits, CANALES[bits], linea)

    def test_framebuffer_simulado(self):
        for bits, ancho, alto, relleno in self.CASOS:
            with self.subTest(bits=bits, tam="%dx%d" % (ancho, alto), relleno=relleno):
                ruta, geo = self.fichero(ancho, alto, bits, relleno)
                linea = geo[4]
                with mock.patch.object(self.FB, "geometria", return_value=geo):
                    fb = self.FB.Framebuffer(ruta)
                self.addCleanup(_cerrar, fb)
                fb.volcar(self.imagen)
                fb.volcar(self.imagen)   # la segunda vez ya tiene la zona calculada
                self.assertEqual(len(fb.costes), 2)
                fb.mapa.flush()
                with open(ruta, "rb") as f:
                    datos = f.read()
                self.assertEqual(len(datos), linea * alto)
                # la imagen, centrada y ampliada sin deformar (por un número entero si cabe)
                k = min(ancho / W, alto / H)
                k = int(k) if k >= 1 else k
                dw, dh = int(W * k), int(H * k)
                x0, y0 = fb.zona.get_abs_offset()
                self.assertEqual(fb.zona.get_size(), (dw, dh))
                self.assertEqual((x0, y0), ((ancho - dw) // 2, (alto - dh) // 2))
                muestras = [(x0 + i * (dw - 1) // 19, y0 + j * (dh - 1) // 19) for i in range(20) for j in range(20)]
                encendidos = [p for p in muestras if _pixel(datos, p[0], p[1], bits, linea) != (0, 0, 0)]
                self.assertGreater(len(encendidos), len(muestras) * 0.9)
                if k == int(k):   # cada píxel de la pantalla es uno de la imagen, con su color
                    margen = 0 if bits == 32 else 9
                    for x, y in muestras:
                        esperado = self.imagen.get_at(((x - x0) // int(k), (y - y0) // int(k)))[:3]
                        leido = _pixel(datos, x, y, bits, linea)
                        for a, b in zip(esperado, leido):
                            self.assertLessEqual(abs(a - b), margen, (x, y, esperado, leido))
                # fuera de la imagen, negro; y lo que sobra de cada línea, sin tocar
                for x, y in ((0, 0), (ancho - 1, alto - 1), (0, alto - 1), (ancho - 1, 0)):
                    if not fb.zona.get_rect(topleft=(x0, y0)).collidepoint(x, y):
                        self.assertEqual(_pixel(datos, x, y, bits, linea), (0, 0, 0))
                if relleno:
                    usado = ancho * bits // 8
                    self.assertFalse(any(any(datos[y * linea + usado:(y + 1) * linea]) for y in range(alto)))

    def test_main_vuelca_al_framebuffer(self):
        for bits in (16, 32):
            with self.subTest(bits=bits):
                ruta, geo = self.fichero(1280, 1024, bits)
                volcados = []
                original = self.FB.Framebuffer.volcar

                def volcar(fb, imagen):
                    original(fb, imagen)
                    volcados.append(fb)
                    pygame.event.post(pygame.event.Event(pygame.QUIT))   # y se sale, como con la q

                argv = ["hormiguero_fb.py", "--fecha", "2026-06-15", "--hora", "12:00", "-c", CONFIG,
                        "--salas", repo("salas"), "--tipos", repo("tipos"), "--idos", repo("idos.toml"),
                        "--calendario", repo("calendario.toml")]
                self.addCleanup(signal.signal, signal.SIGTERM, signal.getsignal(signal.SIGTERM))
                salida = io.StringIO()
                entorno = {k: v for k, v in os.environ.items() if k != "HORMIGUERO_FB_INFO"}
                entorno["HORMIGUERO_FB"] = ruta
                with mock.patch.object(self.FB, "geometria", return_value=geo), \
                        mock.patch.object(self.FB, "modo_grafico_consola"), \
                        mock.patch.object(self.FB.Framebuffer, "volcar", volcar), \
                        mock.patch.dict(os.environ, entorno, clear=True), \
                        mock.patch.object(sys, "argv", argv), \
                        mock.patch.object(pygame.display, "set_mode", pygame.display.set_mode), \
                        mock.patch.object(pygame.display, "flip", pygame.display.flip), \
                        mock.patch.object(pygame.display, "update", pygame.display.update), \
                        contextlib.redirect_stdout(salida):
                    self.FB.main()
                self.assertTrue(volcados)
                self.addCleanup(_cerrar, volcados[0])
                self.assertIn("framebuffer 1280x1024", salida.getvalue())
                with open(ruta, "rb") as f:
                    datos = f.read()
                muestras = [(x, y) for x in range(0, 1280, 64) for y in range(0, 1024, 64)]
                encendidos = [p for p in muestras if _pixel(datos, p[0], p[1], bits, geo[4]) != (0, 0, 0)]
                self.assertGreater(len(encendidos), len(muestras) * 0.9)
                self.assertGreater(len({_pixel(datos, x, y, bits, geo[4]) for x, y in muestras}), 20)


# ===================================================================== herramientas/galeria.py

def _sello(carpeta_):
    """Qué hay en una carpeta y cuándo se tocó (para ver que no se ha escrito nada)."""
    if not os.path.isdir(carpeta_):
        return None
    return sorted((n, os.stat(os.path.join(carpeta_, n)).st_mtime_ns, os.path.getsize(os.path.join(carpeta_, n)))
                  for n in os.listdir(carpeta_))


class TestGaleria(ConTemporal):
    @classmethod
    def setUpClass(cls):
        ruta = os.path.join(RAIZ, "herramientas", "galeria.py")
        spec = importlib.util.spec_from_file_location("galeria_de_prueba", ruta)
        cls.G = importlib.util.module_from_spec(spec)
        with mock.patch.dict(os.environ):   # pone SDL_VIDEODRIVER=dummy: que no quede puesto
            spec.loader.exec_module(cls.G)
        cls.m, cls.r, cls.cfg = cls.G.mundo_de_ejemplo()
        cls.letras = Letras()

    def assertRejilla(self, img, celdas, ancho, alto):
        filas = math.ceil(celdas / 4)
        self.assertEqual(img.get_size(), ((4 * (ancho + 10) + 10) * 2, (26 + filas * (alto + 10) + 10) * 2))
        self.assertGreater(colores(img, 8), 20)

    def test_galeria_de_muebles(self):
        self.assertRejilla(self.G.galeria_muebles(self.m, self.r, self.letras), len(MU.PIEZAS), 176, 92)

    def test_galeria_de_tipos(self):
        tipos = self.cfg["tipos"]
        self.assertTrue(tipos)
        self.assertRejilla(self.G.galeria_tipos(self.m, self.r, self.letras, tipos), len(tipos), 176, 92)

    def test_galeria_del_paisaje(self):
        img = self.G.galeria_paisaje(self.letras, self.m.semilla)
        self.assertRejilla(img, len(PA.SUELO) + len(PA.FONDO), 228, 104)

    def test_escenas_del_paisaje(self):
        for noche in (False, True):
            for nombre in PA.SUELO:
                with self.subTest(suelo=nombre, noche=noche):
                    self.assertEqual(self.G.escena_suelo(nombre, noche, 2026).get_size(), (110, 80))
            for nombre in PA.FONDO:
                with self.subTest(fondo=nombre, noche=noche):
                    self.assertEqual(self.G.escena_fondo(nombre, noche, 2026).get_size(), (150, 80))

    def test_sala_vacia(self):
        for paredes in ("madera", "azulejo", "piedra", "#203040"):
            for suelo in ("madera", "baldosa", "tierra"):
                s, r = self.G.sala_vacia(176, 64, paredes, suelo)
                self.assertEqual(s.get_size(), (176, 64))
                self.assertEqual(r.size, (176, 61))

    def test_main_sin_tocar_docs(self):
        """main() escribe en <raíz>/docs: con la raíz en un directorio temporal, el docs/ del
        repositorio no se toca."""
        raiz = os.path.join(self.tmp, "raiz")
        os.makedirs(raiz)
        for n in ("config.toml", "idos.toml", "calendario.toml"):
            shutil.copy(repo(n), raiz)
        for n in ("salas", "tipos"):
            shutil.copytree(repo(n), os.path.join(raiz, n))
        antes = _sello(repo("docs"))
        with mock.patch.object(self.G, "RAIZ", raiz), contextlib.redirect_stdout(io.StringIO()) as salida:
            self.G.main()
        self.assertEqual(_sello(repo("docs")), antes)
        for n in ("galeria-muebles.png", "galeria-tipos.png", "galeria-paisaje.png"):
            ruta = os.path.join(raiz, "docs", n)
            self.assertIn("guardada " + ruta, salida.getvalue())
            self.assertGreater(colores(pygame.image.load(ruta), 8), 20)


# ===================================================================== rendimiento

class TestRendimiento(ConTemporal):
    # segundos por fotograma (simulación y dibujo): el tiempo que hay en la Pi a 20 fps. En un PC
    # va muy por debajo, así que sólo salta si algo se ha vuelto muchísimo más lento.
    LIMITE = 0.05

    def medir(self, e, n=100, dt=0.05):
        e.fotogramas(10, dt)   # los primeros pintan la tierra, el cielo y las capas: no cuentan
        t0 = time.perf_counter()
        e.fotogramas(n, dt)
        return (time.perf_counter() - t0) / n

    def test_fotograma_normal(self):
        media = self.medir(Escena("2026-06-15 11:00"))
        self.assertLess(media, self.LIMITE, "%.1f ms por fotograma" % (media * 1000))

    def test_fotograma_con_todo(self):
        """Tormenta de noche con todas las fiestas, cumpleaños y el cementerio lleno."""
        salas = carpeta(self.tmp, "salas", {"fiesta.toml": sala_toml("Fiesta", 2, 30, "comedor", ["Ana", "Luis"],
                                                                      cumple="31-10")}, )
        lista = fiestas(*({"decoracion": d, "gorro": "bruja", "desde": "31-10"} for d in F.DECORACIONES))
        idos = [{"nombre": "Ido %d" % i} for i in range(12)]
        e = Escena("2026-10-31 23:58", tiempo="tormenta", salas=salas, fiestas=lista, idos=idos)
        media = self.medir(e)
        self.assertLess(media, self.LIMITE, "%.1f ms por fotograma" % (media * 1000))


if __name__ == "__main__":
    unittest.main()
