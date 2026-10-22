"""Pruebas del trazado del hormiguero: hormiga/tierra.py.

Se monta el plan (el nido del día 0 y las obras del año) con muchas semillas y muchas
configuraciones: las salas de ejemplo del repositorio, todas en una o en dos plantas,
una sola sala, ninguna, muchas, salas muy anchas, columnas fijas, plantas fuera de rango,
obras repetidas y entradas raras. En todas se comprueba que:

  - las salas no se pisan y todo lo cavado queda dentro de la tierra,
  - se llega andando desde la entrada a todas las salas el día 0 y al acabar el año,
  - ninguna obra empieza lejos de lo que ya está cavado,
  - las claves de las salas del año no chocan con las del nido ni entre sí,
  - la misma semilla da siempre el mismo trazado,
  - y montar el plan tarda poco.

Sólo se leen ficheros del repositorio (salas/, tipos/ y config.toml); no se escribe nada.
Las fechas son fijas: no depende del día en que se pase.

    SDL_VIDEODRIVER=dummy python3 -m unittest tests.test_trazado -v
"""

import copy
import datetime
import json
import os
import subprocess
import sys
import time
import tomllib
import unittest
from collections import deque
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hormiga import app as A  # noqa: E402
from hormiga import tierra as T  # noqa: E402
from hormiga.tierra import ANCHO, BORDE, GAP, PISOS, PROF, Plan  # noqa: E402
from pixel import muebles as MU  # noqa: E402

FUNDACION = datetime.date(2026, 1, 1)
SEMILLAS = (0, 1, 2, 3, 5, 7, 11, 19, 42, 2026, "otoño", 10 ** 12)
FIN_DEL_ANO = 400.0   # un día en que ya han terminado todas las obras


def sala(clave, planta=2, ancho=30, x=None, **resto):
    """Una sala del nido como las que salen de salas/*.toml."""
    d = {"clave": clave, "nombre": resto.pop("nombre", clave.capitalize()), "planta": planta,
         "ancho": ancho, "tipo": "trabajo", "funcion": "trabajo", "color": "blanco"}
    if x is not None:
        d["x"] = x
    d.update(resto)
    return d


# Las salas de ejemplo (salas/*.toml) copiadas aquí: así estas pruebas no cambian al editarlas
SALAS_EJEMPLO = (
    sala("comedor", 1, 34, x=40, nombre="Comedor", tipo="comedor", funcion="comedor"),
    sala("desarrollo", 2, 40, nombre="Desarrollo"),
    sala("despacho", 1, 22, nombre="Despacho", tipo="despacho", funcion="despacho"),
    sala("diseno", 2, 34, nombre="Diseño"),
    sala("fuente", 4, 28, nombre="Fuente", tipo="fuente", funcion="agua"),
    sala("reuniones", 1, 30, nombre="Reuniones", tipo="reuniones", funcion="reuniones"),
)
# Las obras de siempre, copiadas antes de que nadie las toque (mundo.py les añade campos)
OBRAS_EJEMPLO = tuple({k: o[k] for k in ("clave", "nombre", "ancho")} for o in T.OBRAS)


def _config_del_repo():
    """Las salas de salas/*.toml y las obras de config.toml, como las monta el hormiguero:
    hormiga/app.py lee las salas, pixel/app.py apunta lo que necesitan los muebles de cada
    tipo y hormiga/mundo.py prepara con eso las obras del año."""
    avisos = []
    tipos = A.cargar_tipos(os.path.join(RAIZ, "tipos"), avisos)
    for t in tipos.values():
        piezas = [str(mu.get("pieza", "")).lower() for mu in t["muebles"]]
        t["ancho_minimo"] = max([MU.ancho_minimo(p) for p in piezas if p in MU.PIEZAS], default=0)
    salas = []
    carpeta = os.path.join(RAIZ, "salas")
    for nombre in sorted(os.listdir(carpeta)):
        if nombre.endswith(".toml") and not nombre.startswith("."):
            with open(os.path.join(carpeta, nombre), "rb") as f:
                salas.append(A._sala(tomllib.load(f), nombre, tipos, avisos))
    with open(os.path.join(RAIZ, "config.toml"), "rb") as f:
        nido = tomllib.load(f).get("nido", {})
    por_clave = {o["clave"]: o for o in OBRAS_EJEMPLO}
    obras = []
    for n in nido.get("obras", [o["clave"] for o in OBRAS_EJEMPLO]):
        o = dict(por_clave.get(str(n).lower(), {"clave": str(n).lower(), "nombre": str(n), "ancho": 22}))
        tipo = tipos.get(o.get("tipo", o["clave"]), {})
        o["funcion"] = tipo.get("funcion", "otra")
        o["minimo"] = tipo.get("ancho_minimo", 0)
        obras.append(o)
    return salas, obras, int(nido.get("entrada", 20))


def _esc(salas, obras=OBRAS_EJEMPLO, entrada=20, semillas=SEMILLAS, fundacion=FUNDACION, sur=False):
    return {"salas": [dict(s) for s in salas], "obras": None if obras is None else [dict(o) for o in obras],
            "entrada": entrada, "semillas": semillas, "fundacion": fundacion, "sur": sur}


def _en_plantas(plantas):
    """Las salas de ejemplo repartidas por esas plantas (sin columna fija)."""
    return [dict(s, planta=plantas[i % len(plantas)], x=None) for i, s in enumerate(SALAS_EJEMPLO)]


def _muchas(n, ancho, plantas=(1, 2, 3, 4)):
    return [sala("s%02d" % i, plantas[i % len(plantas)], ancho, nombre="Sala %02d" % i) for i in range(n)]


_REPO = _config_del_repo()

ESCENARIOS = {
    # las de ejemplo, con muchas semillas
    "ejemplo": _esc(SALAS_EJEMPLO, semillas=tuple(range(40)) + ("otoño", 10 ** 12)),
    "repo": _esc(_REPO[0], _REPO[1], _REPO[2]),
    "obras_por_defecto": _esc(SALAS_EJEMPLO, obras=None),
    "sin_obras": _esc(SALAS_EJEMPLO, obras=[]),
    # todas en una planta o en dos
    "todas_en_la_1": _esc(_en_plantas([1])),
    "todas_en_la_2": _esc(_en_plantas([2])),
    "todas_en_la_4": _esc(_en_plantas([4])),
    "plantas_1_y_2": _esc(_en_plantas([1, 2])),
    "plantas_1_y_3": _esc(_en_plantas([1, 3])),
    "plantas_2_y_4": _esc(_en_plantas([2, 4])),
    # una sola, o ninguna
    "una_en_la_1": _esc([sala("unica", 1)]),
    "una_en_la_4": _esc([sala("unica", 4)]),
    "una_fija_en_la_4": _esc([sala("unica", 4, x=100)]),
    "una_estrecha": _esc([sala("unica", 3, 14)]),
    "ninguna": _esc([]),
    "ninguna_ni_obras": _esc([], obras=[]),
    # muchas
    "muchas_40": _esc(_muchas(40, 14), semillas=(0, 1, 2026)),
    "muchas_20": _esc(_muchas(20, 20), semillas=(0, 1, 2, 7, 2026)),
    "doce_en_la_1": _esc(_muchas(12, 14, (1,))),
    # anchas
    "ancha_100": _esc([sala("ancha", 1, 100)]),
    "ancha_154": _esc([sala("ancha", 2, 154)], semillas=(0, 1, 2026)),
    "ancha_200": _esc([sala("ancha", 2, 200)], semillas=(0, 1, 2026)),
    "anchas_en_todas": _esc([sala("s%d" % n, n, 120) for n in range(1, 5)], semillas=(0, 1, 2026)),
    "dos_de_70": _esc([sala("a", 2, 70), sala("b", 2, 70)]),
    # columnas fijas
    "x_fijas": _esc([sala("a", 1, 30, x=3), sala("b", 1, 30, x=120), sala("c", 2, 30, x=60),
                     sala("d", 3, 30, x=10), sala("e", 4, 28)]),
    "x_fuera": _esc([sala("a", 1, 30, x=-50), sala("b", 2, 30, x=1000), sala("c", 3, 30, x=0)]),
    "x_chocan": _esc([sala("a", 2, 30, x=50), sala("b", 2, 30, x=50), sala("c", 2, 30, x=55)]),
    # plantas fuera de rango (y una sin planta ni ancho: la 2 y 32 columnas)
    "plantas_fuera": _esc([sala("a", 0), sala("b", -3), sala("c", 5), sala("d", 99),
                           {"clave": "e", "nombre": "E"}]),
    # obras del año raras
    "obras_repetidas": _esc(SALAS_EJEMPLO, obras=[OBRAS_EJEMPLO[0]] * 3),
    "obras_claves_trampa": _esc(
        [sala("obra-despensa", 1, 20, nombre="Obra despensa"), sala("obra-despensa-2", 2, 20, nombre="Otra"),
         sala("despensa", 3, 20, nombre="Despensa del nido")],
        obras=[{"clave": "despensa", "nombre": "Despensa", "ancho": 16},
               {"clave": "despensa", "nombre": "Despensa", "ancho": 16},
               {"clave": "despensa-2", "nombre": "Despensa dos", "ancho": 16}]),
    "obras_muchas": _esc(SALAS_EJEMPLO, obras=list(OBRAS_EJEMPLO) * 3),
    "obras_anchas": _esc(SALAS_EJEMPLO, obras=[{"clave": "x%d" % i, "nombre": "Ancha %d" % i, "ancho": 60}
                                               for i in range(4)]),
    "obras_con_minimo": _esc(SALAS_EJEMPLO, obras=[{"clave": "x%d" % i, "nombre": "Mínimo %d" % i,
                                                    "ancho": 14, "minimo": 40} for i in range(4)]),
    # entradas
    "entrada_0": _esc(SALAS_EJEMPLO, entrada=0),
    "entrada_80": _esc(SALAS_EJEMPLO, entrada=80),
    "entrada_159": _esc(SALAS_EJEMPLO, entrada=159),
    "entrada_fuera": _esc(SALAS_EJEMPLO, entrada=500),
    "entrada_negativa": _esc(SALAS_EJEMPLO, entrada=-5),
    # otras fundaciones y el hemisferio sur
    "sur": _esc(SALAS_EJEMPLO, fundacion=datetime.date(2026, 6, 21), sur=True),
    "bisiesto": _esc(SALAS_EJEMPLO, fundacion=datetime.date(2024, 2, 29)),
}

_PLANES = {}


def montar(nombre, semilla, salas=None):
    """Un plan nuevo de ese escenario (con salas, esas en lugar de las suyas). Sin obras, las de
    siempre: mundo.py les añade campos al montar un hormiguero, así que se usa una copia limpia
    para que no dependa de las otras pruebas."""
    e = ESCENARIOS[nombre]
    with mock.patch.object(T, "OBRAS", [dict(o) for o in OBRAS_EJEMPLO]):
        return Plan(semilla, e["fundacion"], copy.deepcopy(e["salas"] if salas is None else salas),
                    obras=copy.deepcopy(e["obras"]), entrada=e["entrada"], sur=e["sur"])


def plan_de(nombre, semilla):
    """El plan de ese escenario y esa semilla (se monta una vez y se reutiliza)."""
    if (nombre, semilla) not in _PLANES:
        _PLANES[nombre, semilla] = montar(nombre, semilla)
    return _PLANES[nombre, semilla]


def todos(pocas=None):
    """(escenario, semilla, plan) de todos los escenarios; con pocas, sólo sus primeras semillas."""
    for nombre, e in ESCENARIOS.items():
        for semilla in e["semillas"][:pocas]:
            yield nombre, semilla, plan_de(nombre, semilla)


def intervalo(s):
    return s.x0, s.x0 + s.ancho - 1


def celdas_de_rampas(plan):
    """Las celdas de todas las rampas: las del nido y las que se cavan en el año (con la salida)."""
    celdas = []
    for arriba, abajo, x, x2 in plan.rampas:
        celdas += T.rampa(x, PISOS[arriba], x2, PISOS[abajo])
    for o in plan.obras:
        if o.tipo in ("rampa", "salida"):
            celdas += o.celdas
    return celdas


def sin_camino(plan, salas, llega):
    """Las salas con algún sitio del suelo que no está en llega."""
    return [s.clave for s in salas if any((x, s.piso) not in llega for x in s.sitios())]


def suelos(plan):
    """Todos los sitios del suelo cavado (donde puede pararse una hormiga) bajo tierra."""
    return [(x, y) for y in range(PROF) for x in range(ANCHO) if plan.suelo_en(x, y)]


def alcanzables_bajo_tierra(plan, origen):
    """Como plan.alcanzables, pero sin andar por la superficie: se empieza en la entrada y
    sólo se va por dentro (los pasos los da el propio plan)."""
    vistos = {origen}
    cola = deque([origen])
    while cola:
        for n in plan._pasos(*cola.popleft(), vistos):
            vistos.add(n)
            if n[1] >= 0:
                cola.append(n)
    return vistos


def dia_con_celdas(obra, k):
    """El día en que esa obra lleva cavadas exactamente k celdas."""
    return obra.ini + (obra.fin - obra.ini) * (k + 0.5) / len(obra.celdas)


def esperada(x, ancho):
    """La columna en que tiene que quedar una sala con columna fija (si no choca con otra)."""
    return max(BORDE, min(ANCHO - BORDE - ancho, int(x)))


class TestLimitesYSolapes(unittest.TestCase):

    def test_todo_lo_cavado_queda_dentro_de_la_tierra(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                fuera = [(o.nombre, (x, y)) for o in plan.obras for x, y in o.celdas
                         if not (BORDE <= x <= ANCHO - 1 - BORDE and 0 <= y < PROF)]
                self.assertEqual([], fuera[:5])
                self.assertTrue(BORDE <= plan.entrada <= ANCHO - 1 - BORDE, plan.entrada)
                plan.actualizar(0.0)
                self.assertTrue(plan.cavado(plan.entrada, 0), "la entrada no está cavada")

    def test_salas_dentro_de_la_tierra_y_en_su_planta(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                for s in plan.salas_todas:
                    a, b = intervalo(s)
                    self.assertTrue(BORDE <= a and b <= ANCHO - 1 - BORDE, (s.clave, a, b))
                    self.assertIn(s.nivel, (1, 2, 3, 4), s.clave)
                    self.assertEqual(PISOS[s.nivel], s.piso, s.clave)
                    self.assertGreaterEqual(s.y0, 0, s.clave)
                    self.assertTrue(len(s.sitios()) > 0 and all(a <= x <= b for x in s.sitios()), s.clave)

    def test_las_salas_no_se_pisan(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                salas = plan.salas_todas
                for i, s in enumerate(salas):
                    for o in salas[i + 1:]:
                        if s.nivel != o.nivel:
                            continue
                        (a1, b1), (a2, b2) = intervalo(s), intervalo(o)
                        # entre dos salas de la misma planta, al menos GAP columnas de tierra
                        self.assertTrue(b1 + GAP < a2 or b2 + GAP < a1, (s.clave, a1, b1, o.clave, a2, b2))
                de_quien = {}
                for s in salas:
                    for c in T.sala_celdas(s):
                        self.assertNotIn(c, de_quien, "%s y %s comparten %s" % (s.clave, de_quien.get(c), c))
                        de_quien[c] = s.clave

    def test_las_rampas_no_atraviesan_salas(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                de_sala = {c: s.clave for s in plan.salas_todas for c in T.sala_celdas(s)}
                cruzadas = sorted({de_sala[c] for c in celdas_de_rampas(plan) if c in de_sala})
                if plan.rampa_mala is None:
                    self.assertEqual([], cruzadas)
                else:   # sólo si no hay más remedio, y con aviso
                    self.assertTrue(any("rampa sin atravesar" in a for a in plan.avisos), plan.avisos)

    def test_las_rampas_bajan_de_una_planta_a_la_siguiente(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                self.assertEqual(0, plan.rampas[0][0])
                self.assertEqual(plan.entrada, plan.rampas[0][2])
                for n, (arriba, abajo, x, x2) in enumerate(plan.rampas):
                    self.assertEqual((n, n + 1), (arriba, abajo))
                    self.assertEqual(2 * (PISOS[abajo] - PISOS[arriba]), abs(x2 - x))
                hondo = max([s.nivel for s in plan.salas_todas if s.principal], default=1)
                self.assertEqual(hondo, len(plan.rampas))

    def test_los_hallazgos_no_se_pisan_ni_estan_en_lo_cavado(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                cavadas = {c for o in plan.obras for c in o.celdas}
                ocupadas = set()
                for x, y, que, icono, _color, _fin in plan.objetos:
                    celdas = {(x + i, y) for i in range(len(icono))}
                    self.assertTrue(all(0 < cx < ANCHO - 1 and 0 <= cy < PROF - 3 for cx, cy in celdas), que)
                    self.assertFalse(celdas & cavadas, que)
                    self.assertFalse(celdas & ocupadas, que)
                    self.assertTrue(all(plan.tipo(cx, cy) != T.ROCA for cx, cy in celdas), que)
                    ocupadas |= celdas


class TestSalasDelNido(unittest.TestCase):

    def test_cada_sala_esta_o_tiene_aviso(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                claves = {s.clave for s in plan.salas_todas if s.principal}
                for d in ESCENARIOS[nombre]["salas"]:
                    if d["clave"] not in claves:
                        self.assertTrue(any(d["nombre"] in a for a in plan.avisos), (d["clave"], plan.avisos))

    def test_las_de_ejemplo_caben_todas_sin_avisos(self):
        for nombre in ("ejemplo", "repo", "obras_por_defecto"):
            for semilla in ESCENARIOS[nombre]["semillas"]:
                plan = plan_de(nombre, semilla)
                with self.subTest(escenario=nombre, semilla=semilla):
                    self.assertEqual([], plan.avisos)
                    self.assertEqual([], plan.sin_sitio)
                    self.assertIsNone(plan.rampa_mala)
                    self.assertEqual(len(ESCENARIOS[nombre]["salas"]),
                                     len([s for s in plan.salas_todas if s.principal]))

    def test_columnas_fijas(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                por_clave = {s.clave: s for s in plan.salas_todas}
                for d in ESCENARIOS[nombre]["salas"]:
                    s = por_clave.get(d["clave"])
                    if d.get("x") is None or s is None:
                        continue
                    if any(a.startswith("%s: la columna" % d["nombre"]) for a in plan.avisos):
                        continue
                    self.assertEqual(esperada(d["x"], d["ancho"]), s.x0, d["clave"])

    def test_columnas_que_chocan(self):
        for semilla in ESCENARIOS["x_chocan"]["semillas"]:
            plan = plan_de("x_chocan", semilla)
            with self.subTest(semilla=semilla):
                por_clave = {s.clave: s for s in plan.salas_todas}
                # se colocan por orden de clave: la primera se queda su columna, las otras avisan
                self.assertEqual(50, por_clave["a"].x0)
                self.assertIn("B: la columna 50 choca con otra sala", plan.avisos)
                self.assertIn("C: la columna 55 choca con otra sala", plan.avisos)
                self.assertEqual({"a", "b", "c"}, set(por_clave) & {"a", "b", "c"})

    def test_plantas_fuera_de_rango(self):
        for semilla in ESCENARIOS["plantas_fuera"]["semillas"]:
            plan = plan_de("plantas_fuera", semilla)
            with self.subTest(semilla=semilla):
                por_clave = {s.clave: s for s in plan.salas_todas}
                self.assertEqual({"a": 1, "b": 1, "c": 4, "d": 4, "e": 2},
                                 {k: por_clave[k].nivel for k in "abcde"})
                self.assertEqual(32, por_clave["e"].ancho)

    def test_salas_que_no_caben(self):
        for semilla in ESCENARIOS["ancha_200"]["semillas"]:
            plan = plan_de("ancha_200", semilla)
            with self.subTest(semilla=semilla):
                self.assertNotIn("ancha", {s.clave for s in plan.salas_todas})
                self.assertIn("Ancha no cabe en la planta 2", plan.avisos)

    def test_muchas_salas(self):
        for nombre in ("muchas_40", "muchas_20", "doce_en_la_1"):
            for semilla in ESCENARIOS[nombre]["semillas"]:
                plan = plan_de(nombre, semilla)
                with self.subTest(escenario=nombre, semilla=semilla):
                    nido = [s for s in plan.salas_todas if s.principal]
                    self.assertGreater(len(nido), 0)
                    # las que se quedan fuera, cada una con su aviso
                    fuera = len(ESCENARIOS[nombre]["salas"]) - len(nido)
                    self.assertEqual(fuera, len([a for a in plan.avisos if " no cabe en la planta " in a]))


class TestCaminos(unittest.TestCase):

    def test_todas_las_salas_alcanzables_el_dia_0(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                plan.actualizar(0.0)
                nido = [s for s in plan.salas_todas if s.principal]
                self.assertEqual({s.clave for s in nido}, {s.clave for s in plan.salas(0.0)})
                self.assertEqual([], sin_camino(plan, nido, plan.alcanzables((plan.entrada, -1))))
                self.assertEqual([plan.entrada], plan.salidas(0.0))

    def test_todas_las_salas_alcanzables_al_acabar_el_ano(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                plan.actualizar(FIN_DEL_ANO)
                self.assertEqual(len(plan.salas_todas), len(plan.salas(FIN_DEL_ANO)))
                llega = plan.alcanzables((plan.entrada, -1))
                self.assertEqual([], sin_camino(plan, plan.salas_todas, llega))
                # y cualquier sitio del suelo cavado (galerías, rampas, salidas)
                self.assertEqual([], [c for c in suelos(plan) if c not in llega][:5])

    def test_camino_desde_la_entrada_hasta_cada_sala(self):
        for nombre, semilla, plan in todos(pocas=2):
            with self.subTest(escenario=nombre, semilla=semilla):
                plan.actualizar(FIN_DEL_ANO)
                for s in plan.salas_todas:
                    destino = (s.sitios()[len(s.sitios()) // 2], s.piso)
                    ruta = plan.camino((plan.entrada, -1), destino)
                    self.assertIsNotNone(ruta, s.clave)
                    self.assertEqual(destino, ruta[-1])
                    for (x1, y1), (x2, y2) in zip([(plan.entrada, -1)] + ruta, ruta):
                        self.assertEqual(1, abs(x2 - x1))   # paso a paso, sin saltos
                        self.assertLessEqual(abs(y2 - y1), 8)
                        self.assertTrue(plan.suelo_en(x2, y2))

    def test_las_salas_del_ano_alcanzables_al_terminarse(self):
        for nombre, semilla, plan in todos(pocas=3):
            with self.subTest(escenario=nombre, semilla=semilla):
                for o in plan.obras:
                    if o.sala is None:
                        continue
                    plan.actualizar(o.fin)
                    self.assertIn(o.sala, plan.salas(o.fin))
                    self.assertEqual([], sin_camino(plan, plan.salas(o.fin), plan.alcanzables((plan.entrada, -1))))

    def test_ninguna_obra_empieza_desconectada(self):
        """Cada obra empieza junto a algo ya cavado, y las hormigas llegan andando a su frente."""
        for nombre, semilla, plan in todos(pocas=4):
            with self.subTest(escenario=nombre, semilla=semilla):
                for o in plan.obras[1:]:
                    plan.actualizar(o.ini)
                    x, y = o.celdas[0]
                    junto = [(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                    self.assertTrue(any(plan.cavado(*c) for c in junto), (o.nombre, o.celdas[0]))
                    d = dia_con_celdas(o, 1)
                    plan.actualizar(d)
                    self.assertIs(o, plan.obra_actual(d))
                    frente = plan.frente(d)
                    self.assertIsNotNone(frente, o.nombre)
                    self.assertIsNotNone(plan.camino((plan.entrada, -1), frente), (o.nombre, frente))

    def test_ninguna_obra_empieza_desconectada_con_las_de_ejemplo(self):
        """Lo mismo con todas las semillas de las salas de ejemplo, mirando sólo lo cavado."""
        for semilla in ESCENARIOS["ejemplo"]["semillas"]:
            plan = plan_de("ejemplo", semilla)
            with self.subTest(semilla=semilla):
                for o in plan.obras[1:]:
                    plan.actualizar(o.ini)
                    x, y = o.celdas[0]
                    junto = [(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                    self.assertTrue(any(plan.cavado(*c) for c in junto), (o.nombre, o.celdas[0]))

    def test_segunda_salida_lejos_de_la_entrada(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                plan.actualizar(FIN_DEL_ANO)
                salidas = plan.salidas(FIN_DEL_ANO)
                self.assertEqual(plan.entrada, salidas[0])
                self.assertLessEqual(len(salidas), 2)
                for x in salidas[1:]:   # si hay sitio para ella: si no, no se cava
                    self.assertGreater(abs(x - plan.entrada), 24)
                    self.assertTrue(BORDE <= x <= ANCHO - 1 - BORDE, x)
                    self.assertTrue(plan.suelo_en(x, 0), x)

    # la segunda salida comunica por dentro con el nido. Antes podía empezar justo encima de la
    # rampa que baja de la planta 1 a la 2: su primer escalón quedaba a 9 filas o más del suelo
    # de esa rampa (las hormigas trepan como mucho 8) y sólo se llegaba a ella desde fuera (con
    # las salas de ejemplo, por ejemplo, con la semilla 19)
    def test_la_segunda_salida_comunica_por_dentro(self):
        for nombre in ("ejemplo", "entrada_159"):
            for semilla in range(40):
                plan = plan_de(nombre, semilla)
                with self.subTest(escenario=nombre, semilla=semilla):
                    plan.actualizar(FIN_DEL_ANO)
                    llega = alcanzables_bajo_tierra(plan, (plan.entrada, -1))
                    for o in plan.obras:
                        if o.tipo == "salida":
                            sueltos = [c for c in o.celdas if plan.suelo_en(*c) and c not in llega]
                            self.assertEqual([], sueltos)

    # y, por lo mismo, mientras se cava se llega andando a su frente (antes, en la última parte,
    # las hormigas no podían ir a cavar)
    def test_el_frente_de_la_segunda_salida_siempre_se_alcanza(self):
        for semilla in range(40):
            plan = plan_de("ejemplo", semilla)
            with self.subTest(semilla=semilla):
                for o in plan.obras:
                    if o.tipo != "salida":
                        continue
                    for k in range(1, len(o.celdas), 2):
                        d = dia_con_celdas(o, k)
                        plan.actualizar(d)
                        frente = plan.frente(d)
                        self.assertIsNotNone(plan.camino((plan.entrada, -1), frente), (k, frente))


class TestObrasDelAno(unittest.TestCase):

    def test_ninguna_obra_mas_estrecha_de_14(self):
        """Si no caben, se estrechan, pero nunca por debajo de 14 columnas (antes, de 16 a 12)."""
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                for o in plan.obras:
                    if o.sala is not None:
                        self.assertGreaterEqual(o.sala.ancho, T.ANCHO_MIN, o.sala.nombre)

    def test_claves_sin_choques(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                claves = [s.clave for s in plan.salas_todas]
                self.assertEqual(len(claves), len(set(claves)))
                nido = {d["clave"] for d in ESCENARIOS[nombre]["salas"]}
                for s in plan.salas_todas:
                    if s.principal:
                        self.assertIn(s.clave, nido)
                    else:
                        self.assertTrue(s.clave.startswith("obra-"), s.clave)

    def test_claves_trampa(self):
        obras = ESCENARIOS["obras_claves_trampa"]["obras"]
        for semilla in ESCENARIOS["obras_claves_trampa"]["semillas"]:
            plan = plan_de("obras_claves_trampa", semilla)
            with self.subTest(semilla=semilla):
                self.assertEqual([], plan.sin_sitio)
                del_ano = [o.sala for o in plan.obras if o.sala is not None]
                self.assertEqual(["obra-despensa-3", "obra-despensa-4", "obra-despensa-2-2"],
                                 [s.clave for s in del_ano])
                for s, d in zip(del_ano, obras):
                    self.assertEqual((d["nombre"], d["clave"], d["clave"]), (s.nombre, s.tipo, s.funcion))
                # las del nido siguen siendo las suyas y están desde el día 0
                self.assertEqual({"obra-despensa", "obra-despensa-2", "despensa"},
                                 {s.clave for s in plan.salas(0.0)})

    def test_obras_repetidas(self):
        for semilla in ESCENARIOS["obras_repetidas"]["semillas"]:
            plan = plan_de("obras_repetidas", semilla)
            with self.subTest(semilla=semilla):
                claves = [o.sala.clave for o in plan.obras if o.sala is not None]
                self.assertEqual(["obra-despensa", "obra-despensa-2", "obra-despensa-3"][:len(claves)], claves)
                self.assertEqual(3, len(claves) + len(plan.sin_sitio))

    def test_cada_sala_del_ano_aparece_al_terminarse(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                for o in plan.obras:
                    if o.sala is None:
                        continue
                    self.assertNotIn(o.sala, plan.salas(o.ini))
                    self.assertIn(o.sala, plan.salas(o.fin))
                    self.assertFalse(o.sala.principal)

    def test_tipo_y_ancho_de_las_salas_del_ano(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                pedidas = list(ESCENARIOS[nombre]["obras"] if ESCENARIOS[nombre]["obras"] is not None
                               else OBRAS_EJEMPLO)
                hechas = [o.sala for o in plan.obras if o.sala is not None]
                self.assertEqual(len(pedidas), len(hechas) + len(plan.sin_sitio))
                i = 0
                for d in pedidas:   # en orden; las que no caben, en sin_sitio
                    if i < len(hechas) and hechas[i].nombre == d["nombre"] and \
                            hechas[i].clave.startswith("obra-" + d["clave"]):
                        s = hechas[i]
                        i += 1
                        minimo = int(d.get("minimo", 0))
                        self.assertGreaterEqual(s.ancho, minimo, s.clave)
                        self.assertLessEqual(s.ancho, max(int(d.get("ancho", 22)), minimo), s.clave)
                        self.assertEqual(d.get("tipo", d["clave"]), s.tipo)
                    else:
                        self.assertIn(d["nombre"], plan.sin_sitio)
                self.assertEqual(len(hechas), i)

    def test_calendario_de_las_obras(self):
        for nombre, semilla, plan in todos():
            with self.subTest(escenario=nombre, semilla=semilla):
                ini = plan.obras[0]
                self.assertEqual(("inicial", -2.0, -1.0), (ini.tipo, ini.ini, ini.fin))
                antes = 0.0
                for o in plan.obras[1:]:
                    self.assertTrue(o.celdas, o.nombre)
                    self.assertGreaterEqual(o.ini, max(1.0, antes), o.nombre)
                    self.assertGreater(o.fin, o.ini, o.nombre)
                    antes = o.fin
                if len(plan.obras) > 1:   # las obras duran el año, pero no más
                    self.assertTrue(300 <= plan.obras[-1].fin <= 365, plan.obras[-1].fin)


class TestDeterminismo(unittest.TestCase):

    @staticmethod
    def huella(plan):
        return (plan.entrada, bytes(plan.suelo), list(plan.avisos), list(plan.sin_sitio), list(plan.objetos),
                [(s.clave, s.nombre, s.x0, s.piso, s.ancho, s.nivel, s.tipo) for s in plan.salas_todas],
                [(o.tipo, o.nombre, list(o.celdas), o.ini, o.fin, o.objeto) for o in plan.obras])

    @staticmethod
    def mapa(plan):
        return tuple(plan.cavado(x, y) for y in range(PROF) for x in range(ANCHO))

    def test_misma_semilla_mismo_trazado(self):
        for nombre in ESCENARIOS:
            for semilla in ESCENARIOS[nombre]["semillas"][:2]:
                with self.subTest(escenario=nombre, semilla=semilla):
                    self.assertEqual(self.huella(plan_de(nombre, semilla)), self.huella(montar(nombre, semilla)))

    def test_no_depende_del_orden_de_las_salas(self):
        for nombre in ("ejemplo", "x_fijas", "plantas_1_y_3", "muchas_20"):
            for semilla in (0, 7):
                with self.subTest(escenario=nombre, semilla=semilla):
                    salas = list(reversed(ESCENARIOS[nombre]["salas"]))
                    self.assertEqual(self.huella(montar(nombre, semilla)),
                                     self.huella(montar(nombre, semilla, salas)))

    def test_semillas_distintas_trazados_distintos(self):
        trazados = {repr(self.huella(plan_de("ejemplo", s))[5]) for s in range(10)}
        self.assertGreaterEqual(len(trazados), 8)

    def test_lo_cavado_un_dia_no_depende_de_como_se_llega(self):
        """Ir hacia delante, volver atrás o saltar días deja lo mismo que montarlo de cero."""
        plan = montar("ejemplo", 3)
        dias = [0.0, 50.5, 120.0, 200.25, FIN_DEL_ANO]
        directo = {}
        for d in dias:
            otro = montar("ejemplo", 3)
            otro.actualizar(d)
            directo[d] = self.mapa(otro)
        for d in dias + list(reversed(dias)) + [120.0, 0.0, 200.25]:
            plan.actualizar(d)
            self.assertEqual(directo[d], self.mapa(plan), d)
            self.assertEqual(sum(directo[d]), plan.total_cavado())

    def test_mismo_trazado_en_otro_proceso(self):
        """Lo que se calcula no depende del azar de cada arranque de Python (PYTHONHASHSEED)."""
        codigo = (
            "import datetime, hashlib, json, sys\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "from hormiga.tierra import Plan\n"
            "d = json.loads(sys.stdin.read())\n"
            "p = Plan(d['semilla'], datetime.date(2026, 1, 1), d['salas'], obras=d['obras'], entrada=20)\n"
            "h = (p.entrada, p.avisos, p.objetos, [(s.clave, s.x0, s.piso, s.ancho) for s in p.salas_todas],\n"
            "     [(o.tipo, o.nombre, o.celdas, o.ini, o.fin) for o in p.obras])\n"
            "print(hashlib.sha256(repr(h).encode('utf-8')).hexdigest())\n")
        datos = json.dumps({"semilla": 19, "salas": list(SALAS_EJEMPLO) + _muchas(6, 16),
                            "obras": list(OBRAS_EJEMPLO)})
        huellas = set()
        for azar in ("0", "1", "4242"):
            entorno = dict(os.environ, PYTHONHASHSEED=azar, PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run([sys.executable, "-c", codigo, RAIZ], input=datos, capture_output=True,
                               text=True, env=entorno, timeout=60)
            self.assertEqual(0, r.returncode, r.stderr)
            huellas.add(r.stdout.strip())
        self.assertEqual(1, len(huellas))


class TestTiempos(unittest.TestCase):

    def test_montar_el_plan_es_rapido(self):
        lento = 0.0
        for semilla in range(10):
            t = time.perf_counter()
            Plan(semilla, FUNDACION, copy.deepcopy(list(SALAS_EJEMPLO)), obras=copy.deepcopy(list(OBRAS_EJEMPLO)))
            lento = max(lento, time.perf_counter() - t)
        self.assertLess(lento, 1.0)

    def test_con_muchas_salas_tambien(self):
        t = time.perf_counter()
        Plan(5, FUNDACION, _muchas(40, 14), obras=[dict(o) for o in OBRAS_EJEMPLO])
        self.assertLess(time.perf_counter() - t, 5.0)

    def test_buscar_caminos_es_rapido(self):
        plan = plan_de("ejemplo", 0)
        plan.actualizar(FIN_DEL_ANO)
        t = time.perf_counter()
        llega = plan.alcanzables((plan.entrada, -1))
        for s in plan.salas_todas:
            plan.camino((plan.entrada, -1), (s.sitios()[0], s.piso))
        self.assertLess(time.perf_counter() - t, 1.0)
        self.assertGreater(len(llega), ANCHO)


if __name__ == "__main__":
    unittest.main()
