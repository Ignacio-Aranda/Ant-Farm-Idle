"""Pruebas de la carga de los ficheros (hormiga/app.py): config.toml, salas/*.toml,
tipos/*.toml, idos.toml y calendario.toml.

Lo que está mal escrito nunca tumba el hormiguero: se avisa y se usa el valor por
defecto. Todo se escribe en carpetas temporales: la raíz del repositorio (y su local/)
se cambia por una temporal y la hora de "ahora" es siempre la misma.

    SDL_VIDEODRIVER=dummy python3 -m unittest discover -s tests -v
"""

import datetime
import io
import json
import os
import shutil
import sys
import tempfile
import textwrap
import types
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from hormiga import app as A  # noqa: E402
from hormiga import estado as E  # noqa: E402
from hormiga import tiempo as T  # noqa: E402
from pixel import app as P  # noqa: E402

HOY = datetime.datetime(2026, 5, 4, 12, 0)     # el "ahora" de las pruebas
ENORME = "1" + "0" * 400                         # un entero de TOML con 400 cifras

# una sala con dos personas, para las reuniones
EQUIPO = """\
nombre = "Diseño"

[[miembro]]
nombre = "Ana"

[[miembro]]
nombre = "Elena"
"""


class Base(unittest.TestCase):
    """Una copia mínima de los ficheros en una carpeta temporal: config.toml con fundación y
    semilla, salas/ vacía, los tipos/ del repositorio, idos.toml y calendario.toml vacíos.
    Así carga sin ningún aviso y cada prueba cambia sólo lo que quiere probar."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hormiga-config-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.raiz = os.path.join(self.tmp, "raiz")     # hace de raíz del repositorio (y de su local/)
        self.datos = os.path.join(self.tmp, "datos")
        os.makedirs(self.raiz)
        os.makedirs(os.path.join(self.datos, "salas"))
        shutil.copytree(os.path.join(REPO, "tipos"), os.path.join(self.datos, "tipos"))
        self.config()
        self.escribir("idos.toml", "")
        self.escribir("calendario.toml", "")
        self.hoy = HOY
        for p in (mock.patch.object(A, "RAIZ", self.raiz),
                  mock.patch.object(T, "ahora", lambda zona=None: self.hoy)):
            p.start()
            self.addCleanup(p.stop)
        self.avisos = []

    # -------------------------------------------------------- ayudas

    def ruta(self, *partes):
        return os.path.join(self.datos, *partes)

    def escribir(self, rel, texto, base=None):
        ruta = os.path.join(base or self.datos, rel)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(texto))
        return ruta

    def config(self, general="", resto=""):
        """config.toml con fundación y semilla (así no se mira local/estado.json)."""
        self.escribir("config.toml", '[general]\nfundacion = "2026-01-01"\nsemilla = 7\n%s\n%s\n'
                      % (general, resto))

    def args(self, **cambios):
        a = types.SimpleNamespace(
            config=self.ruta("config.toml"), salas=self.ruta("salas"), tipos=self.ruta("tipos"),
            idos=self.ruta("idos.toml"), calendario=self.ruta("calendario.toml"),
            demo=False, fecha=None, hora=None, dias=None, acelerar=1.0, captura=None, medir=False,
            sin_estado=True)
        vars(a).update(cambios)
        return a

    def cargar(self, **cambios):
        self.avisos = []
        self.cfg, self.salas, self.idos, self.fiestas = A.cargar(self.args(**cambios), self.avisos)
        return self.cfg, self.salas, self.idos, self.fiestas

    def sala(self, clave):
        for s in self.salas:
            if s["clave"] == clave:
                return s
        self.fail("no se ha cargado la sala «%s»: %r" % (clave, [s["clave"] for s in self.salas]))

    def cargar_sala(self, texto, fichero="prueba.toml"):
        self.escribir("salas/" + fichero, texto)
        self.cargar()
        return self.sala(os.path.splitext(fichero)[0].lower())

    def reuniones(self, texto):
        """Las reuniones de una sala de reuniones con este texto (y Diseño, con Ana y Elena)."""
        self.escribir("salas/diseno.toml", EQUIPO)
        return self.cargar_sala('nombre = "Reuniones"\ntipo = "reuniones"\n\n' + texto,
                                "reuniones.toml")["reuniones"]

    def estado_inicial(self, fundacion, semilla):
        """local/estado.json (en la raíz temporal) con la fundación y la semilla del primer arranque."""
        r = E.ruta(self.raiz)
        os.makedirs(os.path.dirname(r))
        with open(r, "w", encoding="utf-8") as f:
            json.dump({"inicio": {"fundacion": fundacion, "semilla": semilla}}, f)

    def hay_estado(self):
        return os.path.exists(E.ruta(self.raiz))

    def assertAviso(self, trozo):
        self.assertTrue(any(trozo in a for a in self.avisos),
                        "falta el aviso «%s» en %r" % (trozo, self.avisos))

    def assertSinAvisos(self):
        self.assertEqual(self.avisos, [])


# ===================================================================== ejemplos

class FicherosDeEjemplo(Base):
    """Los ficheros del repositorio (los que ve quien lo descarga) cargan sin ningún aviso."""

    def args_del_repo(self, **cambios):
        r = {"config": "config.toml", "salas": "salas", "tipos": "tipos", "idos": "idos.toml",
             "calendario": "calendario.toml"}
        r = {k: os.path.join(REPO, v) for k, v in r.items()}
        r.update(cambios)
        return self.args(**r)

    def test_cargan_sin_avisos(self):
        avisos = []
        cfg, salas, idos, fiestas = A.cargar(self.args_del_repo(), avisos)
        self.assertEqual(avisos, [])
        self.assertTrue(salas and idos and fiestas and cfg["tipos"])

    def test_sin_avisos_tampoco_de_los_muebles(self):
        avisos = []
        P.cargar(A, self.args_del_repo(), avisos)
        self.assertEqual(avisos, [])

    def test_calendario_de_andalucia_sin_avisos(self):
        avisos = []
        ruta = os.path.join(REPO, "ejemplos", "calendario-andalucia.toml")
        _cfg, _salas, _idos, fiestas = A.cargar(self.args_del_repo(calendario=ruta), avisos)
        self.assertEqual(avisos, [])
        self.assertTrue(fiestas)

    def test_lo_que_traen(self):
        avisos = []
        cfg, salas, idos, fiestas = A.cargar(self.args_del_repo(), avisos)
        datetime.date.fromisoformat(cfg["general"]["fundacion"])
        self.assertIn("semilla", cfg["general"])
        claves = {s["clave"] for s in salas}
        gente = {m["nombre"] for s in salas for m in s["miembros"]}
        for s in salas:
            self.assertIn(s["tipo"], cfg["tipos"], s["fichero"])
            for r in s["reuniones"]:   # cada reunión convoca a todos, a una sala o a gente que está
                q = r["quien"]
                self.assertTrue(q == "todos" or q in claves or (isinstance(q, list) and set(q) <= gente), q)
        for n in cfg.get("nido", {}).get("obras", []):
            self.assertIn(n.lower(), cfg["tipos"])
        self.assertNotIn("leeme", cfg["tipos"])   # tipos/LEEME.md no es un tipo

    def test_no_escriben_estado(self):
        A.cargar(self.args_del_repo(), [])
        self.assertFalse(self.hay_estado())


# ================================================================= config.toml

class ConfigToml(Base):

    def test_minima_sin_avisos(self):
        cfg, salas, idos, fiestas = self.cargar()
        self.assertSinAvisos()
        self.assertEqual(cfg["general"]["fundacion"], "2026-01-01")
        self.assertEqual(cfg["general"]["semilla"], 7)
        self.assertEqual((salas, idos, fiestas), ([], [], []))

    def test_toml_roto(self):
        self.escribir("config.toml", '[general]\nfundacion = "2026-01-01\nsemilla = 7\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertTrue(any(a.startswith("config: ") for a in self.avisos), self.avisos)
        datetime.date.fromisoformat(cfg["general"]["fundacion"])   # una fecha que vale
        self.assertIn("semilla", cfg["general"])

    def test_toml_roto_sigue_con_el_hormiguero_de_verdad(self):
        # una errata en config.toml no cambia de hormiguero: el del primer arranque
        self.estado_inicial("2025-06-01", 99)
        self.escribir("config.toml", "[general\n")
        cfg, _s, _i, _f = self.cargar(sin_estado=False)
        self.assertEqual(cfg["general"]["fundacion"], "2025-06-01")
        self.assertEqual(cfg["general"]["semilla"], 99)

    def test_toml_roto_no_escribe_estado(self):
        self.escribir("config.toml", "[general\n")
        self.cargar(sin_estado=False)   # con el reloj de verdad
        self.assertFalse(self.hay_estado())

    def test_fundacion_mal_escrita(self):
        for valor in ('"2026-02-30"', '"ayer"', '"9999-12-31"', '"1800-01-01"', '""', "true",
                      "[2026, 1, 1]", "07:30:00"):
            with self.subTest(fundacion=valor):
                self.escribir("config.toml", "[general]\nfundacion = %s\nsemilla = 7\n" % valor)
                cfg, _s, _i, _f = self.cargar()
                self.assertAviso("config: fundacion mal escrita")
                self.assertAviso("usa AAAA-MM-DD (de 1900 a 2999)")
                self.assertEqual(cfg["general"]["fundacion"], "2026-01-01")   # la de por defecto
                self.assertEqual(cfg["general"]["semilla"], 7)

    def test_fecha_imposible_sin_comillas(self):
        # fundacion = 2026-02-30 sin comillas ni siquiera es TOML: no se puede leer config.toml
        self.estado_inicial("2025-06-01", 99)
        self.escribir("config.toml", "[general]\nfundacion = 2026-02-30\nsemilla = 7\n")
        cfg, _s, _i, _f = self.cargar()
        self.assertEqual(len(self.avisos), 1, self.avisos)
        self.assertTrue(self.avisos[0].startswith("config: "), self.avisos)
        self.assertEqual(cfg["general"]["fundacion"], "2025-06-01")   # sigue el de verdad
        self.assertEqual(cfg["general"]["semilla"], 99)

    def test_fundacion_mal_escrita_usa_la_del_primer_arranque(self):
        self.estado_inicial("2025-06-01", 99)
        self.escribir("config.toml", '[general]\nfundacion = "2026-02-30"\nsemilla = 7\n')
        cfg, _s, _i, _f = self.cargar(sin_estado=False)
        self.assertAviso("config: fundacion mal escrita (2026-02-30)")
        self.assertEqual(cfg["general"]["fundacion"], "2025-06-01")
        self.assertEqual(cfg["general"]["semilla"], 7)   # la semilla sí estaba bien

    def test_fundacion_como_fecha_de_toml(self):
        for valor in ("2026-03-01", "2026-03-01T08:30:00", '" 2026-03-01 "'):
            with self.subTest(fundacion=valor):
                self.escribir("config.toml", "[general]\nfundacion = %s\nsemilla = 7\n" % valor)
                cfg, _s, _i, _f = self.cargar()
                self.assertSinAvisos()
                self.assertEqual(cfg["general"]["fundacion"], "2026-03-01")

    def test_sin_fundacion_ni_semilla(self):
        # las del primer arranque: hoy y una al azar; sin el reloj de verdad no se guardan
        self.escribir("config.toml", "[general]\n")
        cfg, _s, _i, _f = self.cargar()
        self.assertSinAvisos()
        self.assertEqual(cfg["general"]["fundacion"], "2026-05-04")
        self.assertIsInstance(cfg["general"]["semilla"], int)
        self.assertFalse(self.hay_estado())

    def test_sin_fundacion_con_el_reloj_de_verdad_se_guarda(self):
        self.escribir("config.toml", "[general]\n")
        cfg, _s, _i, _f = self.cargar(sin_estado=False)
        self.assertTrue(self.hay_estado())
        semilla = cfg["general"]["semilla"]
        self.hoy = datetime.datetime(2026, 9, 1, 12, 0)   # otro día: sigue siendo el mismo hormiguero
        cfg, _s, _i, _f = self.cargar(sin_estado=False)
        self.assertSinAvisos()
        self.assertEqual(cfg["general"]["fundacion"], "2026-05-04")
        self.assertEqual(cfg["general"]["semilla"], semilla)

    def test_guarda_estado_solo_con_el_reloj_de_verdad(self):
        self.assertTrue(A.guarda_estado(self.args(sin_estado=False)))
        for cambio in ({"sin_estado": True}, {"demo": True}, {"fecha": "2026-01-01"}, {"hora": "10:00"},
                       {"dias": 0.0}, {"acelerar": 60.0}, {"captura": "x.png"}, {"medir": True}):
            with self.subTest(**cambio):
                self.assertFalse(A.guarda_estado(self.args(**dict({"sin_estado": False}, **cambio))))

    def test_numeros_escritos_como_texto(self):
        self.config('fps_pixel = "25,5"\ntexto_aumento = 1.9',
                    '[ciudad]\nlat = "-33,9"\nlon = " 18.4 "\n[tiempo]\ncada_minutos = "5"\n'
                    '[nido]\nentrada = 30.0\n[paisaje]\ncementerio = "80"\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertSinAvisos()
        self.assertEqual(cfg["general"]["fps_pixel"], 25.5)
        self.assertEqual(cfg["general"]["texto_aumento"], 1)
        self.assertEqual(cfg["ciudad"]["lat"], -33.9)
        self.assertEqual(cfg["ciudad"]["lon"], 18.4)
        self.assertEqual(cfg["tiempo"]["cada_minutos"], 5.0)
        self.assertEqual(cfg["nido"]["entrada"], 30)
        self.assertIsInstance(cfg["nido"]["entrada"], int)
        self.assertEqual(cfg["paisaje"]["cementerio"], 80.0)

    def test_numeros_mal_escritos(self):
        for seccion, clave, defecto, _entero in A.NUMEROS:
            for valor in ('"veinte"', "true", "nan", "inf", "-inf", "[1, 2]", '""', "{ a = 1 }"):
                with self.subTest(seccion=seccion, clave=clave, valor=valor):
                    linea = "%s = %s" % (clave, valor)
                    if seccion == "general":
                        self.config(linea)
                    else:
                        self.config(resto="[%s]\n%s\n" % (seccion, linea))
                    cfg, _s, _i, _f = self.cargar()
                    self.assertEqual(self.avisos, ["config: [%s] %s debe ser un número (puse %s)"
                                                   % (seccion, clave, defecto)])
                    self.assertEqual(cfg[seccion][clave], defecto)

    def test_numero_enorme(self):
        # un entero de TOML con muchísimas cifras no se puede pasar a float (OverflowError):
        # se avisa como cualquier número mal escrito
        self.config(resto="[nido]\nentrada = %s\n" % ENORME)
        cfg, _s, _i, _f = self.cargar()
        self.assertEqual(self.avisos, ["config: [nido] entrada debe ser un número (puse 20)"])
        self.assertEqual(cfg["nido"]["entrada"], 20)

    def test_numeros_fuera_de_rango(self):
        for seccion, clave, valor, puesto in (("general", "fps_pixel", "0", 1), ("general", "fps_pixel", "500", 60),
                                              ("general", "texto_aumento", "-20", -3),
                                              ("general", "texto_aumento", "500", 8),
                                              ("ciudad", "lat", "139", 90), ("ciudad", "lon", "-200", -180)):
            with self.subTest(clave=clave, valor=valor):
                linea = "%s = %s" % (clave, valor)
                if seccion == "general":
                    self.config(linea)
                else:
                    self.config(resto="[%s]\n%s\n" % (seccion, linea))
                cfg, _s, _i, _f = self.cargar()
                self.assertEqual(len(self.avisos), 1, self.avisos)
                self.assertTrue(self.avisos[0].startswith("config: [%s] %s va de " % (seccion, clave)), self.avisos)
                self.assertEqual(cfg[seccion][clave], puesto)

    def test_si_o_no(self):
        for valor, esperado in (("true", True), ("false", False), ('"false"', False), ('"No"', False),
                                ('"sí"', True), ('"TRUE"', True)):
            with self.subTest(valor=valor):
                self.config("texto_suavizado = %s" % valor, "[halloween]\nesqueletos = %s\n" % valor)
                cfg, _s, _i, _f = self.cargar()
                self.assertSinAvisos()
                self.assertIs(cfg["general"]["texto_suavizado"], esperado)
                self.assertIs(cfg["halloween"]["esqueletos"], esperado)
        for valor in ('"quizás"', "1", "0", "[true]"):
            with self.subTest(valor=valor):
                self.config(resto="[halloween]\nesqueletos = %s\n" % valor)
                cfg, _s, _i, _f = self.cargar()
                self.assertEqual(self.avisos, ["config: [halloween] esqueletos debe ser true o false (puse false)"])
                self.assertIs(cfg["halloween"]["esqueletos"], False)

    def test_opciones_con_errata(self):
        self.config(resto='[tiempo]\nfuente = "openwether"\n[nido]\ncavar = "encendida"\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertEqual(self.avisos, [
            "config: [tiempo] fuente «openwether» no existe (openweather o estadistico; puse openweather)",
            "config: [nido] cavar «encendida» no existe (encendido o fecha; puse encendido)"])
        self.assertEqual((cfg["tiempo"]["fuente"], cfg["nido"]["cavar"]), ("openweather", "encendido"))
        self.config(resto='[tiempo]\nfuente = " Estadístico "\n[nido]\ncavar = "FECHA"\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertSinAvisos()
        self.assertEqual((cfg["tiempo"]["fuente"], cfg["nido"]["cavar"]), ("estadistico", "fecha"))

    def test_horario(self):
        self.config(resto='[horario]\ndesayuno = "10:00-10:30"\ncomida = "25:00-26:00"\njornada = "18:00-09:00"\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertEqual(len(self.avisos), 2, self.avisos)
        self.assertTrue(self.avisos[0].startswith("config: [horario] comida mal escrito (25:00-26:00)"))
        self.assertTrue(self.avisos[1].startswith("config: [horario] jornada mal escrito (18:00-09:00)"))
        self.assertEqual(cfg["horario"], {"desayuno": "10:00-10:30", "comida": "13:30-15:30",
                                          "jornada": "09:00-18:00"})

    def test_obras_con_tildes_mayusculas_o_espacios(self):
        self.escribir("tipos/sala de juegos.toml", 'funcion = "otra"\n')
        self.config(resto='[nido]\nobras = ["Almacén", " MUSEO ", "Sala de juegos", "sala_de_juegos"]\n')
        self.cargar()
        self.assertSinAvisos()

    def test_errores_de_toml_en_espanol(self):
        self.escribir("config.toml", '[general]\nfundacion = "2026-01-01"\nsemilla = 7\n[nido]\n[nido]\n')
        self.cargar()
        self.assertEqual(self.avisos, ["config: no se puede leer, en la línea 5: la sección [nido] está repetida "
                                       "(escríbela una sola vez)"])

    def test_seccion_que_no_es_tabla(self):
        self.escribir("config.toml", 'ciudad = "Málaga"\nnido = 3\n\n'
                                     '[general]\nfundacion = "2026-01-01"\nsemilla = 7\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertAviso("config: ciudad tiene que ser una sección, [ciudad]")
        self.assertAviso("config: nido tiene que ser una sección, [nido]")
        self.assertNotIsInstance(cfg.get("ciudad", {}), str)
        self.assertEqual(cfg["general"]["fundacion"], "2026-01-01")

    def test_general_que_no_es_tabla(self):
        self.escribir("config.toml", "general = 5\n")
        cfg, _s, _i, _f = self.cargar(sin_estado=False)
        self.assertAviso("config: general tiene que ser una sección, [general]")
        datetime.date.fromisoformat(cfg["general"]["fundacion"])
        self.assertIn("semilla", cfg["general"])
        self.assertFalse(self.hay_estado())   # como si no se hubiera podido leer: no se apunta nada

    def test_claves_desconocidas_no_molestan(self):
        self.config("color_favorito = \"azul\"", "[cosas]\nuna = 1\n")
        self.cargar()
        self.assertSinAvisos()

    def test_obras_que_no_son_lista(self):
        self.config(resto='[nido]\nobras = "despensa"\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertAviso("config: [nido] obras debe ser una lista")
        self.assertNotIn("obras", cfg["nido"])   # las de siempre

    def test_obras_con_valores_que_no_son_texto(self):
        self.config(resto='[nido]\nobras = ["despensa", 3, "", "museo", true]\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertEqual(self.avisos, ["config: [nido] obras: cada obra es un nombre entre comillas"])
        self.assertEqual(cfg["nido"]["obras"], ["despensa", "museo"])

    def test_obra_sin_tipo(self):
        self.config(resto='[nido]\nobras = ["despensa", "piscina"]\n')
        self.cargar()
        self.assertEqual(self.avisos, ["config: [nido] la obra «piscina» no tiene tipo en tipos/ "
                                       "(será una sala vacía)"])

    def test_obras_con_mayusculas_y_espacios(self):
        self.config(resto='[nido]\nobras = ["Museo", " despensa "]\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertSinAvisos()
        self.assertEqual(cfg["nido"]["obras"], ["Museo", "despensa"])

    def test_sin_obras(self):
        self.config(resto="[nido]\nobras = []\n")
        cfg, _s, _i, _f = self.cargar()
        self.assertSinAvisos()
        self.assertEqual(cfg["nido"]["obras"], [])

    @unittest.skipIf(T.zona_horaria("Europe/Madrid") is None, "no hay base de zonas horarias")
    def test_zona_horaria_buena(self):
        self.config(resto='[ciudad]\nzona_horaria = " Europe/Madrid "\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertSinAvisos()
        self.assertEqual(cfg["ciudad"]["zona_horaria"], "Europe/Madrid")

    def test_zona_horaria_que_no_existe(self):
        for valor in ('"Marte/Olympus"', "5", '"../../etc/passwd"'):
            with self.subTest(zona_horaria=valor):
                self.config(resto="[ciudad]\nzona_horaria = %s\n" % valor)
                cfg, _s, _i, _f = self.cargar()
                self.assertEqual(len(self.avisos), 1, self.avisos)
                self.assertAviso("config: [ciudad] zona_horaria «")
                self.assertAviso("no existe")
                self.assertNotIn("zona_horaria", cfg["ciudad"])

    def test_zona_horaria_vacia(self):
        self.config(resto='[ciudad]\nzona_horaria = ""\n')
        cfg, _s, _i, _f = self.cargar()
        self.assertSinAvisos()
        self.assertNotIn("zona_horaria", cfg["ciudad"])


# ======================================================= rutas que no existen

class Rutas(Base):

    OPCIONES = (("config", "-c"), ("salas", "--salas"), ("tipos", "--tipos"), ("idos", "--idos"),
                ("calendario", "--calendario"))

    def test_cada_opcion_que_no_existe_avisa(self):
        for campo, opcion in self.OPCIONES:
            with self.subTest(opcion=opcion):
                ruta = os.path.join(self.tmp, "no-existe", campo)
                self.cargar(**{campo: ruta})
                self.assertAviso("%s: no encuentro %s" % (opcion, ruta))

    def test_tipos_que_no_existe_avisa_tambien_de_las_obras(self):
        cfg, _s, _i, _f = self.cargar(tipos=os.path.join(self.tmp, "no-existe"))
        self.assertEqual(cfg["tipos"], {})
        self.assertAviso("config: [nido] la obra «despensa» no tiene tipo en tipos/")

    def test_config_que_no_existe_sigue_con_el_hormiguero_de_verdad(self):
        self.estado_inicial("2025-06-01", 99)
        cfg, _s, _i, _f = self.cargar(config=os.path.join(self.tmp, "no-existe.toml"), sin_estado=False)
        self.assertEqual(cfg["general"]["fundacion"], "2025-06-01")
        self.assertEqual(cfg["general"]["semilla"], 99)

    def test_los_de_la_raiz_que_faltan_no_avisan(self):
        # sin el fichero de ejemplo en su sitio, no es un error: se usa lo de por defecto
        defectos = {"config": "config.toml", "salas": "salas", "tipos": "tipos", "idos": "idos.toml",
                    "calendario": "calendario.toml"}
        for campo, _opcion in self.OPCIONES:
            with self.subTest(campo=campo):
                self.cargar(**{campo: os.path.join(self.raiz, defectos[campo])})
                self.assertFalse(any("no encuentro" in a for a in self.avisos), self.avisos)


# ================================================================== salas/*.toml

class Salas(Base):

    def test_sala_bien_escrita(self):
        s = self.cargar_sala("""\
            nombre = "  Desarrollo  "
            color = " cian "
            planta = 3
            x = 40
            ancho = 36
            tipo = "Trabajo"
            jefe = true

            [[miembro]]
            nombre = " Ana "
            cumple = "14-03"
            color = "naranja"
            alta = "2026-03-01"

            [[mueble]]
            pieza = "planta"
            sitio = "derecha"
            """)
        self.assertSinAvisos()
        self.assertEqual(s["clave"], "prueba")
        self.assertEqual(s["fichero"], "salas/prueba.toml")
        self.assertEqual(s["nombre"], "Desarrollo")
        self.assertEqual(s["color"], "cian")
        self.assertEqual((s["planta"], s["x"], s["ancho"]), (3, 40, 36))
        self.assertEqual((s["tipo"], s["funcion"]), ("trabajo", "trabajo"))
        self.assertIs(s["jefe"], True)
        self.assertEqual(s["miembros"], [{"nombre": "Ana", "cumple": "14-03", "color": "naranja",
                                          "alta": "2026-03-01"}])
        self.assertEqual(s["muebles"], [{"pieza": "planta", "sitio": "derecha"}])

    def test_sala_vacia_va_con_lo_de_por_defecto(self):
        s = self.cargar_sala("")
        self.assertSinAvisos()
        self.assertEqual(s["nombre"], "prueba")    # el del fichero
        self.assertEqual(s["color"], "blanco")
        self.assertEqual((s["planta"], s["x"], s["ancho"]), (2, None, 32))
        self.assertEqual((s["tipo"], s["funcion"]), ("trabajo", "trabajo"))
        self.assertIs(s["jefe"], False)
        self.assertEqual((s["miembros"], s["reuniones"], s["muebles"]), ([], [], []))

    def test_clave_del_fichero_en_minusculas(self):
        s = self.cargar_sala("", "Mi Sala.toml")
        self.assertEqual(s["clave"], "mi sala")
        self.assertEqual(s["nombre"], "Mi Sala")

    def test_toml_roto_no_tumba_las_demas(self):
        self.escribir("salas/buena.toml", 'nombre = "Buena"\n')
        self.escribir("salas/rota.toml", 'nombre = "Rota\n')
        self.cargar()
        self.assertEqual([s["clave"] for s in self.salas], ["buena"])
        self.assertEqual(len(self.avisos), 1, self.avisos)
        self.assertTrue(self.avisos[0].startswith("salas/rota.toml: "), self.avisos)

    def test_fichero_en_ansi_o_con_bom(self):
        # como los guarda a veces el Bloc de notas de Windows: también se entienden
        for contenido in (b'nombre = "Caf\xe9"\n', b'\xef\xbb\xbfnombre = "Caf\xc3\xa9"\n'):
            with self.subTest(contenido=contenido):
                with open(self.ruta("salas", "rara.toml"), "wb") as f:
                    f.write(contenido)
                self.cargar()
                self.assertSinAvisos()
                self.assertEqual(self.sala("rara")["nombre"], "Café")

    def test_carpeta_con_nombre_de_toml(self):
        os.makedirs(self.ruta("salas", "carpeta.toml"))
        self.cargar()
        self.assertEqual(self.salas, [])
        self.assertAviso("salas/carpeta.toml: ")

    def test_ignora_ocultos_y_lo_que_no_es_toml(self):
        for n in (".oculta.toml", "notas.txt", "buena.toml.swp", "buena.toml~", ".#buena.toml"):
            self.escribir("salas/" + n, "esto no es TOML [[[")
        self.escribir("salas/buena.toml", "")
        self.cargar()
        self.assertSinAvisos()
        self.assertEqual([s["clave"] for s in self.salas], ["buena"])

    def test_tipo_que_no_existe(self):
        for valor, tipo in (('"cocina"', "cocina"), ("5", "5")):
            with self.subTest(tipo=valor):
                s = self.cargar_sala("tipo = %s\n" % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: no existe el tipo «%s» (en tipos/)" % tipo])
                self.assertEqual(s["funcion"], "trabajo")
        # con espacios, mayúsculas o tildes de más sí se encuentra
        for valor in ('"trabajo "', '"Reuniones"', '"Almacén"'):
            with self.subTest(tipo=valor):
                s = self.cargar_sala("tipo = %s\n" % valor)
                self.assertSinAvisos()
                self.assertEqual(s["tipo"], valor.strip('"').strip().lower().replace("é", "e"))

    def test_tipo_da_la_funcion(self):
        s = self.cargar_sala('tipo = "Comedor"\n')
        self.assertSinAvisos()
        self.assertEqual((s["tipo"], s["funcion"]), ("comedor", "comedor"))

    def test_colores_buenos(self):
        for valor, color in (('"cian"', "cian"), ('" Rojo "', "Rojo"), ('"#0f0"', "#0f0"),
                             ('"#00FF88"', "#00FF88"), ("200", 200), ('"200"', "200"),
                             ('"magenta_brillante"', "magenta_brillante"),
                             ('"azul brillante"', "azul brillante"), ('"c"', "c")):
            with self.subTest(color=valor):
                s = self.cargar_sala("color = %s\n" % valor)
                self.assertSinAvisos()
                self.assertEqual(s["color"], color)

    def test_colores_malos(self):
        for valor, texto in (('"#GG0000"', "#GG0000"), ('"#12345"', "#12345"), ('"#"', "#"),
                             ('"verde_fosforito"', "verde_fosforito"), ("256", "256"), ("-1", "-1"),
                             ("true", "True"), ("[1, 2]", "[1, 2]"), ("1.5", "1.5")):
            with self.subTest(color=valor):
                s = self.cargar_sala("color = %s\n" % valor)
                self.assertEqual(self.avisos,
                                 ["salas/prueba.toml: no existe el color «%s» (puse blanco)" % texto])
                self.assertEqual(s["color"], "blanco")

    def test_planta(self):
        for valor, planta in (("1", 1), ("4", 4), ('"3"', 3), ("2.9", 2), ('" 3,0 "', 3)):
            with self.subTest(planta=valor):
                s = self.cargar_sala("planta = %s\n" % valor)
                self.assertSinAvisos()
                self.assertEqual(s["planta"], planta)

    def test_planta_fuera_de_rango(self):
        for valor, planta in (("0", 1), ("-3", 1), ("5", 4), ("99", 4)):
            with self.subTest(planta=valor):
                s = self.cargar_sala("planta = %s\n" % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: la planta va de 1 a 4 (puse %d)" % planta])
                self.assertEqual(s["planta"], planta)

    def test_planta_que_no_es_numero(self):
        for valor in ('"dos"', "true", "[2]", "nan"):
            with self.subTest(planta=valor):
                s = self.cargar_sala("planta = %s\n" % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: planta debe ser un número (puse 2)"])
                self.assertEqual(s["planta"], 2)

    def test_nivel_vale_como_planta(self):
        s = self.cargar_sala("nivel = 3\n")
        self.assertSinAvisos()
        self.assertEqual(s["planta"], 3)
        s = self.cargar_sala("planta = 1\nnivel = 3\n")   # si están las dos, manda planta
        self.assertEqual(s["planta"], 1)

    def test_ancho(self):
        s = self.cargar_sala('ancho = "40"\n')
        self.assertSinAvisos()
        self.assertEqual(s["ancho"], 40)
        for valor in ("5", "-100", "0"):
            with self.subTest(ancho=valor):
                s = self.cargar_sala("ancho = %s\n" % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: el ancho mínimo es 14 (puse 14)"])
                self.assertEqual(s["ancho"], 14)
        s = self.cargar_sala('ancho = "ancho"\n')
        self.assertEqual(self.avisos, ["salas/prueba.toml: ancho debe ser un número (puse 32)"])
        self.assertEqual(s["ancho"], 32)

    def test_x(self):
        for valor, x in (("40", 40), ('"12,5"', 12), ("7.9", 7)):
            with self.subTest(x=valor):
                s = self.cargar_sala("x = %s\n" % valor)
                self.assertSinAvisos()
                self.assertEqual(s["x"], x)
        for valor in ('"abc"', '""', "true", "inf"):
            with self.subTest(x=valor):
                s = self.cargar_sala("x = %s\n" % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: x debe ser un número (no lo tengo en cuenta)"])
                self.assertIsNone(s["x"])

    def test_numero_enorme(self):
        # un entero de TOML con muchísimas cifras (ancho, planta, x o los minutos de una
        # reunión) se avisa como cualquier número mal escrito
        s = self.cargar_sala("ancho = %s\n" % ENORME)
        self.assertEqual(self.avisos, ["salas/prueba.toml: ancho debe ser un número (puse 32)"])
        self.assertEqual(s["ancho"], 32)

    def test_nombre(self):
        for valor, nombre in (('"  Sala  "', "Sala"), ("5", "5"), ("2.5", "2.5")):
            with self.subTest(nombre=valor):
                s = self.cargar_sala("nombre = %s\n" % valor)
                self.assertSinAvisos()
                self.assertEqual(s["nombre"], nombre)
        for valor in ('""', '"   "', "true", '["a"]', "{ a = 1 }"):
            with self.subTest(nombre=valor):
                s = self.cargar_sala("nombre = %s\n" % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: nombre mal escrito (puse «prueba»)"])
                self.assertEqual(s["nombre"], "prueba")

    def test_jefe_escrito_como_texto(self):
        # jefe = "false" (o "no"), con comillas, es false; antes contaba como true sin avisar
        for valor, jefe in (('"false"', False), ('"no"', False), ('"true"', True), ('"Sí"', True)):
            with self.subTest(jefe=valor):
                s = self.cargar_sala("jefe = %s\n" % valor)
                self.assertSinAvisos()
                self.assertIs(s["jefe"], jefe)
        for valor in ('"quizás"', "1", "[true]"):
            with self.subTest(jefe=valor):
                s = self.cargar_sala("jefe = %s\n" % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: jefe debe ser true o false (puse false)"])
                self.assertIs(s["jefe"], False)

    def test_claves_de_la_sala_dentro_de_un_bloque(self):
        # escritas debajo de un [[miembro]] son suyas (así lo lee TOML): se avisa
        s = self.cargar_sala('[[miembro]]\nnombre = "Ana"\njefe = true\nmiembro = ["Nuria"]\n')
        self.assertEqual(self.avisos, [
            "salas/prueba.toml: «jefe» está dentro de un [[miembro]] (Ana) y la sala no lo ve; ponlo arriba, "
            "antes del primer [[...]]",
            "salas/prueba.toml: «miembro» está dentro de un [[miembro]] (Ana) y la sala no lo ve; ponlo arriba, "
            "antes del primer [[...]]"])
        self.assertIs(s["jefe"], False)

    def test_miembros_como_lista_de_nombres(self):
        s = self.cargar_sala('miembro = ["Ana", " Luis ", ""]\n')
        self.assertEqual([m["nombre"] for m in s["miembros"]], ["Ana", "Luis"])
        self.assertEqual(self.avisos, ["salas/prueba.toml: miembro mal escrito (), usa [[miembro]]"])

    def test_miembro_como_texto_suelto(self):
        s = self.cargar_sala('miembro = "Ana"\n')
        self.assertSinAvisos()
        self.assertEqual(s["miembros"], [{"nombre": "Ana"}])

    def test_miembro_como_tabla_simple(self):
        # [miembro] en vez de [[miembro]]: cuenta como uno
        s = self.cargar_sala('[miembro]\nnombre = "Ana"\ncumple = "14-03"\n')
        self.assertSinAvisos()
        self.assertEqual(s["miembros"], [{"nombre": "Ana", "cumple": "14-03"}])

    def test_miembro_mal_escrito(self):
        s = self.cargar_sala('miembro = [1, true, "Ana"]\n')
        self.assertEqual(self.avisos, ["salas/prueba.toml: miembro mal escrito (1), usa [[miembro]]",
                                       "salas/prueba.toml: miembro mal escrito (True), usa [[miembro]]"])
        self.assertEqual(s["miembros"], [{"nombre": "Ana"}])

    def test_miembro_sin_nombre(self):
        s = self.cargar_sala('[[miembro]]\ncumple = "14-03"\n\n[[miembro]]\nnombre = "  "\n\n'
                             '[[miembro]]\nnombre = "Ana"\n')
        self.assertEqual(self.avisos, ["salas/prueba.toml: hay un [[miembro]] sin nombre"] * 2)
        self.assertEqual([m["nombre"] for m in s["miembros"]], ["Ana"])

    def test_color_de_miembro(self):
        s = self.cargar_sala('[[miembro]]\nnombre = "Ana"\ncolor = " lima "\n')
        self.assertSinAvisos()
        self.assertEqual(s["miembros"][0]["color"], "lima")
        for valor, texto in (('"#GG0000"', "#GG0000"), ("300", "300"), ('"chillón"', "chillón")):
            with self.subTest(color=valor):
                s = self.cargar_sala('[[miembro]]\nnombre = "Ana"\ncolor = %s\n' % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: Ana: no existe el color «%s»" % texto])
                self.assertNotIn("color", s["miembros"][0])

    def test_cumples_buenos(self):
        for valor in ('"14-03"', '"14/03"', '"14-03-1990"', '"1990-03-14"', '"29-02"', '"03-25"',
                      "1990-03-14"):
            with self.subTest(cumple=valor):
                s = self.cargar_sala('[[miembro]]\nnombre = "Ana"\ncumple = %s\n' % valor)
                self.assertSinAvisos()
                self.assertIn("cumple", s["miembros"][0])

    def test_cumples_imposibles(self):
        for valor, texto in (('"31-02"', "31-02"), ('"30-02"', "30-02"), ('"99-99"', "99-99"),
                             ('"0-5"', "0-5"), ('"mañana"', "mañana"), ("1403", "1403"),
                             ("true", "True"), ('"14-03-1990-1"', "14-03-1990-1"), ('"  "', "  "),
                             ('"14-%s"' % ENORME, "14-" + ENORME)):
            with self.subTest(cumple=valor[:20]):
                s = self.cargar_sala('[[miembro]]\nnombre = "Ana"\ncumple = %s\n' % valor)
                self.assertEqual(self.avisos, ["salas/prueba.toml: Ana: cumple mal escrito (%s), usa DD-MM"
                                               % texto])
                self.assertEqual(s["miembros"], [{"nombre": "Ana"}])

    def test_fecha_imposible_sin_comillas(self):
        # cumple = 2026-02-30 sin comillas no es TOML: esa sala no se puede leer (con aviso)
        self.escribir("salas/buena.toml", "")
        self.escribir("salas/prueba.toml", '[[miembro]]\nnombre = "Ana"\ncumple = 2026-02-30\n')
        self.cargar()
        self.assertEqual([s["clave"] for s in self.salas], ["buena"])
        self.assertEqual(len(self.avisos), 1, self.avisos)
        self.assertTrue(self.avisos[0].startswith("salas/prueba.toml: "), self.avisos)

    def test_muebles_de_la_sala(self):
        s = self.cargar_sala('mueble = ["sillon", "planta"]\n')
        self.assertSinAvisos()
        self.assertEqual(s["muebles"], [{"pieza": "sillon"}, {"pieza": "planta"}])
        s = self.cargar_sala("mueble = [3]\n")
        self.assertEqual(self.avisos, ["salas/prueba.toml: mueble mal escrito (3), usa [[mueble]]"])
        self.assertEqual(s["muebles"], [])


# ===================================================================== reuniones

class Reuniones(Base):

    def test_reunion_bien_escrita(self):
        rs = self.reuniones("""\
            [[reunion]]
            nombre = "Diaria"
            dia = "miercoles"
            hora = "9:5"
            minutos = "45,5"
            quien = "todos"
            """)
        self.assertSinAvisos()
        self.assertEqual(rs, [{"nombre": "Diaria", "dia": "miércoles", "hora": "09:05", "minutos": 45.5,
                               "quien": "todos"}])

    def test_reunion_con_lo_de_por_defecto(self):
        rs = self.reuniones('[[reunion]]\nnombre = "Café"\n')
        self.assertSinAvisos()
        self.assertEqual(rs, [{"nombre": "Café", "hora": "10:00", "dia": "todos", "minutos": 60,
                               "quien": "todos"}])

    def test_hora_de_toml(self):
        rs = self.reuniones("[[reunion]]\nhora = 09:30:00\n")
        self.assertSinAvisos()
        self.assertEqual(rs[0]["hora"], "09:30")

    def test_hora_mal_escrita(self):
        for valor, texto in (('"25:00"', "25:00"), ('"24:00"', "24:00"), ('"10:60"', "10:60"),
                             ('"diez"', "diez"), ('"10"', "10"), ("10", "10"), ('"10:00:00"', "10:00:00"),
                             ('"-1:30"', "-1:30"), ('""', ""), ("true", "True"), ("[10, 0]", "[10, 0]")):
            with self.subTest(hora=valor):
                rs = self.reuniones('[[reunion]]\nnombre = "Diaria"\nhora = %s\n' % valor)
                self.assertEqual(self.avisos, ["salas/reuniones.toml: reunión «Diaria»: hora mal escrita "
                                               "(%s), usa HH:MM, de 00:00 a 23:59" % texto])
                self.assertEqual(rs, [])

    def test_dias(self):
        for valor, dia in (('"Lunes"', "lunes"), ('"MIÉRCOLES"', "miércoles"), ('"sabado"', "sábado"),
                           ('" viernes "', "viernes"), ('"Todos"', "todos"), ('"domingo"', "domingo")):
            with self.subTest(dia=valor):
                rs = self.reuniones("[[reunion]]\ndia = %s\n" % valor)
                self.assertSinAvisos()
                self.assertEqual(rs[0]["dia"], dia)

    def test_dia_mal_escrito(self):
        for valor, texto in (('"funday"', "funday"), ("3", "3"), ('["lunes"]', "['lunes']"), ('""', "")):
            with self.subTest(dia=valor):
                rs = self.reuniones('[[reunion]]\nnombre = "Diaria"\ndia = %s\n' % valor)
                self.assertEqual(self.avisos, ["salas/reuniones.toml: reunión «Diaria»: día mal escrito "
                                               "(%s), usa lunes, martes... o todos" % texto])
                self.assertEqual(rs, [])

    def test_minutos_mal_escritos(self):
        for valor in ('"mucho"', "true", "nan", "[30]"):
            with self.subTest(minutos=valor):
                rs = self.reuniones('[[reunion]]\nnombre = "Diaria"\nminutos = %s\n' % valor)
                self.assertEqual(self.avisos, ["salas/reuniones.toml: reunión «Diaria»: minutos debe ser "
                                               "un número (puse 60)"])
                self.assertEqual(rs[0]["minutos"], 60)   # la reunión se hace igual

    def test_reunion_que_no_es_tabla(self):
        rs = self.reuniones('reunion = "a las diez"\n')
        self.assertEqual(self.avisos, ["salas/reuniones.toml: reunion mal escrito (a las diez), usa [[reunion]]"])
        self.assertEqual(rs, [])

    def test_reunion_como_tabla_simple(self):
        rs = self.reuniones('[reunion]\nnombre = "Diaria"\n')
        self.assertSinAvisos()
        self.assertEqual([r["nombre"] for r in rs], ["Diaria"])

    def test_una_mala_no_quita_las_demas(self):
        rs = self.reuniones('[[reunion]]\nnombre = "Mala"\nhora = "99:99"\n\n'
                            '[[reunion]]\nnombre = "Buena"\nhora = "12:00"\n')
        self.assertEqual(len(self.avisos), 1, self.avisos)
        self.assertEqual([r["nombre"] for r in rs], ["Buena"])


# ========================================================== a quién convocan

class Quien(Base):

    def quien(self, valor):
        return self.reuniones('[[reunion]]\nnombre = "Diaria"\nquien = %s\n' % valor)

    def test_todos(self):
        for valor in ('"todos"', '"TODOS"', '" Todos "'):
            with self.subTest(quien=valor):
                rs = self.quien(valor)
                self.assertSinAvisos()
                self.assertEqual(rs[0]["quien"], "todos")

    def test_sala_por_su_clave_o_por_su_nombre(self):
        for valor in ('"diseno"', '"Diseno"', '"Diseño"', '"DISEÑO"', '"diseño"', '" diseno "'):
            with self.subTest(quien=valor):
                rs = self.quien(valor)
                self.assertSinAvisos()
                self.assertEqual(rs[0]["quien"], "diseno")

    def test_sala_con_otro_nombre_visible(self):
        self.escribir("salas/dev.toml", 'nombre = "Desarrollo web"\n[[miembro]]\nnombre = "Luis"\n')
        for valor in ('"dev"', '"Desarrollo web"', '"desarrollo WEB"'):
            with self.subTest(quien=valor):
                rs = self.quien(valor)
                self.assertSinAvisos()
                self.assertEqual(rs[0]["quien"], "dev")

    def test_una_persona(self):
        for valor in ('"Elena"', '"elena"', '"ELENA"', '" Elena "'):
            with self.subTest(quien=valor):
                rs = self.quien(valor)
                self.assertSinAvisos()
                self.assertEqual(rs[0]["quien"], ["Elena"])

    def test_lista_de_nombres(self):
        rs = self.quien('["elena", "ANA"]')
        self.assertSinAvisos()
        self.assertEqual(rs[0]["quien"], ["Elena", "Ana"])

    def test_lista_con_alguien_que_no_esta(self):
        rs = self.quien('["Elena", "Nadie"]')
        self.assertEqual(self.avisos, ["salas/reuniones.toml: reunión «Diaria»: «Nadie» no es nadie "
                                       "del hormiguero"])
        self.assertEqual(rs[0]["quien"], ["Elena"])

    def test_lista_sin_nadie_que_este(self):
        rs = self.quien('["Nadie", "Tampoco"]')
        self.assertEqual(len(self.avisos), 2, self.avisos)
        self.assertEqual(rs, [])

    def test_ni_sala_ni_persona(self):
        rs = self.quien('"Nadie"')
        self.assertEqual(self.avisos, ["salas/reuniones.toml: reunión «Diaria»: «Nadie» no es ninguna sala "
                                       "ni nadie del hormiguero"])
        self.assertEqual(rs, [])

    def test_lista_vacia(self):
        rs = self.quien("[]")
        self.assertEqual(self.avisos, ["salas/reuniones.toml: reunión «Diaria»: quien está vacío, así que "
                                       "no convoca a nadie"])
        self.assertEqual(rs, [])

    def test_valores_raros(self):
        for valor in ("5", "true", "1.5", "{ a = 1 }", "[1, 2]", '[["Ana"]]', '""'):
            with self.subTest(quien=valor):
                rs = self.quien(valor)
                self.assertTrue(self.avisos)
                self.assertTrue(all(a.startswith("salas/reuniones.toml: reunión «Diaria»: ")
                                    for a in self.avisos), self.avisos)
                self.assertEqual(rs, [])

    def test_persona_con_nombre_repetido(self):
        # la segunda Ana sale como «Ana (Diseño)», y así se la puede convocar
        self.escribir("salas/desarrollo.toml", 'nombre = "Desarrollo"\n[[miembro]]\nnombre = "Ana"\n')
        rs = self.quien('["ana (diseno)", "Ana"]')
        self.assertEqual(self.avisos, ["hay dos «Ana» (en salas/desarrollo.toml y en salas/diseno.toml): "
                                       "la segunda sale como «Ana (Diseño)»"])
        self.assertEqual(rs[0]["quien"], ["Ana (Diseño)", "Ana"])


# ============================================================ nombres repetidos

class Repetidos(Base):

    def test_dos_salas_con_la_misma_persona(self):
        self.escribir("salas/desarrollo.toml", 'nombre = "Desarrollo"\n[[miembro]]\nnombre = "Ana"\n')
        self.escribir("salas/diseno.toml", 'nombre = "Diseño"\n[[miembro]]\nnombre = "Ana"\ncumple = "14-03"\n')
        self.cargar()
        self.assertEqual(self.avisos, ["hay dos «Ana» (en salas/desarrollo.toml y en salas/diseno.toml): "
                                       "la segunda sale como «Ana (Diseño)»"])
        self.assertEqual(self.sala("desarrollo")["miembros"], [{"nombre": "Ana"}])
        self.assertEqual(self.sala("diseno")["miembros"], [{"nombre": "Ana (Diseño)", "cumple": "14-03"}])

    def test_mayusculas_cuentan_como_el_mismo_nombre(self):
        self.escribir("salas/desarrollo.toml", 'nombre = "Desarrollo"\nmiembro = ["ANA"]\n')
        self.escribir("salas/diseno.toml", 'nombre = "Diseño"\nmiembro = ["ana"]\n')
        self.cargar()
        self.assertAviso("hay dos «ana»")
        self.assertEqual(self.sala("diseno")["miembros"], [{"nombre": "ana (Diseño)"}])

    def test_tres_en_la_misma_sala(self):
        s = self.cargar_sala('nombre = "Prueba"\nmiembro = ["Ana", "Ana", "Ana", "Luis"]\n')
        self.assertEqual(self.avisos, ["hay dos «Ana» (en salas/prueba.toml): la segunda sale como "
                                       "«Ana (Prueba)»",
                                       "salas/prueba.toml: hay más de dos «Ana»; las que sobran no salen "
                                       "(cambia un nombre)"])
        self.assertEqual([m["nombre"] for m in s["miembros"]], ["Ana", "Ana (Prueba)", "Luis"])

    def test_en_una_sala_y_en_idos_sin_fecha(self):
        self.escribir("salas/prueba.toml", 'miembro = ["Irene"]\n')
        self.escribir("idos.toml", '[[ido]]\nnombre = "irene"\n')
        self.cargar()
        self.assertEqual(self.avisos, ["«irene» está en salas/prueba.toml y en idos.toml sin fecha "
                                       "(ya se fue), así que no sale; si son dos personas, cambia un nombre"])

    def test_en_una_sala_y_en_idos_con_fecha(self):
        # se va ese día: hasta entonces sigue en su sala
        self.escribir("salas/prueba.toml", 'miembro = ["Irene"]\n')
        self.escribir("idos.toml", '[[ido]]\nnombre = "Irene"\nfecha = "2026-09-30"\n')
        self.cargar()
        self.assertSinAvisos()


# ===================================================================== idos.toml

class Idos(Base):

    def test_idos_bien_escritos(self):
        self.escribir("idos.toml", """\
            [[ido]]
            nombre = "  Carlos  "
            epitafio = "gone, but not forgotten"

            [[ido]]
            nombre = "Irene"
            fecha = "2026-09-30"
            """)
        _cfg, _s, idos, _f = self.cargar()
        self.assertSinAvisos()
        self.assertEqual(idos, [{"nombre": "Carlos", "epitafio": "gone, but not forgotten"},
                                {"nombre": "Irene", "fecha": "2026-09-30"}])

    def test_tabla_simple_lista_y_texto(self):
        for texto, nombres in (('[ido]\nnombre = "Pepe"\n', ["Pepe"]),
                               ('ido = ["Pepe", "Juan"]\n', ["Pepe", "Juan"]),
                               ('ido = "Pepe"\n', ["Pepe"]), ("[[ido]]\nnombre = 5\n", ["5"])):
            with self.subTest(idos=texto):
                self.escribir("idos.toml", texto)
                _cfg, _s, idos, _f = self.cargar()
                self.assertSinAvisos()
                self.assertEqual([d["nombre"] for d in idos], nombres)

    def test_ido_mal_escrito(self):
        self.escribir("idos.toml", 'ido = [1, "Pepe"]\n')
        _cfg, _s, idos, _f = self.cargar()
        self.assertEqual(self.avisos, ["idos.toml: ido mal escrito (1), usa [[ido]]"])
        self.assertEqual(idos, [{"nombre": "Pepe"}])

    def test_toml_roto(self):
        self.escribir("idos.toml", '[[ido]]\nnombre = "Pepe\n')
        _cfg, _s, idos, _f = self.cargar()
        self.assertEqual(idos, [])
        self.assertEqual(len(self.avisos), 1, self.avisos)
        self.assertTrue(self.avisos[0].startswith("idos.toml: "), self.avisos)

    def test_ido_sin_nombre_avisa(self):
        # un [[ido]] sin nombre (p. ej. con «nombe» mal escrito) se quita con un aviso, como un
        # [[miembro]] sin nombre
        self.escribir("idos.toml", '[[ido]]\nnombe = "Pepe"\nepitafio = "adiós"\n')
        _cfg, _s, idos, _f = self.cargar()
        self.assertEqual(idos, [])
        self.assertEqual(self.avisos, ["idos.toml: hay un [[ido]] sin nombre"])


# ==================================================================== tipos/*.toml

class Tipos(Base):

    def tipo(self, texto, fichero="cocina.toml"):
        self.escribir("tipos/" + fichero, texto)
        self.cargar()
        return self.cfg["tipos"].get(os.path.splitext(fichero)[0].lower())

    def test_tipo_bien_escrito(self):
        t = self.tipo("""\
            funcion = "Comedor"
            paredes = "#FF8800"
            suelo = " Baldosa "

            [[mueble]]
            pieza = "nevera"
            sitio = "izquierda"

            [[mueble]]
            pieza = "encimera"
            """)
        self.assertSinAvisos()
        self.assertEqual(t, {"funcion": "comedor", "paredes": "#ff8800", "suelo": "baldosa",
                             "fichero": "tipos/cocina.toml",
                             "muebles": [{"pieza": "nevera", "sitio": "izquierda"}, {"pieza": "encimera"}]})

    def test_tipo_vacio(self):
        t = self.tipo("")
        self.assertSinAvisos()
        self.assertEqual((t["funcion"], t["paredes"], t["suelo"], t["muebles"]), ("otra", "madera", "madera", []))

    def test_funciones(self):
        for funcion in A.FUNCIONES:
            with self.subTest(funcion=funcion):
                t = self.tipo('funcion = "%s"\n' % funcion.upper())
                self.assertSinAvisos()
                self.assertEqual(t["funcion"], funcion)

    def test_funcion_desconocida(self):
        for valor, texto in (('"cocina"', "cocina"), ("5", "5"), ("true", "true")):
            with self.subTest(funcion=valor):
                t = self.tipo("funcion = %s\n" % valor)
                self.assertEqual(self.avisos, ["tipos/cocina.toml: función desconocida «%s»" % texto])
                self.assertEqual(t["funcion"], "otra")

    def test_paredes(self):
        for valor, paredes in (('"Azulejo"', "azulejo"), ('" piedra "', "piedra"), ('"#abc"', "#abc")):
            with self.subTest(paredes=valor):
                t = self.tipo("paredes = %s\n" % valor)
                self.assertSinAvisos()
                self.assertEqual(t["paredes"], paredes)
        for valor, texto in (('"rojo"', "rojo"), ('"#GG8800"', "#GG8800"), ("5", "5"), ('"#12"', "#12")):
            with self.subTest(paredes=valor):
                t = self.tipo("paredes = %s\n" % valor)
                self.assertEqual(self.avisos, ["tipos/cocina.toml: paredes «%s» no existe (madera, azulejo, "
                                               "piedra o \"#RRGGBB\"; puse madera)" % texto])
                self.assertEqual(t["paredes"], "madera")

    def test_suelo_que_no_existe(self):
        for valor, texto in (('"moqueta"', "moqueta"), ("3", "3"), ('"#ffffff"', "#ffffff")):
            with self.subTest(suelo=valor):
                t = self.tipo("suelo = %s\n" % valor)
                self.assertEqual(self.avisos, ["tipos/cocina.toml: suelo «%s» no existe (madera, baldosa o "
                                               "tierra; puse madera)" % texto])
                self.assertEqual(t["suelo"], "madera")

    def test_muebles(self):
        t = self.tipo('mueble = ["sillon", "planta"]\n')
        self.assertSinAvisos()
        self.assertEqual(t["muebles"], [{"pieza": "sillon"}, {"pieza": "planta"}])
        t = self.tipo('[mueble]\npieza = "sillon"\n')
        self.assertSinAvisos()
        self.assertEqual(t["muebles"], [{"pieza": "sillon"}])
        t = self.tipo("mueble = [3]\n")
        self.assertEqual(self.avisos, ["tipos/cocina.toml: mueble mal escrito (3), usa [[mueble]]"])
        self.assertEqual(t["muebles"], [])

    def test_toml_roto(self):
        t = self.tipo('funcion = "comedor\n')
        self.assertIsNone(t)
        self.assertEqual(len(self.avisos), 1, self.avisos)
        self.assertTrue(self.avisos[0].startswith("tipos/cocina.toml: "), self.avisos)

    def test_clave_en_minusculas_y_ocultos(self):
        self.escribir("tipos/.oculto.toml", "roto [[[")
        self.escribir("tipos/notas.txt", "roto [[[")
        t = self.tipo('funcion = "comedor"\n', "Cocina.toml")
        self.assertSinAvisos()
        self.assertEqual(t["fichero"], "tipos/Cocina.toml")
        self.assertNotIn(".oculto", self.cfg["tipos"])

    def test_la_sala_toma_la_funcion_de_su_tipo(self):
        self.escribir("tipos/cocina.toml", 'funcion = "comedor"\n')
        s = self.cargar_sala('tipo = "cocina"\n')
        self.assertSinAvisos()
        self.assertEqual(s["funcion"], "comedor")


# ================================================================ calendario.toml

class Calendario(Base):

    def calendario(self, texto):
        self.escribir("calendario.toml", texto)
        self.cargar()
        return self.fiestas

    def test_fiesta_bien_escrita(self):
        fs = self.calendario("""\
            [[fiesta]]
            nombre = "Feria"
            desde = "15-08"
            hasta = "22-08"
            decoracion = "Feria"
            gorro = " Flor "
            mensaje = "¡Feria!"

            [[fiesta]]
            nombre = "Semana Santa"
            desde = "pascua-7"
            hasta = "pascua"

            [[fiesta]]
            nombre = "San Valentín"
            desde = "14/02"
            """)
        self.assertSinAvisos()
        self.assertEqual([f.nombre for f in fs], ["Feria", "Semana Santa", "San Valentín"])
        self.assertEqual((fs[0].decoracion, fs[0].gorro, fs[0].mensaje), ("feria", "flor", "¡Feria!"))
        self.assertTrue(fs[0].activa(datetime.date(2026, 8, 20)))
        self.assertTrue(fs[1].activa(datetime.date(2026, 4, 5)))     # Domingo de Resurrección de 2026
        self.assertEqual(fs[2].hasta, "14/02")                         # sin hasta: un solo día

    def test_29_de_febrero(self):
        fs = self.calendario('[[fiesta]]\nnombre = "Bisiesto"\ndesde = "29-02"\n')
        self.assertSinAvisos()
        self.assertTrue(fs[0].activa(datetime.date(2028, 2, 29)))
        self.assertFalse(fs[0].activa(datetime.date(2027, 3, 1)))

    def test_fechas_imposibles(self):
        for valor, texto in (('"31-02"', "31-02"), ('"00-01"', "00-01"), ('"15-13"', "15-13"),
                             ('"pascua+x"', "pascua+x"), ('"pascua+1.5"', "pascua+1.5"),
                             ('"pascua+99999999999999999999"', "pascua+99999999999999999999"),
                             ("2026-12-24", "2026-12-24"), ("5", "5"), ('"navidad"', "navidad")):
            with self.subTest(desde=valor):
                fs = self.calendario('[[fiesta]]\nnombre = "Mala"\ndesde = %s\n' % valor)
                self.assertEqual(self.avisos, ["calendario: «Mala»: fecha mal escrita (%s), usa DD-MM o pascua+N"
                                               % texto])
                self.assertEqual(fs, [])

    def test_hasta_imposible(self):
        fs = self.calendario('[[fiesta]]\nnombre = "Mala"\ndesde = "01-01"\nhasta = "32-01"\n'
                             '\n[[fiesta]]\nnombre = "Buena"\ndesde = "01-01"\n')
        self.assertEqual(self.avisos, ["calendario: «Mala»: fecha mal escrita (32-01), usa DD-MM o pascua+N"])
        self.assertEqual([f.nombre for f in fs], ["Buena"])

    def test_tabla_simple(self):
        fs = self.calendario('[fiesta]\nnombre = "Sola"\ndesde = "01-05"\n')
        self.assertEqual(self.avisos, ["calendario: escribe [[fiesta]], con dos corchetes (con [fiesta] "
                                       "sólo cabe una)"])
        self.assertEqual([f.nombre for f in fs], ["Sola"])

    def test_fiesta_que_no_es_tabla(self):
        fs = self.calendario('fiesta = "Navidad"\n')
        self.assertEqual(self.avisos, ["calendario: fiesta mal escrita (Navidad), usa [[fiesta]]"])
        self.assertEqual(fs, [])
        fs = self.calendario('fiesta = [1, { nombre = "Buena", desde = "01-05" }]\n')
        self.assertEqual(self.avisos, ["calendario: fiesta mal escrita (1), usa [[fiesta]]"])
        self.assertEqual([f.nombre for f in fs], ["Buena"])

    def test_decoracion_y_gorro_que_no_existen(self):
        fs = self.calendario('[[fiesta]]\nnombre = "Rara"\ndesde = "01-05"\ndecoracion = "fuegos"\n'
                             'gorro = "sombrero"\n')
        self.assertEqual(self.avisos, ["calendario: «Rara»: no existe la decoración «fuegos»",
                                       "calendario: «Rara»: no existe el gorro «sombrero»"])
        self.assertEqual([f.nombre for f in fs], ["Rara"])   # se queda, con lo que sepa pintar

    def test_toml_roto(self):
        fs = self.calendario('[[fiesta]]\nnombre = "Rota\n')
        self.assertEqual(fs, [])
        self.assertEqual(len(self.avisos), 1, self.avisos)
        self.assertTrue(self.avisos[0].startswith("calendario: "), self.avisos)


# ================================================= valores raros: nunca excepción

# valores de TOML de todos los tipos (sin el número enorme: ver test_numero_enorme)
RAROS = ('""', '"  "', "true", "0", "-7", "1.5", "nan", "-inf", "[]", '[1, "a"]', "{ a = 1 }",
         "[{ a = 1 }]", "1979-05-27", "07:32:00", "1979-05-27T07:32:00Z", '"ñ€😀"', '"-"', '":"', '"#"')


class NuncaExcepcion(Base):
    """Cualquier valor en cualquier clave: cargar() (también la de pixel, con los muebles)
    termina sin excepción y devuelve lo de siempre."""

    def probar(self, rel, plantilla, claves):
        for clave in claves:
            for valor in RAROS:
                texto = plantilla % (clave, valor)
                with self.subTest(fichero=rel, texto=texto):
                    self.escribir(rel, texto)
                    self.cargar()
                    P.cargar(A, self.args(), [])
                    self.assertIsInstance(self.cfg["general"]["fundacion"], str)
                    datetime.date.fromisoformat(self.cfg["general"]["fundacion"])
                    self.assertTrue(all(isinstance(a, str) for a in self.avisos))

    def test_config(self):
        self.probar("config.toml", '[general]\nfundacion = "2026-01-01"\n%s = %s\n',
                    ("semilla", "fps_pixel", "texto_aumento", "nombre"))
        self.probar("config.toml", '[general]\nsemilla = 7\n%s = %s\n', ("fundacion",))
        for seccion, claves in (("ciudad", ("lat", "lon", "zona_horaria")), ("tiempo", ("cada_minutos", "fuente")),
                                ("nido", ("entrada", "obras")), ("paisaje", ("cementerio",))):
            self.probar("config.toml", '[general]\nfundacion = "2026-01-01"\nsemilla = 7\n[%s]\n' % seccion
                        + "%s = %s\n", claves)
        self.probar("config.toml", '%s = %s\n[general]\nfundacion = "2026-01-01"\nsemilla = 7\n',
                    ("ciudad", "nido", "general"))

    def test_sala(self):
        self.probar("salas/prueba.toml", "%s = %s\n", ("nombre", "color", "planta", "nivel", "x", "ancho",
                                                       "tipo", "jefe", "miembro", "reunion", "mueble"))

    def test_miembro(self):
        self.probar("salas/prueba.toml", '[[miembro]]\n%s = %s\n', ("nombre",))
        self.probar("salas/prueba.toml", '[[miembro]]\nnombre = "Ana"\n%s = %s\n', ("cumple", "color", "alta"))

    def test_reunion(self):
        self.escribir("salas/diseno.toml", EQUIPO)
        self.probar("salas/reuniones.toml", '[[reunion]]\n%s = %s\n',
                    ("nombre", "dia", "hora", "minutos", "quien"))

    def test_muebles(self):
        self.probar("salas/prueba.toml", '[[mueble]]\n%s = %s\n', ("pieza", "sitio", "aparece"))
        self.probar("tipos/cocina.toml", '[[mueble]]\n%s = %s\n', ("pieza", "sitio", "aparece"))

    def test_tipo(self):
        self.probar("tipos/cocina.toml", "%s = %s\n", ("funcion", "paredes", "suelo", "mueble"))

    def test_idos(self):
        self.probar("idos.toml", "%s = %s\n", ("ido",))
        self.probar("idos.toml", '[[ido]]\n%s = %s\n', ("nombre",))
        self.probar("idos.toml", '[[ido]]\nnombre = "Pepe"\n%s = %s\n', ("fecha", "epitafio"))

    def test_calendario(self):
        self.probar("calendario.toml", "%s = %s\n", ("fiesta",))
        self.probar("calendario.toml", '[[fiesta]]\ndesde = "01-01"\n%s = %s\n',
                    ("nombre", "hasta", "decoracion", "gorro", "mensaje"))
        self.probar("calendario.toml", '[[fiesta]]\n%s = %s\n', ("desde",))


# ================================================ y luego se monta el hormiguero

class TrasLaCarga(Base):
    """Lo que cargar() deja pasar sin aviso lo tiene que entender el hormiguero (hormiga.mundo):
    con lo cargado se monta sin excepción."""

    def setUp(self):
        super().setUp()
        self.config(resto='[tiempo]\nfuente = "estadistico"\n')   # nunca internet

    def montar(self):
        from hormiga.mundo import Mundo
        # otro día que el "ahora" de las pruebas: tampoco pide el tiempo real
        m = Mundo(self.cfg, self.salas, self.idos, self.fiestas, P.PantallaNula(),
                  lambda: datetime.datetime(2026, 10, 30, 13, 0), list(self.avisos))
        m.paso(0.05)
        return m

    def test_se_monta_con_fechas_bien_escritas(self):
        self.escribir("salas/prueba.toml", '[[miembro]]\nnombre = "Ana"\nalta = "2026-03-01"\n\n'
                                           '[[miembro]]\nnombre = "Luis"\nalta = 2026-03-01\n')
        self.escribir("idos.toml", '[[ido]]\nnombre = "Pepe"\nfecha = "2026-03-01"\n\n'
                                   '[[ido]]\nnombre = "Juan"\nfecha = 2026-03-01\n')
        self.cargar()
        self.assertSinAvisos()
        self.montar()

    def test_semilla_de_texto(self):
        self.escribir("config.toml", '[general]\nfundacion = "2026-01-01"\nsemilla = "hormigas"\n'
                                     '[tiempo]\nfuente = "estadistico"\n')
        self.cargar()
        self.montar()

    def test_alta_con_hora(self):
        # alta = 2026-03-01T09:00:00 (fecha y hora de TOML, sin comillas): vale el día. Antes
        # hormiga/mundo.py la dejaba con la hora y, al compararla con un día, no arrancaba
        self.escribir("salas/prueba.toml", '[[miembro]]\nnombre = "Ana"\nalta = 2026-03-01T09:00:00\n')
        self.cargar()
        self.assertSinAvisos()
        self.assertIn("Ana", self.montar().hormigas)

    def test_fecha_de_ido_con_hora(self):
        # lo mismo con la fecha de un [[ido]] (fecha = 2026-03-01T09:00:00)
        self.escribir("idos.toml", '[[ido]]\nnombre = "Pepe"\nfecha = 2026-03-01T09:00:00\n')
        self.cargar()
        self.assertEqual(self.montar().idos, ["Pepe"])

    def test_semilla_que_es_una_lista(self):
        # semilla = [1, 2] (o una tabla, o una fecha): aviso y la de por defecto. Antes no se
        # comprobaba y el hormiguero no arrancaba (unhashable type en hormiga/tiempo.py)
        for valor in ("[1, 2]", "{ a = 1 }", "2026-01-01", "true", "nan"):
            with self.subTest(semilla=valor):
                self.escribir("config.toml", '[general]\nfundacion = "2026-01-01"\nsemilla = %s\n'
                                             '[tiempo]\nfuente = "estadistico"\n' % valor)
                self.cargar()
                self.assertEqual(len(self.avisos), 1, self.avisos)
                self.assertTrue(self.avisos[0].startswith("config: semilla mal escrita"), self.avisos)
                self.assertEqual(self.cfg["general"]["semilla"], A.POR_DEFECTO["general"]["semilla"])
                self.montar()

    def test_paisaje_suelo_que_no_es_lista(self):
        # [paisaje] suelo = true (o un número, o un texto) en vez de [[paisaje.suelo]]: aviso y
        # el de siempre. Antes hormiga/superficie.py daba TypeError y el hormiguero no arrancaba
        for clave in ("suelo", "fondo"):
            for valor in ("true", "3", '"olivo"', "2026-01-01"):
                with self.subTest(clave=clave, valor=valor):
                    self.config(resto='[tiempo]\nfuente = "estadistico"\n[paisaje]\n%s = %s\n' % (clave, valor))
                    self.cargar()
                    avisos = self.montar().todos_los_avisos()
                    self.assertTrue(any(a.startswith("paisaje: %s mal escrito" % clave) for a in avisos), avisos)

    def test_paisaje_con_si_o_no_y_claves_raras(self):
        self.config(resto='[tiempo]\nfuente = "estadistico"\n[paisaje]\nmontes = "false"\ncostas = true\n'
                          '[[paisaje.suelo]]\npieza = " Olivo "\nX = 30\ncosta = false\n')
        self.cargar()
        m = self.montar()
        self.assertIs(m.superficie.montes_lejos, False)
        self.assertIs(m.superficie.costa, True)
        self.assertEqual([p for p, _x in m.superficie.piezas_suelo], ["olivo"])
        avisos = [a for a in m.todos_los_avisos() if a.startswith("paisaje")]
        self.assertEqual(avisos, ["paisaje: no conozco «costas» (no lo tengo en cuenta)",
                                  "paisaje: olivo: no conozco «X» (no lo tengo en cuenta)",
                                  "paisaje: «costa» está dentro de una pieza (olivo) y [paisaje] no lo ve; "
                                  "ponlo arriba, antes de la primera [[paisaje...]]"])

    def test_valores_raros_en_fechas_y_semilla(self):
        """Lo que sea en alta, fecha o semilla: el hormiguero se monta (con aviso si hace falta)."""
        for valor in RAROS:
            with self.subTest(valor=valor):
                self.escribir("salas/prueba.toml", '[[miembro]]\nnombre = "Ana"\nalta = %s\n' % valor)
                self.escribir("idos.toml", '[[ido]]\nnombre = "Pepe"\nfecha = %s\n' % valor)
                self.escribir("config.toml", '[general]\nfundacion = "2026-01-01"\nsemilla = %s\n'
                                             '[tiempo]\nfuente = "estadistico"\n' % valor)
                self.cargar()
                self.montar()

    def test_paisaje_con_tabla_simple(self):
        # [paisaje.suelo] en vez de [[paisaje.suelo]]: no tumba el hormiguero y avisa
        self.config(resto='[tiempo]\nfuente = "estadistico"\n[paisaje.suelo]\npieza = "olivo"\nx = 40\n')
        self.cargar()
        m = self.montar()
        self.assertTrue(any(a.startswith("paisaje: ") for a in m.todos_los_avisos()), m.todos_los_avisos())


# ============================================== local/ manda sobre el repositorio

class LocalTienePrioridad(Base):
    """pixel.app.tus_datos: si existe local/<fichero>, se usa en lugar del de ejemplo."""

    def setUp(self):
        super().setUp()
        p = mock.patch.object(P, "RAIZ", self.raiz)
        p.start()
        self.addCleanup(p.stop)
        self.local = os.path.join(self.raiz, "local")

    def en_raiz(self, rel, texto=""):
        return self.escribir(rel, texto, self.raiz)

    def test_tus_datos_prefiere_local(self):
        self.en_raiz("config.toml")
        propio = self.en_raiz("local/config.toml")
        self.assertEqual(P.tus_datos("config.toml"), propio)

    def test_sin_local_el_del_repositorio(self):
        self.en_raiz("config.toml")
        self.assertEqual(P.tus_datos("config.toml"), os.path.join(self.raiz, "config.toml"))
        os.makedirs(self.local)   # local/ vacío tampoco cambia nada
        self.assertEqual(P.tus_datos("config.toml"), os.path.join(self.raiz, "config.toml"))
        self.assertEqual(P.tus_datos("salas"), os.path.join(self.raiz, "salas"))

    def test_cada_fichero_por_separado(self):
        self.en_raiz("config.toml")
        self.en_raiz("idos.toml")
        os.makedirs(os.path.join(self.raiz, "salas"))
        os.makedirs(os.path.join(self.local, "salas"))
        self.en_raiz("local/idos.toml")
        a = P.argumentos([])
        self.assertEqual(a.config, os.path.join(self.raiz, "config.toml"))
        self.assertEqual(a.salas, os.path.join(self.local, "salas"))
        self.assertEqual(a.idos, os.path.join(self.local, "idos.toml"))
        self.assertEqual(a.tipos, os.path.join(self.raiz, "tipos"))   # no existe en ninguno: el del repo

    def test_las_opciones_mandan(self):
        self.en_raiz("local/config.toml")
        otro = self.ruta("config.toml")
        self.assertEqual(P.argumentos(["-c", otro]).config, otro)

    def test_se_cargan_los_de_local(self):
        self.en_raiz("config.toml", '[general]\nnombre = "del repositorio"\n')
        self.en_raiz("salas/repo.toml", 'nombre = "Del repositorio"\n')
        shutil.copytree(os.path.join(REPO, "tipos"), os.path.join(self.raiz, "tipos"))
        self.en_raiz("local/config.toml", '[general]\nnombre = "mío"\nfundacion = "2026-01-01"\nsemilla = 7\n'
                                          '[nido]\nobras = ["trabajo"]\n')
        self.en_raiz("local/salas/mia.toml", 'nombre = "Mía"\n')
        self.en_raiz("local/tipos/trabajo.toml", 'funcion = "trabajo"\n')
        args = P.argumentos([])
        args.sin_estado = True
        avisos = []
        cfg, salas, idos, fiestas = A.cargar(args, avisos)
        self.assertEqual(avisos, [])   # idos.toml y calendario.toml no están: no pasa nada
        self.assertEqual(cfg["general"]["nombre"], "mío")
        self.assertEqual([s["nombre"] for s in salas], ["Mía"])
        self.assertEqual(sorted(cfg["tipos"]), ["trabajo"])   # local/tipos sustituye entero al del repo
        self.assertEqual((idos, fiestas), ([], []))

    def test_tipos_de_local_sustituye_entero(self):
        shutil.copytree(os.path.join(REPO, "tipos"), os.path.join(self.raiz, "tipos"))
        self.en_raiz("local/config.toml", '[general]\nfundacion = "2026-01-01"\nsemilla = 7\n')
        self.en_raiz("local/tipos/trabajo.toml", 'funcion = "trabajo"\n')
        args = P.argumentos([])
        args.sin_estado = True
        avisos = []
        cfg, _s, _i, _f = A.cargar(args, avisos)
        self.assertEqual(sorted(cfg["tipos"]), ["trabajo"])
        # las obras de siempre no tienen tipo en local/tipos
        self.assertIn("config: [nido] la obra «despensa» no tiene tipo en tipos/ (será una sala vacía)",
                      avisos)


# ======================================================================== firma

class Firma(Base):
    """firma(): lo que se vigila para recargar al guardar (sólo los .toml de salas/)."""

    def preparar(self):
        for n in ("a.toml", "b.toml", ".oculta.toml", "a.toml.swp", "a.toml~", ".#a.toml", "notas.txt"):
            self.escribir("salas/" + n, "")
        for r in [self.ruta("salas", n) for n in os.listdir(self.ruta("salas"))] + \
                 [self.ruta(n) for n in ("config.toml", "idos.toml", "calendario.toml")]:
            os.utime(r, (1_700_000_000, 1_700_000_000))

    def test_solo_los_toml(self):
        self.preparar()
        firma = A.firma(self.args())
        self.assertIsInstance(firma, tuple)
        # también tipos/: no se aplica hasta reiniciar, pero así se avisa de que hay que hacerlo
        tipos = [self.ruta("tipos", n) for n in sorted(os.listdir(self.ruta("tipos"))) if n.endswith(".toml")]
        self.assertEqual([r for r, _t in firma],
                         [self.ruta("idos.toml"), self.ruta("config.toml"), self.ruta("calendario.toml"),
                          self.ruta("salas", "a.toml"), self.ruta("salas", "b.toml")] + tipos)

    def test_cambia_al_guardar_un_toml(self):
        self.preparar()
        antes = A.firma(self.args())
        os.utime(self.ruta("salas", "b.toml"), (1_700_000_060, 1_700_000_060))
        self.assertNotEqual(A.firma(self.args()), antes)

    def test_no_cambia_con_los_ficheros_del_editor(self):
        self.preparar()
        antes = A.firma(self.args())
        for n in (".oculta.toml", "a.toml.swp", "a.toml~", ".#a.toml", "notas.txt"):
            os.utime(self.ruta("salas", n), (1_700_000_060, 1_700_000_060))
        self.escribir("salas/c.toml.swp", "")
        self.assertEqual(A.firma(self.args()), antes)

    def test_cambia_al_crear_o_borrar_una_sala(self):
        self.preparar()
        antes = A.firma(self.args())
        self.escribir("salas/c.toml", "")
        despues = A.firma(self.args())
        self.assertNotEqual(despues, antes)
        os.remove(self.ruta("salas", "c.toml"))
        self.assertEqual(A.firma(self.args()), antes)

    def test_ficheros_que_no_existen(self):
        no = os.path.join(self.tmp, "no-existe")
        firma = A.firma(self.args(salas=no, tipos=no, idos=os.path.join(no, "idos.toml"),
                                  calendario=os.path.join(no, "c.toml")))
        self.assertEqual([r for r, _t in firma], [self.ruta("config.toml")])


# ============================================ lo que sólo se aplica al reiniciar

class Reinicio(Base):
    """pixel.app.avisos_de_reinicio: al recargar en marcha, lo que no se aplica hasta reiniciar
    (config.toml, tipos/ y el plano de las salas) deja un aviso en vez de parecer ya arreglado."""

    def foto(self):
        self.cargar()
        return P.para_reiniciar(self.args(), self.salas)

    def test_sin_cambios_no_avisa(self):
        self.escribir("salas/a.toml", 'nombre = "A"\n[[miembro]]\nnombre = "Ana"\n')
        antes = self.foto()
        self.escribir("salas/a.toml", 'nombre = "A"\n# un comentario\n[[miembro]]\nnombre = "Ana"\n'
                                      '[[miembro]]\nnombre = "Luis"\n')   # la gente sí se aplica sola
        self.assertEqual(P.avisos_de_reinicio(antes, self.foto()), [])

    def test_config_tipos_y_salas(self):
        self.escribir("salas/a.toml", 'nombre = "A"\n')
        self.escribir("salas/b.toml", 'nombre = "B"\n')
        antes = self.foto()
        self.config(resto='[ciudad]\nlat = 40.4\n')
        self.escribir("tipos/trabajo.toml", 'funcion = "trabajo"\nparedes = "azulejo"\n')
        self.escribir("salas/a.toml", 'nombre = "A"\nplanta = 3\n')
        os.remove(self.ruta("salas", "b.toml"))
        self.escribir("salas/c.toml", 'nombre = "C"\n')
        self.assertEqual(P.avisos_de_reinicio(antes, self.foto()), [
            "config.toml ha cambiado: reinicia el hormiguero para aplicarlo",
            "tipos/ ha cambiado: reinicia el hormiguero para aplicarlo",
            "salas/a.toml: el nombre, el color, la planta, x, el ancho y el tipo de la sala se aplican al "
            "reiniciar el hormiguero",
            "salas/b.toml ya no está: su sala se quita al reiniciar el hormiguero",
            "salas/c.toml es nueva: la sala sale al reiniciar el hormiguero (su gente, mientras, en otra)"])


# ============================================================== opciones

class Opciones(unittest.TestCase):
    """pixel.app.argumentos: --fecha y --hora mal escritas se explican en español, sin traceback."""

    def error(self, *argv):
        salida = io.StringIO()
        with mock.patch("sys.stderr", salida), self.assertRaises(SystemExit) as e:
            P.argumentos(list(argv))
        self.assertEqual(e.exception.code, 2)
        return salida.getvalue()

    def test_bien_escritas(self):
        a = P.argumentos(["--fecha", "2026-12-24", "--hora", "9:05", "--semilla", "7"])
        self.assertEqual((a.fecha, a.hora, a.semilla), ("2026-12-24", "09:05", 7))

    def test_mal_escritas(self):
        for argv, texto in ((("--fecha", "24-12-2026"), "no es una fecha"), (("--hora", "21"), "no es una hora"),
                            (("--hora", "25:00"), "no es una hora"), (("--dias", "diez"), "no es un número"),
                            (("--semilla", "1.5"), "no es un número entero"), (("--nada",), "no conozco")):
            with self.subTest(argv=argv):
                salida = self.error(*argv)
                self.assertIn(texto, salida)
                self.assertIn("uso: ", salida)
                self.assertNotIn("Traceback", salida)

    def test_ayuda_en_espanol(self):
        salida = io.StringIO()
        with mock.patch("sys.stdout", salida), self.assertRaises(SystemExit):
            P.argumentos(["--help"])
        self.assertIn("uso: ", salida.getvalue())
        self.assertIn("opciones", salida.getvalue())
        self.assertIn("enseña esta ayuda", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
