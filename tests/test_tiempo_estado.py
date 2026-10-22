"""Pruebas del sol, las estaciones, las fiestas, el tiempo real (OpenWeather) y el estado guardado.

Nunca se usa la red ni la hora de verdad: OpenWeather se prueba con respuestas simuladas
(sustituyendo urllib.request.urlopen) y un reloj falso, y todo lo que se escribe va a
directorios temporales.
"""

import datetime
import io
import json
import os
import sys
import tempfile
import types
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hormiga import clima_real as CR   # noqa: E402
from hormiga import estado as E        # noqa: E402
from hormiga import fiestas as F       # noqa: E402
from hormiga import tiempo as T        # noqa: E402

UTC = datetime.timezone.utc
TOLERANCIA = 5   # minutos de margen con las horas publicadas de salida y puesta del sol


def _hay_zonas():
    """¿Están las zonas horarias del sistema? (sin ellas no se puede probar la hora local)."""
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo("Europe/Madrid")
        ZoneInfo("Australia/Sydney")
        return True
    except Exception:
        return False


con_zonas = unittest.skipUnless(_hay_zonas(), "faltan las zonas horarias del sistema (tzdata)")


def _minutos(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _hhmm(minutos):
    return "%02d:%02d" % divmod(round(minutos), 60)


# ===================================================================== tiempo.py: el sol

# Horas publicadas (timeanddate.com) para 2024. "24:03" es pasada la medianoche.
CIUDADES = [
    ("Madrid", 40.4168, -3.7038, "Europe/Madrid", (6, 21), "06:44", "21:48"),
    ("Madrid", 40.4168, -3.7038, "Europe/Madrid", (12, 21), "08:33", "17:53"),
    ("Málaga", 36.72, -4.42, "Europe/Madrid", (6, 21), "06:59", "21:41"),
    ("Londres", 51.5074, -0.1278, "Europe/London", (6, 21), "04:43", "21:21"),
    ("Londres", 51.5074, -0.1278, "Europe/London", (12, 21), "08:03", "15:53"),
    ("Nueva York", 40.7128, -74.0060, "America/New_York", (6, 21), "05:25", "20:31"),
    ("Nueva York", 40.7128, -74.0060, "America/New_York", (12, 21), "07:16", "16:32"),
    ("Sídney", -33.8688, 151.2093, "Australia/Sydney", (6, 21), "07:00", "16:54"),
    ("Sídney", -33.8688, 151.2093, "Australia/Sydney", (12, 21), "05:41", "20:05"),
    ("Tokio", 35.6762, 139.6503, "Asia/Tokyo", (6, 21), "04:25", "19:00"),
    ("Buenos Aires", -34.6037, -58.3816, "America/Argentina/Buenos_Aires", (6, 21), "08:00", "17:50"),
    ("Reikiavik", 64.1466, -21.9426, "Atlantic/Reykjavik", (6, 21), "02:55", "24:03"),
    ("Reikiavik", 64.1466, -21.9426, "Atlantic/Reykjavik", (12, 21), "11:22", "15:29"),
]

TROMSO = (69.6492, 18.9553)
LONGYEARBYEN = (78.2232, 15.6267)
MCMURDO = (-77.85, 166.67)


def _de_noche(sol, minuto):
    """Igual que el hormiguero (hormiga/mundo.py): de noche si no está entre amanecer y anochecer."""
    a, p = sol
    return not (a <= minuto < p)


class SolTest(unittest.TestCase):

    @con_zonas
    def test_ciudades_conocidas(self):
        for nombre, lat, lon, zona, (mes, dia), amanecer, anochecer in CIUDADES:
            fecha = datetime.date(2024, mes, dia)
            with self.subTest(ciudad=nombre, fecha=fecha):
                a, p = T.sol(fecha, lat, lon, zona)
                self.assertLessEqual(abs(a - _minutos(amanecer)), TOLERANCIA,
                                     "amanecer %s, esperado %s" % (_hhmm(a), amanecer))
                self.assertLessEqual(abs(p - _minutos(anochecer)), TOLERANCIA,
                                     "anochecer %s, esperado %s" % (_hhmm(p), anochecer))

    @con_zonas
    def test_malaga_por_defecto(self):
        fecha = datetime.date(2025, 8, 15)
        self.assertEqual(T.sol(fecha, zona="Europe/Madrid"), T.sol(fecha, 36.72, -4.42, "Europe/Madrid"))

    def test_noche_polar(self):
        casos = [("Tromsø", TROMSO, datetime.date(2024, 12, 21)),
                 ("Longyearbyen", LONGYEARBYEN, datetime.date(2025, 1, 10)),
                 ("McMurdo", MCMURDO, datetime.date(2024, 6, 21))]
        for nombre, (lat, lon), fecha in casos:
            with self.subTest(lugar=nombre, fecha=fecha):
                s = T.sol(fecha, lat, lon, "UTC")
                self.assertEqual(s[0], s[1])
                self.assertTrue(all(_de_noche(s, m) for m in range(0, 24 * 60, 15)))

    def test_sol_de_medianoche(self):
        casos = [("Tromsø", TROMSO, datetime.date(2024, 6, 21)),
                 ("Longyearbyen", LONGYEARBYEN, datetime.date(2025, 7, 10)),
                 ("McMurdo", MCMURDO, datetime.date(2024, 12, 21))]
        for nombre, (lat, lon), fecha in casos:
            with self.subTest(lugar=nombre, fecha=fecha):
                s = T.sol(fecha, lat, lon, "UTC")
                self.assertEqual(s, (0, 24 * 60))
                self.assertFalse(any(_de_noche(s, m) for m in range(24 * 60)))

    def test_noche_polar_no_depende_de_la_zona(self):
        # sin sol en todo el día, da igual la zona horaria (ni siquiera hace falta tzdata)
        fecha = datetime.date(2024, 12, 21)
        self.assertEqual(T.sol(fecha, TROMSO[0], TROMSO[1], "Europe/Oslo"),
                         T.sol(fecha, TROMSO[0], TROMSO[1], None))

    @con_zonas
    def test_tromso_en_el_equinoccio_tiene_dia_y_noche(self):
        a, p = T.sol(datetime.date(2024, 3, 20), TROMSO[0], TROMSO[1], "Europe/Oslo")
        self.assertLess(0, a)
        self.assertLess(a, p)
        self.assertLess(p, 24 * 60)
        self.assertLess(abs((p - a) - 12 * 60), 30)

    @con_zonas
    def test_hemisferios_al_reves(self):
        junio, diciembre = datetime.date(2024, 6, 21), datetime.date(2024, 12, 21)

        def largo(fecha, lat, lon, zona):
            a, p = T.sol(fecha, lat, lon, zona)
            return p - a

        self.assertGreater(largo(junio, 40.4168, -3.7038, "Europe/Madrid"),
                           largo(diciembre, 40.4168, -3.7038, "Europe/Madrid"))
        self.assertLess(largo(junio, -33.8688, 151.2093, "Australia/Sydney"),
                        largo(diciembre, -33.8688, 151.2093, "Australia/Sydney"))
        # en el ecuador el día dura casi lo mismo todo el año
        quito = [largo(f, -0.1807, -78.4678, "America/Guayaquil") for f in (junio, diciembre)]
        self.assertLess(abs(quito[0] - quito[1]), 10)
        self.assertLess(abs(quito[0] - 12 * 60), 15)

    @con_zonas
    def test_la_zona_solo_desplaza_las_horas(self):
        fecha = datetime.date(2024, 7, 1)
        madrid = T.sol(fecha, 40.4168, -3.7038, "Europe/Madrid")
        utc = T.sol(fecha, 40.4168, -3.7038, "UTC")
        self.assertAlmostEqual(madrid[0] - utc[0], 120)
        self.assertAlmostEqual(madrid[1] - utc[1], 120)

    @con_zonas
    def test_desfase_horario_con_horario_de_verano(self):
        casos = [("Europe/Madrid", datetime.date(2024, 7, 1), 120),
                 ("Europe/Madrid", datetime.date(2024, 1, 15), 60),
                 ("Europe/Madrid", datetime.date(2024, 3, 31), 120),   # día del cambio de hora
                 ("Europe/Madrid", datetime.date(2024, 10, 27), 60),
                 ("Australia/Sydney", datetime.date(2024, 6, 21), 600),
                 ("Australia/Sydney", datetime.date(2024, 12, 21), 660),
                 ("America/New_York", datetime.date(2024, 7, 4), -240),
                 ("America/New_York", datetime.date(2024, 1, 15), -300),
                 ("UTC", datetime.date(2024, 7, 1), 0)]
        for zona, fecha, minutos in casos:
            with self.subTest(zona=zona, fecha=fecha):
                self.assertEqual(T.desfase_horario(fecha, zona), minutos)

    def test_zona_horaria_que_no_existe(self):
        for nombre in (None, "", "No/Existe", "Europa/Madriz"):
            with self.subTest(nombre=nombre):
                self.assertIsNone(T.zona_horaria(nombre))

    @con_zonas
    def test_zona_horaria_con_espacios(self):
        self.assertIsNotNone(T.zona_horaria("  Europe/Madrid "))


# ===================================================================== tiempo.py: estaciones

class EstacionTest(unittest.TestCase):

    def test_cambios_de_estacion_en_el_norte(self):
        casos = [((1, 15), "invierno"), ((3, 19), "invierno"), ((3, 20), "primavera"),
                 ((6, 20), "primavera"), ((6, 21), "verano"), ((9, 22), "verano"),
                 ((9, 23), "otoño"), ((12, 20), "otoño"), ((12, 21), "invierno"),
                 ((12, 31), "invierno"), ((2, 29), "invierno")]
        for (mes, dia), esperada in casos:
            with self.subTest(fecha="%02d-%02d" % (dia, mes)):
                self.assertEqual(T.estacion(datetime.date(2024, mes, dia)), esperada)

    def test_hemisferio_sur_al_reves(self):
        casos = [((1, 15), "verano"), ((4, 15), "otoño"), ((7, 15), "invierno"),
                 ((10, 15), "primavera"), ((12, 25), "verano")]
        for (mes, dia), esperada in casos:
            with self.subTest(fecha="%02d-%02d" % (dia, mes)):
                self.assertEqual(T.estacion(datetime.date(2025, mes, dia), sur=True), esperada)

    def test_todo_el_anio_cuadra_entre_hemisferios(self):
        dia = datetime.date(2024, 1, 1)
        vistas = set()
        while dia.year == 2024:
            norte, sur = T.estacion(dia), T.estacion(dia, sur=True)
            self.assertEqual(sur, T.ESTACIONES[(T.ESTACIONES.index(norte) + 2) % 4], dia)
            vistas.add(norte)
            dia += datetime.timedelta(days=1)
        self.assertEqual(vistas, set(T.ESTACIONES))


# ===================================================================== tiempo.py: el tiempo

class TiempoForzadoTest(unittest.TestCase):

    def test_cada_tipo(self):
        esperado = {   # tipo: (llueve, tormenta, nieve, calima, hay lluvia o nieve)
            "despejado": (False, False, False, False, False),
            "nublado": (False, False, False, False, False),
            "lluvia": (True, False, False, False, True),
            "tormenta": (True, True, False, False, True),
            "nieve": (False, False, True, False, True),
            "calima": (False, False, False, True, False),
        }
        self.assertEqual(set(esperado), set(T.TiempoForzado.TIPOS))
        for tipo, (llueve, tormenta, nieve, calima, cae) in esperado.items():
            with self.subTest(tipo=tipo):
                t = T.TiempoForzado(tipo)
                self.assertEqual((t.llueve, t.tormenta, t.nieve, t.calima), (llueve, tormenta, nieve, calima))
                self.assertFalse(t.terral)
                self.assertIsNone(t.sol)
                self.assertTrue(0 <= t.nubes <= 1)
                for minuto in (0, 600, 1439):
                    self.assertEqual(t.lluvia(minuto) > 0, cae)
                    self.assertTrue(0 <= t.lluvia(minuto) <= 1)

    def test_nubes(self):
        self.assertLess(T.TiempoForzado("despejado").nubes, 0.5)
        self.assertGreater(T.TiempoForzado("nublado").nubes, 0.8)
        self.assertGreater(T.TiempoForzado("tormenta").lluvia(0), T.TiempoForzado("lluvia").lluvia(0))

    def test_temperatura(self):
        self.assertEqual(T.TiempoForzado("despejado").temperatura(720), 15.0)
        self.assertLess(T.TiempoForzado("nieve").temperatura(720), 0)
        self.assertEqual(T.TiempoForzado("nieve", 3.5).temperatura(0), 3.5)
        self.assertEqual(T.TiempoForzado("lluvia", 0).temperatura(0), 0)   # 0 grados no es "sin dar"
        self.assertEqual(T.TiempoForzado("calima", 38).temp, 38)


class TiempoDelDiaTest(unittest.TestCase):

    def test_el_mismo_dia_siempre_igual(self):
        fecha = datetime.date(2024, 11, 3)
        a, b = T.TiempoDelDia(fecha, 7), T.TiempoDelDia(fecha, 7)
        for k in ("llueve", "lluvias", "tormenta", "nubes", "calima", "terral", "variacion"):
            self.assertEqual(getattr(a, k), getattr(b, k), k)
        self.assertIs(T.tiempo_del_dia(fecha, 7), T.tiempo_del_dia(fecha, 7))

    def test_otra_semilla_otro_tiempo(self):
        dias = [datetime.date(2024, 1, 1) + datetime.timedelta(days=d) for d in range(365)]
        a = [T.TiempoDelDia(d, 1).llueve for d in dias]
        b = [T.TiempoDelDia(d, 2).llueve for d in dias]
        self.assertNotEqual(a, b)

    def test_llueve_mas_en_otono_que_en_verano(self):
        def dias_de_lluvia(mes):
            return sum(T.TiempoDelDia(datetime.date(anio, mes, d), 3).llueve
                       for anio in range(2010, 2030) for d in range(1, 29))
        self.assertGreater(dias_de_lluvia(11), 3 * max(1, dias_de_lluvia(7)))

    def test_valores_con_sentido(self):
        dia = datetime.date(2023, 1, 1)
        for _ in range(730):
            t = T.TiempoDelDia(dia, 5)
            self.assertEqual(t.llueve, bool(t.lluvias), dia)
            if t.tormenta:
                self.assertTrue(t.llueve, dia)
                self.assertIn(dia.month, (9, 10, 11, 12, 1), dia)
            if t.calima or t.terral:
                self.assertFalse(t.llueve, dia)
            self.assertTrue(0 <= t.nubes <= 1, dia)
            for ini, fin, inten in t.lluvias:
                self.assertTrue(0 <= ini < fin <= 24 * 60, dia)
                self.assertTrue(0 < inten <= 1, dia)
            for minuto in range(0, 24 * 60, 30):
                self.assertTrue(0 <= t.lluvia(minuto) <= 1, dia)
                self.assertTrue(-10 < t.temperatura(minuto) < 45, dia)
            dia += datetime.timedelta(days=1)

    def test_llovio_hace(self):
        # un rato con lluvia y otro sin lluvia en las horas anteriores, buscados con fecha fija
        dia, con_lluvia, seco = datetime.date(2024, 10, 1), None, None
        for _ in range(400):
            t = T.tiempo_del_dia(dia, 9)
            if con_lluvia is None and t.lluvias:
                ini, fin, _i = t.lluvias[0]
                minuto = int((ini + fin) / 2)
                con_lluvia = datetime.datetime.combine(dia, datetime.time(minuto // 60, minuto % 60))
            ayer = T.tiempo_del_dia(dia - datetime.timedelta(days=1), 9)
            if seco is None and not t.lluvias and not ayer.lluvias:
                seco = datetime.datetime.combine(dia, datetime.time(20, 0))
            if con_lluvia and seco:
                break
            dia += datetime.timedelta(days=1)
        self.assertIsNotNone(con_lluvia)
        self.assertIsNotNone(seco)
        self.assertTrue(T.llovio_hace(con_lluvia, 0, 9))
        self.assertTrue(T.llovio_hace(con_lluvia, 8, 9))
        self.assertFalse(T.llovio_hace(seco, 8, 9))

    def test_fase_lunar(self):
        self.assertAlmostEqual(T.fase_lunar(datetime.date(2000, 1, 6)), 0.0)
        self.assertAlmostEqual(T.fase_lunar(datetime.date(2024, 4, 23)), 0.5, delta=0.04)   # luna llena
        nueva = T.fase_lunar(datetime.date(2024, 4, 8))                                      # luna nueva
        self.assertLess(min(nueva, 1 - nueva), 0.04)


# ===================================================================== fiestas.py

class PascuaTest(unittest.TestCase):

    def test_anios_conocidos(self):
        conocidas = {1818: (3, 22), 1943: (4, 25), 2000: (4, 23), 2008: (3, 23), 2011: (4, 24),
                     2019: (4, 21), 2023: (4, 9), 2024: (3, 31), 2025: (4, 20), 2026: (4, 5),
                     2027: (3, 28), 2028: (4, 16), 2038: (4, 25), 2285: (3, 22)}
        for anio, (mes, dia) in conocidas.items():
            with self.subTest(anio=anio):
                self.assertEqual(T.pascua(anio), datetime.date(anio, mes, dia))

    def test_siempre_domingo_entre_22_de_marzo_y_25_de_abril(self):
        for anio in range(1900, 2200):
            p = T.pascua(anio)
            self.assertEqual(p.weekday(), 6, anio)
            self.assertTrue(datetime.date(anio, 3, 22) <= p <= datetime.date(anio, 4, 25), anio)


class FechaFiestaTest(unittest.TestCase):

    def test_formas_de_escribirla(self):
        casos = {"pascua": (4, 20), "pascua+0": (4, 20), "Pascua + 1": (4, 21), "PASCUA-2": (4, 18),
                 "pascua-47": (3, 4), "pascua+49": (6, 8), "pascua+60": (6, 19),
                 "14-02": (2, 14), " 01/05 ": (5, 1), "6-1": (1, 6)}
        for espec, (mes, dia) in casos.items():
            with self.subTest(espec=espec):
                self.assertEqual(F._fecha(espec, 2025), datetime.date(2025, mes, dia))

    def test_mal_escritas_dan_valueerror(self):
        for espec in ("32-01", "29-02", "pascua+x", "pascua+99999999999", "pascua-999999",
                      "1-2-3", "", "navidad", "01-99999999999999999999"):
            with self.subTest(espec=espec):
                with self.assertRaises(ValueError):
                    F._fecha(espec, 2025)

    def test_29_de_febrero_en_bisiesto(self):
        self.assertEqual(F._fecha("29-02", 2028), datetime.date(2028, 2, 29))


def _fiesta(desde, hasta=None, **mas):
    d = dict(nombre="Prueba", desde=desde, **mas)
    if hasta is not None:
        d["hasta"] = hasta
    return F.Fiesta(d)


def _dias(desde, hasta):
    d = desde
    while d <= hasta:
        yield d
        d += datetime.timedelta(days=1)


class RangoFiestaTest(unittest.TestCase):

    def test_rango_que_cruza_el_anio(self):
        navidad = _fiesta("15-12", "06-01")
        self.assertEqual(navidad.rango(2024), (datetime.date(2024, 12, 15), datetime.date(2025, 1, 6)))
        for d in _dias(datetime.date(2024, 12, 15), datetime.date(2025, 1, 6)):
            self.assertTrue(navidad.activa(d), d)
        for d in (datetime.date(2024, 12, 14), datetime.date(2025, 1, 7), datetime.date(2025, 7, 1)):
            self.assertFalse(navidad.activa(d), d)
        # los primeros días del año salen del rango que empezó el año anterior
        self.assertTrue(navidad.activa(datetime.date(2024, 1, 3)))
        self.assertTrue(navidad.empieza(datetime.date(2024, 12, 15)))
        self.assertFalse(navidad.empieza(datetime.date(2025, 1, 1)))
        self.assertEqual(navidad.duracion(), 22)

    def test_nochevieja(self):
        f = _fiesta("31-12", "01-01")
        self.assertTrue(f.activa(datetime.date(2025, 12, 31)))
        self.assertTrue(f.activa(datetime.date(2026, 1, 1)))
        self.assertFalse(f.activa(datetime.date(2026, 1, 2)))
        self.assertFalse(f.activa(datetime.date(2025, 12, 30)))
        self.assertEqual(f.duracion(), 1)

    def test_un_solo_dia(self):
        f = _fiesta("23-04")
        self.assertEqual(f.hasta, "23-04")
        self.assertTrue(f.activa(datetime.date(2026, 4, 23)))
        self.assertFalse(f.activa(datetime.date(2026, 4, 24)))
        self.assertEqual(f.duracion(), 0)

    def test_semana_santa_con_pascua_mas_n(self):
        f = _fiesta("pascua-7", "pascua")
        casos = {2024: (datetime.date(2024, 3, 24), datetime.date(2024, 3, 31)),
                 2025: (datetime.date(2025, 4, 13), datetime.date(2025, 4, 20)),
                 2026: (datetime.date(2026, 3, 29), datetime.date(2026, 4, 5))}
        for anio, (a, b) in casos.items():
            with self.subTest(anio=anio):
                self.assertEqual(f.rango(anio), (a, b))
                self.assertTrue(f.empieza(a))
                for d in _dias(a, b):
                    self.assertTrue(f.activa(d), d)
                self.assertFalse(f.activa(a - datetime.timedelta(days=1)))
                self.assertFalse(f.activa(b + datetime.timedelta(days=1)))

    def test_carnaval_y_corpus(self):
        carnaval = _fiesta("pascua-49", "pascua-47")
        self.assertEqual(carnaval.rango(2024), (datetime.date(2024, 2, 11), datetime.date(2024, 2, 13)))
        self.assertEqual(carnaval.rango(2025), (datetime.date(2025, 3, 2), datetime.date(2025, 3, 4)))
        corpus = _fiesta("pascua+60")
        self.assertTrue(corpus.activa(datetime.date(2025, 6, 19)))
        self.assertTrue(corpus.activa(datetime.date(2026, 6, 4)))
        self.assertFalse(corpus.activa(datetime.date(2026, 6, 19)))

    def test_29_de_febrero_solo_en_bisiestos(self):
        f = _fiesta("29-02")
        self.assertTrue(f.activa(datetime.date(2028, 2, 29)))
        self.assertTrue(f.empieza(datetime.date(2028, 2, 29)))
        for d in _dias(datetime.date(2025, 2, 25), datetime.date(2025, 3, 3)):   # sin cascar
            self.assertFalse(f.activa(d), d)
            self.assertFalse(f.empieza(d), d)

    def test_hasta_el_29_de_febrero(self):
        # los años sin 29 de febrero, una fiesta que acaba ese día acaba el 28 (no se pierde entera)
        f = _fiesta("20-02", "29-02")
        self.assertEqual(f.rango(2027), (datetime.date(2027, 2, 20), datetime.date(2027, 2, 28)))
        self.assertTrue(f.activa(datetime.date(2027, 2, 25)))
        self.assertTrue(f.activa(datetime.date(2028, 2, 29)))
        self.assertFalse(f.activa(datetime.date(2027, 3, 1)))

    def test_activas_de_la_mas_larga_a_la_mas_corta(self):
        fiestas = F.cargar({"fiesta": [
            {"nombre": "Nochevieja", "desde": "31-12", "hasta": "01-01", "decoracion": "nochevieja"},
            {"nombre": "Navidad", "desde": "15-12", "hasta": "06-01", "decoracion": "navidad"},
            {"nombre": "Verano", "desde": "21-06", "hasta": "22-09"},
        ]})
        act = F.activas(fiestas, datetime.date(2025, 12, 31))
        self.assertEqual([f.nombre for f in act], ["Navidad", "Nochevieja"])
        self.assertEqual([f.nombre for f in F.activas(fiestas, datetime.date(2026, 1, 1))],
                         ["Navidad", "Nochevieja"])
        self.assertEqual(F.activas(fiestas, datetime.date(2026, 3, 1)), [])


class CargarFiestasTest(unittest.TestCase):

    def test_bien_escritas(self):
        avisos = []
        fs = F.cargar({"fiesta": [
            {"nombre": "Reyes", "desde": "05-01", "hasta": "06-01", "decoracion": "Reyes", "gorro": "corona"},
            {"nombre": "Semana Santa", "desde": "pascua-7", "hasta": "pascua", "decoracion": "semana_santa"},
        ]}, avisos)
        self.assertEqual(avisos, [])
        self.assertEqual([f.nombre for f in fs], ["Reyes", "Semana Santa"])
        self.assertEqual(fs[0].decoracion, "reyes")
        self.assertEqual(fs[0].gorro, "corona")
        self.assertEqual(fs[0].mensaje, "Reyes")
        self.assertIsNone(fs[1].gorro)

    def test_fechas_mal_escritas_se_quitan_con_aviso(self):
        avisos = []
        fs = F.cargar({"fiesta": [
            {"nombre": "Mala", "desde": "32-13"},
            {"nombre": "Pascua rara", "desde": "pascua+x", "hasta": "pascua+99999999999"},
            {"nombre": "Buena", "desde": "29-02"},
        ]}, avisos)
        self.assertEqual([f.nombre for f in fs], ["Buena"])
        self.assertEqual(len(avisos), 2)
        self.assertIn("Mala", avisos[0])
        self.assertIn("pascua+x", avisos[1])

    def test_decoracion_o_gorro_que_no_existen(self):
        avisos = []
        fs = F.cargar({"fiesta": [{"nombre": "Rara", "desde": "01-08", "decoracion": "cohetes",
                                   "gorro": "chistera"}]}, avisos)
        self.assertEqual(len(fs), 1)   # se queda, pero avisa
        self.assertEqual(len(avisos), 2)
        self.assertIn("cohetes", avisos[0])
        self.assertIn("chistera", avisos[1])

    def test_un_solo_corchete_y_cosas_raras(self):
        avisos = []
        fs = F.cargar({"fiesta": {"nombre": "Sola", "desde": "01-05"}}, avisos)
        self.assertEqual([f.nombre for f in fs], ["Sola"])
        self.assertIn("[[fiesta]]", avisos[0])
        avisos = []
        self.assertEqual(F.cargar({"fiesta": ["texto", 3]}, avisos), [])
        self.assertEqual(len(avisos), 2)
        self.assertEqual(F.cargar({}), [])


class CumpleTest(unittest.TestCase):

    def test_dia_mes(self):
        casos = {"05-03": (3, 5), "5/3": (3, 5), "05-03-1990": (3, 5), "1990-03-05": (3, 5),
                 "12-25": (12, 25), "29-02": (2, 29), " 31-12 ": (12, 31)}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(F.dia_mes(texto), esperado)

    def test_dia_mes_mal_escrito(self):
        for texto in ("31-02", "13-13", "00-05", "abc", "", "1-2-3-4", "99999999999999999999-01"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    F.dia_mes(texto)

    def test_cumple_del_29_de_febrero(self):
        p = {"nombre": "Ana", "cumple": "29-02"}
        self.assertTrue(F.es_cumple(p, datetime.date(2025, 2, 28)))   # año no bisiesto: el 28
        self.assertFalse(F.es_cumple(p, datetime.date(2025, 3, 1)))
        self.assertTrue(F.es_cumple(p, datetime.date(2028, 2, 29)))
        self.assertFalse(F.es_cumple(p, datetime.date(2028, 2, 28)))

    def test_cumple_normal_y_sin_cumple(self):
        self.assertTrue(F.es_cumple({"cumple": "14-07"}, datetime.date(2026, 7, 14)))
        self.assertFalse(F.es_cumple({"cumple": "14-07"}, datetime.date(2026, 7, 15)))
        self.assertFalse(F.es_cumple({}, datetime.date(2026, 7, 14)))
        self.assertFalse(F.es_cumple({"cumple": "nunca"}, datetime.date(2026, 7, 14)))


# ===================================================================== clima_real.py

# 15 de noviembre de 2024 a mediodía (UTC): la hora "de ahora" de las pruebas
T0 = datetime.datetime(2024, 11, 15, 12, 0, tzinfo=UTC).timestamp()
HORA = 3600


def _respuesta(codigo=800, temp=20.0, nubes=0, **mas):
    """Lo que devuelve OpenWeather (lo justo)."""
    d = {"weather": [{"id": codigo, "main": "x", "description": "descripción %d" % codigo}],
         "main": {"temp": temp}, "clouds": {"all": nubes}, "sys": {}, "cod": 200}
    d.update(mas)
    return d


class RedFalsa:
    """Sustituye a urllib.request.urlopen: devuelve (o lanza) las respuestas en orden y apunta
    lo que se pidió. Si se pide más de lo previsto, falla (y nunca sale a la red de verdad)."""

    def __init__(self):
        self.respuestas = []
        self.pedidas = []

    def __call__(self, url, timeout=None, **_):
        self.pedidas.append((url, timeout))
        if not self.respuestas:
            raise AssertionError("petición no prevista a %s" % url)
        r = self.respuestas.pop(0)
        if isinstance(r, BaseException):
            raise r
        if isinstance(r, dict):
            r = json.dumps(r)
        if isinstance(r, str):
            r = r.encode("utf-8")
        return io.BytesIO(r)


class ClimaBase(unittest.TestCase):
    """Reloj falso, red falsa, sin hilo de fondo y todo en un directorio temporal."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.carpeta = os.path.join(tmp.name, "local")
        self.ruta = os.path.join(self.carpeta, "openweather.json")
        self.t = T0
        self.red = RedFalsa()
        reloj = types.SimpleNamespace(time=lambda: self.t, sleep=lambda s: None)
        parches = [
            mock.patch.object(CR.OpenWeather, "_bucle", lambda s: None),   # sin hilo que pida solo
            mock.patch.object(urllib.request, "urlopen", self.red),
            mock.patch.object(CR, "time", reloj),
            mock.patch.object(T, "ahora", lambda zona=None: datetime.datetime.fromtimestamp(
                self.t, UTC).replace(tzinfo=None)),
        ]
        for p in parches:
            p.start()
            self.addCleanup(p.stop)

    def cliente(self, cada_minutos=10, zona=None):
        return CR.OpenWeather("clave-de-prueba", 36.72, -4.42, self.carpeta, cada_minutos, zona)

    def escribir_cache(self, contenido):
        os.makedirs(self.carpeta, exist_ok=True)
        modo = "wb" if isinstance(contenido, bytes) else "w"
        with open(self.ruta, modo) as f:
            f.write(contenido if isinstance(contenido, (str, bytes)) else json.dumps(contenido))

    def leer_cache(self):
        with open(self.ruta) as f:
            return json.load(f)

    def pedir(self, ow, respuesta):
        self.red.respuestas.append(respuesta)
        ow._pedir()


class TiempoRealTest(unittest.TestCase):

    def test_lluvia(self):
        casos = {300: 0.3, 500: 0.45, 501: 0.7, 502: 1.0, 511: 0.6, 520: 0.5, 521: 0.7, 531: 1.0}
        for codigo, inten in casos.items():
            with self.subTest(codigo=codigo):
                t = CR.TiempoReal(_respuesta(codigo))
                self.assertTrue(t.llueve)
                self.assertFalse(t.tormenta)
                self.assertFalse(t.nieve)
                self.assertEqual(t.lluvia(0), inten)

    def test_tormenta(self):
        for codigo, inten in {200: 0.85, 211: 0.85, 231: 0.45, 232: 0.45}.items():
            with self.subTest(codigo=codigo):
                t = CR.TiempoReal(_respuesta(codigo))
                self.assertTrue(t.tormenta)
                self.assertTrue(t.llueve)
                self.assertEqual(t.lluvia(720), inten)

    def test_nieve(self):
        for codigo, inten in {600: 0.4, 601: 0.7, 602: 1.0, 611: 0.6, 622: 0.6}.items():
            with self.subTest(codigo=codigo):
                t = CR.TiempoReal(_respuesta(codigo, temp=-2))
                self.assertTrue(t.nieve)
                self.assertFalse(t.llueve)
                self.assertFalse(t.tormenta)
                self.assertEqual(t.lluvia(0), inten)
                self.assertEqual(t.temperatura(0), -2.0)

    def test_sin_lluvia(self):
        for codigo in (800, 801, 804, 701, 741, 761):
            with self.subTest(codigo=codigo):
                t = CR.TiempoReal(_respuesta(codigo))
                self.assertFalse(t.llueve or t.nieve or t.tormenta)
                self.assertEqual(t.lluvia(0), 0.0)
        self.assertTrue(CR.TiempoReal(_respuesta(761)).calima)
        self.assertTrue(CR.TiempoReal(_respuesta(741)).niebla)
        self.assertFalse(CR.TiempoReal(_respuesta(800)).calima)

    def test_nubes_y_temperatura(self):
        self.assertEqual(CR.TiempoReal(_respuesta(nubes=75)).nubes, 0.75)
        self.assertEqual(CR.TiempoReal(_respuesta(nubes=150)).nubes, 1.0)
        d = _respuesta()
        del d["clouds"]
        self.assertEqual(CR.TiempoReal(d).nubes, 0.0)
        self.assertEqual(CR.TiempoReal(_respuesta(temp="21.5")).temperatura(0), 21.5)

    @con_zonas
    def test_sol_en_hora_de_la_ciudad(self):
        sale = datetime.datetime(2024, 6, 21, 4, 44, tzinfo=UTC).timestamp()    # 06:44 en Madrid
        se_pone = datetime.datetime(2024, 6, 21, 19, 48, tzinfo=UTC).timestamp()  # 21:48 en Madrid
        t = CR.TiempoReal(_respuesta(sys={"sunrise": sale, "sunset": se_pone}), "Europe/Madrid")
        self.assertAlmostEqual(t.sol[0], 6 * 60 + 44)
        self.assertAlmostEqual(t.sol[1], 21 * 60 + 48)

    def test_sin_sol(self):
        self.assertIsNone(CR.TiempoReal(_respuesta()).sol)
        self.assertIsNone(CR.TiempoReal(_respuesta(sys={"sunrise": 0, "sunset": 0})).sol)

    def test_respuestas_que_no_valen(self):
        for d in ({}, {"cod": 401, "message": "Invalid API key"}, {"weather": [{"id": 800}]},
                  {"weather": [{"id": "x"}], "main": {"temp": 1}}):
            with self.subTest(datos=d):
                with self.assertRaises(Exception):
                    CR.TiempoReal(d)


class OpenWeatherTest(ClimaBase):

    def test_sin_datos_no_hay_tiempo_real(self):
        ow = self.cliente()
        self.assertIsNone(ow.actual())
        self.assertIsNone(ow.dia(datetime.date(2024, 11, 15)))
        self.assertFalse(ow.llovio_hace(8))
        self.assertFalse(ow.nevo_hace(24))
        self.assertLessEqual(ow.proximo, self.t)   # sin datos, toca pedirlos ya
        self.assertEqual(self.red.pedidas, [])
        self.assertFalse(os.path.exists(self.carpeta))

    def test_pide_la_url_correcta(self):
        ow = self.cliente()
        self.pedir(ow, _respuesta())
        url, timeout = self.red.pedidas[0]
        partes = urllib.parse.urlsplit(url)
        self.assertEqual(partes.scheme, "https")
        self.assertEqual(partes.netloc, "api.openweathermap.org")
        q = dict(urllib.parse.parse_qsl(partes.query))
        self.assertEqual(q, {"lat": "36.72", "lon": "-4.42", "appid": "clave-de-prueba",
                             "units": "metric", "lang": "es"})
        self.assertTrue(timeout and timeout <= 60)

    def test_cada_cuanto(self):
        self.assertEqual(self.cliente(1).cada, 5 * 60)    # nunca menos de 5 minutos
        self.assertEqual(self.cliente(30).cada, 30 * 60)
        self.assertEqual(self.cliente("15").cada, 15 * 60)

    def test_lluvia_queda_apuntada(self):
        ow = self.cliente()
        self.pedir(ow, _respuesta(501, temp=14.0))
        t = ow.actual()
        self.assertTrue(t.llueve)
        self.assertEqual(t.temperatura(0), 14.0)
        self.assertIsNone(ow.error)
        self.assertEqual(ow.hora, T0)
        self.assertEqual(ow.proximo, T0 + 600)
        self.assertEqual(ow.dia(datetime.date(2024, 11, 15)),
                         {"llueve": True, "tormenta": False, "nieve": False, "calima": False, "tmax": 14.0})
        self.assertTrue(ow.llovio_hace(8))
        self.t = T0 + 9 * HORA
        self.assertFalse(ow.llovio_hace(8))
        self.assertTrue(ow.llovio_hace(10))
        # y en el disco, sin restos del guardado
        self.assertEqual(os.listdir(self.carpeta), ["openweather.json"])
        guardado = self.leer_cache()
        self.assertEqual(guardado["hora"], T0)
        self.assertEqual(guardado["ultima_lluvia"], T0)
        self.assertTrue(guardado["historial"]["2024-11-15"]["llueve"])

    def test_tormenta_y_despues_despejado_el_mismo_dia(self):
        ow = self.cliente()
        self.pedir(ow, _respuesta(211, temp=18.0))
        self.assertTrue(ow.actual().tormenta)
        self.t += HORA
        self.pedir(ow, _respuesta(800, temp=22.5))
        self.t += HORA
        self.pedir(ow, _respuesta(800, temp=20.0))
        ahora = ow.actual()
        self.assertFalse(ahora.tormenta or ahora.llueve)
        dia = ow.dia(datetime.date(2024, 11, 15))
        self.assertTrue(dia["tormenta"])   # lo que pasó en el día no se olvida
        self.assertTrue(dia["llueve"])
        self.assertEqual(dia["tmax"], 22.5)
        self.assertEqual(ow.ultima_lluvia, T0)
        self.assertTrue(ow.llovio_hace(3))

    def test_nieve(self):
        ow = self.cliente()
        self.pedir(ow, _respuesta(601, temp=-1.0))
        self.assertTrue(ow.actual().nieve)
        self.assertTrue(ow.dia(datetime.date(2024, 11, 15))["nieve"])
        self.assertEqual(ow.ultima_nieve, T0)
        self.assertTrue(ow.nevo_hace(24))
        self.assertTrue(ow.llovio_hace(1))   # la nieve también moja
        self.t = T0 + 25 * HORA
        self.assertFalse(ow.nevo_hace(24))
        self.assertEqual(self.leer_cache()["ultima_nieve"], T0)

    def test_cada_dia_su_entrada(self):
        ow = self.cliente()
        self.pedir(ow, _respuesta(500, temp=15.0))
        self.t = T0 + 24 * HORA
        self.pedir(ow, _respuesta(800, temp=19.0))
        self.assertTrue(ow.dia(datetime.date(2024, 11, 15))["llueve"])
        self.assertFalse(ow.dia(datetime.date(2024, 11, 16))["llueve"])
        self.assertEqual(ow.dia(datetime.date(2024, 11, 16))["tmax"], 19.0)
        self.assertIsNone(ow.dia(datetime.date(2024, 11, 17)))

    def test_error_de_red_no_rejuvenece_los_datos(self):
        ow = self.cliente()
        self.pedir(ow, _respuesta(500))
        self.t = T0 + 2 * HORA
        self.pedir(ow, urllib.error.URLError("sin red"))
        self.assertEqual(ow.hora, T0)            # los datos conservan su hora
        self.assertIn("sin red", ow.error)
        self.assertEqual(ow.proximo, self.t + 120)   # reintenta pronto
        self.assertIsNotNone(ow.actual())        # dos horas: aún valen
        self.t = T0 + 3.5 * HORA
        self.pedir(ow, TimeoutError("se acabó el tiempo"))
        self.assertEqual(ow.hora, T0)
        self.assertIsNone(ow.actual())           # tres horas y media: ya no valen
        self.assertEqual(self.leer_cache()["hora"], T0)
        # cuando vuelve la red, vuelven los datos
        self.pedir(ow, _respuesta(800))
        self.assertIsNotNone(ow.actual())
        self.assertIsNone(ow.error)
        self.assertEqual(ow.hora, self.t)

    def test_clave_rechazada_avisa(self):
        ow = self.cliente()
        no_vale = urllib.error.HTTPError(CR.URL, 401, "Unauthorized", {}, None)
        for _ in range(CR.FALLOS_AVISO - 1):
            self.pedir(ow, no_vale)
        self.assertIsNone(ow.aviso())
        self.pedir(ow, urllib.error.URLError("sin red"))   # sin red no es culpa de la clave
        self.assertIsNone(ow.aviso())
        for _ in range(CR.FALLOS_AVISO):
            self.pedir(ow, no_vale)
        self.assertIn("no acepta la clave", ow.aviso())
        self.pedir(ow, _respuesta(800))
        self.assertIsNone(ow.aviso())

    def test_respuestas_raras_cuentan_como_error(self):
        malas = [
            urllib.error.HTTPError(CR.URL, 401, "Unauthorized", {}, None),
            "<html>no es json</html>",
            {"cod": 401, "message": "Invalid API key"},
            {"weather": [], "main": {"temp": 3}},
            OSError("red caída"),
        ]
        ow = self.cliente()
        for mala in malas:
            with self.subTest(respuesta=repr(mala)[:40]):
                self.pedir(ow, mala)
                self.assertIsNotNone(ow.error)
                self.assertIsNone(ow.datos)
                self.assertIsNone(ow.actual())
                self.assertEqual(ow.historial, {})
                self.assertEqual(ow.proximo, self.t + 120)
        self.assertFalse(os.path.exists(self.ruta))

    def test_datos_del_disco(self):
        self.escribir_cache({"datos": _respuesta(500), "hora": T0 - HORA, "historial": {},
                             "ultima_lluvia": T0 - HORA, "ultima_nieve": None})
        ow = self.cliente()
        self.assertTrue(ow.actual().llueve)
        self.assertEqual(ow.proximo, T0 - HORA + 600)
        self.assertTrue(ow.llovio_hace(2))
        self.assertEqual(self.red.pedidas, [])

    def test_datos_viejos_del_disco_caducan(self):
        self.escribir_cache({"datos": _respuesta(500), "hora": T0 - 4 * HORA, "historial": {}})
        ow = self.cliente()
        self.assertIsNone(ow.actual())
        self.assertLessEqual(ow.proximo, self.t)   # toca pedir ya
        self.pedir(ow, urllib.error.URLError("sin red"))
        self.assertIsNone(ow.actual())             # el fallo no los da por buenos
        self.assertEqual(ow.hora, T0 - 4 * HORA)

    def test_formato_antiguo_sin_nieve(self):
        # lo que guardaba la primera versión: sin "ultima_nieve"
        self.escribir_cache({"datos": _respuesta(800), "hora": T0 - 600,
                             "historial": {"2024-11-14": {"llueve": True, "tormenta": False, "nieve": False,
                                                          "calima": False, "tmax": 16}},
                             "ultima_lluvia": T0 - 5 * HORA})
        ow = self.cliente()
        self.assertIsNotNone(ow.actual())
        self.assertIsNone(ow.ultima_nieve)
        self.assertFalse(ow.nevo_hace(24))
        self.assertTrue(ow.llovio_hace(6))
        self.assertTrue(ow.dia(datetime.date(2024, 11, 14))["llueve"])
        self.pedir(ow, _respuesta(800))
        self.assertIn("ultima_nieve", self.leer_cache())
        self.assertIn("2024-11-14", self.leer_cache()["historial"])

    def test_cache_corrupta(self):
        for contenido in ("", "esto no es json", '{"datos": {"weather": [', b"\xff\xfe\x00basura",
                          '{"hora": "ayer"}'):
            with self.subTest(contenido=contenido):
                self.escribir_cache(contenido)
                ow = self.cliente()
                self.assertIsNone(ow.actual())
                self.assertEqual(ow.historial, {})
                self.assertFalse(ow.llovio_hace(100))
                self.pedir(ow, _respuesta(500))        # al llegar datos buenos, se rehace
                self.assertTrue(ow.actual().llueve)
                self.assertTrue(self.leer_cache()["historial"]["2024-11-15"]["llueve"])
                self.assertEqual(os.listdir(self.carpeta), ["openweather.json"])

    # si local/openweather.json es JSON válido pero no tiene la forma esperada ([], null,
    # "hora": null, "historial": [], "weather": []), cuenta como una caché corrupta (antes
    # OpenWeather() o sus consultas lanzaban AttributeError, TypeError o IndexError)
    def test_cache_con_json_valido_pero_forma_rara(self):
        for contenido in ("[]", "null", '{"hora": null}', '{"historial": []}',
                          json.dumps({"datos": {"weather": []}, "hora": T0})):
            with self.subTest(contenido=contenido):
                self.escribir_cache(contenido)
                ow = self.cliente()
                self.assertIsNone(ow.actual())
                self.assertIsNone(ow.dia(datetime.date(2024, 11, 15)))

    # si la caché se guardó con el reloj adelantado ("hora" en el futuro), esos datos no valen y
    # se pide el tiempo enseguida (antes se daban por buenos, sin pedir otros, hasta esa fecha)
    def test_datos_con_hora_en_el_futuro(self):
        self.escribir_cache({"datos": _respuesta(500), "hora": T0 + 10 * 24 * HORA, "historial": {}})
        ow = self.cliente()
        self.assertLessEqual(ow.proximo, T0 + ow.cada)   # hay que pedir el tiempo pronto
        self.assertIsNone(ow.actual())                    # y no fiarse de unos datos "de dentro de 10 días"

    def test_historial_de_dos_anios(self):
        hoy = datetime.date(2024, 11, 15)
        viejo = {(hoy - datetime.timedelta(days=d)).isoformat():
                 {"llueve": d % 7 == 0, "tormenta": False, "nieve": False, "calima": False, "tmax": 20}
                 for d in range(1, 801)}
        self.escribir_cache({"datos": None, "hora": 0, "historial": viejo})
        ow = self.cliente()
        self.assertEqual(len(ow.historial), 800)
        self.pedir(ow, _respuesta(800))
        self.assertEqual(len(ow.historial), 730)
        claves = sorted(ow.historial)
        self.assertEqual(claves[-1], hoy.isoformat())
        self.assertEqual(claves[0], (hoy - datetime.timedelta(days=729)).isoformat())
        self.assertTrue(ow.dia(hoy - datetime.timedelta(days=7))["llueve"])
        self.assertIsNone(ow.dia(hoy - datetime.timedelta(days=800)))
        self.assertEqual(len(self.leer_cache()["historial"]), 730)

    def test_otro_cliente_lee_lo_guardado(self):
        ow = self.cliente()
        self.pedir(ow, _respuesta(211, temp=17.0))
        self.t += 600
        otro = self.cliente()
        self.assertTrue(otro.actual().tormenta)
        self.assertEqual(otro.historial, ow.historial)
        self.assertEqual(otro.ultima_lluvia, T0)
        self.assertEqual(otro.proximo, T0 + 600)
        self.assertEqual(len(self.red.pedidas), 1)

    def test_no_poder_guardar_no_tumba(self):
        # "local" es un fichero: no se puede crear la carpeta
        with open(self.carpeta, "w") as f:
            f.write("estorbo")
        ow = CR.OpenWeather("k", 1, 2, self.carpeta)
        self.pedir(ow, _respuesta(500))
        self.assertTrue(ow.actual().llueve)


class DesdeConfigTest(ClimaBase):

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.raiz = tmp.name
        p = mock.patch.dict(os.environ)
        p.start()
        self.addCleanup(p.stop)
        os.environ.pop("OPENWEATHER_API_KEY", None)

    def poner_fichero(self, texto):
        os.makedirs(os.path.join(self.raiz, "local"), exist_ok=True)
        with open(os.path.join(self.raiz, "local", "openweather_clave.txt"), "w") as f:
            f.write(texto)

    def test_sin_clave_no_hay_cliente(self):
        self.assertIsNone(CR.desde_config({}, self.raiz))
        self.assertIsNone(CR.desde_config({"tiempo": {"clave": "  "}}, self.raiz))

    def test_fuente_estadistica(self):
        os.environ["OPENWEATHER_API_KEY"] = "de-entorno"
        self.assertIsNone(CR.desde_config({"tiempo": {"fuente": "estadistico"}}, self.raiz))
        self.assertIsNotNone(CR.desde_config({"tiempo": {"fuente": "OpenWeather"}}, self.raiz))

    def test_fichero_vacio_o_con_bom(self):
        cfg = {"tiempo": {"clave": "de-config"}}
        self.poner_fichero("\n")   # vacío: vale la de config.toml
        self.assertEqual(CR.desde_config(cfg, self.raiz).clave, "de-config")
        with open(os.path.join(self.raiz, "local", "openweather_clave.txt"), "wb") as f:
            f.write(b"\xef\xbb\xbfcon-bom\r\n")   # «UTF-8 con BOM» del Bloc de notas
        self.assertEqual(CR.desde_config(cfg, self.raiz).clave, "con-bom")

    def test_clave_por_orden(self):
        cfg = {"tiempo": {"clave": " de-config "}}
        self.assertEqual(CR.desde_config(cfg, self.raiz).clave, "de-config")
        self.poner_fichero("  de-fichero\n")
        self.assertEqual(CR.desde_config(cfg, self.raiz).clave, "de-fichero")
        os.environ["OPENWEATHER_API_KEY"] = " de-entorno "
        self.assertEqual(CR.desde_config(cfg, self.raiz).clave, "de-entorno")

    def test_datos_de_la_ciudad(self):
        os.environ["OPENWEATHER_API_KEY"] = "k"
        ow = CR.desde_config({"ciudad": {"lat": -33.87, "lon": 151.21, "zona_horaria": "Australia/Sydney"},
                              "tiempo": {"cada_minutos": 20}}, self.raiz)
        self.assertEqual((ow.lat, ow.lon, ow.zona, ow.cada), (-33.87, 151.21, "Australia/Sydney", 1200))
        self.assertEqual(ow.ruta, os.path.join(self.raiz, "local", "openweather.json"))
        por_defecto = CR.desde_config({}, self.raiz)
        self.assertEqual((por_defecto.lat, por_defecto.lon, por_defecto.cada), (36.72, -4.42, 600))
        self.assertEqual(self.red.pedidas, [])


# ===================================================================== estado.py

PALETA = ["rojo", "verde", "azul", "amarillo"]


def _hormiga(nombre, x, y, esqueleto=False):
    return types.SimpleNamespace(nombre=nombre, x=x, y=y, esqueleto=esqueleto)


class EstadoBase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.raiz = tmp.name
        self.ruta = E.ruta(self.raiz)

    def escribir(self, contenido):
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        modo = "wb" if isinstance(contenido, bytes) else "w"
        with open(self.ruta, modo) as f:
            f.write(contenido if isinstance(contenido, (str, bytes)) else json.dumps(contenido))

    def leer(self):
        with open(self.ruta) as f:
            return json.load(f)


class EstadoTest(EstadoBase):

    def test_ruta(self):
        self.assertEqual(self.ruta, os.path.join(self.raiz, "local", "estado.json"))

    def test_sin_fichero(self):
        e = E.Estado(self.raiz, "2024-01-01", 7)
        self.assertEqual((e.dias, e.acabadas, e.posiciones, e.colores, e.inicio), (0.0, {}, {}, {}, {}))
        self.assertEqual(e.clave, "2024-01-01-7")
        self.assertFalse(os.path.exists(os.path.join(self.raiz, "local")))   # leer no crea nada
        self.assertIsNone(E.ultimo(self.raiz))
        self.assertIsNone(E.de_verdad(self.raiz))

    def test_guardar_y_leer(self):
        e = E.Estado(self.raiz, "2024-01-01", 7)
        e.dias = 2.5
        self.assertTrue(e.acabar("0 Despensa", 12.7))
        self.assertEqual(e.color("Begoña", [], PALETA), "rojo")
        e.guardar([_hormiga("Begoña", 10, 20), _hormiga("Íñigo", 3.5, 4),
                   _hormiga("Pepe ☠", 1, 2, esqueleto=True)])
        self.assertEqual(os.listdir(os.path.dirname(self.ruta)), ["estado.json"])   # sin .tmp
        otra = E.Estado(self.raiz, "2024-01-01", 7)
        self.assertEqual(otra.dias, 2.5)
        self.assertEqual(otra.acabadas, {"0 Despensa": 12})
        self.assertEqual(otra.colores, {"Begoña": "rojo"})
        self.assertEqual(otra.posiciones, {"Begoña": [10, 20], "Íñigo": [3.5, 4]})   # sin el esqueleto
        self.assertEqual(E.ultimo(self.raiz), ("2024-01-01", 7))

    def test_guardar_sin_hormigas_conserva_las_posiciones(self):
        e = E.Estado(self.raiz, "2024-01-01", 7)
        e.guardar([_hormiga("Ana", 1, 2)])
        otra = E.Estado(self.raiz, "2024-01-01", 7)
        otra.dias = 1.0
        otra.guardar()
        self.assertEqual(E.Estado(self.raiz, "2024-01-01", 7).posiciones, {"Ana": [1, 2]})

    def test_fichero_corrupto(self):
        for contenido in ("", "{\"inicio\": {\"fund", "basura", b"\xff\xfe\x00\x81", "[]", "null", "42",
                          '{"hormigueros": []}', '{"hormigueros": {"2024-01-01-7": 5}}',
                          '{"colores": "rojo", "inicio": 3, "hormigueros": {"x": {"obras": []}}}',
                          '{"hormigueros": {"2024-01-01-7": {"obras": {"acabadas": 3}, "posiciones": "x"}}}'):
            with self.subTest(contenido=contenido):
                self.escribir(contenido)
                e = E.Estado(self.raiz, "2024-01-01", 7)
                self.assertEqual((e.dias, e.acabadas, e.posiciones), (0.0, {}, {}))
                self.assertIsInstance(e.colores, dict)
                self.assertIsInstance(e.inicio, dict)
                e.dias = 1.5
                e.color("Ana", [], PALETA)
                e.guardar([_hormiga("Ana", 4, 5)])
                datos = self.leer()               # se rehace bien
                self.assertEqual(datos["hormigueros"]["2024-01-01-7"]["obras"]["dias"], 1.5)
                self.assertEqual(datos["colores"]["Ana"], "rojo")
                self.assertEqual(E.ultimo(self.raiz), ("2024-01-01", 7))

    # con un estado.json que es JSON válido pero con "dias" que no es un número (null, texto...)
    # se empieza de cero (antes Estado() lanzaba TypeError o ValueError y no arrancaba)
    def test_dias_que_no_son_un_numero(self):
        for dias in (None, "muchos", [1], True, 10 ** 400):
            with self.subTest(dias=dias):
                self.escribir({"hormigueros": {"2024-01-01-7": {"obras": {"dias": dias}}}})
                e = E.Estado(self.raiz, "2024-01-01", 7)
                self.assertEqual(e.dias, 0.0)

    def test_nombres_con_cualquier_letra_en_utf8(self):
        # siempre en UTF-8, también en Windows: un nombre con letras que no tiene cp1252 no tumba
        # el hormiguero al guardar, y el fichero vale igual en otro ordenador
        e = E.Estado(self.raiz, "2024-01-01", 7)
        e.color("Łukasz Ωmega 😀", [], PALETA)
        e.guardar([_hormiga("Łukasz Ωmega 😀", 1, 2)])
        with open(self.ruta, encoding="utf-8") as f:
            self.assertIn("Łukasz Ωmega 😀", f.read())
        self.assertEqual(E.Estado(self.raiz, "2024-01-01", 7).posiciones, {"Łukasz Ωmega 😀": [1, 2]})

    def test_lo_guardado_con_otra_forma_no_cuenta(self):
        self.escribir({"colores": {"Ana": "rojo", "Luis": 3},
                       "hormigueros": {"2024-01-01-7": {"obras": {"dias": 1.5, "acabadas": {"0 A": 4, "1 B": "x"}},
                                                        "posiciones": {"Ana": [1, 2], "Luis": [1], "Eva": "x"}}}})
        e = E.Estado(self.raiz, "2024-01-01", 7)
        self.assertEqual((e.colores, e.acabadas, e.posiciones), ({"Ana": "rojo"}, {"0 A": 4}, {"Ana": [1, 2]}))

    def test_varios_hormigueros_sin_pisarse(self):
        a = E.Estado(self.raiz, "2024-01-01", 7)
        b = E.Estado(self.raiz, "2024-01-01", 8)       # abiertos a la vez, antes de guardar nada
        c = E.Estado(self.raiz, "2023-06-01", 7)
        a.dias = 1.0
        a.acabar("0 Despensa", 3)
        a.color("Ana", [], PALETA)
        a.guardar([_hormiga("Ana", 1, 1)])
        b.dias = 5.0
        b.color("Luis", ["rojo"], PALETA)
        b.guardar([_hormiga("Luis", 9, 9)])
        self.assertEqual(E.ultimo(self.raiz), ("2024-01-01", 8))
        c.guardar([_hormiga("Eva", 2, 2)])
        self.assertEqual(E.ultimo(self.raiz), ("2023-06-01", 7))
        a.guardar()
        self.assertEqual(E.ultimo(self.raiz), ("2024-01-01", 7))   # el último que guarda, al final

        a2, b2, c2 = (E.Estado(self.raiz, *k) for k in (("2024-01-01", 7), ("2024-01-01", 8), ("2023-06-01", 7)))
        self.assertEqual((a2.dias, a2.acabadas, a2.posiciones), (1.0, {"0 Despensa": 3}, {"Ana": [1, 1]}))
        self.assertEqual((b2.dias, b2.acabadas, b2.posiciones), (5.0, {}, {"Luis": [9, 9]}))
        self.assertEqual((c2.dias, c2.posiciones), (0.0, {"Eva": [2, 2]}))
        # los colores son de todos y no se pierden aunque cada uno no viera los del otro
        self.assertEqual(a2.colores, {"Ana": "rojo", "Luis": "verde"})
        self.assertEqual(set(self.leer()["hormigueros"]), {"2024-01-01-7", "2024-01-01-8", "2023-06-01-7"})

    def test_formato_antiguo(self):
        antiguo = {"inicio": {"fundacion": "2023-05-01", "semilla": 42}, "clave": "2023-05-01-42",
                   "colores": {"Ana": "azul"}, "posiciones": {"Ana": [3, 4]},
                   "obras": {"dias": 3.5, "acabadas": {"0 Despensa": 10}}}
        self.escribir(antiguo)
        self.assertEqual(E.ultimo(self.raiz), ("2023-05-01", 42))
        e = E.Estado(self.raiz, "2023-05-01", 42)
        self.assertEqual((e.dias, e.acabadas, e.posiciones, e.colores),
                         (3.5, {"0 Despensa": 10}, {"Ana": [3, 4]}, {"Ana": "azul"}))
        # otro hormiguero empieza de cero, pero comparte los colores
        otro = E.Estado(self.raiz, "2023-05-01", 43)
        self.assertEqual((otro.dias, otro.posiciones, otro.colores), (0.0, {}, {"Ana": "azul"}))
        otro.dias = 0.5
        otro.guardar()
        datos = self.leer()
        self.assertNotIn("clave", datos)                     # ya en el formato nuevo
        self.assertEqual(datos["inicio"], antiguo["inicio"])
        self.assertEqual(set(datos["hormigueros"]), {"2023-05-01-42", "2023-05-01-43"})
        self.assertEqual(E.Estado(self.raiz, "2023-05-01", 42).dias, 3.5)   # el antiguo sigue ahí
        self.assertEqual(E.ultimo(self.raiz), ("2023-05-01", 43))

    def test_formato_antiguo_con_claves_raras(self):
        casos = {"2023-05-01--5": ("2023-05-01", -5), "2023-05-01-abc": ("2023-05-01", "abc"),
                 "rara": None, "2023-05-01-": None}
        for clave, esperado in casos.items():
            with self.subTest(clave=clave):
                self.escribir({"clave": clave, "obras": {"dias": 1}})
                self.assertEqual(E.ultimo(self.raiz), esperado)

    def test_avanzar(self):
        e = E.Estado(self.raiz, "2024-01-01", 7)
        t = datetime.datetime(2024, 3, 1, 12, 0)
        e.avanzar(t)
        self.assertEqual(e.dias, 0.0)
        e.avanzar(t + datetime.timedelta(seconds=60))
        self.assertAlmostEqual(e.dias, 60 / 86400)
        e.avanzar(t + datetime.timedelta(seconds=360))       # 5 minutos justos: cuenta
        self.assertAlmostEqual(e.dias, 360 / 86400)
        e.avanzar(t + datetime.timedelta(hours=8))            # salto (suspensión): no cuenta
        self.assertAlmostEqual(e.dias, 360 / 86400)
        e.avanzar(t + datetime.timedelta(hours=7))            # hacia atrás: no cuenta
        self.assertAlmostEqual(e.dias, 360 / 86400)
        e.avanzar(t + datetime.timedelta(hours=7, seconds=30))
        self.assertAlmostEqual(e.dias, 390 / 86400)

    def test_acabar_solo_la_primera_vez(self):
        e = E.Estado(self.raiz, "2024-01-01", 7)
        self.assertTrue(e.acabar("1 Cuadra", 40.9))
        self.assertFalse(e.acabar("1 Cuadra", 55))
        self.assertEqual(e.acabadas, {"1 Cuadra": 40})

    def test_color(self):
        e = E.Estado(self.raiz, "2024-01-01", 7)
        self.assertEqual(e.color("Ana", ["rojo", "rojo", "verde"], PALETA), "azul")
        self.assertEqual(e.color("Luis", ["rojo", "verde", "azul", "amarillo"], PALETA), "rojo")
        self.assertEqual(e.color("Ana", [], PALETA), "azul")      # el de siempre

    def test_toca_guardar(self):
        reloj = [1000.0]
        with mock.patch.object(E, "time", types.SimpleNamespace(monotonic=lambda: reloj[0])):
            e = E.Estado(self.raiz, "2024-01-01", 7)
            reloj[0] += E.GUARDAR_CADA
            self.assertFalse(e.toca_guardar())
            reloj[0] += 1
            self.assertTrue(e.toca_guardar())
            e.guardar()
            self.assertFalse(e.toca_guardar())

    def test_no_poder_escribir_no_tumba(self):
        with open(os.path.join(self.raiz, "local"), "w") as f:   # "local" es un fichero
            f.write("estorbo")
        e = E.Estado(self.raiz, "2024-01-01", 7)
        e.guardar([_hormiga("Ana", 1, 2)])
        self.assertEqual(E.inicio(self.raiz, True, True, True, datetime.date(2024, 1, 1))[0], "2024-01-01")


class InicioTest(EstadoBase):

    def test_primer_arranque(self):
        fundacion, semilla = E.inicio(self.raiz, True, True, guardar=True, hoy=datetime.date(2024, 5, 1))
        self.assertEqual(fundacion, "2024-05-01")
        self.assertIsInstance(semilla, int)
        self.assertTrue(1 <= semilla < 100000)
        self.assertEqual(self.leer()["inicio"], {"fundacion": "2024-05-01", "semilla": semilla})
        # al reiniciar otro día no cambia nada
        self.assertEqual(E.inicio(self.raiz, True, True, guardar=True, hoy=datetime.date(2025, 2, 2)),
                         (fundacion, semilla))
        self.assertEqual(E.de_verdad(self.raiz), (fundacion, semilla))

    def test_sin_guardar_no_escribe(self):
        r = E.inicio(self.raiz, True, True, guardar=False, hoy=datetime.date(2024, 5, 1))
        self.assertEqual(r[0], "2024-05-01")
        self.assertFalse(os.path.exists(self.ruta))
        self.assertEqual(E.inicio(self.raiz, True, False, guardar=False, hoy=datetime.date(2024, 6, 1)),
                         ("2024-06-01", None))

    def test_solo_lo_que_falta(self):
        self.assertEqual(E.inicio(self.raiz, False, False, guardar=True, hoy=datetime.date(2024, 5, 1)),
                         (None, None))
        self.assertFalse(os.path.exists(self.ruta))
        fundacion, semilla = E.inicio(self.raiz, False, True, guardar=True, hoy=datetime.date(2024, 5, 1))
        self.assertIsNone(fundacion)
        self.assertEqual(self.leer()["inicio"], {"semilla": semilla})
        # más tarde falta también la fundación: se añade sin tocar la semilla
        self.assertEqual(E.inicio(self.raiz, True, True, guardar=True, hoy=datetime.date(2024, 9, 9)),
                         ("2024-09-09", semilla))

    def test_conserva_lo_demas(self):
        e = E.Estado(self.raiz, "2020-01-01", 3)
        e.color("Ana", [], PALETA)
        e.dias = 4.0
        e.guardar([_hormiga("Ana", 7, 8)])
        ini = E.inicio(self.raiz, True, True, guardar=True, hoy=datetime.date(2024, 5, 1))
        datos = self.leer()
        self.assertEqual(datos["colores"], {"Ana": "rojo"})
        self.assertEqual(datos["hormigueros"]["2020-01-01-3"]["obras"]["dias"], 4.0)
        # y un Estado abierto antes no borra el inicio al guardar
        e.guardar()
        self.assertEqual(self.leer()["inicio"], {"fundacion": ini[0], "semilla": ini[1]})

    def test_con_fichero_corrupto(self):
        self.escribir("{roto")
        self.assertEqual(E.inicio(self.raiz, True, False, guardar=True, hoy=datetime.date(2024, 5, 1)),
                         ("2024-05-01", None))
        self.assertEqual(self.leer(), {"inicio": {"fundacion": "2024-05-01"}})

    def test_de_verdad(self):
        a = E.Estado(self.raiz, "2022-02-02", 5)
        a.guardar()
        # sin inicio completo: el último hormiguero guardado
        self.assertEqual(E.de_verdad(self.raiz), ("2022-02-02", 5))
        E.inicio(self.raiz, True, False, guardar=True, hoy=datetime.date(2024, 5, 1))
        self.assertEqual(E.de_verdad(self.raiz), ("2022-02-02", 5))
        # con fundación y semilla del primer arranque, mandan esas (una prueba con otra semilla no las cambia)
        s = E.inicio(self.raiz, True, True, guardar=True, hoy=datetime.date(2024, 5, 1))[1]
        E.Estado(self.raiz, "2024-05-01", 77).guardar()
        self.assertEqual(E.de_verdad(self.raiz), ("2024-05-01", s))


if __name__ == "__main__":
    unittest.main()
